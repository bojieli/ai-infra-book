package classifier

import (
	"testing"
	"time"
)

func TestNewFlowGetsInteractiveClassAfterBudget(t *testing.T) {
	c := New(DefaultConfig())
	got := c.Observe(Observation{
		Age:                      4 * time.Second,
		SinceLastPayload:         300 * time.Millisecond,
		BytesUp:                  1024,
		BytesDown:                2048,
		Bidirectional:            true,
		SmallBidirectionalBursts: true,
	})
	if got != ClassInteractive {
		t.Fatalf("class = %s, want interactive", got)
	}
}

func TestSustainedOneWayFlowBecomesBulk(t *testing.T) {
	c := New(DefaultConfig())
	got := c.Observe(Observation{
		Age:              3 * time.Second,
		BytesDown:        4 * 1024 * 1024,
		DownRate:         8 * 1024 * 1024,
		SinceLastPayload: 5 * time.Millisecond,
	})
	if got != ClassBulk {
		t.Fatalf("class = %s, want bulk", got)
	}
}

func TestBulkPromotionStartsAtEarlyLaneIsolationBoundary(t *testing.T) {
	c := New(DefaultConfig())
	got := c.Observe(Observation{
		Age: 1 * time.Second, BytesDown: 128 * 1024,
		DownRate: 128 * 1024, SinceLastPayload: 5 * time.Millisecond,
	})
	if got != ClassBulk {
		t.Fatalf("class = %s, want bulk at the configured promotion boundary", got)
	}
}

func TestConstrainedOneWayFlowStillBecomesBulk(t *testing.T) {
	c := New(DefaultConfig())
	got := c.Observe(Observation{
		Age: 4 * time.Second, BytesDown: 4 * 1024 * 1024,
		DownRate: 512 * 1024, SinceLastPayload: 5 * time.Millisecond,
	})
	if got != ClassBulk {
		t.Fatalf("class = %s, want bulk on a constrained path", got)
	}
}

func TestInteractiveBurstIsNotBulk(t *testing.T) {
	c := New(DefaultConfig())
	got := c.Observe(Observation{
		Age:                      30 * time.Second,
		BytesUp:                  8 * 1024 * 1024,
		BytesDown:                8 * 1024 * 1024,
		UpRate:                   32 * 1024,
		DownRate:                 32 * 1024,
		Bidirectional:            true,
		SmallBidirectionalBursts: true,
	})
	if got != ClassInteractive {
		t.Fatalf("class = %s, want interactive", got)
	}
}

func TestBulkClassDoesNotFlap(t *testing.T) {
	c := New(DefaultConfig())
	c.Observe(Observation{Age: 4 * time.Second, BytesDown: 4 * 1024 * 1024, DownRate: 8 * 1024 * 1024})
	got := c.Observe(Observation{Age: 12 * time.Second, BytesDown: 4 * 1024 * 1024, SinceLastPayload: 10 * time.Second})
	if got != ClassBulk {
		t.Fatalf("class = %s after idle gap, want bulk", got)
	}
}

// The measured regression these settings exist for: a connection carrying
// repeated megabyte requests accumulates enough bytes to cross the access-link
// bulk threshold, is demoted permanently, and is then isolated to protect
// interactive traffic that does not exist on it. On the China-US datacenter
// path that cost a factor of two while every other case gained five to
// seventeen times.
//
// The thresholds carry most of this: one request must not look like a
// transfer. The veto carries the rest: many requests must not add up to one.
func dcClassifier() *Classifier { return New(dcClassifierConfig()) }

func TestOneLargeRequestIsNotBulkOnADatacenterLeg(t *testing.T) {
	c := dcClassifier()
	busy := Observation{BytesUp: 5 << 20, Age: 2 * time.Second,
		SinceLastPayload: 10 * time.Millisecond, UpRate: 20 << 20}
	if got := c.Observe(busy); got == ClassBulk {
		t.Fatalf("a single 5MB request classified %v", got)
	}
}

func TestManyRequestsDoNotAddUpToBulk(t *testing.T) {
	c := dcClassifier()
	busy := Observation{BytesUp: 1 << 20, Age: 2 * time.Second,
		SinceLastPayload: 10 * time.Millisecond, UpRate: 20 << 20}
	// Enough requests to pass even the datacenter byte threshold several times
	// over. Each one is a burst and then a wait, because that is what a request
	// is: the wait is not incidental to the shape, it is the shape.
	for i := range 60 {
		busy.BytesUp += 1 << 20
		busy.Age += 2 * time.Second
		if got := c.Observe(busy); got == ClassBulk {
			t.Fatalf("request %d classified bulk at %d bytes", i, busy.BytesUp)
		}
		idle := busy
		idle.SinceLastPayload = 2 * time.Second
		if got := c.Observe(idle); got == ClassBulk {
			t.Fatalf("request %d classified bulk while the caller waited", i)
		}
	}
}

// The veto must not change the profile whose published results depend on the
// old behaviour: there, a slow bulk transfer is slow because the path is bad,
// and it still has to unlock lanes.
func TestIdleGapVetoDisabledLeavesBulkReachable(t *testing.T) {
	cfg := DefaultConfig()
	if cfg.BulkIdleGapVeto != 0 {
		t.Fatalf("default profile enabled the veto: %v", cfg.BulkIdleGapVeto)
	}
	c := New(cfg)
	o := Observation{BytesUp: 300 * 1024, Age: 2 * time.Second,
		SinceLastPayload: 5 * time.Second}
	if got := c.Observe(o); got != ClassBulk {
		t.Fatalf("with the veto off, a long-idle large flow classified %v, want bulk", got)
	}
}

// A genuine bulk transfer never stops asking, so it must still be demoted on
// the datacenter profile. Otherwise that profile would have no bulk class at
// all rather than a correctly narrow one.
func TestSustainedTransferStillBecomesBulkOnADatacenterLeg(t *testing.T) {
	c := dcClassifier()
	o := Observation{Age: 11 * time.Second, SinceLastPayload: 5 * time.Millisecond,
		UpRate: 100 << 20}
	for i := 0; i < 60; i++ {
		o.BytesUp += 4 << 20
		o.Age += time.Second
		if c.Observe(o) == ClassBulk {
			return
		}
	}
	t.Fatalf("a continuously busy multi-hundred-megabyte transfer never became bulk")
}

// The veto is sticky. A flow seen idle must not become bulk later merely
// because a subsequent observation lands mid-burst -- which is the common case,
// since the scheduler ticks during bursts too.
func TestIdleVetoSurvivesLaterBusyObservations(t *testing.T) {
	c := dcClassifier()
	// Two separate gaps, which is what it takes for going quiet to count as
	// something this flow does rather than something that happened to it. The
	// busy observation between them is what makes them separate.
	c.Observe(Observation{Age: 2 * time.Second, SinceLastPayload: 3 * time.Second})
	c.Observe(Observation{Age: 3 * time.Second, SinceLastPayload: time.Millisecond})
	c.Observe(Observation{Age: 4 * time.Second, SinceLastPayload: 3 * time.Second})
	busy := Observation{BytesUp: 500 << 20, Age: 300 * time.Second,
		SinceLastPayload: time.Millisecond, UpRate: 100 << 20}
	for i := 0; i < 10; i++ {
		if got := c.Observe(busy); got == ClassBulk {
			t.Fatalf("observation %d after an idle re-enabled bulk", i)
		}
	}
}

// The datacenter profile's two classifier changes are checked here for whether
// they still change any outcome, because a knob that no longer does is a knob
// to delete rather than to document.
//
// Since whether a flow is made of small exchanges became a rate over a recent
// window rather than a lifetime total, a long conversation stays interactive on
// every profile and neither of these is what saves it. What they still do is
// narrower and worth keeping: the thresholds stop one multi-megabyte request
// being read as a transfer, and the veto stops many requests adding up to one.
func TestTheDatacenterClassifierChangesStillChangeSomething(t *testing.T) {
	dc := dcClassifierConfig()

	// A single large request, busy while observed, is bulk on the access-link
	// thresholds and not on the datacenter ones.
	single := Observation{BytesUp: 5 << 20, Age: 2 * time.Second,
		SinceLastPayload: 5 * time.Millisecond, UpRate: 20 << 20}
	if New(DefaultConfig()).Observe(single) != ClassBulk {
		t.Error("a 5MB burst is no longer bulk on the access-link profile; the thresholds have stopped differing")
	}
	if got := New(dc).Observe(single); got == ClassBulk {
		t.Errorf("a 5MB request classified %v on the datacenter profile", got)
	}

	// Many requests on one connection, past even the datacenter byte
	// threshold. Only the veto keeps these out of bulk.
	many := func(cfg Config) Class {
		c := New(cfg)
		busy := Observation{Age: 12 * time.Second, SinceLastPayload: 5 * time.Millisecond,
			UpRate: 40 << 20}
		idle := busy
		idle.SinceLastPayload = 2 * time.Second
		var last Class
		for i := 0; i < 40; i++ {
			busy.BytesUp += 1 << 20
			busy.Age += time.Second
			last = c.Observe(busy)
			idle.BytesUp, idle.Age = busy.BytesUp, busy.Age
			c.Observe(idle)
		}
		return last
	}
	noVeto := dc
	noVeto.BulkIdleGapVeto = 0
	if many(dc) == ClassBulk {
		t.Error("forty requests past the threshold went bulk with the veto on")
	}
	if many(noVeto) != ClassBulk {
		t.Error("the veto no longer changes anything at these thresholds; delete it rather than document it")
	}
}

// dcClassifierConfig mirrors what internal/profile ships for dc-long-haul.
// The profile package imports this one, so these tests cannot import it back;
// TestDatacenterProfileMatchesWhatItsTestsAssume over there fails if the two
// ever drift, which is how this copy stayed wrong through one change already.
func dcClassifierConfig() Config {
	c := DefaultConfig()
	c.BulkBytes = 32 << 20
	c.BulkMinimumAge = 10 * time.Second
	c.BulkIdleGapVeto = time.Second
	c.BulkIdleGapVetoEpisodes = 2
	return c
}

// A declaration buys the first second, which is the window inference cannot
// cover and which a short request spends entirely inside.
func TestDeclareSetsTheStartingClass(t *testing.T) {
	c := New(DefaultConfig())
	if c.Class() != ClassNew {
		t.Fatalf("a fresh classifier is %v", c.Class())
	}
	c.Declare(ClassInteractive)
	if c.Class() != ClassInteractive {
		t.Errorf("after declaring interactive, class is %v", c.Class())
	}
}

// It is a starting point, not a promise. A flow declared interactive that
// behaves like a transfer is still demoted, or the declaration would be a way
// to opt out of classification entirely.
func TestADeclaredFlowIsStillJudgedByWhatItDoes(t *testing.T) {
	c := New(DefaultConfig())
	c.Declare(ClassInteractive)
	o := Observation{Age: 2 * time.Second, SinceLastPayload: time.Millisecond,
		UpRate: 100 << 20}
	for i := 0; i < 5; i++ {
		o.BytesUp += 8 << 20
		o.Age += time.Second
		if c.Observe(o) == ClassBulk {
			return
		}
	}
	t.Error("a flow declared interactive was never demoted despite moving 40MB")
}

// Bulk is sticky whether it was inferred or declared, since a declaration is
// the same conclusion reached earlier.
func TestDeclaringBulkIsSticky(t *testing.T) {
	c := New(DefaultConfig())
	c.Declare(ClassBulk)
	c.Declare(ClassInteractive)
	if c.Class() != ClassBulk {
		t.Errorf("bulk was undeclared by a later hint: %v", c.Class())
	}
	if got := c.Observe(Observation{Age: time.Second, SinceLastPayload: 5 * time.Second}); got != ClassBulk {
		t.Errorf("a declared-bulk flow reclassified to %v", got)
	}
}

// An unknown class does nothing rather than defaulting, because a hint that
// silently did nothing is indistinguishable from one that never matched.
func TestDeclaringNonsenseChangesNothing(t *testing.T) {
	c := New(DefaultConfig())
	c.Declare(Class(99))
	if c.Class() != ClassNew {
		t.Errorf("an unknown class was applied: %v", c.Class())
	}
}

// The datacenter profile carries five workload shapes, not one, and each of
// them has to land somewhere defensible. This table is the record of where.
//
// It exists because every threshold in the datacenter config was chosen from
// the request case, and a threshold chosen from one shape is a threshold
// untested against the other four. A change that improves the request case and
// silently reclassifies token streams should fail here rather than in a
// deployment.
func TestEveryDatacenterWorkloadShapeLandsSomewhere(t *testing.T) {
	// tick is one scheduler observation.
	type tick struct {
		up, down uint64
		since    time.Duration
		upRate   float64
		downRate float64
	}
	// A conversation's recent-rate test is what SmallBidirectionalBursts
	// reports; the observer computes it from a one-second window, so these
	// cases state it directly.
	for _, tc := range []struct {
		name    string
		small   bool
		bidi    bool
		ticks   []tick
		wantNot Class
		wantIs  Class
		note    string
	}{
		{
			name: "one recognition request, cold",
			bidi: true, small: false,
			ticks:   []tick{{up: 355 << 10, since: 5 * time.Millisecond, upRate: 1 << 20}},
			wantNot: ClassBulk,
			note:    "300ms of upload never reaches the ten-second minimum age",
		},
		{
			name: "recognition on a held-open connection",
			bidi: true, small: false,
			ticks: []tick{
				{up: 355 << 10, since: 5 * time.Millisecond, upRate: 1 << 20},
				{up: 355 << 10, since: 1700 * time.Millisecond},
				{up: 710 << 10, since: 5 * time.Millisecond, upRate: 1 << 20},
				{up: 710 << 10, since: 1700 * time.Millisecond},
			},
			wantNot: ClassBulk,
			wantIs:  ClassInteractive,
			note:    "the caller waits between utterances, whatever the running total",
		},
		{
			name: "a language model streaming tokens",
			bidi: true, small: true,
			ticks: []tick{
				{up: 1 << 10, down: 800, since: 30 * time.Millisecond, downRate: 800},
				{up: 1 << 10, down: 24000, since: 30 * time.Millisecond, downRate: 800},
				{up: 1 << 10, down: 48000, since: 30 * time.Millisecond, downRate: 800},
			},
			wantNot: ClassBulk,
			wantIs:  ClassInteractive,
			note: "tokens arrive too close together to look idle, so the small " +
				"recent rate is the only thing that separates this from a transfer",
		},
		{
			name: "a checkpoint pull",
			bidi: false, small: false,
			ticks: func() []tick {
				var out []tick
				var got uint64
				for i := range 40 {
					got += 4 << 20
					out = append(out, tick{down: got, since: 5 * time.Millisecond,
						downRate: 100 << 20})
					_ = i
				}
				return out
			}(),
			wantIs: ClassBulk,
			note:   "never stops asking, and passes both the byte and age floors",
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			c := dcClassifier()
			age := 11 * time.Second
			var got Class
			for _, tk := range tc.ticks {
				age += time.Second
				got = c.Observe(Observation{
					BytesUp: tk.up, BytesDown: tk.down,
					UpRate: tk.upRate, DownRate: tk.downRate,
					Age: age, SinceLastPayload: tk.since,
					Bidirectional:            tc.bidi,
					SmallBidirectionalBursts: tc.small,
				})
			}
			if tc.wantIs != ClassNew && got != tc.wantIs {
				t.Fatalf("%s classified %v, want %v (%s)", tc.name, got, tc.wantIs, tc.note)
			}
			if tc.wantNot != ClassNew && got == tc.wantNot {
				t.Fatalf("%s classified %v, which it must not (%s)", tc.name, got, tc.note)
			}
		})
	}
}
