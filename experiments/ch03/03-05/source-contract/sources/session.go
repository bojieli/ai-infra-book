package bench

import (
	"context"
	"encoding/base64"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/bojieli/OpenRealtime/binding"
	"github.com/bojieli/OpenRealtime/internal/audio"
	"github.com/bojieli/OpenRealtime/pcm"
	"github.com/bojieli/OpenRealtime/protocol/openrealtime"
	"github.com/bojieli/OpenRealtime/realtimeclient"
)

// Every suite reduces to the same thing: play audio into a session and judge
// what came out. This is that, once, so five suites do not each grow their own
// slightly different session driver - and so a timing number from one is
// comparable with a timing number from another.

// Moment is one thing that happened, with when it happened.
//
// A suite judges a conversation from this record rather than from the wire,
// which is what lets the same recording be scored for endpointing, overlap,
// and tool use without three different clients.
type Moment struct {
	// AtMS is milliseconds from the start of playback, so a moment can be
	// compared against a recording's own annotations.
	AtMS float64 `json:"at_ms"`
	Kind string  `json:"kind"`
	Text string  `json:"text,omitempty"`
	// AudioMS is how much audio a speech moment carried.
	AudioMS float64 `json:"audio_ms,omitempty"`
	// PlayoutAtMS is the start of this audio delta in the captured waveform.
	// AtMS remains its arrival time; a prefetched response may finish on the
	// wire before its queued audio has played. Historical moments omit this.
	PlayoutAtMS float64 `json:"playout_at_ms,omitempty"`
	// StreamAtMS is where in the input audio the endpoint says this happened.
	//
	// A speech_started event carries audio_start_ms, which is the endpoint's
	// own position in the stream it was fed - not when the notice reached the
	// client. Keeping only the arrival time confuses two different questions:
	// how long the detector took to hear speech, and how long the notice took
	// to come back. Subtracting one from the other separates them. Endpoints
	// that omit the field leave this zero.
	StreamAtMS float64 `json:"stream_at_ms,omitempty"`
	// Response fields preserve protocol evidence without inferring why a
	// response ended. Empty fields mean that the endpoint did not supply them.
	ResponseID           string `json:"response_id,omitempty"`
	ResponseStatus       string `json:"response_status,omitempty"`
	ResponseStatusReason string `json:"response_status_reason,omitempty"`
	Name                 string `json:"name,omitempty"`
	CallID               string `json:"call_id,omitempty"`
	// Arguments preserves the action the model actually grounded. Accuracy
	// cannot be reconstructed from a tool name alone.
	Arguments string `json:"arguments,omitempty"`
	Source    string `json:"source,omitempty"`
	Observer  string `json:"observer,omitempty"`
}

// Moment kinds.
const (
	MomentSpeechStarted = "user_speech_started"
	MomentSpeechStopped = "user_speech_stopped"
	MomentTranscript    = "transcript"
	MomentAgentText     = "agent_text"
	MomentAgentAudio    = "agent_audio"
	MomentResponseDone  = "response_done"
	MomentToolCall      = "tool_call"
	MomentToolResult    = "tool_result"
	MomentVideoFrame    = "video_frame_sent"
	MomentObservation   = "observation"
	MomentReady         = "environment_ready"
	// MomentScheduled marks a non-audio event the harness injected, so a
	// transcript shows why the agent spoke when nobody had said anything.
	MomentScheduled = "scheduled"
	MomentError     = "error"
)

// Transcript is the complete timed record of one conversation.
type Transcript struct {
	Moments []Moment `json:"moments"`
	// PlaybackMS is how long the input recording was.
	PlaybackMS float64                `json:"playback_ms"`
	SpeechCues []SpeechCueObservation `json:"speech_cues,omitempty"`
	Failure    string                 `json:"failure,omitempty"`
	// NegotiatedObservers is the authoritative observer set returned by the
	// session.updated OpenRealtime negotiation response. A nil slice means the
	// endpoint returned no OpenRealtime response; a non-nil empty slice means
	// the extension negotiated successfully but selected no observers.
	//
	// This deliberately does not come from Runtime. Graph-native runtime status
	// describes execution identity, while observer selection is wire-negotiated
	// session state.
	NegotiatedObservers []string `json:"negotiated_observers,omitempty"`
	// Runtime is the handshake-resolved architecture evidence emitted after
	// session.update. It is present only when CaptureRuntimeEvidence was set;
	// ordinary benchmark clients retain their existing wire behavior.
	Runtime *binding.Status `json:"runtime,omitempty"`
	// Execution is the versioned graph-native or explicitly legacy proof
	// produced by RuntimeAttestor from the live post-handshake status.
	Execution *ExecutionEvidence `json:"execution_evidence,omitempty"`
	// ExecutionError retains attestor/refusal details without turning a model
	// behavior row into an infrastructure score. Result.Reportable is the
	// publication gate.
	ExecutionError string `json:"execution_evidence_error,omitempty"`
	// Outstanding lifecycle counts are normally zero. They are retained so a
	// timeout distinguishes an agent still synthesising/responding from a
	// harness that merely waited too little after playback.
	OutstandingResponses int `json:"outstanding_responses,omitempty"`
	OutstandingTools     int `json:"outstanding_tools,omitempty"`
	// inspection is deliberately not serialized or exposed as benchmark data.
	// It exists only until attestTranscript spends the one-session bearer.
	inspection *openrealtime.InspectionAccess
}

// UserTurns returns what the user was heard to say, in order.
func (transcript Transcript) UserTurns() []string {
	var turns []string
	for _, moment := range transcript.Moments {
		if moment.Kind == MomentTranscript && strings.TrimSpace(moment.Text) != "" {
			turns = append(turns, moment.Text)
		}
	}
	return turns
}

// AgentTurns returns what the agent said, one entry per response.
func (transcript Transcript) AgentTurns() []string {
	var turns []string
	current := strings.Builder{}
	for _, moment := range transcript.Moments {
		switch moment.Kind {
		case MomentAgentText:
			current.WriteString(moment.Text)
		case MomentResponseDone:
			if strings.TrimSpace(current.String()) != "" {
				turns = append(turns, current.String())
			}
			current.Reset()
		}
	}
	if strings.TrimSpace(current.String()) != "" {
		turns = append(turns, current.String())
	}
	return turns
}

// ToolCalls returns the names of calls handed to the client.
func (transcript Transcript) ToolCalls() []string {
	var names []string
	for _, moment := range transcript.Moments {
		if moment.Kind == MomentToolCall {
			names = append(names, moment.Name)
		}
	}
	return names
}

// AudioBetween totals the agent audio emitted in a window, which is how
// overlap and barge-in are judged: whether the agent was making sound while
// the user was talking, and how quickly it stopped.
func (transcript Transcript) AudioBetween(fromMS, toMS float64) float64 {
	total := 0.0
	for _, moment := range transcript.Moments {
		if moment.Kind != MomentAgentAudio || moment.AtMS < fromMS || moment.AtMS > toMS {
			continue
		}
		total += moment.AudioMS
	}
	return total
}

// AudioStartedBetween is agent audio from turns that began inside the window.
//
// A silence check asks whether something in the window made the agent speak,
// and audio still playing from a turn that began before it cannot have. The
// distinction is not academic: an agent asked to report a build finishing says
// briefly that it will, and the tail of that sentence was being counted as a
// reaction to the first screen it saw three seconds later. Counting it that
// way also contradicts the scenario next to it, where the agent keeping the
// floor through somebody's "mhm" is the behaviour being asked for.
//
// A turn's audio begins at its first frame after the last response, which is
// the protocol's own boundary rather than a gap this has to guess at.
func (transcript Transcript) AudioStartedBetween(fromMS, toMS float64) float64 {
	total, startedAt := 0.0, -1.0
	for _, moment := range transcript.Moments {
		switch moment.Kind {
		case MomentResponseDone:
			startedAt = -1
		case MomentAgentAudio:
			if startedAt < 0 {
				startedAt = moment.AtMS
			}
			if startedAt < fromMS || startedAt > toMS {
				continue
			}
			if moment.AtMS < fromMS || moment.AtMS > toMS {
				continue
			}
			total += moment.AudioMS
		}
	}
	return total
}

// FirstAudioAfter is the latency from a moment in the recording to the next
// audio the agent produced.
func (transcript Transcript) FirstAudioAfter(fromMS float64) (float64, bool) {
	for _, moment := range transcript.Moments {
		if moment.Kind == MomentAgentAudio && moment.AtMS >= fromMS {
			return moment.AtMS - fromMS, true
		}
	}
	return 0, false
}

// FirstToolCallAfter is the wait from a moment in the recording to the next
// time a named tool was called.
//
// A silent act is still an answer. Measuring how soon it happened as a wait
// for speech asks an agent whose right move is to press a key and say nothing
// to fail either the latency check or the silence one beside it.
func (transcript Transcript) FirstToolCallAfter(name string, fromMS float64) (float64, bool) {
	for _, moment := range transcript.Moments {
		if moment.Kind == MomentToolCall && moment.Name == name && moment.AtMS >= fromMS {
			return moment.AtMS - fromMS, true
		}
	}
	return 0, false
}

// SessionConfig configures one conversation.
type SessionConfig struct {
	// Endpoint is the WebSocket protocol endpoint or WebRTC SDP endpoint.
	Endpoint string
	// Transport selects websocket or webrtc. Empty preserves websocket.
	Transport string
	Token     string
	Model     string
	// Instructions is the agent instruction for this task.
	Instructions string
	// Tools are declared to the session. Their results come from Respond.
	Tools []json.RawMessage
	// Respond answers a tool call. Returning an error ends the task; a nil
	// function refuses every call, which is correct for a suite with no tools.
	Respond func(name string, arguments json.RawMessage) (json.RawMessage, error)
	// HandleTool is the context-aware form used by interactive environments.
	// It takes precedence over Respond and receives the call identity so an
	// evaluator can retain an exact action trace and propagate idempotency.
	HandleTool func(context.Context, ToolRequest) (json.RawMessage, error)
	// ConcurrentTools runs HandleTool outside the protocol event collector.
	//
	// Meeting and agent evaluations use this when a knowledge tool deliberately
	// remains outstanding while more audio and video arrive. The collector
	// continues recording those events and does not declare the conversation
	// quiet until every tool result has returned. Ordinary suites retain the
	// historical synchronous behavior by leaving this false.
	ConcurrentTools bool
	// Observers selects the named OpenRealtime perception plug-ins for this
	// session. Empty delegates to the binding's documented default set. Names
	// are sent only when the OpenRealtime extension is otherwise negotiated.
	Observers []string
	// Realtime plays audio at its own rate. Turning it off makes a suite
	// faster and its timing numbers meaningless, so it stays on for anything
	// that reports latency.
	Realtime bool
	// TrailingSilence is appended so server endpointing fires on the last
	// utterance. Zero selects 1200 ms.
	TrailingSilence time.Duration
	// WorkingTimeout bounds silence while the agent still owes a response, as
	// distinct from the short quiet that means it has finished. Zero selects
	// thirty seconds.
	WorkingTimeout time.Duration
	// PostPlaybackQuiet is how long a session with no protocol work visibly
	// outstanding must remain quiet after playback before collection ends.
	// Passive observation and debug traffic is recorded but does not extend
	// this interval; continuing video cannot keep a completed task alive.
	// Zero selects three seconds. Suites with an asynchronous slow lane may
	// raise this without weakening their action deadlines; Timeout remains the
	// hard conversation horizon.
	PostPlaybackQuiet time.Duration
	// Timeout bounds one conversation.
	Timeout time.Duration
	// Quiet suppresses per-task progress.
	Quiet bool
	// CaptureAudio receives a copy of the exact room/input PCM and timed agent
	// output after the attempt ends. It is called once on every return path,
	// including connection, protocol, and timeout failures. Audio is not added
	// to Transcript or its JSON representation. A capture error is joined to
	// the attempt error so a requested review artifact cannot fail silently.
	CaptureAudio func(SessionAudioCapture) error
	// CaptureVideo receives each non-empty video frame after it has been
	// successfully sent. Calls are synchronous and serialized across every
	// configured stream; a sink error terminates the attempt. Frame bytes are
	// owned by the recipient and are not added to Transcript or its JSON.
	CaptureVideo func(SessionVideoCapture) error
	// CaptureScheduled receives an immutable owned copy of each authored event
	// only after the exact canonical JSON value was successfully submitted to
	// the transport. Calls are synchronous and ordered by cue time. A callback
	// error terminates the attempt and the event is not recorded as a successful
	// MomentScheduled. Scheduled metadata and encoded bytes are validated and
	// bounded before the session connection is opened.
	CaptureScheduled func(SessionScheduledCapture) error
	// CaptureRuntimeEvidence negotiates the session debug category and retains
	// the live binding status. Architecture experiments set it for every task;
	// it is opt-in because the developer trace is not application behavior.
	CaptureRuntimeEvidence bool
	// RuntimeAttestor resolves exact element/capability identities after the
	// live status arrives. Setting it automatically enables runtime evidence
	// negotiation. Graph-native cells use GraphAttestor; non-graph runtime
	// claims are deliberately not promoted to equivalent execution evidence.
	RuntimeAttestor RuntimeAttestor
	// AttestationScope identifies this task/session to a live inspector. Suites
	// set it to their task ID so selected paths cannot be attributed to a
	// different concurrent session.
	AttestationScope string
	// Scheduled are protocol events to send at points in the playback.
	//
	// A conversation is not only speech. A screen changes, a camera sees
	// something, a system event lands - and each of those has a moment,
	// exactly as an utterance does. Scheduling them on the same timeline is
	// what lets a scenario ask whether the agent spoke because of something it
	// saw while nobody was talking, which no amount of audio can express.
	Scheduled []ScheduledEvent
	// SpeechCues insert pre-authored PCM into reserved silence after observed
	// agent speech. They require Realtime and preserve actual cue positions.
	SpeechCues []SpeechCue
	// Video streams live frames until the conversation finishes. Unlike a
	// Scheduled event, a stream keeps observing while the agent acts, which is
	// necessary for multi-step computer use and transient visual tasks.
	Video []VideoStream
	// Ready runs after session configuration and video-source declarations but
	// before audio playback and frame capture. Browser tasks reset their clock
	// here so cue-to-action latency excludes connection setup.
	Ready func(context.Context) error
}

// ToolRequest is one complete model action received over the protocol.
type ToolRequest struct {
	CallID    string
	Name      string
	Arguments json.RawMessage
	Received  time.Time
}

// VideoStream is one declared source sampled for the duration of a task.
// Capture returns encoded JPEG or PNG bytes. A nil frame skips this tick.
type VideoStream struct {
	Source   string
	Width    int
	Height   int
	Interval time.Duration
	Capture  func(context.Context) ([]byte, error)
}

// ScheduledEvent is one protocol event and when to send it.
type ScheduledEvent struct {
	// AtMS is measured from the start of playback, like everything else in a
	// transcript, so a scheduled event and an utterance can be placed against
	// each other.
	AtMS int
	// Name is a stable harness-local identity copied onto MomentScheduled.
	// Review consumers use it to distinguish authored media from other
	// protocol events without inferring event kind from a generic moment count.
	Name  string
	Event map[string]any
}

// ErrConversationTimeout means a connected session continued working beyond
// its configured conversation horizon. Suites with a deterministic evaluator
// may score the state reached at that horizon as a completed negative outcome;
// setup, transport, and capture errors remain distinct infrastructure errors.
var ErrConversationTimeout = errors.New("the conversation did not finish before the timeout")

// ErrSessionFailure means the connected endpoint emitted a protocol error.
// Unlike ErrConversationTimeout, this is not an agent reaching a scoring
// horizon: ASR, model, engine, or transport work failed, so a suite must leave
// the task incomplete rather than publish the outage as a capability result.
var ErrSessionFailure = errors.New("the session reported a failure")

// Play drives one recording through a session and returns the timed record.
func Play(ctx context.Context, config SessionConfig, wavPath string) (Transcript, error) {
	samples, err := loadPCM24k(wavPath)
	if err != nil {
		return Transcript{}, err
	}
	return PlaySamples(ctx, config, samples)
}

// PlaySamples drives 24 kHz PCM16 samples through a session.
func PlaySamples(
	ctx context.Context, config SessionConfig, samples []int16,
) (transcript Transcript, runErr error) {
	audioRecorder := newSessionAudioRecorder(samples)
	if config.CaptureAudio != nil {
		defer func() {
			if err := config.CaptureAudio(audioRecorder.snapshot()); err != nil {
				runErr = errors.Join(runErr, fmt.Errorf("capture session audio: %w", err))
			}
		}()
	}
	if strings.TrimSpace(config.Endpoint) == "" {
		return Transcript{}, errors.New("a session needs an endpoint")
	}
	transport := strings.ToLower(strings.TrimSpace(config.Transport))
	if transport == "" {
		transport = TransportWebSocket
	}
	if transport != TransportWebSocket && transport != TransportWebRTC {
		return Transcript{}, fmt.Errorf("session transport must be websocket or webrtc, got %q", config.Transport)
	}
	if config.Timeout <= 0 {
		config.Timeout = 3 * time.Minute
	}
	if config.RuntimeAttestor != nil {
		config.CaptureRuntimeEvidence = true
	}
	if config.TrailingSilence <= 0 {
		config.TrailingSilence = 1200 * time.Millisecond
	}
	for index := range config.Video {
		stream := &config.Video[index]
		if strings.TrimSpace(stream.Source) == "" || stream.Width <= 0 || stream.Height <= 0 {
			return Transcript{}, fmt.Errorf("video stream %d requires a source and positive geometry", index)
		}
		if stream.Capture == nil {
			return Transcript{}, fmt.Errorf("video stream %q requires capture", stream.Source)
		}
		if stream.Interval <= 0 {
			stream.Interval = time.Second / 3
		}
	}
	for index, observer := range config.Observers {
		if strings.TrimSpace(observer) == "" || strings.TrimSpace(observer) != observer {
			return Transcript{}, fmt.Errorf("observer %d must be a canonical non-empty name", index)
		}
		for previous := range index {
			if config.Observers[previous] == observer {
				return Transcript{}, fmt.Errorf("observer %q is selected more than once", observer)
			}
		}
	}
	scheduled, err := prepareScheduledEvents(config.Scheduled)
	if err != nil {
		return Transcript{}, err
	}
	samples = append(samples, make([]int16, int(config.TrailingSilence.Seconds()*24_000))...)
	audioRecorder.setRoom(samples)
	cues, err := prepareSpeechCues(config.SpeechCues, samples, config.Realtime)
	if err != nil {
		return Transcript{}, err
	}
	defer func() { transcript.SpeechCues = append([]SpeechCueObservation(nil), cues.observed...) }()

	timed, cancel := context.WithTimeout(ctx, config.Timeout)
	// Whatever noticed the conversation horizon first, the outcome is the
	// horizon. It cancels every worker in the session at once, so a handshake,
	// a send, or a frame write that was in flight when it expired fails with
	// that deadline and would otherwise be published as an infrastructure
	// failure - the opposite of what the horizon means, which is that the
	// agent was still working and that is a scored negative. On an idle
	// machine the horizon almost always wins the race and the driver looked
	// deterministic; under load it does not. A transport fault that is not the
	// horizon, a protocol failure the endpoint reported, and a caller who
	// cancelled all still surface as themselves.
	defer func() {
		switch {
		case runErr == nil,
			errors.Is(runErr, ErrConversationTimeout), errors.Is(runErr, ErrSessionFailure),
			ctx.Err() != nil, !errors.Is(timed.Err(), context.DeadlineExceeded):
			return
		}
		runErr = ErrConversationTimeout
	}()
	defer cancel()
	// The conversation horizon bounds task behavior, not the underlying
	// connection's identity lifetime. Keep the transport alive until terminal
	// runtime attestation has spent the session-scoped inspection capability;
	// otherwise the read deadline closes the server session first and a timed-
	// out-but-scoreable task loses its exact graph evidence to a 404 race.
	connectionContext, closeConnectionContext := context.WithCancel(ctx)
	defer closeConnectionContext()
	endpoint := config.Endpoint
	if transport == TransportWebRTC &&
		(strings.HasPrefix(strings.ToLower(endpoint), "ws://") ||
			strings.HasPrefix(strings.ToLower(endpoint), "wss://")) {
		// A benchmark may point at an ordinary production protocol endpoint.
		// Terminate WebRTC in-process with the same adapter `serve` uses so the
		// sensor/executor still crosses RTP and SCTP without requiring the target
		// process to have opened an additional port.
		var closeAdapter func()
		endpoint, closeAdapter, err = startLoopbackWebRTC(endpoint, config.Token, config.Model)
		if err != nil {
			return Transcript{}, fmt.Errorf("start benchmark WebRTC adapter: %w", err)
		}
		defer closeAdapter()
	}
	var client realtimeSession
	if transport == TransportWebRTC {
		client, err = dialWebRTC(timed, connectionContext, endpoint, config.Token, config.Model)
	} else {
		client, err = realtimeclient.Dial(timed, realtimeclient.Config{
			URL: config.Endpoint, Token: config.Token, Model: config.Model,
			LifetimeContext: connectionContext,
		})
	}
	if err != nil {
		return Transcript{}, err
	}
	defer client.Close()

	recorder := &recorder{
		started: time.Now(), configured: make(chan struct{}), audio: audioRecorder,
	}
	collected := make(chan Transcript, 1)
	go func() { collected <- recorder.collect(timed, client, config) }()

	update := map[string]any{
		"type": "realtime",
		"audio": map[string]any{
			"input":  map[string]any{"format": map[string]any{"type": "audio/pcm", "rate": 24000}},
			"output": map[string]any{"format": map[string]any{"type": "audio/pcm", "rate": 24000}},
		},
	}
	if strings.TrimSpace(config.Instructions) != "" {
		update["instructions"] = config.Instructions
	}
	if len(config.Tools) > 0 {
		tools := make([]json.RawMessage, len(config.Tools))
		copy(tools, config.Tools)
		update["tools"] = tools
	}
	if len(config.Video) > 0 || len(config.Observers) > 0 || config.CaptureRuntimeEvidence {
		extension := map[string]any{"version": openrealtime.Version}
		if len(config.Video) > 0 {
			extension["supports"] = []string{
				string(openrealtime.FeatureVideoInput),
				string(openrealtime.FeatureObservations),
				string(openrealtime.FeatureComputerUse),
			}
		}
		if len(config.Observers) > 0 {
			extension["observers"] = append([]string(nil), config.Observers...)
		}
		if config.CaptureRuntimeEvidence {
			extension["debug"] = map[string]any{
				"enabled": true, "categories": []string{string(openrealtime.DebugSession)},
			}
		}
		update["openrealtime"] = extension
	}
	if err := client.Send(timed, map[string]any{"type": "session.update", "session": update}); err != nil {
		return Transcript{}, err
	}
	for _, stream := range config.Video {
		if err := client.Send(timed, map[string]any{
			"type": openrealtime.EventVideoSourceUpdate, "source": stream.Source,
			"state": openrealtime.SourceActive, "width": stream.Width, "height": stream.Height,
		}); err != nil {
			return Transcript{}, err
		}
	}
	if transport == TransportWebRTC {
		// RTP and SCTP are independently ordered. A browser can start its media
		// track while session.update is still crossing the data channel, which
		// makes the server correctly refuse the late configuration as an active-
		// speech mutation. Wait for the protocol acknowledgement before letting
		// recorded media start; WebSocket gets this ordering from one stream.
		select {
		case <-recorder.configured:
		case <-timed.Done():
			return recorder.snapshot(), fmt.Errorf("wait for WebRTC session configuration: %w", timed.Err())
		}
		// Establish the RTP receiver before the first recorded syllable. Browsers
		// keep a live microphone track open before a person begins speaking; an
		// evaluator that sends speech in its very first RTP packet instead makes
		// track startup part of ASR accuracy. Pace silence here so OnTrack, the
		// adapter's media pump, and the acoustic gate are all live. This setup is
		// deliberately outside the episode clock below.
		if mediaTransport, ok := client.(pcmInput); ok {
			if err := warmWebRTCAudio(timed, mediaTransport); err != nil {
				return recorder.snapshot(), fmt.Errorf("warm WebRTC audio track: %w", err)
			}
		}
	}
	if config.Ready != nil {
		if err := config.Ready(timed); err != nil {
			return Transcript{}, fmt.Errorf("prepare session environment: %w", err)
		}
	}
	// Ready is the shared zero point for authored audio cues, page events,
	// screen actions, and the transcript. Connection/configuration/media warmup
	// must not inflate reaction latency or move a later cue's scoring window.
	recorder.beginEpisode()
	recorder.add(Moment{Kind: MomentReady})

	// A conversation and its video workers have different shutdown edges. A
	// normal conversation may finish while Capture is inside a multi-command
	// operation (for example, installing, capturing, and removing a set-of-mark
	// overlay). Canceling that operation and returning immediately lets the
	// orphaned worker race the next benchmark case and can invalidate a shared
	// browser connection. Stop scheduling frames, let the one already in flight
	// finish under the caller's run-wide context, and join every worker before
	// the session or environment can be reused.
	videoStop := make(chan struct{})
	videoErrors := make(chan error, max(1, len(config.Video)))
	videoCapture := newSessionVideoCaptureSink(config.CaptureVideo)
	var videoWorkers sync.WaitGroup
	for _, stream := range config.Video {
		stream := stream
		videoWorkers.Add(1)
		go func() {
			defer videoWorkers.Done()
			streamVideo(ctx, videoStop, client, recorder, stream, videoCapture, videoErrors)
		}()
	}
	var stopVideoOnce sync.Once
	stopVideo := func() {
		stopVideoOnce.Do(func() { close(videoStop) })
		videoWorkers.Wait()
	}
	drainVideoErrors := func(initial error) error {
		errorsSeen := make([]error, 0, len(config.Video))
		if initial != nil {
			errorsSeen = append(errorsSeen, initial)
		}
		for {
			select {
			case err := <-videoErrors:
				if err != nil {
					errorsSeen = append(errorsSeen, err)
				}
			default:
				return errors.Join(errorsSeen...)
			}
		}
	}
	// This named-return cleanup covers every exit after workers start, including
	// scheduled-event and audio-send failures before the terminal select. A
	// requested capture sink must never disappear merely because another
	// protocol failure won the race to return.
	defer func() {
		stopVideo()
		runErr = errors.Join(runErr, drainVideoErrors(nil))
	}()

	frameSamples := 2400 // 100 ms for protocol audio frames.
	if _, mediaTransport := client.(pcmInput); mediaTransport {
		// RTP is packetised at 20 ms. Sending five packets in a 100 ms burst
		// would make the benchmark's sensor unlike the browser it is measuring.
		frameSamples = 480
	}
	started := time.Now()
	sent := 0
	for offset := 0; offset < len(samples); offset += frameSamples {
		end := min(offset+frameSamples, len(samples))
		// Anything due by this point in the playback goes first, so a scheduled
		// event lands before the audio that follows it rather than after.
		atMS := offset * 1000 / 24_000
		for sent < len(scheduled) && scheduled[sent].AtMS <= atMS {
			if cause := context.Cause(timed); cause != nil {
				return recorder.snapshot(), cause
			}
			sendErr := client.Send(timed, scheduled[sent].EventJSON)
			if cause := context.Cause(timed); cause != nil {
				return recorder.snapshot(), errors.Join(cause, sendErr)
			}
			if sendErr != nil {
				return recorder.snapshot(), sendErr
			}
			if err := emitScheduledCapture(timed, config.CaptureScheduled, scheduled[sent]); err != nil {
				return recorder.snapshot(), fmt.Errorf(
					"capture sent scheduled event %q: %w", scheduled[sent].Name, err,
				)
			}
			recorder.add(Moment{
				AtMS: float64(scheduled[sent].AtMS), Kind: MomentScheduled, Name: scheduled[sent].Name,
			})
			sent++
		}
		frame := cues.frame(offset, samples[offset:end], audioRecorder)
		if mediaTransport, ok := client.(pcmInput); ok {
			if err := mediaTransport.SendPCM24k(timed, frame); err != nil {
				return recorder.snapshot(), err
			}
		} else if err := client.Send(timed, map[string]any{
			"type":  "input_audio_buffer.append",
			"audio": base64.StdEncoding.EncodeToString(encodePCM(frame)),
		}); err != nil {
			return recorder.snapshot(), err
		}
		cues.sent(offset, frame, audioRecorder)
		if config.Realtime {
			elapsed := time.Duration(end) * time.Second / 24_000
			if wait := elapsed - time.Since(started); wait > 0 {
				select {
				case <-time.After(wait):
				case <-timed.Done():
					break
				}
			}
		}
	}
	recorder.playbackDone(float64(len(samples)) / 24.0)

	select {
	case <-collected:
		stopVideo()
		// A synchronous capture sink may still be finalizing a frame after the
		// protocol collector reaches quiet. Snapshot again after joining every
		// worker so the transcript and retained media describe the same sent
		// frame set.
		transcript := recorder.snapshot()
		transcript = attestTranscript(ctx, config, transcript)
		if strings.TrimSpace(transcript.Failure) != "" {
			return transcript, fmt.Errorf("%w: %s", ErrSessionFailure, transcript.Failure)
		}
		return transcript, nil
	case err := <-videoErrors:
		stopVideo()
		transcript := attestTranscript(ctx, config, recorder.snapshot())
		// The conversation horizon cancels the video sender along with
		// everything else, so a frame that was mid-write when it expired fails
		// with that deadline rather than with a fault of its own. Which worker
		// noticed the horizon first is a scheduling accident, and on a loaded
		// machine it is often this one; the outcome is still the horizon. A
		// transport fault that is not the horizon, and a caller who cancelled,
		// both still surface as themselves.
		if errors.Is(timed.Err(), context.DeadlineExceeded) {
			if strings.TrimSpace(transcript.Failure) != "" {
				return transcript, fmt.Errorf("%w: %s", ErrSessionFailure, transcript.Failure)
			}
			return transcript, ErrConversationTimeout
		}
		return transcript, err
	case <-timed.Done():
		stopVideo()
		transcript := attestTranscript(ctx, config, recorder.snapshot())
		if strings.TrimSpace(transcript.Failure) != "" {
			return transcript, fmt.Errorf("%w: %s", ErrSessionFailure, transcript.Failure)
		}
		return transcript, ErrConversationTimeout
	}
}

func attestTranscript(ctx context.Context, config SessionConfig, transcript Transcript) Transcript {
	inspection := transcript.inspection
	transcript.inspection = nil
	if config.RuntimeAttestor == nil {
		return transcript
	}
	if transcript.Runtime == nil {
		transcript.ExecutionError = "runtime attestation requested but the endpoint emitted no live session status"
		return transcript
	}
	// Evidence collection is bounded independently from task execution. A
	// session can reach its own horizon while the caller remains live; this
	// still lets an inspector read final route state without allowing a failed
	// inspector to hang the benchmark driver.
	attestationContext, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	evidence, err := config.RuntimeAttestor.Attest(attestationContext, AttestationRequest{
		Scope: config.AttestationScope, Status: *transcript.Runtime, Inspection: inspection,
	})
	if err == nil {
		err = evidence.Validate()
	}
	if err != nil {
		transcript.ExecutionError = err.Error()
		return transcript
	}
	copy := evidence.Clone()
	transcript.Execution = &copy
	return transcript
}

const webRTCAudioWarmup = 200 * time.Millisecond

func warmWebRTCAudio(ctx context.Context, client pcmInput) error {
	const packetDuration = 20 * time.Millisecond
	packet := make([]int16, 24_000*int(packetDuration)/int(time.Second))
	started := time.Now()
	for sent := time.Duration(0); sent < webRTCAudioWarmup; sent += packetDuration {
		if err := client.SendPCM24k(ctx, packet); err != nil {
			return err
		}
		deadline := started.Add(sent + packetDuration)
		if wait := time.Until(deadline); wait > 0 {
			timer := time.NewTimer(wait)
			select {
			case <-timer.C:
			case <-ctx.Done():
				if !timer.Stop() {
					select {
					case <-timer.C:
					default:
					}
				}
				return context.Cause(ctx)
			}
		}
	}
	return nil
}

func streamVideo(
	ctx context.Context, stop <-chan struct{}, client realtimeSession, recorder *recorder,
	stream VideoStream, capture *sessionVideoCaptureSink, failures chan<- error,
) {
	send := func() error {
		frame, err := stream.Capture(ctx)
		if err != nil {
			return fmt.Errorf("capture video source %q: %w", stream.Source, err)
		}
		if len(frame) == 0 {
			return nil
		}
		mediaType, err := sessionVideoMediaType(frame)
		if err != nil {
			return fmt.Errorf("capture video source %q: %w", stream.Source, err)
		}
		wireTimestamp := time.Now().UnixMilli()
		if err := client.Send(ctx, map[string]any{
			"type": openrealtime.EventVideoFrameAppend, "source": stream.Source,
			"frame":        base64.StdEncoding.EncodeToString(frame),
			"timestamp_ms": wireTimestamp,
		}); err != nil {
			return fmt.Errorf("send video source %q: %w", stream.Source, err)
		}
		episodeAtMS := recorder.at()
		captureErr := capture.emit(SessionVideoCapture{
			Source: stream.Source, Width: stream.Width, Height: stream.Height,
			MediaType: mediaType, WireTimestamp: wireTimestamp,
			EpisodeAtMS: episodeAtMS, Data: frame,
		})
		recorder.add(Moment{Kind: MomentVideoFrame, Source: stream.Source})
		if captureErr != nil {
			return fmt.Errorf("capture sent video source %q: %w", stream.Source, captureErr)
		}
		return nil
	}
	if err := send(); err != nil {
		failures <- err
		return
	}
	ticker := time.NewTicker(stream.Interval)
	defer ticker.Stop()
	for {
		select {
		case <-stop:
			return
		case <-ctx.Done():
			return
		case <-ticker.C:
			if err := send(); err != nil {
				failures <- err
				return
			}
		}
	}
}

type recorder struct {
	mu         sync.Mutex
	started    time.Time
	moments    []Moment
	playbackMS float64
	// openResponses counts responses the server has created and not finished.
	// While it is above zero the agent still owes this turn something, so
	// silence is work rather than completion.
	openResponses       int
	openTools           int
	playbackFinishedAt  time.Time
	lastActivity        time.Time
	failure             string
	negotiatedObservers []string
	runtime             *binding.Status
	inspection          *openrealtime.InspectionAccess
	configured          chan struct{}
	configuredOnce      sync.Once
	audio               *sessionAudioRecorder
}

func (recorder *recorder) at() float64 {
	return float64(time.Since(recorder.started).Microseconds()) / 1000
}

func (recorder *recorder) add(moment Moment) {
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	moment.AtMS = recorder.at()
	recorder.moments = append(recorder.moments, moment)
	// Do not update lastActivity here. Moments also include locally sampled
	// video frames, which can continue forever and must not prevent quiet
	// detection. Conversational protocol events and completed tool work touch
	// activity at their actual boundaries below.
}

func (recorder *recorder) beginEpisode() {
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	recorder.started = time.Now()
	// Setup events are outside the episode clock, but a terminal protocol error
	// may race this transition and must remain in the returned evidence.
	var retained []Moment
	for _, moment := range recorder.moments {
		if moment.Kind == MomentError {
			moment.AtMS = 0
			retained = append(retained, moment)
		}
	}
	recorder.moments = retained
	recorder.lastActivity = time.Time{}
	recorder.audio.beginEpisode()
}

func (recorder *recorder) touch() {
	recorder.mu.Lock()
	recorder.lastActivity = time.Now()
	recorder.mu.Unlock()
}

func (recorder *recorder) playbackDone(milliseconds float64) {
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	recorder.playbackMS = milliseconds
	recorder.playbackFinishedAt = time.Now()
}

func (recorder *recorder) snapshot() Transcript {
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	moments := append([]Moment(nil), recorder.moments...)
	sort.SliceStable(moments, func(left, right int) bool {
		return moments[left].AtMS < moments[right].AtMS
	})
	var runtime *binding.Status
	if recorder.runtime != nil {
		copied := *recorder.runtime
		copied.Observers = append([]string(nil), recorder.runtime.Observers...)
		runtime = &copied
	}
	var inspection *openrealtime.InspectionAccess
	if recorder.inspection != nil {
		copied := *recorder.inspection
		inspection = &copied
	}
	var negotiatedObservers []string
	if recorder.negotiatedObservers != nil {
		negotiatedObservers = append([]string{}, recorder.negotiatedObservers...)
	}
	return Transcript{
		Moments: moments, PlaybackMS: recorder.playbackMS, Failure: recorder.failure,
		NegotiatedObservers: negotiatedObservers, Runtime: runtime,
		OutstandingResponses: recorder.openResponses, OutstandingTools: recorder.openTools,
		inspection: inspection,
	}
}

// collect reads the session until it goes quiet after playback.
//
// "Quiet after playback" rather than "a fixed number of responses": a suite
// recording may contain one turn or five, and counting responses would make
// the driver suite-specific.
//
// Quiet is measured from the later of playback ending and the last
// conversational event (excluding passive observation and debug traffic),
// which matters more than it sounds. Arming a timer only when an event arrives
// means a session that produces nothing after playback never arms it at all,
// and every task in that cell fails with a timeout - which looks like the
// system hanging rather than the harness waiting.
//
// Quiet only means finished while the agent owes nothing. This system has a
// reasoning phase that is silent by construction, so a turn that needs it is
// quiet for as long as the question is hard - and a driver that read that as
// completion would score the agent on the answers it managed before the stop
// watch, which is a measurement of the harness. An open response is the
// protocol saying work is still owed, so quiet is not the test while one is
// open; workingFor bounds that separately, because a server that opens a
// response and never finishes it must still fail rather than hang.
func (recorder *recorder) collect(
	ctx context.Context, client realtimeSession, config SessionConfig,
) Transcript {
	quietFor := config.PostPlaybackQuiet
	if quietFor <= 0 {
		quietFor = 3 * time.Second
	}
	workingFor := config.WorkingTimeout
	if workingFor <= 0 {
		workingFor = 30 * time.Second
	}
	ticker := time.NewTicker(200 * time.Millisecond)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return recorder.snapshot()
		case <-ticker.C:
			recorder.mu.Lock()
			finishedAt := recorder.playbackFinishedAt
			lastActivity := recorder.lastActivity
			working := recorder.openResponses > 0 || recorder.openTools > 0
			recorder.mu.Unlock()
			if finishedAt.IsZero() {
				continue
			}
			since := finishedAt
			if lastActivity.After(since) {
				since = lastActivity
			}
			limit := quietFor
			if working {
				limit = workingFor
			}
			if time.Since(since) >= limit {
				return recorder.snapshot()
			}
		case event, open := <-client.Events():
			if !open {
				// The stream ended. If the audio is still playing, this run
				// measured nothing: whatever the agent would have done for the
				// rest of the scenario never had a chance to happen, and every
				// check about staying silent passes by default. Measured, six
				// runs in one suite ended between one and eight seconds into a
				// thirty-five second scenario and three of them were scored as
				// passes.
				why := "the session stream ended while the scenario was still playing"
				if err := client.Err(); err != nil {
					why += ": " + err.Error()
				}
				recorder.mu.Lock()
				if recorder.playbackFinishedAt.IsZero() && recorder.failure == "" {
					recorder.failure = why
				}
				recorder.mu.Unlock()
				return recorder.snapshot()
			}
			switch event.Type {
			case openrealtime.EventObservationAdded, openrealtime.EventDebug:
				// These are passive sensor and inspection outputs. A camera may
				// keep observing after the agent has settled, and debug traffic
				// must not turn a completed conversation into a timeout. Preserve
				// both below without treating them as new conversational work.
			default:
				recorder.touch()
			}
			recorder.handle(ctx, client, config, event)
			recorder.mu.Lock()
			failed := recorder.failure != ""
			recorder.mu.Unlock()
			if failed {
				return recorder.snapshot()
			}
		}
	}
}

func (recorder *recorder) handle(
	ctx context.Context, client realtimeSession,
	config SessionConfig, event realtimeclient.Event,
) {
	switch event.Type {
	case "session.updated":
		var decoded struct {
			Session struct {
				OpenRealtime *openrealtime.Response `json:"openrealtime"`
			} `json:"session"`
		}
		if event.Decode(&decoded) == nil && decoded.Session.OpenRealtime != nil {
			// Start from a non-nil empty slice so an acknowledged selection of no
			// observers remains distinguishable from no OpenRealtime response.
			observers := append([]string{}, decoded.Session.OpenRealtime.Observers...)
			recorder.mu.Lock()
			recorder.negotiatedObservers = observers
			if config.CaptureRuntimeEvidence && decoded.Session.OpenRealtime.Debug != nil &&
				decoded.Session.OpenRealtime.Debug.Inspection != nil {
				access := *decoded.Session.OpenRealtime.Debug.Inspection
				recorder.inspection = &access
			}
			recorder.mu.Unlock()
		}
		if recorder.configured != nil {
			recorder.configuredOnce.Do(func() { close(recorder.configured) })
		}
	case "response.created":
		recorder.mu.Lock()
		recorder.openResponses++
		recorder.mu.Unlock()
	case "input_audio_buffer.speech_started":
		var decoded struct {
			AudioStartMS float64 `json:"audio_start_ms"`
		}
		_ = event.Decode(&decoded)
		recorder.add(Moment{Kind: MomentSpeechStarted, StreamAtMS: decoded.AudioStartMS})
	case "input_audio_buffer.speech_stopped":
		var decoded struct {
			AudioEndMS float64 `json:"audio_end_ms"`
		}
		_ = event.Decode(&decoded)
		recorder.add(Moment{Kind: MomentSpeechStopped, StreamAtMS: decoded.AudioEndMS})
	case "conversation.item.input_audio_transcription.completed":
		var decoded struct {
			Transcript string `json:"transcript"`
		}
		_ = event.Decode(&decoded)
		recorder.add(Moment{Kind: MomentTranscript, Text: decoded.Transcript})
	case "response.output_audio_transcript.delta":
		var decoded struct {
			Delta      string `json:"delta"`
			ResponseID string `json:"response_id"`
		}
		_ = event.Decode(&decoded)
		if strings.TrimSpace(decoded.Delta) != "" {
			recorder.add(Moment{Kind: MomentAgentText, Text: decoded.Delta, ResponseID: decoded.ResponseID})
		}
	case "response.output_audio.delta":
		var decoded struct {
			Delta      string `json:"delta"`
			ResponseID string `json:"response_id"`
		}
		_ = event.Decode(&decoded)
		payload, err := base64.StdEncoding.DecodeString(decoded.Delta)
		switch {
		case err != nil:
			recorder.failProtocol("response.output_audio.delta is not valid base64")
		case len(payload)%2 != 0:
			recorder.failProtocol(fmt.Sprintf(
				"response.output_audio.delta carried %d bytes; PCM16 requires whole two-byte samples",
				len(payload)))
		case len(payload) > 0:
			samples := make([]int16, len(payload)/2)
			for index := range samples {
				samples[index] = int16(binary.LittleEndian.Uint16(payload[index*2:]))
			}
			playout := recorder.audio.addAgent(recorder.at(), samples)
			recorder.add(Moment{Kind: MomentAgentAudio, AudioMS: float64(len(payload)/2) / 24.0,
				ResponseID: decoded.ResponseID, PlayoutAtMS: playout})
		}
	case "response.done":
		var decoded struct {
			Response struct {
				ID            string `json:"id"`
				Status        string `json:"status"`
				StatusDetails struct {
					Reason string `json:"reason"`
				} `json:"status_details"`
			} `json:"response"`
		}
		if err := event.Decode(&decoded); err != nil {
			decoded.Response.Status = ""
			decoded.Response.StatusDetails.Reason = ""
		}
		recorder.mu.Lock()
		if recorder.openResponses > 0 {
			recorder.openResponses--
		}
		recorder.mu.Unlock()
		recorder.add(Moment{Kind: MomentResponseDone, ResponseID: decoded.Response.ID,
			ResponseStatus: decoded.Response.Status, ResponseStatusReason: decoded.Response.StatusDetails.Reason})
	case "response.function_call_arguments.done":
		var decoded struct {
			CallID string `json:"call_id"`
			Name   string `json:"name"`
			// The protocol carries arguments as a JSON *string*, not as an
			// object. Decoding it as raw JSON and handing that to a suite
			// gives every suite a quoted blob that will never match anything
			// it compares against - which looks like a model that always gets
			// arguments wrong.
			Arguments string `json:"arguments"`
		}
		_ = event.Decode(&decoded)
		recorder.add(Moment{
			Kind: MomentToolCall, CallID: decoded.CallID, Name: decoded.Name,
			Arguments: decoded.Arguments,
		})
		arguments := json.RawMessage(decoded.Arguments)
		if !json.Valid(arguments) {
			arguments = json.RawMessage(`{}`)
		}
		if config.ConcurrentTools && config.HandleTool != nil {
			recorder.mu.Lock()
			recorder.openTools++
			recorder.mu.Unlock()
			go func(callID, name string, arguments json.RawMessage) {
				err := recorder.answer(ctx, client, config, callID, name, arguments)
				recorder.mu.Lock()
				if recorder.openTools > 0 {
					recorder.openTools--
				}
				if err != nil && recorder.failure == "" && ctx.Err() == nil {
					recorder.failure = err.Error()
				}
				recorder.mu.Unlock()
			}(decoded.CallID, decoded.Name, append(json.RawMessage(nil), arguments...))
		} else if err := recorder.answer(ctx, client, config, decoded.CallID, decoded.Name, arguments); err != nil {
			recorder.mu.Lock()
			if recorder.failure == "" && ctx.Err() == nil {
				recorder.failure = err.Error()
			}
			recorder.mu.Unlock()
		}
	case openrealtime.EventObservationAdded:
		var decoded struct {
			Observer string `json:"observer"`
			Source   string `json:"source"`
			Text     string `json:"text"`
		}
		_ = event.Decode(&decoded)
		recorder.add(Moment{
			Kind: MomentObservation, Observer: decoded.Observer,
			Source: decoded.Source, Text: decoded.Text,
		})
	case openrealtime.EventDebug:
		if !config.CaptureRuntimeEvidence {
			break
		}
		var decoded struct {
			Category   string `json:"category"`
			Name       string `json:"name"`
			Attributes struct {
				Runtime *binding.Status `json:"runtime"`
			} `json:"attributes"`
		}
		_ = event.Decode(&decoded)
		if decoded.Category == string(openrealtime.DebugSession) &&
			decoded.Name == "session.updated" && decoded.Attributes.Runtime != nil {
			recorder.mu.Lock()
			copied := *decoded.Attributes.Runtime
			copied.Observers = append([]string(nil), decoded.Attributes.Runtime.Observers...)
			recorder.runtime = &copied
			recorder.mu.Unlock()
		}
	case "error":
		var decoded struct {
			Error struct {
				Message string `json:"message"`
			} `json:"error"`
		}
		_ = event.Decode(&decoded)
		recorder.add(Moment{Kind: MomentError, Text: decoded.Error.Message})
		recorder.mu.Lock()
		recorder.failure = decoded.Error.Message
		recorder.mu.Unlock()
	}
}

func (recorder *recorder) failProtocol(message string) {
	recorder.add(Moment{Kind: MomentError, Text: message})
	recorder.mu.Lock()
	if recorder.failure == "" {
		recorder.failure = message
	}
	recorder.mu.Unlock()
}

// answer returns a tool result.
//
// A suite with no tools still answers, with a refusal. Leaving a call
// unanswered would hang the turn and make every task in the cell time out,
// which would look like the system failing rather than the harness.
func (recorder *recorder) answer(
	ctx context.Context, client realtimeSession,
	config SessionConfig, callID, name string, arguments json.RawMessage,
) error {
	output := json.RawMessage(`{"error":"no tools are available in this task"}`)
	if config.HandleTool != nil {
		produced, err := config.HandleTool(ctx, ToolRequest{
			CallID: callID, Name: name, Arguments: arguments, Received: time.Now(),
		})
		if err != nil {
			// Realtime function_call_output has no error member. The gateway's
			// deliberately narrow, protocol-wide failure representation is an
			// output beginning with "Error:". A JSON object containing an error
			// field is ordinary tool data and must not be misclassified.
			output = json.RawMessage("Error: " + err.Error())
		} else if len(produced) > 0 {
			output = produced
		}
	} else if config.Respond != nil {
		produced, err := config.Respond(name, arguments)
		if err != nil {
			output = json.RawMessage("Error: " + err.Error())
		} else if len(produced) > 0 {
			output = produced
		}
	}
	if err := client.Send(ctx, map[string]any{
		"type": "conversation.item.create",
		"item": map[string]any{
			"type": "function_call_output", "call_id": callID, "output": string(output),
		},
	}); err != nil {
		return fmt.Errorf("send result for %s: %w", name, err)
	}
	recorder.add(Moment{
		Kind: MomentToolResult, CallID: callID, Name: name, Text: string(output),
	})
	recorder.touch()
	if err := client.Send(ctx, map[string]any{"type": "response.create"}); err != nil {
		return fmt.Errorf("resume after %s: %w", name, err)
	}
	return nil
}

func encodePCM(samples []int16) []byte {
	encoded := make([]byte, len(samples)*2)
	for index, sample := range samples {
		binary.LittleEndian.PutUint16(encoded[index*2:], uint16(sample))
	}
	return encoded
}

// loadPCM24k reads a WAV file as 24 kHz mono PCM16, resampling if needed.
// LoadPCM24k reads a recording as the samples a session would play.
//
// Suites that judge a recording against its own annotations need the audio the
// harness sends, not the file as it sits on disk: the rate conversion is part
// of what the endpoint hears.
func LoadPCM24k(path string) ([]int16, error) { return loadPCM24k(path) }

func loadPCM24k(path string) ([]int16, error) {
	if _, err := os.Stat(path); err != nil {
		return nil, err
	}
	decoded, err := audio.ReadFile(path)
	if err != nil {
		return nil, err
	}
	return pcm24k(decoded)
}

// DecodePCM24k decodes an in-memory WAV into the format the Realtime protocol
// uses. Benchmark suites embed their audio so an installed binary owns every
// task asset and does not depend on a source checkout at runtime.
func DecodePCM24k(raw []byte) ([]int16, error) {
	decoded, err := audio.Decode(raw)
	if err != nil {
		return nil, err
	}
	return pcm24k(decoded)
}

func pcm24k(decoded audio.Decoded) ([]int16, error) {
	payload := decoded.PCM16LE
	if decoded.Metadata.SampleRateHz != 24_000 {
		resampler, err := pcm.NewResampler(decoded.Metadata.SampleRateHz, 24_000)
		if err != nil {
			return nil, err
		}
		converted, err := resampler.Push(payload)
		if err != nil {
			return nil, err
		}
		terminal, err := resampler.Finalize()
		if err != nil {
			return nil, err
		}
		payload = append(converted, terminal...)
	}
	samples := make([]int16, len(payload)/2)
	for index := range samples {
		samples[index] = int16(binary.LittleEndian.Uint16(payload[index*2:]))
	}
	return samples, nil
}
