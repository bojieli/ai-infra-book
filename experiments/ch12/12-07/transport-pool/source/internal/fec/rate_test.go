package fec

import (
	"fmt"
	"math"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/lossmodel"
)

func livePath() Params {
	return Params{
		Class:           ClassBulk,
		ShardBytes:      1200,
		RateBytesPerSec: 25e6 / 8,
		RoundTrip:       300 * time.Millisecond,
	}
}

// The channel measured on the live path, below its knee: 42% loss, independent.
func liveSnapshot() lossmodel.Snapshot {
	return lossmodel.Snapshot{
		Samples: 20000, Loss: 0.42, Floor: 0.42, Recent: 0.42,
		LossAfterArrival: 0.42, ArrivalAfterLoss: 0.58,
		MeanBurst: 1.72, BurstFactor: 1.0, Memoryless: true,
	}
}

// Coding for the measured erasure rather than for a filtered floor is the
// redesign's central claim, and it is the reverse of what this file asserted
// before. The floor existed because parity was added on top of the sending
// rate, so coding for a queue's drops fed the queue. Parity is now drawn from
// the same budget as data, so a rise in measured loss must reach the code.
func TestTheCodeFollowsTheMeasuredErasure(t *testing.T) {
	calm := liveSnapshot()
	worse := calm
	worse.Loss = 0.72
	worse.Recent = 0.72
	worse.BurstFactor = 1.6
	worse.MeanBurst = 5.7
	worse.Memoryless = false

	before := Choose(calm, livePath())
	during := Choose(worse, livePath())
	t.Logf("42%%: (%d,%d) rate=%.3f; 72%%: (%d,%d) rate=%.3f",
		before.K, before.N, before.Rate, during.K, during.N, during.Rate)

	if !before.Code || !during.Code {
		t.Fatalf("expected both to be coded: %+v %+v", before, during)
	}
	if during.Rate >= before.Rate {
		t.Fatalf("erasure rose from 42%% to 72%% and the code rate did not fall: %.3f then %.3f",
			before.Rate, during.Rate)
	}
	if during.LossCoded != worse.Loss {
		t.Fatalf("sized for %.3f against a measured %.3f: the plan is reading something else",
			during.LossCoded, worse.Loss)
	}
}

// A path with nothing to repair must carry no parity, and it must reach that
// answer from the objective rather than from a threshold constant: there is no
// minimum coded loss any more, so a clean path is only uncoded if spending
// wire on parity genuinely delivers its data no sooner.
func TestAPathWithNothingToRepairIsNotCoded(t *testing.T) {
	clean := liveSnapshot()
	clean.Loss, clean.Floor, clean.Recent = 0, 0, 0
	if plan := Choose(clean, livePath()); plan.Code {
		t.Fatalf("a lossless path was coded at %.2fx overhead: %+v", plan.Overhead(), plan)
	}
}

// A barely lossy path may buy a little parity, because a block of 256 shards
// at one loss in a thousand still stalls better than a fifth of the time, and
// a round trip is expensive on the path this transport is for. What it must
// not do is spend real bandwidth on it.
func TestABarelyLossyPathBuysLittleParity(t *testing.T) {
	barely := liveSnapshot()
	barely.Loss, barely.Floor, barely.Recent = 0.001, 0.001, 0.001
	plan := Choose(barely, livePath())
	t.Logf("0.1%% loss: coded=%v overhead=%.4fx residual=%.2e", plan.Code, plan.Overhead(), plan.Residual)
	if plan.Overhead() > 1.05 {
		t.Fatalf("a 0.1%% loss path was charged %.3fx overhead: %+v", plan.Overhead(), plan)
	}
}

// Correlated loss makes a block code weaker at the same loss rate, because a
// burst is one erasure event rather than several independent ones. A controller
// that ignored this would certify a rate the path defeats.
func TestClusteredLossCostsMoreParityThanIndependentLoss(t *testing.T) {
	independent := liveSnapshot()
	clustered := independent
	clustered.BurstFactor = 3
	clustered.MeanBurst = 5.2
	clustered.Memoryless = false

	a, b := Choose(independent, livePath()), Choose(clustered, livePath())
	t.Logf("independent: rate=%.3f overhead=%.2fx; clustered: rate=%.3f overhead=%.2fx",
		a.Rate, a.Overhead(), b.Rate, b.Overhead())
	if !a.Code || !b.Code {
		t.Fatalf("expected both to be coded: %+v %+v", a, b)
	}
	if b.Overhead() <= a.Overhead() {
		t.Fatalf("clustered loss chose overhead %.2fx, no more than independent loss at %.2fx",
			b.Overhead(), a.Overhead())
	}
}

// Correlation is answered by rate. Interleaving would be the other answer and
// is deliberately absent: it makes a block wait for every block it is
// interleaved with, which gives back the latency that coding was bought for,
// and nothing measured on this path asks for that trade.
func TestCorrelationIsAnsweredByRateAndNotByInterleaving(t *testing.T) {
	independent := liveSnapshot()
	clustered := independent
	clustered.BurstFactor = 4
	clustered.Memoryless = false

	flat := Choose(independent, livePath())
	deep := Choose(clustered, livePath())
	if deep.Rate >= flat.Rate {
		t.Fatalf("clustered loss chose rate %.3f, no lower than independent loss at %.3f",
			deep.Rate, flat.Rate)
	}
	if deep.EffectiveBurst != clustered.BurstFactor {
		t.Fatalf("effective burst %.2f against a measured %.2f: nothing should be dividing it",
			deep.EffectiveBurst, clustered.BurstFactor)
	}
}

// An interactive flow trades rate for a block short enough that a repair beats
// a retransmission by a wide margin. It must not be handed a block that takes
// most of a round trip to send.
func TestInteractiveFlowsGetShorterBlocks(t *testing.T) {
	bulk := Choose(liveSnapshot(), livePath())
	p := livePath()
	p.Class = ClassInteractive
	interactive := Choose(liveSnapshot(), p)

	t.Logf("bulk: (%d,%d); interactive: (%d,%d)", bulk.K, bulk.N, interactive.K, interactive.N)
	if interactive.N >= bulk.N {
		t.Fatalf("interactive block of %d shards is not shorter than the bulk %d",
			interactive.N, bulk.N)
	}
	// And it must still be a usable code, not a token one.
	if !interactive.Code || interactive.Rate < 0.2 {
		t.Fatalf("interactive plan is not usable: %+v", interactive)
	}
	span := time.Duration(float64(interactive.N) * float64(p.ShardBytes) / p.RateBytesPerSec * float64(time.Second))
	if span > p.RoundTrip/2 {
		t.Fatalf("interactive block takes %v of a %v round trip", span, p.RoundTrip)
	}
}

// The code rate can never exceed the channel's capacity, which is (1-p). A plan
// that claimed otherwise would be promising to deliver more than arrives.
func TestNoPlanExceedsChannelCapacity(t *testing.T) {
	for _, loss := range []float64{0.05, 0.2, 0.42, 0.6, 0.75} {
		s := liveSnapshot()
		s.Loss, s.Floor, s.Recent = loss, loss, loss
		s.ArrivalAfterLoss = 1 - loss
		s.MeanBurst = 1 / (1 - loss)
		plan := Choose(s, livePath())
		if !plan.Code {
			t.Logf("loss %.2f: not coded (%s)", loss, plan.Why)
			continue
		}
		t.Logf("loss %.2f: (%d,%d) rate=%.3f overhead=%.2fx residual=%.1e",
			loss, plan.K, plan.N, plan.Rate, plan.Overhead(), plan.Residual)
		if plan.Rate > 1-loss {
			t.Fatalf("loss %.2f: code rate %.3f exceeds the channel capacity %.3f",
				loss, plan.Rate, 1-loss)
		}
	}
}

// A channel too lossy to code at any usable rate must say so rather than
// returning a code that cannot work.
func TestAnImpossibleChannelIsReportedNotCoded(t *testing.T) {
	s := liveSnapshot()
	s.Loss, s.Floor, s.Recent = 0.97, 0.97, 0.97
	plan := Choose(s, livePath())
	if plan.Code {
		t.Fatalf("97%% loss produced a code: %+v", plan)
	}
	if plan.Why == "" {
		t.Fatal("no reason given for refusing to code")
	}
}

// The binomial tail is the arithmetic every plan rests on, so it is checked
// against values computed independently.
func TestBinomialTail(t *testing.T) {
	for _, test := range []struct {
		n    int
		q    float64
		k    int
		want float64
	}{
		{n: 10, q: 0.5, k: 1, want: 0.0009765625},  // P(X = 0)
		{n: 10, q: 0.5, k: 6, want: 0.623046875},   // P(X <= 5)
		{n: 1, q: 0.3, k: 1, want: 0.7},            // P(X = 0)
		{n: 64, q: 0.58, k: 0, want: 0},            // vacuous
		{n: 64, q: 0.58, k: 65, want: 1},           // certain
		{n: 20, q: 0.9, k: 20, want: 0.8784233454}, // P(X <= 19) = 1 - 0.9^20
	} {
		got := binomialTailBelow(test.n, test.q, test.k)
		if math.Abs(got-test.want) > 1e-9 {
			t.Errorf("binomialTailBelow(%d, %v, %d) = %.10f, want %.10f",
				test.n, test.q, test.k, got, test.want)
		}
	}
}

// A loss rate of one or more is not a measurement: every honest rate is a
// count of losses over a count of trials. Sizing a code for one would spend
// the lowest rate this search allows -- eight times the wire per delivered
// byte -- on the path that produced the impossible figure.
func TestChooseRefusesAnImpossibleLossRate(t *testing.T) {
	params := Params{ShardBytes: 1200, RateBytesPerSec: 1e6, RoundTrip: 300 * time.Millisecond}
	for _, loss := range []float64{1, 1.2527, math.Inf(1), math.NaN()} {
		t.Run(fmt.Sprintf("%v", loss), func(t *testing.T) {
			plan := Choose(lossmodel.Snapshot{Loss: loss, Floor: loss, Recent: loss, BurstFactor: 1}, params)
			if plan.Code {
				t.Fatalf("coded for a loss rate of %v: %+v", loss, plan)
			}
			if _, ok := ShardsFor(8, lossmodel.Snapshot{Loss: loss, Floor: loss, BurstFactor: 1}, params); ok {
				t.Fatalf("sized a block for a loss rate of %v", loss)
			}
		})
	}
	// The guard must not touch a rate that is merely high.
	plan := Choose(lossmodel.Snapshot{Loss: 0.42, Floor: 0.42, Recent: 0.42, BurstFactor: 1}, params)
	if !plan.Code {
		t.Fatalf("refused to code a 42%% erasure channel: %+v", plan)
	}
}

// The incident this redesign answers was not a code that was slightly weak. It
// was a code sized for a tenth of the erasure actually present: at 19.9%
// measured downstream erasure the gateway's plan was sized for 1.76%, and
// every one of 14,792 flows above 5% erasure ran a code sized for less than
// half of it. The floor that produced those numbers is gone, so this holds the
// replacement to the property that was violated -- the plan is sized for what
// the channel is measured to do, and the residual it predicts is one the
// session above can absorb rather than one that re-issues a tenth of the
// payload.
func TestNoPlanIsSizedForAFractionOfTheMeasuredErasure(t *testing.T) {
	for _, loss := range []float64{0.05, 0.10, 0.199, 0.30, 0.42, 0.50} {
		s := liveSnapshot()
		s.Loss, s.Floor, s.Recent = loss, loss, loss
		s.ArrivalAfterLoss = 1 - loss
		plan := Choose(s, livePath())
		if !plan.Code {
			t.Fatalf("erasure %.3f was left uncoded (%s)", loss, plan.Why)
		}
		t.Logf("erasure %.3f: rate=%.3f overhead=%.2fx residual=%.2e sized_for=%.3f",
			loss, plan.Rate, plan.Overhead(), plan.Residual, plan.LossCoded)
		if plan.LossCoded < loss {
			t.Errorf("erasure %.3f: plan sized for %.3f, less than the channel is doing",
				loss, plan.LossCoded)
		}
		// The parity has to be worth something against that erasure. A code
		// whose block still fails a tenth of the time hands the tenth back to
		// the session, which is the residual the incident was made of.
		if plan.Residual > 0.1 {
			t.Errorf("erasure %.3f: rate %.3f leaves a residual of %.3f for the session to re-issue",
				loss, plan.Rate, plan.Residual)
		}
		// And it must not have overcorrected into spending the path on parity.
		if plan.Overhead() > 1/(1-loss)*2 {
			t.Errorf("erasure %.3f: overhead %.2fx is more than twice what the channel costs",
				loss, plan.Overhead())
		}
	}
}

// A block that sealed short did so because the producer stopped, and the
// throughput objective prices a retransmission in symbols the producer was not
// going to send. Left to itself it declines the parity and takes the round
// trip, which on a token stream is a reader watching a sentence stop.
func TestAShortBlockIsSizedForDeliveryRatherThanThroughput(t *testing.T) {
	snap := lossmodel.Snapshot{Loss: 0.14, BurstFactor: 1.03, ArrivalAfterLoss: 0.86}
	// The rate estimate an application-limited flow produces. It is low
	// because the flow is not sending, which is exactly when this must not be
	// read as "a retransmission is cheap".
	// A real symbol is a datagram, not a token: the size is what the carrier
	// allows, and using a small one here would prove something about a
	// configuration that does not ship.
	p := Params{ShardBytes: 1100, RateBytesPerSec: 20000, RoundTrip: 200 * time.Millisecond}
	n, ok := ShardsFor(1, snap, p)
	if !ok {
		t.Fatal("a single symbol on a 14% channel got no code at all, which is what " +
			"the throughput objective did at this rate estimate")
	}
	if n-1 < 3 {
		t.Fatalf("one symbol got %d repairs; at 14%% erasure that leaves a residual of "+
			"%.2f%%, and every one of those is a round trip the reader waits through",
			n-1, 100*math.Pow(0.14, float64(n)))
	}
}

// The same sizing must not depend on how fast the flow happens to be going,
// because that is the input that was wrong.
func TestShortBlockSizingDoesNotFollowTheRateEstimate(t *testing.T) {
	snap := lossmodel.Snapshot{Loss: 0.14, BurstFactor: 1.03, ArrivalAfterLoss: 0.86}
	var first int
	for i, rate := range []float64{2e4, 1e5, 8.5e5, 2e6} {
		n, _ := ShardsFor(1, snap, Params{
			ShardBytes: 1100, RateBytesPerSec: rate, RoundTrip: 200 * time.Millisecond,
		})
		if i == 0 {
			first = n
			continue
		}
		if n < first {
			t.Fatalf("at %.0f B/s a single symbol got %d shards, fewer than the %d it got "+
				"at 20000 B/s: the estimate is still deciding the protection", rate, n, first)
		}
	}
}

// Long blocks keep the throughput answer. A transfer is measured in bytes per
// second, and there the parity genuinely costs what the objective says.
func TestALongBlockKeepsTheThroughputAnswer(t *testing.T) {
	snap := lossmodel.Snapshot{Loss: 0.14, BurstFactor: 1.03, ArrivalAfterLoss: 0.86}
	p := Params{ShardBytes: 1200, RateBytesPerSec: 850000, RoundTrip: 200 * time.Millisecond}
	n, ok := ShardsFor(64, snap, p)
	if !ok {
		t.Fatal("a 64-symbol block got no code")
	}
	// Held to a rate rather than an exact count, so that retuning the objective
	// does not fail this for the wrong reason. What must not happen is a long
	// block acquiring a short block's redundancy.
	if rate := float64(64) / float64(n); rate < 0.5 {
		t.Fatalf("a 64-symbol block was coded at rate %.2f; the short-block rule has "+
			"leaked into blocks that are paying for their parity in throughput", rate)
	}
}
