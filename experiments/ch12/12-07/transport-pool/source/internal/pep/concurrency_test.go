package pep

import (
	"context"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/binary"
	"fmt"
	"io"
	"log/slog"
	"math/big"
	"net"
	"sort"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/baseline"
	"github.com/bojieli/queqiao/internal/pathsim"
)

// The datacenter workload is not one flow. It is hundreds of concurrent
// requests, every one of them latency-critical, and the question this file
// exists to answer is what happens to the slowest of them.
//
// That question cannot be answered by a throughput number or by a single
// flow's completion time, and it is the one the published comparison in
// docs/COMPARISON.md currently loses: SSH p99 under load at 940ms against
// TUIC's 662ms. On an access link that is a caveat, because the bulk transfer
// it competes with is also the thing being won. On a datacenter leg there is
// no bulk transfer -- every flow is a request -- so the tail is not a caveat,
// it is the whole result.
//
// The comparison runs against internal/baseline, which is TUIC's data-path
// shape on the same QUIC fork and the same controllers in the same process, so
// a gap is the design rather than the library.

// requestSize is one inference request: the payload size the datacenter path
// characterisation measured, chosen because it is what an audio upload is.
const requestSize = 300 * 1024

// concurrentFlows is the load. It is large enough that flows contend and small
// enough that a laptop can run it; the shape of the tail, not its absolute
// value, is what transfers to a real gateway.
const concurrentFlows = 48

type latencies []time.Duration

func (l latencies) quantile(p float64) time.Duration {
	if len(l) == 0 {
		return 0
	}
	s := append(latencies(nil), l...)
	sort.Slice(s, func(i, j int) bool { return s[i] < s[j] })
	i := int(p * float64(len(s)-1))
	return s[i]
}

func (l latencies) report(t *testing.T, name string) {
	t.Helper()
	if len(l) == 0 {
		t.Fatalf("%s: no flow completed", name)
	}
	p50, p99 := l.quantile(0.50), l.quantile(0.99)
	ratio := float64(p99) / float64(p50)
	t.Logf("%-22s n=%3d p50=%7.1fms p90=%7.1fms p99=%7.1fms  p99/p50=%.2f",
		name, len(l),
		float64(p50.Microseconds())/1000,
		float64(l.quantile(0.90).Microseconds())/1000,
		float64(p99.Microseconds())/1000, ratio)
}

// echoServer answers each request with a single byte once it has the whole
// thing, which is the request/response shape and makes completion something
// the peer confirms rather than something the sender's socket reports.
func echoServer(t *testing.T) net.Listener {
	t.Helper()
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = ln.Close() })
	go func() {
		for {
			c, err := ln.Accept()
			if err != nil {
				return
			}
			go func(c net.Conn) {
				defer c.Close()
				if _, err := io.CopyN(io.Discard, c, requestSize); err != nil {
					return
				}
				_, _ = c.Write([]byte{1})
			}(c)
		}
	}()
	return ln
}

// driveConcurrent opens every flow at once through the SOCKS listener and
// returns how long each took from dial to acknowledgement.
//
// They start together on purpose. Staggering them would measure a queue that
// never forms, and the case the datacenter profile has to survive is a gateway
// whose sessions all speak at once because their users did.
func driveConcurrent(t *testing.T, socksAddr string, destination net.Listener, n int) latencies {
	t.Helper()
	payload := make([]byte, requestSize)
	if _, err := rand.Read(payload[:1024]); err != nil {
		t.Fatal(err)
	}
	var mu sync.Mutex
	var out latencies
	var wg sync.WaitGroup
	start := make(chan struct{})
	for i := 0; i < n; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			<-start
			began := time.Now()
			conn, err := trySocksDial(socksAddr, destination, 120*time.Second)
			if err != nil {
				return
			}
			defer conn.Close()
			if _, err := conn.Write(payload); err != nil {
				return
			}
			ack := make([]byte, 1)
			_ = conn.SetReadDeadline(time.Now().Add(120 * time.Second))
			if _, err := io.ReadFull(conn, ack); err != nil {
				return
			}
			mu.Lock()
			out = append(out, time.Since(began))
			mu.Unlock()
		}()
	}
	close(start)
	wg.Wait()
	return out
}

// TestTailUnderConcurrentRequests is the Phase 6 gate of the datacenter plan.
//
// It is skipped in short mode because it runs a hundred flows across an
// emulated 200ms path, and it reports rather than asserts a threshold: the
// number that matters is the gap to the reference, and pinning an absolute
// millisecond figure to a shared CI machine would produce a test that fails
// for reasons having nothing to do with the transport.
// TestConcurrencyHarnessWorksAtOne verifies both arms before either is
// believed at load. An arm that completes nothing under concurrency and an arm
// that was never wired correctly are indistinguishable in the result, and only
// one of them is a finding.
func TestConcurrencyHarnessWorksAtOne(t *testing.T) {
	if testing.Short() {
		t.Skip("brings up two transports across an emulated path")
	}
	clean := pathsim.DCLongHaulClean()
	if got := measureBaselineTailN(t, clean, 1); len(got) != 1 {
		t.Fatalf("the reference arm completed %d of 1 flow on a clean path: the harness is wrong, not the transport", len(got))
	} else {
		got.report(t, "reference @1 clean")
	}
	// Separating the two variables matters. An arm that fails at concurrency
	// on a lossy path has told us nothing until we know whether it fails at
	// one flow on the same path.
	lossy := pathsim.DCLongHaul()
	got := measureBaselineTailN(t, lossy, 1)
	if len(got) == 0 {
		t.Log("reference @1 lossy: no flow completed -- the 14% erasure alone defeats it, before any concurrency")
	} else {
		got.report(t, "reference @1 lossy")
	}
	qq := measureQueqiaoTailN(t, lossy, 1)
	if len(qq) == 0 {
		t.Log("queqiao @1 lossy: no flow completed")
	} else {
		qq.report(t, "queqiao   @1 lossy")
	}
}

func TestTailUnderConcurrentRequests(t *testing.T) {
	if testing.Short() {
		t.Skip("concurrent tail measurement is slow by construction")
	}
	path := pathsim.DCLongHaul()

	// A sweep rather than a single load. One point tells you whether an arm
	// survived a number somebody picked; a curve tells you where it stops
	// surviving, and the shape between those points is the scheduling
	// behaviour this gate exists to examine.
	for _, n := range []int{1, 4, 16, 48} {
		qq := measureQueqiaoTailN(t, path, n)
		ref := measureBaselineTailN(t, path, n)
		t.Logf("--- %d concurrent 300KB requests ---", n)
		reportOrSilence(t, fmt.Sprintf("queqiao   @%d", n), qq, n)
		reportOrSilence(t, fmt.Sprintf("reference @%d", n), ref, n)
	}
}

// reportOrSilence prints the distribution, or says plainly that flows did not
// finish. Completion rate is part of the result: an arm that abandons flows has
// a better tail for the worst possible reason, and averaging over only the
// survivors would hide it.
func reportOrSilence(t *testing.T, name string, l latencies, want int) {
	t.Helper()
	if len(l) == 0 {
		t.Logf("%-22s completed 0/%d", name, want)
		return
	}
	p50, p99 := l.quantile(0.50), l.quantile(0.99)
	t.Logf("%-22s %d/%d  p50=%7.1fms p90=%7.1fms p99=%7.1fms  p99/p50=%.2f",
		name, len(l), want,
		float64(p50.Microseconds())/1000,
		float64(l.quantile(0.90).Microseconds())/1000,
		float64(p99.Microseconds())/1000, float64(p99)/float64(p50))
}

func measureQueqiaoTail(t *testing.T, path pathsim.Config) latencies {
	return measureQueqiaoTailN(t, path, concurrentFlows)
}

func measureQueqiaoTailN(t *testing.T, path pathsim.Config, n int) latencies {
	t.Helper()
	socks, destination := codedPairWith(t, true, &path, func(ln net.Listener) {
		for {
			c, err := ln.Accept()
			if err != nil {
				return
			}
			go func(c net.Conn) {
				defer c.Close()
				if _, err := io.CopyN(io.Discard, c, requestSize); err != nil {
					return
				}
				_, _ = c.Write([]byte{1})
			}(c)
		}
	})
	return driveConcurrent(t, socks, destination, n)
}

// measureBaselineTail runs the same load across the same emulated path through
// the TUIC-shaped reference.
func measureBaselineTail(t *testing.T, path pathsim.Config) latencies {
	return measureBaselineTailN(t, path, concurrentFlows)
}

func measureBaselineTailN(t *testing.T, path pathsim.Config, n int) latencies {
	t.Helper()
	destination := echoServer(t)

	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	token := make([]byte, 32)
	if _, err := rand.Read(token); err != nil {
		t.Fatal(err)
	}
	packet, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = packet.Close() })

	cert, pool := baselineIdentity(t)
	server, err := baseline.NewServer(baseline.ServerConfig{
		ListenAddr: "127.0.0.1:0", Certificate: cert,
		Token: token, Logger: logger,
	})
	if err != nil {
		t.Skipf("baseline server unavailable: %v", err)
	}
	relay, err := pathsim.New("127.0.0.1:0", packet.LocalAddr().String(), path)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = relay.Close() })

	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = listener.Close() })
	client, err := baseline.NewClient(baseline.ClientConfig{
		ListenAddr: listener.Addr().String(), RemoteAddr: relay.LocalAddr(),
		ServerName: "queqiao.test", RootCAs: pool,
		Token: token, Logger: logger,
	})
	if err != nil {
		t.Skipf("baseline client unavailable: %v", err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	t.Cleanup(cancel)
	go func() { _ = server.Serve(ctx, packet) }()
	go func() { _ = client.ServeListener(ctx, listener) }()

	return driveConcurrent(t, listener.Addr().String(), destination, n)
}

// The reference takes a tls.Certificate and an *x509.CertPool where queqiao
// takes its own credential types, so the harness issues one identity for the
// reference arm and reuses it. Both arms then present a certificate of the
// same shape, which matters because handshake size is not the variable under
// test.
var (
	baselineOnce sync.Once
	baselineCert tls.Certificate
	baselinePool *x509.CertPool
	baselineErr  error
)

func baselineIdentity(t *testing.T) (tls.Certificate, *x509.CertPool) {
	t.Helper()
	baselineOnce.Do(func() {
		key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
		if err != nil {
			baselineErr = err
			return
		}
		serial, err := rand.Int(rand.Reader, new(big.Int).Lsh(big.NewInt(1), 128))
		if err != nil {
			baselineErr = err
			return
		}
		template := x509.Certificate{
			SerialNumber:          serial,
			Subject:               pkix.Name{CommonName: "queqiao.test"},
			DNSNames:              []string{"queqiao.test"},
			NotBefore:             time.Now().Add(-time.Hour),
			NotAfter:              time.Now().Add(24 * time.Hour),
			KeyUsage:              x509.KeyUsageDigitalSignature | x509.KeyUsageCertSign,
			ExtKeyUsage:           []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
			IsCA:                  true,
			BasicConstraintsValid: true,
		}
		der, err := x509.CreateCertificate(rand.Reader, &template, &template, &key.PublicKey, key)
		if err != nil {
			baselineErr = err
			return
		}
		leaf, err := x509.ParseCertificate(der)
		if err != nil {
			baselineErr = err
			return
		}
		baselineCert = tls.Certificate{Certificate: [][]byte{der}, PrivateKey: key, Leaf: leaf}
		baselinePool = x509.NewCertPool()
		baselinePool.AddCert(leaf)
	})
	if baselineErr != nil {
		t.Fatalf("baseline identity: %v", baselineErr)
	}
	return baselineCert, baselinePool
}

// The other traffic shape. A voice session sends a 20ms frame of audio fifty
// times a second, and a gateway carries hundreds of them at once. Nothing
// about that resembles the burst measured above: the payloads are tens of
// bytes rather than hundreds of kilobytes, the flow never ends, and what
// matters is not when it completes but whether any single frame arrives late.
//
// The mechanisms it stresses are different too. A burst is a rate problem; a
// frame stream is a scheduling and head-of-line problem, where one lost packet
// can hold up a session that had nothing to do with it.
const (
	frameBytes    = 80
	frameInterval = 20 * time.Millisecond
	framesPerFlow = 100 // two seconds of speech
	voiceSessions = 24
	// pathRoundTrip is what pathsim.DCLongHaul emulates, and the floor no
	// frame can beat.
	pathRoundTrip = 200 * time.Millisecond
)

// TestFrameLatencyUnderConcurrentSessions measures the other half of §2.3.
//
// It reports the distribution of per-frame round trips rather than a
// completion time, because a session that finishes on schedule while a tenth
// of its frames arrived 400ms late is a session the listener heard break up.
func TestFrameLatencyUnderConcurrentSessions(t *testing.T) {
	if testing.Short() {
		t.Skip("brings up a transport across an emulated path")
	}
	path := pathsim.DCLongHaul()
	socks, destination := codedPairWith(t, true, &path, echoFrames)

	var mu sync.Mutex
	var all latencies
	var late int
	var wg sync.WaitGroup
	start := make(chan struct{})
	for i := 0; i < voiceSessions; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			<-start
			conn, err := trySocksDial(socks, destination, 120*time.Second)
			if err != nil {
				return
			}
			defer conn.Close()
			frame := make([]byte, frameBytes)
			reply := make([]byte, frameBytes)
			ticker := time.NewTicker(frameInterval)
			defer ticker.Stop()
			for f := 0; f < framesPerFlow; f++ {
				<-ticker.C
				sent := time.Now()
				if _, err := conn.Write(frame); err != nil {
					return
				}
				_ = conn.SetReadDeadline(time.Now().Add(10 * time.Second))
				if _, err := io.ReadFull(conn, reply); err != nil {
					return
				}
				rtt := time.Since(sent)
				mu.Lock()
				all = append(all, rtt)
				// Lateness has to be measured against the path, not against
				// the frame interval. Every frame on a 200ms path takes at
				// least 200ms, so counting anything above one interval counts
				// all of them and distinguishes nothing. What a jitter buffer
				// actually has to absorb is the spread above the path's own
				// minimum, and a frame more than one interval above it has
				// displaced the frame behind it.
				if rtt > pathRoundTrip+frameInterval {
					late++
				}
				mu.Unlock()
			}
		}()
	}
	close(start)
	wg.Wait()

	if len(all) == 0 {
		t.Fatal("no frame completed a round trip")
	}
	p50, p99 := all.quantile(0.50), all.quantile(0.99)
	t.Logf("%d sessions x %d frames: %d delivered, p50=%.1fms p90=%.1fms p99=%.1fms p99.9=%.1fms",
		voiceSessions, framesPerFlow, len(all),
		float64(p50.Microseconds())/1000,
		float64(all.quantile(0.90).Microseconds())/1000,
		float64(p99.Microseconds())/1000,
		float64(all.quantile(0.999).Microseconds())/1000)
	t.Logf("frames more than one interval above the path's own round trip: %d of %d (%.2f%%)",
		late, len(all), 100*float64(late)/float64(len(all)))
	// The path's own round trip is 200ms, so a frame cannot beat that and the
	// interesting quantity is how far above it the tail sits.
	t.Logf("p99 above the path's round trip: %.1fms", float64((p99-200*time.Millisecond).Microseconds())/1000)
}

// echoFrames returns each frame as it arrives, which is what a decoder feeding
// a response stream does.
func echoFrames(ln net.Listener) {
	for {
		c, err := ln.Accept()
		if err != nil {
			return
		}
		go func(c net.Conn) {
			defer c.Close()
			buf := make([]byte, frameBytes)
			for {
				if _, err := io.ReadFull(c, buf); err != nil {
					return
				}
				if _, err := c.Write(buf); err != nil {
					return
				}
			}
		}(c)
	}
}

// A session has to keep its repair after it crosses the byte cutoff, which is
// where the old rule silently withdrew it.
//
// codedFlowBytes is 256KB. A voice call at four kilobytes a second reaches
// that after about a minute, and before this was fixed it then carried the
// rest of itself uncoded: the cutoff was written for a transfer, where round
// trips amortise over many bytes, and applied to a session, where every lost
// message pays a full round trip by itself.
//
// The messages here are 600 bytes at 50Hz, thirty kilobytes a second, so the
// flow crosses the cutoff in about nine seconds instead of a minute. The rate
// is still well inside what a conversation looks like.
func TestASessionKeepsItsRepairPastTheByteCutoff(t *testing.T) {
	if testing.Short() {
		t.Skip("runs a session across an emulated path for long enough to cross the cutoff")
	}
	const (
		// A real voice frame at a real cadence: four kilobytes a second, which
		// is nowhere near the rate separating a conversation from a transfer.
		msgSize  = 80
		cadence  = 20 * time.Millisecond
		messages = 2600 // 52 seconds of speech, past the cutoff with room after
	)
	path := pathsim.DCLongHaul()
	socks, destination := codedPairWith(t, true, &path, func(ln net.Listener) {
		for {
			c, err := ln.Accept()
			if err != nil {
				return
			}
			go func(c net.Conn) {
				defer c.Close()
				buf := make([]byte, msgSize)
				for {
					if _, err := io.ReadFull(c, buf); err != nil {
						return
					}
					if _, err := c.Write(buf); err != nil {
						return
					}
				}
			}(c)
		}
	})

	conn, err := trySocksDial(socks, destination, 120*time.Second)
	if err != nil {
		t.Fatalf("dial: %v", err)
	}
	defer conn.Close()

	// Sending and receiving run apart. A voice stream does not hold the next
	// frame until the last one is acknowledged, and a test that does is
	// clocked by the round trip rather than by the cadence: at 208ms per
	// exchange it sends five frames a second instead of fifty and never
	// reaches the byte volume it was written to cross.
	var mu sync.Mutex
	sentAt := make(map[uint32]time.Time, messages)
	var beforeCutoff, afterCutoff latencies
	done := make(chan struct{})

	go func() {
		defer close(done)
		buf := make([]byte, msgSize)
		for {
			_ = conn.SetReadDeadline(time.Now().Add(30 * time.Second))
			if _, err := io.ReadFull(conn, buf); err != nil {
				return
			}
			seq := binary.LittleEndian.Uint32(buf[:4])
			mu.Lock()
			at, ok := sentAt[seq]
			if ok {
				rtt := float64(time.Since(at).Microseconds()) / 1000
				// Each message costs msgSize in each direction.
				if int(seq)*msgSize*2 < codedFlowBytes {
					beforeCutoff = append(beforeCutoff, time.Duration(rtt*float64(time.Millisecond)))
				} else {
					afterCutoff = append(afterCutoff, time.Duration(rtt*float64(time.Millisecond)))
				}
			}
			mu.Unlock()
		}
	}()

	msg := make([]byte, msgSize)
	tick := time.NewTicker(cadence)
	defer tick.Stop()
	for i := 0; i < messages; i++ {
		<-tick.C
		binary.LittleEndian.PutUint32(msg[:4], uint32(i))
		mu.Lock()
		sentAt[uint32(i)] = time.Now()
		mu.Unlock()
		if _, err := conn.Write(msg); err != nil {
			break
		}
	}
	time.Sleep(2 * time.Second) // let the tail come back
	conn.Close()
	<-done

	mu.Lock()
	before, after := beforeCutoff, afterCutoff
	mu.Unlock()
	if len(before) == 0 || len(after) == 0 {
		t.Fatalf("the session did not straddle the cutoff: %d before, %d after",
			len(before), len(after))
	}
	before.report(t, "before cutoff")
	after.report(t, "after cutoff")
	// The class is the mechanism and the sharp assertion. A session demoted to
	// bulk stops preferring coding, and on this path that is the difference
	// between repairing a lost frame inside the round trip that carried it and
	// waiting out a timeout. The latency below is reported rather than
	// asserted, because the frame tail on an ordered stream is bad throughout
	// -- that is a separate problem, and averaging the two together would let
	// either one hide the other.
	if reg := lastClientMetrics; reg != nil {
		snap := reg.Snapshot()
		t.Logf("class transitions: interactive=%d bulk=%d",
			snap.ClassTransitions[1], snap.ClassTransitions[2])
		// Whether the coded substrate was used at all, which is a different
		// question from whether the flow was allowed to use it.
		t.Logf("coded: sources=%d recovered=%d lost=%d receive_erasure=%.4f",
			snap.QUICCodedSources, snap.QUICCodedRecovered,
			snap.QUICCodedLost, snap.ReceiveErasure())
		if snap.ClassTransitions[2] > 0 {
			t.Errorf("the session was demoted to bulk after carrying %d bytes; "+
				"a call longer than a minute loses its repair exactly where it needs it",
				messages*msgSize*2)
		}
	}
	t.Logf("p99 before the cutoff %v, after %v", before.quantile(0.99), after.quantile(0.99))
}

// tokenStreamBytes is what one generated token weighs on the wire once it is
// wrapped in the event framing a model server uses.
const (
	tokenStreamBytes    = 48
	tokenStreamInterval = 30 * time.Millisecond
	tokensPerStream     = 200
)

// serveTokensAndSink answers two kinds of connection on one listener. A client
// that writes a byte gets a token stream; a client that writes nothing gets its
// bytes swallowed as fast as they arrive.
//
// One listener rather than two because the point is contention: both flows have
// to cross the same emulated path, through the same transport, at the same
// time.
func serveTokensAndSink(ln net.Listener) {
	for {
		c, err := ln.Accept()
		if err != nil {
			return
		}
		go func(c net.Conn) {
			defer c.Close()
			kind := make([]byte, 1)
			if _, err := io.ReadFull(c, kind); err != nil {
				return
			}
			if kind[0] != 's' {
				_, _ = io.Copy(io.Discard, c)
				return
			}
			token := make([]byte, tokenStreamBytes)
			ticker := time.NewTicker(tokenStreamInterval)
			defer ticker.Stop()
			for range tokensPerStream {
				<-ticker.C
				if _, err := c.Write(token); err != nil {
					return
				}
			}
		}(c)
	}
}

// readTokenLateness consumes a stream and reports how far behind the
// generator's own cadence each token arrived, measured from the first one so
// that the path's fixed delay cancels.
func readTokenLateness(t *testing.T, socks string, destination net.Listener) []time.Duration {
	t.Helper()
	conn, err := trySocksDial(socks, destination, 120*time.Second)
	if err != nil {
		return nil
	}
	defer conn.Close()
	if _, err := conn.Write([]byte{'s'}); err != nil {
		return nil
	}
	buf := make([]byte, tokenStreamBytes)
	var first time.Time
	var out []time.Duration
	for i := range tokensPerStream {
		_ = conn.SetReadDeadline(time.Now().Add(20 * time.Second))
		if _, err := io.ReadFull(conn, buf); err != nil {
			break
		}
		now := time.Now()
		if i == 0 {
			first = now
			continue
		}
		out = append(out, now.Sub(first)-time.Duration(i)*tokenStreamInterval)
	}
	return out
}

// A checkpoint pull beside a model answering.
//
// This question could not be measured on the live path. The stream got worse
// throughout the experiment whether or not a transfer was running, so the run
// with the transfer was not evidence that the transfer cost anything: the arm
// measured last was the worst one, and it was the arm with no transfer in it.
// A drift that runs one way for the length of the experiment is not something
// order alternation can remove.
//
// Here the channel holds still, so the difference between the arms is the
// transfer.
func TestATransferBesideATokenStream(t *testing.T) {
	if testing.Short() {
		t.Skip("brings up a transport across an emulated path")
	}
	// The measured path's knee is 333 Mbit/s, which a userspace transport on
	// loopback cannot fill, so at that rate the transfer and the stream would
	// never actually compete and this test would pass without asking anything.
	// Narrowing the bottleneck is what makes the question real.
	path := pathsim.DCLongHaul()
	path.RateBytesPerSec = 20 * 1000 * 1000 / 8
	socks, destination := codedPairWith(t, true, &path, serveTokensAndSink)

	alone := readTokenLateness(t, socks, destination)
	if len(alone) < tokensPerStream/2 {
		t.Skipf("only %d tokens arrived without a transfer; the harness is not "+
			"healthy enough to measure contention", len(alone))
	}

	stop := make(chan struct{})
	var moved atomic.Uint64
	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		conn, err := trySocksDial(socks, destination, 120*time.Second)
		if err != nil {
			return
		}
		defer conn.Close()
		if _, err := conn.Write([]byte{'b'}); err != nil {
			return
		}
		block := make([]byte, 64<<10)
		for {
			select {
			case <-stop:
				return
			default:
			}
			n, err := conn.Write(block)
			moved.Add(uint64(n))
			if err != nil {
				return
			}
		}
	}()
	// Long enough that the transfer is established and moving before the
	// stream starts, rather than ramping through the measurement.
	time.Sleep(2 * time.Second)
	before := moved.Load()
	start := time.Now()
	beside := readTokenLateness(t, socks, destination)
	elapsed := time.Since(start)
	close(stop)
	wg.Wait()

	// A transfer that was not using the path did not contend for it, and a
	// stream that stayed fast beside it has not been shown anything.
	offered := float64(moved.Load()-before) * 8 / elapsed.Seconds() / 1e6
	t.Logf("transfer offered %.1f Mbit/s against a %.0f Mbit/s bottleneck",
		offered, float64(path.RateBytesPerSec)*8/1e6)
	if offered < float64(path.RateBytesPerSec)*8/1e6/4 {
		t.Skipf("the transfer only reached %.1f Mbit/s, so it never competed for the "+
			"bottleneck and this run says nothing about contention", offered)
	}

	if len(beside) < tokensPerStream/2 {
		t.Fatalf("only %d of %d tokens arrived while a transfer ran; the transfer is "+
			"not sharing the path, it is taking it", len(beside), tokensPerStream)
	}

	sort.Slice(alone, func(i, j int) bool { return alone[i] < alone[j] })
	sort.Slice(beside, func(i, j int) bool { return beside[i] < beside[j] })
	q := func(v []time.Duration, p float64) time.Duration {
		return v[int(p*float64(len(v)-1))]
	}
	t.Logf("alone:  p50=%v p90=%v p99=%v (n=%d)", q(alone, 0.5), q(alone, 0.9), q(alone, 0.99), len(alone))
	t.Logf("beside: p50=%v p90=%v p99=%v (n=%d)", q(beside, 0.5), q(beside, 0.9), q(beside, 0.99), len(beside))

	// The bar is the tail, because a reader notices a stall and does not notice
	// a millisecond. Held loosely: what must not happen is a transfer turning a
	// stream into something that stutters, and a factor of four on the p99 of a
	// 30ms cadence is that.
	if got, want := q(beside, 0.99), 4*q(alone, 0.99)+time.Second; got > want {
		t.Fatalf("a transfer beside the stream took its p99 lateness from %v to %v; "+
			"the transfer is not being kept out of the stream's way",
			q(alone, 0.99), got)
	}
}
