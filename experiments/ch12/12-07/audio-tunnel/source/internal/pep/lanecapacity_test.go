package pep

import (
	"context"
	"crypto/x509"
	"errors"
	"io"
	"log/slog"
	"net"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/metrics"
	"github.com/bojieli/queqiao/internal/protocol"
	"github.com/bojieli/queqiao/internal/session"
)

// The reset code on a refused JOIN is the peer's retry policy: capacity must
// stay the transient answer, while the TCP-mode refusal is a permanent
// rejection an AUTO recovery path can also recognize and act on.
func TestCompleteLaneJoinMapsResetCodesToRetryPolicy(t *testing.T) {
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	for _, test := range []struct {
		name          string
		code          session.ResetCode
		want          error
		stillRejected bool
	}{
		{name: "capacity stays transient", code: session.ResetFlowLimit, want: errLaneJoinCapacity},
		{name: "tcp mode is a recognizable rejection", code: session.ResetTransport, want: errLaneJoinTCPMode, stillRejected: true},
		{name: "protocol is permanent", code: session.ResetProtocol, want: errLaneJoinRejected},
	} {
		t.Run(test.name, func(t *testing.T) {
			local, remote := net.Pipe()
			t.Cleanup(func() { _ = local.Close(); _ = remote.Close() })
			go func() {
				frames := newFrameConn(remote)
				request, err := frames.Read()
				if err != nil {
					return
				}
				_ = frames.Write(protocol.Frame{Header: protocol.Header{
					Version: protocol.Version, Type: protocol.TypeReset,
					SessionID: request.Header.SessionID, FlowID: request.Header.FlowID,
					Class: protocol.ClassBulk,
				}, Payload: session.ResetPayload(test.code, "refused")})
			}()
			client := &Client{cfg: ClientConfig{Logger: logger, HandshakeTimeout: 2 * time.Second}}
			_, err := client.completeLaneJoin(&authenticatedLane{
				fc: newFrameConn(local), outer: local, sessionID: [16]byte{1}, kind: TransportQUIC, laneID: 1,
			}, 7, 0)
			if !errors.Is(err, test.want) {
				t.Fatalf("err = %v, want %v", err, test.want)
			}
			if got := errors.Is(err, errLaneJoinRejected); got != test.stillRejected && test.want != errLaneJoinRejected {
				t.Fatalf("errors.Is(err, errLaneJoinRejected) = %t, want %t", got, test.stillRejected)
			}
		})
	}
}

// A sprayed attempt learning the TCP-mode refusal must not cancel the round:
// the answer is actionable, and only attempt zero can act on it with a TCP
// commit. Attempt zero reporting it ends the round like any rejection --
// there is no commit left to wait for.
func TestTCPModeRefusalDoesNotCancelAttemptZero(t *testing.T) {
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	client := &Client{cfg: ClientConfig{Logger: logger}, metrics: metrics.New()}
	flow := newGraceTestFlow(t)
	winner, _ := rescueTestLane(t, 2)
	attempts := []rescueAttempt{
		func(ctx context.Context) (*mpLane, error) {
			// Attempt zero's TCP commit is slower than the sprayed attempts
			// learning the same answer from the peer.
			time.Sleep(50 * time.Millisecond)
			return winner, nil
		},
		func(ctx context.Context) (*mpLane, error) { return nil, errLaneJoinTCPMode },
	}
	lane, _, err := client.raceRescueAttempts(context.Background(), flow, attempts)
	if err != nil || lane != winner {
		t.Fatalf("lane = %v, err = %v, want attempt zero's commit to win the round", lane, err)
	}

	rejected := []rescueAttempt{
		func(ctx context.Context) (*mpLane, error) { return nil, errLaneJoinTCPMode },
		func(ctx context.Context) (*mpLane, error) {
			<-ctx.Done()
			return nil, ctx.Err()
		},
	}
	start := time.Now()
	if _, _, err := client.raceRescueAttempts(context.Background(), flow, rejected); !errors.Is(err, errLaneJoinTCPMode) {
		t.Fatalf("err = %v, want %v", err, errLaneJoinTCPMode)
	}
	if elapsed := time.Since(start); elapsed > time.Second {
		t.Fatalf("attempt zero's own refusal took %s to end the round", elapsed)
	}
}

// joinTestRig is a real gateway and client with the server-side flow
// registered by hand, so the test decides the admission state a rescue JOIN
// meets rather than growing one through the SOCKS path.
type joinTestRig struct {
	client     *Client
	serverFlow *multipathFlow
	serverSess *serverFlow
	cancel     context.CancelFunc
	errorsCh   chan error
}

func newJoinTestRig(t *testing.T, clientTransport, initialKind TransportKind, tcpMaxLanes int) *joinTestRig {
	t.Helper()
	certificate, roots := testCertificate(t)
	leaf, err := x509.ParseCertificate(roots.Certificate.Certificate[0])
	if err != nil {
		t.Fatal(err)
	}
	principal, err := identity.PrincipalFromCertificate(leaf)
	if err != nil {
		t.Fatal(err)
	}
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	serverListener, packetConn := listenTCPAndUDPOnOnePort(t)
	server, err := NewServer(ServerConfig{
		ListenAddr: serverListener.Addr().String(), Credentials: certificate,
		DestinationPolicy: DestinationPolicy{AllowPrivate: true},
		EnableTCP:         true, EnableQUIC: true, Logger: logger,
		HandshakeTimeout: 2 * time.Second,
	})
	if err != nil {
		t.Fatal(err)
	}
	serverFlow := newIsolationTestFlow(t, true)
	serverSession := newServerFlow(serverFlow, principal, initialKind, tcpMaxLanes)
	server.sessionsMu.Lock()
	server.sessions[serverFlow.sessionID] = serverSession
	server.sessionsMu.Unlock()

	client, err := NewClient(ClientConfig{
		ListenAddr: "127.0.0.1:0", RemoteAddr: serverListener.Addr().String(),
		Credentials: roots, Transport: clientTransport, EnableQUICPool: true,
		FallbackDelay: 100 * time.Millisecond, FallbackGrace: 2 * time.Second,
		DialTimeout: 2 * time.Second, HandshakeTimeout: 2 * time.Second, Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	errorsCh := make(chan error, 2)
	go func() { errorsCh <- server.ServeListener(ctx, serverListener) }()
	go func() { errorsCh <- server.ServePacketConn(ctx, packetConn) }()
	rig := &joinTestRig{
		client: client, serverFlow: serverFlow, serverSess: serverSession,
		cancel: cancel, errorsCh: errorsCh,
	}
	t.Cleanup(func() {
		cancel()
		for range 2 {
			select {
			case <-errorsCh:
			case <-time.After(3 * time.Second):
				return
			}
		}
		_ = serverListener.Close()
		_ = packetConn.Close()
	})
	return rig
}

// A peer that answers a rescue JOIN with "flow switched to TCP fallback" is
// stating a permanent fact about the flow. An AUTO client must take it at its
// word and commit to TCP at once, not spend the replacement grace on QUIC
// retries the peer has already ruled out.
func TestAutoRecoveryCommitsToTCPWhenPeerSaysFlowIsOnTCP(t *testing.T) {
	rig := newJoinTestRig(t, TransportAuto, TransportTCP, 1)
	flow := newGraceTestFlow(t)
	flow.reserveControlLane = true
	if err := flow.addLane(isolationLane(t, 0)); err != nil {
		t.Fatal(err)
	}
	lane, err := rig.client.openRecoveryLane(context.Background(), flow, rig.serverFlow.sessionID, rig.serverFlow.flowID)
	if err != nil {
		t.Fatal(err)
	}
	if lane.kind != TransportTCP {
		t.Fatalf("recovery lane transport = %s, want TCP", lane.kind)
	}
}

// One capacity answer is the ordinary loser of a rescue race, so the AUTO
// TCP commit stays suppressed for it. When the answer repeats with no
// successful round between, a wedged admission slot on the peer is the
// likelier reading, and the commit stops being suppressed.
func TestPersistentCapacityAnswerLetsAutoCommitToTCP(t *testing.T) {
	rig := newJoinTestRig(t, TransportAuto, TransportQUIC, 4)
	// Fill the ceiling with lanes too young to evict, so every JOIN is
	// answered with the transient capacity refusal. The ids stay clear of the
	// ones the client flow allocates for its JOINs.
	control := isolationLane(t, 7)
	control.control = true
	if err := rig.serverSess.addLane(control); err != nil {
		t.Fatal(err)
	}
	if err := rig.serverSess.addLane(isolationLane(t, 8)); err != nil {
		t.Fatal(err)
	}
	flow := newGraceTestFlow(t)
	flow.reserveControlLane = true
	if err := flow.addLane(isolationLane(t, 0)); err != nil {
		t.Fatal(err)
	}
	if _, err := rig.client.openRecoveryLane(context.Background(), flow, rig.serverFlow.sessionID, rig.serverFlow.flowID); !errors.Is(err, errLaneJoinCapacity) {
		t.Fatalf("first capacity answer = %v, want %v", err, errLaneJoinCapacity)
	}
	flow.noteLaneCapacityRefusal()
	flow.noteLaneCapacityRefusal()
	lane, err := rig.client.openRecoveryLane(context.Background(), flow, rig.serverFlow.sessionID, rig.serverFlow.flowID)
	if err != nil {
		t.Fatal(err)
	}
	if lane.kind != TransportTCP {
		t.Fatalf("recovery lane transport = %s, want TCP once the answer repeated", lane.kind)
	}
	if !rig.serverSess.tcpMode {
		t.Fatal("server flow did not commit to TCP")
	}
}

// A successful round is what makes the capacity answer believable again:
// whatever the streak was before, it restarts from zero.
func TestSuccessfulRescueRoundResetsTheCapacityStreak(t *testing.T) {
	rig := newJoinTestRig(t, TransportQUIC, TransportQUIC, 1)
	flow := newGraceTestFlow(t)
	flow.reserveControlLane = true
	if err := flow.addLane(isolationLane(t, 0)); err != nil {
		t.Fatal(err)
	}
	flow.noteLaneCapacityRefusal()
	if err := rig.client.runRescueRound(context.Background(), flow, rig.serverFlow.sessionID, rig.serverFlow.flowID); err != nil {
		t.Fatal(err)
	}
	if got := flow.laneCapacityRefusals(); got != 0 {
		t.Fatalf("capacity streak after a successful round = %d, want 0", got)
	}
}

// The stall-rescue loop believes the transient capacity answer only so many
// consecutive times: at the recovery-attempt cap with no successful round
// between, the flow is marked unresumable and the manager stops, so the
// application reconnects on a fresh flow instead of retrying for the flow's
// life.
func TestStallRescueGivesUpAfterConsecutiveCapacityRefusals(t *testing.T) {
	rig := newJoinTestRig(t, TransportQUIC, TransportQUIC, 1)
	control := isolationLane(t, 7)
	control.control = true
	if err := rig.serverSess.addLane(control); err != nil {
		t.Fatal(err)
	}
	if err := rig.serverSess.addLane(isolationLane(t, 8)); err != nil {
		t.Fatal(err)
	}
	flow := newGraceTestFlow(t)
	flow.reserveControlLane = true
	if err := flow.addLane(isolationLane(t, 0)); err != nil {
		t.Fatal(err)
	}
	for range maxLaneRecoveryAttempts - 1 {
		flow.noteLaneCapacityRefusal()
	}
	done := make(chan struct{})
	go func() {
		rig.client.manageQUICLanes(context.Background(), flow, rig.serverFlow.sessionID, rig.serverFlow.flowID)
		close(done)
	}()
	flow.stallSignal <- struct{}{}
	select {
	case <-done:
	case <-time.After(15 * time.Second):
		t.Fatal("lane manager kept rescuing after the capacity answer persisted")
	}
	if !flow.resumeRefused.Load() {
		t.Fatal("consecutive capacity refusals did not mark the flow unresumable")
	}
}
