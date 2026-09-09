package pep

import (
	"bufio"
	"context"
	"io"
	"sync"
	"sync/atomic"
	"time"

	"github.com/bojieli/queqiao/internal/coded"
	"github.com/bojieli/queqiao/internal/protocol"
)

// frameConn is a lane's framing. It always has a control substrate, and may
// additionally have a coded one for bulk payload.
//
// The split is by frame type because the two substrates are good at opposite
// things. Control frames -- the handshake, the flow's open and close, and
// above all the acknowledgements -- are small, are on the critical path of
// whatever comes next, and must arrive; a QUIC stream delivers them reliably
// and immediately. Bulk data frames are large, are already sequenced by byte
// offset, and are already retained and re-issued by the session if they go
// missing; coded datagrams carry them without the head-of-line blocking that a
// stream imposes at this path's loss rate.
//
// Carrying both on one substrate is what made the first coded lane slow. With
// everything coded, a session's own acknowledgements queued behind the data
// whose progress they release: the same channel measured 0.87 Mbit/s in one
// direction and 0.008 when the reverse direction had to carry them.
//
// The reordering this introduces is one the session already tolerates. Data
// frames carry byte offsets and are reassembled across lanes, so a data frame
// overtaking or lagging a control frame is the ordinary multipath case rather
// than a new one.
type frameConn struct {
	control io.ReadWriteCloser
	bulk    *coded.Path

	writeMu sync.Mutex
	// writeBuf is reused under writeMu so that every frame reaches the
	// transport as one write without allocating per frame.
	writeBuf []byte
	// reader coalesces the header and payload reads. A QUIC stream read is not
	// buffered, so reading a 46-byte header directly from it costs one full
	// stream-lock acquisition per frame in addition to the payload reads.
	reader *bufio.Reader
	// bulkQueueFrames is a tiny per-flow descriptor queue into the one shared
	// connection-level datagram demultiplexer. Payload capacity remains bounded
	// by the connection and endpoint budgets.
	bulkQueueFrames int

	// wantsCoding reports whether this lane's flow would rather spend bytes
	// than round trips. Nil means it would.
	wantsCoding func() bool
	// openUnconfirmed is installed only on an optimistic client lane. The first
	// coded DATA frame sent before OPEN_OK is also written once behind OPEN on
	// the reliable stream. The coded copy keeps short-flow latency; the bounded
	// reliable copy guarantees the byte-zero gap eventually closes even if all
	// early datagrams outrun or miss remote flow creation.
	openUnconfirmed func() bool
	openSafetyCopy  atomic.Bool
	// packetsForcedToStream keeps SOCKS UDP on the control stream even where
	// datagrams are available. It exists to measure the difference rather
	// than to be a tuning knob, and defaults false.
	packetsForcedToStream bool
	// codedData and streamData count where this lane's payload actually went,
	// which is the only way to tell "the class never changed" from "the class
	// changed and coding continued".
	codedData  atomic.Uint64
	streamData atomic.Uint64
	// codedPackets and streamPackets are the same question for SOCKS UDP,
	// and the only way to confirm from outside that an association took the
	// datagram substrate rather than falling back to the stream.
	codedPackets  atomic.Uint64
	streamPackets atomic.Uint64

	closeOnce sync.Once
	done      chan struct{}
}

// setCodingPolicy tells the framing which currency this flow prefers. It must
// be called before the lane's goroutines start, because from then on the
// answer is read on every write.
func (c *frameConn) setCodingPolicy(wants func() bool) { c.wantsCoding = wants }

func (c *frameConn) setOpenSafetyPolicy(unconfirmed func() bool) {
	c.openUnconfirmed = unconfirmed
	c.openSafetyCopy.Store(true)
}

// setPacketsOnStream keeps SOCKS UDP on the control stream even where the
// connection has datagrams. Same ordering rule as above.
//
// It exists so the two substrates can be measured against each other on one
// build, which is what the release gate asks for, and not as something to
// tune: a UDP packet on a reliable ordered stream is the wrong shape for
// every application that chose UDP, whatever it measures.
func (c *frameConn) setPacketsOnStream(onStream bool) { c.packetsForcedToStream = onStream }

// frameReadBuffer is sized above one default chunk so a data frame's header
// and payload are normally satisfied from one underlying stream read.
const frameReadBuffer = 64 * 1024

// writeBufferRetain bounds the per-lane write buffer that survives a frame.
// It sits above the largest ordinary DATA chunk and below protocol.MaxPayload,
// so a lane that once carried a maximum-size PACKET releases that allocation
// instead of holding it for as long as the lane lives.
const writeBufferRetain = 64 * 1024

// bulkProvider is a lane transport that also carries coded datagrams. The
// transport decides whether a lane has one; the framing only has to discover
// it, which keeps the choice where the connection is and out of every call
// site that builds a lane.
type bulkProvider interface {
	bulkPath() *coded.Path
}

func newFrameConn(conn io.ReadWriteCloser) *frameConn {
	return newFrameConnSized(conn, frameReadBuffer)
}

func newFrameConnSized(conn io.ReadWriteCloser, readBuffer int) *frameConn {
	return newFrameConnLimited(conn, readBuffer, 256)
}

func newFrameConnLimited(conn io.ReadWriteCloser, readBuffer, bulkQueueFrames int) *frameConn {
	var bulk *coded.Path
	if provider, ok := conn.(bulkProvider); ok {
		bulk = provider.bulkPath()
	}
	return newSplitFrameConnLimited(conn, bulk, readBuffer, bulkQueueFrames)
}

// newSplitFrameConn gives a lane a coded substrate for its bulk payload in
// addition to its control stream.
func newSplitFrameConn(control io.ReadWriteCloser, bulk *coded.Path) *frameConn {
	return newSplitFrameConnSized(control, bulk, frameReadBuffer)
}

func newSplitFrameConnSized(control io.ReadWriteCloser, bulk *coded.Path, readBuffer int) *frameConn {
	return newSplitFrameConnLimited(control, bulk, readBuffer, 256)
}

func newSplitFrameConnLimited(control io.ReadWriteCloser, bulk *coded.Path, readBuffer, bulkQueueFrames int) *frameConn {
	if readBuffer < 512 || readBuffer > frameReadBuffer {
		readBuffer = frameReadBuffer
	}
	if bulkQueueFrames < 1 || bulkQueueFrames > 256 {
		bulkQueueFrames = 256
	}
	return &frameConn{
		control:         control,
		bulk:            bulk,
		reader:          bufio.NewReaderSize(control, readBuffer),
		bulkQueueFrames: bulkQueueFrames,
		done:            make(chan struct{}),
	}
}

// bulkFrame decides which substrate a frame belongs on.
//
// Data frames may go to the coded path; everything else is control, including
// the acknowledgements that release them. Two further conditions apply, and
// both are measurements rather than settings.
//
// The path must be coding at all. Datagrams carry no reliability of their own,
// so on a path clean enough not to warrant parity an uncoded lost frame waits
// for the session's re-issue where the stream would have retransmitted it
// within a round trip.
//
// And the flow must be one that wants latency more than bandwidth. Coding and
// retransmission cost the same thing in different currencies: on a memoryless
// erasure channel retransmission resends only what was lost, 1/(1-p), where a
// code must provision for the binomial. Measured live at 37% loss, a
// bulk download ran at 10.1 Mbit/s on the stream and 5.0 coded -- the code
// spending exactly the difference the arithmetic predicts. A small exchange
// went the other way, 1.9 s uncoded against 618 ms coded, because there the
// currency is a round trip and not a byte. So bulk stays on the stream and
// everything else is coded.
func (c *frameConn) bulkFrame(f protocol.Frame) bool {
	switch f.Header.Type {
	case protocol.TypeData:
		return c.codesData()
	case protocol.TypePacket:
		return c.packetsOnDatagrams()
	default:
		return false
	}
}

// packetsOnDatagrams reports whether this lane's SOCKS UDP packets go over the
// connection's datagrams.
//
// It does not ask whether the path is coding, which is the one place this
// differs from data. A data frame is on the coded path for its parity, and
// where parity costs more than a retransmission it belongs on the stream. A
// UDP packet is there for the substrate itself: it must not be retransmitted,
// because an application that chose UDP has already decided a late packet is
// worse than a lost one, and it must not hold up the packet behind it, which
// on a stream it does at every gap. Both of those are true on a clean path as
// well as a lossy one, so the question is only whether the substrate exists.
//
// It exists exactly when QUIC negotiated DATAGRAM in both directions, which
// is also what makes this symmetric without a capability of its own: both
// endpoints build their coded path from the same connection state, so a
// sender never routes a packet to a substrate its peer is not reading.
// A TLS/TCP lane has no such path and keeps the stream framing unchanged.
func (c *frameConn) packetsOnDatagrams() bool {
	return c.bulk != nil && !c.packetsForcedToStream
}

// codesData reports whether this lane's data frames are going over the coded
// path right now. Both conditions above have to hold, and it is one question
// rather than two because the scheduler asks the same one: a lane whose data
// is coded can lose a chunk outright and needs to be allowed to resend it,
// while a lane whose data is on the stream must not, because QUIC has already
// retransmitted it and a second copy is pure waste.
//
// Asking two different questions in the two places is what made a bulk flow
// pay twice. The routing said "stream, because this flow is bulk"; the
// scheduler said "unreliable, because the path is coding" -- and so every
// chunk was re-issued on a lane that had already delivered it. Measured live,
// that halved a download: 6.2 Mbit/s against the 10.1 the same path gives when
// each chunk is sent once.
func (c *frameConn) codesData() bool {
	if !c.codingBulk() {
		return false
	}
	return c.wantsCoding == nil || c.wantsCoding()
}

// codingBulk reports whether this lane's data is going over the coded path,
// which is also what decides whether the lane can lose a chunk outright.
func (c *frameConn) codingBulk() bool { return c.bulk != nil && c.bulk.Coding() }

// Read returns the next control frame. It reads the stream synchronously,
// because that is what every caller's read deadline is set on, and a shared
// background reader cannot honour a deadline belonging to one caller -- a
// handshake timeout would kill the reader for everyone, which is exactly what
// it did.
//
// Bulk frames do not come through here. They arrive on their own substrate and
// are read by ReadBulk, because merging two substrates into one call means
// giving one of them the other's semantics.
func (c *frameConn) Read() (protocol.Frame, error) {
	return protocol.ReadFrame(c.reader)
}

// bulkFrames claims this lane's flow's share of the connection's coded
// datagrams. Nil when the lane has no coded substrate.
//
// The claim is by flow rather than by lane because the datagrams belong to the
// connection: one stream of them carries every flow multiplexed on it, so a
// reader per lane would consume frames belonging to other flows.
func (c *frameConn) bulkFrames(flowID uint64) <-chan protocol.Frame {
	demux := connBulkDemux(c.bulk, c.bulkQueueFrames)
	if demux == nil {
		return nil
	}
	return demux.subscribe(flowID)
}

func (c *frameConn) releaseBulk(flowID uint64) {
	if demux := connBulkDemux(c.bulk, c.bulkQueueFrames); demux != nil {
		demux.release(flowID)
	}
}

// DataSubstrates reports how many data frames this lane sent each way.
func (c *frameConn) DataSubstrates() (coded, stream uint64) {
	return c.codedData.Load(), c.streamData.Load()
}

// PacketSubstrates reports the same for SOCKS UDP packets.
func (c *frameConn) PacketSubstrates() (datagram, stream uint64) {
	return c.codedPackets.Load(), c.streamPackets.Load()
}

// CodedPath reports what the connection's coded substrate has done, or false
// when this lane has none.
//
// It is the connection's rather than this lane's, because the datagrams are:
// one coded path carries every flow multiplexed on the connection. A flow's
// log therefore shows the substrate it shared, which is what explains a flow
// that was carried well or badly by it.
func (c *frameConn) CodedPath() (coded.Stats, bool) {
	if c.bulk == nil {
		return coded.Stats{}, false
	}
	return c.bulk.Stats(), true
}

func (c *frameConn) countData(f protocol.Frame, coded bool) {
	switch f.Header.Type {
	case protocol.TypeData:
		if coded {
			c.codedData.Add(1)
		} else {
			c.streamData.Add(1)
		}
	case protocol.TypePacket:
		if coded {
			c.codedPackets.Add(1)
		} else {
			c.streamPackets.Add(1)
		}
	}
}

func (c *frameConn) Write(f protocol.Frame) error {
	if c.bulkFrame(f) {
		c.countData(f, true)
		if err := c.writeCoded(f); err != nil {
			return err
		}
		if c.needsOpenSafetyCopy(f) {
			c.countData(f, false)
			c.writeMu.Lock()
			defer c.writeMu.Unlock()
			return c.writeLocked(f)
		}
		return nil
	}
	c.countData(f, false)
	c.writeMu.Lock()
	defer c.writeMu.Unlock()
	return c.writeLocked(f)
}

// writeCoded hands a bulk frame to the coded substrate, falling back to the
// control stream if it will not take it: correctness is not worth trading for
// the coding.
func (c *frameConn) writeCoded(f protocol.Frame) error {
	buf, err := protocol.AppendFrame(nil, f)
	if err != nil {
		return err
	}
	if err := c.bulk.Send(buf); err != nil {
		c.writeMu.Lock()
		defer c.writeMu.Unlock()
		return c.writeLocked(f)
	}
	return nil
}

func (c *frameConn) writeLocked(f protocol.Frame) error {
	buf, err := protocol.AppendFrame(c.writeBuf[:0], f)
	if err != nil {
		return err
	}
	// Retain the grown buffer for the next frame, but do not let one oversized
	// payload pin a large allocation for the life of the lane.
	//
	// The bound is a memory policy rather than a wire limit: protocol.MaxPayload
	// is what a peer may legally send, and retaining that much per lane on every
	// lane that once carried a maximum-size datagram is not the same question as
	// whether the frame was legal. Ordinary chunked DATA sits well under this,
	// so the common path still reuses its buffer.
	if cap(buf) <= writeBufferRetain {
		c.writeBuf = buf
	}
	return writeFull(c.control, buf)
}

const frameWriteTimeout = 15 * time.Second

// WriteContext bounds a transport write even when the peer stops consuming
// stream data.  A QUIC stream and TLS connection both expose a write-specific
// deadline; transports without that optional method retain their normal
// behavior and are still interruptible by Close from the flow coordinator.
func (c *frameConn) WriteContext(ctx context.Context, f protocol.Frame) error {
	if c.bulkFrame(f) {
		if err := ctx.Err(); err != nil {
			return err
		}
		c.countData(f, true)
		if err := c.writeCoded(f); err != nil {
			return err
		}
		if !c.needsOpenSafetyCopy(f) {
			return nil
		}
		c.countData(f, false)
		return c.writeControlContext(ctx, f)
	}
	c.countData(f, false)
	return c.writeControlContext(ctx, f)
}

func (c *frameConn) needsOpenSafetyCopy(f protocol.Frame) bool {
	return f.Header.Type == protocol.TypeData && c.openUnconfirmed != nil &&
		c.openUnconfirmed() && c.openSafetyCopy.CompareAndSwap(true, false)
}

func (c *frameConn) writeControlContext(ctx context.Context, f protocol.Frame) error {
	c.writeMu.Lock()
	defer c.writeMu.Unlock()
	if err := ctx.Err(); err != nil {
		return err
	}
	if deadlineConn, ok := c.control.(interface{ SetWriteDeadline(time.Time) error }); ok {
		deadline := time.Now().Add(frameWriteTimeout)
		if ctxDeadline, has := ctx.Deadline(); has && ctxDeadline.Before(deadline) {
			deadline = ctxDeadline
		}
		if err := deadlineConn.SetWriteDeadline(deadline); err != nil {
			return err
		}
		defer deadlineConn.SetWriteDeadline(time.Time{})
	}
	return c.writeLocked(f)
}

// transport is the substrate a lane's statistics come from. It is the control
// stream's, because that is the QUIC connection: the coded path rides the same
// one.
func (c *frameConn) transport() io.ReadWriteCloser { return c.control }

// Close ends this lane's framing. The coded substrate is deliberately left
// alone: it belongs to the QUIC connection and is shared with every other lane
// on it, so closing it here would take those down too.
func (c *frameConn) Close() error {
	c.closeOnce.Do(func() { close(c.done) })
	return c.control.Close()
}
