package pep

import (
	"errors"
	"io"
	"net"
	"sync/atomic"
	"syscall"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/pathmodel"
	"github.com/bojieli/queqiao/internal/pathsim"
	"github.com/bojieli/queqiao/internal/protocol"
)

func TestCurrentUplinkAppliesSocketControl(t *testing.T) {
	_, credentials := testCertificate(t)
	var calls atomic.Int64
	client, err := NewClient(ClientConfig{
		ListenAddr: "127.0.0.1:0", RemoteAddr: "127.0.0.1:9", Credentials: credentials,
		SocketControl: func(_, _ string, conn syscall.RawConn) error {
			return conn.Control(func(uintptr) { calls.Add(1) })
		},
	})
	if err != nil {
		t.Fatal(err)
	}
	if got := client.currentUplink(); got == "" {
		t.Fatal("protected uplink probe did not resolve a source address")
	}
	if calls.Load() != 1 {
		t.Fatalf("socket control calls = %d, want 1", calls.Load())
	}
}

func TestPathProbeEchoIsOneForOneAndDestinationFree(t *testing.T) {
	serverConn, clientConn := net.Pipe()
	serverFrames := newFrameConn(serverConn)
	clientFrames := newFrameConn(clientConn)
	defer serverFrames.Close()
	defer clientFrames.Close()

	var sessionID [16]byte
	sessionID[0] = 1
	probe := func(sequence uint64) protocol.Frame {
		return protocol.Frame{Header: protocol.Header{
			Version: protocol.Version, Type: protocol.TypeProbe,
			SessionID: sessionID, FlowID: probeFlowID, Sequence: sequence, Class: protocol.ClassNew,
		}, Payload: make([]byte, probePayloadBytes)}
	}

	done := make(chan struct{})
	go func() {
		(&Server{}).handlePathProbe(serverFrames, probe(0))
		close(done)
	}()
	for sequence := uint64(0); sequence < 4; sequence++ {
		if sequence > 0 {
			if err := clientFrames.Write(probe(sequence)); err != nil {
				t.Fatal(err)
			}
		}
		echo, err := clientFrames.Read()
		if err != nil {
			t.Fatal(err)
		}
		if echo.Header.Type != protocol.TypeProbe || echo.Header.SessionID != sessionID ||
			echo.Header.FlowID != probeFlowID || echo.Header.Sequence != sequence ||
			len(echo.Payload) != probePayloadBytes {
			t.Fatalf("probe echo %d changed identity or size: %+v", sequence, echo.Header)
		}
	}
	_ = clientFrames.Close()
	select {
	case <-done:
	case <-time.After(time.Second):
		t.Fatal("probe handler did not stop at the delimited input")
	}
}

// Flow initiation is what an application feels. The first connection to a
// server may cost what it must -- a QUIC handshake and one authentication
// exchange -- but every flow after that is a fresh application connection on a
// pool that is already up, and should cost as close to nothing as the protocol
// allows.
//
// This measures it the way a user would: the wall-clock time from dialing the
// local SOCKS port to having the reply in hand, across an emulated 300 ms
// path, for the first flow and then for later ones.
func TestFlowInitiationCostsNoRoundTripsWhenTheConnectionIsWarm(t *testing.T) {
	if testing.Short() {
		t.Skip("brings up QUIC across an emulated 300 ms path")
	}
	const oneWay = 150 * time.Millisecond
	path := pathsim.Config{OneWayDelay: oneWay, Seed: 31}
	socks, destination := codedPairWith(t, true, &path, echoDestination)

	measure := func() time.Duration {
		start := time.Now()
		conn := socksDial(t, socks, destination, 30*time.Second)
		elapsed := time.Since(start)
		// Prove the flow actually carries data, not just that a reply arrived.
		if _, err := conn.Write([]byte("x")); err != nil {
			t.Fatal(err)
		}
		got := make([]byte, 1)
		if _, err := io.ReadFull(conn, got); err != nil {
			t.Fatalf("flow did not carry data: %v", err)
		}
		_ = conn.Close()
		return elapsed
	}

	// Establishment is the first flow, which authenticates the connection, and
	// the second, which proves the fast open once so no later flow has to.
	// Both are allowed to cost a round trip. Everything after is the case an
	// application actually repeats.
	establishing := []time.Duration{measure(), measure()}
	var warm []time.Duration
	for i := 0; i < 3; i++ {
		warm = append(warm, measure())
	}
	roundTrip := 2 * oneWay
	t.Logf("establishing %v %v; warm flows %v %v %v (round trip %v)",
		establishing[0].Round(time.Millisecond), establishing[1].Round(time.Millisecond),
		warm[0].Round(time.Millisecond), warm[1].Round(time.Millisecond),
		warm[2].Round(time.Millisecond), roundTrip)

	for i, elapsed := range warm {
		if elapsed > roundTrip/4 {
			t.Errorf("warm flow %d took %v against a %v round trip: a flow on a "+
				"connection that is already established should not wait for the far end",
				i, elapsed.Round(time.Millisecond), roundTrip)
		}
	}
	// And establishment must stay bounded rather than creeping. Listener
	// readiness now includes the one-time bidirectional path measurement, so a
	// caller which connects before readiness may wait for the handshake plus
	// that bounded exchange. The later flows are still the latency property
	// this test exists to protect.
	if establishing[0] > 5*roundTrip {
		t.Errorf("first flow took %v, more than five round trips including path measurement", establishing[0].Round(time.Millisecond))
	}
	_ = net.Dialer{}
}

// A path is an uplink and a peer, not a peer. The same server reached over
// Wi-Fi and over a cellular link erases differently, is bottlenecked
// differently and has a different minimum round trip; carrying one's
// measurements into the other is worse than having none, because everything
// downstream is sized from a confident wrong answer.
func TestAPathIsAnUplinkAndAPeer(t *testing.T) {
	wifi := &net.UDPAddr{IP: net.IPv4(192, 168, 1, 20), Port: 51000}
	cellular := &net.UDPAddr{IP: net.IPv4(10, 55, 3, 7), Port: 51000}
	server := &net.UDPAddr{IP: net.IPv4(23, 135, 236, 244), Port: 12443}

	overWiFi := pathKey(wifi, server)
	overCellular := pathKey(cellular, server)
	if overWiFi == overCellular {
		t.Fatalf("two uplinks to one server share a path key: %q", overWiFi)
	}
	// The same uplink and peer must key the same, whatever port it used, or a
	// second lane would be treated as a different path and learn it again.
	second := &net.UDPAddr{IP: wifi.IP, Port: 51001}
	if again := pathKey(second, server); again != overWiFi {
		t.Fatalf("a second lane on one uplink keyed %q against %q", again, overWiFi)
	}
}

// The uplink is discovered by asking the routing table which source address
// this destination gets, which sends nothing and so can be asked often.
func TestTheUplinkIsWhicheverAddressReachesTheServer(t *testing.T) {
	listener, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	client := &Client{cfg: ClientConfig{RemoteAddr: listener.LocalAddr().String()}}

	uplink := client.currentUplink()
	if uplink != "127.0.0.1" {
		t.Fatalf("uplink to a loopback server = %q, want 127.0.0.1", uplink)
	}
	// Asking twice must give the same answer, or every poll would look like a
	// network change and tear down the pool.
	if again := client.currentUplink(); again != uplink {
		t.Fatalf("uplink changed between two questions: %q then %q", uplink, again)
	}
	// A destination that cannot be reached at all has no uplink, and must not
	// be reported as one: an empty answer is ignored rather than acted on, so
	// a transient resolver failure cannot look like a network change and tear
	// the pool down. The address is malformed rather than merely unresolvable,
	// because a resolver that answers everything -- this machine's does, with
	// a fake address in 198.18.0.0/15 -- would otherwise give it an uplink.
	unreachable := &Client{cfg: ClientConfig{RemoteAddr: "127.0.0.1:not-a-port"}}
	if got := unreachable.currentUplink(); got != "" {
		t.Fatalf("unreachable server reported uplink %q", got)
	}
}

// An explicit binding is the route the transport actually takes. A VPN may
// own the default route to the server while the outer connection is pinned to
// a physical interface; the watcher must observe the pinned address or it
// will invent uplink changes and repeatedly destroy a healthy QUIC pool.
func TestTheConfiguredUplinkMatchesTheBoundOuterAddress(t *testing.T) {
	client := &Client{cfg: ClientConfig{
		RemoteAddr:   "127.0.0.1:not-a-port",
		LocalAddress: "192.0.2.10",
	}}
	if got := client.currentUplink(); got != "192.0.2.10" {
		t.Fatalf("configured uplink = %q, want 192.0.2.10", got)
	}
}

// The prewarm exists to measure, so it has to leave a measurement behind.
//
// A path that erases is only coded around once something has noticed it does,
// and the first flow on a fresh uplink notices nothing: a handshake is about
// ten packets, and an erasure rate estimated from ten packets is a guess wider
// than the parity it would choose. The prewarm sends enough to answer the
// question before a flow has to ask it.
func TestThePrewarmLeavesTheUplinkMeasured(t *testing.T) {
	if testing.Short() {
		t.Skip("brings up QUIC across an emulated 300 ms path")
	}
	path := pathsim.Config{
		OneWayDelay: 150 * time.Millisecond, RateBytesPerSec: uint64(25e6 / 8),
		PolicerRefillPeriod: 8 * time.Millisecond, LossRate: 0.42, Seed: 53,
	}
	loopback := &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1), Port: 0}
	key := pathKey(loopback, loopback)

	// Start from nothing known about this uplink.
	before := pathmodel.Shared(key).Current().Erasure

	// ServeListener starts the production uplink watcher, which performs one
	// automatic prewarm. Calling prewarmPath here as well used to race a
	// second artificial prewarm against it. Besides not representing the
	// deployed behavior, the two probes could each consume the other's pooled
	// connection budget and made this assertion intermittently observe neither
	// completed measurement.
	_, _ = clientServerAcross(t, &path)
	deadline := time.Now().Add(prewarmTimeout + 5*time.Second)
	var after float64
	for time.Now().Before(deadline) {
		after = pathmodel.Shared(key).Current().Erasure
		if after > 0 {
			break
		}
		time.Sleep(measurementPoll)
	}

	t.Logf("erasure floor known for this uplink: %.3f before the prewarm, %.3f after", before, after)
	if after <= 0 {
		t.Fatal("the prewarm left the uplink unmeasured, so the first flow on it " +
			"will be carried uncoded across a channel that erases 42% of packets")
	}
	// And what it measured has to resemble the path, or it is worse than
	// nothing: everything downstream is sized from this number.
	if after < 0.2 || after > 0.7 {
		t.Fatalf("measured floor %.3f on a 42%% erasure channel", after)
	}
}

// The probe echo is an obligation, not a courtesy. A gateway that authenticates
// on a protocol-1 ALPN has agreed to reflect the sequence, so a client that
// quietly accepted a short or altered echo would be carrying a peer whose
// disagreement about the wire it never learned about -- and would draw its
// erasure model from traffic it never sent.
func TestPathProbeEchoFailuresAreDistinguishedFromASlowPath(t *testing.T) {
	var sessionID [16]byte
	sessionID[0] = 7
	echo := func(sequence uint64) protocol.Frame {
		return protocol.Frame{Header: protocol.Header{
			Version: protocol.Version, Type: protocol.TypeProbe,
			SessionID: sessionID, FlowID: probeFlowID, Sequence: sequence, Class: protocol.ClassNew,
		}, Payload: make([]byte, probePayloadBytes)}
	}

	for _, tc := range []struct {
		name string
		// gateway writes whatever this build of a peer would answer with, then
		// closes its side.
		gateway   func(t *testing.T, fc *frameConn)
		violation bool
	}{
		{
			name: "conforming gateway",
			gateway: func(t *testing.T, fc *frameConn) {
				for sequence := uint64(0); sequence < 3; sequence++ {
					if err := fc.Write(echo(sequence)); err != nil {
						return
					}
				}
			},
		},
		{
			name: "gateway that does not echo at all",
			gateway: func(t *testing.T, fc *frameConn) {
			},
			violation: true,
		},
		{
			name: "gateway that stops early",
			gateway: func(t *testing.T, fc *frameConn) {
				_ = fc.Write(echo(0))
			},
			violation: true,
		},
		{
			name: "gateway that reorders the sequence",
			gateway: func(t *testing.T, fc *frameConn) {
				_ = fc.Write(echo(0))
				_ = fc.Write(echo(2))
			},
			violation: true,
		},
		{
			name: "gateway that changes the payload size",
			gateway: func(t *testing.T, fc *frameConn) {
				short := echo(0)
				short.Payload = short.Payload[:probePayloadBytes-1]
				_ = fc.Write(short)
			},
			violation: true,
		},
		{
			name: "gateway that answers under another session",
			gateway: func(t *testing.T, fc *frameConn) {
				other := echo(0)
				other.Header.SessionID[0] = 9
				_ = fc.Write(other)
			},
			violation: true,
		},
		{
			name: "gateway that answers with a different frame type",
			gateway: func(t *testing.T, fc *frameConn) {
				wrong := echo(0)
				wrong.Header.Type = protocol.TypeData
				_ = fc.Write(wrong)
			},
			violation: true,
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			serverConn, clientConn := net.Pipe()
			serverFrames := newFrameConn(serverConn)
			clientFrames := newFrameConn(clientConn)
			defer clientFrames.Close()

			go func() {
				tc.gateway(t, serverFrames)
				_ = serverFrames.Close()
			}()

			client := &Client{}
			lane := &authenticatedLane{fc: clientFrames, sessionID: sessionID}
			err := client.readPathProbeEchoes(lane, 3)
			var violation probeEchoViolation
			switch {
			case tc.violation && !errors.As(err, &violation):
				t.Fatalf("non-conforming gateway accepted: err = %v", err)
			case !tc.violation && err != nil:
				t.Fatalf("conforming gateway rejected: %v", err)
			}
		})
	}

	// A path too slow to return the echo inside the probe budget is not a
	// violation. The measurement is simply incomplete, which is what bounding
	// the probe in time buys.
	t.Run("slow path is not a violation", func(t *testing.T) {
		serverConn, clientConn := net.Pipe()
		defer serverConn.Close()
		clientFrames := newFrameConn(clientConn)
		defer clientFrames.Close()
		if err := clientConn.SetReadDeadline(time.Now().Add(20 * time.Millisecond)); err != nil {
			t.Fatal(err)
		}
		client := &Client{}
		lane := &authenticatedLane{fc: clientFrames, sessionID: sessionID}
		if err := client.readPathProbeEchoes(lane, 3); err != nil {
			t.Fatalf("expired probe budget reported as a peer violation: %v", err)
		}
	})
}
