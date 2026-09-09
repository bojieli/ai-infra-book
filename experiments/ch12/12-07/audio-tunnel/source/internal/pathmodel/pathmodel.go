// Package pathmodel is the one place a path is measured.
//
// Everything that adapts to this project's path needs the same three
// quantities -- how much it erases, how much of that is congestion, and how
// fast it is -- and each of them used to be estimated separately by whatever
// needed it. A congestion controller measured the erasure floor from the
// packets it sent; an erasure code measured it again from the shards it
// received; a second lane measured it a third time from scratch. Three
// estimates of one number, each wrong until it converged, and each converging
// on its own traffic.
//
// The cost is not only duplication. An estimate that starts at zero is an
// estimate that says "this path is clean", and a code sized by it carries no
// parity. A sender that runs ahead of its own feedback therefore commits its
// whole window to the wire uncoded -- measured, that is the difference between
// 1.03 and 1.74 Mbit/s across the emulated channel, and it is not a tuning
// error but a consequence of asking each component to learn the path alone.
//
// So the path is measured once, per endpoint pair, and read by everyone. The
// congestion controller contributes what it learns from its own
// acknowledgements, which is the erasure rate of the direction it sends into;
// that is exactly the number an erasure code needs and would otherwise wait
// for the peer to tell it.
package pathmodel

import (
	"sync"
	"time"
)

// PathModel is what everything sending to one endpoint pair has in common,
// which on this project's path is almost everything.
//
// Lanes were measured to be worth less than nothing here: one lane delivers
// about 11 Mbit/s live and four deliver about 8. The open-loop probe explains
// why -- the bottleneck is per endpoint pair rather than per 4-tuple, so lanes
// cannot multiply the share -- but it does not explain the loss, and the loss
// is what this type is for.
//
// Two things go wrong when each lane decides alone. Each measures the erasure
// floor from its own packets, so four lanes spend four times as long reaching a
// usable estimate and then disagree; and each discovers the bottleneck from its
// own delivered rate, so each probes above its own share and the aggregate
// overshoots by however many lanes there are. Past the knee the path's loss
// stops being memoryless, which costs more than the lanes were ever going to
// win.
//
// Sharing fixes both. The floor is pooled, so it converges on the sample count
// of every lane together. The bottleneck is discovered once for the endpoint
// pair, and each lane is capped at its share of it, so the aggregate on the
// wire is what one sender would have put there.
//
// Membership is by activity rather than registration. A congestion controller
// has no close hook to deregister in, and a lane that has stopped reporting has
// stopped sending, which is the same thing for this purpose.
type PathModel struct {
	mu      sync.Mutex
	members map[Member]*report
	// knowledge belongs to the path, not to whichever connection happened to
	// measure it. Members expire because they stop consuming a bottleneck
	// share; letting their floor and minimum RTT expire at the same time made a
	// quiet path become "unknown" five seconds after its prewarm. Forget is the
	// lifecycle boundary for this state.
	knowledge pathKnowledge
	// aggregate is a windowed maximum of the summed delivered rate, which is
	// the endpoint pair's bottleneck as measured from this side.
	aggregate []bandwidthSample
}

type pathKnowledge struct {
	erasure         float64
	burst           float64
	erasureKnown    bool
	observedSamples float64
	roundTrip       time.Duration
}

// Member identifies one contributor within a model. Callers allocate these
// monotonically; uniqueness among live owners is all membership needs.
type Member uint64

type report struct {
	erasure   float64
	burst     float64
	observed  float64
	delivered float64
	roundTrip time.Duration
	at        time.Time
}

// Observation is what one contributor has measured about the direction it
// sends into.
//
// Floor and Erasure are the same channel seen with opposite bias, and they are
// carried separately because their consumers fail in opposite directions.
// A congestion controller must under-estimate erasure: believing loss is
// congestion makes it slow down, which is safe. A code must not: believing
// loss is congestion makes it send no parity into a channel that is erasing,
// which is what docs/CONTROL-REDESIGN.md was written about. One number cannot
// serve both, so the model pools both and each consumer reads the one whose
// error it can survive.
type Observation struct {
	// Erasure is the loss rate this contributor measured, unclassified, and
	// BurstFactor is how much of it arrived in runs. Both are what a code has
	// to be sized against; neither is safe to pace from.
	Erasure     float64
	BurstFactor float64
	// ObservedSamples records measurement progress even while the floor is
	// still unknown, which is what distinguishes a measured clean path from an
	// unmeasured one.
	ObservedSamples float64
	// Delivered is this contributor's delivered rate in bytes per second, and
	// RoundTrip the smallest round trip it has seen.
	Delivered float64
	RoundTrip time.Duration
}

// State is what an endpoint pair has been measured to do, from the point of
// view of one contributor.
type State struct {
	// Erasure is the loss rate the contributors measured on the direction they
	// send into, pooled and unclassified, and BurstFactor is how much of it
	// arrived in runs. This is what a code is sized against.
	Erasure     float64
	BurstFactor float64
	// ObservedSamples is how many packet outcomes contributors have measured,
	// including outcomes not yet sufficient to establish a non-zero erasure
	// floor. It distinguishes a measured clean path from an unmeasured one
	// without giving an untrusted zero any weight in Floor.
	ObservedSamples float64
	// Share is this contributor's allowance of the bottleneck in bytes per
	// second. Zero means the contributor must not cap itself -- either because
	// the bottleneck is not yet known, or because it is the only one here and
	// so has nothing to compound with.
	//
	// A share is deliberately larger than an even split. The bottleneck is
	// measured from what the contributors deliver, and they deliver what this
	// number lets them, so a share with no headroom is a cap computed from its
	// own effect: it can be held, never exceeded, and any dip in delivery
	// lowers it permanently. See shareProbeGain.
	Share float64
	// Seed is the rate a contributor joining now should start from, which is
	// its expected portion of the bottleneck. Unlike Share it is never a
	// ceiling -- it exists so a replacement lane does not rediscover a path
	// its siblings already measured.
	Seed float64
	// RoundTrip is the path's minimum round trip, which is the smallest any
	// lane has seen: a larger one is that lane's queueing, not the path.
	RoundTrip time.Duration
}

type bandwidthSample struct {
	rate float64
	at   time.Time
}

const (
	// memberIdle is how long a contributor may go without reporting before it
	// stops counting. It is several round trips on a long-haul path, so one
	// that is merely quiet is not evicted and made to rediscover the path.
	memberIdle = 5 * time.Second
	// bottleneckWindow is how long a delivered-rate sample stands. Long enough
	// to survive a probe cycle, short enough that a path which genuinely
	// narrowed is believed within a few seconds.
	bottleneckWindow = 10 * time.Second
	// shareProbeGain is the headroom a share leaves above an even split.
	//
	// It is BBR's own probe gain, and it is here for the same reason BBR has
	// it: an estimate of a bottleneck can only grow if something is allowed to
	// send above it. The bottleneck here is measured from what the members
	// deliver, so without this factor the cap is derived from the traffic the
	// cap itself limits -- a loop with one stable point and a downward
	// ratchet. Any interval where a member is application-limited lowers the
	// windowed maximum, which lowers every share, which lowers what can be
	// delivered next, and the path is never re-measured upward.
	//
	// With the gain, the members together may put 1.25x the measured
	// bottleneck on the wire, which is what one BBR sender would have done
	// probing on its own -- which is exactly the property the share exists to
	// preserve.
	shareProbeGain = 1.25
)

// NewPathModel returns an empty model. Callers normally want SharedPath.
func NewPathModel() *PathModel {
	return &PathModel{members: make(map[Member]*report)}
}

// Report records what one lane currently believes, and returns what the
// endpoint pair believes. floorSamples weights only established floor
// evidence; observedSamples records measurement progress even while the floor
// is still unknown.
func (m *PathModel) Report(member Member, o Observation) State {
	// A nil model reports nothing rather than panicking. This matters because
	// consumers now hold the Model interface: a nil *PathModel stored in an
	// interface is not equal to nil, so the caller's own guard does not fire
	// and what would have been an obvious nil-pointer dereference becomes a
	// crash inside the transport instead.
	if m == nil {
		return State{}
	}
	now := time.Now()
	m.mu.Lock()
	defer m.mu.Unlock()

	entry, ok := m.members[member]
	if !ok {
		entry = &report{}
		m.members[member] = entry
	}
	entry.erasure, entry.burst = o.Erasure, o.BurstFactor
	entry.observed, entry.delivered, entry.at = o.ObservedSamples, o.Delivered, now
	if o.RoundTrip > 0 {
		entry.roundTrip = o.RoundTrip
	}

	var state State
	var observed, sum float64
	var erasureWeighted, burstWeighted float64
	live := 0
	for key, other := range m.members {
		if now.Sub(other.at) > memberIdle {
			delete(m.members, key)
			continue
		}
		live++
		sum += other.delivered
		// A lane with few samples should not move the pooled estimate much,
		// which is also what lets a new lane join without disturbing it.
		erasureWeighted += other.erasure * other.observed
		burstWeighted += other.burst * other.observed
		observed += other.observed
		if other.roundTrip > 0 && (state.RoundTrip == 0 || other.roundTrip < state.RoundTrip) {
			state.RoundTrip = other.roundTrip
		}
	}
	if observed > 0 {
		state.Erasure = erasureWeighted / observed
		state.BurstFactor = burstWeighted / observed
		m.knowledge.erasure, m.knowledge.burst = state.Erasure, state.BurstFactor
		m.knowledge.erasureKnown = true
	} else if m.knowledge.erasureKnown {
		state.Erasure, state.BurstFactor = m.knowledge.erasure, m.knowledge.burst
	}
	if state.BurstFactor < 1 {
		// A burst factor below one is not a channel, it is an unmeasured or
		// half-filled report. Independent loss is the assumption that makes a
		// code weakest, so it is the safe one to fall back to.
		state.BurstFactor = 1
	}
	if observed > m.knowledge.observedSamples {
		m.knowledge.observedSamples = observed
	}
	state.ObservedSamples = m.knowledge.observedSamples
	if state.RoundTrip > 0 && (m.knowledge.roundTrip == 0 || state.RoundTrip < m.knowledge.roundTrip) {
		m.knowledge.roundTrip = state.RoundTrip
	} else if state.RoundTrip == 0 {
		state.RoundTrip = m.knowledge.roundTrip
	}

	if sum > 0 {
		m.aggregate = append(m.aggregate, bandwidthSample{rate: sum, at: now})
	}
	bottleneck := 0.0
	kept := m.aggregate[:0]
	for _, sample := range m.aggregate {
		if now.Sub(sample.at) > bottleneckWindow {
			continue
		}
		kept = append(kept, sample)
		if sample.rate > bottleneck {
			bottleneck = sample.rate
		}
	}
	m.aggregate = kept

	if live > 0 && bottleneck > 0 {
		state.Seed = bottleneck / float64(live)
		// A lone member has nothing to compound with, so there is nothing for
		// a cap to protect and everything for it to break: its share would be
		// the whole bottleneck, the bottleneck is the maximum of what it has
		// recently delivered, and a sender held at its own recent maximum can
		// never probe past it. Measured, that is a transport that runs at line
		// rate and then collapses to a fiftieth of it for the rest of the
		// process's life.
		if live > 1 {
			state.Share = shareProbeGain * state.Seed
		}
	}
	return state
}

// Current is what the model already knows, without contributing to it: the
// pooled erasure floor and the share a lane joining now would be given.
//
// A lane that starts from nothing has to rediscover a path its siblings
// already measured, and on a channel that erases 40% of packets that discovery
// is expensive -- it is the same ramp that costs a loss-based controller the
// path in the first place. A replacement lane, opened because its predecessor
// died, would pay it every time.
func (m *PathModel) Current() State {
	if m == nil {
		return State{}
	}
	now := time.Now()
	m.mu.Lock()
	defer m.mu.Unlock()
	var state State
	var observed, bottleneck float64
	var erasureWeighted, burstWeighted float64
	live := 0
	for key, entry := range m.members {
		if now.Sub(entry.at) > memberIdle {
			delete(m.members, key)
			continue
		}
		live++
		erasureWeighted += entry.erasure * entry.observed
		burstWeighted += entry.burst * entry.observed
		observed += entry.observed
		if entry.roundTrip > 0 && (state.RoundTrip == 0 || entry.roundTrip < state.RoundTrip) {
			state.RoundTrip = entry.roundTrip
		}
	}
	if observed > 0 {
		state.Erasure = erasureWeighted / observed
		state.BurstFactor = burstWeighted / observed
		m.knowledge.erasure, m.knowledge.burst = state.Erasure, state.BurstFactor
		m.knowledge.erasureKnown = true
	} else if m.knowledge.erasureKnown {
		state.Erasure, state.BurstFactor = m.knowledge.erasure, m.knowledge.burst
	}
	if state.BurstFactor < 1 {
		// A burst factor below one is not a channel, it is an unmeasured or
		// half-filled report. Independent loss is the assumption that makes a
		// code weakest, so it is the safe one to fall back to.
		state.BurstFactor = 1
	}
	if observed > m.knowledge.observedSamples {
		m.knowledge.observedSamples = observed
	}
	state.ObservedSamples = m.knowledge.observedSamples
	if state.RoundTrip > 0 && (m.knowledge.roundTrip == 0 || state.RoundTrip < m.knowledge.roundTrip) {
		m.knowledge.roundTrip = state.RoundTrip
	} else if state.RoundTrip == 0 {
		state.RoundTrip = m.knowledge.roundTrip
	}
	for _, sample := range m.aggregate {
		if now.Sub(sample.at) <= bottleneckWindow && sample.rate > bottleneck {
			bottleneck = sample.rate
		}
	}
	if bottleneck > 0 {
		// The joining lane counts too, or the first thing it does is take a
		// share sized for a path with one fewer lane on it.
		state.Seed = bottleneck / float64(live+1)
		// Only a lane that will actually share the path takes a ceiling with
		// it. A lane joining an empty model is alone, and capping it at what
		// the last occupant delivered is how a fresh connection inherits a
		// dead one's collapse.
		if live > 0 {
			state.Share = shareProbeGain * state.Seed
		}
	}
	return state
}

// Members is how many contributors are currently reporting.
func (m *PathModel) Members() int {
	if m == nil {
		return 0
	}
	now := time.Now()
	m.mu.Lock()
	defer m.mu.Unlock()
	live := 0
	for key, entry := range m.members {
		if now.Sub(entry.at) > memberIdle {
			delete(m.members, key)
			continue
		}
		live++
	}
	return live
}

// shared holds one model per endpoint pair. The map only ever grows by the
// number of distinct peers, and an idle model is a few words, so there is
// nothing to reclaim that would be worth the lifetime tracking.
var (
	sharedMu sync.Mutex
	shared   = make(map[string]*PathModel)
)

// Forget drops what is known about a path.
//
// A path that is gone should not be remembered indefinitely: the registry only
// grows by the number of distinct uplinks a machine has used, which is small,
// but a measurement kept past the network it describes is a confident wrong
// answer waiting to be read.
func Forget(key string) {
	sharedMu.Lock()
	defer sharedMu.Unlock()
	delete(shared, key)
}

// Reset drops every model.
//
// It exists for tests, and it exists because of what a path key is. A model is
// keyed by the endpoint pair, which is the right key for a real network and
// the wrong one for a process where every pair is loopback to loopback: two
// tests that could not affect each other on a real path share one model here,
// and the second inherits whatever the first measured. That has produced
// failures that look like flakes and are not -- a test whose channel erases
// 42% of packets, sizing its code from a floor a previous test measured on a
// clean one, and stalling until its deadline.
//
// A test that brings up its own endpoints starts from nothing by calling this.
func Reset() {
	sharedMu.Lock()
	defer sharedMu.Unlock()
	clear(shared)
}

// Live reports the model for every endpoint pair this process is currently
// measuring.
//
// It exists because the measured erasure is what a code is sized from and is
// not exported as a metric, so a test that wants to know whether the stack
// noticed a channel change has no other way to ask. Callers that know their
// peer should use Shared; this is for the ones observing from outside.
func Live() []*PathModel {
	sharedMu.Lock()
	defer sharedMu.Unlock()
	models := make([]*PathModel, 0, len(shared))
	for _, model := range shared {
		models = append(models, model)
	}
	return models
}

// Shared returns the model for an endpoint pair, creating it on first use.
// The key should identify the peer rather than the connection: lanes to the
// same peer are exactly the ones that must share.
func Shared(key string) *PathModel {
	sharedMu.Lock()
	defer sharedMu.Unlock()
	model, ok := shared[key]
	if !ok {
		model = NewPathModel()
		shared[key] = model
	}
	return model
}
