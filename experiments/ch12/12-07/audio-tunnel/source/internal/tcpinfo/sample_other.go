//go:build !linux

package tcpinfo

import (
	"errors"
	"net"
	"syscall"
)

// ErrUnsupported is returned where the kernel has no TCP_INFO to give. The
// measurement tools that use this package are meaningful only on the hosts
// whose paths are being characterised, and those are Linux; building
// elsewhere has to succeed so the rest of the tree stays portable.
var ErrUnsupported = errors.New("tcpinfo: not supported on this platform")

func Get(*net.TCPConn) (Info, error) { return Info{}, ErrUnsupported }

func SetCongestionControl(syscall.RawConn, string) error { return ErrUnsupported }
