package socks5

import (
	"bytes"
	"io"
	"testing"
)

// The SOCKS5 port is the one this proxy opens to whatever is on the machine,
// so its parser answers bytes nobody authenticated. ReadUDPDatagram is the
// sharper of the two: it indexes a caller-supplied buffer by an address type
// and a length that the same buffer declares.
func FuzzReadUDPDatagramNeverPanics(f *testing.F) {
	// A well-formed IPv4 datagram, one per address type, and the truncations
	// around each length that the header claims.
	f.Add([]byte{0, 0, 0, 1, 127, 0, 0, 1, 0x1f, 0x90, 'h', 'i'})
	f.Add([]byte{0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0x1f, 0x90})
	f.Add([]byte{0, 0, 0, 3, 3, 'a', 'b', 'c', 0x1f, 0x90})
	f.Add([]byte{0, 0, 0, 3, 0xff, 'a'})
	f.Add([]byte{0, 0, 0, 3, 0})
	f.Add([]byte{0, 0, 1, 1, 127, 0, 0, 1, 0, 80})
	f.Add([]byte{0, 0, 0, 9})
	f.Add([]byte{})
	f.Fuzz(func(t *testing.T, packet []byte) {
		datagram, err := ReadUDPDatagram(packet)
		if err != nil {
			return
		}
		// A datagram that parsed has to be one this proxy can act on: an
		// empty destination would be forwarded to whatever a dialer makes of
		// it, and a payload aliasing the caller's buffer would be rewritten
		// underneath the association.
		if datagram.Destination == "" {
			t.Fatalf("accepted a datagram with no destination: %q", packet)
		}
		if len(datagram.Payload) > 0 && &datagram.Payload[0] == &packet[len(packet)-len(datagram.Payload)] {
			t.Fatal("payload aliases the packet it was parsed from")
		}
	})
}

// ReadRequest reads from a stream rather than a buffer, and writes to it: a
// rejected greeting or an unsupported command is answered before the error is
// returned. So the fuzz has to give it something that is both, and the reply
// going nowhere is the point rather than a shortcoming.
func FuzzReadRequestNeverPanics(f *testing.F) {
	f.Add([]byte{5, 1, 0, 5, 1, 0, 1, 127, 0, 0, 1, 0x1f, 0x90})
	f.Add([]byte{5, 1, 0, 5, 3, 0, 1, 127, 0, 0, 1, 0x1f, 0x90})
	f.Add([]byte{5, 1, 0, 5, 1, 0, 3, 3, 'a', 'b', 'c', 0x1f, 0x90})
	f.Add([]byte{5, 0xff, 0})
	f.Add([]byte{5, 0})
	f.Add([]byte{4, 1, 0})
	f.Add([]byte{})
	// The username/password path parses two more caller-declared lengths
	// before the request, so it gets its own seeds: a complete exchange, a
	// truncated password, and a sub-negotiation version nobody supports.
	f.Add([]byte{5, 1, 2, 1, 2, 'h', 'i', 2, 'p', 'w', 5, 1, 0, 1, 127, 0, 0, 1, 0x1f, 0x90})
	f.Add([]byte{5, 1, 2, 1, 2, 'h', 'i', 0xff, 'p'})
	f.Add([]byte{5, 1, 2, 9, 1, 'h'})
	f.Add([]byte{5, 1, 2, 1, 0})
	f.Fuzz(func(t *testing.T, in []byte) {
		// Both listener configurations read the same attacker-controlled
		// bytes, and only the authenticated one can reach the sub-negotiation
		// parser, so neither is redundant.
		for _, credentials := range []*Credentials{nil, {Username: "hi", Password: "pw"}} {
			stream := struct {
				io.Reader
				io.Writer
			}{bytes.NewReader(in), io.Discard}
			request, err := ReadRequest(stream, credentials)
			if err != nil {
				continue
			}
			if request.Command != CommandConnect && request.Command != CommandUDPAssociate {
				t.Fatalf("accepted command %d", request.Command)
			}
			if request.Destination == "" {
				t.Fatal("accepted a request with no destination")
			}
		}
	})
}
