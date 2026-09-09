package pep

import (
	"context"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/protocol"
)

// laneRate installs a synthetic rate/RTT sample so lane selection can be
// exercised without a QUIC connection. sendRate caches these fields, and a
// fresh sample timestamp keeps the cache from being refreshed from a nil
// transport.
func laneRate(lane *mpLane, bytesPerSecond float64, rtt time.Duration) {
	lane.rateMu.Lock()
	lane.rateSampled, lane.rateBytes, lane.rateRTT = time.Now(), bytesPerSecond, rtt
	lane.rateMu.Unlock()
}

// A flow's data plane is one lane, so there is no spilling to another when it
// is full: the flow really is limited by the connection carrying it, and it
// waits.
//
// This replaces a test that asserted the opposite. With a flow's data striped
// across lanes, committing to one and then waiting for a queue slot let a
// single slow lane throttle the whole flow while another sat idle -- the
// producer stopped, so no later frame was ever offered to the idle lane and
// the scheduler never saw the imbalance it existed to correct. Striping is
// deleted, and with it both the failure and the machinery that avoided it.
func TestAFullDataLaneIsWaitedOnRatherThanSpilled(t *testing.T) {
	flow := &multipathFlow{
		ctx: context.Background(), done: make(chan struct{}), laneErr: make(chan laneFailure, 4),
		chunkSize: defaultChunkSize, lanes: map[uint64]*mpLane{},
	}
	full := &mpLane{
		id: 0, writeQ: make(chan laneFrame, 1), writeSlots: make(chan struct{}, 1),
		writeDone: make(chan struct{}),
	}
	idle := &mpLane{
		id: 1, writeQ: make(chan laneFrame, 4), writeSlots: make(chan struct{}, 4),
		writeDone: make(chan struct{}),
	}
	flow.lanes[0], flow.lanes[1] = full, idle
	laneRate(full, 1<<30, time.Millisecond)
	laneRate(idle, 1<<20, 10*time.Millisecond)
	full.writeSlots <- struct{}{}
	full.writeQ <- laneFrame{frame: protocol.Frame{Header: protocol.Header{Version: protocol.Version, Type: protocol.TypeData}}}

	frame := protocol.Frame{
		Header:  protocol.Header{Version: protocol.Version, Type: protocol.TypeData, Class: protocol.ClassBulk},
		Payload: make([]byte, 16),
	}
	done := make(chan error, 1)
	go func() { done <- flow.enqueueOnHealthyLane(context.Background(), frame, true) }()
	select {
	case err := <-done:
		t.Fatalf("enqueue returned %v with the data lane full; it should have waited", err)
	case <-time.After(250 * time.Millisecond):
	}
	if len(idle.writeQ) != 0 {
		t.Fatalf("the other lane received %d frames; a flow's data must not spread across lanes", len(idle.writeQ))
	}
	// Drain a slot so the blocked enqueue completes and the goroutine ends.
	<-full.writeQ
	<-full.writeSlots
	select {
	case err := <-done:
		if err != nil {
			t.Fatalf("enqueue after the lane drained: %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("enqueue did not complete once its lane had room")
	}
	if len(full.writeQ) != 1 {
		t.Fatalf("the data lane received %d frames, want the waited-for frame", len(full.writeQ))
	}
}
