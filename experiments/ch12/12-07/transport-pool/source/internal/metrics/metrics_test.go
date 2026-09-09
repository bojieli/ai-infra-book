package metrics

import (
	"math"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"
)

func TestRegistryCountersAndHandler(t *testing.T) {
	r := New()
	r.FlowStarted()
	r.ClassTransition(2)
	r.LaneFailure()
	r.LaneReplacement()
	r.Fallback()
	r.UDPPathUnavailable()
	r.EndpointTransportRaceFailure()
	r.TransientUDPSendError()
	r.UDPAssociationReconnect()
	r.UDPAssociationRescueFailure()
	r.FlowTimeout()
	r.ObserveQUIC(1, QUICObservation{
		Lanes: 2, LatestRTT: 250 * time.Millisecond, SmoothedRTT: 200 * time.Millisecond,
		ControllerKind: "bbr", ControllerMode: 3, ControllerMaxBandwidth: 1_000_000,
		ControllerLatestSample: 900_000, ControllerLatestAckRate: 1_100_000,
		ControllerLatestSendRate: 900_000, ControllerRound: 7,
		ControllerPacingRate: 1_250_000, ControllerCongestionWindow: 400_000,
		ControllerBytesInFlight: 200_000, ControllerMinRTT: 190 * time.Millisecond,
		ControllerInRecovery: true,
	})
	r.AddQUICConnectionCounters(QUICConnectionCounters{
		BytesSent: 100, BytesReceived: 200, PacketsSent: 80, PacketsReceived: 75,
		LossObservedPackets: 4, ControllerSamples: 12,
		ControllerNonAppSamples: 10, ControllerAppSamples: 2,
		ControllerStateMisses: 1, ControllerZeroSamples: 3,
	})
	r.FlowFinished(10, 20, false)
	r.FlowStarted()
	r.FlowFinished(1, 2, true)
	s := r.Snapshot()
	if s.ActiveFlows != 0 || s.FlowsStarted != 2 || s.FlowsCompleted != 1 || s.FlowsFailed != 1 || s.BytesUp != 11 || s.BytesDown != 22 {
		t.Fatalf("unexpected snapshot: %+v", s)
	}
	if s.UDPPathUnavailable != 1 || s.EndpointTransportRaceFailures != 1 || s.TransientUDPSendErrors != 1 {
		t.Fatalf("unexpected endpoint transport snapshot: %+v", s)
	}
	if s.QUICPacketsSent != 80 || s.QUICPacketsReceived != 75 || s.QUICLossObservedPackets != 4 {
		t.Fatalf("unexpected loss telemetry snapshot: %+v", s)
	}
	rec := httptest.NewRecorder()
	r.ServeHTTP(rec, httptest.NewRequest("GET", "/metrics", nil))
	if rec.Code != 200 || !strings.Contains(rec.Body.String(), "queqiao_lane_replacements_total 1") || !strings.Contains(rec.Body.String(), "queqiao_udp_path_unavailable_total 1") || !strings.Contains(rec.Body.String(), "queqiao_endpoint_transport_races_failed_total 1") || !strings.Contains(rec.Body.String(), "queqiao_udp_transient_send_errors_total 1") || !strings.Contains(rec.Body.String(), "queqiao_udp_association_reconnects_total 1") || !strings.Contains(rec.Body.String(), "queqiao_udp_association_rescue_failures_total 1") || !strings.Contains(rec.Body.String(), "queqiao_flow_timeouts_total 1") || !strings.Contains(rec.Body.String(), "queqiao_quic_smoothed_rtt_seconds 0.200000000") || !strings.Contains(rec.Body.String(), "queqiao_quic_packets_sent 80") || !strings.Contains(rec.Body.String(), "queqiao_quic_packets_received 75") || !strings.Contains(rec.Body.String(), "queqiao_quic_controller_kind{kind=\"bbr\"} 1") || !strings.Contains(rec.Body.String(), "queqiao_quic_controller_latest_sample_bytes_per_second 900000") || !strings.Contains(rec.Body.String(), "queqiao_quic_controller_latest_ack_rate_bytes_per_second 1100000") || !strings.Contains(rec.Body.String(), "queqiao_quic_controller_non_app_limited_samples_total 10") || !strings.Contains(rec.Body.String(), "queqiao_quic_controller_state_misses_total 1") || !strings.Contains(rec.Body.String(), "queqiao_quic_controller_round 7") || !strings.Contains(rec.Body.String(), "queqiao_quic_controller_pacing_rate_bytes_per_second 1250000") || !strings.Contains(rec.Body.String(), "queqiao_quic_controller_in_recovery 1") {
		t.Fatalf("unexpected exposition: %s", rec.Body.String())
	}
}

func TestFlowFinishedNeverMakesActiveGaugeNegative(t *testing.T) {
	r := New()
	const workers = 64
	var wg sync.WaitGroup
	wg.Add(workers)
	for i := 0; i < workers; i++ {
		go func() {
			defer wg.Done()
			r.FlowFinished(0, 0, true)
		}()
	}
	wg.Wait()
	if got := r.Snapshot().ActiveFlows; got != 0 {
		t.Fatalf("active gauge = %d, want 0", got)
	}
}

func TestMetricsHandlerRejectsMutationMethods(t *testing.T) {
	r := New()
	rec := httptest.NewRecorder()
	r.ServeHTTP(rec, httptest.NewRequest(http.MethodPost, "/metrics", nil))
	if rec.Code != http.StatusMethodNotAllowed {
		t.Fatalf("POST status = %d, want %d", rec.Code, http.StatusMethodNotAllowed)
	}
	r.RemoveQUIC(1)
	if got := r.Snapshot().QUICLanes; got != 0 {
		t.Fatalf("removed QUIC telemetry still reports %d lanes", got)
	}
}

func TestZeroValueRegistryIsSafe(t *testing.T) {
	var r Registry
	r.ObserveQUIC(7, QUICObservation{Lanes: 1, SmoothedRTT: time.Millisecond})
	if got := r.Snapshot().QUICLanes; got != 1 {
		t.Fatalf("zero-value registry lanes = %d, want 1", got)
	}
	r.RemoveQUIC(7)
}

// The rescue window is dropped rather than allowed to throttle the
// application. That trade has to be visible: once a flow has evicted part of
// its window, a lane failure fails the flow instead of recovering it, so an
// operator needs to see it happening.
func TestReplayAndIsolationCountersAreExported(t *testing.T) {
	registry := New()
	registry.ReplayBytes(1024)
	registry.ReplayBytes(512)
	registry.ReplayBytes(-1024)
	registry.BulkIsolated()

	got := registry.Snapshot()
	if got.ReplayBytesInUse != 512 {
		t.Fatalf("replay bytes in use = %d, want 512", got.ReplayBytesInUse)
	}
	if got.BulkIsolations != 1 {
		t.Fatalf("bulk isolations = %d, want 1", got.BulkIsolations)
	}

	recorder := httptest.NewRecorder()
	registry.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/metrics", nil))
	body := recorder.Body.String()
	for _, want := range []string{
		"queqiao_replay_bytes_in_use 512",
		"queqiao_bulk_isolations_total 1",
	} {
		if !strings.Contains(body, want) {
			t.Fatalf("metrics output is missing %q", want)
		}
	}
}

// The stall-watchdog and parallel-rescue counters are exported both in the
// snapshot and on /metrics, with the winning attempt as a bounded label.
func TestStallAndRescueCountersAreExported(t *testing.T) {
	registry := New()
	registry.FlowStallDetected()
	registry.StallSpareAttached()
	registry.LaneRescueAttempt()
	registry.LaneRescueAttempt()
	registry.LaneRescueAttempt()
	registry.LaneRescueWin(2)
	registry.LaneRescueWin(-1)
	registry.LaneRescueWin(RescueAttemptSlots)
	registry.LaneGraceExtended()

	got := registry.Snapshot()
	if got.FlowStallsDetected != 1 || got.StallSpareAttaches != 1 || got.LaneGraceExtensions != 1 {
		t.Fatalf("unexpected stall snapshot: %+v", got)
	}
	if got.LaneRescueAttempts != 3 {
		t.Fatalf("rescue attempts = %d, want 3", got.LaneRescueAttempts)
	}
	if got.LaneRescueWins != [RescueAttemptSlots]uint64{0, 0, 1} {
		t.Fatalf("rescue wins = %v, want only attempt 2", got.LaneRescueWins)
	}

	recorder := httptest.NewRecorder()
	registry.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/metrics", nil))
	body := recorder.Body.String()
	for _, want := range []string{
		"queqiao_flow_stalls_detected_total 1",
		"queqiao_stall_spare_attaches_total 1",
		"queqiao_lane_rescue_attempts_total 3",
		"queqiao_lane_rescue_wins_total{attempt=\"2\"} 1",
		"queqiao_lane_grace_extensions_total 1",
	} {
		if !strings.Contains(body, want) {
			t.Fatalf("metrics output is missing %q", want)
		}
	}
}

// Releasing more than was acquired must not drive the gauge negative, or the
// endpoint budget would appear to have capacity it does not have.
func TestReplayBytesGaugeCannotGoNegative(t *testing.T) {
	registry := New()
	registry.ReplayBytes(256)
	registry.ReplayBytes(-4096)
	if got := registry.Snapshot().ReplayBytesInUse; got != 0 {
		t.Fatalf("replay bytes in use = %d after an oversized release, want 0", got)
	}
}

// A nil registry is the "metrics disabled" case and must stay safe.
func TestNilRegistryIsSafe(t *testing.T) {
	var registry *Registry
	registry.ReplayBytes(10)
	registry.BulkIsolated()
}

// The exported round-trip estimate is a maximum over per-flow observations, so
// an entry that stops being refreshed and is never removed holds the estimate
// at whatever the path used to be for as long as the process lives. Expiring
// it is what keeps the aggregate a measurement rather than a record high.
func TestSnapshotExpiresQUICObservationsNobodyRefreshes(t *testing.T) {
	registry := New()
	now := time.Now()
	registry.clock = func() time.Time { return now }

	registry.ObserveQUIC(1, QUICObservation{Lanes: 2, LatestRTT: 900 * time.Millisecond, SmoothedRTT: 800 * time.Millisecond})
	now = now.Add(quicObservationTTL + time.Second)
	registry.ObserveQUIC(2, QUICObservation{Lanes: 1, LatestRTT: 320 * time.Millisecond, SmoothedRTT: 300 * time.Millisecond})

	got := registry.Snapshot()
	if got.QUICSmoothedRTT != 300*time.Millisecond || got.QUICLatestRTT != 320*time.Millisecond {
		t.Fatalf("stale observation still steers the aggregate: smoothed=%s latest=%s", got.QUICSmoothedRTT, got.QUICLatestRTT)
	}
	if got.QUICLanes != 1 {
		t.Fatalf("QUIC lanes = %d, want 1", got.QUICLanes)
	}
	if got.QUICObservationsExpired != 1 {
		t.Fatalf("expired observations = %d, want 1", got.QUICObservationsExpired)
	}

	// The expired entry is gone rather than re-examined on every scrape, and
	// the counter reports the one expiry instead of counting it again.
	registry.telemetryMu.Lock()
	remaining := len(registry.quicFlows)
	registry.telemetryMu.Unlock()
	if remaining != 1 {
		t.Fatalf("registry retains %d observations, want 1", remaining)
	}
	if again := registry.Snapshot(); again.QUICObservationsExpired != 1 {
		t.Fatalf("expired observations = %d on the second scrape, want 1", again.QUICObservationsExpired)
	}

	recorder := httptest.NewRecorder()
	registry.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/metrics", nil))
	if body := recorder.Body.String(); !strings.Contains(body, "queqiao_quic_observations_expired_total 1") {
		t.Fatalf("metrics output is missing the expiry counter: %s", body)
	}
}

// A flow that keeps publishing keeps its entry, however long it lives.
func TestSnapshotKeepsRefreshedQUICObservations(t *testing.T) {
	registry := New()
	now := time.Now()
	registry.clock = func() time.Time { return now }
	for i := 0; i < 10; i++ {
		registry.ObserveQUIC(1, QUICObservation{Lanes: 1, SmoothedRTT: 250 * time.Millisecond})
		now = now.Add(quicObservationTTL - time.Second)
		if got := registry.Snapshot(); got.QUICSmoothedRTT != 250*time.Millisecond || got.QUICObservationsExpired != 0 {
			t.Fatalf("refreshed observation expired after %d intervals: %+v", i, got)
		}
	}
}

// Account admission had no counter at all, so a gateway refusing every second
// flow an account opened was indistinguishable from a healthy one. The reasons
// are counted apart because they need different fixes: a flow ceiling too low
// for a browser is a misconfiguration, and a device limit reached is the
// policy working.
func TestAccountAdmissionRefusalsAreCountedByReason(t *testing.T) {
	registry := New()
	registry.AccountAdmissionRefused(AccountRefusalFlowLimit)
	registry.AccountAdmissionRefused(AccountRefusalFlowLimit)
	registry.AccountAdmissionRefused(AccountRefusalClientLimit)
	registry.AccountAdmissionRefused(AccountRefusalReasons) // out of range: ignored
	registry.AccountAdmissionRefused(AccountRefusal(-1))

	got := registry.Snapshot()
	if got.AccountAdmissionRefusals[AccountRefusalFlowLimit] != 2 || got.AccountAdmissionRefusals[AccountRefusalClientLimit] != 1 {
		t.Fatalf("refusals = %v", got.AccountAdmissionRefusals)
	}
	if got.AccountAdmissionRefusals[AccountRefusalUnauthorized] != 0 {
		t.Fatalf("unauthorized counted %d refusals it never saw", got.AccountAdmissionRefusals[AccountRefusalUnauthorized])
	}

	recorder := httptest.NewRecorder()
	registry.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/metrics", nil))
	body := recorder.Body.String()
	for _, want := range []string{
		"queqiao_account_admission_refused_total{reason=\"flow_limit\"} 2",
		"queqiao_account_admission_refused_total{reason=\"client_limit\"} 1",
		"queqiao_account_admission_refused_total{reason=\"unauthorized\"} 0",
	} {
		if !strings.Contains(body, want) {
			t.Fatalf("metrics output is missing %q:\n%s", want, body)
		}
	}
}

// The refusal reasons are counted apart because they send an operator to
// different places: a forgotten session is a peer whose flows are failing, a
// principal mismatch is a peer reaching for a session that is not its own.
func TestLaneJoinRefusalsAreCountedByReason(t *testing.T) {
	registry := New()
	registry.LaneJoinRefused(LaneJoinUnknownSession)
	registry.LaneJoinRefused(LaneJoinUnknownSession)
	registry.LaneJoinRefused(LaneJoinPrincipalMismatch)
	registry.LaneJoinRefused(LaneJoinReasons) // out of range: ignored
	registry.LaneJoinRefused(LaneJoinRefusal(-1))

	got := registry.Snapshot()
	if got.LaneJoinRefusals[LaneJoinUnknownSession] != 2 || got.LaneJoinRefusals[LaneJoinPrincipalMismatch] != 1 {
		t.Fatalf("refusals = %v", got.LaneJoinRefusals)
	}
	if got.LaneJoinRefusals[LaneJoinFlowMismatch] != 0 {
		t.Fatalf("flow mismatch counted %d refusals it never saw", got.LaneJoinRefusals[LaneJoinFlowMismatch])
	}

	recorder := httptest.NewRecorder()
	registry.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/metrics", nil))
	body := recorder.Body.String()
	for _, want := range []string{
		"queqiao_lane_join_refused_total{reason=\"unknown_session\"} 2",
		"queqiao_lane_join_refused_total{reason=\"principal_mismatch\"} 1",
		"queqiao_lane_join_refused_total{reason=\"flow_mismatch\"} 0",
		"queqiao_lane_join_refused_total{reason=\"lane_unavailable\"} 0",
	} {
		if !strings.Contains(body, want) {
			t.Fatalf("metrics output is missing %q:\n%s", want, body)
		}
	}

	var nilRegistry *Registry
	nilRegistry.LaneJoinRefused(LaneJoinUnknownSession)
}

// The QUIC counters used to be derived by summing what every live flow
// reported, and each flow reported the cumulative counters of the connections
// its lanes sat on. That made the exported total a function of which flows
// happened to be live at scrape time: it rose when a long-lived flow appeared
// and fell when one ended, so a dashboard differencing consecutive scrapes
// read the churn rather than the path. A counter that falls is not a counter.
func TestQUICCountersDoNotFallWhenTheFlowsReportingThemEnd(t *testing.T) {
	r := New()
	r.AddQUICConnectionCounters(QUICConnectionCounters{
		BytesSent: 4096, PacketsSent: 40, LossObservedPackets: 2, ControllerPacketsLost: 3,
	})
	r.ObserveQUIC(1, QUICObservation{Lanes: 2, SmoothedRTT: 200 * time.Millisecond})
	before := r.Snapshot()
	if before.QUICBytesSent != 4096 || before.QUICPacketsSent != 40 {
		t.Fatalf("counters not exported: %+v", before)
	}

	// Every flow ends. The connections they were reading may well still be
	// open, and what they already carried certainly still happened.
	r.RemoveQUIC(1)
	after := r.Snapshot()
	if after.QUICBytesSent != before.QUICBytesSent || after.QUICPacketsSent != before.QUICPacketsSent {
		t.Fatalf("counters fell when the flow ended: before=%d/%d after=%d/%d",
			before.QUICBytesSent, before.QUICPacketsSent, after.QUICBytesSent, after.QUICPacketsSent)
	}
	if after.QUICLossObservedPackets != 2 || after.QUICControllerPacketsLost != 3 {
		t.Fatalf("loss counters fell when the flow ended: %+v", after)
	}
	if after.QUICLanes != 0 {
		t.Fatalf("lane gauge = %d after the flow ended, want 0", after.QUICLanes)
	}
}

// A flow's telemetry entry expiring must not disturb the counters either. The
// gauges it was holding up go away, which is the point of the expiry; the
// bytes the connection carried do not.
func TestExpiringFlowTelemetryLeavesTheCountersAlone(t *testing.T) {
	r := New()
	now := time.Now()
	r.clock = func() time.Time { return now }
	r.ObserveQUIC(1, QUICObservation{Lanes: 1, SmoothedRTT: 300 * time.Millisecond})
	r.AddQUICConnectionCounters(QUICConnectionCounters{BytesSent: 900, PacketsSent: 9})
	now = now.Add(quicObservationTTL + time.Second)

	got := r.Snapshot()
	if got.QUICObservationsExpired != 1 || got.QUICLanes != 0 || got.QUICSmoothedRTT != 0 {
		t.Fatalf("stale gauges survived expiry: %+v", got)
	}
	if got.QUICBytesSent != 900 || got.QUICPacketsSent != 9 {
		t.Fatalf("expiry moved the counters: %+v", got)
	}
}

// Observing flows must not move the counters at all. Their numbers come from
// the connections, published once each, and a flow republishing every second
// would otherwise multiply them by the scrape rate.
func TestFlowObservationsDoNotContributeToTheCounters(t *testing.T) {
	r := New()
	for i := 0; i < 20; i++ {
		r.ObserveQUIC(uint64(i+1), QUICObservation{Lanes: 3, SmoothedRTT: time.Second})
	}
	if got := r.Snapshot(); got.QUICBytesSent != 0 || got.QUICPacketsSent != 0 || got.QUICLossObservedPackets != 0 {
		t.Fatalf("flow gauges leaked into the counters: %+v", got)
	}
}

// quic-go is allowed to withdraw a loss it later decides was reordering, and a
// pooled connection replaced by a new generation restarts at zero. Measuring
// the distance between two readings with unsigned arithmetic turns either into
// an enormous forward jump, which is the same fabricated-traffic failure this
// change exists to remove.
func TestConnectionCountersIgnoreBackwardMovement(t *testing.T) {
	first := QUICConnectionCounters{BytesSent: 10_000, PacketsSent: 100, LossObservedPackets: 9}
	// The peer acknowledges a packet previously declared lost.
	second := QUICConnectionCounters{BytesSent: 11_000, PacketsSent: 110, LossObservedPackets: 7}
	delta := second.Advance(first)
	if delta.BytesSent != 1000 || delta.PacketsSent != 10 {
		t.Fatalf("forward movement mismeasured: %+v", delta)
	}
	if delta.LossObservedPackets != 0 {
		t.Fatalf("withdrawn loss reported as %d packets of new loss", delta.LossObservedPackets)
	}

	// A fresh connection generation restarts every counter at zero.
	restarted := QUICConnectionCounters{BytesSent: 12, PacketsSent: 1}
	if delta := restarted.Advance(second); !delta.IsZero() {
		t.Fatalf("a restarted connection reported movement: %+v", delta)
	}
}

// The same reading published twice -- which is exactly what two flows sharing
// one pooled connection produce -- must count once.
func TestRepublishingTheSameConnectionReadingCountsOnce(t *testing.T) {
	r := New()
	reading := QUICConnectionCounters{BytesSent: 5000, PacketsSent: 50}
	var baseline QUICConnectionCounters
	for i := 0; i < 5; i++ {
		delta := reading.Advance(baseline)
		baseline = reading
		r.AddQUICConnectionCounters(delta)
	}
	if got := r.Snapshot(); got.QUICBytesSent != 5000 || got.QUICPacketsSent != 50 {
		t.Fatalf("one connection reading counted %d bytes / %d packets, want 5000/50",
			got.QUICBytesSent, got.QUICPacketsSent)
	}
}

// quic-go increments its own loss counters only inside its cubic sender, and
// this transport installs its own controller through SetCongestionControl, so
// queqiao_quic_packets_lost and queqiao_quic_bytes_lost could never leave zero.
// They were published anyway, and the dashboard divided by them. A counter
// that cannot be produced is worse than a missing one once it is monotonic,
// because it then reads as a measurement rather than as an absence.
func TestTheExpositionPublishesNoCounterItCannotProduce(t *testing.T) {
	r := New()
	r.AddQUICConnectionCounters(QUICConnectionCounters{
		PacketsSent: 1000, LossObservedPackets: 200, ControllerPacketsLost: 40,
	})
	rec := httptest.NewRecorder()
	r.ServeHTTP(rec, httptest.NewRequest("GET", "/metrics", nil))
	body := rec.Body.String()

	for _, dead := range []string{"queqiao_quic_packets_lost", "queqiao_quic_bytes_lost"} {
		for _, line := range strings.Split(body, "\n") {
			if name, _, ok := strings.Cut(line, " "); ok && name == dead {
				t.Errorf("%s is still published, and nothing can move it off zero", dead)
			}
		}
	}
	for _, want := range []string{
		"queqiao_quic_loss_observed_packets_total 200",
		"queqiao_quic_controller_packets_lost 40",
	} {
		if !strings.Contains(body, want) {
			t.Errorf("exposition is missing %q", want)
		}
	}
}

// The three loss figures are only readable together if they add up, and they
// have to keep adding up after the per-connection folding that banks them.
func TestObservedLossIsTheSumOfChargedAndSuppressedAcrossConnections(t *testing.T) {
	r := New()
	for _, c := range []QUICConnectionCounters{
		{PacketsSent: 500, LossObservedPackets: 100, ControllerPacketsLost: 100},
		{PacketsSent: 300, LossObservedPackets: 60, ControllerPacketsLost: 60},
	} {
		r.AddQUICConnectionCounters(c)
	}
	s := r.Snapshot()
	if s.QUICLossObservedPackets != 160 {
		t.Fatalf("observed = %d, want 160", s.QUICLossObservedPackets)
	}
	if s.QUICLossObservedPackets != s.QUICControllerPacketsLost {
		t.Fatalf("observed %d != charged %d; nothing is withheld from the controller any more",
			s.QUICLossObservedPackets, s.QUICControllerPacketsLost)
	}
	// And the loss rate a dashboard would derive is the channel's, not the
	// controller's. Publishing only the charged figure understated a fifth of
	// downstream erasure as a few percent.
	if observed := 100 * float64(s.QUICLossObservedPackets) / float64(s.QUICPacketsSent); observed < 15 {
		t.Fatalf("observed loss rate reads %.1f%% against 160 losses in 800 packets", observed)
	}
}

// A dead counter must not come back as a silently-zero one either: the totals
// only ever move forward from what a connection actually reported.
func TestLossTotalsOnlyMoveForward(t *testing.T) {
	r := New()
	r.AddQUICConnectionCounters(QUICConnectionCounters{LossObservedPackets: 50})
	before := r.Snapshot()
	// quic-go may withdraw a loss it decides was reordering, and a pooled
	// connection replaced by a fresh generation restarts at zero.
	r.AddQUICConnectionCounters(QUICConnectionCounters{})
	after := r.Snapshot()
	if after.QUICLossObservedPackets < before.QUICLossObservedPackets {
		t.Fatalf("observed total fell from %d to %d", before.QUICLossObservedPackets, after.QUICLossObservedPackets)
	}
}

// An erasure figure without a direction cannot be read. The one that used to be
// published was the controller's floor: biased low for pacing, a lower envelope
// for a connection's lifetime, and the only erasure number that left the
// process. On the live incident it read 1.76% while the channel erased 19.9%,
// so nothing on a dashboard could show what the code was being sized for.
func TestTheMeasuredErasureIsPublishedBesideTheFloorAndLabelledByDirection(t *testing.T) {
	r := New()
	r.ObserveQUIC(1, QUICObservation{
		ControllerKind: "erasure", ControllerErasure: 0.199,
	})
	s := r.Snapshot()
	if s.QUICErasureSend != 0.199 {
		t.Fatalf("measured send erasure = %v, want 0.199", s.QUICErasureSend)
	}

	rec := httptest.NewRecorder()
	r.ServeHTTP(rec, httptest.NewRequest("GET", "/metrics", nil))
	body := rec.Body.String()
	for _, want := range []string{
		`queqiao_erasure_ratio{direction="send"} 0.199000000`,
	} {
		if !strings.Contains(body, want) {
			t.Errorf("exposition is missing %q", want)
		}
	}
}

// Both figures arrive already pooled across the lanes of one endpoint pair, so
// folding several observations must select the worst pair rather than turning
// into a maximum over lanes -- which is what made the floor read "the worst
// single lane right now" and jump between 1.8% and 6.9% within minutes.
func TestErasureFoldsAcrossEndpointPairsNotLanes(t *testing.T) {
	r := New()
	r.ObserveQUIC(1, QUICObservation{ControllerKind: "erasure", ControllerErasure: 0.05})
	r.ObserveQUIC(2, QUICObservation{ControllerKind: "erasure", ControllerErasure: 0.30})
	r.ObserveQUIC(3, QUICObservation{ControllerKind: "erasure", ControllerErasure: 0.10})
	if s := r.Snapshot(); s.QUICErasureSend != 0.30 {
		t.Fatalf("send erasure = %v across three pairs, want the worst at 0.30", s.QUICErasureSend)
	}
}

// The residual is what the code could not repair and the session has to
// re-issue a round trip later. It is the number the motivating incident was
// made of -- 11% of the downstream payload -- and it had no metric at all: the
// decoders measured it per flow and it never left the process.
func TestTheReceiveDirectionIsPublishedFromItsOwnCounters(t *testing.T) {
	r := New()
	// A thousand symbols the peer sent: 800 arrived, 150 the code rebuilt, 50
	// left the window missing. That is 20% erasure with a 5% residual.
	r.AddQUICConnectionCounters(QUICConnectionCounters{
		CodedSources: 800, CodedRecovered: 150, CodedLost: 50,
	})
	s := r.Snapshot()
	if got := s.ReceiveErasure(); math.Abs(got-0.2) > 1e-9 {
		t.Fatalf("receive erasure = %v, want 0.2", got)
	}
	if got := s.ReceiveResidual(); math.Abs(got-0.05) > 1e-9 {
		t.Fatalf("receive residual = %v, want 0.05", got)
	}

	rec := httptest.NewRecorder()
	r.ServeHTTP(rec, httptest.NewRequest("GET", "/metrics", nil))
	body := rec.Body.String()
	for _, want := range []string{
		`queqiao_coded_symbols_total{outcome="arrived"} 800`,
		`queqiao_coded_symbols_total{outcome="recovered"} 150`,
		`queqiao_coded_symbols_total{outcome="lost"} 50`,
		`queqiao_erasure_ratio{direction="receive"} 0.200000000`,
		`queqiao_erasure_residual_ratio{direction="receive"} 0.050000000`,
	} {
		if !strings.Contains(body, want) {
			t.Errorf("exposition is missing %q", want)
		}
	}
}

// The ratios are derived from summed counters rather than averaged over flows,
// because a mean of per-flow ratios weights a flow that moved a kilobyte the
// same as one that moved a gigabyte.
func TestReceiveRatiosAreCountersOverCountersNotMeansOfRatios(t *testing.T) {
	r := New()
	// One tiny connection erasing everything, one large one erasing nothing.
	r.AddQUICConnectionCounters(QUICConnectionCounters{CodedSources: 0, CodedLost: 10})
	r.AddQUICConnectionCounters(QUICConnectionCounters{CodedSources: 9990, CodedLost: 0})
	s := r.Snapshot()
	// A mean of the two ratios would be 0.5. The honest figure is 10 in 10000.
	if got := s.ReceiveErasure(); got > 0.01 {
		t.Fatalf("receive erasure = %v; a mean of per-connection ratios would give 0.5, "+
			"the counters give 0.001", got)
	}
	if s.QUICCodedSources+s.QUICCodedRecovered+s.QUICCodedLost != 10000 {
		t.Fatalf("the denominator lost symbols: %d", s.QUICCodedSources+s.QUICCodedRecovered+s.QUICCodedLost)
	}
}

// An endpoint with no coded traffic reports zero rather than dividing by it.
func TestReceiveRatiosOnAPathWithNoCodedTraffic(t *testing.T) {
	s := New().Snapshot()
	if s.ReceiveErasure() != 0 || s.ReceiveResidual() != 0 {
		t.Fatalf("erasure %v residual %v with no symbols", s.ReceiveErasure(), s.ReceiveResidual())
	}
}
