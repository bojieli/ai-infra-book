package pep

import (
	"context"
	"time"
)

// Lane admission, and why there is no flow-level congestion window above it.
//
// RFC 6356's linked increase used to sit here, bounding what a flow could
// commit across all its lanes so that a multipath flow took no more of a
// shared bottleneck than a single-path one would. It went when the fairness
// obligation did, and the QUIC lanes it coupled went after it: a QUIC flow's
// data is carried by one connection. The explicit TCP-only bundle below does
// not recreate that controller; each socket remains kernel paced. See
// docs/DESIGN.md.
//
// What is left is per-lane, and is not a congestion window. The transport
// already has one of those, and two nested controllers would be a mistake.

const (
	// laneSampleInterval is how often lane congestion state is read. It is
	// well inside a round trip on the paths this targets, so a loss episode is
	// seen while it still means something.
	laneSampleInterval = 50 * time.Millisecond
	// tcpStripingOutstandingBytes limits byte-offset commitment, not network
	// flight. A TLS write returns when the kernel socket buffer accepts bytes,
	// so without this bound the first TCP lane can own the whole read-ahead
	// window before a joined lane gets work. One MiB is several BDPs on the
	// measured 200-250 ms fallback path and keeps BBR application-fed while
	// leaving ready chunks for every other lane.
	tcpStripingOutstandingBytes = 1024 * 1024
)

// laneAdmission answers the scheduler's admission questions for one flow.
//
// A lane's write-ahead allowance is what its own transport says the path can
// hold. Negotiated TCP striping adds an acknowledgement-side commitment bound
// because a kernel TCP write is buffered rather than congestion-paced from the
// caller's perspective.
type laneAdmission struct {
	flow *multipathFlow
}

func (w *laneAdmission) Lane(laneID uint64, _ uint64) int {
	allowance := minLaneQueueBytes
	if lane := w.flow.laneByID(laneID); lane != nil {
		allowance = lane.windowBytes()
	}
	return allowance
}

func (w *laneAdmission) Outstanding(laneID uint64, _ uint64) int {
	if !w.flow.tcpStriping.Load() {
		return 0
	}
	lane := w.flow.laneByID(laneID)
	if lane == nil || lane.kind != TransportTCP {
		return 0
	}
	return tcpStripingOutstandingBytes
}

// Total is zero: independent TCP congestion controllers must not be coupled by
// another congestion window. Memory remains bounded by scheduler retention.
func (w *laneAdmission) Total() int { return 0 }

// laneByID returns a lane by identifier, or nil.
func (f *multipathFlow) laneByID(laneID uint64) *mpLane {
	f.lanesMu.RLock()
	defer f.lanesMu.RUnlock()
	return f.lanes[laneID]
}

// sampleLaneCongestion reads each lane's transport for the telemetry the path
// model and the lane trace are built from.
func (f *multipathFlow) sampleLaneCongestion(ctx context.Context) {
	ticker := time.NewTicker(laneSampleInterval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-f.done:
			return
		case <-ticker.C:
		}
		for _, lane := range f.healthyLanes() {
			provider, ok := lane.fc.transport().(laneStatsProvider)
			if !ok {
				continue
			}
			stats := provider.transportStats()
			traceLane(f, lane.id, stats)
		}
	}
}
