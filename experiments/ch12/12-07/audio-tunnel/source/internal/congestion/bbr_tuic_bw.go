package congestion

import (
	"slices"

	"math/bits"
	"time"

	quiccongestion "github.com/apernet/quic-go/congestion"
	"github.com/apernet/quic-go/monotime"
)

// tuicBandwidthEstimator is a bounded packet-state delivery sampler.  TUIC's
// BBR takes the minimum of an ACK-rate and a send-rate slope, then retains a
// maximum over a finite round window.  The important detail is that each
// acknowledged packet carries the cumulative send/ACK state captured when it
// was sent.  A cumulative event-only estimator loses that information under
// ACK coalescing and can mistake one delayed packet for the path bandwidth.
//
// The public quic-go callback does not currently populate ReceivedTime, so the
// sampler uses the congestion event time as the ACK time and automatically
// benefits from per-packet receive times when a future fork supplies them.
// Memory is bounded even if a peer stops acknowledging packets.
type tuicBandwidthEstimator struct {
	totalAcked uint64
	// sampleTrace, when set, receives every delivery-rate sample the estimator
	// considered for the filter. It is nil in production and exists because
	// three attempts to fix the estimate on a policed path were made by
	// reasoning about what these numbers should be, and each was wrong.
	sampleTrace func(bandwidthSampleTrace)

	// Sample summary, kept always rather than behind the trace hook, because
	// the question it answers cannot be asked of a harness: whether the samples
	// this estimator is built from are the right shape on a real path.
	//
	// A rate on its own cannot say whether it is high because the path is fast
	// or because the window it was measured over was short, so the widest
	// sample is kept together with the interval and the delivery behind it. The
	// mean beside it says whether a high maximum is the distribution or its
	// tail.
	sampleCount        uint64
	sampleRateSum      uint64
	sampleRateMax      uint64
	sampleMaxDelivered uint64
	sampleMaxInterval  time.Duration

	totalSent      uint64
	latestSample   uint64
	latestAckRate  uint64
	latestSendRate uint64
	samples        uint64
	nonAppSamples  uint64
	appSamples     uint64
	stateMisses    uint64
	zeroSamples    uint64

	lastAckedSentTime monotime.Time
	lastAckedAckTime  monotime.Time
	totalSentAtAck    uint64
	lastAckedPacket   quiccongestion.PacketNumber
	lastSentPacket    quiccongestion.PacketNumber
	appLimited        bool
	endAppLimitedAt   quiccongestion.PacketNumber
	maxFilter         tuicMinMax
	ackedAtWindow     uint64
	packetStates      map[quiccongestion.PacketNumber]tuicPacketState
	// lowestState is the smallest packet number that may still be present in
	// packetStates. Packet numbers only increase, so it turns removeObsolete
	// from a scan of everything in flight into a walk of what is actually
	// being dropped. See there for what that cost.
	lowestState        quiccongestion.PacketNumber
	lowestKnown        bool
	legacyPrevAcked    uint64
	legacyPrevAckTime  monotime.Time
	legacyPrevSent     uint64
	legacyPrevSentTime monotime.Time
	legacyAckedTime    monotime.Time
	legacySentTime     monotime.Time
}

type tuicPacketState struct {
	sentTime          monotime.Time
	totalSentAtSend   uint64
	totalSentAtAck    uint64
	totalAckedAtSend  uint64
	lastAckedSentTime monotime.Time
	lastAckedAckTime  monotime.Time
	appLimited        bool
	// bytesInFlight is the post-send flight recorded with this packet. Native
	// TUIC uses this send-time state both for mixed ACK/loss event ordering and
	// for the bounded STARTUP loss-exit test.
	bytesInFlight uint64
}

// tuicSendState is the small part of a packet snapshot consumed by the BBR
// state machine after a congestion event. Keeping the packet number here makes
// mixed ACK/loss selection independent of callback slice ordering.
type tuicSendState struct {
	packetNumber  quiccongestion.PacketNumber
	bytesInFlight uint64
	appLimited    bool
	valid         bool
}

const tuicMaxSendStates = 8192

func newTUICBandwidthEstimator() tuicBandwidthEstimator {
	return tuicBandwidthEstimator{
		lastAckedPacket: quiccongestion.PacketNumber(-1),
		lastSentPacket:  quiccongestion.PacketNumber(-1),
		endAppLimitedAt: quiccongestion.PacketNumber(-1),
		maxFilter:       newTUICMinMax(),
		packetStates:    make(map[quiccongestion.PacketNumber]tuicPacketState),
	}
}

// markAppLimited starts the same packet-scoped app-limited phase used by
// TUIC's sampler. Packets already in flight remain ordinary samples; packets
// sent after this point carry the marker until an ACK for a later packet ends
// the phase. This is more precise than classifying an entire congestion event
// from its wall-clock gap, and it avoids suppressing samples after loss merely
// because only one packet was left in flight.
func (e *tuicBandwidthEstimator) markAppLimited() {
	e.appLimited = true
	e.endAppLimitedAt = e.lastSentPacket
}

// onSentPacket records the cumulative state at the time a congestion
// controlled packet is sent. Non-retransmittable packets are intentionally
// excluded from delivery-rate samples, matching QUIC BBR practice.
func (e *tuicBandwidthEstimator) onSentPacket(now monotime.Time, number quiccongestion.PacketNumber, bytes, bytesInFlight uint64, retransmittable bool) {
	e.lastSentPacket = number
	if !retransmittable || bytes == 0 {
		return
	}
	e.totalSent = satAddUint64(e.totalSent, bytes)
	// TUIC's sampler establishes an A0/S0 point whenever a new flight starts.
	// Without this point the entire first congestion window produces no
	// delivery sample. On a lossy long-RTT path the second flight may already
	// be recovery-limited, permanently seeding BBR at only a few packets per
	// RTT. The first packet itself has a zero send interval and therefore uses
	// the ACK slope; later packets in the same flight obtain both slopes.
	if bytesInFlight == 0 {
		e.lastAckedAckTime = now
		e.lastAckedSentTime = now
		e.totalSentAtAck = e.totalSent
	}
	if len(e.packetStates) >= tuicMaxSendStates {
		e.pruneStates()
	}
	if !e.lowestKnown {
		e.lowestState, e.lowestKnown = number, true
	}
	e.packetStates[number] = tuicPacketState{
		sentTime:          now,
		totalSentAtSend:   e.totalSent,
		totalSentAtAck:    e.totalSentAtAck,
		totalAckedAtSend:  e.totalAcked,
		lastAckedSentTime: e.lastAckedSentTime,
		lastAckedAckTime:  e.lastAckedAckTime,
		appLimited:        e.appLimited,
		bytesInFlight:     satAddUint64(bytesInFlight, bytes),
	}
}

// onLost deliberately retains packet state. QUIC can report a packet lost and
// later receive it (spurious loss/reordering), and TUIC uses that ACK to keep
// the delivery sampler's cumulative curves consistent. Obsolete states are
// removed by removeObsolete after each congestion event; the bounded prune is
// only a final memory guard.
func (e *tuicBandwidthEstimator) onLost(number quiccongestion.PacketNumber) tuicSendState {
	state, ok := e.packetStates[number]
	if !ok {
		return tuicSendState{}
	}
	return tuicSendState{
		packetNumber:  number,
		bytesInFlight: state.bytesInFlight,
		appLimited:    state.appLimited,
		valid:         true,
	}
}

// removeObsolete drops states that are below the oldest packet QUIC is likely
// to retain. The extended quic-go callback does not expose FirstOutstanding,
// so callers pass the same bounded packet-threshold approximation used by the
// upstream TUIC controller.
//
// It walks the range being dropped rather than scanning the map, because
// packet numbers only increase and so everything below leastUnacked that is
// still present lies in [lowestState, leastUnacked). The scan it replaces cost
// the whole of what was in flight on every congestion event: at 300 Mbit/s over
// a 200ms round trip that is about six thousand entries, re-walked per
// acknowledgement, and a CPU profile of a 294 Mbit/s transfer attributed 13% of
// all time to this one loop. Walking the range instead costs one delete per
// packet number ever sent, amortised, which is one per packet.
//
// pruneStates can empty the map without the watermark seeing it, so the walk is
// only taken while the range is no longer than the map; past that the scan is
// the cheaper of the two and is bounded by tuicMaxSendStates.
func (e *tuicBandwidthEstimator) removeObsolete(leastUnacked quiccongestion.PacketNumber) {
	if len(e.packetStates) == 0 {
		e.lowestState, e.lowestKnown = leastUnacked, true
		return
	}
	if gap := leastUnacked - e.lowestState; e.lowestKnown && gap >= 0 && int(gap) <= 2*len(e.packetStates) {
		for number := e.lowestState; number < leastUnacked; number++ {
			delete(e.packetStates, number)
		}
		e.lowestState = leastUnacked
		return
	}
	for number := range e.packetStates {
		if number < leastUnacked {
			delete(e.packetStates, number)
		}
	}
	e.lowestState, e.lowestKnown = leastUnacked, true
}

// bandwidthSampleTrace is one delivery-rate sample with the two quantities it
// was computed from, which is what a maximum filter hides: the rate alone
// cannot say whether it is high because the path is fast or because the window
// it was measured over was short.
type bandwidthSampleTrace struct {
	Round        uint64
	AckRate      uint64
	SendRate     uint64
	Sample       uint64
	AckInterval  time.Duration
	SendInterval time.Duration
	AckedDelta   uint64
	SentDelta    uint64
	AppLimited   bool
}

type tuicAckSample struct {
	lastAppLimited   bool
	hasSample        bool
	maxBandwidth     uint64
	sampleAppLimited bool
	minRTT           time.Duration
	lastSendState    tuicSendState
}

// onAckBatch consumes one congestion event. ACK packets are processed in the
// order supplied by quic-go, but all contribute to one cumulative ACK clock.
// A packet's captured state supplies the preceding A0/S0 points, avoiding the
// zero-duration samples caused by calling an estimator once per packet at one
// event timestamp.
func (e *tuicBandwidthEstimator) onAckBatch(eventTime monotime.Time, acked []quiccongestion.AckedPacketInfo, round uint64) tuicAckSample {
	if eventTime.IsZero() {
		eventTime = monotime.Now()
	}
	result := tuicAckSample{}
	var largestState tuicPacketState
	var largestPN quiccongestion.PacketNumber
	var haveLargest bool
	for _, packet := range acked {
		if packet.BytesAcked <= 0 {
			continue
		}
		state, ok := e.packetStates[packet.PacketNumber]
		if !ok {
			e.stateMisses = satAddUint64(e.stateMisses, 1)
			continue
		}
		bytes := uint64(packet.BytesAcked)
		e.totalAcked = satAddUint64(e.totalAcked, bytes)
		if e.appLimited && (e.endAppLimitedAt < 0 || packet.PacketNumber > e.endAppLimitedAt) {
			e.appLimited = false
		}
		ackTime := eventTime
		if !packet.ReceivedTime.IsZero() {
			ackTime = packet.ReceivedTime
		}
		if ackTime.After(state.sentTime) {
			rtt := ackTime.Sub(state.sentTime)
			if result.minRTT <= 0 || rtt < result.minRTT {
				result.minRTT = rtt
			}
		}
		ackRate := uint64(0)
		if !state.lastAckedAckTime.IsZero() && ackTime.After(state.lastAckedAckTime) && e.totalAcked >= state.totalAckedAtSend {
			ackRate = rateFromDelta(e.totalAcked-state.totalAckedAtSend, ackTime.Sub(state.lastAckedAckTime))
		}
		sendRate := uint64(0)
		if !state.lastAckedSentTime.IsZero() && state.sentTime.After(state.lastAckedSentTime) && state.totalSentAtSend >= state.totalSentAtAck {
			sendRate = rateFromDelta(state.totalSentAtSend-state.totalSentAtAck, state.sentTime.Sub(state.lastAckedSentTime))
		}
		if e.sampleTrace != nil {
			trace := bandwidthSampleTrace{Round: round, AckRate: ackRate, SendRate: sendRate, AppLimited: state.appLimited}
			if !state.lastAckedAckTime.IsZero() && ackTime.After(state.lastAckedAckTime) {
				trace.AckInterval = ackTime.Sub(state.lastAckedAckTime)
				if e.totalAcked >= state.totalAckedAtSend {
					trace.AckedDelta = e.totalAcked - state.totalAckedAtSend
				}
			}
			if !state.lastAckedSentTime.IsZero() && state.sentTime.After(state.lastAckedSentTime) {
				trace.SendInterval = state.sentTime.Sub(state.lastAckedSentTime)
				if state.totalSentAtSend >= state.totalSentAtAck {
					trace.SentDelta = state.totalSentAtSend - state.totalSentAtAck
				}
			}
			trace.Sample = ackRate
			if sendRate > 0 && (trace.Sample == 0 || sendRate < trace.Sample) {
				trace.Sample = sendRate
			}
			e.sampleTrace(trace)
		}
		{
			candidate := ackRate
			if sendRate > 0 && (candidate == 0 || sendRate < candidate) {
				candidate = sendRate
			}
			if candidate > 0 {
				e.sampleCount = satAddUint64(e.sampleCount, 1)
				e.sampleRateSum = satAddUint64(e.sampleRateSum, candidate)
				if candidate > e.sampleRateMax {
					e.sampleRateMax = candidate
					if !state.lastAckedAckTime.IsZero() && ackTime.After(state.lastAckedAckTime) {
						e.sampleMaxInterval = ackTime.Sub(state.lastAckedAckTime)
					} else {
						e.sampleMaxInterval = 0
					}
					if e.totalAcked >= state.totalAckedAtSend {
						e.sampleMaxDelivered = e.totalAcked - state.totalAckedAtSend
					} else {
						e.sampleMaxDelivered = 0
					}
				}
			}
		}
		sample := ackRate
		e.latestAckRate = ackRate
		e.latestSendRate = sendRate
		if sendRate > 0 && (sample == 0 || sendRate < sample) {
			sample = sendRate
		}
		e.latestSample = sample
		if sample > 0 {
			result.hasSample = true
			e.samples = satAddUint64(e.samples, 1)
			if state.appLimited {
				e.appSamples = satAddUint64(e.appSamples, 1)
			} else {
				e.nonAppSamples = satAddUint64(e.nonAppSamples, 1)
			}
		} else {
			e.zeroSamples = satAddUint64(e.zeroSamples, 1)
		}
		// Native TUIC selects one maximum bandwidth sample for the complete ACK
		// event and updates its ten-round filter once. Updating the filter for
		// every packet in a coalesced ACK batch changes the second/third samples
		// and can expire a valid peak early even though all packets share a round.
		if sample > result.maxBandwidth {
			result.maxBandwidth = sample
			result.sampleAppLimited = state.appLimited
		}
		if !haveLargest || packet.PacketNumber > largestPN {
			largestPN, largestState, haveLargest = packet.PacketNumber, state, true
		}
		delete(e.packetStates, packet.PacketNumber)
	}
	if haveLargest {
		ackTime := eventTime
		for _, packet := range acked {
			if packet.PacketNumber == largestPN && !packet.ReceivedTime.IsZero() {
				ackTime = packet.ReceivedTime
				break
			}
		}
		e.lastAckedSentTime = largestState.sentTime
		e.lastAckedAckTime = ackTime
		e.totalSentAtAck = largestState.totalSentAtSend
		e.lastAckedPacket = largestPN
		result.lastAppLimited = largestState.appLimited
		result.lastSendState = tuicSendState{
			packetNumber:  largestPN,
			bytesInFlight: largestState.bytesInFlight,
			appLimited:    largestState.appLimited,
			valid:         true,
		}
	}
	// App-limited samples cannot lower the model, but an app-limited event
	// above the current best is still proof of higher deliverable bandwidth.
	//
	// The exception is a standing estimate that has outlived its window. That
	// rule protects a live estimate from a sender that had nothing to send and
	// therefore learned nothing; once the estimate has expired there is
	// nothing left to protect, and refusing the only samples on offer is how
	// the filter would keep a value it has already decided not to trust. On a
	// connection that is application limited essentially always -- 99.98% of
	// samples on the path this was measured against -- that exception is the
	// only way the estimate ever comes down.
	if result.maxBandwidth > 0 &&
		(!result.sampleAppLimited || result.maxBandwidth > e.maxFilter.get() || e.maxFilter.stale(eventTime)) {
		if result.minRTT > 0 {
			e.maxFilter.setRoundTrip(result.minRTT)
		}
		e.maxFilter.updateMax(round, eventTime, result.maxBandwidth)
	}
	return result
}

// onSent and onAck are retained as aggregate helpers for deterministic unit
// tests and callers that do not have packet numbers. Production QUIC callbacks
// use onSentPacket and onAckBatch above.
func (e *tuicBandwidthEstimator) onSent(now monotime.Time, bytes uint64) {
	e.legacyPrevSent = e.totalSent
	e.totalSent = satAddUint64(e.totalSent, bytes)
	e.legacyPrevSentTime = e.legacySentTime
	e.legacySentTime = now
}

func (e *tuicBandwidthEstimator) onAck(now monotime.Time, bytes, round uint64, appLimited bool) {
	if bytes == 0 {
		return
	}
	e.legacyPrevAcked = e.totalAcked
	e.totalAcked = satAddUint64(e.totalAcked, bytes)
	e.legacyPrevAckTime = e.legacyAckedTime
	e.legacyAckedTime = now
	if e.legacyPrevAckTime.IsZero() || e.legacyPrevSentTime.IsZero() {
		return
	}
	sendRate := rateFromDelta(e.totalSent-e.legacyPrevSent, e.legacySentTime.Sub(e.legacyPrevSentTime))
	ackRate := rateFromDelta(e.totalAcked-e.legacyPrevAcked, e.legacyAckedTime.Sub(e.legacyPrevAckTime))
	if !appLimited && sendRate > 0 && ackRate > 0 {
		// The aggregate helpers are for deterministic tests and callers with no
		// packet numbers, and carry no event time; a zero leaves the sample on
		// the round clock alone.
		e.maxFilter.updateMax(round, monotime.Time(0), minUint64(sendRate, ackRate))
	}
}

func (e *tuicBandwidthEstimator) onAckEvent(now monotime.Time, bytes, round uint64, appLimited bool) {
	e.onAck(now, bytes, round, appLimited)
}

// pruneStates drops the oldest quarter of the table when it fills.
//
// Packet numbers are assigned in send order, so the oldest states are the
// lowest numbers and one partial selection finds the cut. The previous version
// rescanned the whole map to find a single oldest entry and did that 2048
// times -- about 17 million map iterations, on the send path, every time an
// 8192-entry table filled. At 200 Mbit/s that is roughly every 0.4 seconds.
func (e *tuicBandwidthEstimator) pruneStates() {
	remove := tuicMaxSendStates / 4
	if remove <= 0 || len(e.packetStates) == 0 {
		return
	}
	if remove >= len(e.packetStates) {
		clear(e.packetStates)
		return
	}
	numbers := make([]quiccongestion.PacketNumber, 0, len(e.packetStates))
	for pn := range e.packetStates {
		numbers = append(numbers, pn)
	}
	slices.Sort(numbers)
	for _, pn := range numbers[:remove] {
		delete(e.packetStates, pn)
	}
}

func (e *tuicBandwidthEstimator) bytesAckedThisWindow() uint64 {
	if e.totalAcked < e.ackedAtWindow {
		return 0
	}
	return e.totalAcked - e.ackedAtWindow
}

func (e *tuicBandwidthEstimator) endAcks() { e.ackedAtWindow = e.totalAcked }

func (e *tuicBandwidthEstimator) estimate() uint64 { return e.maxFilter.get() }

// sampleSummary is the shape of the samples the estimate is built from: how
// many, their mean, the widest one, and the interval and delivery behind that
// widest one.
//
// The maximum alone is what the filter reports and is not enough to read it. A
// maximum far above the mean is a tail, and a tail measured over a short
// interval is a measurement artefact rather than a path.
func (e *tuicBandwidthEstimator) sampleSummary() (count, mean, max, delivered uint64, interval time.Duration) {
	if e.sampleCount > 0 {
		mean = e.sampleRateSum / e.sampleCount
	}
	return e.sampleCount, mean, e.sampleRateMax, e.sampleMaxDelivered, e.sampleMaxInterval
}

func rateFromDelta(bytes uint64, elapsed time.Duration) uint64 {
	if bytes == 0 || elapsed <= 0 {
		return 0
	}
	ns := uint64(elapsed.Nanoseconds())
	if ns == 0 {
		return 0
	}
	// Divide a 128-bit product by a 64-bit duration. bits.Div64 reports
	// overflow when the quotient would not fit in uint64; saturating is safer
	// than wrapping a telemetry or pacing rate.
	hi, lo := bits.Mul64(bytes, 1_000_000_000)
	if hi >= ns {
		return ^uint64(0)
	}
	q, _ := bits.Div64(hi, lo, ns)
	return q
}

func satAddUint64(a, b uint64) uint64 {
	if ^uint64(0)-a < b {
		return ^uint64(0)
	}
	return a + b
}

func minUint64(a, b uint64) uint64 {
	if a < b {
		return a
	}
	return b
}
