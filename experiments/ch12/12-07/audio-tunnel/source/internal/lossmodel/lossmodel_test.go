package lossmodel

import (
	"math"
	"math/rand"
	"testing"
	"time"
)

// bernoulli returns the arrival pattern of an independent erasure channel.
func bernoulli(rng *rand.Rand, n int, loss float64) []bool {
	arrived := make([]bool, n)
	for i := range arrived {
		arrived[i] = rng.Float64() >= loss
	}
	return arrived
}

// gilbert returns the arrival pattern of a two-state channel whose bad state
// drops everything, with the given long-run loss and mean burst length.
func gilbert(rng *rand.Rand, n int, loss, meanBurst float64) []bool {
	arrived := make([]bool, n)
	recover := 1 / meanBurst
	enter := recover * loss / (1 - loss)
	bad := false
	for i := range arrived {
		if bad {
			if rng.Float64() < recover {
				bad = false
			}
		} else if rng.Float64() < enter {
			bad = true
		}
		arrived[i] = !bad
	}
	return arrived
}

func feed(e *Estimator, arrived []bool) {
	for i, ok := range arrived {
		if ok {
			e.Observe(uint64(i))
		}
	}
	// Nothing decides the tail, so push the sequence past it.
	for i := len(arrived); i < len(arrived)+2*DefaultReorderTolerance; i++ {
		e.Observe(uint64(i))
	}
}

// The whole design rests on being able to tell an independent channel from a
// queue, so that has to hold at the loss rate actually measured on the path.
func TestIndependentLossIsRecognisedAsIndependent(t *testing.T) {
	rng := rand.New(rand.NewSource(1))
	e := New(Config{RoundSamples: 1000})
	feed(e, bernoulli(rng, 20000, 0.42))

	s := e.Snapshot()
	if !s.Memoryless {
		t.Fatalf("independent loss reported as correlated: %+v", s)
	}
	if math.Abs(s.Loss-0.42) > 0.02 {
		t.Fatalf("loss = %.3f, want about 0.42", s.Loss)
	}
	if math.Abs(s.BurstFactor-1) > 0.1 {
		t.Fatalf("burst factor = %.3f, want about 1 for an independent channel", s.BurstFactor)
	}
	// An independent channel still has runs; what it does not have is runs
	// longer than independence alone produces.
	if want := 1 / (1 - s.Loss); math.Abs(s.MeanBurst-want) > 0.15 {
		t.Fatalf("mean burst = %.3f, want about %.3f", s.MeanBurst, want)
	}
}

// The queue above the knee loses in runs, and answering it with parity rather
// than with restraint is the failure this test exists to prevent.
func TestClusteredLossIsRecognisedAsClustered(t *testing.T) {
	rng := rand.New(rand.NewSource(2))
	e := New(Config{RoundSamples: 1000})
	feed(e, gilbert(rng, 20000, 0.5, 6))

	s := e.Snapshot()
	if s.Memoryless {
		t.Fatalf("clustered loss reported as independent: %+v", s)
	}
	if s.BurstFactor < 1.5 {
		t.Fatalf("burst factor = %.3f, want well above 1 for clustered loss", s.BurstFactor)
	}
	if s.MeanBurst < 4 {
		t.Fatalf("mean burst = %.3f, want near the configured 6", s.MeanBurst)
	}
}

// The floor is what separates the channel from congestion. It must survive a
// congestion episode: a filter that lets the episode raise the floor reports
// no congestion during exactly the interval that has some.
func TestTheFloorSurvivesACongestionEpisode(t *testing.T) {
	rng := rand.New(rand.NewSource(3))
	e := New(Config{RoundSamples: 1000, Rounds: 8})

	var pattern []bool
	pattern = append(pattern, bernoulli(rng, 4000, 0.42)...)
	pattern = append(pattern, gilbert(rng, 3000, 0.72, 6)...)
	feed(e, pattern)

	s := e.Snapshot()
	if math.Abs(s.Floor-0.42) > 0.04 {
		t.Fatalf("floor = %.3f, want the channel's own rate of about 0.42", s.Floor)
	}
	if s.Recent < 0.6 {
		t.Fatalf("recent loss = %.3f, want the episode's rate of about 0.72", s.Recent)
	}
	if s.Congestive < 0.2 {
		t.Fatalf("congestive share = %.3f, want about 0.3", s.Congestive)
	}
	if s.Memoryless {
		t.Fatalf("the episode's clustered loss was reported as independent: %+v", s)
	}
}

// Congestion and clustering are different questions and the answer to one must
// not be read off the other. A policer that drops independently raises the
// loss rate without clustering it, and a transport that only watched burst
// length would sail straight past it.
func TestIndependentCongestionIsStillCongestion(t *testing.T) {
	rng := rand.New(rand.NewSource(4))
	// The floor filter has to remember the quiet period for the whole episode,
	// so its window is set wide enough to hold both phases here. A filter that
	// forgets sooner than the episode lasts reports no congestion during
	// exactly the interval that has some, which is why the congestion
	// controller has to periodically drain and re-measure the floor rather
	// than trust a filter alone.
	e := New(Config{RoundSamples: 1000, Rounds: 32})

	var pattern []bool
	pattern = append(pattern, bernoulli(rng, 4000, 0.42)...)
	pattern = append(pattern, bernoulli(rng, 14000, 0.70)...)
	feed(e, pattern)

	s := e.Snapshot()
	if s.Congestive < 0.2 {
		t.Fatalf("congestive share = %.3f, want the rise above the floor", s.Congestive)
	}
	if !s.Memoryless {
		t.Fatalf("independent loss at a higher rate is still independent: %+v", s)
	}
}

// A path that reorders must not be read as a path that drops. The tolerance is
// what buys that, and packets beyond it are counted as reordered rather than
// quietly revising a statistic that has already been read.
func TestReorderingWithinToleranceIsNotLoss(t *testing.T) {
	e := New(Config{RoundSamples: 1000, ReorderTolerance: 8})
	// Deliver in swapped pairs: every packet arrives, none in order.
	for i := uint64(0); i < 4000; i += 2 {
		e.Observe(i + 1)
		e.Observe(i)
	}
	for i := uint64(4000); i < 4032; i++ {
		e.Observe(i)
	}
	if s := e.Snapshot(); s.Loss > 0.001 {
		t.Fatalf("loss = %.4f on a lossless but reordering path: %+v", s.Loss, s)
	}
	if s := e.Snapshot(); s.Reordered != 0 {
		t.Fatalf("reordered = %d within the tolerance, want 0", s.Reordered)
	}
}

func TestReorderingBeyondToleranceIsCountedNotRewritten(t *testing.T) {
	e := New(Config{RoundSamples: 1000, ReorderTolerance: 4})
	for i := uint64(0); i < 100; i++ {
		if i == 10 {
			continue
		}
		e.Observe(i)
	}
	// Far too late: sequence 10 was decided ninety packets ago.
	e.Observe(10)
	s := e.Snapshot()
	if s.Reordered != 1 {
		t.Fatalf("reordered = %d, want the one late packet", s.Reordered)
	}
	if s.Decided == 0 || s.Loss <= 0 {
		t.Fatalf("the late packet's slot should still read as lost: %+v", s)
	}
}

func TestExplicitOutcomesDoNotInferPacketNumberGaps(t *testing.T) {
	e := New(Config{RoundSamples: 100})
	for i := 0; i < 80; i++ {
		e.ObserveOutcome(i%4 != 0)
	}
	s := e.Snapshot()
	if s.Decided != 80 {
		t.Fatalf("explicit outcomes decided %d packets, want 80", s.Decided)
	}
	if math.Abs(s.Loss-0.25) > 0.001 {
		t.Fatalf("explicit outcomes measured loss %.3f, want 0.25", s.Loss)
	}
}

// The estimator infers loss under a reorder tolerance; Analyze knows every
// packet's fate. On an in-order stream they must agree, or one of them is
// measuring something other than the channel.
func TestTheOnlineEstimateMatchesTheOfflineOne(t *testing.T) {
	rng := rand.New(rand.NewSource(5))
	arrived := gilbert(rng, 20000, 0.45, 3)

	e := New(Config{RoundSamples: 1000})
	feed(e, arrived)
	online := e.Snapshot()
	offline := Analyze(arrived)

	if math.Abs(online.Loss-offline.Loss) > 0.03 {
		t.Fatalf("loss: online %.3f, offline %.3f", online.Loss, offline.Loss)
	}
	if math.Abs(online.MeanBurst-offline.MeanBurst) > 0.4 {
		t.Fatalf("mean burst: online %.3f, offline %.3f", online.MeanBurst, offline.MeanBurst)
	}
	if math.Abs(online.BurstFactor-offline.BurstFactor) > 0.2 {
		t.Fatalf("burst factor: online %.3f, offline %.3f", online.BurstFactor, offline.BurstFactor)
	}
}

// The independence verdict decides whether the transport codes or backs off,
// so it must refuse to answer before it can. A confident wrong answer in the
// first few packets of a flow is worse than none.
func TestIndependenceIsNotClaimedBeforeItIsKnown(t *testing.T) {
	rng := rand.New(rand.NewSource(6))
	e := New(Config{RoundSamples: 1000})
	feed(e, bernoulli(rng, 50, 0.42))
	if s := e.Snapshot(); s.Memoryless {
		t.Fatalf("independence claimed from 50 packets: %+v", s)
	}
}

// Analyze is what measurement tools report, so it has to reproduce the
// published figures for the path. These are the live 1 Mbit/s numbers from
// docs/PATH-CHARACTER-20260813.md, regenerated from the same channel model.
func TestAnalyzeReproducesTheMeasuredChannel(t *testing.T) {
	rng := rand.New(rand.NewSource(7))
	p := Analyze(bernoulli(rng, 200000, 0.45))

	if math.Abs(p.Loss-0.45) > 0.01 {
		t.Fatalf("loss = %.3f, want 0.45", p.Loss)
	}
	// The live run measured 0.454 and 0.556 against a loss rate of 0.450.
	if math.Abs(p.LossAfterArrival-p.Loss) > 0.01 {
		t.Fatalf("P(loss|prev arrived) = %.3f, want the loss rate %.3f", p.LossAfterArrival, p.Loss)
	}
	if math.Abs(p.ArrivalAfterLoss-(1-p.Loss)) > 0.01 {
		t.Fatalf("P(arrived|prev lost) = %.3f, want %.3f", p.ArrivalAfterLoss, 1-p.Loss)
	}
	if p.LongestBurst < 5 {
		t.Fatalf("longest burst = %d, want the handful an independent channel gives", p.LongestBurst)
	}
	if total := func() int {
		n := 0
		for length, count := range p.Bursts {
			n += length * count
		}
		return n
	}(); total != p.Lost {
		t.Fatalf("burst histogram accounts for %d losses, want %d", total, p.Lost)
	}
}

// The sequence number an arrival carries comes off the wire, so how far the
// estimator walks to catch up with it is the peer's choice. A datagram naming
// a sequence 2^32 ahead used to retire that many slots one at a time,
// fabricating a loss for each, and never returned.
func TestASequenceFarAheadIsADiscontinuityNotFourBillionLosses(t *testing.T) {
	e := New(Config{})
	for seq := uint64(0); seq < 200; seq++ {
		e.Observe(seq)
	}
	before := e.Snapshot()

	done := make(chan struct{})
	go func() { e.Observe(1 << 32); close(done) }()
	select {
	case <-done:
	case <-time.After(10 * time.Second):
		t.Fatal("a sequence 2^32 ahead did not return")
	}

	if e.Discontinuities() != 1 {
		t.Fatalf("the jump was counted as %d discontinuities", e.Discontinuities())
	}
	after := e.Snapshot()
	if after.Samples > before.Samples+maxDecidedPerArrival {
		t.Fatalf("the jump added %v samples, so it was counted out rather than skipped",
			after.Samples-before.Samples)
	}
	// The estimator still works where it now is: the sequences beside the
	// jump are counted as arrivals, not as the far side of a gap.
	for seq := uint64(1 << 32); seq < 1<<32+200; seq++ {
		e.Observe(seq)
	}
	if loss := e.Snapshot().Loss; loss > 0.5 {
		t.Fatalf("a clean run after the jump measured %.2f loss", loss)
	}
}

// Every figure the estimator reports as a probability is a count of outcomes
// over a count of trials, so none of them can leave [0,1] on its own. What
// reads them cannot tell a rate from an accounting failure, though, and a
// figure above one sizes parity for a channel that delivers nothing -- so the
// reported values are rates whatever the counters behind them say.
func TestSnapshotReportsProbabilitiesEvenFromInconsistentCounters(t *testing.T) {
	e := New(Config{})
	// Counters that cannot arise from Observe, standing in for any future
	// accounting path that charges a loss to a trial that never happened.
	e.samples, e.losses = 100, 125.27
	e.fromArrival, e.lossAfterArrival = 10, 40
	e.fromLoss, e.arrivalAfterLoss = 10, 30
	e.rounds = []float64{1.4, 2.2}

	s := e.Snapshot()
	for name, value := range map[string]float64{
		"loss": s.Loss, "loss after arrival": s.LossAfterArrival,
		"arrival after loss": s.ArrivalAfterLoss, "floor": s.Floor,
		"recent": s.Recent, "congestive": s.Congestive,
	} {
		if value < 0 || value > 1 {
			t.Fatalf("%s = %v is not a probability", name, value)
		}
	}
}

// A path that really erases nothing must still report zero rather than the
// clamp's bounds, or the guard would be hiding the measurement it protects.
func TestSnapshotLeavesAnOrdinaryEstimateAlone(t *testing.T) {
	e := New(Config{RoundSamples: 100})
	for i := 0; i < 1000; i++ {
		e.ObserveOutcome(i%4 != 0)
	}
	if s := e.Snapshot(); s.Loss < 0.2 || s.Loss > 0.3 {
		t.Fatalf("loss = %v, want about a quarter", s.Loss)
	}
}
