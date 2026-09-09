//go:build windows

package udperr

import (
	"errors"

	"golang.org/x/sys/windows"
)

// transientDatagramError names the Winsock codes that describe one datagram.
//
// WSAECONNRESET arrives on a UDP socket when an earlier send drew an ICMP
// port-unreachable -- routine whenever a peer has gone away -- and
// WSAECONNREFUSED is its connected-socket counterpart. WSAEMSGSIZE means the
// datagram exceeded the buffer and was truncated, so the next read is fine.
// WSAENETRESET is the TTL-expired equivalent. None of them say the socket is
// finished.
func transientDatagramError(err error) bool {
	return errors.Is(err, windows.WSAECONNRESET) ||
		errors.Is(err, windows.WSAECONNREFUSED) ||
		errors.Is(err, windows.WSAEMSGSIZE) ||
		errors.Is(err, windows.WSAENETRESET)
}
