// Package limiter contains bounded pacing primitives shared by all lanes of
// an endpoint.  It is deliberately independent of QUIC: the same budget can
// protect TCP rescue lanes and QUIC lanes from competing per-connection
// controllers.
package limiter

import (
	"context"
	"errors"
	"math"
	"sync"
	"time"
)

var ErrInvalidRequest = errors.New("limiter request exceeds configured burst")

// Config describes one aggregate byte budget.  ReserveBytesPerSec is
// unavailable to bulk traffic, preserving a small service rate for new and
// interactive flows when bulk lanes are saturated.
type Config struct {
	TotalBytesPerSec   uint64
	ReserveBytesPerSec uint64
	Burst              time.Duration
}

type Budget struct {
	mu      sync.Mutex
	total   float64
	reserve float64
	last    time.Time
	bulkCap float64
	intCap  float64
	bulkR   float64
	intR    float64
}

func New(cfg Config) *Budget {
	if cfg.TotalBytesPerSec == 0 {
		return nil
	}
	if cfg.Burst <= 0 {
		cfg.Burst = 250 * time.Millisecond
	}
	if cfg.ReserveBytesPerSec > cfg.TotalBytesPerSec {
		cfg.ReserveBytesPerSec = cfg.TotalBytesPerSec
	}
	bulkRate := float64(cfg.TotalBytesPerSec - cfg.ReserveBytesPerSec)
	reserveRate := float64(cfg.ReserveBytesPerSec)
	bulkCap := math.Max(64*1024, bulkRate*cfg.Burst.Seconds())
	intCap := math.Max(16*1024, reserveRate*cfg.Burst.Seconds())
	if bulkRate == 0 {
		bulkCap = 0
	}
	if reserveRate == 0 {
		intCap = 0
	}
	now := time.Now()
	return &Budget{
		total: bulkCap, reserve: intCap, last: now,
		bulkCap: bulkCap, intCap: intCap, bulkR: bulkRate, intR: reserveRate,
	}
}

func (b *Budget) refill(now time.Time) {
	if now.Before(b.last) {
		b.last = now
		return
	}
	delta := now.Sub(b.last).Seconds()
	b.total = math.Min(b.bulkCap, b.total+b.bulkR*delta)
	b.reserve = math.Min(b.intCap, b.reserve+b.intR*delta)
	b.last = now
}

// capacity is the largest single request this budget can ever admit for one
// class.  Bulk is confined to bulk capacity; interactive may also draw on
// whatever bulk capacity is idle, so its ceiling is the sum.  These fields are
// fixed by New and never written afterwards, so reading them needs no lock.
func (b *Budget) capacity(interactive bool) float64 {
	total := b.bulkCap
	if interactive {
		total += b.intCap
	}
	return total
}

// MaxRequest reports the largest single request Wait can ever admit for this
// class.  Anything above it is refused outright with ErrInvalidRequest rather
// than slept on, so a caller that chooses its own request sizes -- a sending
// chunk size, say -- has to stay at or below this to be paced rather than
// rejected.  A nil Budget paces nothing and so imposes no ceiling.
func (b *Budget) MaxRequest(interactive bool) int {
	if b == nil {
		return math.MaxInt
	}
	total := b.capacity(interactive)
	if total >= float64(math.MaxInt) {
		return math.MaxInt
	}
	return int(total)
}

// Wait reserves n bytes.  A nil Budget disables pacing.  Interactive traffic
// can consume its reserve and any currently idle bulk capacity; bulk traffic
// can consume only bulk capacity.  The request is never partially released,
// which makes accounting exact across a failed lane write.
func (b *Budget) Wait(ctx context.Context, n int, interactive bool) error {
	if b == nil || n <= 0 {
		return nil
	}
	// A token bucket cannot ever satisfy a request larger than its burst
	// capacity.  Returning explicitly is important: otherwise a malformed
	// configuration (for example a 1 MiB frame on a 10 KiB/s budget) would
	// sleep and retry forever, retaining application and replay buffers until
	// the caller's much longer timeout expires.
	if float64(n) > b.capacity(interactive) {
		return ErrInvalidRequest
	}
	for {
		b.mu.Lock()
		now := time.Now()
		b.refill(now)
		need := float64(n)
		if interactive {
			if b.reserve+b.total >= need {
				fromReserve := math.Min(b.reserve, need)
				b.reserve -= fromReserve
				b.total -= need - fromReserve
				b.mu.Unlock()
				return nil
			}
		} else if b.total >= need {
			b.total -= need
			b.mu.Unlock()
			return nil
		}
		var waitSeconds float64
		if interactive {
			deficit := need - b.reserve - b.total
			waitRate := b.intR + b.bulkR
			if b.reserve >= need {
				deficit = 0
				waitRate = b.intR
			}
			if waitRate > 0 {
				waitSeconds = deficit / waitRate
			}
		} else if b.bulkR > 0 {
			waitSeconds = (need - b.total) / b.bulkR
		} else {
			b.mu.Unlock()
			return ErrInvalidRequest
		}
		b.mu.Unlock()
		if waitSeconds < 0.001 {
			waitSeconds = 0.001
		}
		timer := time.NewTimer(time.Duration(waitSeconds * float64(time.Second)))
		select {
		case <-timer.C:
		case <-ctx.Done():
			if !timer.Stop() {
				select {
				case <-timer.C:
				default:
				}
			}
			return ctx.Err()
		}
	}
}
