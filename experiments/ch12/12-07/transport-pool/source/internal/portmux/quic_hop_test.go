package portmux_test

import (
	"context"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"io"
	"math/big"
	"net"
	"testing"
	"time"

	"github.com/apernet/quic-go"
	"github.com/bojieli/queqiao/internal/portmux"
)

const hopQuicALPN = "queqiao-hop-test"

func hopTestTLSConfig(t *testing.T) *tls.Config {
	t.Helper()
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	tmpl := &x509.Certificate{
		SerialNumber: big.NewInt(1),
		Subject:      pkix.Name{CommonName: "hop-test"},
		NotBefore:    time.Now().Add(-time.Hour),
		NotAfter:     time.Now().Add(time.Hour),
		KeyUsage:     x509.KeyUsageDigitalSignature,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
	}
	der, err := x509.CreateCertificate(rand.Reader, tmpl, tmpl, &key.PublicKey, key)
	if err != nil {
		t.Fatal(err)
	}
	return &tls.Config{
		Certificates: []tls.Certificate{{Certificate: [][]byte{der}, PrivateKey: key}},
		NextProtos:   []string{hopQuicALPN},
	}
}

// serveQUICEcho runs a quic-go listener on conn and echoes one stream back.
func serveQUICEcho(t *testing.T, conn net.PacketConn, tlsCfg *tls.Config) {
	t.Helper()
	listener, err := quic.Listen(conn, tlsCfg, &quic.Config{})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = conn.Close(); _ = listener.Close() })
	go func() {
		for {
			quicConn, err := listener.Accept(context.Background())
			if err != nil {
				return
			}
			go func() {
				for {
					stream, err := quicConn.AcceptStream(context.Background())
					if err != nil {
						return
					}
					go func() {
						defer stream.Close()
						_, _ = io.Copy(stream, stream)
					}()
				}
			}()
		}
	}()
}

func dialQUICEcho(t *testing.T, packetConn net.PacketConn, serverAddr *net.UDPAddr, payload []byte) []byte {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	conn, err := quic.Dial(ctx, packetConn, serverAddr,
		&tls.Config{InsecureSkipVerify: true, NextProtos: []string{hopQuicALPN}}, &quic.Config{})
	if err != nil {
		t.Fatalf("QUIC dial: %v", err)
	}
	defer conn.CloseWithError(0, "")
	stream, err := conn.OpenStreamSync(ctx)
	if err != nil {
		t.Fatalf("open stream: %v", err)
	}
	if _, err := stream.Write(payload); err != nil {
		t.Fatalf("stream write: %v", err)
	}
	if err := stream.Close(); err != nil {
		t.Fatalf("stream close: %v", err)
	}
	got, err := io.ReadAll(stream)
	if err != nil {
		t.Fatalf("stream read: %v", err)
	}
	return got
}

// A client whose every packet goes to a secondary hop port must still
// complete the QUIC handshake: the server mux has to feed hop-port datagrams
// to the listener and route replies back through the same socket.
func TestQUICHandshakeViaSecondaryHopPort(t *testing.T) {
	primary, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	primaryPort := primary.LocalAddr().(*net.UDPAddr).Port
	ports := portmux.HopPorts("hop-itest", primaryPort, 3)
	if len(ports) < 3 {
		t.Fatalf("want at least 3 hop ports, got %v", ports)
	}

	mux, err := portmux.NewServerPortMux(primary, ports)
	if err != nil {
		t.Fatal(err)
	}
	serveQUICEcho(t, mux, hopTestTLSConfig(t))

	serverAddr := &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1), Port: primaryPort}
	clientConn, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	cmux := portmux.NewClientPortMux(clientConn, serverAddr, ports)
	defer cmux.Close()
	// Hop onto a secondary port before sending a single packet.
	from, to := cmux.Hop(1)
	if from != primaryPort || to == primaryPort {
		t.Fatalf("unexpected hop %d -> %d", from, to)
	}

	payload := []byte("echo-over-a-hop-port")
	if got := dialQUICEcho(t, cmux, serverAddr, payload); string(got) != string(payload) {
		t.Fatalf("echo mismatch: got %q want %q", got, payload)
	}
}

// An established connection must survive a mid-session hop: packets start
// arriving on a different server socket and replies must follow them.
func TestQUICConnectionSurvivesMidSessionHop(t *testing.T) {
	primary, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	primaryPort := primary.LocalAddr().(*net.UDPAddr).Port
	ports := portmux.HopPorts("hop-itest-mid", primaryPort, 3)

	mux, err := portmux.NewServerPortMux(primary, ports)
	if err != nil {
		t.Fatal(err)
	}
	serveQUICEcho(t, mux, hopTestTLSConfig(t))

	serverAddr := &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1), Port: primaryPort}
	clientConn, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	cmux := portmux.NewClientPortMux(clientConn, serverAddr, ports)
	defer cmux.Close()

	// Dial on the primary port, open a stream, then hop mid-stream.
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	conn, err := quic.Dial(ctx, cmux, serverAddr,
		&tls.Config{InsecureSkipVerify: true, NextProtos: []string{hopQuicALPN}}, &quic.Config{})
	if err != nil {
		t.Fatalf("QUIC dial: %v", err)
	}
	defer conn.CloseWithError(0, "")
	stream, err := conn.OpenStreamSync(ctx)
	if err != nil {
		t.Fatalf("open stream: %v", err)
	}

	cmux.Hop(2)
	payload := []byte("post-hop-echo")
	if _, err := stream.Write(payload); err != nil {
		t.Fatalf("stream write after hop: %v", err)
	}
	if err := stream.Close(); err != nil {
		t.Fatalf("stream close: %v", err)
	}
	got, err := io.ReadAll(stream)
	if err != nil {
		t.Fatalf("stream read after hop: %v", err)
	}
	if string(got) != string(payload) {
		t.Fatalf("echo mismatch after hop: got %q want %q", got, payload)
	}
}
