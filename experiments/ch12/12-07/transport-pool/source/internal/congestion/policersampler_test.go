package congestion

import (
	"sort"
	"testing"
	"time"

	quiccongestion "github.com/apernet/quic-go/congestion"
	"github.com/apernet/quic-go/monotime"
)

// policer is a token bucket that admits or drops, and never queues, which is
// what makes a policed path produce loss with no delay.
type policer struct {
	rate    float64 // bytes per second
	bucket  float64
	tokens  float64
	refill  time.Duration
	nextAt  time.Duration
	started bool
}

func (p *policer) admit(at time.Duration, size int) bool {
	quantum := p.rate * p.refill.Seconds()
	if !p.started {
		p.started, p.tokens, p.nextAt = true, p.bucket, at
	}
	for p.nextAt <= at {
		if p.tokens += quantum; p.tokens > p.bucket {
			p.tokens = p.bucket
		}
		p.nextAt += p.refill
	}
	if p.tokens < float64(size) {
		return false
	}
	p.tokens -= float64(size)
	return true
}

type samplerEvent struct {
	at    time.Duration
	send  bool
	pn    quiccongestion.PacketNumber
	acked bool
}

// driveThroughPolicer runs the estimator against a sender that offers traffic
// far faster than a policer will pass it, with every event processed in
// timestamp order. Getting that ordering wrong is what made an earlier attempt
// at this measurement report 4,000 B/s on a 250 KB/s path.
func driveThroughPolicer(t *testing.T, offered, shaped float64, rtt time.Duration, seconds float64) (tuicBandwidthEstimator, []bandwidthSampleTrace) {
	return driveThroughPolicerBursty(t, offered, shaped, rtt, seconds, 1)
}

// driveThroughPolicerBursty offers the same average rate in flights of burst
// packets rather than evenly spaced, which is what a paced sender does and what
// an evenly-spaced harness cannot reproduce.
func driveThroughPolicerBursty(t *testing.T, offered, shaped float64, rtt time.Duration, seconds float64, burst int) (tuicBandwidthEstimator, []bandwidthSampleTrace) {
	t.Helper()
	const size = 1200
	e := newTUICBandwidthEstimator()
	var traces []bandwidthSampleTrace
	e.sampleTrace = func(s bandwidthSampleTrace) { traces = append(traces, s) }

	p := &policer{rate: shaped, refill: 8 * time.Millisecond}
	p.bucket = shaped*p.refill.Seconds() + size

	if burst < 1 {
		burst = 1
	}
	sendGap := time.Duration(float64(time.Second) * size / offered)
	flightGap := sendGap * time.Duration(burst)
	var events []samplerEvent
	pn := quiccongestion.PacketNumber(0)
	for at := time.Duration(0); at < time.Duration(seconds*float64(time.Second)); at += flightGap {
		for i := 0; i < burst; i++ {
			// A flight leaves back to back, then the sender waits.
			sendAt := at + time.Duration(i)*time.Microsecond
			admitted := p.admit(sendAt, size)
			events = append(events, samplerEvent{at: sendAt, send: true, pn: pn})
			events = append(events, samplerEvent{at: sendAt + rtt, pn: pn, acked: admitted})
			pn++
		}
	}
	sort.SliceStable(events, func(i, j int) bool { return events[i].at < events[j].at })

	base := monotime.Now()
	inflight := uint64(0)
	round := uint64(1)
	roundEnd := quiccongestion.PacketNumber(-1)
	maxSent := quiccongestion.PacketNumber(-1)
	var batch []quiccongestion.AckedPacketInfo
	var batchAt time.Duration
	flush := func() {
		if len(batch) == 0 {
			return
		}
		largest := batch[len(batch)-1].PacketNumber
		if largest > roundEnd {
			roundEnd = maxSent
			round++
		}
		e.onAckBatch(base.Add(batchAt), batch, round)
		batch = nil
	}
	for _, ev := range events {
		if ev.send {
			flush()
			e.onSentPacket(base.Add(ev.at), ev.pn, size, inflight, true)
			inflight += size
			maxSent = ev.pn
			continue
		}
		if !ev.acked {
			if inflight >= size {
				inflight -= size
			}
			continue
		}
		if len(batch) > 0 && ev.at != batchAt {
			flush()
		}
		batchAt = ev.at
		batch = append(batch, quiccongestion.AckedPacketInfo{
			PacketNumber: ev.pn, BytesAcked: size, ReceivedTime: base.Add(ev.at),
		})
		if inflight >= size {
			inflight -= size
		}
	}
	flush()
	return e, traces
}

// The measurement three failed fixes were missing. It reports what the
// estimator concludes about a policed path and, when it is wrong, which of the
// two quantities behind the sample is responsible.
func TestWhatTheSamplerSeesOnAPolicedPath(t *testing.T) {
	const (
		shaped  = 250_000.0
		offered = 9_000_000.0
		rtt     = 300 * time.Millisecond
	)
	e, traces := driveThroughPolicer(t, offered, shaped, rtt, 6)
	_ = traces
	if len(traces) == 0 {
		t.Fatal("no samples were produced, so this measured nothing")
	}

	estimate := float64(e.estimate())
	t.Logf("offered %.0f B/s through a %.0f B/s policer: estimate %.0f (%.2fx), %d samples",
		offered, shaped, estimate, estimate/shaped, len(traces))

	// The distribution behind the maximum. If the typical sample is right and
	// only the tail is wrong, the statistic is the problem; if the typical
	// sample is already wrong, the inputs are.
	rates := make([]float64, 0, len(traces))
	var intervals []time.Duration
	for _, s := range traces {
		rates = append(rates, float64(s.Sample))
		intervals = append(intervals, s.AckInterval)
	}
	sort.Float64s(rates)
	sort.Slice(intervals, func(i, j int) bool { return intervals[i] < intervals[j] })
	q := func(v []float64, p float64) float64 { return v[int(p*float64(len(v)-1))] }
	qd := func(v []time.Duration, p float64) time.Duration { return v[int(p*float64(len(v)-1))] }
	t.Logf("  sample rate    p50=%.0f (%.2fx) p90=%.0f (%.2fx) p99=%.0f (%.2fx) max=%.0f (%.2fx)",
		q(rates, .5), q(rates, .5)/shaped, q(rates, .9), q(rates, .9)/shaped,
		q(rates, .99), q(rates, .99)/shaped, rates[len(rates)-1], rates[len(rates)-1]/shaped)
	t.Logf("  ack interval   p50=%v p90=%v p99=%v max=%v",
		qd(intervals, .5).Round(time.Millisecond), qd(intervals, .9).Round(time.Millisecond),
		qd(intervals, .99).Round(time.Millisecond), intervals[len(intervals)-1].Round(time.Millisecond))

	worst := traces[0]
	for _, s := range traces {
		if s.Sample > worst.Sample {
			worst = s
		}
	}
	t.Logf("  worst sample: rate=%d ack=%d bytes over %v, send=%d bytes over %v, applimited=%v",
		worst.Sample, worst.AckedDelta, worst.AckInterval.Round(time.Microsecond),
		worst.SentDelta, worst.SendInterval.Round(time.Microsecond), worst.AppLimited)
}

// A negative result, kept because it was the most plausible remaining
// explanation and it is wrong.
//
// A paced sender emits flights rather than evenly spaced packets, and a flight
// arriving at a token bucket partly passes and partly drops, so the packets
// that do pass leave together and are acknowledged together -- a short
// measurement window carrying a lot of bytes, which is the shape a maximum
// filter would report as the path. It does not happen. From flights of one to
// flights of sixty-four the estimate stays within two per cent of the policer's
// rate.
//
// So burstiness is not why the full stack reads twice the path while the
// estimator driven directly reads 1.01 times it. Whatever the difference is, it
// is not in the sampler's response to bursts.
func TestBurstinessDoesNotInflateTheEstimate(t *testing.T) {
	const (
		shaped  = 250_000.0
		offered = 9_000_000.0
		rtt     = 300 * time.Millisecond
	)
	for _, burst := range []int{1, 4, 16, 64} {
		e, traces := driveThroughPolicerBursty(t, offered, shaped, rtt, 6, burst)
		if len(traces) == 0 {
			t.Fatalf("burst %d produced no samples", burst)
		}
		estimate := float64(e.estimate())
		t.Logf("flights of %2d packets: estimate %.0f (%.2fx the path), %d samples",
			burst, estimate, estimate/shaped, len(traces))
		if estimate > shaped*1.5 {
			t.Errorf("flights of %d inflated the estimate to %.2fx; that would make burstiness "+
				"an explanation for the full stack's reading, which this test records it is not",
				burst, estimate/shaped)
		}
	}
}

// The summary the running stack publishes has to describe the same samples the
// trace hook sees, or reading it off a real path proves nothing.
func TestTheSampleSummaryMatchesTheSamples(t *testing.T) {
	const (
		shaped  = 250_000.0
		offered = 9_000_000.0
		rtt     = 300 * time.Millisecond
	)
	e, traces := driveThroughPolicer(t, offered, shaped, rtt, 6)
	count, mean, max, delivered, interval := e.sampleSummary()
	if count != uint64(len(traces)) {
		t.Fatalf("summary counted %d samples, the trace saw %d", count, len(traces))
	}

	var sum, widest uint64
	var widestTrace bandwidthSampleTrace
	for _, s := range traces {
		sum += s.Sample
		if s.Sample > widest {
			widest, widestTrace = s.Sample, s
		}
	}
	if max != widest {
		t.Fatalf("summary's widest sample is %d, the trace's is %d", max, widest)
	}
	if want := sum / uint64(len(traces)); mean != want {
		t.Fatalf("summary mean %d against %d over the traced samples", mean, want)
	}
	// The interval and delivery must come from the same sample as the maximum,
	// which is the whole point of keeping them: a rate divorced from its window
	// cannot be read.
	if interval != widestTrace.AckInterval || delivered != widestTrace.AckedDelta {
		t.Fatalf("summary reports %v over %d bytes for its widest sample; the trace says %v over %d",
			interval, delivered, widestTrace.AckInterval, widestTrace.AckedDelta)
	}
	t.Logf("on a policed path: %d samples, mean %d (%.2fx), max %d (%.2fx) over %v carrying %d bytes",
		count, mean, float64(mean)/shaped, max, float64(max)/shaped, interval.Round(time.Millisecond), delivered)
}
