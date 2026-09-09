package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net"
	"strings"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/pathseg"
)

// Both ping families have to parse, because the fallback exists precisely for
// gateways this project did not install and does not control.
func TestParsePingSummaryReadsBothFamilies(t *testing.T) {
	iputils := `PING example.com (203.0.113.9) 56(84) bytes of data.

--- example.com ping statistics ---
50 packets transmitted, 47 received, 6% packet loss, time 9803ms
rtt min/avg/max/mdev = 189.123/191.456/295.789/12.345 ms
`
	bsd := `PING example.com (203.0.113.9): 56 data bytes

--- example.com ping statistics ---
50 packets transmitted, 47 packets received, 6.0% packet loss
round-trip min/avg/max/stddev = 189.123/191.456/295.789/12.345 ms
`
	for name, out := range map[string]string{"iputils": iputils, "bsd": bsd} {
		leg, err := parsePingSummary(out, "example.com:443")
		if err != nil {
			t.Fatalf("%s: %v", name, err)
		}
		if leg.Sent != 50 || leg.Arrived != 47 {
			t.Fatalf("%s: sent %d arrived %d", name, leg.Sent, leg.Arrived)
		}
		if got := leg.Loss; got < 0.059 || got > 0.061 {
			t.Fatalf("%s: loss %v, want about 0.06", name, got)
		}
		if leg.MinMS != 189.123 || leg.P99MS != 295.789 {
			t.Fatalf("%s: timing %v/%v", name, leg.MinMS, leg.P99MS)
		}
		// ping reports a mean and this tool reports medians everywhere else.
		// Folding one into the other would misreport exactly the tailed
		// distributions this command is pointed at.
		if leg.MeanMS != 191.456 {
			t.Fatalf("%s: mean %v", name, leg.MeanMS)
		}
		if leg.P50MS != 0 {
			t.Fatalf("%s: a mean was reported as a median: %v", name, leg.P50MS)
		}
	}
}

func TestParsePingSummaryMarksATotalLossAsBlocked(t *testing.T) {
	leg, err := parsePingSummary(
		"50 packets transmitted, 0 received, 100% packet loss, time 9999ms\n", "x:443")
	if err != nil {
		t.Fatal(err)
	}
	if !leg.Blocked {
		t.Fatal("a run with no replies was not marked blocked")
	}
	if leg.Usable() {
		t.Fatal("a blocked leg is being offered as evidence")
	}
}

func TestParsePingSummaryRefusesOutputItCannotRead(t *testing.T) {
	if _, err := parsePingSummary("ping: command not found\n", "x:443"); err == nil {
		t.Fatal("unparseable output was accepted as a measurement")
	}
}

// ssh hands the command to a shell on the far side, so a path with a space in
// it would otherwise arrive as two arguments and run something else.
func TestShellQuoteSurvivesAShell(t *testing.T) {
	for in, want := range map[string]string{
		"queqiaod":                 `'queqiaod'`,
		"/opt/my gateway/queqiaod": `'/opt/my gateway/queqiaod'`,
		"/opt/it's/queqiaod":       `'/opt/it'\''s/queqiaod'`,
		"; rm -rf /; echo":         `'; rm -rf /; echo'`,
	} {
		if got := shellQuote(in); got != want {
			t.Fatalf("shellQuote(%q) = %s, want %s", in, got, want)
		}
	}
}

// The agent writes to a pipe that ssh carries back, so anything on stdout that
// is not the result arrives at the other end as a parse error.
func TestTheAgentWritesNothingButJSON(t *testing.T) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = ln.Close() }()
	go func() {
		for {
			c, err := ln.Accept()
			if err != nil {
				return
			}
			_ = c.Close()
		}
	}()

	req := pathseg.AgentRequest{
		References: []string{ln.Addr().String()},
		Count:      2, IntervalMS: 20, TimeoutMS: 200, EstablishCount: 1,
	}
	payload, err := json.Marshal(req)
	if err != nil {
		t.Fatal(err)
	}
	var out bytes.Buffer
	if err := runSegmentsAgent(bytes.NewReader(payload), &out); err != nil {
		t.Fatal(err)
	}
	var resp pathseg.AgentResponse
	if err := json.Unmarshal(out.Bytes(), &resp); err != nil {
		t.Fatalf("the agent wrote something that is not JSON: %v\n%s", err, out.String())
	}
	if len(resp.References) != 1 {
		t.Fatalf("%d references came back", len(resp.References))
	}
	if resp.References[0].Establish.Arrived != 1 {
		t.Fatalf("the reachability instrument did not reach a listener that accepted: %+v",
			resp.References[0].Establish)
	}
}

func TestTheAgentRefusesARequestItCannotRead(t *testing.T) {
	var out bytes.Buffer
	if err := runSegmentsAgent(strings.NewReader("{}"), &out); err == nil {
		t.Fatal("a request naming nothing to measure was accepted")
	}
	if out.Len() != 0 {
		t.Fatalf("a refused request still wrote to stdout: %s", out.String())
	}
}

func TestSegmentsRefusesToRunWithoutAGateway(t *testing.T) {
	err := runSegmentsCommand([]string{"--count", "1"})
	if err == nil || !strings.Contains(err.Error(), "--endpoint") {
		t.Fatalf("a run with no gateway gave %v", err)
	}
}

func TestSegmentsRefusesAnEmptyRun(t *testing.T) {
	err := runSegmentsCommand([]string{"--endpoint", "gw:443", "--count", "0"})
	if err == nil || !strings.Contains(err.Error(), "--count") {
		t.Fatalf("a zero-probe run gave %v", err)
	}
}

// The two anchors are one Chinese and one global on purpose, and they are used
// unchanged at both ends: a probe from a filtered network to a filtered
// destination measures the filter, and whichever anchor answers cleanly is the
// one that establishes that vantage point's own link.
func TestTheDefaultAnchorsSpanBothSidesOfAFilter(t *testing.T) {
	if len(defaultReferences) < 2 {
		t.Fatal("a single default anchor cannot distinguish a filtered route from a lossy link")
	}
	joined := strings.Join(defaultReferences, ",")
	for _, want := range []string{"baidu.com", "google.com"} {
		if !strings.Contains(joined, want) {
			t.Fatalf("the defaults omit %s: %v", want, defaultReferences)
		}
	}
}

func TestRenderShowsTheVerdictTheLegsAndWhatWasNotMeasured(t *testing.T) {
	e := pathseg.Evidence{
		Gateway: pathseg.Reference{Target: "gw:12443",
			Echo: pathseg.Leg{Name: "echo:gw", To: "gw:12443", Method: "icmp",
				Sent: 50, Arrived: 50, MinMS: 195, P50MS: 197, P99MS: 240}},
		ClientReferences: []pathseg.Reference{{Target: "baidu.com:443",
			Echo: pathseg.Leg{Name: "echo:baidu", To: "baidu.com:443", Method: "icmp",
				Sent: 50, Arrived: 50, MinMS: 11, P50MS: 12, P99MS: 20}}},
		Tunnel: pathseg.TunnelView{Present: true, ReceiveErasure: 0.142, SendErasure: 0.003,
			ReceiveResidual: 0.011, MinRTTMS: 197, SmoothedRTTMS: 214, Lanes: 2,
			CodedSymbols: 100000, PacketsSent: 100000},
	}
	r := segmentReport{
		Version: "test", StartedAt: time.Now().UTC(), Probes: 50, IntervalMS: 100,
		Gateway: "gw:12443", Evidence: e, Attribution: pathseg.Attribute(e),
		Notes: []string{"a note that should survive rendering"},
	}
	var out bytes.Buffer
	renderSegments(&out, r)
	got := out.String()
	for _, want := range []string{
		"VERDICT", "client-to-gateway", "14.2%", "baidu.com:443", "icmp",
		"a note that should survive rendering",
		// The absence of a far vantage point has to be visible, or silence
		// about the gateway's own transit reads as a clean bill of health.
		"far vantage    none",
	} {
		if !strings.Contains(got, want) {
			t.Fatalf("the report omits %q:\n%s", want, got)
		}
	}
}

// A leg that got nothing back must never be rendered as a hundred percent loss,
// which would be the strongest number in the table drawn from the weakest
// evidence in it.
func TestRenderCallsAnUnansweredLegUnanswered(t *testing.T) {
	leg := pathseg.Leg{Name: "echo:x", To: "x:443", Method: "icmp", Sent: 50, Loss: 1, Blocked: true}
	row := legRow("client", "x:443", leg)
	if !strings.Contains(row, "no reply") {
		t.Fatalf("row does not say the probes went unanswered: %s", row)
	}
	if strings.Contains(row, "100.0%") {
		t.Fatalf("an unanswered leg was rendered as total loss: %s", row)
	}
}

func TestWrapKeepsWholeWords(t *testing.T) {
	lines := wrap("the quick brown fox jumps over the lazy dog", 12)
	if len(lines) < 3 {
		t.Fatalf("no wrapping happened: %v", lines)
	}
	for _, l := range lines {
		if len(l) > 12 {
			t.Fatalf("line %q exceeds the width", l)
		}
	}
	if strings.Join(lines, " ") != "the quick brown fox jumps over the lazy dog" {
		t.Fatalf("wrapping lost or reordered words: %v", lines)
	}
}

func TestWithDefaultPortLeavesAnExplicitOneAlone(t *testing.T) {
	if got := withDefaultPort("example.com"); got != "example.com:443" {
		t.Fatalf("got %q", got)
	}
	if got := withDefaultPort("example.com:8443"); got != "example.com:8443" {
		t.Fatalf("got %q", got)
	}
}

func TestFirstLinePrefersStderrThenTheError(t *testing.T) {
	if got := firstLine("\n  ssh: connect refused\nmore\n", nil); got != "ssh: connect refused" {
		t.Fatalf("got %q", got)
	}
	if got := firstLine("", fmt.Errorf("exit status 127")); got != "exit status 127" {
		t.Fatalf("got %q", got)
	}
	if got := firstLine("", nil); got != "no output" {
		t.Fatalf("got %q", got)
	}
}

// A failed leg has no figures, and threading its error through the table would
// widen a numeric column to the width of a sentence and make every measured row
// unreadable. The reason still has to appear somewhere.
func TestAFailedLegIsListedApartFromTheTable(t *testing.T) {
	e := pathseg.Evidence{
		Gateway: pathseg.Reference{Target: "gw:12443",
			Echo: pathseg.Leg{Name: "echo:gw", To: "gw:12443", Method: "icmp",
				Sent: 10, Arrived: 10, MinMS: 195, P50MS: 197, P99MS: 240}},
		GatewayReferences: []pathseg.Reference{{Target: "baidu.com:443",
			Error: "ssh: Could not resolve hostname gateway.invalid: nodename nor servname provided"}},
		GatewayVantage: true,
	}
	rows, problems := legRows(e)
	for _, row := range rows {
		if strings.Contains(row, "Could not resolve") {
			t.Fatalf("an error was rendered inside the table: %s", row)
		}
	}
	if len(problems) != 1 || !strings.Contains(problems[0], "Could not resolve") {
		t.Fatalf("the failure was dropped instead of listed: %v", problems)
	}
	if !strings.Contains(problems[0], "gateway") {
		t.Fatalf("the failure does not say which vantage point it was: %s", problems[0])
	}

	var out bytes.Buffer
	renderSegments(&out, segmentReport{Version: "test", StartedAt: time.Now().UTC(),
		Evidence: e, Attribution: pathseg.Attribute(e)})
	if !strings.Contains(out.String(), "not measured") {
		t.Fatalf("the report hides the failed leg:\n%s", out.String())
	}
}

// A profile spends tens of seconds per leg producing no output, so silence has
// to be broken or an operator kills the run before it reaches the verdict.
func TestProgressNarratesEachLeg(t *testing.T) {
	var out bytes.Buffer
	p := &progress{w: &out, on: true, total: 2}
	done := p.begin("client", "baidu.com:443")
	done("clean, 28ms")
	p.notef("metrics: %d symbols", 1234)

	got := out.String()
	for _, want := range []string{"[1/2]", "client", "baidu.com:443", "clean, 28ms", "metrics: 1234 symbols"} {
		if !strings.Contains(got, want) {
			t.Fatalf("progress omits %q:\n%s", want, got)
		}
	}
	// The leg has to be announced on one line with its result, or a reader
	// cannot tell which leg a figure belongs to.
	if lines := strings.Count(strings.TrimSpace(got), "\n"); lines != 1 {
		t.Fatalf("expected two lines, got:\n%s", got)
	}
}

// --quiet exists for a log that should hold only the result, and it has to
// silence the narration completely rather than merely shorten it.
func TestQuietProgressWritesNothing(t *testing.T) {
	var out bytes.Buffer
	p := &progress{w: &out, on: false, total: 3}
	p.begin("client", "baidu.com:443")("clean")
	p.notef("something")
	if out.Len() != 0 {
		t.Fatalf("--quiet still wrote: %s", out.String())
	}
}

func TestSummarizeReferenceNamesWhatTheVerdictWillRestOn(t *testing.T) {
	clean := pathseg.Reference{Target: "baidu.com:443",
		Echo:      pathseg.Leg{Name: "e", Method: "icmp", Sent: 20, Arrived: 20, P50MS: 28},
		Establish: pathseg.Leg{Name: "s", Method: "tcp-connect", Sent: 3, Arrived: 3, P50MS: 30}}
	if got := summarizeReference(clean); got != "clean, 28ms" {
		t.Fatalf("got %q", got)
	}

	lossy := clean
	lossy.Echo = pathseg.Leg{Name: "e", Method: "icmp", Sent: 20, Arrived: 18, Loss: 0.1, P50MS: 213}
	if got := summarizeReference(lossy); got != "10.0% loss, 213ms" {
		t.Fatalf("got %q", got)
	}

	// The filtering signature has its own line, because "no reply" and "the
	// handshake was refused" send an operator to different places.
	blocked := clean
	blocked.Establish = pathseg.Leg{Name: "s", Method: "tcp-connect", Sent: 3, Loss: 1, Blocked: true}
	if got := summarizeReference(blocked); got != "echo ok, handshake refused" {
		t.Fatalf("got %q", got)
	}

	dead := pathseg.Reference{Target: "x:443",
		Echo:      pathseg.Leg{Name: "e", Method: "icmp", Sent: 20, Loss: 1, Blocked: true},
		Establish: pathseg.Leg{Name: "s", Method: "tcp-connect", Sent: 3, Loss: 1, Blocked: true}}
	if got := summarizeReference(dead); got != "no reply" {
		t.Fatalf("got %q", got)
	}

	if got := summarizeReference(pathseg.Reference{Target: "x", Error: "resolve failed"}); got != "failed" {
		t.Fatalf("got %q", got)
	}
}
