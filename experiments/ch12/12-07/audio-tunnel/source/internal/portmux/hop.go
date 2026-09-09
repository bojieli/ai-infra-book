package portmux

import (
	"context"
	"crypto/rand"
	"log/slog"
	"math/big"
	"sync"
	"time"
)

// HopWalk is the client-wide port-walking state shared by every dial. Each
// new dial and each reactive hop consumes the next index from a shuffled
// permutation of the hop port list, so successive dials neither restart on
// the (typically burned) primary port nor repeat one another, and ports are
// tried in an order an observer cannot predict from the derivation hash.
type HopWalk struct {
	mu    sync.Mutex
	order []int
	pos   int
}

// shuffleInts is Fisher-Yates over crypto/rand. The port order is meant to be
// unpredictable to the same network observer who already knows the HopPorts
// derivation hash, so a weak PRNG would not do.
func shuffleInts(order []int) {
	for i := len(order) - 1; i > 0; i-- {
		j, err := rand.Int(rand.Reader, big.NewInt(int64(i+1)))
		if err != nil {
			return // leave the rest unshuffled rather than fail the dial path
		}
		k := int(j.Int64())
		order[i], order[k] = order[k], order[i]
	}
}

// NewHopWalk returns a walk over the port-list indices [0, count) in a
// freshly shuffled order.
func NewHopWalk(count int) *HopWalk {
	order := make([]int, count)
	for i := range order {
		order[i] = i
	}
	shuffleInts(order)
	return &HopWalk{order: order}
}

// Next returns the next port-list index to try, reshuffling whenever the
// current permutation is exhausted so no long-term order is observable.
func (w *HopWalk) Next() int32 {
	w.mu.Lock()
	defer w.mu.Unlock()
	if w.pos >= len(w.order) {
		shuffleInts(w.order)
		w.pos = 0
	}
	idx := w.order[w.pos]
	w.pos++
	// idx < count, and count is the configured hop pool size (order 100), so
	// the int32 conversion cannot overflow.
	return int32(idx)
}

// HopMetrics is the narrow interface the HopController needs from the metrics
// registry. Using an interface avoids a direct import of the metrics package
// from portmux and keeps the dependency graph clean.
type HopMetrics interface {
	PortHop()
}

// HopConfig controls the loss-detection and cooldown behaviour.
type HopConfig struct {
	// DetectWindow is how long a zero-receive window must persist before a
	// hop is triggered. Default 4 s: short enough that a 10 s dial timeout
	// still allows several hops per dial, long enough that a slow but
	// working path (which keeps receiving) never trips it.
	DetectWindow time.Duration
	// MinSent is the minimum number of packets that must have been sent in the
	// detect window before loss is considered actionable. A quiet connection
	// should not hop just because it sent nothing and received nothing.
	MinSent uint64
	// Cooldown is the minimum interval between successive hops. Default 3 s.
	// It must stay well below the QUIC dial timeout so one dial can walk
	// several ports; it also bounds thrash when every port is blocked.
	Cooldown time.Duration
	// PollInterval is how often the controller samples the counters.
	// Default 2 s. Lower values improve detection latency at the cost of
	// slightly more CPU; values below 1 s are clamped to 1 s.
	PollInterval time.Duration
	// Walk selects which port to hop to. It is shared across all dials of a
	// client so port choices accumulate across connection attempts instead
	// of restarting at the primary port every dial. Nil installs a private
	// shuffled walk (used by tests).
	Walk *HopWalk

	Metrics HopMetrics
	Logger  *slog.Logger
}

func (c *HopConfig) resolved() HopConfig {
	r := *c
	if r.DetectWindow <= 0 {
		r.DetectWindow = 4 * time.Second
	}
	if r.MinSent == 0 {
		r.MinSent = 5
	}
	if r.Cooldown <= 0 {
		r.Cooldown = 3 * time.Second
	}
	if r.PollInterval <= 0 {
		r.PollInterval = 2 * time.Second
	}
	if r.PollInterval < time.Second {
		r.PollInterval = time.Second
	}
	return r
}

// HopController monitors the send/receive ratio on a ClientPortMux and
// triggers a port hop when it detects the characteristic zero-receive pattern
// caused by per-port GFW blocking.
//
// Detection logic: sample (sendCount, recvCount) every PollInterval. Maintain
// a sliding window of duration DetectWindow. If totalSent > MinSent and
// totalReceived == 0 over the window, trigger a hop.
//
// RTT guard: GFW blocking produces total loss; congestion produces partial
// loss. The zero-receive threshold implicitly distinguishes them: even a path
// with 99% congestion loss receives something. A hop under congestion is
// harmless (the new port shares the same bottleneck) but the guard keeps churn
// low on paths that are merely slow.
//
// Cooldown: successive hops are separated by at least Cooldown. Ports are
// chosen from the shared HopWalk (shuffled, persistent across dials), so the
// pool is walked in random order rather than scanned predictably from the
// primary port.
type HopController struct {
	mux  *ClientPortMux
	cfg  HopConfig
	walk *HopWalk
}

// NewHopController creates a controller for mux using cfg.
func NewHopController(mux *ClientPortMux, cfg HopConfig) *HopController {
	cfg = cfg.resolved()
	walk := cfg.Walk
	if walk == nil {
		walk = NewHopWalk(len(mux.ports))
	}
	return &HopController{
		mux:  mux,
		cfg:  cfg,
		walk: walk,
	}
}

// Run starts the monitoring loop. It returns when ctx is cancelled, which
// happens when the associated ClientPortMux is closed.
func (h *HopController) Run(ctx context.Context) {
	cfg := h.cfg

	// ringSize is the number of samples kept in the sliding window.
	// Each sample covers PollInterval; the window is DetectWindow.
	samplesPerWindow := int(cfg.DetectWindow / cfg.PollInterval)
	if samplesPerWindow < 2 {
		samplesPerWindow = 2
	}

	type sample struct {
		sent uint64
		recv uint64
	}
	ring := make([]sample, samplesPerWindow)
	ringPos := 0
	// filled counts recorded samples up to a full window. Triggering on a
	// partially filled window hops on as little as one poll interval of
	// evidence, which made every fresh dial hop almost immediately.
	filled := 0

	var (
		lastSend uint64
		lastRecv uint64
		lastHop  time.Time
	)

	ticker := time.NewTicker(cfg.PollInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
		}

		sent := h.mux.sendCount.Load()
		recv := h.mux.recvCount.Load()

		// Record the delta since the last sample.
		ring[ringPos] = sample{
			sent: sent - lastSend,
			recv: recv - lastRecv,
		}
		lastSend = sent
		lastRecv = recv
		ringPos = (ringPos + 1) % samplesPerWindow
		if filled < samplesPerWindow {
			filled++
		}

		// Sum the entire window.
		var windowSent, windowRecv uint64
		for _, s := range ring {
			windowSent += s.sent
			windowRecv += s.recv
		}

		// Trigger condition: a full window of actively sending but receiving
		// nothing.
		if filled < samplesPerWindow || windowSent < cfg.MinSent || windowRecv > 0 {
			continue
		}

		// Respect cooldown: don't hop again too soon.
		now := time.Now()
		if !lastHop.IsZero() && now.Sub(lastHop) < cfg.Cooldown {
			continue
		}

		if len(h.mux.ports) <= 1 {
			continue // no alternative ports
		}
		// Draw until the walk offers a different port: hopping "to" the port
		// already in use wastes a cooldown on no change.
		idx := h.walk.Next()
		for idx == h.mux.CurrentIndex() {
			idx = h.walk.Next()
		}

		fromPort, toPort := h.mux.Hop(idx)
		lastHop = now

		// Reset the window so the new port gets a fresh evaluation.
		for i := range ring {
			ring[i] = sample{}
		}
		filled = 0

		if cfg.Metrics != nil {
			cfg.Metrics.PortHop()
		}
		if cfg.Logger != nil {
			cfg.Logger.Info("port hop", "from_port", fromPort, "to_port", toPort)
		}
	}
}
