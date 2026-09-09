package limiter

import (
	"context"
	"math"
	"testing"
	"time"
)

func TestBulkCannotConsumeInteractiveReserve(t *testing.T) {
	b := New(Config{TotalBytesPerSec: 1000, ReserveBytesPerSec: 500, Burst: time.Second})
	if err := b.Wait(context.Background(), int(b.bulkCap), false); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Millisecond)
	defer cancel()
	if err := b.Wait(ctx, 100, false); err == nil {
		t.Fatal("bulk unexpectedly consumed reserved capacity")
	}
}

func TestInteractiveReserveSurvivesBulk(t *testing.T) {
	b := New(Config{TotalBytesPerSec: 1000, ReserveBytesPerSec: 500, Burst: time.Second})
	if err := b.Wait(context.Background(), int(b.bulkCap), false); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()
	if err := b.Wait(ctx, 250, true); err != nil {
		t.Fatal(err)
	}
}

func TestDisabledBudgetAndCancellation(t *testing.T) {
	if err := (*Budget)(nil).Wait(context.Background(), 1<<30, false); err != nil {
		t.Fatal(err)
	}
	b := New(Config{TotalBytesPerSec: 100, ReserveBytesPerSec: 0, Burst: time.Millisecond})
	if err := b.Wait(context.Background(), int(b.bulkCap), false); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if err := b.Wait(ctx, 1000, false); err == nil {
		t.Fatal("canceled wait succeeded")
	}
}

func TestRequestLargerThanBurstFailsImmediately(t *testing.T) {
	b := New(Config{TotalBytesPerSec: 1024, ReserveBytesPerSec: 512, Burst: time.Millisecond})
	if b == nil {
		t.Fatal("expected enabled budget")
	}
	started := time.Now()
	if err := b.Wait(context.Background(), int(b.bulkCap+b.intCap)+1, true); err != ErrInvalidRequest {
		t.Fatalf("large interactive request error = %v, want %v", err, ErrInvalidRequest)
	}
	if elapsed := time.Since(started); elapsed > 100*time.Millisecond {
		t.Fatalf("impossible request took too long: %s", elapsed)
	}
	if err := b.Wait(context.Background(), int(b.bulkCap)+1, false); err != ErrInvalidRequest {
		t.Fatalf("large bulk request error = %v, want %v", err, ErrInvalidRequest)
	}
}

// MaxRequest exists so a caller that picks its own request sizes can stay
// inside what Wait will admit instead of discovering the refusal at send time,
// which makes agreement with Wait the whole point of it.
func TestMaxRequestIsTheAdmissionCeiling(t *testing.T) {
	if got := (*Budget)(nil).MaxRequest(false); got != math.MaxInt {
		t.Fatalf("disabled budget ceiling = %d, want no ceiling", got)
	}
	cfg := Config{TotalBytesPerSec: 1024, ReserveBytesPerSec: 512, Burst: time.Millisecond}
	b := New(cfg)
	if b == nil {
		t.Fatal("expected enabled budget")
	}
	for _, interactive := range []bool{false, true} {
		ceiling := b.MaxRequest(interactive)
		if err := b.Wait(context.Background(), ceiling+1, interactive); err != ErrInvalidRequest {
			t.Fatalf("interactive=%v above ceiling error = %v, want %v", interactive, err, ErrInvalidRequest)
		}
		// A full bucket, so a request at the ceiling is admitted without
		// waiting rather than merely being admissible in principle.
		if err := New(cfg).Wait(context.Background(), ceiling, interactive); err != nil {
			t.Fatalf("interactive=%v at ceiling %d was refused: %v", interactive, ceiling, err)
		}
	}
}

// Bulk is the tighter class, and every budget that admits bulk at all admits a
// whole 64 KiB frame of it. Endpoints size their chunks against this floor, so
// it is a promise rather than an implementation detail.
func TestBulkCeilingNeverFallsBelowTheBurstFloor(t *testing.T) {
	for _, cfg := range []Config{
		{TotalBytesPerSec: 1},
		{TotalBytesPerSec: 2, ReserveBytesPerSec: 1},
		{TotalBytesPerSec: 1 << 20, ReserveBytesPerSec: 1<<20 - 1, Burst: time.Microsecond},
	} {
		b := New(cfg)
		if b == nil {
			t.Fatalf("%+v: expected enabled budget", cfg)
		}
		if got := b.MaxRequest(false); got < 64*1024 {
			t.Fatalf("%+v: bulk ceiling = %d, want at least 64 KiB", cfg, got)
		}
	}
}
