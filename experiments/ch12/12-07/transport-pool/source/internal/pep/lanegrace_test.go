package pep

import (
	"context"
	"errors"
	"log/slog"
	"net"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/metrics"
	"github.com/bojieli/queqiao/internal/protocol"
)

// The replacement grace covers the time a replacement lane needs to arrive.
// The flow used to end it only on an explicit refusal, which arrives when a
// rescue handshake completes -- and on a path lossy enough to have killed
// every lane, the rescue handshake is usually what fails instead. So the
// answer often never came and the application waited in silence: 25s on
// average and 573s at worst in the reported incident.
func TestWaitEndsWhenNoReplacementWillBeAttempted(t *testing.T) {
	flow := newGraceTestFlow(t)
	waits := make(chan error, 1)
	go func() { waits <- flow.waitForHealthyLane(context.Background(), laneReplacementWait) }()

	select {
	case err := <-waits:
		t.Fatalf("the wait ended with no evidence at all: %v", err)
	case <-time.After(150 * time.Millisecond):
	}

	flow.noteReplacementAbandoned()
	select {
	case err := <-waits:
		if !errors.Is(err, errReplacementAbandoned) {
			t.Fatalf("wait error = %v, want %v", err, errReplacementAbandoned)
		}
	case <-time.After(2 * time.Second):
		t.Fatalf("the flow waited out its grace after replacement was abandoned")
	}
}

// A flow that already knows nothing is coming must not enter the wait at all.
func TestWaitIsNotEnteredOnceReplacementIsAbandoned(t *testing.T) {
	flow := newGraceTestFlow(t)
	flow.noteReplacementAbandoned()
	start := time.Now()
	if err := flow.waitForHealthyLane(context.Background(), laneReplacementWait); !errors.Is(err, errReplacementAbandoned) {
		t.Fatalf("wait error = %v, want %v", err, errReplacementAbandoned)
	}
	if elapsed := time.Since(start); elapsed > time.Second {
		t.Fatalf("the wait took %s to report what it already knew", elapsed)
	}
}

// A healthy lane is still the answer, whatever the manager has stopped doing.
func TestAbandonedReplacementDoesNotFailAFlowWithALane(t *testing.T) {
	flow := newGraceTestFlow(t)
	local, remote := net.Pipe()
	t.Cleanup(func() { _ = local.Close(); _ = remote.Close() })
	flow.lanes[1] = &mpLane{id: 1, kind: TransportQUIC, fc: newFrameConn(local)}
	flow.noteReplacementAbandoned()
	if err := flow.waitForHealthyLane(context.Background(), laneReplacementWait); err != nil {
		t.Fatalf("a flow with a healthy lane failed: %v", err)
	}
}

// The wait is a client-side conclusion drawn from the client's own behaviour.
// A server flow never draws it: the rescue is still somebody's to send, and
// its grace is what gives the peer time to send it.
func TestTheLaneManagerIsWhatAbandonsReplacement(t *testing.T) {
	flow := newGraceTestFlow(t)
	if flow.replacementAbandoned.Load() {
		t.Fatal("a fresh flow starts with its replacement grace already spent")
	}
	client := &Client{cfg: ClientConfig{Logger: slog.New(slog.NewTextHandler(discardWriter{}, nil))}}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	client.manageQUICLanes(ctx, flow, flow.sessionID, flow.flowID)
	if !flow.replacementAbandoned.Load() {
		t.Fatal("the lane manager returned without ending the flow's replacement grace")
	}
}

type discardWriter struct{}

func (discardWriter) Write(p []byte) (int, error) { return len(p), nil }

func newGraceTestFlow(t *testing.T) *multipathFlow {
	t.Helper()
	inner, peer := net.Pipe()
	t.Cleanup(func() { _ = inner.Close(); _ = peer.Close() })
	return newMultipathFlow(context.Background(), inner, [16]byte{2}, 3, defaultChunkSize, protocol.FlagAckUp, protocol.FlagAckDown, nil, nil)
}

// A flow that fails with "lane replacement timeout" used to say only that it
// gave up. The live gateway produced 521 of those in two hours, all of them
// ordinary small exchanges that had already moved a few kilobytes, and the
// record could not say whether a replacement lane had ever been offered or how
// many graces the flow burned before failing. That is the difference between a
// pool that will not rebuild and a path that will not carry a handshake, and
// neither the flow's own log nor the gateway's could distinguish them. See
// issue #53.
func TestAFlowRecordsWhatItsLaneReplacementsDid(t *testing.T) {
	flow := newGraceTestFlow(t)

	if waits, timeouts, joined, waited := flow.replacementDiagnostics(); waits != 0 || timeouts != 0 || joined != 0 || waited != 0 {
		t.Fatalf("a flow that has not waited reports waits=%d timeouts=%d joined=%d waited=%s",
			waits, timeouts, joined, waited)
	}

	// A grace that runs out is the case the incident was made of.
	const grace = 200 * time.Millisecond
	if err := flow.waitForHealthyLane(context.Background(), grace); err == nil {
		t.Fatal("the wait succeeded with no healthy lane")
	}
	waits, timeouts, _, waited := flow.replacementDiagnostics()
	if waits != 1 || timeouts != 1 {
		t.Fatalf("one exhausted grace recorded waits=%d timeouts=%d, want 1 and 1", waits, timeouts)
	}
	if waited < grace {
		t.Fatalf("the flow waited %s but recorded %s", grace, waited)
	}

	// A second waiter for the same missing lane has to be visible as a second
	// waiter -- the counters are how a gateway record separates one call site
	// giving up from four of them -- but it must not buy the flow a second
	// grace. The observed durations clustered at roughly twice
	// laneReplacementWait, which is what that used to cost.
	if err := flow.waitForHealthyLane(context.Background(), grace); err == nil {
		t.Fatal("the second wait succeeded with no healthy lane")
	}
	waits, timeouts, _, twice := flow.replacementDiagnostics()
	if waits != 2 || timeouts != 2 {
		t.Fatalf("two waiters recorded waits=%d timeouts=%d, want 2 and 2", waits, timeouts)
	}
	if twice >= 2*grace {
		t.Fatalf("two waiters on one outage spent %s, at least two graces of %s", twice, grace)
	}

	// And an exit that is not a timeout must not be counted as one, or the
	// field cannot separate "nothing came" from "we stopped waiting".
	flow.noteReplacementAbandoned()
	if err := flow.waitForHealthyLane(context.Background(), grace); !errors.Is(err, errReplacementAbandoned) {
		t.Fatalf("wait error = %v, want %v", err, errReplacementAbandoned)
	}
	if _, timeouts, _, _ := flow.replacementDiagnostics(); timeouts != 2 {
		t.Fatalf("abandoning replacement counted as a timeout: timeouts=%d, want 2", timeouts)
	}
}

// The grace is what a flow is prepared to wait for a lane that is not there.
// It was being spent per waiter rather than per outage: run, the frame and
// control writers and the acknowledgement loop all wait for the same missing
// lane, so a flow that was never going to be rescued paid the whole grace
// once for each of them. The live gateway showed it as failures clustered at
// 76-106 s against a 45 s grace -- two of them, for flows that had finished
// their work in the first second. See issue #53.
func TestOneOutageSpendsOneGraceHoweverManyWaitersItHas(t *testing.T) {
	flow := newGraceTestFlow(t)
	const grace = 300 * time.Millisecond
	const concurrent = 3

	// Waiters that are already blocked when the grace runs out share it: a
	// lane dying with writes in flight puts several of them here at once.
	started := time.Now()
	errs := make(chan error, concurrent)
	for i := 0; i < concurrent; i++ {
		go func() { errs <- flow.waitForHealthyLane(context.Background(), grace) }()
	}
	for i := 0; i < concurrent; i++ {
		select {
		case err := <-errs:
			if !errors.Is(err, errLaneReplacementTimeout) {
				t.Fatalf("wait error = %v, want %v", err, errLaneReplacementTimeout)
			}
		case <-time.After(5 * time.Second):
			t.Fatal("a waiter never returned")
		}
	}

	// And a waiter that arrives afterwards is told at once. This is the one
	// that cost the flows in the incident: run waits for the lane only after
	// the failure reaches it, which on a flow whose writer was already blocked
	// is one whole grace after the outage began. It used to start a second.
	arrived := time.Now()
	if err := flow.waitForHealthyLane(context.Background(), grace); !errors.Is(err, errLaneReplacementTimeout) {
		t.Fatalf("wait error = %v, want %v", err, errLaneReplacementTimeout)
	}
	if late := time.Since(arrived); late > grace/2 {
		t.Fatalf("a waiter arriving after the grace was spent waited %s of a fresh %s", late, grace)
	}
	if elapsed := time.Since(started); elapsed >= 2*grace {
		t.Fatalf("one outage took %s, at least two graces of %s", elapsed, grace)
	}

	// Every waiter still has to be counted, or the record cannot say how many
	// call sites were stuck on the same absent lane.
	const waiters = concurrent + 1
	if waits, timeouts, _, _ := flow.replacementDiagnostics(); waits != waiters || timeouts != waiters {
		t.Fatalf("recorded waits=%d timeouts=%d, want %d and %d", waits, timeouts, waiters, waiters)
	}
}

// Spending the grace once per outage must not mean spending it once per flow.
// A long-lived flow that is genuinely being rescued loses a lane, gets one
// back, and may lose another an hour later; that second outage is a new one
// and is owed the whole grace.
func TestANewOutageIsOwedAWholeGrace(t *testing.T) {
	flow := newGraceTestFlow(t)
	const grace = 200 * time.Millisecond

	if err := flow.waitForHealthyLane(context.Background(), grace); !errors.Is(err, errLaneReplacementTimeout) {
		t.Fatalf("wait error = %v, want %v", err, errLaneReplacementTimeout)
	}

	// A lane arriving is what ends an outage, and it ends it in startLane --
	// the one point a lane starts carrying traffic -- rather than wherever a
	// waiter next happens to look.
	replacement := &mpLane{id: 7, kind: TransportQUIC, fc: newFrameConn(gracePipe(t))}
	if err := flow.addLane(replacement); err != nil {
		t.Fatalf("adding a replacement lane: %v", err)
	}
	if flow.replacementDeadline.Load() != 0 {
		t.Fatal("a replacement lane arrived and the spent outage was still holding its deadline")
	}

	flow.failLane(replacement, errors.New("lane died again"))
	started := time.Now()
	if err := flow.waitForHealthyLane(context.Background(), grace); !errors.Is(err, errLaneReplacementTimeout) {
		t.Fatalf("wait error = %v, want %v", err, errLaneReplacementTimeout)
	}
	if elapsed := time.Since(started); elapsed < grace {
		t.Fatalf("the second outage waited %s of its %s grace", elapsed, grace)
	}
}

func gracePipe(t *testing.T) net.Conn {
	t.Helper()
	local, remote := net.Pipe()
	t.Cleanup(func() { _ = local.Close(); _ = remote.Close() })
	return local
}

// A deadline can outlive the outage it belonged to. A waiter that finds no
// lane, and whose lane arrives before it records its deadline, writes that
// deadline after the arriving lane has already cleared the outage, and nothing
// is then left to remove it. Read as current, it would expire the flow's next
// outage before that outage began -- failing in an instant a flow that had a
// full grace coming to it.
func TestAStaleDeadlineDoesNotDenyTheNextOutageItsGrace(t *testing.T) {
	flow := newGraceTestFlow(t)
	const grace = 200 * time.Millisecond
	flow.replacementDeadline.Store(time.Now().Add(-time.Hour).UnixNano())

	started := time.Now()
	if err := flow.waitForHealthyLane(context.Background(), grace); !errors.Is(err, errLaneReplacementTimeout) {
		t.Fatalf("wait error = %v, want %v", err, errLaneReplacementTimeout)
	}
	if elapsed := time.Since(started); elapsed < grace {
		t.Fatalf("an outage inheriting a stale deadline waited %s of its %s grace", elapsed, grace)
	}
}

// The gateway's failing flows say a replacement never arrived: 84% of its
// lane-replacement-timeout failures ended with no replacement lane ever
// admitted. The record could not say why, and the two reasons need different
// fixes -- a client pool that will not rebuild opens nothing, and a path that
// will not carry a handshake opens attempts that never complete. A dial that
// fails never reaches addLane, so `lanes_joined` reads the same either way.
// See issue #53.
func TestAFlowRecordsWhetherAReplacementWasEvenAttempted(t *testing.T) {
	fields := func(f *multipathFlow) map[string]any {
		raw := f.replacementLogFields()
		out := map[string]any{}
		for i := 0; i+1 < len(raw); i += 2 {
			out[raw[i].(string)] = raw[i+1]
		}
		return out
	}

	// Nothing tried: the pool never rebuilt.
	quiet := newGraceTestFlow(t)
	got := fields(quiet)
	if got["lane_replacement_attempts"] != uint64(0) || got["lane_replacement_failures"] != uint64(0) {
		t.Fatalf("a flow that attempted nothing reports attempts=%v failures=%v",
			got["lane_replacement_attempts"], got["lane_replacement_failures"])
	}

	// Tried and could not finish a handshake: the path will not carry one.
	refused := newGraceTestFlow(t)
	for i := 0; i < 3; i++ {
		refused.noteReplacementAttempt()
		refused.noteReplacementFailure()
	}
	got = fields(refused)
	if got["lane_replacement_attempts"] != uint64(3) || got["lane_replacement_failures"] != uint64(3) {
		t.Fatalf("three failed dials reported attempts=%v failures=%v, want 3 and 3",
			got["lane_replacement_attempts"], got["lane_replacement_failures"])
	}

	// Both flows are indistinguishable by the fields that existed before: they
	// waited for nothing and nothing joined. That is the gap being closed.
	if fields(quiet)["lanes_joined"] != fields(refused)["lanes_joined"] {
		t.Fatal("the test no longer exercises the case the attempt counts were added for")
	}

	// A dial still outstanding is not yet a failure, or "nothing came back
	// yet" would read as "the path refused it".
	pending := newGraceTestFlow(t)
	pending.noteReplacementAttempt()
	got = fields(pending)
	if got["lane_replacement_attempts"] != uint64(1) || got["lane_replacement_failures"] != uint64(0) {
		t.Fatalf("an outstanding dial reported attempts=%v failures=%v, want 1 and 0",
			got["lane_replacement_attempts"], got["lane_replacement_failures"])
	}
}

// A rescue JOIN arriving mid-grace is the peer's recovery proving itself
// alive. The grace restarts from that evidence rather than expiring
// underneath the handshake it was waiting for; a flow not in an outage has
// nothing to extend, and a deadline a whole grace in the past is an ended
// outage's residue, not evidence to build on.
func TestRescueEvidenceRestartsTheReplacementGrace(t *testing.T) {
	flow := newGraceTestFlow(t)
	now := time.Now()
	if flow.extendReplacementOutage(now, laneReplacementWait) {
		t.Fatal("a flow not in an outage had its grace extended")
	}
	if remaining := flow.replacementBudget(now, laneReplacementWait); remaining != laneReplacementWait {
		t.Fatalf("opening an outage left %s, want the whole grace", remaining)
	}
	before := flow.replacementDeadline.Load()
	later := now.Add(time.Second)
	if !flow.extendReplacementOutage(later, laneReplacementWait) {
		t.Fatal("a live outage refused its extension")
	}
	if got, want := flow.replacementDeadline.Load(), later.Add(laneReplacementWait).UnixNano(); got != want {
		t.Fatalf("extended deadline = %d, want %d", got, want)
	}
	if flow.replacementDeadline.Load() <= before {
		t.Fatal("the extension did not move the deadline forward")
	}
	flow.replacementDeadline.Store(now.Add(-2 * laneReplacementWait).UnixNano())
	if flow.extendReplacementOutage(now, laneReplacementWait) {
		t.Fatal("a stale deadline was revived by rescue evidence")
	}
}

// The gateway observes the rescue at JOIN validation time: a JOIN naming a
// live session currently waiting out an outage restarts that outage's grace
// and is counted.
func TestLaneJoinDuringGraceExtendsTheBudget(t *testing.T) {
	owner := identity.Principal{ProviderID: "provider", AccountID: "account", DeviceID: "owner"}
	registry := metrics.New()
	server := &Server{
		cfg:      ServerConfig{Logger: slog.New(slog.NewTextHandler(discardWriter{}, nil))},
		sessions: map[[16]byte]*serverFlow{},
		metrics:  registry,
	}
	flow := newGraceTestFlow(t)
	server.sessions[flow.sessionID] = newServerFlow(flow, owner, TransportTCP, 1)
	now := time.Now()
	if remaining := flow.replacementBudget(now, laneReplacementWait); remaining != laneReplacementWait {
		t.Fatalf("opening an outage left %s, want the whole grace", remaining)
	}

	local, remote := net.Pipe()
	t.Cleanup(func() { _ = local.Close(); _ = remote.Close() })
	ctx, cancel := context.WithCancel(context.Background())
	t.Cleanup(cancel)
	request := protocol.Frame{Header: protocol.Header{
		Version: protocol.Version, Type: protocol.TypeJoin, SessionID: flow.sessionID,
		FlowID: flow.flowID, Class: protocol.ClassBulk,
	}}
	go server.handleLaneJoinOpen(ctx, local, newFrameConn(local), owner, flow.sessionID, 1, request)
	response, err := newFrameConn(remote).Read()
	if err != nil {
		t.Fatal(err)
	}
	if response.Header.Type != protocol.TypeOpenOK {
		t.Fatalf("response = %d, want OPEN_OK", response.Header.Type)
	}
	if got := registry.Snapshot().LaneGraceExtensions; got != 1 {
		t.Fatalf("grace extensions = %d, want 1", got)
	}
	// The deadline itself goes away once the admitted lane is activated,
	// which is the extension working as intended: what it bought was the time
	// between this JOIN becoming observable and its admission completing.
	// Activation trails the acknowledgement by a scheduling beat, so wait
	// for it.
	for deadline := time.Now().Add(2 * time.Second); ; {
		if flow.replacementDeadline.Load() == 0 {
			break
		}
		if time.Now().After(deadline) {
			t.Fatal("the admitted lane never ended the outage")
		}
		time.Sleep(5 * time.Millisecond)
	}
}
