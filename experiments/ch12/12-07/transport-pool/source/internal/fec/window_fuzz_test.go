package fec

import (
	"encoding/binary"
	"testing"
)

// The decoder is driven entirely by fields a peer chooses. A repair declares
// which symbol it starts at and how many it spans, and that span is what sizes
// the linear system it is solved in -- so the memory one connection can be
// made to hold is a number off the wire, and the rows it eliminates against
// are indexed by another.
//
// maxDecoderWidth is what bounds the first of those. This asserts it holds
// against inputs no encoder would produce: spans of 65535, repairs starting
// past where the window has reached, repairs that overlap nothing.
func FuzzWindowDecoderNeverPanics(f *testing.F) {
	// One source symbol, then a repair spanning it.
	f.Add([]byte{
		0, 0, 0, 0, 1, 2, 3, 4,
	}, uint32(0), uint32(0), uint16(1))
	// A repair claiming the widest span expressible.
	f.Add([]byte{0, 0, 0, 5, 9}, uint32(7), uint32(0), uint16(0xffff))
	// A repair starting far past anything seen.
	f.Add([]byte{0, 0, 0, 0, 1}, uint32(1), uint32(0xfffffff0), uint16(8))
	f.Add([]byte{}, uint32(0), uint32(0), uint16(0))

	f.Fuzz(func(t *testing.T, sources []byte, rid, first uint32, count uint16) {
		d := NewWindowDecoder()
		// Each record in sources is a 4-byte ESI and a length-prefixed
		// vector, so one corpus entry drives a sequence of arrivals into one
		// decoder rather than a single call into a fresh one.
		for len(sources) >= 5 {
			esi := binary.BigEndian.Uint32(sources)
			n := int(sources[4])
			sources = sources[5:]
			if n > len(sources) {
				n = len(sources)
			}
			for _, r := range d.Source(esi, sources[:n]).Recovered {
				if r.Vector == nil {
					t.Fatal("recovered a symbol with no vector")
				}
			}
			sources = sources[n:]
		}
		delivery := d.Repair(RepairSymbol{RID: rid, First: first, Count: int(count), Vector: sources})
		for _, r := range delivery.Recovered {
			if r.Vector == nil {
				t.Fatal("recovered a symbol with no vector")
			}
		}
		// Whatever the peer claimed, the window it made the decoder hold is
		// the one the package bounds itself to.
		if width := len(d.slots); width > maxDecoderWidth {
			t.Fatalf("a repair claiming %d symbols grew the window to %d, past the %d bound",
				count, width, maxDecoderWidth)
		}
	})
}
