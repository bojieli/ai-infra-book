package pep

import (
	"fmt"
	"sync"
	"time"
)

// recordLogInterval is how often one label is written to the log while a storm
// is running. The first record of a label is always written; the ones a storm
// suppresses are counted and reported with the next.
//
// Every caller has wanted the same ten seconds so far. If one ever needs a
// different cadence, this becomes a field on recordLimiter -- which costs the
// zero value its usability, so it is not worth doing before there is a second
// answer.
const recordLogInterval = 10 * time.Second

// recordLimiter keeps a storm of repeated operational records legible. It
// writes one record per label per interval and counts the ones that record
// stands in for, so a gateway under a storm produces a readable log rather
// than either a flood or a silence.
//
// Grouping is by label rather than by the identifiers in the event. Per
// session or per invitation would read better, but those identifiers are the
// peer's to choose: a map keyed by them is memory whose size a peer decides,
// and a storm is exactly when a peer is producing identifiers this endpoint
// has never seen. Every label space here is closed at compile time -- lane
// join refusals, account admission refusals, enrollment outcomes -- so the map
// stays bounded by construction.
//
// The zero value is ready to use.
type recordLimiter struct {
	mu     sync.Mutex
	labels map[string]*recordCounter
}

type recordCounter struct {
	last       time.Time
	suppressed uint64
	total      uint64
}

// due reports whether this label should be written now, how many of its events
// went unwritten since the last time it was, and how many there have been in
// total.
//
// The total is there because the suppressed count alone is reported one record
// late: a storm that stops leaves its tail in a record that never gets
// written. Measured on a gateway restart, ninety-four refusals produced one
// record saying it stood for none of them, which is the same silence this
// logging exists to end. Every record carries the count for its label, so one
// record is the whole story.
func (l *recordLimiter) due(label fmt.Stringer, now time.Time) (write bool, suppressed, total uint64) {
	key := label.String()
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.labels == nil {
		l.labels = make(map[string]*recordCounter)
	}
	counter, ok := l.labels[key]
	if !ok {
		counter = &recordCounter{}
		l.labels[key] = counter
	}
	counter.total++
	total = counter.total
	if !counter.last.IsZero() && now.Sub(counter.last) < recordLogInterval {
		counter.suppressed++
		return false, 0, total
	}
	suppressed = counter.suppressed
	counter.last, counter.suppressed = now, 0
	return true, suppressed, total
}
