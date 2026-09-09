package portmux_test

import (
	"net"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/portmux"
)

// — HopPorts tests —

func TestHopPortsPrimaryFirst(t *testing.T) {
	ports := portmux.HopPorts("test-provider", 12540, 10)
	if len(ports) != 10 {
		t.Fatalf("want 10 ports, got %d", len(ports))
	}
	if ports[0] != 12540 {
		t.Errorf("first port must be the primary port; got %d", ports[0])
	}
}

func TestHopPortsDeterministic(t *testing.T) {
	a := portmux.HopPorts("abc", 1234, 50)
	b := portmux.HopPorts("abc", 1234, 50)
	for i := range a {
		if a[i] != b[i] {
			t.Fatalf("HopPorts is not deterministic: index %d got %d and %d", i, a[i], b[i])
		}
	}
}

func TestHopPortsDifferentProviders(t *testing.T) {
	a := portmux.HopPorts("provider-A", 12540, 20)
	b := portmux.HopPorts("provider-B", 12540, 20)
	// Different providers should yield different secondary ports
	// (primary is the same by definition; check at least one secondary differs).
	differ := false
	for i := 1; i < 20; i++ {
		if a[i] != b[i] {
			differ = true
			break
		}
	}
	if !differ {
		t.Error("different providerIDs should yield different port sequences")
	}
}

func TestHopPortsNoDuplicates(t *testing.T) {
	ports := portmux.HopPorts("dupecheck", 55555, 100)
	seen := make(map[int]bool, len(ports))
	for _, p := range ports {
		if seen[p] {
			t.Errorf("duplicate port %d in HopPorts output", p)
		}
		seen[p] = true
	}
}

func TestHopPortsRange(t *testing.T) {
	ports := portmux.HopPorts("rangecheck", 9000, 100)
	for _, p := range ports[1:] { // skip primary which may be outside range
		if p < 1024 || p >= 65535 {
			t.Errorf("port %d out of range [1024, 65535)", p)
		}
	}
}

func TestHopPortsSingleOrZero(t *testing.T) {
	for _, count := range []int{0, 1} {
		ports := portmux.HopPorts("x", 4444, count)
		if len(ports) != 1 || ports[0] != 4444 {
			t.Errorf("count=%d: want [4444], got %v", count, ports)
		}
	}
}

// — ClientPortMux address-rewriting tests —

// newLoopbackPair returns two connected UDP sockets suitable for testing the
// port mux without a real server. a and b are peers.
func newLoopbackPair(t *testing.T) (a, b *net.UDPConn) {
	t.Helper()
	la, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	lb, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		la.Close()
		t.Fatal(err)
	}
	return la, lb
}

func TestClientPortMuxRewritesOnWrite(t *testing.T) {
	client, server := newLoopbackPair(t)
	defer client.Close()
	defer server.Close()

	serverAddr := server.LocalAddr().(*net.UDPAddr)
	// Build a 2-port list; ports[1] is a fake "second" port. Stay inside the
	// valid port range no matter which ephemeral port the OS assigned.
	altPort := serverAddr.Port + 100
	if altPort > 65535 {
		altPort = serverAddr.Port - 100
	}
	ports := []int{serverAddr.Port, altPort}

	mux := portmux.NewClientPortMux(client, serverAddr, ports)
	defer mux.Close()

	// Hop to index 1 (altPort).
	mux.Hop(1)

	// Write to the primary address — mux should rewrite to altPort.
	sent := []byte("hello")
	if _, err := mux.WriteTo(sent, serverAddr); err != nil {
		t.Fatalf("WriteTo: %v", err)
	}

	// Server is not actually listening on altPort; just verify the outgoing
	// destination was rewritten by checking CurrentPort.
	if mux.CurrentPort() != altPort {
		t.Errorf("CurrentPort = %d, want %d", mux.CurrentPort(), altPort)
	}
}

func TestClientPortMuxNormalisesIncoming(t *testing.T) {
	// Simulate: server sends from altPort; mux should normalise to primaryPort.
	clientConn, serverConn := newLoopbackPair(t)
	defer clientConn.Close()
	defer serverConn.Close()

	// Open a second server socket on a different port to simulate the hop port.
	altServerConn, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	defer altServerConn.Close()

	primaryAddr := serverConn.LocalAddr().(*net.UDPAddr)
	altPort := altServerConn.LocalAddr().(*net.UDPAddr).Port

	ports := []int{primaryAddr.Port, altPort}
	mux := portmux.NewClientPortMux(clientConn, primaryAddr, ports)
	defer mux.Close()

	clientAddr := clientConn.LocalAddr().(*net.UDPAddr)

	// Alt server sends a reply packet to the client.
	go func() {
		time.Sleep(5 * time.Millisecond)
		_, _ = altServerConn.WriteTo([]byte("reply"), clientAddr)
	}()

	buf := make([]byte, 64)
	_ = clientConn.SetReadDeadline(time.Now().Add(time.Second))
	n, addr, err := mux.ReadFrom(buf)
	if err != nil {
		t.Fatalf("ReadFrom: %v", err)
	}
	if string(buf[:n]) != "reply" {
		t.Errorf("payload = %q, want %q", buf[:n], "reply")
	}
	// The returned address should be the primary address, not the alt port.
	uaddr, ok := addr.(*net.UDPAddr)
	if !ok {
		t.Fatalf("addr is not *net.UDPAddr")
	}
	if uaddr.Port != primaryAddr.Port {
		t.Errorf("source port = %d, want primary %d (src from alt port must be normalised)",
			uaddr.Port, primaryAddr.Port)
	}
}

func TestClientPortMuxCounters(t *testing.T) {
	clientConn, serverConn := newLoopbackPair(t)
	defer clientConn.Close()
	defer serverConn.Close()

	serverAddr := serverConn.LocalAddr().(*net.UDPAddr)
	mux := portmux.NewClientPortMux(clientConn, serverAddr, []int{serverAddr.Port})
	defer mux.Close()

	if mux.SendCount() != 0 || mux.RecvCount() != 0 {
		t.Fatal("counters must start at zero")
	}

	// Send two packets.
	clientAddr := clientConn.LocalAddr().(*net.UDPAddr)
	_, _ = mux.WriteTo([]byte("a"), serverAddr)
	_, _ = mux.WriteTo([]byte("b"), serverAddr)
	if mux.SendCount() != 2 {
		t.Errorf("SendCount = %d, want 2", mux.SendCount())
	}

	// Server echoes them back.
	buf := make([]byte, 8)
	for i := 0; i < 2; i++ {
		_, _, _ = serverConn.ReadFrom(buf)
		_, _ = serverConn.WriteTo(buf[:1], clientAddr)
	}
	// Drain the client side.
	_ = clientConn.SetReadDeadline(time.Now().Add(500 * time.Millisecond))
	for i := 0; i < 2; i++ {
		_, _, _ = mux.ReadFrom(buf)
	}
	if mux.RecvCount() != 2 {
		t.Errorf("RecvCount = %d, want 2", mux.RecvCount())
	}
}

// — HopController tests —

type nopMetrics struct{ count int }

func (n *nopMetrics) PortHop() { n.count++ }

// — HopWalk tests —

func TestHopWalkVisitsEveryIndexOncePerRound(t *testing.T) {
	const count = 20
	w := portmux.NewHopWalk(count)
	for round := 0; round < 3; round++ {
		seen := make(map[int32]bool, count)
		for i := 0; i < count; i++ {
			idx := w.Next()
			if idx < 0 || idx >= count {
				t.Fatalf("round %d: index %d out of range [0, %d)", round, idx, count)
			}
			if seen[idx] {
				t.Fatalf("round %d: index %d returned twice within one permutation", round, idx)
			}
			seen[idx] = true
		}
	}
}

// Note: HopConfig clamps PollInterval to a minimum of 1s and the controller
// requires a full detect window before triggering, so these tests run on a
// 1s poll cadence and need multi-second durations.

func TestHopControllerWaitsForFullWindow(t *testing.T) {
	clientConn, _ := newLoopbackPair(t)
	defer clientConn.Close()

	serverAddr := &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1), Port: 19998}
	ports := portmux.HopPorts("test", serverAddr.Port, 5)
	mux := portmux.NewClientPortMux(clientConn, serverAddr, ports)
	defer mux.Close()

	m := &nopMetrics{}
	ctrl := portmux.NewHopController(mux, portmux.HopConfig{
		DetectWindow: 1500 * time.Millisecond, // 2 samples at the clamped 1s poll
		PollInterval: 100 * time.Millisecond,  // clamped to 1s
		MinSent:      3,
		Cooldown:     time.Second,
		Metrics:      m,
	})
	go ctrl.Run(mux.Context())

	send := func(d time.Duration) {
		deadline := time.Now().Add(d)
		for time.Now().Before(deadline) {
			clientConn.SetWriteDeadline(time.Now().Add(time.Millisecond))
			_, _ = mux.WriteTo([]byte("x"), serverAddr)
			time.Sleep(20 * time.Millisecond)
		}
	}

	// A partially filled window must not trigger, no matter how lossy it looks.
	send(1500 * time.Millisecond)
	if m.count != 0 {
		t.Fatalf("hop triggered after one sample with a two-sample detect window")
	}

	// Once the window is full of zero-receive evidence, the hop fires.
	send(2500 * time.Millisecond)
	if m.count == 0 {
		t.Fatal("no hop after a full window of zero-receive loss")
	}
}

func TestHopControllerTriggersOnLoss(t *testing.T) {
	clientConn, _ := newLoopbackPair(t)
	defer clientConn.Close()

	serverAddr := &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1), Port: 19999}
	ports := portmux.HopPorts("test", serverAddr.Port, 5)
	mux := portmux.NewClientPortMux(clientConn, serverAddr, ports)
	defer mux.Close()

	m := &nopMetrics{}
	ctrl := portmux.NewHopController(mux, portmux.HopConfig{
		DetectWindow: 500 * time.Millisecond,
		PollInterval: 100 * time.Millisecond,
		MinSent:      3,
		Cooldown:     200 * time.Millisecond,
		Metrics:      m,
	})

	ctx := mux.Context()
	go ctrl.Run(ctx)

	// Simulate sustained sending with zero receives.
	for i := 0; i < 20; i++ {
		mux.SendCount() // just read; we need to increment sendCount manually
		// Directly increment the send counter to simulate sends without
		// actually sending UDP packets (the server addr is not really listening).
		// Use the exported counter indirectly through WriteTo which may fail.
		// Instead we call WriteTo and accept the send error.
		clientConn.SetWriteDeadline(time.Now().Add(time.Millisecond))
		_, _ = mux.WriteTo([]byte("x"), serverAddr)
		time.Sleep(20 * time.Millisecond)
	}

	// Wait for the two-sample detect window to fill at the clamped 1s poll
	// cadence, plus margin.
	time.Sleep(2600 * time.Millisecond)

	if m.count == 0 {
		t.Error("HopController did not trigger a hop despite sustained zero-receive loss")
	}
	if mux.CurrentPort() == serverAddr.Port {
		t.Error("port is still primary after hop controller triggered")
	}
}

func TestHopControllerNoHopWhenReceiving(t *testing.T) {
	clientConn, serverConn := newLoopbackPair(t)
	defer clientConn.Close()
	defer serverConn.Close()

	serverAddr := serverConn.LocalAddr().(*net.UDPAddr)
	ports := portmux.HopPorts("test", serverAddr.Port, 5)
	mux := portmux.NewClientPortMux(clientConn, serverAddr, ports)
	defer mux.Close()

	m := &nopMetrics{}
	ctrl := portmux.NewHopController(mux, portmux.HopConfig{
		DetectWindow: 300 * time.Millisecond,
		PollInterval: 50 * time.Millisecond,
		MinSent:      3,
		Cooldown:     200 * time.Millisecond,
		Metrics:      m,
	})
	go ctrl.Run(mux.Context())

	clientAddr := clientConn.LocalAddr().(*net.UDPAddr)

	// Send and receive traffic to simulate a healthy path.
	done := make(chan struct{})
	go func() {
		defer close(done)
		buf := make([]byte, 8)
		for {
			serverConn.SetReadDeadline(time.Now().Add(200 * time.Millisecond))
			_, _, err := serverConn.ReadFrom(buf)
			if err != nil {
				return
			}
			serverConn.WriteTo(buf[:1], clientAddr)
		}
	}()

	buf := make([]byte, 8)
	// Keep the path busy well past the two-sample detect window (1s clamped
	// polls), so the receive guard is what actually suppresses the hop.
	deadline := time.Now().Add(2600 * time.Millisecond)
	for time.Now().Before(deadline) {
		_, _ = mux.WriteTo([]byte("x"), serverAddr)
		clientConn.SetReadDeadline(time.Now().Add(100 * time.Millisecond))
		_, _, _ = mux.ReadFrom(buf)
		time.Sleep(20 * time.Millisecond)
	}
	time.Sleep(400 * time.Millisecond)

	if m.count > 0 {
		t.Errorf("HopController triggered %d hops on a healthy path; want 0", m.count)
	}
	<-done
}

// A hop pool is derived from a hash, so a derivation will eventually land on a
// port the host will not hand out -- Windows carves dynamic exclusion ranges
// out of the same space and refuses them outright. Losing one of several hop
// ports has to degrade the pool rather than take the gateway down with it.
func TestAnUnbindableHopPortIsSkippedRatherThanFatal(t *testing.T) {
	primary, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	// Hold one hop port ourselves, which is the portable stand-in for a port
	// the operating system has reserved.
	blocker, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = blocker.Close() }()
	blocked := blocker.LocalAddr().(*net.UDPAddr).Port

	free, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	usable := free.LocalAddr().(*net.UDPAddr).Port
	_ = free.Close()

	primaryPort := primary.LocalAddr().(*net.UDPAddr).Port
	mux, err := portmux.NewServerPortMux(primary, []int{primaryPort, blocked, usable})
	if err != nil {
		t.Fatalf("one unbindable hop port took the whole mux down: %v", err)
	}
	defer func() { _ = mux.Close() }()

	if got := mux.SkippedPorts(); len(got) != 1 || got[0] != blocked {
		t.Fatalf("skipped ports %v, want exactly [%d]", got, blocked)
	}
	// The port that was available still has to be listening, or the pool has
	// silently collapsed to the primary.
	probe, err := net.DialUDP("udp", nil, &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1), Port: usable})
	if err != nil {
		t.Fatalf("the usable hop port is not listening: %v", err)
	}
	_ = probe.Close()
}

// Losing every hop port is a different condition from losing one: hopping is
// then not degraded but absent, and an operator who configured it should be
// told rather than left to infer it from traffic that never evades anything.
func TestAHopPoolThatBindsNothingIsAnError(t *testing.T) {
	primary, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = primary.Close() }()
	blocker, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = blocker.Close() }()
	blocked := blocker.LocalAddr().(*net.UDPAddr).Port

	primaryPort := primary.LocalAddr().(*net.UDPAddr).Port
	if _, err := portmux.NewServerPortMux(primary, []int{primaryPort, blocked}); err == nil {
		t.Fatal("a pool that bound no hop port at all was accepted")
	}
}

// A mux asked for no hop ports at all is not a degraded pool; it is hopping
// switched off, and it must not be turned into an error by the check above.
func TestASinglePortPoolIsNotTreatedAsAFailure(t *testing.T) {
	primary, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	primaryPort := primary.LocalAddr().(*net.UDPAddr).Port
	mux, err := portmux.NewServerPortMux(primary, []int{primaryPort})
	if err != nil {
		t.Fatalf("a single-port pool was rejected: %v", err)
	}
	defer func() { _ = mux.Close() }()
	if len(mux.SkippedPorts()) != 0 {
		t.Fatalf("skipped %v with nothing to skip", mux.SkippedPorts())
	}
}
