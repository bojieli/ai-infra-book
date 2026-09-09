package pathsim

import (
	"net"
	"testing"
	"time"
)

// The relay must keep carrying traffic after a peer it has sent to disappears.
// On Windows the send to the vanished peer draws an ICMP port-unreachable that
// is reported on a later receive; before this was classified, that receive
// ended the direction and the emulated path went silently dead.
//
// Whether the host actually delivers that error decides what this test can
// prove. Windows reports it on both connected and unconnected UDP sockets, so
// there it exercises the real path; Linux reports it only on a connected one,
// which is the per-peer socket; macOS does not report it here at all. So this
// passes with or without the classification on a developer's machine and is
// load-bearing on the runner that found the bug. The classification itself is
// pinned on every platform by the table in internal/udperr.
//
// What made the consequence severe is that r.local is shared by every client
// of one relay, so the direction that died carried all of them: a test whose
// first half looked healthy could have its second half degraded by an
// unreachable drawn on behalf of some other flow entirely.
func TestARelaySurvivesAPeerThatDisappears(t *testing.T) {
	target, err := net.ListenUDP("udp", mustResolve(t, "127.0.0.1:0"))
	if err != nil {
		t.Fatal(err)
	}
	defer target.Close()

	relay, err := New("127.0.0.1:0", target.LocalAddr().String(), Config{})
	if err != nil {
		t.Fatal(err)
	}
	defer relay.Close()

	relayAddr := mustResolve(t, relay.LocalAddr())

	// A client that sends one packet and vanishes, so the relay's reply has
	// nowhere to go and the host generates an unreachable for it.
	gone, err := net.ListenUDP("udp", mustResolve(t, "127.0.0.1:0"))
	if err != nil {
		t.Fatal(err)
	}
	if _, err := gone.WriteTo([]byte("first"), relayAddr); err != nil {
		t.Fatal(err)
	}
	buf := make([]byte, 1500)
	_ = target.SetReadDeadline(time.Now().Add(5 * time.Second))
	n, from, err := target.ReadFrom(buf)
	if err != nil {
		t.Fatalf("relay did not forward the first packet: %v", err)
	}
	if string(buf[:n]) != "first" {
		t.Fatalf("forwarded %q, want %q", buf[:n], "first")
	}
	if err := gone.Close(); err != nil {
		t.Fatal(err)
	}
	// Reply to the address that has just been closed, which is what draws the
	// unreachable back to the relay.
	for i := 0; i < 3; i++ {
		if _, err := target.WriteTo([]byte("reply"), from); err != nil {
			t.Fatal(err)
		}
		time.Sleep(20 * time.Millisecond)
	}

	// A second client must still get through. Before the fix the relay's
	// client-side loop had returned and this timed out.
	survivor, err := net.ListenUDP("udp", mustResolve(t, "127.0.0.1:0"))
	if err != nil {
		t.Fatal(err)
	}
	defer survivor.Close()
	if _, err := survivor.WriteTo([]byte("second"), relayAddr); err != nil {
		t.Fatal(err)
	}
	_ = target.SetReadDeadline(time.Now().Add(10 * time.Second))
	for {
		n, _, err := target.ReadFrom(buf)
		if err != nil {
			t.Fatalf("relay stopped forwarding after a peer disappeared: %v", err)
		}
		if string(buf[:n]) == "second" {
			return
		}
	}
}

func mustResolve(t *testing.T, addr string) *net.UDPAddr {
	t.Helper()
	resolved, err := net.ResolveUDPAddr("udp", addr)
	if err != nil {
		t.Fatal(err)
	}
	return resolved
}
