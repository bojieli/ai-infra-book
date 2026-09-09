package baseline

import (
	"bytes"
	"context"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/binary"
	"encoding/pem"
	"io"
	"log/slog"
	"math/big"
	"net"
	"testing"
	"time"
)

func testCertificate(t *testing.T) (tls.Certificate, *x509.CertPool) {
	t.Helper()
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	template := &x509.Certificate{
		SerialNumber: big.NewInt(1),
		Subject:      pkix.Name{CommonName: "queqiao.test"},
		DNSNames:     []string{"queqiao.test"},
		NotBefore:    time.Now().Add(-time.Minute),
		NotAfter:     time.Now().Add(time.Hour),
		KeyUsage:     x509.KeyUsageDigitalSignature | x509.KeyUsageKeyEncipherment,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
	}
	der, err := x509.CreateCertificate(rand.Reader, template, template, &key.PublicKey, key)
	if err != nil {
		t.Fatal(err)
	}
	keyDER, err := x509.MarshalPKCS8PrivateKey(key)
	if err != nil {
		t.Fatal(err)
	}
	certPEM := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})
	keyPEM := pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: keyDER})
	certificate, err := tls.X509KeyPair(certPEM, keyPEM)
	if err != nil {
		t.Fatal(err)
	}
	roots := x509.NewCertPool()
	if !roots.AppendCertsFromPEM(certPEM) {
		t.Fatal("append test certificate")
	}
	return certificate, roots
}

// echoDestination is the origin the reference proxy relays to.
func echoDestination(t *testing.T) net.Listener {
	t.Helper()
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = listener.Close() })
	go func() {
		for {
			conn, err := listener.Accept()
			if err != nil {
				return
			}
			go func() {
				defer conn.Close()
				_, _ = io.Copy(conn, conn)
			}()
		}
	}()
	return listener
}

type harness struct {
	socks string
	token []byte
}

// referenceDialTimeout bounds the loopback QUIC handshake these tests need.
//
// It was 5s, which is half the production default, so the harness held the
// reference to a stricter bound than the thing it is a control for -- and on
// macos-15-intel one handshake missed it, surfacing as SOCKS5 reply code 1
// after exactly 5.00s. Nothing here wants a tight bound: the dial is to a
// loopback listener in the same process, and the timeout exists only so a
// wedged dial fails instead of hanging. Take the production default rather
// than inventing a stricter number for a slower machine.
const referenceDialTimeout = defaultDialTimeout

func startReference(t *testing.T, token []byte) harness {
	t.Helper()
	certificate, roots := testCertificate(t)
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	packet, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	server, err := NewServer(ServerConfig{
		ListenAddr: packet.LocalAddr().String(), Certificate: certificate,
		Token: token, Transport: TUICTransport(), Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	socksListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	client, err := NewClient(ClientConfig{
		ListenAddr: socksListener.Addr().String(), RemoteAddr: packet.LocalAddr().String(),
		ServerName: "queqiao.test", RootCAs: roots, Token: token,
		Transport: TUICTransport(), DialTimeout: referenceDialTimeout, Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	go func() { _ = server.Serve(ctx, packet) }()
	go func() { _ = client.ServeListener(ctx, socksListener) }()
	t.Cleanup(func() {
		client.Close()
		cancel()
		_ = socksListener.Close()
		_ = packet.Close()
	})
	return harness{socks: socksListener.Addr().String(), token: token}
}

func socksConnect(t *testing.T, socksAddr, destination string) net.Conn {
	t.Helper()
	conn, err := net.DialTimeout("tcp", socksAddr, 5*time.Second)
	if err != nil {
		t.Fatal(err)
	}
	_ = conn.SetDeadline(time.Now().Add(15 * time.Second))
	host, port, err := net.SplitHostPort(destination)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := conn.Write([]byte{5, 1, 0}); err != nil {
		t.Fatal(err)
	}
	var method [2]byte
	if _, err := io.ReadFull(conn, method[:]); err != nil {
		t.Fatal(err)
	}
	portNumber := 0
	for _, r := range port {
		portNumber = portNumber*10 + int(r-'0')
	}
	request := []byte{5, 1, 0, 3, byte(len(host))}
	request = append(request, host...)
	request = binary.BigEndian.AppendUint16(request, uint16(portNumber))
	if _, err := conn.Write(request); err != nil {
		t.Fatal(err)
	}
	reply := make([]byte, 4)
	if _, err := io.ReadFull(conn, reply); err != nil {
		t.Fatal(err)
	}
	if reply[1] != 0 {
		t.Fatalf("SOCKS5 reply code = %d, want success", reply[1])
	}
	// Skip the bound address.
	skip := 4 + 2
	if reply[3] == 4 {
		skip = 16 + 2
	}
	if _, err := io.CopyN(io.Discard, conn, int64(skip)); err != nil {
		t.Fatal(err)
	}
	return conn
}

func TestReferenceRelaysBytesBothWays(t *testing.T) {
	destination := echoDestination(t)
	token := make([]byte, tokenSize)
	h := startReference(t, token)

	conn := socksConnect(t, h.socks, destination.Addr().String())
	defer conn.Close()
	payload := bytes.Repeat([]byte("reference"), 4096)
	go func() { _, _ = conn.Write(payload) }()
	echoed := make([]byte, len(payload))
	if _, err := io.ReadFull(conn, echoed); err != nil {
		t.Fatalf("read echo: %v", err)
	}
	if !bytes.Equal(echoed, payload) {
		t.Fatal("echoed bytes differ from what was sent")
	}
}

// The reference multiplexes several relayed connections onto one QUIC
// connection, exactly as TUIC does. If a later stream were mistakenly asked to
// authenticate, or the first stream's token were reused, the control would be
// measuring something other than TUIC's shape.
func TestReferenceMultiplexesLaterStreams(t *testing.T) {
	destination := echoDestination(t)
	token := make([]byte, tokenSize)
	for i := range token {
		token[i] = byte(i)
	}
	h := startReference(t, token)

	for attempt := range 3 {
		conn := socksConnect(t, h.socks, destination.Addr().String())
		payload := []byte{byte(attempt), 'x', 'y', 'z'}
		if _, err := conn.Write(payload); err != nil {
			t.Fatalf("stream %d write: %v", attempt, err)
		}
		echoed := make([]byte, len(payload))
		if _, err := io.ReadFull(conn, echoed); err != nil {
			t.Fatalf("stream %d read: %v", attempt, err)
		}
		if !bytes.Equal(echoed, payload) {
			t.Fatalf("stream %d echoed %v, want %v", attempt, echoed, payload)
		}
		_ = conn.Close()
	}
}

// A control that accepts an unauthenticated client would silently stop being a
// control.
func TestReferenceRejectsAWrongToken(t *testing.T) {
	destination := echoDestination(t)
	serverToken := make([]byte, tokenSize)
	for i := range serverToken {
		serverToken[i] = 1
	}
	certificate, roots := testCertificate(t)
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	packet, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer packet.Close()
	server, err := NewServer(ServerConfig{
		ListenAddr: packet.LocalAddr().String(), Certificate: certificate,
		Token: serverToken, Transport: TUICTransport(), Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	socksListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer socksListener.Close()
	clientToken := make([]byte, tokenSize) // all zeroes: deliberately wrong
	client, err := NewClient(ClientConfig{
		ListenAddr: socksListener.Addr().String(), RemoteAddr: packet.LocalAddr().String(),
		ServerName: "queqiao.test", RootCAs: roots, Token: clientToken,
		Transport: TUICTransport(), DialTimeout: 3 * time.Second, Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	defer client.Close()
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	go func() { _ = server.Serve(ctx, packet) }()
	go func() { _ = client.ServeListener(ctx, socksListener) }()

	conn := socksConnect(t, socksListener.Addr().String(), destination.Addr().String())
	defer conn.Close()
	// The server drops the stream instead of relaying, so the read ends
	// without the echo ever arriving.
	_ = conn.SetDeadline(time.Now().Add(5 * time.Second))
	if _, err := conn.Write([]byte("should not be relayed")); err != nil {
		return // an immediate write failure is an equally valid rejection
	}
	buf := make([]byte, 8)
	if _, err := io.ReadFull(conn, buf); err == nil {
		t.Fatal("a wrong token was relayed")
	}
}

func TestNewClientAndServerRejectAShortToken(t *testing.T) {
	if _, err := NewServer(ServerConfig{Token: []byte("short")}); err == nil {
		t.Fatal("server accepted a short token")
	}
	if _, err := NewClient(ClientConfig{Token: []byte("short")}); err == nil {
		t.Fatal("client accepted a short token")
	}
}

// The reference exists to reproduce TUIC's transport settings; if these drift,
// every comparison against it silently changes meaning.
func TestTUICTransportMatchesPublishedDefaults(t *testing.T) {
	transport := TUICTransport()
	if transport.SendWindow != 16*1024*1024 {
		t.Fatalf("send window = %d, want TUIC's 16 MiB", transport.SendWindow)
	}
	if transport.StreamReceiveWindow != 8*1024*1024 {
		t.Fatalf("stream receive window = %d, want TUIC's 8 MiB", transport.StreamReceiveWindow)
	}
	if transport.InitialPacketSize != 1200 {
		t.Fatalf("initial packet size = %d, want TUIC's 1200", transport.InitialPacketSize)
	}
	cfg := transport.quicConfig()
	// quinn's stream_receive_window has no ramp, so the initial and maximum
	// windows must be identical or the control would auto-tune where TUIC
	// does not.
	if cfg.InitialStreamReceiveWindow != cfg.MaxStreamReceiveWindow {
		t.Fatalf("stream window ramps from %d to %d; TUIC's does not ramp",
			cfg.InitialStreamReceiveWindow, cfg.MaxStreamReceiveWindow)
	}
	if cfg.InitialConnectionReceiveWindow != cfg.MaxConnectionReceiveWindow {
		t.Fatalf("connection window ramps from %d to %d; TUIC's does not ramp",
			cfg.InitialConnectionReceiveWindow, cfg.MaxConnectionReceiveWindow)
	}
	if !cfg.DisablePathMTUDiscovery {
		t.Fatal("MTU probing is enabled; TUIC's default disables it")
	}
}
