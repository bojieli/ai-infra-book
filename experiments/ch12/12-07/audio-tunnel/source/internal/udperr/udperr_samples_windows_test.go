//go:build windows

package udperr

import "golang.org/x/sys/windows"

// perDatagramSamples names the codes Winsock reports for one datagram. These
// are the WSA values, not the syscall package's same-named constants: on
// Windows syscall.ECONNREFUSED is a synthetic APPLICATION_ERROR value that no
// socket ever returns.
var perDatagramSamples = []struct {
	name string
	err  error
}{
	{"unreachable peer", windows.WSAECONNREFUSED},
	{"reset", windows.WSAECONNRESET},
	{"oversized datagram", windows.WSAEMSGSIZE},
	{"ttl expired", windows.WSAENETRESET},
}
