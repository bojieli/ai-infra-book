package session

import (
	"errors"
	"fmt"
	"net"
	"strconv"
	"strings"
)

const maxDestinationLength = 255

// EncodeDestination stores a single TCP destination in a bounded, canonical
// host:port representation. DNS resolution deliberately happens on the US
// agent so that the destination's egress remains there.
func EncodeDestination(destination string) ([]byte, error) {
	destination = strings.TrimSpace(destination)
	if len(destination) == 0 || len(destination) > maxDestinationLength {
		return nil, errors.New("destination is empty or too long")
	}
	host, port, err := net.SplitHostPort(destination)
	if err != nil || host == "" {
		return nil, errors.New("destination must be host:port")
	}
	// A host is never whitespace or control characters, and rejecting them
	// is what makes this function idempotent. Brackets are stripped by
	// SplitHostPort and re-added below only for a host containing a colon, so
	// "[ ]:1" canonicalized to " :1" -- which this function then refused,
	// because the TrimSpace above ate the host and left ":1". A canonical
	// form that the canonicalizer rejects is not one, and the same check
	// disposes of "a\nb:1" and "x :1", which are not destinations either.
	if strings.ContainsFunc(host, func(r rune) bool { return r <= ' ' || r == 0x7f }) {
		return nil, errors.New("destination host contains space or control characters")
	}
	p, err := strconv.Atoi(port)
	if err != nil || p < 1 || p > 65535 {
		return nil, errors.New("destination port is invalid")
	}
	// Re-encode to avoid ambiguous forms and to preserve IPv6 brackets.
	canonical := net.JoinHostPort(host, strconv.Itoa(p))
	return []byte(canonical), nil
}

// DecodeDestination returns the canonical form of what the peer sent, not
// what the peer sent. EncodeDestination re-encodes precisely to remove
// ambiguous spellings, and this used to compute that form, use it to decide
// the payload was valid, and then discard it -- so "host:0000443" was
// accepted and passed on as itself, and one destination had as many names as
// a peer cared to write. Nothing keys on the string today and the dial policy
// re-parses and checks the resolved address rather than matching text, so this
// was not a way past it; it is fixed because a decoder that validates by
// canonicalizing should return what it canonicalized.
func DecodeDestination(payload []byte) (string, error) {
	if len(payload) == 0 || len(payload) > maxDestinationLength {
		return "", errors.New("invalid destination payload length")
	}
	canonical, err := EncodeDestination(string(payload))
	if err != nil {
		return "", fmt.Errorf("invalid destination: %w", err)
	}
	return string(canonical), nil
}
