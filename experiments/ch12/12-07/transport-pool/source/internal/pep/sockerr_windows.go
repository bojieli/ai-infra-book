//go:build windows

package pep

import (
	"errors"

	"golang.org/x/sys/windows"
)

// The Winsock half of the socket-error vocabulary, and the reason it has to
// exist separately at all.
//
// syscall.ENETUNREACH and its neighbours are not Winsock codes on Windows.
// GOROOT's syscall/zerrors_windows.go defines them under the heading "Invented
// values to support what package os and others expects", as APPLICATION_ERROR
// + iota -- values above 1<<29 that no socket ever returns. A real interface
// going away gives WSAENETUNREACH, 10051. syscall.Errno.Is bridges only
// ErrPermission, ErrExist, ErrNotExist and ErrUnsupported, so errors.Is never
// connects the invented constant to the code the socket reported.
//
// This catches syscall.ECONNRESET too, which is easy to trust because package
// syscall does define a WSAECONNRESET on Windows -- as a separate constant,
// 10054. The one spelled syscall.ECONNRESET is the invented one, and it is the
// spelling shared with Unix, so it is the one that gets written.
//
// A classifier built from the syscall names therefore compiles on Windows,
// passes any test that injects those same syscall names, and matches nothing a
// real socket produces. That is how this shipped: the route-error tolerance
// that keeps a QUIC connection alive across a network change was dead on the
// platform whose users change networks most, and its tests were green because
// they asserted against the same invented constants the classifier read.
//
// ERROR_NETNAME_DELETED appears alongside WSAECONNRESET because Windows raises
// it for the same condition on an overlapped operation; the standard library
// treats the two as interchangeable in internal/poll.

func unreachableRouteErrno(err error) bool {
	return errors.Is(err, windows.WSAENETUNREACH) ||
		errors.Is(err, windows.WSAEHOSTUNREACH) ||
		errors.Is(err, windows.WSAENETDOWN) ||
		errors.Is(err, windows.WSAEHOSTDOWN)
}

func transientRouteWriteErrno(err error) bool {
	return unreachableRouteErrno(err) ||
		errors.Is(err, windows.WSAENOBUFS)
}

// halfCloseErrno also names WSAESHUTDOWN, which is what a send reports once
// the local side has shut the socket down. There is no EPIPE counterpart to
// carry over: a Windows socket says WSAECONNRESET or WSAECONNABORTED where a
// Unix one says EPIPE.
func halfCloseErrno(err error) bool {
	return errors.Is(err, windows.WSAENOTCONN) ||
		errors.Is(err, windows.WSAESHUTDOWN) ||
		errors.Is(err, windows.WSAECONNRESET) ||
		errors.Is(err, windows.WSAECONNABORTED) ||
		errors.Is(err, windows.ERROR_NETNAME_DELETED)
}

func destinationCloseErrno(err error) bool {
	return errors.Is(err, windows.WSAECONNRESET) ||
		errors.Is(err, windows.WSAECONNABORTED) ||
		errors.Is(err, windows.WSAENOTCONN) ||
		errors.Is(err, windows.ERROR_NETNAME_DELETED)
}
