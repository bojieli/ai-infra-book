package main

import (
	"context"
	"crypto/tls"
	"fmt"
	"math"
	"net"
	"sort"
	"strings"
	"time"

	"golang.org/x/net/proxy"
)

// This file adds the one measurement a deployment needs before it exists and
// cannot get from anywhere else: whether this gateway is on the useful side of
// this client's path to a destination it actually calls.
//
// The rest of the doctor checks preconditions on the host. Those are worth
// checking and they are not the question an operator gets wrong. The question
// an operator gets wrong is placement, because the transport improves the
// client-to-gateway segment and nothing past it, so a gateway sited on the
// wrong side of the traffic's real bottleneck lengthens the path while every
// local check passes. A destination fronted by an anycast edge is the ordinary
// way this happens: the session terminates at a point of presence near the
// client, the long haul runs inside the provider's own backbone where neither
// end of this transport can reach it, and routing that traffic through a
// distant gateway adds the whole gateway leg for nothing.
//
// What follows measures connection establishment and stops there. Establishment
// is what placement determines, and it is the part a local instrument can hold
// still. Throughput, loss, and completion time under load belong to
// cmd/pathprobe and cmd/pathmeasure, which drive the path rather than sampling
// it, and this command should not grow into a worse copy of either.

// latency reduces a set of establishment samples to the three figures a
// placement decision is read from.
//
// The minimum is the path's own floor -- the sample least contaminated by a
// queue, and the reference a delay-bounded controller holds itself against. The
// median is what a caller usually gets. The tail is what a caller held to a p99
// is held to, and it moves independently of the median often enough that
// reporting either alone is misleading: on the characterised path a warm
// request sat at 240.9ms at the median and 916.7ms at p99 in a minute when the
// path was erasing, a spread no median would have shown.
type latency struct {
	N   int     `json:"n"`
	Min float64 `json:"min_ms"`
	P50 float64 `json:"p50_ms"`
	P99 float64 `json:"p99_ms"`
}

func (l latency) String() string {
	if l.N == 0 {
		return "no samples"
	}
	return fmt.Sprintf("min %.1fms p50 %.1fms p99 %.1fms (n=%d)", l.Min, l.P50, l.P99, l.N)
}

// summarize sorts a copy so a caller's slice keeps the order it was collected
// in, which is what the position analysis below still needs.
func summarize(samples []float64) latency {
	if len(samples) == 0 {
		return latency{}
	}
	s := append([]float64(nil), samples...)
	sort.Float64s(s)
	return latency{N: len(s), Min: s[0], P50: quantile(s, 0.50), P99: quantile(s, 0.99)}
}

// quantile reads a percentile off an already sorted sample set by nearest rank,
// which is the same convention cmd/pathmeasure reports with. Interpolating
// would invent a value between two measurements that were both real.
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

// probeGateway establishes and discards TCP connections to the gateway.
//
// The figure it produces is used twice: on its own, as the round trip every
// tunnelled flow pays before it reaches anything, and as the term subtracted
// from a tunnelled establishment to leave the gateway's own hop to the
// destination. A single dial cannot serve either purpose, because one sample
// carries whatever the local stack was doing at the time.
func probeGateway(ctx context.Context, endpoint string, rounds int) (latency, error) {
	var samples []float64
	var lastErr error
	var dialer net.Dialer
	for i := 0; i < rounds; i++ {
		if ctx.Err() != nil {
			break
		}
		start := time.Now()
		conn, err := dialer.DialContext(ctx, "tcp", endpoint)
		if err != nil {
			lastErr = err
			continue
		}
		samples = append(samples, float64(time.Since(start).Microseconds())/1000)
		_ = conn.Close()
	}
	if len(samples) == 0 {
		return latency{}, lastErr
	}
	return summarize(samples), nil
}

// destinationProbe is one destination measured both ways.
type destinationProbe struct {
	Target      string  `json:"target"`
	TLS         bool    `json:"tls"`
	Direct      latency `json:"direct"`
	Tunneled    latency `json:"tunneled"`
	DirectError string  `json:"direct_error,omitempty"`
	TunnelError string  `json:"tunnel_error,omitempty"`
	// ArmEffect and OrderEffect are the two candidate explanations for the
	// difference between the arms, in milliseconds. The second is the noise
	// floor of the first.
	ArmEffect   float64 `json:"arm_effect_ms"`
	OrderEffect float64 `json:"order_effect_ms"`
	// GatewayLeg is the measured client-to-gateway round trip, and FarLeg is
	// what is left of a tunnelled establishment once it is removed. FarLeg is
	// a derivation, not a measurement, and Decomposed says whether there was
	// enough to derive it from.
	GatewayLeg float64 `json:"gateway_leg_ms,omitempty"`
	FarLeg     float64 `json:"gateway_to_destination_ms,omitempty"`
	Decomposed bool    `json:"decomposed"`
}

// probeDestination compares reaching one destination directly against reaching
// it through the local SOCKS listener.
//
// It alternates the arms every round and reports the order effect beside the
// arm effect, because this project has already paid for the lesson that a
// comparison run one way round measures the path's drift and calls it the
// change: on the characterised path, position in the sequence was worth 158ms
// where the policy under test was worth 2.4ms, and sorting the arms produced a
// 53% win that reversed when the order reversed. The same rule that governs
// cmd/pathmeasure's ab mode governs this, for the same reason.
func probeDestination(ctx context.Context, target, socksAddr string, rounds int, gateway latency) destinationProbe {
	p := destinationProbe{Target: target, TLS: wantsTLS(target)}

	// One establishment on each arm is thrown away before anything is
	// recorded. It pays for the local resolver cache, the gateway's resolver
	// cache, and a tunnel that may not yet have a lane open, none of which a
	// steady-state comparison should be charged for. A cold tunnel is a real
	// cost and a real advantage of this transport, but it is a completion-time
	// question that cmd/pathmeasure answers with a workload, not something to
	// smuggle into a placement check as a one-off outlier.
	_, _ = establish(ctx, target, "", p.TLS)
	_, _ = establish(ctx, target, socksAddr, p.TLS)

	var direct, tunneled, first, second []float64
	for r := 0; r < rounds; r++ {
		if ctx.Err() != nil {
			break
		}
		for _, directFirst := range []bool{true, false} {
			firstProxy, secondProxy := "", socksAddr
			if !directFirst {
				firstProxy, secondProxy = socksAddr, ""
			}
			fs, ferr := establish(ctx, target, firstProxy, p.TLS)
			ss, serr := establish(ctx, target, secondProxy, p.TLS)
			d, t, derr, terr := fs, ss, ferr, serr
			if !directFirst {
				d, t, derr, terr = ss, fs, serr, ferr
			}
			if derr == nil {
				direct = append(direct, ms(d))
			} else if p.DirectError == "" {
				p.DirectError = derr.Error()
			}
			if terr == nil {
				tunneled = append(tunneled, ms(t))
			} else if p.TunnelError == "" {
				p.TunnelError = terr.Error()
			}
			if ferr == nil {
				first = append(first, ms(fs))
			}
			if serr == nil {
				second = append(second, ms(ss))
			}
		}
	}

	p.Direct, p.Tunneled = summarize(direct), summarize(tunneled)
	if p.Direct.N > 0 && p.Tunneled.N > 0 {
		p.ArmEffect = absDelta(p.Direct.P50, p.Tunneled.P50)
		p.OrderEffect = absDelta(summarize(first).P50, summarize(second).P50)
	}
	if p.Tunneled.N > 0 && gateway.N > 0 {
		p.GatewayLeg = gateway.P50
		p.FarLeg = p.Tunneled.P50 - gateway.P50
		if p.FarLeg < 0 {
			p.FarLeg = 0
		}
		p.Decomposed = true
	}
	// Every figure here came from a microsecond clock, so a difference of two
	// of them carries a tail of binary noise that a JSON reader would have to
	// decide whether to trust. Rounding back to the resolution the samples
	// actually had answers that once, here.
	p.ArmEffect, p.OrderEffect, p.FarLeg = round3(p.ArmEffect), round3(p.OrderEffect), round3(p.FarLeg)
	return p
}

// establish opens one connection to target and returns how long it took to
// become usable, through the SOCKS listener when one is given.
//
// The tunnelled arm resolves the name at the gateway and the direct arm
// resolves it locally, which is not a flaw in the comparison but the thing
// being compared: an anycast name resolves to whatever is near whoever asked,
// so a name looked up at the gateway and the same name looked up here can be
// two different machines on two different continents. Resolving once and
// dialling both arms at the same address would hide exactly the case this
// check exists to find.
//
// TLS is included where the port says it is expected, because a handshake is a
// second round trip on the same path and doubles the signal without doubling
// the interpretation.
//
// The certificate is verified, and that is load-bearing rather than incidental.
// The two arms resolve the name independently and may therefore reach two
// different machines, which is the whole point of the comparison and also its
// one way of going quietly wrong: two arms that reached two unrelated services
// would produce a difference with no topological meaning. A chain that
// validates for the requested name is the cheapest available evidence that
// both arms arrived somewhere entitled to answer for it. A destination that
// answers TCP and then fails the handshake is reported as an error rather than
// silently measured as a bare connect.
func establish(ctx context.Context, target, socksAddr string, useTLS bool) (time.Duration, error) {
	start := time.Now()
	conn, err := dialTarget(ctx, target, socksAddr)
	if err != nil {
		return 0, err
	}
	defer func() { _ = conn.Close() }()
	if !useTLS {
		return time.Since(start), nil
	}
	host, _, splitErr := net.SplitHostPort(target)
	if splitErr != nil {
		return 0, splitErr
	}
	tc := tls.Client(conn, &tls.Config{ServerName: host, MinVersion: tls.VersionTLS12})
	if err := tc.HandshakeContext(ctx); err != nil {
		return 0, err
	}
	return time.Since(start), nil
}

func dialTarget(ctx context.Context, target, socksAddr string) (net.Conn, error) {
	if socksAddr == "" {
		var d net.Dialer
		return d.DialContext(ctx, "tcp", target)
	}
	d, err := proxy.SOCKS5("tcp", socksAddr, nil, &net.Dialer{})
	if err != nil {
		return nil, err
	}
	cd, ok := d.(proxy.ContextDialer)
	if !ok {
		return nil, fmt.Errorf("socks5 dialer for %s does not honour a context", socksAddr)
	}
	return cd.DialContext(ctx, "tcp", target)
}

// checkSOCKSListener dials the local listener before any destination is
// probed, so that a client which is simply not running is reported once as
// itself rather than once per destination as a connection failure.
func checkSOCKSListener(ctx context.Context, socksAddr string) check {
	var d net.Dialer
	conn, err := d.DialContext(ctx, "tcp", socksAddr)
	if err != nil {
		return check{Name: "socks_listener", Status: "warn",
			Detail: fmt.Sprintf("%v; no destination could be compared through the tunnel. "+
				"Start the client, or name the listener with --socks", err)}
	}
	_ = conn.Close()
	return check{Name: "socks_listener", Status: "pass", Detail: socksAddr}
}

// Thresholds for the placement verdict.
//
// A tunnel always adds a hop, so a tunnelled establishment being slower than a
// direct one is the ordinary case and not a finding. What separates a healthy
// deployment from a misplaced gateway is how much slower, relative to the
// direct path: a client whose direct path to the destination is genuinely long
// pays a small fraction extra to route through a gateway near it, while a
// client already sitting a few milliseconds from an anycast edge pays the whole
// gateway leg and has no erasure on that short hop to earn it back.
//
// The ratios are round numbers chosen to sit either side of that difference
// rather than measured constants, and the absolute floor keeps a couple of
// milliseconds on a short path from reading as a topology problem. The order
// effect gates the warning as well: a difference smaller than the drift
// measured in the same minutes has not been resolved by this comparison.
const (
	placementRatioClean    = 1.2
	placementRatioMisplace = 2.0
	placementFloorMS       = 5.0
)

// checkPlacement turns one probe into the verdict an operator can act on.
func checkPlacement(p destinationProbe) check {
	name := "destination:" + p.Target
	switch {
	case p.Direct.N == 0 && p.Tunneled.N == 0:
		return check{Name: name, Status: "fail",
			Detail: fmt.Sprintf("neither arm reached it. direct: %s. tunnel: %s",
				orNone(p.DirectError), orNone(p.TunnelError))}
	case p.Tunneled.N == 0:
		return check{Name: name, Status: "fail",
			Detail: fmt.Sprintf("the tunnel did not reach it (%s), though a direct connection did at %s. "+
				"A destination the gateway cannot open is a gateway problem, not a placement one",
				orNone(p.TunnelError), p.Direct)}
	case p.Direct.N == 0:
		return check{Name: name, Status: "pass",
			Detail: fmt.Sprintf("no direct connection completed (%s), and the tunnel reached it at %s. "+
				"Placement is not a latency question where the tunnel is the only path",
				orNone(p.DirectError), p.Tunneled)}
	}

	ratio := p.Tunneled.P50 / max(p.Direct.P50, 0.001)
	excess := p.Tunneled.P50 - p.Direct.P50
	detail := fmt.Sprintf("direct %s; tunnel %s; %s", p.Direct, p.Tunneled, decomposition(p))

	if p.OrderEffect >= p.ArmEffect {
		return check{Name: name, Status: "warn",
			Detail: fmt.Sprintf("%s. ORDER DOMINATES: the path drifted %.1fms between arms and the arms "+
				"differ by %.1fms, so this comparison has not resolved the difference. Re-run it, "+
				"or take the question to cmd/pathmeasure -mode ab with more rounds",
				detail, p.OrderEffect, p.ArmEffect)}
	}
	if ratio > placementRatioMisplace && excess > placementFloorMS && excess > p.OrderEffect {
		return check{Name: name, Status: "warn",
			Detail: fmt.Sprintf("%s. The tunnel is %.1fx the direct establishment, so this destination is "+
				"served closer to this client than the gateway is. Check whether the name is fronted by "+
				"an anycast edge: if the session already terminates near this client, the long haul runs "+
				"inside the provider's network where this transport cannot reach it, and the gateway leg "+
				"is added for nothing", detail, ratio)}
	}
	if ratio > placementRatioClean {
		return check{Name: name, Status: "pass",
			Detail: fmt.Sprintf("%s. The tunnel adds %.1fms, which the transfer has to earn back. "+
				"Whether it does is a workload question: cmd/pathmeasure -mode workload against this "+
				"endpoint, with the direct arm tuned", detail, excess)}
	}
	return check{Name: name, Status: "pass",
		Detail: fmt.Sprintf("%s. The tunnel is %.2fx the direct establishment, so the gateway is not "+
			"costing this destination a detour", detail, ratio)}
}

// decomposition splits a tunnelled establishment into the leg this transport
// carries and the leg it does not, which is what makes a verdict actionable:
// a large gateway leg is a placement decision the operator can revisit, and a
// large far leg is the gateway's own transit, which moving the client will not
// change.
// The far leg here is a subtraction, and queqiaod segments --ssh measures the
// same leg from the gateway itself. Two commands answering one question with
// two methods will disagree, so the derived one has to name the measured one
// rather than let a reader take a subtraction for an observation.
func decomposition(p destinationProbe) string {
	if !p.Decomposed {
		return "the gateway leg was not measured, so the tunnelled time is not decomposed; " +
			"queqiaod segments measures the legs separately"
	}
	return fmt.Sprintf("of which %.1fms is the leg to the gateway and about %.1fms is the gateway's own hop "+
		"to the destination -- a subtraction rather than a measurement, which queqiaod segments --ssh "+
		"takes from the gateway itself, along with the loss on each leg that this check cannot see",
		p.GatewayLeg, p.FarLeg)
}

// wantsTLS decides whether a handshake belongs in the measurement. Port 443 is
// the case worth covering and guessing more widely would turn a refused
// handshake into a reported failure on a destination that was answering fine.
func wantsTLS(target string) bool {
	_, port, err := net.SplitHostPort(target)
	return err == nil && port == "443"
}

func ms(d time.Duration) float64 { return float64(d.Microseconds()) / 1000 }

func round3(v float64) float64 { return math.Round(v*1000) / 1000 }

func absDelta(a, b float64) float64 {
	if a > b {
		return a - b
	}
	return b - a
}

func orNone(s string) string {
	if s == "" {
		return "no error recorded"
	}
	return s
}

// stringList collects a flag given more than once, so several destinations can
// be probed in the run whose report is read as a whole.
type stringList []string

func (s *stringList) String() string { return strings.Join(*s, ",") }

func (s *stringList) Set(v string) error {
	if v == "" {
		return fmt.Errorf("empty value")
	}
	*s = append(*s, v)
	return nil
}
