package pep

import (
	"sync"
	"sync/atomic"

	"github.com/apernet/quic-go"
	"github.com/bojieli/queqiao/internal/metrics"
)

// A QUIC connection's cumulative counters belong to the connection, not to
// any flow that borrows it. Connections here are pooled, so at any moment
// several lanes across several flows are reading the same numbers out of the
// same connection, and each of those flows publishes telemetry on its own
// timer. Whatever consumes those publications has to fold one connection's
// movement in exactly once, however many flows saw it.
//
// This file is where that happens. Each connection keeps the last reading
// anybody published, and a publication contributes only the distance from it.
// A second flow reading the same connection in the same interval therefore
// contributes nothing rather than a duplicate, and a flow that ends between
// two readings costs the total nothing, because what it already published was
// banked at the time.
type connTelemetry struct {
	id uint64
	mu sync.Mutex
	// previous is the last reading folded into the process totals. The zero
	// value is the correct starting point for a live connection: its counters
	// start at zero when it is established, so the first reading is itself the
	// distance travelled so far.
	previous metrics.QUICConnectionCounters
}

var (
	// connTelemetryMu serialises creation so two lanes racing on a new
	// connection cannot each install an entry and each bank the same first
	// reading.
	connTelemetryMu sync.Mutex
	// connTelemetries maps *quic.Conn to *connTelemetry. It follows the
	// lifetime of the connection: the entry is dropped once the connection's
	// context is done, the same way the coded bulk path is.
	connTelemetries sync.Map
	// connTelemetrySeq names connections for the lifetime of the process. It
	// is never reused, so an identifier is safe to deduplicate on within one
	// round of observations.
	connTelemetrySeq atomic.Uint64
)

// connTelemetryFor returns the bookkeeping for one connection, creating it on
// first sight.
//
// current is the reading that prompted the lookup, and it matters only for a
// connection that has already closed. Dropping the entry at close is what
// keeps this map bounded, but a lane can still be polled for a moment after
// the connection it sat on went away, and re-creating an entry from the zero
// baseline would read that connection's entire lifetime as movement and add
// all of it a second time. Seeding a posthumous entry at the current reading
// makes such a publication contribute nothing, which is the honest answer:
// everything this connection did was already banked while it was alive.
func connTelemetryFor(conn *quic.Conn, current metrics.QUICConnectionCounters) *connTelemetry {
	if conn == nil {
		return nil
	}
	if existing, ok := connTelemetries.Load(conn); ok {
		return existing.(*connTelemetry)
	}
	connTelemetryMu.Lock()
	defer connTelemetryMu.Unlock()
	if existing, ok := connTelemetries.Load(conn); ok {
		return existing.(*connTelemetry)
	}
	created := &connTelemetry{id: connTelemetrySeq.Add(1)}
	context := conn.Context()
	if context.Err() != nil {
		created.previous = current
		return created
	}
	connTelemetries.Store(conn, created)
	go func() {
		<-context.Done()
		connTelemetryMu.Lock()
		connTelemetries.Delete(conn)
		connTelemetryMu.Unlock()
	}()
	return created
}

// advance banks a reading and reports how far the connection moved since the
// last one.
func (t *connTelemetry) advance(current metrics.QUICConnectionCounters) metrics.QUICConnectionCounters {
	if t == nil {
		return metrics.QUICConnectionCounters{}
	}
	t.mu.Lock()
	defer t.mu.Unlock()
	delta := current.Advance(t.previous)
	// Re-baseline on every reading, including one that went backwards. A
	// counter that decreased is quic-go withdrawing a loss it decided was
	// reordering after all, or a pooled connection replaced by a fresh
	// generation; in both cases the new reading is the truth to measure the
	// next one against.
	t.previous = current
	return delta
}

// connectionCounters is the cumulative half of a lane's transport statistics,
// named at the scope it is actually measured at.
func connectionCounters(stats laneTransportStats) metrics.QUICConnectionCounters {
	return metrics.QUICConnectionCounters{
		BytesSent:               stats.bytesSent,
		BytesReceived:           stats.bytesReceived,
		PacketsSent:             stats.packetsSent,
		PacketsReceived:         stats.packetsReceived,
		LossObservedPackets:     stats.controller.PacketsLostObserved,
		CodedSources:            stats.codedSources,
		CodedRecovered:          stats.codedRecovered,
		CodedLost:               stats.codedLost,
		ControllerBytesLost:     stats.controller.BytesLost,
		ControllerPacketsLost:   stats.controller.PacketsLost,
		ControllerSamples:       stats.controller.Samples,
		ControllerNonAppSamples: stats.controller.NonAppSamples,
		ControllerAppSamples:    stats.controller.AppSamples,
		ControllerStateMisses:   stats.controller.StateMisses,
		ControllerZeroSamples:   stats.controller.ZeroSamples,
	}
}

// laneConnectionProvider is a lane that sits on a QUIC connection it may be
// sharing. Reporting the connection's identity alongside its movement is what
// lets one round of observations fold connection-scoped values in once rather
// than once per lane.
type laneConnectionProvider interface {
	connectionTelemetry(laneTransportStats) (uint64, metrics.QUICConnectionCounters)
}

func (c *quicStreamConn) connectionTelemetry(stats laneTransportStats) (uint64, metrics.QUICConnectionCounters) {
	if c == nil || c.conn == nil {
		return 0, metrics.QUICConnectionCounters{}
	}
	current := connectionCounters(stats)
	entry := connTelemetryFor(c.conn, current)
	if entry == nil {
		return 0, metrics.QUICConnectionCounters{}
	}
	return entry.id, entry.advance(current)
}
