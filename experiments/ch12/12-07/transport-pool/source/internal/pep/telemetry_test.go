package pep

import (
	"context"
	"io"
	"net"
	"testing"
	"time"

	wancongestion "github.com/bojieli/queqiao/internal/congestion"
	"github.com/bojieli/queqiao/internal/metrics"
)

// statsConn is a lane transport that reports fixed QUIC connection statistics.
type statsConn struct {
	stats laneTransportStats
}

func (c *statsConn) Read([]byte) (int, error)           { return 0, io.EOF }
func (c *statsConn) Write(p []byte) (int, error)        { return len(p), nil }
func (c *statsConn) Close() error                       { return nil }
func (c *statsConn) transportStats() laneTransportStats { return c.stats }

// A flow's telemetry entry is removed when the flow ends, but the lane
// managers poll the same snapshot on a timer and stop only once the flow
// signals done. A publication from that window reinstates an entry which
// nothing will ever remove or refresh again, and since the registry reports
// round-trip time as a maximum over entries, one such entry pins the exported
// estimate at that flow's final measurement for the life of the process.
func TestFinishedFlowStopsPublishingQUICTelemetry(t *testing.T) {
	registry := metrics.New()
	local, remote := net.Pipe()
	t.Cleanup(func() { _ = local.Close(); _ = remote.Close() })
	flow := newMultipathFlow(context.Background(), local, [16]byte{1}, 7, 0, 0, 0, nil, registry)
	flow.lanes[0] = &mpLane{id: 0, kind: TransportQUIC, fc: newFrameConn(&statsConn{
		stats: laneTransportStats{latestRTT: 900 * time.Millisecond, smoothedRTT: 800 * time.Millisecond},
	})}

	flow.snapshot()
	if got := registry.Snapshot(); got.QUICLanes != 1 || got.QUICSmoothedRTT != 800*time.Millisecond {
		t.Fatalf("live flow telemetry lanes=%d smoothed=%s, want 1 and 800ms", got.QUICLanes, got.QUICSmoothedRTT)
	}

	// What flow.run does while a lane manager is between its own done check
	// and its next snapshot.
	flow.finished.Store(true)
	registry.RemoveQUIC(flow.telemetryID)

	flow.snapshot()
	if got := registry.Snapshot(); got.QUICLanes != 0 || got.QUICSmoothedRTT != 0 {
		t.Fatalf("finished flow republished telemetry: lanes=%d smoothed=%s", got.QUICLanes, got.QUICSmoothedRTT)
	}
}

// pooledStatsConn is a lane sitting on a QUIC connection it shares with other
// lanes and other flows, which is what the client connection pool hands out.
// Every such lane reads the same cumulative counters out of the same
// connection.
type pooledStatsConn struct {
	stats  laneTransportStats
	shared *connTelemetry
}

func (c *pooledStatsConn) Read([]byte) (int, error)           { return 0, io.EOF }
func (c *pooledStatsConn) Write(p []byte) (int, error)        { return len(p), nil }
func (c *pooledStatsConn) Close() error                       { return nil }
func (c *pooledStatsConn) transportStats() laneTransportStats { return c.stats }

func (c *pooledStatsConn) connectionTelemetry(stats laneTransportStats) (uint64, metrics.QUICConnectionCounters) {
	return c.shared.id, c.shared.advance(connectionCounters(stats))
}

func pooledLane(id uint64, shared *connTelemetry, stats laneTransportStats) *mpLane {
	return &mpLane{id: id, kind: TransportQUIC, fc: newFrameConn(&pooledStatsConn{stats: stats, shared: shared})}
}

// A flow routinely runs several lanes over one pooled connection. The
// connection's counters describe the connection, so folding them in once per
// lane reports traffic and loss that never happened -- and the congestion
// window it reports is likewise the connection's, not a number to be added up
// per stream sharing it.
func TestPooledConnectionCountsOncePerConnectionNotPerLane(t *testing.T) {
	registry := metrics.New()
	local, remote := net.Pipe()
	t.Cleanup(func() { _ = local.Close(); _ = remote.Close() })
	flow := newMultipathFlow(context.Background(), local, [16]byte{1}, 7, 0, 0, 0, nil, registry)

	shared := &connTelemetry{id: 1}
	stats := laneTransportStats{
		smoothedRTT: 200 * time.Millisecond,
		bytesSent:   10_000, packetsSent: 100,
		controller: wancongestion.ControllerTelemetry{
			Kind: "erasure", CongestionWindow: 400_000, PacingRate: 1_250_000,
			PacketsLost: 4, PacketsLostObserved: 4, Samples: 12,
		},
	}
	flow.lanes[0] = pooledLane(0, shared, stats)
	flow.lanes[1] = pooledLane(1, shared, stats)
	flow.lanes[2] = pooledLane(2, shared, stats)

	flow.snapshot()

	got := registry.Snapshot()
	if got.QUICLanes != 3 {
		t.Fatalf("lane gauge = %d, want the true lane count 3", got.QUICLanes)
	}
	if got.QUICBytesSent != 10_000 || got.QUICPacketsSent != 100 {
		t.Fatalf("three lanes on one connection counted %d bytes / %d packets, want 10000/100",
			got.QUICBytesSent, got.QUICPacketsSent)
	}
	if got.QUICLossObservedPackets != 4 || got.QUICControllerPacketsLost != 4 {
		t.Fatalf("loss multiplied by the lane count: packets=%d controller=%d, want 4/4",
			got.QUICLossObservedPackets, got.QUICControllerPacketsLost)
	}
	if got.QUICControllerSamples != 12 {
		t.Fatalf("controller samples = %d, want 12", got.QUICControllerSamples)
	}
	if got.QUICControllerCongestionWindow != 400_000 || got.QUICControllerPacingRate != 1_250_000 {
		t.Fatalf("connection gauges added per lane: cwnd=%d pacing=%d, want 400000/1250000",
			got.QUICControllerCongestionWindow, got.QUICControllerPacingRate)
	}
}

// Two flows sharing one pooled connection each publish on their own timer.
// Whichever reads it first banks the movement; the other must add nothing.
func TestTwoFlowsSharingAConnectionCountItOnce(t *testing.T) {
	registry := metrics.New()
	shared := &connTelemetry{id: 1}
	stats := laneTransportStats{
		bytesSent: 8_000, packetsSent: 80,
		controller: wancongestion.ControllerTelemetry{Kind: "erasure", Samples: 5},
	}

	for _, flowID := range []uint64{7, 9} {
		local, remote := net.Pipe()
		t.Cleanup(func() { _ = local.Close(); _ = remote.Close() })
		flow := newMultipathFlow(context.Background(), local, [16]byte{1}, flowID, 0, 0, 0, nil, registry)
		flow.lanes[0] = pooledLane(0, shared, stats)
		flow.snapshot()
	}

	if got := registry.Snapshot(); got.QUICBytesSent != 8_000 || got.QUICPacketsSent != 80 || got.QUICControllerSamples != 5 {
		t.Fatalf("a shared connection counted once per flow: bytes=%d packets=%d samples=%d, want 8000/80/5",
			got.QUICBytesSent, got.QUICPacketsSent, got.QUICControllerSamples)
	}
}

// Publishing on a timer must not multiply a connection by the scrape rate:
// only what moved between two readings is new.
func TestRepeatedPublicationCountsOnlyWhatMoved(t *testing.T) {
	registry := metrics.New()
	local, remote := net.Pipe()
	t.Cleanup(func() { _ = local.Close(); _ = remote.Close() })
	flow := newMultipathFlow(context.Background(), local, [16]byte{1}, 7, 0, 0, 0, nil, registry)

	shared := &connTelemetry{id: 1}
	lane := &pooledStatsConn{shared: shared, stats: laneTransportStats{bytesSent: 1_000, packetsSent: 10}}
	flow.lanes[0] = &mpLane{id: 0, kind: TransportQUIC, fc: newFrameConn(lane)}

	flow.snapshot()
	flow.snapshot()
	flow.snapshot()
	if got := registry.Snapshot(); got.QUICBytesSent != 1_000 {
		t.Fatalf("an idle connection published three times counted %d bytes, want 1000", got.QUICBytesSent)
	}

	// The connection carries more, and only the difference is new.
	lane.stats.bytesSent = 2_500
	lane.stats.packetsSent = 25
	flow.snapshot()
	if got := registry.Snapshot(); got.QUICBytesSent != 2_500 || got.QUICPacketsSent != 25 {
		t.Fatalf("counters = %d bytes / %d packets, want 2500/25", got.QUICBytesSent, got.QUICPacketsSent)
	}
}

// A finished flow stops publishing its gauges, but the connection under it may
// still be carrying other flows, and what it moved before this flow's last
// reading is not the finished flow's to withdraw.
func TestFinishedFlowStillBanksConnectionMovement(t *testing.T) {
	registry := metrics.New()
	local, remote := net.Pipe()
	t.Cleanup(func() { _ = local.Close(); _ = remote.Close() })
	flow := newMultipathFlow(context.Background(), local, [16]byte{1}, 7, 0, 0, 0, nil, registry)

	shared := &connTelemetry{id: 1}
	lane := &pooledStatsConn{shared: shared, stats: laneTransportStats{bytesSent: 600, packetsSent: 6}}
	flow.lanes[0] = &mpLane{id: 0, kind: TransportQUIC, fc: newFrameConn(lane)}

	flow.finished.Store(true)
	registry.RemoveQUIC(flow.telemetryID)
	flow.snapshot()

	got := registry.Snapshot()
	if got.QUICLanes != 0 {
		t.Fatalf("finished flow republished its gauges: lanes=%d", got.QUICLanes)
	}
	if got.QUICBytesSent != 600 {
		t.Fatalf("connection movement discarded with the finished flow: %d bytes, want 600", got.QUICBytesSent)
	}
}
