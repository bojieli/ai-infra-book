// Package pathsim provides a deterministic UDP path emulator. It exists so
// transport changes can be compared against a fixed reference under a
// reproducible delay/loss/bandwidth regime instead of a live long-haul link
// whose loss rate moves by tens of percent between trials.
//
// The emulator is a UDP relay: clients send to Relay.LocalAddr and packets are
// forwarded to the configured target. Each direction independently applies
// tail-drop queueing at the configured bottleneck rate, random loss from a
// seeded generator, and a fixed propagation delay.
package pathsim

import (
	"errors"
	"fmt"
	"math/rand"
	"net"
	"sync"
	"sync/atomic"
	"time"
)

// Keep host UDP buffers comfortably above the short packet bursts used by the
// emulator. Otherwise a default Linux receive buffer can drop packets before
// the relay observes them, bypassing the configured deterministic loss model.
const relaySocketBuffer = 4 * 1024 * 1024

// Config describes one emulated path. Zero values disable the corresponding
// impairment, so a Config{} relay is a plain forwarder.
type Config struct {
	// OneWayDelay is added in each direction, so the emulated RTT is twice
	// this value.
	OneWayDelay time.Duration
	// DelayJitter is the maximum extra delay added to a packet, drawn
	// uniformly from [0, DelayJitter). Because the draw is per packet, this
	// also produces reordering, which is what a real path does and which
	// changes when a QUIC sender declares a packet lost.
	DelayJitter time.Duration
	// LossRate is the overall per-packet drop probability applied in each
	// direction, in [0,1).
	LossRate float64
	// UpstreamLossRate overrides LossRate for the client-to-server direction.
	// Zero means "use LossRate", so a symmetric path needs only LossRate.
	//
	// Asymmetric loss is worth modelling because a transport can depend on the
	// reverse direction in ways that are invisible when both directions are
	// impaired equally: anything the receiver has to send back - protocol
	// acknowledgements, window updates - competes for a congestion window that
	// heavy reverse loss collapses, and the forward flow stalls even though its
	// own direction is healthy.
	UpstreamLossRate float64
	// UpstreamClean states that the client-to-server direction erases nothing,
	// which UpstreamLossRate cannot express because its zero means "inherit
	// LossRate".
	//
	// The distinction is not hypothetical. The China-US datacenter path
	// measured in docs/PATH-CHARACTER-DC-20260826.md erases 14% downstream and
	// 0.0% upstream -- zero of 41,663 datagrams at 50 Mbit/s -- and that
	// asymmetry is its defining feature. An emulator that can only say
	// "different and non-zero" cannot reproduce the case where a transport's
	// acknowledgements cross a clean channel while its data does not, which is
	// exactly when a coding decision is easiest to get wrong.
	UpstreamClean bool
	// LossBurstPackets is the mean length, in packets, of a loss burst. One
	// (or zero) gives independent Bernoulli loss. Larger values switch to a
	// Gilbert model: the path alternates between a lossless good state and a
	// bad state that drops everything, with LossRate as the long-run fraction
	// of packets in the bad state.
	//
	// Long-haul loss is correlated, and correlated loss is a different regime
	// for a transport than the same average rate spread evenly: a burst can
	// take out a whole flight, including the retransmissions of the previous
	// one. Independent loss alone will not reproduce it.
	LossBurstPackets float64
	// RateBytesPerSec is the bottleneck serialization rate in each direction.
	// Zero means unlimited.
	RateBytesPerSec uint64
	// PerFlowRateBytesPerSec additionally polices each client source address
	// independently, modelling a path that shapes per 4-tuple rather than only
	// in aggregate. This is the regime in which multiple transport lanes can
	// raise a single application flow's goodput; with only an aggregate limit
	// they cannot, and should not be expected to. Zero disables it.
	PerFlowRateBytesPerSec uint64
	// QueueBytes bounds the bottleneck buffer. Packets that would exceed it
	// are tail-dropped. Zero selects one bandwidth-delay product, with a small
	// floor, which is the usual "reasonably provisioned router" assumption.
	QueueBytes int
	// DelayWander is the amplitude of a correlated random walk added to
	// OneWayDelay, and DelayWanderPeriod is how often it steps. Zero disables
	// it.
	//
	// This is the impairment the emulator lacked, and lacking it made it lie.
	// DelayJitter draws independently per packet, so it mostly reorders and
	// leaves the smoothed round trip near the minimum. A real long-haul path
	// does the opposite: the delay wanders over hundreds of milliseconds, so a
	// whole flight shifts together and the smoothed round trip sits well above
	// the minimum without much reordering at all. Measured on the China-US
	// path this targets, the round trip ranged 226 to 440 ms with a 48 ms
	// standard deviation while the minimum stayed put.
	//
	// That distinction decides transport behaviour. A congestion controller
	// sizes its window from the minimum round trip and measures delivery over
	// the current one, so a wandering path produces a stream of spuriously low
	// delivery-rate samples. A change to this project's controller measured
	// better on the emulator without this and cost more than half the
	// throughput live; with it, the emulator reproduces the live verdict.
	DelayWander       time.Duration
	DelayWanderPeriod time.Duration
	// PolicerRefillPeriod makes the bottleneck a token bucket refilled in
	// quanta of one period's worth of bytes, rather than a queue drained
	// continuously. It does not queue, so it adds no delay: a packet arriving
	// with no tokens left is dropped where a queue would have held it. Zero
	// keeps the queue.
	//
	// The live path is a policer, and the evidence is in the conditionals
	// rather than in the rate. At twice the bottleneck rate it shows arrival
	// runs averaging 2.3 packets and loss runs averaging 5.7. An arrival run
	// of 2.3 is 1/0.42, which is the erasure channel by itself -- so within a
	// run of arrivals nothing but the channel is dropping. The loss runs are
	// far longer than the channel alone gives. That is a limiter which passes
	// everything for a while and then drops everything for a while, which is
	// what a bucket refilled on a timer tick does.
	//
	// It is not what a queue does. A queue at steady overload admits a packet
	// exactly as fast as it drains one, so it drops nearly every other packet:
	// emulated that way, at every buffer size from 32 KiB to a full
	// bandwidth-delay product, the burst factor came out between 1.15 and 1.19
	// against the live path's 1.62. Nor is the clustering the sender's own --
	// reducing the probe's send burst from 64 packets to 4 left the live
	// figures unchanged. At an 8 ms refill the emulator reproduces all five
	// live statistics at once; see TestTheEmulatorReproducesTheMeasuredPath.
	//
	// Burst length is what decides whether an erasure code can repair a block,
	// so a model that under-reports it would certify a code rate that fails on
	// the real path.
	PolicerRefillPeriod time.Duration
	// PolicerBurstBytes is the token bucket's depth: how much a sender may put
	// through after an idle period before the shaping rate shows through.
	// Zero keeps the shallow bucket that models the live path, one refill
	// quantum plus a packet.
	//
	// A deep bucket is what makes a shaped path something other than a slower
	// one. A short probe drains the bucket and measures the line rate, while
	// sustained load measures the shaping rate, so the path has two rates and
	// no single bandwidth -- which is the case a max filter reports wrongly by
	// construction, and the reason a bandwidth estimate has to be able to fall.
	PolicerBurstBytes int
	// Seed makes the loss pattern reproducible across runs.
	Seed int64
	// MTU bounds a single datagram. Zero selects 1500.
	MTU int
}

func (c Config) withDefaults() Config {
	if c.MTU <= 0 {
		c.MTU = 1500
	}
	if c.DelayWander > 0 && c.DelayWanderPeriod <= 0 {
		// A step every fifth of a round trip: slow enough that a flight shares
		// one offset, fast enough to move within a transfer.
		c.DelayWanderPeriod = (2 * c.OneWayDelay) / 5
		if c.DelayWanderPeriod <= 0 {
			c.DelayWanderPeriod = 40 * time.Millisecond
		}
	}
	if c.QueueBytes <= 0 {
		if c.RateBytesPerSec > 0 {
			bdp := float64(c.RateBytesPerSec) * (2 * c.OneWayDelay).Seconds()
			c.QueueBytes = int(bdp)
		}
		if c.QueueBytes < 64*1024 {
			c.QueueBytes = 64 * 1024
		}
	}
	return c
}

// Stats reports what the emulator did, so a benchmark can distinguish "the
// transport was slow" from "the emulated path dropped the traffic".
type Stats struct {
	PacketsIn      uint64
	PacketsOut     uint64
	PacketsLost    uint64
	PacketsDropped uint64 // tail drop at the bottleneck queue
	BytesIn        uint64
	BytesOut       uint64
}

type direction struct {
	mu       sync.Mutex
	nextFree time.Time
	rng      *rand.Rand
	// inBurst is the Gilbert model's bad state. It is meaningful only when
	// the configuration asks for correlated loss.
	inBurst bool
	// lossRate is this direction's drop probability, which may differ from the
	// other direction's.
	lossRate float64
	// wander is the current correlated delay offset, and wanderAt is when it
	// last stepped. Consecutive packets see almost the same offset, which is
	// what makes this delay variation rather than reordering.
	wander   time.Duration
	wanderAt time.Time
	// backlog is the bottleneck queue's occupancy in bytes and drainAt is when
	// it was last drained; tokens is the policer's remaining allowance in
	// bytes and tokenAt is when it is next refilled. A direction uses one or
	// the other, never both.
	backlog float64
	drainAt time.Time
	tokens  float64
	tokenAt time.Time

	packetsIn      atomic.Uint64
	packetsOut     atomic.Uint64
	packetsLost    atomic.Uint64
	packetsDropped atomic.Uint64
	bytesIn        atomic.Uint64
	bytesOut       atomic.Uint64
}

func (d *direction) stats() Stats {
	return Stats{
		PacketsIn: d.packetsIn.Load(), PacketsOut: d.packetsOut.Load(),
		PacketsLost: d.packetsLost.Load(), PacketsDropped: d.packetsDropped.Load(),
		BytesIn: d.bytesIn.Load(), BytesOut: d.bytesOut.Load(),
	}
}

// schedule returns the absolute delivery time for a packet, or ok=false when
// the packet is dropped. Serialization is modelled by a virtual transmit
// clock: a packet may only start once the previous one finished, and the
// backlog ahead of it is the queue occupancy.
func (d *direction) schedule(now time.Time, size int, cfg Config) (time.Time, bool) {
	d.mu.Lock()
	defer d.mu.Unlock()
	start := now
	if cfg.RateBytesPerSec > 0 && cfg.PolicerRefillPeriod > 0 {
		if !d.policeLocked(now, size, cfg) {
			d.packetsDropped.Add(1)
			return time.Time{}, false
		}
	} else if cfg.RateBytesPerSec > 0 {
		// The queue holds bytes, and drains at the bottleneck rate.
		//
		// Holding it as a departure time instead, and recovering the occupancy
		// as elapsed-time times rate, is exact only while the rate never
		// moves. It is the same quantity only under that assumption, and the
		// assumption is not one the emulator should need.
		rate := float64(cfg.RateBytesPerSec)
		if !d.drainAt.IsZero() {
			d.backlog -= now.Sub(d.drainAt).Seconds() * rate
			if d.backlog < 0 {
				d.backlog = 0
			}
		}
		d.drainAt = now
		if int(d.backlog)+size > cfg.QueueBytes {
			d.packetsDropped.Add(1)
			return time.Time{}, false
		}
		d.backlog += float64(size)
		start = now.Add(time.Duration(d.backlog / rate * float64(time.Second)))
	}
	// The erasure segment is downstream of the limiter: a packet it drops has
	// already spent the bottleneck's capacity.
	//
	// The order is not a detail, and the measured path picks it. Offering 50
	// Mbit/s to a path with a 25 Mbit/s limiter and 42% loss delivered 14.4
	// Mbit/s live, which is 25 x 0.58. Erasing first would have fed the
	// limiter 29 Mbit/s and delivered 25. Putting the loss upstream also makes
	// the two regimes mutually exclusive -- the channel would shield the
	// limiter from ever being overrun -- so a model built that way can never
	// show the correlated loss the live path shows above its knee.
	if d.lossRate > 0 && d.dropLocked(cfg) {
		d.packetsLost.Add(1)
		return time.Time{}, false
	}
	arrival := start.Add(cfg.OneWayDelay).Add(d.wanderOffset(now, cfg))
	if cfg.DelayJitter > 0 {
		arrival = arrival.Add(time.Duration(d.rng.Int63n(int64(cfg.DelayJitter))))
	}
	return arrival, true
}

// scheduleStream is the schedule a byte-stream relay needs: the same
// serialization and propagation model, but it never drops.
//
// Tail drop is meaningless for a stream. Discarding a chunk delivers a hole
// rather than triggering a retransmission, and treating the drop as fatal
// truncates the transfer at exactly one queue's worth of data - which is how
// this was found, with 4 MiB transfers ending at 1.25 MiB, the configured
// bandwidth-delay product. A stream relay applies backpressure instead, by
// bounding its own queue.
func (d *direction) scheduleStream(now time.Time, size int, cfg Config) time.Time {
	d.mu.Lock()
	defer d.mu.Unlock()
	start := now
	if cfg.RateBytesPerSec > 0 {
		if d.nextFree.After(start) {
			start = d.nextFree
		}
		serialize := time.Duration(float64(size) / float64(cfg.RateBytesPerSec) * float64(time.Second))
		d.nextFree = start.Add(serialize)
		start = d.nextFree
	}
	arrival := start.Add(cfg.OneWayDelay).Add(d.wanderOffset(now, cfg))
	if cfg.DelayJitter > 0 {
		arrival = arrival.Add(time.Duration(d.rng.Int63n(int64(cfg.DelayJitter))))
	}
	return arrival
}

// wanderOffset advances the correlated delay walk and returns the current
// offset. It must be called with the direction's lock held.
//
// The walk is reflected at both ends rather than clamped, so the offset does
// not stick to a boundary, and it steps by at most a third of the amplitude so
// consecutive flights overlap rather than jumping past each other.
func (d *direction) wanderOffset(now time.Time, cfg Config) time.Duration {
	if cfg.DelayWander <= 0 {
		return 0
	}
	if d.wanderAt.IsZero() {
		d.wanderAt = now
		d.wander = time.Duration(d.rng.Int63n(int64(cfg.DelayWander) + 1))
		return d.wander
	}
	for !d.wanderAt.After(now) {
		step := time.Duration(d.rng.Int63n(int64(cfg.DelayWander)/3+1)) - cfg.DelayWander/6
		next := d.wander + step
		if next < 0 {
			next = -next
		}
		if next > cfg.DelayWander {
			next = 2*cfg.DelayWander - next
		}
		if next < 0 {
			next = 0
		}
		d.wander = next
		d.wanderAt = d.wanderAt.Add(cfg.DelayWanderPeriod)
	}
	return d.wander
}

// policeLocked charges this packet against the token bucket, refilling it in
// whole quanta first, and reports whether it may pass. It must be called with
// the direction's lock held.
func (d *direction) policeLocked(now time.Time, size int, cfg Config) bool {
	quantum := float64(cfg.RateBytesPerSec) * cfg.PolicerRefillPeriod.Seconds()
	if quantum <= 0 {
		return true
	}
	// The bucket holds a quantum plus one packet rather than exactly a
	// quantum. With exactly a quantum the remainder below a packet's size is
	// discarded at every refill and the limiter delivers less than its
	// configured rate: with a 3125-byte quantum and 1200-byte packets it
	// passed two packets per period instead of two and a half, which measured
	// as 19 Mbit/s out of a 25 Mbit/s limiter.
	bucket := quantum + float64(cfg.MTU)
	if burst := float64(cfg.PolicerBurstBytes); burst > bucket {
		bucket = burst
	}
	if d.tokenAt.IsZero() {
		d.tokenAt = now
		// A bucket a sender has not touched yet is full, which is what gives
		// the first burst its allowance.
		d.tokens = bucket
	}
	// Bounded because an idle path can leave an arbitrary gap since the last
	// packet, and the bucket saturates after two refills anyway.
	for steps := 0; !d.tokenAt.After(now) && steps < 64; steps++ {
		if d.tokens += quantum; d.tokens > bucket {
			d.tokens = bucket
		}
		d.tokenAt = d.tokenAt.Add(cfg.PolicerRefillPeriod)
	}
	if d.tokenAt.Before(now) {
		d.tokenAt = now
	}
	if d.tokens < float64(size) {
		return false
	}
	d.tokens -= float64(size)
	return true
}

// dropLocked decides whether this packet is lost. With no burst length
// configured it is one Bernoulli trial. Otherwise it is a two-state Gilbert
// chain whose bad state drops everything: the mean bad run is
// LossBurstPackets, and the transition into it is chosen so the long-run drop
// fraction is LossRate.
func (d *direction) dropLocked(cfg Config) bool {
	if cfg.LossBurstPackets <= 1 {
		return d.rng.Float64() < d.lossRate
	}
	recover := 1 / cfg.LossBurstPackets
	enter := recover * d.lossRate / (1 - d.lossRate)
	if d.inBurst {
		if d.rng.Float64() < recover {
			d.inBurst = false
		}
		return true
	}
	if d.rng.Float64() < enter {
		d.inBurst = true
		return true
	}
	return false
}

type peer struct {
	client net.Addr
	conn   *net.UDPConn
	last   atomic.Int64
	// up and down are this source address's own policer, used only when the
	// configuration asks for per-flow shaping. They deliberately do not apply
	// loss: loss stays a property of the shared path so that per-flow shaping
	// can be varied independently of the loss regime.
	up   direction
	down direction
}

// Relay is a running emulated path. It is safe for concurrent use and is
// stopped with Close.
type Relay struct {
	cfg    Config
	target *net.UDPAddr
	local  *net.UDPConn

	// upstream and downstream may be this relay's own, or shared with other
	// relays through a Bottleneck.
	upstream   *direction // client -> server
	downstream *direction // server -> client
	owned      [2]direction

	mu     sync.Mutex
	peers  map[string]*peer
	closed bool

	// queues hold packets until their modelled arrival. One goroutine per
	// direction replaces one per in-flight packet; see deliveryQueue.
	queueMu sync.Mutex
	queues  map[*direction]*deliveryQueue

	wg   sync.WaitGroup
	done chan struct{}
}

// Bottleneck is one shared link: a serialization clock, a queue and a loss
// process that several relays contend for.
//
// Without it every endpoint gets its own private path, and two transports can
// only ever be measured one after the other. That answers "which is faster
// alone" and cannot answer "which takes more of the link when both want it",
// which is a different question and, for a transport whose goal is to win a
// contended bottleneck, the only one that matters.
type Bottleneck struct {
	up   direction
	down direction
}

// NewBottleneck returns a link that relays can be attached to with Attach.
func NewBottleneck(cfg Config) *Bottleneck {
	cfg = cfg.withDefaults()
	b := &Bottleneck{}
	b.up.rng = rand.New(rand.NewSource(cfg.Seed))
	b.down.rng = rand.New(rand.NewSource(cfg.Seed + 1))
	b.up.lossRate = cfg.LossRate
	if cfg.UpstreamClean {
		b.up.lossRate = 0
	} else if cfg.UpstreamLossRate > 0 {
		b.up.lossRate = cfg.UpstreamLossRate
	}
	b.down.lossRate = cfg.LossRate
	return b
}

// Stats returns the shared link's counters, which aggregate every attached
// relay.
func (b *Bottleneck) Stats() (up, down Stats) { return b.up.stats(), b.down.stats() }

// Attach starts a relay that contends for this bottleneck instead of having a
// path of its own.
func (b *Bottleneck) Attach(listen, target string, cfg Config) (*Relay, error) {
	return newRelay(listen, target, cfg, b)
}

// New starts a relay on listen (use "127.0.0.1:0" for an ephemeral port) that
// forwards to target.
func New(listen, target string, cfg Config) (*Relay, error) {
	return newRelay(listen, target, cfg, nil)
}

func newRelay(listen, target string, cfg Config, shared *Bottleneck) (*Relay, error) {
	if cfg.LossRate < 0 || cfg.LossRate >= 1 {
		return nil, fmt.Errorf("loss rate %v must be in [0,1)", cfg.LossRate)
	}
	if cfg.UpstreamLossRate < 0 || cfg.UpstreamLossRate >= 1 {
		return nil, fmt.Errorf("upstream loss rate %v must be in [0,1)", cfg.UpstreamLossRate)
	}
	cfg = cfg.withDefaults()
	targetAddr, err := net.ResolveUDPAddr("udp", target)
	if err != nil {
		return nil, fmt.Errorf("resolve target: %w", err)
	}
	listenAddr, err := net.ResolveUDPAddr("udp", listen)
	if err != nil {
		return nil, fmt.Errorf("resolve listen: %w", err)
	}
	local, err := net.ListenUDP("udp", listenAddr)
	if err != nil {
		return nil, fmt.Errorf("listen: %w", err)
	}
	if err := configureUDPBuffers(local); err != nil {
		_ = local.Close()
		return nil, fmt.Errorf("configure listener buffers: %w", err)
	}
	r := &Relay{
		cfg: cfg, target: targetAddr, local: local,
		peers: make(map[string]*peer), done: make(chan struct{}),
	}
	if shared != nil {
		r.upstream, r.downstream = &shared.up, &shared.down
	} else {
		r.upstream, r.downstream = &r.owned[0], &r.owned[1]
		// Separate generators keep each direction's loss pattern independent of
		// the other direction's packet count, which would otherwise make a result
		// depend on unrelated timing.
		r.upstream.rng = rand.New(rand.NewSource(cfg.Seed))
		r.downstream.rng = rand.New(rand.NewSource(cfg.Seed + 1))
		r.upstream.lossRate = cfg.LossRate
		if cfg.UpstreamClean {
			r.upstream.lossRate = 0
		} else if cfg.UpstreamLossRate > 0 {
			r.upstream.lossRate = cfg.UpstreamLossRate
		}
		r.downstream.lossRate = cfg.LossRate
	}
	r.wg.Add(1)
	go r.readClient()
	return r, nil
}

// LocalAddr is the address clients should use in place of the real server.
func (r *Relay) LocalAddr() string { return r.local.LocalAddr().String() }

// SetLossRate changes what the path erases, in each direction, while traffic
// is already crossing it.
//
// A path that only ever erases what it was constructed with cannot express the
// case a transport most needs to survive: one whose channel changes under a
// live flow. The motivating incident was exactly that -- downstream erasure
// moving from a few percent to sixty over a working afternoon -- and a
// controller that reads a floor established during the clean window will size
// its code for a channel that no longer exists. Emulating the step is the only
// way to test that the estimate follows.
//
// A negative rate leaves that direction alone, so a caller may change one
// without knowing the other.
func (r *Relay) SetLossRate(upstream, downstream float64) {
	r.upstream.setLossRate(upstream)
	r.downstream.setLossRate(downstream)
}

// SetLossRate changes what a shared bottleneck erases, for every relay
// attached to it.
func (b *Bottleneck) SetLossRate(upstream, downstream float64) {
	b.up.setLossRate(upstream)
	b.down.setLossRate(downstream)
}

// setLossRate takes the same lock the drop decision is made under, so a change
// lands between packets rather than during one.
func (d *direction) setLossRate(rate float64) {
	if rate < 0 {
		return
	}
	if rate > 1 {
		rate = 1
	}
	d.mu.Lock()
	defer d.mu.Unlock()
	d.lossRate = rate
	// A Gilbert chain mid-burst would otherwise carry the old regime's bad
	// state across the change and erase everything until it happened to
	// recover, which reads as the new rate arriving late.
	d.inBurst = false
}

// Stats returns the upstream (client to server) and downstream counters.
func (r *Relay) Stats() (up, down Stats) { return r.upstream.stats(), r.downstream.stats() }

// Sources is how many distinct client source addresses have been seen, which
// is how many buckets a per-source policer has actually applied.
//
// It is the number a striping measurement turns on: lanes only multiply a
// per-source allowance if they arrive from different sources, and a lane that
// shares a connection with another shares its bucket too. Counting them is the
// difference between measuring the transport and measuring how many sockets it
// happened to open.
func (r *Relay) Sources() int {
	r.mu.Lock()
	defer r.mu.Unlock()
	return len(r.peers)
}

func (r *Relay) Close() error {
	r.mu.Lock()
	if r.closed {
		r.mu.Unlock()
		return nil
	}
	r.closed = true
	close(r.done)
	peers := make([]*peer, 0, len(r.peers))
	for _, p := range r.peers {
		peers = append(peers, p)
	}
	r.peers = nil
	r.mu.Unlock()
	_ = r.local.Close()
	for _, p := range peers {
		_ = p.conn.Close()
	}
	r.queueMu.Lock()
	queues := make([]*deliveryQueue, 0, len(r.queues))
	for _, queue := range r.queues {
		queues = append(queues, queue)
	}
	r.queues = nil
	r.queueMu.Unlock()
	for _, queue := range queues {
		queue.close()
	}
	r.wg.Wait()
	return nil
}

func (r *Relay) readClient() {
	defer r.wg.Done()
	buf := make([]byte, r.cfg.MTU)
	for {
		n, addr, err := r.local.ReadFrom(buf)
		if err != nil {
			if fatalReadError(err) {
				return
			}
			// One datagram's problem, not the socket's. Returning here would
			// stop emulating the path without saying so.
			continue
		}
		p, err := r.peerFor(addr)
		if err != nil {
			continue
		}
		payload := make([]byte, n)
		copy(payload, buf[:n])
		r.forward(r.upstream, &p.up, payload, func(b []byte) {
			_, _ = p.conn.Write(b)
		})
	}
}

func (r *Relay) peerFor(addr net.Addr) (*peer, error) {
	key := addr.String()
	r.mu.Lock()
	defer r.mu.Unlock()
	if r.closed {
		return nil, errors.New("relay is closed")
	}
	if existing, ok := r.peers[key]; ok {
		existing.last.Store(time.Now().UnixNano())
		return existing, nil
	}
	conn, err := net.DialUDP("udp", nil, r.target)
	if err != nil {
		return nil, err
	}
	if err := configureUDPBuffers(conn); err != nil {
		_ = conn.Close()
		return nil, fmt.Errorf("configure peer buffers: %w", err)
	}
	p := &peer{client: addr, conn: conn}
	p.up.rng = rand.New(rand.NewSource(r.cfg.Seed))
	p.down.rng = rand.New(rand.NewSource(r.cfg.Seed))
	p.last.Store(time.Now().UnixNano())
	r.peers[key] = p
	r.wg.Add(1)
	go r.readServer(p)
	return p, nil
}

func configureUDPBuffers(conn *net.UDPConn) error {
	if err := conn.SetReadBuffer(relaySocketBuffer); err != nil {
		return err
	}
	return conn.SetWriteBuffer(relaySocketBuffer)
}

func (r *Relay) readServer(p *peer) {
	defer r.wg.Done()
	buf := make([]byte, r.cfg.MTU)
	for {
		n, err := p.conn.Read(buf)
		if err != nil {
			if fatalReadError(err) {
				return
			}
			continue
		}
		payload := make([]byte, n)
		copy(payload, buf[:n])
		client := p.client
		r.forward(r.downstream, &p.down, payload, func(b []byte) {
			_, _ = r.local.WriteTo(b, client)
		})
	}
}

// forward applies the impairment model and hands the packet to send at its
// scheduled delivery time. One timer goroutine per in-flight packet is
// acceptable here: the emulator runs in the benchmark process, and the
// bandwidth-delay product bounds the concurrent count.
func (r *Relay) forward(d *direction, perFlow *direction, payload []byte, send func([]byte)) {
	d.packetsIn.Add(1)
	d.bytesIn.Add(uint64(len(payload)))
	now := time.Now()
	if perFlow != nil && r.cfg.PerFlowRateBytesPerSec > 0 {
		// The per-flow policer runs first and contributes only queueing delay
		// and its own tail drop; the shared path then adds loss and the
		// aggregate bottleneck.
		flowCfg := r.cfg
		flowCfg.RateBytesPerSec = r.cfg.PerFlowRateBytesPerSec
		flowCfg.OneWayDelay = 0
		// Size the policer's own bucket from its own rate. Inheriting the
		// aggregate path's queue gave each source a bucket sized for the whole
		// link -- at 400 Mbit/s aggregate and 25 Mbit/s per source, three
		// seconds of buffering, which is a deep buffer rather than the policer
		// it is meant to be. Every conclusion drawn about "shallow policers"
		// from that configuration was drawn about the wrong path.
		if r.cfg.QueueBytes > 0 && r.cfg.RateBytesPerSec > 0 {
			scaled := float64(r.cfg.QueueBytes) * float64(r.cfg.PerFlowRateBytesPerSec) / float64(r.cfg.RateBytesPerSec)
			flowCfg.QueueBytes = int(scaled)
			if flowCfg.QueueBytes < 64*1024 {
				flowCfg.QueueBytes = 64 * 1024
			}
		}
		released, allowed := perFlow.schedule(now, len(payload), flowCfg)
		if !allowed {
			d.packetsDropped.Add(1)
			return
		}
		if released.After(now) {
			now = released
		}
	}
	deliver, ok := d.schedule(now, len(payload), r.cfg)
	if !ok {
		return
	}
	if !deliver.After(time.Now()) {
		d.packetsOut.Add(1)
		d.bytesOut.Add(uint64(len(payload)))
		send(payload)
		return
	}
	r.queueFor(d).add(scheduled{deliver: deliver, payload: payload, send: send, direction: d})
}

// queueFor returns the delivery queue for a direction, created on first use so
// an unimpaired relay starts no extra goroutines at all.
func (r *Relay) queueFor(d *direction) *deliveryQueue {
	r.queueMu.Lock()
	defer r.queueMu.Unlock()
	if r.queues == nil {
		r.queues = make(map[*direction]*deliveryQueue, 2)
	}
	queue, ok := r.queues[d]
	if !ok {
		queue = newDeliveryQueue(r.done)
		r.queues[d] = queue
	}
	return queue
}
