package session

import (
	"bytes"
	"testing"
)

func TestUDPPacketRoundTripIncludingEmptyPayload(t *testing.T) {
	for _, payload := range [][]byte{nil, []byte("dns")} {
		encoded, err := EncodeUDPPacket("example.com:53", payload)
		if err != nil {
			t.Fatal(err)
		}
		destination, decoded, err := DecodeUDPPacket(encoded)
		if err != nil {
			t.Fatal(err)
		}
		if destination != "example.com:53" || !bytes.Equal(decoded, payload) {
			t.Fatalf("destination=%q payload=%q", destination, decoded)
		}
	}
}

func TestUDPPacketRejectsMalformedAndOversizedPayloads(t *testing.T) {
	if _, _, err := DecodeUDPPacket([]byte{0, 0}); err == nil {
		t.Fatal("truncated packet accepted")
	}
	if _, err := EncodeUDPPacket("example.com:53", bytes.Repeat([]byte{'x'}, maxUDPPayload+1)); err == nil {
		t.Fatal("oversized payload accepted")
	}
	if _, _, err := DecodeUDPPacket([]byte{0, 1, 'x'}); err == nil {
		t.Fatal("invalid destination accepted")
	}
}
