package pathseg

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"os"
	"time"
)

// The gateway half of a profile runs this code, reached over SSH, rather than a
// second implementation driven by parsing some other program's output.
//
// That is the point of the agent. The whole method rests on comparing what one
// vantage point sees with what another sees, and a comparison between two
// instruments measures the instruments as much as the path: a different probe
// size, a different cadence, a different idea of what counts as a timeout, and
// the difference between the two ends is no longer attributable to the network.
// One binary, one set of options, two places.
//
// There is a fallback that parses ping(8) for gateways whose queqiaod is older
// than this command, and it is a fallback precisely because it gives that
// property up; the report says so wherever it is used.

// AgentRequest is what the near side asks the far side to measure.
type AgentRequest struct {
	References []string `json:"references"`
	Count      int      `json:"count"`
	IntervalMS int      `json:"interval_ms"`
	TimeoutMS  int      `json:"timeout_ms"`
	// EstablishCount is kept small: it is a reachability instrument rather than
	// a timing one, and every sample is a real connection to a third party.
	EstablishCount int `json:"establish_count"`
	// MetricsURL is read on the far side, because a gateway publishes its
	// metrics on loopback and the only way to reach them is from there.
	MetricsURL string `json:"metrics_url,omitempty"`
	// PinAddress forces a target to one address, so that both vantage points
	// measure the same machine when the operator wants them to. Left empty,
	// each side resolves for itself, which is what shows up an anycast name
	// that resolves to two different continents.
	PinAddress map[string]string `json:"pin_address,omitempty"`
}

// AgentResponse is what comes back.
type AgentResponse struct {
	Version      string      `json:"version"`
	Hostname     string      `json:"hostname,omitempty"`
	References   []Reference `json:"references"`
	Metrics      TunnelView  `json:"metrics"`
	MetricsError string      `json:"metrics_error,omitempty"`
}

// ProbeConfig is the cadence both vantage points share.
type ProbeConfig struct {
	Count          int
	Interval       time.Duration
	Timeout        time.Duration
	EstablishCount int
	LocalAddress   string
	PinAddress     map[string]string
}

// MeasureReferences points both instruments at each anchor in turn.
//
// The anchors are measured one after another rather than at once. They are
// third parties, and a tool that fans probes out in parallel to several of them
// looks like something other than a diagnostic; the run is short enough that
// the path does not move underneath it, which is the only reason to have
// preferred parallel.
func MeasureReferences(ctx context.Context, targets []string, cfg ProbeConfig) []Reference {
	out := make([]Reference, 0, len(targets))
	for _, target := range targets {
		out = append(out, MeasureReference(ctx, target, cfg))
	}
	return out
}

// MeasureReference measures one anchor. It is separate from the loop above so
// that a caller which wants to say what it is doing between anchors can drive
// the loop itself: a run takes tens of seconds per leg and minutes in total,
// and silence for that long is indistinguishable from a hang.
func MeasureReference(ctx context.Context, target string, cfg ProbeConfig) Reference {
	r := Reference{Target: target}
	host, hostPort := splitReference(target)

	// One address for both instruments. Resolving twice would let the echo leg
	// and the establishment leg land on two machines and turn a load balancer
	// into a finding.
	var ip net.IP
	if pinned := cfg.PinAddress[target]; pinned != "" {
		ip = net.ParseIP(pinned)
	}
	if ip == nil {
		resolved, err := Resolve(ctx, host, cfg.LocalAddress)
		if err != nil {
			r.Error = fmt.Sprintf("resolve %s: %v", host, err)
			return r
		}
		ip = resolved
	}
	r.Address = ip.String()

	seq, err := Ping(ctx, PingOptions{
		Target: ip, LocalAddress: cfg.LocalAddress,
		Count: cfg.Count, Interval: cfg.Interval, Timeout: cfg.Timeout,
	})
	r.Echo = Summarize("echo:"+target, "", target, "icmp", seq)
	r.Echo.Address = r.Address
	if err != nil {
		r.Echo.Error = err.Error()
	}

	establishCount := cfg.EstablishCount
	if establishCount <= 0 {
		establishCount = 3
	}
	eseq := Establish(ctx, EstablishOptions{
		Target: hostPort, Address: r.Address, LocalAddress: cfg.LocalAddress,
		Count: establishCount, Interval: cfg.Interval, Timeout: cfg.Timeout,
	})
	r.Establish = Summarize("establish:"+target, "", target, "tcp-connect", eseq)
	r.Establish.Address = r.Address
	return r
}

// splitReference accepts a bare host or a host:port and returns both forms.
// Port 443 is the default because it is the port a filtered path is filtered
// on, and a reachability check on a port nothing is listening to would report
// every anchor as blocked.
func splitReference(target string) (host, hostPort string) {
	if h, p, err := net.SplitHostPort(target); err == nil {
		return h, net.JoinHostPort(h, p)
	}
	return target, net.JoinHostPort(target, "443")
}

// RunAgent performs one far-side measurement. It is the whole of what the
// remote half does, so that the remote half cannot drift from the near one.
func RunAgent(ctx context.Context, req AgentRequest, version string) AgentResponse {
	cfg := ProbeConfig{
		Count:          req.Count,
		Interval:       time.Duration(req.IntervalMS) * time.Millisecond,
		Timeout:        time.Duration(req.TimeoutMS) * time.Millisecond,
		EstablishCount: req.EstablishCount,
		PinAddress:     req.PinAddress,
	}
	resp := AgentResponse{Version: version}
	if name, err := os.Hostname(); err == nil {
		resp.Hostname = name
	}
	resp.References = MeasureReferences(ctx, req.References, cfg)
	if req.MetricsURL != "" {
		view, err := FetchMetrics(ctx, req.MetricsURL)
		if err != nil {
			resp.MetricsError = err.Error()
		} else {
			resp.Metrics = view
		}
	}
	return resp
}

// DecodeAgentRequest reads a request, bounding it so that a wrong pipe cannot
// be read until this process runs out of memory.
func DecodeAgentRequest(r io.Reader) (AgentRequest, error) {
	var req AgentRequest
	if err := json.NewDecoder(io.LimitReader(r, 1<<20)).Decode(&req); err != nil {
		return AgentRequest{}, err
	}
	if len(req.References) == 0 {
		return AgentRequest{}, fmt.Errorf("the request names no references")
	}
	// The far side is a third party's machine as far as this process is
	// concerned, so the request is bounded here rather than trusted.
	if req.Count <= 0 || req.Count > 1000 {
		req.Count = 50
	}
	if req.IntervalMS <= 0 || req.IntervalMS > 10000 {
		req.IntervalMS = 100
	}
	if req.TimeoutMS <= 0 || req.TimeoutMS > 60000 {
		req.TimeoutMS = 2000
	}
	if req.EstablishCount < 0 || req.EstablishCount > 50 {
		req.EstablishCount = 3
	}
	if len(req.References) > 16 {
		req.References = req.References[:16]
	}
	return req, nil
}
