package pep

import (
	"errors"
	"fmt"
	"strings"
)

const tcpCongestionSystem = "system"

func normalizeTCPCongestion(name string) (string, error) {
	name = strings.ToLower(strings.TrimSpace(name))
	if name == "" {
		return tcpCongestionSystem, nil
	}
	if name == tcpCongestionSystem {
		return name, nil
	}
	// Linux TCP_CA_NAME_MAX is 16 including the terminating NUL. Rejecting
	// punctuation also prevents a mistyped flag from becoming a surprising
	// kernel module name.
	if len(name) > 15 {
		return "", errors.New("TCP congestion controller name must not exceed 15 characters")
	}
	for _, r := range name {
		if (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') || r == '_' || r == '-' {
			continue
		}
		return "", fmt.Errorf("invalid TCP congestion controller name %q", name)
	}
	return name, nil
}
