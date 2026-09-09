package multipath

import (
	"bytes"
	"errors"
	"testing"

	"github.com/bojieli/queqiao/internal/memlimit"
)

func TestReassemblerSharesHardMemoryBudget(t *testing.T) {
	budget := memlimit.New(4)
	first := NewReassembler(Config{MaxBufferedBytes: 64, MaxBufferedFrames: 8, Memory: budget})
	second := NewReassembler(Config{MaxBufferedBytes: 64, MaxBufferedFrames: 8, Memory: budget})
	if _, _, err := first.Insert(Segment{Sequence: 4, Payload: []byte("four")}); err != nil {
		t.Fatal(err)
	}
	if _, _, err := second.Insert(Segment{Sequence: 4, Payload: []byte("more")}); !errors.Is(err, ErrMemoryBudget) {
		t.Fatalf("second insert error = %v", err)
	}
	first.Close()
	if got := budget.Snapshot().Used; got != 0 {
		t.Fatalf("used after close = %d", got)
	}
	if _, _, err := second.Insert(Segment{Sequence: 4, Payload: []byte("more")}); err != nil {
		t.Fatal(err)
	}
	second.Close()
}

func TestReassemblerReordersAndDrains(t *testing.T) {
	r := NewReassembler(Config{MaxBufferedBytes: 64, MaxBufferedFrames: 8})
	if out, closed, err := r.Insert(Segment{Sequence: 5, Payload: []byte(" world")}); err != nil || out != nil || closed {
		t.Fatalf("out-of-order insert: out=%q closed=%v err=%v", out, closed, err)
	}
	out, closed, err := r.Insert(Segment{Sequence: 0, Payload: []byte("hello")})
	if err != nil || closed || !bytes.Equal(out, []byte("hello world")) {
		t.Fatalf("drain: out=%q closed=%v err=%v", out, closed, err)
	}
	if _, closed, err := r.Insert(Segment{Sequence: 11, Final: true}); err != nil || !closed {
		t.Fatalf("fin: closed=%v err=%v", closed, err)
	}
	if !r.Closed() || r.NextSequence() != 11 {
		t.Fatalf("state: closed=%v next=%d", r.Closed(), r.NextSequence())
	}
}

func TestReassemblerFinMayArriveBeforeMissingData(t *testing.T) {
	r := NewReassembler(Config{MaxBufferedBytes: 64, MaxBufferedFrames: 8})
	if _, closed, err := r.Insert(Segment{Sequence: 5, Payload: []byte(" world")}); err != nil || closed {
		t.Fatalf("data insert: closed=%v err=%v", closed, err)
	}
	if _, closed, err := r.Insert(Segment{Sequence: 11, Final: true}); err != nil || closed {
		t.Fatalf("buffered FIN insert: closed=%v err=%v", closed, err)
	}
	out, closed, err := r.Insert(Segment{Sequence: 0, Payload: []byte("hello")})
	if err != nil || !closed || !bytes.Equal(out, []byte("hello world")) {
		t.Fatalf("FIN drain: out=%q closed=%v err=%v", out, closed, err)
	}
	if !r.Closed() || r.NextSequence() != 11 {
		t.Fatalf("state: closed=%v next=%d", r.Closed(), r.NextSequence())
	}
}

func TestReassemblerBoundsOutOfOrderData(t *testing.T) {
	r := NewReassembler(Config{MaxBufferedBytes: 4, MaxBufferedFrames: 1})
	if _, _, err := r.Insert(Segment{Sequence: 10, Payload: []byte("12345")}); !errors.Is(err, ErrWindowExceeded) {
		t.Fatalf("expected byte window error, got %v", err)
	}
	if _, _, err := r.Insert(Segment{Sequence: 2, Payload: []byte("12")}); err != nil {
		t.Fatal(err)
	}
	if _, _, err := r.Insert(Segment{Sequence: 4, Payload: []byte("34")}); !errors.Is(err, ErrWindowExceeded) {
		t.Fatalf("expected frame window error, got %v", err)
	}
}

func TestReassemblerRejectsOverlap(t *testing.T) {
	r := NewReassembler(DefaultConfig())
	if _, _, err := r.Insert(Segment{Sequence: 4, Payload: []byte("abcd")}); err != nil {
		t.Fatal(err)
	}
	if _, _, err := r.Insert(Segment{Sequence: 6, Payload: []byte("xy")}); err == nil {
		t.Fatal("expected overlap rejection")
	}
}

func TestReceivedRangesMergesAndOrders(t *testing.T) {
	r := NewReassembler(DefaultConfig())
	// Deliberately out of order, with two adjacent segments that must merge.
	for _, segment := range []Segment{
		{Sequence: 300, Payload: []byte("ccc")},
		{Sequence: 100, Payload: []byte("aa")},
		{Sequence: 102, Payload: []byte("bb")},
	} {
		if _, _, err := r.Insert(segment); err != nil {
			t.Fatalf("insert at %d: %v", segment.Sequence, err)
		}
	}
	got := r.ReceivedRanges(8)
	want := [][2]uint64{{100, 104}, {300, 303}}
	if len(got) != len(want) {
		t.Fatalf("ranges = %v, want %v", got, want)
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("ranges = %v, want %v", got, want)
		}
	}
}

// A truncated report must describe the bytes closest to the contiguous point,
// which are the ones the sender is most likely to still be holding.
func TestReceivedRangesTruncatesFromTheLowest(t *testing.T) {
	r := NewReassembler(DefaultConfig())
	for i := range uint64(5) {
		if _, _, err := r.Insert(Segment{Sequence: 100 + i*10, Payload: []byte("xx")}); err != nil {
			t.Fatal(err)
		}
	}
	got := r.ReceivedRanges(2)
	if len(got) != 2 || got[0][0] != 100 || got[1][0] != 110 {
		t.Fatalf("ranges = %v, want the two lowest", got)
	}
}

func TestReceivedRangesIgnoresContiguousAndEmpty(t *testing.T) {
	r := NewReassembler(DefaultConfig())
	if got := r.ReceivedRanges(4); got != nil {
		t.Fatalf("ranges = %v on an empty reassembler, want none", got)
	}
	// A segment delivered contiguously is not buffered, so it is not a range.
	if _, _, err := r.Insert(Segment{Sequence: 0, Payload: []byte("abc")}); err != nil {
		t.Fatal(err)
	}
	if got := r.ReceivedRanges(4); got != nil {
		t.Fatalf("ranges = %v after contiguous delivery, want none", got)
	}
	if got := r.ReceivedRanges(0); got != nil {
		t.Fatalf("ranges = %v with a zero cap, want none", got)
	}
}

// Scanning the whole buffer on every insert makes a transfer quadratic in the
// number of buffered segments. That is invisible on one lane, where almost
// nothing is buffered, and throttles the receiver exactly when striping makes
// the reorder span large.
func BenchmarkInsertIntoLargeReorderBuffer(b *testing.B) {
	const buffered = 4000
	for range b.N {
		r := NewReassembler(Config{MaxBufferedBytes: 64 << 20, MaxBufferedFrames: buffered + 16})
		// Leave a hole at zero so nothing is ever delivered contiguously and
		// the buffer keeps growing.
		for i := uint64(1); i <= buffered; i++ {
			if _, _, err := r.Insert(Segment{Sequence: i * 100, Payload: make([]byte, 100)}); err != nil {
				b.Fatalf("insert %d: %v", i, err)
			}
		}
	}
}

// The neighbour check must still reject every overlap the full scan did.
func TestOverlapDetectionAfterIndexing(t *testing.T) {
	r := NewReassembler(DefaultConfig())
	for _, sequence := range []uint64{100, 300, 500} {
		if _, _, err := r.Insert(Segment{Sequence: sequence, Payload: make([]byte, 50)}); err != nil {
			t.Fatal(err)
		}
	}
	for name, segment := range map[string]Segment{
		"starts inside an existing segment": {Sequence: 120, Payload: make([]byte, 10)},
		"ends inside an existing segment":   {Sequence: 280, Payload: make([]byte, 40)},
		"spans an existing segment":         {Sequence: 90, Payload: make([]byte, 100)},
		"duplicate start with new length":   {Sequence: 300, Payload: make([]byte, 10)},
	} {
		if _, _, err := r.Insert(segment); err == nil {
			t.Fatalf("%s was accepted", name)
		}
	}
	// A segment in a genuine gap is still accepted.
	if _, _, err := r.Insert(Segment{Sequence: 200, Payload: make([]byte, 50)}); err != nil {
		t.Fatalf("a non-overlapping segment was rejected: %v", err)
	}
	got := r.BufferedSequences()
	want := []uint64{100, 200, 300, 500}
	if len(got) != len(want) {
		t.Fatalf("buffered %v, want %v", got, want)
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("buffered %v, want %v", got, want)
		}
	}
}

// The index has to shrink as segments are consumed, or it would report
// sequences that are no longer buffered and grow without bound.
func TestOrderIndexShrinksOnDelivery(t *testing.T) {
	r := NewReassembler(DefaultConfig())
	if _, _, err := r.Insert(Segment{Sequence: 100, Payload: []byte("bbbb")}); err != nil {
		t.Fatal(err)
	}
	if _, _, err := r.Insert(Segment{Sequence: 200, Payload: []byte("cccc")}); err != nil {
		t.Fatal(err)
	}
	// Filling the hole delivers the first two segments contiguously.
	out, _, err := r.Insert(Segment{Sequence: 0, Payload: make([]byte, 100)})
	if err != nil {
		t.Fatal(err)
	}
	if len(out) != 104 {
		t.Fatalf("delivered %d bytes, want the gap plus the first buffered segment", len(out))
	}
	if got := r.BufferedSequences(); len(got) != 1 || got[0] != 200 {
		t.Fatalf("buffered %v, want only the still-unreachable segment", got)
	}
}
