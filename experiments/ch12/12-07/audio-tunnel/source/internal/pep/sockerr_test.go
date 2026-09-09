package pep

import (
	"errors"
	"net"
	"syscall"
	"testing"
)

// errnoSample names one code a real socket reports for a condition the
// classifiers have to recognise. The lists live in the build-tagged sample
// files, because the constants that spell them differ by platform even where
// the condition does not.
type errnoSample struct {
	name string
	err  error
}

// Each classifier must accept every code this platform reports for its
// condition, bare and wrapped the way the net package hands it back.
func TestThisPlatformsSocketCodesAreClassified(t *testing.T) {
	for _, group := range []struct {
		what    string
		samples []errnoSample
		accepts func(error) bool
	}{
		{"a transient route write failure", transientRouteWriteSamples, transientRouteWriteError},
		{"an unreachable route", unreachableRouteSamples, unreachableRouteErrno},
		{"a local half-close", halfCloseSamples, expectedHalfCloseError},
		{"a destination close", destinationCloseSamples, expectedDestinationCloseError},
	} {
		t.Run(group.what, func(t *testing.T) {
			if len(group.samples) == 0 {
				t.Fatal("no codes named for this platform")
			}
			for _, sample := range group.samples {
				t.Run(sample.name, func(t *testing.T) {
					for label, err := range map[string]error{
						"bare":    sample.err,
						"wrapped": &net.OpError{Op: "write", Net: "udp", Err: sample.err},
					} {
						if !group.accepts(err) {
							t.Errorf("%s %v was not recognised as %s", label, err, group.what)
						}
					}
				})
			}
		})
	}
}

// A permanent socket error must not be swallowed by any of them. Tolerating a
// route error turns a failed write into a dropped packet, which is right for a
// route that will come back and wrong for a socket that will not.
func TestPermanentSocketErrorsAreNotTolerated(t *testing.T) {
	err := &net.OpError{Op: "write", Net: "udp", Err: permanentSocketError}
	for what, accepts := range map[string]func(error) bool{
		"a transient route write failure": transientRouteWriteError,
		"an unreachable route":            unreachableRouteErrno,
		"a local half-close":              expectedHalfCloseError,
		"a destination close":             expectedDestinationCloseError,
	} {
		if accepts(err) {
			t.Errorf("%v was treated as %s", err, what)
		}
	}
}

// The sample lists above are hand-written against the platform's documented
// codes, and a hand-written list is exactly what was wrong before: the
// classifiers named syscall.ENETUNREACH and friends, which on Windows are
// synthetic APPLICATION_ERROR values no socket returns, and the tests injected
// those same constants. Both were self-consistently wrong, and the feature was
// dead on Windows while its tests were green.
//
// This draws the codes from the host instead. Each case performs an operation
// whose failure is not in doubt and requires the classifier to recognise
// whatever the host actually reported, so a list that drifts from reality
// fails here rather than in production.
func TestTheCodesTheHostActuallyReportsAreClassified(t *testing.T) {
	for _, probe := range []struct {
		what    string
		draw    func(*testing.T) error
		accepts func(error) bool
	}{
		{
			// Binding to an address this host does not hold is the one source
			// error a test can provoke without touching the machine's network
			// configuration. A socket bound to an address which vanished cannot
			// adopt the replacement address, so this must remain fatal instead
			// of being disguised as one lost datagram.
			what:    "a source address this host does not hold",
			draw:    bindToAnAddressThisHostDoesNotHold,
			accepts: func(err error) bool { return !transientRouteWriteError(err) },
		},
		{
			// A write to a socket whose peer has gone reports the local
			// half-close condition, whichever spelling this platform uses.
			what:    "a write to a connection the peer closed",
			draw:    writeToAClosedPeer,
			accepts: expectedHalfCloseError,
		},
	} {
		t.Run(probe.what, func(t *testing.T) {
			err := probe.draw(t)
			if err == nil {
				t.Skip("this host did not fail the operation")
			}
			var errno syscall.Errno
			if !errors.As(err, &errno) {
				t.Skipf("host reported %#v, which carries no errno", err)
			}
			if !probe.accepts(err) {
				t.Fatalf("the host reported errno %d (%v) for %s and no classifier "+
					"recognises it; the sample list is missing that code",
					uintptr(errno), errno, probe.what)
			}
			t.Logf("host reported errno %d (%v)", uintptr(errno), errno)
		})
	}
}

// bindToAnAddressThisHostDoesNotHold uses a TEST-NET-3 address, which is
// reserved for documentation and so is never a real local interface.
func bindToAnAddressThisHostDoesNotHold(t *testing.T) error {
	conn, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(203, 0, 113, 7)})
	if err == nil {
		t.Cleanup(func() { _ = conn.Close() })
		return nil
	}
	return err
}

// writeToAClosedPeer keeps writing until the peer's close is reported, since
// the first write after a close often succeeds into the socket buffer.
func writeToAClosedPeer(t *testing.T) error {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Skipf("no loopback listener: %v", err)
	}
	defer listener.Close()
	client, err := net.Dial("tcp", listener.Addr().String())
	if err != nil {
		t.Skipf("no loopback connection: %v", err)
	}
	defer client.Close()
	server, err := listener.Accept()
	if err != nil {
		t.Skipf("no accepted connection: %v", err)
	}
	// A reset rather than an orderly close, so the writer is told rather than
	// simply reaching EOF on its next read.
	if tcp, ok := server.(*net.TCPConn); ok {
		_ = tcp.SetLinger(0)
	}
	_ = server.Close()
	payload := make([]byte, 64*1024)
	for attempt := 0; attempt < 16; attempt++ {
		if _, err := client.Write(payload); err != nil {
			return err
		}
	}
	return nil
}
