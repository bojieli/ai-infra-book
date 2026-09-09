package pep

import (
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/metrics"
)

// A storm must stay legible: the label is written, the events it stood in for
// are counted, and the count is reported rather than lost.
func TestRecordLimiterSurvivesAStorm(t *testing.T) {
	var limiter recordLimiter
	start := time.Unix(1700000000, 0)
	write, suppressed, total := limiter.due(metrics.LaneJoinUnknownSession, start)
	if !write || suppressed != 0 || total != 1 {
		t.Fatalf("first record write=%t suppressed=%d total=%d, want true, 0 and 1", write, suppressed, total)
	}
	const storm = 500
	for i := 0; i < storm; i++ {
		if write, _, _ := limiter.due(metrics.LaneJoinUnknownSession, start.Add(time.Duration(i)*time.Millisecond)); write {
			t.Fatalf("event %d was written inside the interval", i)
		}
	}
	write, suppressed, total = limiter.due(metrics.LaneJoinUnknownSession, start.Add(recordLogInterval))
	if !write || suppressed != storm || total != storm+2 {
		t.Fatalf("after the interval write=%t suppressed=%d total=%d, want true, %d and %d",
			write, suppressed, total, storm, storm+2)
	}
	if write, suppressed, _ = limiter.due(metrics.LaneJoinUnknownSession, start.Add(2*recordLogInterval)); !write || suppressed != 0 {
		t.Fatalf("suppressed count survived being reported: write=%t suppressed=%d", write, suppressed)
	}
}

// A storm that stops must still say how big it was. The suppressed count is
// reported one record late, so on a gateway restart ninety-four refusals
// produced a single record claiming to stand for none of them; the total is
// what makes one record the whole story.
func TestARecordSaysHowManyThereHaveBeen(t *testing.T) {
	var limiter recordLimiter
	start := time.Unix(1700000000, 0)
	if _, _, total := limiter.due(metrics.LaneJoinUnknownSession, start); total != 1 {
		t.Fatalf("total = %d on the first event, want 1", total)
	}
	for i := 0; i < 93; i++ {
		limiter.due(metrics.LaneJoinUnknownSession, start.Add(time.Duration(i)*time.Millisecond))
	}
	// Nothing more arrives, so no further record is written and the suppressed
	// count is never reported. The record that was written must already carry
	// the count, which the next one confirms.
	if _, _, total := limiter.due(metrics.LaneJoinUnknownSession, start.Add(recordLogInterval)); total != 95 {
		t.Fatalf("total = %d, want every event counted", total)
	}
}

// Labels are rate-limited apart, so a storm of one cannot bury the single
// event an operator is looking for -- across all three label spaces sharing
// this implementation, and whether or not they share a limiter.
func TestRecordLimiterSeparatesLabels(t *testing.T) {
	var limiter recordLimiter
	now := time.Unix(1700000000, 0)
	if write, _, _ := limiter.due(metrics.LaneJoinUnknownSession, now); !write {
		t.Fatal("the first record was suppressed")
	}
	if write, _, _ := limiter.due(metrics.LaneJoinUnknownSession, now.Add(time.Second)); write {
		t.Fatal("a repeated label was written inside the interval")
	}
	for _, label := range []interface {
		String() string
	}{
		metrics.LaneJoinPrincipalMismatch,
		metrics.AccountRefusalFlowLimit,
		metrics.AccountRefusalClientLimit,
		enrollmentOutcome("rejected"),
		enrollmentOutcome("store_unavailable"),
		admissionRefused,
	} {
		if write, _, total := limiter.due(label, now.Add(time.Second)); !write || total != 1 {
			t.Fatalf("%s shared a budget with another label: write=%t total=%d", label, write, total)
		}
	}
	// Separate limiters are separate: an enrollment storm cannot suppress a
	// refusal record, and neither can suppress the other's totals.
	var other recordLimiter
	if write, _, total := other.due(metrics.LaneJoinUnknownSession, now.Add(time.Second)); !write || total != 1 {
		t.Fatalf("a second limiter shared the first's state: write=%t total=%d", write, total)
	}
}
