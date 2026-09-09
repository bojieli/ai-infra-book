package pathmodel

import (
	"math"
	"sort"
	"sync"
	"time"
)

// Which segments a path actually shares is an empirical question, and this is
// the instrument for answering it.
//
// The tree in tree.go is bootstrapped from a static hierarchy -- uplink, then
// region, then peer -- which encodes somebody's belief about what is shared.
// That belief is testable: two destinations sit behind a common bottleneck if
// and only if congestion at one shows up at the other. When it does, they
// belong under one node and should pool what they learn; when it does not,
// giving them a shared node makes a busy peer throttle a healthy one.
//
// The trap is correlating the wrong thing. Loss and delay on almost any two
// Internet paths rise in the evening and fall at four in the morning, so
// correlating levels finds that everything correlates with everything and
// collapses the tree to a single root for a reason that has nothing to do with
// a shared bottleneck. What distinguishes a genuinely shared segment is that
// its congestion arrives and leaves *together*, on the scale of a queue rather
// than of a working day.
//
// So this correlates first differences of short buckets. Differencing removes
// any trend the two series have in common -- which is exactly the diurnal
// signal -- and leaves the sub-second coincidences that a shared queue
// produces and independent paths do not.

const (
	// bucketWidth is the resolution of the signal. A queue at a shared
	// bottleneck fills and drains within a round trip, so the bucket has to be
	// shorter than one; a bucket of seconds averages the event away.
	bucketWidth = 200 * time.Millisecond
	// bucketCount is how many are retained: ten seconds, matching the
	// bottleneck window the rest of the model uses.
	bucketCount = 50
	// minPairedBuckets is the fewest overlapping buckets a correlation may be
	// computed from. A coefficient from four points is noise with a decimal
	// point.
	minPairedBuckets = 20
)

// Signal is one group's congestion state during one bucket.
type Signal struct {
	// LossRate is the fraction erased in this bucket.
	LossRate float64
	// RTTInflation is how far the round trip rose above this group's own
	// minimum, in seconds. It is relative to the group's own baseline because
	// two paths of different lengths are being compared for whether they
	// *change* together, not for which is longer.
	RTTInflation float64
}

type bucket struct {
	at     time.Time
	signal Signal
	filled bool
}

type series struct {
	buckets [bucketCount]bucket
	next    int
}

func (s *series) observe(now time.Time, sig Signal) {
	slot := now.UnixNano() / int64(bucketWidth)
	last := &s.buckets[(s.next-1+bucketCount)%bucketCount]
	if last.filled && last.at.UnixNano()/int64(bucketWidth) == slot {
		// Same bucket: keep the worst observation, since a queue that formed
		// and drained within one bucket still formed.
		if sig.LossRate > last.signal.LossRate {
			last.signal.LossRate = sig.LossRate
		}
		if sig.RTTInflation > last.signal.RTTInflation {
			last.signal.RTTInflation = sig.RTTInflation
		}
		return
	}
	s.buckets[s.next] = bucket{at: now, signal: sig, filled: true}
	s.next = (s.next + 1) % bucketCount
}

// aligned returns the retained buckets keyed by bucket index, so two groups
// can be compared only where both observed.
func (s *series) aligned() map[int64]Signal {
	out := make(map[int64]Signal, bucketCount)
	for _, b := range s.buckets {
		if !b.filled {
			continue
		}
		out[b.at.UnixNano()/int64(bucketWidth)] = b.signal
	}
	return out
}

// Correlator records congestion signals per group and reports which groups
// move together.
type Correlator struct {
	mu     sync.Mutex
	groups map[string]*series
}

func NewCorrelator() *Correlator {
	return &Correlator{groups: make(map[string]*series)}
}

// Observe records one group's state now.
func (c *Correlator) Observe(group string, now time.Time, sig Signal) {
	if c == nil || group == "" {
		return
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	s, ok := c.groups[group]
	if !ok {
		s = &series{}
		c.groups[group] = s
	}
	s.observe(now, sig)
}

// Groups lists what has been observed, sorted.
func (c *Correlator) Groups() []string {
	if c == nil {
		return nil
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	out := make([]string, 0, len(c.groups))
	for k := range c.groups {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

// Correlation reports how strongly two groups' congestion moves together, on
// the differenced series described above.
//
// ok is false when the two have not been observed in enough of the same
// buckets to say anything, which is a different answer from "they do not
// correlate" and must not be collapsed into it: an unmeasured pair that reads
// as uncorrelated would be split apart on no evidence.
func (c *Correlator) Correlation(a, b string) (r float64, paired int, ok bool) {
	if c == nil {
		return 0, 0, false
	}
	c.mu.Lock()
	sa, okA := c.groups[a]
	sb, okB := c.groups[b]
	var alignedA, alignedB map[int64]Signal
	if okA && okB {
		alignedA, alignedB = sa.aligned(), sb.aligned()
	}
	c.mu.Unlock()
	if !okA || !okB {
		return 0, 0, false
	}

	slots := make([]int64, 0, len(alignedA))
	for k := range alignedA {
		if _, both := alignedB[k]; both {
			slots = append(slots, k)
		}
	}
	sort.Slice(slots, func(i, j int) bool { return slots[i] < slots[j] })

	// First differences between consecutive retained buckets. Any trend the
	// two series share -- the reason everything looks correlated at 8pm -- is
	// removed by the differencing, leaving the coincident changes that a
	// shared queue causes.
	var da, db []float64
	for i := 1; i < len(slots); i++ {
		if slots[i]-slots[i-1] != 1 {
			// Non-adjacent buckets: a difference across a gap is not a rate of
			// change, so it is skipped rather than treated as one.
			continue
		}
		da = append(da, combined(alignedA[slots[i]])-combined(alignedA[slots[i-1]]))
		db = append(db, combined(alignedB[slots[i]])-combined(alignedB[slots[i-1]]))
	}
	// The bar is on the differences rather than on the paired buckets,
	// because the differences are what the coefficient is computed from: a
	// pair observed in fifty scattered buckets that are never adjacent yields
	// no usable point, and counting the buckets would say otherwise.
	if len(da) < minPairedBuckets {
		return 0, len(da), false
	}
	return pearson(da, db), len(da), true
}

// combined reduces a bucket to one congestion number.
//
// Loss and delay are two views of the same queue: it fills, delay rises, it
// overflows, loss starts. Summing them with delay scaled to the same order as
// a loss fraction lets a shared bottleneck be recognised from whichever
// symptom it happens to be producing.
func combined(s Signal) float64 {
	return s.LossRate + s.RTTInflation*10
}

func pearson(x, y []float64) float64 {
	n := float64(len(x))
	if n == 0 {
		return 0
	}
	var mx, my float64
	for i := range x {
		mx += x[i]
		my += y[i]
	}
	mx, my = mx/n, my/n
	var num, dx, dy float64
	for i := range x {
		a, b := x[i]-mx, y[i]-my
		num += a * b
		dx += a * a
		dy += b * b
	}
	if dx == 0 || dy == 0 {
		// One series never moved. That is not correlation and not its
		// absence: a group whose congestion never changed carries no evidence
		// about what it shares.
		return 0
	}
	return num / math.Sqrt(dx*dy)
}

// Merge is a proposal that two groups sit behind one bottleneck.
type Merge struct {
	A, B        string
	Correlation float64
	Buckets     int
}

// SuggestMerges reports the pairs whose congestion moves together strongly
// enough to be worth treating as one segment.
//
// It reports rather than acts. Changing a live tree's topology re-parents
// every flow's budget, and the evidence for doing so is the hard part while
// applying it is a map assignment -- so the evidence is produced here and the
// decision is left to a caller that can be held to a policy. MergeGroups
// applies one.
func (c *Correlator) SuggestMerges(threshold float64) []Merge {
	groups := c.Groups()
	var out []Merge
	for i := 0; i < len(groups); i++ {
		for j := i + 1; j < len(groups); j++ {
			r, paired, ok := c.Correlation(groups[i], groups[j])
			if !ok || r < threshold {
				continue
			}
			out = append(out, Merge{A: groups[i], B: groups[j], Correlation: r, Buckets: paired})
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Correlation > out[j].Correlation })
	return out
}

// Forget drops a group's history, for a path that is gone.
func (c *Correlator) Forget(group string) {
	if c == nil {
		return
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	delete(c.groups, group)
}

// ResetCorrelator drops every group, for tests, for the same reason ResetTree
// exists: the correlator is process-wide and two tests that could not affect
// each other on a real network share it here.
func ResetCorrelator() {
	sharedCorrelator.mu.Lock()
	defer sharedCorrelator.mu.Unlock()
	sharedCorrelator.groups = make(map[string]*series)
}
