package pep

import (
	"context"
	"crypto/x509"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/protocol"
)

// isolationLane builds a lane with a usable frame connection, which addLane
// requires.
func isolationLane(t *testing.T, id uint64) *mpLane {
	return isolationLaneKind(t, id, TransportQUIC)
}

func isolationLaneKind(t *testing.T, id uint64, kind TransportKind) *mpLane {
	t.Helper()
	local, remote := net.Pipe()
	t.Cleanup(func() { _ = local.Close(); _ = remote.Close() })
	return &mpLane{id: id, kind: kind, fc: newFrameConn(local)}
}

func TestServerTCPHandoffRetiresQUICAndExpandsItsAdmissionCeiling(t *testing.T) {
	flow := newIsolationTestFlow(t, false)
	session := newServerFlow(flow, identity.Principal{}, TransportQUIC, 8)
	if err := session.addLane(isolationLaneKind(t, 0, TransportQUIC)); err != nil {
		t.Fatal(err)
	}
	if err := session.addLane(isolationLaneKind(t, 1, TransportTCP)); err != nil {
		t.Fatalf("TCP handoff refused: %v", err)
	}
	if !session.tcpMode || session.maxLanes != 8 || !flow.tcpStriping.Load() {
		t.Fatalf("handoff state tcp=%t max=%d striping=%t", session.tcpMode, session.maxLanes, flow.tcpStriping.Load())
	}
	lanes := flow.healthyLanes()
	if len(lanes) != 1 || lanes[0].kind != TransportTCP {
		t.Fatalf("handoff retained %+v, want only the TCP rescue", lanes)
	}
	for id := uint64(2); id <= 8; id++ {
		if err := session.addLane(isolationLaneKind(t, id, TransportTCP)); err != nil {
			t.Fatalf("TCP lane %d refused: %v", id, err)
		}
	}
	if got := flow.laneCount(); got != 8 {
		t.Fatalf("TCP lane count = %d, want admission ceiling 8", got)
	}
	if err := session.addLane(isolationLaneKind(t, 9, TransportQUIC)); err == nil {
		t.Fatal("QUIC lane was admitted after TCP-only handoff")
	}
}

func TestLaneJoinCannotCrossDevicePrincipal(t *testing.T) {
	flow := newIsolationTestFlow(t, false)
	owner := identity.Principal{ProviderID: "provider", AccountID: "account", DeviceID: "owner"}
	existingFlow := newServerFlow(flow, owner, TransportTCP, 1)
	server := &Server{cfg: ServerConfig{Logger: slog.New(slog.NewTextHandler(io.Discard, nil))}, sessions: map[[16]byte]*serverFlow{flow.sessionID: existingFlow}}
	local, remote := net.Pipe()
	defer local.Close()
	defer remote.Close()
	other := owner
	other.DeviceID = "other"
	request := protocol.Frame{Header: protocol.Header{
		Version: protocol.Version, Type: protocol.TypeJoin, SessionID: flow.sessionID,
		FlowID: flow.flowID, Class: protocol.ClassBulk,
	}}
	go server.handleLaneJoinOpen(context.Background(), local, newFrameConn(local), other, flow.sessionID, 1, request)
	response, err := newFrameConn(remote).Read()
	if err != nil {
		t.Fatal(err)
	}
	if response.Header.Type != protocol.TypeReset {
		t.Fatalf("cross-device lane join response = %d, want RESET", response.Header.Type)
	}
}

func TestActiveFlowClosesAfterDeviceRevocation(t *testing.T) {
	serverCredentials, clientCredentials := testCertificate(t)
	leaf, err := x509.ParseCertificate(clientCredentials.Certificate.Certificate[0])
	if err != nil {
		t.Fatal(err)
	}
	principal, err := identity.PrincipalFromCertificate(leaf)
	if err != nil {
		t.Fatal(err)
	}
	flow := newIsolationTestFlow(t, false)
	serverFlow := newServerFlow(flow, principal, TransportTCP, 1)
	server := &Server{cfg: ServerConfig{Credentials: serverCredentials}}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	go server.watchAuthorization(ctx, serverFlow)
	if err := serverCredentials.Store.RevokeDevice(principal.DeviceID, time.Now()); err != nil {
		t.Fatal(err)
	}
	select {
	case <-flow.doneChan():
	case <-time.After(2500 * time.Millisecond):
		t.Fatal("active flow remained open after device revocation")
	}
}

func newIsolationTestFlow(t *testing.T, reserveControl bool) *multipathFlow {
	t.Helper()
	inner, peer := net.Pipe()
	t.Cleanup(func() { _ = inner.Close(); _ = peer.Close() })
	flow := newMultipathFlow(context.Background(), inner, [16]byte{1}, 1, defaultChunkSize, protocol.FlagAckUp, protocol.FlagAckDown, nil, nil)
	flow.reserveControlLane = reserveControl
	return flow
}

func TestStagedJoinLaneIsInvisibleUntilAcknowledged(t *testing.T) {
	flow := newIsolationTestFlow(t, true)
	lane := isolationLane(t, 1)
	lane.staged = true
	lane.control = true
	if err := flow.addLane(lane); err != nil {
		t.Fatal(err)
	}
	if got := flow.laneCount(); got != 1 {
		t.Fatalf("staged lane consumes %d admission slots, want one", got)
	}
	if got := len(flow.healthyLanes()); got != 0 {
		t.Fatalf("%d staged lanes became schedulable before OPEN_OK", got)
	}
	if err := flow.activateLane(lane); err != nil {
		t.Fatal(err)
	}
	if got := len(flow.healthyLanes()); got != 1 {
		t.Fatalf("healthy lanes after OPEN_OK = %d, want one", got)
	}
}

// A flow's data lives on one lane. A flow that negotiated the control-lane
// reservation keeps lane zero for interactive and rescue traffic in addition
// to that one.
//
// Counting the control lane against the budget makes the server reject and
// close every joined bulk lane. The peer sees an immediate EOF, retries, and
// the flow churns through lanes instead of transferring: with one configured
// lane this stalled a 50 MiB transfer at under 3 MiB.
func TestServerAdmitsBulkLanesBesidesTheControlLane(t *testing.T) {
	flow := newIsolationTestFlow(t, true)
	if err := flow.addLane(isolationLane(t, 0)); err != nil {
		t.Fatal(err)
	}
	session := &serverFlow{flow: flow, maxLanes: serverLaneBudget(flow.reserveControlLane)}
	if err := session.addLane(isolationLane(t, 1)); err != nil {
		t.Fatalf("server refused the only bulk lane: %v", err)
	}
	if got := flow.laneCount(); got != 2 {
		t.Fatalf("lane count = %d, want the control lane plus one bulk lane", got)
	}
}

func TestServerReplacesALaneWithTheSameRole(t *testing.T) {
	flow := newIsolationTestFlow(t, true)
	session := newServerFlow(flow, identity.Principal{}, TransportQUIC, 1)
	control := isolationLane(t, 0)
	control.control = true
	bulk := isolationLane(t, 1)
	if err := session.addLane(control); err != nil {
		t.Fatal(err)
	}
	if err := session.addLane(bulk); err != nil {
		t.Fatal(err)
	}
	// Eviction exists for lanes whose peer has already moved on, so the
	// victims here must be older than the rescue-race window: a freshly
	// admitted lane is never retired to make room.
	control.admitted = time.Now().Add(-2 * laneDeadPathDetection)
	bulk.admitted = time.Now().Add(-2 * laneDeadPathDetection)

	bulkReplacement := isolationLane(t, 2)
	if err := session.addLane(bulkReplacement); err != nil {
		t.Fatalf("bulk replacement refused: %v", err)
	}
	if control.closed.Load() || !bulk.closed.Load() {
		t.Fatalf("bulk replacement retired control=%t bulk=%t, want false/true", control.closed.Load(), bulk.closed.Load())
	}

	controlReplacement := isolationLane(t, 3)
	controlReplacement.control = true
	if err := session.addLane(controlReplacement); err != nil {
		t.Fatalf("control replacement refused: %v", err)
	}
	if !control.closed.Load() || bulkReplacement.closed.Load() {
		t.Fatalf("control replacement retired old-control=%t bulk=%t, want true/false", control.closed.Load(), bulkReplacement.closed.Load())
	}
}

// Parallel rescue JOINs race one another to the gateway, which admits in
// arrival order while the peer crowns the first finisher. Once the live
// lanes are older than the rescue-race window, admission at the lane ceiling
// is always by eviction: a stalled flow's retry matters more than seniority,
// so an old lane is never shielded from a newer rescue.
func TestRacingJoinIsAdmittedByEvictingTheOldestLane(t *testing.T) {
	flow := newIsolationTestFlow(t, true)
	session := newServerFlow(flow, identity.Principal{}, TransportQUIC, 1)
	control := isolationLane(t, 0)
	control.control = true
	bulk := isolationLane(t, 1)
	if err := session.addLane(control); err != nil {
		t.Fatal(err)
	}
	if err := session.addLane(bulk); err != nil {
		t.Fatal(err)
	}
	control.admitted = time.Now().Add(-2 * laneDeadPathDetection)
	bulk.admitted = time.Now().Add(-2 * laneDeadPathDetection)

	racing := isolationLane(t, 2)
	if err := session.addLane(racing); err != nil {
		t.Fatalf("racing join refused at the lane ceiling: %v", err)
	}
	if !bulk.closed.Load() || control.closed.Load() || racing.closed.Load() {
		t.Fatalf("racing join retired bulk=%t control=%t racing=%t, want true/false/false", bulk.closed.Load(), control.closed.Load(), racing.closed.Load())
	}
	if got := flow.laneCount(); got != 2 {
		t.Fatalf("lane count = %d, want the admission ceiling of 2", got)
	}
}

// A lane whose JOIN handshake is still in flight is the one lane eviction
// never takes: parallel rescue attempts race to the gateway, and evicting a
// staged lane can kill the attempt the peer has just crowned. The racing
// join is refused instead -- the transient capacity answer the peer already
// expects for its losing attempts -- and the protection ends with the
// rescue-race window: once the lane is live and older than the window, it is
// evictable by any newer rescue.
func TestStagedLaneIsProtectedOnlyUntilActivated(t *testing.T) {
	flow := newIsolationTestFlow(t, false)
	session := newServerFlow(flow, identity.Principal{}, TransportQUIC, 1)
	staged := isolationLane(t, 1)
	staged.staged = true
	if err := session.addLane(staged); err != nil {
		t.Fatal(err)
	}
	racer := isolationLane(t, 2)
	if err := session.addLane(racer); err == nil {
		t.Fatal("a racing join evicted a lane whose handshake was in flight")
	}
	if staged.closed.Load() {
		t.Fatal("the in-flight lane was retired by the racing join")
	}
	if err := flow.activateLane(staged); err != nil {
		t.Fatal(err)
	}
	staged.admitted = time.Now().Add(-2 * laneDeadPathDetection)
	if err := session.addLane(racer); err != nil {
		t.Fatalf("join behind a live lane refused: %v", err)
	}
	if !staged.closed.Load() || racer.closed.Load() {
		t.Fatalf("eviction retired staged=%t racer=%t, want true/false", staged.closed.Load(), racer.closed.Load())
	}
	if got := flow.laneCount(); got != 1 {
		t.Fatalf("lane count = %d, want the admission ceiling of 1", got)
	}
}

// Role only orders the victim choice; it never blocks a rescue. When no
// lane with the replacement's role is evictable, the oldest lane of any role
// is retired instead of refusing the join.
func TestEvictionCrossesRolesWhenNoSameRoleLaneIsLive(t *testing.T) {
	flow := newIsolationTestFlow(t, true)
	session := newServerFlow(flow, identity.Principal{}, TransportQUIC, 1)
	control := isolationLane(t, 0)
	control.control = true
	otherControl := isolationLane(t, 1)
	otherControl.control = true
	if err := flow.addLane(control); err != nil {
		t.Fatal(err)
	}
	if err := flow.addLane(otherControl); err != nil {
		t.Fatal(err)
	}
	control.admitted = time.Now().Add(-2 * laneDeadPathDetection)
	otherControl.admitted = time.Now().Add(-2 * laneDeadPathDetection)
	bulk := isolationLane(t, 2)
	if err := session.addLane(bulk); err != nil {
		t.Fatalf("bulk join behind two control lanes refused: %v", err)
	}
	if !control.closed.Load() || otherControl.closed.Load() {
		t.Fatalf("cross-role eviction retired oldest-control=%t other=%t, want true/false", control.closed.Load(), otherControl.closed.Load())
	}
	if got := flow.laneCount(); got != 2 {
		t.Fatalf("lane count = %d, want the admission ceiling of 2", got)
	}
}

// A staged JOIN lane whose acknowledgement could not be written must leave
// the flow entirely: keeping it would count a lane that can never carry
// traffic against the admission ceiling for the life of the flow.
func TestFailedStagedJoinIsRemovedFromTheFlow(t *testing.T) {
	flow := newIsolationTestFlow(t, true)
	lane := isolationLane(t, 1)
	lane.staged = true
	if err := flow.addLane(lane); err != nil {
		t.Fatal(err)
	}
	if got := flow.laneCount(); got != 1 {
		t.Fatalf("staged lane consumes %d admission slots, want one", got)
	}
	flow.removeLane(lane)
	if got := flow.laneCount(); got != 0 {
		t.Fatalf("failed staged join still consumes %d admission slots", got)
	}
	if !lane.closed.Load() {
		t.Fatal("removed lane was not closed")
	}
	// A second removal -- for example when a racing eviction already withdrew
	// the lane -- must not panic or miscount.
	flow.removeLane(lane)
}

// Without the reservation there is no separate control lane, so the budget is
// exactly one and a second lane must be refused.
func TestServerBudgetIsExactWithoutControlReservation(t *testing.T) {
	flow := newIsolationTestFlow(t, false)
	if err := flow.addLane(isolationLane(t, 0)); err != nil {
		t.Fatal(err)
	}
	session := &serverFlow{flow: flow, maxLanes: serverLaneBudget(flow.reserveControlLane)}
	// A lane over budget is admitted only by retiring an existing one, so the
	// total never exceeds the configured maximum.
	_ = session.addLane(isolationLane(t, 1))
	if got := flow.laneCount(); got > 1 {
		t.Fatalf("lane count = %d, want at most the configured maximum of 1", got)
	}
}

// A bulk flow must be able to leave the shared pooled connection with one data
// lane: isolation, not striping, is what keeps interactive traffic off a bulk
// congestion window. Striping is deleted; this is the property that outlived
// it, and it is a latency argument rather than a capacity one.
func TestBulkIsolationAppliesAtOneConfiguredLane(t *testing.T) {
	for _, test := range []struct {
		name           string
		reserveControl bool
		wantBulkBudget int
		wantReserve    int
	}{
		{"isolated bulk keeps a control lane beside its own", true, 1, 1},
		{"no reservation keeps one total lane", false, 1, 0},
	} {
		t.Run(test.name, func(t *testing.T) {
			budget, reserve := bulkLaneBudget(test.reserveControl)
			if budget != test.wantBulkBudget || reserve != test.wantReserve {
				t.Fatalf("budget=%d reserve=%d, want %d and %d", budget, reserve, test.wantBulkBudget, test.wantReserve)
			}
		})
	}
}

// A staged lane is protected from eviction only while its handshake could
// still be in flight. The admission's OPEN_OK write is bounded by the same
// budget as the rescue-race window, so a staged lane older than the window
// that never activated is not a handshake in flight but a wedged admission,
// and the next join must be able to take its slot.
func TestStaleStagedLaneIsEvictableWithoutActivation(t *testing.T) {
	flow := newIsolationTestFlow(t, false)
	session := newServerFlow(flow, identity.Principal{}, TransportQUIC, 1)
	staged := isolationLane(t, 1)
	staged.staged = true
	if err := session.addLane(staged); err != nil {
		t.Fatal(err)
	}
	racer := isolationLane(t, 2)
	if err := session.addLane(racer); err == nil {
		t.Fatal("a racing join evicted a lane whose handshake could still be in flight")
	}
	if staged.closed.Load() {
		t.Fatal("the young staged lane was retired inside the rescue-race window")
	}
	// Past the window the never-activated staged lane is a wedged admission:
	// counted against the ceiling yet never able to carry traffic.
	staged.admitted = time.Now().Add(-2 * laneDeadPathDetection)
	if err := session.addLane(racer); err != nil {
		t.Fatalf("join behind a wedged staged lane refused: %v", err)
	}
	if !staged.closed.Load() || racer.closed.Load() {
		t.Fatalf("eviction retired staged=%t racer=%t, want true/false", staged.closed.Load(), racer.closed.Load())
	}
	if got := flow.laneCount(); got != 1 {
		t.Fatalf("lane count = %d, want the admission ceiling of 1", got)
	}
}

// Admission refusals are typed by how permanent they are, because the join
// handler answers each with the reset code the peer's retry policy is built
// on: only the genuine ceiling may wear the transient capacity answer.
func TestLaneAdmissionRefusalsAreTypedByPermanence(t *testing.T) {
	flow := newIsolationTestFlow(t, false)
	session := newServerFlow(flow, identity.Principal{}, TransportTCP, 4)
	if err := session.addLane(isolationLaneKind(t, 1, TransportQUIC)); !errors.Is(err, errLaneFlowTCPMode) {
		t.Fatalf("QUIC join against a TCP-mode flow = %v, want %v", err, errLaneFlowTCPMode)
	}
	if err := session.addLane(isolationLaneKind(t, 1, TransportTCP)); err != nil {
		t.Fatal(err)
	}
	if err := session.addLane(isolationLaneKind(t, 1, TransportTCP)); !errors.Is(err, errLaneDuplicateID) {
		t.Fatalf("duplicate lane id = %v, want %v", err, errLaneDuplicateID)
	}
	closedFlow := newIsolationTestFlow(t, false)
	closedSession := newServerFlow(closedFlow, identity.Principal{}, TransportTCP, 1)
	closedFlow.closeAll()
	if err := closedSession.addLane(isolationLaneKind(t, 1, TransportTCP)); !errors.Is(err, errLaneFlowClosed) {
		t.Fatalf("join against a closed flow = %v, want %v", err, errLaneFlowClosed)
	}
	// The ceiling answer: one young lane fills a budget of one, and eviction
	// cannot take it inside the rescue-race window.
	fullFlow := newIsolationTestFlow(t, false)
	fullSession := newServerFlow(fullFlow, identity.Principal{}, TransportTCP, 1)
	if err := fullSession.addLane(isolationLaneKind(t, 1, TransportTCP)); err != nil {
		t.Fatal(err)
	}
	if err := fullSession.addLane(isolationLaneKind(t, 2, TransportTCP)); !errors.Is(err, errLaneLimitReached) {
		t.Fatalf("join at the admission ceiling = %v, want %v", err, errLaneLimitReached)
	}
}

// Isolation costs a handshake and a fresh congestion window, so it must only
// happen while another flow actually shares the control connection. The count
// that decides this has to track pooled flows exactly, or a lone bulk transfer
// pays about 8% of its goodput for nothing.
func TestPooledFlowCountTracksOpenAndClose(t *testing.T) {
	destinationListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer destinationListener.Close()
	go discardDestination(destinationListener)

	certificate, roots := testCertificate(t)
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	packetConn, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	server, err := NewServer(ServerConfig{
		ListenAddr: packetConn.LocalAddr().String(), Credentials: certificate,
		DestinationPolicy: DestinationPolicy{AllowPrivate: true}, EnableQUIC: true, Logger: logger,
		HandshakeTimeout: time.Second,
	})
	if err != nil {
		t.Fatal(err)
	}
	client, err := NewClient(ClientConfig{
		ListenAddr: "127.0.0.1:0", RemoteAddr: packetConn.LocalAddr().String(), Credentials: roots, Transport: TransportQUIC, EnableQUICPool: true, Logger: logger, HandshakeTimeout: time.Second,
	})
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	serverErr := make(chan error, 1)
	go func() { serverErr <- server.ServePacketConn(ctx, packetConn) }()

	if got := client.quicPoolActive.Load(); got != 0 {
		t.Fatalf("pooled flow count = %d before any flow, want 0", got)
	}
	first, err := client.openFlow(ctx, destinationListener.Addr().String())
	if err != nil {
		t.Fatalf("first pooled flow: %v", err)
	}
	if got := client.quicPoolActive.Load(); got != 1 {
		t.Fatalf("pooled flow count = %d after one flow, want 1", got)
	}
	second, err := client.openFlow(ctx, destinationListener.Addr().String())
	if err != nil {
		t.Fatalf("second pooled flow: %v", err)
	}
	if got := client.quicPoolActive.Load(); got != 2 {
		t.Fatalf("pooled flow count = %d after two flows, want 2", got)
	}
	_ = second.outer.Close()
	if got := client.quicPoolActive.Load(); got != 1 {
		t.Fatalf("pooled flow count = %d after one close, want 1", got)
	}
	// Closing twice must not double-decrement; the count decides a policy.
	_ = second.outer.Close()
	if got := client.quicPoolActive.Load(); got != 1 {
		t.Fatalf("pooled flow count = %d after a repeated close, want 1", got)
	}
	_ = first.outer.Close()
	if got := client.quicPoolActive.Load(); got != 0 {
		t.Fatalf("pooled flow count = %d after all closes, want 0", got)
	}
	client.closeQUICPool()
	cancel()
	select {
	case err := <-serverErr:
		if err != nil {
			t.Fatalf("server shutdown: %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("server shutdown timeout")
	}
}

func TestBulkIsolationCapacityCannotEscapeIntoDedicatedConnections(t *testing.T) {
	certificate, roots := testCertificate(t)
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	packetConn, err := net.ListenPacket("udp4", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	server, err := NewServer(ServerConfig{
		ListenAddr: packetConn.LocalAddr().String(), Credentials: certificate,
		DestinationPolicy: DestinationPolicy{AllowPrivate: true}, EnableQUIC: true,
		Logger: logger, HandshakeTimeout: time.Second,
	})
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	serverErr := make(chan error, 1)
	go func() { serverErr <- server.ServePacketConn(ctx, packetConn) }()

	var sockets atomic.Int64
	client, err := NewClient(ClientConfig{
		ListenAddr: "127.0.0.1:0", RemoteAddr: packetConn.LocalAddr().String(),
		LocalAddress: "127.0.0.1", Credentials: roots,
		Transport: TransportQUIC, EnableQUICPool: true,
		DialTimeout: 2 * time.Second, HandshakeTimeout: 2 * time.Second,
		Logger: logger,
		SocketControl: func(network, _ string, _ syscall.RawConn) error {
			if strings.HasPrefix(network, "udp") {
				sockets.Add(1)
			}
			return nil
		},
	})
	if err != nil {
		t.Fatal(err)
	}
	client.memoryLimits.maxBulkConnections = 1

	occupied, err := client.reserveBulkConn(ctx)
	if err != nil {
		t.Fatal(err)
	}
	defer occupied.close("test complete")

	const waiters = 16
	var wg sync.WaitGroup
	errs := make(chan error, waiters)
	for i := 0; i < waiters; i++ {
		wg.Add(1)
		go func(laneID uint64) {
			defer wg.Done()
			_, laneErr := client.openJoinLane(ctx, TransportQUIC, [16]byte{1}, 1, laneID)
			errs <- laneErr
		}(uint64(i + 1))
	}
	wg.Wait()
	close(errs)
	for laneErr := range errs {
		if !errors.Is(laneErr, errBulkConnectionLimit) {
			t.Fatalf("over-budget lane = %v, want capacity decision", laneErr)
		}
	}
	if got := sockets.Load(); got != 1 {
		t.Fatalf("over-budget isolation opened %d UDP sockets, want the one admitted connection", got)
	}

	client.closeQUICPool()
	cancel()
	select {
	case serveErr := <-serverErr:
		if serveErr != nil && !errors.Is(serveErr, net.ErrClosed) {
			t.Fatalf("server shutdown: %v", serveErr)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("server shutdown timeout")
	}
}

func TestDedicatedBulkFallbackIsReservedForRecoverablePoolFailures(t *testing.T) {
	if dedicatedBulkFallbackAllowed(errBulkConnectionLimit) {
		t.Fatal("capacity decision was treated as a pool failure")
	}
	if dedicatedBulkFallbackAllowed(fmt.Errorf("wrapped: %w", errBulkConnectionLimit)) {
		t.Fatal("wrapped capacity decision was treated as a pool failure")
	}
	if dedicatedBulkFallbackAllowed(context.Canceled) || dedicatedBulkFallbackAllowed(context.DeadlineExceeded) {
		t.Fatal("expired caller started a dedicated fallback")
	}
	if !dedicatedBulkFallbackAllowed(errors.New("pooled stream unavailable")) {
		t.Fatal("recoverable pool failure did not retain dedicated fallback")
	}
}

// The internal off state remains safe for tests and partial flow setup even
// though protocol v1 enables ranges on every established flow.
func TestRangesAreNotSentBeforeRangeTrackingIsEnabled(t *testing.T) {
	conn := newAckCaptureConn(0, nil)
	flow := newAckTestFlow(conn)
	flow.rangesMu.Lock()
	flow.pendingRanges = [][2]uint64{{100, 200}}
	flow.rangesMu.Unlock()

	if err := flow.writeACK(context.Background(), 50, protocol.FlagAckDown, false); err != nil {
		t.Fatal(err)
	}
	frame := waitAckFrame(t, conn)
	if frame.Header.Flags&protocol.FlagAckRanges != 0 || len(frame.Payload) != 0 {
		t.Fatalf("ranges were sent before range tracking was enabled: %+v", frame.Header)
	}

	flow.ackRanges.Store(true)
	if err := flow.writeACK(context.Background(), 50, protocol.FlagAckDown, false); err != nil {
		t.Fatal(err)
	}
	frame = waitAckFrame(t, conn)
	if frame.Header.Flags&protocol.FlagAckRanges == 0 || len(frame.Payload) != protocol.AckRangeSize {
		t.Fatalf("ranges were not sent to a capable peer: %+v", frame.Header)
	}
}
