package pathsim

import (
	"bytes"
	"io"
	"math/rand"
	"net"
	"runtime"
	"testing"
	"time"
)

// echoServer returns a UDP socket that echoes every datagram back to its
// sender, which is enough to observe the emulator's delay and loss behavior.
func echoServer(t *testing.T) net.PacketConn {
	t.Helper()
	conn, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	go func() {
		buf := make([]byte, 2048)
		for {
			n, addr, err := conn.ReadFrom(buf)
			if err != nil {
				return
			}
			_, _ = conn.WriteTo(buf[:n], addr)
		}
	}()
	t.Cleanup(func() { _ = conn.Close() })
	return conn
}

func TestRelayAppliesRoundTripDelay(t *testing.T) {
	server := echoServer(t)
	relay, err := New("127.0.0.1:0", server.LocalAddr().String(), Config{OneWayDelay: 40 * time.Millisecond})
	if err != nil {
		t.Fatal(err)
	}
	defer relay.Close()

	client, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer client.Close()
	target, err := net.ResolveUDPAddr("udp", relay.LocalAddr())
	if err != nil {
		t.Fatal(err)
	}

	payload := []byte("round trip")
	started := time.Now()
	if _, err := client.WriteTo(payload, target); err != nil {
		t.Fatal(err)
	}
	buf := make([]byte, 64)
	_ = client.SetReadDeadline(time.Now().Add(2 * time.Second))
	n, _, err := client.ReadFrom(buf)
	if err != nil {
		t.Fatal(err)
	}
	elapsed := time.Since(started)
	if !bytes.Equal(buf[:n], payload) {
		t.Fatalf("echoed payload = %q, want %q", buf[:n], payload)
	}
	// The emulator adds the one-way delay in each direction. Only the lower
	// bound is asserted: scheduling jitter can add to it but never remove it.
	if elapsed < 80*time.Millisecond {
		t.Fatalf("round trip took %s, want at least 80ms", elapsed)
	}
}

func TestRelayDropsAtConfiguredLossRate(t *testing.T) {
	server := echoServer(t)
	relay, err := New("127.0.0.1:0", server.LocalAddr().String(), Config{LossRate: 0.5, Seed: 7})
	if err != nil {
		t.Fatal(err)
	}
	defer relay.Close()

	client, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer client.Close()
	target, err := net.ResolveUDPAddr("udp", relay.LocalAddr())
	if err != nil {
		t.Fatal(err)
	}
	const sent = 400
	for range sent {
		if _, err := client.WriteTo([]byte("x"), target); err != nil {
			t.Fatal(err)
		}
	}
	// Give the relay time to process the burst before sampling counters.
	deadline := time.Now().Add(2 * time.Second)
	for time.Now().Before(deadline) {
		if up, _ := relay.Stats(); up.PacketsIn >= sent {
			break
		}
		time.Sleep(5 * time.Millisecond)
	}
	up, _ := relay.Stats()
	if up.PacketsIn < sent {
		t.Fatalf("relay observed %d of %d packets", up.PacketsIn, sent)
	}
	// A seeded Bernoulli process at p=0.5 over 400 packets sits far inside
	// this band; the test is checking the loss model is applied at roughly the
	// configured rate, not the precise draw.
	if up.PacketsLost < sent*3/10 || up.PacketsLost > sent*7/10 {
		t.Fatalf("dropped %d of %d packets, want roughly half", up.PacketsLost, sent)
	}
}

func TestRelayIsReproducibleForOneSeed(t *testing.T) {
	losses := make([]uint64, 2)
	for attempt := range losses {
		server := echoServer(t)
		relay, err := New("127.0.0.1:0", server.LocalAddr().String(), Config{LossRate: 0.3, Seed: 99})
		if err != nil {
			t.Fatal(err)
		}
		client, err := net.ListenPacket("udp", "127.0.0.1:0")
		if err != nil {
			t.Fatal(err)
		}
		target, err := net.ResolveUDPAddr("udp", relay.LocalAddr())
		if err != nil {
			t.Fatal(err)
		}
		const sent = 200
		for range sent {
			if _, err := client.WriteTo([]byte("x"), target); err != nil {
				t.Fatal(err)
			}
		}
		deadline := time.Now().Add(2 * time.Second)
		for time.Now().Before(deadline) {
			if up, _ := relay.Stats(); up.PacketsIn >= sent {
				break
			}
			time.Sleep(5 * time.Millisecond)
		}
		up, _ := relay.Stats()
		losses[attempt] = up.PacketsLost
		_ = client.Close()
		_ = relay.Close()
	}
	// Reproducibility is the whole reason this emulator exists: two runs of
	// the same seed over the same packet count must drop the same packets.
	if losses[0] != losses[1] {
		t.Fatalf("seeded loss was not reproducible: %d then %d", losses[0], losses[1])
	}
}

func TestRelayRejectsInvalidLossRate(t *testing.T) {
	if _, err := New("127.0.0.1:0", "127.0.0.1:1", Config{LossRate: 1}); err == nil {
		t.Fatal("loss rate of 1 was accepted")
	}
	if _, err := New("127.0.0.1:0", "127.0.0.1:1", Config{LossRate: -0.1}); err == nil {
		t.Fatal("negative loss rate was accepted")
	}
}

func TestBottleneckQueueTailDrops(t *testing.T) {
	// A slow bottleneck with a small buffer must drop rather than buffer an
	// unbounded burst; otherwise the emulator would report a queueing delay no
	// real router would provide.
	d := &direction{}
	cfg := Config{RateBytesPerSec: 1000, QueueBytes: 2000}.withDefaults()
	cfg.QueueBytes = 2000
	now := time.Now()
	accepted := 0
	for range 20 {
		if _, ok := d.schedule(now, 500, cfg); ok {
			accepted++
		}
	}
	if accepted == 20 {
		t.Fatal("bottleneck accepted an unbounded burst")
	}
	if accepted == 0 {
		t.Fatal("bottleneck dropped every packet")
	}
	if got := d.packetsDropped.Load(); got != uint64(20-accepted) {
		t.Fatalf("tail drop count = %d, want %d", got, 20-accepted)
	}
}

func TestBurstLossProducesRunsAtTheConfiguredRate(t *testing.T) {
	// Correlated loss is a different regime for a transport than the same
	// average spread evenly, so the model has to deliver both the requested
	// long-run rate and genuinely clustered drops.
	d := &direction{rng: rand.New(rand.NewSource(11)), lossRate: 0.2}
	cfg := Config{LossRate: 0.2, LossBurstPackets: 12}
	const trials = 200000
	dropped, runs, inRun := 0, 0, false
	for range trials {
		if d.dropLocked(cfg) {
			dropped++
			if !inRun {
				runs++
				inRun = true
			}
			continue
		}
		inRun = false
	}
	rate := float64(dropped) / trials
	if rate < 0.17 || rate > 0.23 {
		t.Fatalf("long-run drop rate %.3f, want about 0.20", rate)
	}
	meanRun := float64(dropped) / float64(runs)
	if meanRun < 9 || meanRun > 15 {
		t.Fatalf("mean burst length %.1f packets, want about 12", meanRun)
	}
}

func TestIndependentLossHasNoBurstStructure(t *testing.T) {
	d := &direction{rng: rand.New(rand.NewSource(11)), lossRate: 0.2}
	cfg := Config{LossRate: 0.2}
	const trials = 200000
	dropped, runs, inRun := 0, 0, false
	for range trials {
		if d.dropLocked(cfg) {
			dropped++
			if !inRun {
				runs++
				inRun = true
			}
			continue
		}
		inRun = false
	}
	// Bernoulli runs average 1/(1-p) = 1.25 packets.
	if meanRun := float64(dropped) / float64(runs); meanRun > 1.5 {
		t.Fatalf("independent loss produced %.2f-packet runs, want about 1.25", meanRun)
	}
}

func TestAsymmetricLossAppliesPerDirection(t *testing.T) {
	// A transport can depend on the reverse direction in ways that are
	// invisible when both directions are impaired equally, so the emulator has
	// to be able to make one direction much worse than the other.
	server := echoServer(t)
	relay, err := New("127.0.0.1:0", server.LocalAddr().String(), Config{UpstreamLossRate: 0.6, Seed: 5})
	if err != nil {
		t.Fatal(err)
	}
	defer relay.Close()
	client, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer client.Close()
	target, err := net.ResolveUDPAddr("udp", relay.LocalAddr())
	if err != nil {
		t.Fatal(err)
	}
	const sent = 400
	for range sent {
		if _, err := client.WriteTo([]byte("x"), target); err != nil {
			t.Fatal(err)
		}
	}
	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		if up, _ := relay.Stats(); up.PacketsIn >= sent {
			break
		}
		time.Sleep(5 * time.Millisecond)
	}
	up, down := relay.Stats()
	if up.PacketsLost < sent*4/10 {
		t.Fatalf("upstream dropped %d of %d, want roughly 60%%", up.PacketsLost, sent)
	}
	if down.PacketsLost != 0 {
		t.Fatalf("downstream dropped %d packets, want none", down.PacketsLost)
	}
}

func TestAsymmetricLossRateIsValidated(t *testing.T) {
	if _, err := New("127.0.0.1:0", "127.0.0.1:1", Config{UpstreamLossRate: 1}); err == nil {
		t.Fatal("upstream loss rate of 1 was accepted")
	}
}

func TestDelayJitterReordersPackets(t *testing.T) {
	// Jitter is drawn per packet, so it reorders. Reordering changes when a
	// QUIC sender declares a packet lost, which is exactly why the emulator
	// should be able to produce it.
	d := &direction{rng: rand.New(rand.NewSource(3))}
	cfg := Config{OneWayDelay: 10 * time.Millisecond, DelayJitter: 20 * time.Millisecond}
	now := time.Now()
	var previous time.Time
	reordered := 0
	for i := range 200 {
		arrival, ok := d.schedule(now.Add(time.Duration(i)*time.Millisecond), 1200, cfg)
		if !ok {
			t.Fatal("jitter must not drop packets")
		}
		if i > 0 && arrival.Before(previous) {
			reordered++
		}
		previous = arrival
	}
	if reordered == 0 {
		t.Fatal("jitter produced no reordering")
	}
}

func TestNoJitterPreservesOrder(t *testing.T) {
	d := &direction{rng: rand.New(rand.NewSource(3))}
	cfg := Config{OneWayDelay: 10 * time.Millisecond}
	now := time.Now()
	var previous time.Time
	for i := range 100 {
		arrival, ok := d.schedule(now.Add(time.Duration(i)*time.Millisecond), 1200, cfg)
		if !ok {
			t.Fatal("an unimpaired path must not drop packets")
		}
		if i > 0 && arrival.Before(previous) {
			t.Fatal("packets were reordered without jitter configured")
		}
		previous = arrival
	}
}

// echoTCP is a TCP origin that echoes and can send a fixed volume on request.
func echoTCP(t *testing.T, volume int) net.Listener {
	t.Helper()
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = listener.Close() })
	go func() {
		for {
			conn, err := listener.Accept()
			if err != nil {
				return
			}
			go func() {
				defer conn.Close()
				var request [1]byte
				if _, err := conn.Read(request[:]); err != nil {
					return
				}
				payload := make([]byte, 32*1024)
				sent := 0
				for sent < volume {
					chunk := len(payload)
					if remaining := volume - sent; remaining < chunk {
						chunk = remaining
					}
					n, err := conn.Write(payload[:chunk])
					if err != nil {
						return
					}
					sent += n
				}
			}()
		}
	}()
	return listener
}

// A bottleneck must not truncate a stream. Tail drop is meaningless for a byte
// stream - discarding a chunk delivers a hole rather than triggering a
// retransmission - and treating it as fatal ended transfers at exactly one
// bandwidth-delay product.
func TestTCPRelayDeliversMoreThanOneQueueOfData(t *testing.T) {
	const volume = 4 << 20
	origin := echoTCP(t, volume)
	relay, err := NewTCP("127.0.0.1:0", origin.Addr().String(), Config{
		OneWayDelay: 10 * time.Millisecond, RateBytesPerSec: 12500000,
	})
	if err != nil {
		t.Fatal(err)
	}
	defer relay.Close()

	conn, err := net.DialTimeout("tcp", relay.LocalAddr(), 5*time.Second)
	if err != nil {
		t.Fatal(err)
	}
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(30 * time.Second))
	if _, err := conn.Write([]byte{'g'}); err != nil {
		t.Fatal(err)
	}
	received, err := io.Copy(io.Discard, io.LimitReader(conn, volume))
	if err != nil {
		t.Fatalf("after %d bytes: %v", received, err)
	}
	if received != volume {
		t.Fatalf("received %d of %d bytes; a stream relay must apply backpressure, not drop", received, volume)
	}
}

// Reading and delayed writing have to be separate stages. Holding a chunk
// inline before reading the next makes the relay serial, capping throughput at
// one buffer per one-way delay no matter what rate is configured.
func TestTCPRelayPipelinesAcrossTheDelay(t *testing.T) {
	const volume = 2 << 20
	origin := echoTCP(t, volume)
	// 40 ms one way with a 16 KiB read size would cap a serial relay near
	// 3 Mbit/s; the configured bottleneck is far above that.
	relay, err := NewTCP("127.0.0.1:0", origin.Addr().String(), Config{
		OneWayDelay: 40 * time.Millisecond, RateBytesPerSec: 12500000,
	})
	if err != nil {
		t.Fatal(err)
	}
	defer relay.Close()

	conn, err := net.DialTimeout("tcp", relay.LocalAddr(), 5*time.Second)
	if err != nil {
		t.Fatal(err)
	}
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(30 * time.Second))
	if _, err := conn.Write([]byte{'g'}); err != nil {
		t.Fatal(err)
	}
	started := time.Now()
	received, err := io.Copy(io.Discard, io.LimitReader(conn, volume))
	elapsed := time.Since(started)
	if err != nil || received != volume {
		t.Fatalf("received %d of %d bytes: %v", received, volume, err)
	}
	mbits := float64(volume) * 8 / elapsed.Seconds() / 1e6
	if mbits < 20 {
		t.Fatalf("throughput %.1f Mbit/s over a 100 Mbit/s bottleneck; the relay is not pipelining", mbits)
	}
}

// Loss cannot be emulated for a stream relay, and silently ignoring the
// request would produce a lossless result labelled as lossy.
func TestTCPRelayRefusesLoss(t *testing.T) {
	if _, err := NewTCP("127.0.0.1:0", "127.0.0.1:1", Config{LossRate: 0.1}); err == nil {
		t.Fatal("a TCP relay accepted a loss rate it cannot apply")
	}
	if _, err := NewTCP("127.0.0.1:0", "127.0.0.1:1", Config{UpstreamLossRate: 0.1}); err == nil {
		t.Fatal("a TCP relay accepted an upstream loss rate it cannot apply")
	}
}

// An emulator that becomes the bottleneck silently caps every result taken
// with it. One goroutine and one timer per delayed packet does exactly that: at
// 200 ms of delay every packet in flight is a live goroutine, so offered load
// turns into scheduler pressure. Configured at 1 Gbit/s with no loss, that
// implementation delivered *less* than the same path configured at 100 Mbit/s,
// and it capped measured transport throughput near 20-30 Mbit/s; replacing it
// took a single connection from 29.5 to 94.8 Mbit/s on an otherwise identical
// path.
//
// Throughput itself is too environment-dependent to assert here, so this pins
// the design property that made it possible: delayed packets must not cost a
// goroutine each.
func TestDelayedPacketsDoNotCostAGoroutineEach(t *testing.T) {
	sink, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer sink.Close()
	go func() {
		buf := make([]byte, 2048)
		for {
			if _, _, err := sink.ReadFrom(buf); err != nil {
				return
			}
		}
	}()

	// A long delay keeps every packet in flight for the whole test.
	relay, err := New("127.0.0.1:0", sink.LocalAddr().String(), Config{
		OneWayDelay: 5 * time.Second, RateBytesPerSec: 125_000_000,
	})
	if err != nil {
		t.Fatal(err)
	}
	defer relay.Close()

	client, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer client.Close()
	target, err := net.ResolveUDPAddr("udp", relay.LocalAddr())
	if err != nil {
		t.Fatal(err)
	}

	baseline := runtime.NumGoroutine()
	const packets = 3000
	payload := make([]byte, 1200)
	for range packets {
		if _, err := client.WriteTo(payload, target); err != nil {
			t.Fatal(err)
		}
		// Pace slightly so the relay's socket buffer does not drop the burst
		// before the delay model ever sees it.
		if runtime.NumGoroutine() < 0 {
			return
		}
	}
	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		if up, _ := relay.Stats(); up.PacketsIn >= packets/2 {
			break
		}
		time.Sleep(10 * time.Millisecond)
	}
	up, _ := relay.Stats()
	if up.PacketsIn < packets/2 {
		t.Skipf("only %d of %d packets reached the relay; the socket buffer dropped the burst", up.PacketsIn, packets)
	}
	if up.PacketsOut > 0 {
		t.Fatalf("%d packets were delivered despite a 5s delay; they are not being held", up.PacketsOut)
	}
	growth := runtime.NumGoroutine() - baseline
	// One scheduler goroutine per direction, plus whatever the runtime and the
	// test itself are doing. A goroutine per in-flight packet would be three
	// orders of magnitude above this.
	if growth > 64 {
		t.Fatalf("goroutines grew by %d with %d packets in flight; delayed packets are costing a goroutine each",
			growth, up.PacketsIn)
	}
}

// Wander is the impairment the emulator lacked, and it is not jitter. Jitter
// draws per packet, so it reorders and leaves the smoothed round trip near the
// minimum; a real long-haul path varies its delay over hundreds of
// milliseconds, so a whole flight shifts together. Measured on the China-US
// path this targets, the round trip ranged 226 to 440 ms while the minimum
// stayed put.
func TestDelayWanderVariesTheRoundTripWithoutReordering(t *testing.T) {
	d := &direction{rng: rand.New(rand.NewSource(7))}
	cfg := Config{
		OneWayDelay:       100 * time.Millisecond,
		DelayWander:       100 * time.Millisecond,
		DelayWanderPeriod: 40 * time.Millisecond,
	}
	now := time.Now()
	var previous time.Time
	var min, max time.Duration
	reordered := 0
	for i := range 500 {
		sent := now.Add(time.Duration(i) * time.Millisecond)
		arrival, ok := d.schedule(sent, 1200, cfg)
		if !ok {
			t.Fatal("wander must not drop packets")
		}
		delay := arrival.Sub(sent)
		if min == 0 || delay < min {
			min = delay
		}
		if delay > max {
			max = delay
		}
		if i > 0 && arrival.Before(previous) {
			reordered++
		}
		previous = arrival
	}
	if min < cfg.OneWayDelay {
		t.Fatalf("wander moved the delay below the configured minimum: %v < %v", min, cfg.OneWayDelay)
	}
	if max > cfg.OneWayDelay+cfg.DelayWander {
		t.Fatalf("wander exceeded its amplitude: %v > %v", max, cfg.OneWayDelay+cfg.DelayWander)
	}
	if spread := max - min; spread < cfg.DelayWander/4 {
		t.Fatalf("wander produced only %v of spread against a %v amplitude", spread, cfg.DelayWander)
	}
	// The point of the distinction: this is delay variation, not reordering.
	if reordered > 25 {
		t.Fatalf("wander reordered %d of 500 packets; that is jitter's job, not this one", reordered)
	}
}

// The per-source policer must be sized from its own rate. Inheriting the
// aggregate path's queue gave each source a bucket sized for the whole link --
// at 400 Mbit/s aggregate and 25 Mbit/s per source, three seconds of buffering,
// which is a deep buffer rather than a policer.
func TestPerFlowPolicerBucketFollowsItsOwnRate(t *testing.T) {
	relay, err := New("127.0.0.1:0", "127.0.0.1:1", Config{
		OneWayDelay:            100 * time.Millisecond,
		RateBytesPerSec:        50_000_000,
		PerFlowRateBytesPerSec: 3_125_000,
	})
	if err != nil {
		t.Fatal(err)
	}
	defer relay.Close()

	aggregate := relay.cfg.QueueBytes
	want := int(float64(aggregate) * float64(relay.cfg.PerFlowRateBytesPerSec) / float64(relay.cfg.RateBytesPerSec))
	if aggregate <= want {
		t.Fatalf("test is not meaningful: aggregate queue %d is not above the per-flow share %d", aggregate, want)
	}
	// Drive one source past the per-flow bucket but well inside the aggregate
	// one, and require that it is policed.
	client, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer client.Close()
	target, err := net.ResolveUDPAddr("udp", relay.LocalAddr())
	if err != nil {
		t.Fatal(err)
	}
	payload := make([]byte, 1200)
	for range 2000 {
		if _, err := client.WriteTo(payload, target); err != nil {
			t.Fatal(err)
		}
	}
	deadline := time.Now().Add(2 * time.Second)
	for time.Now().Before(deadline) {
		if up, _ := relay.Stats(); up.PacketsIn >= 2000 {
			break
		}
		time.Sleep(10 * time.Millisecond)
	}
	up, _ := relay.Stats()
	if up.PacketsDropped == 0 {
		t.Fatalf("a source exceeding its own bucket was not policed: in=%d dropped=%d", up.PacketsIn, up.PacketsDropped)
	}
}

// A path whose erasure never changes cannot express the case a transport most
// needs to survive: a channel that moves under a live flow. The motivating
// incident was exactly that, downstream erasure going from a few percent to
// sixty over an afternoon, so the emulator has to be able to step it.
func TestLossRateChangesUnderALiveFlow(t *testing.T) {
	server := echoServer(t)
	relay, err := New("127.0.0.1:0", server.LocalAddr().String(), Config{Seed: 5})
	if err != nil {
		t.Fatal(err)
	}
	defer relay.Close()

	client, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer client.Close()
	target, err := net.ResolveUDPAddr("udp", relay.LocalAddr())
	if err != nil {
		t.Fatal(err)
	}

	measure := func(packets int) float64 {
		t.Helper()
		before, _ := relay.Stats()
		for range packets {
			if _, err := client.WriteTo([]byte("x"), target); err != nil {
				t.Fatal(err)
			}
		}
		deadline := time.Now().Add(5 * time.Second)
		for time.Now().Before(deadline) {
			if up, _ := relay.Stats(); up.PacketsIn >= before.PacketsIn+uint64(packets) {
				break
			}
			time.Sleep(5 * time.Millisecond)
		}
		after, _ := relay.Stats()
		crossed := after.PacketsIn - before.PacketsIn
		if crossed == 0 {
			t.Fatal("no packets crossed the relay")
		}
		return float64(after.PacketsLost-before.PacketsLost) / float64(crossed)
	}

	if clean := measure(400); clean != 0 {
		t.Fatalf("a path configured with no loss erased %.3f of its packets", clean)
	}

	relay.SetLossRate(0.5, 0)
	if lossy := measure(1200); lossy < 0.35 || lossy > 0.65 {
		t.Fatalf("after asking for 50%% upstream erasure the path erased %.3f", lossy)
	}

	relay.SetLossRate(0, 0)
	if back := measure(600); back != 0 {
		t.Fatalf("after returning to a clean path it still erased %.3f", back)
	}

	// A negative rate means "leave this direction alone", so one direction can
	// be changed without the caller knowing the other.
	relay.SetLossRate(0.5, -1)
	if again := measure(1200); again < 0.35 {
		t.Fatalf("a negative downstream rate disturbed the upstream change: %.3f", again)
	}
	relay.SetLossRate(-1, -1)
	if held := measure(1200); held < 0.35 {
		t.Fatalf("two negative rates changed the erasure: %.3f", held)
	}

	// Out-of-range rates are clamped rather than producing a probability above
	// one, which the Gilbert chain would divide by.
	relay.SetLossRate(2, -1)
	if all := measure(400); all < 0.95 {
		t.Fatalf("a rate above one erased only %.3f", all)
	}
}

// A shaped path has two rates, not one. A short probe drains the bucket and
// measures the line rate; sustained load measures the shaping rate. Emulating
// only the second makes a shaped path indistinguishable from a slower one, and
// the case a bandwidth estimate gets wrong by construction is exactly the gap
// between them.
func TestADeepBucketPassesABurstThenShapes(t *testing.T) {
	server := echoServer(t)
	const (
		shaped = 200_000 // bytes per second
		burst  = 120_000
		packet = 1200
	)
	relay, err := New("127.0.0.1:0", server.LocalAddr().String(), Config{
		RateBytesPerSec: shaped, PolicerRefillPeriod: 8 * time.Millisecond,
		PolicerBurstBytes: burst, Seed: 11,
	})
	if err != nil {
		t.Fatal(err)
	}
	defer relay.Close()

	client, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer client.Close()
	target, err := net.ResolveUDPAddr("udp", relay.LocalAddr())
	if err != nil {
		t.Fatal(err)
	}

	payload := make([]byte, packet)
	// One burst, sent as fast as the socket takes it. A bucket this deep must
	// let most of it through: that is what a burst allowance is.
	const burstPackets = burst / packet
	for range burstPackets {
		if _, err := client.WriteTo(payload, target); err != nil {
			t.Fatal(err)
		}
	}
	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		if up, _ := relay.Stats(); up.PacketsIn >= burstPackets {
			break
		}
		time.Sleep(5 * time.Millisecond)
	}
	afterBurst, _ := relay.Stats()
	if afterBurst.PacketsDropped > burstPackets/4 {
		t.Fatalf("a %d byte bucket dropped %d of a %d packet burst; it is not a burst allowance",
			burst, afterBurst.PacketsDropped, burstPackets)
	}

	// Now sustained load well above the shaping rate. The bucket is empty, so
	// what gets through is the rate rather than the line.
	const sustainedPackets = 2000
	for range sustainedPackets {
		if _, err := client.WriteTo(payload, target); err != nil {
			t.Fatal(err)
		}
	}
	deadline = time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		if up, _ := relay.Stats(); up.PacketsIn >= afterBurst.PacketsIn+sustainedPackets {
			break
		}
		time.Sleep(5 * time.Millisecond)
	}
	end, _ := relay.Stats()
	sustainedDropped := end.PacketsDropped - afterBurst.PacketsDropped
	if sustainedDropped == 0 {
		t.Fatal("sustained load far above the shaping rate was not policed at all")
	}
	// The two regimes have to be visibly different, which is the whole point:
	// a path with only one rate cannot express what a max filter gets wrong.
	burstDropRate := float64(afterBurst.PacketsDropped) / float64(burstPackets)
	sustainedDropRate := float64(sustainedDropped) / float64(sustainedPackets)
	t.Logf("burst dropped %.3f, sustained dropped %.3f", burstDropRate, sustainedDropRate)
	if sustainedDropRate <= burstDropRate {
		t.Fatalf("the bucket shaped the burst as hard as the sustained load (%.3f vs %.3f), "+
			"so there is no burst allowance to drain", burstDropRate, sustainedDropRate)
	}
}

// A path that asks for no burst keeps the shallow bucket that models the live
// policer, so existing campaigns are unaffected.
func TestNoBurstAllowanceKeepsTheShallowBucket(t *testing.T) {
	server := echoServer(t)
	relay, err := New("127.0.0.1:0", server.LocalAddr().String(), Config{
		RateBytesPerSec: 200_000, PolicerRefillPeriod: 8 * time.Millisecond, Seed: 11,
	})
	if err != nil {
		t.Fatal(err)
	}
	defer relay.Close()
	client, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer client.Close()
	target, err := net.ResolveUDPAddr("udp", relay.LocalAddr())
	if err != nil {
		t.Fatal(err)
	}
	payload := make([]byte, 1200)
	const packets = 100
	for range packets {
		if _, err := client.WriteTo(payload, target); err != nil {
			t.Fatal(err)
		}
	}
	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		if up, _ := relay.Stats(); up.PacketsIn >= packets {
			break
		}
		time.Sleep(5 * time.Millisecond)
	}
	up, _ := relay.Stats()
	if up.PacketsDropped == 0 {
		t.Fatal("a shallow bucket passed a 100 packet burst without policing any of it")
	}
}
