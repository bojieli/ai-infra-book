package udperr

import (
	"errors"
	"net"
	"os"
	"testing"
	"time"
)

// The distinction this package exists to draw: a datagram's error leaves the
// socket usable, a closed socket does not, and anything unrecognised is
// treated as fatal so a permanent error cannot become a busy loop.
//
// The per-datagram codes themselves live in the build-tagged sample files,
// because a code is only per-datagram on the platform that reports it. On
// Windows syscall.ECONNREFUSED is a synthetic APPLICATION_ERROR value rather
// than WSAECONNREFUSED, and syscall.Errno.Is does not bridge the two, so a
// table of Unix errnos asserts nothing about what a Winsock socket returns.
func TestOneDatagramsErrorIsNotTheSocketsError(t *testing.T) {
	for _, test := range []struct {
		name      string
		err       error
		transient bool
		fatal     bool
	}{
		{"nothing", nil, false, false},
		{"closed socket", net.ErrClosed, false, true},
		{"wrapped closed socket", &net.OpError{Op: "read", Err: net.ErrClosed}, false, true},
		{"deadline", os.ErrDeadlineExceeded, false, false},
		{"unrecognised", errors.New("never seen before"), false, true},
	} {
		t.Run(test.name, func(t *testing.T) {
			if got := Transient(test.err); got != test.transient {
				t.Errorf("Transient(%v) = %v, want %v", test.err, got, test.transient)
			}
			if got := Fatal(test.err); got != test.fatal {
				t.Errorf("Fatal(%v) = %v, want %v", test.err, got, test.fatal)
			}
		})
	}
}

// Each code this platform reports for a single datagram must be skippable,
// bare and wrapped the way the net package hands it back.
func TestThisPlatformsPerDatagramCodesAreSkippable(t *testing.T) {
	if len(perDatagramSamples) == 0 {
		t.Fatal("no per-datagram codes named for this platform")
	}
	for _, sample := range perDatagramSamples {
		t.Run(sample.name, func(t *testing.T) {
			for label, err := range map[string]error{
				"bare":    sample.err,
				"wrapped": &net.OpError{Op: "read", Err: sample.err},
			} {
				if !Transient(err) {
					t.Errorf("Transient(%s %v) = false, want true", label, err)
				}
				if Fatal(err) {
					t.Errorf("Fatal(%s %v) = true, want false", label, err)
				}
			}
		})
	}
}

// A closed socket must stay fatal even though Winsock reports the close with a
// code this package otherwise skips, so the two checks cannot be reordered.
func TestAClosedSocketIsNeverTransient(t *testing.T) {
	closed := &net.OpError{Op: "read", Err: net.ErrClosed}
	if Transient(closed) {
		t.Fatal("a closed socket must not be reported as a per-datagram error")
	}
	if !Fatal(closed) {
		t.Fatal("a closed socket must be fatal")
	}
}

// The sample lists above are hand-written, so they can drift from what the
// host actually reports -- which is the mistake that first shipped here. This
// draws a real ICMP port-unreachable and requires the classifier to recognise
// whatever code arrives, so a listed-codes-versus-real-codes mismatch fails
// here instead of silently killing a read loop.
//
// Both socket kinds are probed because the platforms disagree about which one
// is told. Windows reports it on an unconnected socket, which is the case the
// production read loops actually hit; Linux and macOS report it only on a
// connected socket. A host that reports neither skips rather than failing,
// and the subtest logs which route it took so the CI record says whether the
// assertion was load-bearing on that runner.
func TestTheCodeTheHostActuallyReportsIsRecognised(t *testing.T) {
	for _, probe := range []struct {
		name string
		dial func(*net.UDPAddr) (sender, error)
	}{
		{"unconnected socket", dialUnconnected},
		{"connected socket", dialConnected},
	} {
		t.Run(probe.name, func(t *testing.T) {
			vanished, err := closedLoopbackPort()
			if err != nil {
				t.Skipf("no closed loopback port: %v", err)
			}
			conn, err := probe.dial(vanished)
			if err != nil {
				t.Skipf("no socket: %v", err)
			}
			t.Cleanup(conn.Close)
			requireTheReportedCodeIsSkippable(t, conn)
		})
	}
}

// sender is the part of a UDP socket this probe needs, so one body can drive
// both the connected and the unconnected form.
type sender interface {
	send() error
	receive([]byte, time.Duration) error
	Close()
}

func closedLoopbackPort() (*net.UDPAddr, error) {
	held, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		return nil, err
	}
	addr := held.LocalAddr().(*net.UDPAddr)
	if err := held.Close(); err != nil {
		return nil, err
	}
	return addr, nil
}

type connectedSender struct{ conn *net.UDPConn }

func dialConnected(to *net.UDPAddr) (sender, error) {
	conn, err := net.DialUDP("udp", nil, to)
	if err != nil {
		return nil, err
	}
	return &connectedSender{conn: conn}, nil
}

func (s *connectedSender) send() error { _, err := s.conn.Write([]byte("probe")); return err }
func (s *connectedSender) receive(buf []byte, within time.Duration) error {
	if err := s.conn.SetReadDeadline(time.Now().Add(within)); err != nil {
		return err
	}
	_, _, err := s.conn.ReadFromUDP(buf)
	return err
}
func (s *connectedSender) Close() { _ = s.conn.Close() }

type unconnectedSender struct {
	conn *net.UDPConn
	to   *net.UDPAddr
}

func dialUnconnected(to *net.UDPAddr) (sender, error) {
	conn, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		return nil, err
	}
	return &unconnectedSender{conn: conn, to: to}, nil
}

func (s *unconnectedSender) send() error {
	_, err := s.conn.WriteToUDP([]byte("probe"), s.to)
	return err
}
func (s *unconnectedSender) receive(buf []byte, within time.Duration) error {
	if err := s.conn.SetReadDeadline(time.Now().Add(within)); err != nil {
		return err
	}
	_, _, err := s.conn.ReadFromUDP(buf)
	return err
}
func (s *unconnectedSender) Close() { _ = s.conn.Close() }

func requireTheReportedCodeIsSkippable(t *testing.T, conn sender) {
	t.Helper()
	// The first send draws the ICMP reply and a later read reports it, so
	// send repeatedly: which read carries it is not guaranteed.
	buf := make([]byte, 128)
	for attempt := 1; attempt <= 8; attempt++ {
		if err := conn.send(); err != nil {
			if Transient(err) {
				t.Logf("the send reported the unreachable peer: %#v", err)
				return
			}
			t.Skipf("cannot send to a closed port: %v", err)
		}
		err := conn.receive(buf, 250*time.Millisecond)
		if err == nil {
			t.Skip("something answered on the closed port")
		}
		var netErr net.Error
		if errors.As(err, &netErr) && netErr.Timeout() {
			continue
		}
		if !Transient(err) {
			t.Fatalf("the host reported %#v for an unreachable peer and this package "+
				"calls it fatal; the per-datagram sample list is missing that code", err)
		}
		if Fatal(err) {
			t.Fatalf("Fatal(%#v) = true for a live socket", err)
		}
		t.Logf("read %d reported the unreachable peer: %#v", attempt, err)
		return
	}
	t.Skip("this host does not report an unreachable peer on this socket kind")
}
