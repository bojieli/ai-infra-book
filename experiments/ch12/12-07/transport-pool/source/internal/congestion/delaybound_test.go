package congestion

import (
	"testing"
	"time"

	quiccongestion "github.com/apernet/quic-go/congestion"
	"github.com/apernet/quic-go/monotime"
)

// fixedRTT is a round-trip provider a test can move under a live sender.
type fixedRTT struct{ min, smoothed time.Duration }

func (f *fixedRTT) MinRTT() time.Duration        { return f.min }
func (f *fixedRTT) LatestRTT() time.Duration     { return f.smoothed }
func (f *fixedRTT) SmoothedRTT() time.Duration   { return f.smoothed }
func (f *fixedRTT) MeanDeviation() time.Duration { return 0 }
func (f *fixedRTT) MaxAckDelay() time.Duration   { return 0 }
func (f *fixedRTT) PTO(bool) time.Duration       { return f.smoothed }
func (f *fixedRTT) UpdateRTT(_, _ time.Duration) {}
func (f *fixedRTT) SetMaxAckDelay(time.Duration) {}
func (f *fixedRTT) SetInitialRTT(time.Duration)  {}

var _ quiccongestion.RTTStatsProvider = (*fixedRTT)(nil)

// senderAtRTT builds a sender whose inner controller has established minRTT and
// whose provider reports the given smoothed round trip.
func senderAtRTT(t *testing.T, minRTT, smoothed time.Duration) *ErasureSender {
	t.Helper()
	e := NewErasureSender(1200)
	e.inner.minRTT = minRTT
	e.SetRTTStatsProvider(&fixedRTT{min: minRTT, smoothed: smoothed})
	return e
}

// The bound is that the round trip may not exceed twice the path's own
// minimum, which is the same statement as "the queue may hold at most one
// bandwidth-delay product". Below that the sender is not touched at all: a
// brake that engages before the bound would make the bound a target.
func TestTheDelayBoundIsSilentBelowOneRoundTripOfQueue(t *testing.T) {
	const minRTT = 200 * time.Millisecond
	for _, smoothed := range []time.Duration{
		minRTT,                        // no queue
		minRTT + 50*time.Millisecond,  // a quarter
		minRTT + 199*time.Millisecond, // just inside
		2 * minRTT,                    // exactly at the bound
	} {
		e := senderAtRTT(t, minRTT, smoothed)
		if got := e.delayBounded(1000); got != 1000 {
			t.Errorf("smoothed %v (queue %v) scaled the rate to %.1f, want it untouched",
				smoothed, smoothed-minRTT, got)
		}
		if brake := e.Telemetry().DelayBrake; brake != 0 {
			t.Errorf("smoothed %v published a brake of %.4f with no queue past the bound", smoothed, brake)
		}
	}
}

// Past the bound the response is proportional to the overshoot rather than to
// the fact of it: at one round trip of queue the factor is one, and it falls
// continuously from there.
func TestTheDelayBoundScalesWithTheOvershoot(t *testing.T) {
	const minRTT = 200 * time.Millisecond
	for _, test := range []struct {
		queue time.Duration
		want  float64
	}{
		{queue: 2 * minRTT, want: 500},  // twice the bound, half the rate
		{queue: 4 * minRTT, want: 250},  // four times, a quarter
		{queue: 10 * minRTT, want: 100}, // ten times, a tenth
	} {
		e := senderAtRTT(t, minRTT, minRTT+test.queue)
		got := e.delayBounded(1000)
		if got < test.want*0.99 || got > test.want*1.01 {
			t.Errorf("queue %v scaled 1000 to %.1f, want about %.1f", test.queue, got, test.want)
		}
		brake := e.Telemetry().DelayBrake
		if brake <= 0 || brake >= 1 {
			t.Errorf("queue %v published a brake of %.4f, want a share in (0,1)", test.queue, brake)
		}
	}
	// And it is monotone: more queue never means less braking.
	previous := 1e9
	for multiple := 1; multiple <= 8; multiple++ {
		e := senderAtRTT(t, minRTT, minRTT+time.Duration(multiple)*minRTT)
		got := e.delayBounded(1000)
		if got > previous {
			t.Fatalf("queue of %d round trips gave %.1f, more than the %.1f at one less",
				multiple, got, previous)
		}
		previous = got
	}
}

// A path nobody has measured has no bound to apply, and a sender with no
// provider must behave exactly as it did before the bound existed.
func TestTheDelayBoundNeedsAMeasuredPath(t *testing.T) {
	e := NewErasureSender(1200)
	if got := e.delayBounded(1000); got != 1000 {
		t.Fatalf("a sender with no round-trip provider scaled the rate to %.1f", got)
	}
	e.inner.minRTT = 0
	e.SetRTTStatsProvider(&fixedRTT{min: 0, smoothed: time.Second})
	if got := e.delayBounded(1000); got != 1000 {
		t.Fatalf("a sender with no established minimum scaled the rate to %.1f", got)
	}
}

// The bound is applied after the erasure compensation, because the queue holds
// what was sent rather than what arrived.
//
// This is the case the window gain cannot cover. On an erasure path the
// compensation multiplies the window so that a full one *arrives*, which means
// what is put on the wire is larger by the same factor -- and the bottleneck
// queue is downstream of that multiplication and does not care why the bytes
// were sent. Measuring the three points in order is what shows the bound
// catching the compensation rather than being applied before it.
func TestTheDelayBoundAppliesToWhatIsSentNotWhatArrives(t *testing.T) {
	const minRTT = 200 * time.Millisecond
	at := func(arrival float64, smoothed time.Duration) float64 {
		e := senderAtRTT(t, minRTT, smoothed)
		e.inner.estimator.maxFilter.updateMax(1, monotime.Now(), 1_000_000)
		e.arrival.Store(uint64(arrival * partsPerMillion))
		return float64(e.bandwidth())
	}

	clean := at(1, minRTT)
	if clean <= 0 {
		t.Fatal("a clean path with a measured bandwidth reported none")
	}
	// Half the packets arrive, so twice as many must be sent for a full window
	// to land. That is the compensation, and it is deliberate.
	compensated := at(0.5, minRTT)
	if ratio := compensated / clean; ratio < 1.9 || ratio > 2.1 {
		t.Fatalf("erasure compensation scaled the rate by %.2f, want about 2", ratio)
	}
	// Two round trips of queue halves it back. Had the bound been applied
	// before the compensation, the compensation would have undone it and this
	// would still read twice the clean rate.
	braked := at(0.5, minRTT+2*minRTT)
	if ratio := braked / clean; ratio < 0.9 || ratio > 1.1 {
		t.Fatalf("with two round trips of queue the rate is %.2fx the clean one; the erasure "+
			"compensation is escaping the delay bound", ratio)
	}
}

// Telemetry runs on the flow telemetry goroutine while quic-go invokes the
// controller on its packet goroutine. Everything it reports must therefore come
// from an atomic, and this is the test that says so.
//
// It exists because that invariant was broken by a one-line convenience: the
// delay brake was recomputed inside Telemetry so a trace taken while nothing
// was sending would still be fresh, and recomputing it reached through to the
// inner sender's minimum round trip, which refreshRTTSample writes. The race
// detector found it on one CI architecture and on none of eight local runs.
//
// The sender is driven with real sent packets and shrinking round trips, which
// is what makes refreshRTTSample write rather than return early. Without that
// the test passes against the defect it was written for.
func TestTelemetryIsSafeBesideTheControllerGoroutine(t *testing.T) {
	e := NewErasureSender(1200)
	e.SetRTTStatsProvider(&fixedRTT{min: time.Second, smoothed: time.Second})

	done := make(chan struct{})
	go func() {
		defer close(done)
		base := monotime.Now()
		number := quiccongestion.PacketNumber(0)
		for i := 0; i < 3000; i++ {
			// A round trip that keeps shrinking, so every event takes the
			// branch in refreshRTTSample that stores a new minimum.
			rtt := time.Duration(400-(i%350)) * time.Millisecond
			sent := base.Add(time.Duration(i) * time.Millisecond)
			e.OnPacketSent(sent, 2400, number, 1200, true)
			e.OnCongestionEventEx(2400, sent.Add(rtt), []quiccongestion.AckedPacketInfo{
				{PacketNumber: number, BytesAcked: 1200, ReceivedTime: sent.Add(rtt)},
			}, nil)
			number++
		}
	}()
	for i := 0; i < 3000; i++ {
		_ = e.Telemetry()
	}
	<-done
}
