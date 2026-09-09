// Package stripe schedules one byte stream across several independent lanes by
// self-pacing: a lane is handed its next chunk when it finishes the last one.
//
// The design it replaces predicted. It estimated each lane's rate, computed
// which lane would deliver a frame soonest, and committed frames to that lane's
// queue ahead of time -- up to 56 frames, 1.75 MiB, on a queue the scheduler
// could not take back. Every byte of that commitment was a bet on an estimate.
// When the bet was wrong, the bytes were already numbered and sitting behind a
// lane that had slowed down, and the receiver could not deliver past them; the
// remedies for that (reinjecting a stalled head on a timer, a replay window
// sized to the whole reorder span) were all corrections for mis-prediction.
//
// Self-pacing needs no estimate. A lane asks for work when it has capacity, so
// a lane that is fast asks often and a lane that is throttled asks rarely; a
// lane that has stopped entirely asks never and is thereby excluded without
// anyone deciding to exclude it. The rate each lane gets is whatever it can
// actually carry, measured by the only instrument that cannot be wrong about
// it: the lane itself.
//
// Two properties follow, and both are the point:
//
//   - A lane's commitment is bounded by what its transport has not yet taken,
//     not by a queue depth chosen in advance. The transport's own congestion
//     control is therefore the clock: a stream write returns when the packer
//     has consumed the bytes, which it does only when the congestion window and
//     the pacer allow. Losing a lane costs that commitment and nothing more,
//     and the loss is recoverable because any chunk may be re-issued anywhere.
//   - Lanes are time-independent. Nothing about chunk N's placement constrains
//     chunk N+1, so there is no ordering to violate and no schedule to fall
//     behind. Order is reconstructed at the receiver from byte offsets, which
//     is where it belongs.
package stripe

import (
	"context"
	"errors"
	"io"
	"sort"
	"sync"
	"time"

	"github.com/bojieli/queqiao/internal/memlimit"
)

// ErrClosed reports that the scheduler has been closed.
var ErrClosed = errors.New("stripe: scheduler closed")

// Windows supplies the admission limits a lane must satisfy to be handed more
// work.
//
// Keeping this an interface is what stops congestion control leaking into the
// scheduler. The scheduler's job is to hand the oldest ready chunk to a lane
// that has room; deciding how much room a lane has is a different question,
// answered by the lane's transport.
type Windows interface {
	// Lane is how many bytes this lane may hold that its transport has not yet
	// taken, given how many it holds now. It is a write-ahead bound, not a
	// congestion window: the transport already has one of those, and what this
	// governs is how far ahead of it the sender commits bytes that no other
	// lane can then take back.
	Lane(laneID uint64, queued uint64) int
	// Total is how much the flow may hold unacknowledged across every lane. It
	// is what stops N lanes claiming N times a single connection's share.
	Total() int
}

// OutstandingWindows optionally bounds bytes assigned to a lane until the
// peer acknowledges them. Stream writes normally supply the scheduler's clock,
// but a kernel TCP write returns after copying into the socket buffer rather
// than after congestion control sends the bytes. A TCP bundle therefore uses
// this second bound to keep one socket from pre-claiming the whole stream.
type OutstandingWindows interface {
	Outstanding(laneID uint64, outstanding uint64) int
}

// Config bounds the scheduler.
type Config struct {
	// ChunkSize is the largest chunk handed to a lane. It trades balance
	// granularity against per-chunk overhead: with C bytes per chunk, the most
	// any single lane can hold up is C bytes of the receiver's contiguous
	// point, so this is the head-of-line exposure of one stalled lane.
	ChunkSize int
	// LaneWindow caps how many chunks a lane may hold unacknowledged, as a
	// backstop on bookkeeping. The binding limits are the byte bounds: Windows
	// for what a lane may commit ahead of its transport, and
	// MaxOutstandingBytes for what the flow may retain.
	LaneWindow int
	// MaxOutstanding bounds chunks held across all lanes.
	MaxOutstanding int
	// Retention, when set, reports the current bound instead. It is consulted
	// rather than fixed because what a flow must retain is a property of the
	// path: the lanes' combined congestion windows, plus what the peer has not
	// yet acknowledged. A constant either starves a fast path or lets a slow
	// one hold memory it will never use.
	Retention func() int
	// MaxOutstandingBytes bounds the same set by size, and is the ceiling on
	// Retention. Counting chunks cannot bound memory when a chunk is whatever one
	// read returned: 2048 chunks is 64 MiB if they are full and a fraction of
	// that if they are not, so a count generous enough to keep a fast path busy
	// is also generous enough to let a flow retain tens of megabytes. Measured
	// with a count-only bound, throughput fell across successive transfers in
	// one process as the heap grew.
	MaxOutstandingBytes int
	// Memory is shared by every flow of an endpoint. The producer acquires one
	// full ChunkSize before allocating a source buffer and holds it until the
	// logical chunk is acknowledged. This turns aggregate read-ahead into a
	// hard endpoint limit instead of MaxOutstandingBytes multiplied by flows.
	// Nil preserves the unbounded server/default profile.
	Memory *memlimit.Budget
	// RetransmitAfter is asked how long a chunk may be outstanding before it is
	// presumed lost and offered again. Re-issuing duplicates bytes the receiver
	// discards, so this trades a little bandwidth for not waiting on a lane
	// that has gone quiet. Nil, or a zero answer, disables it.
	//
	// It is asked rather than fixed because the answer is a property of the
	// path. A chunk with data behind it is proved lost by that data within a
	// round trip, and this timer only governs the case where there is nothing
	// behind it -- a small exchange, or the last chunks of a transfer. Fixed at
	// a second and a half it was six round trips on the path this targets, and
	// measured live, one small flow in five cost 1.79 s instead of 0.29
	// because it spent that constant waiting for a chunk the code had failed
	// to repair.
	RetransmitAfter func() time.Duration
	// ReliableReissueBurst bounds how many chunks already carried by reliable
	// lanes a single timer sweep may copy. Zero keeps the unbounded legacy
	// behavior. TCP striping sets one: the oldest missing byte is what blocks
	// delivery, while copying every chunk behind it only multiplies traffic.
	ReliableReissueBurst int
	// Reliable reports whether a lane retransmits for itself. When nil every
	// lane is taken to be reliable, which is what a lane on a QUIC stream is.
	//
	// It decides the lifecycle of an attempt. A reliable one remains active
	// until delivery or lane failure, and may have one speculative copy on a
	// different lane. A written unreliable one is terminal after its recovery
	// deadline or receiver evidence; it is retired before the logical chunk is
	// offered again, including to the same lane. Without that retirement a
	// single coded lane accumulates one admission charge per erasure and
	// eventually cannot retry the bytes which are missing.
	Reliable func(laneID uint64) bool
	// Windows supplies admission limits. When nil, only LaneWindow and
	// MaxOutstanding apply, which is the behaviour of a flow with no
	// congestion coupling.
	Windows Windows
	// Now is the clock, for tests.
	Now func() time.Time
}

// DefaultConfig returns bounds suitable for a long-haul path.
func DefaultConfig() Config {
	return Config{
		ChunkSize:           64 * 1024,
		LaneWindow:          4,
		MaxOutstanding:      64,
		MaxOutstandingBytes: 16 * 1024 * 1024,
		RetransmitAfter:     func() time.Duration { return 2 * time.Second },
	}
}

func (c *Config) applyDefaults() {
	d := DefaultConfig()
	if c.ChunkSize <= 0 {
		c.ChunkSize = d.ChunkSize
	}
	if c.LaneWindow <= 0 {
		c.LaneWindow = d.LaneWindow
	}
	if c.MaxOutstanding <= 0 {
		c.MaxOutstanding = d.MaxOutstanding
	}
	if c.MaxOutstanding < c.LaneWindow {
		c.MaxOutstanding = c.LaneWindow
	}
	if c.MaxOutstandingBytes <= 0 {
		c.MaxOutstandingBytes = d.MaxOutstandingBytes
	}
	if c.Now == nil {
		c.Now = time.Now
	}
}

// Chunk is a contiguous run of the source stream, addressed by byte offset.
// Offsets are what makes lanes independent: a chunk carries where it belongs,
// so it can travel any lane and arrive in any order.
type Chunk struct {
	Offset uint64
	Data   []byte
	// Final marks the chunk that ends the stream. It is delivered like any
	// other, so the end of the stream is ordered with respect to the data
	// rather than being a separate event that can overtake it.
	Final bool

	// urgent marks a chunk that came back from a lane which stalled or died.
	// Such a chunk is admitted to a lane even when that lane is at its window,
	// because it is almost certainly the one holding up the receiver's
	// contiguous point: every other lane is then full of chunks that cannot be
	// acknowledged until this one lands, so respecting the window here would
	// deadlock the flow with every lane waiting on a chunk none of them is
	// allowed to carry.
	urgent bool
	// attempt identifies one dispatch of this logical byte range. It is not
	// transmitted: byte offsets identify data to the peer, while this identity
	// lets local completion callbacks distinguish a retired unreliable attempt
	// from the replacement carrying the same bytes on the same lane.
	attempt uint64
	// reservation is charged once for the backing allocation, not once per
	// retransmission. Copies handed to lanes clear it; only the scheduler's
	// canonical chunk releases it.
	reservation int
}

// End returns the offset one past this chunk's last byte.
func (c *Chunk) End() uint64 { return c.Offset + uint64(len(c.Data)) }

type attempt struct {
	id       uint64
	lane     uint64
	deadline time.Time
	// reliable records whether the lane retransmitted for itself at the moment
	// this chunk was handed to it.
	//
	// It belongs to the attempt and not to the lane, because a lane's answer
	// changes: one that carried a chunk over a coded datagram path may be
	// carrying the next over its stream. Asking the lane as it is now, rather
	// than as it was when it took these bytes, strands exactly the chunks that
	// were sent unreliably -- nothing will re-issue them, because the lane now
	// says it did not need to. Measured live, that took a download from 6.2
	// Mbit/s to 0.25.
	reliable bool
	// written records that the lane's transport has taken these bytes. Until
	// then they are the lane's queued commitment and bound its admission;
	// afterwards they are the transport's problem, and the scheduler retains
	// them only so they can be re-issued if the lane dies.
	written bool
}

type outstanding struct {
	chunk    *Chunk
	attempts []attempt
}

// Stats reports what the scheduler did, for tests and metrics.
type Stats struct {
	ChunksIssued      uint64
	ChunksRetransmit  uint64
	ChunksCompleted   uint64
	BytesIssued       uint64
	BytesRetransmit   uint64
	LaneFailures      uint64
	SourceBytes       uint64
	PeakOutstanding   int
	CompletedByLaneID map[uint64]uint64
}

// Scheduler hands chunks of a source stream to lanes that ask for them.
//
// It is safe for concurrent use: one goroutine per lane calls Next, and the
// completion path may be called from anywhere.
type Scheduler struct {
	cfg Config

	mu       sync.Mutex
	ready    sync.Cond // a lane may have work, or space freed
	produced sync.Cond // the producer may read more

	src         io.Reader
	nextOffset  uint64
	pending     []*Chunk
	live        map[uint64]*outstanding
	laneLoad    map[uint64]int
	laneBytes   map[uint64]uint64
	laneQueued  map[uint64]uint64
	totalBytes  uint64
	nextAttempt uint64
	eof         bool
	srcErr      error
	closed      bool
	finished    chan struct{}
	producerCtx context.Context
	cancel      context.CancelFunc
	stats       Stats
}

// New returns a scheduler that reads src and hands it out in chunks. It starts
// one goroutine to read ahead; Close stops it.
func New(src io.Reader, cfg Config) *Scheduler {
	cfg.applyDefaults()
	producerCtx, cancel := context.WithCancel(context.Background())
	s := &Scheduler{
		cfg:         cfg,
		src:         src,
		live:        make(map[uint64]*outstanding),
		laneLoad:    make(map[uint64]int),
		laneBytes:   make(map[uint64]uint64),
		laneQueued:  make(map[uint64]uint64),
		finished:    make(chan struct{}),
		producerCtx: producerCtx,
		cancel:      cancel,
	}
	s.stats.CompletedByLaneID = make(map[uint64]uint64)
	s.ready.L = &s.mu
	s.produced.L = &s.mu
	go s.produce()
	return s
}

// produce reads the source into ready chunks, staying within MaxOutstanding so
// a stalled transfer cannot buffer the whole stream in memory.
func (s *Scheduler) produce() {
	for {
		s.mu.Lock()
		for !s.closed && (len(s.pending)+len(s.live) >= s.cfg.MaxOutstanding ||
			s.retainedBytes() >= uint64(s.readAheadLimit())) {
			s.produced.Wait()
		}
		if s.closed {
			s.mu.Unlock()
			return
		}
		s.mu.Unlock()

		if err := s.cfg.Memory.Acquire(s.producerCtx, s.cfg.ChunkSize); err != nil {
			s.mu.Lock()
			if !s.closed {
				s.srcErr = err
				s.eof = true
				s.ready.Broadcast()
			}
			s.mu.Unlock()
			return
		}
		buf := make([]byte, s.cfg.ChunkSize)
		// One Read rather than ReadFull: a chunk is at most ChunkSize, not
		// exactly it. Waiting for a full buffer would hold a small write --
		// a request, an interactive turn -- until enough later bytes arrived
		// to fill the chunk, which is latency invented by the scheduler.
		n, err := s.src.Read(buf)

		s.mu.Lock()
		if s.closed {
			s.mu.Unlock()
			s.cfg.Memory.Release(s.cfg.ChunkSize)
			return
		}
		if n > 0 {
			chunk := &Chunk{Offset: s.nextOffset, Data: buf[:n], reservation: s.cfg.ChunkSize}
			s.nextOffset += uint64(n)
			s.stats.SourceBytes += uint64(n)
			s.pending = append(s.pending, chunk)
		} else {
			s.cfg.Memory.Release(s.cfg.ChunkSize)
		}
		if err != nil {
			if errors.Is(err, io.EOF) {
				s.markEOFLocked()
			} else {
				s.srcErr = err
				s.eof = true
			}
			s.signalIfDoneLocked()
			s.ready.Broadcast()
			s.mu.Unlock()
			return
		}
		s.ready.Broadcast()
		s.mu.Unlock()
	}
}

// readAheadLimit is how much the flow may retain: chunks read and not yet
// acknowledged, because a lane that dies may not have delivered what its
// transport accepted. It is a memory bound and nothing else -- what a lane may
// commit is bounded separately, by Windows.
func (s *Scheduler) readAheadLimit() int {
	if s.cfg.Retention == nil {
		return s.cfg.MaxOutstandingBytes
	}
	want := s.cfg.Retention()
	if want <= 0 || want > s.cfg.MaxOutstandingBytes {
		return s.cfg.MaxOutstandingBytes
	}
	return want
}

// retainedBytes is what the flow is holding: chunks read but not yet
// acknowledged. Must be called with the lock held.
func (s *Scheduler) retainedBytes() uint64 {
	total := s.totalBytes
	for _, chunk := range s.pending {
		total += uint64(len(chunk.Data))
	}
	return total
}

// markEOFLocked records the end of the stream. The final marker rides on the
// last chunk when there is one, so a receiver cannot see the end before the
// bytes that precede it.
func (s *Scheduler) markEOFLocked() {
	s.eof = true
	if len(s.pending) > 0 {
		s.pending[len(s.pending)-1].Final = true
		return
	}
	for _, out := range s.live {
		if out.chunk.End() == s.nextOffset {
			// The last data chunk is already in flight; it cannot be amended,
			// so the stream is ended by an empty final chunk at the tail.
			break
		}
	}
	s.pending = append(s.pending, &Chunk{Offset: s.nextOffset, Final: true})
}

// Next blocks until this lane should carry a chunk, and returns it. It returns
// nil with a nil error when the stream is finished, and ErrClosed after Close.
//
// This is the whole of the pacing policy: a lane calls it when it is ready for
// more work, so the lane's own speed decides its share. There is no rate
// estimate here, and no decision about which lane deserves the chunk -- the
// lane that asks first gets it, and a lane asks when it is free.
func (s *Scheduler) Next(ctx context.Context, laneID uint64, windowBytes int) (*Chunk, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	stop := context.AfterFunc(ctx, func() { s.ready.Broadcast() })
	defer stop()

	for {
		if s.closed {
			return nil, ErrClosed
		}
		if err := ctx.Err(); err != nil {
			return nil, err
		}
		if s.laneLoad[laneID] < s.cfg.LaneWindow {
			if chunk := s.takeReadyLocked(laneID, windowBytes); chunk != nil {
				return chunk, nil
			}
			if err := s.finishedLocked(); err != nil {
				return nil, err
			} else if s.doneLocked() {
				return nil, nil
			}
		}
		s.ready.Wait()
	}
}

// takeReadyLocked assigns the oldest ready chunk to a lane. Oldest first
// matters: the receiver delivers contiguously, so the chunk nearest its
// contiguous point is the one whose absence is holding up delivery.
func (s *Scheduler) takeReadyLocked(laneID uint64, windowBytes int) *Chunk {
	for i, chunk := range s.pending {
		// Room is charged against the chunk's actual size. Charging a nominal
		// ChunkSize instead looks harmless and is not: a read from a TCP socket
		// usually returns far less than the maximum, so the windows fill with
		// chunks that are mostly accounting. Measured on a 100 Mbit/s path,
		// that under-filled a 2 MB window to about 224 KB of real data and cost
		// a quarter of single-lane throughput.
		if !s.hasRoomLocked(laneID, windowBytes, uint64(len(chunk.Data))) && !chunk.urgent {
			// The lane is full. Only recovery work jumps the window, and it is
			// always at the head of the ready set, so stopping here keeps the
			// scan cheap.
			return nil
		}
		if out, ok := s.live[chunk.Offset]; ok && laneHasReliableAttempt(out, laneID) {
			// This lane already took this chunk in a way that will deliver it
			// or die, so a second copy is spent on the one outcome it cannot
			// help. Had it taken it unreliably the opposite would hold: the
			// chunk may simply be gone, and on a single-lane flow this is the
			// only way it comes back.
			//
			continue
		}
		s.pending = append(s.pending[:i], s.pending[i+1:]...)
		out, exists := s.live[chunk.Offset]
		if !exists {
			out = &outstanding{chunk: chunk}
			s.live[chunk.Offset] = out
			s.stats.ChunksIssued++
			s.stats.BytesIssued += uint64(len(chunk.Data))
		} else {
			s.stats.ChunksRetransmit++
			s.stats.BytesRetransmit += uint64(len(chunk.Data))
		}
		var deadline time.Time
		if after := s.retransmitAfter(); after > 0 {
			deadline = s.cfg.Now().Add(after)
		}
		s.nextAttempt++
		if s.nextAttempt == 0 {
			// Zero belongs to source chunks which have not been dispatched. A
			// wrap is not realistic in one flow, but preserving the invariant is
			// free and keeps stale callbacks unambiguous even there.
			s.nextAttempt++
		}
		id := s.nextAttempt
		out.attempts = append(out.attempts, attempt{
			id: id, lane: laneID, deadline: deadline, reliable: s.laneRetransmits(laneID),
		})
		chunk.urgent = false
		s.laneLoad[laneID]++
		s.laneBytes[laneID] += uint64(len(chunk.Data))
		s.laneQueued[laneID] += uint64(len(chunk.Data))
		s.totalBytes += uint64(len(chunk.Data))
		if len(s.live) > s.stats.PeakOutstanding {
			s.stats.PeakOutstanding = len(s.live)
		}
		s.produced.Signal()
		issued := *chunk
		issued.reservation = 0
		issued.attempt = id
		return &issued
	}
	return nil
}

// laneRetransmits reports whether a lane recovers its own losses.
func (s *Scheduler) laneRetransmits(laneID uint64) bool {
	if s.cfg.Reliable == nil {
		return true
	}
	return s.cfg.Reliable(laneID)
}

// laneHasAttempt reports whether this lane is carrying this chunk at all,
// however it took it.
func laneHasAttempt(out *outstanding, laneID uint64) bool {
	for _, a := range out.attempts {
		if a.lane == laneID {
			return true
		}
	}
	return false
}

// laneHasReliableAttempt reports whether this lane already holds this chunk in
// a form that will arrive or fail loudly.
func laneHasReliableAttempt(out *outstanding, laneID uint64) bool {
	for _, a := range out.attempts {
		if a.lane == laneID && a.reliable {
			return true
		}
	}
	return false
}

func (s *Scheduler) finishedLocked() error {
	if s.srcErr != nil && len(s.pending) == 0 && len(s.live) == 0 {
		return s.srcErr
	}
	return nil
}

func (s *Scheduler) doneLocked() bool {
	return s.eof && len(s.pending) == 0 && len(s.live) == 0
}

// Complete reports that a chunk arrived. It is idempotent and indifferent to
// which lane carried it: a chunk re-issued on a second lane is complete when
// either copy lands, and the other lane's attempt is released with it.
func (s *Scheduler) Complete(laneID uint64, chunk *Chunk) {
	if chunk == nil {
		return
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	live, ok := s.live[chunk.Offset]
	if ok {
		for _, a := range live.attempts {
			s.releaseLaneLocked(a.lane, uint64(len(live.chunk.Data)), !a.written)
		}
		delete(s.live, chunk.Offset)
		s.stats.ChunksCompleted++
		s.stats.CompletedByLaneID[laneID]++
	}
	// A chunk can be in the ready set and in flight at the same time: that is
	// what re-offering a slow lane's chunk to another lane means. If it then
	// arrives by the first route, the copy waiting in the ready set is bytes
	// the peer already has, and handing it to a lane sends them again. Left
	// unremoved, this measured a 50% overhead on a 20% loss path -- 481 chunks
	// issued for a 320-chunk object -- and it was invisible in the retransmit
	// counter, because a chunk taken after its completion is no longer live and
	// counts as a new issue rather than a re-issue.
	dropped := s.removePendingLocked(chunk.Offset)
	if !ok && dropped == nil {
		return
	}
	if ok {
		s.releaseChunkLocked(live.chunk)
	} else {
		s.releaseChunkLocked(dropped)
	}
	s.signalIfDoneLocked()
	s.produced.Signal()
	s.ready.Broadcast()
}

// Fail reports that a lane could not carry a chunk. The chunk returns to the
// ready set for any other lane to pick up, so a lane that breaks mid-transfer
// costs its window and nothing more.
func (s *Scheduler) Fail(laneID uint64, chunk *Chunk) {
	if chunk == nil {
		return
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	out, ok := s.live[chunk.Offset]
	if !ok {
		return
	}
	if !s.dropAttemptLocked(out, laneID, chunk.attempt) {
		// This callback belongs to an unreliable attempt already retired by
		// timeout or receiver evidence. It must not fail its replacement merely
		// because both used the same lane and byte range.
		return
	}
	s.stats.LaneFailures++
	if len(out.attempts) == 0 {
		// The logical chunk remains outstanding even though this physical
		// attempt ended. Keeping that distinction makes a replacement a retry,
		// preserves late logical completion, and avoids briefly treating the
		// same retained bytes as new source work.
		s.requeueLocked(out.chunk)
	}
	s.ready.Broadcast()
}

// RetireLane releases every chunk a lane was carrying, for a lane that has
// died rather than a single chunk that failed.
func (s *Scheduler) RetireLane(laneID uint64) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, out := range s.live {
		if !laneHasAttempt(out, laneID) {
			continue
		}
		s.stats.LaneFailures++
		s.dropLaneAttemptsLocked(out, laneID)
		if len(out.attempts) == 0 {
			s.requeueLocked(out.chunk)
		}
	}
	delete(s.laneLoad, laneID)
	delete(s.laneBytes, laneID)
	delete(s.laneQueued, laneID)
	s.ready.Broadcast()
}

func (s *Scheduler) dropAttemptLocked(out *outstanding, laneID, attemptID uint64) bool {
	for i, a := range out.attempts {
		if a.id != attemptID || a.lane != laneID {
			continue
		}
		queued := !a.written
		out.attempts = append(out.attempts[:i], out.attempts[i+1:]...)
		s.releaseLaneLocked(a.lane, uint64(len(out.chunk.Data)), queued)
		return true
	}
	return false
}

func (s *Scheduler) dropLaneAttemptsLocked(out *outstanding, laneID uint64) {
	kept := out.attempts[:0]
	for _, a := range out.attempts {
		if a.lane != laneID {
			kept = append(kept, a)
			continue
		}
		s.releaseLaneLocked(a.lane, uint64(len(out.chunk.Data)), !a.written)
	}
	out.attempts = kept
}

func (s *Scheduler) releaseLaneLocked(laneID uint64, size uint64, queued bool) {
	if s.laneLoad[laneID] > 0 {
		s.laneLoad[laneID]--
	}
	if queued {
		s.releaseQueuedLocked(laneID, size)
	}
	if s.laneBytes[laneID] >= size {
		s.laneBytes[laneID] -= size
	} else {
		size = s.laneBytes[laneID]
		s.laneBytes[laneID] = 0
	}
	if s.totalBytes >= size {
		s.totalBytes -= size
	} else {
		s.totalBytes = 0
	}
}

// hasRoomLocked reports whether a lane may be handed another chunk: it must fit
// both the lane's own window and the flow's.
//
// A lane holding nothing is always allowed one chunk. A window smaller than a
// chunk is otherwise able to stall a lane permanently, and a flow window that
// has collapsed must still make progress rather than deadlock.
func (s *Scheduler) hasRoomLocked(laneID uint64, windowBytes int, chunk uint64) bool {
	// The escape hatch is deliberately keyed on the flow holding nothing, not
	// on this lane holding nothing. Per-lane, it would hand every lane a free
	// chunk and let the flow exceed its window by one chunk per lane -- which
	// is exactly the over-claiming the flow window exists to prevent.
	if s.totalBytes == 0 {
		return true
	}
	if chunk == 0 {
		chunk = 1
	}
	// The flow's own window binds first and has no per-lane escape: it is what
	// stops N lanes claiming N times a single connection's share, so a lane
	// with nothing queued must not be able to step over it.
	if s.cfg.Windows != nil {
		if total := s.cfg.Windows.Total(); total > 0 && s.totalBytes+chunk > uint64(total) {
			return false
		}
		if windows, ok := s.cfg.Windows.(OutstandingWindows); ok {
			outstanding := s.laneBytes[laneID]
			if lane := windows.Outstanding(laneID, outstanding); lane > 0 && outstanding+chunk > uint64(lane) {
				return false
			}
		}
	}
	queued := s.laneQueued[laneID]
	if queued == 0 {
		// A lane whose transport has taken everything it was given always gets
		// one more chunk. Otherwise a bound smaller than a chunk stalls that
		// lane permanently, and the flow can deadlock with every lane waiting
		// for room none of them will get.
		return true
	}
	if windowBytes > 0 && queued+chunk > uint64(windowBytes) {
		return false
	}
	if s.cfg.Windows != nil {
		if lane := s.cfg.Windows.Lane(laneID, queued); lane > 0 && queued+chunk > uint64(lane) {
			return false
		}
	}
	return true
}

// retransmitAfter is how long the caller currently wants a chunk to wait
// before it is presumed lost.
func (s *Scheduler) retransmitAfter() time.Duration {
	if s.cfg.RetransmitAfter == nil {
		return 0
	}
	return s.cfg.RetransmitAfter()
}

// requeueLocked returns a chunk to the ready set in offset order, so the
// receiver's contiguous point is always what the next free lane works on.
func (s *Scheduler) requeueLocked(chunk *Chunk) {
	if s.pendingHas(chunk.Offset) {
		return
	}
	// A chunk only returns to the ready set because a lane stalled or failed,
	// which makes it the work most likely to be blocking delivery.
	chunk.urgent = true
	i := 0
	for i < len(s.pending) && s.pending[i].Offset < chunk.Offset {
		i++
	}
	s.pending = append(s.pending, nil)
	copy(s.pending[i+1:], s.pending[i:])
	s.pending[i] = chunk
}

// ReissueUnacknowledgedBelow re-offers chunks the peer has proved it did not
// receive, and reports how many.
//
// The proof is data acknowledged beyond them. A peer that reports holding
// bytes above a chunk received those bytes over the same path, so a chunk
// still outstanding well below that point is not late, it is gone -- the same
// inference a fast retransmit makes, at the layer where an unrepairable coded
// symbol actually goes missing.
//
// Only attempts that cannot recover themselves are re-offered. A chunk on a
// reliable lane will be retransmitted by that lane, and a second copy is spent
// on the one outcome it cannot help.
//
// Without this the only recovery was a timer, and the timer is a second and a
// half: measured live, a single chunk erased from the coded prefix of a
// download held the receiver's contiguous point -- and therefore every
// acknowledgement, and therefore the sender's entire clock -- for five
// seconds, on a transfer that took nine.
func (s *Scheduler) ReissueUnacknowledgedBelow(offset uint64) int {
	s.mu.Lock()
	defer s.mu.Unlock()
	reissued := 0
	for _, out := range s.live {
		if out.chunk.End() > offset || len(out.attempts) == 0 {
			continue
		}
		if s.pendingHas(out.chunk.Offset) {
			continue
		}
		// The peer has proved that written unreliable copies are gone. Retire
		// their admission charges before making the replacement; retaining every
		// lost datagram attempt grows the lane window forever and eventually
		// makes a single missing tail chunk impossible to retry.
		s.retireUnreliableAttemptsLocked(out, time.Time{})
		reliable := false
		for _, a := range out.attempts {
			reliable = reliable || a.reliable
		}
		if reliable {
			// A reliable original is still capable of delivering. Retiring a
			// proven-missing speculative datagram is necessary accounting, but
			// receiver evidence alone does not justify another copy while that
			// original has not reached its recovery deadline.
			continue
		}
		if len(out.attempts) != 0 {
			// A copy not yet taken by its transport is still real work. Its Wrote
			// callback will make it eligible for the normal timed retry.
			continue
		}
		s.requeueLocked(out.chunk)
		reissued++
	}
	if reissued > 0 {
		s.ready.Broadcast()
	}
	return reissued
}

// ReissueExpired advances attempts according to their transport semantics.
//
// A reliable attempt remains live: its transport will deliver it or fail
// loudly, so recovery may add one copy on another lane but never replaces it.
// An unreliable attempt is different. Once its transport accepted the bytes
// and its recovery deadline passed, that attempt is terminally lost. It is
// retired before the logical chunk is dispatched again, keeping one active
// unreliable attempt per chunk no matter how many consecutive copies the path
// erases. Each dispatch has its own identity, so a late callback from the
// retired attempt cannot mutate the replacement.
func (s *Scheduler) ReissueExpired() int {
	after := s.retransmitAfter()
	if after <= 0 {
		return 0
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	now := s.cfg.Now()
	candidates := make([]*outstanding, 0)
	for _, out := range s.live {
		if len(out.attempts) == 0 || s.pendingHas(out.chunk.Offset) {
			continue
		}
		// A reliable original can have one speculative copy on an unreliable
		// lane. That copy has its own terminal lifecycle: once written and
		// expired it must release its accounting before the original is
		// considered for another speculation. Treating the mixed set as simply
		// "reliable" left the lost copy in the set forever.
		retired := s.retireUnreliableAttemptsLocked(out, now)
		if len(out.attempts) == 0 && retired {
			candidates = append(candidates, out)
			continue
		}
		reliable, expired := false, false
		for _, a := range out.attempts {
			reliable = reliable || a.reliable
			expired = expired || (!a.deadline.IsZero() && !now.Before(a.deadline))
		}
		if !expired {
			continue
		}
		// Reliable attempts can have one speculative copy on another lane.
		// Unreliable attempts are terminal after their deadline and are retired
		// before the same logical bytes are dispatched again.
		if reliable {
			if len(out.attempts) > 1 {
				continue
			}
		} else {
			if len(out.attempts) != 0 {
				continue
			}
		}
		candidates = append(candidates, out)
	}
	sort.Slice(candidates, func(i, j int) bool {
		return candidates[i].chunk.Offset < candidates[j].chunk.Offset
	})
	reissued := 0
	reliableReissued := 0
	for _, out := range candidates {
		reliable := len(out.attempts) > 0 && out.attempts[0].reliable
		if reliable && s.cfg.ReliableReissueBurst > 0 {
			if reliableReissued >= s.cfg.ReliableReissueBurst {
				continue
			}
			reliableReissued++
		}
		// Retained reliable attempts get a new deadline so their pending copy
		// cannot be offered on every supervisor tick. Unreliable replacements
		// receive a fresh deadline when Next dispatches them.
		if len(out.attempts) > 0 {
			out.attempts[0].deadline = now.Add(after)
		}
		s.requeueLocked(out.chunk)
		reissued++
	}
	if reissued > 0 {
		s.ready.Broadcast()
	}
	return reissued
}

// retireUnreliableAttemptsLocked removes written unreliable attempts. With a
// non-zero deadline, only attempts expired at that instant are terminal; a
// zero deadline means receiver range evidence already proved them missing.
func (s *Scheduler) retireUnreliableAttemptsLocked(out *outstanding, deadline time.Time) bool {
	kept := out.attempts[:0]
	retired := false
	for _, a := range out.attempts {
		retire := !a.reliable && a.written
		if retire && !deadline.IsZero() {
			retire = !a.deadline.IsZero() && !deadline.Before(a.deadline)
		}
		if !retire {
			kept = append(kept, a)
			continue
		}
		s.releaseLaneLocked(a.lane, uint64(len(out.chunk.Data)), false)
		retired = true
	}
	out.attempts = kept
	return retired
}

// removePendingLocked drops a chunk from the ready set, for a chunk that has
// arrived by another route.
func (s *Scheduler) removePendingLocked(offset uint64) *Chunk {
	for i, chunk := range s.pending {
		if chunk.Offset != offset {
			continue
		}
		s.pending = append(s.pending[:i], s.pending[i+1:]...)
		return chunk
	}
	return nil
}

func (s *Scheduler) releaseChunkLocked(chunk *Chunk) {
	if chunk == nil || chunk.reservation == 0 {
		return
	}
	reservation := chunk.reservation
	chunk.reservation = 0
	s.cfg.Memory.Release(reservation)
}

func (s *Scheduler) pendingHas(offset uint64) bool {
	for _, c := range s.pending {
		if c.Offset == offset {
			return true
		}
	}
	return false
}

// Done is closed once every byte of the source has been delivered. A caller
// that must act at the end of the stream -- sending a FIN, for instance --
// waits on this rather than on the lanes, because which lane carried the last
// chunk is not knowable in advance and does not matter.
func (s *Scheduler) Done() <-chan struct{} { return s.finished }

// Err returns the source's read error, if the stream ended in one.
func (s *Scheduler) Err() error {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.srcErr
}

func (s *Scheduler) signalIfDoneLocked() {
	if !s.doneLocked() {
		return
	}
	select {
	case <-s.finished:
	default:
		close(s.finished)
	}
}

// releaseQueuedLocked drops bytes from a lane's queued commitment.
func (s *Scheduler) releaseQueuedLocked(laneID uint64, size uint64) {
	if s.laneQueued[laneID] >= size {
		s.laneQueued[laneID] -= size
		return
	}
	s.laneQueued[laneID] = 0
}

// Wrote reports that a lane's transport has taken a chunk's bytes.
//
// This is what paces a lane, and it is deliberately not the same event as
// acknowledgement. A QUIC stream write returns once the transport has packed
// the bytes into packets, which it does only when its congestion window and
// pacer allow -- so a lane that cannot move data stops accepting it, at the
// transport's own clock rather than a round trip later. Waiting for the peer's
// application-level acknowledgement instead adds a whole return trip to that
// loop, and a sender that must cover it commits several times as much to one
// lane, where no other lane can take it back.
//
// The chunk stays retained until Complete, because a lane that dies may not
// have delivered what its transport accepted.
func (s *Scheduler) Wrote(laneID uint64, chunk *Chunk) {
	if chunk == nil {
		return
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	out, ok := s.live[chunk.Offset]
	if !ok {
		return
	}
	for i := range out.attempts {
		if out.attempts[i].id != chunk.attempt || out.attempts[i].lane != laneID || out.attempts[i].written {
			continue
		}
		out.attempts[i].written = true
		s.releaseQueuedLocked(laneID, uint64(len(out.chunk.Data)))
		s.ready.Broadcast()
		return
	}
}

// LaneOutstanding reports what one lane is holding: chunks handed to it and
// not yet acknowledged, their total size, and how much of that its transport
// has not yet taken. It answers the question a throughput number cannot --
// whether a lane is short of work or full of it -- and the last of the three is
// what admission is compared against.
func (s *Scheduler) LaneOutstanding(laneID uint64) (chunks int, retained, queued uint64) {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.laneLoad[laneID], s.laneBytes[laneID], s.laneQueued[laneID]
}

// Pending reports chunks read from the source and not yet handed to any lane,
// and the flow's total unacknowledged bytes.
func (s *Scheduler) Pending() (ready int, outstandingBytes uint64) {
	s.mu.Lock()
	defer s.mu.Unlock()
	return len(s.pending), s.totalBytes
}

// Stats returns a snapshot.
func (s *Scheduler) Stats() Stats {
	s.mu.Lock()
	defer s.mu.Unlock()
	out := s.stats
	out.CompletedByLaneID = make(map[uint64]uint64, len(s.stats.CompletedByLaneID))
	for k, v := range s.stats.CompletedByLaneID {
		out.CompletedByLaneID[k] = v
	}
	return out
}

// Close releases every waiter. Chunks in flight are abandoned.
func (s *Scheduler) Close() {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.closed {
		return
	}
	s.closed = true
	s.cancel()
	seen := make(map[*Chunk]struct{}, len(s.pending)+len(s.live))
	for _, chunk := range s.pending {
		seen[chunk] = struct{}{}
	}
	for _, out := range s.live {
		seen[out.chunk] = struct{}{}
	}
	for chunk := range seen {
		s.releaseChunkLocked(chunk)
	}
	s.pending = nil
	s.live = make(map[uint64]*outstanding)
	s.ready.Broadcast()
	s.produced.Broadcast()
}
