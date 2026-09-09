package pep

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"net"
	"sort"
	"sync"
	"sync/atomic"
	"time"

	"github.com/bojieli/queqiao/internal/classifier"
	"github.com/bojieli/queqiao/internal/coded"
	"github.com/bojieli/queqiao/internal/limiter"
	"github.com/bojieli/queqiao/internal/memlimit"
	"github.com/bojieli/queqiao/internal/metrics"
	"github.com/bojieli/queqiao/internal/multipath"
	"github.com/bojieli/queqiao/internal/protocol"
	"github.com/bojieli/queqiao/internal/stripe"
)

var nextTelemetryID atomic.Uint64

const (
	maxLaneEvents = 256
	// The receiver's out-of-order capacity must be at least the sender's send
	// window, or an ordinary striped transfer can legitimately overflow it and
	// abort a healthy application flow. Bytes buffered out of order are always
	// bytes the sender has not had acknowledged, so sizing both from the same
	// constant makes overflow impossible between peers running this code, and
	// keeps a hostile peer bounded by the same per-flow figure.
	//
	// The receiver cannot instead apply backpressure here: every lane feeds one
	// ordered reassembler, so pausing consumption would also pause the lane
	// carrying the segment that would close the gap.
	// It is sized against the sender's own retention bound, so a peer running
	// this code can never overflow it: the sender stops reading before it can
	// hold more unacknowledged bytes than this.
	maxReassemblyBytes = 2 * maxFlowOutstandingBytes
	// The byte bound above is what limits memory. This frame bound only stops
	// a peer using very small frames from turning the window into millions of
	// map entries.
	maxReassemblyFrames = 16384
	maxLaneWriteQueue   = 64
	// Keep a small part of the bounded queue available for interactive/new
	// frames even when a bulk producer has filled its queue. This is a hard
	// reservation, not an additional memory allowance: writeSlots still caps
	// the combined queues at maxLaneWriteQueue.
	maxLaneInteractiveReserve = 8
	maxLaneBulkQueue          = maxLaneWriteQueue - maxLaneInteractiveReserve
	// laneDeadPathDetection is how long QUIC spends deciding that a silent
	// lane is dead: it is the MaxIdleTimeout every lane is configured with in
	// quicConfig, named here because the replacement grace below is derived
	// from it. The two are one budget in two halves, not two independent
	// constants -- a flow cannot be given a replacement grace shorter than the
	// time its peer needs to notice there is anything to replace, so raising
	// the detection budget raises the grace with it.
	laneDeadPathDetection = 15 * time.Second
	// laneRescueHandshake is what a replacement lane still needs after the
	// peer has noticed: one scheduler tick, and a bounded handshake on a path
	// that has just proved hostile enough to kill a lane.
	laneRescueHandshake = 30 * time.Second
	// laneReplacementWait is the whole budget a flow spends with no healthy
	// lane before it gives up. It is spent per outage rather than per wait:
	// several call sites wait for the same missing lane, and each used to
	// start its own copy of this grace, so a flow that was never going to be
	// rescued burned the budget once per waiter. On the live gateway that was
	// visible as failures clustered at 76-106 s -- two graces, not one -- for
	// flows that had done their work in the first second. See issue #53.
	laneReplacementWait = laneDeadPathDetection + laneRescueHandshake
	// Once both FIN directions are observed, no additional application bytes
	// can be delivered. This grace lets a healthy final ACK arrive, but bounds
	// retention when the peer closes its last lane at exactly that point.
	flowCompletionGrace = 5 * time.Second
	// A local EOF is ambiguous between TCP half-close and full application
	// close. Escalate only after response traffic stops making progress, or
	// after the peer has acknowledged the local FIN; interactive sessions get
	// more time for legitimate quiet periods.
	flowAbortGrace        = 5 * time.Second
	interactiveAbortGrace = 30 * time.Second
	remoteFinDrainGrace   = 500 * time.Millisecond
	// Once the peer FIN has proved the receive sequence complete, do not spend
	// the full lane-replacement window trying to deliver its final ACK. If the
	// local direction is also closing, the server completion tombstone can
	// absorb a lost ACK without keeping the application flow alive.
	finalAckWriteGrace = 2 * time.Second
	// These limits are deliberately long enough for quiet SSH and remote
	// desktop sessions, while preventing an abandoned authenticated flow from
	// retaining a destination socket and replay window forever.
	defaultFlowIdleTimeout = 30 * time.Minute
	defaultFlowMaxLifetime = 24 * time.Hour
)

var (
	errFlowIdleTimeout       = errors.New("flow idle timeout")
	errFlowLifetime          = errors.New("flow lifetime exceeded")
	errLocalApplicationClose = errors.New("local application closed")
)

type mpLane struct {
	id          uint64
	kind        TransportKind
	fc          *frameConn
	tcpStriping bool
	// staged lanes consume admission capacity but cannot carry any flow frame
	// until their JOIN acknowledgement is on the wire. Without this state, an
	// active scheduler can put replayed DATA ahead of OPEN_OK on a replacement
	// stream, making a correct client reject the handshake.
	staged bool
	ready  atomic.Bool
	// control is a role, not a lane number. Lane zero begins in this role on a
	// pooled flow, but after a connection-generation reset its replacement has
	// a non-zero join ID and must inherit the same scheduling protection.
	control bool
	// writeHook is an internal deterministic fault-injection point used by
	// integration tests. Production lanes leave it nil, so the data path has
	// only one predictable nil check before the real framed write.
	writeHook func(protocol.Frame) error
	// writeQ is the bounded bulk/data queue. Interactive and new-flow frames
	// use writeInteractiveQ when it is initialized. Keeping a separate queue
	// lets the writer avoid sitting behind a burst of bulk retransmissions.
	// writeSlots is a semaphore shared by both queues, so the total queued
	// frames remain bounded by maxLaneWriteQueue rather than by the sum of
	// both channel capacities.
	writeQ chan laneFrame
	// pulling guards against two workers on one lane.
	pulling atomic.Bool
	// cwnd caches the transport's congestion window. Admission reads it for
	// every chunk offered to every lane.
	cwndMu        sync.Mutex
	cwndBytes     int
	inFlightBytes int
	cwndSampled   time.Time
	// admitted is when this lane joined the flow. It bounds eviction at the
	// lane ceiling: a lane younger than the rescue-race window may still be
	// waiting on the peer's crowning decision, so it is never the victim.
	admitted          time.Time
	writeInteractiveQ chan laneFrame
	writeSlots        chan struct{}
	writeDone         chan struct{}
	closed            atomic.Bool
	sent              atomic.Uint64
	recv              atomic.Uint64
	// suspected is the flow-stall watchdog's demotion mark: the lane is
	// believed to be carrying nothing useful, so it is passed over for new
	// writes while a healthier lane exists. It is never closed for this --
	// it keeps receiving, and an acknowledgement arriving on it clears the
	// mark, because that is direct proof the lane still round-trips.
	suspected atomic.Bool
	// rateMu guards a short-lived cache of the lane's transport statistics.
	// Reading them from QUIC on every frame would take the connection lock on
	// the hot path for information that changes on an RTT timescale.
	rateMu      sync.Mutex
	rateSampled time.Time
	rateBytes   float64       // estimated send rate in bytes per second
	rateRTT     time.Duration // smoothed round-trip time
}

// laneRateCacheTTL is far below one long-haul RTT, so the scheduler still
// reacts within a single congestion round while avoiding per-frame lock
// traffic on a fast local path.
const laneRateCacheTTL = 5 * time.Millisecond

func (l *mpLane) sendRate() (float64, time.Duration) {
	l.rateMu.Lock()
	defer l.rateMu.Unlock()
	now := time.Now()
	if !l.rateSampled.IsZero() && now.Sub(l.rateSampled) < laneRateCacheTTL {
		return l.rateBytes, l.rateRTT
	}
	if l.fc == nil {
		return 0, 0
	}
	provider, ok := l.fc.transport().(laneStatsProvider)
	if !ok {
		l.rateSampled = now
		return l.rateBytes, l.rateRTT
	}
	stats := provider.transportStats()
	rtt := stats.smoothedRTT
	if rtt <= 0 {
		rtt = stats.latestRTT
	}
	rate := float64(stats.controller.PacingRate)
	if rate <= 0 && stats.controller.CongestionWindow > 0 && rtt > 0 {
		rate = float64(stats.controller.CongestionWindow) / rtt.Seconds()
	}
	l.rateSampled, l.rateBytes, l.rateRTT = now, rate, rtt
	return rate, rtt
}

// laneFrame is a frame queued for one lane's writer, with an optional
// notification for when the transport has taken its bytes.
type laneFrame struct {
	frame     protocol.Frame
	onWritten func()
}

type inboundEvent struct {
	lane  *mpLane
	frame protocol.Frame
}

// laneFailure is emitted once for a physical lane. The identity prevents a
// delayed error from an old lane being confused with a replacement failure.
type laneFailure struct {
	lane *mpLane
	err  error
}

type multipathFlow struct {
	ctx           context.Context
	inner         net.Conn
	sessionID     [16]byte
	flowID        uint64
	chunkSize     int
	budget        *limiter.Budget
	metrics       *metrics.Registry
	logger        *slog.Logger
	memoryLimits  flowMemoryLimits
	sendMemory    *memlimit.Budget
	receiveMemory *memlimit.Budget

	sendAckFlag uint16
	recvAckFlag uint16

	lanesMu  sync.RWMutex
	lanes    map[uint64]*mpLane
	events   chan inboundEvent
	laneErr  chan laneFailure
	finalAck chan struct{}
	sendDone chan struct{}
	done     chan struct{}
	ackWake  chan struct{}
	ackErr   chan error

	classifier *classifier.Classifier
	// reserveControlLane is negotiated for pooled flows and is what separates
	// this flow's control plane from its data plane.
	//
	// Lane 0 is the authenticated, pooled connection and carries control:
	// OPEN, ACK, FIN, RESET. Once this flow has a lane of its own, its data
	// moves there and lane 0 keeps only control. Two things follow, and both
	// are the reason the reservation exists rather than side effects of it:
	// a bulk congestion window stays off the connection short flows share,
	// and the flow's own acknowledgements stay off the stream carrying its
	// own bulk.
	//
	// If no isolated lane is healthy, both planes fall back to lane 0. An
	// available flow beats an isolated one.
	reserveControlLane bool
	// resumeRefused records that the peer answered a lane join by saying it
	// does not know this session. That answer is permanent, so it ends the
	// replacement grace rather than being retried.
	resumeRefused atomic.Bool
	// capacityRefusals counts consecutive rescue rounds the peer answered
	// with its lane-admission ceiling. One answer is the ordinary loser of a
	// rescue race; several in a row with no successful round between them are
	// the signature of a wedged admission slot the peer cannot see, which is
	// when the answer stops being treated as transient.
	capacityRefusals atomic.Int64
	// replacementAbandoned records that whatever opens replacement lanes for
	// this flow has stopped: its attempt budget is spent, or its manager has
	// returned. The grace exists to cover the time a replacement needs to
	// arrive, so once nothing is going to attempt one it is only silence the
	// application is waiting through. It is set on the endpoint that opens
	// replacements; the other end keeps waiting for a rescue that is still
	// somebody's to send.
	replacementAbandoned atomic.Bool

	// Replacement diagnostics. A flow that fails with "lane replacement
	// timeout" records only that it gave up, and the live gateway produced 521
	// of those in two hours without the log saying whether a replacement lane
	// was ever offered, how many graces were burned, or how long the flow
	// spent with no lane at all. Distinguishing "nothing was opened" from
	// "lanes were opened and never became ready" is the difference between a
	// pool that will not rebuild and a path that will not carry a handshake,
	// and it cannot be recovered after the fact. See issue #53.
	replacementWaits     atomic.Uint64
	replacementTimeouts  atomic.Uint64
	replacementWaitNanos atomic.Int64
	lanesJoined          atomic.Uint64
	// replacementDeadline is when the current outage's grace runs out, in Unix
	// nanoseconds, or zero when the flow is not in an outage. It is what makes
	// laneReplacementWait a budget the flow spends once rather than one each
	// waiter spends separately, and it is cleared in startLane so that a flow
	// which really is being rescued gets a fresh grace for its next outage.
	replacementDeadline atomic.Int64
	// Replacement attempts, counted only for a flow that has no lane left.
	// `lanes_joined` says whether a replacement was ever admitted, and for
	// 84% of the gateway's lane-replacement-timeout failures the answer is no
	// -- but it cannot say why, because a dial whose handshake never completes
	// never reaches addLane and leaves the record identical to a flow where
	// nothing was ever dialled. Those are the two faults #53 needs separated:
	// a client pool that will not rebuild, against a path that will not carry
	// a handshake. Only the endpoint that opens replacements can tell them
	// apart, and only while it is trying. The other endpoint reports zeroes,
	// which is the true answer there: it opens nothing.
	replacementAttempts atomic.Uint64
	replacementFailures atomic.Uint64
	// Stall watchdog state. A lane is declared dead only on I/O error, which
	// on a path losing one direction means fifteen seconds of receive silence
	// -- while a flow with a full send window and no acknowledgements is
	// making no progress long before that. The watchdog measures progress
	// where delivery to the peer is actually recorded (the acknowledged send
	// offset and payload arrival) and, finding none while work is pending,
	// demotes the lane and asks for a rescue beside it. Nothing here closes
	// anything: suspected lanes keep receiving, and recover their full
	// eligibility on the first acknowledgement they carry.
	//
	// All of it is atomic or local to the watchdog goroutine; it introduces
	// no lock, and in particular never touches lanesMu while holding chunkMu
	// or replayMu.
	lastAckProgressNS atomic.Int64
	lastUpPayloadNS   atomic.Int64
	lastDownPayloadNS atomic.Int64
	// upAtLastDown is bytesUp at the moment the last downstream payload
	// arrived. bytesUp above it means the application sent something the
	// peer has not answered yet, which is the watchdog's "outstanding
	// request" gate for flows waiting on a response.
	upAtLastDown atomic.Uint64
	// minRTTNS is the smallest controller minimum-RTT the flow's lanes have
	// reported, refreshed by observeTransport. The stall threshold is three
	// of these.
	minRTTNS atomic.Int64
	// stallSignal advises the lane manager that a stall episode is in
	// progress. It is buffered at one and sent non-blockingly: the manager
	// acts on the flow's current state when it wakes, so a coalesced signal
	// loses nothing, and a flow with no listener (the server end) never
	// blocks its watchdog.
	stallSignal chan struct{}
	// rescueInFlight is set by the lane manager for the duration of one
	// rescue round. While it is set the watchdog does not signal: a request
	// queued behind an active round would only fire a redundant round the
	// moment the first one returns, before its fresh lane had any chance to
	// prove itself.
	rescueInFlight atomic.Bool
	// stallWatchdogDisabled turns the watchdog goroutine off entirely. Zero
	// in production; tests that pin exact dial counts set it so recovery
	// behaviour under measurement is deterministic.
	stallWatchdogDisabled bool
	// stallScan and stallGrace are zero in production. Tests shorten them so
	// the watchdog can be exercised without sleeping for seconds, the same
	// pattern as abortGrace above.
	stallScan  time.Duration
	stallGrace time.Duration
	// controlLaneShared reports whether another flow is currently using the
	// pooled control connection. Nil means "no", which is what a flow on a
	// dedicated connection should answer.
	controlLaneShared func() bool
	started           time.Time
	completionGrace   time.Duration
	// abortGrace and abortDrainGrace are zero in production. Tests shorten
	// the two independently so the inactivity and bounded-drain state machine
	// can be exercised without sleeping for seconds.
	abortGrace      time.Duration
	abortDrainGrace time.Duration
	bytesUp         atomic.Uint64
	bytesDown       atomic.Uint64
	class           atomic.Uint32
	// ackTrack answers "has this range arrived?", which is what clocks every
	// lane. scheduler and sendCtx let a lane joined mid-flow start carrying
	// data as soon as it is admitted.
	ackTrack  *ackTracker
	scheduler atomic.Pointer[stripe.Scheduler]
	sendCtx   atomic.Pointer[context.Context]
	// outstandingChunks are chunks written and not yet acknowledged. A single
	// watcher completes them as acknowledgements arrive, because they complete
	// out of order by design and a waiter goroutine per chunk would mean
	// hundreds a second on a fast flow.
	chunkMu           sync.Mutex
	outstandingChunks []outstandingChunk
	residency         residency
	acksIn            atomic.Uint64
	acksOut           atomic.Uint64
	acksSched         atomic.Uint64
	ackWriteNS        atomic.Uint64
	finSequence       atomic.Uint64
	remoteFinSequence atomic.Uint64
	finSent           atomic.Bool
	remoteFinSeen     atomic.Bool
	localClosed       atomic.Bool
	localClosedOnce   sync.Once
	localClosedCh     chan struct{}
	remoteAbort       atomic.Bool
	remoteAbortOnce   sync.Once
	remoteAbortCh     chan struct{}
	localAbortSent    atomic.Bool
	laneFailures      atomic.Uint64
	// openAckPending is set only when the caller waited for nothing. The
	// application may begin sending immediately, but the eventual OPEN_OK is
	// still required on the authenticated stream and is consumed by the flow
	// reader before ordinary data/control frames are accepted.
	openAckPending bool
	// openConfirmationRequired is true between an optimistic OPEN and OPEN_OK.
	// A coded lane uses it to place one reliable safety copy behind OPEN while
	// still sending the latency-sensitive coded copy immediately.
	openConfirmationRequired atomic.Bool
	// ackRanges is mandatory in protocol v1. It is useful to striped flows and
	// harmless for a single lane.
	ackRanges atomic.Bool
	// tcpStriping is negotiated per flow. When true, and only while every
	// healthy lane is TCP, the scheduler may distribute byte-offset chunks
	// across all lanes and re-inject a retired lane's unacknowledged chunks.
	tcpStriping atomic.Bool
	// gapPending marks that the peer should be told what is held above a gap,
	// which is an acknowledgement whose cumulative point has not moved.
	gapPending atomic.Bool
	// receivedRanges publishes what the reassembler currently holds out of
	// order, so the acknowledgement loop can report it without touching the
	// reassembler from another goroutine.
	rangesMu      sync.Mutex
	pendingRanges [][2]uint64
	ackSequence   atomic.Uint64
	ackClosing    atomic.Bool
	lastPayload   atomic.Int64
	// lastClassified is when the flow last re-examined its own class, so that
	// a flow which has stopped reading is still reclassified as it ages.
	lastClassified atomic.Int64
	lastActivity   atomic.Int64
	closeOnce      sync.Once
	doneOnce       sync.Once
	finished       atomic.Bool
	nextJoinID     uint64
	telemetryID    uint64
	baselineRTTNS  atomic.Int64
	currentRTTNS   atomic.Int64
	idleTimeout    time.Duration
	maxLifetime    time.Duration

	reinjections atomic.Uint64

	// recentMu guards the two-bucket window behind recentBytes, which decides
	// whether this flow is conversing or transferring at the moment rather
	// than over its whole life.
	recentMu               sync.Mutex
	recentStart            time.Time
	currentUp, currentDown uint64
	priorUp, priorDown     uint64

	replayMu sync.Mutex
	// closeFrame is this flow's half-close, retained until the peer
	// acknowledges it so a replacement lane can be handed it. It is the whole
	// of the retention window: everything else a replacement needs is held by
	// the scheduler, which re-offers it to any lane.
	closeFrame  *protocol.Frame
	acked       uint64
	highestSent uint64
}

func newMultipathFlow(ctx context.Context, inner net.Conn, sessionID [16]byte, flowID uint64, chunkSize int, sendAckFlag, recvAckFlag uint16, budget *limiter.Budget, registry *metrics.Registry, loggers ...*slog.Logger) *multipathFlow {
	var logger *slog.Logger
	if len(loggers) > 0 {
		logger = loggers[0]
	}
	return newMultipathFlowWithMemory(ctx, inner, sessionID, flowID, chunkSize, sendAckFlag, recvAckFlag, budget, registry, logger, defaultFlowMemoryLimits(), nil, nil, classifier.DefaultConfig())
}

func newMultipathFlowWithMemory(ctx context.Context, inner net.Conn, sessionID [16]byte, flowID uint64, chunkSize int, sendAckFlag, recvAckFlag uint16, budget *limiter.Budget, registry *metrics.Registry, logger *slog.Logger, memoryLimits flowMemoryLimits, sendMemory, receiveMemory *memlimit.Budget, classifierCfg classifier.Config) *multipathFlow {
	// A zero config would classify nothing, which reads as "every flow is new"
	// rather than as a misconfiguration. Falling back to the documented default
	// keeps a caller that forgot the parameter on the supported policy.
	if classifierCfg.NewBytes == 0 || classifierCfg.BulkBytes == 0 {
		classifierCfg = classifier.DefaultConfig()
	}
	if chunkSize <= 0 {
		chunkSize = defaultChunkSize
	}
	if memoryLimits.eventQueue <= 0 {
		memoryLimits = defaultFlowMemoryLimits()
	}
	f := &multipathFlow{
		ctx: ctx, inner: inner, sessionID: sessionID, flowID: flowID, chunkSize: chunkSize, budget: budget, metrics: registry,
		logger: logger, memoryLimits: memoryLimits, sendMemory: sendMemory, receiveMemory: receiveMemory,
		sendAckFlag: sendAckFlag, recvAckFlag: recvAckFlag,
		lanes: make(map[uint64]*mpLane), events: make(chan inboundEvent, memoryLimits.eventQueue), laneErr: make(chan laneFailure, memoryLimits.eventQueue),
		finalAck: make(chan struct{}, 1), sendDone: make(chan struct{}),
		done: make(chan struct{}), localClosedCh: make(chan struct{}), remoteAbortCh: make(chan struct{}),
		ackWake: make(chan struct{}, 1), ackErr: make(chan error, 1),
		stallSignal: make(chan struct{}, 1),
		classifier:  classifier.New(classifierCfg), started: time.Now(), completionGrace: flowCompletionGrace,
	}
	f.idleTimeout = defaultFlowIdleTimeout
	f.maxLifetime = defaultFlowMaxLifetime
	f.lastActivity.Store(f.started.UnixNano())
	f.telemetryID = nextTelemetryID.Add(1)
	f.class.Store(uint32(protocol.ClassNew))
	f.ackTrack = newAckTracker()
	return f
}

// requireOpenConfirmation is called before the first lane starts. Only the
// optimistic client path needs it; server flows and clients that explicitly
// waited for OPEN_OK use the zero-value, already-confirmed state.
func (f *multipathFlow) requireOpenConfirmation() {
	f.openConfirmationRequired.Store(true)
}

func (f *multipathFlow) confirmOpen() {
	f.openConfirmationRequired.Store(false)
}

func (f *multipathFlow) addLane(lane *mpLane) error {
	if lane == nil || lane.fc == nil {
		return errors.New("invalid lane")
	}
	select {
	case <-f.done:
		return errLaneFlowClosed
	default:
	}
	f.lanesMu.Lock()
	if _, exists := f.lanes[lane.id]; exists {
		f.lanesMu.Unlock()
		return errLaneDuplicateID
	}
	limits := f.memoryLimits
	if limits.laneWriteQueue < 2 || limits.laneControlReserve >= limits.laneWriteQueue {
		limits = defaultFlowMemoryLimits()
	}
	bulkQueue := limits.laneWriteQueue - limits.laneControlReserve
	if lane.writeQ == nil {
		lane.writeQ = make(chan laneFrame, bulkQueue)
	}
	if lane.writeInteractiveQ == nil {
		lane.writeInteractiveQ = make(chan laneFrame, limits.laneWriteQueue)
	}
	if lane.writeSlots == nil {
		lane.writeSlots = make(chan struct{}, limits.laneWriteQueue)
	}
	if lane.writeDone == nil {
		lane.writeDone = make(chan struct{})
	}
	lane.admitted = time.Now()
	f.lanes[lane.id] = lane
	f.lanesJoined.Add(1)
	if lane.id >= f.nextJoinID {
		f.nextJoinID = lane.id + 1
	}
	f.lanesMu.Unlock()
	if lane.staged {
		return nil
	}
	f.startLane(lane)
	return nil
}

// activateLane publishes a staged JOIN lane only after its OPEN_OK was
// successfully written. QUIC buffers peer data during this tiny interval, so
// no application frame needs to race the acknowledgement.
func (f *multipathFlow) activateLane(lane *mpLane) error {
	if lane == nil || !lane.staged {
		return errors.New("lane is not staged")
	}
	f.lanesMu.RLock()
	current := f.lanes[lane.id]
	closed := lane.closed.Load()
	f.lanesMu.RUnlock()
	if current != lane || closed || f.doneChanClosed() {
		return errors.New("staged lane is no longer available")
	}
	if !lane.ready.CompareAndSwap(false, true) {
		return nil
	}
	f.startLane(lane)
	return nil
}

func (f *multipathFlow) startLane(lane *mpLane) {
	// This is the one point a lane actually begins carrying traffic, reached
	// from addLane for an immediate lane and from activateLane for a staged
	// one, so it is where an outage ends. Ending it here rather than where a
	// waiter happens to observe the lane matters: nothing obliges a waiter to
	// look again once it has what it wanted, and a deadline left behind by a
	// recovered outage would expire the next one before it began.
	f.endReplacementOutage()
	// The policy is set before either goroutine exists. Setting it from the
	// reader, as the first version did, meant the writer could already be
	// asking for it.
	lane.fc.setCodingPolicy(f.prefersCodingOverRetransmission)
	if f.openConfirmationRequired.Load() {
		lane.fc.setOpenSafetyPolicy(func() bool { return f.openConfirmationRequired.Load() })
	}
	go f.readLane(lane)
	go f.writeLane(lane)
	// A lane admitted while the flow is sending starts carrying data at once;
	// it does not wait for anything to notice it.
	if sched := f.scheduler.Load(); sched != nil {
		if ctx := f.sendCtx.Load(); ctx != nil {
			f.startLanePuller(*ctx, lane, sched)
		}
	}
}

// writeLane serializes data and close frames for one lane while allowing
// other lanes to make progress independently. Interactive/new frames are
// always selected before queued bulk frames. A bulk frame already in the
// underlying write may finish, but a later interactive frame does not wait
// behind the rest of the bulk queue. ACK/PING/PONG writes may still call
// frameConn.Write directly; its mutex preserves frame integrity.
func (f *multipathFlow) writeLane(lane *mpLane) {
	defer close(lane.writeDone)
	for {
		queued, ok := nextLaneFrame(lane, f.done, f.ctx.Done())
		if !ok {
			return
		}
		frame := queued.frame
		if lane.writeSlots != nil {
			// A slot is released when the writer takes ownership of a frame.
			// The non-blocking receive is safe because every initialized queue
			// insertion acquires exactly one slot first.
			select {
			case <-lane.writeSlots:
			default:
			}
		}
		if lane.writeHook != nil {
			if err := lane.writeHook(frame); err != nil {
				f.failLane(lane, fmt.Errorf("lane %d injected write failure: %w", lane.id, err))
				return
			}
		}
		err := lane.fc.WriteContext(f.ctx, frame)
		if err != nil {
			f.failLane(lane, fmt.Errorf("lane %d write: %w", lane.id, err))
			return
		}
		if frame.Header.Type == protocol.TypeData {
			lane.sent.Add(uint64(len(frame.Payload)))
		}
		// The transport has taken these bytes, which is what frees the lane to
		// accept more. A QUIC stream write returns only once the packer has
		// consumed the data, so this is the transport's own congestion clock.
		if queued.onWritten != nil {
			queued.onWritten()
		}
	}
}

// nextLaneFrame gives the interactive queue strict preference without
// starving shutdown: check it once before allowing the bulk queue to win a
// select, then check both queues while waiting. The non-blocking first check
// closes the common race where both queues already have work.
func nextLaneFrame(lane *mpLane, done <-chan struct{}, ctxDone <-chan struct{}) (laneFrame, bool) {
	if lane.writeInteractiveQ != nil {
		select {
		case frame := <-lane.writeInteractiveQ:
			return frame, true
		default:
		}
	}
	for {
		select {
		case <-done:
			return laneFrame{}, false
		case <-ctxDone:
			return laneFrame{}, false
		default:
		}
		if lane.writeInteractiveQ != nil {
			select {
			case frame := <-lane.writeInteractiveQ:
				return frame, true
			default:
			}
		}
		select {
		case frame := <-lane.writeInteractiveQ:
			return frame, true
		case frame := <-lane.writeQ:
			return frame, true
		case <-done:
			return laneFrame{}, false
		case <-ctxDone:
			return laneFrame{}, false
		}
	}
}

type flowSnapshot struct {
	Class        classifier.Class
	CurrentLanes int
	HealthyLanes int
	Bytes        uint64
	BytesUp      uint64
	BytesDown    uint64
	Elapsed      time.Duration
	BaselineRTT  time.Duration
	CurrentRTT   time.Duration
}

func (f *multipathFlow) snapshot() flowSnapshot {
	lanes := f.healthyLanes()
	f.observeTransport(lanes)
	bytesUp, bytesDown := f.bytesUp.Load(), f.bytesDown.Load()
	return flowSnapshot{
		Class: classifier.Class(f.classifier.Class()), CurrentLanes: f.laneCount(), HealthyLanes: len(lanes),
		Bytes: bytesUp + bytesDown, BytesUp: bytesUp, BytesDown: bytesDown, Elapsed: time.Since(f.started),
		BaselineRTT: time.Duration(f.baselineRTTNS.Load()), CurrentRTT: time.Duration(f.currentRTTNS.Load()),
	}
}

func (f *multipathFlow) localAbortGrace() time.Duration {
	if f.abortGrace > 0 {
		return f.abortGrace
	}
	if classifier.Class(f.class.Load()) == classifier.ClassInteractive {
		return interactiveAbortGrace
	}
	return flowAbortGrace
}

func (f *multipathFlow) localAbortDrainGrace() time.Duration {
	if f.abortDrainGrace > 0 {
		return f.abortDrainGrace
	}
	return finalAckWriteGrace
}

// noteLocalClose publishes the source sequence before announcing EOF. The
// receive side may have to send a full-close marker before the scheduler has
// delivered every source chunk, so sendFinal is too late to be the first place
// that records this sequence.
func (f *multipathFlow) noteLocalClose(sequence uint64) {
	f.sendSequence(sequence)
	f.localClosed.Store(true)
	if f.localClosedCh != nil {
		f.localClosedOnce.Do(func() { close(f.localClosedCh) })
	}
}

// noteRemoteAbort makes an explicit full close an out-of-band cancellation
// source for the sender. Waiting for its outstanding chunks to be acknowledged
// cannot work: the peer has just said that its application will not read them.
func (f *multipathFlow) noteRemoteAbort() {
	f.remoteAbort.Store(true)
	if f.remoteAbortCh != nil {
		f.remoteAbortOnce.Do(func() { close(f.remoteAbortCh) })
	}
}

func (f *multipathFlow) observeTransport(lanes []*mpLane) {
	var observation metrics.QUICObservation
	// moved is how far the connections under this flow travelled since anyone
	// last read them. It is not a per-flow quantity: the connections are
	// pooled, so it is measured against a baseline the connection itself
	// holds, and a connection two flows share contributes to whichever of
	// them reads it first rather than to both.
	var moved metrics.QUICConnectionCounters
	// folded names the connections whose connection-scoped values have already
	// been added to this observation. Several lanes of one flow routinely sit
	// on one pooled connection, and a congestion window or pacing rate added
	// once per lane describes a transport that does not exist.
	var folded map[uint64]struct{}
	for _, lane := range lanes {
		provider, ok := lane.fc.transport().(laneStatsProvider)
		if !ok {
			continue
		}
		stats := provider.transportStats()
		observation.Lanes++
		if stats.latestRTT > observation.LatestRTT {
			observation.LatestRTT = stats.latestRTT
		}
		if stats.smoothedRTT > observation.SmoothedRTT {
			observation.SmoothedRTT = stats.smoothedRTT
		}
		if counted, ok := provider.(laneConnectionProvider); ok {
			id, delta := counted.connectionTelemetry(stats)
			moved.Add(delta)
			if _, seen := folded[id]; seen {
				continue
			}
			if folded == nil {
				folded = make(map[uint64]struct{}, len(lanes))
			}
			folded[id] = struct{}{}
		}
		controller := stats.controller
		if controller.Kind != "" {
			if observation.ControllerKind == "" {
				observation.ControllerKind = controller.Kind
			} else if observation.ControllerKind != controller.Kind {
				observation.ControllerKind = "mixed"
			}
			if controller.Mode > observation.ControllerMode {
				observation.ControllerMode = controller.Mode
			}
			observation.ControllerMaxBandwidth += controller.MaxBandwidth
			if controller.LatestSample > observation.ControllerLatestSample {
				observation.ControllerLatestSample = controller.LatestSample
			}
			if controller.LatestAckRate > observation.ControllerLatestAckRate {
				observation.ControllerLatestAckRate = controller.LatestAckRate
			}
			if controller.LatestSendRate > observation.ControllerLatestSendRate {
				observation.ControllerLatestSendRate = controller.LatestSendRate
			}
			if controller.Round > observation.ControllerRound {
				observation.ControllerRound = controller.Round
			}
			observation.ControllerPacingRate += controller.PacingRate
			observation.ControllerCongestionWindow += controller.CongestionWindow
			observation.ControllerBytesInFlight += controller.BytesInFlight
			if controller.MinRTT > observation.ControllerMinRTT {
				observation.ControllerMinRTT = controller.MinRTT
			}
			if controller.Erasure > observation.ControllerErasure {
				observation.ControllerErasure = controller.Erasure
			}
			if controller.SampleMax > observation.ControllerSampleMax {
				observation.ControllerSampleMax = controller.SampleMax
				observation.ControllerSampleDelivered = controller.SampleMaxDelivered
				observation.ControllerSampleInterval = controller.SampleMaxInterval
			}
			if controller.SampleMean > observation.ControllerSampleMean {
				observation.ControllerSampleMean = controller.SampleMean
			}
			if controller.DelayBrake > observation.ControllerDelayBrake {
				observation.ControllerDelayBrake = controller.DelayBrake
			}
			observation.ControllerInRecovery = observation.ControllerInRecovery || controller.InRecovery
		}
	}
	if observation.SmoothedRTT > 0 {
		f.currentRTTNS.Store(observation.SmoothedRTT.Nanoseconds())
		f.baselineRTTNS.CompareAndSwap(0, observation.SmoothedRTT.Nanoseconds())
	}
	// The stall watchdog sizes its patience from the smallest minimum-RTT any
	// lane reports: the best case the path has shown, not the worst lane's
	// current estimate the telemetry aggregate above publishes.
	var minRTT time.Duration
	for _, lane := range lanes {
		provider, ok := lane.fc.transport().(laneStatsProvider)
		if !ok {
			continue
		}
		if rtt := provider.transportStats().controller.MinRTT; rtt > 0 && (minRTT == 0 || rtt < minRTT) {
			minRTT = rtt
		}
	}
	if minRTT > 0 {
		f.minRTTNS.Store(minRTT.Nanoseconds())
	}
	// The connection totals are banked whether or not this flow may still
	// publish its own gauges. They are monotonic and belong to the connection,
	// so a late reading can neither pin nor inflate them, and discarding it
	// would drop bytes the connection really did carry. A nil registry counts
	// nothing at all, and the call is a no-op against one.
	f.metrics.AddQUICConnectionCounters(moved)
	// A finished flow must not publish again. Its registry entry is removed
	// during teardown, and the lane managers keep polling this snapshot for a
	// moment after that; a late publication would reinstate an entry with
	// nothing left to remove it. The process-wide aggregate reports RTT as a
	// maximum, so one reinstated entry pins the exported estimate at that
	// flow's last measurement until the process restarts.
	if f.metrics != nil && !f.finished.Load() {
		f.metrics.ObserveQUIC(f.telemetryID, observation)
	}
}

// noteLaneCapacityRefusal records a rescue round the peer answered with its
// lane-admission ceiling; resetLaneCapacityRefusals clears the streak on any
// other round outcome, since only consecutive answers mark the desync.
func (f *multipathFlow) noteLaneCapacityRefusal() { f.capacityRefusals.Add(1) }

func (f *multipathFlow) resetLaneCapacityRefusals() { f.capacityRefusals.Store(0) }

func (f *multipathFlow) laneCapacityRefusals() int64 { return f.capacityRefusals.Load() }

func (f *multipathFlow) laneCount() int {
	f.lanesMu.RLock()
	defer f.lanesMu.RUnlock()
	count := 0
	for _, lane := range f.lanes {
		if !lane.closed.Load() {
			count++
		}
	}
	return count
}

// retireOldestLane makes room for a replacement when the peer has observed a
// dead lane but the server-side socket is still half-open. It is only used at
// the configured lane cap; deleting the entry keeps the cap a real resource
// bound rather than allowing unbounded historical lane IDs.
//
// The victim is the oldest evictable lane with the replacement's role, or the
// oldest evictable lane of any role when no same-role lane exists: role
// orders the choice but never blocks a rescue. One lane is never evictable --
// a lane younger than minAge, whatever its state. Parallel rescue JOINs race
// to this endpoint, and admission order is not the order the peer crowned its
// winner in, so a freshly admitted lane may still be waiting on the peer's
// decision while the racing losers it beat are still arriving; the half-open
// sockets eviction exists for are never that young. The age window is also
// what protects a staged lane whose JOIN handshake is still in flight:
// admission writes its OPEN_OK under a deadline of the same budget, so a
// staged lane that never activated and is older than minAge is not a
// handshake in flight but a wedged admission, and retiring it is how the slot
// is freed. With no evictable lane the JOIN is refused -- the transient
// capacity answer the racing peer already expects for its losing attempts.
func (f *multipathFlow) retireOldestLane(control bool, minAge time.Duration) bool {
	f.lanesMu.Lock()
	var victim *mpLane
	for _, lane := range f.lanes {
		if lane.closed.Load() {
			continue
		}
		if minAge > 0 && time.Since(lane.admitted) < minAge {
			continue
		}
		switch {
		case victim == nil:
			victim = lane
		case f.laneIsControl(lane) == control && f.laneIsControl(victim) != control:
			// A lane with the replacement's role always beats any other role.
			victim = lane
		case f.laneIsControl(lane) == f.laneIsControl(victim) && lane.id < victim.id:
			victim = lane
		}
	}
	if victim == nil {
		f.lanesMu.Unlock()
		return false
	}
	delete(f.lanes, victim.id)
	victim.closed.Store(true)
	f.lanesMu.Unlock()
	if victim.fc != nil {
		_ = victim.fc.Close()
	}
	return true
}

// removeLane withdraws a lane whose admission failed after it entered the
// flow -- a staged JOIN lane whose OPEN_OK never left. Anything less leaves
// a lane that counts against the admission cap but can neither carry traffic
// nor be scheduled, leaking the slot for the life of the flow.
func (f *multipathFlow) removeLane(lane *mpLane) {
	f.lanesMu.Lock()
	if f.lanes[lane.id] != lane {
		f.lanesMu.Unlock()
		return
	}
	delete(f.lanes, lane.id)
	lane.closed.Store(true)
	f.lanesMu.Unlock()
	if lane.fc != nil {
		_ = lane.fc.Close()
	}
}

// retireLanesExcept performs an intentional transport handoff without
// reporting a path failure. Scheduler retirement is still immediate: chunks
// assigned to a retired lane must be made available to the replacement TCP
// bundle before the old socket's reader notices the close.
func (f *multipathFlow) retireLanesExcept(kind TransportKind) int {
	f.lanesMu.Lock()
	retired := make([]*mpLane, 0)
	for id, lane := range f.lanes {
		if lane.closed.Load() || lane.kind == kind {
			continue
		}
		delete(f.lanes, id)
		if lane.closed.CompareAndSwap(false, true) {
			retired = append(retired, lane)
		}
	}
	f.lanesMu.Unlock()
	for _, lane := range retired {
		if sched := f.scheduler.Load(); sched != nil {
			sched.RetireLane(lane.id)
		}
		if lane.fc != nil {
			_ = lane.fc.Close()
		}
	}
	return len(retired)
}

// retireLeastProductiveLane removes one non-control lane.  It is used only
// after the scheduler has measured a negative marginal contribution or an
// RTT-budget violation.  The first lane is retained as the control/rescue
// lane so a reduction never strands the logical flow without a preferred
// path.
func (f *multipathFlow) retireLeastProductiveLane() bool {
	f.lanesMu.Lock()
	var victim *mpLane
	for _, lane := range f.lanes {
		if lane.closed.Load() || !f.laneReady(lane) || lane.id == 0 || f.laneIsControl(lane) {
			continue
		}
		if victim == nil || lane.sent.Load()+lane.recv.Load() < victim.sent.Load()+victim.recv.Load() ||
			(lane.sent.Load()+lane.recv.Load() == victim.sent.Load()+victim.recv.Load() && lane.id > victim.id) {
			victim = lane
		}
	}
	if victim == nil {
		f.lanesMu.Unlock()
		return false
	}
	delete(f.lanes, victim.id)
	victim.closed.Store(true)
	f.lanesMu.Unlock()
	if victim.fc != nil {
		_ = victim.fc.Close()
	}
	return true
}

func (f *multipathFlow) allocateJoinID() (uint64, error) {
	f.lanesMu.Lock()
	defer f.lanesMu.Unlock()
	for id := f.nextJoinID; id < 1<<20; id++ {
		if _, exists := f.lanes[id]; !exists {
			f.nextJoinID = id + 1
			return id, nil
		}
	}
	return 0, errors.New("unable to allocate lane id")
}

// readLane reads a lane's two substrates into one handler.
//
// They are two loops rather than one because they have different semantics,
// not merely different sources: the control stream is read synchronously so
// that a caller's read deadline still means something, while the coded
// substrate has no deadlines and no ordering. Merging them into a single call
// gave the stream the datagram path's semantics, and a handshake timeout then
// killed the reader for good.
func (f *multipathFlow) readLane(lane *mpLane) {
	go f.readLaneBulk(lane)
	sawRemoteTerminal := false
	for {
		frame, err := lane.fc.Read()
		if err != nil {
			// A protocol CLOSE ends the peer's sending direction, and RESET ends
			// the whole logical flow. The stream EOF that follows either terminal
			// frame is protocol teardown, not evidence that the path failed. For a
			// CLOSE, this lane's write direction remains available for the final
			// ACK and response bytes.
			if !sawRemoteTerminal {
				f.failLane(lane, fmt.Errorf("lane %d: %w", lane.id, err))
			}
			return
		}
		if !f.deliverInbound(lane, frame) {
			return
		}
		if frame.Header.Type == protocol.TypeClose || frame.Header.Type == protocol.TypeReset {
			sawRemoteTerminal = true
		}
	}
}

// readLaneBulk drains this flow's share of the connection's coded datagrams.
// Its end is not the lane's failure: the control stream still works, and what
// the coded path dropped is re-issued by the scheduler like any other
// unacknowledged chunk.
func (f *multipathFlow) readLaneBulk(lane *mpLane) {
	frames := lane.fc.bulkFrames(f.flowID)
	if frames == nil {
		return
	}
	defer lane.fc.releaseBulk(f.flowID)
	for {
		select {
		case frame, ok := <-frames:
			if !ok {
				return
			}
			if !f.deliverInbound(lane, frame) {
				return
			}
		case <-f.done:
			// The flow's own closure, not the context it was started with:
			// that context belongs to the whole client and outlives every flow
			// on it, so waiting on it is waiting forever.
			return
		}
	}
}

func (f *multipathFlow) deliverInbound(lane *mpLane, frame protocol.Frame) bool {
	if frame.Header.Type == protocol.TypeData {
		lane.recv.Add(uint64(len(frame.Payload)))
	}
	select {
	case f.events <- inboundEvent{lane: lane, frame: frame}:
		return true
	case <-f.done:
		// Flow teardown is independent of the client lifetime. In particular,
		// a reader can be waiting behind a full event queue when another lane
		// completes or aborts the flow; waiting only on f.ctx would strand that
		// goroutine until the entire VPN stopped.
		return false
	case <-f.ctx.Done():
		return false
	}
}

// prefersCodingOverRetransmission reports whether this flow would rather spend
// bytes than round trips.
//
// A bulk transfer would not: it is measured by how many bytes arrive per
// second, and a code that provisions for the binomial spends more of them than
// retransmitting what was actually lost. Everything else would: an exchange
// too short to trigger a fast retransmit recovers by timeout, and a timeout is
// a round trip that coding does not spend.
func (f *multipathFlow) prefersCodingOverRetransmission() bool {
	// How much this flow has moved is the immediate answer; the class is the
	// considered one. Both are needed because they become available at
	// different times, and each is wrong about a case the other gets right.
	f.refreshClass()
	switch classifier.Class(f.class.Load()) {
	case classifier.ClassBulk:
		// Measured by bytes per second, and a code that provisions for the
		// binomial spends more of them than retransmitting what was lost.
		return false
	case classifier.ClassInteractive:
		// A sequence of small exchanges, however many of them it has done.
		//
		// The byte cutoff below cannot see this and gets it exactly backwards.
		// Eighty bytes fifty times a second is four kilobytes a second, so a
		// voice call crosses the cutoff after about a minute and carries the
		// rest of itself uncoded -- losing its repair precisely where the
		// repair matters, because a stream of small messages separated by idle
		// never amortises a round trip over anything. Every lost frame pays a
		// full round trip by itself. Measured on an emulated 14% path, an
		// uncoded frame stream loses 71 of 400 frames outright where a
		// duplicated one loses 10, and the delivered frames are no slower.
		return true
	}
	// Still unclassified. The class takes a second to settle, and a transfer
	// from a fast local destination produces most of its frames inside that
	// second -- measured live, 265 of a download's 557 data frames were coded
	// before the class caught up. A flow that has already moved more than a
	// small exchange's worth is not a small exchange, whatever it is later
	// decided to be.
	return f.bytesUp.Load()+f.bytesDown.Load() <= codedFlowBytes
}

// codedFlowBytes is how much a flow may carry and still be treated as an
// exchange worth coding. Past it, the round trips coding saves are amortised
// over so many bytes that the parity costs more than the waiting.
const codedFlowBytes = 256 * 1024

// classRefreshInterval bounds how often a flow re-examines what it is. The
// classifier's own thresholds move on the scale of seconds, so this is far
// finer than the answer can change.
const classRefreshInterval = 250 * time.Millisecond

// refreshClass re-examines the flow from what it has carried so far.
//
// The classifier is otherwise driven only by reads from the inner connection,
// and that is not when a flow becomes what it is. A server reading a ten
// megabyte file from a local destination does every one of those reads inside
// a second -- before the bulk test's minimum age has elapsed -- and then never
// reads again. Nothing re-examined it, so the flow stayed ClassNew for its
// whole life and was coded from first byte to last: measured live, 605 data
// frames coded and 4 on the stream, on a transfer that was bulk by any
// description after its first second.
func (f *multipathFlow) refreshClass() {
	now := time.Now()
	last := f.lastClassified.Load()
	if now.Sub(time.Unix(0, last)) < classRefreshInterval {
		return
	}
	if !f.lastClassified.CompareAndSwap(last, now.UnixNano()) {
		return
	}
	// Zero bytes: this is a re-examination of what has already been carried,
	// not a new observation of anything.
	f.observe(0, false)
}

// laneRetransmits reports whether a lane recovers its own losses, which is
// true exactly when its data is going over the stream rather than the coded
// datagram path. A lane whose bulk path is coding can lose a chunk outright.
func (f *multipathFlow) laneRetransmits(laneID uint64) bool {
	f.lanesMu.RLock()
	lane := f.lanes[laneID]
	f.lanesMu.RUnlock()
	if lane == nil || lane.fc == nil {
		return true
	}
	return !lane.fc.codesData()
}

// failLane transitions a lane to failed exactly once, stops both of its I/O
// goroutines, and notifies the flow-level recovery coordinator. A failed lane
// is never selected again, even if a buffered write completes later.
func (f *multipathFlow) failLane(lane *mpLane, err error) {
	if lane != nil && lane.fc != nil && !lane.closed.Load() {
		if observer, ok := lane.fc.transport().(interface{ transportFailed(error) }); ok {
			observer.transportFailed(err)
		}
	}
	if !f.closeFailedLane(lane) {
		return
	}
	f.reportLaneFailure(lane, err)
}

// closeFailedLane atomically removes a broken lane from transport and
// scheduling before any replacement decision observes it.
func (f *multipathFlow) closeFailedLane(lane *mpLane) bool {
	if lane == nil || !lane.closed.CompareAndSwap(false, true) {
		return false
	}
	if lane.fc != nil {
		_ = lane.fc.Close()
	}
	if sched := f.scheduler.Load(); sched != nil {
		sched.RetireLane(lane.id)
	}
	return true
}

// reportLaneFailure exports and coordinates a lane already transitioned by
// closeFailedLane.
func (f *multipathFlow) reportLaneFailure(lane *mpLane, err error) {
	if f.finished.Load() {
		return
	}
	// Once both FIN directions are observed, a peer closing an outer lane is
	// the normal final-ACK/stream-close race, not a transport degradation.
	// The tombstone path retains the final sequence for any late replacement;
	// do not pollute lane-health metrics with this expected close.
	if f.finSent.Load() && f.remoteFinSeen.Load() {
		return
	}
	select {
	case <-f.done:
		return
	default:
	}
	if f.metrics != nil {
		f.metrics.LaneFailure()
	}
	f.laneFailures.Add(1)
	if f.logger != nil {
		coded, stream := f.dataSubstrates()
		f.logger.Debug("multipath lane failed", "flow_id", f.flowID, "lane_id", lane.id,
			"transport", lane.kind, "error", err,
			"data_coded", coded, "data_stream", stream,
			"class", classifier.Class(f.class.Load()),
			"bytes_up", f.bytesUp.Load(), "bytes_down", f.bytesDown.Load(),
			"classifier_says", f.classifier.Class(), "age", time.Since(f.started))
	}
	select {
	case f.laneErr <- laneFailure{lane: lane, err: err}:
	default:
		// The lane is already marked failed. The coordinator also observes
		// current health directly, so coalescing notifications is safe.
	}
}

func (f *multipathFlow) laneFailureCount() uint64 { return f.laneFailures.Load() }

func (f *multipathFlow) healthyLanes() []*mpLane {
	f.lanesMu.RLock()
	defer f.lanesMu.RUnlock()
	lanes := make([]*mpLane, 0, len(f.lanes))
	for _, lane := range f.lanes {
		if !lane.closed.Load() && f.laneReady(lane) {
			lanes = append(lanes, lane)
		}
	}
	sort.Slice(lanes, func(i, j int) bool { return lanes[i].id < lanes[j].id })
	return lanes
}

func (f *multipathFlow) laneReady(lane *mpLane) bool {
	return lane != nil && (!lane.staged || lane.ready.Load())
}

// laneCandidates returns the lanes eligible to carry a frame, in preference
// order. QUIC has at most one for data; a negotiated TCP-only fallback may
// return its bounded bundle. The ordering matters only for control.
//
// This is the flow's control and data plane split, and it is a second one --
// the framing has already split control from bulk *within* a connection, by
// putting control frames on the QUIC stream and coded bulk on that
// connection's datagrams. The two are not alternatives and neither subsumes
// the other, because they cover different flows:
//
//   - A flow that would rather spend bytes than round trips gets the substrate
//     split. Its data is coded onto datagrams, its control stays on the
//     stream, and one connection carries both.
//   - A bulk flow would rather spend round trips than bytes, so its data is
//     not coded and rides a stream. If that were the same stream its control
//     rides, the flow's own acknowledgements would sit strictly behind its own
//     bulk, and a lost data frame would head-of-line block the acknowledgement
//     that releases the peer's sender. So a bulk flow's data moves to a
//     connection of its own and its control stays on the pooled one.
//
// Both are the same rule stated at different layers: what releases the data
// must not be queued behind the data. The coded case measured that at a factor
// of a hundred -- 0.87 Mbit/s one way against 0.008 when acknowledgements had
// to come back over the same coded substrate.
//
// The candidates are not ranked by speed, and that is deliberate. Ranking was
// the previous scheduler's core idea: estimate each lane's rate, predict which
// would deliver soonest, and commit the frame there. Every prediction it got
// wrong put numbered bytes behind a lane that had slowed, and the receiver
// could not deliver past them.
func (f *multipathFlow) laneCandidates(bulk bool) ([]*mpLane, error) {
	lanes := f.healthyLanes()
	if len(lanes) == 0 {
		return nil, errors.New("no healthy lanes")
	}
	lanes = preferUnsuspectedLanes(lanes)
	if !bulk {
		// Prefer the explicit control role. It begins on lane zero, but a
		// connection-generation reset replaces it with a non-zero JOIN lane.
		// Falling back to the oldest healthy lane keeps old/non-reserved flows
		// and the interval before a replacement is admitted available.
		for _, lane := range lanes {
			if f.laneIsControl(lane) {
				return []*mpLane{lane}, nil
			}
		}
		return lanes[:1], nil
	}
	return f.dataLane(lanes), nil
}

// preferUnsuspectedLanes implements the watchdog's demote-don't-kill rule:
// while any healthy lane is not stall-suspected, new writes avoid the
// suspected ones. When every healthy lane is suspected the set is returned
// unchanged -- a suspected lane that is the only lane still carries the flow,
// because the suspicion is a reason to look for something better, never a
// reason to stop using what there is.
func preferUnsuspectedLanes(lanes []*mpLane) []*mpLane {
	clear := 0
	for _, lane := range lanes {
		if !lane.suspected.Load() {
			clear++
		}
	}
	if clear == 0 || clear == len(lanes) {
		return lanes
	}
	preferred := make([]*mpLane, 0, clear)
	for _, lane := range lanes {
		if !lane.suspected.Load() {
			preferred = append(preferred, lane)
		}
	}
	return preferred
}

// dataLane selects the lanes a flow's data rides.
//
// QUIC remains one data lane. A negotiated TCP-only flow is the one exception:
// each lane has its own kernel congestion controller, so the existing byte
// scheduler stripes across them and re-injects work when one is retired.
func (f *multipathFlow) dataLane(lanes []*mpLane) []*mpLane {
	if f.tcpStriping.Load() && len(lanes) > 1 {
		for _, lane := range lanes {
			if lane.kind != TransportTCP {
				return lanes[:1]
			}
		}
		return lanes
	}
	if len(lanes) == 1 || !f.reserveControlLane {
		return lanes[:1]
	}
	// The lane carrying the control role is the control plane. Prefer the
	// isolated lane for data, but
	// only once one is actually healthy: during a join failure or a lane
	// recovery, falling back to lane zero is what keeps the flow alive, and an
	// available flow beats an isolated one.
	var control *mpLane
	for _, lane := range lanes {
		if f.laneIsControl(lane) {
			control = lane
			continue
		}
		if f.isolateFromControlLane(control) {
			return []*mpLane{lane}
		}
		break
	}
	return lanes[:1]
}

func (f *multipathFlow) laneIsControl(lane *mpLane) bool {
	if lane == nil || !f.reserveControlLane {
		return false
	}
	// The lane-zero fallback preserves the role for flows constructed by older
	// peers and for focused tests which predate the explicit role field.
	return lane.control || lane.id == 0
}

// isolateFromControlLane reports whether a bulk flow should stop putting
// payload on the pooled control lane now that it has one of its own.
//
// Isolation exists to keep a bulk congestion window out of the connection that
// short and interactive flows share, and it is not free: the flow gives up a
// warmed-up path for one with a fresh congestion window. Measured on a path
// policing each source at 25 Mbit/s, a lane arrived five seconds into a 20 MiB
// transfer and the flow abandoned a lane running at the full policed rate for a
// cold one; the last quarter of the transfer then took nearly half its total
// time, 19.1 Mbit/s against 23.0 without the handover.
//
// So it is paid only when there is something to protect. While no other flow is
// using the pooled connection, a bulk flow's window is inconveniencing nobody
// and the control lane carries payload like any other. The moment another flow
// arrives, the next chunk goes elsewhere -- the test is per selection, not once
// per flow, so yielding takes one chunk rather than a policy epoch.
func (f *multipathFlow) isolateFromControlLane(control *mpLane) bool {
	if control == nil || f.controlLaneShared == nil {
		// Nothing to weigh, or no way to tell. Protect the control lane, which
		// is what a flow that has not been told otherwise should do.
		return true
	}
	return f.controlLaneShared()
}

func (f *multipathFlow) run(ctx context.Context) (FlowStats, error) {
	runCtx, cancelRun := context.WithCancel(ctx)
	defer cancelRun()
	ackCtx, cancelACKs := context.WithCancel(runCtx)
	go f.ackLoop(ackCtx)
	telemetryStop := make(chan struct{})
	go f.telemetryLoop(telemetryStop)
	completionStop := make(chan struct{})
	go f.completionWatchdog(completionStop)
	stallStop := make(chan struct{})
	if !f.stallWatchdogDisabled {
		go f.stallWatchdog(stallStop)
	}
	limitsStop := make(chan struct{})
	limitErr := make(chan error, 1)
	go f.watchLimits(limitsStop, limitErr)
	if f.metrics != nil {
		// Registered before signalDone so that it runs after it: the lane
		// managers stop on the done channel and poll this flow's telemetry
		// until they do, so removing the entry first leaves a window in which
		// one of them republishes it permanently.
		defer f.metrics.RemoveQUIC(f.telemetryID)
	}
	defer f.signalDone()
	defer func() {
		cancelACKs()
		close(limitsStop)
		close(completionStop)
		close(stallStop)
		close(telemetryStop)
	}()
	defer f.finished.Store(true)
	stats := FlowStats{Started: f.started}
	results := make(chan error, 2)
	go func() { results <- f.sendInnerStriped(runCtx) }()
	go func() { results <- f.receiveInner(runCtx) }()
	completed := 0
	for completed < 2 {
		select {
		case err := <-results:
			completed++
			if errors.Is(err, errLocalApplicationClose) || f.remoteAbort.Load() ||
				(f.localAbortSent.Load() && f.doneChanClosed()) {
				// A local full-close marker has had a bounded opportunity to
				// reach the peer, or an authenticated remote marker has already
				// canceled this flow. It is safe to stop the sibling sender even
				// when its scheduler still holds chunks the vanished application
				// can never acknowledge. In particular, closing a Windows
				// destination wakes its read worker with a socket error; that
				// cleanup race is not a transport failure.
				cancelRun()
				f.closeAll()
				stats.Ended = time.Now()
				stats.BytesSent = f.bytesUp.Load()
				stats.BytesRead = f.bytesDown.Load()
				stats.LaneBytes = f.laneStats()
				return stats, nil
			}
			if err != nil {
				// A destination can reset immediately after the client has
				// sent its FIN. Give the receive worker a short bounded window
				// to consume that in-flight FIN and emit the final ACK before
				// closing the lanes; otherwise a correct close is misclassified
				// as a failed flow and the client loses its completion signal.
				if expectedDestinationCloseError(err) {
					remoteFIN := f.remoteFinSeen.Load() || f.waitForRemoteFIN(ctx, remoteFinDrainGrace)
					if remoteFIN {
						// Keep the lane alive briefly after the final ACK write so
						// a 200 ms-class cross-Pacific RTT can deliver it before
						// the destination-reset cleanup closes the physical stream.
						drain := time.NewTimer(remoteFinDrainGrace)
						select {
						case <-drain.C:
						case <-ctx.Done():
							if !drain.Stop() {
								<-drain.C
							}
						}
						f.closeAll()
						stats.Ended = time.Now()
						stats.BytesSent = f.bytesUp.Load()
						stats.BytesRead = f.bytesDown.Load()
						stats.LaneBytes = f.laneStats()
						return stats, nil
					}
				}
				if err != nil {
					// Once the bounded remote-FIN drain above is exhausted, stop the
					// sibling worker before tearing down the physical lanes. Otherwise
					// a blocked application read can outlive the logical flow.
					cancelRun()
					f.closeAll()
					stats.Ended = time.Now()
					stats.BytesSent = f.bytesUp.Load()
					stats.BytesRead = f.bytesDown.Load()
					stats.LaneBytes = f.laneStats()
					return stats, err
				}
			}
		case err := <-limitErr:
			if err == nil {
				continue
			}
			if f.metrics != nil {
				f.metrics.FlowTimeout()
			}
			cancelRun()
			f.closeAll()
			stats.Ended = time.Now()
			stats.BytesSent = f.bytesUp.Load()
			stats.BytesRead = f.bytesDown.Load()
			stats.LaneBytes = f.laneStats()
			return stats, err
		case err := <-f.ackErr:
			if err == nil {
				continue
			}
			cancelRun()
			f.closeAll()
			stats.Ended = time.Now()
			stats.BytesSent = f.bytesUp.Load()
			stats.BytesRead = f.bytesDown.Load()
			stats.LaneBytes = f.laneStats()
			return stats, fmt.Errorf("cumulative acknowledgement: %w", err)
		case failure := <-f.laneErr:
			err := failure.err
			// Both FIN directions have already been observed. The application
			// bytes are complete, and a tombstone can replay a lost final ACK;
			// waiting the full lane-replacement grace here would leak an active
			// server flow after a normal peer close.
			if f.finSent.Load() && f.remoteFinSeen.Load() {
				f.closeAll()
				stats.Ended = time.Now()
				stats.BytesSent = f.bytesUp.Load()
				stats.BytesRead = f.bytesDown.Load()
				stats.LaneBytes = f.laneStats()
				return stats, nil
			}
			// A secondary lane can fail without invalidating the bytes already
			// delivered on the logical flow. Replay unacknowledged frames on a
			// surviving lane. If the last lane fails, or replay is impossible,
			// fail closed and let the caller retry the application flow.
			if len(f.healthyLanes()) == 0 {
				if waitErr := f.waitForHealthyLane(ctx, laneReplacementWait); waitErr != nil {
					err = fmt.Errorf("last lane failed (%v): %w", err, waitErr)
				}
			}
			if f.localAbortSent.Load() {
				f.closeAll()
				stats.Ended = time.Now()
				stats.BytesSent = f.bytesUp.Load()
				stats.BytesRead = f.bytesDown.Load()
				stats.LaneBytes = f.laneStats()
				return stats, nil
			}
			if len(f.healthyLanes()) > 0 {
				// The scheduler retains every unacknowledged chunk and will
				// re-offer what the dead lane was carrying, so the only state a
				// replacement needs handed to it is the half-close.
				if replayErr := f.replayPending(ctx); replayErr == nil {
					continue
				} else {
					err = fmt.Errorf("lane failed (%v), replay failed: %w", err, replayErr)
				}
			}
			f.closeAll()
			stats.Ended = time.Now()
			stats.BytesSent = f.bytesUp.Load()
			stats.BytesRead = f.bytesDown.Load()
			stats.LaneBytes = f.laneStats()
			return stats, err
		case <-ctx.Done():
			cancelRun()
			f.closeAll()
			stats.Ended = time.Now()
			stats.BytesSent = f.bytesUp.Load()
			stats.BytesRead = f.bytesDown.Load()
			stats.LaneBytes = f.laneStats()
			return stats, ctx.Err()
		}
	}
	f.closeAll()
	stats.Ended = time.Now()
	stats.BytesSent = f.bytesUp.Load()
	stats.BytesRead = f.bytesDown.Load()
	stats.LaneBytes = f.laneStats()
	return stats, nil
}

// watchLimits turns silent or unbounded flows into explicit, observable
// failures.  It never closes the flow itself: run owns teardown so the
// timeout has the same bounded worker/lane cleanup path as any other error.
func (f *multipathFlow) watchLimits(stop <-chan struct{}, out chan<- error) {
	idle := f.idleTimeout
	lifetime := f.maxLifetime
	if idle <= 0 && lifetime <= 0 {
		return
	}
	interval := time.Second
	if idle > 0 && idle/4 < interval {
		interval = idle / 4
		if interval < 10*time.Millisecond {
			interval = 10 * time.Millisecond
		}
	}
	ticker := time.NewTicker(interval)
	defer ticker.Stop()
	var lifetimeTimer *time.Timer
	var lifetimeC <-chan time.Time
	if lifetime > 0 {
		lifetimeTimer = time.NewTimer(lifetime)
		lifetimeC = lifetimeTimer.C
		defer lifetimeTimer.Stop()
	}
	for {
		select {
		case <-ticker.C:
			if idle > 0 {
				last := f.lastActivity.Load()
				if last == 0 || time.Since(time.Unix(0, last)) >= idle {
					select {
					case out <- errFlowIdleTimeout:
					case <-stop:
					}
					return
				}
			}
		case <-lifetimeC:
			select {
			case out <- errFlowLifetime:
			case <-stop:
			}
			return
		case <-stop:
			return
		case <-f.ctx.Done():
			return
		}
	}
}

func (f *multipathFlow) waitForRemoteFIN(ctx context.Context, timeout time.Duration) bool {
	timer := time.NewTimer(timeout)
	defer timer.Stop()
	ticker := time.NewTicker(5 * time.Millisecond)
	defer ticker.Stop()
	for {
		if f.remoteFinSeen.Load() {
			return true
		}
		select {
		case <-ticker.C:
		case <-timer.C:
			return f.remoteFinSeen.Load()
		case <-ctx.Done():
			return false
		case <-f.done:
			return f.remoteFinSeen.Load()
		}
	}
}

// completionWatchdog handles the one remaining shutdown race that transport
// recovery cannot solve: both application FINs are known, but the final ACK
// is lost while the last physical lane is closing. The FIN pair is the
// correctness boundary; after a small grace period it is safe to release all
// workers and lanes. Normal completion stops run before this timer fires.
func (f *multipathFlow) completionWatchdog(stop <-chan struct{}) {
	ticker := time.NewTicker(50 * time.Millisecond)
	defer ticker.Stop()
	grace := f.completionGrace
	if grace <= 0 {
		grace = flowCompletionGrace
	}
	var bothSince time.Time
	for {
		select {
		case <-ticker.C:
			if f.finSent.Load() && f.remoteFinSeen.Load() {
				if bothSince.IsZero() {
					bothSince = time.Now()
					continue
				}
				if time.Since(bothSince) >= grace {
					if f.metrics != nil {
						f.metrics.CompletionTimeout()
					}
					f.closeAll()
					return
				}
			} else {
				bothSince = time.Time{}
			}
		case <-stop:
			return
		case <-f.ctx.Done():
			return
		}
	}
}

const (
	// stallScanInterval is the watchdog's detection granularity. It is well
	// under the smallest threshold the clamp below can produce, so a stall is
	// suspected within one threshold of becoming true rather than one scan.
	stallScanInterval = 100 * time.Millisecond
	// The threshold is three minimum round trips, clamped. The floor keeps a
	// fast LAN path from paying a rescue for an ordinary scheduling hiccup;
	// the cap keeps a slow path from waiting so long that the rescue itself
	// becomes the flow's whole remaining budget. Before any RTT sample
	// exists the flow gets the conservative default: long enough that a
	// handshake still finding its path is not a stall, short enough to
	// matter against the fifteen seconds an I/O error takes.
	stallRTTMultiplier    = 3
	stallThresholdFloor   = 250 * time.Millisecond
	stallThresholdCap     = 2 * time.Second
	stallThresholdDefault = time.Second
)

// stallThreshold is how long pending work may see no forward progress before
// the flow is suspected stalled: three minimum round trips, clamped.
func (f *multipathFlow) stallThreshold() time.Duration {
	if f.stallGrace > 0 {
		return f.stallGrace
	}
	rtt := time.Duration(f.minRTTNS.Load())
	if rtt <= 0 {
		rtt = time.Duration(f.currentRTTNS.Load())
	}
	if rtt <= 0 {
		return stallThresholdDefault
	}
	threshold := stallRTTMultiplier * rtt
	if threshold < stallThresholdFloor {
		return stallThresholdFloor
	}
	if threshold > stallThresholdCap {
		return stallThresholdCap
	}
	return threshold
}

// pendingOutbound reports whether the flow holds bytes the peer has not
// acknowledged. This is the watchdog's strict gate: a flow whose application
// simply has nothing to send is never a stall, however quiet the path is.
func (f *multipathFlow) pendingOutbound() bool {
	f.replayMu.Lock()
	unacked := f.highestSent > f.acked
	f.replayMu.Unlock()
	if unacked {
		return true
	}
	f.chunkMu.Lock()
	pending := len(f.outstandingChunks) > 0
	f.chunkMu.Unlock()
	return pending
}

// responseOutstanding reports whether the flow is waiting on an answer: the
// application sent something since the last downstream payload arrived, and
// neither side has closed. An idle conversation fails this test because its
// last send was answered, so waiting on one never triggers the watchdog.
func (f *multipathFlow) responseOutstanding() bool {
	if f.remoteFinSeen.Load() || f.finSent.Load() || f.localAbortSent.Load() {
		return false
	}
	return f.bytesUp.Load() > f.upAtLastDown.Load()
}

// scanStall advances one pending/progress pair and reports whether the pair
// has now been pending without progress for the threshold. The clock starts
// when pending is first observed and restarts at every newer progress stamp,
// so a flow that sat idle for an hour and then sent one byte gets a full
// threshold for that byte's round trip.
func scanStall(pending bool, progressNS int64, now time.Time, threshold time.Duration, since *time.Time) bool {
	if !pending {
		*since = time.Time{}
		return false
	}
	if since.IsZero() {
		*since = now
		return false
	}
	if progressNS > 0 {
		if progress := time.Unix(0, progressNS); progress.After(*since) {
			*since = progress
			return false
		}
	}
	return now.Sub(*since) >= threshold
}

// stallWatchdog is the flow's "lane sick" detector, the complement of
// failLane: failLane learns a lane is dead from an I/O error, which on a path
// erasing one direction takes the transport's whole idle timeout of receive
// silence. This watchdog instead measures forward progress -- the
// acknowledged send offset moving, payload arriving -- and, finding none for
// three round trips while work is pending, demotes the current data lane and
// asks the lane manager for a rescue. It never fails a lane and never closes
// anything: the suspected lane keeps receiving and is used again the moment
// nothing healthier exists, and an acknowledgement arriving on it clears the
// suspicion outright.
func (f *multipathFlow) stallWatchdog(stop <-chan struct{}) {
	interval := f.stallScan
	if interval <= 0 {
		interval = stallScanInterval
	}
	ticker := time.NewTicker(interval)
	defer ticker.Stop()
	var sendSince, responseSince time.Time
	episode := false
	var lastSignal time.Time
	for {
		select {
		case <-ticker.C:
		case <-stop:
			return
		case <-f.ctx.Done():
			return
		}
		now := time.Now()
		threshold := f.stallThreshold()
		stalledSend := scanStall(f.pendingOutbound(), f.lastAckProgressNS.Load(), now, threshold, &sendSince)
		var responseBase int64
		if down, up := f.lastDownPayloadNS.Load(), f.lastUpPayloadNS.Load(); down > up {
			responseBase = down
		} else {
			responseBase = up
		}
		stalledResponse := scanStall(f.responseOutstanding(), responseBase, now, threshold, &responseSince)
		if !stalledSend && !stalledResponse {
			episode = false
			continue
		}
		if !episode {
			episode = true
			spare := f.suspectDataLanes()
			if f.metrics != nil {
				f.metrics.FlowStallDetected()
				if spare {
					f.metrics.StallSpareAttached()
				}
			}
			if f.logger != nil {
				f.logger.Info("flow stall suspected; lane demoted and rescue requested",
					"flow_id", f.flowID, "threshold", threshold,
					"send_stalled", stalledSend, "response_stalled", stalledResponse,
					"healthy_spare", spare, "lanes", f.laneCount(),
					"bytes_up", f.bytesUp.Load(), "bytes_down", f.bytesDown.Load())
			}
		}
		// The manager's own backoff paces the dials; this pacing only keeps a
		// persistent stall from queueing signals faster than they can be
		// acted on. An episode that outlives its rescue still re-asks, because
		// the stall it describes is still true. While a round is in flight it
		// does not ask at all: the queued request would be answered by state
		// the round is about to change.
		if now.Sub(lastSignal) >= threshold && !f.rescueInFlight.Load() {
			select {
			case f.stallSignal <- struct{}{}:
				lastSignal = now
			default:
			}
		}
	}
}

// suspectDataLanes marks the lanes currently carrying the flow's data as
// stall-suspected and reports whether a non-suspected healthy lane remains to
// take over new writes at once -- the warm-spare case, where the switch costs
// one scheduler poll rather than a handshake.
func (f *multipathFlow) suspectDataLanes() bool {
	lanes := f.healthyLanes()
	if len(lanes) == 0 {
		return false
	}
	for _, lane := range f.dataLane(lanes) {
		lane.suspected.Store(true)
	}
	for _, lane := range f.healthyLanes() {
		if !lane.suspected.Load() {
			return true
		}
	}
	return false
}

// stallSignals exposes the watchdog's rescue request to the lane manager.
func (f *multipathFlow) stallSignals() <-chan struct{} { return f.stallSignal }

func (f *multipathFlow) telemetryLoop(stop <-chan struct{}) {
	ticker := time.NewTicker(time.Second)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			f.observeTransport(f.healthyLanes())
		case <-stop:
			return
		case <-f.ctx.Done():
			return
		}
	}
}

func (f *multipathFlow) signalDone() {
	if f.done != nil {
		f.doneOnce.Do(func() {
			close(f.done)
			if f.ackTrack != nil {
				f.ackTrack.Close()
			}
		})
	}
}

func (f *multipathFlow) laneStats() map[uint64]LaneStats {
	f.lanesMu.RLock()
	defer f.lanesMu.RUnlock()
	stats := make(map[uint64]LaneStats, len(f.lanes))
	for id, lane := range f.lanes {
		stats[id] = LaneStats{Kind: lane.kind, Sent: lane.sent.Load(), Received: lane.recv.Load()}
	}
	return stats
}

func (f *multipathFlow) doneChan() <-chan struct{} { return f.done }

func (f *multipathFlow) doneChanClosed() bool {
	select {
	case <-f.done:
		return true
	default:
		return false
	}
}

func (f *multipathFlow) enqueueFrame(ctx context.Context, lane *mpLane, frame protocol.Frame) error {
	return f.enqueueFrameClass(ctx, lane, frame, frame.Header.Class == protocol.ClassBulk)
}

func (f *multipathFlow) enqueueFrameClass(ctx context.Context, lane *mpLane, frame protocol.Frame, bulk bool) error {
	return f.enqueueFrameWritten(ctx, lane, frame, bulk, nil)
}

// enqueueFrameWritten is enqueueFrameClass with a callback invoked once the
// lane's transport has taken the frame's bytes.
func (f *multipathFlow) enqueueFrameWritten(ctx context.Context, lane *mpLane, frame protocol.Frame, bulk bool, onWritten func()) error {
	if lane == nil || lane.closed.Load() {
		return errors.New("lane is closed")
	}
	if f.budget != nil {
		interactive := !bulk
		if err := f.budget.Wait(ctx, len(frame.Payload), interactive); err != nil {
			return fmt.Errorf("aggregate pacing: %w", err)
		}
	}
	queue := lane.writeQ
	if !bulk && lane.writeInteractiveQ != nil {
		queue = lane.writeInteractiveQ
	}
	if queue == nil {
		return errors.New("lane writer queue is unavailable")
	}
	acquired := false
	if lane.writeSlots != nil {
		select {
		case lane.writeSlots <- struct{}{}:
			acquired = true
		case <-lane.writeDone:
			f.failLane(lane, errors.New("lane writer stopped"))
			return errors.New("lane writer stopped")
		case <-f.done:
			return errors.New("flow is closed")
		case <-ctx.Done():
			return ctx.Err()
		}
	}
	select {
	case queue <- laneFrame{frame: frame, onWritten: onWritten}:
		return nil
	case <-lane.writeDone:
		if acquired {
			<-lane.writeSlots
		}
		f.failLane(lane, errors.New("lane writer stopped"))
		return errors.New("lane writer stopped")
	case <-f.done:
		if acquired {
			<-lane.writeSlots
		}
		return errors.New("flow is closed")
	case <-ctx.Done():
		if acquired {
			<-lane.writeSlots
		}
		return ctx.Err()
	}
}

func (f *multipathFlow) enqueueOnHealthyLane(ctx context.Context, frame protocol.Frame, bulk bool) error {
	for {
		// One lane carries this plane: the isolated one for data, lane zero for
		// control. This used to try each of several without blocking before
		// committing to one, because with a flow's data striped across lanes,
		// waiting on a full lane while another sat idle stopped the producer
		// and hid the imbalance from the scheduler. There is nowhere to spill
		// to now, and a full lane means what it says -- the flow is limited by
		// the connection carrying it.
		candidates, err := f.laneCandidates(bulk)
		if err == nil {
			if accepted, _ := f.tryEnqueueFrameClass(candidates[0], frame, bulk); accepted {
				return nil
			}
			if err = f.enqueueFrameClass(ctx, candidates[0], frame, bulk); err == nil {
				return nil
			}
		}
		if err := f.waitForHealthyLane(ctx, laneReplacementWait); err != nil {
			return err
		}
	}
}

// tryEnqueueFrameClass offers a frame to one lane without blocking. It reports
// accepted=false with a nil error when the lane is merely full, so the caller
// can move on to the next lane, and a non-nil error when the lane is unusable.
func (f *multipathFlow) tryEnqueueFrameClass(lane *mpLane, frame protocol.Frame, bulk bool) (bool, error) {
	if lane == nil || lane.closed.Load() {
		return false, errors.New("lane is closed")
	}
	queue := lane.writeQ
	if !bulk && lane.writeInteractiveQ != nil {
		queue = lane.writeInteractiveQ
	}
	if queue == nil {
		return false, errors.New("lane writer queue is unavailable")
	}
	acquired := false
	if lane.writeSlots != nil {
		select {
		case lane.writeSlots <- struct{}{}:
			acquired = true
		case <-lane.writeDone:
			f.failLane(lane, errors.New("lane writer stopped"))
			return false, errors.New("lane writer stopped")
		default:
			return false, nil
		}
	}
	select {
	case queue <- laneFrame{frame: frame}:
		return true, nil
	case <-lane.writeDone:
		if acquired {
			<-lane.writeSlots
		}
		f.failLane(lane, errors.New("lane writer stopped"))
		return false, errors.New("lane writer stopped")
	default:
		if acquired {
			<-lane.writeSlots
		}
		return false, nil
	}
}

// noteReplacementAbandoned records that no further replacement lane will be
// attempted for this flow.
//
// It is a statement about this endpoint's own behaviour rather than a guess
// about the path or the peer, which is what makes it safe to act on: waiting
// longer cannot produce a lane nobody is going to open.
func (f *multipathFlow) noteReplacementAbandoned() { f.replacementAbandoned.Store(true) }

// replacementLogFields is what this flow's lane replacements did, named the
// same way on both endpoints so a client record and a gateway record about the
// same failure can be read side by side.
//
// They are emitted on every flow record rather than only on failures. A
// replacement that succeeded is the control case for one that did not, and a
// field that appears only when something went wrong cannot be compared against
// the ordinary run of flows.
func (f *multipathFlow) replacementLogFields() []any {
	waits, timeouts, joined, waited := f.replacementDiagnostics()
	return []any{
		"lane_replacement_waits", waits,
		"lane_replacement_timeouts", timeouts,
		"lane_replacement_wait", waited,
		"lanes_joined", joined,
		"lane_replacement_attempts", f.replacementAttempts.Load(),
		"lane_replacement_failures", f.replacementFailures.Load(),
	}
}

// noteReplacementAttempt records that this endpoint has begun opening a
// replacement lane for a flow that has none. It is counted at the point the
// dial starts rather than when it finishes, because a dial that never returns
// is exactly the case the count exists to make visible.
func (f *multipathFlow) noteReplacementAttempt() { f.replacementAttempts.Add(1) }

// noteReplacementFailure records that one such attempt did not produce a lane.
// Attempts without failures mean the dials are still outstanding; attempts
// equal to failures mean the path is refusing to carry a handshake; no
// attempts at all means nothing tried.
func (f *multipathFlow) noteReplacementFailure() { f.replacementFailures.Add(1) }

// replacementDiagnostics reports what this flow's lane replacements did, for
// the record written when a flow ends. Zero waits is the ordinary case and
// says the flow never lost its last healthy lane.
func (f *multipathFlow) replacementDiagnostics() (waits, timeouts, joined uint64, waited time.Duration) {
	return f.replacementWaits.Load(), f.replacementTimeouts.Load(), f.lanesJoined.Load(),
		time.Duration(f.replacementWaitNanos.Load())
}

func (f *multipathFlow) waitForHealthyLane(ctx context.Context, timeout time.Duration) error {
	if len(f.healthyLanes()) > 0 {
		f.endReplacementOutage()
		return nil
	}
	if f.resumeRefused.Load() {
		return errResumeRefused
	}
	if f.replacementAbandoned.Load() {
		return errReplacementAbandoned
	}
	f.replacementWaits.Add(1)
	waitStarted := time.Now()
	defer func() { f.replacementWaitNanos.Add(int64(time.Since(waitStarted))) }()
	// The grace belongs to the outage, not to this call. Four call sites wait
	// for the last lane -- run, the frame and control writers, and the
	// acknowledgement loop -- and a lane that dies with a write in flight puts
	// more than one of them here for the same missing lane. Each used to start
	// a full grace of its own, so the flow's real willingness to wait was a
	// multiple of this constant that depended on which writers happened to be
	// blocked.
	remaining := f.replacementBudget(waitStarted, timeout)
	if remaining <= 0 {
		// The outage already outlived its grace. Waiting again cannot produce
		// a lane; it only holds the application open for another full grace
		// before telling it what is already known.
		f.replacementTimeouts.Add(1)
		return errLaneReplacementTimeout
	}
	timer := time.NewTimer(remaining)
	defer timer.Stop()
	ticker := time.NewTicker(25 * time.Millisecond)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			if len(f.healthyLanes()) > 0 {
				f.endReplacementOutage()
				return nil
			}
			if f.resumeRefused.Load() {
				// The peer does not have this session, and never will: a
				// session identifier is random and is not reissued. Waiting out
				// the replacement grace here is time the application spends
				// learning nothing. Measured under 35% correlated loss, where
				// the handshake itself often fails, this was 45 seconds of
				// silence per lost flow.
				return errResumeRefused
			}
			if f.replacementAbandoned.Load() {
				// The refusal above is the answer this flow gets when a rescue
				// handshake completes. On a path lossy enough to kill every
				// lane, the rescue handshake is usually what fails instead, so
				// that answer often never arrives and the flow used to wait out
				// the whole grace -- and then, once the attempt budget reset,
				// several more of them. This is the same conclusion reached
				// from evidence this endpoint already has: it has stopped
				// trying to replace the lane.
				return errReplacementAbandoned
			}
		case <-timer.C:
			f.replacementTimeouts.Add(1)
			return errLaneReplacementTimeout
		case <-f.done:
			return errors.New("flow closed while waiting for lane replacement")
		case <-ctx.Done():
			return ctx.Err()
		}
	}
}

// replacementBudget reports what is left of the current outage's grace,
// opening one at now+grace if this waiter is the first to find the flow
// without a lane. A negative or zero result means the outage has already had
// its whole grace and nothing is owed to a further waiter.
//
// A deadline more than a grace into the past is not this outage's. It is the
// residue of one that ended in the narrow window between a waiter finding no
// lane and the arriving lane clearing the outage, where the waiter's own
// deadline lands after the clear and nothing is left to remove it. Reading it
// as current would deny a whole grace to an outage that had not started, so
// it is discarded. The cost of being wrong is the opposite and smaller: a
// waiter that turns up more than a grace after the last one expired -- on a
// flow the expiry has usually already failed -- gets one grace of its own
// rather than none.
func (f *multipathFlow) replacementBudget(now time.Time, grace time.Duration) time.Duration {
	for {
		if deadline := f.replacementDeadline.Load(); deadline != 0 {
			remaining := time.Unix(0, deadline).Sub(now)
			if remaining > -grace {
				return remaining
			}
			if !f.replacementDeadline.CompareAndSwap(deadline, 0) {
				continue
			}
		}
		if f.replacementDeadline.CompareAndSwap(0, now.Add(grace).UnixNano()) {
			return grace
		}
	}
}

// endReplacementOutage forgets the current outage's deadline, so the next one
// starts from a full grace.
func (f *multipathFlow) endReplacementOutage() { f.replacementDeadline.Store(0) }

// extendReplacementOutage restarts the current outage's grace from now, and
// reports whether there was an outage to extend. It exists for the endpoint
// that waits for a rescue rather than sends one: a rescue JOIN that arrives
// while the flow is waiting out its grace is observable proof that the peer's
// recovery is alive and mid-handshake, and letting the hard deadline expire
// underneath that handshake fails the flow at the moment its rescue is
// landing. A flow not in an outage has nothing to extend, and a deadline
// more than a grace into the past is the residue of an outage that already
// ended, which replacementBudget's own staleness rule discards.
func (f *multipathFlow) extendReplacementOutage(now time.Time, grace time.Duration) bool {
	for {
		deadline := f.replacementDeadline.Load()
		if deadline == 0 {
			return false
		}
		if time.Unix(0, deadline).Sub(now) <= -grace {
			return false
		}
		if f.replacementDeadline.CompareAndSwap(deadline, now.Add(grace).UnixNano()) {
			return true
		}
	}
}

func (f *multipathFlow) acknowledgeReplay(sequence uint64, final bool) error {
	f.replayMu.Lock()
	if sequence > f.highestSent {
		f.replayMu.Unlock()
		return fmt.Errorf("acknowledgement %d exceeds sent sequence %d", sequence, f.highestSent)
	}
	if sequence < f.acked {
		f.replayMu.Unlock()
		return nil // delayed ACK from a slower lane
	}
	advanced := sequence > f.acked
	f.acked = sequence
	if f.ackTrack != nil {
		f.ackTrack.Advance(sequence)
	}
	if final && f.closeFrame != nil && f.closeFrame.Header.Sequence <= sequence {
		f.closeFrame = nil
	}
	f.replayMu.Unlock()
	if advanced {
		// The acknowledged send offset is the most direct proof that this
		// flow's bytes are reaching the peer: it only moves when the peer's
		// receiver says so. It is the stall watchdog's send-side clock.
		f.lastAckProgressNS.Store(time.Now().UnixNano())
	}
	return nil
}

// noteSent records that bytes have been written without retaining them.
//
// Under self-pacing the scheduler already holds every unacknowledged chunk and
// can re-issue it on any healthy lane, so retaining a second copy in the replay
// window buys nothing and costs a great deal: the two have different limits, so
// the scheduler outruns the window, the window evicts, the flow is marked
// unreplayable, and the next lane failure kills a transfer the scheduler could
// have finished. The acknowledgement path still needs to know how far the
// stream has been written, which is all this records.
func (f *multipathFlow) noteSent(sequence uint64, n int) {
	f.replayMu.Lock()
	defer f.replayMu.Unlock()
	if end := sequence + uint64(n); end > f.highestSent {
		f.highestSent = end
	}
}

func (f *multipathFlow) sendSequence(sequence uint64) {
	// The sequence is immutable after FIN and is read by the receive loop when
	// an ACK arrives. A channel would also work, but atomic storage avoids a
	// second synchronization point on every data frame.
	f.finSequence.Store(sequence)
}

func (f *multipathFlow) writeControl(ctx context.Context, frame protocol.Frame, preferred *mpLane) error {
	var attempted map[uint64]bool
	if preferred != nil {
		attempted = map[uint64]bool{preferred.id: true}
	}
	for {
		lanes := f.healthyLanes()
		if len(lanes) == 0 {
			if err := f.waitForHealthyLane(ctx, laneReplacementWait); err != nil {
				return err
			}
			continue
		}
		for _, lane := range lanes {
			if attempted != nil && attempted[lane.id] {
				continue
			}
			if err := lane.fc.WriteContext(ctx, frame); err != nil {
				f.failLane(lane, fmt.Errorf("lane %d control write: %w", lane.id, err))
				if attempted == nil {
					attempted = make(map[uint64]bool)
				}
				attempted[lane.id] = true
				continue
			}
			return nil
		}
		// Every lane in this pass failed. Start a new pass so a replacement
		// installed by the lane manager can carry the control frame.
		attempted = nil
	}
}

func (f *multipathFlow) writeACK(ctx context.Context, sequence uint64, direction uint16, final bool) error {
	flags := direction
	if final {
		flags |= protocol.FlagAckFinal
	}
	var payload []byte
	// A final acknowledgement proves everything arrived, so ranges would add
	// nothing; and a peer that did not advertise support must never see them.
	if !final && f.ackRanges.Load() {
		if encoded, err := protocol.EncodeAckRanges(f.takeReceivedRanges(sequence)); err == nil && len(encoded) > 0 {
			payload = encoded
			flags |= protocol.FlagAckRanges
		}
	}
	frame := protocol.Frame{Header: protocol.Header{
		Version: protocol.Version, Type: protocol.TypeAck, Flags: flags,
		SessionID: f.sessionID, FlowID: f.flowID, Sequence: sequence,
		Class: protocol.Class(f.class.Load()),
	}, Payload: payload}
	// ACKs are cumulative and their state is replayable.  Do not wait for the
	// full lane-replacement timeout when every current lane rejects one: the
	// flow coordinator must observe the failure immediately so a replacement
	// can be admitted and the latest ACK/FIN state replayed there.
	lanes := f.healthyLanes()
	if len(lanes) == 0 {
		return errors.New("no healthy lane for acknowledgement")
	}
	var lastErr error
	for _, lane := range lanes {
		if err := lane.fc.WriteContext(ctx, frame); err == nil {
			return nil
		} else {
			lastErr = err
			f.failLane(lane, fmt.Errorf("lane %d acknowledgement write: %w", lane.id, err))
		}
	}
	if lastErr == nil {
		lastErr = errors.New("all lanes rejected acknowledgement")
	}
	return lastErr
}

// A protocol ACK is a window-release message layered above a reliable
// transport, not a loss-recovery signal: QUIC already retransmits. Its rate
// should therefore follow how fast the sender's replay window is being
// consumed, not how often the receiver happens to read.
//
// Acknowledging every 2 ms sent thousands of tiny frames up the reverse
// direction of a download. On a path losing 40% of packets that is actively
// harmful: the reverse stream is ordered, so a lost ACK frame blocks the ones
// behind it, and the retransmissions consume the client's congestion window
// and delay QUIC's own acknowledgements, which is the feedback the sender's
// congestion controller runs on.
//
// Acknowledge instead once a meaningful part of the window has been consumed,
// or after a bounded delay, whichever comes first. The delay stays far below
// one long-haul round trip, and it cannot hold up application bytes in any
// case: a half-close is acknowledged by the separate immediate final-ACK path,
// so this delay only defers releasing replay-window space. The byte threshold
// stays far below the smallest replay window so a sender never runs out of
// window waiting for one.
const (
	// Under self-pacing an acknowledgement is not just bookkeeping: it is what
	// frees window space for the next chunk, so its latency adds directly to
	// the flow's effective round trip. At 200ms RTT the old 50ms coalescing
	// delay was a fifth of the loop, and the self-paced sender measured about
	// 12% below the pushing one largely because of it. TCP acknowledges every
	// couple of segments for the same reason; a chunk here is 32 KiB, so two
	// chunks is the threshold and the timer is only a backstop. The reverse
	// path cost is a few dozen small frames a second.
	ackCoalesceDelay  = 10 * time.Millisecond
	ackBytesThreshold = 64 * 1024
)

// scheduleACK publishes the newest cumulative receive sequence without
// blocking application delivery on a control-frame write. QUIC already
// provides hop reliability; these protocol ACKs exist to bound the replay
// window and support cross-lane resume, so they can be cumulative and
// coalesced. A failed write transitions the lane and lets run's normal rescue
// coordinator replace it; an independent error is reported through ackErr.
// acknowledgeArrival tells the peer what has arrived, whether or not this
// segment advanced the contiguous point, and returns the cumulative point now
// acknowledged.
//
// A segment that did not advance it is the one arrival that proves a gap
// exists, and it used to be the one arrival that said nothing. The sender's
// whole clock is these reports: a chunk completes when its bytes are
// acknowledged, a lane's admission frees when its chunks complete, and nothing
// is issued until it does. So a single unrepaired chunk stopped the sender
// dead -- measured live, a 10 MB download spent three to five seconds with an
// empty pipe and a full lane window, waiting for a gap it had never been told
// about, until the reissue timer eventually filled it.
func (f *multipathFlow) acknowledgeArrival(reassembler *multipath.Reassembler, lastAck uint64) uint64 {
	if next := reassembler.NextSequence(); next > lastAck {
		f.publishReceivedRanges(reassembler)
		f.scheduleACK(next)
		return next
	}
	if reassembler.BufferedFrames() > 0 {
		f.publishReceivedRanges(reassembler)
		f.reportGap()
	}
	return lastAck
}

// reportGap asks for an acknowledgement whose cumulative point has not moved,
// because what it carries is the ranges above it.
func (f *multipathFlow) reportGap() {
	if f.ackClosing.Load() || !f.ackRanges.Load() {
		return
	}
	f.gapPending.Store(true)
	select {
	case f.ackWake <- struct{}{}:
	default:
	}
}

func (f *multipathFlow) scheduleACK(sequence uint64) {
	if sequence == 0 || f.ackClosing.Load() {
		return
	}
	f.acksSched.Add(1)
	for {
		old := f.ackSequence.Load()
		if sequence <= old || f.ackSequence.CompareAndSwap(old, sequence) {
			break
		}
	}
	select {
	case f.ackWake <- struct{}{}:
	default:
	}
}

func (f *multipathFlow) ackLoop(ctx context.Context) {
	var sent uint64
	for {
		select {
		case <-f.ackWake:
		case <-ctx.Done():
			return
		case <-f.done:
			return
		}
		// Coalesce unless the sender's window is already being consumed fast
		// enough that waiting could stall it.
		if f.ackSequence.Load() < sent+ackBytesThreshold {
			timer := time.NewTimer(ackCoalesceDelay)
			select {
			case <-timer.C:
			case <-ctx.Done():
				if !timer.Stop() {
					select {
					case <-timer.C:
					default:
					}
				}
				return
			case <-f.done:
				if !timer.Stop() {
					select {
					case <-timer.C:
					default:
					}
				}
				return
			}
		}
		for {
			if f.ackClosing.Load() {
				return
			}
			sequence := f.ackSequence.Load()
			// A gap report carries the same cumulative point as the last
			// acknowledgement and different ranges above it, so the cumulative
			// point cannot be what decides whether to send.
			if sequence <= sent && !f.gapPending.Swap(false) {
				break
			}
			ackStart := time.Now()
			err := f.writeACK(ctx, sequence, f.recvAckFlag, false)
			f.ackWriteNS.Add(uint64(time.Since(ackStart)))
			f.acksOut.Add(1)
			if err != nil {
				// A failed ACK write is a lane's failure, not the flow's. The
				// lane is already transitioned by writeACK; this loop must
				// outlive it, because the peer's sender is clocked by these
				// acknowledgements and cannot finish without them.
				//
				// Returning here was a silent deadlock. Measured on the rescue
				// path: every application byte crossed in both directions, and
				// then neither endpoint could finish, because the receiver had
				// stopped acknowledging the moment its last lane died and never
				// resumed on the replacement that arrived half a second later.
				// The flow sat until the application gave up.
				if waitErr := f.waitForHealthyLane(ctx, laneReplacementWait); waitErr != nil {
					if ctx.Err() == nil && !f.doneChanClosed() {
						select {
						case f.ackErr <- err:
						default:
						}
					}
					return
				}
				// Re-acknowledge from where the peer was last told, so the
				// replacement lane carries the state the dead one was holding.
				continue
			}
			sent = sequence
			// If more bytes arrived during the write, immediately emit the
			// newer cumulative value. Otherwise return to the wake channel.
			if f.ackSequence.Load() <= sent {
				break
			}
		}
	}
}

func (f *multipathFlow) acknowledgeRemoteFIN(ctx context.Context, sequence uint64, abort bool) error {
	f.remoteFinSequence.Store(sequence)
	f.remoteFinSeen.Store(true)
	f.ackClosing.Store(true)
	if abort {
		// Publish cancellation before any best-effort close or ACK. The send
		// scheduler may hold response chunks forever once the peer has removed
		// its reader, and must not depend on those operations succeeding.
		f.noteRemoteAbort()
		_ = f.inner.Close()
	}
	if cw, ok := f.inner.(closeWriter); ok {
		if err := cw.CloseWrite(); err != nil && !expectedHalfCloseError(err) {
			return err
		}
	}
	ackCtx, cancel := context.WithTimeout(ctx, finalAckWriteGrace)
	err := f.writeACK(ackCtx, sequence, f.recvAckFlag, true)
	cancel()
	if err != nil {
		// The peer FIN and reassembly sequence prove that all inbound bytes are
		// complete. Once our side is also closing, failure to return the final
		// ACK is a cleanup race, not an application-data failure. The server
		// retains a bounded tombstone and can replay/absorb the close state.
		if f.finSent.Load() || f.localClosed.Load() || abort {
			return nil
		}
		return err
	}
	return nil
}

func (f *multipathFlow) receiveInner(ctx context.Context) error {
	reassembler := multipath.NewReassembler(multipath.Config{
		MaxBufferedBytes:  f.memoryLimits.maxReceiveBytes,
		MaxBufferedFrames: f.memoryLimits.maxReceiveFrames,
		Memory:            f.receiveMemory,
	})
	defer reassembler.Close()
	remoteFin := false
	var lastAckSequence uint64
	var abortTimer *time.Timer
	var abortTimerC <-chan time.Time
	resetAbortTimer := func(delay time.Duration) {
		if abortTimer == nil {
			abortTimer = time.NewTimer(delay)
		} else {
			if !abortTimer.Stop() {
				select {
				case <-abortTimer.C:
				default:
				}
			}
			abortTimer.Reset(delay)
		}
		abortTimerC = abortTimer.C
	}
	startLocalAbort := func() error {
		if !f.localAbortSent.CompareAndSwap(false, true) {
			return nil
		}
		if len(f.healthyLanes()) == 0 {
			return errors.New("no healthy lane for local abort")
		}
		writeCtx, cancel := context.WithTimeout(ctx, f.localAbortDrainGrace())
		err := f.writeControl(writeCtx, protocol.Frame{Header: protocol.Header{
			Version: protocol.Version, Type: protocol.TypeClose,
			Flags:     protocol.FlagFin | protocol.FlagCloseAbort,
			SessionID: f.sessionID, FlowID: f.flowID, Sequence: f.finSequence.Load(),
			Class: protocol.Class(f.class.Load()),
		}}, nil)
		cancel()
		return err
	}
	deliverToInner := func(out []byte) error {
		if len(out) == 0 || f.localAbortSent.Load() {
			return nil
		}
		if err := writeFull(f.inner, out); err != nil {
			if !expectedHalfCloseError(err) && !expectedDestinationCloseError(err) {
				return err
			}
			// A failed response write is direct proof that this was a full
			// close, not merely a send-side half-close. Escalate immediately;
			// waiting for the inactivity grace would retain the peer's sender
			// and endpoint for no benefit.
			f.noteLocalClose(f.bytesUp.Load())
			if err := startLocalAbort(); err != nil {
				f.closeAll()
				return errLocalApplicationClose
			}
			resetAbortTimer(f.localAbortDrainGrace())
			return nil
		}
		f.observe(len(out), false)
		f.bytesDown.Add(uint64(len(out)))
		if f.localClosed.Load() {
			// A successful write proves that the application kept its receive
			// half open. Measure the grace from the last such proof, not from
			// the original EOF.
			resetAbortTimer(f.localAbortGrace())
		}
		return nil
	}
	defer func() {
		if abortTimer != nil {
			abortTimer.Stop()
		}
	}()
	// EOF is published by flowSource. It cannot by itself arm the timer: TCP
	// presents CloseWrite and Close identically, so a quiet local EOF may be a
	// legitimate half-close. Buffered response data, a successful response
	// write, or the peer's final ACK supplies the additional evidence that
	// makes a bounded response-side grace appropriate.
	localClosedC := f.localClosedCh
	sendDoneC := f.sendDone
	for {
		select {
		case <-localClosedC:
			localClosedC = nil
			if reassembler.BufferedBytes() > 0 && abortTimer == nil {
				resetAbortTimer(f.localAbortGrace())
			}
		case event := <-f.events:
			frame := event.frame
			if frame.Header.SessionID != f.sessionID || frame.Header.FlowID != f.flowID {
				return errors.New("frame belongs to another session or flow")
			}
			switch frame.Header.Type {
			case protocol.TypeData:
				if remoteFin {
					return errors.New("data received after flow FIN")
				}
				out, closed, err := reassembler.Insert(multipath.Segment{Sequence: frame.Header.Sequence, Payload: frame.Payload})
				if err != nil {
					return err
				}
				if len(out) > 0 {
					if err := deliverToInner(out); err != nil {
						return err
					}
				} else if f.localClosed.Load() && reassembler.BufferedBytes() > 0 && abortTimer == nil {
					// Transport data is arriving but an earlier gap prevents any
					// write to the application. This was the live leak: without a
					// timer no operation remained that could discover its close.
					resetAbortTimer(f.localAbortGrace())
				}
				lastAckSequence = f.acknowledgeArrival(reassembler, lastAckSequence)
				if closed {
					// A FIN may arrive on one lane before an earlier data
					// segment on another lane. Once that gap is filled,
					// Reassembler reports closed=true here; the FIN was valid
					// and must complete the normal ACK/half-close path.
					abort := f.remoteAbort.Load()
					if err := f.acknowledgeRemoteFIN(ctx, reassembler.NextSequence(), abort); err != nil {
						return err
					}
					remoteFin = true
					if abort {
						return nil
					}
					select {
					case <-f.sendDone:
						return nil
					default:
					}
				}
			case protocol.TypeClose:
				if frame.Header.Flags&protocol.FlagFin == 0 || len(frame.Payload) != 0 || frame.Header.Flags&protocol.FlagAckFinal != 0 || frame.Header.Flags&(protocol.FlagAckUp|protocol.FlagAckDown) != 0 {
					return errors.New("invalid flow close frame")
				}
				abort := frame.Header.Flags&protocol.FlagCloseAbort != 0
				if abort {
					// A full close is cancellation, not an ordered half-close. The
					// peer no longer wants bytes in either direction, so waiting
					// for a missing request segment before stopping the response
					// sender only preserves work that can never be consumed.
					return f.acknowledgeRemoteFIN(ctx, frame.Header.Sequence, true)
				}
				out, closed, err := reassembler.Insert(multipath.Segment{Sequence: frame.Header.Sequence, Final: true})
				if err != nil {
					return err
				}
				if len(out) > 0 {
					if err := deliverToInner(out); err != nil {
						return err
					}
				}
				if closed {
					if err := f.acknowledgeRemoteFIN(ctx, reassembler.NextSequence(), abort); err != nil {
						return err
					}
					remoteFin = true
					select {
					case <-f.sendDone:
						return nil
					default:
					}
				}
			case protocol.TypeAck:
				f.acksIn.Add(1)
				if frame.Header.Flags&f.sendAckFlag == 0 {
					return errors.New("acknowledgement has wrong direction")
				}
				// An acknowledgement carrying new delivery information --
				// a cumulative point that moved, ranges, or the final ACK --
				// and arriving on a suspected lane is direct proof the lane
				// still round-trips: the peer received this flow's bytes and
				// its answer travelled back on this lane. A bare duplicate
				// proves nothing about delivery, so it does not clear the
				// mark. Progress itself is recorded in acknowledgeReplay and
				// the ranges branch below.
				clearSuspicion := frame.Header.Flags&protocol.FlagAckFinal != 0 ||
					frame.Header.Flags&protocol.FlagAckRanges != 0
				if frame.Header.Flags&protocol.FlagAckFinal == 0 {
					f.replayMu.Lock()
					advances := frame.Header.Sequence > f.acked
					f.replayMu.Unlock()
					clearSuspicion = clearSuspicion || advances
				}
				if clearSuspicion && event.lane != nil {
					event.lane.suspected.Store(false)
				}
				if frame.Header.Flags&protocol.FlagAckFinal == 0 {
					if err := f.acknowledgeReplay(frame.Header.Sequence, false); err != nil {
						return err
					}
					if frame.Header.Flags&protocol.FlagAckRanges != 0 {
						ranges, err := protocol.DecodeAckRanges(frame.Payload, frame.Header.Sequence)
						if err != nil {
							return fmt.Errorf("acknowledgement ranges: %w", err)
						}
						f.ackTrack.Add(ranges)
						// Ranges above the cumulative point are arrivals too:
						// the peer has these bytes even though a gap stops
						// the acknowledged offset from moving.
						f.lastAckProgressNS.Store(time.Now().UnixNano())
					}
					continue
				}
				if frame.Header.Sequence == f.finSequence.Load() {
					if err := f.acknowledgeReplay(frame.Header.Sequence, true); err != nil {
						return err
					}
					select {
					case f.finalAck <- struct{}{}:
					default:
					}
					if f.localAbortSent.Load() {
						// This acknowledgement covers the abort sequence and every
						// source chunk before it. Tell run to retire the sender rather
						// than waiting for a remote FIN that an aborted flow will not
						// send.
						return errLocalApplicationClose
					}
					if remoteFin {
						return nil
					}
					if f.localClosed.Load() {
						resetAbortTimer(f.localAbortGrace())
					}
				} else {
					return errors.New("final acknowledgement sequence mismatch")
				}
			case protocol.TypeOpenOK:
				if !f.openAckPending || frame.Header.SessionID != f.sessionID || frame.Header.FlowID != f.flowID || len(frame.Payload) != 0 {
					return errors.New("unexpected flow open acknowledgement")
				}
				f.openAckPending = false
				f.confirmOpen()
			case protocol.TypeReset:
				if len(frame.Payload) > 1 {
					return fmt.Errorf("peer reset flow: %s", string(frame.Payload[1:]))
				}
				return errors.New("peer reset flow")
			default:
				return fmt.Errorf("unexpected flow frame type %d", frame.Header.Type)
			}
		case <-f.done:
			// closeAll is used by the completion watcher after both FIN
			// directions have been observed, and by fatal shutdown paths.
			// In the former case no additional frame is required; in the
			// latter run has already selected the original error and is only
			// draining this worker.
			if f.finSent.Load() && f.remoteFinSeen.Load() {
				return nil
			}
			return errors.New("flow closed")
		case <-sendDoneC:
			sendDoneC = nil
			if f.localAbortSent.Load() {
				return errLocalApplicationClose
			}
		case <-abortTimerC:
			if f.localAbortSent.Load() {
				// The abort write received a bounded drain window. Do not let a
				// missing final ACK recreate the permanent flow leak.
				f.closeAll()
				return errLocalApplicationClose
			}
			if err := startLocalAbort(); err != nil {
				// run may currently be inside a bounded lane-replacement wait
				// rather than selecting worker results. Closing done is the
				// wake-up that makes this a real termination source.
				f.closeAll()
				return errLocalApplicationClose
			}
			drainGrace := f.localAbortDrainGrace()
			// Keep consuming acknowledgements briefly. A final ACK lets the
			// scheduler release retained chunks cleanly; expiry is still a clean
			// local cancellation and run will stop the sibling explicitly.
			resetAbortTimer(drainGrace)
		case <-ctx.Done():
			return ctx.Err()
		}
	}
}

// smallExchangeBytes is how much a direction may carry per second and still be
// one of the small exchanges an interactive flow is made of. It matches the
// classifier's own new-flow byte budget: past this, a direction is carrying
// content rather than conversation.
//
// It is a rate rather than a total. Measuring the total made the signal expire
// with the flow's age: a voice call carrying eighty bytes fifty times a second
// crosses any fixed byte budget eventually, and then stops looking like a
// conversation for the rest of the call however it behaves. Sixty-four
// kilobytes a second is half a megabit, which no conversation approaches and
// no transfer stays under.
const smallExchangeBytes = 64 * 1024

// exchangeWindow is the period the rate above is measured over. It is longer
// than a round trip on the paths this project targets, so a single burst in
// flight does not fill it, and short enough that a flow which changes what it
// is doing is reclassified within a few seconds.
const exchangeWindow = time.Second

// recentBytes reports what each direction has carried in the last
// exchangeWindow, which is what says whether this flow is conversing or
// transferring right now.
//
// The window is a pair of buckets rather than a ring: one accumulating and one
// finished. When the accumulating bucket ages out it becomes the finished one
// and a fresh bucket starts, so the reported figure covers between one and two
// windows of traffic. That is coarse, and it is deliberately coarser than the
// decision it feeds: the classifier's thresholds are an order of magnitude
// apart, so a factor of two in the measurement window cannot move a
// conversation across them.
func (f *multipathFlow) recentBytes(now time.Time, n int, up bool) (uint64, uint64) {
	f.recentMu.Lock()
	defer f.recentMu.Unlock()
	if f.recentStart.IsZero() {
		f.recentStart = now
	}
	if now.Sub(f.recentStart) >= exchangeWindow {
		f.priorUp, f.priorDown = f.currentUp, f.currentDown
		f.currentUp, f.currentDown = 0, 0
		f.recentStart = now
	}
	// A byte count is never negative, but this is the one place a wrong sign
	// would wrap the window to something enormous and make every flow look
	// like a transfer for the next two seconds.
	if n > 0 {
		if up {
			f.currentUp += uint64(n)
		} else {
			f.currentDown += uint64(n)
		}
	}
	return f.currentUp + f.priorUp, f.currentDown + f.priorDown
}

func (f *multipathFlow) observe(n int, up bool) bool {
	now := time.Now()
	f.lastActivity.Store(now.UnixNano())
	previousPayload := f.lastPayload.Swap(now.UnixNano())
	age := now.Sub(f.started)
	if age <= 0 {
		age = time.Nanosecond
	}
	upBytes := f.bytesUp.Load()
	downBytes := f.bytesDown.Load()
	if up {
		upBytes += uint64(n)
		if n > 0 {
			f.lastUpPayloadNS.Store(now.UnixNano())
		}
	} else {
		downBytes += uint64(n)
		// n == 0 is refreshClass re-examining what was already carried, not
		// an arrival: only real payload answers what was sent.
		if n > 0 {
			f.lastDownPayloadNS.Store(now.UnixNano())
			// A downstream payload answers everything sent so far. Anything
			// sent after this point is a request the peer has not answered yet.
			f.upAtLastDown.Store(upBytes)
		}
	}
	recentUp, recentDown := f.recentBytes(now, n, up)
	obs := classifier.Observation{
		BytesUp: upBytes, BytesDown: downBytes,
		UpRate: float64(upBytes) / age.Seconds(), DownRate: float64(downBytes) / age.Seconds(),
		Age: age, Bidirectional: upBytes > 0 && downBytes > 0,
		SinceLastPayload: func() time.Duration {
			if previousPayload == 0 {
				return age
			}
			return now.Sub(time.Unix(0, previousPayload))
		}(),
		// Whether this flow is made of small exchanges, measured over a recent
		// window rather than over its whole life.
		//
		// Taking it from the read size made a download permanently
		// unclassifiable: a 10 MB transfer is read in 16 KiB chunks, so every
		// read looked like a small burst, and a download is bidirectional -- a
		// short request, a long response -- so the bulk test's
		// "not bidirectional or not small bursts" was never satisfied. The
		// flow stayed ClassNew to the end and was coded from first byte to
		// last, which cost about a fifth of its throughput on the measured
		// path.
		//
		// Taking it from the lifetime total has the opposite failure and it is
		// the one that matters for a session. Any long-lived conversation
		// eventually carries more than a fixed budget, so it stops satisfying
		// this and is demoted to bulk while still behaving exactly as it
		// always did. A voice call reaches that point after about a minute.
		//
		// A recent rate is right for both. A transfer never drops under it; a
		// conversation never reaches it, whatever its age.
		SmallBidirectionalBursts: recentUp <= smallExchangeBytes && recentDown <= smallExchangeBytes,
	}
	oldClass := classifier.Class(f.class.Load())
	newClass := f.classifier.Observe(obs)
	f.class.Store(uint32(protocol.Class(newClass)))
	if f.metrics != nil && newClass != oldClass {
		f.metrics.ClassTransition(int(newClass))
	}
	return newClass == classifier.ClassBulk
}

// codedSubstrate reports what the coded path under this flow's lanes has done,
// which is what says whether a flow that went slowly was one the code failed
// or one that never used it.
func (f *multipathFlow) codedSubstrate() (coded.Stats, bool) {
	// run closes the physical lanes before its caller writes the completion
	// record. The frame connection retains the coded path's atomic counters
	// after Close, so inspect every lane here rather than only lanes still
	// marked healthy. Otherwise a normal completed flow would usually report
	// fec_available=false precisely when its final FEC record is needed.
	f.lanesMu.RLock()
	defer f.lanesMu.RUnlock()
	for _, lane := range f.lanes {
		if lane.fc == nil {
			continue
		}
		if stats, ok := lane.fc.CodedPath(); ok {
			return stats, true
		}
	}
	return coded.Stats{}, false
}

// codedSubstrateFields renders a coded path's counters for a log line, or
// "none" for a lane that has no coded substrate at all.
func codedSubstrateFields(stats coded.Stats, ok bool) string {
	if !ok {
		return "none"
	}
	// arrived and sources are printed next to lost because without them the
	// line invites a ratio between opposite directions: sent is what this
	// endpoint transmitted, lost is what it failed to receive, and "lost is
	// ten times sent" is an ordinary asymmetric flow rather than a fault. The
	// two rates carry the direction in their names for the same reason, and to
	// match the typed fields below.
	return fmt.Sprintf("sent=%d repairs=%d arrived=%d sources=%d recovered=%d lost=%d recv_residual=%.4f recv_erasure=%.4f window=%d coding=%t rate=%.2f",
		stats.Sent, stats.Repairs, stats.Arrived, stats.Sources, stats.Recovered, stats.Lost,
		stats.Residual(), stats.Erasure(), stats.Window,
		stats.Plan.Code, stats.Plan.Rate)
}

// codedSubstrateLogFields exposes the code plan and the loss estimator as
// typed attributes. coded_substrate above remains for old text consumers, but
// production analysis must not have to parse an opaque summary string.
func codedSubstrateLogFields(stats coded.Stats, ok bool) []any {
	fields := []any{"fec_available", ok}
	if !ok {
		return fields
	}
	snapshot, plan := stats.Snapshot, stats.Plan
	return append(fields,
		"fec_sent_total", stats.Sent,
		"fec_repairs_total", stats.Repairs,
		"fec_recovered_total", stats.Recovered,
		"fec_residual_lost_total", stats.Lost,
		"fec_arrived_total", stats.Arrived,
		"fec_source_symbols_total", stats.SourceSymbols(),
		// The receive direction's own rates, named for it. An endpoint reports
		// two erasure figures that differ by orders of magnitude on an
		// asymmetric path -- these, and the controller's floor, which measures
		// the direction it sends into -- and an operator comparing them
		// without knowing that is the confusion this accounting was fixed for.
		// fec_observed_loss below is a third thing again: what the estimator
		// infers from transmission-sequence gaps rather than what the decoder
		// accounted for. Both of these are in [0,1] by construction.
		"fec_receive_erasure", stats.Erasure(),
		"fec_receive_residual_loss", stats.Residual(),
		"fec_oversize_total", stats.Oversize,
		"fec_window_symbols", stats.Window,
		"fec_coding", plan.Code,
		"fec_plan_k", plan.K,
		"fec_plan_n", plan.N,
		"fec_code_rate", plan.Rate,
		"fec_estimated_residual", plan.Residual,
		"fec_loss_coded", plan.LossCoded,
		"fec_effective_burst", plan.EffectiveBurst,
		"fec_reason", plan.Why,
		"fec_observed_samples", snapshot.Samples,
		"fec_observed_loss", snapshot.Loss,
		"fec_loss_after_arrival", snapshot.LossAfterArrival,
		"fec_arrival_after_loss", snapshot.ArrivalAfterLoss,
		"fec_mean_burst", snapshot.MeanBurst,
		"fec_burst_factor", snapshot.BurstFactor,
		"fec_memoryless", snapshot.Memoryless,
		"fec_erasure_floor", snapshot.Floor,
		"fec_congestive_loss", snapshot.Congestive,
		"fec_recent_loss", snapshot.Recent,
		"fec_reordered_total", snapshot.Reordered,
		"fec_decided_total", snapshot.Decided,
	)
}

// dataSubstrates totals where this flow's payload went across its lanes.
func (f *multipathFlow) dataSubstrates() (coded, stream uint64) {
	f.lanesMu.RLock()
	defer f.lanesMu.RUnlock()
	for _, lane := range f.lanes {
		if lane.fc == nil {
			continue
		}
		c, s := lane.fc.DataSubstrates()
		coded += c
		stream += s
	}
	return coded, stream
}

func (f *multipathFlow) closeAll() {
	f.closeOnce.Do(func() {
		// Mark completion before closing physical lanes. Their reader goroutines
		// can observe the resulting EOF concurrently; those expected shutdown
		// errors must not be exported as transport failures.
		f.finished.Store(true)
		_ = f.inner.Close()
		f.lanesMu.RLock()
		defer f.lanesMu.RUnlock()
		for _, lane := range f.lanes {
			_ = lane.fc.Close()
		}
	})
	f.signalDone()
}

// publishReceivedRanges snapshots what the reassembler holds out of order.
// The acknowledgement loop runs on its own goroutine and must not touch the
// reassembler, which belongs to the receive loop.
func (f *multipathFlow) publishReceivedRanges(reassembler *multipath.Reassembler) {
	if !f.ackRanges.Load() {
		return
	}
	ranges := reassembler.ReceivedRanges(protocol.MaxAckRanges)
	f.rangesMu.Lock()
	f.pendingRanges = ranges
	f.rangesMu.Unlock()
}

// takeReceivedRanges returns the published ranges that are still above the
// cumulative point this acknowledgement carries.
//
// The snapshot is taken when a segment is inserted, but the acknowledgement is
// coalesced and sent later with a newer cumulative sequence. Ranges the cursor
// has since passed are not merely redundant: the peer rejects an ACK whose
// ranges start below its cumulative point, which failed the flow outright.
func (f *multipathFlow) takeReceivedRanges(cumulative uint64) [][2]uint64 {
	f.rangesMu.Lock()
	defer f.rangesMu.Unlock()
	fresh := f.pendingRanges[:0]
	for _, r := range f.pendingRanges {
		if r[0] >= cumulative {
			fresh = append(fresh, r)
		}
	}
	f.pendingRanges = fresh
	return fresh
}

// errResumeRefused reports that the peer cannot resume this association: it
// has no such session, so no replacement lane can be attached to it.
var errResumeRefused = errors.New("peer does not hold this session")

// errReplacementAbandoned reports that this endpoint has stopped attempting
// replacement lanes for the flow, so its grace has nothing left to wait for.
var errReplacementAbandoned = errors.New("no replacement lane will be attempted")

// errLaneReplacementTimeout reports that an outage outlived the whole
// replacement grace. The text is what the live gateway's failure records
// already say, and is kept verbatim so those records stay greppable.
var errLaneReplacementTimeout = errors.New("lane replacement timeout")

// retainClose keeps this flow's half-close so a replacement lane can be given
// it when the lane that carried it dies first.
//
// This is all that remains of a retention window that used to hold every
// unacknowledged DATA frame, with a per-flow byte limit, growth drawn from an
// endpoint-wide memory budget, an eviction path, stall accounting, and an
// "unreplayable" state that failed the flow outright. None of it had anything
// left to retain once the scheduler took over: a chunk is held there until the
// peer acknowledges it and may be re-offered to any lane, so the frame-level
// copy was the same bytes under a second limit. Its own completeness check had
// already been reduced to "return true" for every flow this transport creates.
//
// One frame needs no budget.
func (f *multipathFlow) retainClose(frame protocol.Frame) error {
	if frame.Header.Type != protocol.TypeClose {
		return errors.New("only a close frame is retained for replay")
	}
	retained := frame
	retained.Payload = nil
	f.replayMu.Lock()
	f.closeFrame = &retained
	f.replayMu.Unlock()
	return nil
}

// replayPending re-sends the retained half-close on a lane that still works.
func (f *multipathFlow) replayPending(ctx context.Context) error {
	f.replayMu.Lock()
	frame := f.closeFrame
	f.replayMu.Unlock()
	if frame == nil {
		return nil
	}
	return f.enqueueOnHealthyLane(ctx, *frame, false)
}
