//go:build linux

package pep

import (
	"errors"
	"fmt"
	"net"
	"syscall"

	"golang.org/x/sys/unix"
)

func setTCPListenerCongestion(listener net.Listener, name string) error {
	if name == tcpCongestionSystem {
		return nil
	}
	return setSocketCongestion(listener, name)
}

func setTCPConnCongestion(conn net.Conn, name string) error {
	if name == tcpCongestionSystem {
		return nil
	}
	return setSocketCongestion(conn, name)
}

func setSocketCongestion(socket any, name string) error {
	sc, ok := socket.(syscall.Conn)
	if !ok {
		return errors.New("TCP socket does not expose a raw connection")
	}
	raw, err := sc.SyscallConn()
	if err != nil {
		return err
	}
	var socketErr error
	if err := raw.Control(func(fd uintptr) {
		socketErr = unix.SetsockoptString(int(fd), unix.IPPROTO_TCP, unix.TCP_CONGESTION, name)
	}); err != nil {
		return err
	}
	if socketErr != nil {
		return fmt.Errorf("set TCP_CONGESTION=%s: %w", name, socketErr)
	}
	return nil
}
