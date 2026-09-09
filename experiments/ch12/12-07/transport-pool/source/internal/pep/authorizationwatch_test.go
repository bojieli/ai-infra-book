package pep

import (
	"testing"
	"time"
)

// The first failure of a run must always be written: it is the only record
// that says when the outage began.
func TestAuthorizationWatchAlwaysRecordsTheFirstFailure(t *testing.T) {
	var watch authorizationWatch
	start := time.Unix(1700000000, 0)
	write, consecutive, suppressed, failingFor := watch.failed(start)
	if !write {
		t.Fatal("the failure that began the run was suppressed")
	}
	if consecutive != 1 || suppressed != 0 || failingFor != 0 {
		t.Fatalf("consecutive=%d suppressed=%d failingFor=%s", consecutive, suppressed, failingFor)
	}
}

// A once-a-second refresh wrote 86,400 identical lines a day. The run is
// restated at a bounded rate instead, and each record carries the run length
// and the count it stands for.
func TestAuthorizationWatchBoundsAContinuingOutage(t *testing.T) {
	var watch authorizationWatch
	start := time.Unix(1700000000, 0)
	if write, _, _, _ := watch.failed(start); !write {
		t.Fatal("first failure suppressed")
	}
	writes := 0
	for i := 1; i <= 600; i++ {
		if write, _, _, _ := watch.failed(start.Add(time.Duration(i) * time.Second)); write {
			writes++
		}
	}
	// Ten minutes of once-a-second failures at one record a minute.
	if writes != 10 {
		t.Fatalf("ten minutes of failures produced %d records; want 10", writes)
	}
	write, consecutive, suppressed, failingFor := watch.failed(start.Add(601 * time.Second))
	if write {
		t.Fatal("wrote inside the interval")
	}
	if consecutive != 602 {
		t.Fatalf("consecutive=%d; want 602", consecutive)
	}
	if failingFor != 601*time.Second {
		t.Fatalf("failingFor=%s; want 601s", failingFor)
	}
	_ = suppressed
}

// Every failure is counted even when its record is suppressed, so the next
// record can say how large the run it stands for was.
func TestAuthorizationWatchCountsSuppressedFailures(t *testing.T) {
	var watch authorizationWatch
	start := time.Unix(1700000000, 0)
	watch.failed(start)
	for i := 1; i < 60; i++ {
		watch.failed(start.Add(time.Duration(i) * time.Second))
	}
	write, consecutive, suppressed, _ := watch.failed(start.Add(authorizationRecordInterval))
	if !write {
		t.Fatal("no record after the interval elapsed")
	}
	if suppressed != 59 {
		t.Fatalf("suppressed=%d; want 59", suppressed)
	}
	if consecutive != 61 {
		t.Fatalf("consecutive=%d; want 61", consecutive)
	}
}

// A run that ends silently leaves an operator reading an error with no ending.
func TestAuthorizationWatchReportsRecovery(t *testing.T) {
	var watch authorizationWatch
	start := time.Unix(1700000000, 0)
	for i := 0; i < 5; i++ {
		watch.failed(start.Add(time.Duration(i) * time.Second))
	}
	recovered, attempts, unreadableFor := watch.succeeded(start.Add(5 * time.Second))
	if !recovered {
		t.Fatal("recovery from a five-attempt outage was not reported")
	}
	if attempts != 5 {
		t.Fatalf("attempts=%d; want 5", attempts)
	}
	if unreadableFor != 5*time.Second {
		t.Fatalf("unreadableFor=%s; want 5s", unreadableFor)
	}
	// A healthy gateway must not announce a recovery on every tick.
	if recovered, _, _ := watch.succeeded(start.Add(6 * time.Second)); recovered {
		t.Fatal("reported a recovery with no preceding failure")
	}
}

// After recovery the next outage is a new run, not a continuation.
func TestAuthorizationWatchStartsAFreshRunAfterRecovery(t *testing.T) {
	var watch authorizationWatch
	start := time.Unix(1700000000, 0)
	watch.failed(start)
	watch.succeeded(start.Add(time.Second))
	write, consecutive, _, failingFor := watch.failed(start.Add(2 * time.Second))
	if !write {
		t.Fatal("the first failure of a new run was suppressed by the previous one")
	}
	if consecutive != 1 || failingFor != 0 {
		t.Fatalf("consecutive=%d failingFor=%s; want a fresh run", consecutive, failingFor)
	}
}
