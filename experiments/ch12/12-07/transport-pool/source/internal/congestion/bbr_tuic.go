package congestion

import (
	"math"
	"math/bits"
	"time"

	quiccongestion "github.com/apernet/quic-go/congestion"
	"github.com/apernet/quic-go/monotime"
)

// TUICBBRSender is a Go port of the BBR controller used by TUIC's
// quinn-congestions fork. It is intentionally opt-in while it is being
// validated against the stock controller and the existing BBRSender.
//
// quic-go's public CongestionControlEx callback does not expose an explicit
// application-limited notification, so the controller derives the same
// congestion-window-headroom condition at each event and records that marker
// per packet. ACK receive timestamps are used when the QUIC fork supplies them
// and the congestion-event time otherwise.
type TUICBBRSender struct {
	rttStats quiccongestion.RTTStatsProvider
	// lossIsCongestion decides whether a loss may put this sender into
	// recovery. It is true for a sender used on its own, which is TUIC's
	// behaviour and what the benchmark reference must keep. ErasureSender
	// clears it: on a path that erases packets for reasons unrelated to the
	// sending rate, a controller that reads every loss as congestion gives the
	// path away, and the brake is the delay bound instead.
	//
	// Losses still reach this method either way. They have to: bytesInFlight
	// below is priorInFlight less what was acknowledged and what was lost, so
	// a sender that is not told about a loss believes the pipe is fuller than
	// it is and throttles itself for a packet that is already gone.
	lossIsCongestion bool
	maxDatagramSize  quiccongestion.ByteCount
	pacer            *pacer

	mode                 tuicBbrMode
	pacingGain           float64
	highGain             float64
	drainGain            float64
	cwndGain             float64
	highCwndGain         float64
	lastCycle            monotime.Time
	cycleOffset          uint8
	randomState          uint64
	initialCwnd          quiccongestion.ByteCount
	minCwnd              quiccongestion.ByteCount
	maxCwnd              quiccongestion.ByteCount
	exitProbeRTT         monotime.Time
	probeRTTRoundPassed  bool
	minRTT               time.Duration
	minRTTAt             monotime.Time
	exitingQuiescence    bool
	maxAckedPN           quiccongestion.PacketNumber
	maxSentPN            quiccongestion.PacketNumber
	endRecoveryPN        quiccongestion.PacketNumber
	cwnd                 quiccongestion.ByteCount
	roundEndPN           quiccongestion.PacketNumber
	round                uint64
	bwAtLastRound        uint64
	roundsNoGain         uint8
	fullBandwidth        bool
	lastSampleAppLimited bool
	// peakBandwidth is the most this connection has ever been measured to
	// deliver, which outlives the filter's ten-round memory of it.
	peakBandwidth uint64
	// peakBandwidthAt is when peakBandwidth was observed. Without it the peak
	// is an all-time maximum, and restartFromIdle puts an all-time maximum
	// back into a filter whose whole purpose is to forget.
	peakBandwidthAt   monotime.Time
	lossEventsInRound uint64
	bytesLostInRound  uint64

	estimator      tuicBandwidthEstimator
	ackedBytes     uint64
	ackAgg         tuicAckAggregation
	recovery       tuicRecoveryState
	recoveryWindow quiccongestion.ByteCount

	pacingRate    uint64
	bytesInFlight quiccongestion.ByteCount
	telemetry     telemetryState
}

type tuicBbrMode uint8

const (
	tuicBbrStartup tuicBbrMode = iota
	tuicBbrDrain
	tuicBbrProbeBW
	tuicBbrProbeRTT
)

type tuicRecoveryState uint8

const (
	tuicNotInRecovery tuicRecoveryState = iota
	tuicConservation
	tuicGrowth
)

func (r tuicRecoveryState) inRecovery() bool { return r != tuicNotInRecovery }

type tuicAckAggregation struct {
	maxAckHeight tuicMinMax
	epochStart   monotime.Time
	epochBytes   uint64
}

const (
	tuicHighGain            = 2.885
	tuicDrainGain           = 1 / tuicHighGain
	tuicCwndGain            = 2.0
	tuicProbeRTTInterval    = 10 * time.Second
	tuicProbeRTTDuration    = 200 * time.Millisecond
	tuicStartupGrowth       = 1.25
	tuicStartupNoGainRounds = 3
	tuicStartupLossEvents   = 8
	tuicStartupLossFraction = 0.02
	tuicMaxBurstPackets     = 10
	// sing-quic's TUIC BBR uses the standard 32-packet initial window.
	// A previous port accidentally used 200 packets, creating a burst roughly
	// six times larger than TUIC's IW on a 200-ms path.  That burst is
	// especially damaging on the measured lossy China-US path: the first loss
	// event then dominates the delivery estimator and recovery window.
	tuicInitialPackets        = 32
	tuicDefaultMinRate uint64 = 64 * 1024
	tuicMaxRate        uint64 = 2 * 1024 * 1024 * 1024
)

var tuicPacingGains = [...]float64{1.25, 0.75, 1, 1, 1, 1, 1, 1}

var _ quiccongestion.CongestionControlEx = (*TUICBBRSender)(nil)

func NewTUICBBRSender(initialPacketSize quiccongestion.ByteCount) *TUICBBRSender {
	if initialPacketSize < quiccongestion.MinInitialPacketSize {
		initialPacketSize = quiccongestion.InitialPacketSize
	}
	initial := quiccongestion.ByteCount(tuicInitialPackets) * initialPacketSize
	minCwnd := 4 * initialPacketSize
	if initial < minCwnd {
		initial = minCwnd
	}
	maxCwnd := quiccongestion.MaxCongestionWindowPackets * initialPacketSize
	if initial > maxCwnd {
		initial = maxCwnd
	}
	b := &TUICBBRSender{
		maxDatagramSize: initialPacketSize,
		initialCwnd:     initial,
		minCwnd:         minCwnd,
		maxCwnd:         maxCwnd,
		cwnd:            initial,
		mode:            tuicBbrStartup,
		pacingGain:      tuicHighGain,
		highGain:        tuicHighGain,
		drainGain:       tuicDrainGain,
		// TUIC uses a 2.0 congestion-window gain in STARTUP.  The pacing gain
		// remains highGain; applying that factor to cwnd as well overfills the
		// initial flight before a delivery model exists.
		cwndGain:     tuicCwndGain,
		highCwndGain: tuicCwndGain,
		// A sender used on its own keeps TUIC's behaviour, which is what the
		// benchmark reference and every non-erasure path expect.
		lossIsCongestion: true,
		maxAckedPN:       quiccongestion.PacketNumber(-1),
		maxSentPN:        quiccongestion.PacketNumber(-1),
		endRecoveryPN:    quiccongestion.PacketNumber(-1),
		roundEndPN:       quiccongestion.PacketNumber(-1),
		estimator:        newTUICBandwidthEstimator(),
		ackAgg:           tuicAckAggregation{maxAckHeight: newTUICMinMax()},
		randomState:      uint64(monotime.Now()) ^ uint64(initialPacketSize)<<17,
		telemetry:        newTelemetryState("bbr-tuic"),
	}
	b.pacer = newTUICPacer(b.bandwidth)
	b.publishTelemetry()
	return b
}

func (b *TUICBBRSender) SetRTTStatsProvider(provider quiccongestion.RTTStatsProvider) {
	b.rttStats = provider
	b.publishTelemetry()
}

func (b *TUICBBRSender) rtt() time.Duration {
	if b.minRTT > 0 {
		return b.minRTT
	}
	if b.rttStats != nil {
		if r := b.rttStats.MinRTT(); r > 0 {
			return r
		}
	}
	return 100 * time.Millisecond
}

// refreshRTTSample mirrors TUIC's sampler-owned minimum RTT model. The
// provider's smoothed RTT is a safe pacing fallback, but it must not become a
// permanent min_rtt: doing so prevents ProbeRTT from correcting queueing bias.
// Returns true when an existing min_rtt expired at this event.
func (b *TUICBBRSender) refreshRTTSample(now monotime.Time, sample time.Duration) bool {
	if sample <= 0 {
		return false
	}
	expired := !b.minRTTAt.IsZero() && now.Sub(b.minRTTAt) >= tuicProbeRTTInterval
	if b.minRTT <= 0 || sample < b.minRTT || expired {
		b.minRTT = sample
		b.minRTTAt = now
	}
	return expired
}

func (b *TUICBBRSender) bandwidth() quiccongestion.ByteCount {
	rate := b.pacingRate
	if rate == 0 {
		// TUIC initializes pacing to IW/RTT once an RTT is available. A Go
		// controller must provide the same finite schedule to quic-go or the
		// first application packet could be delayed forever.
		rate = b.initialPacingRate()
	}
	if rate < tuicDefaultMinRate {
		rate = tuicDefaultMinRate
	}
	if rate > tuicMaxRate {
		rate = tuicMaxRate
	}
	b.telemetry.pacingRate.Store(rate)
	return quiccongestion.ByteCount(rate)
}

// seedBandwidth starts this sender from a delivered rate something else has
// already measured, instead of from the initial window over the round trip.
//
// A lane joining a path its siblings have already mapped should not repeat
// their discovery. On a channel that erases 40% of packets that discovery is
// the expensive part -- it is the same ramp a loss-based controller never
// finishes -- and a lane opened to replace one that died would pay it again on
// a path nothing has forgotten.
//
// It seeds the estimate rather than the pacing rate, and that distinction is
// the whole of it. BBR derives two things from one bandwidth estimate: the
// rate it paces at, and the window it is willing to fill. Seeding only the
// rate leaves the window at the initial one, and the window is what binds --
// traced live on a path already measured at 15 Mbit/s, a flow began with a
// 37 KB window and a 60 Mbit/s pacing rate, and spent eight round trips
// doubling the window while the pacer waited on it. Seeding the estimate moves
// both, because both were always the same number.
//
// The round trip is needed because a window is a rate times one. Without a
// measured round trip the estimate still seeds the pacing rate, and the window
// follows one round trip later when the first acknowledgement supplies it.
//
// What it must not do is adopt that round trip as this sender's own minimum.
// A minimum is a floor that only ever moves down, and `minRTTAt` is what lets
// ProbeRTT expire one and measure again -- a seed that writes `minRTT` without
// stamping `minRTTAt` is therefore permanent, which is exactly what the note
// on refreshRTTSample says must never happen.
//
// It is also wrong on the merits. The seed arrives from a shared model, so it
// is some other lane's minimum, and one bad sample anywhere poisons every
// connection made afterwards: BBR's target window is bandwidth times min_rtt,
// so a lane seeded with 4 ms on a 200 ms path sizes its window fifty times too
// small and holds around 1 Mbit/s forever. Measured on the emulator, that was
// one trial at 37 Mbit/s followed by every later trial in the same process at
// 0.7 to 1.5, and it is the shape of the live stall in
// docs/archive/2026-08-development/MEASUREMENTS-20260816.md. This sender measures its own round trip
// within one round; the seeded window carries it until then.
//
// The rate is only ever raised, so a seed below what this sender has already
// found costs nothing.
func (b *TUICBBRSender) seedBandwidth(rate uint64, roundTrip time.Duration) {
	if rate == 0 {
		return
	}
	if rate > tuicMaxRate {
		rate = tuicMaxRate
	}
	// The seed is stamped with the current time like any other sample, so a
	// lane that inherits a rate and then goes quiet lets it expire rather than
	// pacing from another lane's peak indefinitely.
	if roundTrip > 0 {
		b.estimator.maxFilter.setRoundTrip(roundTrip)
	}
	b.estimator.maxFilter.updateMax(b.round, monotime.Now(), rate)
	if pacing := uint64(float64(rate) * b.highGain); pacing > b.pacingRate {
		b.pacingRate = minUint64(pacing, tuicMaxRate)
	}
	if roundTrip <= 0 {
		return
	}
	window := quiccongestion.ByteCount(float64(rate) * roundTrip.Seconds())
	if window > b.maxCwnd {
		window = b.maxCwnd
	}
	if window > b.cwnd {
		b.cwnd = window
	}
}

// minRoundTrip is the smallest round trip this sender has seen, which is the
// path's rather than any one queue's.
func (b *TUICBBRSender) minRoundTrip() time.Duration { return b.minRTT }

// restartFromIdle restores what this sender had measured before the pipe
// emptied.
//
// An estimate is forgotten by idling, not disproved by it. The filter holds ten
// rounds, and a connection that spends a minute carrying small exchanges keeps
// only what those exchanges delivered -- so when a download arrives on it, it
// starts from the trickle. Probing bandwidth climbs a quarter per cycle, and
// measured live on a pooled connection that had been carrying small exchanges,
// an estimate that had fallen to 0.4 Mbit/s took nineteen seconds to find the
// 12 Mbit/s the path had had all along. The same download on a fresh
// connection ran at nine.
//
// So the peak this connection has actually seen is put back, and probing
// continues from there. This is a bet that a path which delivered 12 Mbit/s a
// minute ago still does, and it is the same bet the shared path model already
// makes for a lane that joins. If it is wrong the filter's own window
// disproves it within ten rounds, which is what the filter is for -- where
// being wrong the other way costs nineteen seconds every time a connection is
// reused, which is exactly what pooling connections is meant to make cheap.
func (b *TUICBBRSender) restartFromIdle(now monotime.Time) {
	if b.peakBandwidth <= b.estimator.estimate() {
		return
	}
	// A peak the filter would already have dropped must not be put back.
	//
	// The bet above -- that a path which delivered 12 Mbit/s a minute ago still
	// does -- is only safe because "the filter's own window disproves it within
	// ten rounds". It cannot. This fires whenever the pipe empties, which on a
	// connection that is application limited essentially always is constantly,
	// so the peak is re-armed faster than any window can retire it. Measured on
	// a live gateway, the estimate stood at four times the widest delivery
	// sample the connection had ever taken -- arithmetically impossible for a
	// maximum over samples, and the proof that this path was supplying it.
	//
	// Bounding it by the filter's own window is what makes the sentence above
	// true rather than aspirational: a seed is a hypothesis about the path
	// standing in for a measurement, so it expires when a measurement of that
	// age would have.
	//
	// The alternative, the filter's ten-second ceiling, was measured and is
	// worse: it costs the same on an erasure channel and leaves the policed
	// path at 9.5 times its capacity where this leaves it at 2.4.
	if b.estimator.maxFilter.expired(tuicMinMaxSample{at: b.peakBandwidthAt, value: b.peakBandwidth}, now) {
		return
	}
	b.seedBandwidth(b.peakBandwidth, b.minRTT)
}

func (b *TUICBBRSender) initialPacingRate() uint64 {
	rtt := b.rtt()
	if rtt <= 0 {
		return tuicDefaultMinRate
	}
	// TUIC's BBR starts at high_gain * IW / RTT.  The prior port omitted
	// high_gain, so after correcting IW from 200 packets to 32 it would seed
	// the delivery model at only one-third of TUIC's startup rate.  STARTUP
	// never decreases this value; the normal full-bandwidth and loss tests
	// still bound the transition to DRAIN/ProbeBW.
	rate := uint64(float64(b.initialCwnd) * b.highGain / rtt.Seconds())
	if rate < tuicDefaultMinRate {
		return tuicDefaultMinRate
	}
	if rate > tuicMaxRate {
		return tuicMaxRate
	}
	return rate
}

func (b *TUICBBRSender) TimeUntilSend(quiccongestion.ByteCount) monotime.Time {
	return b.pacer.timeUntilSend()
}

func (b *TUICBBRSender) HasPacingBudget(now monotime.Time) bool {
	return b.pacer.budget(now) >= b.maxDatagramSize
}

func (b *TUICBBRSender) OnPacketSent(sentTime monotime.Time, bytesInFlight quiccongestion.ByteCount, number quiccongestion.PacketNumber, bytes quiccongestion.ByteCount, retransmittable bool) {
	b.maxSentPN = number
	// apNet/quic-go calls this hook after adding an ack-eliciting packet to its
	// connection flight. TUIC's sampler, however, takes the pre-send flight and
	// adds the packet itself when it snapshots send state. Convert at this
	// adapter boundary; otherwise every packet's sampler flight is one packet
	// too large and a first packet can never be recognized as opening a flight.
	preSendFlight := preSendBytesInFlight(bytesInFlight, bytes, retransmittable)
	if preSendFlight == 0 {
		b.exitingQuiescence = true
		b.restartFromIdle(sentTime)
	}
	// Keep the controller telemetry in the same post-send units as quic-go.
	b.bytesInFlight = maxByteCount(0, bytesInFlight)
	b.estimator.onSentPacket(sentTime, number, uint64(maxByteCount(0, bytes)), uint64(preSendFlight), retransmittable)
	b.pacer.sentPacket(sentTime, bytes)
	b.publishTelemetry()
}

func preSendBytesInFlight(postSend, bytes quiccongestion.ByteCount, retransmittable bool) quiccongestion.ByteCount {
	if postSend <= 0 || !retransmittable || bytes <= 0 {
		return maxByteCount(0, postSend)
	}
	if postSend <= bytes {
		return 0
	}
	return postSend - bytes
}

func (b *TUICBBRSender) CanSend(bytesInFlight quiccongestion.ByteCount) bool {
	return bytesInFlight < b.GetCongestionWindow()
}

func (b *TUICBBRSender) MaybeExitSlowStart() {}

func (b *TUICBBRSender) OnPacketAcked(_ quiccongestion.PacketNumber, _ quiccongestion.ByteCount, _ quiccongestion.ByteCount, _ monotime.Time) {
}

// OnCongestionEvent is the legacy loss callback. quic-go calls it once for
// every newly detected lost packet and then calls OnCongestionEventEx with the
// complete loss batch. The extended callback is the single source of truth, so
// this callback deliberately does nothing.
func (b *TUICBBRSender) OnCongestionEvent(_ quiccongestion.PacketNumber, _ quiccongestion.ByteCount, _ quiccongestion.ByteCount) {
}

func (b *TUICBBRSender) OnCongestionEventEx(priorInFlight quiccongestion.ByteCount, eventTime monotime.Time, acked []quiccongestion.AckedPacketInfo, lost []quiccongestion.LostPacketInfo) {
	if eventTime.IsZero() {
		eventTime = monotime.Now()
	}
	hasLosses := len(lost) != 0
	ackedBytes := uint64(0)
	lostBytes := uint64(0)
	largestAck := quiccongestion.PacketNumber(-1)
	largestLoss := quiccongestion.PacketNumber(-1)
	lastLostState := tuicSendState{}
	for _, p := range acked {
		if p.BytesAcked > 0 {
			ackedBytes = satAddUint64(ackedBytes, uint64(p.BytesAcked))
		}
		if p.PacketNumber > largestAck {
			largestAck = p.PacketNumber
		}
	}
	for _, p := range lost {
		if p.BytesLost > 0 {
			lostBytes = satAddUint64(lostBytes, uint64(p.BytesLost))
		}
		state := b.estimator.onLost(p.PacketNumber)
		if state.valid && p.PacketNumber > largestLoss {
			largestLoss = p.PacketNumber
			lastLostState = state
		}
	}
	if hasLosses {
		b.telemetry.observeLoss(lostBytes, uint64(len(lost)))
	}
	b.bytesInFlight = saturatingRemaining(priorInFlight, ackedBytes, lostBytes)

	// Match TUIC's connection-level app-limited notification: if the sender
	// was not filling its current window, packets sent after this event belong
	// to an app-limited phase. The sampler records the marker per packet and
	// ends it only after an ACK for a later packet, rather than suppressing an
	// entire event based on an idle-gap guess.
	appLimited := b.appLimited(priorInFlight)
	if appLimited {
		b.estimator.markAppLimited()
	}

	// QUIC's round counter advances before the delivery sampler is evaluated.
	// Using the previous round here delayed the ten-round max filter by one
	// round and made sparse/loss-delayed ACKs expire valid peaks too early.
	isRoundStart := false
	if ackedBytes > 0 && largestAck > b.roundEndPN {
		isRoundStart = true
		b.roundEndPN = b.maxSentPN
		b.round++
	}
	// TUIC changes recovery only on events with an ACK. A loss-only callback
	// updates sampler/loss accounting, but waits for an ACK-clocked event before
	// entering or advancing packet conservation.
	if len(acked) != 0 {
		b.updateRecoveryState(largestAck, hasLosses && b.lossIsCongestion, isRoundStart)
	}
	// Process the complete ACK batch as one sample. quic-go gives every packet
	// in this callback the same receive/event time; updating the estimator once
	// per packet would make all but the first packet have a zero ACK interval.
	sample := tuicAckSample{}
	if ackedBytes > 0 {
		sample = b.estimator.onAckBatch(eventTime, acked, b.round)
	}
	minRTTExpired := false
	if ackedBytes > 0 {
		// The sampler owns BBR's expiring minimum-RTT model, but its packet
		// table cannot distinguish QUIC's overlapping packet-number spaces:
		// the public congestion callback carries a number, not its space. The
		// RTT provider has already resolved that ambiguity in the ACK handler,
		// so its latest sample is authoritative when it is available. Keeping
		// our own expiring minimum still lets ProbeRTT replace an old sample;
		// the provider supplies an event sample, not the permanent minimum.
		rttSample := sample.minRTT
		if b.rttStats != nil {
			if latest := b.rttStats.LatestRTT(); latest > 0 {
				rttSample = latest
			}
		}
		if rttSample > 0 {
			minRTTExpired = b.refreshRTTSample(eventTime, rttSample)
		}
		b.maxAckedPN = largestAck
	}

	bytesAckedWindow := b.estimator.bytesAckedThisWindow()
	b.ackedBytes = satAddUint64(b.ackedBytes, bytesAckedWindow)
	excessAcked := uint64(0)
	if bytesAckedWindow > 0 {
		excessAcked = b.ackAgg.update(bytesAckedWindow, eventTime, b.round, b.estimator.estimate())
	}
	b.estimator.endAcks()
	// What this connection has been measured to deliver outlives the filter's
	// memory of it, so that a pipe which empties can be refilled from what it
	// already knows rather than from what a trickle left behind.
	if bw := b.estimator.estimate(); bw > b.peakBandwidth {
		b.peakBandwidth, b.peakBandwidthAt = bw, eventTime
	}
	lastSendState := sample.lastSendState
	if lastLostState.valid && (!lastSendState.valid || lastLostState.packetNumber > lastSendState.packetNumber) {
		lastSendState = lastLostState
	}
	if lastSendState.valid {
		b.lastSampleAppLimited = lastSendState.appLimited
	}
	if hasLosses {
		b.lossEventsInRound = satAddUint64(b.lossEventsInRound, 1)
		b.bytesLostInRound = satAddUint64(b.bytesLostInRound, lostBytes)
	}
	if b.mode == tuicBbrProbeBW {
		b.updateGainCycle(eventTime, priorInFlight, b.bytesInFlight, hasLosses)
	}
	if isRoundStart && !b.fullBandwidth {
		b.checkFullBandwidth(lastSendState)
	}
	b.maybeExitStartupDrain(eventTime, b.bytesInFlight)
	b.maybeProbeRTT(eventTime, isRoundStart, b.bytesInFlight, minRTTExpired)
	b.calculatePacingRate()
	b.calculateCwnd(bytesAckedWindow, excessAcked)
	// Native TUIC calculates recovery from the post-event in-flight remainder.
	// Adding bytesAcked in calculateRecoveryWindow then permits the newly
	// acknowledged amount while accounting for losses in the same event.
	b.calculateRecoveryWindow(bytesAckedWindow, lostBytes, b.bytesInFlight)
	if leastUnacked, ok := obsoletePacketNumber(acked, lost); ok {
		b.estimator.removeObsolete(leastUnacked)
	}
	if isRoundStart {
		b.lossEventsInRound = 0
		b.bytesLostInRound = 0
	}
	b.publishTelemetry()
}

func saturatingRemaining(inFlight quiccongestion.ByteCount, acked, lost uint64) quiccongestion.ByteCount {
	if inFlight <= 0 {
		return 0
	}
	remaining := uint64(inFlight)
	if acked >= remaining {
		return 0
	}
	remaining -= acked
	if lost >= remaining {
		return 0
	}
	return quiccongestion.ByteCount(remaining - lost)
}

func saturatingByteAdd(a quiccongestion.ByteCount, b uint64) quiccongestion.ByteCount {
	if a < 0 {
		a = 0
	}
	max := uint64(maxCongestionByteCount)
	if uint64(a) >= max || b > max-uint64(a) {
		return maxCongestionByteCount
	}
	return a + quiccongestion.ByteCount(b)
}

// appLimited reports whether the sender had window it did not use, which marks
// the packets sent after this event as application-limited.
//
// Any unused window at all counts, outside DRAIN. That is deliberately liberal,
// and an attempt to tighten it -- requiring a full burst of unused window, on
// the reasoning that a paced sender is below its window at almost every
// acknowledgement -- was measured and reverted. On the emulator it looked
// right: the controller left startup promptly instead of holding 2.9 congestion
// windows in flight for a whole transfer.
//
// On the real China-US path it cost more than half the throughput: 4.3 Mbit/s
// against the reference's 8.8, restored to 9.7 against 9.9 by putting this rule
// back, measured in alternating paired rounds so the comparison sits inside one
// path window. The emulator has constant delay and independent loss; the live
// path varies between 226 and 440 ms and loses in bursts, which produces a
// stream of spuriously low delivery-rate samples. Marking them
// application-limited is what keeps them out of the bandwidth filter, and
// treating them as valid drags the estimate -- and with it the congestion
// window -- to half of what the path offers.
//
// The emulator finding was real and is not addressed by this: on a constant
// path the controller does stay in startup too long. Fixing that needs a
// mechanism that does not also discard the live path's noise.
// appLimited reports whether the application, rather than the path, is what
// is holding the sending rate down. quic-go's congestion interface has no
// OnApplicationLimited callback, so it has to be inferred, and the inference
// has to be conservative in one specific direction: BBR only updates its
// bandwidth filter from samples that are *not* app-limited, so marking too
// eagerly does not make the estimate cautious, it stops the estimate existing.
//
// Being under the congestion window is not the test. A paced sender is almost
// always under its window -- that is what pacing does -- so `priorInFlight <
// window` is true nearly every event on a busy connection. Measured on a
// healthy 100 Mbit/s transfer, that marked 347 of 347 samples app-limited and
// left the bandwidth estimate at 18 kB/s, about seven hundred times under the
// rate actually flowing. The controller was running with no working estimate
// of the path at all.
//
// Outside Drain the rule is deliberately liberal: any unused window counts.
// That looks wrong -- on a saturating transfer it marks nearly every sample,
// and the bandwidth filter then updates only from the rare event that fills
// the window exactly -- and it has been tightened twice and reverted twice.
// Requiring a burst of unused window, or half the window, measures better on
// the emulator and costs more than half the throughput on the real China-US
// path, where delivery-rate samples are noisy-low and this marking is what
// keeps them out of the filter. See TestTUICAppLimitedCountsAnyUnusedWindow-
// OutsideDrain and DESIGN-MULTIPATH.md 7.6 before touching it again.
//
// A near-100% app-limited count in the telemetry is therefore expected, not a
// symptom. Note also that the /metrics endpoint reports one lane: with
// --quic-pool that is usually the pooled control connection, which really is
// idle, so a low bandwidth estimate there says nothing about the lane carrying
// the data.
func (b *TUICBBRSender) appLimited(priorInFlight quiccongestion.ByteCount) bool {
	window := b.GetCongestionWindow()
	if priorInFlight >= window {
		return false
	}
	available := window - priorInFlight
	drainLimited := b.mode == tuicBbrDrain && priorInFlight > window/2
	return !drainLimited || available > tuicMaxBurstPackets*b.maxDatagramSize
}

func obsoletePacketNumber(acked []quiccongestion.AckedPacketInfo, lost []quiccongestion.LostPacketInfo) (quiccongestion.PacketNumber, bool) {
	var largest quiccongestion.PacketNumber = -1
	if len(acked) > 0 {
		for _, packet := range acked {
			if packet.PacketNumber > largest {
				largest = packet.PacketNumber
			}
		}
		if largest < 0 {
			return 0, false
		}
		if largest > 1 {
			return largest - 2, true
		}
		return 0, true
	}
	for _, packet := range lost {
		if packet.PacketNumber > largest {
			largest = packet.PacketNumber
		}
	}
	if largest < 0 {
		return 0, false
	}
	if largest == quiccongestion.PacketNumber(^uint64(0)>>1) {
		return largest, true
	}
	return largest + 1, true
}

func (b *TUICBBRSender) updateRecoveryState(lastAckedPacket quiccongestion.PacketNumber, hasLosses, roundStart bool) {
	// TUIC deliberately suppresses packet conservation until STARTUP has
	// established the bottleneck model. Mode alone is not sufficient: ProbeRTT
	// can occur before full bandwidth is known.
	if !b.fullBandwidth {
		return
	}
	if hasLosses {
		b.endRecoveryPN = b.maxSentPN
	}
	switch b.recovery {
	case tuicNotInRecovery:
		if hasLosses {
			b.recovery = tuicConservation
			b.recoveryWindow = 0
			b.roundEndPN = b.maxSentPN
		}
	case tuicConservation, tuicGrowth:
		if b.recovery == tuicConservation && roundStart {
			b.recovery = tuicGrowth
		}
		if !hasLosses && lastAckedPacket > b.endRecoveryPN {
			b.recovery = tuicNotInRecovery
		}
	}
}

func (b *TUICBBRSender) updateGainCycle(now monotime.Time, priorInFlight, inFlight quiccongestion.ByteCount, hasLosses bool) {
	advance := !b.lastCycle.IsZero() && now.Sub(b.lastCycle) > b.rtt()
	if b.pacingGain > 1 && !hasLosses && priorInFlight < b.targetCwnd(b.pacingGain) {
		advance = false
	}
	if b.pacingGain < 1 && inFlight <= b.targetCwnd(1) {
		advance = true
	}
	if !advance {
		return
	}
	b.cycleOffset = (b.cycleOffset + 1) % uint8(len(tuicPacingGains))
	b.lastCycle = now
	b.pacingGain = tuicPacingGains[b.cycleOffset]
}

func (b *TUICBBRSender) maybeExitStartupDrain(now monotime.Time, inFlight quiccongestion.ByteCount) {
	if b.mode == tuicBbrStartup && b.fullBandwidth {
		b.mode = tuicBbrDrain
		b.pacingGain = b.drainGain
		b.cwndGain = b.highCwndGain
	}
	if b.mode == tuicBbrDrain && inFlight <= b.targetCwnd(1) {
		b.mode = tuicBbrProbeBW
		b.cwndGain = tuicCwndGain
		b.lastCycle = now
		b.cycleOffset = b.nextCycleOffset()
		b.pacingGain = tuicPacingGains[b.cycleOffset]
	}
}

func (b *TUICBBRSender) nextCycleOffset() uint8 {
	// A per-controller xorshift state avoids synchronized ProbeBW cycles while
	// keeping the hot path allocation- and lock-free. The time/MTU seed is
	// different for independently created lanes; zero is repaired defensively.
	if b.randomState == 0 {
		b.randomState = uint64(monotime.Now()) ^ uint64(b.maxDatagramSize)<<19 ^ 0x9e3779b97f4a7c15
	}
	x := b.randomState
	x ^= x << 13
	x ^= x >> 7
	x ^= x << 17
	b.randomState = x
	offset := uint8(x % uint64(len(tuicPacingGains)-1))
	// TUIC starts ProbeBW at gain index 0 or 2..7. Index 1 is excluded so a
	// connection never enters the 0.75 drain phase without first probing.
	if offset >= 1 {
		offset++
	}
	return offset
}

func (b *TUICBBRSender) checkFullBandwidth(lastSendState tuicSendState) {
	if b.lastSampleAppLimited {
		return
	}
	target := uint64(float64(b.bwAtLastRound) * tuicStartupGrowth)
	bw := b.estimator.estimate()
	if bw >= target {
		b.bwAtLastRound = bw
		b.roundsNoGain = 0
		return
	}
	b.roundsNoGain++
	if b.roundsNoGain >= tuicStartupNoGainRounds || b.shouldExitStartupForLoss(lastSendState) {
		b.fullBandwidth = true
	}
}

func (b *TUICBBRSender) shouldExitStartupForLoss(lastSendState tuicSendState) bool {
	if b.lossEventsInRound < tuicStartupLossEvents || !lastSendState.valid || lastSendState.bytesInFlight == 0 || b.bytesLostInRound == 0 {
		return false
	}
	return float64(b.bytesLostInRound) > float64(lastSendState.bytesInFlight)*tuicStartupLossFraction
}

func (b *TUICBBRSender) maybeProbeRTT(now monotime.Time, roundStart bool, inFlight quiccongestion.ByteCount, minRTTExpired bool) {
	if minRTTExpired && !b.exitingQuiescence && b.mode != tuicBbrProbeRTT {
		b.mode = tuicBbrProbeRTT
		b.pacingGain = 1
		b.exitProbeRTT = 0
	}
	if b.mode != tuicBbrProbeRTT {
		b.exitingQuiescence = false
		return
	}
	// ProbeRTT samples are intentionally application-limited. Otherwise the
	// forced four-packet window can replace a valid bandwidth peak with the
	// artificial ProbeRTT delivery rate.
	b.estimator.markAppLimited()
	if b.exitProbeRTT.IsZero() && inFlight < b.probeRTTCwnd()+b.maxDatagramSize {
		b.exitProbeRTT = now.Add(tuicProbeRTTDuration)
		b.probeRTTRoundPassed = false
	}
	if !b.exitProbeRTT.IsZero() && roundStart {
		b.probeRTTRoundPassed = true
	}
	if !b.exitProbeRTT.IsZero() && b.probeRTTRoundPassed && !now.Before(b.exitProbeRTT) {
		b.minRTTAt = now
		if b.fullBandwidth {
			b.mode = tuicBbrProbeBW
			b.cwndGain = tuicCwndGain
			b.lastCycle = now
			b.cycleOffset = b.nextCycleOffset()
			b.pacingGain = tuicPacingGains[b.cycleOffset]
		} else {
			b.mode = tuicBbrStartup
			b.pacingGain = b.highGain
			b.cwndGain = b.highCwndGain
		}
	}
	b.exitingQuiescence = false
}

func (b *TUICBBRSender) targetCwnd(gain float64) quiccongestion.ByteCount {
	bw := b.estimator.estimate()
	if bw == 0 {
		target := float64(b.initialCwnd) * gain
		if target > float64(b.maxCwnd) {
			return b.maxCwnd
		}
		return maxByteCount(b.minCwnd, quiccongestion.ByteCount(target))
	}
	rtt := b.minRTT
	if rtt <= 0 {
		rtt = b.rtt()
	}
	bdp := float64(bw) * rtt.Seconds() * gain
	if math.IsNaN(bdp) || math.IsInf(bdp, 0) || bdp < float64(b.minCwnd) {
		return b.minCwnd
	}
	if bdp > float64(b.maxCwnd) {
		return b.maxCwnd
	}
	return quiccongestion.ByteCount(bdp)
}

func (b *TUICBBRSender) probeRTTCwnd() quiccongestion.ByteCount {
	return b.minCwnd
}

func (b *TUICBBRSender) calculatePacingRate() {
	bw := b.estimator.estimate()
	if bw == 0 {
		return
	}
	target := uint64(float64(bw) * b.pacingGain)
	if b.fullBandwidth {
		b.pacingRate = target
	} else {
		// The public startup rate is high_gain*IW/RTT while the stored rate is
		// still zero. On the first useful event with a provider RTT, native TUIC
		// seeds the stored model at IW/min_rtt before later ACKs grow it toward
		// the delivery estimate.
		if b.pacingRate == 0 && b.rttStats != nil {
			if rtt := b.rttStats.MinRTT(); rtt > 0 {
				b.pacingRate = rateFromDelta(uint64(b.initialCwnd), rtt)
				if b.pacingRate > tuicMaxRate {
					b.pacingRate = tuicMaxRate
				}
				return
			}
		}
		if b.pacingRate < target {
			b.pacingRate = target
		}
	}
	if b.pacingRate > tuicMaxRate {
		b.pacingRate = tuicMaxRate
	}
}

func (b *TUICBBRSender) calculateCwnd(bytesAcked, excessAcked uint64) {
	if b.mode == tuicBbrProbeRTT {
		return
	}
	target := b.targetCwnd(b.cwndGain)
	if b.fullBandwidth {
		target = minByteCount(b.maxCwnd, saturatingByteAdd(target, b.ackAgg.maxAckHeight.get()))
	}
	if b.fullBandwidth {
		b.cwnd = minByteCount(target, saturatingByteAdd(b.cwnd, bytesAcked))
	} else if b.cwnd < target || b.ackedBytes < uint64(b.initialCwnd) {
		b.cwnd = minByteCount(b.maxCwnd, saturatingByteAdd(b.cwnd, bytesAcked))
	}
	if b.cwnd < b.minCwnd {
		b.cwnd = b.minCwnd
	}
}

func (b *TUICBBRSender) calculateRecoveryWindow(bytesAcked, bytesLost uint64, inFlight quiccongestion.ByteCount) {
	if !b.recovery.inRecovery() {
		return
	}
	lost := maxCongestionByteCount
	if bytesLost < uint64(maxCongestionByteCount) {
		lost = quiccongestion.ByteCount(bytesLost)
	}
	if b.recoveryWindow == 0 {
		b.recoveryWindow = maxByteCount(b.minCwnd, saturatingByteAdd(inFlight, bytesAcked))
		return
	}
	if b.recoveryWindow >= lost {
		b.recoveryWindow -= lost
	} else {
		b.recoveryWindow = b.maxDatagramSize
	}
	if b.recovery == tuicGrowth {
		b.recoveryWindow = saturatingByteAdd(b.recoveryWindow, bytesAcked)
	}
	minimum := maxByteCount(b.minCwnd, saturatingByteAdd(inFlight, bytesAcked))
	if b.recoveryWindow < minimum {
		b.recoveryWindow = minimum
	}
}

func (b *TUICBBRSender) OnRetransmissionTimeout(retransmitted bool) {
	// QUIC PTOs are probe events, not proof that the bottleneck model is
	// invalid. Native TUIC leaves BBR state intact and lets the ordinary ACK /
	// loss event update recovery. Resetting to a four-packet window here makes
	// one lossy-RTT PTO create a long throughput collapse.
	_ = retransmitted
}

func (b *TUICBBRSender) SetMaxDatagramSize(size quiccongestion.ByteCount) {
	if size <= 0 {
		return
	}
	oldSize := b.maxDatagramSize
	if oldSize <= 0 {
		oldSize = size
	}
	oldMinCwnd := b.minCwnd
	oldInitialCwnd := b.initialCwnd
	b.maxDatagramSize = size
	b.minCwnd = 4 * size
	b.maxCwnd = quiccongestion.MaxCongestionWindowPackets * size
	b.initialCwnd = scaleTUICWindow(oldInitialCwnd, oldSize, size)
	b.initialCwnd = minByteCount(b.maxCwnd, maxByteCount(b.minCwnd, b.initialCwnd))
	switch b.cwnd {
	case oldMinCwnd:
		b.cwnd = b.minCwnd
	case oldInitialCwnd:
		b.cwnd = b.initialCwnd
	default:
		b.cwnd = minByteCount(b.maxCwnd, maxByteCount(b.minCwnd, b.cwnd))
	}
	// Recovery is a byte budget accumulated from actual ACK/loss events, not a
	// packet-count setting. Preserve its byte value across an MTU increase and
	// only clamp it to the newly valid window range.
	b.recoveryWindow = minByteCount(b.maxCwnd, maxByteCount(b.minCwnd, b.recoveryWindow))
	b.pacer.setMaxDatagramSize(size)
	b.publishTelemetry()
}

func scaleTUICWindow(window, oldSize, newSize quiccongestion.ByteCount) quiccongestion.ByteCount {
	if window <= 0 || oldSize <= 0 || newSize <= 0 || oldSize == newSize {
		return window
	}
	if window > maxCongestionByteCount/newSize {
		return maxCongestionByteCount
	}
	return window * newSize / oldSize
}

func (b *TUICBBRSender) InSlowStart() bool { return b.mode == tuicBbrStartup }
func (b *TUICBBRSender) InRecovery() bool  { return b.recovery.inRecovery() }

func (b *TUICBBRSender) GetCongestionWindow() quiccongestion.ByteCount {
	window := b.cwnd
	if b.mode == tuicBbrProbeRTT {
		window = b.probeRTTCwnd()
	}
	if window < b.minCwnd {
		window = b.minCwnd
	}
	if b.recovery.inRecovery() && b.mode != tuicBbrStartup && b.recoveryWindow > 0 && window > b.recoveryWindow {
		window = b.recoveryWindow
	}
	return window
}

func (b *TUICBBRSender) publishTelemetry() {
	mode := ControllerModeStartup
	switch b.mode {
	case tuicBbrDrain:
		mode = ControllerModeDrain
	case tuicBbrProbeBW:
		mode = ControllerModeProbeBW
	case tuicBbrProbeRTT:
		mode = ControllerModeProbeRTT
	}
	b.telemetry.update(mode, b.estimator.estimate(), uint64(b.bandwidth()), int64(b.GetCongestionWindow()), int64(b.bytesInFlight), b.minRTT, b.recovery.inRecovery())
	b.telemetry.updateSampler(
		b.estimator.latestSample,
		b.estimator.latestAckRate,
		b.estimator.latestSendRate,
		b.estimator.samples,
		b.estimator.nonAppSamples,
		b.estimator.appSamples,
		b.estimator.stateMisses,
		b.estimator.zeroSamples,
		b.round,
	)
	_, mean, max, delivered, interval := b.estimator.sampleSummary()
	b.telemetry.updateSampleShape(mean, max, delivered, interval)
}

func (b *TUICBBRSender) Telemetry() ControllerTelemetry { return b.telemetry.snapshot() }

func (a *tuicAckAggregation) update(newlyAcked uint64, now monotime.Time, round, bandwidth uint64) uint64 {
	if newlyAcked == 0 || bandwidth == 0 {
		a.epochBytes = newlyAcked
		a.epochStart = now
		return 0
	}
	var expected uint64
	if !a.epochStart.IsZero() && now.After(a.epochStart) {
		elapsedMicros := uint64(now.Sub(a.epochStart).Microseconds())
		hi, lo := bits.Mul64(bandwidth, elapsedMicros)
		if hi == 0 {
			expected = lo / 1_000_000
		} else {
			expected = ^uint64(0)
		}
	}
	if a.epochBytes <= expected {
		a.epochBytes = newlyAcked
		a.epochStart = now
		return 0
	}
	a.epochBytes = satAddUint64(a.epochBytes, newlyAcked)
	diff := a.epochBytes - expected
	// The ack-aggregation filter keeps the original round-only clock: it
	// measures how much more than expected one round delivered, which is a
	// statement about rounds and means nothing between them. A zero time
	// leaves it exactly as it was.
	a.maxAckHeight.updateMax(round, monotime.Time(0), diff)
	return diff
}
