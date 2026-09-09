package congestion

import (
	"testing"

	quiccongestion "github.com/apernet/quic-go/congestion"
)

// removeObsolete used to scan everything in flight on every congestion event.
// At 300 Mbit/s over a 200ms round trip that is about six thousand entries per
// acknowledgement, and a CPU profile of a 294 Mbit/s transfer attributed 13% of
// all time to that one loop.
func BenchmarkRemoveObsolete(b *testing.B) {
	const inFlight = 6000
	for b.Loop() {
		b.StopTimer()
		e := newTUICBandwidthEstimator()
		for i := range inFlight {
			e.packetStates[quiccongestion.PacketNumber(i)] = tuicPacketState{}
		}
		e.lowestState, e.lowestKnown = 0, true
		b.StartTimer()
		// QUIC acknowledges roughly every other packet, so a window is retired
		// over hundreds of congestion events rather than a handful. The scan
		// costs the whole window on each of them; the walk costs the window
		// once, however many events it is spread across.
		const acks = 300
		for k := 1; k <= acks; k++ {
			e.removeObsolete(quiccongestion.PacketNumber(k * inFlight / acks))
		}
	}
}

// The walk and the scan have to agree, including when a bulk prune has emptied
// the map behind the watermark's back.
func TestRemoveObsoleteMatchesAScan(t *testing.T) {
	for _, tc := range []struct {
		name    string
		prepare func(*tuicBandwidthEstimator)
		cut     quiccongestion.PacketNumber
	}{
		{"contiguous", func(e *tuicBandwidthEstimator) {}, 500},
		{"nothing to drop", func(e *tuicBandwidthEstimator) {}, 0},
		{"everything", func(e *tuicBandwidthEstimator) {}, 1000},
		{"past the end", func(e *tuicBandwidthEstimator) {}, 5000},
		{"after a bulk prune", func(e *tuicBandwidthEstimator) {
			for i := range 900 {
				delete(e.packetStates, quiccongestion.PacketNumber(i))
			}
		}, 950},
	} {
		t.Run(tc.name, func(t *testing.T) {
			build := func() *tuicBandwidthEstimator {
				e := newTUICBandwidthEstimator()
				for i := range 1000 {
					e.packetStates[quiccongestion.PacketNumber(i)] = tuicPacketState{}
				}
				e.lowestState, e.lowestKnown = 0, true
				tc.prepare(&e)
				return &e
			}
			fast := build()
			fast.removeObsolete(tc.cut)

			slow := build()
			for number := range slow.packetStates {
				if number < tc.cut {
					delete(slow.packetStates, number)
				}
			}
			if len(fast.packetStates) != len(slow.packetStates) {
				t.Fatalf("walk left %d states, scan left %d", len(fast.packetStates), len(slow.packetStates))
			}
			for number := range slow.packetStates {
				if _, ok := fast.packetStates[number]; !ok {
					t.Fatalf("walk dropped packet %d that the scan kept", number)
				}
			}
		})
	}
}
