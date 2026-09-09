package pep

import (
	"context"
	"errors"
	"io"
	"log/slog"
	"net"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/metrics"
	"github.com/bojieli/queqiao/internal/protocol"
)

func newStallTestFlow(t *testing.T, registry *metrics.Registry) *multipathFlow {
	t.Helper()
	inner, peer := net.Pipe()
	t.Cleanup(func() { _ = inner.Close(); _ = peer.Close() })
	return newMultipathFlow(context.Background(), inner, [16]byte{4}, 7, defaultChunkSize, protocol.FlagAckUp, protocol.FlagAckDown, nil, registry)
}

// The threshold is three minimum round trips, clamped: a fast path never
// waits less than the floor, a slow one never more than the cap, and a flow
// with no RTT sample yet gets the conservative default.
func TestStallThresholdClamp(t *testing.T) {
	flow := newStallTestFlow(t, nil)
	if got := flow.stallThreshold(); got != stallThresholdDefault {
		t.Fatalf("no RTT sample: threshold = %s, want %s", got, stallThresholdDefault)
	}
	for _, test := range []struct {
		rtt  time.Duration
		want time.Duration
	}{
		{50 * time.Millisecond, stallThresholdFloor},
		{83 * time.Millisecond, stallThresholdFloor},
		{200 * time.Millisecond, 600 * time.Millisecond},
		{500 * time.Millisecond, 1500 * time.Millisecond},
		{time.Second, stallThresholdCap},
		{5 * time.Second, stallThresholdCap},
	} {
		flow.minRTTNS.Store(test.rtt.Nanoseconds())
		if got := flow.stallThreshold(); got != test.want {
			t.Fatalf("minRTT %s: threshold = %s, want %s", test.rtt, got, test.want)
		}
	}
	// A controller that reports no minimum still leaves the smoothed reading.
	flow.minRTTNS.Store(0)
	flow.currentRTTNS.Store((200 * time.Millisecond).Nanoseconds())
	if got := flow.stallThreshold(); got != 600*time.Millisecond {
		t.Fatalf("smoothed fallback: threshold = %s, want 600ms", got)
	}
	// The test override wins over every sample.
	flow.stallGrace = 10 * time.Millisecond
	if got := flow.stallThreshold(); got != 10*time.Millisecond {
		t.Fatalf("override: threshold = %s, want 10ms", got)
	}
}

// The gate is strict: nothing pending never stalls, and a stall is measured
// from when the work appeared (or last progressed), never from before it.
func TestScanStallGating(t *testing.T) {
	threshold := 100 * time.Millisecond
	now := time.Now()
	var since time.Time
	if scanStall(false, 0, now, threshold, &since) {
		t.Fatal("an idle flow stalled")
	}
	// First observation of pending work starts the clock rather than firing,
	// however old the last progress is.
	stale := now.Add(-time.Hour).UnixNano()
	if scanStall(true, stale, now, threshold, &since) {
		t.Fatal("work pending for one scan stalled on an ancient clock")
	}
	// Progress newer than the clock restarts it.
	if scanStall(true, now.Add(10*time.Millisecond).UnixNano(), now.Add(20*time.Millisecond), threshold, &since) {
		t.Fatal("work that just progressed stalled")
	}
	if !scanStall(true, 0, now.Add(20*time.Millisecond+threshold), threshold, &since) {
		t.Fatal("work pending a full threshold without progress did not stall")
	}
	// Going idle resets the clock, so the next burst gets a full threshold.
	scanStall(false, 0, now, threshold, &since)
	if scanStall(true, 0, now.Add(50*time.Millisecond), threshold, &since) {
		t.Fatal("fresh work inherited the previous burst's clock")
	}
}

// The response gate opens when the application sent something the peer has
// not answered, and closes on any downstream payload or either close. A flow
// whose last send was answered is idle, not waiting.
func TestResponseOutstandingGating(t *testing.T) {
	flow := newStallTestFlow(t, nil)
	if flow.responseOutstanding() {
		t.Fatal("a flow that never sent is waiting on a response")
	}
	flow.observe(64, true)
	flow.bytesUp.Add(64)
	if !flow.responseOutstanding() {
		t.Fatal("an unanswered request did not open the response gate")
	}
	flow.observe(128, false)
	flow.bytesDown.Add(128)
	if flow.responseOutstanding() {
		t.Fatal("an answered request kept the response gate open")
	}
	flow.observe(64, true)
	flow.bytesUp.Add(64)
	flow.remoteFinSeen.Store(true)
	if flow.responseOutstanding() {
		t.Fatal("a flow that saw the peer's FIN is still waiting")
	}
}

// Demotion is not death: a suspected lane is passed over for new writes while
// a healthier lane exists, keeps its place in the healthy set, and is fully
// eligible again the moment it is the only thing left.
func TestSuspectedLaneIsDemotedNotKilled(t *testing.T) {
	flow := newStallTestFlow(t, nil)
	flow.reserveControlLane = true
	controlLocal, controlRemote := net.Pipe()
	dataLocal, dataRemote := net.Pipe()
	t.Cleanup(func() {
		_ = controlLocal.Close()
		_ = controlRemote.Close()
		_ = dataLocal.Close()
		_ = dataRemote.Close()
	})
	control := &mpLane{id: 0, kind: TransportQUIC, fc: newFrameConn(controlLocal), control: true}
	data := &mpLane{id: 1, kind: TransportQUIC, fc: newFrameConn(dataLocal)}
	if err := flow.addLane(control); err != nil {
		t.Fatal(err)
	}
	if err := flow.addLane(data); err != nil {
		t.Fatal(err)
	}
	candidates, err := flow.laneCandidates(true)
	if err != nil || len(candidates) != 1 || candidates[0] != data {
		t.Fatalf("data candidates before stall = %v, %v", candidates, err)
	}
	if spare := flow.suspectDataLanes(); !spare {
		t.Fatal("demoting the data lane found no warm spare in the control lane")
	}
	if data.closed.Load() {
		t.Fatal("the watchdog closed a suspected lane")
	}
	if len(flow.healthyLanes()) != 2 {
		t.Fatal("a suspected lane left the healthy set")
	}
	candidates, err = flow.laneCandidates(true)
	if err != nil || len(candidates) != 1 || candidates[0] != control {
		t.Fatalf("data candidates after demotion = %v, %v, want the control lane", candidates, err)
	}
	// With every healthy lane suspected there is nothing healthier, and the
	// set is used exactly as before.
	control.suspected.Store(true)
	candidates, err = flow.laneCandidates(true)
	if err != nil || len(candidates) != 1 || candidates[0] != data {
		t.Fatalf("all-suspected candidates = %v, %v, want the data lane again", candidates, err)
	}
	// An acknowledgement carrying new delivery information clears the mark.
	data.suspected.Store(false)
	control.suspected.Store(false)
}

// The watchdog fires once per episode, demotes the data lane, and asks the
// lane manager for a rescue; an idle flow with the same timing never fires.
func TestStallWatchdogDetectsPendingWorkWithoutProgress(t *testing.T) {
	registry := metrics.New()
	flow := newStallTestFlow(t, registry)
	flow.stallScan = 5 * time.Millisecond
	flow.stallGrace = 20 * time.Millisecond
	stop := make(chan struct{})
	t.Cleanup(func() { close(stop) })
	go flow.stallWatchdog(stop)

	// Nothing pending: the scan runs and stays silent.
	select {
	case <-flow.stallSignals():
		t.Fatal("an idle flow raised a stall")
	case <-time.After(100 * time.Millisecond):
	}

	flow.noteSent(0, 512)
	select {
	case <-flow.stallSignals():
	case <-time.After(2 * time.Second):
		t.Fatal("pending work with no progress raised no stall")
	}
	if got := registry.Snapshot().FlowStallsDetected; got != 1 {
		t.Fatalf("stall detections = %d, want 1", got)
	}

	// Acknowledging the work is progress; the episode ends and a quiet flow
	// with nothing outstanding does not re-fire.
	if err := flow.acknowledgeReplay(512, false); err != nil {
		t.Fatal(err)
	}
	time.Sleep(50 * time.Millisecond)
	if got := registry.Snapshot().FlowStallsDetected; got != 1 {
		t.Fatalf("stall detections after progress = %d, want still 1", got)
	}
}

// A warm spare is counted when the demotion leaves a non-suspected healthy
// lane, and not when the stalled lane was the only one.
func TestStallWatchdogCountsTheWarmSpare(t *testing.T) {
	registry := metrics.New()
	flow := newStallTestFlow(t, registry)
	flow.reserveControlLane = true
	controlLocal, controlRemote := net.Pipe()
	dataLocal, dataRemote := net.Pipe()
	t.Cleanup(func() {
		_ = controlLocal.Close()
		_ = controlRemote.Close()
		_ = dataLocal.Close()
		_ = dataRemote.Close()
	})
	if err := flow.addLane(&mpLane{id: 0, kind: TransportQUIC, fc: newFrameConn(controlLocal), control: true}); err != nil {
		t.Fatal(err)
	}
	if err := flow.addLane(&mpLane{id: 1, kind: TransportQUIC, fc: newFrameConn(dataLocal)}); err != nil {
		t.Fatal(err)
	}
	flow.noteSent(0, 512)
	flow.stallScan = 5 * time.Millisecond
	flow.stallGrace = 20 * time.Millisecond
	stop := make(chan struct{})
	t.Cleanup(func() { close(stop) })
	go flow.stallWatchdog(stop)
	select {
	case <-flow.stallSignals():
	case <-time.After(2 * time.Second):
		t.Fatal("no stall signal")
	}
	snapshot := registry.Snapshot()
	if snapshot.FlowStallsDetected != 1 || snapshot.StallSpareAttaches != 1 {
		t.Fatalf("stalls = %d, spare attaches = %d, want 1 and 1", snapshot.FlowStallsDetected, snapshot.StallSpareAttaches)
	}
}

func rescueTestLane(t *testing.T, id uint64) (*mpLane, net.Conn) {
	t.Helper()
	local, remote := net.Pipe()
	t.Cleanup(func() { _ = local.Close(); _ = remote.Close() })
	return &mpLane{id: id, kind: TransportQUIC, fc: newFrameConn(local)}, remote
}

// The first completed JOIN wins; every losing attempt is cancelled, and a
// loser that finishes anyway has its lane closed rather than installed. The
// attempts here share nothing -- the analogue of several dials on the same
// single port, where independence is the whole value.
func TestParallelRescueFirstWinsAndLosersAreCancelled(t *testing.T) {
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	registry := metrics.New()
	client := &Client{cfg: ClientConfig{Logger: logger}, metrics: registry}
	flow := newGraceTestFlow(t)

	loserStarted := make(chan struct{})
	loserLane, loserRemote := rescueTestLane(t, 1)
	winnerLane, _ := rescueTestLane(t, 2)
	attempts := []rescueAttempt{
		func(ctx context.Context) (*mpLane, error) {
			close(loserStarted)
			<-ctx.Done()
			// A dial cancelled mid-handshake returns its context's error.
			return nil, ctx.Err()
		},
		func(ctx context.Context) (*mpLane, error) {
			<-loserStarted
			return winnerLane, nil
		},
		func(ctx context.Context) (*mpLane, error) {
			// A loser that completes its JOIN before the cancellation
			// reaches it must have its lane closed, not leaked.
			<-loserStarted
			time.Sleep(20 * time.Millisecond)
			return loserLane, nil
		},
	}
	lane, winner, err := client.raceRescueAttempts(context.Background(), flow, attempts)
	if err != nil {
		t.Fatal(err)
	}
	if winner != 1 || lane != winnerLane {
		t.Fatalf("winner = %d (%v), want attempt 1", winner, lane)
	}
	snapshot := registry.Snapshot()
	if snapshot.LaneRescueAttempts != 3 {
		t.Fatalf("rescue attempts = %d, want 3", snapshot.LaneRescueAttempts)
	}
	if snapshot.LaneRescueWins[1] != 1 || snapshot.LaneRescueWins[0] != 0 || snapshot.LaneRescueWins[2] != 0 {
		t.Fatalf("rescue wins = %v, want attempt 1 only", snapshot.LaneRescueWins)
	}
	// The late loser's lane is closed once its attempt unwinds.
	if err := loserRemote.SetReadDeadline(time.Now().Add(2 * time.Second)); err != nil {
		t.Fatal(err)
	}
	if _, err := loserRemote.Read(make([]byte, 1)); err == nil {
		t.Fatal("the losing lane's connection stayed open")
	}
}

// A refusal is the peer's permanent answer about the session: it ends the
// round immediately rather than being outvoted by slower attempts.
func TestParallelRescueRefusalEndsTheRound(t *testing.T) {
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	client := &Client{cfg: ClientConfig{Logger: logger}, metrics: metrics.New()}
	flow := newGraceTestFlow(t)
	slow := make(chan struct{})
	t.Cleanup(func() { close(slow) })
	attempts := []rescueAttempt{
		func(ctx context.Context) (*mpLane, error) { return nil, errLaneJoinRejected },
		func(ctx context.Context) (*mpLane, error) {
			select {
			case <-slow:
				lane, _ := rescueTestLane(t, 9)
				return lane, nil
			case <-ctx.Done():
				return nil, ctx.Err()
			}
		},
	}
	start := time.Now()
	if _, _, err := client.raceRescueAttempts(context.Background(), flow, attempts); !errors.Is(err, errLaneJoinRejected) {
		t.Fatalf("err = %v, want %v", err, errLaneJoinRejected)
	}
	if elapsed := time.Since(start); elapsed > time.Second {
		t.Fatalf("the round waited %s for attempts a refusal already answered", elapsed)
	}
}

// When every attempt fails, the round reports the first failure rather than
// installing anything.
func TestParallelRescueAllAttemptsFail(t *testing.T) {
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	client := &Client{cfg: ClientConfig{Logger: logger}, metrics: metrics.New()}
	flow := newGraceTestFlow(t)
	first := errors.New("dial refused")
	attempts := []rescueAttempt{
		func(ctx context.Context) (*mpLane, error) { return nil, first },
		func(ctx context.Context) (*mpLane, error) {
			time.Sleep(50 * time.Millisecond)
			return nil, errors.New("dial timeout")
		},
	}
	if _, _, err := client.raceRescueAttempts(context.Background(), flow, attempts); !errors.Is(err, first) {
		t.Fatalf("err = %v, want the first failure", err)
	}
	if got := client.metrics.Snapshot().LaneRescueAttempts; got != 2 {
		t.Fatalf("rescue attempts = %d, want 2", got)
	}
}
