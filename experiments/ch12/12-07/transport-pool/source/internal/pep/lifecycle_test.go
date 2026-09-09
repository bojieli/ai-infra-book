package pep

import (
	"context"
	"encoding/binary"
	"io"
	"log/slog"
	"net"
	"runtime"
	"strings"
	"testing"
	"time"
)

// countGoroutines waits briefly for the process to settle, because a released
// flow tears down several goroutines asynchronously and a sample taken too
// early reports a leak that is only a race with shutdown.
func countGoroutines(t *testing.T, want int) int {
	t.Helper()
	deadline := time.Now().Add(5 * time.Second)
	count := runtime.NumGoroutine()
	for time.Now().Before(deadline) {
		count = runtime.NumGoroutine()
		if count <= want {
			return count
		}
		time.Sleep(25 * time.Millisecond)
	}
	return count
}

func goroutineDump() string {
	buf := make([]byte, 1<<20)
	return string(buf[:runtime.Stack(buf, true)])
}

// A proxy runs for months. Every flow starts a writer, a reader, an
// acknowledgement loop, a telemetry loop, a completion watchdog, and a limit
// watcher, and every configured lane starts more; if any of them outlives its
// flow, the process leaks steadily under normal traffic rather than failing
// visibly.
func TestFlowLifecycleDoesNotLeakGoroutines(t *testing.T) {
	destinationListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer destinationListener.Close()
	go echoDestination(destinationListener)

	certificate, roots := testCertificate(t)
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	packetConn, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	server, err := NewServer(ServerConfig{
		ListenAddr: packetConn.LocalAddr().String(), Credentials: certificate,
		DestinationPolicy: DestinationPolicy{AllowPrivate: true}, EnableQUIC: true, Logger: logger,
		HandshakeTimeout: 2 * time.Second,
	})
	if err != nil {
		t.Fatal(err)
	}
	client, err := NewClient(ClientConfig{
		ListenAddr: "127.0.0.1:0", RemoteAddr: packetConn.LocalAddr().String(), Credentials: roots, Transport: TransportQUIC, EnableQUICPool: true, Logger: logger,
		HandshakeTimeout: 2 * time.Second,
	})
	if err != nil {
		t.Fatal(err)
	}
	clientListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	go func() { _ = server.ServePacketConn(ctx, packetConn) }()
	go func() { _ = client.ServeListener(ctx, clientListener) }()

	// One warm-up flow establishes the pooled connection and its long-lived
	// goroutines, so the baseline does not count them as a leak.
	runEchoFlow(t, clientListener.Addr().String(), destinationListener.Addr().String())
	baseline := countGoroutines(t, 0)

	const flows = 12
	for range flows {
		runEchoFlow(t, clientListener.Addr().String(), destinationListener.Addr().String())
	}

	// Allow a generous constant for bookkeeping that legitimately varies, and
	// for what a connection costs once rather than per flow: its coded path
	// runs a send loop, a receive loop, a demultiplexer and a watcher that
	// closes them with the connection. These flows share one pooled
	// connection, so that is a constant here -- and a per-flow leak, which is
	// what this guards, would exceed the whole allowance many times over
	// rather than sitting just inside it.
	const slack = 24
	if got := countGoroutines(t, baseline+slack); got > baseline+slack {
		t.Fatalf("goroutines grew from %d to %d over %d flows, which is more than "+
			"bookkeeping variance:\n%s", baseline, got, flows, goroutineDump())
	}

	client.closeQUICPool()
	cancel()
	_ = clientListener.Close()
	_ = packetConn.Close()
}

// runEchoFlow drives one complete SOCKS flow and closes it.
func runEchoFlow(t *testing.T, socksAddr, destination string) {
	t.Helper()
	conn, err := net.DialTimeout("tcp", socksAddr, 5*time.Second)
	if err != nil {
		t.Fatal(err)
	}
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(15 * time.Second))
	if _, err := conn.Write([]byte{5, 1, 0}); err != nil {
		t.Fatal(err)
	}
	var method [2]byte
	if _, err := io.ReadFull(conn, method[:]); err != nil {
		t.Fatal(err)
	}
	host, portText, _ := net.SplitHostPort(destination)
	ip := net.ParseIP(host).To4()
	port, _ := net.LookupPort("tcp", portText)
	request := []byte{5, 1, 0, 1}
	request = append(request, ip...)
	request = binary.BigEndian.AppendUint16(request, uint16(port))
	if _, err := conn.Write(request); err != nil {
		t.Fatal(err)
	}
	var reply [10]byte
	if _, err := io.ReadFull(conn, reply[:]); err != nil {
		t.Fatal(err)
	}
	if reply[1] != 0 {
		t.Fatalf("SOCKS connect failed: %v", reply)
	}
	payload := []byte(strings.Repeat("lifecycle", 64))
	if _, err := conn.Write(payload); err != nil {
		t.Fatal(err)
	}
	echoed := make([]byte, len(payload))
	if _, err := io.ReadFull(conn, echoed); err != nil {
		t.Fatalf("read echo: %v", err)
	}
}
