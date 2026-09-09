package pathmodel

import (
	"math"
	"testing"
	"time"
)

// base is a fixed instant so the bucketing is deterministic.
var base = time.Unix(1767225600, 0)

func at(i int) time.Time { return base.Add(time.Duration(i) * bucketWidth) }

// The failure this whole design guards against: two paths that share nothing
// still both get slower in the evening and faster at four in the morning. A
// correlator that compares levels finds that everything correlates with
// everything and collapses the tree to one root for a reason that has nothing
// to do with a shared bottleneck.
func TestDiurnalTrendDoesNotLookLikeASharedBottleneck(t *testing.T) {
	c := NewCorrelator()
	for i := 0; i < 40; i++ {
		// A slow ramp both groups share, plus independent jitter that does not
		// coincide.
		trend := 0.20 * float64(i) / 40
		c.Observe("tokyo", at(i), Signal{LossRate: trend + independentA(i)})
		c.Observe("frankfurt", at(i), Signal{LossRate: trend + independentB(i)})
	}
	r, paired, ok := c.Correlation("tokyo", "frankfurt")
	if !ok {
		t.Fatalf("not enough paired buckets: %d", paired)
	}
	if r > 0.5 {
		t.Errorf("a shared slow trend produced correlation %.3f; the differencing did not remove it", r)
	}
}

// independentA and independentB are deterministic sequences that do not
// coincide, standing in for unrelated congestion on two unrelated paths.
func independentA(i int) float64 { return 0.05 * math.Abs(math.Sin(float64(i)*1.7)) }
func independentB(i int) float64 { return 0.05 * math.Abs(math.Sin(float64(i)*0.41+2.2)) }

// A genuinely shared bottleneck produces congestion that arrives and leaves
// together, on the scale of a queue.
func TestCoincidentCongestionIsRecognised(t *testing.T) {
	c := NewCorrelator()
	for i := 0; i < 40; i++ {
		// A burst that both see at the same buckets, which is what one queue
		// upstream of both looks like.
		spike := 0.0
		if i%7 == 0 || i%7 == 1 {
			spike = 0.25
		}
		c.Observe("svc-a", at(i), Signal{LossRate: spike + 0.01*float64(i%3)})
		c.Observe("svc-b", at(i), Signal{LossRate: spike + 0.01*float64(i%3)})
	}
	r, paired, ok := c.Correlation("svc-a", "svc-b")
	if !ok {
		t.Fatalf("not enough paired buckets: %d", paired)
	}
	if r < 0.8 {
		t.Errorf("coincident congestion produced correlation %.3f, want a strong signal", r)
	}
	merges := c.SuggestMerges(0.7)
	if len(merges) != 1 || merges[0].Correlation < 0.8 {
		t.Errorf("SuggestMerges returned %+v", merges)
	}
}

// Delay and loss are two views of one queue, so a shared bottleneck must be
// recognised when one group is seeing it as delay and the other as loss.
func TestDelayAndLossAreBothCongestionSignals(t *testing.T) {
	c := NewCorrelator()
	for i := 0; i < 40; i++ {
		busy := i%5 == 0
		lossSig, delaySig := Signal{}, Signal{}
		if busy {
			lossSig.LossRate = 0.20
			delaySig.RTTInflation = 0.020 // 20ms of queueing
		}
		c.Observe("sees-loss", at(i), lossSig)
		c.Observe("sees-delay", at(i), delaySig)
	}
	r, _, ok := c.Correlation("sees-loss", "sees-delay")
	if !ok {
		t.Fatal("insufficient buckets")
	}
	if r < 0.8 {
		t.Errorf("a queue seen as loss by one group and delay by the other correlated only %.3f", r)
	}
}

// "Not enough evidence" and "does not correlate" are different answers, and
// collapsing them would split two groups apart on no evidence at all.
func TestInsufficientEvidenceIsNotAVerdict(t *testing.T) {
	c := NewCorrelator()
	for i := 0; i < 5; i++ {
		c.Observe("a", at(i), Signal{LossRate: 0.1})
		c.Observe("b", at(i), Signal{LossRate: 0.1})
	}
	if _, _, ok := c.Correlation("a", "b"); ok {
		t.Error("a verdict was returned from five buckets")
	}
	if got := c.SuggestMerges(0.0); len(got) != 0 {
		t.Errorf("SuggestMerges proposed %+v from insufficient evidence", got)
	}
	if _, _, ok := c.Correlation("a", "never-seen"); ok {
		t.Error("a verdict was returned for a group never observed")
	}
}

// A group whose congestion never changed carries no evidence about what it
// shares. Reporting a correlation there would be reading a coefficient off a
// flat line.
func TestAFlatGroupYieldsNoCorrelation(t *testing.T) {
	c := NewCorrelator()
	for i := 0; i < 40; i++ {
		c.Observe("flat", at(i), Signal{LossRate: 0.05})
		c.Observe("varying", at(i), Signal{LossRate: 0.05 * float64(i%4)})
	}
	r, _, ok := c.Correlation("flat", "varying")
	if ok && r != 0 {
		t.Errorf("a flat series correlated at %.3f", r)
	}
}

// Buckets that are not adjacent cannot be differenced: the change across a gap
// is not a rate of change, and treating it as one invents a coincidence.
func TestGapsAreNotDifferenced(t *testing.T) {
	c := NewCorrelator()
	// Two runs separated by a long silence.
	for i := 0; i < 15; i++ {
		c.Observe("a", at(i), Signal{LossRate: 0.1 * float64(i%2)})
		c.Observe("b", at(i), Signal{LossRate: 0.1 * float64(i%2)})
	}
	for i := 200; i < 215; i++ {
		c.Observe("a", at(i), Signal{LossRate: 0.1 * float64(i%2)})
		c.Observe("b", at(i), Signal{LossRate: 0.1 * float64(i%2)})
	}
	// 30 paired buckets exist but only 28 adjacent pairs, and the gap must not
	// contribute one. The result is either a refusal or a coefficient computed
	// without the fabricated pair; both are acceptable, inventing one is not.
	if _, paired, ok := c.Correlation("a", "b"); ok && paired > 28 {
		t.Errorf("the correlation used %d differences across a gap of 185 buckets", paired)
	}
}

// Observations landing in one bucket keep the worst, because a queue that
// formed and drained inside 200ms still formed.
func TestWithinBucketKeepsTheWorstObservation(t *testing.T) {
	c := NewCorrelator()
	now := at(0)
	c.Observe("g", now, Signal{LossRate: 0.01, RTTInflation: 0.001})
	c.Observe("g", now.Add(10*time.Millisecond), Signal{LossRate: 0.30, RTTInflation: 0.050})
	c.Observe("g", now.Add(20*time.Millisecond), Signal{LossRate: 0.02, RTTInflation: 0.002})
	c.mu.Lock()
	defer c.mu.Unlock()
	got := c.groups["g"].aligned()
	if len(got) != 1 {
		t.Fatalf("three observations in one bucket produced %d buckets", len(got))
	}
	for _, sig := range got {
		if sig.LossRate != 0.30 || sig.RTTInflation != 0.050 {
			t.Errorf("bucket kept %+v, want the worst of the three", sig)
		}
	}
}

func TestForgetDropsAGroup(t *testing.T) {
	c := NewCorrelator()
	for i := 0; i < 30; i++ {
		c.Observe("gone", at(i), Signal{LossRate: 0.1})
	}
	c.Forget("gone")
	if len(c.Groups()) != 0 {
		t.Errorf("groups after Forget: %v", c.Groups())
	}
}

// A nil correlator is inert, so a caller that has not built one does not have
// to guard every call site.
func TestNilCorrelatorIsInert(t *testing.T) {
	var c *Correlator
	c.Observe("a", base, Signal{LossRate: 1})
	if _, _, ok := c.Correlation("a", "b"); ok {
		t.Error("a nil correlator returned a verdict")
	}
	if c.Groups() != nil || c.SuggestMerges(0) != nil {
		t.Error("a nil correlator returned data")
	}
	c.Forget("a")
}
