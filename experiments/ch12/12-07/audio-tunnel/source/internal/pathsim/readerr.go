package pathsim

import (
	"github.com/bojieli/queqiao/internal/udperr"
)

// fatalReadError reports whether a relay read error means the socket is
// finished, as opposed to something one datagram did.
//
// The relay's two read loops used to return on any error, and on Windows that
// silently blackholed the emulated path: a send to a QUIC endpoint that had
// gone away drew an ICMP port-unreachable, the host reported it on a later
// receive as WSAECONNRESET, and the direction ended for good. Every packet
// after that was dropped by the emulator rather than by its configured loss
// model, so the path did not error -- it just stopped carrying bytes, and the
// test using it failed on a read deadline a minute later with nothing pointing
// at the cause.
//
// Only internal/pep saw it, because it is the one package that runs QUIC
// across this relay, and QUIC opens and closes sockets as connections come and
// go. pathsim's own tests send plain UDP between endpoints that stay up, so
// they never produce an unreachable -- which is why the emulator's suite
// passed on Windows while the pep tests using it failed there.
//
// See internal/udperr for the classification itself.
func fatalReadError(err error) bool { return udperr.Fatal(err) }
