package pathseg

import (
	"strings"
	"testing"
)

// reference builds an anchor that answered both instruments, with the loss and
// round trip given.
func reference(target string, loss, rttMS float64) Reference {
	sent := 100
	arrived := sent - int(loss*float64(sent)+0.5)
	return Reference{
		Target: target,
		Echo: Leg{Name: "echo:" + target, To: target, Method: "icmp",
			Sent: sent, Arrived: arrived, Loss: loss, BurstFactor: 1.0,
			MinMS: rttMS, P50MS: rttMS, P99MS: rttMS * 2},
		Establish: Leg{Name: "establish:" + target, To: target, Method: "tcp-connect",
			Sent: 3, Arrived: 3, MinMS: rttMS, P50MS: rttMS, P99MS: rttMS},
	}
}

// filtered is the signature this whole design exists to keep out of the loss
// column: the address answers echo and a handshake to it never completes.
func filtered(target string) Reference {
	r := reference(target, 0, 40)
	r.Establish = Leg{Name: "establish:" + target, To: target, Method: "tcp-connect",
		Sent: 3, Arrived: 0, Loss: 1, Blocked: true}
	return r
}

func findingFor(t *testing.T, a Attribution, segment string) Finding {
	t.Helper()
	for _, f := range a.Findings {
		if f.Segment == segment {
			return f
		}
	}
	t.Fatalf("no finding for %q in %+v", segment, a.Findings)
	return Finding{}
}

// The client's first mile is under every other leg measured from the client, so
// when it is lossy the leg to the gateway inherits that loss and has not
// separated anything. Reporting both as faults would send an operator to fix a
// long haul that may be in perfect health.
func TestLossOnTheClientAnchorIsChargedToItsAccessLink(t *testing.T) {
	a := Attribute(Evidence{
		Gateway:          reference("gw:12443", 0.09, 200),
		ClientReferences: []Reference{reference("baidu.com:443", 0.08, 12)},
	})
	access := findingFor(t, a, SegmentClientAccess)
	if access.Severity != SeverityFault {
		t.Fatalf("a lossy local anchor reported %q: %s", access.Severity, access.Summary)
	}
	long := findingFor(t, a, SegmentLongHaul)
	if long.Severity != SeverityWarn {
		t.Fatalf("the long haul reported %q where the first mile was already lossy", long.Severity)
	}
	if !strings.Contains(long.Detail, "crosses it") {
		t.Fatalf("the long haul finding does not say it inherits the access link: %s", long.Detail)
	}
}

// The same loss on the gateway leg with a clean local anchor is the long haul,
// which is the one segment this transport repairs.
func TestLossToTheGatewayWithACleanAnchorIsTheLongHaul(t *testing.T) {
	a := Attribute(Evidence{
		Gateway:          reference("gw:12443", 0.09, 200),
		ClientReferences: []Reference{reference("baidu.com:443", 0.0, 12)},
	})
	if got := findingFor(t, a, SegmentLongHaul); got.Severity != SeverityFault {
		t.Fatalf("the long haul reported %q: %s", got.Severity, got.Summary)
	}
	if got := findingFor(t, a, SegmentClientAccess); got.Severity != SeverityOK {
		t.Fatalf("a clean anchor reported %q", got.Severity)
	}
	if !strings.Contains(a.Headline, SegmentLongHaul) {
		t.Fatalf("the headline does not name the segment: %s", a.Headline)
	}
}

// Loss past the gateway is not this transport's to repair, and saying so is the
// point: coding, pacing and lane recovery all stop at the gateway.
func TestLossPastTheGatewayIsNamedAsBeyondRepair(t *testing.T) {
	a := Attribute(Evidence{
		Gateway:           reference("gw:12443", 0.0, 200),
		ClientReferences:  []Reference{reference("baidu.com:443", 0.0, 12)},
		GatewayReferences: []Reference{reference("www.google.com:443", 0.07, 8)},
		GatewayVantage:    true,
	})
	egress := findingFor(t, a, SegmentGatewayEgress)
	if egress.Severity != SeverityFault {
		t.Fatalf("a lossy gateway transit reported %q: %s", egress.Severity, egress.Summary)
	}
	if !strings.Contains(egress.Detail, "stop at the gateway") {
		t.Fatalf("the finding does not say the transport cannot repair it: %s", egress.Detail)
	}
	if got := findingFor(t, a, SegmentLongHaul); got.Severity != SeverityOK {
		t.Fatalf("the long haul was implicated by the gateway's own transit: %q", got.Severity)
	}
}

// The case this tool would be worst at if it were naive. A client behind a
// filter probing a blocked anchor sees a dead destination; charged as loss it
// would convict an access link that is carrying traffic perfectly well, which
// is both wrong and the most expensive kind of wrong -- it sends the operator
// to their ISP.
func TestAFilteredAnchorIsNotChargedToTheAccessLink(t *testing.T) {
	a := Attribute(Evidence{
		Gateway: reference("gw:12443", 0.0, 200),
		ClientReferences: []Reference{
			reference("baidu.com:443", 0.0, 12),
			filtered("www.google.com:443"),
		},
	})
	if got := findingFor(t, a, SegmentClientAccess); got.Severity != SeverityOK {
		t.Fatalf("a filtered second anchor moved the access link to %q: %s", got.Severity, got.Summary)
	}
	note := findingFor(t, a, SegmentDestination)
	if note.Severity != SeverityNote {
		t.Fatalf("filtering reported as %q rather than a note", note.Severity)
	}
	if !strings.Contains(note.Summary, "refuses a handshake") {
		t.Fatalf("the filtering finding does not describe the signature: %s", note.Summary)
	}
	if !strings.Contains(a.Headline, "clean") {
		t.Fatalf("a filtered anchor produced a fault headline: %s", a.Headline)
	}
}

// An anchor that answers nothing at all has measured nothing at all. It is
// indistinguishable from here from a firewall that drops echo, so it must not
// become the strongest possible finding.
func TestAnUnansweredAnchorDoesNotConvictAnything(t *testing.T) {
	dead := Reference{Target: "unreachable:443",
		Echo:      Leg{Name: "echo:unreachable", To: "unreachable:443", Method: "icmp", Sent: 100, Loss: 1, Blocked: true},
		Establish: Leg{Name: "establish:unreachable", To: "unreachable:443", Method: "tcp-connect", Sent: 3, Loss: 1, Blocked: true}}
	a := Attribute(Evidence{
		Gateway:          reference("gw:12443", 0.0, 200),
		ClientReferences: []Reference{dead},
	})
	access := findingFor(t, a, SegmentClientAccess)
	if access.Severity != SeverityNote {
		t.Fatalf("an unanswered anchor reported %q rather than declining to conclude", access.Severity)
	}
	if !strings.Contains(access.Summary, "not measured") {
		t.Fatalf("the finding claims a measurement it did not take: %s", access.Summary)
	}
}

// Silence about the far side must not read as health. Without a vantage point
// on the gateway, a clean report has not examined its transit at all.
func TestNoGatewayVantageIsReportedRatherThanAssumedClean(t *testing.T) {
	a := Attribute(Evidence{
		Gateway:          reference("gw:12443", 0.0, 200),
		ClientReferences: []Reference{reference("baidu.com:443", 0.0, 12)},
	})
	egress := findingFor(t, a, SegmentGatewayEgress)
	if egress.Severity != SeverityNote {
		t.Fatalf("an unmeasured gateway transit reported %q", egress.Severity)
	}
	for _, want := range []string{"--ssh", "does not rule this segment out"} {
		if !strings.Contains(egress.Detail, want) {
			t.Fatalf("the finding omits %q: %s", want, egress.Detail)
		}
	}
}

// The transport's own figures beat any probe this command can send, and the
// reason is the direction: an echo probe averages the two halves of a path that
// this project has measured differing by fourteen points.
func TestTheTunnelsOwnErasureIsPreferredAndNamesTheDirection(t *testing.T) {
	a := Attribute(Evidence{
		Gateway:          reference("gw:12443", 0.0, 200),
		ClientReferences: []Reference{reference("baidu.com:443", 0.0, 12)},
		Tunnel: TunnelView{Present: true, ReceiveErasure: 0.142, SendErasure: 0.003,
			ReceiveResidual: 0.011, MinRTTMS: 197, CodedSymbols: 100000, PacketsSent: 100000},
	})
	long := findingFor(t, a, SegmentLongHaul)
	if long.Severity != SeverityFault {
		t.Fatalf("14%% erasure reported as %q", long.Severity)
	}
	for _, want := range []string{"14.2%", "0.3%", "downstream (gateway to client)", "197ms"} {
		if !strings.Contains(long.Summary+long.Detail, want) {
			t.Fatalf("the finding omits %q: %s / %s", want, long.Summary, long.Detail)
		}
	}
}

// An idle session's ratios are not evidence, so the probe has to take over
// rather than the report quoting a figure drawn from nothing.
func TestAnIdleTunnelFallsBackToTheProbe(t *testing.T) {
	a := Attribute(Evidence{
		Gateway:          reference("gw:12443", 0.06, 200),
		ClientReferences: []Reference{reference("baidu.com:443", 0.0, 12)},
		Tunnel:           TunnelView{Present: true, ReceiveErasure: 0.5, CodedSymbols: 4, PacketsSent: 4},
	})
	long := findingFor(t, a, SegmentLongHaul)
	if !strings.Contains(long.Summary, "6.0%") {
		t.Fatalf("the probe's figure was not used: %s", long.Summary)
	}
	if strings.Contains(long.Summary, "50.0%") {
		t.Fatal("a ratio from four symbols was quoted as a measurement")
	}
}

// A destination the direct arm cannot reach and the tunnel can is not a fault
// anywhere; it is the deployment working.
func TestADestinationOnlyTheTunnelReachesIsNotAFault(t *testing.T) {
	a := Attribute(Evidence{
		Gateway:          reference("gw:12443", 0.0, 200),
		ClientReferences: []Reference{reference("baidu.com:443", 0.0, 12)},
		Direct:           []Leg{{To: "www.google.com:443", Method: "tcp-connect", Sent: 4, Blocked: true, Loss: 1}},
		Tunneled:         []Leg{{To: "www.google.com:443", Method: "tcp-connect", Sent: 4, Arrived: 4, P50MS: 210}},
	})
	got := findingFor(t, a, SegmentTunnel)
	if got.Severity != SeverityOK {
		t.Fatalf("the tunnel doing its job reported %q: %s", got.Severity, got.Summary)
	}
}

// A destination the gateway cannot open, that the client can, is the gateway's
// problem rather than the path's.
func TestADestinationOnlyTheDirectArmReachesIsAGatewayFault(t *testing.T) {
	a := Attribute(Evidence{
		Gateway:          reference("gw:12443", 0.0, 200),
		ClientReferences: []Reference{reference("baidu.com:443", 0.0, 12)},
		Direct:           []Leg{{To: "internal:443", Method: "tcp-connect", Sent: 4, Arrived: 4, P50MS: 5}},
		Tunneled:         []Leg{{To: "internal:443", Method: "tcp-connect", Sent: 4, Blocked: true, Loss: 1}},
	})
	if got := findingFor(t, a, SegmentTunnel); got.Severity != SeverityFault {
		t.Fatalf("a destination the gateway cannot open reported %q", got.Severity)
	}
}

// Independent loss and clustered loss need opposite responses, so the report
// has to say which it saw rather than only how much.
func TestThePatternDistinguishesErasureFromCongestion(t *testing.T) {
	independent := reference("gw:12443", 0.09, 200)
	independent.Echo.BurstFactor = 1.02
	a := Attribute(Evidence{Gateway: independent,
		ClientReferences: []Reference{reference("baidu.com:443", 0.0, 12)}})
	if got := findingFor(t, a, SegmentLongHaul); !strings.Contains(got.Detail, "sending slower will not") {
		t.Fatalf("independent loss was not named as an erasure channel: %s", got.Detail)
	}

	clustered := reference("gw:12443", 0.09, 200)
	clustered.Echo.BurstFactor, clustered.Echo.LongestBurst = 6.2, 14
	b := Attribute(Evidence{Gateway: clustered,
		ClientReferences: []Reference{reference("baidu.com:443", 0.0, 12)}})
	if got := findingFor(t, b, SegmentLongHaul); !strings.Contains(got.Detail, "queue or a policer") {
		t.Fatalf("clustered loss was not named as congestion: %s", got.Detail)
	}
}

func TestFilteredIsNotClaimedWhenEchoIsAlsoDown(t *testing.T) {
	r := filtered("x:443")
	if !r.Filtered() {
		t.Fatal("the filtering signature was not recognised")
	}
	r.Echo.Blocked = true
	r.Echo.Arrived = 0
	if r.Filtered() {
		t.Fatal("a destination nothing reached was called filtered")
	}
}

// Where no echo socket exists at all -- an ordinary unprivileged Linux host --
// the anchor still has to yield a verdict from the instrument that did work.
func TestHealthFallsBackToEstablishmentWhenEchoIsUnavailable(t *testing.T) {
	r := reference("baidu.com:443", 0, 12)
	r.Echo = Leg{Name: "echo:x", Error: ErrICMPUnavailable.Error()}
	leg, ok := r.Health()
	if !ok || leg.Method != "tcp-connect" {
		t.Fatalf("no fallback to establishment: %+v ok=%v", leg, ok)
	}
}

// Where no echo socket exists -- an ordinary unprivileged Linux host -- the
// verdict falls back to the establishment leg, and reading that leg's
// connection failure rate as loss would be a false negative on exactly the
// paths this tool exists for: TCP retransmits, so almost every connection
// still completes on a path erasing a fifth of everything, and the failure
// rate stays at zero while the path is in ruins. The cost of those
// retransmissions is what the fallback has to read instead.
func TestWithoutAnEchoSocketTheHandshakeTailStandsInForLoss(t *testing.T) {
	ruined := Reference{Target: "baidu.com:443",
		Echo: Leg{Name: "echo:baidu", Error: ErrICMPUnavailable.Error()},
		Establish: Leg{Name: "establish:baidu", To: "baidu.com:443", Method: "tcp-connect",
			// Every connection completed, and a third of them paid a
			// retransmission timeout to do it.
			Sent: 30, Arrived: 30, Loss: 0, TailRate: 0.33,
			MinMS: 30, P50MS: 40, P99MS: 1300}}
	a := Attribute(Evidence{
		Gateway:          reference("gw:12443", 0.0, 200),
		ClientReferences: []Reference{ruined},
	})
	access := findingFor(t, a, SegmentClientAccess)
	if access.Severity != SeverityFault {
		t.Fatalf("a link where a third of handshakes retransmitted reported %q: %s",
			access.Severity, access.Summary)
	}
	// The figure is a stand-in and the report has to say so, because a reader
	// acting on it should know it is not a counted loss rate.
	if !strings.Contains(access.Detail, "retransmission timeout") {
		t.Fatalf("the finding does not say the figure is a proxy: %s", access.Detail)
	}
}

// The same fallback must not invent a fault where the tail is clean.
func TestACleanHandshakeTailIsStillClean(t *testing.T) {
	fine := Reference{Target: "baidu.com:443",
		Echo: Leg{Name: "echo:baidu", Error: ErrICMPUnavailable.Error()},
		Establish: Leg{Name: "establish:baidu", To: "baidu.com:443", Method: "tcp-connect",
			Sent: 30, Arrived: 30, TailRate: 0, MinMS: 30, P50MS: 32, P99MS: 40}}
	a := Attribute(Evidence{
		Gateway:          reference("gw:12443", 0.0, 200),
		ClientReferences: []Reference{fine},
	})
	if got := findingFor(t, a, SegmentClientAccess); got.Severity != SeverityOK {
		t.Fatalf("a clean establishment leg reported %q: %s", got.Severity, got.Summary)
	}
}

// An echo leg's loss rate is a counted loss rate and must not be relabelled a
// proxy, or every finding would carry a caveat that does not apply to it.
func TestAnEchoLegIsNotReportedAsAProxy(t *testing.T) {
	a := Attribute(Evidence{
		Gateway:          reference("gw:12443", 0.0, 200),
		ClientReferences: []Reference{reference("baidu.com:443", 0.09, 12)},
	})
	if got := findingFor(t, a, SegmentClientAccess); strings.Contains(got.Detail, "retransmission timeout") {
		t.Fatalf("a counted loss rate was labelled a proxy: %s", got.Detail)
	}
}
