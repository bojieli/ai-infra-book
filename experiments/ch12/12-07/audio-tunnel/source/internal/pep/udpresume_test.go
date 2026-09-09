package pep

import (
	"context"
	"encoding/binary"
	"io"
	"log/slog"
	"net"
	"sync"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/session"
	"github.com/bojieli/queqiao/internal/socks5"
)

var udpTestPrincipal = identity.Principal{ProviderID: "provider", AccountID: "account", DeviceID: "device"}

// The store's own rules, stated where they can be checked cheaply: a token is
// good once, an expired relay is not handed back, and neither a wrong length
// nor a wrong value gets one.
func TestARetainedRelayIsHandedBackOnceAndOnlyToItsToken(t *testing.T) {
	store := newUDPRelayStore()
	relay := func(t *testing.T) *net.UDPConn {
		t.Helper()
		conn, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
		if err != nil {
			t.Fatal(err)
		}
		return conn
	}

	token, err := newUDPResumeToken()
	if err != nil {
		t.Fatal(err)
	}
	held := relay(t)
	port := held.LocalAddr().(*net.UDPAddr).Port
	store.retain(token, udpTestPrincipal, held)
	if store.retained() != 1 {
		t.Fatalf("retained %d relays, want 1", store.retained())
	}

	// A token that is not this one gets nothing, and does not disturb it.
	other, err := newUDPResumeToken()
	if err != nil {
		t.Fatal(err)
	}
	if store.claim(other[:], udpTestPrincipal) != nil {
		t.Fatal("a wrong token claimed a relay")
	}
	if store.claim(token[:len(token)-1], udpTestPrincipal) != nil {
		t.Fatal("a short token claimed a relay")
	}
	if store.retained() != 1 {
		t.Fatal("a failed claim consumed the relay it did not match")
	}

	claimed := store.claim(token[:], udpTestPrincipal)
	if claimed == nil {
		t.Fatal("the right token did not claim its relay")
	}
	if got := claimed.LocalAddr().(*net.UDPAddr).Port; got != port {
		t.Fatalf("claimed a relay on port %d, want %d", got, port)
	}
	// One token, one use. A lane that failed once must not be replayable
	// against whatever relay the association has later.
	if store.claim(token[:], udpTestPrincipal) != nil {
		t.Fatal("a token claimed a relay twice")
	}
	_ = claimed.Close()

	store.closeAll()

	// Expiry hands nothing back and leaves nothing behind.
	expired := newUDPRelayStoreWith(time.Nanosecond, udpRelaysRetained)
	expiring, err := newUDPResumeToken()
	if err != nil {
		t.Fatal(err)
	}
	expired.retain(expiring, udpTestPrincipal, relay(t))
	time.Sleep(time.Millisecond)
	if expired.claim(expiring[:], udpTestPrincipal) != nil {
		t.Fatal("an expired relay was handed back")
	}
	if expired.retained() != 0 {
		t.Fatalf("%d relays left after expiry", expired.retained())
	}
	expired.closeAll()
}

func TestRetainedRelayCannotCrossDevicePrincipal(t *testing.T) {
	store := newUDPRelayStore()
	token, err := newUDPResumeToken()
	if err != nil {
		t.Fatal(err)
	}
	relay, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	store.retain(token, udpTestPrincipal, relay)
	other := udpTestPrincipal
	other.DeviceID = "other-device"
	if claimed := store.claim(token[:], other); claimed != nil {
		_ = claimed.Close()
		t.Fatal("another device claimed a retained UDP relay")
	}
	if store.retained() != 0 {
		t.Fatal("cross-device claim left a replayable relay behind")
	}
}

// A relay is bounded because a peer creates them by failing associations. The
// bound refuses the new one rather than evicting an existing one: refusing
// degrades to the behaviour that existed before resume, while evicting breaks
// an association that was working.
func TestRetainedRelaysAreBounded(t *testing.T) {
	store := newUDPRelayStoreWith(udpRelayGrace, 3)
	var tokens [][session.UDPResumeTokenSize]byte
	for i := 0; i < 6; i++ {
		token, err := newUDPResumeToken()
		if err != nil {
			t.Fatal(err)
		}
		conn, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
		if err != nil {
			t.Fatal(err)
		}
		store.retain(token, udpTestPrincipal, conn)
		tokens = append(tokens, token)
	}
	if store.retained() != 3 {
		t.Fatalf("retained %d relays against a maximum of 3", store.retained())
	}
	for _, token := range tokens[:3] {
		if store.claim(token[:], udpTestPrincipal) == nil {
			t.Fatal("a relay retained before the bound was reached was lost")
		}
	}
	store.closeAll()
}

// The property the token exists for.
//
// A UDP association's relay is a socket on the server, and its source address
// is what the destination is answering. A rescue used to open a new one, so a
// destination that pinned the flow -- a NAT binding, a game server, a QUIC
// peer -- saw the association move to a different client mid-conversation.
// The local SOCKS socket surviving, which it already did, does not help with
// that: it is the far end that stops recognising the traffic.
func TestARescuedUDPAssociationKeepsItsRemoteSourceAddress(t *testing.T) {
	destination, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	defer destination.Close()
	var sourcesMu sync.Mutex
	var sources []string
	go func() {
		buf := make([]byte, 2048)
		for {
			n, addr, readErr := destination.ReadFromUDP(buf)
			if readErr != nil {
				return
			}
			sourcesMu.Lock()
			sources = append(sources, addr.String())
			sourcesMu.Unlock()
			_, _ = destination.WriteToUDP(buf[:n], addr)
		}
	}()
	seenSources := func() []string {
		sourcesMu.Lock()
		defer sourcesMu.Unlock()
		return append([]string(nil), sources...)
	}

	tlsCert, roots := testCertificate(t)
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	tcpListener, quicPacketConn := listenTCPAndUDPOnOnePort(t)
	serverAddr := tcpListener.Addr().String()
	server, err := NewServer(ServerConfig{
		ListenAddr: serverAddr, Credentials: tlsCert,
		DestinationPolicy: DestinationPolicy{AllowPrivate: true}, EnableTCP: true, EnableQUIC: true,
		Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	clientListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer clientListener.Close()
	client, err := NewClient(ClientConfig{
		ListenAddr: clientListener.Addr().String(), RemoteAddr: serverAddr, Credentials: roots, Transport: TransportAuto, FallbackDelay: 5 * time.Second,
		UDPFailureThreshold: 1, UDPCooldown: time.Minute, Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	serviceCtx, serviceCancel := context.WithCancel(context.Background())
	defer serviceCancel()
	quicCtx, quicCancel := context.WithCancel(serviceCtx)
	errorsCh := make(chan error, 3)
	go func() { errorsCh <- server.ServeListener(serviceCtx, tcpListener) }()
	go func() { errorsCh <- server.ServePacketConn(quicCtx, quicPacketConn) }()
	go func() { errorsCh <- client.ServeListener(serviceCtx, clientListener) }()

	control, err := net.DialTimeout("tcp", clientListener.Addr().String(), 5*time.Second)
	if err != nil {
		t.Fatal(err)
	}
	defer control.Close()
	bound := openTestUDPAssociation(t, control)
	udpClient, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	defer udpClient.Close()
	destinationAddr := destination.LocalAddr().(*net.UDPAddr)

	send := func(payload string) {
		t.Helper()
		request := append([]byte{0, 0, 0, 1}, destinationAddr.IP.To4()...)
		var portBytes [2]byte
		binary.BigEndian.PutUint16(portBytes[:], uint16(destinationAddr.Port))
		request = append(append(request, portBytes[:]...), payload...)
		if _, err := udpClient.WriteToUDP(request, bound); err != nil {
			t.Fatal(err)
		}
		buf := make([]byte, 2048)
		_ = udpClient.SetReadDeadline(time.Now().Add(10 * time.Second))
		n, _, readErr := udpClient.ReadFromUDP(buf)
		if readErr != nil {
			t.Fatalf("no echo for %q: %v", payload, readErr)
		}
		got, decodeErr := socks5.ReadUDPDatagram(buf[:n])
		if decodeErr != nil {
			t.Fatal(decodeErr)
		}
		if string(got.Payload) != payload {
			t.Fatalf("echo %q, want %q", got.Payload, payload)
		}
	}

	send("before-rescue")
	before := seenSources()
	if len(before) != 1 {
		t.Fatalf("the destination saw %d packets before the rescue, want 1", len(before))
	}

	// Kill the QUIC listener under the association. The client rescues onto
	// TLS/TCP, which is a different transport to the same server -- so the
	// relay it reclaims is genuinely the retained one and not an artefact of
	// the connection surviving.
	quicCancel()
	deadline := time.Now().Add(10 * time.Second)
	for client.Metrics().Snapshot().UDPAssociationReconnects == 0 && time.Now().Before(deadline) {
		time.Sleep(25 * time.Millisecond)
	}
	if got := client.Metrics().Snapshot(); got.UDPAssociationReconnects == 0 {
		t.Fatalf("the QUIC lane failure did not trigger a rescue: %+v", got)
	}
	send("after-rescue")

	after := seenSources()
	if len(after) < 2 {
		t.Fatalf("the destination saw %d packets in total, want at least 2", len(after))
	}
	if after[0] != after[len(after)-1] {
		t.Errorf("the destination saw %s before the rescue and %s after it, so the "+
			"association moved to a different source address mid-conversation",
			after[0], after[len(after)-1])
	}

	serviceCancel()
	for range 3 {
		select {
		case <-errorsCh:
		case <-time.After(5 * time.Second):
			t.Fatal("service shutdown timeout")
		}
	}
}
