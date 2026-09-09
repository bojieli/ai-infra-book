package stripe

import (
	"bytes"
	"context"
	"errors"
	"io"
	"math/rand"
	"sync"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/memlimit"
)

func TestConcurrentSchedulersShareOneFixedMemoryBudget(t *testing.T) {
	const (
		chunkSize = 4 * 1024
		flows     = 16
	)
	memory := memlimit.New(2 * chunkSize)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	var wg sync.WaitGroup
	errs := make(chan error, flows)
	for range flows {
		scheduler := New(bytes.NewReader(make([]byte, 8*chunkSize)), Config{
			ChunkSize: chunkSize, LaneWindow: 8, MaxOutstanding: 32,
			MaxOutstandingBytes: 8 * chunkSize, Memory: memory,
		})
		wg.Add(1)
		go func() {
			defer wg.Done()
			defer scheduler.Close()
			for {
				chunk, err := scheduler.Next(ctx, 1, 0)
				if err != nil {
					errs <- err
					return
				}
				if chunk == nil {
					return
				}
				scheduler.Complete(1, chunk)
			}
		}()
	}
	wg.Wait()
	close(errs)
	for err := range errs {
		t.Fatal(err)
	}
	got := memory.Snapshot()
	if got.Used != 0 || got.Peak > got.Capacity || got.Peak != 2*chunkSize {
		t.Fatalf("shared memory = %+v", got)
	}
}

// drainLanes runs n lane workers, each taking chunks and completing them after
// the delay its rate implies. It returns the bytes each lane carried, which is
// the share the pacing produced.
func drainLanes(t *testing.T, s *Scheduler, rates []time.Duration) (map[uint64]uint64, []byte) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()

	var mu sync.Mutex
	carried := make(map[uint64]uint64)
	received := make(map[uint64][]byte)

	var wg sync.WaitGroup
	for i := range rates {
		wg.Add(1)
		go func(laneID uint64, perByte time.Duration) {
			defer wg.Done()
			for {
				chunk, err := s.Next(ctx, laneID, 0)
				if err != nil || chunk == nil {
					return
				}
				if perByte > 0 {
					time.Sleep(perByte * time.Duration(len(chunk.Data)))
				}
				mu.Lock()
				carried[laneID] += uint64(len(chunk.Data))
				if len(chunk.Data) > 0 {
					received[chunk.Offset] = append([]byte(nil), chunk.Data...)
				}
				mu.Unlock()
				s.Complete(laneID, chunk)
			}
		}(uint64(i), rates[i])
	}
	wg.Wait()

	mu.Lock()
	defer mu.Unlock()
	var out []byte
	for offset := uint64(0); ; {
		data, ok := received[offset]
		if !ok {
			break
		}
		out = append(out, data...)
		offset += uint64(len(data))
	}
	return carried, out
}

func after(d time.Duration) func() time.Duration { return func() time.Duration { return d } }

func TestSchedulerDeliversEveryByteInOrder(t *testing.T) {
	payload := make([]byte, 512*1024)
	rand.New(rand.NewSource(1)).Read(payload)
	s := New(bytes.NewReader(payload), Config{ChunkSize: 8 * 1024, LaneWindow: 2})
	defer s.Close()

	_, got := drainLanes(t, s, []time.Duration{0, 0, 0})
	if !bytes.Equal(got, payload) {
		t.Fatalf("reassembled %d bytes, want %d", len(got), len(payload))
	}
}

// The property the whole design exists for: a lane's share is whatever it can
// carry. Nothing measures the lanes or divides the work between them -- a fast
// lane simply comes back for more sooner.
func TestFastLaneCarriesMoreWithoutBeingMeasured(t *testing.T) {
	payload := make([]byte, 256*1024)
	s := New(bytes.NewReader(payload), Config{ChunkSize: 4 * 1024, LaneWindow: 1})
	defer s.Close()

	// Lane 0 is eight times slower per byte than lanes 1 and 2.
	carried, got := drainLanes(t, s, []time.Duration{
		800 * time.Nanosecond, 100 * time.Nanosecond, 100 * time.Nanosecond,
	})
	if len(got) != len(payload) {
		t.Fatalf("reassembled %d bytes, want %d", len(got), len(payload))
	}
	slow, fast := carried[0], carried[1]+carried[2]
	if slow == 0 {
		t.Fatal("slow lane carried nothing; it should still contribute")
	}
	if fast <= slow*3 {
		t.Fatalf("fast lanes carried %d, slow lane %d: pacing did not follow capacity", fast, slow)
	}
}

// A lane that stops entirely must not be able to hold up the transfer. Under
// the design this replaces, the bytes committed to that lane's queue were
// already sequenced and the receiver could not deliver past them.
func TestStalledLaneDoesNotHoldUpTheTransfer(t *testing.T) {
	payload := make([]byte, 128*1024)
	rand.New(rand.NewSource(2)).Read(payload)
	s := New(bytes.NewReader(payload), Config{
		ChunkSize: 4 * 1024, LaneWindow: 2, RetransmitAfter: after(50 * time.Millisecond),
	})
	defer s.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()

	// A supervisor re-offers chunks the stalled lane is sitting on.
	done := make(chan struct{})
	go func() {
		ticker := time.NewTicker(10 * time.Millisecond)
		defer ticker.Stop()
		for {
			select {
			case <-done:
				return
			case <-ticker.C:
				s.ReissueExpired()
			}
		}
	}()
	defer close(done)

	var mu sync.Mutex
	received := make(map[uint64][]byte)

	// Lane 0 takes a chunk and never completes it. Its goroutine never
	// returns, which is the point: only the healthy lane's progress is waited
	// on, because a real stalled lane does not politely exit either.
	go func() {
		if _, err := s.Next(ctx, 0, 0); err != nil {
			return
		}
		<-ctx.Done()
	}()

	// Lane 1 works normally and must be able to finish the whole transfer.
	finished := make(chan struct{})
	go func() {
		defer close(finished)
		for {
			chunk, err := s.Next(ctx, 1, 0)
			if err != nil || chunk == nil {
				return
			}
			mu.Lock()
			if len(chunk.Data) > 0 {
				received[chunk.Offset] = append([]byte(nil), chunk.Data...)
			}
			mu.Unlock()
			s.Complete(1, chunk)
		}
	}()

	select {
	case <-finished:
	case <-time.After(15 * time.Second):
		t.Fatal("a single stalled lane blocked the transfer")
	}

	mu.Lock()
	defer mu.Unlock()
	var out []byte
	for offset := uint64(0); ; {
		data, ok := received[offset]
		if !ok {
			break
		}
		out = append(out, data...)
		offset += uint64(len(data))
	}
	if !bytes.Equal(out, payload) {
		t.Fatalf("healthy lane delivered %d of %d bytes", len(out), len(payload))
	}
}

// A lane that dies must cost only what it was holding, and that must be
// recoverable on any other lane.
func TestRetiredLaneReleasesItsChunks(t *testing.T) {
	payload := make([]byte, 64*1024)
	rand.New(rand.NewSource(3)).Read(payload)
	s := New(bytes.NewReader(payload), Config{ChunkSize: 4 * 1024, LaneWindow: 3})
	defer s.Close()

	ctx := context.Background()
	// Lane 0 takes its window and dies.
	var held []*Chunk
	for i := 0; i < 3; i++ {
		chunk, err := s.Next(ctx, 0, 0)
		if err != nil || chunk == nil {
			t.Fatalf("lane 0 next: %v", err)
		}
		held = append(held, chunk)
	}
	s.RetireLane(0)

	// Every chunk it held must be available to lane 1.
	seen := make(map[uint64]bool)
	for range held {
		chunk, err := s.Next(ctx, 1, 0)
		if err != nil || chunk == nil {
			t.Fatalf("lane 1 next: %v", err)
		}
		seen[chunk.Offset] = true
		s.Complete(1, chunk)
	}
	for _, chunk := range held {
		if !seen[chunk.Offset] {
			t.Fatalf("chunk at offset %d was lost with the lane", chunk.Offset)
		}
	}
}

// A chunk must never be re-issued on the lane already carrying it: that is the
// one lane whose failure the copy would not survive.
func TestReissueAvoidsTheLaneAlreadyCarryingIt(t *testing.T) {
	now := time.Now()
	clock := func() time.Time { return now }
	payload := make([]byte, 12*1024)
	s := New(bytes.NewReader(payload), Config{
		ChunkSize: 4 * 1024, LaneWindow: 4, RetransmitAfter: after(time.Second), Now: clock,
	})
	defer s.Close()

	ctx := context.Background()
	first, err := s.Next(ctx, 0, 0)
	if err != nil || first == nil {
		t.Fatalf("next: %v", err)
	}
	// A second lane, because re-offering a chunk is offering it to another
	// lane: with only the one that already holds it reliably, there is nobody
	// for the copy to go to and it is not made.
	if _, err := s.Next(ctx, 1, 0); err != nil {
		t.Fatalf("second lane: %v", err)
	}
	now = now.Add(2 * time.Second)
	if n := s.ReissueExpired(); n != 2 {
		t.Fatalf("re-offered %d chunks, want both lanes'", n)
	}
	// Lane 0 must not be handed the same chunk back.
	next, err := s.Next(ctx, 0, 0)
	if err != nil {
		t.Fatalf("next: %v", err)
	}
	if next != nil && next.Offset == first.Offset {
		t.Fatal("re-issued a chunk on the lane already carrying it")
	}
	// Lane 1 must be.
	other, err := s.Next(ctx, 1, 0)
	if err != nil || other == nil {
		t.Fatalf("lane 1 next: %v", err)
	}
	if other.Offset != first.Offset {
		t.Fatalf("lane 1 got offset %d, want the expired chunk at %d", other.Offset, first.Offset)
	}
	// And either copy completing must release both lanes' hold on that chunk.
	// Lane 0 legitimately still carries the chunk it was handed instead, so
	// what matters is that its charge for *this* chunk was released.
	s.mu.Lock()
	before := s.laneLoad[0]
	s.mu.Unlock()
	s.Complete(1, other)
	s.mu.Lock()
	after := s.laneLoad[0]
	s.mu.Unlock()
	if after != before-1 {
		t.Fatalf("lane 0 charge went %d -> %d; completing elsewhere must release its attempt", before, after)
	}
}

func TestReliableReissueBurstCopiesOnlyTheOldestExpiredChunk(t *testing.T) {
	now := time.Now()
	s := New(bytes.NewReader(make([]byte, 16*1024)), Config{
		ChunkSize: 4 * 1024, LaneWindow: 4, RetransmitAfter: after(time.Second),
		ReliableReissueBurst: 1, Now: func() time.Time { return now },
	})
	defer s.Close()
	ctx := context.Background()
	first, err := s.Next(ctx, 0, 0)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := s.Next(ctx, 0, 0); err != nil {
		t.Fatal(err)
	}
	if _, err := s.Next(ctx, 1, 0); err != nil {
		t.Fatal(err)
	}
	now = now.Add(2 * time.Second)
	if got := s.ReissueExpired(); got != 1 {
		t.Fatalf("reissued %d reliable chunks, want the bounded oldest one", got)
	}
	copy, err := s.Next(ctx, 1, 0)
	if err != nil {
		t.Fatal(err)
	}
	if copy.Offset != first.Offset {
		t.Fatalf("reissued offset %d, want oldest %d", copy.Offset, first.Offset)
	}
}

// Memory must stay bounded when lanes are slower than the source.
func TestOutstandingIsBounded(t *testing.T) {
	payload := make([]byte, 1024*1024)
	s := New(bytes.NewReader(payload), Config{
		ChunkSize: 4 * 1024, LaneWindow: 2, MaxOutstanding: 8,
	})
	defer s.Close()

	ctx := context.Background()
	var held []*Chunk
	for i := 0; i < 2; i++ {
		chunk, err := s.Next(ctx, 0, 0)
		if err != nil || chunk == nil {
			t.Fatalf("next: %v", err)
		}
		held = append(held, chunk)
	}
	// Give the producer time to read ahead as far as it will.
	time.Sleep(100 * time.Millisecond)
	s.mu.Lock()
	buffered := len(s.pending) + len(s.live)
	s.mu.Unlock()
	if buffered > 8 {
		t.Fatalf("buffered %d chunks, want at most MaxOutstanding=8", buffered)
	}
	for _, c := range held {
		s.Complete(0, c)
	}
}

// The end of the stream must be ordered with the data, not race ahead of it.
func TestFinalChunkIsTheLastByteRange(t *testing.T) {
	payload := make([]byte, 10*1024)
	s := New(bytes.NewReader(payload), Config{ChunkSize: 4 * 1024, LaneWindow: 8})
	defer s.Close()

	ctx := context.Background()
	var last *Chunk
	var end uint64
	for {
		chunk, err := s.Next(ctx, 0, 0)
		if err != nil {
			t.Fatalf("next: %v", err)
		}
		if chunk == nil {
			break
		}
		if chunk.End() > end {
			end = chunk.End()
		}
		if chunk.Final {
			last = chunk
		}
		s.Complete(0, chunk)
	}
	if last == nil {
		t.Fatal("stream never produced a final chunk")
	}
	if last.End() != end {
		t.Fatalf("final chunk ends at %d but the stream ends at %d", last.End(), end)
	}
	if end != uint64(len(payload)) {
		t.Fatalf("stream ended at %d, want %d", end, len(payload))
	}
}

func TestSourceErrorIsReported(t *testing.T) {
	want := errors.New("source broke")
	s := New(&failingReader{err: want}, Config{ChunkSize: 1024, LaneWindow: 1})
	defer s.Close()

	_, err := s.Next(context.Background(), 0, 0)
	if !errors.Is(err, want) {
		t.Fatalf("next error = %v, want %v", err, want)
	}
}

type failingReader struct {
	err  error
	once bool
}

func (r *failingReader) Read(p []byte) (int, error) {
	if r.once {
		return 0, r.err
	}
	r.once = true
	return 0, r.err
}

func TestCloseReleasesWaiters(t *testing.T) {
	pr, pw := io.Pipe()
	defer pw.Close()
	s := New(pr, Config{ChunkSize: 1024, LaneWindow: 1})

	errs := make(chan error, 1)
	go func() {
		_, err := s.Next(context.Background(), 0, 0)
		errs <- err
	}()
	time.Sleep(50 * time.Millisecond)
	s.Close()
	select {
	case err := <-errs:
		if !errors.Is(err, ErrClosed) {
			t.Fatalf("next after close = %v, want ErrClosed", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("Close did not release a waiting lane")
	}
}

func TestNextRespectsContext(t *testing.T) {
	pr, pw := io.Pipe()
	defer pw.Close()
	s := New(pr, Config{ChunkSize: 1024, LaneWindow: 1})
	defer s.Close()

	ctx, cancel := context.WithCancel(context.Background())
	errs := make(chan error, 1)
	go func() {
		_, err := s.Next(ctx, 0, 0)
		errs <- err
	}()
	time.Sleep(50 * time.Millisecond)
	cancel()
	select {
	case err := <-errs:
		if !errors.Is(err, context.Canceled) {
			t.Fatalf("next after cancel = %v, want context.Canceled", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("Next ignored context cancellation")
	}
}

// The lane declares how much it can hold, so a lane whose capacity collapses
// stops being handed work without the scheduler measuring it.
func TestLaneWindowInBytesBoundsCommitment(t *testing.T) {
	payload := make([]byte, 256*1024)
	s := New(bytes.NewReader(payload), Config{ChunkSize: 4 * 1024, LaneWindow: 64})
	defer s.Close()

	ctx := context.Background()
	// A 16 KiB window admits four 4 KiB chunks and no more.
	var held []*Chunk
	for i := 0; i < 4; i++ {
		chunk, err := s.Next(ctx, 0, 16*1024)
		if err != nil || chunk == nil {
			t.Fatalf("chunk %d: %v", i, err)
		}
		held = append(held, chunk)
	}
	done := make(chan struct{})
	go func() {
		defer close(done)
		s.Next(ctx, 0, 16*1024)
	}()
	select {
	case <-done:
		t.Fatal("lane was handed a fifth chunk beyond its declared window")
	case <-time.After(100 * time.Millisecond):
	}
	// Completing one frees exactly one chunk's worth of room.
	s.Complete(0, held[0])
	select {
	case <-done:
	case <-time.After(2 * time.Second):
		t.Fatal("completing a chunk did not free window space")
	}
}

// A window smaller than one chunk must not deadlock the lane.
func TestTinyWindowStillAdmitsOneChunk(t *testing.T) {
	payload := make([]byte, 64*1024)
	s := New(bytes.NewReader(payload), Config{ChunkSize: 8 * 1024, LaneWindow: 4})
	defer s.Close()

	chunk, err := s.Next(context.Background(), 0, 128)
	if err != nil || chunk == nil {
		t.Fatalf("a window below one chunk stalled the lane: %v", err)
	}
}

func TestDoneClosesWhenEveryChunkLands(t *testing.T) {
	payload := make([]byte, 32*1024)
	s := New(bytes.NewReader(payload), Config{ChunkSize: 4 * 1024, LaneWindow: 8})
	defer s.Close()

	ctx := context.Background()
	go func() {
		for {
			chunk, err := s.Next(ctx, 0, 0)
			if err != nil || chunk == nil {
				return
			}
			s.Complete(0, chunk)
		}
	}()
	select {
	case <-s.Done():
	case <-time.After(5 * time.Second):
		t.Fatal("Done never closed after the stream was fully delivered")
	}
}

// Done must not close while a chunk is still outstanding, or a caller would
// send a FIN ahead of data still in flight.
func TestDoneWaitsForOutstandingChunks(t *testing.T) {
	payload := make([]byte, 8*1024)
	s := New(bytes.NewReader(payload), Config{ChunkSize: 4 * 1024, LaneWindow: 8})
	defer s.Close()

	// Take everything the scheduler has, including the marker that ends the
	// stream. Stopping after a fixed count assumed the producer would still
	// have a chunk pending when it reached EOF -- true only when the lane is
	// slower than the producer, which the race detector's slowdown inverts.
	ctx := context.Background()
	var held []*Chunk
	for {
		probeCtx, cancel := context.WithTimeout(ctx, 200*time.Millisecond)
		chunk, err := s.Next(probeCtx, 0, 0)
		cancel()
		if chunk == nil {
			if err != nil && !errors.Is(err, context.DeadlineExceeded) {
				t.Fatalf("next: %v", err)
			}
			break
		}
		held = append(held, chunk)
	}
	if len(held) < 2 {
		t.Fatalf("took %d chunks, want at least the two the payload makes", len(held))
	}
	select {
	case <-s.Done():
		t.Fatal("Done closed with chunks still outstanding")
	case <-time.After(100 * time.Millisecond):
	}
	for _, c := range held {
		s.Complete(0, c)
	}
	select {
	case <-s.Done():
	case <-time.After(5 * time.Second):
		t.Fatal("Done never closed")
	}
}

// The deadlock this guards against: every lane's window fills with chunks that
// cannot be acknowledged because an earlier chunk is missing, so no lane has
// room to carry the missing one and the flow stops with every lane waiting on
// work none of them is allowed to take.
func TestRecoveredChunkBypassesAFullLaneWindow(t *testing.T) {
	payload := make([]byte, 64*1024)
	s := New(bytes.NewReader(payload), Config{ChunkSize: 4 * 1024, LaneWindow: 64})
	defer s.Close()

	ctx := context.Background()
	window := 8 * 1024 // two chunks

	// Lane 0 takes the head chunk and then dies holding it.
	head, err := s.Next(ctx, 0, window)
	if err != nil || head == nil {
		t.Fatalf("head: %v", err)
	}
	// Lane 1 fills its window with later chunks.
	for i := 0; i < 2; i++ {
		if c, err := s.Next(ctx, 1, window); err != nil || c == nil {
			t.Fatalf("lane 1 chunk %d: %v", i, err)
		}
	}
	// Next blocks when the lane is full, so prove that with a deadline rather
	// than by expecting a nil return.
	probeCtx, probeCancel := context.WithTimeout(ctx, 100*time.Millisecond)
	if c, _ := s.Next(probeCtx, 1, window); c != nil {
		probeCancel()
		t.Fatal("lane 1 exceeded its window before recovery was needed")
	}
	probeCancel()
	s.RetireLane(0)

	// Lane 1 is at its window, but the recovered head is what unblocks
	// delivery, so it must be admitted anyway.
	got, err := s.Next(ctx, 1, window)
	if err != nil {
		t.Fatalf("recovery: %v", err)
	}
	if got == nil {
		t.Fatal("recovered chunk was not admitted; every lane would wait forever")
	}
	if got.Offset != head.Offset {
		t.Fatalf("admitted offset %d, want the recovered head at %d", got.Offset, head.Offset)
	}
}

// fixedWindows is a Windows that reports constant limits.
type fixedWindows struct{ lane, total int }

func (w fixedWindows) Lane(uint64, uint64) int { return w.lane }
func (w fixedWindows) Total() int              { return w.total }

type ackBoundWindows struct {
	fixedWindows
	outstanding int
}

func (w ackBoundWindows) Outstanding(uint64, uint64) int { return w.outstanding }

func TestAcknowledgementWindowPreventsOneBufferedLaneClaimingAllWork(t *testing.T) {
	s := New(bytes.NewReader(make([]byte, 64*1024)), Config{
		ChunkSize: 4 * 1024, LaneWindow: 64, MaxOutstanding: 64,
		Windows: ackBoundWindows{fixedWindows: fixedWindows{lane: 64 * 1024}, outstanding: 8 * 1024},
	})
	defer s.Close()
	ctx := context.Background()
	first, err := s.Next(ctx, 0, 0)
	if err != nil {
		t.Fatal(err)
	}
	s.Wrote(0, first)
	second, err := s.Next(ctx, 0, 0)
	if err != nil {
		t.Fatal(err)
	}
	s.Wrote(0, second)

	blocked, cancel := context.WithTimeout(ctx, 25*time.Millisecond)
	defer cancel()
	if _, err := s.Next(blocked, 0, 0); !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("buffered lane exceeded its acknowledgement window: %v", err)
	}
	if _, err := s.Next(ctx, 1, 0); err != nil {
		t.Fatalf("idle second lane could not take ready work: %v", err)
	}

	s.Complete(0, first)
	if _, err := s.Next(ctx, 0, 0); err != nil {
		t.Fatalf("acknowledgement did not release lane window: %v", err)
	}
}

// The flow window is what stops N lanes claiming N times a single connection's
// share, so it must bind even when every individual lane still has room.
func TestFlowWindowBoundsEveryLaneTogether(t *testing.T) {
	payload := make([]byte, 1024*1024)
	s := New(bytes.NewReader(payload), Config{
		ChunkSize: 4 * 1024, LaneWindow: 64,
		// Each lane could hold 64 KiB, but the flow may only hold 16 KiB.
		Windows: fixedWindows{lane: 64 * 1024, total: 16 * 1024},
	})
	defer s.Close()

	ctx := context.Background()
	admitted := 0
	for lane := uint64(0); lane < 4; lane++ {
		for {
			probeCtx, cancel := context.WithTimeout(ctx, 50*time.Millisecond)
			chunk, _ := s.Next(probeCtx, lane, 0)
			cancel()
			if chunk == nil {
				break
			}
			admitted++
		}
	}
	if admitted > 4 {
		t.Fatalf("admitted %d chunks (%d KiB) against a 16 KiB flow window",
			admitted, admitted*4)
	}
	if admitted == 0 {
		t.Fatal("flow window admitted nothing at all")
	}
}

// A collapsed flow window must not deadlock the transfer: a lane holding
// nothing is always allowed one chunk.
func TestCollapsedFlowWindowStillMakesProgress(t *testing.T) {
	payload := make([]byte, 64*1024)
	s := New(bytes.NewReader(payload), Config{
		ChunkSize: 8 * 1024, LaneWindow: 8,
		Windows: fixedWindows{lane: 1, total: 1},
	})
	defer s.Close()

	chunk, err := s.Next(context.Background(), 0, 0)
	if err != nil || chunk == nil {
		t.Fatalf("a collapsed window stalled the flow entirely: %v", err)
	}
}

// A lane is paced by its transport, not by the peer's acknowledgement: what
// bounds admission is how much the lane has been handed that its transport has
// not yet taken. Chunks already written stay retained so they can be re-issued
// if the lane dies, and must not go on bounding the lane.
func TestAdmissionCountsUnwrittenBytesNotUnacknowledgedOnes(t *testing.T) {
	payload := make([]byte, 512*1024)
	s := New(bytes.NewReader(payload), Config{
		ChunkSize: 4 * 1024, LaneWindow: 1024,
		Windows: fixedWindows{lane: 8 * 1024},
	})
	defer s.Close()

	ctx := context.Background()
	var carried []*Chunk
	for {
		probeCtx, cancel := context.WithTimeout(ctx, 50*time.Millisecond)
		chunk, _ := s.Next(probeCtx, 1, 0)
		cancel()
		if chunk == nil {
			break
		}
		carried = append(carried, chunk)
	}
	if len(carried) == 0 {
		t.Fatal("admitted nothing at all")
	}
	if len(carried) > 3 {
		t.Fatalf("admitted %d chunks against an 8 KiB write-ahead bound", len(carried))
	}

	// Reporting them written frees the lane even though none is acknowledged.
	for _, chunk := range carried {
		s.Wrote(1, chunk)
	}
	if _, _, queued := s.LaneOutstanding(1); queued != 0 {
		t.Fatalf("lane still holds %d unwritten bytes after every chunk was written", queued)
	}
	if _, retained, _ := s.LaneOutstanding(1); retained == 0 {
		t.Fatal("written chunks were not retained for re-issue")
	}
	probeCtx, cancel := context.WithTimeout(ctx, 50*time.Millisecond)
	next, _ := s.Next(probeCtx, 1, 0)
	cancel()
	if next == nil {
		t.Fatal("a lane whose transport took everything was not handed more work")
	}
}

// A chunk can be waiting in the ready set and in flight at the same time: that
// is what re-offering a slow lane's chunk means. If it arrives by the first
// route, the copy in the ready set is bytes the peer already has, and sending
// them again is pure overhead the retransmit counter does not even record.
func TestCompletedChunkLeavesTheReadySet(t *testing.T) {
	now := time.Now()
	clock := func() time.Time { return now }
	payload := make([]byte, 8*1024)
	s := New(bytes.NewReader(payload), Config{
		ChunkSize: 4 * 1024, LaneWindow: 4, RetransmitAfter: after(time.Second), Now: clock,
	})
	defer s.Close()

	ctx := context.Background()
	first, err := s.Next(ctx, 0, 0)
	if err != nil || first == nil {
		t.Fatalf("next: %v", err)
	}
	// A second lane, so that the first lane's chunk has somewhere to be
	// re-offered to.
	if _, err := s.Next(ctx, 1, 0); err != nil {
		t.Fatalf("second lane: %v", err)
	}
	now = now.Add(2 * time.Second)
	if n := s.ReissueExpired(); n != 2 {
		t.Fatalf("re-offered %d chunks, want both lanes'", n)
	}
	// It arrives on the lane that already had it, while the re-offered copy is
	// still waiting for a lane to pick up.
	s.Complete(0, first)

	// No lane may now be handed those bytes.
	for lane := uint64(1); lane < 3; lane++ {
		for {
			probeCtx, cancel := context.WithTimeout(ctx, 20*time.Millisecond)
			chunk, _ := s.Next(probeCtx, lane, 0)
			cancel()
			if chunk == nil {
				break
			}
			if chunk.Offset == first.Offset {
				t.Fatal("a completed chunk was handed to a lane again")
			}
			s.Complete(lane, chunk)
		}
	}
}

// A flow with one unreliable lane must still recover a chunk that lane lost.
//
// The rule that a chunk is never re-offered to the lane already carrying it is
// right for a reliable lane, which will deliver it or die. It is fatal for an
// unreliable one: a coded datagram path repairs most loss and not all, and
// with a single lane there is nowhere else to offer the chunk, so the flow
// waits forever for bytes that are simply gone.
func TestAnUnreliableLaneMayCarryAChunkTwice(t *testing.T) {
	now := time.Now()
	scheduler := New(bytes.NewReader([]byte("12345678")), Config{
		ChunkSize: 8, LaneWindow: 4, MaxOutstanding: 8,
		RetransmitAfter: after(time.Second),
		Reliable:        func(uint64) bool { return false },
		Now:             func() time.Time { return now },
	})
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	first, err := scheduler.Next(ctx, 1, 1<<20)
	if err != nil || first == nil {
		t.Fatalf("no chunk offered to the only lane: %v", err)
	}
	scheduler.Wrote(1, first)
	// The lane lost it. Nothing acknowledges, the deadline passes, and the
	// scheduler re-queues it.
	now = now.Add(2 * time.Second)
	if reissued := scheduler.ReissueExpired(); reissued != 1 {
		t.Fatalf("re-issued %d chunks, want the one that was lost", reissued)
	}
	again, err := scheduler.Next(ctx, 1, 1<<20)
	if err != nil || again == nil {
		t.Fatalf("the only lane was not offered the chunk it lost (%v): a "+
			"single-lane flow over an unreliable substrate can never recover", err)
	}
	if again.Offset != first.Offset {
		t.Fatalf("re-offered offset %d, want the lost %d", again.Offset, first.Offset)
	}
	if again.attempt == first.attempt {
		t.Fatal("replacement reused the retired attempt identity")
	}
	scheduler.Wrote(1, again)

	// A second erasure is the same state transition as the first, not an
	// attempt-count boundary. Retry again while retaining only one live copy.
	now = now.Add(2 * time.Second)
	if reissued := scheduler.ReissueExpired(); reissued != 1 {
		t.Fatalf("re-issued %d chunks after the second loss, want one", reissued)
	}
	third, err := scheduler.Next(ctx, 1, 1<<20)
	if err != nil || third == nil || third.Offset != first.Offset {
		t.Fatalf("third attempt = %v, %v; want offset %d", third, err, first.Offset)
	}
	if chunks, retained, _ := scheduler.LaneOutstanding(1); chunks != 1 || retained != 8 {
		t.Fatalf("live attempts = %d chunks/%d bytes, want one bounded 8-byte attempt", chunks, retained)
	}
}

// And a reliable lane must still refuse it, or every stream lane pays for a
// retransmission QUIC has already made.
func TestAReliableLaneRefusesTheSameChunkTwice(t *testing.T) {
	now := time.Now()
	scheduler := New(bytes.NewReader([]byte("12345678")), Config{
		ChunkSize: 8, LaneWindow: 4, MaxOutstanding: 8,
		RetransmitAfter: after(time.Second),
		Now:             func() time.Time { return now },
	})
	ready, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	if _, err := scheduler.Next(ready, 1, 1<<20); err != nil {
		t.Fatalf("no chunk offered: %v", err)
	}
	now = now.Add(2 * time.Second)
	scheduler.ReissueExpired()

	// It is back in the ready set but this lane must not be given it, so the
	// only outcome available is the context expiring.
	blocked, stop := context.WithTimeout(context.Background(), 300*time.Millisecond)
	defer stop()
	if again, err := scheduler.Next(blocked, 1, 1<<20); err == nil {
		t.Fatalf("a reliable lane was offered the same chunk twice at offset %d", again.Offset)
	}
}

// Reliability belongs to the attempt, not to the lane. A lane whose answer
// changes -- one that carried a chunk over a coded datagram path and now
// carries them over its stream -- must still be allowed to re-issue what it
// took unreliably, or exactly those chunks are stranded and the flow waits for
// bytes nothing will resend.
func TestAChunkTakenUnreliablyStaysReissuableWhenTheLaneChanges(t *testing.T) {
	now := time.Now()
	coded := true
	scheduler := New(bytes.NewReader([]byte("12345678")), Config{
		ChunkSize: 8, LaneWindow: 4, MaxOutstanding: 8,
		RetransmitAfter: after(time.Second),
		Reliable:        func(uint64) bool { return !coded },
		Now:             func() time.Time { return now },
	})
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	first, err := scheduler.Next(ctx, 1, 1<<20)
	if err != nil {
		t.Fatalf("no chunk offered while the lane was coding: %v", err)
	}
	scheduler.Wrote(1, first)
	// The flow is now bulk, so the lane carries data on its stream and reports
	// itself reliable. The chunk it already took is still coded and still gone.
	coded = false
	now = now.Add(2 * time.Second)
	if reissued := scheduler.ReissueExpired(); reissued != 1 {
		t.Fatalf("re-issued %d chunks, want the one taken unreliably", reissued)
	}
	again, err := scheduler.Next(ctx, 1, 1<<20)
	if err != nil {
		t.Fatalf("the lane refused to resend a chunk it had taken unreliably: %v", err)
	}
	scheduler.Wrote(1, again)
	now = now.Add(2 * time.Second)
	if reissued := scheduler.ReissueExpired(); reissued != 1 {
		t.Fatalf("made %d reliable chunks ready for another lane, want one", reissued)
	}
	blocked, stop := context.WithTimeout(context.Background(), 20*time.Millisecond)
	defer stop()
	if duplicate, err := scheduler.Next(blocked, 1, 1<<20); err == nil {
		t.Fatalf("reliable replacement was physically duplicated on its own lane: %+v", duplicate)
	}
}

func TestLostUnreliableSpeculationDoesNotBlockAReliableOriginal(t *testing.T) {
	now := time.Now()
	scheduler := New(bytes.NewReader([]byte("12345678")), Config{
		ChunkSize: 8, LaneWindow: 4, MaxOutstanding: 8,
		RetransmitAfter: after(time.Second),
		Reliable:        func(lane uint64) bool { return lane == 1 },
		Now:             func() time.Time { return now },
	})
	defer scheduler.Close()
	ctx := context.Background()

	original, err := scheduler.Next(ctx, 1, 1<<20)
	if err != nil {
		t.Fatal(err)
	}
	scheduler.Wrote(1, original)
	now = now.Add(2 * time.Second)
	if got := scheduler.ReissueExpired(); got != 1 {
		t.Fatalf("queued %d speculative copies, want one", got)
	}
	copy1, err := scheduler.Next(ctx, 2, 1<<20)
	if err != nil {
		t.Fatal(err)
	}
	scheduler.Wrote(2, copy1)

	// The original remains recoverable by its transport, while the coded copy
	// is terminally lost. Its expiration must free lane 2 and permit a new
	// bounded speculation instead of leaving two attempts charged forever.
	now = now.Add(2 * time.Second)
	if got := scheduler.ReissueExpired(); got != 1 {
		t.Fatalf("queued %d copies after the speculative loss, want one replacement", got)
	}
	if chunks, retained, queued := scheduler.LaneOutstanding(2); chunks != 0 || retained != 0 || queued != 0 {
		t.Fatalf("expired speculation left lane 2 at %d chunks/%d retained/%d queued", chunks, retained, queued)
	}
	copy2, err := scheduler.Next(ctx, 2, 1<<20)
	if err != nil || copy2 == nil {
		t.Fatalf("replacement speculation = %v, %v", copy2, err)
	}
	if copy2.Offset != original.Offset || copy2.attempt == copy1.attempt {
		t.Fatalf("replacement speculation offset/attempt = %d/%d, want %d/new", copy2.Offset, copy2.attempt, original.Offset)
	}
	if chunks, retained, _ := scheduler.LaneOutstanding(1); chunks != 1 || retained != 8 {
		t.Fatalf("reliable original changed to %d chunks/%d retained", chunks, retained)
	}
}

func TestReliableRecoveryWaitsReadyForALaneThatJoinsLater(t *testing.T) {
	now := time.Now()
	scheduler := New(bytes.NewReader([]byte("12345678")), Config{
		ChunkSize: 8, LaneWindow: 4, MaxOutstanding: 8,
		RetransmitAfter: after(time.Second), Now: func() time.Time { return now },
	})
	defer scheduler.Close()

	original, err := scheduler.Next(context.Background(), 1, 1<<20)
	if err != nil {
		t.Fatal(err)
	}
	scheduler.Wrote(1, original)
	now = now.Add(2 * time.Second)
	if got := scheduler.ReissueExpired(); got != 1 {
		t.Fatalf("queued %d recoveries before another lane joined, want one ready logical chunk", got)
	}

	// Readiness is logical state, not a count of lanes which happened to have
	// received earlier work. A newly admitted replacement lane must see the
	// recovery immediately.
	replacement, err := scheduler.Next(context.Background(), 2, 1<<20)
	if err != nil || replacement == nil || replacement.Offset != original.Offset {
		t.Fatalf("late lane got %v, %v; want offset %d", replacement, err, original.Offset)
	}
}

// Attempt identity is what makes replacing unreliable work safe. A callback
// from an older dispatch can arrive after the same bytes have been dispatched
// again on the same lane; matching by lane and offset would mutate or fail the
// replacement.
func TestRetiredAttemptCallbacksCannotMutateItsReplacement(t *testing.T) {
	now := time.Now()
	scheduler := New(bytes.NewReader([]byte("12345678")), Config{
		ChunkSize: 8, LaneWindow: 4, MaxOutstanding: 8,
		RetransmitAfter: after(time.Second),
		Reliable:        func(uint64) bool { return false },
		Now:             func() time.Time { return now },
	})
	defer scheduler.Close()
	ctx := context.Background()

	first, err := scheduler.Next(ctx, 1, 1<<20)
	if err != nil {
		t.Fatal(err)
	}
	// An unwritten dispatch is queued, not lost, even if its timer passes.
	now = now.Add(2 * time.Second)
	if got := scheduler.ReissueExpired(); got != 0 {
		t.Fatalf("re-issued %d unwritten attempts, want none", got)
	}
	scheduler.Wrote(1, first)
	if got := scheduler.ReissueExpired(); got != 1 {
		t.Fatalf("re-issued %d written expired attempts, want one", got)
	}
	replacement, err := scheduler.Next(ctx, 1, 1<<20)
	if err != nil {
		t.Fatal(err)
	}

	// A duplicate/late write completion for the retired identity must not mark
	// the replacement written.
	scheduler.Wrote(1, first)
	if _, _, queued := scheduler.LaneOutstanding(1); queued != 8 {
		t.Fatalf("late Wrote changed replacement queue accounting to %d bytes", queued)
	}
	// Nor may a late failure retire that replacement.
	scheduler.Fail(1, first)
	if chunks, retained, _ := scheduler.LaneOutstanding(1); chunks != 1 || retained != 8 {
		t.Fatalf("late Fail changed replacement to %d chunks/%d bytes", chunks, retained)
	}

	scheduler.Wrote(1, replacement)
	if _, _, queued := scheduler.LaneOutstanding(1); queued != 0 {
		t.Fatalf("replacement Wrote left %d queued bytes", queued)
	}
	// A late arrival remains useful: ACKs identify logical bytes, so the old
	// copy completing must complete the replacement too.
	scheduler.Complete(1, first)
	if chunks, retained, queued := scheduler.LaneOutstanding(1); chunks != 0 || retained != 0 || queued != 0 {
		t.Fatalf("late completion left %d chunks/%d retained/%d queued", chunks, retained, queued)
	}
}

func TestLaneFailureWhileAReplacementIsPendingDoesNotDuplicateTheChunk(t *testing.T) {
	now := time.Now()
	scheduler := New(bytes.NewReader([]byte("12345678abcdefgh")), Config{
		ChunkSize: 8, LaneWindow: 4, MaxOutstanding: 8,
		RetransmitAfter: after(time.Second), Now: func() time.Time { return now },
	})
	defer scheduler.Close()
	ctx := context.Background()

	first, err := scheduler.Next(ctx, 1, 1<<20)
	if err != nil {
		t.Fatal(err)
	}
	second, err := scheduler.Next(ctx, 2, 1<<20)
	if err != nil {
		t.Fatal(err)
	}
	scheduler.Wrote(1, first)
	scheduler.Wrote(2, second)

	// Both reliable attempts expire while another lane exists, so each logical
	// chunk has one speculative replacement waiting in the ready set.
	now = now.Add(2 * time.Second)
	if got := scheduler.ReissueExpired(); got != 2 {
		t.Fatalf("re-issued %d chunks, want two", got)
	}
	// The original attempt fails before its waiting replacement is taken. The
	// failure transition and the timer transition both request a replacement,
	// but the logical ready state must remain singular.
	scheduler.Fail(1, first)
	scheduler.mu.Lock()
	copies := 0
	for _, chunk := range scheduler.pending {
		if chunk.Offset == first.Offset {
			copies++
		}
	}
	scheduler.mu.Unlock()
	if copies != 1 {
		t.Fatalf("ready set contains %d copies of failed offset %d, want one", copies, first.Offset)
	}
}

// A chunk the peer has proved it did not receive must be re-offered at once.
//
// The proof is data acknowledged beyond it: a peer holding bytes above a chunk
// received them over the same path, so a chunk still outstanding well below
// that point is gone rather than late. Waiting for the reissue timer instead
// costs a second and a half with the receiver's contiguous point stopped
// behind the hole -- and with it every acknowledgement, and with them the
// sender's whole clock.
func TestAChunkProvedMissingIsReissuedWithoutWaiting(t *testing.T) {
	source := bytes.NewReader(bytes.Repeat([]byte("x"), 8*1024))
	s := New(source, Config{
		ChunkSize: 1024, LaneWindow: 64, MaxOutstanding: 64,
		MaxOutstandingBytes: 1 << 20, Retention: func() int { return 1 << 20 },
		RetransmitAfter: after(time.Hour), // only the proof may re-offer anything
		// An unreliable lane, which is what a coded lane is: what it loses has
		// no other way back.
		Reliable: func(uint64) bool { return false },
	})
	defer s.Close()

	ctx := context.Background()
	var taken []*Chunk
	for i := 0; i < 4; i++ {
		chunk, err := s.Next(ctx, 1, 1<<20)
		if err != nil || chunk == nil {
			t.Fatalf("chunk %d: %v", i, err)
		}
		taken = append(taken, chunk)
		s.Wrote(1, chunk)
	}

	// The peer acknowledges everything except the first chunk.
	for _, chunk := range taken[1:] {
		s.Complete(1, chunk)
	}
	if n := s.ReissueUnacknowledgedBelow(taken[0].End()); n != 1 {
		t.Fatalf("re-offered %d chunks, want the one the peer proved missing", n)
	}
	// And it is offered again, to the same lane, because an unreliable lane
	// losing a chunk is the only way that chunk comes back.
	again, err := s.Next(ctx, 1, 1<<20)
	if err != nil {
		t.Fatal(err)
	}
	if again == nil || again.Offset != taken[0].Offset {
		t.Fatalf("next chunk was %v, want the missing one at offset %d", again, taken[0].Offset)
	}

	// A chunk a reliable lane is carrying must not be re-offered: that lane
	// will retransmit it, and a second copy is spent on the one outcome it
	// cannot help.
	reliable := New(bytes.NewReader(bytes.Repeat([]byte("y"), 4*1024)), Config{
		ChunkSize: 1024, LaneWindow: 64, MaxOutstanding: 64,
		MaxOutstandingBytes: 1 << 20, Retention: func() int { return 1 << 20 },
		RetransmitAfter: after(time.Hour),
	})
	defer reliable.Close()
	first, err := reliable.Next(ctx, 1, 1<<20)
	if err != nil || first == nil {
		t.Fatalf("reliable lane took nothing: %v", err)
	}
	reliable.Wrote(1, first)
	if n := reliable.ReissueUnacknowledgedBelow(first.End() + 1<<20); n != 0 {
		t.Fatalf("re-offered %d chunks from a reliable lane, want none", n)
	}
}
