package congestion

import (
	"math/rand"
	"testing"
	"time"

	"github.com/apernet/quic-go/monotime"

	quiccongestion "github.com/apernet/quic-go/congestion"

	"github.com/bojieli/queqiao/internal/pathmodel"
)

func losses(n int) []quiccongestion.LostPacketInfo {
	out := make([]quiccongestion.LostPacketInfo, n)
	for i := range out {
		out[i] = quiccongestion.LostPacketInfo{PacketNumber: quiccongestion.PacketNumber(i), BytesLost: 1200}
	}
	return out
}

func TestExplicitCongestionOutcomesDoNotInferAmbiguousPacketGaps(t *testing.T) {
	e := NewErasureSender(1200)
	acked := []quiccongestion.AckedPacketInfo{
		{PacketNumber: 1000, BytesAcked: 1200},
		{PacketNumber: 0, BytesAcked: 1200},
	}
	lost := []quiccongestion.LostPacketInfo{{PacketNumber: 500, BytesLost: 1200}}
	e.OnCongestionEventEx(0, monotime.Now(), acked, lost)
	snapshot := e.estimator.Snapshot()
	if snapshot.Decided != 3 {
		t.Fatalf("three explicit outcomes decided %d packet fates", snapshot.Decided)
	}
	if snapshot.Loss < 0.32 || snapshot.Loss > 0.34 {
		t.Fatalf("one explicit loss in three outcomes measured %.3f", snapshot.Loss)
	}
}

// A first flight can overrun a clean path's queue before the controller has
// found its bottleneck. Those losses arrive in runs: they are evidence of
// congestion, not evidence that the channel erases packets independently of
// rate. Trusting the partial-round minimum here creates positive feedback --
// the controller compensates for its own queue drops and sends still faster.
func TestClusteredStartupLossDoesNotBecomeAnErasureFloor(t *testing.T) {
	e := NewErasureSender(1200)
	var acked []quiccongestion.AckedPacketInfo
	var lost []quiccongestion.LostPacketInfo
	for pn := 0; pn < 1000; pn++ {
		if pn%100 < 50 {
			acked = append(acked, quiccongestion.AckedPacketInfo{
				PacketNumber: quiccongestion.PacketNumber(pn), BytesAcked: 1200,
			})
		} else {
			lost = append(lost, quiccongestion.LostPacketInfo{
				PacketNumber: quiccongestion.PacketNumber(pn), BytesLost: 1200,
			})
		}
	}
	e.OnCongestionEventEx(0, monotime.Now(), acked, lost)

	if snapshot := e.estimator.Snapshot(); snapshot.Floor < 0.4 || snapshot.Memoryless {
		t.Fatalf("test pattern is not an untrusted clustered floor: %+v", snapshot)
	}
	if got := e.arrivalRate(); got < 0.97 {
		t.Fatalf("clustered startup loss produced arrival rate %.3f, want no material compensation", got)
	}
}

// Compensation is a bet that sending more delivers more, and it is now taken
// one step at a time with each step tested against the delivered rate.
//
// Where the bet pays -- a channel that erases independently of the sending
// rate -- it must still get there, or pacing a delivered-rate estimate makes
// the sending rate its own input and the loop walks down to nothing.
func TestCompensationGrowsWhileItBuysDelivery(t *testing.T) {
	e := NewErasureSender(1200)
	e.inner.minRTT = 200 * time.Millisecond
	e.SetRTTStatsProvider(&fixedRTT{min: 200 * time.Millisecond, smoothed: 200 * time.Millisecond})

	// Delivery improves every round, which is what compensating for genuine
	// erasure looks like.
	delivered := uint64(100_000)
	for round := uint64(1); round <= 12; round++ {
		e.inner.round = round
		delivered += 20_000
		e.inner.estimator.maxFilter.updateMax(round, monotime.Now(), delivered)
		e.compensationFor(0.58)
	}
	if got := e.appliedArrival; got > 0.62 || got < 0.55 {
		t.Fatalf("applied arrival %.3f after twelve rounds of improving delivery, want about 0.58", got)
	}
}

// Where the bet does not pay -- a policer, which drops because of the sending
// rate rather than independently of it -- compensation must stay where it is.
// Sending harder there raises the loss that asks for more compensation, which
// is a loop that ends at many times the path's capacity.
func TestCompensationHoldsWhenItBuysNothing(t *testing.T) {
	e := NewErasureSender(1200)
	e.inner.minRTT = 200 * time.Millisecond
	e.SetRTTStatsProvider(&fixedRTT{min: 200 * time.Millisecond, smoothed: 200 * time.Millisecond})

	// Delivery is flat however hard the sender is asked to try.
	e.inner.estimator.maxFilter.updateMax(1, monotime.Now(), 250_000)
	for round := uint64(1); round <= 12; round++ {
		e.inner.round = round
		e.compensationFor(0.28)
	}
	if got := e.appliedArrival; got < 0.85 {
		t.Fatalf("applied arrival fell to %.3f on a path whose delivery never improved; "+
			"that is the policer feedback loop", got)
	}
}

// Before a round trip has been measured the brake cannot act, so compensation
// must not either. The sender is then plain BBR that ignores loss.
func TestCompensationWaitsForTheBrake(t *testing.T) {
	e := NewErasureSender(1200)
	rng := rand.New(rand.NewSource(3))
	number := quiccongestion.PacketNumber(0)
	for round := 0; round < 20; round++ {
		var acked []quiccongestion.AckedPacketInfo
		var lost []quiccongestion.LostPacketInfo
		for i := 0; i < 500; i++ {
			if rng.Float64() < 0.42 {
				lost = append(lost, quiccongestion.LostPacketInfo{PacketNumber: number, BytesLost: 1200})
			} else {
				acked = append(acked, quiccongestion.AckedPacketInfo{PacketNumber: number, BytesAcked: 1200})
			}
			number++
		}
		e.OnCongestionEventEx(0, monotime.Now(), acked, lost)
	}
	if got := e.arrivalRate(); got < 0.99 {
		t.Fatalf("compensated at %.3f with no measured round trip, so nothing could have "+
			"bounded it", got)
	}
}

// The compensation is the other half of the design: BBR estimates the rate
// that arrives while its pacer governs the rate that is sent, and on an
// erasure channel those differ by the arrival rate. Without the correction the
// sending rate becomes its own input and walks down to nothing.
func TestThePacingRateIsCompensatedForErasure(t *testing.T) {
	e := NewErasureSender(1200)
	plain := e.inner.bandwidth()

	e.arrival.Store(uint64(0.58 * partsPerMillion))
	compensated := e.bandwidth()
	if want := float64(plain) / 0.58; float64(compensated) < want*0.95 || float64(compensated) > want*1.05 {
		t.Fatalf("compensated bandwidth %d against a delivered estimate of %d at 58%% arrival, want about %.0f",
			compensated, plain, want)
	}

	// A clean path must be left alone.
	e.arrival.Store(partsPerMillion)
	if got := e.bandwidth(); got != plain {
		t.Fatalf("bandwidth %d on a lossless path, want the uncorrected %d", got, plain)
	}
}

// The divisor is bounded. An arrival rate near zero would turn a measurement
// error into an unbounded send rate, which is the one failure mode worse than
// giving up the path.
func TestTheCompensationIsBounded(t *testing.T) {
	e := NewErasureSender(1200)
	e.arrival.Store(uint64(0.001 * partsPerMillion))
	if got := e.arrivalRate(); got != erasureMinArrival {
		t.Fatalf("arrival rate %v at a measured 0.001, want the floor of %v", got, erasureMinArrival)
	}
	plain := e.inner.bandwidth()
	if got := e.bandwidth(); float64(got) > float64(plain)/erasureMinArrival*1.01 {
		t.Fatalf("bandwidth %d exceeds the bounded compensation of %d", got, plain)
	}
}

// The congestion window is compensated for the same reason the rate is: it
// bounds what is on the wire, and on an erasure channel that is more than what
// will arrive.
func TestTheCongestionWindowIsCompensated(t *testing.T) {
	e := NewErasureSender(1200)
	e.arrival.Store(uint64(0.58 * partsPerMillion))
	inner := e.inner.GetCongestionWindow()
	outer := e.GetCongestionWindow()
	if want := float64(inner) / 0.58; float64(outer) < want*0.95 || float64(outer) > want*1.05 {
		t.Fatalf("compensated window %d against an inner %d, want about %.0f", outer, inner, want)
	}
	if !e.CanSend(inner) {
		t.Fatal("a sender at the inner window's limit should still have room on an erasure channel")
	}
	if e.CanSend(outer) {
		t.Fatal("a sender at the compensated window's limit should be blocked")
	}
}

// A controller joining a path something else has already measured must start
// from what is known rather than at the initial window. On a channel that
// erases 40% of packets the ramp is the expensive part, and a lane opened to
// replace one that died would otherwise repeat it on a path nothing has
// forgotten.
func TestAJoiningSenderStartsFromWhatIsAlreadyKnown(t *testing.T) {
	model := pathmodel.NewPathModel()
	const perMember = 2e6
	model.Report(1, pathmodel.Observation{Erasure: 0.42, BurstFactor: 1, ObservedSamples: 5000, Delivered: perMember, RoundTrip: 0})
	model.Report(2, pathmodel.Observation{Erasure: 0.42, BurstFactor: 1, ObservedSamples: 5000, Delivered: perMember, RoundTrip: 0})

	seeded := NewErasureSenderOn(1200, model)
	if seeded.Share() <= 0 {
		t.Fatal("a sender joining a measured path was given no share")
	}
	fresh := NewErasureSender(1200)
	if seeded.bandwidth() <= fresh.bandwidth() {
		t.Fatalf("seeded sender starts at %d, no better than an unseeded %d",
			seeded.bandwidth(), fresh.bandwidth())
	}
}

// And the window has to be seeded too, not only the rate.
//
// BBR will not send beyond its congestion window however fast it is paced, so
// a sender that knows the path's rate and starts at the initial window spends
// its ramp doubling that window with the pacer idle behind it. Traced live,
// that was 37 KB against a 60 Mbit/s pacing rate, and eight round trips of
// doubling on a path already measured at 15 Mbit/s -- about two seconds of a
// ten-second transfer, paid again by every flow.
func TestAJoiningSenderStartsWithTheWindowItsRateImplies(t *testing.T) {
	const rate, roundTrip = 2e6, 250 * time.Millisecond
	model := pathmodel.NewPathModel()
	model.Report(1, pathmodel.Observation{Erasure: 0.42, BurstFactor: 1, ObservedSamples: 5000, Delivered: rate, RoundTrip: roundTrip})

	seeded := NewErasureSenderOn(1200, model)
	fresh := NewErasureSender(1200)
	if seeded.GetCongestionWindow() <= fresh.GetCongestionWindow() {
		t.Fatalf("a sender joining a path measured at %.0f bytes/s and %v starts "+
			"with a %d-byte window, no better than an unseeded %d",
			rate, roundTrip, seeded.GetCongestionWindow(), fresh.GetCongestionWindow())
	}
	// The window it should hold is a round trip of what it will put on the
	// wire, which on an erasing path is more than what arrives.
	want := quiccongestion.ByteCount(rate / (1 - 0.42) * roundTrip.Seconds())
	if got := seeded.GetCongestionWindow(); got < want/2 || got > want*2 {
		t.Errorf("window %d against a bandwidth-delay product of %d", got, want)
	}

	// Without a measured round trip there is no window to compute, and the
	// sender must still start from the rate rather than refusing to start.
	blind := NewErasureSenderOn(1200, func() *pathmodel.PathModel {
		m := pathmodel.NewPathModel()
		m.Report(1, pathmodel.Observation{Erasure: 0.42, BurstFactor: 1, ObservedSamples: 5000, Delivered: rate, RoundTrip: 0})
		return m
	}())
	if blind.bandwidth() <= NewErasureSender(1200).bandwidth() {
		t.Error("a sender given a rate but no round trip did not use the rate")
	}
}

// A connection whose pipe has emptied must not have to rediscover the path.
//
// The bandwidth filter holds ten rounds, so a connection that spends a while
// carrying small exchanges keeps only what those exchanges delivered. When a
// download then arrives on it, probing climbs a quarter per cycle from there:
// measured live, an estimate that had decayed to 0.4 Mbit/s took nineteen
// seconds to find the 12 Mbit/s the path had all along, on a connection that
// was pooled precisely so that using it again would be cheap.
func TestAnEmptiedPipeKeepsWhatItMeasured(t *testing.T) {
	sender := NewTUICBBRSender(1200)
	sender.minRTT = 250 * time.Millisecond
	const peak = 2 << 20

	// What the connection once measured, and then forgot as its filter aged
	// out over rounds of carrying almost nothing.
	sender.seedBandwidth(peak, sender.minRTT)
	sender.peakBandwidth = peak
	sender.estimator.maxFilter.reset()
	sender.estimator.maxFilter.updateMax(sender.round, monotime.Time(0), peak/32)
	if before := sender.estimator.estimate(); before >= peak {
		t.Fatalf("the filter still holds %d; this test is not testing decay", before)
	}

	// Work arrives on an empty pipe.
	sendTUICPacket(sender, monotime.Now(), 0, 1, 1200)

	if got := sender.estimator.estimate(); got < peak {
		t.Errorf("a connection that had measured %d bytes/s restarted from %d, "+
			"and will spend cycles climbing back to what it already knew", peak, got)
	}
}

// Every loss now reaches the controller, so what this sender saw and what the
// controller was charged must be the same number.
//
// They are derived independently -- one from this sender's own counter, one
// from the controller's telemetry -- so the agreement is a check rather than a
// tautology. While loss was classified they differed by most of the loss, and
// publishing only the controller's figure let a gateway erasing a fifth of its
// downstream report single-digit loss.
func TestEveryLossReachesTheController(t *testing.T) {
	e := NewErasureSender(1200)

	const erasure = 0.2
	rng := rand.New(rand.NewSource(7))
	number := quiccongestion.PacketNumber(0)
	observedLost := 0
	for round := 0; round < 40; round++ {
		var acked []quiccongestion.AckedPacketInfo
		var lost []quiccongestion.LostPacketInfo
		for i := 0; i < 500; i++ {
			if rng.Float64() < erasure {
				lost = append(lost, quiccongestion.LostPacketInfo{PacketNumber: number, BytesLost: 1200})
				observedLost++
			} else {
				acked = append(acked, quiccongestion.AckedPacketInfo{PacketNumber: number, BytesAcked: 1200})
			}
			number++
		}
		e.OnCongestionEventEx(0, monotime.Now(), acked, lost)
	}

	telemetry := e.Telemetry()
	_, passed := e.Channel()
	t.Logf("observed=%d charged=%d (channel lost %d of %d)",
		telemetry.PacketsLostObserved, telemetry.PacketsLost, observedLost, number)

	if telemetry.PacketsLostObserved != uint64(observedLost) {
		t.Fatalf("observed %d losses, the channel produced %d", telemetry.PacketsLostObserved, observedLost)
	}
	if telemetry.PacketsLostObserved != telemetry.PacketsLost {
		t.Fatalf("this sender saw %d losses and the controller was charged %d; nothing should be "+
			"withheld any more", telemetry.PacketsLostObserved, telemetry.PacketsLost)
	}
	if passed != uint64(observedLost) {
		t.Fatalf("the sender's own counter says %d against a channel that lost %d", passed, observedLost)
	}
}

// Charging the controller for every loss must not put it into recovery on an
// erasure path. That is the collapse this controller exists to avoid, and it is
// the reason loss used to be classified before being forwarded.
func TestErasureDoesNotDriveTheControllerIntoRecovery(t *testing.T) {
	e := NewErasureSender(1200)
	rng := rand.New(rand.NewSource(11))
	number := quiccongestion.PacketNumber(0)
	for round := 0; round < 30; round++ {
		var acked []quiccongestion.AckedPacketInfo
		var lost []quiccongestion.LostPacketInfo
		for i := 0; i < 400; i++ {
			if rng.Float64() < 0.42 {
				lost = append(lost, quiccongestion.LostPacketInfo{PacketNumber: number, BytesLost: 1200})
			} else {
				acked = append(acked, quiccongestion.AckedPacketInfo{PacketNumber: number, BytesAcked: 1200})
			}
			number++
		}
		e.OnCongestionEventEx(0, monotime.Now(), acked, lost)
	}
	if e.InRecovery() {
		t.Fatal("a 42% erasure channel put the controller into recovery; loss is being read as congestion")
	}
}

// A controller that classifies nothing must still answer the same question, or
// a dashboard cannot read one metric across the kinds this build ships.
func TestControllersThatDoNotClassifyReportObservedEqualToCharged(t *testing.T) {
	for name, sender := range map[string]interface {
		OnCongestionEventEx(quiccongestion.ByteCount, monotime.Time, []quiccongestion.AckedPacketInfo, []quiccongestion.LostPacketInfo)
		Telemetry() ControllerTelemetry
	}{
		"bbr-tuic": NewTUICBBRSender(1200),
		"brutal":   NewBrutalSender(1_000_000, false),
	} {
		t.Run(name, func(t *testing.T) {
			sender.OnCongestionEventEx(12_000, monotime.Now(), nil, losses(6))
			got := sender.Telemetry()
			if got.PacketsLostObserved != got.PacketsLost {
				t.Fatalf("observed %d against charged %d for a controller that classifies nothing",
					got.PacketsLostObserved, got.PacketsLost)
			}
		})
	}
}

// The code is sized from the measured erasure and the pacer from the floor, and
// the two are different numbers about the same channel. A trace that carries
// only the floor cannot explain a code rate, which is what made the live
// incident unreadable: the floor read 1.76% while the channel erased 19.9%.
func TestTheSenderPublishesTheMeasurementItsCodeIsSizedFrom(t *testing.T) {
	model := pathmodel.NewPathModel()
	// A model whose floor and measurement disagree the way the live one did.
	model.Report(2, pathmodel.Observation{
		Erasure: 0.199, BurstFactor: 1,
		ObservedSamples: 5000, Delivered: 2e6, RoundTrip: 200 * time.Millisecond,
	})
	e := NewErasureSenderOn(1200, model)

	// One congestion event is enough to make this sender a member and pull the
	// pooled state through.
	e.OnCongestionEventEx(0, monotime.Now(), []quiccongestion.AckedPacketInfo{
		{PacketNumber: 1, BytesAcked: 1200},
	}, nil)

	got := e.Telemetry()
	t.Logf("published erasure %.4f", got.Erasure)
	if got.Erasure < 0.1 {
		t.Fatalf("the sender published %.4f on a path measured at 0.199", got.Erasure)
	}

}

// characterized gives a sender the evidence the burst rule needs before it will
// read a clean channel as clean. The tests below state the estimator's
// conclusions directly rather than driving packets through it, so they have to
// state how much was behind them as well: a sender that has just started has
// measured nothing, and nothing is not a report of a clean path.
func characterized(e *ErasureSender) *ErasureSender {
	e.samples.Store(burstEvidenceSamples)
	return e
}

// The pacer used to meter every send at a bandwidth estimate that a
// request-shaped flow cannot raise, because such a flow is application-limited
// by construction. On the measured datacenter path that cost 67ms of a 355KB
// request, which was the whole of this transport's deficit against a tuned TCP
// client on the same link.
//
// The controller already knew there was nothing to protect: no queue beyond the
// path's own minimum, and no loss the estimator attributed to rate. These pin
// that the burst follows that evidence rather than a constant.
func TestNoCongestionEvidenceMeansNoMetering(t *testing.T) {
	e := characterized(senderAtRTT(t, 200*time.Millisecond, 202*time.Millisecond))
	got := e.unmeteredBurst()
	if got <= 0 {
		t.Fatal("a path holding almost no queue, with no loss attributed to rate, is " +
			"still being metered; the pacer is protecting a queue that is not forming")
	}
	if want := e.GetCongestionWindow(); got != want {
		t.Fatalf("unmetered burst is %d, want the congestion window %d: below the delay "+
			"bound, the window and the acknowledgement clock are what bound the send",
			got, want)
	}
}

// The delay bound permits a queue of one round trip. At it, the sender is doing
// the thing pacing exists to prevent, so metering has to come back.
func TestAQueueAtTheBoundRestoresMetering(t *testing.T) {
	e := characterized(senderAtRTT(t, 200*time.Millisecond, 400*time.Millisecond))
	if got := e.unmeteredBurst(); got != 0 {
		t.Fatalf("a path holding a full round trip of queue reported an unmetered burst "+
			"of %d; that is the bound this controller says must not be exceeded", got)
	}
}

// Loss that only appears when you push is the other half of the evidence, and
// separating it from the channel's own erasure is what this project is for.
// Erasure alone must not restore metering; congestive loss must.
func TestOnlyCongestiveLossRestoresMetering(t *testing.T) {
	e := characterized(senderAtRTT(t, 200*time.Millisecond, 201*time.Millisecond))
	if e.unmeteredBurst() <= 0 {
		t.Fatal("precondition: a quiet path should not be metered")
	}
	e.congestive.Store(uint64(0.02 * partsPerMillion))
	if got := e.unmeteredBurst(); got != 0 {
		t.Fatalf("with 2%% of loss attributed to rate the burst is still %d; that is the "+
			"one signal a sender can act on by slowing down", got)
	}
	e.congestive.Store(0)
	if e.unmeteredBurst() <= 0 {
		t.Fatal("metering did not lift once the rate-dependent loss went away")
	}
}

// Without round-trip measurements there is no delay signal, so there is no
// evidence of absence either and the constant has to stand.
func TestNoRoundTripMeasurementKeepsTheConstant(t *testing.T) {
	e := NewErasureSender(1200)
	if got := e.unmeteredBurst(); got != 0 {
		t.Fatalf("a sender with no round-trip measurement reported %d; it cannot know "+
			"whether a queue is forming, so it must not stop metering", got)
	}
}

// A policer is the path where bursting is worst and where both of the signals
// above read clean: it holds no queue, and its loss is sustained enough that
// the estimator's floor rises to meet it and reports nothing congestive.
// Gating on those two alone took an emulated policer from 3.0x overdrive to
// 4.0x and from 32.9% loss to 54.9%, because metering was the last thing
// holding the rate down. See internal/pep/case4_test.go.
func TestALossyDirectionIsStillMetered(t *testing.T) {
	e := characterized(senderAtRTT(t, 200*time.Millisecond, 201*time.Millisecond))
	if e.unmeteredBurst() <= 0 {
		t.Fatal("precondition: a clean quiet path should not be metered")
	}
	e.erasure.Store(uint64(0.33 * partsPerMillion))
	if got := e.unmeteredBurst(); got != 0 {
		t.Fatalf("a direction losing a third of what it sends reported an unmetered "+
			"burst of %d; on a policed path neither the delay bound nor the congestive "+
			"component can see the overload, so this is the only thing left", got)
	}
}

// The datacenter path's upload direction lost nothing at all, which is the case
// the burst exists for. A trace of loss must not close the gate, or the rule
// would never fire on a real link.
func TestAnAlmostCleanDirectionStillBursts(t *testing.T) {
	e := characterized(senderAtRTT(t, 200*time.Millisecond, 201*time.Millisecond))
	e.erasure.Store(uint64(0.001 * partsPerMillion))
	if e.unmeteredBurst() <= 0 {
		t.Fatal("a direction losing one packet in a thousand is being metered; the " +
			"measured datacenter upload lost 0 of 41,663 and this rule has to fire there")
	}
}

// The burst has to come out of what the path already holds, not be added to
// it. Every signal the two rules above consult reads clean for a saturating
// flow on an erasing path -- no queue past the minimum, no loss attributed to
// rate -- so without this the flow was handed a further bandwidth-delay
// product on top of a window that was already in flight. It drove that into
// the bottleneck, the delay brake read the queue that built, and the rate it
// clamped to was the rate the flow kept: on the emulated erasure path the
// erasure controller fell from 10.5 to 0.9 Mbit/s of a 14.5 Mbit/s capacity,
// and monotonically worse the larger the burst.
//
// TestTheErasureControllerReachesThePathOthersGiveAway is what caught it, and
// that test skips under -short, so it reached main through a green CI and was
// found by a release candidate. This one is here so the next such change fails
// in the normal suite instead.
func TestAFlowAlreadyUsingThePathIsStillMetered(t *testing.T) {
	const minRTT = 200 * time.Millisecond
	e := characterized(senderAtRTT(t, minRTT, minRTT+2*time.Millisecond))

	// The product is computed from what the path delivers rather than from
	// what this sender puts on the wire. The two differ by the erasure
	// compensation, and it is the delivered figure that says how much the path
	// holds; the compensated one says only that we send more to get it there.
	product := quiccongestion.ByteCount(float64(e.inner.bandwidth()) * minRTT.Seconds())
	if product <= 0 {
		t.Fatalf("no bandwidth-delay product to reason about: %d", product)
	}

	// An empty pipe is the case the burst exists for and must keep.
	e.TimeUntilSend(0)
	empty := e.unmeteredBurst()
	if empty <= 0 {
		t.Fatal("a flow with an empty pipe on an uncongested path is being metered; " +
			"that is the 355KB request this rule was written for")
	}

	// A flow already holding a product is doing the thing pacing exists to
	// bound, whatever the other two signals say about it.
	e.TimeUntilSend(product)
	if got := e.unmeteredBurst(); got != 0 {
		t.Errorf("a flow already holding one product in flight was granted a further "+
			"%d bytes unmetered; the burst has to be what the path holds, not an "+
			"addition to it", got)
	}

	// And between the two the allowance is what remains of the product, so it
	// falls as the pipe fills rather than switching off at one end of it. The
	// window is the other bound and binds first on an empty pipe, so leave
	// less than a window of the product to see the product doing the work.
	window := e.GetCongestionWindow()
	e.TimeUntilSend(product - window/2)
	partial := e.unmeteredBurst()
	if partial != window/2 {
		t.Errorf("with %d bytes of the product unused, the allowance is %d, want %d: "+
			"what is left of it", window/2, partial, window/2)
	}
	if partial >= empty {
		t.Errorf("a part-full pipe was granted %d, no less than the %d an empty one "+
			"gets", partial, empty)
	}
}

// Both gates read their own zero value as a clean channel, so a sender that has
// measured nothing looks exactly like a sender on a perfect path. It is not the
// same claim, and reading it as one granted a startup burst on a channel erasing
// 42%: by the time the erasure ceiling had a measurement to refuse with, the
// burst had built the queue that the delay brake then holds the rate down for.
// Closing this window was worth about a tenth of the erasure controller's rate
// on the emulated path, over and above the in-flight bound above.
func TestAChannelNothingHasMeasuredIsNotACleanChannel(t *testing.T) {
	e := senderAtRTT(t, 200*time.Millisecond, 202*time.Millisecond)
	e.TimeUntilSend(0)

	if got := e.unmeteredBurst(); got != 0 {
		t.Errorf("a sender that has decided no packets granted a burst of %d; nothing "+
			"has reported on this channel, and nothing is not a report of a clean one", got)
	}

	// The same sender, once there is evidence behind that reading.
	e.samples.Store(burstEvidenceSamples)
	if e.unmeteredBurst() <= 0 {
		t.Error("a measured clean path is being metered; the evidence gate has to open " +
			"once there is evidence, or the burst never fires on a real link")
	}
}
