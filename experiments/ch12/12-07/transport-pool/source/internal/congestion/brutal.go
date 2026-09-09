package congestion

import (
	"time"

	quiccongestion "github.com/apernet/quic-go/congestion"
	"github.com/apernet/quic-go/monotime"
)

// BrutalSender is the Hysteria-style fixed-rate controller. It is useful when
// a measured, operator-supplied per-lane rate is available. It intentionally
// does not infer a target from a short request: use AdaptiveSender for mixed
// traffic and leave this mode for controlled bulk experiments.
type BrutalSender struct {
	rttStats                quiccongestion.RTTStatsProvider
	bps                     quiccongestion.ByteCount
	maxDatagramSize         quiccongestion.ByteCount
	pacer                   *pacer
	ackRate                 float64
	ackCount                uint64
	lossCount               uint64
	lastSample              monotime.Time
	disableLossCompensation bool
	telemetry               telemetryState
}

const (
	brutalMinRate    = 64 * 1024
	brutalMinSamples = 50
)

var _ quiccongestion.CongestionControlEx = (*BrutalSender)(nil)

func NewBrutalSender(bytesPerSecond uint64, disableLossCompensation bool) *BrutalSender {
	if bytesPerSecond < brutalMinRate {
		bytesPerSecond = brutalMinRate
	}
	b := &BrutalSender{
		bps:                     quiccongestion.ByteCount(bytesPerSecond),
		maxDatagramSize:         quiccongestion.InitialPacketSize,
		ackRate:                 1,
		disableLossCompensation: disableLossCompensation,
		telemetry:               newTelemetryState("brutal"),
	}
	b.pacer = newPacer(b.bandwidth)
	b.publishTelemetry()
	return b
}

func (b *BrutalSender) SetRTTStatsProvider(r quiccongestion.RTTStatsProvider) {
	b.rttStats = r
	b.publishTelemetry()
}
func (b *BrutalSender) bandwidth() quiccongestion.ByteCount {
	if b.ackRate <= 0 {
		b.ackRate = 1
	}
	b.telemetry.pacingRate.Store(uint64(float64(b.bps) / b.ackRate))
	return quiccongestion.ByteCount(float64(b.bps) / b.ackRate)
}
func (b *BrutalSender) TimeUntilSend(_ quiccongestion.ByteCount) monotime.Time {
	return b.pacer.timeUntilSend()
}
func (b *BrutalSender) HasPacingBudget(now monotime.Time) bool {
	return b.pacer.budget(now) >= b.maxDatagramSize
}
func (b *BrutalSender) OnPacketSent(sentTime monotime.Time, _ quiccongestion.ByteCount, _ quiccongestion.PacketNumber, bytes quiccongestion.ByteCount, _ bool) {
	b.pacer.sentPacket(sentTime, bytes)
	b.publishTelemetry()
}
func (b *BrutalSender) CanSend(bytesInFlight quiccongestion.ByteCount) bool {
	return bytesInFlight < b.GetCongestionWindow()
}
func (b *BrutalSender) MaybeExitSlowStart() {}
func (b *BrutalSender) OnPacketAcked(_ quiccongestion.PacketNumber, _ quiccongestion.ByteCount, _ quiccongestion.ByteCount, _ monotime.Time) {
}
func (b *BrutalSender) OnCongestionEvent(_ quiccongestion.PacketNumber, _ quiccongestion.ByteCount, _ quiccongestion.ByteCount) {
}
func (b *BrutalSender) OnRetransmissionTimeout(_ bool) {}
func (b *BrutalSender) InSlowStart() bool              { return false }
func (b *BrutalSender) InRecovery() bool               { return false }
func (b *BrutalSender) GetCongestionWindow() quiccongestion.ByteCount {
	rtt := 200 * time.Millisecond
	if b.rttStats != nil {
		if measured := b.rttStats.SmoothedRTT(); measured > 0 {
			rtt = measured
		}
	}
	cwnd := quiccongestion.ByteCount(float64(b.bps) * rtt.Seconds() * 2 / b.ackRate)
	return maxByteCount(b.maxDatagramSize, cwnd)
}
func (b *BrutalSender) SetMaxDatagramSize(size quiccongestion.ByteCount) {
	if size > 0 {
		b.maxDatagramSize = size
		b.pacer.setMaxDatagramSize(size)
		b.publishTelemetry()
	}
}
func (b *BrutalSender) OnCongestionEventEx(_ quiccongestion.ByteCount, eventTime monotime.Time, acked []quiccongestion.AckedPacketInfo, lost []quiccongestion.LostPacketInfo) {
	var lostBytes uint64
	for _, p := range lost {
		if p.BytesLost > 0 {
			lostBytes = satAddUint64(lostBytes, uint64(p.BytesLost))
		}
	}
	if lostBytes > 0 {
		b.telemetry.observeLoss(lostBytes, uint64(len(lost)))
	}
	for range acked {
		b.ackCount++
	}
	for range lost {
		b.lossCount++
	}
	if b.disableLossCompensation || b.lastSample.IsZero() {
		b.lastSample = eventTime
		return
	}
	if eventTime.Sub(b.lastSample) < 1*time.Second || b.ackCount+b.lossCount < brutalMinSamples {
		return
	}
	rate := float64(b.ackCount) / float64(b.ackCount+b.lossCount)
	if rate < 0.8 {
		rate = 0.8
	}
	b.ackRate = rate
	b.ackCount, b.lossCount = 0, 0
	b.lastSample = eventTime
	b.publishTelemetry()
}

func (b *BrutalSender) publishTelemetry() {
	b.telemetry.update(ControllerModeBrutal, uint64(b.bps), uint64(b.bandwidth()), int64(b.GetCongestionWindow()), 0, b.currentRTT(), false)
}

func (b *BrutalSender) currentRTT() time.Duration {
	if b.rttStats != nil {
		if rtt := b.rttStats.SmoothedRTT(); rtt > 0 {
			return rtt
		}
	}
	return 200 * time.Millisecond
}

func (b *BrutalSender) Telemetry() ControllerTelemetry { return b.telemetry.snapshot() }
