package pep

import (
	"context"
	"errors"
	"io"
	"time"

	"github.com/bojieli/queqiao/internal/protocol"
	"github.com/bojieli/queqiao/internal/stripe"
)

const (
	// maxLaneChunkWindow caps chunks outstanding on one lane. The byte window is
	// meant to be the binding limit and this only stops the bookkeeping growing
	// without bound, so it has to be far above what the byte window admits.
	//
	// It was 96, which sounds generous and is not: a chunk is whatever one read
	// from the application socket returned, often a few kilobytes rather than
	// the 32 KiB maximum, so 96 chunks can be under 800 KB. Against a 210ms
	// feedback loop that caps a lane near 30 Mbit/s regardless of the path, and
	// it is why the self-paced sender measured a third below the pushing one on
	// a single lane at 100 Mbit/s.
	// Measured, not reasoned: with the commitment level pinned at two
	// bandwidth-delay products, 96 chunks per lane measured 26.9 Mbit/s on four
	// lanes over the policed path and 1024 measured 19.3. A chunk is whatever
	// one read returned, so a count is a crude bound on bytes -- but it is also
	// a bound on how many *separate* pieces of the receiver's contiguous point
	// one lane can be holding, and that is what a striped flow pays for when a
	// lane slows.
	maxLaneChunkWindow = 16384
	// maxFlowOutstandingChunks bounds chunks retained across every lane, which
	// bounds a flow's memory: a chunk is held until acknowledged because it may
	// have to be re-issued elsewhere.
	//
	// It has to clear the flow's bandwidth-delay product or it, rather than the
	// windows, becomes the limit. At 100 Mbit/s and 200ms one lane alone needs
	// 2.5 MB in flight and four need ten; the first value here was 4 MiB, and
	// on that path the self-paced sender measured a fifth below the pushing one
	// purely because the producer stopped reading. The real limit on commitment
	// is the per-lane window, which shrinks with the lane; this is the memory
	// ceiling behind it.
	maxFlowOutstandingChunks = 16384
	// maxFlowOutstandingBytes is the ceiling on what one flow may retain. The
	// working value is measured from the lanes (see retentionBytes); this is
	// the memory bound behind it.
	//
	// It was 16 MiB and fixed, and that was the limit on a high bandwidth-delay
	// path rather than anything structural. Measured at 200 ms with four lanes:
	// each lane's congestion window reached 10.5 MB and each held only 4.5 MB
	// in flight, its write-ahead queue empty and the producer stopped, because
	// 16 MiB divided across four lanes is 4 MB each. The lanes were idle, not
	// saturated.
	maxFlowOutstandingBytes = 64 * 1024 * 1024
	// minFlowRetentionBytes is what a flow may retain before it has measured
	// anything.
	minFlowRetentionBytes = 16 * 1024 * 1024
	// lostChunkEvidence is how far beyond a chunk the peer's acknowledgements
	// must reach before the chunk is presumed lost rather than late.
	//
	// One chunk's worth would call a reordering a loss on a striped flow,
	// where lanes deliver out of order by construction. Two is enough that the
	// peer has received a chunk's worth of data that was sent after this one
	// and cannot plausibly still be waiting for it.
	lostChunkEvidence = 2 * defaultChunkSize
	// minChunkReissueDelay and maxChunkReissueDelay bound what the measured
	// round trip may ask for. The floor keeps a fast path from re-sending
	// something that is merely in flight; the ceiling keeps an unmeasured or
	// absurd round trip from restoring the constant this replaced.
	minChunkReissueDelay = 200 * time.Millisecond
	maxChunkReissueDelay = 1500 * time.Millisecond
	// chunkReissueInterval is how often the supervisor looks for chunks to
	// re-offer.
	chunkReissueInterval = 250 * time.Millisecond
	// TCP already retransmits loss and does not expose QUIC's RTT telemetry to
	// this layer. Treating its unknown RTT as the 200 ms floor re-injected every
	// healthy chunk on the measured 200-250 ms path just before its protocol ACK
	// arrived, nearly doubling physical bytes. A hard lane close still retires
	// and reissues immediately; this delay covers only a live-but-stalled socket.
	tcpStripingReissueDelay = 2 * time.Second
	// laneEligibilityPoll is how long a lane waits before rechecking whether
	// the flow's class now lets it carry data. Classification changes at most
	// once or twice in a flow's life, so polling is cheaper than a broadcast.
	laneEligibilityPoll = 20 * time.Millisecond
	// minLaneQueueBytes and maxLaneQueueBytes bound that queue. Two chunks is
	// the floor because one leaves the writer idle while the next is fetched;
	// the ceiling stops a lane with a very large congestion window turning the
	// queue into a buffer no other lane can reach into.
	minLaneQueueBytes = 2 * defaultChunkSize
	maxLaneQueueBytes = 512 * 1024
)

// windowBytes is how many bytes this lane may hold that its transport has not
// yet taken. It is deliberately small.
//
// A lane is paced by its transport: a QUIC stream write returns once the packer
// has consumed the bytes, and the packer consumes them only when the congestion
// window and pacer allow. So the queue in front of that write is the only
// commitment the scheduler makes to one lane in advance, and every byte of it is
// head-of-line exposure -- bytes numbered into the application stream that no
// other lane can take back if this one slows.
//
// It has to be more than nothing, because a lane whose queue empties leaves its
// transport with nothing to send, and a QUIC sender with nothing to send marks
// its bandwidth samples application-limited. BBR discards those, so a lane
// starved even briefly can stop its controller ever leaving startup: measured on
// a path policing each source at 25 Mbit/s, that held a lane at 2.9 times its
// bandwidth-delay product for four seconds and doubled the round trip.
//
// A quarter of the congestion window covers the writer's own scheduling jitter
// on any path, shrinks with a lane that slows, and is bounded above so a fast
// lane cannot turn it into a buffer.
func (l *mpLane) windowBytes() int {
	cwnd, _ := l.congestionState()
	if cwnd <= 0 {
		// No transport telemetry: a TCP rescue lane, or a QUIC connection
		// before its first acknowledgement.
		if rate, rtt := l.sendRate(); rate > 0 && rtt > 0 {
			cwnd = int(rate * rtt.Seconds())
		}
	}
	return laneQueueBytes(cwnd)
}

// retentionBytes is how much this flow may hold unacknowledged: the lanes'
// combined congestion windows, doubled to cover the acknowledgement coming back
// while the next window's worth is already in flight.
//
// This has to follow the path rather than be chosen. A chunk is retained from
// the moment it is read until the peer acknowledges it, so the quantity is
// whatever the lanes can have outstanding at once -- which is what a congestion
// window means. Fixed at 16 MiB it was the binding limit on a fast path and
// four times more than a slow one will ever use.
func (f *multipathFlow) retentionBytes() int {
	total := 0
	for _, lane := range f.healthyLanes() {
		cwnd, _ := lane.congestionState()
		total += cwnd
	}
	if total <= 0 {
		return minFlowRetentionBytes
	}
	if want := 2 * total; want > minFlowRetentionBytes {
		return want
	}
	return minFlowRetentionBytes
}

// reissueDelay is how long a chunk waits before it is presumed lost, which is
// a property of the path rather than a constant.
//
// It only governs the case where nothing follows the chunk to prove it lost --
// a small exchange, or the last chunks of a transfer. Everything else is
// proved by the data behind it within a round trip. Two round trips is what a
// transport's own probe timeout waits for the same reason, and a fixed second
// and a half was six of them on the path this targets: measured live, one
// small flow in five cost 1.79 s instead of 0.29 waiting out that constant.
func (f *multipathFlow) reissueDelay() time.Duration {
	if f.tcpStriping.Load() {
		return tcpStripingReissueDelay
	}
	longest := time.Duration(0)
	for _, lane := range f.healthyLanes() {
		if _, rtt := lane.sendRate(); rtt > longest {
			longest = rtt
		}
	}
	delay := 2 * longest
	if delay < minChunkReissueDelay {
		return minChunkReissueDelay
	}
	if delay > maxChunkReissueDelay {
		return maxChunkReissueDelay
	}
	return delay
}

// laneQueueBytes is how far ahead of its transport a lane may be committed.
func laneQueueBytes(cwnd int) int {
	queue := cwnd / 4
	if queue < minLaneQueueBytes {
		queue = minLaneQueueBytes
	}
	if queue > maxLaneQueueBytes {
		queue = maxLaneQueueBytes
	}
	return queue
}

// congestionState reports the transport's congestion window and what it
// currently has in flight.
func (l *mpLane) congestionState() (cwnd, inFlight int) {
	if l == nil || l.fc == nil {
		return 0, 0
	}
	l.cwndMu.Lock()
	defer l.cwndMu.Unlock()
	now := time.Now()
	if !l.cwndSampled.IsZero() && now.Sub(l.cwndSampled) < laneRateCacheTTL {
		return l.cwndBytes, l.inFlightBytes
	}
	provider, ok := l.fc.transport().(laneStatsProvider)
	if !ok {
		return 0, 0
	}
	controller := provider.transportStats().controller
	l.cwndBytes = int(controller.CongestionWindow)
	l.inFlightBytes = int(controller.BytesInFlight)
	l.cwndSampled = now
	return l.cwndBytes, l.inFlightBytes
}

// flowSource adapts the application connection to the scheduler's reader,
// keeping the classification and half-close handling that used to live in the
// send loop.
type flowSource struct{ flow *multipathFlow }

func (s *flowSource) Read(p []byte) (int, error) {
	n, err := s.flow.inner.Read(p)
	if n > 0 {
		s.flow.observe(n, true)
		s.flow.bytesUp.Add(uint64(n))
	}
	if err != nil {
		// HTTP clients often close a fully-consumed SOCKS socket without a TCP
		// half-close. Treat that as EOF while the logical flow is still live,
		// so the peer receives a normal FIN and releases its destination
		// connection.
		if expectedHalfCloseError(err) {
			err = io.EOF
		}
		if errors.Is(err, io.EOF) {
			// Publish the final source sequence at EOF, not later in
			// sendFinal. A full application close may need to abort while
			// unacknowledged source chunks still keep the scheduler alive.
			s.flow.noteLocalClose(s.flow.bytesUp.Load())
		}
	}
	return n, err
}

// sendInnerStriped carries the application stream to the peer by self-pacing:
// the scheduler holds chunks, and each lane takes one when it has room.
//
// Nothing here decides how to divide the stream between lanes. A lane that is
// fast finishes its chunk sooner, asks sooner, and carries more; a lane that is
// throttled asks rarely; a lane that has stopped never asks, and its chunks are
// re-offered to lanes that are still moving. The division is an outcome, not a
// policy.
func (f *multipathFlow) sendInnerStriped(ctx context.Context) (err error) {
	defer close(f.sendDone)

	sched := stripe.New(&flowSource{flow: f}, stripe.Config{
		ChunkSize:      f.chunkSize,
		LaneWindow:     min(maxLaneChunkWindow, f.memoryLimits.maxOutstanding),
		MaxOutstanding: f.memoryLimits.maxOutstanding,
		// The flow's memory bound is also its read-ahead bound: a chunk is
		// retained from the moment it is read until the peer acknowledges it,
		// because a lane that dies may not have delivered what its transport
		// accepted. Nothing narrower is needed now that a lane's admission is
		// bounded by what its transport has not yet taken.
		MaxOutstandingBytes:  f.memoryLimits.maxSendBytes,
		Memory:               f.sendMemory,
		Retention:            f.retentionBytes,
		RetransmitAfter:      f.reissueDelay,
		ReliableReissueBurst: f.reliableReissueBurst(),
		// A lane carrying its data over coded datagrams does not retransmit
		// for itself: the code repairs most loss and not all, and what it
		// cannot repair has no other way back on a single-lane flow.
		Reliable: f.laneRetransmits,
		Windows:  &laneAdmission{flow: f},
	})
	defer sched.Close()

	sendCtx, cancel := context.WithCancel(ctx)
	defer cancel()
	f.sendCtx.Store(&sendCtx)
	f.scheduler.Store(sched)
	defer f.scheduler.Store(nil)

	for _, lane := range f.healthyLanes() {
		f.startLanePuller(sendCtx, lane, sched)
	}
	go f.superviseChunks(sendCtx, sched)
	go f.watchChunkCompletion(sendCtx, sched)
	go f.sampleLaneCongestion(sendCtx)

	select {
	case <-sched.Done():
	case <-f.remoteAbortCh:
		// A full-close marker says the peer no longer has an application
		// reader. Outstanding response chunks can never be acknowledged and
		// are no longer useful, so cancellation is the successful outcome.
		return nil
	case <-sendCtx.Done():
		return sendCtx.Err()
	case <-f.done:
		if f.finSent.Load() && f.remoteFinSeen.Load() {
			return nil
		}
		return errors.New("flow closed before send completed")
	}
	if srcErr := sched.Err(); srcErr != nil {
		return srcErr
	}
	if f.remoteAbort.Load() {
		// The peer closed its full application socket; a local read error is a
		// consequence of that, not a transport failure.
		return nil
	}
	if f.localAbortSent.Load() {
		// receiveInner already sent the stronger FIN|CLOSE_ABORT marker. Do
		// not follow it with an ordinary FIN for the same sequence.
		return nil
	}
	return f.sendFinal(ctx, sched.Stats().SourceBytes)
}

func (f *multipathFlow) reliableReissueBurst() int {
	if f.tcpStriping.Load() {
		return 1
	}
	return 0
}

// superviseChunks re-offers chunks that a lane has gone quiet on. Self-pacing
// stops a slow lane being handed more work, but a chunk already on it needs
// somebody to notice, and the receiver cannot deliver past it meanwhile.
func (f *multipathFlow) superviseChunks(ctx context.Context, sched *stripe.Scheduler) {
	ticker := time.NewTicker(chunkReissueInterval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-sched.Done():
			return
		case <-f.done:
			return
		case <-ticker.C:
			if n := sched.ReissueExpired(); n > 0 && f.metrics != nil {
				for i := 0; i < n; i++ {
					f.metrics.Reinjected()
				}
			}
		}
	}
}

// startLanePuller runs one worker for a lane. Lanes joined mid-flow get one
// when they are admitted, so a lane starts carrying data as soon as it exists.
func (f *multipathFlow) startLanePuller(ctx context.Context, lane *mpLane, sched *stripe.Scheduler) {
	if lane == nil || sched == nil {
		return
	}
	if !lane.pulling.CompareAndSwap(false, true) {
		return
	}
	go f.runLanePuller(ctx, lane, sched)
}

func (f *multipathFlow) runLanePuller(ctx context.Context, lane *mpLane, sched *stripe.Scheduler) {
	defer lane.pulling.Store(false)
	defer sched.RetireLane(lane.id)
	for {
		if lane.closed.Load() || f.doneChanClosed() {
			return
		}
		bulk := protocol.Class(f.class.Load()) == protocol.ClassBulk
		if !f.laneCarriesData(lane, bulk) {
			select {
			case <-time.After(laneEligibilityPoll):
				continue
			case <-ctx.Done():
				return
			case <-f.done:
				return
			}
		}
		// The window is supplied by laneAdmission, which sees what the lane is
		// already holding; passing a second copy here would apply a stale one.
		chunk, err := sched.Next(ctx, lane.id, 0)
		if err != nil || chunk == nil {
			return
		}
		if err := f.sendChunk(ctx, lane, chunk, bulk); err != nil {
			sched.Fail(lane.id, chunk)
			return
		}
		// The chunk is now this lane's outstanding work, and it stays that way
		// until the peer acknowledges it. The lane does not block here: it
		// keeps pulling until its window is full of unacknowledged bytes, and
		// the window is what paces it. Waiting for each acknowledgement inline
		// would cap the lane at one chunk per round trip -- 32 KiB per 200ms,
		// about 1.3 Mbit/s -- however large its window was.
		f.trackChunk(lane.id, chunk)
	}
}

// outstandingChunk is a chunk written to a lane and not yet acknowledged.
type outstandingChunk struct {
	lane   uint64
	chunk  *stripe.Chunk
	issued time.Time
}

func (f *multipathFlow) trackChunk(laneID uint64, chunk *stripe.Chunk) {
	var issued time.Time
	if laneTrace.Load() {
		issued = time.Now()
	}
	f.chunkMu.Lock()
	for i := range f.outstandingChunks {
		pending := &f.outstandingChunks[i]
		if pending.chunk.Offset != chunk.Offset {
			continue
		}
		// The scheduler tracks transport attempts separately from logical byte
		// ranges. ACK coverage is about the latter, so one completion record is
		// sufficient no matter how many unreliable attempts the same range
		// needed. Keeping one also bounds this list during a prolonged outage.
		pending.lane = laneID
		pending.chunk = chunk
		pending.issued = issued
		f.chunkMu.Unlock()
		return
	}
	f.outstandingChunks = append(f.outstandingChunks, outstandingChunk{lane: laneID, chunk: chunk, issued: issued})
	f.chunkMu.Unlock()
	// Enqueue and tracking are intentionally separate: the lane writer owns
	// transport pacing, while this list owns logical ACK completion. On a fast
	// path the peer can acknowledge between them, and the watcher can consume
	// that one generation change before this chunk appears in its list. If the
	// range is already covered now, advance the generation once more so the
	// watcher reconciles it. This includes an empty final chunk, whose range is
	// covered by definition.
	if f.ackTrack.Covered(chunk.Offset, chunk.End()) {
		f.ackTrack.Touch()
	}
}

// watchChunkCompletion completes chunks as their bytes are acknowledged.
//
// One watcher per flow rather than one waiter per chunk: chunks complete out of
// order by design, and at 100 Mbit/s a 32 KiB chunk size would otherwise mean
// several hundred short-lived goroutines a second per flow.
func (f *multipathFlow) watchChunkCompletion(ctx context.Context, sched *stripe.Scheduler) {
	var gen uint64
	for {
		// One snapshot per pass rather than a locked query per chunk. With
		// hundreds of chunks outstanding and an acknowledgement arriving every
		// few milliseconds, the per-chunk form takes the tracker's lock tens of
		// thousands of times a second for an answer that cannot change during
		// the pass.
		acked := f.ackTrack.Snapshot()
		// What the peer has reported receiving above a chunk is proof the
		// chunk did not arrive. Waiting for the reissue timer instead means
		// waiting a second and a half with the receiver's contiguous point --
		// and so every acknowledgement, and so this sender's clock -- stopped
		// behind it.
		if top := acked.highest(); top > lostChunkEvidence {
			if n := sched.ReissueUnacknowledgedBelow(top - lostChunkEvidence); n > 0 {
				f.reinjections.Add(uint64(n))
				for i := 0; i < n && f.metrics != nil; i++ {
					f.metrics.Reinjected()
				}
			}
		}
		f.chunkMu.Lock()
		kept := f.outstandingChunks[:0]
		var completed []outstandingChunk
		for _, pending := range f.outstandingChunks {
			if acked.covers(pending.chunk.Offset, pending.chunk.End()) {
				completed = append(completed, pending)
				continue
			}
			kept = append(kept, pending)
		}
		f.outstandingChunks = kept
		f.chunkMu.Unlock()
		for _, done := range completed {
			if !done.issued.IsZero() {
				f.observeResidency(time.Since(done.issued))
			}
			sched.Complete(done.lane, done.chunk)
		}

		var err error
		if gen, err = f.ackTrack.WaitChange(ctx, gen); err != nil {
			return
		}
	}
}

// laneCarriesData reports whether this lane is the one carrying this flow's
// data plane. Exactly one is, and a reserved control lane is not it.
func (f *multipathFlow) laneCarriesData(lane *mpLane, bulk bool) bool {
	candidates, err := f.laneCandidates(bulk)
	if err != nil {
		return false
	}
	for _, candidate := range candidates {
		if candidate.id == lane.id {
			return true
		}
	}
	return false
}

// sendChunk writes one chunk on one lane. The chunk's offset is its sequence
// number, so the receiver can place it without knowing which lane it came from
// or what order the lanes ran in.
func (f *multipathFlow) sendChunk(ctx context.Context, lane *mpLane, chunk *stripe.Chunk, bulk bool) error {
	if len(chunk.Data) == 0 {
		// An empty final chunk carries no bytes; the FIN that follows the
		// stream is what ends it.
		return nil
	}
	frame := protocol.Frame{Header: protocol.Header{
		Version: protocol.Version, Type: protocol.TypeData, SessionID: f.sessionID, FlowID: f.flowID,
		Sequence: chunk.Offset, Class: protocol.Class(f.class.Load()),
	}, Payload: chunk.Data}
	// Deliberately not retained here: the scheduler is holding this chunk until
	// it is acknowledged, and is the thing that will re-issue it if this lane
	// stops. Recording it again would put the same bytes under two limits.
	f.noteSent(chunk.Offset, len(chunk.Data))
	var written func()
	if sched := f.scheduler.Load(); sched != nil {
		written = func() { sched.Wrote(lane.id, chunk) }
	}
	return f.enqueueFrameWritten(ctx, lane, frame, bulk, written)
}

// sendFinal closes the outbound direction once every byte has been
// acknowledged, and waits for the peer's final acknowledgement.
func (f *multipathFlow) sendFinal(ctx context.Context, sequence uint64) error {
	f.noteLocalClose(sequence)
	fin := protocol.Frame{Header: protocol.Header{
		Version: protocol.Version, Type: protocol.TypeClose, Flags: protocol.FlagFin,
		SessionID: f.sessionID, FlowID: f.flowID, Sequence: sequence, Class: protocol.Class(f.class.Load()),
	}}
	if err := f.retainClose(fin); err != nil {
		return err
	}
	// Publish the logical FIN before enqueueing it: a lane writer can fail
	// immediately, and recovery must know the FIN is pending so it replays it
	// rather than treating the flow as one-sided.
	f.finSent.Store(true)
	if err := f.enqueueOnHealthyLane(ctx, fin, false); err != nil {
		return err
	}
	select {
	case <-f.finalAck:
		return nil
	case <-f.done:
		// Both FIN directions prove every application byte crossed the flow. A
		// final ACK can be lost in the normal last-lane close race, and the
		// completed-session tombstone can replay it, so do not hold this
		// worker indefinitely.
		if f.finSent.Load() && f.remoteFinSeen.Load() {
			return nil
		}
		return errors.New("flow closed before final acknowledgement")
	case <-ctx.Done():
		return ctx.Err()
	}
}
