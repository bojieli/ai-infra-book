// Package session contains flow identifiers and bounded flow metadata. Peer
// authentication is deliberately not part of this package: protocol v1 binds
// every flow to the device principal established by mutual TLS.
package session

import (
	"crypto/rand"
	"fmt"
)

func NewSessionID() ([16]byte, error) {
	var id [16]byte
	if _, err := rand.Read(id[:]); err != nil {
		return id, fmt.Errorf("generate session id: %w", err)
	}
	return id, nil
}

func IsZeroSessionID(id [16]byte) bool {
	var zero [16]byte
	return id == zero
}

// ResetCode values are intentionally coarse. They guide client behavior
// without exposing provider authorization details.
type ResetCode byte

const (
	ResetProtocol ResetCode = iota + 1
	ResetAuthentication
	ResetDestination
	ResetFlowLimit
	ResetTransport
)

func ResetPayload(code ResetCode, message string) []byte {
	if len(message) > 256 {
		message = message[:256]
	}
	b := make([]byte, 1+len(message))
	b[0] = byte(code)
	copy(b[1:], message)
	return b
}
