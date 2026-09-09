// Package lossmodel decides what a lost packet means.
//
// On a long-haul path loss is not one process. Measured on the China-US path
// this project targets (docs/PATH-CHARACTER-20260813.md), about 42% of packets
// are dropped at 1 Mbit/s as readily as at 12, and ICMP loses 37% at five
// packets per second: a property of the channel that no amount of backing off
// will reduce. Above the bottleneck a second process appears whose losses
// cluster into runs, and that one is congestion.
//
// A transport that cannot tell them apart fails twice over. Reading the
// channel as congestion, it collapses to the Mathis limit -- about 30 kbit/s
// on this path, which is what plain TCP achieves there. Reading congestion as
// the channel, it answers an overflowing queue by adding parity to it.
//
// The separation is made from the only evidence a receiver has: which sequence
// numbers arrived, and in what order. Two statistics do the work.
//
// The first is P(loss | previous arrived). A memoryless channel drops each
// packet independently, so that conditional equals the overall loss rate; a
// queue drops runs, so it does not. The second is the mean loss-burst length
// relative to the value a memoryless channel would produce, which is
// BurstFactor here. It is one for an independent channel and larger when
// losses cluster, and it is exactly the factor by which correlation shortens
// the effective length of an erasure-coded block.
//
// Which part of the loss is congestion is then a min-filter, in the same
// spirit as BBR's windowed minimum round trip: the channel's erasure rate is
// the lowest loss seen recently, because the channel does not stop being lossy
// when the queue drains, and everything above that floor is what the sender
// caused and can remove.
package lossmodel

import "math"

// DefaultRoundSamples is how many packets make up one round of the loss floor
// filter. A round has to be long enough that its loss rate is a usable
// estimate -- at 42% loss, 2000 packets put the standard error near one
// percentage point -- and short enough that several rounds fit inside one
// congestion episode.
const DefaultRoundSamples = 2000

// DefaultRounds is how many rounds the floor filter remembers. The floor must
// outlive a congestion episode or the episode raises the floor and hides
// itself.
const DefaultRounds = 8

// DefaultReorderTolerance is how far past a gap the estimator waits before
// calling it a loss. A packet that arrives later than this is counted as
// reordered rather than retroactively un-lost, so the Markov statistics are
// never rewritten after the fact.
const DefaultReorderTolerance = 8

// decay is applied to the Markov counters at each round boundary. It gives an
// effective memory of about DefaultRoundSamples/(1-decay) packets, so the
// statistics follow a regime change instead of averaging across one.
const decay = 0.75

// ringSize bounds the sequence numbers held undecided at once. It only has to
// exceed the reorder tolerance; the extra room means a burst of reordering
// costs accuracy rather than correctness.
const ringSize = 1024

// Config tunes an Estimator. The zero value selects the defaults.
type Config struct {
	RoundSamples     int
	Rounds           int
	ReorderTolerance int
}

func (c Config) withDefaults() Config {
	if c.RoundSamples <= 0 {
		c.RoundSamples = DefaultRoundSamples
	}
	if c.Rounds <= 0 {
		c.Rounds = DefaultRounds
	}
	if c.ReorderTolerance <= 0 {
		c.ReorderTolerance = DefaultReorderTolerance
	}
	if c.ReorderTolerance >= ringSize {
		c.ReorderTolerance = ringSize - 1
	}
	return c
}

// Estimator consumes the sequence numbers that arrive on one path, in the
// order they arrive, and reports what kind of loss the path is applying. It is
// not safe for concurrent use; a lane owns one.
type Estimator struct {
	cfg Config

	arrived [ringSize]bool
	// next is the lowest sequence number not yet decided, and highest is the
	// largest ever seen. A sequence is decided once highest has moved a
	// reorder tolerance past it.
	next    uint64
	highest uint64
	started bool
	// discontinuities counts the arrivals whose sequence number was too far
	// ahead to be a gap in this numbering. On a working path it is zero.
	discontinuities uint64

	// The Markov counters are floating point because they decay: a regime
	// change has to be able to overwrite the history rather than be averaged
	// into it.
	samples          float64
	losses           float64
	fromArrival      float64
	lossAfterArrival float64
	fromLoss         float64
	arrivalAfterLoss float64

	prevLost bool
	havePrev bool

	roundSamples int
	roundLosses  int
	rounds       []float64
	roundAt      int

	reordered uint64
	decided   uint64
}

// New returns an Estimator. The zero Config is the right choice unless a
// caller has measured a reason to differ.
func New(cfg Config) *Estimator {
	cfg = cfg.withDefaults()
	return &Estimator{cfg: cfg, rounds: make([]float64, 0, cfg.Rounds)}
}

// Observe records that the packet with this sequence number arrived. Losses
// are inferred from the gaps, so nothing has to be reported for them.
func (e *Estimator) Observe(seq uint64) {
	if !e.started {
		e.started = true
		e.next = seq
		e.highest = seq
		e.arrived[seq%ringSize] = true
		return
	}
	if seq < e.next {
		if e.decided > 0 || e.highest-seq >= ringSize {
			// Already decided. Counting it as an arrival now would mean
			// revising a transition that has already been folded into the
			// statistics, and a statistic that can be revised cannot be read
			// at any particular time.
			e.reordered++
			return
		}
		// Nothing has been decided yet, so the base is still just "the first
		// sequence number that happened to arrive". A path that reorders
		// delivers that out of order too, and starting one packet late would
		// charge the flow a loss it never had.
		e.next = seq
	}
	if seq > e.highest {
		e.highest = seq
	}
	// A jump larger than the ring means the undecided range no longer fits.
	// Decide from the bottom until it does, before marking, so this packet's
	// own slot is never one of the ones retired.
	//
	// How far that walks is the peer's to choose, though: the sequence number
	// comes off the wire, and one datagram naming a sequence 2^32 ahead used
	// to retire that many slots one at a time -- under the receiving path's
	// lock, fabricating a loss for each -- and never returned. So a gap past
	// what any real burst could be is a discontinuity in the numbering rather
	// than a measurement of it, and the estimator restarts from where it now
	// is instead of counting out the distance.
	if e.highest-e.next > maxDecidedPerArrival {
		e.restart(seq)
	}
	for e.highest-e.next >= ringSize {
		e.decide()
	}
	e.arrived[seq%ringSize] = true
	for e.highest-e.next >= uint64(e.cfg.ReorderTolerance) {
		e.decide()
	}
}

// ObserveOutcome records one packet fate when the transport already resolved
// it. Callers should use either Observe, when gaps are their only loss signal,
// or ObserveOutcome, when their acknowledgement API reports losses directly.
// The latter is essential for QUIC congestion callbacks: packet numbers
// overlap across encryption spaces and the public callback omits the space,
// so inferring gaps from those numbers fabricates loss.
func (e *Estimator) ObserveOutcome(arrived bool) {
	e.record(arrived)
}

// maxDecidedPerArrival bounds how many sequence numbers one arrival may
// retire. It is generous against anything a path does -- 8192 consecutive
// losses is a path that has stopped rather than one that is dropping -- and
// finite against anything a peer says.
const maxDecidedPerArrival = 8 * ringSize

// restart abandons the undecided window and begins again at seq. The two
// sides of a discontinuity are not one sequence space, so nothing is carried
// across: not the ring, and not the previous packet's fate, which is what the
// conditional loss probabilities are chained on.
func (e *Estimator) restart(seq uint64) {
	e.arrived = [ringSize]bool{}
	e.next, e.highest = seq, seq
	e.havePrev = false
	e.discontinuities++
}

// decide retires the lowest undecided sequence number.
func (e *Estimator) decide() {
	slot := e.next % ringSize
	arrived := e.arrived[slot]
	e.arrived[slot] = false
	e.next++
	e.record(arrived)
}

func (e *Estimator) record(arrived bool) {
	e.decided++

	e.samples++
	if !arrived {
		e.losses++
	}
	if e.havePrev {
		if e.prevLost {
			e.fromLoss++
			if arrived {
				e.arrivalAfterLoss++
			}
		} else {
			e.fromArrival++
			if !arrived {
				e.lossAfterArrival++
			}
		}
	}
	e.prevLost = !arrived
	e.havePrev = true

	e.roundSamples++
	if !arrived {
		e.roundLosses++
	}
	if e.roundSamples >= e.cfg.RoundSamples {
		e.closeRound()
	}
}

func (e *Estimator) closeRound() {
	loss := float64(e.roundLosses) / float64(e.roundSamples)
	if len(e.rounds) < e.cfg.Rounds {
		e.rounds = append(e.rounds, loss)
	} else {
		e.rounds[e.roundAt] = loss
		e.roundAt = (e.roundAt + 1) % e.cfg.Rounds
	}
	e.roundSamples, e.roundLosses = 0, 0

	e.samples *= decay
	e.losses *= decay
	e.fromArrival *= decay
	e.lossAfterArrival *= decay
	e.fromLoss *= decay
	e.arrivalAfterLoss *= decay
}

// Snapshot is what the estimator currently believes about the path.
type Snapshot struct {
	// Samples is the effective number of decided packets behind these
	// figures. It is fractional because the counters decay.
	Samples float64
	// Loss is the overall drop probability.
	Loss float64
	// LossAfterArrival is P(loss | previous packet arrived), and
	// ArrivalAfterLoss is P(arrival | previous packet was lost). A memoryless
	// channel has the first equal to Loss and the second to 1-Loss.
	LossAfterArrival float64
	ArrivalAfterLoss float64
	// MeanBurst is the mean length of a run of consecutive losses.
	MeanBurst float64
	// BurstFactor is MeanBurst divided by the value a memoryless channel with
	// this loss rate would show. It is one for independent loss and larger
	// when losses cluster, and an erasure-coded block of n packets carries
	// only about n/BurstFactor independent erasure trials.
	BurstFactor float64
	// Memoryless reports whether the observed clustering is within sampling
	// noise of an independent channel. It is false until there are enough
	// samples to tell, so a caller that has just started sees "not yet known"
	// rather than a confident wrong answer.
	Memoryless bool
	// Floor is the lowest per-round loss rate seen in the filter window: the
	// erasure rate the channel imposes regardless of sending rate. Congestive
	// is what this instant's loss adds on top, and is the only part a sender
	// can remove by slowing down.
	Floor      float64
	Congestive float64
	// Recent is the loss rate over the round just closed, which is what
	// Congestive is measured against.
	Recent float64
	// Reordered counts packets that arrived after being declared lost.
	Reordered uint64
	// Decided counts sequence numbers resolved either way, ever.
	Decided uint64
}

// minMemorylessSamples is how many arrival-to-next transitions are needed
// before the independence test is allowed to answer. Below this the test's own
// noise exceeds the effect it is looking for.
const minMemorylessSamples = 200

// Discontinuities reports how many arrivals named a sequence too far ahead to
// be a gap in this numbering. It is zero on a working path, and a way to tell
// a path that is losing packets from a peer that is not numbering them.
func (e *Estimator) Discontinuities() uint64 { return e.discontinuities }

// probability keeps a reported rate a rate.
//
// Every quotient below is a count of outcomes over a count of trials, so each
// is in [0,1] by construction and this clamp should never bind. It is here
// because the consequence of it binding is silent and expensive: a rate above
// one reaching Choose sizes parity for a channel that delivers nothing, and
// parity is load on the path that produced the impossible number. A figure
// outside [0,1] is not evidence about a path, so it is not passed on as if it
// were.
func probability(v float64) float64 {
	if !(v > 0) {
		// Also catches NaN, which compares false against everything and would
		// otherwise travel through every threshold below untouched.
		return 0
	}
	if v > 1 {
		return 1
	}
	return v
}

// Snapshot reports the current estimate.
func (e *Estimator) Snapshot() Snapshot {
	s := Snapshot{Reordered: e.reordered, Decided: e.decided, Samples: e.samples}
	if e.samples <= 0 {
		return s
	}
	s.Loss = probability(e.losses / e.samples)
	if e.fromArrival > 0 {
		s.LossAfterArrival = probability(e.lossAfterArrival / e.fromArrival)
	}
	if e.fromLoss > 0 {
		s.ArrivalAfterLoss = probability(e.arrivalAfterLoss / e.fromLoss)
		if s.ArrivalAfterLoss > 0 {
			s.MeanBurst = 1 / s.ArrivalAfterLoss
		}
	}
	// A memoryless channel loses a mean run of 1/(1-Loss), so dividing by that
	// normalises the burst length to one for independent loss.
	if s.MeanBurst > 0 {
		s.BurstFactor = s.MeanBurst * (1 - s.Loss)
	}
	if s.BurstFactor < 1 {
		// Anti-correlated loss is not a regime this code models, and a factor
		// below one would shorten a block rather than lengthen it, which is
		// the unsafe direction.
		s.BurstFactor = 1
	}
	s.Memoryless = e.memoryless(s)

	s.Floor, s.Recent = e.floor()
	s.Floor, s.Recent = probability(s.Floor), probability(s.Recent)
	if s.Recent > s.Floor {
		s.Congestive = s.Recent - s.Floor
	}
	return s
}

// memoryless tests P(loss | previous arrived) against the overall loss rate.
// Under independence the two are equal, so their difference divided by its
// standard error is a standard normal, and three sigma is the threshold.
func (e *Estimator) memoryless(s Snapshot) bool {
	if e.fromArrival < minMemorylessSamples || s.Loss <= 0 || s.Loss >= 1 {
		return false
	}
	stderr := math.Sqrt(s.Loss * (1 - s.Loss) / e.fromArrival)
	if stderr <= 0 {
		return false
	}
	return math.Abs(s.LossAfterArrival-s.Loss)/stderr < 3
}

// floor returns the minimum and the most recent of the per-round loss rates.
// With no completed round it falls back to the round in progress, so a short
// flow still gets an answer rather than a zero that reads as a clean path.
func (e *Estimator) floor() (minimum, recent float64) {
	if len(e.rounds) == 0 {
		if e.roundSamples == 0 {
			return 0, 0
		}
		partial := float64(e.roundLosses) / float64(e.roundSamples)
		return partial, partial
	}
	minimum = e.rounds[0]
	for _, loss := range e.rounds[1:] {
		if loss < minimum {
			minimum = loss
		}
	}
	recent = e.rounds[len(e.rounds)-1]
	if len(e.rounds) == e.cfg.Rounds {
		recent = e.rounds[(e.roundAt+e.cfg.Rounds-1)%e.cfg.Rounds]
	}
	// A round in progress is more current than the last closed one, and once
	// it is a quarter full it is worth more than it costs in noise.
	if e.roundSamples*4 >= e.cfg.RoundSamples {
		recent = float64(e.roundLosses) / float64(e.roundSamples)
		if recent < minimum {
			minimum = recent
		}
	}
	return minimum, recent
}

// Pattern is the exact loss structure of a finished run. Analyze computes it
// offline, where every packet's fate is already known and nothing has to be
// inferred under a reorder tolerance; measurement tools use it to check what
// the online estimator concludes.
type Pattern struct {
	Total            int
	Lost             int
	Loss             float64
	LossAfterArrival float64
	ArrivalAfterLoss float64
	MeanBurst        float64
	BurstFactor      float64
	LongestBurst     int
	// Bursts maps a run length to the number of runs of that length.
	Bursts map[int]int
}

// Analyze computes the loss pattern of a run, given one boolean per sequence
// number in order.
func Analyze(arrived []bool) Pattern {
	p := Pattern{Total: len(arrived), Bursts: map[int]int{}}
	var fromArrival, lossAfterArrival, fromLoss, arrivalAfterLoss, run int
	for i, ok := range arrived {
		if !ok {
			p.Lost++
			run++
		} else if run > 0 {
			p.Bursts[run]++
			if run > p.LongestBurst {
				p.LongestBurst = run
			}
			run = 0
		}
		if i > 0 {
			if !arrived[i-1] {
				fromLoss++
				if ok {
					arrivalAfterLoss++
				}
			} else {
				fromArrival++
				if !ok {
					lossAfterArrival++
				}
			}
		}
	}
	if run > 0 {
		p.Bursts[run]++
		if run > p.LongestBurst {
			p.LongestBurst = run
		}
	}
	if p.Total > 0 {
		p.Loss = float64(p.Lost) / float64(p.Total)
	}
	if fromArrival > 0 {
		p.LossAfterArrival = float64(lossAfterArrival) / float64(fromArrival)
	}
	if fromLoss > 0 {
		p.ArrivalAfterLoss = float64(arrivalAfterLoss) / float64(fromLoss)
		p.MeanBurst = 1 / p.ArrivalAfterLoss
		p.BurstFactor = p.MeanBurst * (1 - p.Loss)
	}
	if p.BurstFactor < 1 {
		p.BurstFactor = 1
	}
	return p
}
