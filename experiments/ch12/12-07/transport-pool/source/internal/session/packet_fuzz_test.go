package session

import (
	"bytes"
	"testing"
)

// A UDP packet frame is the peer's, and the destination inside it is what the
// far end will dial. Decoding has to reject anything it would not have
// produced rather than pass a half-parsed address to a resolver.
func FuzzDecodeUDPPacketNeverPanics(f *testing.F) {
	encoded, err := EncodeUDPPacket("127.0.0.1:80", []byte("payload"))
	if err != nil {
		f.Fatal(err)
	}
	f.Add(encoded)
	f.Add([]byte{0xff, 0xff, 'a'})
	f.Add([]byte{0, 0, 'a'})
	f.Add([]byte{0, 3, 'a'})
	f.Add([]byte{0, 1, ':'})
	f.Add([]byte{})
	f.Fuzz(func(t *testing.T, payload []byte) {
		destination, packet, err := DecodeUDPPacket(payload)
		if err != nil {
			return
		}
		// Whatever parsed has to survive its own round trip. Not byte-for-byte
		// against what arrived -- the decoder canonicalizes, so a packet
		// naming "host:0000443" re-encodes shorter than it came -- but as a
		// fixed point: re-encoding what was decoded and decoding that again
		// must give the same destination and the same bytes.
		again, err := EncodeUDPPacket(destination, packet)
		if err != nil {
			t.Fatalf("decoded %q from %q and could not re-encode it: %v", destination, payload, err)
		}
		destinationAgain, packetAgain, err := DecodeUDPPacket(again)
		if err != nil {
			t.Fatalf("re-encoded %q into something undecodable: %v", destination, err)
		}
		if destinationAgain != destination || !bytes.Equal(packetAgain, packet) {
			t.Fatalf("round trip moved %q/%q to %q/%q", destination, packet, destinationAgain, packetAgain)
		}
	})
}

// The destination on its own, because OPEN carries it without the packet
// framing around it.
func FuzzDecodeDestinationNeverPanics(f *testing.F) {
	f.Add([]byte("127.0.0.1:443"))
	f.Add([]byte("[::1]:443"))
	f.Add([]byte("example.com:0"))
	f.Add([]byte("example.com:99999"))
	f.Add([]byte(":443"))
	f.Add([]byte("host:"))
	f.Add([]byte{})
	f.Fuzz(func(t *testing.T, payload []byte) {
		destination, err := DecodeDestination(payload)
		if err != nil {
			return
		}
		// The decoder canonicalizes, so what comes back is a fixed point of
		// itself even when it is not what was sent.
		again, err := DecodeDestination([]byte(destination))
		if err != nil {
			t.Fatalf("decoded %q to %q, which does not decode: %v", payload, destination, err)
		}
		if again != destination {
			t.Fatalf("decoding %q gave %q and decoding that gave %q", payload, destination, again)
		}
	})
}
