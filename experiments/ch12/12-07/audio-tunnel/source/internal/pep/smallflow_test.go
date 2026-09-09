package pep

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net"
	"sort"
	"strings"
	"testing"
	"time"

	"github.com/apernet/quic-go"
	"github.com/bojieli/queqiao/internal/classifier"
	"github.com/bojieli/queqiao/internal/metrics"
	"github.com/bojieli/queqiao/internal/multipath"
	"github.com/bojieli/queqiao/internal/pathmodel"
	"github.com/bojieli/queqiao/internal/pathsim"
	"github.com/bojieli/queqiao/internal/protocol"
	"github.com/bojieli/queqiao/internal/stripe"
)

// requestResponse serves a destination that answers each small request with a
// small response, which is what an interactive flow actually looks like.
func requestResponse(size int) func(net.Listener) {
	return func(listener net.Listener) {
		for {
			conn, err := listener.Accept()
			if err != nil {
				return
			}
			go func(c net.Conn) {
				defer c.Close()
				buf := make([]byte, 16)
				reply := make([]byte, size)
				for {
					if _, err := io.ReadFull(c, buf); err != nil {
						return
					}
					if _, err := c.Write(reply); err != nil {
						return
					}
				}
			}(conn)
		}
	}
}

func median(samples []time.Duration) time.Duration {
	if len(samples) == 0 {
		return 0
	}
	sorted := append([]time.Duration(nil), samples...)
	sort.Slice(sorted, func(i, j int) bool { return sorted[i] < sorted[j] })
	return sorted[len(sorted)/2]
}

func TestTrackingReconcilesAnAcknowledgementWhichArrivedFirst(t *testing.T) {
	flow := &multipathFlow{ackTrack: newAckTracker()}
	chunk := &stripe.Chunk{Offset: 8, Data: []byte("ack-first")}
	flow.ackTrack.Add([][2]uint64{{chunk.Offset, chunk.End()}})

	flow.ackTrack.mu.Lock()
	before := flow.ackTrack.gen
	flow.ackTrack.mu.Unlock()
	flow.trackChunk(1, chunk)
	flow.ackTrack.mu.Lock()
	after := flow.ackTrack.gen
	flow.ackTrack.mu.Unlock()

	if after != before+1 {
		t.Fatalf("tracking an already acknowledged chunk advanced generation %d -> %d, want one reconciliation", before, after)
	}
}

// A small request and its small reply are the case an erasure channel treats
// worst. Three packets at 42% loss means three quarters of exchanges lose one,
// and with nothing behind it to trigger a fast retransmit the recovery is a
// probe timeout -- a round trip, then another if the probe is lost too.
//
// Coding repairs that without a round trip, but only if the path is known to
// erase before the exchange starts, because a block sealed knowing nothing
// carries no parity. Both halves run on one connection, so the only thing that
// differs between them is what is known.
func TestSmallExchangesAreRepairedOnceThePathIsKnown(t *testing.T) {
	if testing.Short() {
		t.Skip("brings up QUIC across an emulated 300 ms path")
	}
	requireStableImpairmentClock(t)
	const oneWay = 150 * time.Millisecond
	loopback := &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1), Port: 0}
	key := pathKey(loopback, loopback)
	// Every pair in this process reaches loopback by loopback, so they share
	// one path key. Start from nothing so the first half really is blind.
	pathmodel.Forget(key)
	t.Cleanup(func() { pathmodel.Forget(key) })

	path := pathsim.Config{
		OneWayDelay: oneWay, RateBytesPerSec: uint64(25e6 / 8),
		PolicerRefillPeriod: 8 * time.Millisecond, LossRate: 0.42, Seed: 41,
	}
	socks, destination := codedPairWith(t, true, &path, requestResponse(2700))
	// A connection to a path that erases 42% of packets is sometimes simply
	// lost, which is the path and not a defect. This measures what exchanges
	// cost once a flow exists, so it is worth another attempt to get one.
	conn := dialWithRetries(t, socks, destination, 3)
	defer conn.Close()

	// Each exchange gets its own deadline, and each batch its own budget.
	// The flow used to run under the single deadline its dial had set, which
	// covered the setup, the blind half and the measured half together -- so
	// the two halves and the handshake competed for one 90-second budget on a
	// path where the handshake alone can cost tens of seconds. When the blind
	// half was slow the measured half never ran, and the test failed at
	// whichever exchange happened to be in flight: two runs in eight, always
	// at exactly 90 s, always before reaching the thing it asserts.
	//
	// A budget is not a bound on what is being measured. 30 s is a hundred
	// round trips, so an exchange that hits it has stalled rather than been
	// cut short, and a batch that hits its own has already said what it had
	// to say.
	const perExchange = 30 * time.Second
	exchange := func(n int, budget time.Duration) []time.Duration {
		var samples []time.Duration
		request, reply := make([]byte, 16), make([]byte, 2700)
		until := time.Now().Add(budget)
		for i := 0; i < n; i++ {
			// Checked before rather than after, so the budget decides
			// whether another exchange starts and never truncates one that
			// is already running. A batch always takes at least one sample.
			if i > 0 && time.Now().After(until) {
				break
			}
			if err := conn.SetDeadline(time.Now().Add(perExchange)); err != nil {
				t.Fatal(err)
			}
			start := time.Now()
			if _, err := conn.Write(request); err != nil {
				t.Fatal(err)
			}
			if _, err := io.ReadFull(conn, reply); err != nil {
				t.Fatalf("exchange %d of %d: %v", i, n, err)
			}
			samples = append(samples, time.Since(start))
		}
		return samples
	}

	// The blind half is logged, not asserted, and it is the expensive one:
	// every loss it takes waits out a probe timeout, which is the whole point
	// of it. Its first exchange alone can cost twenty seconds, because a flow
	// is answered as soon as its open is queued and on this path that open is
	// often lost. So the budget has to be several times that or it reports
	// one outlier as a median, and it is a wall clock rather than a count so
	// that the cost of the case being demonstrated does not become the cost
	// of the test. What makes the measured half fast is the seeding below,
	// not the number of exchanges before it.
	blindSamples := exchange(10, time.Minute)
	blind := median(blindSamples)
	// What the endpoint pair is already known to erase. A long-lived proxy
	// learns this from its own traffic or from the prewarm; only the floor is
	// seeded, because a delivered rate would also claim a share of the
	// bottleneck and that is a different experiment.
	pathmodel.Shared(key).Report(99, pathmodel.Observation{Erasure: 0.42, BurstFactor: 1, ObservedSamples: 5000, Delivered: 0, RoundTrip: 0})
	knowingSamples := exchange(10, time.Minute)
	knowing := median(knowingSamples)

	roundTrip := 2 * oneWay
	t.Logf("median exchange: %v over %d when the path is unknown, %v over %d once it is "+
		"known (round trip %v)", blind.Round(time.Millisecond), len(blindSamples),
		knowing.Round(time.Millisecond), len(knowingSamples), roundTrip)

	// What matters is the absolute cost, not that seeding the model improved
	// it. The two halves share a connection, and the controller measures the
	// floor from its own acknowledgements as it goes -- so by the time the
	// blind half has run a few exchanges the path is no longer unknown, and
	// the first half can be as fast as the second. That is the code working
	// sooner than the test can arrange for it not to, and asserting an
	// improvement makes a better result look like a worse one.
	//
	// A repair costs no round trip; a probe timeout costs at least one more.
	// Half a round trip of slack separates them by a wide margin.
	if knowing > roundTrip*3/2 {
		t.Errorf("a small exchange cost %v against a round trip of %v, so it is "+
			"being repaired by a probe timeout rather than by the code",
			knowing.Round(time.Millisecond), roundTrip)
	}
	if knowing > blind+roundTrip/2 {
		t.Errorf("knowing the path gave %v against %v when blind; knowing it "+
			"cannot make an exchange slower", knowing.Round(time.Millisecond),
			blind.Round(time.Millisecond))
	}
}

// A refused destination and a lost attempt are different answers, and only one
// of them is worth asking again.
//
// The peer answering "I could not reach that" has told the application
// something true; asking again only delays it. A path that lost the asking has
// told it nothing, and reporting that as an unreachable destination is a lie
// about the destination -- the application's own retry costs a fresh TCP
// connection and a fresh SOCKS negotiation for something this layer could have
// tried again itself.
func TestOnlyALostAttemptIsRetried(t *testing.T) {
	client := &Client{cfg: ClientConfig{Logger: slog.New(slog.NewTextHandler(io.Discard, nil))}}
	client.flowOpenRetryDelayForTest = func(int) time.Duration { return 0 }

	attempts := 0
	client.openFlowForTest = func() (*openedFlow, error) {
		attempts++
		return nil, errDestinationUnavailable
	}
	if _, err := client.openFlowWithRetries(context.Background(), "example.test:80"); err == nil {
		t.Fatal("a refused destination was reported as success")
	}
	if attempts != 1 {
		t.Fatalf("a refused destination was asked %d times, want 1", attempts)
	}

	attempts = 0
	client.openFlowForTest = func() (*openedFlow, error) {
		attempts++
		return nil, peerResponse(errors.New("server rejected protocol operation"))
	}
	if _, err := client.openFlowWithRetries(context.Background(), "example.test:80"); err == nil {
		t.Fatal("a protocol rejection was reported as success")
	}
	if attempts != 1 {
		t.Fatalf("a protocol rejection was asked %d times, want 1", attempts)
	}

	attempts = 0
	client.openFlowForTest = func() (*openedFlow, error) {
		attempts++
		return nil, errors.New("quic lane: context deadline exceeded")
	}
	if _, err := client.openFlowWithRetries(context.Background(), "example.test:80"); err == nil {
		t.Fatal("a lost attempt was reported as success")
	}
	if attempts != flowOpenAttempts {
		t.Fatalf("a lost attempt was asked %d times, want %d", attempts, flowOpenAttempts)
	}

	// And a path that loses the first attempt but not the second must not cost
	// the application anything at all.
	attempts = 0
	client.openFlowForTest = func() (*openedFlow, error) {
		if attempts++; attempts == 1 {
			return nil, errors.New("quic lane: context deadline exceeded")
		}
		return &openedFlow{}, nil
	}
	if _, err := client.openFlowWithRetries(context.Background(), "example.test:80"); err != nil {
		t.Fatalf("a path that lost one attempt failed the flow: %v", err)
	}
}

func TestFlowOpenRetryUsesJitteredExponentialWindows(t *testing.T) {
	for attempt, bounds := range map[int][2]time.Duration{
		1: {250 * time.Millisecond, 500 * time.Millisecond},
		2: {500 * time.Millisecond, time.Second},
	} {
		for range 100 {
			delay := flowOpenRetryDelay(attempt)
			if delay < bounds[0] || delay > bounds[1] {
				t.Fatalf("attempt %d delay = %v, want %v..%v", attempt, delay, bounds[0], bounds[1])
			}
		}
	}
}

func TestFlowOpenRetryBackoffHonorsCancellation(t *testing.T) {
	client := &Client{cfg: ClientConfig{Logger: slog.New(slog.NewTextHandler(io.Discard, nil))}}
	waiting := make(chan struct{})
	client.flowOpenRetryDelayForTest = func(int) time.Duration {
		close(waiting)
		return time.Hour
	}
	attempts := 0
	client.openFlowForTest = func() (*openedFlow, error) {
		attempts++
		return nil, errors.New("transport unavailable")
	}
	ctx, cancel := context.WithCancel(context.Background())
	result := make(chan error, 1)
	go func() {
		_, err := client.openFlowWithRetries(ctx, "example.test:80")
		result <- err
	}()
	<-waiting
	cancel()
	if err := <-result; !errors.Is(err, context.Canceled) {
		t.Fatalf("cancelled retry = %v, want context cancellation", err)
	}
	if attempts != 1 {
		t.Fatalf("cancelled flow attempted %d opens, want 1", attempts)
	}
}

func TestColdQUICDestinationRefusalDoesNotFallBackOrRetry(t *testing.T) {
	client := &Client{
		cfg: ClientConfig{
			Transport: TransportAuto, FallbackDelay: time.Second,
		},
		udpHealth: newUDPHealth(1, time.Minute),
		metrics:   metrics.New(),
	}
	var quicCalls, tcpCalls int
	client.dialPipelinedFlowForTest = func(_ context.Context, kind TransportKind, _ []byte) (*openedFlow, error) {
		if kind == TransportQUIC {
			quicCalls++
			return nil, errDestinationUnavailable
		}
		tcpCalls++
		return nil, errors.New("unexpected TCP fallback")
	}
	_, err := client.openInitialFlow(context.Background(), "example.test:443")
	if !errors.Is(err, errDestinationUnavailable) {
		t.Fatalf("cold-flow result = %v, want destination unavailable", err)
	}
	if quicCalls != 1 || tcpCalls != 0 {
		t.Fatalf("cold-flow candidates: QUIC=%d TCP=%d, want one QUIC and no TCP", quicCalls, tcpCalls)
	}
	if !client.udpHealth.allow(time.Now()) {
		t.Fatal("the destination response poisoned QUIC health")
	}
	if got := client.metrics.Snapshot().Fallbacks; got != 0 {
		t.Fatalf("destination response recorded %d fallbacks", got)
	}
}

func TestServerQUICShutdownDoesNotPoisonGlobalPathHealth(t *testing.T) {
	client := &Client{
		cfg:       ClientConfig{Transport: TransportAuto, FallbackDelay: time.Second},
		udpHealth: newUDPHealth(1, time.Minute), metrics: metrics.New(),
	}
	client.dialPipelinedFlowForTest = func(_ context.Context, kind TransportKind, _ []byte) (*openedFlow, error) {
		if kind == TransportQUIC {
			return nil, &quic.ApplicationError{Remote: true, ErrorMessage: "server restarting"}
		}
		return &openedFlow{kind: TransportTCP}, nil
	}
	flow, err := client.openInitialFlow(context.Background(), "example.test:443")
	if err != nil || flow == nil || flow.kind != TransportTCP {
		t.Fatalf("fallback flow = %+v, error = %v", flow, err)
	}
	if !client.udpHealth.allow(time.Now()) {
		t.Fatal("a peer-terminated QUIC connection blocked future QUIC attempts")
	}
}

func TestQUICReachabilityTimeoutWithWorkingTCPEntersCooldown(t *testing.T) {
	var logs bytes.Buffer
	client := &Client{
		cfg: ClientConfig{
			RemoteAddr: "egress.example:443", Transport: TransportAuto, FallbackDelay: time.Second,
			Logger: slog.New(slog.NewTextHandler(&logs, nil)),
		},
		udpHealth: newUDPHealth(1, time.Minute), metrics: metrics.New(),
	}
	client.dialPipelinedFlowForTest = func(_ context.Context, kind TransportKind, _ []byte) (*openedFlow, error) {
		if kind == TransportQUIC {
			return nil, &quic.HandshakeTimeoutError{}
		}
		return &openedFlow{kind: TransportTCP}, nil
	}
	flow, err := client.openInitialFlow(context.Background(), "example.test:443")
	if err != nil || flow == nil || flow.kind != TransportTCP {
		t.Fatalf("fallback flow = %+v, error = %v", flow, err)
	}
	if client.udpHealth.allow(time.Now()) {
		t.Fatal("a QUIC reachability timeout against a working TCP control did not enter cooldown")
	}
	got := client.metrics.Snapshot()
	if got.UDPPathUnavailable != 1 || got.EndpointTransportRaceFailures != 0 {
		t.Fatalf("unexpected endpoint transport metrics: %+v", got)
	}
	for _, want := range []string{
		"UDP path explicitly failed",
		"endpoint=egress.example:443",
		"fallback=tcp",
		"quic_error",
	} {
		if !strings.Contains(logs.String(), want) {
			t.Fatalf("UDP failure log is missing %q: %s", want, logs.String())
		}
	}
}

func TestReadyTCPDoesNotDisplaceSlowWorkingQUIC(t *testing.T) {
	client := &Client{
		cfg: ClientConfig{
			RemoteAddr: "egress.example:443", Transport: TransportAuto, FallbackDelay: time.Millisecond,
			Logger: slog.New(slog.NewTextHandler(io.Discard, nil)),
		},
		udpHealth: newUDPHealth(3, time.Minute), metrics: metrics.New(),
	}
	quicRelease := make(chan struct{})
	tcpReady := make(chan struct{})
	client.dialPipelinedFlowForTest = func(_ context.Context, kind TransportKind, _ []byte) (*openedFlow, error) {
		if kind == TransportQUIC {
			<-quicRelease
			return &openedFlow{kind: TransportQUIC}, nil
		}
		close(tcpReady)
		return &openedFlow{kind: TransportTCP}, nil
	}

	result := make(chan openedFlowResult, 1)
	go func() {
		flow, err := client.openInitialFlow(context.Background(), "example.test:443")
		result <- openedFlowResult{flow: flow, err: err}
	}()
	select {
	case <-tcpReady:
	case <-time.After(time.Second):
		t.Fatal("TCP standby was not started")
	}
	select {
	case got := <-result:
		close(quicRelease)
		t.Fatalf("ready TCP displaced pending QUIC: flow=%+v err=%v", got.flow, got.err)
	case <-time.After(25 * time.Millisecond):
	}
	close(quicRelease)
	got := <-result
	if got.err != nil || got.flow == nil || got.flow.kind != TransportQUIC {
		t.Fatalf("QUIC-preferred result = %+v, error = %v", got.flow, got.err)
	}
	if snapshot := client.metrics.Snapshot(); snapshot.Fallbacks != 0 || snapshot.UDPPathUnavailable != 0 {
		t.Fatalf("a slow working QUIC path was reported as failed: %+v", snapshot)
	}
	if !client.udpHealth.allow(time.Now()) {
		t.Fatal("a slow working QUIC path entered cooldown")
	}
}

func TestReadyTCPDoesNotDisplaceSlowWorkingPooledQUIC(t *testing.T) {
	client := &Client{
		cfg: ClientConfig{
			RemoteAddr: "egress.example:443", Transport: TransportAuto, FallbackDelay: time.Millisecond,
			Logger: slog.New(slog.NewTextHandler(io.Discard, nil)),
		},
		udpHealth: newUDPHealth(3, time.Minute), metrics: metrics.New(),
	}
	quicRelease := make(chan struct{})
	tcpReady := make(chan struct{})
	client.dialAuthenticatedLaneForTest = func(_ context.Context, kind TransportKind) (*authenticatedLane, error) {
		if kind == TransportQUIC {
			<-quicRelease
			return &authenticatedLane{kind: TransportQUIC}, nil
		}
		close(tcpReady)
		return &authenticatedLane{kind: TransportTCP}, nil
	}

	result := make(chan laneResult, 1)
	go func() {
		lane, err := client.raceUDPAndTCP(context.Background())
		result <- laneResult{lane: lane, err: err}
	}()
	select {
	case <-tcpReady:
	case <-time.After(time.Second):
		t.Fatal("TCP standby was not started")
	}
	select {
	case got := <-result:
		close(quicRelease)
		t.Fatalf("ready TCP displaced pending pooled QUIC: lane=%+v err=%v", got.lane, got.err)
	case <-time.After(25 * time.Millisecond):
	}
	close(quicRelease)
	got := <-result
	if got.err != nil || got.lane == nil || got.lane.kind != TransportQUIC {
		t.Fatalf("QUIC-preferred pooled result = %+v, error = %v", got.lane, got.err)
	}
	if snapshot := client.metrics.Snapshot(); snapshot.Fallbacks != 0 || snapshot.UDPPathUnavailable != 0 {
		t.Fatalf("a slow working pooled QUIC path was reported as failed: %+v", snapshot)
	}
}

func TestReadyTCPIsCommittedAfterExplicitQUICFailure(t *testing.T) {
	client := &Client{
		cfg: ClientConfig{
			RemoteAddr: "egress.example:443", Transport: TransportAuto, FallbackDelay: time.Millisecond,
			Logger: slog.New(slog.NewTextHandler(io.Discard, nil)),
		},
		udpHealth: newUDPHealth(1, time.Minute), metrics: metrics.New(),
	}
	quicRelease := make(chan struct{})
	tcpReady := make(chan struct{})
	client.dialPipelinedFlowForTest = func(_ context.Context, kind TransportKind, _ []byte) (*openedFlow, error) {
		if kind == TransportQUIC {
			<-quicRelease
			return nil, &quic.HandshakeTimeoutError{}
		}
		close(tcpReady)
		return &openedFlow{kind: TransportTCP}, nil
	}

	result := make(chan openedFlowResult, 1)
	go func() {
		flow, err := client.openInitialFlow(context.Background(), "example.test:443")
		result <- openedFlowResult{flow: flow, err: err}
	}()
	select {
	case <-tcpReady:
	case <-time.After(time.Second):
		t.Fatal("TCP standby was not started")
	}
	close(quicRelease)
	got := <-result
	if got.err != nil || got.flow == nil || got.flow.kind != TransportTCP {
		t.Fatalf("explicit-failure fallback = %+v, error = %v", got.flow, got.err)
	}
	if snapshot := client.metrics.Snapshot(); snapshot.Fallbacks != 1 || snapshot.UDPPathUnavailable != 1 {
		t.Fatalf("explicit differential failure was not recorded: %+v", snapshot)
	}
	if client.udpHealth.allow(time.Now()) {
		t.Fatal("an explicit QUIC failure against working TCP did not enter cooldown")
	}
}

func TestPreferenceGraceUsesTCPWithoutPoisoningUDPAndLatePoolRecovers(t *testing.T) {
	client := &Client{
		cfg: ClientConfig{
			RemoteAddr: "egress.example:443", Transport: TransportAuto, EnableQUICPool: true,
			FallbackDelay: time.Millisecond, FallbackGrace: 20 * time.Millisecond,
			Logger: slog.New(slog.NewTextHandler(io.Discard, nil)),
		},
		udpHealth: newUDPHealth(1, time.Minute), metrics: metrics.New(),
	}
	// Begin in cooldown to prove that a late successful QUIC pool attempt
	// positively restores health after this request has already used TCP.
	client.udpHealth.failure(time.Now())
	quicRelease := make(chan struct{})
	client.dialAuthenticatedLaneForTest = func(_ context.Context, kind TransportKind) (*authenticatedLane, error) {
		if kind == TransportQUIC {
			<-quicRelease
			return &authenticatedLane{kind: TransportQUIC}, nil
		}
		return &authenticatedLane{kind: TransportTCP}, nil
	}

	lane, err := client.raceUDPAndTCP(context.Background())
	if err != nil || lane == nil || lane.kind != TransportTCP {
		t.Fatalf("preference-expiry result = %+v, error = %v", lane, err)
	}
	if snapshot := client.metrics.Snapshot(); snapshot.Fallbacks != 1 || snapshot.UDPPathUnavailable != 0 {
		t.Fatalf("preference expiry was mistaken for UDP failure: %+v", snapshot)
	}
	close(quicRelease)
	deadline := time.Now().Add(time.Second)
	for !client.udpHealth.allow(time.Now()) && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	if !client.udpHealth.allow(time.Now()) {
		t.Fatal("late pooled QUIC success did not restore UDP health")
	}
}

func TestLatePooledQUICFailureIsRecordedOnlyWhenItBecomesExplicit(t *testing.T) {
	client := &Client{
		cfg: ClientConfig{
			RemoteAddr: "egress.example:443", Transport: TransportAuto, EnableQUICPool: true,
			FallbackDelay: time.Millisecond, FallbackGrace: 20 * time.Millisecond,
			Logger: slog.New(slog.NewTextHandler(io.Discard, nil)),
		},
		udpHealth: newUDPHealth(1, time.Minute), metrics: metrics.New(),
	}
	quicRelease := make(chan struct{})
	client.dialAuthenticatedLaneForTest = func(_ context.Context, kind TransportKind) (*authenticatedLane, error) {
		if kind == TransportQUIC {
			<-quicRelease
			return nil, &quic.HandshakeTimeoutError{}
		}
		return &authenticatedLane{kind: TransportTCP}, nil
	}

	lane, err := client.raceUDPAndTCP(context.Background())
	if err != nil || lane == nil || lane.kind != TransportTCP {
		t.Fatalf("preference-expiry result = %+v, error = %v", lane, err)
	}
	if snapshot := client.metrics.Snapshot(); snapshot.UDPPathUnavailable != 0 {
		t.Fatalf("pending QUIC was counted before it failed: %+v", snapshot)
	}
	close(quicRelease)
	deadline := time.Now().Add(time.Second)
	for client.metrics.Snapshot().UDPPathUnavailable == 0 && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	if snapshot := client.metrics.Snapshot(); snapshot.UDPPathUnavailable != 1 {
		t.Fatalf("explicit late QUIC failure was not recorded: %+v", snapshot)
	}
	if client.udpHealth.allow(time.Now()) {
		t.Fatal("explicit late QUIC failure did not enter cooldown")
	}
}

func TestColdFlowReportsBothEndpointTransportsFailing(t *testing.T) {
	var logs bytes.Buffer
	client := &Client{
		cfg: ClientConfig{
			RemoteAddr: "egress.example:443", Transport: TransportAuto, FallbackDelay: time.Second,
			Logger: slog.New(slog.NewTextHandler(&logs, nil)),
		},
		udpHealth: newUDPHealth(1, time.Minute), metrics: metrics.New(),
	}
	client.dialPipelinedFlowForTest = func(_ context.Context, kind TransportKind, _ []byte) (*openedFlow, error) {
		return nil, fmt.Errorf("%s path unavailable", kind)
	}

	if _, err := client.openInitialFlow(context.Background(), "example.test:443"); err == nil {
		t.Fatal("a cold flow with neither transport was reported as successful")
	}
	got := client.metrics.Snapshot()
	if got.EndpointTransportRaceFailures != 1 || got.UDPPathUnavailable != 0 {
		t.Fatalf("unexpected endpoint transport metrics: %+v", got)
	}
	for _, want := range []string{
		"configured endpoint failed on both transports",
		"endpoint=egress.example:443",
		"quic_error",
		"tcp_error",
	} {
		if !strings.Contains(logs.String(), want) {
			t.Fatalf("dual-transport failure log is missing %q: %s", want, logs.String())
		}
	}
}

func TestPooledFlowReportsBothEndpointTransportsFailing(t *testing.T) {
	var logs bytes.Buffer
	client := &Client{
		cfg: ClientConfig{
			RemoteAddr: "127.0.0.1:not-a-port", Transport: TransportAuto, EnableQUICPool: true, FallbackDelay: time.Second,
			Logger: slog.New(slog.NewTextHandler(&logs, nil)),
		},
		udpHealth: newUDPHealth(1, time.Minute), metrics: metrics.New(),
	}

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	if _, err := client.raceUDPAndTCP(ctx); err == nil {
		t.Fatal("a pooled flow with neither transport was reported as successful")
	}
	got := client.metrics.Snapshot()
	if got.EndpointTransportRaceFailures != 1 || got.UDPPathUnavailable != 0 {
		t.Fatalf("unexpected endpoint transport metrics: %+v", got)
	}
	if text := logs.String(); !strings.Contains(text, "configured endpoint failed on both transports") ||
		!strings.Contains(text, "endpoint=127.0.0.1:not-a-port") {
		t.Fatalf("pooled dual-transport failure was not logged: %s", text)
	}
}

// A flow becomes what it is as it ages, not only when it reads.
//
// This is the considered answer rather than the immediate one: a flow that has
// already moved more than a small exchange stops coding at once, without
// waiting for the class. Both matter, because they arrive at different times.
//
// The classifier was driven only by reads from the inner connection, and a
// server reading a ten megabyte file from a local destination does every one
// of those inside a second -- before the bulk test's minimum age -- and then
// never reads again. Nothing re-examined the flow, so it stayed ClassNew for
// its whole life and was coded from first byte to last.
func TestAFlowIsReclassifiedAsItAges(t *testing.T) {
	inner, peer := net.Pipe()
	defer inner.Close()
	defer peer.Close()
	f := newMultipathFlow(context.Background(), inner, [16]byte{1}, 1, 64*1024,
		protocol.FlagAckUp, protocol.FlagAckDown, nil, nil, nil)

	// Ten megabytes read before the bulk test's minimum age has elapsed, which
	// is what a fast local destination gives a server.
	f.observe(84, false)
	f.bytesDown.Add(84)
	for sent := 0; sent < 10_000_000; sent += 64 * 1024 {
		f.observe(64*1024, true)
		f.bytesUp.Add(64 * 1024)
	}
	if got := classifier.Class(f.class.Load()); got != classifier.ClassNew {
		t.Fatalf("class %v before the minimum age, want new", got)
	}

	// The reads are over. Only age separates this flow from being bulk, and
	// re-examining it is the only thing that can notice.
	f.started = f.started.Add(-5 * time.Second)
	f.lastClassified.Store(0)
	f.refreshClass()
	if got := classifier.Class(f.class.Load()); got != classifier.ClassBulk {
		t.Fatalf("class %v after ageing, want bulk; the flow was never "+
			"re-examined once it stopped reading", got)
	}
}

// And a flow that has already moved bulk quantities stops coding immediately,
// without waiting a second for the class to settle. That second is where a
// download produces most of its frames.
func TestAFlowThatHasMovedBulkQuantitiesStopsCodingAtOnce(t *testing.T) {
	inner, peer := net.Pipe()
	defer inner.Close()
	defer peer.Close()
	f := newMultipathFlow(context.Background(), inner, [16]byte{1}, 1, 64*1024,
		protocol.FlagAckUp, protocol.FlagAckDown, nil, nil, nil)

	if !f.prefersCodingOverRetransmission() {
		t.Fatal("a flow that has carried nothing should still prefer coding")
	}
	f.bytesUp.Store(codedFlowBytes + 1)
	if f.prefersCodingOverRetransmission() {
		t.Fatalf("a flow that has moved %d bytes still prefers coding, and will "+
			"go on doing so for the second its class takes to settle", f.bytesUp.Load())
	}
}

// A gap has to be reported when it is seen, not when it closes.
//
// The sender is clocked entirely by these acknowledgements: a chunk completes
// when its bytes are acknowledged, a lane's admission frees when its chunks
// complete, and nothing is issued until it does. A receiver that stays silent
// while it buffers above a hole therefore stops the sender dead -- and the one
// arrival that proves a hole exists is exactly the arrival that does not
// advance the cumulative point.
func TestAGapIsReportedWhenItIsSeenNotWhenItCloses(t *testing.T) {
	inner, peer := net.Pipe()
	defer inner.Close()
	defer peer.Close()
	f := newMultipathFlow(context.Background(), inner, [16]byte{1}, 1, 64*1024,
		protocol.FlagAckUp, protocol.FlagAckDown, nil, nil, nil)
	f.ackRanges.Store(true)

	reassembler := multipath.NewReassembler(multipath.Config{
		MaxBufferedBytes: maxReassemblyBytes, MaxBufferedFrames: maxReassemblyFrames,
	})
	payload := bytes.Repeat([]byte("x"), 1000)

	// The first segment is contiguous, so it advances the cumulative point and
	// is acknowledged in the ordinary way.
	if _, _, err := reassembler.Insert(multipath.Segment{Sequence: 0, Payload: payload}); err != nil {
		t.Fatal(err)
	}
	last := f.acknowledgeArrival(reassembler, 0)
	if last != 1000 {
		t.Fatalf("cumulative point %d after a contiguous segment, want 1000", last)
	}
	if f.gapPending.Load() {
		t.Fatal("a contiguous arrival was reported as a gap")
	}

	// The next segment arrives above a hole. The cumulative point cannot move,
	// which is precisely why the peer has to be told something.
	if _, _, err := reassembler.Insert(multipath.Segment{Sequence: 2000, Payload: payload}); err != nil {
		t.Fatal(err)
	}
	if got := f.acknowledgeArrival(reassembler, last); got != last {
		t.Fatalf("cumulative point moved to %d across a hole", got)
	}
	if !f.gapPending.Load() {
		t.Fatal("a segment arriving above a hole asked for no acknowledgement, so " +
			"the sender learns nothing until its reissue timer fires")
	}
	ranges := f.takeReceivedRanges(last)
	if len(ranges) == 0 {
		t.Fatal("the gap report carried no ranges, so it says only what was " +
			"already known")
	}
	if ranges[0][0] != 2000 || ranges[0][1] != 3000 {
		t.Fatalf("reported range %v, want the 2000-3000 that actually arrived", ranges[0])
	}
}

// What a short-lived flow costs, which is the case this transport exists for.
//
// A browser opens a connection, asks for something small, and closes it. Every
// such flow is a new one, so nothing about it is warm except the connection
// underneath, and there is never any data behind its packets to prove one
// lost. Measured live, most cost one round trip and a quarter cost a second
// and a half more: the difference is a chunk the code failed to repair, waited
// out by a timer.
func TestAShortFlowCostsARoundTrip(t *testing.T) {
	if testing.Short() {
		t.Skip("brings up QUIC across an emulated 300 ms path")
	}
	requireStableImpairmentClock(t)
	const oneWay = 150 * time.Millisecond
	path := pathsim.Config{
		OneWayDelay: oneWay, RateBytesPerSec: uint64(25e6 / 8),
		PolicerRefillPeriod: 8 * time.Millisecond, LossRate: 0.45, Seed: 61,
	}
	const replyBytes = 1400
	// The destination records when each request reached it, which splits what
	// a flow costs into the half spent getting there and the half coming back.
	arrivals := make(chan time.Time, 64)
	socks, destination := codedPairWith(t, true, &path, func(listener net.Listener) {
		for {
			conn, err := listener.Accept()
			if err != nil {
				return
			}
			go func(c net.Conn) {
				defer c.Close()
				buf := make([]byte, 16)
				body := make([]byte, replyBytes)
				for {
					if _, err := io.ReadFull(c, buf); err != nil {
						return
					}
					select {
					case arrivals <- time.Now():
					default:
					}
					if _, err := c.Write(body); err != nil {
						return
					}
				}
			}(conn)
		}
	})
	// The path has to be known before the question is asked: a flow on an
	// unmeasured path is carried uncoded, which is a different experiment.
	// Discovery and the prewarm have their own integration test. Seed this
	// timing test explicitly so scheduler speed under -race cannot decide how
	// many of its measured flows run before the asynchronous prewarm finishes.
	loopback := &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1), Port: 0}
	pathmodel.Shared(pathKey(loopback, loopback)).Report(99, pathmodel.Observation{Erasure: path.LossRate, BurstFactor: 1, ObservedSamples: 5000, Delivered: 0, RoundTrip: 0})
	// Warm the shared transport independently of the path measurement.
	warm := dialWithRetries(t, socks, destination, 3)
	request := make([]byte, 16)
	reply := make([]byte, replyBytes)
	for i := 0; i < 5; i++ {
		if _, err := warm.Write(request); err != nil {
			t.Fatal(err)
		}
		if _, err := io.ReadFull(warm, reply); err != nil {
			t.Fatalf("warming exchange %d: %v", i, err)
		}
	}
	warm.Close()

	const flows = 20
	var samples, dials, outbound []time.Duration
	for i := 0; i < flows; i++ {
		for len(arrivals) > 0 {
			<-arrivals
		}
		start := time.Now()
		conn, err := trySocksDial(socks, destination, 20*time.Second)
		if err != nil {
			t.Fatalf("flow %d: %v", i, err)
		}
		dialed := time.Now()
		if _, err := conn.Write(request); err == nil {
			if _, err := io.ReadFull(conn, reply); err != nil {
				conn.Close()
				continue
			}
			samples = append(samples, time.Since(start))
			dials = append(dials, dialed.Sub(start))
			select {
			case at := <-arrivals:
				outbound = append(outbound, at.Sub(start))
			default:
			}
		}
		conn.Close()
	}
	if len(outbound) > 0 {
		sorted := append([]time.Duration(nil), outbound...)
		sort.Slice(sorted, func(i, j int) bool { return sorted[i] < sorted[j] })
		t.Logf("  of which the request reaching the destination: median %v, max %v",
			sorted[len(sorted)/2].Round(time.Millisecond), sorted[len(sorted)-1].Round(time.Millisecond))
	}
	if len(dials) > 0 {
		sorted := append([]time.Duration(nil), dials...)
		sort.Slice(sorted, func(i, j int) bool { return sorted[i] < sorted[j] })
		t.Logf("  of which opening the flow: median %v, max %v",
			sorted[len(sorted)/2].Round(time.Millisecond), sorted[len(sorted)-1].Round(time.Millisecond))
	}
	if len(samples) < flows/2 {
		t.Fatalf("only %d of %d short flows completed", len(samples), flows)
	}
	sort.Slice(samples, func(i, j int) bool { return samples[i] < samples[j] })
	median := samples[len(samples)/2]
	p90 := samples[int(float64(len(samples)-1)*0.9)]
	roundTrip := 2 * oneWay
	rounded := make([]string, len(samples))
	for i, s := range samples {
		rounded[i] = s.Round(time.Millisecond).String()
	}
	t.Logf("%d short flows over a %.0f%% erasure channel: median %v, p90 %v, max %v (round trip %v)",
		len(samples), path.LossRate*100, median.Round(time.Millisecond),
		p90.Round(time.Millisecond), samples[len(samples)-1].Round(time.Millisecond), roundTrip)
	t.Logf("  each: %s", strings.Join(rounded, " "))
	// Three round trips, not one: the channel erases, and a flow whose repair
	// was itself erased pays for it. What this separates is a transport where
	// a short flow costs round trips from one where it costs a timer -- before
	// the demultiplexer held frames for flows that had not claimed them yet,
	// every short flow cost 1.055 s on a 300 ms path, which is the reissue
	// delay and not the path.
	//
	// Only the median is asserted. The distribution above it is real and worth
	// reading -- it is logged in full -- but it moves with how fast the machine
	// running the test is, and under the race detector it moves by a round
	// trip. A bound that fails on a slow machine tests the machine.
	if median > 3*roundTrip {
		t.Errorf("a short flow costs %v against a round trip of %v", median.Round(time.Millisecond), roundTrip)
	}
}

// A voice session is a sequence of small exchanges however many it has done,
// and the byte cutoff above cannot see that.
//
// Eighty bytes fifty times a second is four kilobytes a second, so a call
// crosses codedFlowBytes after about sixty-four seconds and then carries the
// rest of itself uncoded. That is exactly backwards: the reason the cutoff
// exists is that a transfer amortises a round trip over many bytes, and a
// stream of small messages separated by idle never amortises anything. Every
// lost frame pays a full round trip on its own.
//
// Measured on an emulated 14% path, an uncoded frame stream loses 71 of 400
// frames outright while a duplicated one loses 10.
func TestALongInteractiveSessionKeepsCoding(t *testing.T) {
	inner, peer := net.Pipe()
	defer inner.Close()
	defer peer.Close()
	f := newMultipathFlow(context.Background(), inner, [16]byte{1}, 1, 64*1024,
		protocol.FlagAckUp, protocol.FlagAckDown, nil, nil, nil)

	// Two minutes of a voice call: past the cutoff, and still small messages
	// with a gap between them.
	f.bytesUp.Store(4 * 1024 * 120)
	f.bytesDown.Store(4 * 1024 * 120)
	f.started = time.Now().Add(-120 * time.Second)
	// Frames keep arriving at a conversational rate: eighty bytes every 20ms.
	for i := 0; i < 60; i++ {
		f.observe(80, i%2 == 0)
	}

	if !f.prefersCodingOverRetransmission() {
		t.Fatalf("a %d-byte interactive session stopped coding; a call longer "+
			"than about a minute loses its repair exactly where it needs it",
			f.bytesUp.Load()+f.bytesDown.Load())
	}
}

// The cutoff still has to catch the case it was written for: a fast download
// producing most of its frames before the class settles.
func TestAFastDownloadStillStopsCodingBeforeItsClassSettles(t *testing.T) {
	inner, peer := net.Pipe()
	defer inner.Close()
	defer peer.Close()
	f := newMultipathFlow(context.Background(), inner, [16]byte{1}, 1, 64*1024,
		protocol.FlagAckUp, protocol.FlagAckDown, nil, nil, nil)
	f.bytesDown.Store(codedFlowBytes + 1)
	if f.prefersCodingOverRetransmission() {
		t.Fatal("a flow past the cutoff kept coding while still unclassified")
	}
}

// The rate window has to keep getting the download right, which is the case
// the previous rule was written for and the reason it used a total at all.
// A transfer reading in 16 KiB chunks looks small per read and is not small
// per second.
func TestASustainedDownloadIsStillBulk(t *testing.T) {
	inner, peer := net.Pipe()
	defer inner.Close()
	defer peer.Close()
	f := newMultipathFlow(context.Background(), inner, [16]byte{1}, 1, 64*1024,
		protocol.FlagAckUp, protocol.FlagAckDown, nil, nil, nil)
	f.started = time.Now().Add(-5 * time.Second)
	f.observe(64, true) // the request
	// A megabyte inside one window, in the 16 KiB reads a transfer uses.
	for i := 0; i < 64; i++ {
		f.bytesDown.Add(16 << 10)
		f.observe(16<<10, false)
	}
	if got := classifier.Class(f.class.Load()); got != classifier.ClassBulk {
		t.Errorf("a megabyte per second classified %v, want bulk", got)
	}
	if f.prefersCodingOverRetransmission() {
		t.Error("a sustained download still prefers coding")
	}
}

// And a flow that transfers, then stops and starts conversing, has to be
// allowed to become interactive again rather than carrying a bulk label it
// earned a minute ago. Sticky bulk is deliberate, so this documents what the
// rate window does and does not change.
func TestBulkStaysStickyEvenWhenTheRateFalls(t *testing.T) {
	inner, peer := net.Pipe()
	defer inner.Close()
	defer peer.Close()
	f := newMultipathFlow(context.Background(), inner, [16]byte{1}, 1, 64*1024,
		protocol.FlagAckUp, protocol.FlagAckDown, nil, nil, nil)
	f.started = time.Now().Add(-5 * time.Second)
	f.observe(64, true)
	for i := 0; i < 64; i++ {
		f.bytesDown.Add(16 << 10)
		f.observe(16<<10, false)
	}
	if classifier.Class(f.class.Load()) != classifier.ClassBulk {
		t.Fatal("setup did not reach bulk")
	}
	// Now converse. The classifier keeps bulk on purpose: hysteresis stops
	// queue policy flapping through a gap in a large transfer.
	f.lastClassified.Store(0)
	for i := 0; i < 10; i++ {
		f.observe(80, i%2 == 0)
	}
	if got := classifier.Class(f.class.Load()); got != classifier.ClassBulk {
		t.Errorf("bulk stopped being sticky: %v", got)
	}
}

// The window has to roll, or the rate it reports is a lifetime total wearing a
// different name and the demotion it was written to prevent comes back.
//
// A voice call at four kilobytes a second passes sixty-four kilobytes after
// sixteen seconds. If the buckets never age out, that is exactly when it stops
// looking like a conversation, which is the bug this replaced.
func TestTheExchangeWindowRolls(t *testing.T) {
	inner, peer := net.Pipe()
	defer inner.Close()
	defer peer.Close()
	f := newMultipathFlow(context.Background(), inner, [16]byte{1}, 1, 64*1024,
		protocol.FlagAckUp, protocol.FlagAckDown, nil, nil, nil)

	now := time.Now()
	var up uint64
	// Twenty windows of conversation: four kilobytes each, 80 KB in total,
	// which is past smallExchangeBytes if nothing ever ages out.
	for w := 0; w < 20; w++ {
		for i := 0; i < 50; i++ {
			up, _ = f.recentBytes(now, 80, true)
		}
		now = now.Add(exchangeWindow)
	}
	if up > smallExchangeBytes {
		t.Errorf("recent up = %d after 20 windows of 4KB; the window is not rolling", up)
	}
	// It reports between one and two windows of traffic, so a conversation
	// that just carried 4KB in a window must not report zero either.
	if up == 0 {
		t.Error("recent up = 0 while frames were still arriving")
	}

	// A transfer inside a single window still reports its full rate.
	burst, _ := f.recentBytes(now, 0, true)
	for i := 0; i < 64; i++ {
		burst, _ = f.recentBytes(now, 16<<10, true)
	}
	if burst <= smallExchangeBytes {
		t.Errorf("recent up = %d after a megabyte in one window, want above %d",
			burst, smallExchangeBytes)
	}

	// And the bucket that just aged out still counts, or a transfer would be
	// invisible for the first moments of every window and a download crossing
	// a boundary would read as a conversation.
	now = now.Add(exchangeWindow)
	spanning, _ := f.recentBytes(now, 80, true)
	if spanning <= smallExchangeBytes {
		t.Errorf("recent up = %d just after a boundary that a megabyte "+
			"preceded; the finished bucket was dropped", spanning)
	}
}
