package congestion

import (
	"testing"
	"time"

	quiccongestion "github.com/apernet/quic-go/congestion"
	"github.com/apernet/quic-go/monotime"
)

// sendTUICPacket models the pre-send flight that the sampler consumes. The
// production QUIC adapter receives post-send bytesInFlight and converts it at
// the controller boundary.
func sendTUICPacket(sender *TUICBBRSender, sentTime monotime.Time, preSend quiccongestion.ByteCount, number quiccongestion.PacketNumber, bytes quiccongestion.ByteCount) {
	postSend := preSend + bytes
	sender.OnPacketSent(sentTime, postSend, number, bytes, true)
}

func TestTUICMinMaxRetainsPeakForTenRounds(t *testing.T) {
	m := newTUICMinMax()
	m.updateMax(1, monotime.Time(0), 100)
	m.updateMax(3, monotime.Time(0), 120)
	m.updateMax(5, monotime.Time(0), 160)
	m.updateMax(7, monotime.Time(0), 100)
	m.updateMax(10, monotime.Time(0), 100)
	if got := m.get(); got != 160 {
		t.Fatalf("peak was lost inside filter window: %d", got)
	}
	m.updateMax(16, monotime.Time(0), 100)
	if got := m.get(); got != 100 {
		t.Fatalf("expired peak remained in filter: %d", got)
	}
}

func TestTUICMinMaxHalfWindowStartsAtThirdSample(t *testing.T) {
	m := newTUICMinMax()
	m.updateMax(0, monotime.Time(0), 100)
	// The quarter-window refresh records the second and third samples at round
	// three. The half-window clock must start there, not at the original best.
	m.updateMax(3, monotime.Time(0), 90)
	m.updateMax(6, monotime.Time(0), 80)
	if got := m.samples[2]; got.round != 3 || got.value != 90 {
		t.Fatalf("third sample advanced before its half-window elapsed: %+v", got)
	}
	m.updateMax(9, monotime.Time(0), 80)
	if got := m.samples[2]; got.round != 9 || got.value != 80 {
		t.Fatalf("third sample did not advance after its half-window: %+v", got)
	}
}

func TestTUICPacerUsesNativeBurstInterval(t *testing.T) {
	rate := quiccongestion.ByteCount(100 * 1024 * 1024)
	p := newTUICPacer(func() quiccongestion.ByteCount { return rate })
	want := quiccongestion.ByteCount(tuicBurstPacingDelay.Nanoseconds()) * rate / 1e9
	if floor := quiccongestion.ByteCount(maxBurstPackets) * p.maxDatagramSize; want < floor {
		want = floor
	}
	if got := p.maxBurstSize(); got != want {
		t.Fatalf("TUIC burst budget=%d, want %d", got, want)
	}
}

func TestTUICBandwidthUsesMinimumOfSendAndACKRates(t *testing.T) {
	e := newTUICBandwidthEstimator()
	start := monotime.Now()
	e.onSent(start, 1200)
	e.onSent(start.Add(10*time.Millisecond), 1200)
	e.onAck(start.Add(210*time.Millisecond), 1200, 1, false)
	e.onSent(start.Add(220*time.Millisecond), 1200)
	e.onSent(start.Add(230*time.Millisecond), 1200)
	e.onAck(start.Add(410*time.Millisecond), 1200, 1, false)
	if got := e.estimate(); got == 0 || got > 130*1024 {
		t.Fatalf("unexpected first bandwidth estimate: %d", got)
	}
}

func TestTUICBandwidthAggregatesCoalescedAckBatch(t *testing.T) {
	e := newTUICBandwidthEstimator()
	start := monotime.Now()
	// Send at 1 MiB/s for one RTT, then acknowledge a 64 KiB burst in one
	// event. The aggregate event must produce a useful ACK slope; processing
	// each packet with the same timestamp would only account for one packet.
	for i := 0; i < 64; i++ {
		e.onSent(start.Add(time.Duration(i)*time.Millisecond), 1024)
	}
	e.onAckEvent(start.Add(264*time.Millisecond), 64*1024, 1, false)
	for i := 0; i < 64; i++ {
		e.onSent(start.Add(264*time.Millisecond+time.Duration(i)*time.Millisecond), 1024)
	}
	e.onAckEvent(start.Add(528*time.Millisecond), 64*1024, 2, false)
	if got := e.estimate(); got < 200*1024 {
		t.Fatalf("coalesced ACK batch was underestimated: %d B/s", got)
	}
}

func TestTUICPacketSamplerUsesPerPacketSendState(t *testing.T) {
	e := newTUICBandwidthEstimator()
	start := monotime.Now()
	var pn quiccongestion.PacketNumber
	first := make([]quiccongestion.AckedPacketInfo, 0, 50)
	for i := 0; i < 50; i++ {
		e.onSentPacket(start.Add(time.Duration(i)*time.Millisecond), pn, 1200, uint64(i)*1200, true)
		first = append(first, quiccongestion.AckedPacketInfo{PacketNumber: pn, BytesAcked: 1200})
		pn++
	}
	e.onAckBatch(start.Add(100*time.Millisecond), first, 1)
	if got := e.estimate(); got == 0 {
		t.Fatal("the initial flight did not seed a delivery-rate sample")
	}
	second := make([]quiccongestion.AckedPacketInfo, 0, 50)
	for i := 0; i < 50; i++ {
		e.onSentPacket(start.Add(101*time.Millisecond+time.Duration(i)*time.Millisecond), pn, 1200, uint64(50+i)*1200, true)
		second = append(second, quiccongestion.AckedPacketInfo{PacketNumber: pn, BytesAcked: 1200})
		pn++
	}
	e.onAckBatch(start.Add(200*time.Millisecond), second, 2)
	if got := e.estimate(); got < 500*1024 {
		t.Fatalf("packet-state sampler underestimated ACK batch: %d B/s", got)
	}
}

func TestTUICPacketSamplerKeepsPerPacketSendBaseline(t *testing.T) {
	e := newTUICBandwidthEstimator()
	start := monotime.Now()
	e.onSentPacket(start, 0, 1200, 0, true)
	e.onAckBatch(start.Add(100*time.Millisecond), []quiccongestion.AckedPacketInfo{{PacketNumber: 0, BytesAcked: 1200}}, 1)
	// Keep one flight open. ACK packet 1 before packet 2 so the estimator's
	// global last-ACK point advances while packet 2 still needs the older A0/S0
	// baseline captured at its send time.
	e.onSentPacket(start.Add(10*time.Millisecond), 1, 1200, 1200, true)
	e.onSentPacket(start.Add(20*time.Millisecond), 2, 1200, 2400, true)
	e.onAckBatch(start.Add(100*time.Millisecond), []quiccongestion.AckedPacketInfo{{PacketNumber: 1, BytesAcked: 1200}}, 2)
	e.onAckBatch(start.Add(200*time.Millisecond), []quiccongestion.AckedPacketInfo{{PacketNumber: 2, BytesAcked: 1200}}, 3)
	want := rateFromDelta(2400, 20*time.Millisecond)
	if e.latestSendRate != want {
		t.Fatalf("send slope used a later global ACK baseline: got %d, want %d", e.latestSendRate, want)
	}
}

func TestTUICPacketSamplerRetainsSpuriousLossState(t *testing.T) {
	e := newTUICBandwidthEstimator()
	start := monotime.Now()
	e.onSentPacket(start, 0, 1200, 0, true)
	e.onSentPacket(start.Add(time.Millisecond), 1, 1200, 1200, true)
	e.onLost(0)
	if _, ok := e.packetStates[0]; !ok {
		t.Fatal("loss discarded delivery state before a possible spurious ACK")
	}
	result := e.onAckBatch(start.Add(100*time.Millisecond), []quiccongestion.AckedPacketInfo{{PacketNumber: 0, BytesAcked: 1200}}, 1)
	if !result.hasSample || e.estimate() == 0 || e.totalAcked != 1200 {
		t.Fatalf("spurious ACK did not repair the delivery model: sample=%v estimate=%d acked=%d", result.hasSample, e.estimate(), e.totalAcked)
	}
}

func TestTUICAppLimitedMarkerIsPacketScoped(t *testing.T) {
	e := newTUICBandwidthEstimator()
	start := monotime.Now()
	e.onSentPacket(start, 0, 1200, 0, true)
	e.markAppLimited()
	e.onSentPacket(start.Add(time.Millisecond), 1, 1200, 1200, true)
	if e.packetStates[0].appLimited || !e.packetStates[1].appLimited {
		t.Fatal("app-limited marker was not captured at packet send time")
	}
	e.onAckBatch(start.Add(100*time.Millisecond), []quiccongestion.AckedPacketInfo{{PacketNumber: 0, BytesAcked: 1200}}, 1)
	if !e.appLimited {
		t.Fatal("ACK of a pre-marker packet ended the app-limited phase")
	}
	result := e.onAckBatch(start.Add(200*time.Millisecond), []quiccongestion.AckedPacketInfo{{PacketNumber: 1, BytesAcked: 1200}}, 2)
	if !result.lastAppLimited || e.appLimited {
		t.Fatalf("phase boundary was not preserved: sample_app_limited=%v phase=%v", result.lastAppLimited, e.appLimited)
	}
	e.onSentPacket(start.Add(201*time.Millisecond), 2, 1200, 0, true)
	if e.packetStates[2].appLimited {
		t.Fatal("packet after the phase boundary remained app-limited")
	}
}

func TestTUICAppLimitedSampleCanRaiseBandwidth(t *testing.T) {
	e := newTUICBandwidthEstimator()
	e.maxFilter.updateMax(1, monotime.Time(0), 100)
	start := monotime.Now()
	e.markAppLimited()
	e.onSentPacket(start, 0, 1200, 0, true)
	e.onAckBatch(start.Add(100*time.Millisecond), []quiccongestion.AckedPacketInfo{{PacketNumber: 0, BytesAcked: 1200}}, 2)
	if got := e.estimate(); got <= 100 {
		t.Fatalf("higher app-limited sample did not raise bandwidth: %d", got)
	}
}

func TestTUICFirstPacketStartsFirstRound(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.SetRTTStatsProvider(&fakeRTT{smoothed: 100 * time.Millisecond})
	start := monotime.Now()
	sendTUICPacket(sender, start, 0, 0, 1200)
	sender.OnCongestionEventEx(1200, start.Add(100*time.Millisecond), []quiccongestion.AckedPacketInfo{{PacketNumber: 0, BytesAcked: 1200}}, nil)
	if sender.round != 1 {
		t.Fatalf("packet zero did not start the first BBR round: %d", sender.round)
	}
}

// QUIC has three packet-number spaces, and their numbers overlap. The
// congestion-controller API does not identify the space, so a packet in a
// later space can replace the sampler state for a packet with the same number
// in an earlier one. Delivery-rate sampling tolerates the resulting missed or
// short sample, but min_rtt cannot: one false minimum sizes every later BBR
// target window. The RTT provider resolves packet-number spaces before it
// publishes LatestRTT, so it is the authoritative sample when available.
func TestTUICMinRTTUsesProviderAcrossPacketNumberSpaces(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.SetRTTStatsProvider(&fakeRTT{smoothed: 200 * time.Millisecond})
	start := monotime.Now()

	// Model packet zero in an earlier space, followed just before its ACK by
	// packet zero in 1-RTT. The sampler can only retain the latter send time.
	sendTUICPacket(sender, start, 0, 0, 1200)
	sendTUICPacket(sender, start.Add(199*time.Millisecond), 1200, 0, 1200)
	sender.OnCongestionEventEx(2400, start.Add(200*time.Millisecond),
		[]quiccongestion.AckedPacketInfo{{PacketNumber: 0, BytesAcked: 1200}}, nil)

	if got := sender.minRoundTrip(); got != 200*time.Millisecond {
		t.Fatalf("min_rtt used the ambiguous packet sample: got %v, want provider RTT 200ms", got)
	}
}

func TestTUICInitialPacingFieldMatchesNativeTransition(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	// With no RTT sample, the public rate uses TUIC's 100-ms fallback while the
	// internal pacing field remains zero.
	wantFallback := quiccongestion.ByteCount(float64(sender.initialCwnd) * tuicHighGain / 0.1)
	if got := sender.bandwidth(); got != wantFallback || sender.pacingRate != 0 {
		t.Fatalf("fallback pacing mismatch: public=%d stored=%d want=%d", got, sender.pacingRate, wantFallback)
	}
	sender.SetRTTStatsProvider(&fakeRTT{smoothed: 200 * time.Millisecond})
	wantPublic := quiccongestion.ByteCount(float64(sender.initialCwnd) * tuicHighGain / 0.2)
	if got := sender.bandwidth(); got != wantPublic || sender.pacingRate != 0 {
		t.Fatalf("provider pacing seeded stored field early: public=%d stored=%d want=%d", got, sender.pacingRate, wantPublic)
	}
	start := monotime.Now()
	sendTUICPacket(sender, start, 0, 0, 1200)
	sender.OnCongestionEventEx(1200, start.Add(200*time.Millisecond), []quiccongestion.AckedPacketInfo{{PacketNumber: 0, BytesAcked: 1200}}, nil)
	wantStored := rateFromDelta(uint64(sender.initialCwnd), 200*time.Millisecond)
	if sender.pacingRate != wantStored {
		t.Fatalf("first useful event pacing=%d, want IW/min_rtt=%d", sender.pacingRate, wantStored)
	}
}

func TestTUICFlightTelemetryUsesPreSendValueAndIgnoresLegacyCallbacks(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	start := monotime.Now()
	sendTUICPacket(sender, start, 12_000, 7, 1200)
	if sender.bytesInFlight != 13_200 {
		t.Fatalf("send telemetry stored post-send flight: %d", sender.bytesInFlight)
	}
	sender.OnPacketAcked(7, 1200, 10_800, start.Add(time.Millisecond))
	sender.OnCongestionEvent(7, 1200, 9_600)
	if sender.bytesInFlight != 13_200 {
		t.Fatalf("legacy callbacks mutated extended-event flight state: %d", sender.bytesInFlight)
	}
	if got := sender.estimator.packetStates[7].bytesInFlight; got != 13_200 {
		t.Fatalf("packet snapshot flight=%d, want post-send 13200", got)
	}
}

func TestTUICLossOnlyEventDoesNotEnterRecovery(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.fullBandwidth = true
	sender.mode = tuicBbrProbeBW
	start := monotime.Now()
	sendTUICPacket(sender, start, 0, 0, 1200)
	sender.OnCongestionEventEx(1200, start.Add(200*time.Millisecond), nil, []quiccongestion.LostPacketInfo{{PacketNumber: 0, BytesLost: 1200}})
	if sender.InRecovery() {
		t.Fatal("loss-only event entered recovery before an ACK-clocked event")
	}
}

func TestTUICRecoveryRequiresFullBandwidthAndUsesLossPresence(t *testing.T) {
	start := monotime.Now()
	newMixedEvent := func(sender *TUICBBRSender) {
		sendTUICPacket(sender, start, 0, 0, 1200)
		sendTUICPacket(sender, start.Add(time.Millisecond), 1200, 1, 1200)
		sender.OnCongestionEventEx(2400, start.Add(200*time.Millisecond),
			[]quiccongestion.AckedPacketInfo{{PacketNumber: 0, BytesAcked: 1200}},
			[]quiccongestion.LostPacketInfo{{PacketNumber: 1, BytesLost: 0}})
	}
	beforeModel := NewTUICBBRSender(1200)
	beforeModel.mode = tuicBbrProbeRTT
	newMixedEvent(beforeModel)
	if beforeModel.InRecovery() {
		t.Fatal("non-STARTUP mode bypassed the full-bandwidth recovery guard")
	}
	afterModel := NewTUICBBRSender(1200)
	afterModel.fullBandwidth = true
	afterModel.mode = tuicBbrProbeBW
	newMixedEvent(afterModel)
	if !afterModel.InRecovery() {
		t.Fatal("zero-byte loss entry was ignored despite a non-empty loss batch")
	}
	if got := afterModel.Telemetry(); got.PacketsLost != 1 || got.BytesLost != 0 {
		t.Fatalf("zero-byte loss telemetry mismatch: %+v", got)
	}
}

func TestTUICMixedEventUsesNewestPacketSendState(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.SetRTTStatsProvider(&fakeRTT{smoothed: 200 * time.Millisecond})
	start := monotime.Now()
	sendTUICPacket(sender, start, 0, 0, 1200)
	sender.estimator.markAppLimited()
	sendTUICPacket(sender, start.Add(time.Millisecond), 1200, 1, 1200)
	sender.OnCongestionEventEx(2400, start.Add(200*time.Millisecond),
		[]quiccongestion.AckedPacketInfo{{PacketNumber: 0, BytesAcked: 1200}},
		[]quiccongestion.LostPacketInfo{{PacketNumber: 1, BytesLost: 1200}})
	if !sender.lastSampleAppLimited {
		t.Fatal("newer lost packet did not provide the event's app-limited state")
	}
	if sender.roundsNoGain != 0 {
		t.Fatalf("app-limited mixed event advanced STARTUP no-gain rounds: %d", sender.roundsNoGain)
	}
}

func TestTUICStartupExitsOnlyAfterBoundedLossEvidence(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.SetRTTStatsProvider(&fakeRTT{smoothed: 200 * time.Millisecond})
	sender.bwAtLastRound = 10 * 1024 * 1024
	start := monotime.Now()
	for i := 0; i < 10; i++ {
		sendTUICPacket(sender, start.Add(time.Duration(i)*time.Millisecond), quiccongestion.ByteCount(i*1200), quiccongestion.PacketNumber(i), 1200)
	}
	for i := 0; i < tuicStartupLossEvents; i++ {
		sender.OnCongestionEventEx(quiccongestion.ByteCount((10-i)*1200), start.Add(time.Duration(100+i)*time.Millisecond), nil,
			[]quiccongestion.LostPacketInfo{{PacketNumber: quiccongestion.PacketNumber(i), BytesLost: 1200}})
		if sender.fullBandwidth {
			t.Fatalf("STARTUP exited before an ACK round at loss event %d", i)
		}
	}
	sender.OnCongestionEventEx(2400, start.Add(200*time.Millisecond),
		[]quiccongestion.AckedPacketInfo{{PacketNumber: 9, BytesAcked: 1200}}, nil)
	if !sender.fullBandwidth {
		t.Fatal("bounded repeated-loss evidence did not exit STARTUP")
	}
}

func TestTUICLossRecoveryPreservesRateModelAtQuarterLoss(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.SetRTTStatsProvider(&fakeRTT{smoothed: 200 * time.Millisecond})
	start := monotime.Now()
	var pn quiccongestion.PacketNumber
	for round := 0; round < 12; round++ {
		flightStart := start.Add(time.Duration(round) * 200 * time.Millisecond)
		var inFlight quiccongestion.ByteCount
		acked := make([]quiccongestion.AckedPacketInfo, 0, 24)
		lost := make([]quiccongestion.LostPacketInfo, 0, 8)
		for i := 0; i < 32; i++ {
			sent := flightStart.Add(time.Duration(i) * time.Millisecond)
			sendTUICPacket(sender, sent, inFlight, pn, 1200)
			inFlight += 1200
			if i%4 == 0 {
				lost = append(lost, quiccongestion.LostPacketInfo{PacketNumber: pn, BytesLost: 1200})
			} else {
				acked = append(acked, quiccongestion.AckedPacketInfo{PacketNumber: pn, BytesAcked: 1200})
			}
			pn++
		}
		sender.OnCongestionEventEx(inFlight, flightStart.Add(200*time.Millisecond), acked, lost)
	}
	if got := sender.estimator.estimate(); got < 100*1024 {
		t.Fatalf("quarter-loss recovery collapsed the delivery model: %d B/s", got)
	}
	if got := sender.GetCongestionWindow(); got <= sender.minCwnd {
		t.Fatalf("quarter-loss recovery collapsed cwnd to floor: %d", got)
	}
}

func TestTUICRecoveryWindowUsesPostEventFlight(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.SetRTTStatsProvider(&fakeRTT{smoothed: 200 * time.Millisecond})
	sender.fullBandwidth = true
	sender.mode = tuicBbrProbeBW
	sender.recovery = tuicConservation
	start := monotime.Now()
	prior := quiccongestion.ByteCount(32 * 1200)
	acked := make([]quiccongestion.AckedPacketInfo, 0, 24)
	lost := make([]quiccongestion.LostPacketInfo, 0, 8)
	for i := 0; i < 32; i++ {
		pn := quiccongestion.PacketNumber(i)
		sendTUICPacket(sender, start.Add(time.Duration(i)*time.Millisecond), quiccongestion.ByteCount(i*1200), pn, 1200)
		if i%4 == 0 {
			lost = append(lost, quiccongestion.LostPacketInfo{PacketNumber: pn, BytesLost: 1200})
		} else {
			acked = append(acked, quiccongestion.AckedPacketInfo{PacketNumber: pn, BytesAcked: 1200})
		}
	}
	sender.OnCongestionEventEx(prior, start.Add(200*time.Millisecond), acked, lost)
	want := prior - quiccongestion.ByteCount(len(lost))*1200
	if sender.recoveryWindow != want {
		t.Fatalf("recovery window=%d, want post-event flight plus ACKs = %d", sender.recoveryWindow, want)
	}
}

func TestTUICRateArithmeticSaturates(t *testing.T) {
	if got := rateFromDelta(^uint64(0), time.Nanosecond); got != ^uint64(0) {
		t.Fatalf("rate arithmetic wrapped: %d", got)
	}
	if got := saturatingByteAdd(maxCongestionByteCount-1, 2); got != maxCongestionByteCount {
		t.Fatalf("byte addition wrapped: %d", got)
	}
}

func TestTUICRecoverySaturatesOversizedLoss(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.recovery = tuicConservation
	sender.recoveryWindow = sender.initialCwnd
	sender.calculateRecoveryWindow(0, ^uint64(0), sender.initialCwnd)
	if sender.recoveryWindow < sender.minCwnd || sender.recoveryWindow > sender.initialCwnd {
		t.Fatalf("oversized loss corrupted recovery window: %d", sender.recoveryWindow)
	}
}

func TestTUICBBRSenderStartupAndRecovery(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.SetRTTStatsProvider(&fakeRTT{smoothed: 200 * time.Millisecond})
	if sender.initialCwnd != tuicInitialPackets*1200 {
		t.Fatalf("unexpected TUIC initial window: %d", sender.initialCwnd)
	}
	if sender.cwndGain != tuicCwndGain {
		t.Fatalf("unexpected TUIC startup cwnd gain: %v", sender.cwndGain)
	}
	if got, want := sender.bandwidth(), quiccongestion.ByteCount(float64(sender.initialCwnd)*tuicHighGain/0.2); got != want {
		// TUIC startup pacing is high_gain*IW/RTT. The high gain is applied
		// exactly once; the startup cwnd gain remains 2.0.
		t.Fatalf("startup pacing=%d, want high_gain*IW/RTT=%d", got, want)
	}
	start := monotime.Now()
	var pn quiccongestion.PacketNumber
	for round := 0; round < 8; round++ {
		var inFlight quiccongestion.ByteCount
		for i := 0; i < 32; i++ {
			sent := start.Add(time.Duration(round)*200*time.Millisecond + time.Duration(i)*time.Millisecond)
			sendTUICPacket(sender, sent, inFlight, pn, 1200)
			inFlight += 1200
			pn++
		}
		sender.OnCongestionEventEx(inFlight, start.Add(time.Duration(round+1)*200*time.Millisecond), []quiccongestion.AckedPacketInfo{{PacketNumber: pn - 1, BytesAcked: 32 * 1200}}, nil)
	}
	if sender.estimator.estimate() == 0 {
		t.Fatal("TUIC-aligned estimator did not record bandwidth")
	}
	if sender.bandwidth() < quiccongestion.ByteCount(tuicDefaultMinRate) {
		t.Fatalf("pacing rate below safety floor: %d", sender.bandwidth())
	}
	// The synthetic sender above emits only half of its grown congestion
	// window, so TUIC correctly classifies later rounds as application-limited.
	// Establish a completed model explicitly before testing recovery behavior.
	sender.fullBandwidth = true
	sender.mode = tuicBbrProbeBW
	before := sender.GetCongestionWindow()
	sendTUICPacket(sender, start.Add(3*time.Second), 0, pn, 1200)
	sendTUICPacket(sender, start.Add(3*time.Second+time.Millisecond), 1200, pn+1, 1200)
	sender.OnCongestionEventEx(2400, start.Add(3200*time.Millisecond), []quiccongestion.AckedPacketInfo{{PacketNumber: pn, BytesAcked: 1200}}, []quiccongestion.LostPacketInfo{{PacketNumber: pn + 1, BytesLost: 1200}})
	if !sender.InRecovery() || sender.GetCongestionWindow() > before {
		t.Fatalf("loss did not bound recovery: recovery=%v cwnd=%d before=%d", sender.InRecovery(), sender.GetCongestionWindow(), before)
	}
}

func TestTUICBBRTimeoutPreservesDeliveryModel(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.fullBandwidth = true
	sender.mode = tuicBbrProbeBW
	sender.pacingRate = 10 * 1024 * 1024
	sender.cwnd = 2 * 1024 * 1024
	sender.OnRetransmissionTimeout(true)
	if sender.mode != tuicBbrProbeBW || !sender.fullBandwidth || sender.pacingRate != 10*1024*1024 {
		t.Fatalf("PTO destroyed controller model: mode=%v full=%v rate=%d", sender.mode, sender.fullBandwidth, sender.pacingRate)
	}
	if sender.GetCongestionWindow() != 2*1024*1024 {
		t.Fatalf("PTO window=%d, want preserved model", sender.GetCongestionWindow())
	}
}

func TestTUICDatagramResizePreservesPacketSizedWindows(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.cwnd = sender.initialCwnd
	sender.recoveryWindow = 64 * 1200
	sender.SetMaxDatagramSize(1400)
	if sender.initialCwnd != 32*1400 || sender.cwnd != sender.initialCwnd {
		t.Fatalf("initial window resize mismatch: initial=%d cwnd=%d", sender.initialCwnd, sender.cwnd)
	}
	if sender.minCwnd != 4*1400 || sender.recoveryWindow != 64*1200 {
		t.Fatalf("window resize mismatch: min=%d recovery=%d", sender.minCwnd, sender.recoveryWindow)
	}
}

func TestTUICTelemetryReportsControllerLoss(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.OnCongestionEventEx(2400, monotime.Now(), nil, []quiccongestion.LostPacketInfo{
		{PacketNumber: 1, BytesLost: 1200}, {PacketNumber: 2, BytesLost: 1200},
	})
	got := sender.Telemetry()
	if got.BytesLost != 2400 || got.PacketsLost != 2 {
		t.Fatalf("loss telemetry=%d bytes/%d packets, want 2400/2", got.BytesLost, got.PacketsLost)
	}
}

func TestTUICTelemetryReportsSamplerDiagnostics(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.SetRTTStatsProvider(&fakeRTT{smoothed: 100 * time.Millisecond})
	start := monotime.Now()
	sendTUICPacket(sender, start, 0, 0, 1200)
	sender.OnCongestionEventEx(1200, start.Add(100*time.Millisecond), []quiccongestion.AckedPacketInfo{{PacketNumber: 0, BytesAcked: 1200}}, nil)
	got := sender.Telemetry()
	if got.LatestSample == 0 || got.LatestAckRate == 0 || got.Samples == 0 || got.NonAppSamples == 0 || got.Round != 1 {
		t.Fatalf("incomplete sampler telemetry: %+v", got)
	}
	if got.AppSamples != 0 || got.StateMisses != 0 {
		t.Fatalf("unexpected sampler diagnostics: %+v", got)
	}
}

func TestTUICStartupLossDoesNotCollapseBeforeBandwidthModel(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.SetRTTStatsProvider(&fakeRTT{smoothed: 200 * time.Millisecond})
	start := monotime.Now()
	var pn quiccongestion.PacketNumber
	acked := make([]quiccongestion.AckedPacketInfo, 0, 5)
	lost := make([]quiccongestion.LostPacketInfo, 0, 195)
	for i := 0; i < 200; i++ {
		sendTUICPacket(sender, start.Add(time.Duration(i)*time.Millisecond), quiccongestion.ByteCount(i*1200), pn, 1200)
		if i%40 == 39 {
			acked = append(acked, quiccongestion.AckedPacketInfo{PacketNumber: pn, BytesAcked: 1200})
		} else {
			lost = append(lost, quiccongestion.LostPacketInfo{PacketNumber: pn, BytesLost: 1200})
		}
		pn++
	}
	sender.OnCongestionEventEx(200*1200, start.Add(200*time.Millisecond), acked, lost)
	if sender.fullBandwidth {
		t.Fatal("startup loss prematurely declared the bottleneck model complete")
	}
	if sender.InRecovery() {
		t.Fatal("startup loss entered recovery before a delivery model existed")
	}
	if got := sender.GetCongestionWindow(); got <= sender.minCwnd {
		t.Fatalf("startup loss collapsed cwnd to safety floor: %d", got)
	}

	// Once the model is known, the same loss must still enter bounded
	// recovery; this guard prevents the startup exception from becoming an
	// unlimited loss-ignoring mode.
	sender.fullBandwidth = true
	sendTUICPacket(sender, start.Add(300*time.Millisecond), 0, pn, 1200)
	sendTUICPacket(sender, start.Add(301*time.Millisecond), 1200, pn+1, 1200)
	sender.OnCongestionEventEx(2400, start.Add(400*time.Millisecond), []quiccongestion.AckedPacketInfo{{PacketNumber: pn, BytesAcked: 1200}}, []quiccongestion.LostPacketInfo{{PacketNumber: pn + 1, BytesLost: 1200}})
	if !sender.InRecovery() {
		t.Fatal("loss after startup did not enter recovery")
	}
}

func TestTUICStartupDoesNotExitOnOnePostModelLoss(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.fullBandwidth = false
	sender.recovery = tuicConservation
	sender.roundsNoGain = 0
	sender.bwAtLastRound = 1
	sender.estimator.maxFilter.updateMax(1, monotime.Time(0), 1)
	sender.checkFullBandwidth(tuicSendState{valid: true})
	if sender.fullBandwidth {
		t.Fatal("one recovery event prematurely exited startup")
	}
}

func TestTUICProbeBWInitialOffsetSkipsDrain(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	for seed := uint64(1); seed <= 1024; seed++ {
		sender.randomState = seed
		if offset := sender.nextCycleOffset(); offset == 1 || offset >= uint8(len(tuicPacingGains)) {
			t.Fatalf("invalid initial ProbeBW offset %d for seed %d", offset, seed)
		}
	}
}

func TestTUICProbeBWLowGainDoesNotStickAboveTarget(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.SetRTTStatsProvider(&fakeRTT{smoothed: 200 * time.Millisecond})
	sender.mode = tuicBbrProbeBW
	sender.pacingGain = tuicPacingGains[1]
	sender.cycleOffset = 1
	sender.estimator.maxFilter.updateMax(1, monotime.Time(0), 1024*1024)
	start := monotime.Now()
	sender.lastCycle = start
	inFlight := sender.targetCwnd(1) + sender.maxDatagramSize
	sender.updateGainCycle(start.Add(201*time.Millisecond), inFlight, inFlight, false)
	if sender.pacingGain != 1 || sender.cycleOffset != 2 {
		t.Fatalf("low-gain cycle remained stuck: gain=%v offset=%d", sender.pacingGain, sender.cycleOffset)
	}
}

func TestTUICProbeRTTPreservesModelAndExitsAfterPriorRound(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.fullBandwidth = true
	sender.mode = tuicBbrProbeBW
	sender.cwnd = 512 * 1024
	sender.estimator.maxFilter.updateMax(1, monotime.Time(0), 2*1024*1024)
	start := monotime.Now()
	sender.maybeProbeRTT(start, false, 0, true)
	if sender.mode != tuicBbrProbeRTT || sender.GetCongestionWindow() != sender.minCwnd || !sender.estimator.appLimited {
		t.Fatalf("ProbeRTT entry mismatch: mode=%v window=%d app_limited=%v", sender.mode, sender.GetCongestionWindow(), sender.estimator.appLimited)
	}
	sender.calculateCwnd(64*1024, 0)
	if sender.cwnd != 512*1024 {
		t.Fatalf("ProbeRTT destroyed saved congestion window: %d", sender.cwnd)
	}
	// A round can pass before the 200-ms timer. Native TUIC remembers it and
	// exits as soon as the timer expires; it does not wait for another round.
	sender.maybeProbeRTT(start.Add(100*time.Millisecond), true, 0, false)
	sender.maybeProbeRTT(start.Add(201*time.Millisecond), false, 0, false)
	if sender.mode != tuicBbrProbeBW {
		t.Fatalf("ProbeRTT did not exit after timer and prior round: mode=%v", sender.mode)
	}
}

func TestTUICTargetWindowUsesStartupGainWithoutBandwidth(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	if got, want := sender.targetCwnd(2), 2*sender.initialCwnd; got != want {
		t.Fatalf("startup target=%d, want gain*IW=%d", got, want)
	}
}

func TestTUICStartupGrowthPreservesAckHeight(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.ackAgg.maxAckHeight.updateMax(1, monotime.Time(0), 24*1200)
	sender.estimator.maxFilter.updateMax(1, monotime.Time(0), 1024*1024)
	sender.checkFullBandwidth(tuicSendState{valid: true})
	if got := sender.ackAgg.maxAckHeight.get(); got != 24*1200 {
		t.Fatalf("startup bandwidth growth discarded ACK height: %d", got)
	}
}

// The application-limited rule is liberal outside DRAIN on purpose: any unused
// window counts. Tightening it to require a full burst measured better on the
// emulator and cost more than half the throughput on the real China-US path,
// where delivery-rate samples are noisy-low and this marking is what keeps them
// out of the bandwidth filter. See appLimited's comment for the numbers.
func TestTUICAppLimitedCountsAnyUnusedWindowOutsideDrain(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.cwnd = 64 * sender.maxDatagramSize
	window := sender.GetCongestionWindow()
	if sender.appLimited(window) {
		t.Fatal("a full congestion window was classified as application-limited")
	}
	if !sender.appLimited(window - sender.maxDatagramSize) {
		t.Fatal("one packet of unused window was not classified as application-limited")
	}
	// DRAIN is the exception: there, being below the window is the point.
	sender.mode = tuicBbrDrain
	if sender.appLimited(window - sender.maxDatagramSize) {
		t.Fatal("small headroom in DRAIN was classified as application-limited")
	}
	if !sender.appLimited(window - 11*sender.maxDatagramSize) {
		t.Fatal("large DRAIN headroom was not classified as application-limited")
	}
}

// A seed is another lane's measurement. It may raise this sender's bandwidth
// estimate, which is a windowed maximum and expires on its own, and it must
// never touch min_rtt, which is a floor that only moves down and which
// seedBandwidth has no way to stamp for expiry.
//
// Live, a 4 ms round trip seeded onto a 200 ms path sized BBR's target window
// fifty times too small and held the connection near 1 Mbit/s for the rest of
// the process's life -- every connection made afterwards inherited it through
// the shared path model. See
// docs/archive/2026-08-development/MEASUREMENTS-20260816.md.
func TestSeedBandwidthNeverAdoptsAForeignRoundTrip(t *testing.T) {
	b := NewTUICBBRSender(1200)
	measured := 200 * time.Millisecond
	b.refreshRTTSample(monotime.Now(), measured)

	b.seedBandwidth(12_000_000, 4*time.Millisecond)

	if got := b.minRoundTrip(); got != measured {
		t.Fatalf("min_rtt is %v after a 4ms seed, want the measured %v", got, measured)
	}
	// The seed is still useful: it raises the estimate the pacer works from.
	if b.estimator.maxFilter.get() < 12_000_000 {
		t.Fatalf("bandwidth estimate %d, want the seeded 12000000", b.estimator.maxFilter.get())
	}
}

// A sender with no measurement of its own must not have one invented for it
// either: it should still be measuring, not holding a number a sibling passed.
func TestSeedBandwidthLeavesAnUnmeasuredRoundTripUnset(t *testing.T) {
	b := NewTUICBBRSender(1200)
	b.seedBandwidth(12_000_000, 4*time.Millisecond)
	if got := b.minRoundTrip(); got != 0 {
		t.Fatalf("min_rtt is %v from a seed alone, want 0 so the sender measures it", got)
	}
}

// pruneStates drops the oldest quarter when the table fills. It ran on the
// send path and rescanned the whole map once per entry removed -- about 17
// million map iterations for one call at the 8192-entry bound, which at
// 200 Mbit/s recurs roughly every 0.4 s.
func TestPruneStatesDropsTheOldestQuarter(t *testing.T) {
	e := newTUICBandwidthEstimator()
	now := monotime.Now()
	for i := 0; i < tuicMaxSendStates; i++ {
		e.packetStates[quiccongestion.PacketNumber(i)] = tuicPacketState{
			sentTime: now.Add(time.Duration(i) * time.Microsecond),
		}
	}
	e.pruneStates()

	removed := tuicMaxSendStates / 4
	if len(e.packetStates) != tuicMaxSendStates-removed {
		t.Fatalf("table holds %d after prune, want %d", len(e.packetStates), tuicMaxSendStates-removed)
	}
	// Packet numbers are assigned in send order, so the oldest are the lowest.
	for i := 0; i < removed; i++ {
		if _, ok := e.packetStates[quiccongestion.PacketNumber(i)]; ok {
			t.Fatalf("packet %d survived the prune, want the oldest quarter gone", i)
		}
	}
	for i := removed; i < tuicMaxSendStates; i++ {
		if _, ok := e.packetStates[quiccongestion.PacketNumber(i)]; !ok {
			t.Fatalf("packet %d was pruned, want the newest three quarters kept", i)
		}
	}
}

// A prune must stay cheap enough to sit on the send path.
func BenchmarkPruneStates(b *testing.B) {
	now := monotime.Now()
	for b.Loop() {
		b.StopTimer()
		e := newTUICBandwidthEstimator()
		for i := 0; i < tuicMaxSendStates; i++ {
			e.packetStates[quiccongestion.PacketNumber(i)] = tuicPacketState{
				sentTime: now.Add(time.Duration(i) * time.Microsecond),
			}
		}
		b.StartTimer()
		e.pruneStates()
	}
}
