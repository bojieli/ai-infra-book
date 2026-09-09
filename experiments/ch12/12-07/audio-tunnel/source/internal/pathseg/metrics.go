package pathseg

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"strings"
	"time"
)

// TunnelView is what the running transport already knows about the one segment
// it sits on, read from the endpoint queqiaod publishes with --metrics-listen.
//
// This is the best measurement of the client-to-gateway segment that exists,
// and no external probe can match it. It was taken on the real four-tuple, at
// the real rate, in the direction it names, by the code that had to decide what
// to do about it -- where an echo probe offers a few packets a second on a
// path whose loss behaviour changes with load, and cannot tell the two
// directions apart at all. On the path this project was built for, that last
// point is the whole story: upstream and downstream differed by fourteen
// percentage points minutes apart, and a round-trip figure would have averaged
// that into nothing.
//
// It measures only that segment, which is why the rest of this package exists.
type TunnelView struct {
	Present bool `json:"present"`

	// SendErasure is the share of what this endpoint sent that the path did
	// not deliver -- upstream, from a client's point of view. ReceiveErasure
	// is the opposite direction, measured by this endpoint's own decoders
	// rather than inferred from acknowledgements.
	SendErasure     float64 `json:"send_erasure"`
	ReceiveErasure  float64 `json:"receive_erasure"`
	ReceiveResidual float64 `json:"receive_residual"`

	MinRTTMS      float64 `json:"min_rtt_ms"`
	SmoothedRTTMS float64 `json:"smoothed_rtt_ms"`
	LatestRTTMS   float64 `json:"latest_rtt_ms"`

	Lanes       int     `json:"lanes"`
	ActiveFlows int     `json:"active_flows"`
	DelayBrake  float64 `json:"delay_brake_ratio"`

	// CodedSymbols is the denominator the receive-direction ratios were
	// computed over. It is reported because a ratio without one is not a
	// measurement: an erasure figure drawn from a handful of symbols says
	// nothing, and a report that quoted it anyway would manufacture a finding
	// out of an idle tunnel.
	CodedSymbols   uint64 `json:"coded_symbols"`
	PacketsSent    uint64 `json:"packets_sent"`
	LossObserved   uint64 `json:"loss_observed_packets"`
	Fallbacks      uint64 `json:"fallbacks"`
	LaneFailures   uint64 `json:"lane_failures"`
	FlowStalls     uint64 `json:"flow_stalls_detected"`
	PortHops       uint64 `json:"port_hops"`
	BytesUp        uint64 `json:"bytes_up"`
	BytesDown      uint64 `json:"bytes_down"`
	FlowsFailed    uint64 `json:"flows_failed"`
	FlowsCompleted uint64 `json:"flows_completed"`
}

// significanceFloor is how many coded symbols the receive-direction erasure has
// to be drawn from before it is quoted as a measurement. It is a few seconds of
// an ordinary flow and far below anything a busy tunnel produces, so it
// excludes only the case it is meant to exclude: a tunnel that has been idle.
const significanceFloor = 500

// ReceiveSignificant reports whether the receive-direction erasure was measured
// over enough traffic to be worth attributing to anything.
func (v TunnelView) ReceiveSignificant() bool {
	return v.Present && v.CodedSymbols >= significanceFloor
}

// SendSignificant reports the same for the send direction, whose denominator is
// the packets this endpoint put on the wire.
func (v TunnelView) SendSignificant() bool {
	return v.Present && v.PacketsSent >= significanceFloor
}

// FetchMetrics reads one metrics endpoint.
func FetchMetrics(ctx context.Context, url string) (TunnelView, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return TunnelView{}, err
	}
	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return TunnelView{}, err
	}
	defer func() { _ = resp.Body.Close() }()
	if resp.StatusCode != http.StatusOK {
		return TunnelView{}, fmt.Errorf("%s returned %s", url, resp.Status)
	}
	// A metrics page is a few kilobytes. The cap is there so that a wrong URL
	// pointed at something that streams cannot be read until this process runs
	// out of memory.
	return ParseMetrics(io.LimitReader(resp.Body, 1<<20))
}

// ParseMetrics reads the subset of the exposition format queqiaod emits, which
// is one sample per line with at most one label.
//
// It deliberately does not pull in a Prometheus parser. The producer is in this
// repository, the format it writes is fixed by metrics.Registry.ServeHTTP, and
// a dependency whose job is to tolerate input this endpoint never emits would
// be larger than the code it replaced.
func ParseMetrics(r io.Reader) (TunnelView, error) {
	v := TunnelView{}
	scanner := bufio.NewScanner(r)
	scanner.Buffer(make([]byte, 0, 64*1024), 1<<20)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		name, value, ok := strings.Cut(line, " ")
		if !ok {
			continue
		}
		f, err := strconv.ParseFloat(strings.TrimSpace(value), 64)
		// ParseFloat accepts "NaN" and "+Inf", and a ratio whose denominator
		// was zero upstream would arrive as one of them. Carrying it forward
		// would put a value into the report that JSON cannot encode, so a
		// sample that is not a number is treated as a sample that is not there.
		if err != nil || !finite(f) {
			continue
		}
		v.Present = true
		switch name {
		case `queqiao_erasure_ratio{direction="send"}`:
			v.SendErasure = f
		case `queqiao_erasure_ratio{direction="receive"}`:
			v.ReceiveErasure = f
		case `queqiao_erasure_residual_ratio{direction="receive"}`:
			v.ReceiveResidual = f
		case "queqiao_quic_controller_min_rtt_seconds":
			v.MinRTTMS = round3(f * 1000)
		case "queqiao_quic_smoothed_rtt_seconds":
			v.SmoothedRTTMS = round3(f * 1000)
		case "queqiao_quic_latest_rtt_seconds":
			v.LatestRTTMS = round3(f * 1000)
		case "queqiao_quic_lanes":
			v.Lanes = int(f)
		case "queqiao_active_flows":
			v.ActiveFlows = int(f)
		case "queqiao_delay_brake_ratio":
			v.DelayBrake = f
		case `queqiao_coded_symbols_total{outcome="arrived"}`,
			`queqiao_coded_symbols_total{outcome="recovered"}`,
			`queqiao_coded_symbols_total{outcome="lost"}`:
			v.CodedSymbols += uint64(f)
		case "queqiao_quic_packets_sent":
			v.PacketsSent = uint64(f)
		case "queqiao_quic_loss_observed_packets_total":
			v.LossObserved = uint64(f)
		case "queqiao_fallbacks_total":
			v.Fallbacks = uint64(f)
		case "queqiao_lane_failures_total":
			v.LaneFailures = uint64(f)
		case "queqiao_flow_stalls_detected_total":
			v.FlowStalls = uint64(f)
		case "queqiao_port_hops_total":
			v.PortHops = uint64(f)
		case "queqiao_bytes_up_total":
			v.BytesUp = uint64(f)
		case "queqiao_bytes_down_total":
			v.BytesDown = uint64(f)
		case "queqiao_flows_failed_total":
			v.FlowsFailed = uint64(f)
		case "queqiao_flows_completed_total":
			v.FlowsCompleted = uint64(f)
		}
	}
	if err := scanner.Err(); err != nil {
		return TunnelView{}, err
	}
	if !v.Present {
		return TunnelView{}, fmt.Errorf("no metrics samples found")
	}
	return v, nil
}
