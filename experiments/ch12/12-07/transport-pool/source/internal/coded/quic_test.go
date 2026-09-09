package coded

import (
	"context"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"math/big"
	"testing"
	"time"

	"github.com/apernet/quic-go"
	wancongestion "github.com/bojieli/queqiao/internal/congestion"
	"github.com/bojieli/queqiao/internal/pathsim"
)

func testTLS(t *testing.T) (*tls.Config, *tls.Config) {
	t.Helper()
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	template := x509.Certificate{
		SerialNumber: big.NewInt(1),
		Subject:      pkix.Name{CommonName: "coded.test"},
		NotBefore:    time.Now().Add(-time.Hour),
		NotAfter:     time.Now().Add(time.Hour),
		DNSNames:     []string{"coded.test"},
		KeyUsage:     x509.KeyUsageDigitalSignature | x509.KeyUsageCertSign,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
		IsCA:         true,
	}
	der, err := x509.CreateCertificate(rand.Reader, &template, &template, &key.PublicKey, key)
	if err != nil {
		t.Fatal(err)
	}
	leaf, err := x509.ParseCertificate(der)
	if err != nil {
		t.Fatal(err)
	}
	roots := x509.NewCertPool()
	roots.AddCert(leaf)
	server := &tls.Config{
		Certificates: []tls.Certificate{{Certificate: [][]byte{der}, PrivateKey: key, Leaf: leaf}},
		NextProtos:   []string{"coded-test"},
	}
	client := &tls.Config{RootCAs: roots, ServerName: "coded.test", NextProtos: []string{"coded-test"}}
	return server, client
}

// liveChannel is the China-US path as measured on 2026-08-13: a token bucket
// at 25 Mbit/s refilled every 8 ms, with an independent 42% erasure segment
// behind it. See docs/PATH-CHARACTER-20260813.md and
// pathsim.TestTheEmulatorReproducesTheMeasuredPath.
func liveChannel() pathsim.Config {
	return pathsim.Config{
		OneWayDelay:         150 * time.Millisecond,
		RateBytesPerSec:     uint64(25e6 / 8),
		PolicerRefillPeriod: 8 * time.Millisecond,
		LossRate:            0.42,
		Seed:                23,
	}
}

// quicPair brings up a QUIC connection whose packets cross the emulated path.
func quicPair(t *testing.T, cfg pathsim.Config) (client, server *quic.Conn) {
	t.Helper()
	client, server = quicPairWithout(t, cfg)
	// The controller decides whether any of this is reachable. Across this
	// channel a loss-responsive sender gives the path away -- 0.13 Mbit/s for
	// quic-go's default, 5.56 for the BBR port this project ships -- so a
	// measurement taken over one of those measures the controller and not the
	// layer above it.
	client.SetCongestionControl(wancongestion.NewErasureSender(client.InitialPacketSize()))
	server.SetCongestionControl(wancongestion.NewErasureSender(server.InitialPacketSize()))
	return client, server
}

// quicPairWithout leaves the congestion controller to the caller.
func quicPairWithout(t *testing.T, cfg pathsim.Config) (client, server *quic.Conn) {
	t.Helper()
	serverTLS, clientTLS := testTLS(t)
	quicCfg := &quic.Config{
		EnableDatagrams:                true,
		MaxIdleTimeout:                 90 * time.Second,
		KeepAlivePeriod:                5 * time.Second,
		InitialStreamReceiveWindow:     8 << 20,
		InitialConnectionReceiveWindow: 16 << 20,
		MaxStreamReceiveWindow:         64 << 20,
		MaxConnectionReceiveWindow:     128 << 20,
	}

	listener, err := quic.ListenAddr("127.0.0.1:0", serverTLS, quicCfg)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = listener.Close() })

	relay, err := pathsim.New("127.0.0.1:0", listener.Addr().String(), cfg)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = relay.Close() })

	accepted := make(chan *quic.Conn, 1)
	go func() {
		conn, err := listener.Accept(context.Background())
		if err != nil {
			return
		}
		accepted <- conn
	}()

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	client, err = quic.DialAddr(ctx, relay.LocalAddr(), clientTLS, quicCfg)
	if err != nil {
		t.Fatalf("dial across the emulated path: %v", err)
	}
	t.Cleanup(func() { _ = client.CloseWithError(0, "") })

	select {
	case server = <-accepted:
	case <-time.After(30 * time.Second):
		t.Fatal("server did not accept across the emulated path")
	}
	t.Cleanup(func() { _ = server.CloseWithError(0, "") })
	return client, server
}

// Every datagram this path sends has to fit what the connection will
// accept. It is not a tuning question: a datagram over the limit is refused
// rather than fragmented, so a shard sized against a guess disappears, and a
// block that loses its full-size shards never completes. Short frames still go
// through, so the symptom is a session that handshakes and then stalls on its
// first real frame.
func TestNoShardExceedsTheCarriersDatagramLimit(t *testing.T) {
	if testing.Short() {
		t.Skip("brings up QUIC across an emulated 300 ms path")
	}
	client, _ := quicPair(t, liveChannel())
	carrier, err := NewQUICCarrier(client)
	if err != nil {
		t.Fatal(err)
	}
	limit := carrier.MaxDatagramBytes()
	if limit <= 0 || limit >= int(client.InitialPacketSize()) {
		t.Fatalf("carrier limit %d against a packet size of %d", limit, client.InitialPacketSize())
	}
	// A datagram of exactly the limit must be accepted, which is what makes
	// the limit usable rather than merely conservative.
	if err := carrier.Send(make([]byte, limit)); err != nil {
		t.Fatalf("carrier refused a datagram of its own stated limit %d: %v", limit, err)
	}
	// And a path over it must never build a datagram larger than that, for
	// either kind: a repair carries the longer header, so sizing the payload by
	// the source header alone would put every repair over the limit.
	p := New(carrier, Config{SymbolBytes: DefaultDatagramBytes, RoundTrip: 300 * time.Millisecond})
	defer p.Close()
	if got := p.symbolPayload() + symbolHeader + repairHeader; got > limit {
		t.Fatalf("path builds %d-byte datagrams against a carrier limit of %d", got, limit)
	}
}
