//go:build !linux

package pep

import (
	"fmt"
	"net"
)

func setTCPListenerCongestion(_ net.Listener, name string) error {
	return unsupportedTCPCongestion(name)
}

func setTCPConnCongestion(_ net.Conn, name string) error {
	return unsupportedTCPCongestion(name)
}

func unsupportedTCPCongestion(name string) error {
	if name == tcpCongestionSystem {
		return nil
	}
	return fmt.Errorf("TCP congestion controller %q requires Linux", name)
}
