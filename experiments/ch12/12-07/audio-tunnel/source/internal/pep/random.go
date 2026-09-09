package pep

import (
	"crypto/rand"
	"encoding/binary"
	"fmt"
	"time"
)

func randomFlowID() (uint64, error) {
	var raw [8]byte
	if _, err := rand.Read(raw[:]); err != nil {
		return 0, fmt.Errorf("generate flow id: %w", err)
	}
	id := binary.BigEndian.Uint64(raw[:])
	if id == 0 {
		id = 1
	}
	return id, nil
}

// randomDuration returns a cryptographically random duration in [0, maximum].
// Retry jitter does not protect a secret, but using the same entropy source as
// flow identities avoids predictable reconnect waves and keeps security tools
// from mistaking production randomness for deterministic simulation input.
func randomDuration(maximum time.Duration) time.Duration {
	if maximum <= 0 {
		return 0
	}
	var raw [8]byte
	if _, err := rand.Read(raw[:]); err != nil {
		// Entropy failure must not turn a recoverable transport error into a
		// permanent one. The minimum equal-jitter delay remains in the caller.
		return 0
	}
	// Modulo maximum+1 proves the result fits in both int64 and time.Duration.
	return time.Duration(binary.BigEndian.Uint64(raw[:]) % (uint64(maximum) + 1)) // #nosec G115 -- bounded by positive maximum.
}
