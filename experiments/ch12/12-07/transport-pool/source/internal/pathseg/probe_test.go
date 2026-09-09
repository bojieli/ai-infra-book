package pathseg

import (
	"encoding/json"
	"errors"
	"net"
	"strings"
	"testing"
	"time"
)

// A leg that got nothing back has not measured total loss; it has measured
// nothing. Reporting 100% would make the strongest claim this tool can make out
// of the weakest evidence there is, and on a filtered path that is the ordinary
// outcome rather than a rare one.
func TestAnUnansweredRunIsBlockedRatherThanTotalLoss(t *testing.T) {
	leg := Summarize("echo:x", "client", "x", "icmp", Sequence{Arrived: []bool{false, false, false}})
	if !leg.Blocked {
		t.Fatal("a run with no replies was not marked blocked")
	}
	if leg.Usable() {
		t.Fatal("a blocked leg is being offered as evidence")
	}
	if leg.Loss != 1 {
		t.Fatalf("loss %v, want the raw 1 to remain readable", leg.Loss)
	}
}

func TestSummarizeReportsPercentilesAndPattern(t *testing.T) {
	seq := Sequence{
		Arrived: []bool{true, true, false, false, true, true, true, true, true, true},
		RTTs:    []float64{10, 12, 11, 13, 90, 12, 11, 14},
	}
	leg := Summarize("echo:x", "client", "x", "icmp", seq)
	if leg.Sent != 10 || leg.Arrived != 8 {
		t.Fatalf("sent %d arrived %d", leg.Sent, leg.Arrived)
	}
	if leg.Loss != 0.2 {
		t.Fatalf("loss %v, want 0.2", leg.Loss)
	}
	if leg.LongestBurst != 2 {
		t.Fatalf("longest burst %d, want 2", leg.LongestBurst)
	}
	if leg.MinMS != 10 {
		t.Fatalf("min %v", leg.MinMS)
	}
	// Nearest rank, the convention cmd/pathmeasure and doctor already report
	// with: the p99 of eight samples is the largest one that was actually
	// measured, not a number interpolated between two that were.
	if leg.P99MS != 90 {
		t.Fatalf("p99 %v, want the measured 90", leg.P99MS)
	}
	if leg.Blocked {
		t.Fatal("a run with replies was marked blocked")
	}
}

// The tail is the only loss signal an establishment leg has, because a lost
// handshake packet costs a whole retransmission timeout rather than a missing
// sample.
func TestTheTailRateCountsRetransmissionSizedOutliers(t *testing.T) {
	seq := Sequence{Arrived: []bool{true, true, true, true},
		RTTs: []float64{200, 205, 210, 1250}}
	leg := Summarize("establish:x", "client", "x", "tcp-connect", seq)
	if leg.TailRate != 0.25 {
		t.Fatalf("tail rate %v, want 0.25", leg.TailRate)
	}
}

func TestEstablishTimesARealListener(t *testing.T) {
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
	seq := Establish(t.Context(), EstablishOptions{Target: ln.Addr().String(), Count: 3, Timeout: 2 * time.Second})
	leg := Summarize("establish:local", "client", ln.Addr().String(), "tcp-connect", seq)
	if leg.Sent != 3 || leg.Arrived != 3 {
		t.Fatalf("sent %d arrived %d against a listener that accepted everything", leg.Sent, leg.Arrived)
	}
}

func TestEstablishReportsARefusedPortAsFailureNotAsAHang(t *testing.T) {
	// Port 1 on loopback, which nothing listens on and which refuses fast.
	seq := Establish(t.Context(), EstablishOptions{Target: "127.0.0.1:1", Count: 2, Timeout: 2 * time.Second})
	leg := Summarize("establish:refused", "client", "127.0.0.1:1", "tcp-connect", seq)
	if leg.Sent != 2 {
		t.Fatalf("sent %d, want both attempts recorded", leg.Sent)
	}
	if !leg.Blocked {
		t.Fatal("a refused port was not reported as unreachable")
	}
}

// Both instruments have to reach one machine or the comparison between them is
// between two paths. Address overrides the host and keeps the port.
func TestEstablishHonoursAPinnedAddress(t *testing.T) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = ln.Close() }()
	go func() {
		c, err := ln.Accept()
		if err == nil {
			_ = c.Close()
		}
	}()
	_, port, err := net.SplitHostPort(ln.Addr().String())
	if err != nil {
		t.Fatal(err)
	}
	seq := Establish(t.Context(), EstablishOptions{
		Target: net.JoinHostPort("no-such-host.invalid", port), Address: "127.0.0.1",
		Count: 1, Timeout: 2 * time.Second})
	if len(seq.Arrived) != 1 || !seq.Arrived[0] {
		t.Fatalf("the pinned address was not used: %+v", seq)
	}
}

func TestSplitReferenceDefaultsToTheFilteredPort(t *testing.T) {
	host, hostPort := splitReference("baidu.com")
	if host != "baidu.com" || hostPort != "baidu.com:443" {
		t.Fatalf("got %q and %q", host, hostPort)
	}
	host, hostPort = splitReference("baidu.com:80")
	if host != "baidu.com" || hostPort != "baidu.com:80" {
		t.Fatalf("got %q and %q", host, hostPort)
	}
}

func TestResolveAcceptsAnAddressWithoutAskingTheResolver(t *testing.T) {
	ip, err := Resolve(t.Context(), "203.0.113.7", "")
	if err != nil || ip.String() != "203.0.113.7" {
		t.Fatalf("got %v, %v", ip, err)
	}
}

// The echo probe is exercised against loopback, which is the only target a test
// may assume exists. Where the host will not hand out an echo socket at all --
// an ordinary Linux default -- that is a fact about the host, and the caller's
// contract is that it says so rather than reporting a dead path.
func TestPingMeasuresLoopbackOrSaysItCannot(t *testing.T) {
	seq, err := Ping(t.Context(), PingOptions{
		Target: net.ParseIP("127.0.0.1"), Count: 3,
		Interval: 20 * time.Millisecond, Timeout: time.Second,
	})
	if err != nil {
		if errors.Is(err, ErrICMPUnavailable) {
			t.Skip("this host does not hand out ICMP echo sockets: " + err.Error())
		}
		t.Fatal(err)
	}
	if len(seq.Arrived) != 3 {
		t.Fatalf("sent 3, accounted for %d", len(seq.Arrived))
	}
	leg := Summarize("echo:loopback", "client", "127.0.0.1", "icmp", seq)
	if leg.Blocked {
		t.Skip("loopback echo is filtered on this host")
	}
	if leg.Loss > 0 {
		t.Fatalf("loopback lost %v of three probes", leg.Loss)
	}
}

func TestPingRefusesARunItCannotDescribe(t *testing.T) {
	if _, err := Ping(t.Context(), PingOptions{Target: net.ParseIP("127.0.0.1"), Count: 0}); err == nil {
		t.Fatal("a zero-length run was accepted")
	}
	if _, err := Ping(t.Context(), PingOptions{Count: 3}); err == nil {
		t.Fatal("a run with no target was accepted")
	}
}

func TestErrICMPUnavailableIsIdentifiable(t *testing.T) {
	// The caller falls back to establishment on this error and only on this
	// error, so it has to survive the wrapping listenICMP does to it.
	wrapped := errors.Join(ErrICMPUnavailable, errors.New("operation not permitted"))
	if !errors.Is(wrapped, ErrICMPUnavailable) {
		t.Fatal("the sentinel does not survive wrapping")
	}
	if !strings.Contains(ErrICMPUnavailable.Error(), "ICMP") {
		t.Fatal("the sentinel does not name what was unavailable")
	}
}

// The whole report has to survive JSON encoding, because that is the form meant
// to be attached to a bug. A leg with no arrivals used to produce a burst factor
// of Inf times zero -- NaN -- which JSON cannot encode, so one filtered anchor
// made the entire --json run fail with nothing on stdout.
func TestABlockedLegLeavesTheReportSerialisable(t *testing.T) {
	blocked := Summarize("echo:x", "client", "x:443", "icmp",
		Sequence{Arrived: []bool{false, false, false, false}})
	if !finite(blocked.BurstFactor) {
		t.Fatalf("burst factor is not a number: %v", blocked.BurstFactor)
	}
	if blocked.BurstFactor != 0 {
		t.Fatalf("a run with no arrivals reported a pattern: %v", blocked.BurstFactor)
	}
	if _, err := json.Marshal(blocked); err != nil {
		t.Fatalf("a blocked leg cannot be serialised: %v", err)
	}

	// The same guard has to hold for a whole report, which is what actually
	// broke: an Evidence containing one blocked anchor.
	e := Evidence{
		Gateway: Reference{Target: "gw:12443",
			Echo: Summarize("echo:gw", "client", "gw:12443", "icmp",
				Sequence{Arrived: []bool{true, true}, RTTs: []float64{200, 210}})},
		ClientReferences: []Reference{{Target: "x:443", Echo: blocked}},
	}
	if _, err := json.Marshal(struct {
		Evidence    Evidence    `json:"evidence"`
		Attribution Attribution `json:"attribution"`
	}{e, Attribute(e)}); err != nil {
		t.Fatalf("a report containing a blocked anchor cannot be serialised: %v", err)
	}
}

// A metrics page carrying NaN would put the same unserialisable value into the
// report by a different door.
func TestMetricsRejectsValuesThatAreNotNumbers(t *testing.T) {
	view, err := ParseMetrics(strings.NewReader(
		"queqiao_erasure_ratio{direction=\"send\"} NaN\n" +
			"queqiao_erasure_ratio{direction=\"receive\"} +Inf\n" +
			"queqiao_quic_lanes 2\n"))
	if err != nil {
		t.Fatal(err)
	}
	if !finite(view.SendErasure) || !finite(view.ReceiveErasure) {
		t.Fatalf("a non-numeric sample reached the report: %+v", view)
	}
	if view.Lanes != 2 {
		t.Fatalf("the good sample on the same page was dropped: %d", view.Lanes)
	}
	if _, err := json.Marshal(view); err != nil {
		t.Fatalf("the view cannot be serialised: %v", err)
	}
}
