package congestion

import (
	"math"
	"time"

	quiccongestion "github.com/apernet/quic-go/congestion"
	"github.com/apernet/quic-go/monotime"
)

// AdaptiveSender is a conservative, application-independent rate controller.
// It follows the important BBR shape—pace from a delivery-rate estimate and
// keep roughly two BDPs in flight—without requiring the operator to guess a
// link rate. It is deliberately small and easy to audit; the stock apNet
// controller remains the fallback for any unexpected condition.
//
// This is not presented as a new standard congestion-control algorithm. It is
// an experimental controller for the fixed China-to-US path and must be
// benchmarked against the stock controller before deployment.
type AdaptiveSender struct {
	rttStats        quiccongestion.RTTStatsProvider
	maxDatagramSize quiccongestion.ByteCount
	pacer           *pacer

	rateBps    float64
	minRateBps float64
	maxRateBps float64

	cwnd          quiccongestion.ByteCount
	bytesInFlight quiccongestion.ByteCount
	windowStart   monotime.Time
	windowAcked   quiccongestion.ByteCount
	windowLost    quiccongestion.ByteCount
	lastLoss      monotime.Time
	telemetry     telemetryState
}

const (
	adaptiveMinRate = 64 * 1024.0
	adaptiveMaxRate = 200 * 1024 * 1024.0
)

var _ quiccongestion.CongestionControlEx = (*AdaptiveSender)(nil)

// NewAdaptiveSender creates a controller with a low safe starting rate. It
// grows once per RTT in the absence of loss, and backs off promptly when loss
// is observed. minRate and maxRate are bytes per second; zero selects safe
// defaults.
func NewAdaptiveSender(initialPacketSize quiccongestion.ByteCount, minRate, maxRate uint64) *AdaptiveSender {
	if initialPacketSize <= 0 {
		initialPacketSize = quiccongestion.InitialPacketSize
	}
	if minRate == 0 {
		minRate = adaptiveMinRate
	}
	if maxRate == 0 {
		maxRate = adaptiveMaxRate
	}
	if maxRate < minRate {
		maxRate = minRate
	}
	a := &AdaptiveSender{
		maxDatagramSize: initialPacketSize,
		rateBps:         float64(minRate),
		minRateBps:      float64(minRate),
		maxRateBps:      float64(maxRate),
		cwnd:            32 * initialPacketSize,
		telemetry:       newTelemetryState("adaptive"),
	}
	a.pacer = newPacer(a.bandwidth)
	a.publishTelemetry()
	return a
}

func (a *AdaptiveSender) SetRTTStatsProvider(provider quiccongestion.RTTStatsProvider) {
	a.rttStats = provider
	a.updateWindow()
	a.publishTelemetry()
}

func (a *AdaptiveSender) bandwidth() quiccongestion.ByteCount {
	if a.rateBps < a.minRateBps {
		a.rateBps = a.minRateBps
	}
	if a.rateBps > a.maxRateBps {
		a.rateBps = a.maxRateBps
	}
	a.telemetry.pacingRate.Store(uint64(a.rateBps))
	return quiccongestion.ByteCount(a.rateBps)
}

func (a *AdaptiveSender) TimeUntilSend(_ quiccongestion.ByteCount) monotime.Time {
	return a.pacer.timeUntilSend()
}

func (a *AdaptiveSender) HasPacingBudget(now monotime.Time) bool {
	return a.pacer.budget(now) >= a.maxDatagramSize
}

func (a *AdaptiveSender) OnPacketSent(sentTime monotime.Time, bytesInFlight quiccongestion.ByteCount, _ quiccongestion.PacketNumber, bytes quiccongestion.ByteCount, _ bool) {
	a.pacer.sentPacket(sentTime, bytes)
	a.bytesInFlight = bytesInFlight
	a.publishTelemetry()
}

func (a *AdaptiveSender) CanSend(bytesInFlight quiccongestion.ByteCount) bool {
	// quic-go asks this before adding the next packet to bytes in flight.  A
	// packet is admissible only while the current flight is strictly below the
	// window; using <= permits one extra datagram on every scheduling pass and
	// is especially harmful when several independent lanes are probing at once.
	return bytesInFlight < a.GetCongestionWindow()
}

func (a *AdaptiveSender) MaybeExitSlowStart() {}

func (a *AdaptiveSender) OnPacketAcked(_ quiccongestion.PacketNumber, _ quiccongestion.ByteCount, priorInFlight quiccongestion.ByteCount, _ monotime.Time) {
	a.bytesInFlight = priorInFlight
	a.publishTelemetry()
}

// OnCongestionEvent is the legacy per-packet callback. quic-go follows it
// with OnCongestionEventEx when the controller implements the extended API;
// loss adaptation therefore belongs only in the batch callback to avoid
// backing off twice for one loss event.
func (a *AdaptiveSender) OnCongestionEvent(_ quiccongestion.PacketNumber, _ quiccongestion.ByteCount, priorInFlight quiccongestion.ByteCount) {
	a.bytesInFlight = priorInFlight
	a.publishTelemetry()
}

func (a *AdaptiveSender) OnCongestionEventEx(priorInFlight quiccongestion.ByteCount, eventTime monotime.Time, acked []quiccongestion.AckedPacketInfo, lost []quiccongestion.LostPacketInfo) {
	a.bytesInFlight = priorInFlight
	for _, p := range acked {
		a.windowAcked += p.BytesAcked
	}
	var lostBytes uint64
	for _, p := range lost {
		if p.BytesLost > 0 {
			lostBytes = satAddUint64(lostBytes, uint64(p.BytesLost))
		}
		a.windowLost += p.BytesLost
	}
	if lostBytes > 0 {
		a.telemetry.observeLoss(lostBytes, uint64(len(lost)))
	}
	if a.windowStart.IsZero() {
		a.windowStart = eventTime
	}
	if len(lost) > 0 {
		a.lastLoss = eventTime
		// A large loss burst should reduce the rate more strongly than one
		// isolated packet, but never collapse the controller to zero.
		factor := 0.70
		if len(lost) >= 8 {
			factor = 0.55
		}
		a.backoff(factor)
	}
	interval := eventTime.Sub(a.windowStart)
	rtt := a.rtt()
	if interval < 50*time.Millisecond && (rtt <= 0 || interval < rtt/2) {
		return
	}
	if a.windowAcked > 0 && interval > 0 && a.windowLost == 0 {
		sample := float64(a.windowAcked) / interval.Seconds()
		// Increase only after a clean observation window. Using a bounded
		// geometric step avoids the very slow startup seen with CUBIC on this
		// path while still avoiding an unbounded burst.
		target := sample * 1.05
		if target > a.rateBps {
			a.rateBps = minFloat(a.maxRateBps, maxFloat(a.rateBps*1.12, target))
		} else {
			a.rateBps = minFloat(a.maxRateBps, a.rateBps*1.08)
		}
	}
	a.windowAcked, a.windowLost = 0, 0
	a.windowStart = eventTime
	a.updateWindow()
	a.publishTelemetry()
}

func (a *AdaptiveSender) OnRetransmissionTimeout(packetsRetransmitted bool) {
	if packetsRetransmitted {
		a.backoff(0.50)
		a.publishTelemetry()
	}
}

func (a *AdaptiveSender) SetMaxDatagramSize(size quiccongestion.ByteCount) {
	if size <= 0 {
		return
	}
	a.maxDatagramSize = size
	a.pacer.setMaxDatagramSize(size)
	a.updateWindow()
	a.publishTelemetry()
}

func (a *AdaptiveSender) InSlowStart() bool { return false }

func (a *AdaptiveSender) InRecovery() bool {
	return !a.lastLoss.IsZero() && monotime.Since(a.lastLoss) < a.rtt()
}

func (a *AdaptiveSender) GetCongestionWindow() quiccongestion.ByteCount {
	if a.cwnd < 4*a.maxDatagramSize {
		return 4 * a.maxDatagramSize
	}
	return a.cwnd
}

func (a *AdaptiveSender) publishTelemetry() {
	a.telemetry.update(ControllerModeAdaptive, uint64(a.rateBps), uint64(a.bandwidth()), int64(a.GetCongestionWindow()), int64(a.bytesInFlight), a.rtt(), a.InRecovery())
}

func (a *AdaptiveSender) Telemetry() ControllerTelemetry { return a.telemetry.snapshot() }

func (a *AdaptiveSender) backoff(factor float64) {
	if factor <= 0 || factor >= 1 {
		factor = 0.7
	}
	a.rateBps = maxFloat(a.minRateBps, a.rateBps*factor)
	a.updateWindow()
}

func (a *AdaptiveSender) rtt() time.Duration {
	if a.rttStats == nil {
		return 200 * time.Millisecond
	}
	rtt := a.rttStats.SmoothedRTT()
	if rtt <= 0 {
		rtt = a.rttStats.LatestRTT()
	}
	if rtt <= 0 {
		rtt = 200 * time.Millisecond
	}
	return rtt
}

func (a *AdaptiveSender) updateWindow() {
	rtt := a.rtt()
	// Two BDPs leave enough room for ACK compression without creating a
	// standing queue. The minimum is four datagrams for delayed ACKs.
	target := a.rateBps * rtt.Seconds() * 2
	if math.IsNaN(target) || math.IsInf(target, 0) || target < float64(4*a.maxDatagramSize) {
		target = float64(4 * a.maxDatagramSize)
	}
	if target > float64(quiccongestion.MaxCongestionWindowPackets*a.maxDatagramSize) {
		target = float64(quiccongestion.MaxCongestionWindowPackets * a.maxDatagramSize)
	}
	a.cwnd = quiccongestion.ByteCount(target)
}

func minFloat(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}

func maxFloat(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}
