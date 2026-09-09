// Package congestion contains the optional QUIC send controllers used by
// queqiao. The default remains the controller shipped by apNet quic-go.
//
// The pacer below is adapted from the MIT-licensed Hysteria 2 congestion
// implementation (github.com/apernet/hysteria, core/internal/congestion).
// See NOTICE for attribution.
package congestion

import (
	"time"

	quiccongestion "github.com/apernet/quic-go/congestion"
	"github.com/apernet/quic-go/monotime"
)

const (
	maxBurstPackets         = 10
	defaultBurstPacingDelay = 4 * quiccongestion.MinPacingDelay
	tuicBurstPacingDelay    = quiccongestion.MinPacingDelay + time.Millisecond
)

// pacer is a bounded token bucket. QUIC asks the controller both whether a
// packet may be sent now and when the next packet should be sent. Keeping the
// bucket in the controller makes rate-based controllers work with QUIC's
// packet scheduler without a second application-level ticker.
type pacer struct {
	budgetAtLastSent quiccongestion.ByteCount
	maxDatagramSize  quiccongestion.ByteCount
	lastSentTime     monotime.Time
	getBandwidth     func() quiccongestion.ByteCount // bytes per second
	burstPacingDelay time.Duration
	// burstFloor raises the burst budget above what the constant window
	// allows, so that the amount a sender may release at once can follow the
	// congestion evidence instead of a constant.
	//
	// The constant is a few milliseconds, which on a long path is the wrong
	// question. Pacing exists to stop a sender building a standing queue at a
	// bottleneck, and a burst smaller than the bandwidth-delay product cannot
	// build one: it is by definition less than what the path already holds in
	// flight. Metering it anyway spends latency to protect a queue that cannot
	// form. Measured on a 199ms path, a 355KB request paced at a 42 Mbit/s
	// estimate took 67ms to put on the wire, against about 9ms of actual wire
	// time, and that 67ms was the whole of this transport's deficit against a
	// tuned TCP client on the same path.
	burstFloor func() quiccongestion.ByteCount
}

func newPacer(getBandwidth func() quiccongestion.ByteCount) *pacer {
	return newPacerWithBurstDelay(getBandwidth, defaultBurstPacingDelay)
}

func newTUICPacer(getBandwidth func() quiccongestion.ByteCount) *pacer {
	return newPacerWithBurstDelay(getBandwidth, tuicBurstPacingDelay)
}

func newPacerWithBurstDelay(getBandwidth func() quiccongestion.ByteCount, burstPacingDelay time.Duration) *pacer {
	if burstPacingDelay <= 0 {
		burstPacingDelay = defaultBurstPacingDelay
	}
	return &pacer{
		budgetAtLastSent: maxBurstPackets * quiccongestion.InitialPacketSize,
		maxDatagramSize:  quiccongestion.InitialPacketSize,
		getBandwidth:     getBandwidth,
		burstPacingDelay: burstPacingDelay,
	}
}

func (p *pacer) sentPacket(sendTime monotime.Time, size quiccongestion.ByteCount) {
	budget := p.budget(sendTime)
	if size > budget {
		p.budgetAtLastSent = 0
	} else {
		p.budgetAtLastSent = budget - size
	}
	p.lastSentTime = sendTime
}

func (p *pacer) budget(now monotime.Time) quiccongestion.ByteCount {
	bps := p.getBandwidth()
	if bps <= 0 {
		return 0
	}
	if p.lastSentTime.IsZero() {
		return p.maxBurstSize()
	}
	budget := p.budgetAtLastSent + (bps*quiccongestion.ByteCount(now.Sub(p.lastSentTime).Nanoseconds()))/1e9
	if budget < 0 { // protect against integer overflow
		budget = quiccongestion.ByteCount(1<<62 - 1)
	}
	return minByteCount(p.maxBurstSize(), budget)
}

func (p *pacer) maxBurstSize() quiccongestion.ByteCount {
	size := maxByteCount(
		quiccongestion.ByteCount(p.burstPacingDelay.Nanoseconds())*p.getBandwidth()/1e9,
		maxBurstPackets*p.maxDatagramSize,
	)
	if p.burstFloor != nil {
		if floor := p.burstFloor(); floor > size {
			return floor
		}
	}
	return size
}

// setBurstFloor installs the override. A nil function, or one returning less
// than the constant allows, leaves the default behaviour exactly as it was.
func (p *pacer) setBurstFloor(f func() quiccongestion.ByteCount) { p.burstFloor = f }

func (p *pacer) timeUntilSend() monotime.Time {
	if p.budgetAtLastSent >= p.maxDatagramSize {
		return 0
	}
	bps := uint64(p.getBandwidth())
	if bps == 0 {
		return p.lastSentTime.Add(time.Second)
	}
	diff := 1e9 * uint64(p.maxDatagramSize-p.budgetAtLastSent)
	d := diff / bps
	if diff%bps != 0 {
		d++
	}
	return p.lastSentTime.Add(maxDuration(quiccongestion.MinPacingDelay, time.Duration(d)*time.Nanosecond))
}

func (p *pacer) setMaxDatagramSize(size quiccongestion.ByteCount) {
	if size > 0 {
		p.maxDatagramSize = size
	}
}

func minByteCount(a, b quiccongestion.ByteCount) quiccongestion.ByteCount {
	if a < b {
		return a
	}
	return b
}

func maxByteCount(a, b quiccongestion.ByteCount) quiccongestion.ByteCount {
	if a > b {
		return a
	}
	return b
}

func maxDuration(a, b time.Duration) time.Duration {
	if a > b {
		return a
	}
	return b
}
