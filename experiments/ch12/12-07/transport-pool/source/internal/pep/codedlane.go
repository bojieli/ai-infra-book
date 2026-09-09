package pep

import (
	"sync"
	"time"

	"github.com/apernet/quic-go"

	"github.com/bojieli/queqiao/internal/coded"
	"github.com/bojieli/queqiao/internal/fec"
	"github.com/bojieli/queqiao/internal/pathmodel"
	"github.com/bojieli/queqiao/internal/protocol"
)

// A lane's bulk payload can travel over the connection's unreliable datagrams,
// repaired by an erasure code, while everything else stays on its stream.
//
// The split is what makes coding worth having here. A stream delivers in
// order, so at this path's 42% erasure rate every gap stalls everything behind
// it: measured with 256-byte messages, a stream's median delivery was 1.372 s
// against a coded path's 153 ms. But the session's own acknowledgements must
// not be coded, because they are what releases the data whose symbols they
// would then be queued behind -- with everything on one coded substrate the
// same channel carried 0.87 Mbit/s one way and 0.008 with acknowledgements
// coming back the other.
//
// So a lane is not one substrate or the other. It is a stream for control and
// datagrams for bulk, on one connection, and every lane has the stream.
// bulkDemux routes a connection's coded datagrams to the flow each frame
// belongs to.
//
// The datagrams are the connection's, not a lane's: one stream of them carries
// every flow multiplexed on that connection. Reading it from each lane, as the
// first version did, has every reader competing for frames that mostly belong
// to somebody else -- a frame consumed by the wrong flow is a frame the right
// one waits for forever -- and leaves a reader blocked on a connection-scoped
// receive long after its flow has gone.
//
// So there is one reader, and it demultiplexes on the flow identity the
// protocol already puts in every frame.
type bulkDemux struct {
	path        *coded.Path
	queueFrames int
	heldFrames  int
	heldBytes   int
	mu          sync.Mutex
	// flows is keyed by flow identity.
	flows map[uint64]*subscription
	// held keeps frames that arrived before their flow did, which on a
	// transport whose flows open without waiting is a race rather than a loss.
	held map[uint64][]heldFrame
}

type heldFrame struct {
	frame protocol.Frame
	at    time.Time
}

// A subscription is shared by every lane of one flow, and lives until the last
// of them lets go. Closing it when the first lane does would take the coded
// reads away from the others.
type subscription struct {
	frames chan protocol.Frame
	lanes  int
}

func newBulkDemux(path *coded.Path, queueFrames int) *bulkDemux {
	if queueFrames < 1 || queueFrames > maxBulkQueueFrames {
		queueFrames = maxBulkQueueFrames
	}
	heldFrames := min(maxHeldFrames, 2*queueFrames)
	heldBytes := min(maxHeldBytes, heldFrames*protocol.MaxPayload)
	d := &bulkDemux{
		path: path, queueFrames: queueFrames, heldFrames: heldFrames, heldBytes: heldBytes,
		flows: make(map[uint64]*subscription),
	}
	go d.run()
	return d
}

func (d *bulkDemux) run() {
	for {
		payload, err := d.path.Receive()
		if err != nil {
			d.mu.Lock()
			for id, sub := range d.flows {
				close(sub.frames)
				delete(d.flows, id)
			}
			d.mu.Unlock()
			return
		}
		frame, err := protocol.ParseFrame(payload)
		if err != nil {
			// The coded path hands up whole frames or none, so this is a peer
			// sending something this one cannot parse rather than loss.
			continue
		}
		// The send happens under the lock that release closes under, or the
		// two race: taking the channel and then sending outside the lock lets
		// a flow that let go in between be sent to after its channel closed.
		// The send cannot block, so holding the lock across it costs nothing.
		d.mu.Lock()
		if sub := d.flows[frame.Header.FlowID]; sub != nil {
			select {
			case sub.frames <- frame:
			default:
				// The flow is not keeping up. Dropping is what an unreliable
				// substrate does, and the session re-issues what it needs.
			}
		} else {
			d.holdLocked(frame)
		}
		d.mu.Unlock()
	}
}

// holdLocked keeps a frame for a flow that does not exist here yet.
//
// A flow opens without waiting for the peer to acknowledge it, which is what
// makes opening one cost nothing -- and it means the first data frame can
// arrive before the open that names it has been processed and the flow has
// claimed its share of these datagrams. Dropping it then is not the unreliable
// substrate doing its job, it is a race: the frame arrived, and the only
// reason it was thrown away is that this end was a few hundred microseconds
// behind. Measured on the emulated path, that cost every short flow the
// reissue timer -- 1.055 s where the exchange itself takes 300 ms.
//
// What is held is bounded in both directions: a few frames, briefly. Anything
// beyond that is loss like any other.
func (d *bulkDemux) holdLocked(frame protocol.Frame) {
	if d.held == nil {
		d.held = make(map[uint64][]heldFrame)
	}
	now := time.Now()
	heldFrameLimit, heldByteLimit := d.heldFrames, d.heldBytes
	if heldFrameLimit <= 0 {
		heldFrameLimit = maxHeldFrames
	}
	if heldByteLimit <= 0 {
		heldByteLimit = maxHeldBytes
	}
	frames, bytes := 0, 0
	for id, held := range d.held {
		kept := held[:0]
		for _, one := range held {
			if now.Sub(one.at) <= heldFrameLifetime {
				kept = append(kept, one)
			}
		}
		if len(kept) == 0 {
			delete(d.held, id)
			continue
		}
		d.held[id] = kept
		frames += len(kept)
		for _, one := range kept {
			bytes += len(one.frame.Payload)
		}
	}
	if frames >= heldFrameLimit || bytes+len(frame.Payload) > heldByteLimit {
		return
	}
	d.held[frame.Header.FlowID] = append(d.held[frame.Header.FlowID], heldFrame{frame: frame, at: now})
}

const (
	// heldFrameLifetime is how long a frame waits for its flow to appear. It
	// covers the gap between an optimistic open and the peer acting on it,
	// which is a scheduling delay rather than a round trip.
	heldFrameLifetime = 2 * time.Second
	// maxHeldFrames and maxHeldBytes bound what one connection holds for flows
	// it has never heard of, which is what stops a peer naming flows that
	// never arrive from costing memory. Both are needed: a data frame carries
	// up to a chunk, so a count alone would allow several megabytes, and a
	// byte bound alone would allow a great many empty ones.
	maxHeldFrames      = 256
	maxHeldBytes       = 1 << 20
	maxBulkQueueFrames = 256
)

// subscribe claims a flow's frames until release is called.
func (d *bulkDemux) subscribe(flowID uint64) <-chan protocol.Frame {
	d.mu.Lock()
	defer d.mu.Unlock()
	sub, ok := d.flows[flowID]
	if !ok {
		queueFrames := d.queueFrames
		if queueFrames <= 0 {
			queueFrames = maxBulkQueueFrames
		}
		sub = &subscription{frames: make(chan protocol.Frame, queueFrames)}
		d.flows[flowID] = sub
		// Whatever arrived before this flow existed is delivered now rather
		// than waited for again.
		for _, held := range d.held[flowID] {
			select {
			case sub.frames <- held.frame:
			default:
			}
		}
		delete(d.held, flowID)
	}
	sub.lanes++
	return sub.frames
}

func (d *bulkDemux) release(flowID uint64) {
	d.mu.Lock()
	defer d.mu.Unlock()
	sub, ok := d.flows[flowID]
	if !ok {
		return
	}
	if sub.lanes--; sub.lanes > 0 {
		return
	}
	delete(d.flows, flowID)
	close(sub.frames)
}

// bulkPaths holds one coded path per QUIC connection.
//
// Datagrams are a connection-level facility, not a stream-level one, so a path
// per stream would put several receive loops on one connection competing for
// the same arrivals -- and on a pooled connection would leave some streams
// with a coded substrate and some without, which is worse than none having
// one: a sender that codes into a receiver with no bulk reader loses every
// data frame it sends.
var (
	bulkPaths   sync.Map // *quic.Conn -> *coded.Path
	bulkDemuxs  sync.Map // *coded.Path -> *bulkDemux
	bulkPathMu  sync.Mutex
	bulkDemuxMu sync.Mutex
)

// connBulkDemux returns the demultiplexer for a connection's coded path.
func connBulkDemux(path *coded.Path, queueFrames int) *bulkDemux {
	if path == nil {
		return nil
	}
	bulkDemuxMu.Lock()
	defer bulkDemuxMu.Unlock()
	if existing, ok := bulkDemuxs.Load(path); ok {
		return existing.(*bulkDemux)
	}
	created := newBulkDemux(path, queueFrames)
	bulkDemuxs.Store(path, created)
	return created
}

// connBulkPath returns the connection's coded path, creating it once. It is
// closed with the connection, so no caller owns its lifetime.
func connBulkPath(conn *quic.Conn, queueFrames int) *coded.Path {
	bulkPathMu.Lock()
	defer bulkPathMu.Unlock()
	if existing, ok := bulkPaths.Load(conn); ok {
		return existing.(*coded.Path)
	}
	created := newCodedPath(conn, 0, queueFrames)
	if created == nil {
		return nil
	}
	bulkPaths.Store(conn, created)
	go func() {
		<-conn.Context().Done()
		bulkPathMu.Lock()
		bulkPaths.Delete(conn)
		bulkPathMu.Unlock()
		bulkDemuxMu.Lock()
		bulkDemuxs.Delete(created)
		bulkDemuxMu.Unlock()
		_ = created.Close()
	}()
	return created
}

func newCodedPath(conn *quic.Conn, roundTrip time.Duration, queueFrames int) *coded.Path {
	if support := conn.ConnectionState().SupportsDatagrams; !support.Local || !support.Remote {
		return nil
	}
	carrier, err := coded.NewQUICCarrier(conn)
	if err != nil {
		return nil
	}
	if roundTrip <= 0 {
		roundTrip = 300 * time.Millisecond
	}
	return coded.New(carrier, coded.Config{
		// Bulk payload: the code rate matters more than the recovery latency,
		// because a repair still costs less than the round trip it replaces.
		Class:     fec.ClassBulk,
		RoundTrip: roundTrip,
		// What the endpoint pair has already been measured to do, so the first
		// symbol is coded for the path rather than for a clean one.
		Path: pathmodel.Shared(peerKey(conn)),
		// This bounds both the sender and receiver channel in coded.Path.
		// Zero deliberately preserves the throughput-oriented desktop default.
		Pending: queueFrames,
	})
}
