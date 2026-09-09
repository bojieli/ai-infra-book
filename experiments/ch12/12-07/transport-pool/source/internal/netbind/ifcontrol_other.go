//go:build !darwin

package netbind

import "syscall"

// InterfaceControl returns nil on non-Darwin platforms: kernel-level interface
// binding via socket options is not implemented here. IP-address binding (the
// existing localAddress mechanism) remains in effect.
func InterfaceControl(ifName string) func(string, string, syscall.RawConn) error {
	return nil
}
