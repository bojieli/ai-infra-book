package pathsim_test

import (
	"encoding/binary"
	"fmt"
	"net"
	"sort"
	"sync"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/pathsim"
)

// What to do about a lost voice frame is the datacenter profile's open problem,
// and it is a different problem from the one coding already solves.
//
// A 300KB request is two hundred packets: there is a block to compute parity
// over, and traffic behind a loss to reveal it before a timeout. An 80-byte
// frame sent every 20ms is one packet with neither. Measured on an emulated
// 14% path, that left 4.96% of frames arriving more than a frame interval late
// and a p99 567ms above the floor, while the same transport kept request p99
// within 7% of the median.
//
// Three designs were available and only one of them is cheap. Coding across a
// session's own frames needs a window, which means holding frames back and
// paying the delay on every frame to repair the few that are lost. Coding
// across sessions couples flows that have no other reason to be coupled, and
// makes one session's silence another's parity budget. Sending the frame more
// than once needs no window, no delay and no coupling -- and for a payload of
// eighty bytes the bandwidth is nearly free.
//
// This measures the third against doing nothing, because a design argument
// about a tail should be settled by measuring the tail.

const (
	frameSize    = 80
	frameCadence = 20 * time.Millisecond
	framesPerRun = 400
	frameHdr     = 8
)

// frameEcho reflects each datagram back to its sender, which is what a decoder
// feeding a response stream does.
func frameEcho(t *testing.T) *net.UDPConn {
	t.Helper()
	pc, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	conn := pc.(*net.UDPConn)
	t.Cleanup(func() { _ = conn.Close() })
	go func() {
		buf := make([]byte, 2048)
		for {
			n, from, err := conn.ReadFrom(buf)
			if err != nil {
				return
			}
			_, _ = conn.WriteTo(buf[:n], from)
		}
	}()
	return conn
}

// runFrames sends framesPerRun frames at the cadence, each repeated
// `copies` times back to back, and records when each sequence number first
// came back. Duplicates after the first are discarded, which is what a
// receiver deduplicating on sequence does.
func runFrames(t *testing.T, relayAddr string, copies int) (latencies []float64, lost int) {
	t.Helper()
	conn, err := net.Dial("udp", relayAddr)
	if err != nil {
		t.Fatal(err)
	}
	defer conn.Close()

	var mu sync.Mutex
	sentAt := make(map[uint32]time.Time, framesPerRun)
	seen := make(map[uint32]bool, framesPerRun)
	done := make(chan struct{})

	go func() {
		defer close(done)
		buf := make([]byte, 2048)
		for {
			_ = conn.SetReadDeadline(time.Now().Add(3 * time.Second))
			n, err := conn.Read(buf)
			if err != nil {
				return
			}
			if n < frameHdr {
				continue
			}
			seq := binary.LittleEndian.Uint32(buf[0:4])
			mu.Lock()
			if !seen[seq] {
				if at, ok := sentAt[seq]; ok {
					seen[seq] = true
					latencies = append(latencies, float64(time.Since(at).Microseconds())/1000)
				}
			}
			mu.Unlock()
		}
	}()

	frame := make([]byte, frameSize)
	tick := time.NewTicker(frameCadence)
	defer tick.Stop()
	for i := 0; i < framesPerRun; i++ {
		<-tick.C
		binary.LittleEndian.PutUint32(frame[0:4], uint32(i))
		mu.Lock()
		sentAt[uint32(i)] = time.Now()
		mu.Unlock()
		for c := 0; c < copies; c++ {
			if _, err := conn.Write(frame); err != nil {
				break
			}
		}
	}
	// Let the tail arrive before the reader's deadline ends it.
	time.Sleep(1500 * time.Millisecond)
	<-done

	mu.Lock()
	defer mu.Unlock()
	return latencies, framesPerRun - len(latencies)
}

func quant(v []float64, p float64) float64 {
	if len(v) == 0 {
		return 0
	}
	s := append([]float64(nil), v...)
	sort.Float64s(s)
	return s[int(p*float64(len(s)-1))]
}

// TestFrameRedundancyAgainstTheTail is the experiment that settles the design.
func TestFrameRedundancyAgainstTheTail(t *testing.T) {
	if testing.Short() {
		t.Skip("emulated path, runs for tens of seconds per arm")
	}
	echo := frameEcho(t)
	cfg := pathsim.DCLongHaul()
	// The emulator applies the configured loss in each direction, so a frame
	// and its echo each face it. That is the real case: an audio frame crosses
	// the erasing direction and its acknowledgement crosses back.
	relay, err := pathsim.New("127.0.0.1:0", echo.LocalAddr().String(), cfg)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = relay.Close() })

	type result struct {
		copies  int
		p50     float64
		p90     float64
		p99     float64
		lost    int
		late    int
		samples int
	}
	var results []result
	for _, copies := range []int{1, 2, 3} {
		lat, lost := runFrames(t, relay.LocalAddr(), copies)
		if len(lat) == 0 {
			t.Fatalf("copies=%d: no frame returned", copies)
		}
		floor := quant(lat, 0)
		late := 0
		for _, v := range lat {
			if v > floor+float64(frameCadence.Milliseconds()) {
				late++
			}
		}
		results = append(results, result{
			copies: copies, p50: quant(lat, 0.50), p90: quant(lat, 0.90),
			p99: quant(lat, 0.99), lost: lost, late: late, samples: len(lat),
		})
	}
	t.Logf("%-7s %-9s %-9s %-9s %-9s %-9s %s", "copies", "delivered", "p50_ms", "p90_ms", "p99_ms", "lost", "late(>1 interval)")
	for _, r := range results {
		t.Logf("%-7d %-9s %-9.1f %-9.1f %-9.1f %-9d %d (%.1f%%)",
			r.copies, fmt.Sprintf("%d/%d", r.samples, framesPerRun),
			r.p50, r.p90, r.p99, r.lost, r.late,
			100*float64(r.late)/float64(r.samples))
	}
	// The point of the experiment: over datagrams a frame either arrives in one
	// round trip or does not arrive, so the tail is not lateness, it is loss.
	// One copy on a channel erasing 14% in each direction loses a sixth of
	// them, and the design is only worth its bandwidth if duplication cuts that
	// substantially rather than marginally.
	//
	// The bar is a halving rather than any improvement, because loss counts at
	// this sample size vary by several frames run to run: an assertion that
	// merely required the second arm to be no worse would pass on noise and
	// would pass with duplication removed entirely.
	if results[0].lost < 20 {
		t.Fatalf("the emulated path lost only %d of %d frames, too few for this comparison to mean anything",
			results[0].lost, framesPerRun)
	}
	if results[1].lost*2 >= results[0].lost {
		t.Errorf("two copies lost %d against one copy's %d: not the substantial reduction the design needs",
			results[1].lost, results[0].lost)
	}
	if results[2].lost > results[1].lost {
		t.Errorf("three copies lost %d, more than two copies' %d",
			results[2].lost, results[1].lost)
	}
	// Deduplication has to hold, or the extra copies are counted as extra
	// frames and every figure above is measuring the sender rather than the
	// path.
	for _, r := range results {
		if r.samples > framesPerRun {
			t.Errorf("copies=%d delivered %d of %d frames: duplicates were counted as arrivals",
				r.copies, r.samples, framesPerRun)
		}
	}
	// And the reason to prefer this over a windowed code: it costs no latency.
	// A code that held frames back to compute parity would show up here as a
	// higher median for the arms that carry it.
	if results[1].p50 > results[0].p50+float64(frameCadence.Milliseconds()) {
		t.Errorf("duplication cost %.1fms of median latency, which a windowed code was supposed to be rejected for",
			results[1].p50-results[0].p50)
	}
}
