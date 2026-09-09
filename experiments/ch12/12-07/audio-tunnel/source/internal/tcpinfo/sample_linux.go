//go:build linux

package tcpinfo

import (
	"fmt"
	"net"
	"syscall"
	"unsafe"

	"golang.org/x/sys/unix"
)

// bufLen is generous on purpose. struct tcp_info has grown with almost every
// kernel release, and asking for more than the kernel has costs one page of
// stack and returns a shorter length rather than an error.
const bufLen = 512

// Get reads TCP_INFO from an established connection.
//
// The option is read as raw bytes through the syscall rather than through a
// typed helper for two reasons. A typed binding is compiled against one
// version of a struct the kernel keeps extending, so it misreads a longer
// layout silently; and the string helper truncates at the first zero byte,
// which in a binary struct whose second field is usually zero means it returns
// almost nothing. Both failures are quiet, which is the worst property a
// measurement instrument can have.
func Get(c *net.TCPConn) (Info, error) {
	raw, err := c.SyscallConn()
	if err != nil {
		return Info{}, err
	}
	var buf [bufLen]byte
	length := uint32(bufLen)
	var errno unix.Errno
	cerr := raw.Control(func(fd uintptr) {
		_, _, errno = unix.Syscall6(unix.SYS_GETSOCKOPT, fd,
			uintptr(unix.IPPROTO_TCP), uintptr(unix.TCP_INFO),
			uintptr(unsafe.Pointer(&buf[0])),
			uintptr(unsafe.Pointer(&length)), 0)
	})
	if cerr != nil {
		return Info{}, cerr
	}
	if errno != 0 {
		return Info{}, fmt.Errorf("getsockopt TCP_INFO: %w", errno)
	}
	if length == 0 {
		return Info{}, fmt.Errorf("getsockopt TCP_INFO returned no data")
	}
	return Parse(buf[:length]), nil
}

// SetCongestionControl selects the algorithm for one socket, which is how a
// measurement compares controllers on the same path in the same minutes
// rather than across a day in which the path may have changed.
func SetCongestionControl(c syscall.RawConn, name string) error {
	var oerr error
	if err := c.Control(func(fd uintptr) {
		oerr = unix.SetsockoptString(int(fd), unix.IPPROTO_TCP, unix.TCP_CONGESTION, name)
	}); err != nil {
		return err
	}
	return oerr
}
