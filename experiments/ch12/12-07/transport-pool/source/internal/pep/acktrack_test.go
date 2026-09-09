package pep

import (
	"context"
	"errors"
	"testing"
	"time"
)

func TestAckTrackerCumulativeCoverage(t *testing.T) {
	tr := newAckTracker()
	if tr.Covered(0, 10) {
		t.Fatal("nothing acknowledged yet")
	}
	tr.Advance(10)
	if !tr.Covered(0, 10) {
		t.Fatal("cumulative acknowledgement did not cover the range")
	}
	if tr.Covered(0, 11) {
		t.Fatal("covered a byte past the cumulative point")
	}
}

// The reason ranges exist: a striped receiver holds gaps by construction, so a
// chunk delivered on a fast lane must not read as outstanding merely because a
// slower lane has not filled the hole behind it.
func TestAckTrackerCoversRangeAboveAGap(t *testing.T) {
	tr := newAckTracker()
	tr.Advance(100)
	tr.Add([][2]uint64{{200, 300}})
	if !tr.Covered(200, 300) {
		t.Fatal("range above the cumulative point was not covered")
	}
	if tr.Covered(100, 200) {
		t.Fatal("the gap must not read as covered")
	}
	if tr.Covered(150, 250) {
		t.Fatal("a span straddling the gap must not read as covered")
	}
}

func TestAckTrackerFoldsAdjacentRangesIntoCumulative(t *testing.T) {
	tr := newAckTracker()
	tr.Add([][2]uint64{{100, 200}, {200, 300}})
	tr.Advance(100)
	if !tr.Covered(0, 300) {
		t.Fatal("adjacent ranges should have folded into the cumulative point")
	}
	tr.mu.Lock()
	defer tr.mu.Unlock()
	if len(tr.ranges) != 0 {
		t.Fatalf("ranges = %v, want all folded away", tr.ranges)
	}
	if tr.cumulative != 300 {
		t.Fatalf("cumulative = %d, want 300", tr.cumulative)
	}
}

func TestAckTrackerMergesOverlappingRanges(t *testing.T) {
	tr := newAckTracker()
	tr.Add([][2]uint64{{500, 600}, {550, 700}, {690, 800}})
	if !tr.Covered(500, 800) {
		t.Fatal("overlapping ranges should merge into one span")
	}
	tr.mu.Lock()
	defer tr.mu.Unlock()
	if len(tr.ranges) != 1 {
		t.Fatalf("ranges = %v, want one merged span", tr.ranges)
	}
}

func TestAckTrackerWaitWakesOnAcknowledgement(t *testing.T) {
	tr := newAckTracker()
	done := make(chan error, 1)
	go func() { done <- tr.Wait(context.Background(), 0, 1000) }()

	time.Sleep(20 * time.Millisecond)
	select {
	case <-done:
		t.Fatal("Wait returned before the range was acknowledged")
	default:
	}

	tr.Advance(1000)
	select {
	case err := <-done:
		if err != nil {
			t.Fatalf("Wait: %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("Wait did not wake on acknowledgement")
	}
}

func TestAckTrackerWaitRespectsContext(t *testing.T) {
	tr := newAckTracker()
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	go func() { done <- tr.Wait(ctx, 0, 10) }()
	time.Sleep(20 * time.Millisecond)
	cancel()
	select {
	case err := <-done:
		if !errors.Is(err, context.Canceled) {
			t.Fatalf("Wait = %v, want context.Canceled", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("Wait ignored context cancellation")
	}
}

func TestAckTrackerCloseReleasesWaiters(t *testing.T) {
	tr := newAckTracker()
	done := make(chan error, 1)
	go func() { done <- tr.Wait(context.Background(), 0, 10) }()
	time.Sleep(20 * time.Millisecond)
	tr.Close()
	select {
	case err := <-done:
		if !errors.Is(err, errAckTrackerClosed) {
			t.Fatalf("Wait = %v, want errAckTrackerClosed", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("Close did not release the waiter")
	}
}

// A stale cumulative acknowledgement from a slower lane must not move the
// tracker backwards.
func TestAckTrackerIgnoresStaleAcknowledgements(t *testing.T) {
	tr := newAckTracker()
	tr.Advance(500)
	tr.Advance(200)
	if !tr.Covered(0, 500) {
		t.Fatal("a stale acknowledgement moved the cumulative point backwards")
	}
}
