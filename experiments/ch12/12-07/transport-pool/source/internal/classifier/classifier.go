// Package classifier implements the transport-independent flow classifier.
// It intentionally uses observable flow statistics rather than HTTPS
// decryption or a TLS MITM.
package classifier

import (
	"sync"
	"time"
)

// Class is the scheduling class assigned to a flow.
type Class uint8

const (
	ClassNew Class = iota
	ClassInteractive
	ClassBulk
)

func (c Class) String() string {
	switch c {
	case ClassNew:
		return "new"
	case ClassInteractive:
		return "interactive"
	case ClassBulk:
		return "bulk"
	default:
		return "unknown"
	}
}

// Config controls transition thresholds. Values are deliberately explicit so
// deployments can tune them from measurements rather than hiding policy in
// the implementation.
type Config struct {
	NewBytes            uint64
	NewAge              time.Duration
	BulkBytes           uint64
	BulkRateBytesPerSec float64
	BulkMinimumAge      time.Duration
	InteractiveMaxRate  float64
	InteractiveIdleGap  time.Duration
	// BulkIdleGapVeto disqualifies a flow from ever becoming bulk once it has
	// been observed idle for this long, that many times. Zero disables the
	// veto, which is the behaviour every deployment had before it existed.
	//
	// Cumulative bytes cannot separate a bulk transfer from a series of
	// requests on one connection: three 300KB exchanges and a 900KB download
	// weigh the same, and the classifier latches on the first to cross the
	// threshold. Rate cannot separate them either, because a request burst is
	// briefly faster than the bulk floor, not slower.
	//
	// Duty cycle does separate them. A flow seeking throughput does not stop
	// asking for it; one that voluntarily goes quiet for a second and then
	// resumes is a caller waiting on something, whatever its byte total. The
	// veto is sticky for the same reason the bulk decision is sticky: the
	// evidence is about what kind of flow this is, and it does not expire when
	// the next burst starts.
	BulkIdleGapVeto time.Duration
	// BulkIdleGapVetoEpisodes is how many separate idle gaps it takes. Zero
	// means one, which is what the veto did when it was first written.
	//
	// One is too few, and the measurement that says so is that a transfer
	// stalling once anywhere in its first BulkBytes is vetoed for the rest of
	// its life. That window is the beginning of every transfer, which is where
	// a stall is most likely: a cold source, an authorization round trip, a
	// cache miss. On the datacenter profile a 240MB pull that paused for a
	// second-and-a-half at 12MB spent the remaining 228MB classified
	// interactive, which means coded and holding one lane.
	//
	// What separates the two cases is not whether a flow went quiet but
	// whether going quiet is what it does. Two separate episodes is the
	// smallest evidence that idling is a pattern rather than an event. It
	// still protects the case the veto exists for by a wide margin: a session
	// of a few hundred kilobytes per exchange needs roughly ninety exchanges
	// to reach this profile's byte floor, and it produces an episode on the
	// second one.
	BulkIdleGapVetoEpisodes int
}

func DefaultConfig() Config {
	return Config{
		NewBytes: 64 * 1024,
		NewAge:   3 * time.Second,
		// Demote after a modest byte budget so a path whose single-lane goodput
		// is below the bulk-rate floor can still unlock a pre-warmed independent
		// lane early in a large transfer. Interactive bursts are excluded
		// separately below, and hysteresis keeps a demoted flow in BULK once it
		// crosses this boundary.
		BulkBytes: 128 * 1024,
		// Retained as a configuration/documentation hook for future rate-aware
		// policies. The current classifier does not require a minimum rate: a
		// slow bulk transfer must still be able to unlock additional lanes.
		BulkRateBytesPerSec: 256 * 1024,
		BulkMinimumAge:      1 * time.Second,
		InteractiveMaxRate:  1 * 1024 * 1024,
		InteractiveIdleGap:  250 * time.Millisecond,
	}
}

// Observation contains statistics accumulated by the flow observer. Rates
// are bytes per second over a recent, implementation-defined window.
type Observation struct {
	BytesUp, BytesDown       uint64
	UpRate, DownRate         float64
	Age                      time.Duration
	SinceLastPayload         time.Duration
	Bidirectional            bool
	SmallBidirectionalBursts bool
}

// Classifier is stateful. Once a flow becomes bulk it remains bulk until it
// closes; this hysteresis prevents queue policy from flapping during a short
// idle gap in a large transfer.
// A Classifier is read and written from different goroutines: a flow observes
// its own traffic on whichever goroutine carried the bytes, and asks for the
// class wherever a scheduling decision is made. The class is one word, and one
// word is exactly the size of value a race detector finds and a reader gets
// half of.
type Classifier struct {
	// idleEpisodes counts the times this flow has gone quiet long enough to
	// count under BulkIdleGapVeto, and inIdle debounces a single gap that
	// several consecutive observations land inside. Counting observations
	// rather than episodes would make the veto a function of how often the
	// scheduler happened to tick during one pause.
	//
	// Once the count reaches the threshold the conclusion is sticky, in the
	// same way the bulk decision is: both are about what kind of flow this is
	// rather than about its present moment.
	idleEpisodes int
	inIdle       bool
	cfg          Config
	mu           sync.Mutex
	class        Class
}

// Declare sets the class a flow starts in, from something known before it
// carried anything: what produced it.
//
// It is a starting point rather than a promise. The classifier goes on judging
// the flow by what it does, so a process declared interactive that turns out
// to be moving a checkpoint is still demoted -- the declaration buys the first
// second, which is the window inference cannot cover and which a request
// shorter than it spends entirely inside.
//
// Declaring bulk is sticky in the same way an inferred demotion is, because it
// is the same conclusion reached earlier. Declaring interactive is not: it
// says where to begin, not where to stay.
func (c *Classifier) Declare(class Class) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.class == ClassBulk {
		return
	}
	switch class {
	case ClassInteractive, ClassBulk:
		c.class = class
	}
}

func New(cfg Config) *Classifier {
	if cfg.NewBytes == 0 || cfg.NewAge <= 0 || cfg.BulkBytes == 0 ||
		cfg.BulkRateBytesPerSec <= 0 || cfg.BulkMinimumAge <= 0 {
		cfg = DefaultConfig()
	}
	return &Classifier{cfg: cfg, class: ClassNew}
}

func (c *Classifier) Class() Class {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.class
}

// Observe advances the flow class. The caller should call this at a bounded
// cadence (for example, once per scheduler tick), not once per packet.
func (c *Classifier) Observe(o Observation) Class {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.class == ClassBulk {
		return c.class
	}
	if c.cfg.BulkIdleGapVeto > 0 {
		if o.SinceLastPayload >= c.cfg.BulkIdleGapVeto {
			if !c.inIdle {
				c.idleEpisodes++
				c.inIdle = true
			}
		} else {
			c.inIdle = false
		}
	}
	if c.isBulk(o) {
		c.class = ClassBulk
		return c.class
	}
	if c.class == ClassNew && o.Age >= c.cfg.NewAge {
		if c.isInteractive(o) || o.BytesUp+o.BytesDown >= c.cfg.NewBytes {
			c.class = ClassInteractive
		}
	}
	return c.class
}

func (c *Classifier) isBulk(o Observation) bool {
	if c.vetoed() {
		return false
	}
	return o.Age >= c.cfg.BulkMinimumAge &&
		o.BytesUp+o.BytesDown >= c.cfg.BulkBytes &&
		(!o.Bidirectional || !o.SmallBidirectionalBursts)
}

// vetoed reports whether this flow has gone quiet often enough to be
// disqualified from bulk.
func (c *Classifier) vetoed() bool {
	if c.cfg.BulkIdleGapVeto <= 0 {
		return false
	}
	return c.idleEpisodes >= c.vetoEpisodes()
}

// vetoEpisodes is the configured episode count, treating zero as one so that a
// deployment that set only the duration keeps the behaviour it had.
func (c *Classifier) vetoEpisodes() int {
	if c.cfg.BulkIdleGapVetoEpisodes <= 0 {
		return 1
	}
	return c.cfg.BulkIdleGapVetoEpisodes
}

func (c *Classifier) isInteractive(o Observation) bool {
	if o.Bidirectional && o.SmallBidirectionalBursts {
		return true
	}
	return o.SinceLastPayload >= c.cfg.InteractiveIdleGap &&
		max(o.UpRate, o.DownRate) <= c.cfg.InteractiveMaxRate
}

func max(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}
