// Package pathseg measures a path one segment at a time, so that a loss or
// latency figure can be attributed to the part of the world that produced it.
//
// The instruments this project already has describe a path end to end.
// cmd/pathprobe says what fraction of an offered rate survives, cmd/pathmeasure
// says what a stack achieves on it, and queqiaod doctor says whether the
// gateway is on the useful side of a destination. None of them answers the
// question an operator actually asks when a deployment is slow, which is not
// "how bad is it" but "whose fault is it": the client's own access link, the
// long haul this transport carries, or the gateway's transit onward.
//
// That question is answerable because the three segments overlap. A client
// reaching its gateway and the same client reaching a destination directly
// share the client's first mile and nothing else. A client reaching its gateway
// and the gateway reaching a destination share nothing at all. So three legs
// measured in the same minutes have exactly one segment in common per pair, and
// the pattern of which legs are lossy names the segment they share. attribute.go
// does that reasoning; this file takes the measurements it reasons over.
//
// Two probes are provided because neither alone is enough. ICMP echo counts
// individual packets, which is the only way to see a loss rate at all, and it
// is also the thing a network is most willing to rate-limit or drop outright --
// so a leg with no replies is reported as blocked rather than as total loss,
// because the two are indistinguishable from here and only one of them is a
// finding. TCP establishment cannot count packets, but it travels as ordinary
// traffic that nobody deprioritises, so it is the honest fallback and the
// cross-check.
package pathseg

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/binary"
	"errors"
	"fmt"
	"math"
	"net"
	"sort"
	"sync"
	"time"

	"golang.org/x/net/icmp"
	"golang.org/x/net/ipv4"
	"golang.org/x/net/ipv6"

	"github.com/bojieli/queqiao/internal/lossmodel"
)

// ErrICMPUnavailable reports that no echo socket could be opened at all, which
// is a property of this host rather than of the path. Linux hands out datagram
// ICMP only to groups named in net.ipv4.ping_group_range, and the common
// default names none, so an unprivileged run on an ordinary Linux box lands
// here and has to fall back to establishment timing.
var ErrICMPUnavailable = errors.New("ICMP echo is not usable from this host")

// Sequence is one probe run in send order: whether each probe came back, and
// how long the ones that did took.
//
// The order matters and is why this is not just a pair of counts. Loss that
// arrives in runs and loss that arrives independently need different responses
// -- backing off does not make an erasure channel drop less -- and the
// difference is only visible in the order the outcomes occurred.
type Sequence struct {
	Arrived []bool
	// RTTs holds one millisecond figure per arrived probe, in send order.
	RTTs []float64
}

// Leg is one measured segment, reduced to the figures a verdict is read from.
type Leg struct {
	Name   string `json:"name"`
	From   string `json:"from"`
	To     string `json:"to"`
	Method string `json:"method"`
	// Address is what the vantage point resolved the target to. Two vantage
	// points resolving one name to two addresses are not measuring the same
	// machine, which is a finding in itself rather than a detail.
	Address string `json:"address,omitempty"`

	Sent    int     `json:"sent"`
	Arrived int     `json:"arrived"`
	Loss    float64 `json:"loss"`

	// BurstFactor separates an erasure channel from a congested one. It is 1
	// for memoryless loss and rises as loss clusters, which is the reading
	// cmd/pathprobe's -pattern produces and the same statistic the transport's
	// own estimator publishes.
	BurstFactor  float64 `json:"burst_factor,omitempty"`
	LongestBurst int     `json:"longest_burst,omitempty"`

	MinMS float64 `json:"min_ms,omitempty"`
	P50MS float64 `json:"p50_ms,omitempty"`
	P99MS float64 `json:"p99_ms,omitempty"`
	// MeanMS is set only where the samples themselves were never available and
	// a mean is all the instrument reported -- ping(8)'s summary line. It is
	// kept apart from P50MS rather than folded into it because a mean and a
	// median differ most on exactly the tailed distributions this tool is
	// pointed at, and labelling one as the other would misreport the case that
	// matters.
	MeanMS float64 `json:"mean_ms,omitempty"`

	// TailRate is the share of successful establishments that took materially
	// longer than the fastest one. On a TCP leg it is the only loss signal
	// available, because a retransmitted handshake packet shows up as a whole
	// retransmission timeout rather than as a missing sample. It is a proxy
	// and is named one; a verdict leans on it only when ICMP was unavailable.
	TailRate float64 `json:"tail_rate,omitempty"`

	// Blocked distinguishes a filtered probe from a destroyed one. A leg that
	// got nothing back has not measured 100% loss, it has measured nothing,
	// and attributing on it would invent the strongest possible finding out of
	// a firewall rule.
	Blocked bool   `json:"blocked,omitempty"`
	Error   string `json:"error,omitempty"`
}

// Usable reports whether this leg carries evidence a verdict may rest on.
func (l Leg) Usable() bool { return l.Sent > 0 && !l.Blocked && l.Error == "" }

// PingOptions configures one ICMP echo run.
type PingOptions struct {
	// Target is an address, already resolved. Resolution is the caller's job
	// so that the echo leg and the establishment leg to one destination are
	// aimed at the same machine; a name that resolves differently per probe
	// would silently compare two paths.
	Target net.IP
	// LocalAddress binds the socket to one source address. On a host with a
	// TUN route this is what keeps a "direct" measurement direct rather than
	// carrying it through the very tunnel being measured -- the same reason
	// cmd/pathprobe and cmd/pathmeasure grew the flag.
	LocalAddress string
	Count        int
	Interval     time.Duration
	// Timeout is how long to keep listening after the last probe was sent.
	Timeout time.Duration
	Payload int
}

const (
	tokenSize      = 8
	minPayload     = tokenSize
	defaultPayload = 56
	// maxSequence is what the echo header's 16-bit sequence field can carry.
	// A run longer than this would reuse a number and attribute one probe's
	// reply to another.
	maxSequence = 1<<16 - 1
)

// Ping sends echo requests at a fixed cadence and reports which came back.
//
// The cadence is fixed and the probes are not adaptive, because the question is
// what the path does to traffic offered at a rate nobody is adjusting. That is
// the same discipline cmd/pathprobe applies at a much higher rate; here the
// rate is negligible and the run is safe to point at a third party, which the
// open-loop blast never is.
func Ping(ctx context.Context, opts PingOptions) (Sequence, error) {
	if opts.Count <= 0 {
		return Sequence{}, errors.New("count must be positive")
	}
	if opts.Count > maxSequence {
		opts.Count = maxSequence
	}
	if opts.Interval <= 0 {
		opts.Interval = 100 * time.Millisecond
	}
	if opts.Timeout <= 0 {
		opts.Timeout = 2 * time.Second
	}
	if opts.Payload < minPayload {
		opts.Payload = defaultPayload
	}
	if opts.Target == nil {
		return Sequence{}, errors.New("no target address")
	}

	conn, raw, err := listenICMP(opts.Target, opts.LocalAddress)
	if err != nil {
		return Sequence{}, err
	}
	defer func() { _ = conn.Close() }()

	token := make([]byte, tokenSize)
	if _, err := rand.Read(token); err != nil {
		return Sequence{}, fmt.Errorf("draw a run token: %w", err)
	}

	v6 := opts.Target.To4() == nil
	echoType := icmp.Type(ipv4.ICMPTypeEcho)
	replyType := icmp.Type(ipv4.ICMPTypeEchoReply)
	proto := ipv4.ICMPTypeEchoReply.Protocol()
	if v6 {
		echoType, replyType = ipv6.ICMPTypeEchoRequest, ipv6.ICMPTypeEchoReply
		proto = ipv6.ICMPTypeEchoReply.Protocol()
	}
	dest := icmpDestination(opts.Target, raw)

	// The identifier is only meaningful on a raw socket. A datagram ICMP
	// socket has its identifier rewritten by the kernel, which then demuxes
	// replies to this socket by the value it chose, so matching on the one we
	// wrote would discard every reply on exactly the platforms where the
	// unprivileged path works.
	id := int(binary.BigEndian.Uint16(token[:2]))

	var (
		mu     sync.Mutex
		sentAt = make([]time.Time, opts.Count)
		rtt    = make([]time.Duration, opts.Count)
		got    = make([]bool, opts.Count)
	)

	// stop is what ends the reader. Closing the read deadline alone would not:
	// a deadline in the past makes every read return a timeout immediately,
	// and a reader that treats a timeout as "keep waiting" would spin on the
	// CPU forever instead of returning.
	stop := make(chan struct{})
	done := make(chan struct{})
	go func() {
		defer close(done)
		buf := make([]byte, 1500)
		for {
			// A short read deadline keeps this loop responsive to the outer
			// deadline without blocking on a path that has gone silent.
			_ = conn.SetReadDeadline(time.Now().Add(200 * time.Millisecond))
			n, _, err := conn.ReadFrom(buf)
			if err != nil {
				var ne net.Error
				if errors.As(err, &ne) && ne.Timeout() {
					select {
					case <-ctx.Done():
						return
					case <-stop:
						return
					default:
						continue
					}
				}
				return
			}
			at := time.Now()
			msg, err := icmp.ParseMessage(proto, buf[:n])
			if err != nil || msg.Type != replyType {
				continue
			}
			echo, ok := msg.Body.(*icmp.Echo)
			if !ok || len(echo.Data) < minPayload {
				continue
			}
			if raw && echo.ID != id {
				continue
			}
			// The token is what makes a raw socket, which sees every ICMP
			// message on the host, keep only this run's own replies.
			if !bytes.Equal(echo.Data[:tokenSize], token) {
				continue
			}
			// The sequence is read from the header rather than the payload.
			// A datagram ICMP socket has its identifier rewritten by the
			// kernel but not its sequence number, so this is the one field
			// that survives both socket types unchanged -- and it is already
			// an int, so nothing here converts a number a peer chose.
			seq := echo.Seq
			if seq < 0 || seq >= opts.Count {
				continue
			}
			mu.Lock()
			// A duplicated reply is not a second delivery of the same probe,
			// and counting it would let a duplicating middlebox report more
			// arrivals than there were probes.
			if !got[seq] && !sentAt[seq].IsZero() {
				got[seq] = true
				rtt[seq] = at.Sub(sentAt[seq])
			}
			mu.Unlock()
		}
	}()

	payload := make([]byte, opts.Payload)
	copy(payload, token)
	ticker := time.NewTicker(opts.Interval)
	defer ticker.Stop()
	var sendErr error
send:
	for i := 0; i < opts.Count; i++ {
		if i > 0 {
			select {
			case <-ctx.Done():
				opts.Count = i
				break send
			case <-ticker.C:
			}
		}
		wm := icmp.Message{Type: echoType, Code: 0,
			Body: &icmp.Echo{ID: id, Seq: i, Data: payload}}
		wb, err := wm.Marshal(nil)
		if err != nil {
			return Sequence{}, err
		}
		mu.Lock()
		sentAt[i] = time.Now()
		mu.Unlock()
		if _, err := conn.WriteTo(wb, dest); err != nil {
			// A send that fails locally never reached the path, so it is not
			// evidence about the path and must not be counted as a loss.
			mu.Lock()
			sentAt[i] = time.Time{}
			mu.Unlock()
			sendErr = err
		}
	}

	timer := time.NewTimer(opts.Timeout)
	select {
	case <-timer.C:
	case <-ctx.Done():
	}
	timer.Stop()
	close(stop)
	_ = conn.SetReadDeadline(time.Now())
	<-done

	mu.Lock()
	defer mu.Unlock()
	var seq Sequence
	for i := 0; i < opts.Count; i++ {
		if sentAt[i].IsZero() {
			continue
		}
		seq.Arrived = append(seq.Arrived, got[i])
		if got[i] {
			seq.RTTs = append(seq.RTTs, milliseconds(rtt[i]))
		}
	}
	if len(seq.Arrived) == 0 && sendErr != nil {
		// Every send failed locally, so nothing reached the path and there is
		// no measurement to report. The caller falls back to establishment on
		// this, which is the right response whether the socket was refused or
		// the host has no route.
		return Sequence{}, fmt.Errorf("%w: no probe left this host (%v)", ErrICMPUnavailable, sendErr)
	}
	return seq, nil
}

func listenICMP(target net.IP, localAddress string) (*icmp.PacketConn, bool, error) {
	v6 := target.To4() == nil
	local := localAddress
	if local == "" {
		if v6 {
			local = "::"
		} else {
			local = "0.0.0.0"
		}
	}
	datagram, raw := "udp4", "ip4:icmp"
	if v6 {
		datagram, raw = "udp6", "ip6:ipv6-icmp"
	}
	// Datagram ICMP first: it needs no privilege where the operating system
	// allows it, and a profiling tool an operator has to run as root is a
	// profiling tool they run once.
	if c, err := icmp.ListenPacket(datagram, local); err == nil {
		return c, false, nil
	}
	c, err := icmp.ListenPacket(raw, local)
	if err != nil {
		return nil, false, fmt.Errorf("%w: datagram and raw echo sockets were both refused (%v)", ErrICMPUnavailable, err)
	}
	return c, true, nil
}

func icmpDestination(ip net.IP, raw bool) net.Addr {
	if raw {
		return &net.IPAddr{IP: ip}
	}
	return &net.UDPAddr{IP: ip}
}

// Resolve turns a host into one address, preferring the family of the source
// address the caller intends to bind.
//
// It returns a single address on purpose. Every leg aimed at a destination has
// to be aimed at the same machine, or the comparison between legs is between
// two different paths; where a name is anycast and each vantage point resolves
// it differently, that difference belongs in the report as a finding rather
// than inside a measurement as noise.
func Resolve(ctx context.Context, host, localAddress string) (net.IP, error) {
	if ip := net.ParseIP(host); ip != nil {
		return ip, nil
	}
	addrs, err := net.DefaultResolver.LookupIPAddr(ctx, host)
	if err != nil {
		return nil, err
	}
	wantV6 := false
	if localAddress != "" {
		if ip := net.ParseIP(localAddress); ip != nil && ip.To4() == nil {
			wantV6 = true
		}
	}
	var fallback net.IP
	for _, a := range addrs {
		isV6 := a.IP.To4() == nil
		if isV6 == wantV6 {
			return a.IP, nil
		}
		if fallback == nil {
			fallback = a.IP
		}
	}
	if fallback == nil {
		return nil, fmt.Errorf("no address for %s", host)
	}
	return fallback, nil
}

// EstablishOptions configures a run of TCP establishments.
type EstablishOptions struct {
	// Target is host:port. When Address is set the host is replaced by it, so
	// that this leg reaches the same machine the echo leg did.
	Target       string
	Address      string
	LocalAddress string
	// SOCKS routes the establishment through a local listener, which is how
	// the tunnelled arm is measured with the same instrument as the direct one.
	SOCKS    string
	Count    int
	Interval time.Duration
	Timeout  time.Duration
}

// Establish opens and discards connections, reporting how long each took.
//
// It stops at establishment for the reason queqiaod doctor stops there: a
// handshake is the part of a path a local instrument can hold still, and
// anything past it is a question about a transport rather than about a segment.
// What it adds over doctor is that it is pointed at one segment at a time.
func Establish(ctx context.Context, opts EstablishOptions) Sequence {
	if opts.Count <= 0 {
		opts.Count = 1
	}
	if opts.Timeout <= 0 {
		opts.Timeout = 5 * time.Second
	}
	target := opts.Target
	if opts.Address != "" {
		if _, port, err := net.SplitHostPort(opts.Target); err == nil {
			target = net.JoinHostPort(opts.Address, port)
		}
	}
	dialer := &net.Dialer{}
	if opts.LocalAddress != "" {
		if ip := net.ParseIP(opts.LocalAddress); ip != nil {
			dialer.LocalAddr = &net.TCPAddr{IP: ip}
		}
	}
	var seq Sequence
	for i := 0; i < opts.Count; i++ {
		if ctx.Err() != nil {
			break
		}
		if i > 0 && opts.Interval > 0 {
			timer := time.NewTimer(opts.Interval)
			select {
			case <-ctx.Done():
				timer.Stop()
				return seq
			case <-timer.C:
			}
		}
		attempt, cancel := context.WithTimeout(ctx, opts.Timeout)
		start := time.Now()
		conn, err := dialThrough(attempt, target, opts.SOCKS, dialer)
		elapsed := time.Since(start)
		cancel()
		if err != nil {
			seq.Arrived = append(seq.Arrived, false)
			continue
		}
		_ = conn.Close()
		seq.Arrived = append(seq.Arrived, true)
		seq.RTTs = append(seq.RTTs, milliseconds(elapsed))
	}
	return seq
}

// Summarize reduces a run to the figures a verdict is read from.
//
// The tail threshold is absolute rather than a multiple of the minimum because
// what it is looking for is absolute: a lost handshake packet costs a
// retransmission timeout, which is a second on the initial send and does not
// scale with how far away the peer is.
func Summarize(name, from, to, method string, seq Sequence) Leg {
	leg := Leg{Name: name, From: from, To: to, Method: method, Sent: len(seq.Arrived)}
	if leg.Sent == 0 {
		return leg
	}
	pattern := lossmodel.Analyze(seq.Arrived)
	leg.Arrived = leg.Sent - pattern.Lost
	leg.Loss = pattern.Loss
	leg.BurstFactor = round3(pattern.BurstFactor)
	leg.LongestBurst = pattern.LongestBurst
	// A run with no arrivals has no pattern to report. Its mean burst is one
	// divided by an arrival rate of zero, and its burst factor is that infinity
	// multiplied by a loss rate of one, which is NaN. Left in place that is not
	// merely a meaningless figure: JSON has no NaN, so one blocked leg would
	// make the entire report unserialisable, and the report is the form meant
	// to be attached to a bug.
	if !finite(leg.BurstFactor) {
		leg.BurstFactor = 0
	}
	if leg.Arrived == 0 {
		leg.Blocked = true
		return leg
	}
	sorted := append([]float64(nil), seq.RTTs...)
	sort.Float64s(sorted)
	leg.MinMS = round3(sorted[0])
	leg.P50MS = round3(quantile(sorted, 0.50))
	leg.P99MS = round3(quantile(sorted, 0.99))
	var slow int
	for _, v := range sorted {
		if v > sorted[0]+tailThresholdMS {
			slow++
		}
	}
	leg.TailRate = round3(float64(slow) / float64(len(sorted)))
	return leg
}

// tailThresholdMS is one initial retransmission timeout, rounded down. A
// handshake that took this much longer than the fastest one on the same leg
// most likely retransmitted a packet.
const tailThresholdMS = 900

// quantile reads a percentile by nearest rank, which is the convention
// cmd/pathmeasure and queqiaod doctor already report with. Interpolating would
// invent a value between two measurements that were both real.
func quantile(sorted []float64, p float64) float64 {
	if len(sorted) == 0 {
		return 0
	}
	rank := int(p*float64(len(sorted))+0.5) - 1
	if rank < 0 {
		rank = 0
	}
	if rank >= len(sorted) {
		rank = len(sorted) - 1
	}
	return sorted[rank]
}

func milliseconds(d time.Duration) float64 { return float64(d.Microseconds()) / 1000 }

func round3(v float64) float64 { return math.Round(v*1000) / 1000 }

// finite reports whether a figure can be both believed and serialised.
func finite(v float64) bool { return !math.IsNaN(v) && !math.IsInf(v, 0) }

// Reference is one anchor measured from one vantage point with both
// instruments pointed at it.
//
// Both are needed because they fail differently, and the difference is the
// finding. Echo counts packets and is the only loss instrument here; TCP
// establishment counts nothing but travels as ordinary traffic. A network that
// answers echo cleanly while refusing to complete a handshake to the same
// address has not lost anything -- it has filtered something, which is a
// different fact with a different remedy, and on the paths this project is
// deployed across it is the ordinary case rather than the exotic one.
type Reference struct {
	Target  string `json:"target"`
	Address string `json:"address,omitempty"`
	// Echo is the packet-counting instrument, and Establish the traffic-shaped
	// one. Either may be unusable on its own without the reference being
	// worthless.
	Echo      Leg    `json:"echo"`
	Establish Leg    `json:"establish"`
	Error     string `json:"error,omitempty"`
}

// Health returns the leg this reference's link should be judged on, preferring
// the packet counter and falling back to establishment where no echo socket
// was available -- which is the ordinary case on a Linux host whose
// ping_group_range does not cover the caller.
func (r Reference) Health() (Leg, bool) {
	if r.Echo.Usable() {
		return r.Echo, true
	}
	if r.Establish.Usable() {
		return r.Establish, true
	}
	return Leg{}, false
}

// Filtered reports the signature of a blocked destination rather than a lossy
// one: the address answers echo requests, and a handshake to it never
// completes.
func (r Reference) Filtered() bool {
	return r.Echo.Usable() && r.Echo.Loss < LossyLoss && r.Establish.Sent > 0 && !r.Establish.Usable()
}
