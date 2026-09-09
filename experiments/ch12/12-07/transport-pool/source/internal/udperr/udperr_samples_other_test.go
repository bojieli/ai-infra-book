//go:build !windows

package udperr

import "syscall"

// perDatagramSamples names the codes a Unix socket reports for one datagram.
// ECONNREFUSED is a received ICMP port-unreachable on a connected socket, and
// EMSGSIZE is a datagram truncated into a short buffer.
var perDatagramSamples = []struct {
	name string
	err  error
}{
	{"unreachable peer", syscall.ECONNREFUSED},
	{"reset", syscall.ECONNRESET},
	{"oversized datagram", syscall.EMSGSIZE},
}
