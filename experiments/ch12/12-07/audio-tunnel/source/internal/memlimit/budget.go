// Package memlimit provides hard byte admission for memory retained by many
// concurrent flows. It accounts ownership rather than sampling the Go heap:
// a caller must acquire bytes before allocating or retaining them and release
// exactly those bytes when the data is no longer reachable from the data path.
package memlimit

import (
	"context"
	"errors"
	"sync"
)

var ErrRequestTooLarge = errors.New("memory request exceeds budget capacity")

// Snapshot is a race-free view of a Budget.
type Snapshot struct {
	Capacity int64 `json:"capacity_bytes"`
	Used     int64 `json:"used_bytes"`
	Peak     int64 `json:"peak_bytes"`
	Waiters  int64 `json:"waiters"`
}

// Budget is a fixed-capacity, concurrency-safe byte semaphore. All flows of a
// client share one Budget, so opening more flows changes scheduling and
// backpressure, never the maximum retained payload memory.
//
// Waiters use a broadcast-style generation channel. A release closes the old
// generation and creates a new one, waking every waiter without a goroutine per
// request. Acquisition is deliberately not strictly FIFO: data-path requests
// are uniformly bounded chunks, and allowing a small request through prevents
// an oversized request at the head from blocking control progress.
type Budget struct {
	mu       sync.Mutex
	capacity int64
	used     int64
	peak     int64
	waiters  int64
	changed  chan struct{}
}

func New(capacity int64) *Budget {
	if capacity <= 0 {
		return nil
	}
	return &Budget{capacity: capacity, changed: make(chan struct{})}
}

// Acquire blocks until n bytes are available or ctx ends. A nil Budget is an
// intentionally unbounded configuration and succeeds immediately.
func (b *Budget) Acquire(ctx context.Context, n int) error {
	if b == nil || n <= 0 {
		return nil
	}
	request := int64(n)
	b.mu.Lock()
	if request > b.capacity {
		b.mu.Unlock()
		return ErrRequestTooLarge
	}
	for {
		// Cancellation wins even when capacity is currently available. Callers
		// use cancellation to tear down a flow; admitting a final allocation
		// after that point needlessly extends the lifetime of its payload.
		if err := ctx.Err(); err != nil {
			b.mu.Unlock()
			return err
		}
		if request <= b.capacity-b.used {
			b.used += request
			if b.used > b.peak {
				b.peak = b.used
			}
			b.mu.Unlock()
			return nil
		}
		generation := b.changed
		b.waiters++
		b.mu.Unlock()
		select {
		case <-generation:
		case <-ctx.Done():
			b.mu.Lock()
			b.waiters--
			b.mu.Unlock()
			return ctx.Err()
		}
		b.mu.Lock()
		b.waiters--
	}
}

// TryAcquire reserves n bytes without waiting.
func (b *Budget) TryAcquire(n int) bool {
	if b == nil || n <= 0 {
		return true
	}
	request := int64(n)
	b.mu.Lock()
	defer b.mu.Unlock()
	if request > b.capacity-b.used {
		return false
	}
	b.used += request
	if b.used > b.peak {
		b.peak = b.used
	}
	return true
}

// Release returns n bytes. Releasing bytes that were not acquired is a
// programming error: silently saturating at zero would hide double releases
// and destroy the hard-limit invariant.
func (b *Budget) Release(n int) {
	if b == nil || n <= 0 {
		return
	}
	released := int64(n)
	b.mu.Lock()
	if released > b.used {
		b.mu.Unlock()
		panic("memlimit: release exceeds acquired bytes")
	}
	b.used -= released
	old := b.changed
	b.changed = make(chan struct{})
	close(old)
	b.mu.Unlock()
}

func (b *Budget) Snapshot() Snapshot {
	if b == nil {
		return Snapshot{}
	}
	b.mu.Lock()
	defer b.mu.Unlock()
	return Snapshot{Capacity: b.capacity, Used: b.used, Peak: b.peak, Waiters: b.waiters}
}
