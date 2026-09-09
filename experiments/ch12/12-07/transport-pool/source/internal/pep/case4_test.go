package pep

import (
	"io"
	"math/rand"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/pathsim"
)

// Falsification case 4 from docs/CONTROL-REDESIGN.md, and it fails.
//
// A policer drops what it cannot pass and holds nothing, so overload produces
// loss and no delay. Loss is no longer a congestion signal and there is no
// queue for the delay bound to measure, so neither brake can act. The design
// predicted this case would fail; it does, and by more than expected.
//
// This is a characterization test. It asserts the defect rather than the fix,
// so that the behaviour cannot change silently in either direction. If it
// starts failing because the sender no longer overdrives, that is the case
// being resolved: update it and the design document together.
//
// It matters more than a hypothetical, because internal/pathsim records that
// the live path this project targets is a policer -- "at twice the bottleneck
// rate it shows arrival runs averaging 2.3 packets and loss runs averaging
// 5.7 ... a limiter which passes everything for a while and then drops
// everything for a while".
func TestCase4APolicedPathIsStillUnbraked(t *testing.T) {
	if testing.Short() {
		t.Skip("brings up QUIC across an emulated 300 ms path")
	}
	requireStableImpairmentClock(t)
	const shaped = 250_000
	path := pathsim.Config{
		OneWayDelay:         150 * time.Millisecond,
		RateBytesPerSec:     shaped,
		PolicerRefillPeriod: 8 * time.Millisecond,
		Seed:                53,
	}
	socks, destination := codedPair(t, false, &path)
	conn := socksDial(t, socks, destination, erasureChannelBudget(180*time.Second))
	defer conn.Close()

	payload := make([]byte, 256*1024)
	rand.New(rand.NewSource(29)).Read(payload)
	done := make(chan struct{})
	go func() {
		defer close(done)
		for i := 0; i < 8; i++ {
			if _, err := conn.Write(payload); err != nil {
				return
			}
			got := make([]byte, len(payload))
			if _, err := io.ReadFull(conn, got); err != nil {
				return
			}
		}
	}()

	var peakPacing, peakBandwidth uint64
	var lanes int64
	var lastMode uint32
	var maxQueue time.Duration
	var maxBrake float64
	var lastLoss float64
	deadline := time.After(24 * time.Second)
	for measuring := true; measuring; {
		select {
		case <-done:
			measuring = false
		case <-deadline:
			measuring = false
		case <-time.After(2 * time.Second):
		}
		s := lastClient.Metrics().Snapshot()
		if s.QUICControllerPacingRate > peakPacing {
			peakPacing = s.QUICControllerPacingRate
		}
		if s.QUICControllerMaxBandwidth > peakBandwidth {
			peakBandwidth = s.QUICControllerMaxBandwidth
		}
		if q := s.QUICSmoothedRTT - s.QUICControllerMinRTT; q > maxQueue {
			maxQueue = q
		}
		if s.QUICDelayBrake > maxBrake {
			maxBrake = s.QUICDelayBrake
		}
		lanes = s.QUICLanes
		lastMode = s.QUICControllerMode
		if s.QUICPacketsSent > 0 {
			lastLoss = 100 * float64(s.QUICLossObservedPackets) / float64(s.QUICPacketsSent)
		}
	}

	t.Logf("policed at %d B/s: peak pacing %d (%.1fx), peak bandwidth estimate %d (%.1fx), "+
		"worst queue %v, strongest brake %.4f, loss %.1f%%, lanes %d, controller mode %d",
		shaped, peakPacing, float64(peakPacing)/shaped,
		peakBandwidth, float64(peakBandwidth)/shaped,
		maxQueue.Round(time.Millisecond), maxBrake, lastLoss, lanes, lastMode)

	if peakPacing == 0 {
		t.Skip("the flow never got going, so this run measured nothing")
	}
	// The two amplifiers, recorded separately because they need separate fixes.
	//
	// The bandwidth estimate reads well above the path's sustained rate: a
	// token bucket passes a burst at line rate, and a max filter reports that
	// burst as the path's bandwidth. Bounding the filter's memory in time did
	// not help here, because the bursts recur every refill period, so there is
	// always a recent high sample. The statistic is the problem, not its age.
	if float64(peakBandwidth) < shaped*1.4 {
		t.Errorf("the bandwidth estimate is no longer reporting the burst rate (%d against a "+
			"%d path); falsification case 4 may be resolved -- update the design document",
			peakBandwidth, shaped)
	}
	// And nothing brakes what that estimate then paces.
	if maxQueue > 50*time.Millisecond || maxBrake > 0 {
		t.Errorf("a policer produced %v of queue and a brake of %.4f; if it now queues, this "+
			"is no longer the unbraked case and the design document should say so",
			maxQueue, maxBrake)
	}
	// The overdrive this case records, after the compensation was bounded and a
	// stale peak stopped being re-seeded: 42x became 7.3x became 2.4x. It is
	// still an overdrive and the path is still unbraked, so this still asserts
	// the defect -- but it asserts the current one.
	if float64(peakPacing) < shaped*1.8 {
		t.Errorf("peak pacing %d is only %.1fx a %d path; the overdrive this case records has "+
			"been reduced again -- re-measure and update the design document",
			peakPacing, float64(peakPacing)/shaped, shaped)
	}
}
