package pep

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"github.com/apernet/quic-go"
	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/netbind"
)

type routeErrorPacketConn struct{ err error }

func (*routeErrorPacketConn) ReadFrom([]byte) (int, net.Addr, error) {
	return 0, nil, errors.New("unused read")
}
func (c *routeErrorPacketConn) WriteTo([]byte, net.Addr) (int, error) { return 0, c.err }
func (*routeErrorPacketConn) Close() error                            { return nil }
func (*routeErrorPacketConn) LocalAddr() net.Addr                     { return &net.UDPAddr{} }
func (*routeErrorPacketConn) SetDeadline(time.Time) error             { return nil }
func (*routeErrorPacketConn) SetReadDeadline(time.Time) error         { return nil }
func (*routeErrorPacketConn) SetWriteDeadline(time.Time) error        { return nil }

type routeErrorOOBConn struct {
	*net.UDPConn
	err error
}

type switchableRouteConn struct {
	*net.UDPConn
	failing atomic.Bool
	err     error
}

func (c *switchableRouteConn) failure() error {
	if c.err != nil {
		return c.err
	}
	return injectedRouteError
}

func (c *switchableRouteConn) WriteTo(payload []byte, addr net.Addr) (int, error) {
	if c.failing.Load() {
		return 0, c.failure()
	}
	return c.UDPConn.WriteTo(payload, addr)
}

func (c *switchableRouteConn) WriteMsgUDP(payload, oob []byte, addr *net.UDPAddr) (int, int, error) {
	if c.failing.Load() {
		return 0, 0, c.failure()
	}
	return c.UDPConn.WriteMsgUDP(payload, oob, addr)
}

func (c *routeErrorOOBConn) WriteTo([]byte, net.Addr) (int, error) { return 0, c.err }
func (c *routeErrorOOBConn) WriteMsgUDP([]byte, []byte, *net.UDPAddr) (int, int, error) {
	return 0, 0, c.err
}

// The codes come from this platform's sample list rather than being spelled
// inline: syscall.ENETDOWN and its neighbours are synthetic on Windows, so a
// table of them would assert only that the classifier agrees with itself.
func TestTransientLocalRouteErrorsBecomeQUICPacketLoss(t *testing.T) {
	for _, sample := range transientRouteWriteSamples {
		writeErr := sample.err
		t.Run(sample.name, func(t *testing.T) {
			observed := 0
			conn := tolerateTransientRouteErrors(&routeErrorPacketConn{err: &net.OpError{Op: "write", Net: "udp", Err: writeErr}}, func(error) {
				observed++
			})
			payload := []byte("one lost QUIC datagram")
			n, err := conn.WriteTo(payload, &net.UDPAddr{})
			if err != nil || n != len(payload) {
				t.Fatalf("transient write = %d, %v; want %d, nil", n, err, len(payload))
			}
			if observed != 1 {
				t.Fatalf("observer called %d times, want one", observed)
			}
		})
	}
}

func TestPermanentUDPSocketErrorsRemainFatal(t *testing.T) {
	want := &net.OpError{Op: "write", Net: "udp", Err: permanentSocketError}
	conn := tolerateTransientRouteErrors(&routeErrorPacketConn{err: want}, nil)
	if _, err := conn.WriteTo([]byte("packet"), &net.UDPAddr{}); !errors.Is(err, permanentSocketError) {
		t.Fatalf("permanent socket error = %v, want %v", err, permanentSocketError)
	}
}

func TestVanishedSourceAddressRemainsFatal(t *testing.T) {
	want := &net.OpError{Op: "write", Net: "udp", Err: staleSourceWriteSample.err}
	observed := 0
	conn := tolerateTransientRouteErrors(&routeErrorPacketConn{err: want}, func(error) { observed++ })
	if _, err := conn.WriteTo([]byte("packet"), &net.UDPAddr{}); !errors.Is(err, staleSourceWriteSample.err) {
		t.Fatalf("vanished source write = %v, want %v", err, staleSourceWriteSample.err)
	}
	if observed != 0 {
		t.Fatalf("vanished source was reported as transient %d times", observed)
	}
}

func TestTransientRouteWrapperPreservesAndProtectsQUICFastPath(t *testing.T) {
	udp, err := net.ListenUDP("udp4", &net.UDPAddr{IP: net.IPv4zero, Port: 0})
	if err != nil {
		t.Fatal(err)
	}
	defer udp.Close()
	observed := 0
	wrapped := tolerateTransientRouteErrors(&routeErrorOOBConn{UDPConn: udp, err: injectedRouteError}, func(error) {
		observed++
	})
	oob, ok := wrapped.(quic.OOBCapablePacketConn)
	if !ok {
		t.Fatal("route-error wrapper disabled quic-go's OOBCapablePacketConn fast path")
	}
	payload, control := []byte("packet"), []byte{1, 2, 3}
	n, oobn, err := oob.WriteMsgUDP(payload, control, &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1), Port: 9})
	if err != nil || n != len(payload) || oobn != len(control) {
		t.Fatalf("transient OOB write = %d/%d, %v; want %d/%d, nil", n, oobn, err, len(payload), len(control))
	}
	if observed != 1 {
		t.Fatalf("observer called %d times, want one", observed)
	}
}

func TestQUICConnectionSurvivesATransientLocalRouteOutage(t *testing.T) {
	serverCredentials, clientCredentials := testCertificate(t)
	serverTLS, err := identity.ServerTLSConfig(serverCredentials, defaultALPN, false)
	if err != nil {
		t.Fatal(err)
	}
	clientTLS, err := tlsClientConfig(clientCredentials)
	if err != nil {
		t.Fatal(err)
	}
	serverPacket, err := net.ListenPacket("udp4", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer serverPacket.Close()
	listener, err := quic.Listen(serverPacket, serverTLS, quicConfig(flowWindows{}))
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	payload := []byte("the stream survived the Wi-Fi route disappearing")
	serverResult := make(chan error, 1)
	go func() {
		conn, acceptErr := listener.Accept(ctx)
		if acceptErr != nil {
			serverResult <- acceptErr
			return
		}
		stream, acceptErr := conn.AcceptStream(ctx)
		if acceptErr != nil {
			serverResult <- acceptErr
			return
		}
		got := make([]byte, len(payload))
		_, acceptErr = io.ReadFull(stream, got)
		if acceptErr == nil && string(got) != string(payload) {
			acceptErr = fmt.Errorf("stream payload = %q, want %q", got, payload)
		}
		serverResult <- acceptErr
	}()

	udp, err := net.ListenUDP("udp4", &net.UDPAddr{IP: net.IPv4zero, Port: 0})
	if err != nil {
		t.Fatal(err)
	}
	faults := &switchableRouteConn{UDPConn: udp}
	var suppressed atomic.Int64
	packet := tolerateTransientRouteErrors(faults, func(error) { suppressed.Add(1) })
	remote := serverPacket.LocalAddr().(*net.UDPAddr)
	conn, err := quic.Dial(ctx, packet, remote, clientTLS, quicConfig(flowWindows{}))
	if err != nil {
		_ = packet.Close()
		t.Fatal(err)
	}
	defer func() {
		_ = conn.CloseWithError(0, "test complete")
		_ = packet.Close()
	}()
	stream, err := conn.OpenStreamSync(ctx)
	if err != nil {
		t.Fatal(err)
	}
	faults.failing.Store(true)
	if _, err := stream.Write(payload); err != nil {
		t.Fatalf("write during transient outage: %v", err)
	}
	deadline := time.Now().Add(time.Second)
	for suppressed.Load() == 0 && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	if suppressed.Load() == 0 {
		t.Fatal("fault injection did not reach the QUIC packet writer")
	}
	// Keep the route absent long enough to cross at least one normal local send
	// attempt, but well below the connection idle timeout.
	time.Sleep(150 * time.Millisecond)
	faults.failing.Store(false)
	if err := <-serverResult; err != nil {
		t.Fatalf("stream did not recover after route restoration: %v", err)
	}
	if err := conn.Context().Err(); err != nil {
		t.Fatalf("transient route outage closed QUIC connection: %v", err)
	}
}

func TestQUICConnectionClosesWhenItsBoundSourceDisappears(t *testing.T) {
	serverCredentials, clientCredentials := testCertificate(t)
	serverTLS, err := identity.ServerTLSConfig(serverCredentials, defaultALPN, false)
	if err != nil {
		t.Fatal(err)
	}
	clientTLS, err := tlsClientConfig(clientCredentials)
	if err != nil {
		t.Fatal(err)
	}
	serverPacket, err := net.ListenPacket("udp4", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer serverPacket.Close()
	listener, err := quic.Listen(serverPacket, serverTLS, quicConfig(flowWindows{}))
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	go func() {
		conn, acceptErr := listener.Accept(ctx)
		if acceptErr != nil {
			return
		}
		stream, acceptErr := conn.AcceptStream(ctx)
		if acceptErr == nil {
			var one [1]byte
			_, _ = stream.Read(one[:])
		}
	}()

	udp, err := net.ListenUDP("udp4", &net.UDPAddr{IP: net.IPv4zero, Port: 0})
	if err != nil {
		t.Fatal(err)
	}
	faults := &switchableRouteConn{UDPConn: udp, err: staleSourceWriteSample.err}
	packet := tolerateTransientRouteErrors(faults, nil)
	remote := serverPacket.LocalAddr().(*net.UDPAddr)
	conn, err := quic.Dial(ctx, packet, remote, clientTLS, quicConfig(flowWindows{}))
	if err != nil {
		_ = packet.Close()
		t.Fatal(err)
	}
	defer packet.Close()
	stream, err := conn.OpenStreamSync(ctx)
	if err != nil {
		t.Fatal(err)
	}
	faults.failing.Store(true)
	_, _ = stream.Write(make([]byte, 64*1024))
	select {
	case <-conn.Context().Done():
		if conn.Context().Err() == nil {
			t.Fatal("closed connection has no terminal error")
		}
	case <-time.After(time.Second):
		t.Fatal("QUIC kept a connection whose bound source address disappeared")
	}
}

type closeTrackingQUICStream struct {
	cancelReads int
	closes      int
}

func (*closeTrackingQUICStream) Read([]byte) (int, error)          { return 0, io.EOF }
func (*closeTrackingQUICStream) Write(p []byte) (int, error)       { return len(p), nil }
func (*closeTrackingQUICStream) SetDeadline(time.Time) error       { return nil }
func (*closeTrackingQUICStream) SetWriteDeadline(time.Time) error  { return nil }
func (s *closeTrackingQUICStream) CancelRead(quic.StreamErrorCode) { s.cancelReads++ }
func (s *closeTrackingQUICStream) Close() error                    { s.closes++; return nil }

func TestQUICLaneCloseReleasesBothStreamDirections(t *testing.T) {
	stream := &closeTrackingQUICStream{}
	lane := &quicStreamConn{stream: stream}
	if err := lane.Close(); err != nil {
		t.Fatal(err)
	}
	if err := lane.Close(); err != nil {
		t.Fatal(err)
	}
	if stream.cancelReads != 1 || stream.closes != 1 {
		t.Fatalf("close called CancelRead %d times and Close %d times, want one each", stream.cancelReads, stream.closes)
	}
}

func TestQUICLaneHalfClosePreservesReadUntilFullClose(t *testing.T) {
	stream := &closeTrackingQUICStream{}
	lane := &quicStreamConn{stream: stream}
	if err := lane.CloseWrite(); err != nil {
		t.Fatal(err)
	}
	if err := lane.CloseWrite(); err != nil {
		t.Fatal(err)
	}
	if stream.closes != 1 || stream.cancelReads != 0 {
		t.Fatalf("half-close called Close %d times and CancelRead %d times, want 1 and 0", stream.closes, stream.cancelReads)
	}
	if err := lane.Close(); err != nil {
		t.Fatal(err)
	}
	if stream.closes != 1 || stream.cancelReads != 1 {
		t.Fatalf("full close called Close %d times and CancelRead %d times, want 1 and 1", stream.closes, stream.cancelReads)
	}
}

func TestQUICPathEvidenceExcludesPeerAndLifecycleFailures(t *testing.T) {
	tests := []struct {
		name string
		err  error
		want quicPathEvidence
	}{
		{name: "success", want: quicPathAvailable},
		{name: "destination response", err: errDestinationUnavailable, want: quicPathAvailable},
		{name: "protocol response", err: peerResponse(errors.New("rejected")), want: quicPathAvailable},
		{name: "caller cancellation", err: context.Canceled, want: quicPathNeutral},
		{name: "peer application close", err: &quic.ApplicationError{Remote: true, ErrorMessage: "server shutdown"}, want: quicPathNeutral},
		{name: "peer transport close", err: &quic.TransportError{Remote: true, ErrorCode: quic.InternalError}, want: quicPathNeutral},
		{name: "stateless reset", err: &quic.StatelessResetError{}, want: quicPathNeutral},
		{name: "stream cancellation", err: &quic.StreamError{Remote: true}, want: quicPathNeutral},
		{name: "plain EOF", err: io.EOF, want: quicPathNeutral},
		{name: "handshake timeout", err: &quic.HandshakeTimeoutError{}, want: quicPathUnavailable},
		{name: "idle timeout", err: fmt.Errorf("wrapped: %w", &quic.IdleTimeoutError{}), want: quicPathUnavailable},
		{name: "attempt deadline", err: context.DeadlineExceeded, want: quicPathUnavailable},
		{name: "local no viable path", err: &quic.TransportError{ErrorCode: quic.NoViablePathError}, want: quicPathUnavailable},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			if got := classifyQUICPathEvidence(test.err); got != test.want {
				t.Fatalf("evidence = %d, want %d", got, test.want)
			}
		})
	}
}

func TestNegativeQUICEvidenceRequiresReachableTCPControl(t *testing.T) {
	tests := []struct {
		name      string
		quic, tcp quicPathEvidence
		want      quicPathEvidence
	}{
		{name: "timed out while TCP worked", quic: quicPathUnavailable, tcp: quicPathAvailable, want: quicPathUnavailable},
		{name: "pending is not negative evidence", tcp: quicPathAvailable, want: quicPathNeutral},
		{name: "peer closed while TCP worked", quic: quicPathNeutral, tcp: quicPathAvailable, want: quicPathNeutral},
		{name: "both transports failed", quic: quicPathUnavailable, tcp: quicPathNeutral, want: quicPathNeutral},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			if got := differentialQUICPathEvidence(test.quic, test.tcp); got != test.want {
				t.Fatalf("evidence = %d, want %d", got, test.want)
			}
		})
	}
}

func TestValidateLocalAddressSpec(t *testing.T) {
	for _, spec := range []string{"", "auto", "if:en0", "192.0.2.10", "2001:db8::10"} {
		if err := validateLocalAddressSpec(spec); err != nil {
			t.Errorf("validateLocalAddressSpec(%q): %v", spec, err)
		}
	}
	for _, spec := range []string{"not-an-address", "if:", "if:   "} {
		if err := validateLocalAddressSpec(spec); err == nil {
			t.Errorf("validateLocalAddressSpec(%q) unexpectedly succeeded", spec)
		}
	}
}

func TestResolveLocalAddressLiteral(t *testing.T) {
	got, err := netbind.ResolveWithInterface("192.0.2.10")
	if err != nil {
		t.Fatal(err)
	}
	if got.Addr.String() != "192.0.2.10" {
		t.Fatalf("resolved literal = %s", got.Addr)
	}
	if got.InterfaceName != "" {
		t.Fatalf("literal IP should have no interface name, got %q", got.InterfaceName)
	}
}

func TestResolveLocalAddressAutoOrInterfaceReportsOperationalState(t *testing.T) {
	// The CI host may have no physical IPv4 interface, or may expose more than
	// one. In either case the important contract is a bounded, actionable error;
	// when auto succeeds it must return an IPv4 address that can be bound.
	got, err := netbind.ResolveWithInterface("auto")
	if err != nil {
		if !strings.Contains(err.Error(), "IPv4") && !strings.Contains(err.Error(), "physical") {
			t.Fatalf("unexpected auto-resolution error: %v", err)
		}
		return
	}
	if !got.Addr.Is4() {
		t.Fatalf("auto selected non-IPv4 address %s", got.Addr)
	}
}

func TestALPNFailureExplainsEndpointOrVersionMismatch(t *testing.T) {
	if defaultALPN != "queqiao/1" {
		t.Fatalf("data ALPN = %q, want first public protocol ALPN", defaultALPN)
	}
	err := explainDataHandshakeError("gateway.example:443", "TCP", errors.New("remote error: tls: no application protocol"))
	message := err.Error()
	if !strings.Contains(message, "protocol 1") || !strings.Contains(message, "gateway.example:443") || !strings.Contains(message, "incompatible") {
		t.Fatalf("unhelpful ALPN error: %v", err)
	}
	original := errors.New("connection refused")
	if got := explainDataHandshakeError("gateway.example:443", "TCP", original); got != original {
		t.Fatalf("non-ALPN error was replaced: %v", got)
	}
}
