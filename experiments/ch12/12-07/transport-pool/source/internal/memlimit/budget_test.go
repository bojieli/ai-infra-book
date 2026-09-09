package memlimit

import (
	"context"
	"errors"
	"sync"
	"testing"
	"time"
)

func TestBudgetBlocksAndWakesWithoutExceedingCapacity(t *testing.T) {
	b := New(8)
	if err := b.Acquire(context.Background(), 8); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	acquired := make(chan error, 1)
	go func() { acquired <- b.Acquire(ctx, 1) }()

	deadline := time.Now().Add(time.Second)
	for b.Snapshot().Waiters != 1 && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	if got := b.Snapshot(); got.Used != 8 || got.Waiters != 1 {
		t.Fatalf("while full = %+v", got)
	}
	b.Release(1)
	if err := <-acquired; err != nil {
		t.Fatal(err)
	}
	if got := b.Snapshot(); got.Used != 8 || got.Peak != 8 {
		t.Fatalf("after wake = %+v", got)
	}
	b.Release(8)
}

func TestBudgetCancellationAndOversizedRequest(t *testing.T) {
	b := New(4)
	if !errors.Is(b.Acquire(context.Background(), 5), ErrRequestTooLarge) {
		t.Fatal("oversized request was accepted")
	}
	if err := b.Acquire(context.Background(), 4); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if !errors.Is(b.Acquire(ctx, 1), context.Canceled) {
		t.Fatal("canceled acquisition did not return context.Canceled")
	}
	if got := b.Snapshot().Waiters; got != 0 {
		t.Fatalf("waiters = %d", got)
	}
	b.Release(4)
}

func TestBudgetCanceledContextDoesNotReserveAvailableMemory(t *testing.T) {
	b := New(16)
	ctx, cancel := context.WithCancel(context.Background())
	cancel()

	if err := b.Acquire(ctx, 8); !errors.Is(err, context.Canceled) {
		t.Fatalf("Acquire error = %v, want context.Canceled", err)
	}
	if got := b.Snapshot().Used; got != 0 {
		t.Fatalf("used = %d, want 0", got)
	}
}

func TestBudgetConcurrentPeakIsBounded(t *testing.T) {
	b := New(32)
	var wg sync.WaitGroup
	for range 64 {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if err := b.Acquire(context.Background(), 4); err != nil {
				t.Error(err)
				return
			}
			time.Sleep(time.Microsecond)
			b.Release(4)
		}()
	}
	wg.Wait()
	got := b.Snapshot()
	if got.Used != 0 || got.Peak > got.Capacity {
		t.Fatalf("final budget = %+v", got)
	}
}
