package pep

import (
	"context"
	"encoding/binary"
	"io"
	"log/slog"
	"net"
	"strconv"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/pathmodel"
	"github.com/bojieli/queqiao/internal/socks5"
)

// A UDP association must outlive a destination that stops listening.
//
// Sending to a closed UDP port draws an ICMP port-unreachable, and the host
// reports it to the sender on a *later* read. Windows does this even for an
// unconnected socket, where it arrives as WSAECONNRESET. The relay loops used
// to return on any non-timeout read error, so one dead destination ended the
// whole association -- every other destination the client was talking to went
// with it, and from the application's side nothing failed, traffic just
// stopped.
//
// This is the SOCKS5 data plane rather than the test emulator, so it is a
// shipping bug on Windows and not only a CI one: a client that sends a DNS
// query to a resolver that has gone away loses its association.
func TestAUDPAssociationSurvivesAnUnreachableDestination(t *testing.T) {
	// Every endpoint here is loopback, so this shares one path key with every
	// other test in the package. This one runs over a clean path, and leaving
	// a clean measurement behind would size another test's code from a channel
	// it never ran on.
	pathmodel.Reset()
	t.Cleanup(pathmodel.Reset)

	live, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.ParseIP("127.0.0.1")})
	if err != nil {
		t.Fatal(err)
	}
	defer live.Close()
	go func() {
		buf := make([]byte, 2048)
		for {
			n, addr, readErr := live.ReadFromUDP(buf)
			if readErr != nil {
				return
			}
			_, _ = live.WriteToUDP(buf[:n], addr)
		}
	}()

	// A destination that is bound only long enough to have an address, then
	// closed, so datagrams to it are refused rather than dropped.
	dead, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.ParseIP("127.0.0.1")})
	if err != nil {
		t.Fatal(err)
	}
	deadAddr := dead.LocalAddr().String()
	if err := dead.Close(); err != nil {
		t.Fatal(err)
	}

	certificate, roots := testCertificate(t)
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	serverListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	serverAddr := serverListener.Addr().String()
	server, err := NewServer(ServerConfig{
		ListenAddr: serverAddr, Credentials: certificate,
		DestinationPolicy: DestinationPolicy{AllowPrivate: true},
		EnableTCP:         true, Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	clientListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	client, err := NewClient(ClientConfig{
		ListenAddr: clientListener.Addr().String(), RemoteAddr: serverAddr,
		Credentials: roots, Transport: TransportTCP, Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	errorsCh := make(chan error, 2)
	go func() { errorsCh <- server.ServeListener(ctx, serverListener) }()
	go func() { errorsCh <- client.ServeListener(ctx, clientListener) }()

	control, err := net.DialTimeout("tcp", clientListener.Addr().String(), 5*time.Second)
	if err != nil {
		t.Fatal(err)
	}
	defer control.Close()
	_ = control.SetDeadline(time.Now().Add(15 * time.Second))
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
	bound := net.JoinHostPort(net.IP(reply[4:8]).String(),
		strconv.Itoa(int(binary.BigEndian.Uint16(reply[8:10]))))

	udpClient, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.ParseIP("127.0.0.1")})
	if err != nil {
		t.Fatal(err)
	}
	defer udpClient.Close()

	envelope := func(destination, payload string) []byte {
		host, portText, splitErr := net.SplitHostPort(destination)
		if splitErr != nil {
			t.Fatal(splitErr)
		}
		port, convErr := strconv.Atoi(portText)
		if convErr != nil {
			t.Fatal(convErr)
		}
		out := []byte{0, 0, 0, 1}
		out = append(out, net.ParseIP(host).To4()...)
		var portBytes [2]byte
		binary.BigEndian.PutUint16(portBytes[:], uint16(port))
		out = append(out, portBytes[:]...)
		return append(out, payload...)
	}

	// Establish the association against a destination that answers, so the
	// relay loops are running before anything is refused.
	if _, err := udpClient.WriteToUDP(envelope(live.LocalAddr().String(), "before"),
		mustUDPAddr(t, bound)); err != nil {
		t.Fatal(err)
	}
	buf := make([]byte, 2048)
	_ = udpClient.SetReadDeadline(time.Now().Add(10 * time.Second))
	n, _, err := udpClient.ReadFromUDP(buf)
	if err != nil {
		t.Fatalf("first echo before any unreachable destination: %v", err)
	}
	got, err := socks5.ReadUDPDatagram(buf[:n])
	if err != nil {
		t.Fatal(err)
	}
	if string(got.Payload) != "before" {
		t.Fatalf("payload %q, want %q", got.Payload, "before")
	}

	// Now send to the closed port several times. Each one draws an ICMP
	// unreachable back to whichever socket sent it.
	for i := 0; i < 5; i++ {
		if _, err := udpClient.WriteToUDP(envelope(deadAddr, "gone"),
			mustUDPAddr(t, bound)); err != nil {
			t.Fatal(err)
		}
		time.Sleep(50 * time.Millisecond)
	}

	// The association must still work. Before the fix this timed out on
	// Windows, because the unreachable had ended the relay's read loop.
	if _, err := udpClient.WriteToUDP(envelope(live.LocalAddr().String(), "after"),
		mustUDPAddr(t, bound)); err != nil {
		t.Fatal(err)
	}
	deadline := time.Now().Add(15 * time.Second)
	for {
		remaining := time.Until(deadline)
		if remaining <= 0 {
			t.Fatal("association stopped carrying traffic after a destination became unreachable")
		}
		_ = udpClient.SetReadDeadline(time.Now().Add(remaining))
		n, _, err := udpClient.ReadFromUDP(buf)
		if err != nil {
			t.Fatalf("echo after an unreachable destination: %v", err)
		}
		got, err := socks5.ReadUDPDatagram(buf[:n])
		if err != nil {
			t.Fatal(err)
		}
		if string(got.Payload) == "after" {
			break
		}
	}

	cancel()
	for range 2 {
		if err := <-errorsCh; err != nil {
			t.Fatalf("service shutdown: %v", err)
		}
	}
}
