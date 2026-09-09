//go:build !windows

package pep

import (
	"errors"
	"syscall"
)

// The Unix half of the socket-error vocabulary. Each predicate has a Windows
// twin naming the Winsock code for the same condition; see sockerr_windows.go
// for why the two lists cannot be one.

// unreachableRouteErrno reports the codes that mean the host has no usable
// route to the peer right now, which is negative reachability evidence.
func unreachableRouteErrno(err error) bool {
	return errors.Is(err, syscall.ENETUNREACH) ||
		errors.Is(err, syscall.EHOSTUNREACH) ||
		errors.Is(err, syscall.ENETDOWN) ||
		errors.Is(err, syscall.EHOSTDOWN)
}

// transientRouteWriteErrno reports the codes a local send returns while the
// route is momentarily absent -- changing networks, a link flapping, or the
// send queue briefly full. The socket outlives all of them.
//
// EADDRNOTAVAIL is deliberately absent. It means the source address a bound
// socket owns has disappeared, as happens after DHCP assigns a different
// address on a new Wi-Fi network. That socket cannot adopt the replacement
// address, so hiding the error would keep QUIC retransmitting forever on a
// path which cannot send.
func transientRouteWriteErrno(err error) bool {
	return unreachableRouteErrno(err) ||
		errors.Is(err, syscall.ENOBUFS)
}

// halfCloseErrno reports the codes that mean the local application closed its
// socket around the moment the proxy tried to finish with it.
func halfCloseErrno(err error) bool {
	return errors.Is(err, syscall.ENOTCONN) ||
		errors.Is(err, syscall.EPIPE) ||
		errors.Is(err, syscall.ECONNRESET) ||
		errors.Is(err, syscall.ECONNABORTED)
}

// destinationCloseErrno reports the codes that mean the far side reset the
// connection after the client had already finished with it.
func destinationCloseErrno(err error) bool {
	return errors.Is(err, syscall.ECONNRESET) ||
		errors.Is(err, syscall.ECONNABORTED) ||
		errors.Is(err, syscall.ENOTCONN)
}
