package bench

import "sync"

// SessionAudioCapture is the PCM heard and produced during one benchmark
// episode. It is deliberately separate from Transcript: benchmark records
// stay compact and review audio is retained only when a caller opts in.
//
// RoomPCM16 contains the exact mono 24 kHz PCM16 samples sent to the session,
// including harness trailing silence. Agent contains output chunks positioned
// on the same episode clock. All slices passed to CaptureAudio are owned by the
// recipient and may be retained after PlaySamples returns.
type SessionAudioCapture struct {
	SampleRateHz uint32
	RoomPCM16    []int16
	Agent        []TimedAudioChunk
}

// TimedAudioChunk is one mono PCM16 output chunk and its playout position.
// AtMS is measured from the same zero point as Transcript.Moments. Consecutive
// wire deltas are serialized onto one playout clock, as a speaker would play
// them, even when a server delivers them faster than realtime.
type TimedAudioChunk struct {
	AtMS  float64
	PCM16 []int16
}

type sessionAudioRecorder struct {
	mu             sync.Mutex
	room           []int16
	agent          []TimedAudioChunk
	agentPlayoutMS float64
	active         bool
}

func newSessionAudioRecorder(samples []int16) *sessionAudioRecorder {
	recorder := &sessionAudioRecorder{}
	recorder.setRoom(samples)
	return recorder
}

func (recorder *sessionAudioRecorder) setRoom(samples []int16) {
	if recorder == nil {
		return
	}
	recorder.mu.Lock()
	recorder.room = append(recorder.room[:0], samples...)
	recorder.mu.Unlock()
}

func (recorder *sessionAudioRecorder) beginEpisode() {
	if recorder == nil {
		return
	}
	recorder.mu.Lock()
	recorder.agent = nil
	recorder.agentPlayoutMS = 0
	recorder.active = true
	recorder.mu.Unlock()
}

func (recorder *sessionAudioRecorder) addAgent(atMS float64, samples []int16) float64 {
	if recorder == nil || len(samples) == 0 {
		return atMS
	}
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	if !recorder.active {
		return atMS
	}
	if atMS < recorder.agentPlayoutMS {
		atMS = recorder.agentPlayoutMS
	}
	copyOfSamples := append([]int16(nil), samples...)
	recorder.agent = append(recorder.agent, TimedAudioChunk{AtMS: atMS, PCM16: copyOfSamples})
	recorder.agentPlayoutMS = atMS + float64(len(copyOfSamples))*1000/24_000
	return atMS
}

func (recorder *sessionAudioRecorder) snapshot() SessionAudioCapture {
	if recorder == nil {
		return SessionAudioCapture{SampleRateHz: 24_000}
	}
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	agent := make([]TimedAudioChunk, len(recorder.agent))
	for index, chunk := range recorder.agent {
		agent[index] = TimedAudioChunk{AtMS: chunk.AtMS, PCM16: append([]int16(nil), chunk.PCM16...)}
	}
	return SessionAudioCapture{
		SampleRateHz: 24_000,
		RoomPCM16:    append([]int16(nil), recorder.room...),
		Agent:        agent,
	}
}
