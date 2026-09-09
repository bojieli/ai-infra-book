package congestion

import (
	"testing"
	"time"

	quiccongestion "github.com/apernet/quic-go/congestion"
	"github.com/apernet/quic-go/monotime"
)

// base is an arbitrary non-zero instant. The filter treats a zero time as "no
// wall clock supplied", so a test that wants the time behaviour must not start
// at zero.
func base() monotime.Time { return monotime.Time(int64(time.Hour)) }

// The defect this file exists for. The filter's clock was a packet-timed round
// number, which is the right clock only while rounds advance. On the live
// gateway 99.98% of samples were application limited and the round counter
// moved nine times an hour, so a ten-round memory was sixty-six minutes of wall
// time and one burst through a token bucket set the estimate for the rest of
// the hour: 519 Mbit/s held against a measured sustained 17.6.
func TestABurstDoesNotSetTheEstimateForAnHour(t *testing.T) {
	m := newTUICMinMax()
	m.setRoundTrip(226 * time.Millisecond)

	now := base()
	const burst, sustained = 64_000_000, 2_200_000
	m.updateMax(1, now, burst)
	if got := m.get(); got != burst {
		t.Fatalf("the burst was not recorded: %d", got)
	}

	// Rounds barely advance, exactly as they did on the live path: two rounds
	// over the next ten minutes, while sustained samples keep arriving.
	for elapsed := time.Second; elapsed <= 10*time.Minute; elapsed += time.Second {
		round := uint64(1)
		if elapsed > 5*time.Minute {
			round = 2
		}
		m.updateMax(round, now.Add(elapsed), sustained)
	}

	if got := m.get(); got != sustained {
		t.Fatalf("after ten minutes of sustained samples the estimate is %d, want %d; "+
			"the round clock alone would still be holding the burst", got, sustained)
	}
}

// The estimate has to come down inside its own window, not merely eventually.
func TestTheEstimateFallsWithinItsWindow(t *testing.T) {
	const rtt = 200 * time.Millisecond
	m := newTUICMinMax()
	m.setRoundTrip(rtt)
	window := m.timeWindow

	now := base()
	m.updateMax(1, now, 50_000_000)

	// One round advances, so the round clock cannot expire anything: the
	// ten-round window needs ten.
	held := m.get()
	m.updateMax(2, now.Add(window/2), 1_000_000)
	if m.get() != held {
		t.Fatalf("the estimate moved at half its window: %d, want it held at %d", m.get(), held)
	}
	m.updateMax(2, now.Add(window+time.Millisecond), 1_000_000)
	if got := m.get(); got != 1_000_000 {
		t.Fatalf("the estimate is %d one window after the peak, want it replaced by 1000000", got)
	}
}

// The trap in this change. Application-limited samples may not lower a live
// estimate -- a sender with nothing to send has learned nothing about what the
// path could have carried -- so expiring the estimate on a connection that is
// application limited essentially always could have left nothing able to
// replace it, and an estimate of zero collapses the connection.
func TestAnExpiredEstimateIsReplacedRatherThanEmptied(t *testing.T) {
	e := newTUICBandwidthEstimator()
	e.maxFilter.setRoundTrip(200 * time.Millisecond)
	now := base()

	e.maxFilter.updateMax(1, now, 50_000_000)
	if !e.maxFilter.stale(now.Add(e.maxFilter.timeWindow + time.Millisecond)) {
		t.Fatal("an estimate a window old does not report itself stale")
	}
	if e.maxFilter.stale(now.Add(e.maxFilter.timeWindow / 2)) {
		t.Fatal("an estimate half a window old reports itself stale")
	}

	// The sampler's guard must let an application-limited sample through once
	// the standing estimate has expired, and only then.
	appLimitedAdmitted := func(at monotime.Time, sample uint64) bool {
		return !(sample > e.maxFilter.get()) && e.maxFilter.stale(at)
	}
	if appLimitedAdmitted(now.Add(e.maxFilter.timeWindow/2), 1_000_000) {
		t.Fatal("a lower application-limited sample was admitted against a live estimate")
	}
	if !appLimitedAdmitted(now.Add(e.maxFilter.timeWindow+time.Millisecond), 1_000_000) {
		t.Fatal("a lower application-limited sample was refused against an expired estimate, " +
			"which is how the filter would keep a value it has already decided not to trust")
	}

	e.maxFilter.updateMax(1, now.Add(e.maxFilter.timeWindow+time.Millisecond), 1_000_000)
	if got := e.maxFilter.get(); got == 0 {
		t.Fatal("the estimate emptied instead of being replaced")
	} else if got != 1_000_000 {
		t.Fatalf("estimate = %d, want the replacing sample 1000000", got)
	}
}

// A shaped path does not have a bandwidth. It has a rate and a burst depth, and
// a short probe measures the drain while sustained load measures the rate. The
// filter must settle on the second.
//
// The end-to-end version of this needs a burst-depth knob in internal/pathsim,
// which does not have one: its RateBytesPerSec is a serialization rate with no
// bucket behind it. This holds the filter to the behaviour that matters.
func TestATokenBucketSettlesOnTheShapingRateNotTheDrain(t *testing.T) {
	const (
		rtt      = 200 * time.Millisecond
		drain    = 40_000_000
		shaped   = 2_000_000
		bucketMs = 300
	)
	m := newTUICMinMax()
	m.setRoundTrip(rtt)

	now := base()
	round := uint64(1)
	var last uint64
	for elapsed := time.Duration(0); elapsed < 60*time.Second; elapsed += 100 * time.Millisecond {
		sample := uint64(shaped)
		if elapsed < bucketMs*time.Millisecond {
			// The bucket has not drained yet, so the path delivers at line rate.
			sample = drain
		}
		// The connection is application limited, so rounds crawl.
		if elapsed%(10*time.Second) == 0 {
			round++
		}
		m.updateMax(round, now.Add(elapsed), sample)
		last = m.get()
	}
	if last != shaped {
		t.Fatalf("the estimate settled on %d after a minute of shaping at %d; a drain rate "+
			"held this long is what paced a gateway at 29x the path", last, shaped)
	}
}

// A throttle that tightens under load must be believed, and the estimate must
// settle rather than oscillate.
func TestATighteningThrottleIsBelievedAndSettles(t *testing.T) {
	const rtt = 200 * time.Millisecond
	m := newTUICMinMax()
	m.setRoundTrip(rtt)

	now := base()
	steps := []uint64{20_000_000, 10_000_000, 5_000_000, 2_500_000}
	elapsed := time.Duration(0)
	round := uint64(1)
	for _, rate := range steps {
		for i := 0; i < 200; i++ {
			elapsed += 100 * time.Millisecond
			if i%50 == 0 {
				round++
			}
			m.updateMax(round, now.Add(elapsed), rate)
		}
		if got := m.get(); got != rate {
			t.Fatalf("throttle moved to %d and the estimate reads %d", rate, got)
		}
	}
	// Settled: another twenty seconds at the final rate does not move it.
	settled := m.get()
	for i := 0; i < 200; i++ {
		elapsed += 100 * time.Millisecond
		m.updateMax(round, now.Add(elapsed), steps[len(steps)-1])
	}
	if m.get() != settled {
		t.Fatalf("the estimate moved from %d to %d with no change in the path", settled, m.get())
	}
}

// The window is derived from the measured round trip rather than configured,
// and bounded so that neither a spurious sub-millisecond sample nor a satellite
// path can make the memory meaningless in either direction.
func TestTheWindowIsDerivedFromTheMeasuredRoundTrip(t *testing.T) {
	for _, test := range []struct {
		rtt  time.Duration
		want time.Duration
	}{
		{rtt: 226 * time.Millisecond, want: 2260 * time.Millisecond},
		{rtt: 430 * time.Millisecond, want: 4300 * time.Millisecond},
		{rtt: time.Millisecond, want: minBandwidthTimeWindow},
		{rtt: 5 * time.Second, want: maxBandwidthTimeWindow},
	} {
		m := newTUICMinMax()
		m.setRoundTrip(test.rtt)
		if m.timeWindow != test.want {
			t.Errorf("round trip %v gave a window of %v, want %v", test.rtt, m.timeWindow, test.want)
		}
	}
	// An unmeasured path keeps whatever it had rather than collapsing to zero.
	m := newTUICMinMax()
	before := m.timeWindow
	m.setRoundTrip(0)
	m.setRoundTrip(-time.Second)
	if m.timeWindow != before {
		t.Fatalf("an unmeasured round trip changed the window from %v to %v", before, m.timeWindow)
	}
}

// The ack-aggregation filter measures how much more than expected one round
// delivered. That is a statement about rounds and means nothing between them,
// so it keeps the original clock: supplying no time must leave the filter
// behaving exactly as it did.
func TestAFilterGivenNoTimeKeepsTheRoundClock(t *testing.T) {
	timed, untimed := newTUICMinMax(), newTUICMinMax()
	timed.setRoundTrip(200 * time.Millisecond)
	now := base()

	for round := uint64(1); round <= 30; round++ {
		value := uint64(1000)
		if round == 1 {
			value = 9000
		}
		// Wall time races far ahead of the rounds for the timed filter.
		timed.updateMax(round, now.Add(time.Duration(round)*time.Minute), value)
		untimed.updateMax(round, monotime.Time(0), value)
	}
	if untimed.get() != 1000 {
		t.Fatalf("the round clock alone gave %d after thirty rounds, want 1000", untimed.get())
	}
	// Both end up at the sustained value here; what matters is that the
	// untimed one got there by rounds and never consulted a clock it was not
	// given. A zero time must never be read as an ancient one.
	m := newTUICMinMax()
	m.setRoundTrip(200 * time.Millisecond)
	m.updateMax(1, monotime.Time(0), 5000)
	if m.stale(now.Add(time.Hour)) {
		t.Fatal("a sample carrying no time was reported stale, so a zero was read as ancient")
	}
	if m.get() != 5000 {
		t.Fatalf("untimed sample = %d, want 5000", m.get())
	}
}

// Expiry must not be a way to lose a rising path. A sample above the standing
// estimate is taken immediately, window or no window.
func TestARisingPathIsTakenImmediately(t *testing.T) {
	m := newTUICMinMax()
	m.setRoundTrip(200 * time.Millisecond)
	now := base()
	m.updateMax(1, now, 1_000_000)
	m.updateMax(1, now.Add(10*time.Millisecond), 8_000_000)
	if got := m.get(); got != 8_000_000 {
		t.Fatalf("estimate = %d, want the higher sample 8000000 taken at once", got)
	}
}

// The filter change alone is not enough, and this is the test that proves the
// sampler half is needed. Application-limited samples may not lower a live
// estimate, so on a connection that is application limited essentially always
// -- which is what the live gateway was, at 99.98% of samples -- expiring the
// estimate without also relaxing that rule would leave nothing able to replace
// it. This drives the real sampler rather than poking the filter.
func TestASamplerThatIsAlwaysAppLimitedStillComesDown(t *testing.T) {
	e := newTUICBandwidthEstimator()
	start := base()
	const rtt = 200 * time.Millisecond

	// A first burst, not application limited: the path really did carry this.
	var burstAcks []quiccongestion.AckedPacketInfo
	for i := 0; i < 100; i++ {
		pn := quiccongestion.PacketNumber(i)
		e.onSentPacket(start.Add(time.Duration(i)*time.Microsecond*200), pn, 1200, uint64(i)*1200, true)
		burstAcks = append(burstAcks, quiccongestion.AckedPacketInfo{PacketNumber: pn, BytesAcked: 1200})
	}
	e.onAckBatch(start.Add(rtt), burstAcks, 1)
	peak := e.estimate()
	if peak == 0 {
		t.Fatal("the burst produced no estimate to decay from")
	}
	e.maxFilter.setRoundTrip(rtt)

	// Now a long, slow, application-limited trickle: one packet per 50 ms,
	// with the round barely advancing, which is the shape that latched the
	// estimate for an hour.
	number := quiccongestion.PacketNumber(1000)
	elapsed := rtt
	round := uint64(1)
	for i := 0; i < 400; i++ {
		elapsed += 50 * time.Millisecond
		e.markAppLimited()
		e.onSentPacket(start.Add(elapsed), number, 1200, 1200, true)
		if i%100 == 0 {
			round++
		}
		e.onAckBatch(start.Add(elapsed+rtt), []quiccongestion.AckedPacketInfo{
			{PacketNumber: number, BytesAcked: 1200},
		}, round)
		number++
	}

	settled := e.estimate()
	t.Logf("peak=%d settled=%d after %v of application-limited trickle", peak, settled, elapsed)
	if settled == 0 {
		t.Fatal("the estimate emptied: an application-limited connection collapsed its own bandwidth model")
	}
	if settled >= peak {
		t.Fatalf("estimate held at %d against a peak of %d; the sampler never let a lower "+
			"application-limited sample replace an expired estimate", settled, peak)
	}
}
