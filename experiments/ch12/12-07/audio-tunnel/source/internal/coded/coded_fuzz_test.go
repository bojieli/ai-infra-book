package coded

import (
	"encoding/binary"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/fec"
	"github.com/bojieli/queqiao/internal/lossmodel"
)

// receiveOnly builds the half of a Path that arriving datagrams touch, without
// the two goroutines New starts. onDatagram reads only these three fields, so
// a fuzz iteration costs a decoder and an estimator rather than a scheduler.
func receiveOnly() *Path {
	return &Path{
		decoder:   fec.NewWindowDecoder(),
		estimator: lossmodel.New(lossmodel.Config{ReorderTolerance: 32}),
	}
}

// A datagram is the only thing on this path that arrives without having been
// asked for, and onDatagram is where its bytes first become lengths, indices
// and counts: a symbol's payload length, a fragment's index, how many
// fragments its frame has, a repair's span, and the size of each frame packed
// inside a symbol. Every one of those is chosen by the peer, and the receive
// loop that calls this has no recover above it -- a panic here takes the
// process, not the connection.
//
// This found one: a frame size of 0xffffffff converted to int, which is
// negative on a 32-bit build, passes a `size > len(payload)` bound and panics
// the slice.
func FuzzOnDatagramNeverPanics(f *testing.F) {
	source := func(seq, esi uint32, vector []byte) []byte {
		d := make([]byte, sourceHeader+len(vector))
		binary.BigEndian.PutUint32(d, seq)
		d[4] = kindSource
		binary.BigEndian.PutUint32(d[5:], esi)
		copy(d[sourceHeader:], vector)
		return d
	}
	symbol := func(payload []byte, index, count int) []byte {
		v := make([]byte, symbolHeader+len(payload))
		binary.BigEndian.PutUint16(v, uint16(len(payload)))
		binary.BigEndian.PutUint16(v[2:], uint16(index))
		binary.BigEndian.PutUint16(v[4:], uint16(count))
		copy(v[symbolHeader:], payload)
		return v
	}
	frame := func(body []byte) []byte {
		out := make([]byte, frameHeader+len(body))
		binary.BigEndian.PutUint32(out, uint32(len(body)))
		copy(out[frameHeader:], body)
		return out
	}

	f.Add(source(1, 0, symbol(frame([]byte("hello")), 0, 1)))
	// A frame claiming more than the symbol holds, and the same claim at the
	// width where a 32-bit int turns it negative.
	f.Add(source(2, 1, symbol([]byte{0xff, 0xff, 0xff, 0xff, 1, 2}, 0, 1)))
	f.Add(source(3, 2, symbol([]byte{0x7f, 0xff, 0xff, 0xff, 1, 2}, 0, 1)))
	// A fragment claiming to be one of many, and one claiming an index past
	// the count it declares.
	f.Add(source(4, 3, symbol([]byte("part"), 0, 8)))
	f.Add(source(5, 4, symbol([]byte("part"), 9, 2)))
	// A repair spanning more symbols than any window holds.
	repair := make([]byte, repairHeader+64)
	binary.BigEndian.PutUint32(repair, 6)
	repair[4] = kindRepair
	binary.BigEndian.PutUint32(repair[5:], 1)
	binary.BigEndian.PutUint32(repair[9:], 0)
	binary.BigEndian.PutUint16(repair[13:], 0xffff)
	f.Add(repair)
	f.Add([]byte{})
	f.Add([]byte{0, 0, 0, 0, 9})

	f.Fuzz(func(t *testing.T, data []byte) {
		receiveOnly().onDatagram(data)
	})
}

// The same entry point, fed a sequence rather than one datagram, because the
// decoder and the assembler carry state between arrivals: a window that grew,
// a fragment group waiting for parts that never come, a sequence that jumped.
// A datagram that is harmless alone can still be the second half of something.
func FuzzOnDatagramSequenceNeverPanics(f *testing.F) {
	f.Add([]byte{9, 0, 0, 0, 0, kindSource, 0, 0, 0, 0}, []byte{})
	f.Fuzz(func(t *testing.T, script []byte, tail []byte) {
		p := receiveOnly()
		// The first byte of each record is its length, so one corpus entry
		// is a sequence of datagrams rather than one.
		for len(script) > 0 {
			n := int(script[0])
			script = script[1:]
			if n > len(script) {
				n = len(script)
			}
			p.onDatagram(script[:n])
			script = script[n:]
		}
		p.onDatagram(tail)
	})
}

// The datagram carrying the identifier above is the reachable form of the
// window walk that fec's decoder used to do: onDatagram takes the ESI from
// four bytes off the wire and hands it straight to the decoder, under the
// path's own lock, on the receive loop. So the bound belongs to a peer's
// input, not to an internal caller, and this asserts it there.
func TestADatagramNamingASymbolFarAheadReturns(t *testing.T) {
	p := receiveOnly()
	near := make([]byte, sourceHeader+symbolHeader)
	near[4] = kindSource
	binary.BigEndian.PutUint32(near[5:], 0)
	p.onDatagram(near)

	far := make([]byte, sourceHeader+symbolHeader)
	binary.BigEndian.PutUint32(far, 1)
	far[4] = kindSource
	binary.BigEndian.PutUint32(far[5:], 1<<30)

	done := make(chan struct{})
	go func() { p.onDatagram(far); close(done) }()
	select {
	case <-done:
	case <-time.After(10 * time.Second):
		t.Fatal("a datagram naming a symbol 2^30 ahead did not return")
	}
}
