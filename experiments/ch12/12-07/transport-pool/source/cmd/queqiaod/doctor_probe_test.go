package main

import (
	"context"
	"net"
	"strings"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/socks5"
)

func TestQuantileReadsNearestRankAndSurvivesTheEdges(t *testing.T) {
	sorted := []float64{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
	if got := quantile(sorted, 0.50); got != 5 {
		t.Errorf("p50 of 1..10 is %v", got)
	}
	if got := quantile(sorted, 0.99); got != 10 {
		t.Errorf("p99 of 1..10 is %v", got)
	}
	if got := quantile([]float64{7}, 0.99); got != 7 {
		t.Errorf("p99 of a single sample is %v", got)
	}
	if got := quantile(nil, 0.5); got != 0 {
		t.Errorf("p50 of nothing is %v", got)
	}
}

// summarize must not reorder what it was given. The position analysis reads the
// same slices afterwards, and sorting them in place would turn the order effect
// into a comparison of two sorted lists, which is always zero.
func TestSummarizeLeavesTheCallersOrderAlone(t *testing.T) {
	samples := []float64{9, 1, 5}
	got := summarize(samples)
	if got.Min != 1 || got.P50 != 5 || got.N != 3 {
		t.Fatalf("summary is %+v", got)
	}
	if samples[0] != 9 || samples[1] != 1 || samples[2] != 5 {
		t.Fatalf("the caller's slice was reordered: %v", samples)
	}
}

// The case this check exists for: a destination served from an edge near the
// client, reached through a gateway on another continent. Every host check
// passes and the tunnel is still the wrong answer for this destination.
func TestPlacementWarnsWhenTheDestinationIsServedNearerThanTheGateway(t *testing.T) {
	got := checkPlacement(destinationProbe{
		Target:      "api.example.com:443",
		Direct:      latency{N: 10, Min: 4.0, P50: 4.3, P99: 5.2},
		Tunneled:    latency{N: 10, Min: 70.9, P50: 71.3, P99: 78.4},
		ArmEffect:   67.0,
		OrderEffect: 1.2,
		GatewayLeg:  68.1,
		FarLeg:      3.2,
		Decomposed:  true,
	})
	if got.Status != "warn" {
		t.Fatalf("a gateway on the far side of the destination reported %q: %s", got.Status, got.Detail)
	}
	for _, want := range []string{"anycast", "16.6x", "68.1ms", "3.2ms"} {
		if !strings.Contains(got.Detail, want) {
			t.Errorf("the verdict omits %q: %s", want, got.Detail)
		}
	}
}

// The ordinary healthy deployment. The tunnel costs one hop on a path that is
// long either way, and saying so must not read as a problem.
func TestPlacementAcceptsAGatewayNoFartherThanTheClient(t *testing.T) {
	got := checkPlacement(destinationProbe{
		Target:      "inference.example.net:443",
		Direct:      latency{N: 10, Min: 178, P50: 180, P99: 191},
		Tunneled:    latency{N: 10, Min: 188, P50: 190, P99: 204},
		ArmEffect:   10,
		OrderEffect: 2,
		GatewayLeg:  185,
		FarLeg:      5,
		Decomposed:  true,
	})
	if got.Status != "pass" {
		t.Fatalf("one added hop on a long path reported %q: %s", got.Status, got.Detail)
	}
	if !strings.Contains(got.Detail, "detour") {
		t.Errorf("the verdict does not state what was compared: %s", got.Detail)
	}
}

// Between the two thresholds the honest answer is that establishment got
// slower and only a workload can say whether the transfer earns it back. The
// check must hand that question on rather than settle it from a connect time.
func TestPlacementSendsAModestOverheadToAWorkloadMeasurement(t *testing.T) {
	got := checkPlacement(destinationProbe{
		Target:      "inference.example.net:443",
		Direct:      latency{N: 10, Min: 176, P50: 180, P99: 195},
		Tunneled:    latency{N: 10, Min: 224, P50: 230, P99: 261},
		ArmEffect:   50,
		OrderEffect: 3,
		GatewayLeg:  205,
		FarLeg:      25,
		Decomposed:  true,
	})
	if got.Status != "pass" {
		t.Fatalf("a modest overhead reported %q: %s", got.Status, got.Detail)
	}
	for _, want := range []string{"workload", "50.0ms", "tuned"} {
		if !strings.Contains(got.Detail, want) {
			t.Errorf("the verdict omits %q: %s", want, got.Detail)
		}
	}
}

// A difference smaller than the drift measured in the same minutes has not been
// resolved. This project has already paid for the lesson once, in a 53% win
// that reversed when the order reversed, and a check that reports the drift as
// a finding would reintroduce it in a place operators trust.
func TestPlacementRefusesToConcludeWhenTheOrderEffectDominates(t *testing.T) {
	got := checkPlacement(destinationProbe{
		Target:      "api.example.com:443",
		Direct:      latency{N: 10, Min: 40, P50: 60, P99: 210},
		Tunneled:    latency{N: 10, Min: 42, P50: 66, P99: 240},
		ArmEffect:   6,
		OrderEffect: 41,
		Decomposed:  false,
	})
	if got.Status != "warn" {
		t.Fatalf("an unresolved comparison reported %q: %s", got.Status, got.Detail)
	}
	if !strings.Contains(got.Detail, "ORDER DOMINATES") {
		t.Errorf("the verdict does not say the comparison failed to resolve: %s", got.Detail)
	}
}

// Where the tunnel is the only way to reach something, its latency against a
// direct arm that never completed is not a placement question and must not be
// reported as one.
func TestPlacementPassesWhenOnlyTheTunnelReachesTheDestination(t *testing.T) {
	got := checkPlacement(destinationProbe{
		Target:      "blocked.example.com:443",
		Direct:      latency{},
		DirectError: "i/o timeout",
		Tunneled:    latency{N: 10, Min: 190, P50: 194, P99: 220},
	})
	if got.Status != "pass" {
		t.Fatalf("a destination only the tunnel reaches reported %q: %s", got.Status, got.Detail)
	}
}

// The reverse is a real failure, and calling it a placement warning would file
// a broken gateway under a topology heading.
func TestPlacementFailsWhenTheTunnelCannotReachADestinationThatAnswersDirectly(t *testing.T) {
	got := checkPlacement(destinationProbe{
		Target:      "internal.example.net:443",
		Direct:      latency{N: 10, Min: 3, P50: 3.2, P99: 4},
		Tunneled:    latency{},
		TunnelError: "socks5: CONNECT refused, reply 2",
	})
	if got.Status != "fail" {
		t.Fatalf("a gateway that refuses a destination reported %q: %s", got.Status, got.Detail)
	}
	if !strings.Contains(got.Detail, "gateway problem") {
		t.Errorf("the verdict does not separate this from a placement result: %s", got.Detail)
	}
}

func TestWantsTLSOnlyWhereAHandshakeIsExpected(t *testing.T) {
	if !wantsTLS("example.com:443") {
		t.Error("443 was not treated as a TLS port")
	}
	for _, target := range []string{"example.com:80", "example.com:12345", "not-a-target"} {
		if wantsTLS(target) {
			t.Errorf("%q was treated as a TLS port", target)
		}
	}
}

func TestCheckSOCKSListenerReportsAClientThatIsNotRunning(t *testing.T) {
	ctx, cancel := context.WithTimeout(t.Context(), 3*time.Second)
	defer cancel()
	// Port 1 on loopback, which nothing listens on and which refuses fast.
	got := checkSOCKSListener(ctx, "127.0.0.1:1")
	if got.Status != "warn" {
		t.Fatalf("a missing client reported %q: %s", got.Status, got.Detail)
	}
	if !strings.Contains(got.Detail, "--socks") {
		t.Errorf("the warning does not name the flag that would fix it: %s", got.Detail)
	}
}

// The end-to-end shape: a destination reached directly and through a SOCKS
// listener speaking this project's own server-side parser, so the probe's
// client is exercised against the code a real client runs.
func TestProbeDestinationMeasuresBothArmsAndDecomposesTheTunnelledLeg(t *testing.T) {
	destination := listenAndAccept(t)
	socksAddr := startSOCKSProxy(t)

	ctx, cancel := context.WithTimeout(t.Context(), 20*time.Second)
	defer cancel()
	gateway := latency{N: 4, Min: 0.4, P50: 0.5, P99: 0.9}
	got := probeDestination(ctx, destination, socksAddr, 2, gateway)

	if got.DirectError != "" {
		t.Fatalf("the direct arm failed: %s", got.DirectError)
	}
	if got.TunnelError != "" {
		t.Fatalf("the tunnelled arm failed: %s", got.TunnelError)
	}
	// Two round pairs, each running both orders, is four samples per arm.
	if got.Direct.N != 4 || got.Tunneled.N != 4 {
		t.Fatalf("sample counts are direct=%d tunnel=%d, want 4 and 4", got.Direct.N, got.Tunneled.N)
	}
	if !got.Decomposed {
		t.Error("a measured gateway leg was not subtracted from the tunnelled establishment")
	}
	if got.GatewayLeg != gateway.P50 {
		t.Errorf("the gateway leg is %v, want the measured %v", got.GatewayLeg, gateway.P50)
	}
	if got.FarLeg < 0 {
		t.Errorf("the derived far leg is negative: %v", got.FarLeg)
	}
	if got.TLS {
		t.Error("a loopback port was treated as needing a TLS handshake")
	}
}

// A gateway leg larger than the whole tunnelled establishment would derive a
// negative hop, which is a measurement artefact rather than a distance. It has
// to floor at zero instead of printing a number no reader could act on.
func TestProbeDestinationFloorsAnImpossibleFarLegAtZero(t *testing.T) {
	destination := listenAndAccept(t)
	socksAddr := startSOCKSProxy(t)
	ctx, cancel := context.WithTimeout(t.Context(), 20*time.Second)
	defer cancel()
	got := probeDestination(ctx, destination, socksAddr, 1, latency{N: 4, P50: 10_000})
	if !got.Decomposed {
		t.Fatal("the probe did not decompose the tunnelled leg")
	}
	if got.FarLeg != 0 {
		t.Errorf("an impossible far leg is %v, want 0", got.FarLeg)
	}
}

func TestProbeGatewayReportsADistributionRatherThanOneDial(t *testing.T) {
	endpoint := listenAndAccept(t)
	ctx, cancel := context.WithTimeout(t.Context(), 10*time.Second)
	defer cancel()
	got, err := probeGateway(ctx, endpoint, 5)
	if err != nil {
		t.Fatal(err)
	}
	if got.N != 5 {
		t.Fatalf("got %d samples, want 5", got.N)
	}
	if got.Min > got.P50 || got.P50 > got.P99 {
		t.Fatalf("the summary is not ordered: %+v", got)
	}
}

func TestProbeGatewayReturnsTheErrorWhenNothingAnswers(t *testing.T) {
	ctx, cancel := context.WithTimeout(t.Context(), 3*time.Second)
	defer cancel()
	if _, err := probeGateway(ctx, "127.0.0.1:1", 2); err == nil {
		t.Fatal("a gateway that refuses every dial produced no error")
	}
}

func TestIndentWrapFoldsOntoTheColumnItStartedIn(t *testing.T) {
	const indent, width = 33, 78
	got := indentWrap(strings.Repeat("word ", 40), indent, indent, width)
	lines := strings.Split(got, "\n")
	if len(lines) < 3 {
		t.Fatalf("a detail of 200 columns folded into %d lines", len(lines))
	}
	for i, line := range lines {
		if i > 0 && !strings.HasPrefix(line, strings.Repeat(" ", indent)) {
			t.Fatalf("continuation line %d lost the indent: %q", i, line)
		}
		if got := len(line) + boolToInt(i == 0)*indent; got > width {
			t.Fatalf("line %d reaches column %d: %q", i, got, line)
		}
	}
	if strings.Contains(got, " \n") {
		t.Errorf("a line was padded with trailing space: %q", got)
	}
}

// A name that overruns the pad pushes its first line right, and only its first
// line. Charging the whole block for that would waste a third of the width on
// every line that follows the long name.
func TestIndentWrapChargesOnlyTheFirstLineForALongName(t *testing.T) {
	const indent, width = 33, 78
	got := indentWrap(strings.Repeat("word ", 40), 40, indent, width)
	lines := strings.Split(got, "\n")
	if len(lines[0])+40 > width {
		t.Fatalf("the first line reaches column %d: %q", len(lines[0])+40, lines[0])
	}
	if len(lines[1]) <= len(lines[0]) {
		t.Fatalf("the block did not widen after the first line: %q then %q", lines[0], lines[1])
	}
}

// Past some name length there is no first line worth having, and a detail
// squeezed into what is left would be a ribbon down the right margin. It gives
// the line up instead, and nothing overruns the width.
func TestIndentWrapGivesUpTheFirstLineRatherThanOverrun(t *testing.T) {
	const indent, width = 33, 78
	got := indentWrap(strings.Repeat("word ", 40), 65, indent, width)
	if !strings.HasPrefix(got, "\n"+strings.Repeat(" ", indent)) {
		t.Fatalf("the detail did not start on its own line: %q", got[:40])
	}
	for _, line := range strings.Split(got, "\n") {
		if len(line) > width {
			t.Fatalf("a line reaches column %d: %q", len(line), line)
		}
	}
}

func boolToInt(b bool) int {
	if b {
		return 1
	}
	return 0
}

func TestDoctorRefusesRoundsBelowOne(t *testing.T) {
	err := runDoctorCommand([]string{"--rounds", "0"})
	if err == nil {
		t.Fatal("zero rounds was accepted")
	}
	if !strings.Contains(err.Error(), "--rounds") {
		t.Fatalf("the error does not name the flag: %v", err)
	}
}

func TestDestinationFlagCollectsEveryValue(t *testing.T) {
	var got stringList
	for _, v := range []string{"a:1", "b:2"} {
		if err := got.Set(v); err != nil {
			t.Fatal(err)
		}
	}
	if err := got.Set(""); err == nil {
		t.Error("an empty destination was accepted")
	}
	if got.String() != "a:1,b:2" {
		t.Fatalf("collected %q", got.String())
	}
}

// listenAndAccept starts a listener that accepts and immediately closes, which
// is all an establishment measurement needs on the far side.
func listenAndAccept(t *testing.T) string {
	t.Helper()
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = ln.Close() })
	go func() {
		for {
			conn, err := ln.Accept()
			if err != nil {
				return
			}
			_ = conn.Close()
		}
	}()
	return ln.Addr().String()
}

// startSOCKSProxy runs a CONNECT-only proxy on this project's own request
// parser, so the probe's client is checked against the wire the real listener
// speaks rather than against a second reading of the RFC.
func startSOCKSProxy(t *testing.T) string {
	t.Helper()
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = ln.Close() })
	go func() {
		for {
			conn, err := ln.Accept()
			if err != nil {
				return
			}
			go func() {
				defer func() { _ = conn.Close() }()
				request, err := socks5.ReadRequest(conn, nil)
				if err != nil || request.Command != socks5.CommandConnect {
					return
				}
				upstream, err := net.DialTimeout("tcp", request.Destination, 3*time.Second)
				if err != nil {
					_ = socks5.WriteReply(conn, socks5.ReplyHostUnreachable, nil)
					return
				}
				defer func() { _ = upstream.Close() }()
				_ = socks5.WriteReply(conn, socks5.ReplySucceeded, upstream.LocalAddr())
			}()
		}
	}()
	return ln.Addr().String()
}

// doctor derives the gateway's hop to a destination by subtracting one
// measurement from another, and queqiaod segments measures that same leg from
// the gateway. Two commands answering one question by two methods will
// disagree, so the derived figure has to say which it is and where the measured
// one lives -- otherwise an operator reads a subtraction as an observation.
func TestTheDerivedFarLegNamesTheCommandThatMeasuresIt(t *testing.T) {
	decomposed := decomposition(destinationProbe{Decomposed: true, GatewayLeg: 197, FarLeg: 14})
	for _, want := range []string{"subtraction rather than a measurement", "segments --ssh"} {
		if !strings.Contains(decomposed, want) {
			t.Fatalf("the decomposition omits %q: %s", want, decomposed)
		}
	}
	if !strings.Contains(decomposition(destinationProbe{}), "segments") {
		t.Fatalf("an undecomposed report does not point anywhere: %s", decomposition(destinationProbe{}))
	}
}
