package pathsim

import (
	"fmt"
	"net"
	"sync"
	"testing"
	"time"
)

// measurement is what one blast observed. Reporting offered alongside
// delivered is what separates "the limiter is wrong" from "this host never
// generated the load", which are the two ways a calibration cell can go red
// and which a delivered-only number cannot tell apart.
type measurement struct {
	deliveredMbits float64
	offeredMbits   float64
	dropped        uint64
}

// shortfall reports how far the sender fell below the rate it was asked to
// offer. A paced sender that cannot keep up starves the limiter, and the
// limiter then under-delivers through no fault of its own.
func (m measurement) shortfall(wantMbits float64) float64 {
	if wantMbits <= 0 {
		return 0
	}
	return m.offeredMbits / wantMbits
}

// blast keeps a relay busy, waits for its delay queue to reach steady state,
// and reports delivery during a fixed observation window. offeredMbits == 0
// offers packets as fast as the host can generate them; otherwise the sender
// is paced to that rate so a calibration does not turn into a CPU-contention
// test merely because its source can flood much faster than its target.
func blast(t *testing.T, cfg Config, duration time.Duration, offeredMbits float64) measurement {
	t.Helper()
	sink, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer sink.Close()
	relay, err := New("127.0.0.1:0", sink.LocalAddr().String(), cfg)
	if err != nil {
		t.Fatal(err)
	}
	defer relay.Close()
	target, err := net.ResolveUDPAddr("udp", relay.LocalAddr())
	if err != nil {
		t.Fatal(err)
	}
	client, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer client.Close()
	go func() {
		buf := make([]byte, 2048)
		for {
			if _, _, err := sink.ReadFrom(buf); err != nil {
				return
			}
		}
	}()
	payload := make([]byte, 1200)
	burstPackets := 32
	if offeredMbits > 0 {
		// Keep paced wakeups at least two milliseconds apart. A fixed
		// 32-packet burst requires sub-millisecond timers at the 400 Mbit/s
		// calibration cell; under ordinary `go test ./...` package
		// concurrency the sender can then under-offer while the relay itself
		// remains healthy, producing a false limiter failure. The adaptive
		// burst stays below five percent of the smallest bandwidth-delay
		// product used by that high-rate cell.
		packetsForTwoMilliseconds := int(offeredMbits * 1e6 * (2 * time.Millisecond).Seconds() / float64(len(payload)*8))
		if packetsForTwoMilliseconds > burstPackets {
			burstPackets = packetsForTwoMilliseconds
		}
	}
	stop := make(chan struct{})
	var sender sync.WaitGroup
	sender.Add(1)
	go func() {
		defer sender.Done()
		next := time.Now()
		var burstInterval time.Duration
		if offeredMbits > 0 {
			burstBits := float64(burstPackets * len(payload) * 8)
			burstInterval = time.Duration(burstBits / (offeredMbits * 1e6) * float64(time.Second))
		}
		for {
			if burstInterval > 0 {
				if wait := time.Until(next); wait > 0 {
					timer := time.NewTimer(wait)
					select {
					case <-timer.C:
					case <-stop:
						if !timer.Stop() {
							select {
							case <-timer.C:
							default:
							}
						}
						return
					}
				}
				next = next.Add(burstInterval)
			}
			for range burstPackets {
				select {
				case <-stop:
					return
				default:
					_, _ = client.WriteTo(payload, target)
				}
			}
		}
	}()
	defer func() {
		close(stop)
		sender.Wait()
	}()

	// Two propagation delays plus a scheduler margin lets both the input and
	// output sides settle before the observed interval begins.
	time.Sleep(2*cfg.OneWayDelay + 500*time.Millisecond)
	before, _ := relay.Stats()
	time.Sleep(duration)
	after, _ := relay.Stats()
	perMbit := 8 / duration.Seconds() / 1e6
	return measurement{
		deliveredMbits: float64(after.BytesOut-before.BytesOut) * perMbit,
		// What actually arrived at the relay, which is what the sender managed
		// to generate rather than what it was asked for.
		offeredMbits: float64(after.BytesIn-before.BytesIn) * perMbit,
		dropped:      after.PacketsDropped - before.PacketsDropped,
	}
}

// TestForwardingCapacity measures what the emulator itself can forward with no
// rate limiter, which bounds every transport number taken through it.
func TestForwardingCapacity(t *testing.T) {
	if testing.Short() {
		// The floor below is a statement about the host, not about the
		// emulator: a runner sharing its cores can forward under 100 Mbit/s
		// while the emulator is perfectly correct. Unlike the calibration
		// below, this one has no load guard that could tell those apart, so
		// on the per-PR matrix it is the more fragile of the two. It belongs
		// with the calibration it bounds, in the serialised deep runs.
		t.Skip("forwarding capacity measures the host; runs in deep.yml")
	}
	for _, rtt := range []time.Duration{0, 20 * time.Millisecond, 200 * time.Millisecond} {
		got := blast(t, Config{OneWayDelay: rtt / 2}, 3*time.Second, 0).deliveredMbits
		t.Logf("rtt=%v unlimited capacity=%.0f Mbit/s", rtt, got)
		if got < 100 {
			t.Fatalf("emulator forwards only %.0f Mbit/s at %v", got, rtt)
		}
	}
}

// TestRateLimiterDeliversItsConfiguredRate is the calibration that matters for
// any utilisation claim. A transport is said to under-use a link by comparing
// its goodput with the configured rate; that comparison is only meaningful if
// the emulator's own rate limiter delivers the rate it was asked for. It runs
// at every point of the bandwidth-delay grid the benchmarks use, because the
// limiter's queue is sized from the product and is exactly where a fault would
// hide.
func TestRateLimiterDeliversItsConfiguredRate(t *testing.T) {
	if testing.Short() {
		// This calibration needs a host that can generate several hundred
		// Mbit/s while it simultaneously paces, shapes and polices the same
		// traffic. The per-PR matrix is the wrong place to ask for that: six
		// runners, packages in parallel, and no control over what else shares
		// the core. A cell there can clear both load guards and still
		// under-deliver because the generator and the shaper are competing,
		// which reports a limiter fault the limiter did not commit --
		// observed on windows-11-arm and on macos-15-intel, a different
		// runner each time. deep.yml and release-candidate.yml run this
		// without -short and with -p=1, which is the serialised, uncontended
		// condition a measurement of this kind has to have to mean anything.
		t.Skip("rate calibration is meaningful only on an uncontended host; runs in deep.yml")
	}
	rates := []float64{50, 200, 400}
	if raceDetectorEnabled {
		// Race instrumentation capped the two-core hosted runner near 180
		// Mbit/s, so asking it to generate 200 or 400 Mbit/s measures CPU
		// instrumentation rather than the rate limiter. Keep one attainable
		// cell at every RTT for race coverage; the normal deep job retains the
		// complete calibration matrix.
		rates = []float64{50}
	}
	for _, rtt := range []time.Duration{50, 200, 400} {
		rtt := rtt * time.Millisecond
		unshaped := blast(t, Config{OneWayDelay: rtt / 2}, 2*time.Second, 0).deliveredMbits
		t.Logf("rtt=%v unshaped capacity=%.0f Mbit/s", rtt, unshaped)
		for _, mbits := range rates {
			mbits := mbits
			name := fmt.Sprintf("rtt%v_rate%.0f", rtt, mbits)
			t.Run(name, func(t *testing.T) {
				// A shaped result is meaningful only if this runner can offer
				// comfortably more than the requested rate through the same
				// delayed relay. Slow hosted runners legitimately skip only the
				// unattainable cells; they still exercise every lower cell.
				//
				// The sender is asked for 1.5x the limit so the limiter is the
				// thing that binds, but the host must clear twice the limit
				// unshaped before that offer is credible. The unshaped probe is
				// the wrong shape for a shaped run: it is unpaced, and pacing
				// plus per-packet policing costs more CPU per byte than
				// forwarding flat out, so the generator and the shaper end up
				// competing for the same cores. Two observations fix the bar. A
				// macOS-15-intel runner measured 551 Mbit/s unshaped, cleared an
				// earlier 500 Mbit/s bar for the 400 Mbit/s cell, and delivered
				// 0.73. Another measured 347 Mbit/s, cleared 1.5x for the 200
				// Mbit/s cell, then generated only 288 of the 300 Mbit/s it was
				// asked for and delivered 0.89. In both the headroom over the
				// offered load -- 1.38x and 1.16x -- was inside the noise of the
				// thing it was gating. Requiring 2x the limit leaves 1.33x over
				// the offer itself, which is the quantity that has to hold.
				offered := mbits * 1.5
				if needed := mbits * 2; unshaped < needed {
					t.Skipf("host forwards %.0f Mbit/s unshaped at rtt=%v; need %.0f Mbit/s to calibrate a %.0f Mbit/s limiter under a %.0f Mbit/s offer",
						unshaped, rtt, needed, mbits, offered)
				}
				cfg := Config{
					OneWayDelay:     rtt / 2,
					RateBytesPerSec: uint64(mbits * 1e6 / 8),
				}
				got := blast(t, cfg, 4*time.Second, offered)
				ratio := got.deliveredMbits / mbits
				t.Logf("rtt=%v rate=%.0f delivered=%.1f Mbit/s ratio=%.2f (offered %.0f of %.0f Mbit/s, %d dropped)",
					rtt, mbits, got.deliveredMbits, ratio, got.offeredMbits, offered, got.dropped)
				// A starved sender cannot calibrate a limiter: if the load never
				// reached the relay, an under-delivery says nothing about the
				// limiter. Check the load before judging the limiter, so the
				// failure names the real cause instead of blaming the shaper for
				// a sender the host could not run fast enough.
				if reached := got.shortfall(mbits); reached < 1.05 {
					t.Skipf("sender offered only %.0f Mbit/s (%.2f of the %.0f Mbit/s limit) at rtt=%v; "+
						"this host cannot generate the load the calibration needs",
						got.offeredMbits, reached, mbits, rtt)
				}
				if ratio < 0.9 {
					t.Fatalf("rate limiter delivered %.2f of its configured rate at rtt=%v rate=%.0f "+
						"while offered %.0f Mbit/s; utilisation measured against this path is measuring the emulator",
						ratio, rtt, mbits, got.offeredMbits)
				}
			})
		}
	}
}
