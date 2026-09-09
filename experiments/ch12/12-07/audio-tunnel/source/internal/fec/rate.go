package fec

import (
	"math"
	"time"

	"github.com/bojieli/queqiao/internal/lossmodel"
)

// Class is what a flow needs from the code. It decides the block length, which
// is the only place latency and efficiency genuinely trade against each other.
type Class int

const (
	// ClassBulk wants the code rate as close to capacity as the channel
	// allows, and can wait a block to get it.
	ClassBulk Class = iota
	// ClassInteractive wants a repair sooner than a long block can deliver
	// one, and pays for it in parity.
	ClassInteractive
)

// Params describes the flow the code is for. Everything here except the class
// is measured, not configured.
type Params struct {
	Class Class
	// ShardBytes is the payload one shard carries, normally the path MTU less
	// headers.
	ShardBytes int
	// RateBytesPerSec is the flow's current sending rate. With the block
	// length fixed, this is what converts it into a delay.
	RateBytesPerSec float64
	// RoundTrip is the path's minimum round trip. It bounds the useful block
	// length: a block that takes longer to send than a retransmission takes to
	// arrive has given up the only thing coding was for. It is also what an
	// unrepairable block costs, which is what decides how much parity is worth
	// buying -- see reissueCost.
	RoundTrip time.Duration
}

// Plan is a code chosen for a channel.
type Plan struct {
	// Code is false when parity is not worth sending, and everything below is
	// meaningless.
	Code bool
	K, N int
	// Rate is K/N, the fraction of the wire that carries data.
	Rate float64
	// Residual is the estimated probability that a block cannot be repaired
	// and must be retransmitted.
	Residual float64
	// LossCoded is the erasure probability the code was sized for.
	LossCoded float64
	// EffectiveBurst is the mean loss burst after interleaving, in shards of
	// one block. It is what made the code weaker than the loss rate alone
	// would suggest.
	EffectiveBurst float64
	// Why records the reason in one phrase, for logs and traces.
	Why string
}

// MaxShards is the largest block a block code can have. Each shard needs a
// distinct field element for the generator's construction, and GF(256) has 256
// of them.
//
// It bounds ShardsFor, which sizes a genuine block: the burst a producer has
// just finished, with nothing following it to share parity with. The sliding
// window is not bounded by it -- its coefficients are drawn per repair over at
// most a window's symbols, so it can send as many repairs as the channel needs
// (see WindowRate).
const MaxShards = 256

const (
	// minShards keeps a block long enough that the binomial has some shape. A
	// two-shard block at 42% loss needs a rate near a third to be reliable,
	// which is worse than not coding.
	minShards = 8
	// minRate stops the search descending into codes that spend more than
	// eight times the wire per byte delivered. Past that the channel is not
	// one this transport can use, and saying so is more useful than pretending.
	minRate = 0.125
	// shortBlockSymbols is the largest block that sealed because the producer
	// stopped rather than because the block filled, and below which the
	// throughput objective above is answering the wrong question.
	//
	// That objective trades parity bytes against the cost of a retransmission,
	// and it prices the retransmission in symbols this flow could have sent
	// instead. For a block that sealed short, the flow was not going to send
	// them: it stopped, which is why the block is short. The spare capacity is
	// free and the objective values it as if it were scarce, so it declines
	// the parity and takes the round trip.
	//
	// Measured on the China-US path, a language model's token stream carried
	// 2078 symbols, of which the code recovered 322 and failed on 29 -- a 1.38%
	// residual on a workload where every unrepaired symbol is a reader watching
	// a sentence stop for a round trip. The same run put 2.6% to 4.4% of tokens
	// more than half a second behind the generator's own schedule. Sizing these
	// blocks to a residual instead costs about a hundred bytes per token, on a
	// path whose capacity knee is 333 Mbit/s.
	shortBlockSymbols = 4
	// shortBlockResidual is how often such a block may fail to decode and fall
	// back to a round trip. At this path's 14% erasure it buys three repairs
	// for a single symbol, which is where an emulated frame experiment already
	// found the knee: one copy lost 71 frames of 400, two lost 10, three lost
	// none, and the median moved by 1.4ms.
	shortBlockResidual = 1e-3
	// codeStillRepairs is where a code stops being one. A block that fails
	// more often than it succeeds is not repaired by its parity, it is a
	// lottery ticket bought with bandwidth, and the objective cannot tell the
	// difference on its own: at an erasure rate no rate can carry, every
	// candidate delivers about nothing and the search picks between failures.
	// A half is not a tuning knob but the point where the arithmetic changes
	// meaning.
	codeStillRepairs = 0.5
)

// Choose sizes a code for the erasure the path is measured to be applying to
// the direction this endpoint sends into.
//
// It sizes for the measured erasure rather than for a filtered floor, and that
// is only safe because parity costs a code rate rather than a byte rate.
//
// A floor is the part of the loss that does not respond to sending more
// slowly. Separating it from congestion would matter if coding for a queue's
// drops put more traffic into the queue that was already overflowing -- and
// that is what the floor was defending against. It does not, because a repair
// symbol is not additional load. It crosses the same congestion window as a
// source symbol: coded.QUICCarrier runs on QUIC datagrams, whose congestion
// controller, pacer and loss detector all apply, and ErasureSender.bandwidth
// caps that window at this lane's share of the endpoint pair's measured
// bottleneck so that lanes cannot compound. Raising this estimate therefore
// changes how a fixed window is spent -- more parity, less payload -- and
// never how much is put on the wire.
//
// What made the floor look necessary was that the window was not fixed in
// practice: the bandwidth estimate behind it could be latched at a burst rate
// for the better part of an hour, so the cap was computed from a figure the
// path had never sustained and never bound. That is a defect in the estimate
// rather than a reason to under-size a code, and it is fixed in the filter.
//
// So the classification has no consumer left here, and the number that is
// actually measurable is the one used.
//
// The rate is the one that delivers a block soonest, not one that meets a
// residual target. A target cannot be checked -- the sender never observes the
// residual it chose -- and it is the wrong question anyway: parity always
// costs wire and only ever buys latency, so what decides how much to buy is
// what an unrepairable block costs, which reissueCost measures. That also
// makes the decision to send no parity at all fall out of the same arithmetic
// instead of needing a threshold constant.
func Choose(s lossmodel.Snapshot, p Params) Plan {
	loss := s.Loss
	if loss <= 0 {
		return Plan{Why: "no erasure measured on the sending direction"}
	}
	if !(loss < 1) {
		// Written as a negation so it also refuses NaN, which passes every
		// threshold it is compared against.
		//
		// A rate of one says nothing arrives, and no code repairs that. Every
		// honest loss rate is a count of losses over a count of trials and so
		// cannot reach one here, which makes this an accounting failure rather
		// than a path: something was charged to the channel that the channel
		// did not do. Sizing for it would spend the lowest rate this searches
		// -- eight times the wire per delivered byte -- on the path that
		// produced the impossible figure, so refuse instead and leave the
		// counters saying why.
		return Plan{Why: "loss rate is not a measurement"}
	}
	if p.ShardBytes <= 0 {
		return Plan{Why: "no usable parameters"}
	}

	n := p.blockShards()
	burst := p.effectiveBurst(s)
	arrival := 1 - loss

	// A burst that takes several shards of the same block at once is one
	// erasure event, not several independent ones, so the block carries fewer
	// independent trials than it has shards. Sizing the code as if every shard
	// were an independent trial is the error that would certify a rate the
	// path defeats.
	trials := int(math.Round(float64(n) / burst))
	if trials < 1 {
		trials = 1
	}

	// Walk every rate the block can carry and keep the one that delivers its
	// data soonest. The tail is monotone in k but the objective is not: parity
	// buys a smaller residual and costs wire, so the best rate is an interior
	// point rather than the first k past a threshold.
	best := Plan{LossCoded: loss, EffectiveBurst: burst}
	bestDelivered := 0.0
	for k := n; k >= 1; k-- {
		if float64(k)/float64(n) < minRate {
			break
		}
		residual, ok := residualFor(k, trials, burst, arrival)
		if !ok {
			continue
		}
		delivered := deliveredPerSymbolTime(k, n, residual, p.reissueCost(k))
		if delivered <= bestDelivered {
			continue
		}
		bestDelivered = delivered
		best.K, best.N = k, n
		best.Rate = float64(k) / float64(n)
		best.Residual = residual
	}
	if best.N == 0 {
		best.Why = "no code rate is long enough for this block"
		return best
	}
	if best.Residual >= codeStillRepairs {
		// Every rate this channel allows loses the block more often than it
		// keeps it, so the search has been comparing ways of failing. Sizing
		// one of them would spend the lowest rate minRate permits on a channel
		// that defeats it; saying so is the more useful answer, and it is the
		// same judgement minRate already makes about the wire.
		best.Why = "no code rate this channel allows repairs a block more often than not"
		return best
	}
	if best.K >= best.N {
		// The whole block carrying data delivered soonest, so every repair
		// this channel could have earned cost more wire than the stall it
		// would have saved. Reported rather than coded, because an uncoded
		// path is a decision this made and not a case it failed to consider.
		best.Code = false
		best.Why = "parity costs more wire than the stall it saves"
		return best
	}
	best.Code = true
	best.Why = "sized for the soonest delivery"
	return best
}

// deliveredPerSymbolTime is data shards delivered per symbol-time, counting
// what a block that cannot be repaired costs before its data arrives.
//
// This is the objective, and it is a time rather than a ratio because parity
// never pays for itself in wire: sending k of n shards as data always carries
// less data per byte than sending all n, and a retransmission recovers the
// difference eventually. What parity buys is the eventually. Dividing by the
// stall makes the two comparable, so the arithmetic can decide how much of the
// budget to spend rather than being told by a residual target.
//
// The stall is charged for the re-issues it actually takes, not for one. A
// re-issue crosses the same channel and can be erased in its turn, so a block
// that fails with probability r expects r/(1-r) further round trips rather
// than a single one. At a small residual the difference is nothing; at a large
// one it is the whole answer, because charging a single round trip makes an
// uncoded block on a 72% erasure channel look cheaper than any code -- it
// quietly assumes the one retransmission gets through.
func deliveredPerSymbolTime(k, n int, residual, reissue float64) float64 {
	if !(residual < 1) {
		return 0
	}
	return float64(k) / (float64(n) + residual/(1-residual)*reissue)
}

// reissueCost is what a block the code cannot repair costs, in symbol-times,
// before the data it carried is delivered: one round trip, expressed as the
// symbols this flow could have sent while it waited.
//
// It is the round trip for a bulk flow as well as an interactive one, and that
// is a claim rather than an identity. A bulk flow does keep the pipe full
// while the re-issue is in flight, so it is tempting to charge a residual
// block only the wire to carry it again -- but the gap still stalls
// reassembly, and on a path with this much delay the receive window fills
// behind it long before the re-issue lands. Charging only the wire makes the
// arithmetic decline to code at any loss rate; charging the whole round trip
// makes it code at almost every loss rate. The truth is between them and
// depends on how much of the window the stall actually holds, which is not
// modelled here.
//
// This picks the round trip because removing a round trip from a gap is what
// this transport exists to do, and because under-coding is what the incident
// this design answers was made of. It is the least defensible number in the
// objective and the pathsim cases in docs/CONTROL-REDESIGN.md are what should
// settle it.
func (p Params) reissueCost(k int) float64 {
	if p.RoundTrip <= 0 || p.RateBytesPerSec <= 0 || p.ShardBytes <= 0 {
		return float64(k)
	}
	return p.RoundTrip.Seconds() * p.RateBytesPerSec / float64(p.ShardBytes)
}

// ShardsFor answers Choose's question in the other direction: given how many
// data shards a block actually holds, the total length that delivers them
// soonest.
//
// A block is not always the length the plan assumed. A flow that flushes a
// short write seals a block of one or two shards, and sizing that block by the
// plan's rate would be wrong in both directions -- it would send the plan's
// whole block length for a few bytes, and it would still be too weak, because
// a short block has no room for the binomial to average out. Repairing one
// shard at 42% loss needs eight copies before the stall it saves is worth the
// wire, and that is the honest answer rather than the rate the long blocks use.
func ShardsFor(k int, s lossmodel.Snapshot, p Params) (int, bool) {
	if k < 1 {
		return 0, false
	}
	loss := s.Loss
	if loss <= 0 || !(loss < 1) {
		return k, false
	}
	burst := p.effectiveBurst(s)
	arrival := 1 - loss
	reissue := p.reissueCost(k)
	bestN, bestDelivered := 0, 0.0
	for n := k; n <= MaxShards; n++ {
		if float64(k)/float64(n) < minRate {
			break
		}
		trials := int(math.Round(float64(n) / burst))
		if trials < 1 {
			trials = 1
		}
		residual, ok := residualFor(k, trials, burst, arrival)
		if !ok {
			continue
		}
		if delivered := deliveredPerSymbolTime(k, n, residual, reissue); delivered > bestDelivered {
			bestN, bestDelivered = n, delivered
		}
		if k <= shortBlockSymbols && residual <= shortBlockResidual {
			// See shortBlockSymbols. n ascends, so this is the shortest code
			// that reaches the target; take it unless the objective above
			// already asked for more.
			if n > bestN {
				bestN = n
			}
			break
		}
	}
	if bestN > k {
		return bestN, true
	}
	if bestN == k {
		return k, false
	}
	return 0, false
}

// WindowRate is how many repair symbols each source symbol earns on a sliding
// window of the given capacity, for the target residual.
//
// It is not ShardsFor's answer, and the difference is not small. ShardsFor
// sizes a block, where the only transmissions that can repair an erasure are
// the ones in its own block; on a window they chain, because a repair that
// resolves a neighbouring symbol frees an equation that covers this one, and
// that equation may come from a window this symbol was never in. The code
// therefore behaves like a block several times the window's length, and asking
// for a block's parity over a window's length buys a residual far below the
// one that was asked for -- at 42% erasure and a window of 64, 1.20 repairs
// per symbol where 0.98 was enough, which is a fifth of the wire.
//
// The multiple is measured rather than derived: the chaining depends on how
// the decoder retains equations, which is a property of this implementation
// and not of the arithmetic. TestTheWindowRateIsWhatTheWindowNeeds holds it to
// what the code actually achieves.
//
// The block's shard limit does not apply here either. A block of 256 shards is
// all GF(256) has distinct generator rows for, so ShardsFor gives up above it
// and reports that no code will do -- but a window's coefficients are drawn per
// repair over at most a window's symbols, so the repairs are unbounded and a
// wide window is exactly where the code is cheapest.
func WindowRate(capacity int, s lossmodel.Snapshot, p Params) float64 {
	if capacity < 1 {
		return 0
	}
	loss := s.Loss
	if loss <= 0 || !(loss < 1) {
		return 0
	}
	arrival := 1 - loss
	effective := int(float64(capacity) * windowChaining)
	if effective < 1 {
		return 0
	}
	reissue := p.reissueCost(effective)
	// The objective is not monotone in the number of transmissions -- the tail
	// falls while the wire cost rises -- so the answer is neither a bisection
	// nor the end of a walk. It is cheap to find anyway: the search is bounded
	// by maxWindowRate, and coding() only re-runs this every codingTTL, so a
	// coarse sweep followed by a local refinement costs far less than the
	// estimate feeding it is worth.
	hi := int(float64(effective) * maxWindowRate)
	if hi <= effective {
		return 0
	}
	deliveredAt := func(total int) float64 {
		return deliveredPerSymbolTime(effective, total, binomialTailBelow(total, arrival, effective), reissue)
	}
	const sweep = 32
	bestTotal, bestDelivered := effective, deliveredAt(effective)
	step := (hi - effective) / sweep
	if step < 1 {
		step = 1
	}
	for total := effective + step; total <= hi; total += step {
		if delivered := deliveredAt(total); delivered > bestDelivered {
			bestTotal, bestDelivered = total, delivered
		}
	}
	lo := max(effective, bestTotal-step)
	for total := lo; total <= min(hi, bestTotal+step); total++ {
		if delivered := deliveredAt(total); delivered > bestDelivered {
			bestTotal, bestDelivered = total, delivered
		}
	}
	return float64(bestTotal-effective) / float64(effective)
}

const (
	// windowChaining is how many windows' worth of symbols one window's repairs
	// effectively code over, once equations that resolve neighbouring symbols
	// are counted. Measured, not derived.
	windowChaining = 2.5
	// maxWindowRate stops the search where the channel is no longer one this
	// transport can use, matching minRate's judgement for blocks.
	maxWindowRate = 1 / minRate
)

// residualFor is the probability that a block of k data shards cannot be
// repaired, given how many independent erasure events its total length carries.
// It reports ok=false when the block is too short to hold k shards' worth of
// events at all.
func residualFor(k, trials int, burst, arrival float64) (float64, bool) {
	// In units of erasure events rather than shards.
	need := int(math.Ceil(float64(k) / burst))
	if need > trials {
		return 1, false
	}
	return binomialTailBelow(trials, arrival, need), true
}

// blockShards picks n from the latency the flow can afford. Coding's whole
// latency advantage is that a repair costs a block rather than a round trip, so
// a block is never allowed to take longer than a round trip; an interactive
// flow gets a tighter bound still.
func (p Params) blockShards() int {
	n := MaxShards
	budget := p.RoundTrip
	if p.Class == ClassInteractive {
		// A quarter of the round trip: long enough that the code has shape,
		// short enough that a repaired packet still beats a retransmission by
		// a wide margin.
		budget = p.RoundTrip / 4
	}
	if budget > 0 && p.RateBytesPerSec > 0 {
		fits := int(budget.Seconds() * p.RateBytesPerSec / float64(p.ShardBytes))
		if fits < n {
			n = fits
		}
	}
	if n < minShards {
		n = minShards
	}
	if n > MaxShards {
		n = MaxShards
	}
	return n
}

// effectiveBurst is the mean loss burst as the block sees it.
//
// Correlation is answered by lowering the code rate, not by spreading a
// block's shards across others. Interleaving is the alternative answer, and it
// trades latency for rate: a block is not complete until every block it was
// interleaved with has been sent, which gives back exactly what coding was
// bought for. Nothing measured on this path asks for that trade -- below the
// knee the channel is memoryless, so there is no correlation to undo, and
// above it the right response is to send less rather than to code harder.
func (p Params) effectiveBurst(s lossmodel.Snapshot) float64 {
	burst := s.BurstFactor
	if burst < 1 || math.IsNaN(burst) {
		burst = 1
	}
	return burst
}

// binomialTailBelow returns P(X < k) for X ~ Binomial(n, q), computed in log
// space so a long block's factorials do not overflow.
func binomialTailBelow(n int, q float64, k int) float64 {
	if k <= 0 {
		return 0
	}
	if k > n {
		return 1
	}
	if q <= 0 {
		return 1
	}
	if q >= 1 {
		return 0
	}
	logQ, logP := math.Log(q), math.Log1p(-q)
	logN1, _ := math.Lgamma(float64(n) + 1)
	total := 0.0
	for i := 0; i < k; i++ {
		logI1, _ := math.Lgamma(float64(i) + 1)
		logNI1, _ := math.Lgamma(float64(n-i) + 1)
		total += math.Exp(logN1 - logI1 - logNI1 + float64(i)*logQ + float64(n-i)*logP)
	}
	if total > 1 {
		return 1
	}
	return total
}

// Overhead is the bytes on the wire per byte of data this plan delivers, which
// is what a code rate means to the flow paying for it.
func (p Plan) Overhead() float64 {
	if !p.Code || p.K == 0 {
		return 1
	}
	return float64(p.N) / float64(p.K)
}
