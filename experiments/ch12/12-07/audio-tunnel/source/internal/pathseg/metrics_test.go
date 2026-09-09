package pathseg

import (
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/metrics"
)

// The parser is checked against the registry that writes the page rather than
// against a string copied out of it once. A hand-written fixture keeps passing
// after a metric is renamed, and the failure it would then hide is silent: this
// command would report a clean client-to-gateway segment on a path that was
// erasing half of everything, because the field it reads no longer exists and
// zero is what a missing sample parses to.
func TestParseMetricsReadsWhatTheRegistryWrites(t *testing.T) {
	r := metrics.New()
	r.ObserveQUIC(1, metrics.QUICObservation{
		Lanes:       2,
		SmoothedRTT: 214 * time.Millisecond,
		LatestRTT:   230 * time.Millisecond,
		// The registry aggregates every controller-derived field only for an
		// observation that names its controller, erasure and minimum round
		// trip included. A fixture that leaves this empty parses to zero
		// everywhere and proves nothing.
		ControllerKind:       "queqiao",
		ControllerMinRTT:     197 * time.Millisecond,
		ControllerErasure:    0.031,
		ControllerDelayBrake: 0.25,
	})
	r.AddQUICConnectionCounters(metrics.QUICConnectionCounters{
		PacketsSent:         120_000,
		LossObservedPackets: 3_700,
		CodedSources:        85_800,
		CodedRecovered:      13_100,
		CodedLost:           1_100,
	})
	r.FlowStarted()

	srv := httptest.NewServer(r)
	defer srv.Close()

	view, err := FetchMetrics(t.Context(), srv.URL+"/metrics")
	if err != nil {
		t.Fatal(err)
	}
	if !view.Present {
		t.Fatal("the parser read no samples from a live registry")
	}
	if view.SendErasure != 0.031 {
		t.Fatalf("send erasure %v, want 0.031", view.SendErasure)
	}
	// The receive direction is derived by the registry from the three coded
	// outcomes, and the two ratios are different questions: what the path
	// erased, and what the code could not put back.
	if got, want := view.ReceiveErasure, 14200.0/100000.0; !closeTo(got, want, 1e-6) {
		t.Fatalf("receive erasure %v, want %v", got, want)
	}
	if got, want := view.ReceiveResidual, 1100.0/100000.0; !closeTo(got, want, 1e-6) {
		t.Fatalf("receive residual %v, want %v", got, want)
	}
	if view.MinRTTMS != 197 {
		t.Fatalf("min rtt %v, want 197", view.MinRTTMS)
	}
	if view.SmoothedRTTMS != 214 {
		t.Fatalf("smoothed rtt %v, want 214", view.SmoothedRTTMS)
	}
	if view.Lanes != 2 || view.ActiveFlows != 1 {
		t.Fatalf("lanes %d flows %d, want 2 and 1", view.Lanes, view.ActiveFlows)
	}
	if view.CodedSymbols != 100_000 {
		t.Fatalf("coded symbols %d, want 100000", view.CodedSymbols)
	}
	if view.PacketsSent != 120_000 || view.LossObserved != 3_700 {
		t.Fatalf("packet counters %d/%d", view.PacketsSent, view.LossObserved)
	}
	if !view.ReceiveSignificant() || !view.SendSignificant() {
		t.Fatal("a session with a hundred thousand symbols was called insignificant")
	}
}

// An idle tunnel publishes ratios drawn from almost nothing. Quoting those as
// a measurement would manufacture a finding out of a session that has not
// carried enough traffic to have an opinion.
func TestAnIdleSessionIsNotQuotedAsAMeasurement(t *testing.T) {
	r := metrics.New()
	r.AddQUICConnectionCounters(metrics.QUICConnectionCounters{
		PacketsSent: 10, CodedSources: 8, CodedLost: 2,
	})
	srv := httptest.NewServer(r)
	defer srv.Close()

	view, err := FetchMetrics(t.Context(), srv.URL+"/metrics")
	if err != nil {
		t.Fatal(err)
	}
	if view.ReceiveErasure != 0.2 {
		t.Fatalf("receive erasure %v, want the raw 0.2", view.ReceiveErasure)
	}
	if view.ReceiveSignificant() || view.SendSignificant() {
		t.Fatal("a ten-packet session was treated as evidence")
	}
}

func TestParseMetricsRejectsAPageWithNoSamples(t *testing.T) {
	if _, err := ParseMetrics(strings.NewReader("# just a comment\n\n")); err == nil {
		t.Fatal("a page with no samples parsed successfully")
	}
}

func closeTo(a, b, tol float64) bool { return a-b < tol && b-a < tol }
