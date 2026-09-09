// Package multipath contains transport-independent pieces of the striped
// flow session. The transport package is intentionally unaware of ordering:
// QUIC lanes may deliver frames in different orders, while the application
// stream must remain strictly ordered.
package multipath

import (
	"errors"
	"fmt"
	"sort"

	"github.com/bojieli/queqiao/internal/memlimit"
)

var (
	ErrWindowExceeded = errors.New("reassembly window exceeded")
	ErrMemoryBudget   = errors.New("shared reassembly memory exhausted")
	ErrSequence       = errors.New("invalid reassembly sequence")
)

type Config struct {
	MaxBufferedBytes  uint64
	MaxBufferedFrames int
	// Memory is shared across flows. Out-of-order payloads must acquire it
	// before being retained. It is non-blocking because pausing a lane can also
	// pause the missing segment needed to close the gap; overload fails one flow
	// instead of deadlocking every flow behind a full receiver.
	Memory *memlimit.Budget
}

func DefaultConfig() Config {
	return Config{MaxBufferedBytes: 8 * 1024 * 1024, MaxBufferedFrames: 4096}
}

type Segment struct {
	Sequence uint64
	Payload  []byte
	Final    bool
	charged  bool
}

type Reassembler struct {
	cfg    Config
	next   uint64
	buffer map[uint64]Segment
	// order holds the buffered start sequences, sorted. Buffered segments are
	// disjoint by construction, so an overlap check only has to look at the
	// two neighbours of an insertion point.
	//
	// Scanning the whole buffer instead makes Insert cost O(n) and a transfer
	// O(n squared) in the number of buffered segments. That is invisible on
	// one lane, where almost nothing is buffered, and throttles the receiver
	// exactly when striping makes the reorder span large.
	order   []uint64
	bytes   uint64
	finalAt *uint64
	memory  *memlimit.Budget
}

func NewReassembler(cfg Config) *Reassembler {
	if cfg.MaxBufferedBytes == 0 || cfg.MaxBufferedFrames <= 0 {
		cfg = DefaultConfig()
	}
	return &Reassembler{cfg: cfg, buffer: make(map[uint64]Segment), memory: cfg.Memory}
}

func (r *Reassembler) NextSequence() uint64  { return r.next }
func (r *Reassembler) BufferedBytes() uint64 { return r.bytes }
func (r *Reassembler) BufferedFrames() int   { return len(r.buffer) }
func (r *Reassembler) Closed() bool          { return r.finalAt != nil && r.next >= *r.finalAt }

// Insert adds one non-empty data segment or a zero-length FIN. It returns all
// newly contiguous bytes. The caller owns the returned byte slice. Overlapping
// segments are rejected rather than silently merging untrusted input.
func (r *Reassembler) Insert(segment Segment) ([]byte, bool, error) {
	if segment.Final && len(segment.Payload) != 0 {
		return nil, false, errors.New("FIN segment must not carry payload")
	}
	if !segment.Final && len(segment.Payload) == 0 {
		return nil, false, errors.New("empty data segment")
	}
	if segment.Sequence > ^uint64(0)-uint64(len(segment.Payload)) {
		return nil, false, ErrSequence
	}
	end := segment.Sequence + uint64(len(segment.Payload))
	if segment.Final {
		end = segment.Sequence
	}
	if end < r.next || (segment.Final && segment.Sequence < r.next) {
		// A duplicate segment is harmless if it is wholly before the receive
		// cursor. FIN duplicates are also harmless.
		if end <= r.next {
			return nil, r.Closed(), nil
		}
		return nil, false, errors.New("segment overlaps receive cursor")
	}
	if existing, ok := r.buffer[segment.Sequence]; ok {
		if existing.Final == segment.Final && string(existing.Payload) == string(segment.Payload) {
			return nil, r.Closed(), nil
		}
		return nil, false, errors.New("conflicting duplicate segment")
	}
	if err := r.checkNeighbours(segment, end); err != nil {
		return nil, false, err
	}
	if segment.Sequence != r.next {
		if uint64(len(r.buffer))+1 > uint64(r.cfg.MaxBufferedFrames) || r.bytes+uint64(len(segment.Payload)) > r.cfg.MaxBufferedBytes {
			return nil, false, ErrWindowExceeded
		}
		if !r.memory.TryAcquire(len(segment.Payload)) {
			return nil, false, ErrMemoryBudget
		}
		segment.Payload = append([]byte(nil), segment.Payload...)
		segment.charged = true
		r.buffer[segment.Sequence] = segment
		r.insertOrder(segment.Sequence)
		r.bytes += uint64(len(segment.Payload))
		if segment.Final {
			at := segment.Sequence
			r.finalAt = &at
		}
		return nil, r.Closed(), nil
	}
	return r.consumeContiguous(segment)
}

func (r *Reassembler) consumeContiguous(first Segment) ([]byte, bool, error) {
	var output []byte
	current := first
	for {
		if current.Sequence != r.next {
			return nil, false, fmt.Errorf("internal reassembly cursor mismatch")
		}
		if current.Final {
			at := current.Sequence
			r.finalAt = &at
			return output, true, nil
		}
		output = append(output, current.Payload...)
		if current.charged {
			r.memory.Release(len(current.Payload))
			current.charged = false
		}
		r.next += uint64(len(current.Payload))
		if next, ok := r.buffer[r.next]; ok {
			delete(r.buffer, r.next)
			r.removeOrder(r.next)
			r.bytes -= uint64(len(next.Payload))
			current = next
			continue
		}
		if r.finalAt != nil && r.next >= *r.finalAt {
			return output, true, nil
		}
		return output, false, nil
	}
}

// Close releases shared-memory charges for gaps abandoned with the flow. It
// is idempotent and must be called when a flow ends before becoming contiguous.
func (r *Reassembler) Close() {
	for sequence, segment := range r.buffer {
		if segment.charged {
			r.memory.Release(len(segment.Payload))
		}
		delete(r.buffer, sequence)
	}
	r.order = nil
	r.bytes = 0
}

// BufferedSequences is intended for diagnostics and deterministic tests.
func (r *Reassembler) BufferedSequences() []uint64 {
	return append([]uint64(nil), r.order...)
}

// checkNeighbours rejects a segment that overlaps one already buffered.
// Buffered segments are disjoint, so only the neighbours of the insertion
// point can overlap.
func (r *Reassembler) checkNeighbours(segment Segment, end uint64) error {
	at := sort.Search(len(r.order), func(i int) bool { return r.order[i] >= segment.Sequence })
	if at > 0 {
		previous := r.buffer[r.order[at-1]]
		previousEnd := previous.Sequence + uint64(len(previous.Payload))
		if previous.Final {
			previousEnd = previous.Sequence
		}
		if segment.Sequence < previousEnd {
			return errors.New("overlapping reassembly segments")
		}
	}
	if at < len(r.order) {
		next := r.buffer[r.order[at]]
		if next.Sequence < end {
			return errors.New("overlapping reassembly segments")
		}
		if segment.Final && next.Sequence == segment.Sequence {
			return errors.New("FIN conflicts with buffered segment")
		}
	}
	return nil
}

func (r *Reassembler) insertOrder(sequence uint64) {
	at := sort.Search(len(r.order), func(i int) bool { return r.order[i] >= sequence })
	r.order = append(r.order, 0)
	copy(r.order[at+1:], r.order[at:])
	r.order[at] = sequence
}

func (r *Reassembler) removeOrder(sequence uint64) {
	at := sort.Search(len(r.order), func(i int) bool { return r.order[i] >= sequence })
	if at < len(r.order) && r.order[at] == sequence {
		r.order = append(r.order[:at], r.order[at+1:]...)
	}
}

// ReceivedRanges reports the byte ranges held out of order, merged and sorted,
// capped at max entries.
//
// A striped flow's sender otherwise learns only the contiguous receive point,
// which sits behind whatever the slowest lane has not delivered. Its retention
// window then has to cover the whole reorder span rather than the bytes
// actually outstanding. Reporting what the receiver already holds lets the
// sender release those frames, which is what keeps the window proportional to
// the data in flight.
//
// Ranges are returned lowest first so a truncated report still describes the
// bytes closest to the contiguous point, which are the ones the sender is most
// likely to still be holding.
func (r *Reassembler) ReceivedRanges(max int) [][2]uint64 {
	if max <= 0 || len(r.buffer) == 0 {
		return nil
	}
	ranges := make([][2]uint64, 0, len(r.order))
	for _, start := range r.order {
		segment := r.buffer[start]
		end := start + uint64(len(segment.Payload))
		if segment.Final {
			// A buffered FIN covers no bytes; reporting it would tell the
			// sender a zero-length range it cannot act on.
			continue
		}
		if last := len(ranges) - 1; last >= 0 && ranges[last][1] == start {
			ranges[last][1] = end
			continue
		}
		ranges = append(ranges, [2]uint64{start, end})
	}
	if len(ranges) > max {
		ranges = ranges[:max]
	}
	return ranges
}
