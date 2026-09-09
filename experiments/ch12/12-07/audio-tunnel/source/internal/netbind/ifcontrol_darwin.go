package netbind

import (
	"fmt"
	"net"
	"strings"
	"syscall"
)

// InterfaceControl returns a socket control function that binds the socket to
// the named interface at the kernel level using IP_BOUND_IF (IPv4) or
// IPV6_BOUND_IF (IPv6). This sets the INP_BOUND_IF flag in the kernel PCB,
// which is what NEAppProxyFlow.isBound reflects in the macOS Network Extension
// API. Any transparent proxy that honours isBound will then let these sockets
// bypass capture without needing a per-process exclusion rule.
//
// An empty ifName is a no-op: InterfaceControl("") returns nil.
func InterfaceControl(ifName string) func(string, string, syscall.RawConn) error {
	if ifName == "" {
		return nil
	}
	return func(network, address string, conn syscall.RawConn) error {
		iface, err := net.InterfaceByName(ifName)
		if err != nil {
			return fmt.Errorf("IP_BOUND_IF: look up interface %q: %w", ifName, err)
		}
		idx := iface.Index
		var setErr error
		ctrlErr := conn.Control(func(fd uintptr) {
			if strings.HasSuffix(network, "6") {
				setErr = syscall.SetsockoptInt(int(fd), syscall.IPPROTO_IPV6, syscall.IPV6_BOUND_IF, idx)
			} else {
				setErr = syscall.SetsockoptInt(int(fd), syscall.IPPROTO_IP, syscall.IP_BOUND_IF, idx)
			}
		})
		if ctrlErr != nil {
			return ctrlErr
		}
		return setErr
	}
}
