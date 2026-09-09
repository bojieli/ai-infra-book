package congestion

import (
	"math"
	"time"

	quiccongestion "github.com/apernet/quic-go/congestion"
	"github.com/apernet/quic-go/monotime"
)

// BBRSender is an independently implemented, BBRv1-shaped QUIC controller.
//
// It is intentionally kept separate from AdaptiveSender: Adaptive is a
// conservative rate estimator, while this controller maintains the BBR
// STARTUP/DRAIN/PROBE_BW/PROBE_RTT model, a max delivery-rate filter, and a
// recovery window.  The model only consumes QUIC's public congestion-control
// callbacks; no application plaintext or destination metadata is involved.
//
// The implementation is based on the public BBR model (draft-cardwell-iccrg)
// and is an original Go implementation.  It is experimental until the real
// path campaign demonstrates an acceptable latency/loss trade-off; Reno stays
// the default and Adaptive remains available as a conservative alternative.
type BBRSender struct {
	rttStats        quiccongestion.RTTStatsProvider
	maxDatagramSize quiccongestion.ByteCount
	pacer           *pacer

	mode       bbrMode
	pacingGain float64
	cwndGain   float64

	initialCwnd quiccongestion.ByteCount
	minCwnd     quiccongestion.ByteCount
	maxCwnd     quiccongestion.ByteCount
	cwnd        quiccongestion.ByteCount

	bytesInFlight quiccongestion.ByteCount
	lastSent      quiccongestion.PacketNumber
	lastAcked     quiccongestion.PacketNumber
	lastRoundEnd  quiccongestion.PacketNumber
	roundStarted  bool
	round         uint64

	minRTT       time.Duration
	minRTTAt     monotime.Time
	lastDelivery monotime.Time
	maxBandwidth uint64
	bwSamples    [10]bwSample

	// sendStates is the bounded packet history used for delivery-rate samples.
	// A sample must measure bytes delivered since the packet was sent, not the
	// size of one ACK callback divided by callback spacing; ACK coalescing on a
	// long-haul path makes the latter estimator wildly noisy.
	sendStates     map[quiccongestion.PacketNumber]bbrSendState
	deliveredBytes uint64
	totalSentBytes uint64

	// Cumulative ACK points used by the delivery-rate sampler. A sample is
	// bounded by both the ACK slope and the send slope, which avoids treating
	// one delayed ACK divided by a full RTT as the bottleneck rate.
	lastAckPointTime      monotime.Time
	lastAckPointDelivered uint64
	lastAckPointSentTime  monotime.Time
	lastAckPointSentBytes uint64

	bwAtLastRound uint64
	roundsNoGain  uint8
	fullBandwidth bool

	cycleStart  monotime.Time
	cycleOffset uint8

	inRecovery      bool
	recoveryWindow  quiccongestion.ByteCount
	endRecoveryPN   quiccongestion.PacketNumber
	recoveryLosses  quiccongestion.ByteCount
	probeRTTExit    monotime.Time
	probeRTTStarted bool
	telemetry       telemetryState
}

type bbrMode uint8

const (
	bbrStartup bbrMode = iota
	bbrDrain
	bbrProbeBW
	bbrProbeRTT
)

type bwSample struct {
	round uint64
	bps   uint64
}

type bbrSendState struct {
	sentTime          monotime.Time
	deliveredAtSend   uint64
	deliveredTimeSend monotime.Time
	sentBytesAtSend   uint64
}

const (
	bbrHighGain                   = 2.885
	bbrDrainGain                  = 1 / bbrHighGain
	bbrCwndGain                   = 2.0
	bbrProbeRTTInterval           = 10 * time.Second
	bbrProbeRTTDuration           = 200 * time.Millisecond
	bbrStartupGrowth              = 1.25
	bbrStartupNoGainRounds        = 3
	bbrStartupCwndGain            = 2.0
	bbrMinRate                    = 64 * 1024
	bbrMaxRate             uint64 = 2 * 1024 * 1024 * 1024
	// A loss or a peer that stops acknowledging must not turn the sampler's
	// per-packet state into an unbounded allocation. QUIC's own outstanding
	// packet limit is much lower during normal operation; this cap is a final
	// defense for long-lived or adversarial sessions.
	bbrMaxSendStates       = 8192
	maxCongestionByteCount = quiccongestion.ByteCount(1<<63 - 1)
)

var bbrPacingGains = [...]float64{1.25, 0.75, 1, 1, 1, 1, 1, 1}

var _ quiccongestion.CongestionControlEx = (*BBRSender)(nil)

// NewBBRSender creates a BBR-shaped sender with a conservative 10-packet
// initial window. The initial window is capped by quic-go's safety maximum.
func NewBBRSender(initialPacketSize quiccongestion.ByteCount) *BBRSender {
	if initialPacketSize < quiccongestion.MinInitialPacketSize {
		initialPacketSize = quiccongestion.InitialPacketSize
	}
	// TUIC's BBR uses the standard 32-packet initial window. The old queqiao
	// controller used ten packets, which unnecessarily serialized startup over
	// a 200-ms path and made a single flow look much worse than TUIC before its
	// estimator had any useful sample.
	initial := maxByteCount(32*initialPacketSize, 14720)
	maxCwnd := quiccongestion.MaxCongestionWindowPackets * initialPacketSize
	if initial > maxCwnd {
		initial = maxCwnd
	}
	b := &BBRSender{
		maxDatagramSize: initialPacketSize,
		initialCwnd:     initial,
		minCwnd:         4 * initialPacketSize,
		maxCwnd:         maxCwnd,
		cwnd:            initial,
		mode:            bbrStartup,
		pacingGain:      bbrHighGain,
		// BBR uses a high pacing gain in STARTUP, but its congestion-window
		// gain is 2.0. Applying the pacing gain to the initial rate as well
		// would apply the 2.885 factor twice before a delivery sample exists.
		cwndGain:   bbrStartupCwndGain,
		sendStates: make(map[quiccongestion.PacketNumber]bbrSendState),
		telemetry:  newTelemetryState("bbr"),
	}
	b.pacer = newPacer(b.bandwidth)
	b.publishTelemetry()
	return b
}

func (b *BBRSender) SetRTTStatsProvider(provider quiccongestion.RTTStatsProvider) {
	b.rttStats = provider
	b.refreshRTT(monotime.Now())
	b.updateWindow(0)
	b.publishTelemetry()
}

func (b *BBRSender) rtt() time.Duration {
	if b.minRTT > 0 {
		return b.minRTT
	}
	if b.rttStats != nil {
		if r := b.rttStats.SmoothedRTT(); r > 0 {
			return r
		}
		if r := b.rttStats.LatestRTT(); r > 0 {
			return r
		}
	}
	return 200 * time.Millisecond
}

func (b *BBRSender) refreshRTT(now monotime.Time) {
	measured := time.Duration(0)
	if b.rttStats != nil {
		measured = b.rttStats.MinRTT()
		if measured <= 0 {
			measured = b.rttStats.SmoothedRTT()
		}
		if measured <= 0 {
			measured = b.rttStats.LatestRTT()
		}
	}
	if measured > 0 && (b.minRTT <= 0 || measured < b.minRTT) {
		b.minRTT = measured
		b.minRTTAt = now
		b.updateWindow(0)
	}
}

func (b *BBRSender) bandwidth() quiccongestion.ByteCount {
	rate := b.maxBandwidth
	if rate == 0 {
		rtt := b.rtt()
		if rtt <= 0 {
			rtt = 200 * time.Millisecond
		}
		// The pacing gain is applied below. Keep the initial model at IW/RTT,
		// matching the standard BBR startup behavior and avoiding a squared
		// startup gain on high-RTT paths.
		rate = uint64(float64(b.initialCwnd) / rtt.Seconds())
	}
	if rate < bbrMinRate {
		rate = bbrMinRate
	}
	if rate > bbrMaxRate {
		rate = bbrMaxRate
	}
	paced := float64(rate) * b.pacingGain
	if math.IsNaN(paced) || math.IsInf(paced, 0) || paced < bbrMinRate {
		paced = bbrMinRate
	}
	if paced > float64(bbrMaxRate) {
		paced = float64(bbrMaxRate)
	}
	b.telemetry.pacingRate.Store(uint64(paced))
	return quiccongestion.ByteCount(paced)
}

func (b *BBRSender) TimeUntilSend(_ quiccongestion.ByteCount) monotime.Time {
	return b.pacer.timeUntilSend()
}

func (b *BBRSender) HasPacingBudget(now monotime.Time) bool {
	return b.pacer.budget(now) >= b.maxDatagramSize
}

func (b *BBRSender) OnPacketSent(sentTime monotime.Time, bytesInFlight quiccongestion.ByteCount, number quiccongestion.PacketNumber, bytes quiccongestion.ByteCount, _ bool) {
	b.lastSent = number
	// bytesInFlight is the value before this packet is accounted for.
	if bytes < 0 || bytesInFlight < 0 || bytes > maxCongestionByteCount-bytesInFlight {
		b.bytesInFlight = maxCongestionByteCount
	} else {
		b.bytesInFlight = bytesInFlight + bytes
	}
	if b.sendStates == nil {
		b.sendStates = make(map[quiccongestion.PacketNumber]bbrSendState)
	}
	if len(b.sendStates) >= bbrMaxSendStates {
		b.pruneSendStates()
	}
	deliveredTime := b.lastDelivery
	if deliveredTime.IsZero() {
		deliveredTime = sentTime
	}
	b.sendStates[number] = bbrSendState{
		sentTime: sentTime, deliveredAtSend: b.deliveredBytes,
		deliveredTimeSend: deliveredTime, sentBytesAtSend: b.addSentBytes(bytes),
	}
	b.pacer.sentPacket(sentTime, bytes)
	b.publishTelemetry()
}

func (b *BBRSender) addSentBytes(bytes quiccongestion.ByteCount) uint64 {
	if bytes <= 0 {
		return b.totalSentBytes
	}
	value := uint64(bytes)
	if value > ^uint64(0)-b.totalSentBytes {
		b.totalSentBytes = ^uint64(0)
	} else {
		b.totalSentBytes += value
	}
	return b.totalSentBytes
}

// pruneSendStates removes the oldest quarter of samples when the hard cap is
// reached. QUIC normally removes states on every ACK/loss; this path is only
// exercised when acknowledgements stop arriving, so a bounded scan is safer
// than retaining unacknowledged history indefinitely.
func (b *BBRSender) pruneSendStates() {
	if len(b.sendStates) < bbrMaxSendStates {
		return
	}
	remove := bbrMaxSendStates / 4
	for i := 0; i < remove; i++ {
		var oldestPN quiccongestion.PacketNumber
		var oldest monotime.Time
		first := true
		for pn, state := range b.sendStates {
			if first || state.sentTime.Before(oldest) {
				oldestPN, oldest, first = pn, state.sentTime, false
			}
		}
		if first {
			return
		}
		delete(b.sendStates, oldestPN)
	}
}

func (b *BBRSender) CanSend(bytesInFlight quiccongestion.ByteCount) bool {
	return bytesInFlight < b.GetCongestionWindow()
}

func (b *BBRSender) MaybeExitSlowStart() {}

func (b *BBRSender) OnPacketAcked(_ quiccongestion.PacketNumber, _ quiccongestion.ByteCount, priorInFlight quiccongestion.ByteCount, _ monotime.Time) {
	b.bytesInFlight = priorInFlight
	b.publishTelemetry()
}

func (b *BBRSender) OnCongestionEvent(number quiccongestion.PacketNumber, lostBytes quiccongestion.ByteCount, priorInFlight quiccongestion.ByteCount) {
	// The extended callback receives the complete loss batch and is the single
	// source of truth. Applying noteLoss here as well would halve the recovery
	// window twice when quic-go invokes both callbacks.
	b.bytesInFlight = priorInFlight
	b.publishTelemetry()
}

func (b *BBRSender) OnCongestionEventEx(priorInFlight quiccongestion.ByteCount, eventTime monotime.Time, acked []quiccongestion.AckedPacketInfo, lost []quiccongestion.LostPacketInfo) {
	if eventTime.IsZero() {
		eventTime = monotime.Now()
	}
	b.bytesInFlight = priorInFlight
	var ackedBytes quiccongestion.ByteCount
	var largestAck quiccongestion.PacketNumber
	for _, p := range acked {
		if p.BytesAcked < 0 || ackedBytes > maxCongestionByteCount-p.BytesAcked {
			ackedBytes = maxCongestionByteCount
		} else {
			ackedBytes += p.BytesAcked
		}
		if p.PacketNumber > largestAck {
			largestAck = p.PacketNumber
		}
	}
	if len(acked) > 0 {
		b.lastAcked = largestAck
		b.refreshRTT(eventTime)
		b.updateBandwidthFromPackets(eventTime, acked, uint64(ackedBytes))
		b.updateRound(largestAck)
	}
	var lostBytes uint64
	for _, p := range lost {
		if p.BytesLost > 0 {
			lostBytes = satAddUint64(lostBytes, uint64(p.BytesLost))
		}
		// BBR does not leave STARTUP on an isolated loss. Doing so was a major
		// source of the old controller's collapse on this path: one reordered
		// packet permanently converted a healthy startup into a tiny recovery
		// window. Recovery remains active once the controller has established a
		// bottleneck model, or after a timeout resets it explicitly.
		if b.fullBandwidth || b.mode != bbrStartup {
			b.noteLoss(p.PacketNumber, p.BytesLost, eventTime)
		}
	}
	if lostBytes > 0 {
		b.telemetry.observeLoss(lostBytes, uint64(len(lost)))
	}
	b.transition(eventTime, priorInFlight, len(lost) > 0)
	b.updateWindow(ackedBytes)
	b.bytesInFlight = priorInFlight
	b.deliveredBytes += uint64(ackedBytes)
	for _, p := range acked {
		delete(b.sendStates, p.PacketNumber)
	}
	for _, p := range lost {
		delete(b.sendStates, p.PacketNumber)
	}
	if ackedBytes >= b.recoveryLosses {
		b.recoveryLosses = 0
	} else {
		b.recoveryLosses -= ackedBytes
	}
	b.publishTelemetry()
}

func (b *BBRSender) noteLoss(number quiccongestion.PacketNumber, lostBytes quiccongestion.ByteCount, now monotime.Time) {
	if lostBytes == 0 {
		return
	}
	if !b.inRecovery {
		b.inRecovery = true
		b.recoveryWindow = maxByteCount(b.minCwnd, b.bytesInFlight)
	}
	if number > b.endRecoveryPN {
		b.endRecoveryPN = b.lastSent
	}
	if b.recoveryWindow > lostBytes {
		b.recoveryWindow -= lostBytes
	} else {
		b.recoveryWindow = b.minCwnd
	}
	if lostBytes < 0 || b.recoveryLosses > maxCongestionByteCount-lostBytes {
		b.recoveryLosses = maxCongestionByteCount
	} else {
		b.recoveryLosses += lostBytes
	}
	if b.mode == bbrStartup {
		b.fullBandwidth = true
	}
	if b.cycleStart.IsZero() {
		b.cycleStart = now
	}
}

func (b *BBRSender) updateBandwidthFromPackets(now monotime.Time, acked []quiccongestion.AckedPacketInfo, bytes uint64) {
	if bytes == 0 || len(acked) == 0 {
		return
	}
	var best uint64
	deliveredNow := b.deliveredBytes + bytes
	var ackRate uint64
	if !b.lastAckPointTime.IsZero() && deliveredNow > b.lastAckPointDelivered {
		ackElapsed := now.Sub(b.lastAckPointTime)
		if ackElapsed < time.Millisecond {
			ackElapsed = time.Millisecond
		}
		ackRate = uint64(float64(deliveredNow-b.lastAckPointDelivered) / ackElapsed.Seconds())
	}
	var largestState bbrSendState
	var largestPN quiccongestion.PacketNumber
	var haveLargest bool
	for _, packet := range acked {
		state, ok := b.sendStates[packet.PacketNumber]
		if !ok {
			continue
		}
		if !haveLargest || packet.PacketNumber > largestPN {
			largestPN, largestState, haveLargest = packet.PacketNumber, state, true
		}
		if deliveredNow <= state.deliveredAtSend {
			continue
		}
		// Bound the ACK arrival slope with the actual send slope. The old
		// state.deliveredAtSend/RTT estimate interpreted a stream of individual
		// delayed ACKs as one packet per RTT and forced BBR to its minimum rate.
		sample := ackRate
		if !b.lastAckPointSentTime.IsZero() && state.sentTime.After(b.lastAckPointSentTime) && state.sentBytesAtSend > b.lastAckPointSentBytes {
			sendElapsed := state.sentTime.Sub(b.lastAckPointSentTime)
			if sendElapsed < time.Millisecond {
				sendElapsed = time.Millisecond
			}
			sendRate := uint64(float64(state.sentBytesAtSend-b.lastAckPointSentBytes) / sendElapsed.Seconds())
			if sample == 0 || sendRate < sample {
				sample = sendRate
			}
		}
		if sample > best {
			best = sample
		}
	}
	if haveLargest {
		b.lastAckPointTime = now
		b.lastAckPointDelivered = deliveredNow
		b.lastAckPointSentTime = largestState.sentTime
		b.lastAckPointSentBytes = largestState.sentBytesAtSend
	}
	if best > 0 {
		b.recordBandwidthSample(best)
	}
	b.lastDelivery = now
}

func (b *BBRSender) recordBandwidthSample(sample uint64) {
	if sample == 0 {
		return
	}
	index := b.round % uint64(len(b.bwSamples))
	current := b.bwSamples[index]
	// Multiple ACK events belong to one packet-timed round. The BBR filter is
	// a max filter over rounds, not a last-sample filter: a delayed ACK or an
	// app-idle tail sample must not erase the useful delivery peak learned
	// earlier in the same round.
	if current.bps == 0 || current.round != b.round || sample > current.bps {
		b.bwSamples[index] = bwSample{round: b.round, bps: sample}
	}
	b.recomputeBandwidth()
}

// recomputeBandwidth gives the delivery estimator a finite memory. Keeping a
// peak forever is unsafe on a path that changes from a fast to a congested
// regime: the controller would continue pacing at a stale rate indefinitely.
func (b *BBRSender) recomputeBandwidth() {
	var best uint64
	for _, sample := range b.bwSamples {
		if sample.bps == 0 || sample.round+uint64(len(b.bwSamples)) < b.round {
			continue
		}
		if sample.bps > best {
			best = sample.bps
		}
	}
	b.maxBandwidth = best
}

func (b *BBRSender) updateRound(largestAck quiccongestion.PacketNumber) {
	if !b.roundStarted {
		b.roundStarted = true
		b.round++
		b.lastRoundEnd = b.lastSent
		return
	}
	if largestAck > b.lastRoundEnd {
		b.round++
		b.lastRoundEnd = b.lastSent
		if b.maxBandwidth >= uint64(float64(b.bwAtLastRound)*bbrStartupGrowth) {
			b.bwAtLastRound = b.maxBandwidth
			b.roundsNoGain = 0
		} else if b.mode == bbrStartup {
			b.roundsNoGain++
		}
	}
}

func (b *BBRSender) transition(now monotime.Time, inFlight quiccongestion.ByteCount, hadLoss bool) {
	if b.mode == bbrStartup && (b.fullBandwidth || b.roundsNoGain >= bbrStartupNoGainRounds) {
		b.mode = bbrDrain
		b.pacingGain = bbrDrainGain
		b.cwndGain = bbrStartupCwndGain
	}
	if b.mode == bbrDrain && inFlight <= b.targetWindow(1) {
		b.mode = bbrProbeBW
		b.pacingGain = 1
		b.cwndGain = bbrCwndGain
		b.cycleStart = now
	}
	if b.mode == bbrProbeBW {
		if b.cycleStart.IsZero() {
			b.cycleStart = now
		}
		advance := now.Sub(b.cycleStart) >= b.rtt()
		if b.pacingGain > 1 && !hadLoss && inFlight < b.targetWindow(b.pacingGain) {
			advance = false
		}
		if b.pacingGain < 1 && inFlight <= b.targetWindow(1) {
			advance = true
		}
		if advance {
			b.cycleOffset = (b.cycleOffset + 1) % uint8(len(bbrPacingGains))
			b.cycleStart = now
			b.pacingGain = bbrPacingGains[b.cycleOffset]
		}
	}
	if !b.minRTTAt.IsZero() && now.Sub(b.minRTTAt) >= bbrProbeRTTInterval && b.mode != bbrProbeRTT {
		b.mode = bbrProbeRTT
		b.pacingGain = 1
		b.probeRTTExit = 0
		b.probeRTTStarted = true
	}
	if b.mode == bbrProbeRTT {
		if b.probeRTTExit.IsZero() && inFlight <= b.minCwnd+b.maxDatagramSize {
			b.probeRTTExit = now.Add(bbrProbeRTTDuration)
		}
		if !b.probeRTTExit.IsZero() && !now.Before(b.probeRTTExit) {
			if b.fullBandwidth {
				b.mode = bbrProbeBW
				b.pacingGain = 1
				b.cwndGain = bbrCwndGain
				b.cycleStart = now
			} else {
				b.mode = bbrStartup
				b.pacingGain = bbrHighGain
				b.cwndGain = bbrStartupCwndGain
			}
			b.minRTTAt = now
			b.probeRTTStarted = false
		}
	}
	if b.inRecovery && !hadLoss && b.lastAcked > b.endRecoveryPN {
		b.inRecovery = false
		b.recoveryWindow = 0
	}
}

func (b *BBRSender) targetWindow(gain float64) quiccongestion.ByteCount {
	rtt := b.rtt()
	if b.maxBandwidth == 0 || rtt <= 0 {
		return b.initialCwnd
	}
	target := float64(b.maxBandwidth) * rtt.Seconds() * gain
	if math.IsNaN(target) || math.IsInf(target, 0) || target < float64(b.minCwnd) {
		target = float64(b.minCwnd)
	}
	if target > float64(b.maxCwnd) {
		target = float64(b.maxCwnd)
	}
	return quiccongestion.ByteCount(target)
}

func (b *BBRSender) updateWindow(acked quiccongestion.ByteCount) {
	if b.mode == bbrProbeRTT {
		b.cwnd = b.minCwnd
	} else if b.fullBandwidth {
		target := b.targetWindow(b.cwndGain)
		if b.cwnd < target {
			b.cwnd = minByteCount(target, b.cwnd+acked)
		} else if b.cwnd > target && b.mode != bbrStartup {
			b.cwnd = target
		}
	} else {
		// Startup is ACK-clocked: grow by newly acknowledged bytes while the
		// delivery-rate filter is still finding the path capacity.
		b.cwnd = minByteCount(b.maxCwnd, maxByteCount(b.minCwnd, b.cwnd+acked))
	}
	if b.inRecovery && acked > 0 {
		if acked < 0 || b.recoveryWindow > maxCongestionByteCount-acked {
			b.recoveryWindow = maxCongestionByteCount
		} else {
			b.recoveryWindow += acked
		}
		if b.recoveryWindow < b.minCwnd {
			b.recoveryWindow = b.minCwnd
		}
	}
	if b.cwnd < b.minCwnd {
		b.cwnd = b.minCwnd
	}
	if b.cwnd > b.maxCwnd {
		b.cwnd = b.maxCwnd
	}
}

func (b *BBRSender) OnRetransmissionTimeout(retransmitted bool) {
	if !retransmitted {
		return
	}
	b.inRecovery = true
	b.recoveryWindow = b.minCwnd
	b.cwnd = b.minCwnd
	b.maxBandwidth = 0
	b.roundsNoGain = 0
	b.fullBandwidth = false
	b.mode = bbrStartup
	b.pacingGain = bbrHighGain
	b.cwndGain = bbrStartupCwndGain
	b.lastDelivery = 0
	b.deliveredBytes = 0
	b.totalSentBytes = 0
	b.lastAckPointTime = 0
	b.lastAckPointDelivered = 0
	b.lastAckPointSentTime = 0
	b.lastAckPointSentBytes = 0
	b.sendStates = make(map[quiccongestion.PacketNumber]bbrSendState)
	b.pacer = newPacer(b.bandwidth)
	b.pacer.setMaxDatagramSize(b.maxDatagramSize)
	b.publishTelemetry()
}

func (b *BBRSender) SetMaxDatagramSize(size quiccongestion.ByteCount) {
	if size <= 0 {
		return
	}
	b.maxDatagramSize = size
	b.minCwnd = 4 * size
	b.maxCwnd = quiccongestion.MaxCongestionWindowPackets * size
	if b.initialCwnd < b.minCwnd {
		b.initialCwnd = b.minCwnd
	}
	b.pacer.setMaxDatagramSize(size)
	b.updateWindow(0)
	b.publishTelemetry()
}

func (b *BBRSender) InSlowStart() bool { return b.mode == bbrStartup }
func (b *BBRSender) InRecovery() bool  { return b.inRecovery }
func (b *BBRSender) GetCongestionWindow() quiccongestion.ByteCount {
	window := b.cwnd
	if window < b.minCwnd {
		window = b.minCwnd
	}
	if b.inRecovery && b.recoveryWindow > 0 && window > b.recoveryWindow {
		window = b.recoveryWindow
	}
	return window
}

func (b *BBRSender) publishTelemetry() {
	b.telemetry.update(uint32(b.mode)+ControllerModeStartup, b.maxBandwidth, uint64(b.bandwidth()), int64(b.GetCongestionWindow()), int64(b.bytesInFlight), b.minRTT, b.inRecovery)
}

func (b *BBRSender) Telemetry() ControllerTelemetry { return b.telemetry.snapshot() }
