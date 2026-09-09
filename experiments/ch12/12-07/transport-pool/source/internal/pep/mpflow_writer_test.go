package pep

import (
	"bytes"
	"context"
	"errors"
	"io"
	"net"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/limiter"
	"github.com/bojieli/queqiao/internal/metrics"
	"github.com/bojieli/queqiao/internal/protocol"
)

// ackCaptureConn is a deterministic stream writer used to exercise the
// asynchronous acknowledgement path without involving a QUIC implementation.
// protocol.WriteFrame emits a header and payload in separate writes, so the
// helper assembles both before publishing the decoded frame.
type ackCaptureConn struct {
	mu       sync.Mutex
	buf      bytes.Buffer
	frames   chan protocol.Frame
	delay    time.Duration
	fail     error
	closed   chan struct{}
	closeOne sync.Once
}

type writeFailConn struct {
	net.Conn
	err error
}

func (c *writeFailConn) Write([]byte) (int, error) { return 0, c.err }

func newAckCaptureConn(delay time.Duration, fail error) *ackCaptureConn {
	return &ackCaptureConn{frames: make(chan protocol.Frame, 16), delay: delay, fail: fail, closed: make(chan struct{})}
}

func (c *ackCaptureConn) Read([]byte) (int, error) {
	<-c.closed
	return 0, io.EOF
}

func (c *ackCaptureConn) Write(p []byte) (int, error) {
	if c.delay > 0 {
		time.Sleep(c.delay)
	}
	if c.fail != nil {
		return 0, c.fail
	}
	c.mu.Lock()
	_, _ = c.buf.Write(p)
	for c.buf.Len() >= protocol.HeaderSize {
		raw := append([]byte(nil), c.buf.Bytes()[:protocol.HeaderSize]...)
		h, err := protocol.DecodeHeader(raw)
		if err != nil {
			c.mu.Unlock()
			return 0, err
		}
		total := protocol.HeaderSize + int(h.PayloadLen)
		if c.buf.Len() < total {
			break
		}
		frame := protocol.Frame{Header: h, Payload: append([]byte(nil), c.buf.Bytes()[protocol.HeaderSize:total]...)}
		c.buf.Next(total)
		select {
		case c.frames <- frame:
		default:
		}
	}
	c.mu.Unlock()
	return len(p), nil
}

func (c *ackCaptureConn) Close() error {
	c.closeOne.Do(func() { close(c.closed) })
	return nil
}

func newAckTestFlow(conn *ackCaptureConn) *multipathFlow {
	flow := &multipathFlow{
		ctx: context.Background(), done: make(chan struct{}), ackWake: make(chan struct{}, 1), ackErr: make(chan error, 1), laneErr: make(chan laneFailure, 1),
		lanes: make(map[uint64]*mpLane), sessionID: [16]byte{1}, flowID: 7, recvAckFlag: protocol.FlagAckDown,
	}
	flow.lanes[0] = &mpLane{id: 0, fc: newFrameConn(conn)}
	return flow
}

func waitAckFrame(t *testing.T, conn *ackCaptureConn) protocol.Frame {
	t.Helper()
	select {
	case frame := <-conn.frames:
		return frame
	case <-time.After(time.Second):
		t.Fatal("timed out waiting for acknowledgement frame")
		return protocol.Frame{}
	}
}

func TestACKLoopCoalescesToNewestSequence(t *testing.T) {
	conn := newAckCaptureConn(0, nil)
	flow := newAckTestFlow(conn)
	ctx, cancel := context.WithCancel(context.Background())
	finished := make(chan struct{})
	go func() { flow.ackLoop(ctx); close(finished) }()
	flow.scheduleACK(10)
	flow.scheduleACK(20)
	got := waitAckFrame(t, conn)
	if got.Header.Type != protocol.TypeAck || got.Header.Sequence != 20 || got.Header.Flags != protocol.FlagAckDown {
		t.Fatalf("coalesced ACK = type=%d sequence=%d flags=%x", got.Header.Type, got.Header.Sequence, got.Header.Flags)
	}
	select {
	case extra := <-conn.frames:
		t.Fatalf("coalescer emitted an unnecessary ACK: sequence=%d", extra.Header.Sequence)
	case <-time.After(20 * time.Millisecond):
	}
	cancel()
	select {
	case <-finished:
	case <-time.After(time.Second):
		t.Fatal("ACK loop did not stop after cancellation")
	}
}

func TestScheduleACKDoesNotBlockOnSlowWrite(t *testing.T) {
	conn := newAckCaptureConn(250*time.Millisecond, nil)
	flow := newAckTestFlow(conn)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	go flow.ackLoop(ctx)
	started := time.Now()
	flow.scheduleACK(1)
	if elapsed := time.Since(started); elapsed > 20*time.Millisecond {
		t.Fatalf("scheduleACK blocked for %s on a slow transport write", elapsed)
	}
}

func TestACKLoopWriteFailureReachesLaneRecovery(t *testing.T) {
	want := errors.New("injected ACK write failure")
	conn := newAckCaptureConn(0, want)
	flow := newAckTestFlow(conn)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	go flow.ackLoop(ctx)
	flow.scheduleACK(1)
	select {
	case failure := <-flow.laneErr:
		if !errors.Is(failure.err, want) {
			t.Fatalf("lane recovery error = %v, want %v", failure.err, want)
		}
	case <-time.After(time.Second):
		t.Fatal("ACK write failure was not reported")
	}
}

func TestFinalACKSuppressesLaterNonFinalACK(t *testing.T) {
	conn := newAckCaptureConn(0, nil)
	flow := newAckTestFlow(conn)
	flow.ackClosing.Store(true)
	flow.scheduleACK(100)
	select {
	case <-conn.frames:
		t.Fatal("non-final ACK was emitted after final ACK state")
	case <-time.After(20 * time.Millisecond):
	}
}

func TestCompletionWatchdogReleasesProvenCompleteFlow(t *testing.T) {
	inner, peer := net.Pipe()
	defer peer.Close()
	registry := metrics.New()
	flow := &multipathFlow{
		ctx: context.Background(), inner: inner, done: make(chan struct{}),
		lanes: make(map[uint64]*mpLane), metrics: registry, completionGrace: 10 * time.Millisecond,
	}
	stop := make(chan struct{})
	go flow.completionWatchdog(stop)
	flow.finSent.Store(true)
	flow.remoteFinSeen.Store(true)
	select {
	case <-flow.done:
	case <-time.After(time.Second):
		close(stop)
		t.Fatal("completion watchdog did not close proven-complete flow")
	}
	close(stop)
	if got := registry.Snapshot().CompletionTimeouts; got != 1 {
		t.Fatalf("completion watchdog metric=%d, want 1", got)
	}
}

func TestFlowIdleTimeoutReleasesResources(t *testing.T) {
	inner, peer := net.Pipe()
	defer peer.Close()
	registry := metrics.New()
	flow := newMultipathFlow(context.Background(), inner, [16]byte{1}, 1, 1024, protocol.FlagAckUp, protocol.FlagAckDown, nil, registry)
	flow.idleTimeout = 20 * time.Millisecond
	flow.maxLifetime = time.Second
	stats, err := flow.run(context.Background())
	if !errors.Is(err, errFlowIdleTimeout) {
		t.Fatalf("flow error = %v, want idle timeout", err)
	}
	if stats.Ended.IsZero() {
		t.Fatal("timed-out flow did not record an end time")
	}
	if got := registry.Snapshot(); got.FlowTimeouts != 1 || got.ActiveFlows != 0 {
		t.Fatalf("timeout metrics = %+v, want one timeout and no active flows", got)
	}
}

// A TCP EOF does not distinguish CloseWrite from Close: both tell the proxy
// only that the application's send half is finished. A quiet peer therefore
// must not be aborted merely because the local reader reached EOF. The abort
// grace starts only once response traffic is stalled or the peer has
// acknowledged the local FIN.
func TestQuietLocalHalfCloseDoesNotArmAbort(t *testing.T) {
	inner, peer := net.Pipe()
	defer peer.Close()
	flow := newMultipathFlow(context.Background(), inner, [16]byte{1}, 7, 1024,
		protocol.FlagAckUp, protocol.FlagAckDown, nil, nil)
	flow.abortGrace = 10 * time.Millisecond
	flow.noteLocalClose(0)

	ctx, cancel := context.WithTimeout(context.Background(), 400*time.Millisecond)
	defer cancel()
	err := flow.receiveInner(ctx)
	if !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("quiet half-close ended receive loop with %v, want context deadline", err)
	}
	if flow.localAbortSent.Load() {
		t.Fatal("quiet half-close was escalated to a full-close abort")
	}
}

// The four durations below are a budget, not free parameters. Writing them as
// named constants because the original spelled them inline as 35ms of gap
// against a 60ms grace, and that 25ms of headroom was thinner than a Windows
// timer tick: the abort fired mid-run and the pipe EOF'd, failing the test in
// exactly abortGrace. Every margin here is now at least a gap wide.
//
//	gap < grace                  one late sleep must not exhaust the grace
//	gaps*gap < timeout           all four frames get sent before ctx expires
//	timeout < gaps*gap + grace   ctx ends the loop before the last grace does
//	grace < gaps*gap             a grace that stopped renewing still fails
const (
	halfCloseGraceProbeGap     = 100 * time.Millisecond
	halfCloseGraceProbeGrace   = 250 * time.Millisecond
	halfCloseGraceProbeTimeout = 450 * time.Millisecond
	halfCloseGraceProbeFrames  = 4
)

func TestResponseProgressRenewsLocalHalfCloseGrace(t *testing.T) {
	inner, application := net.Pipe()
	defer application.Close()
	flow := newMultipathFlow(context.Background(), inner, [16]byte{1}, 7, 1024,
		protocol.FlagAckUp, protocol.FlagAckDown, nil, nil)
	flow.abortGrace = halfCloseGraceProbeGrace
	flow.noteLocalClose(0)

	ctx, cancel := context.WithTimeout(context.Background(), halfCloseGraceProbeTimeout)
	defer cancel()
	result := make(chan error, 1)
	go func() { result <- flow.receiveInner(ctx) }()
	for sequence := uint64(0); sequence < halfCloseGraceProbeFrames; sequence++ {
		if sequence > 0 {
			time.Sleep(halfCloseGraceProbeGap)
		}
		flow.events <- inboundEvent{frame: protocol.Frame{Header: protocol.Header{
			Version: protocol.Version, Type: protocol.TypeData,
			SessionID: [16]byte{1}, FlowID: 7, Sequence: sequence,
		}, Payload: []byte{'x'}}}
		var got [1]byte
		if _, err := io.ReadFull(application, got[:]); err != nil {
			// An EOF here is the abort closing inner, which is the failure
			// this test exists to catch -- say so rather than reporting a
			// bare read error.
			t.Fatalf("read response byte %d after %v: %v; the half-close grace "+
				"stopped being renewed by response progress",
				sequence, time.Duration(sequence)*halfCloseGraceProbeGap, err)
		}
	}
	select {
	case err := <-result:
		if !errors.Is(err, context.DeadlineExceeded) {
			t.Fatalf("progressing response ended receive loop with %v, want context deadline", err)
		}
	case <-time.After(4 * halfCloseGraceProbeTimeout):
		t.Fatal("receive loop did not honor its context")
	}
	if flow.localAbortSent.Load() {
		t.Fatal("response progress was escalated to a full-close abort")
	}
}

// The injected write failure is taken from this platform's half-close sample
// list rather than written as syscall.EPIPE. There is no EPIPE on a Windows
// socket -- a send there reports WSAECONNRESET or WSAECONNABORTED -- and the
// syscall constant of that name is one of the synthetic APPLICATION_ERROR
// values no socket returns. Naming it directly asserted that a code Windows
// never produces is treated as a local close, which is the same class of
// mistake sockerr_windows.go exists to correct.
func TestFailedApplicationWriteSendsAbortImmediately(t *testing.T) {
	pipe, peer := net.Pipe()
	defer peer.Close()
	outer := newAckCaptureConn(0, nil)
	flow := newMultipathFlow(context.Background(), &writeFailConn{Conn: pipe, err: halfCloseSamples[0].err},
		[16]byte{1}, 7, 1024, protocol.FlagAckUp, protocol.FlagAckDown, nil, nil)
	flow.abortDrainGrace = 20 * time.Millisecond
	flow.lanes[0] = &mpLane{id: 0, fc: newFrameConn(outer)}

	result := make(chan error, 1)
	go func() { result <- flow.receiveInner(context.Background()) }()
	flow.events <- inboundEvent{frame: protocol.Frame{Header: protocol.Header{
		Version: protocol.Version, Type: protocol.TypeData,
		SessionID: [16]byte{1}, FlowID: 7, Sequence: 0,
	}, Payload: []byte("response")}}
	frame := waitAckFrame(t, outer)
	if frame.Header.Type != protocol.TypeClose || frame.Header.Flags != protocol.FlagFin|protocol.FlagCloseAbort {
		t.Fatalf("failed local write produced type=%d flags=%#x, want CLOSE FIN|CLOSE_ABORT",
			frame.Header.Type, frame.Header.Flags)
	}
	select {
	case err := <-result:
		if !errors.Is(err, errLocalApplicationClose) {
			t.Fatalf("failed local write ended receive loop with %v, want local close", err)
		}
	case <-time.After(time.Second):
		t.Fatal("failed local write did not end after the abort drain")
	}
}

// This is the live leak reduced to one deterministic flow. The application
// closes after the peer has delivered only an out-of-order response segment.
// The local sender is deliberately left with an unacknowledged request, so
// neither the scheduler nor the remote-FIN path can end the flow for us.
func TestLocalCloseAbortsStalledReceiveAndReleasesRun(t *testing.T) {
	inner, application := net.Pipe()
	outer, peer := net.Pipe()
	defer application.Close()
	defer peer.Close()

	sessionID := [16]byte{1}
	const flowID = uint64(7)
	flow := newMultipathFlow(context.Background(), inner, sessionID, flowID, 1024,
		protocol.FlagAckUp, protocol.FlagAckDown, nil, nil)
	flow.abortGrace = 20 * time.Millisecond
	flow.abortDrainGrace = 100 * time.Millisecond
	if err := flow.addLane(&mpLane{id: 0, fc: newFrameConn(outer)}); err != nil {
		t.Fatal(err)
	}

	responseBuffered := make(chan struct{})
	abortSeen := make(chan protocol.Frame, 1)
	peerErr := make(chan error, 1)
	go func() {
		buffered := false
		for {
			frame, err := protocol.ReadFrame(peer)
			if err != nil {
				peerErr <- err
				return
			}
			switch frame.Header.Type {
			case protocol.TypeData:
				if buffered {
					continue
				}
				buffered = true
				// Sequence zero is intentionally absent. receiveInner holds
				// this byte in its reassembler and cannot discover the closed
				// application by attempting a write.
				if err := protocol.WriteFrame(peer, protocol.Frame{Header: protocol.Header{
					Version: protocol.Version, Type: protocol.TypeData,
					SessionID: sessionID, FlowID: flowID, Sequence: 1,
				}, Payload: []byte("stalled")}); err != nil {
					peerErr <- err
					return
				}
				close(responseBuffered)
			case protocol.TypeClose:
				if frame.Header.Flags&protocol.FlagCloseAbort == 0 {
					peerErr <- errors.New("received ordinary FIN instead of abort")
					return
				}
				if frame.Header.Sequence != uint64(len("request")) {
					peerErr <- errors.New("abort did not carry the complete source sequence")
					return
				}
				abortSeen <- frame
				// Deliberately withhold the final ACK. The regression was a
				// flow whose scheduler and receive loop both waited forever;
				// cleanup must therefore be bounded even when the abort's
				// completion signal is also absent.
				return
			}
		}
	}()

	type runResult struct {
		stats FlowStats
		err   error
	}
	result := make(chan runResult, 1)
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	go func() {
		stats, err := flow.run(ctx)
		result <- runResult{stats: stats, err: err}
	}()
	if _, err := application.Write([]byte("request")); err != nil {
		t.Fatal(err)
	}
	select {
	case <-responseBuffered:
	case err := <-peerErr:
		t.Fatalf("peer failed before buffering response: %v", err)
	case <-time.After(time.Second):
		t.Fatal("peer did not send the stalled response segment")
	}
	_ = application.Close()

	select {
	case frame := <-abortSeen:
		if frame.Header.Flags != protocol.FlagFin|protocol.FlagCloseAbort {
			t.Fatalf("abort flags = %#x, want FIN|CLOSE_ABORT", frame.Header.Flags)
		}
	case err := <-peerErr:
		t.Fatalf("peer failed before receiving abort: %v", err)
	case <-time.After(time.Second):
		t.Fatal("local close did not produce a bounded abort")
	}
	select {
	case got := <-result:
		if got.err != nil {
			t.Fatalf("locally aborted flow returned error: %v", got.err)
		}
		if got.stats.BytesSent != uint64(len("request")) {
			t.Fatalf("sent bytes = %d, want %d", got.stats.BytesSent, len("request"))
		}
	case <-time.After(time.Second):
		t.Fatal("flow remained stuck after the bounded abort drain")
	}
}

// A full-close abort is cancellation, not an ordered half-close. In
// particular, the peer's sender may have response chunks outstanding that the
// vanished application will never acknowledge. Receiving the abort must stop
// that scheduler and close the peer-side endpoint immediately.
func TestRemoteAbortStopsUnacknowledgedSenderAndClosesInner(t *testing.T) {
	inner, destination := net.Pipe()
	defer destination.Close()
	// Hold the abort acknowledgement long enough for closing inner to wake
	// the sibling source reader first. Windows reliably schedules this order
	// with a TCP destination; it must remain a clean remote cancellation even
	// when the reader reports its close error before receiveInner returns.
	outer := newAckCaptureConn(250*time.Millisecond, nil)
	sessionID := [16]byte{2}
	const flowID = uint64(9)
	flow := newMultipathFlow(context.Background(), inner, sessionID, flowID, 1024,
		protocol.FlagAckDown, protocol.FlagAckUp, nil, nil)
	if err := flow.addLane(&mpLane{id: 0, fc: newFrameConn(outer)}); err != nil {
		t.Fatal(err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	result := make(chan error, 1)
	go func() {
		_, err := flow.run(ctx)
		result <- err
	}()
	writeDone := make(chan error, 1)
	go func() {
		_, err := destination.Write(bytes.Repeat([]byte("response"), 256))
		writeDone <- err
	}()
	frame := waitAckFrame(t, outer)
	if frame.Header.Type != protocol.TypeData {
		t.Fatalf("first outbound frame type = %d, want DATA", frame.Header.Type)
	}

	flow.events <- inboundEvent{frame: protocol.Frame{Header: protocol.Header{
		Version: protocol.Version, Type: protocol.TypeClose,
		Flags:     protocol.FlagFin | protocol.FlagCloseAbort,
		SessionID: sessionID, FlowID: flowID, Sequence: 0,
	}}}
	select {
	case err := <-result:
		if err != nil {
			t.Fatalf("remote abort ended flow with error: %v", err)
		}
	case <-time.After(time.Second):
		t.Fatal("remote abort left the response scheduler outstanding")
	}
	select {
	case <-writeDone:
	case <-time.After(time.Second):
		t.Fatal("remote abort did not release the destination writer")
	}
	_ = destination.SetWriteDeadline(time.Now().Add(100 * time.Millisecond))
	if _, err := destination.Write([]byte("still open?")); err == nil {
		t.Fatal("destination connection remained writable after remote abort")
	}
}

func TestLaneWriterStopsWhenFlowCompletes(t *testing.T) {
	flow := &multipathFlow{ctx: context.Background(), done: make(chan struct{}), laneErr: make(chan laneFailure, 1)}
	lane := &mpLane{
		writeQ:    make(chan laneFrame, 1),
		writeDone: make(chan struct{}),
	}
	go flow.writeLane(lane)
	close(flow.done)

	select {
	case <-lane.writeDone:
	case <-time.After(time.Second):
		t.Fatal("lane writer did not stop after flow completion")
	}
}

func TestLaneFailureCountIsMonotonicAndIdempotent(t *testing.T) {
	conn := newAckCaptureConn(0, nil)
	flow := &multipathFlow{
		ctx: context.Background(), done: make(chan struct{}), laneErr: make(chan laneFailure, 1),
		lanes: make(map[uint64]*mpLane),
	}
	lane := &mpLane{id: 1, fc: newFrameConn(conn)}
	flow.failLane(lane, errors.New("first"))
	flow.failLane(lane, errors.New("duplicate"))
	if got := flow.laneFailureCount(); got != 1 {
		t.Fatalf("lane failure count = %d, want one transition", got)
	}
	select {
	case <-flow.laneErr:
	default:
		t.Fatal("lane failure was not published")
	}
}

func TestLaneWriterPrioritizesInteractiveFrames(t *testing.T) {
	conn := newAckCaptureConn(0, nil)
	flow := &multipathFlow{
		ctx:     context.Background(),
		done:    make(chan struct{}),
		laneErr: make(chan laneFailure, 1),
	}
	lane := &mpLane{
		id:                1,
		fc:                newFrameConn(conn),
		writeQ:            make(chan laneFrame, maxLaneWriteQueue),
		writeInteractiveQ: make(chan laneFrame, maxLaneWriteQueue),
		writeSlots:        make(chan struct{}, maxLaneWriteQueue),
		writeDone:         make(chan struct{}),
	}
	bulk := protocol.Frame{Header: protocol.Header{Version: protocol.Version, Type: protocol.TypeData, Class: protocol.ClassBulk}, Payload: []byte("bulk")}
	interactive := protocol.Frame{Header: protocol.Header{Version: protocol.Version, Type: protocol.TypeData, Class: protocol.ClassInteractive}, Payload: []byte("interactive")}
	for _, frame := range []protocol.Frame{bulk, interactive} {
		if err := flow.enqueueFrameClass(context.Background(), lane, frame, frame.Header.Class == protocol.ClassBulk); err != nil {
			t.Fatal(err)
		}
	}
	go flow.writeLane(lane)
	first := waitAckFrame(t, conn)
	second := waitAckFrame(t, conn)
	if string(first.Payload) != string(interactive.Payload) || string(second.Payload) != string(bulk.Payload) {
		t.Fatalf("writer order = %q then %q, want interactive then bulk", first.Payload, second.Payload)
	}
	close(flow.done)
	select {
	case <-lane.writeDone:
	case <-time.After(time.Second):
		t.Fatal("lane writer did not stop")
	}
}

func TestSchedulerDataFramesUseAggregateBudget(t *testing.T) {
	flow := &multipathFlow{
		ctx:     context.Background(),
		done:    make(chan struct{}),
		laneErr: make(chan laneFailure, 1),
		budget: limiter.New(limiter.Config{
			TotalBytesPerSec: 1,
			Burst:            time.Millisecond,
		}),
	}
	lane := &mpLane{
		writeQ:    make(chan laneFrame, 1),
		writeDone: make(chan struct{}),
	}
	frame := protocol.Frame{
		Header:  protocol.Header{Version: protocol.Version, Type: protocol.TypeData, Class: protocol.ClassBulk},
		Payload: make([]byte, 64*1024+1),
	}

	err := flow.enqueueFrameWritten(context.Background(), lane, frame, true, nil)
	if !errors.Is(err, limiter.ErrInvalidRequest) {
		t.Fatalf("oversized data frame error = %v, want aggregate pacing rejection", err)
	}
}

// Reserving the control lane is a preference, never a correctness dependency:
// with no other lane healthy, bulk must still go somewhere.
func TestBulkSelectionFallsBackToControlLane(t *testing.T) {
	flow := &multipathFlow{
		done: make(chan struct{}), lanes: map[uint64]*mpLane{0: {id: 0}}, reserveControlLane: true,
	}
	candidates, err := flow.laneCandidates(true)
	if err != nil {
		t.Fatal(err)
	}
	if len(candidates) != 1 || candidates[0].id != 0 {
		t.Fatalf("bulk fallback produced %d lanes, want only the control lane", len(candidates))
	}
}

// A QUIC flow's data rides one lane, whatever lanes it happens to hold.
//
// This used to return every eligible QUIC lane and let the scheduler spread
// chunks across them. There is no policy that grows a QUIC flow to two data
// lanes, but a flow can still transiently hold two during a recovery
// -- and then it would have striped across them with nothing having decided
// to. One lane is now the structure rather than an outcome.
func TestQUICDataRidesOneLaneEvenWhenTheFlowHoldsTwo(t *testing.T) {
	for _, reserve := range []bool{false, true} {
		flow := &multipathFlow{
			done:               make(chan struct{}),
			lanes:              map[uint64]*mpLane{0: {id: 0, kind: TransportQUIC}, 1: {id: 1, kind: TransportQUIC}},
			reserveControlLane: reserve,
		}
		candidates, err := flow.laneCandidates(true)
		if err != nil {
			t.Fatal(err)
		}
		if len(candidates) != 1 {
			t.Fatalf("reserve=%v: data selection produced %d lanes, want exactly one", reserve, len(candidates))
		}
	}
}

func TestNegotiatedTCPFlowStripesOnlyAcrossPureTCPBundle(t *testing.T) {
	flow := &multipathFlow{
		done: make(chan struct{}),
		lanes: map[uint64]*mpLane{
			0: {id: 0, kind: TransportTCP},
			1: {id: 1, kind: TransportTCP},
			2: {id: 2, kind: TransportTCP},
		},
	}
	flow.tcpStriping.Store(true)
	candidates, err := flow.laneCandidates(true)
	if err != nil {
		t.Fatal(err)
	}
	if len(candidates) != 3 {
		t.Fatalf("negotiated TCP candidates = %d, want all three lanes", len(candidates))
	}

	flow.lanes[2].kind = TransportQUIC
	candidates, err = flow.laneCandidates(true)
	if err != nil {
		t.Fatal(err)
	}
	if len(candidates) != 1 {
		t.Fatalf("mixed-transport candidates = %d, want one fail-safe lane", len(candidates))
	}

	flow.lanes[2].kind = TransportTCP
	flow.tcpStriping.Store(false)
	candidates, err = flow.laneCandidates(true)
	if err != nil {
		t.Fatal(err)
	}
	if len(candidates) != 1 {
		t.Fatalf("disabled TCP striping candidates = %d, want one lane", len(candidates))
	}
}

func TestTCPStripingDoesNotUseTheUnknownRTTFloorForReinjection(t *testing.T) {
	flow := &multipathFlow{}
	flow.tcpStriping.Store(true)
	if got := flow.reissueDelay(); got != tcpStripingReissueDelay {
		t.Fatalf("TCP striping reissue delay = %v, want %v", got, tcpStripingReissueDelay)
	}
}

// The two planes go to different places, which is the whole point of the
// reservation: a bulk flow's data is not coded, so it rides a stream, and if
// that were the stream its control rides then its own acknowledgements would
// sit strictly behind its own bulk.
func TestControlAndDataTakeDifferentLanesWhenAFlowIsIsolated(t *testing.T) {
	flow := &multipathFlow{
		done:               make(chan struct{}),
		lanes:              map[uint64]*mpLane{0: {id: 0}, 1: {id: 1}},
		reserveControlLane: true,
		controlLaneShared:  func() bool { return true },
	}
	control, err := flow.laneCandidates(false)
	if err != nil {
		t.Fatal(err)
	}
	data, err := flow.laneCandidates(true)
	if err != nil {
		t.Fatal(err)
	}
	if control[0].id != 0 {
		t.Fatalf("control took lane %d, want the pooled control lane", control[0].id)
	}
	if data[0].id != 1 {
		t.Fatalf("data took lane %d, want the isolated lane", data[0].id)
	}
}

func TestControlRoleSurvivesANonzeroGenerationReplacement(t *testing.T) {
	flow := &multipathFlow{
		done: make(chan struct{}),
		lanes: map[uint64]*mpLane{
			3: {id: 3, kind: TransportQUIC, control: true},
			4: {id: 4, kind: TransportQUIC},
		},
		reserveControlLane: true,
		controlLaneShared:  func() bool { return true },
	}
	control, err := flow.laneCandidates(false)
	if err != nil {
		t.Fatal(err)
	}
	data, err := flow.laneCandidates(true)
	if err != nil {
		t.Fatal(err)
	}
	if len(control) != 1 || control[0].id != 3 {
		t.Fatalf("control selected %+v, want replacement lane 3", control)
	}
	if len(data) != 1 || data[0].id != 4 {
		t.Fatalf("data selected %+v, want isolated lane 4", data)
	}
	if !flow.retireLeastProductiveLane() {
		t.Fatal("no non-control lane was available to retire")
	}
	if flow.lanes[3].closed.Load() {
		t.Fatal("nonzero control replacement was retired as ordinary data")
	}
}

// Isolation is declined while nothing else is on the pooled connection, and
// then both planes share it. Paying a fresh congestion window to protect
// traffic that is not there costs about 8% of bulk goodput for nothing.
func TestBothPlanesShareTheControlLaneWhileItIsUnshared(t *testing.T) {
	flow := &multipathFlow{
		done:               make(chan struct{}),
		lanes:              map[uint64]*mpLane{0: {id: 0}, 1: {id: 1}},
		reserveControlLane: true,
		controlLaneShared:  func() bool { return false },
	}
	data, err := flow.laneCandidates(true)
	if err != nil {
		t.Fatal(err)
	}
	if len(data) != 1 || data[0].id != 0 {
		t.Fatalf("data took lane %d, want the control lane it was never moved off", data[0].id)
	}
}

func TestBulkLanePrewarmRequiresAgeBytesAndDirectionality(t *testing.T) {
	tests := []struct {
		name     string
		snapshot flowSnapshot
		want     bool
	}{
		{name: "young", snapshot: flowSnapshot{Bytes: 256 * 1024, BytesUp: 1, BytesDown: 256 * 1024, Elapsed: 100 * time.Millisecond}},
		{name: "small", snapshot: flowSnapshot{Bytes: 32 * 1024, BytesUp: 1, BytesDown: 32 * 1024, Elapsed: time.Second}},
		{name: "balanced interactive", snapshot: flowSnapshot{Bytes: 256 * 1024, BytesUp: 128 * 1024, BytesDown: 128 * 1024, Elapsed: time.Second}},
		{name: "download", snapshot: flowSnapshot{Bytes: 256*1024 + 1024, BytesUp: 1024, BytesDown: 256 * 1024, Elapsed: time.Second}, want: true},
		{name: "upload", snapshot: flowSnapshot{Bytes: 256*1024 + 1024, BytesUp: 256 * 1024, BytesDown: 1024, Elapsed: time.Second}, want: true},
		{name: "one way", snapshot: flowSnapshot{Bytes: 64 * 1024, BytesDown: 64 * 1024, Elapsed: bulkLanePrewarmAge}, want: true},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			if got := shouldPrewarmBulkLane(test.snapshot); got != test.want {
				t.Fatalf("prewarm = %t, want %t for %+v", got, test.want, test.snapshot)
			}
		})
	}
}

func TestLaneQueueHasGlobalBound(t *testing.T) {
	flow := &multipathFlow{ctx: context.Background(), done: make(chan struct{}), laneErr: make(chan laneFailure, 1)}
	lane := &mpLane{
		writeQ:            make(chan laneFrame, maxLaneWriteQueue),
		writeInteractiveQ: make(chan laneFrame, maxLaneWriteQueue),
		writeSlots:        make(chan struct{}, maxLaneWriteQueue),
		writeDone:         make(chan struct{}),
	}
	frame := protocol.Frame{Header: protocol.Header{Version: protocol.Version, Type: protocol.TypeData, Class: protocol.ClassBulk}, Payload: []byte("x")}
	for i := 0; i < maxLaneBulkQueue; i++ {
		if err := flow.enqueueFrameClass(context.Background(), lane, frame, true); err != nil {
			t.Fatalf("enqueue %d: %v", i, err)
		}
	}
	// The reserved interactive slots remain available even when bulk is at
	// its queue limit. Fill those slots with high-priority frames, then verify
	// that the combined queue cannot exceed the global bound.
	interactive := frame
	interactive.Header.Class = protocol.ClassInteractive
	for i := 0; i < maxLaneInteractiveReserve; i++ {
		if err := flow.enqueueFrameClass(context.Background(), lane, interactive, false); err != nil {
			t.Fatalf("interactive enqueue %d: %v", i, err)
		}
	}
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Millisecond)
	defer cancel()
	if err := flow.enqueueFrameClass(ctx, lane, frame, true); !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("overflow enqueue error = %v, want context deadline", err)
	}
	if got := len(lane.writeSlots); got != maxLaneWriteQueue {
		t.Fatalf("global queue slots used = %d, want %d", got, maxLaneWriteQueue)
	}
}

func TestEnqueueFrameStopsWhenLaneWriterStops(t *testing.T) {
	flow := &multipathFlow{ctx: context.Background(), done: make(chan struct{}), laneErr: make(chan laneFailure, 1)}
	lane := &mpLane{
		writeQ:    make(chan laneFrame),
		writeDone: make(chan struct{}),
	}
	close(lane.writeDone)

	err := flow.enqueueFrame(context.Background(), lane, protocol.Frame{})
	if err == nil {
		t.Fatal("enqueue succeeded after lane writer stopped")
	}
}

func TestRetireLeastProductiveLaneKeepsControlLane(t *testing.T) {
	flow := &multipathFlow{lanes: map[uint64]*mpLane{
		0: {id: 0},
		1: {id: 1},
		2: {id: 2},
	}}
	flow.lanes[1].sent.Store(100)
	flow.lanes[2].sent.Store(10)
	if !flow.retireLeastProductiveLane() {
		t.Fatal("expected a non-control lane to be retired")
	}
	if _, ok := flow.lanes[2]; ok {
		t.Fatal("least productive lane remained attached")
	}
	if flow.lanes[0].closed.Load() {
		t.Fatal("control lane was retired")
	}
}

func TestExpectedCloseDoesNotCountAsLaneFailure(t *testing.T) {
	registry := metrics.New()
	flow := &multipathFlow{done: make(chan struct{}), metrics: registry}
	lane := &mpLane{id: 1}
	flow.finished.Store(true)
	flow.failLane(lane, errors.New("normal close"))
	if got := registry.Snapshot().LaneFailures; got != 0 {
		t.Fatalf("normal close exported as %d lane failures", got)
	}
}

func TestReadLaneTreatsEOFAfterRemoteCloseAsHalfClose(t *testing.T) {
	inner, application := net.Pipe()
	defer application.Close()
	registry := metrics.New()
	outer, peer := net.Pipe()
	defer peer.Close()
	flow := newMultipathFlow(context.Background(), inner, [16]byte{1}, 7, 1024,
		protocol.FlagAckUp, protocol.FlagAckDown, nil, registry)
	lane := &mpLane{id: 0, fc: newFrameConn(outer)}
	flow.lanes[0] = lane
	closeFrame := protocol.Frame{Header: protocol.Header{
		Version: protocol.Version, Type: protocol.TypeClose, Flags: protocol.FlagFin,
		SessionID: [16]byte{1}, FlowID: 7,
	}}
	readerDone := make(chan struct{})
	go func() {
		flow.readLane(lane)
		close(readerDone)
	}()
	writeDone := make(chan error, 1)
	go func() {
		writeDone <- protocol.WriteFrame(peer, closeFrame)
		_ = peer.Close()
	}()

	select {
	case event := <-flow.events:
		if event.frame.Header.Type != protocol.TypeClose {
			t.Fatalf("reader delivered frame type %d, want CLOSE", event.frame.Header.Type)
		}
	case <-time.After(time.Second):
		t.Fatal("timed out waiting for peer CLOSE")
	}
	if err := <-writeDone; err != nil {
		t.Fatal(err)
	}
	select {
	case <-readerDone:
	case <-time.After(time.Second):
		t.Fatal("lane reader did not return after peer EOF")
	}
	if lane.closed.Load() {
		t.Fatal("peer half-close retired the surviving write direction")
	}
	if got := registry.Snapshot().LaneFailures; got != 0 {
		t.Fatalf("CLOSE followed by EOF exported %d lane failures", got)
	}
}

func TestReadLaneTreatsEOFAfterRemoteResetAsProtocolTeardown(t *testing.T) {
	inner, application := net.Pipe()
	defer application.Close()
	registry := metrics.New()
	outer, peer := net.Pipe()
	defer peer.Close()
	flow := newMultipathFlow(context.Background(), inner, [16]byte{1}, 7, 1024,
		protocol.FlagAckUp, protocol.FlagAckDown, nil, registry)
	lane := &mpLane{id: 0, fc: newFrameConn(outer)}
	flow.lanes[0] = lane
	resetFrame := protocol.Frame{Header: protocol.Header{
		Version: protocol.Version, Type: protocol.TypeReset,
		SessionID: [16]byte{1}, FlowID: 7,
	}}
	readerDone := make(chan struct{})
	go func() {
		flow.readLane(lane)
		close(readerDone)
	}()
	writeDone := make(chan error, 1)
	go func() {
		writeDone <- protocol.WriteFrame(peer, resetFrame)
		_ = peer.Close()
	}()

	select {
	case event := <-flow.events:
		if event.frame.Header.Type != protocol.TypeReset {
			t.Fatalf("reader delivered frame type %d, want RESET", event.frame.Header.Type)
		}
	case <-time.After(time.Second):
		t.Fatal("timed out waiting for peer RESET")
	}
	if err := <-writeDone; err != nil {
		t.Fatal(err)
	}
	select {
	case <-readerDone:
	case <-time.After(time.Second):
		t.Fatal("lane reader did not return after peer EOF")
	}
	if lane.closed.Load() {
		t.Fatal("protocol reset was misclassified as a physical lane failure")
	}
	if got := registry.Snapshot().LaneFailures; got != 0 {
		t.Fatalf("RESET followed by EOF exported %d lane failures", got)
	}
}

func TestReadLaneRetiresUnexpectedEOFImmediately(t *testing.T) {
	inner, application := net.Pipe()
	defer application.Close()
	registry := metrics.New()
	outer, peer := net.Pipe()
	flow := newMultipathFlow(context.Background(), inner, [16]byte{1}, 7, 1024,
		protocol.FlagAckUp, protocol.FlagAckDown, nil, registry)
	lane := &mpLane{id: 0, fc: newFrameConn(outer)}
	flow.lanes[0] = lane
	readerDone := make(chan struct{})
	go func() {
		flow.readLane(lane)
		close(readerDone)
	}()
	_ = peer.Close()

	select {
	case <-readerDone:
	case <-time.After(time.Second):
		t.Fatal("lane reader did not return after unexpected EOF")
	}
	if !lane.closed.Load() {
		t.Fatal("unexpected EOF left the lane schedulable")
	}
	if got := registry.Snapshot().LaneFailures; got != 1 {
		t.Fatalf("unexpected EOF exported %d lane failures, want one", got)
	}
}

func TestProvenCompleteFlowDoesNotWaitForLaneReplacementForFinalACK(t *testing.T) {
	flow := &multipathFlow{
		ctx: context.Background(), done: make(chan struct{}),
		lanes: make(map[uint64]*mpLane),
	}
	flow.finSent.Store(true)

	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Millisecond)
	defer cancel()
	started := time.Now()
	err := flow.acknowledgeRemoteFIN(ctx, 0, false)
	if err != nil {
		t.Fatalf("proven-complete final ACK cleanup returned error: %v", err)
	}
	if elapsed := time.Since(started); elapsed > time.Second {
		t.Fatalf("final ACK cleanup took %s; lane replacement was not bounded", elapsed)
	}
}

// Isolation costs a bulk flow its warmed-up path, so it is paid only while
// another flow is actually using the pooled control connection. A flow alone
// on the pool keeps its data on the control lane; the moment a second flow
// arrives, the next selection moves the data plane off it -- and it is a move,
// not a widening: one lane before and one after.
func TestTheDataPlaneMovesOffTheControlLaneWhenThePoolIsShared(t *testing.T) {
	var shared atomic.Bool
	flow := &multipathFlow{
		done: make(chan struct{}),
		lanes: map[uint64]*mpLane{
			0: {id: 0},
			1: {id: 1},
		},
		reserveControlLane: true,
		controlLaneShared:  shared.Load,
	}

	candidates, err := flow.laneCandidates(true)
	if err != nil {
		t.Fatal(err)
	}
	if len(candidates) != 1 || candidates[0].id != 0 {
		t.Fatalf("a flow alone on the pool put data on %d lanes starting at %d, want only the control lane",
			len(candidates), candidates[0].id)
	}

	shared.Store(true)
	candidates, err = flow.laneCandidates(true)
	if err != nil {
		t.Fatal(err)
	}
	if len(candidates) != 1 || candidates[0].id != 1 {
		t.Fatalf("a shared pool put data on %d lanes starting at %d, want only the isolated lane",
			len(candidates), candidates[0].id)
	}
}

func TestInboundDeliveryBlockedByAFullQueueStopsWithTheFlow(t *testing.T) {
	flow := &multipathFlow{
		ctx:    context.Background(),
		done:   make(chan struct{}),
		events: make(chan inboundEvent, 1),
	}
	flow.events <- inboundEvent{}

	started := make(chan struct{})
	result := make(chan bool, 1)
	go func() {
		close(started)
		result <- flow.deliverInbound(&mpLane{id: 1}, protocol.Frame{})
	}()
	<-started
	flow.signalDone()

	select {
	case delivered := <-result:
		if delivered {
			t.Fatal("frame was delivered through a full queue")
		}
	case <-time.After(time.Second):
		t.Fatal("inbound reader remained blocked after flow teardown")
	}
}
