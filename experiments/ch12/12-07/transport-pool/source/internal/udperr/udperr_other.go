//go:build !windows

package udperr

import (
	"errors"
	"syscall"
)

// transientDatagramError is the Unix counterpart. Linux surfaces a received
// ICMP port-unreachable as ECONNREFUSED on a connected UDP socket, so the same
// distinction applies even though the Windows form is the one that broke CI.
// EMSGSIZE covers a truncated oversized datagram.
func transientDatagramError(err error) bool {
	return errors.Is(err, syscall.ECONNREFUSED) ||
		errors.Is(err, syscall.ECONNRESET) ||
		errors.Is(err, syscall.EMSGSIZE)
}
