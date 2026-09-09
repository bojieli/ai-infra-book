package pep

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"encoding/binary"
	"encoding/pem"
	"errors"
	"io"
	"log/slog"
	"net"
	"strconv"
	"sync/atomic"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/metrics"
	"github.com/bojieli/queqiao/internal/protocol"
	"github.com/bojieli/queqiao/internal/socks5"
)

func testCertificate(t *testing.T) (identity.ServerCredentials, identity.ClientCredentials) {
	t.Helper()
	now := time.Now()
	provider, err := identity.InitProvider(t.TempDir()+"/provider", "test provider", "127.0.0.1:1", now)
	if err != nil {
		t.Fatal(err)
	}
	account, err := provider.Store.AddAccount("test account", time.Time{}, identity.AccountLimits{}, now)
	if err != nil {
		t.Fatal(err)
	}
	_, invitation, err := provider.CreateInvitation(account.ID, time.Hour, now)
	if err != nil {
		t.Fatal(err)
	}
	publicKey, privateKey, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	_, device, err := provider.Store.ConsumeInvite(invitation.Token, "test device", publicKey, now)
	if err != nil {
		t.Fatal(err)
	}
	certPEM, err := provider.IssueDevice(account.ID, device.ID, publicKey, now)
	if err != nil {
		t.Fatal(err)
	}
	keyDER, err := x509.MarshalPKCS8PrivateKey(privateKey)
	if err != nil {
		t.Fatal(err)
	}
	keyPEM := pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: keyDER})
	deviceCertificate, err := tls.X509KeyPair(certPEM, keyPEM)
	if err != nil {
		t.Fatal(err)
	}
	client := identity.ClientCredentials{
		ProviderID: provider.Metadata.ProviderID, GatewayID: provider.Metadata.GatewayID,
		Certificate: deviceCertificate, Root: provider.RootCert, RootPin: provider.Metadata.RootPin,
	}
	return provider.ServerCredentials(), client
}

func discardDestination(listener net.Listener) {
	for {
		conn, err := listener.Accept()
		if err != nil {
			return
		}
		go func() {
			_, _ = io.Copy(io.Discard, conn)
			_ = conn.Close()
		}()
	}
}

func TestTLSOneLaneSOCKSEndToEnd(t *testing.T) {
	destinationListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer destinationListener.Close()
	go func() {
		for {
			conn, acceptErr := destinationListener.Accept()
			if acceptErr != nil {
				return
			}
			go func() {
				defer conn.Close()
				_, _ = io.Copy(conn, conn)
			}()
		}
	}()

	certificate, roots := testCertificate(t)
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	server, err := NewServer(ServerConfig{
		ListenAddr: "127.0.0.1:0", Credentials: certificate,
		DestinationPolicy: DestinationPolicy{AllowPrivate: true}, Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	serverListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	client, err := NewClient(ClientConfig{
		ListenAddr: "127.0.0.1:0", RemoteAddr: serverListener.Addr().String(), Credentials: roots, Logger: logger,
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
	errorsCh := make(chan error, 2)
	go func() { errorsCh <- server.ServeListener(ctx, serverListener) }()
	go func() { errorsCh <- client.ServeListener(ctx, clientListener) }()

	conn, err := net.DialTimeout("tcp", clientListener.Addr().String(), 2*time.Second)
	if err != nil {
		t.Fatal(err)
	}
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(5 * time.Second))
	if _, err := conn.Write([]byte{5, 1, 0}); err != nil {
		t.Fatal(err)
	}
	var method [2]byte
	if _, err := io.ReadFull(conn, method[:]); err != nil {
		t.Fatal(err)
	}
	if method != [2]byte{5, 0} {
		t.Fatalf("method response %v", method)
	}
	host, portText, _ := net.SplitHostPort(destinationListener.Addr().String())
	ip := net.ParseIP(host).To4()
	port, _ := net.LookupPort("tcp", portText)
	request := []byte{5, 1, 0, 1}
	request = append(request, ip...)
	var portBytes [2]byte
	binary.BigEndian.PutUint16(portBytes[:], uint16(port))
	request = append(request, portBytes[:]...)
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

	payload := bytes.Repeat([]byte("queqiao-one-lane-"), 8192)
	if _, err := conn.Write(payload); err != nil {
		t.Fatal(err)
	}
	if tcp, ok := conn.(*net.TCPConn); ok {
		if err := tcp.CloseWrite(); err != nil {
			t.Fatal(err)
		}
	}
	got, err := io.ReadAll(conn)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(got, payload) {
		t.Fatalf("echo mismatch: got %d bytes, want %d", len(got), len(payload))
	}

	cancel()
	for range 2 {
		if err := <-errorsCh; err != nil {
			t.Fatalf("service shutdown: %v", err)
		}
	}
}

func TestUDPAssociateSOCKSEndToEnd(t *testing.T) {
	runUDPAssociateSOCKSEndToEnd(t, TransportTCP)
}

func TestUDPAssociateQUICSOCKSEndToEnd(t *testing.T) {
	runUDPAssociateSOCKSEndToEnd(t, TransportQUIC)
}

func runUDPAssociateSOCKSEndToEnd(t *testing.T, transport TransportKind) {
	destination, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.ParseIP("127.0.0.1")})
	if err != nil {
		t.Fatal(err)
	}
	defer destination.Close()
	go func() {
		buf := make([]byte, 2048)
		for {
			n, addr, readErr := destination.ReadFromUDP(buf)
			if readErr != nil {
				return
			}
			_, _ = destination.WriteToUDP(buf[:n], addr)
		}
	}()

	certificate, roots := testCertificate(t)
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	var serverListener net.Listener
	var serverPacketConn net.PacketConn
	if transport == TransportQUIC {
		serverPacketConn, err = net.ListenPacket("udp", "127.0.0.1:0")
	} else {
		serverListener, err = net.Listen("tcp", "127.0.0.1:0")
	}
	if err != nil {
		t.Fatal(err)
	}
	serverAddr := serverListenerAddr(serverListener, serverPacketConn)
	server, err := NewServer(ServerConfig{
		ListenAddr: serverAddr, Credentials: certificate,
		DestinationPolicy: DestinationPolicy{AllowPrivate: true}, EnableTCP: transport != TransportQUIC, EnableQUIC: transport != TransportTCP, Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	clientListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	client, err := NewClient(ClientConfig{
		ListenAddr: clientListener.Addr().String(), RemoteAddr: serverAddr, Credentials: roots, Transport: transport, EnableQUICPool: transport == TransportQUIC, Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	errorsCh := make(chan error, 2)
	if transport == TransportQUIC {
		go func() { errorsCh <- server.ServePacketConn(ctx, serverPacketConn) }()
	} else {
		go func() { errorsCh <- server.ServeListener(ctx, serverListener) }()
	}
	go func() { errorsCh <- client.ServeListener(ctx, clientListener) }()

	control, err := net.DialTimeout("tcp", clientListener.Addr().String(), 2*time.Second)
	if err != nil {
		t.Fatal(err)
	}
	defer control.Close()
	_ = control.SetDeadline(time.Now().Add(5 * time.Second))
	if _, err := control.Write([]byte{5, 1, 0}); err != nil {
		t.Fatal(err)
	}
	var method [2]byte
	if _, err := io.ReadFull(control, method[:]); err != nil || method != [2]byte{5, 0} {
		t.Fatalf("method response %v err=%v", method, err)
	}
	if _, err := control.Write([]byte{5, socks5.CommandUDPAssociate, 0, 1, 0, 0, 0, 0, 0, 0}); err != nil {
		t.Fatal(err)
	}
	var reply [10]byte
	if _, err := io.ReadFull(control, reply[:]); err != nil {
		t.Fatal(err)
	}
	if reply[1] != socks5.ReplySucceeded {
		t.Fatalf("UDP associate failed: %v", reply)
	}
	bound := net.JoinHostPort(net.IP(reply[4:8]).String(), strconv.Itoa(int(binary.BigEndian.Uint16(reply[8:10]))))
	udpClient, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.ParseIP("127.0.0.1")})
	if err != nil {
		t.Fatal(err)
	}
	defer udpClient.Close()
	host, portText, _ := net.SplitHostPort(destination.LocalAddr().String())
	port, _ := strconv.Atoi(portText)
	request := []byte{0, 0, 0, 1}
	request = append(request, net.ParseIP(host).To4()...)
	var portBytes [2]byte
	binary.BigEndian.PutUint16(portBytes[:], uint16(port))
	request = append(request, portBytes[:]...)
	request = append(request, []byte("udp-echo")...)
	if _, err := udpClient.WriteToUDP(request, mustUDPAddr(t, bound)); err != nil {
		t.Fatal(err)
	}
	buf := make([]byte, 2048)
	_ = udpClient.SetReadDeadline(time.Now().Add(5 * time.Second))
	n, _, err := udpClient.ReadFromUDP(buf)
	if err != nil {
		t.Fatal(err)
	}
	got, err := socks5.ReadUDPDatagram(buf[:n])
	if err != nil {
		t.Fatal(err)
	}
	if string(got.Payload) != "udp-echo" {
		t.Fatalf("UDP payload %q", got.Payload)
	}
	cancel()
	for range 2 {
		if err := <-errorsCh; err != nil {
			t.Fatalf("service shutdown: %v", err)
		}
	}
	if snapshot := server.Metrics().Snapshot(); snapshot.FlowsFailed != 0 {
		t.Fatalf("clean UDP association counted as failed: %+v", snapshot)
	}
}

func serverListenerAddr(listener net.Listener, packetConn net.PacketConn) string {
	if listener != nil {
		return listener.Addr().String()
	}
	return packetConn.LocalAddr().String()
}

func mustUDPAddr(t *testing.T, address string) *net.UDPAddr {
	t.Helper()
	addr, err := net.ResolveUDPAddr("udp", address)
	if err != nil {
		t.Fatal(err)
	}
	return addr
}

// listenTCPAndUDPOnOnePort reserves one port number for both TCP and UDP.
//
// The port is chosen by the UDP allocator, and TCP is bound onto it -- not the
// other way around. Windows reserves contiguous excluded port ranges at boot,
// Hyper-V and WinNAT among them, and a bind inside one fails with WSAEACCES
// even though nothing holds the port. Asking TCP for an ephemeral port and then
// forcing UDP onto that number walked into them: the ephemeral allocator hands
// out ports close to sequentially, so all twenty retries landed in the same
// excluded band and every one of them failed.
//
// Letting UDP choose the port only moved which side fails. The exclusions are
// per protocol, so a kernel-chosen UDP port can still be excluded for TCP, and
// then the retry walks the same band for the same reason: 49737, 49757, 49777
// and 49827 on one Windows runner, four attempts marching through one
// reservation. The port has to be free in both protocols, and retrying next to
// the last failure will not find one while the reservation is wider than the
// walk.
//
// So the retry escapes the band rather than walking it. Sockets that failed are
// held open until the loop finishes, which stops the allocator from offering
// the same number twice; and once the kernel's own range has disappointed us
// several times, the remaining attempts pick a port at random from below that
// range, where the dynamic reservations are not. Random rather than sequential,
// because the thing being avoided is contiguous.
func listenTCPAndUDPOnOnePort(t *testing.T) (net.Listener, net.PacketConn) {
	t.Helper()
	var lastErr error
	var held []net.PacketConn
	defer func() {
		for _, conn := range held {
			_ = conn.Close()
		}
	}()
	const kernelChosenAttempts = 8
	for attempt := range 40 {
		address := "127.0.0.1:0"
		if attempt >= kernelChosenAttempts {
			address = "127.0.0.1:" + strconv.Itoa(portBelowTheDynamicRange(t))
		}
		packetConn, err := net.ListenPacket("udp", address)
		if err != nil {
			lastErr = err
			continue
		}
		listener, err := net.Listen("tcp", packetConn.LocalAddr().String())
		if err == nil {
			t.Cleanup(func() {
				_ = packetConn.Close()
				_ = listener.Close()
			})
			return listener, packetConn
		}
		lastErr = err
		held = append(held, packetConn)
	}
	t.Fatalf("could not reserve one TCP/UDP test port: %v", lastErr)
	return nil, nil
}

// portBelowTheDynamicRange returns a port under 49152, which is where the
// Windows dynamic range begins and therefore where the reservations inside it
// begin. A port down here may well be in use by something else on the machine,
// which is what the caller's retry is for; what it is not is administratively
// excluded before anything binds it.
func portBelowTheDynamicRange(t *testing.T) int {
	t.Helper()
	const low, span = 20000, 25000
	var pick [2]byte
	if _, err := rand.Read(pick[:]); err != nil {
		t.Fatal(err)
	}
	return low + int(binary.BigEndian.Uint16(pick[:]))%span
}

func TestQUICOneLaneSOCKSEndToEnd(t *testing.T) {
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
		ListenAddr: "127.0.0.1:0", Credentials: certificate,
		DestinationPolicy: DestinationPolicy{AllowPrivate: true}, EnableQUIC: true, Logger: logger,
		Metrics: metrics.New(), HandshakeTimeout: 300 * time.Millisecond,
	})
	if err != nil {
		t.Fatal(err)
	}
	clientListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	client, err := NewClient(ClientConfig{
		ListenAddr: clientListener.Addr().String(), RemoteAddr: packetConn.LocalAddr().String(), Credentials: roots, Transport: TransportQUIC, EnableQUICPool: true, Logger: logger,
		Metrics: metrics.New(),
	})
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	errorsCh := make(chan error, 2)
	go func() { errorsCh <- server.ServePacketConn(ctx, packetConn) }()
	go func() { errorsCh <- client.ServeListener(ctx, clientListener) }()

	conn, err := net.DialTimeout("tcp", clientListener.Addr().String(), 2*time.Second)
	if err != nil {
		t.Fatal(err)
	}
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(5 * time.Second))
	if _, err := conn.Write([]byte{5, 1, 0}); err != nil {
		t.Fatal(err)
	}
	var method [2]byte
	if _, err := io.ReadFull(conn, method[:]); err != nil {
		t.Fatal(err)
	}
	if method != [2]byte{5, 0} {
		t.Fatalf("method response %v", method)
	}
	host, portText, _ := net.SplitHostPort(destinationListener.Addr().String())
	ip := net.ParseIP(host).To4()
	port, _ := strconv.Atoi(portText)
	request := []byte{5, 1, 0, 1}
	request = append(request, ip...)
	var portBytes [2]byte
	binary.BigEndian.PutUint16(portBytes[:], uint16(port))
	request = append(request, portBytes[:]...)
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
	// The per-stream authentication timeout must not be used as a timer for
	// accepting the next QUIC stream. Keep this established flow idle beyond
	// that bound, then prove that the same stream still transfers data. The old
	// behavior closed the whole connection with "queqiao session complete".
	time.Sleep(750 * time.Millisecond)
	payload := bytes.Repeat([]byte("queqiao-quic-"), 8192)
	if _, err := conn.Write(payload); err != nil {
		t.Fatal(err)
	}
	if tcp, ok := conn.(*net.TCPConn); ok {
		if err := tcp.CloseWrite(); err != nil {
			t.Fatal(err)
		}
	}
	got, err := io.ReadAll(conn)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(got, payload) {
		t.Fatalf("echo mismatch: got %d bytes, want %d", len(got), len(payload))
	}
	// This used to assert that a second lane had been joined. A flow's data
	// lives on one lane now, and the only reason a second appears is bulk
	// isolation, which TestBulkIsolationAppliesAtOneConfiguredLane covers and
	// which needs another flow on the pool to be worth doing. What this test
	// is for is that a pooled QUIC flow transfers correctly, which it just
	// checked.
	// A second logical flow must reuse the pooled QUIC connection without
	// disturbing the first flow's session or destination stream.
	conn2 := dialTestSOCKS(t, clientListener.Addr().String(), destinationListener.Addr().String())
	defer conn2.Close()
	payload2 := bytes.Repeat([]byte("queqiao-pooled-flow-"), 1024)
	if _, err := conn2.Write(payload2); err != nil {
		t.Fatal(err)
	}
	if tcp, ok := conn2.(*net.TCPConn); ok {
		if err := tcp.CloseWrite(); err != nil {
			t.Fatal(err)
		}
	}
	got2, err := io.ReadAll(conn2)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(got2, payload2) {
		t.Fatalf("pooled flow echo mismatch: got %d bytes, want %d", len(got2), len(payload2))
	}
	// A completed logical flow must release its worker goroutines and active
	// gauge promptly even when the final ACK races with physical lane close.
	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		if server.Metrics().Snapshot().ActiveFlows == 0 && client.Metrics().Snapshot().ActiveFlows == 0 {
			break
		}
		time.Sleep(10 * time.Millisecond)
	}
	if got := server.Metrics().Snapshot(); got.ActiveFlows != 0 || got.FlowsCompleted != 2 {
		t.Fatalf("server flow lifecycle leaked: active=%d started=%d completed=%d failed=%d", got.ActiveFlows, got.FlowsStarted, got.FlowsCompleted, got.FlowsFailed)
	}
	if got := client.Metrics().Snapshot(); got.ActiveFlows != 0 || got.FlowsCompleted != 2 {
		t.Fatalf("client flow lifecycle leaked: active=%d started=%d completed=%d failed=%d", got.ActiveFlows, got.FlowsStarted, got.FlowsCompleted, got.FlowsFailed)
	}
	cancel()
	for range 2 {
		if err := <-errorsCh; err != nil {
			t.Fatalf("service shutdown: %v", err)
		}
	}
}

func TestQUICFlowSurvivesOneLaneFailure(t *testing.T) {
	destinationListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer destinationListener.Close()
	go slowEchoDestination(destinationListener)

	certificate, roots := testCertificate(t)
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	packetConn, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	server, err := NewServer(ServerConfig{
		ListenAddr: "127.0.0.1:0", Credentials: certificate,
		DestinationPolicy: DestinationPolicy{AllowPrivate: true}, EnableQUIC: true, ChunkSize: 4 * 1024, Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	clientListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	client, err := NewClient(ClientConfig{
		ListenAddr: clientListener.Addr().String(), RemoteAddr: packetConn.LocalAddr().String(), Credentials: roots, Transport: TransportQUIC, ChunkSize: 4 * 1024, Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	errorsCh := make(chan error, 2)
	go func() { errorsCh <- server.ServePacketConn(ctx, packetConn) }()
	go func() { errorsCh <- client.ServeListener(ctx, clientListener) }()

	conn := dialTestSOCKS(t, clientListener.Addr().String(), destinationListener.Addr().String())
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(15 * time.Second))
	payload := bytes.Repeat([]byte("queqiao-lane-recovery-"), 128*1024)
	writeErr := make(chan error, 1)
	go func() {
		_, err := conn.Write(payload)
		if tcp, ok := conn.(*net.TCPConn); ok && err == nil {
			err = tcp.CloseWrite()
		}
		writeErr <- err
	}()

	// Kill the flow's only lane. This used to wait for a second one and close
	// the spare, which meant the transfer never actually lost the lane it was
	// using -- the other one absorbed it. With a flow's data on one lane there
	// is no spare, so closing it is a real failure and the transfer completes
	// only if recovery opens a replacement and the session replays what the
	// peer had not acknowledged onto it. That is a stronger test of the path
	// this exists to cover.
	deadline := time.Now().Add(5 * time.Second)
	var failedLane *mpLane
	for time.Now().Before(deadline) && failedLane == nil {
		server.sessionsMu.RLock()
		for _, sessionFlow := range server.sessions {
			if lanes := sessionFlow.flow.healthyLanes(); len(lanes) >= 1 {
				failedLane = lanes[0]
				break
			}
		}
		server.sessionsMu.RUnlock()
		if failedLane == nil {
			time.Sleep(10 * time.Millisecond)
		}
	}
	if failedLane == nil {
		t.Fatal("no flow was established")
	}
	if err := failedLane.fc.Close(); err != nil && !errors.Is(err, net.ErrClosed) {
		t.Fatal(err)
	}
	if err := <-writeErr; err != nil {
		t.Fatal(err)
	}
	got, err := io.ReadAll(conn)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(got, payload) {
		t.Fatalf("recovered echo mismatch: got %d bytes, want %d", len(got), len(payload))
	}

	cancel()
	for range 2 {
		if err := <-errorsCh; err != nil {
			t.Fatalf("service shutdown: %v", err)
		}
	}
}

func TestAutoTransportFallsBackToTCPWhenUDPUnavailable(t *testing.T) {
	destinationListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer destinationListener.Close()
	go echoDestination(destinationListener)

	certificate, roots := testCertificate(t)
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	serverListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	server, err := NewServer(ServerConfig{
		ListenAddr: serverListener.Addr().String(), Credentials: certificate,
		DestinationPolicy: DestinationPolicy{AllowPrivate: true}, EnableTCP: true, EnableQUIC: false, Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	clientListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	client, err := NewClient(ClientConfig{
		ListenAddr: clientListener.Addr().String(), RemoteAddr: serverListener.Addr().String(), Credentials: roots, Transport: TransportAuto, FallbackDelay: 10 * time.Millisecond, Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	errorsCh := make(chan error, 2)
	go func() { errorsCh <- server.ServeListener(ctx, serverListener) }()
	go func() { errorsCh <- client.ServeListener(ctx, clientListener) }()

	conn := dialTestSOCKS(t, clientListener.Addr().String(), destinationListener.Addr().String())
	defer conn.Close()
	payload := []byte("auto-fallback")
	if _, err := conn.Write(payload); err != nil {
		t.Fatal(err)
	}
	if tcp, ok := conn.(*net.TCPConn); ok {
		if err := tcp.CloseWrite(); err != nil {
			t.Fatal(err)
		}
	}
	got, err := io.ReadAll(conn)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(got, payload) {
		t.Fatalf("fallback echo mismatch: got %q, want %q", got, payload)
	}

	cancel()
	for range 2 {
		if err := <-errorsCh; err != nil {
			t.Fatalf("service shutdown: %v", err)
		}
	}
}

func TestAutoFlowInstallsTCPRescueAfterAllQUICLanesFail(t *testing.T) {
	destinationListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer destinationListener.Close()
	go slowEchoDestination(destinationListener)

	certificate, roots := testCertificate(t)
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	serverListener, packetConn := listenTCPAndUDPOnOnePort(t)
	server, err := NewServer(ServerConfig{
		ListenAddr: serverListener.Addr().String(), Credentials: certificate,
		DestinationPolicy: DestinationPolicy{AllowPrivate: true}, EnableTCP: true, EnableQUIC: true, ChunkSize: 4 * 1024, Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	clientListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	client, err := NewClient(ClientConfig{
		ListenAddr: clientListener.Addr().String(), RemoteAddr: serverListener.Addr().String(), Credentials: roots, Transport: TransportAuto, FallbackDelay: 300 * time.Millisecond, ChunkSize: 4 * 1024, Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	errorsCh := make(chan error, 3)
	go func() { errorsCh <- server.ServeListener(ctx, serverListener) }()
	go func() { errorsCh <- server.ServePacketConn(ctx, packetConn) }()
	go func() { errorsCh <- client.ServeListener(ctx, clientListener) }()

	conn := dialTestSOCKS(t, clientListener.Addr().String(), destinationListener.Addr().String())
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(15 * time.Second))
	payload := bytes.Repeat([]byte("queqiao-auto-rescue-"), 32*1024)
	writeErr := make(chan error, 1)
	go func() {
		_, writeErrValue := conn.Write(payload)
		if tcp, ok := conn.(*net.TCPConn); ok && writeErrValue == nil {
			writeErrValue = tcp.CloseWrite()
		}
		writeErr <- writeErrValue
	}()

	// Every healthy lane is examined rather than only the first. healthyLanes
	// sorts by lane id and the QUIC lane is created first, so the original
	// lane keeps position zero until it is evicted -- which means a rescue
	// could be fully installed while a check of lanes[0] still reported a
	// QUIC lane. That asked whether the rescue happens to sort first, not
	// whether it happened, and it is why this test failed roughly half the
	// time on the CI runner while passing everywhere else.
	deadline := time.Now().Add(20 * time.Second)
	closedQUIC := false
	rescuedTCP := false
	for time.Now().Before(deadline) {
		server.sessionsMu.RLock()
		var sessionFlow *serverFlow
		for _, candidate := range server.sessions {
			sessionFlow = candidate
			break
		}
		var quicLane *mpLane
		haveTCP := false
		if sessionFlow != nil {
			for _, lane := range sessionFlow.flow.healthyLanes() {
				switch lane.kind {
				case TransportQUIC:
					if quicLane == nil {
						quicLane = lane
					}
				case TransportTCP:
					haveTCP = true
				}
			}
		}
		server.sessionsMu.RUnlock()
		if quicLane != nil && !closedQUIC {
			_ = quicLane.fc.Close()
			closedQUIC = true
		}
		if closedQUIC && haveTCP {
			rescuedTCP = true
			break
		}
		time.Sleep(10 * time.Millisecond)
	}
	if !closedQUIC {
		t.Fatal("initial QUIC lane was not established")
	}
	if !rescuedTCP {
		t.Fatal("TCP rescue lane was not established")
	}

	if err := <-writeErr; err != nil {
		t.Fatal(err)
	}
	got, err := io.ReadAll(conn)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(got, payload) {
		t.Fatalf("TCP rescue echo mismatch: got %d bytes, want %d", len(got), len(payload))
	}

	cancel()
	for i := 0; i < 3; i++ {
		if err := <-errorsCh; err != nil {
			t.Fatalf("service shutdown: %v", err)
		}
	}
}

func TestCompletedFlowTombstoneReplaysFinalAck(t *testing.T) {
	destinationListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer destinationListener.Close()
	go echoDestination(destinationListener)

	certificate, roots := testCertificate(t)
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	serverListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	server, err := NewServer(ServerConfig{
		ListenAddr: serverListener.Addr().String(), Credentials: certificate,
		DestinationPolicy: DestinationPolicy{AllowPrivate: true}, EnableTCP: true, EnableQUIC: false,
		Logger: logger, Metrics: metrics.New(),
	})
	if err != nil {
		t.Fatal(err)
	}
	clientListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	client, err := NewClient(ClientConfig{
		ListenAddr: clientListener.Addr().String(), RemoteAddr: serverListener.Addr().String(), Credentials: roots, Transport: TransportTCP, Logger: logger, Metrics: metrics.New(),
	})
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	errorsCh := make(chan error, 2)
	go func() { errorsCh <- server.ServeListener(ctx, serverListener) }()
	go func() { errorsCh <- client.ServeListener(ctx, clientListener) }()

	conn := dialTestSOCKS(t, clientListener.Addr().String(), destinationListener.Addr().String())
	payload := []byte("tombstone")
	if _, err := conn.Write(payload); err != nil {
		t.Fatal(err)
	}
	if tcp, ok := conn.(*net.TCPConn); ok {
		if err := tcp.CloseWrite(); err != nil {
			t.Fatal(err)
		}
	}
	got, err := io.ReadAll(conn)
	_ = conn.Close()
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(got, payload) {
		t.Fatalf("echo mismatch: got %q, want %q", got, payload)
	}

	var sessionID [16]byte
	var flowID uint64
	var finalSequence uint64
	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		server.sessionsMu.RLock()
		for id, sessionFlow := range server.sessions {
			if sessionFlow.completed.Load() {
				sessionID = id
				flowID = sessionFlow.flow.flowID
				finalSequence = sessionFlow.flow.remoteFinSequence.Load()
			}
		}
		server.sessionsMu.RUnlock()
		if flowID != 0 {
			break
		}
		time.Sleep(10 * time.Millisecond)
	}
	if flowID == 0 {
		t.Fatal("completed flow tombstone was not retained")
	}
	deadline = time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) && server.Metrics().Snapshot().ActiveFlows != 0 {
		time.Sleep(10 * time.Millisecond)
	}
	if got := server.Metrics().Snapshot(); got.ActiveFlows != 0 || got.FlowsCompleted != 1 {
		t.Fatalf("server completion watcher did not release flow: active=%d completed=%d failed=%d", got.ActiveFlows, got.FlowsCompleted, got.FlowsFailed)
	}

	joinCtx, joinCancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer joinCancel()
	lane, err := client.openJoinLane(joinCtx, TransportTCP, sessionID, flowID, 99)
	if err != nil {
		t.Fatal(err)
	}
	defer lane.fc.Close()
	ack, err := lane.fc.Read()
	if err != nil {
		t.Fatal(err)
	}
	if ack.Header.Type != protocol.TypeAck || ack.Header.Flags&protocol.FlagAckFinal == 0 || ack.Header.Sequence != finalSequence {
		t.Fatalf("unexpected tombstone ACK: type=%d flags=%x sequence=%d want=%d", ack.Header.Type, ack.Header.Flags, ack.Header.Sequence, finalSequence)
	}
	fin, err := lane.fc.Read()
	if err != nil {
		t.Fatal(err)
	}
	if fin.Header.Type != protocol.TypeClose || fin.Header.Flags&protocol.FlagFin == 0 {
		t.Fatalf("unexpected tombstone FIN: type=%d flags=%x", fin.Header.Type, fin.Header.Flags)
	}

	cancel()
	for range 2 {
		if err := <-errorsCh; err != nil {
			t.Fatalf("service shutdown: %v", err)
		}
	}
}

func TestLostFinalFINUsesOneTombstoneRescueWithoutStorm(t *testing.T) {
	destinationListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer destinationListener.Close()
	response := bytes.Repeat([]byte("completed-before-fin-loss-"), 4096)
	releaseDestinationClose := make(chan struct{})
	destinationReady := make(chan struct{})
	go func() {
		conn, acceptErr := destinationListener.Accept()
		if acceptErr != nil {
			return
		}
		defer conn.Close()
		request := make([]byte, len("request"))
		if _, readErr := io.ReadFull(conn, request); readErr != nil {
			return
		}
		if writeErr := writeFull(conn, response); writeErr != nil {
			return
		}
		close(destinationReady)
		<-releaseDestinationClose
	}()

	certificate, roots := testCertificate(t)
	var logBuf bytes.Buffer
	logger := slog.New(slog.NewTextHandler(&logBuf, nil))
	packetConn, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	var dropFirstServerFIN atomic.Bool
	dropFirstServerFIN.Store(true)
	serverMetrics := metrics.New()
	server, err := NewServer(ServerConfig{
		ListenAddr: "127.0.0.1:0", Credentials: certificate,
		DestinationPolicy: DestinationPolicy{AllowPrivate: true}, EnableQUIC: true, Logger: logger, Metrics: serverMetrics,
		testLaneWriteHook: func(frame protocol.Frame) error {
			if frame.Header.Type == protocol.TypeClose && frame.Header.Flags&protocol.FlagFin != 0 && dropFirstServerFIN.CompareAndSwap(true, false) {
				return errors.New("injected final FIN loss")
			}
			return nil
		},
	})
	if err != nil {
		t.Fatal(err)
	}
	clientListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	clientMetrics := metrics.New()
	client, err := NewClient(ClientConfig{
		ListenAddr: clientListener.Addr().String(), RemoteAddr: packetConn.LocalAddr().String(), Credentials: roots, Transport: TransportQUIC,
		Logger: logger, Metrics: clientMetrics,
	})
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	errorsCh := make(chan error, 2)
	go func() { errorsCh <- server.ServePacketConn(ctx, packetConn) }()
	go func() { errorsCh <- client.ServeListener(ctx, clientListener) }()

	conn := dialTestSOCKS(t, clientListener.Addr().String(), destinationListener.Addr().String())
	_ = conn.SetDeadline(time.Now().Add(12 * time.Second))
	if _, err := conn.Write([]byte("request")); err != nil {
		t.Fatal(err)
	}
	select {
	case <-destinationReady:
	case <-time.After(3 * time.Second):
		t.Fatal("destination did not write response")
	}
	got := make([]byte, len(response))
	if _, err := io.ReadFull(conn, got); err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(got, response) {
		t.Fatalf("response mismatch: got %d bytes, want %d", len(got), len(response))
	}
	// Closing the destination makes the server enqueue its final logical FIN.
	// The hook drops exactly that frame and fails the original QUIC lane after
	// every response byte is already at the application. Deliberately wait for
	// that failure before fully closing the application socket: this reproduces
	// the real curl race where Content-Length is complete, the final transport
	// close is lost, and only then does the local application close.
	close(releaseDestinationClose)
	faultDeadline := time.Now().Add(3 * time.Second)
	for dropFirstServerFIN.Load() && time.Now().Before(faultDeadline) {
		time.Sleep(time.Millisecond)
	}
	if dropFirstServerFIN.Load() {
		t.Fatal("final FIN fault was not exercised")
	}
	_ = conn.Close()

	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		if serverMetrics.Snapshot().ActiveFlows == 0 && clientMetrics.Snapshot().ActiveFlows == 0 {
			break
		}
		time.Sleep(10 * time.Millisecond)
	}
	if got := clientMetrics.Snapshot(); got.ActiveFlows != 0 || got.FlowsCompleted != 1 || got.FlowsFailed != 0 || got.LaneReplacements != 1 {
		t.Fatalf("client final-FIN recovery = active:%d completed:%d failed:%d replacements:%d, want 0/1/0/1; logs:\n%s", got.ActiveFlows, got.FlowsCompleted, got.FlowsFailed, got.LaneReplacements, logBuf.String())
	}
	if got := serverMetrics.Snapshot(); got.ActiveFlows != 0 || got.FlowsCompleted != 1 || got.FlowsFailed != 0 {
		t.Fatalf("server final-FIN recovery = active:%d completed:%d failed:%d", got.ActiveFlows, got.FlowsCompleted, got.FlowsFailed)
	}

	cancel()
	for range 2 {
		if err := <-errorsCh; err != nil {
			t.Fatalf("service shutdown: %v", err)
		}
	}
}

func TestFullApplicationCloseAbortsKeepAliveDestination(t *testing.T) {
	destinationListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer destinationListener.Close()
	response := bytes.Repeat([]byte("fixed-response-"), 4096)
	go holdResponseDestination(destinationListener, response)

	certificate, roots := testCertificate(t)
	var logBuf bytes.Buffer
	logger := slog.New(slog.NewTextHandler(&logBuf, &slog.HandlerOptions{Level: slog.LevelDebug}))
	t.Cleanup(func() {
		if t.Failed() {
			t.Logf("full-close trace:\n%s", logBuf.String())
		}
	})
	serverListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	serverMetrics := metrics.New()
	server, err := NewServer(ServerConfig{
		ListenAddr: serverListener.Addr().String(), Credentials: certificate,
		DestinationPolicy: DestinationPolicy{AllowPrivate: true}, EnableTCP: true, EnableQUIC: false,
		Logger: logger, Metrics: serverMetrics,
	})
	if err != nil {
		t.Fatal(err)
	}
	clientListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	clientMetrics := metrics.New()
	client, err := NewClient(ClientConfig{
		ListenAddr: clientListener.Addr().String(), RemoteAddr: serverListener.Addr().String(), Credentials: roots, Transport: TransportTCP, Logger: logger, Metrics: clientMetrics,
	})
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	errorsCh := make(chan error, 2)
	go func() { errorsCh <- server.ServeListener(ctx, serverListener) }()
	go func() { errorsCh <- client.ServeListener(ctx, clientListener) }()

	conn := dialTestSOCKS(t, clientListener.Addr().String(), destinationListener.Addr().String())
	if _, err := conn.Write([]byte("request")); err != nil {
		t.Fatal(err)
	}
	got := make([]byte, len(response))
	if _, err := io.ReadFull(conn, got); err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(got, response) {
		t.Fatalf("response mismatch: got %d bytes, want %d", len(got), len(response))
	}
	// Deliberately close the application socket fully. There is no TCP
	// CloseWrite here; the tunnel must carry the explicit full-close marker.
	_ = conn.Close()

	deadline := time.Now().Add(8 * time.Second)
	for time.Now().Before(deadline) {
		if serverMetrics.Snapshot().ActiveFlows == 0 && clientMetrics.Snapshot().ActiveFlows == 0 {
			break
		}
		time.Sleep(10 * time.Millisecond)
	}
	if got := serverMetrics.Snapshot(); got.ActiveFlows != 0 || got.FlowsCompleted != 1 || got.FlowsFailed != 0 {
		t.Fatalf("server did not close keep-alive flow cleanly: active=%d completed=%d failed=%d", got.ActiveFlows, got.FlowsCompleted, got.FlowsFailed)
	}
	if got := clientMetrics.Snapshot(); got.ActiveFlows != 0 || got.FlowsCompleted != 1 || got.FlowsFailed != 0 {
		t.Fatalf("client did not close full application flow cleanly: active=%d completed=%d failed=%d", got.ActiveFlows, got.FlowsCompleted, got.FlowsFailed)
	}

	cancel()
	for range 2 {
		if err := <-errorsCh; err != nil {
			t.Fatalf("service shutdown: %v", err)
		}
	}
}

func TestTCPFallbackStripesOneFlowAcrossFourLanes(t *testing.T) {
	destinationListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer destinationListener.Close()
	prefix := bytes.Repeat([]byte("tcp-prefix-"), 8192)
	tail := bytes.Repeat([]byte("striped-tcp-payload-"), 256*1024)
	response := append(append([]byte(nil), prefix...), tail...)
	go func() {
		conn, acceptErr := destinationListener.Accept()
		if acceptErr != nil {
			return
		}
		defer conn.Close()
		request := make([]byte, len("request"))
		if _, readErr := io.ReadFull(conn, request); readErr != nil {
			return
		}
		if writeErr := writeFull(conn, prefix); writeErr != nil {
			return
		}
		// Hold a body above the prewarm threshold long enough for the client to
		// classify the one-way transfer and finish all three TLS lane joins.
		time.Sleep(750 * time.Millisecond)
		_ = writeFull(conn, tail)
	}()

	certificate, roots := testCertificate(t)
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	serverListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	var server *Server
	var injectLaneFailure atomic.Bool
	injectLaneFailure.Store(true)
	server, err = NewServer(ServerConfig{
		ListenAddr: serverListener.Addr().String(), Credentials: certificate,
		DestinationPolicy: DestinationPolicy{AllowPrivate: true}, EnableTCP: true, EnableQUIC: false,
		TCPFallbackLanes: 4, Logger: logger,
		testLaneWriteHook: func(frame protocol.Frame) error {
			if frame.Header.Type == protocol.TypeData && server != nil && server.maxObservedLanes.Load() == 4 && injectLaneFailure.CompareAndSwap(true, false) {
				return errors.New("injected striped TCP lane failure")
			}
			return nil
		},
	})
	if err != nil {
		t.Fatal(err)
	}
	clientListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	client, err := NewClient(ClientConfig{
		ListenAddr: clientListener.Addr().String(), RemoteAddr: serverListener.Addr().String(), Credentials: roots, Transport: TransportTCP, TCPFallbackLanes: 4, Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	errorsCh := make(chan error, 2)
	go func() { errorsCh <- server.ServeListener(ctx, serverListener) }()
	go func() { errorsCh <- client.ServeListener(ctx, clientListener) }()

	conn := dialTestSOCKS(t, clientListener.Addr().String(), destinationListener.Addr().String())
	_ = conn.SetDeadline(time.Now().Add(15 * time.Second))
	if _, err := conn.Write([]byte("request")); err != nil {
		t.Fatal(err)
	}
	got := make([]byte, len(response))
	if _, err := io.ReadFull(conn, got); err != nil {
		t.Fatalf("read striped response: %v", err)
	}
	if !bytes.Equal(got, response) {
		t.Fatalf("striped response mismatch: got %d bytes, want %d", len(got), len(response))
	}
	if lanes := server.maxObservedLanes.Load(); lanes != 4 {
		t.Fatalf("server observed %d lanes, want exactly four", lanes)
	}
	if injectLaneFailure.Load() {
		t.Fatal("the four-lane transfer completed without exercising lane re-injection")
	}
	_ = conn.Close()

	cancel()
	for range 2 {
		if err := <-errorsCh; err != nil {
			t.Fatalf("service shutdown: %v", err)
		}
	}
}

func dialTestSOCKS(t *testing.T, proxyAddr, destinationAddr string) net.Conn {
	t.Helper()
	conn, err := net.DialTimeout("tcp", proxyAddr, 2*time.Second)
	if err != nil {
		t.Fatal(err)
	}
	_ = conn.SetDeadline(time.Now().Add(5 * time.Second))
	if _, err := conn.Write([]byte{5, 1, 0}); err != nil {
		t.Fatal(err)
	}
	var method [2]byte
	if _, err := io.ReadFull(conn, method[:]); err != nil {
		t.Fatal(err)
	}
	if method != [2]byte{5, 0} {
		t.Fatalf("method response %v", method)
	}
	host, portText, err := net.SplitHostPort(destinationAddr)
	if err != nil {
		t.Fatal(err)
	}
	ip := net.ParseIP(host).To4()
	port, err := strconv.Atoi(portText)
	if err != nil {
		t.Fatal(err)
	}
	request := append([]byte{5, 1, 0, 1}, ip...)
	var portBytes [2]byte
	binary.BigEndian.PutUint16(portBytes[:], uint16(port))
	request = append(request, portBytes[:]...)
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
	_ = conn.SetDeadline(time.Time{})
	return conn
}

func slowEchoDestination(listener net.Listener) {
	for {
		conn, err := listener.Accept()
		if err != nil {
			return
		}
		go func() {
			defer conn.Close()
			buf := make([]byte, 4*1024)
			for {
				n, readErr := conn.Read(buf)
				if n > 0 {
					time.Sleep(time.Millisecond)
					if err := writeFull(conn, buf[:n]); err != nil {
						return
					}
				}
				if readErr != nil {
					return
				}
			}
		}()
	}
}

func echoDestination(listener net.Listener) {
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
}

func holdResponseDestination(listener net.Listener, response []byte) {
	for {
		conn, err := listener.Accept()
		if err != nil {
			return
		}
		go func() {
			defer conn.Close()
			if err := writeFull(conn, response); err != nil {
				return
			}
			// Drain the request and keep the destination socket alive until the
			// proxy receives the application's full-close marker and closes this
			// connection. Reading only one request byte leaves unread receive
			// data; Windows correctly turns a close in that state into a reset,
			// which tests destination failure instead of keep-alive teardown.
			_, _ = io.Copy(io.Discard, conn)
		}()
	}
}
