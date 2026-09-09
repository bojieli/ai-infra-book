package pep

import (
	"context"
	"errors"
	"sort"
	"sync"
)

// ackTracker records which byte ranges of an outbound stream the peer has
// acknowledged, and lets a sender block until a particular range is delivered.
//
// This is what makes self-pacing real rather than nominal. A lane worker that
// treats a completed Write as a completed chunk is measuring its own send
// buffer, which tells it nothing about the path: a QUIC stream with an 8 MiB
// flow-control window accepts megabytes before it pushes back, so every lane
// would look infinitely fast and the scheduler would be pushing again under a
// different name. Waiting until the peer says the bytes arrived clocks each
// lane at the rate the path actually sustains, which is the whole point.
type ackTracker struct {
	mu         sync.Mutex
	cond       *sync.Cond
	cumulative uint64
	// ranges holds acknowledged spans above the cumulative point, sorted by
	// start and merged. A striped receiver holds gaps by construction, so the
	// cumulative point alone would report a chunk delivered on a fast lane as
	// outstanding until a slow lane filled the hole behind it.
	ranges [][2]uint64
	closed bool
	// gen advances whenever the acknowledged set changes, so a watcher can
	// wait for news without polling.
	gen uint64
}

func newAckTracker() *ackTracker {
	t := &ackTracker{}
	t.cond = sync.NewCond(&t.mu)
	return t
}

// Advance records a cumulative acknowledgement: every byte below sequence has
// arrived.
func (t *ackTracker) Advance(sequence uint64) {
	t.mu.Lock()
	defer t.mu.Unlock()
	if sequence <= t.cumulative {
		return
	}
	t.cumulative = sequence
	t.compactLocked()
	t.gen++
	t.cond.Broadcast()
}

// Add records ranges the peer holds out of order.
func (t *ackTracker) Add(ranges [][2]uint64) {
	if len(ranges) == 0 {
		return
	}
	t.mu.Lock()
	defer t.mu.Unlock()
	for _, r := range ranges {
		if r[1] <= r[0] || r[1] <= t.cumulative {
			continue
		}
		t.ranges = append(t.ranges, r)
	}
	t.mergeLocked()
	t.compactLocked()
	t.gen++
	t.cond.Broadcast()
}

// mergeLocked sorts and coalesces overlapping ranges so Covered is a scan
// rather than a search, and so the set cannot grow without bound.
func (t *ackTracker) mergeLocked() {
	if len(t.ranges) < 2 {
		return
	}
	sort.Slice(t.ranges, func(i, j int) bool {
		if t.ranges[i][0] != t.ranges[j][0] {
			return t.ranges[i][0] < t.ranges[j][0]
		}
		return t.ranges[i][1] < t.ranges[j][1]
	})
	merged := t.ranges[:1]
	for _, r := range t.ranges[1:] {
		last := &merged[len(merged)-1]
		if r[0] <= last[1] {
			if r[1] > last[1] {
				last[1] = r[1]
			}
			continue
		}
		merged = append(merged, r)
	}
	t.ranges = merged
}

// compactLocked folds ranges that now sit below or adjacent to the cumulative
// point back into it.
func (t *ackTracker) compactLocked() {
	kept := t.ranges[:0]
	for _, r := range t.ranges {
		if r[1] <= t.cumulative {
			continue
		}
		if r[0] <= t.cumulative {
			t.cumulative = r[1]
			continue
		}
		kept = append(kept, r)
	}
	t.ranges = kept
	// Folding one range into the cumulative point can make the next one
	// adjacent, so repeat until it stops moving.
	for progress := true; progress; {
		progress = false
		kept = t.ranges[:0]
		for _, r := range t.ranges {
			if r[1] <= t.cumulative {
				progress = true
				continue
			}
			if r[0] <= t.cumulative {
				t.cumulative = r[1]
				progress = true
				continue
			}
			kept = append(kept, r)
		}
		t.ranges = kept
	}
}

// Covered reports whether every byte in [start, end) has been acknowledged.
func (t *ackTracker) Covered(start, end uint64) bool {
	t.mu.Lock()
	defer t.mu.Unlock()
	return t.coveredLocked(start, end)
}

func (t *ackTracker) coveredLocked(start, end uint64) bool {
	if end <= start {
		return true
	}
	if end <= t.cumulative {
		return true
	}
	if start < t.cumulative {
		start = t.cumulative
	}
	for _, r := range t.ranges {
		if r[0] > start {
			return false
		}
		if r[1] > start {
			start = r[1]
			if start >= end {
				return true
			}
		}
	}
	return false
}

// Wait blocks until [start, end) is acknowledged, the context ends, or the
// tracker is closed. It reports the context's error, or nil once covered.
func (t *ackTracker) Wait(ctx context.Context, start, end uint64) error {
	t.mu.Lock()
	defer t.mu.Unlock()

	stop := context.AfterFunc(ctx, func() {
		t.mu.Lock()
		defer t.mu.Unlock()
		t.cond.Broadcast()
	})
	defer stop()

	for {
		if t.coveredLocked(start, end) {
			return nil
		}
		if t.closed {
			return errAckTrackerClosed
		}
		if err := ctx.Err(); err != nil {
			return err
		}
		t.cond.Wait()
	}
}

// WaitChange blocks until the acknowledged set has changed since the given
// generation, and returns the new one. It lets a single watcher complete
// chunks as their bytes land, instead of one goroutine per chunk sitting in
// Wait.
func (t *ackTracker) WaitChange(ctx context.Context, since uint64) (uint64, error) {
	t.mu.Lock()
	defer t.mu.Unlock()

	stop := context.AfterFunc(ctx, func() {
		t.mu.Lock()
		defer t.mu.Unlock()
		t.cond.Broadcast()
	})
	defer stop()

	for {
		if t.gen != since {
			return t.gen, nil
		}
		if t.closed {
			return t.gen, errAckTrackerClosed
		}
		if err := ctx.Err(); err != nil {
			return t.gen, err
		}
		t.cond.Wait()
	}
}

// Close releases every waiter, for a flow that is tearing down.
func (t *ackTracker) Close() {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.closed = true
	t.cond.Broadcast()
}

// errAckTrackerClosed reports that a flow tore down while a lane worker was
// waiting for its chunk to be acknowledged.
var errAckTrackerClosed = errors.New("acknowledgement tracker closed")

// Touch advances the generation without changing what is acknowledged, so a
// watcher re-examines its list.
func (t *ackTracker) Touch() {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.gen++
	t.cond.Broadcast()
}

// ackSnapshot is a copy of the acknowledged set, taken once so a caller can
// test many ranges against it without holding the tracker's lock.
type ackSnapshot struct {
	cumulative uint64
	ranges     [][2]uint64
}

// Snapshot copies the acknowledged set.
func (t *ackTracker) Snapshot() ackSnapshot {
	t.mu.Lock()
	defer t.mu.Unlock()
	out := ackSnapshot{cumulative: t.cumulative}
	if len(t.ranges) > 0 {
		out.ranges = append(make([][2]uint64, 0, len(t.ranges)), t.ranges...)
	}
	return out
}

// highest is the greatest byte offset the peer has reported receiving.
//
// Data acknowledged beyond a chunk is evidence about that chunk: the peer
// could not have received bytes above it without the path having carried them,
// so a chunk still outstanding well below this point did not arrive. It is the
// same inference a fast retransmit makes, at the layer where an unrepairable
// coded symbol actually goes missing.
func (s ackSnapshot) highest() uint64 {
	top := s.cumulative
	for _, r := range s.ranges {
		if r[1] > top {
			top = r[1]
		}
	}
	return top
}

// covers reports whether every byte in [start, end) is acknowledged.
func (s ackSnapshot) covers(start, end uint64) bool {
	if end <= start || end <= s.cumulative {
		return true
	}
	if start < s.cumulative {
		start = s.cumulative
	}
	for _, r := range s.ranges {
		if r[0] > start {
			return false
		}
		if r[1] > start {
			start = r[1]
			if start >= end {
				return true
			}
		}
	}
	return false
}
