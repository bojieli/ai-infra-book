package pep

import "time"

// authorizationRecordInterval bounds how often a continuing store outage is
// restated. The refresh runs every second, so an unbounded record wrote 86,400
// identical lines a day, none of which said how long it had been failing. One
// line a minute, each carrying the run length, is the same information in a
// form an operator can read past.
const authorizationRecordInterval = time.Minute

// authorizationWatch tracks a run of refresh failures so the record can
// describe the run rather than the tick.
//
// The refresh loop used to hold no state at all, which is why its record could
// not distinguish a gateway that had been unable to read its authorization
// store for three days from one that had missed a single tick: every line was
// identical. What an operator needs from these records are the edges - when a
// run started, that it is still going and for how long, and when it ended -
// and none of those are visible one tick at a time.
type authorizationWatch struct {
	consecutive  uint64
	failingSince time.Time
	lastRecord   time.Time
	suppressed   uint64
}

// failed records one failed refresh. The first failure of a run always writes,
// because it is the only record that says when the run began; the rest are
// bounded by authorizationRecordInterval and carry the counts they stand for.
func (w *authorizationWatch) failed(now time.Time) (write bool, consecutive, suppressed uint64, failingFor time.Duration) {
	w.consecutive++
	if w.failingSince.IsZero() {
		w.failingSince = now
	}
	failingFor = now.Sub(w.failingSince)
	if !w.lastRecord.IsZero() && now.Sub(w.lastRecord) < authorizationRecordInterval {
		w.suppressed++
		return false, w.consecutive, 0, failingFor
	}
	suppressed = w.suppressed
	w.lastRecord, w.suppressed = now, 0
	return true, w.consecutive, suppressed, failingFor
}

// succeeded records a successful refresh and reports the run it ended, if any.
// A run that closes silently leaves an operator reading an error with no
// ending, so recovery is always worth a record.
func (w *authorizationWatch) succeeded(now time.Time) (recovered bool, failedAttempts uint64, unreadableFor time.Duration) {
	if w.consecutive == 0 {
		return false, 0, 0
	}
	failedAttempts, unreadableFor = w.consecutive, now.Sub(w.failingSince)
	*w = authorizationWatch{}
	return true, failedAttempts, unreadableFor
}
