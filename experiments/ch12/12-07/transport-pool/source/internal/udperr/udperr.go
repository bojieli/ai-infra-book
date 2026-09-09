// Package udperr classifies UDP read errors that describe a single datagram
// rather than the socket carrying it.
//
// A UDP socket can be handed an error caused by a datagram it already sent:
// when a send draws an ICMP port-unreachable, the host reports it on a
// subsequent receive. The socket is still perfectly usable. Code that treats
// every read error as terminal therefore tears down a working relay because
// one peer went away, and the symptom is not an error but silence -- traffic
// simply stops, and whatever was waiting for it fails on a deadline much later
// with nothing to point at.
//
// Windows is where this bites, because it reports the condition on unconnected
// UDP sockets as WSAECONNRESET where Linux reports it only on connected ones.
// quic-go skips the same errors in its own receive loop for the same reason.
package udperr

import (
	"errors"
	"net"
)

// Transient reports whether err describes one datagram, leaving the socket
// usable. A nil error is not transient because there is nothing to skip.
func Transient(err error) bool {
	if err == nil {
		return false
	}
	// A closed socket is terminal however it is wrapped, and must be checked
	// before the per-datagram codes.
	if errors.Is(err, net.ErrClosed) {
		return false
	}
	return transientDatagramError(err)
}

// Fatal reports whether a read error means the loop should stop. Anything
// unrecognised is fatal: continuing on an error that will recur every
// iteration turns a dead socket into a busy loop, which is worse than exiting.
func Fatal(err error) bool {
	if err == nil {
		return false
	}
	if errors.Is(err, net.ErrClosed) {
		return true
	}
	var netErr net.Error
	if errors.As(err, &netErr) && netErr.Timeout() {
		return false
	}
	return !transientDatagramError(err)
}
