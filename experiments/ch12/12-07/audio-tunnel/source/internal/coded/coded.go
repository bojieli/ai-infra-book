// Package coded carries frames over an unreliable datagram service, repairing
// the path's erasures with a code so that most of them cost nothing.
//
// It does not make delivery reliable, and that is the point. The path this
// project targets erases about 42% of packets independently of the sending
// rate, and a code sized for that delivers all but about a thousandth of what
// it carries without a round trip. The remaining thousandth is a job the layer
// above already does: the session sequences by byte offset, acknowledges with
// ranges, retains what is unacknowledged and re-issues it.
//
// A reliability layer here would be a second and worse copy of that. The first
// version of this package was exactly that -- its own block acknowledgements,
// its own retransmission timer, its own flow control, its own in-order
// delivery -- and it carried 1.2 Mbit/s where the path carried 14.5, because
// its feedback was a timer where QUIC's is an arrival and its delivery was
// in-order where the session above already tolerates gaps.
//
// So here a symbol either survives or it does not. If it does not, the frames
// it carried are lost, which is a thing the session above is built to survive.
//
// The code is a sliding window rather than a block code. A block code has to
// choose its parity when it seals the block, before it has finished sending
// into the path it is sizing for; here the source symbols go as they are
// produced and repairs follow at whatever rate the path is currently measured
// to need. Redundancy therefore reflects what is known now rather than what
// was known when a block was sealed, and a repair can cover an erasure that
// happened several symbols ago -- so a burst that would exceed one block's
// parity is spread across every repair that reaches back over it.
//
// Nothing here waits for anything else. A symbol carrying whole frames
// delivers them the moment it arrives, and a frame too large for one symbol
// waits only for its own symbols. An erasure costs the frames it carried and
// nothing behind them, which is the property that made datagrams worth using
// instead of a stream.
package coded

import (
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"sync"
	"sync/atomic"
	"time"

	"github.com/bojieli/queqiao/internal/fec"
	"github.com/bojieli/queqiao/internal/lossmodel"
	"github.com/bojieli/queqiao/internal/pathmodel"
)

// Carrier is the unreliable datagram service underneath. A QUIC connection
// with datagrams enabled is one; so is a UDP socket.
//
// Close must make a blocked Receive return, because the path waits for its
// receive loop to stop before reporting that it has.
type Carrier interface {
	Send([]byte) error
	Receive() ([]byte, error)
	Close() error
}

// SizedCarrier is a Carrier that knows how large a datagram it will accept. A
// carrier that does not implement it is taken at the Config's word.
type SizedCarrier interface {
	Carrier
	MaxDatagramBytes() int
}

var (
	// ErrDatagramTooLarge is a carrier refusing a datagram for its size. It is
	// not fatal: the limit moves with the path, and a datagram refused for
	// being over it is loss like any other.
	ErrDatagramTooLarge = errors.New("coded: datagram too large for the carrier")
	// ErrClosed is returned once the path has stopped.
	ErrClosed = errors.New("coded: path closed")
	// ErrFrameTooLarge means a frame is beyond anything this path will carry.
	ErrFrameTooLarge = errors.New("coded: frame exceeds the largest carried")
)

const (
	// A source datagram names its transmission sequence, says what it is, and
	// identifies the symbol it carries. A repair adds the window it covers.
	//
	// The transmission sequence is what makes the channel measurable: loss is
	// only visible as a gap in the order things were sent, and neither the
	// symbol identifier nor the repair identifier is that order.
	sourceHeader = 4 + 1 + 4
	repairHeader = 4 + 1 + 4 + 4 + 2

	kindSource = 0
	kindRepair = 1

	// symbolHeader prefixes the coded vector: how much payload the symbol
	// carries, and which part of a frame it is. All three are inside the vector
	// rather than in the datagram header because all three have to survive
	// being reconstructed from repairs.
	symbolHeader = 2 + 2 + 2
	// frameHeader prefixes each frame inside a symbol that carries whole ones.
	frameHeader = 4
	// maxFrameBytes bounds what one frame may be.
	maxFrameBytes = 1 << 20
)

// Config describes the path. Every field has a usable default.
type Config struct {
	// SymbolBytes is the datagram one symbol is sent in. It is reduced to
	// whatever the carrier will actually accept.
	SymbolBytes int
	// Class selects the latency-against-efficiency trade the code makes.
	Class fec.Class
	// RoundTrip bounds the window: a window longer than a round trip's sending
	// holds symbols whose repair would arrive later than a retransmission, and
	// coding was for avoiding exactly that.
	RoundTrip time.Duration
	// Path is what the endpoint pair has been measured to do, shared with
	// everything else sending to it -- above all the congestion controller,
	// whose own acknowledgements reveal the erasure rate of exactly this
	// direction. Without it a path starts out believing it is clean and sends
	// its first symbols unprotected.
	Path pathmodel.Model
	// Pending bounds the frames queued for sending before Send blocks.
	Pending int
}

func (c Config) withDefaults() Config {
	if c.SymbolBytes <= 0 {
		c.SymbolBytes = 1100
	}
	if c.RoundTrip <= 0 {
		c.RoundTrip = 300 * time.Millisecond
	}
	if c.Pending <= 0 {
		c.Pending = 256
	}
	return c
}

// Path carries frames over a datagram carrier, coded against erasure.
type Path struct {
	cfg     Config
	carrier Carrier

	pending  chan []byte
	received chan []byte

	// The sending side belongs to one goroutine, and nothing else touches it.
	encoder *fec.WindowEncoder
	packed  []byte
	nextSeq uint32
	nextRID uint32
	credit  float64
	// burst counts what has been sent since the producer last drained, which
	// is what the tail protection is sized from. tail caches how much that
	// costs, because the answer is a binomial search and the question is asked
	// every time the producer pauses.
	burstSymbols int
	burstRepairs int
	tail         map[int]int
	tailAt       int64

	// The receiving side belongs to the receive loop, held under mu only
	// because Stats reads what it writes.
	mu        sync.Mutex
	decoder   *fec.WindowDecoder
	assembler assembler
	estimator *lossmodel.Estimator

	// code is cached because sizing one walks a binomial search, and the
	// question is asked per symbol while the answer changes on the timescale
	// the path does.
	code     atomic.Pointer[coding]
	codedAt  atomic.Int64
	sent     atomic.Uint64
	repairs  atomic.Uint64
	oversize atomic.Uint64
	// arrivals counts datagrams that reached this path, of which sources
	// carried a source symbol. They are the receive direction's own
	// denominator: sent above counts what this endpoint put on the wire in the
	// other direction, so a loss ratio taken against it is not a rate at all
	// and can exceed one without anything being wrong with the path.
	arrivals atomic.Uint64
	sources  atomic.Uint64
	// malformed counts datagrams a peer sent that protocol 1 does not permit.
	// It is kept apart from the erasure estimate on purpose: a rejected
	// datagram is a peer disagreeing about the wire, and folding it into loss
	// would have this path answer a non-conforming sender by buying more
	// parity for a channel that is not erasing anything.
	malformed atomic.Uint64

	closeOnce sync.Once
	done      chan struct{}
	wg        sync.WaitGroup
	err       atomic.Pointer[error]
}

// coding is the code the path is currently using: the plan it came from, how
// wide a window it keeps, and how many repairs each source symbol earns.
type coding struct {
	plan     fec.Plan
	capacity int
	rate     float64
}

// New starts a coded path over the carrier. Close stops it.
func New(carrier Carrier, cfg Config) *Path {
	cfg = cfg.withDefaults()
	p := &Path{
		cfg: cfg, carrier: carrier,
		pending:   make(chan []byte, cfg.Pending),
		received:  make(chan []byte, cfg.Pending),
		encoder:   fec.NewWindowEncoder(initialWindow),
		decoder:   fec.NewWindowDecoder(),
		estimator: lossmodel.New(lossmodel.Config{ReorderTolerance: 32}),
		done:      make(chan struct{}),
	}
	p.wg.Add(2)
	go p.sendLoop()
	go p.receiveLoop()
	return p
}

// initialWindow is what the encoder holds before the path has been measured.
// It is small because an unmeasured path is usually a new one, where the first
// thing sent is a short exchange rather than a stream.
const initialWindow = 16

// Send queues a frame. Delivery is not guaranteed: the code repairs what the
// path erases, and what it cannot repair is the caller's to notice.
func (p *Path) Send(frame []byte) error {
	if len(frame) > maxFrameBytes {
		return fmt.Errorf("%w: %d bytes", ErrFrameTooLarge, len(frame))
	}
	// Closed is checked before the queue, not alongside it: a select chooses
	// at random among ready cases, so offering both would accept sends on a
	// closed path whenever the queue happened to have room.
	select {
	case <-p.done:
		return p.failure()
	default:
	}
	queued := make([]byte, len(frame))
	copy(queued, frame)
	select {
	case p.pending <- queued:
		return nil
	case <-p.done:
		return p.failure()
	}
}

// Receive returns the next frame to arrive, repaired if it had to be.
func (p *Path) Receive() ([]byte, error) {
	select {
	case frame := <-p.received:
		return frame, nil
	case <-p.done:
		// Whatever was already repaired is still worth delivering.
		select {
		case frame := <-p.received:
			return frame, nil
		default:
		}
		return nil, p.failure()
	}
}

// sendLoop packs every frame that is already waiting into symbols, then sends
// what it has because nothing more is waiting.
//
// Draining is the seal signal, and it is not a policy. Under load there is
// always another frame, so symbols fill and the framing overhead is a
// hundredth; when the producer stops the symbol goes at once, so latency is
// the path's. Neither size nor time is chosen, so neither has to be re-chosen
// when the path or the traffic changes -- and a fixed delay is worse than
// either, because on a request-response protocol every delay lands on the
// critical path of the next request and they compound.
//
// The drain is also where the tail is protected. Repairs earned at the running
// rate cover the symbols that precede them, and the last symbols of a burst
// have nothing following: without this they would be the only ones the code
// left bare, and they are the ones an interactive exchange consists of.
func (p *Path) sendLoop() {
	defer p.wg.Done()
	for {
		var frame []byte
		select {
		case <-p.done:
			return
		case frame = <-p.pending:
		}
		for {
			if err := p.appendFrame(frame); err != nil {
				return
			}
			select {
			case frame = <-p.pending:
				continue
			case <-p.done:
				return
			default:
			}
			break
		}
		if err := p.flushPacked(); err != nil {
			return
		}
		if err := p.protectBurst(); err != nil {
			return
		}
	}
}

// appendFrame puts one frame on the wire, whole where it fits and in fragments
// where it does not.
//
// A frame never straddles the boundary between a symbol that carries whole
// frames and one that carries a fragment, because that is what would make one
// symbol's loss cost another symbol's frames. Small frames share a symbol with
// their neighbours; a large one occupies symbols of its own.
func (p *Path) appendFrame(frame []byte) error {
	limit := p.symbolPayload()
	if frameHeader+len(frame) > limit {
		if err := p.flushPacked(); err != nil {
			return err
		}
		return p.sendFragments(frame, limit)
	}
	if len(p.packed)+frameHeader+len(frame) > limit {
		if err := p.flushPacked(); err != nil {
			return err
		}
	}
	var head [frameHeader]byte
	binary.BigEndian.PutUint32(head[:], uint32(len(frame)))
	p.packed = append(append(p.packed, head[:]...), frame...)
	return nil
}

// sendFragments spreads one large frame over symbols of its own. Their count
// is what tells the receiver how many to wait for, and their identifiers are
// consecutive, so any one of them names the group.
func (p *Path) sendFragments(frame []byte, limit int) error {
	count := (len(frame) + limit - 1) / limit
	if count > maxFragments {
		return fmt.Errorf("%w: %d bytes", ErrFrameTooLarge, len(frame))
	}
	for i := 0; i < count; i++ {
		end := min((i+1)*limit, len(frame))
		if err := p.emit(frame[i*limit:end], i, count); err != nil {
			return err
		}
	}
	return nil
}

// maxFragments is what the fragment count field can say.
const maxFragments = 0xFFFF

// flushPacked sends the whole frames accumulated so far as one symbol.
func (p *Path) flushPacked() error {
	if len(p.packed) == 0 {
		return nil
	}
	err := p.emit(p.packed, 0, 1)
	p.packed = p.packed[:0]
	return err
}

// emit codes one symbol, sends it, and sends whatever repairs the running rate
// has earned by it.
func (p *Path) emit(payload []byte, index, count int) error {
	vector := make([]byte, symbolHeader+len(payload))
	binary.BigEndian.PutUint16(vector, uint16(len(payload)))
	binary.BigEndian.PutUint16(vector[2:], uint16(index))
	binary.BigEndian.PutUint16(vector[4:], uint16(count))
	copy(vector[symbolHeader:], payload)

	code := p.coding()
	p.encoder.SetCapacity(code.capacity)
	esi := p.encoder.Add(vector)
	if err := p.sendSource(esi, vector); err != nil {
		return err
	}
	p.burstSymbols++
	if p.burstSymbols >= p.encoder.Capacity() {
		// A window's worth has been covered at the running rate. What still
		// needs protecting when the producer stops is whatever follows this.
		p.burstSymbols, p.burstRepairs = 0, 0
	}
	for p.credit += code.rate; p.credit >= 1; p.credit-- {
		if err := p.sendRepair(0); err != nil {
			return err
		}
		p.burstRepairs++
	}
	return nil
}

// protectBurst tops the burst up to what the code says a run of that length
// needs.
//
// It covers exactly that run rather than the whole window, because a repair is
// as long as the longest symbol it spans: a short exchange protected over a
// window still holding a bulk transfer's symbols would cost a full packet each
// to repair a few dozen bytes.
func (p *Path) protectBurst() error {
	if p.burstSymbols <= 0 {
		return nil
	}
	for want := p.tailRepairs(p.burstSymbols); p.burstRepairs < want; p.burstRepairs++ {
		if err := p.sendRepair(p.burstSymbols); err != nil {
			return err
		}
	}
	p.burstSymbols, p.burstRepairs, p.credit = 0, 0, 0
	return nil
}

// tailRepairs is how many repairs a run of symbols needs to reach the target
// residual on its own, remembered until the path is re-measured.
func (p *Path) tailRepairs(symbols int) int {
	if at := p.codedAt.Load(); at != p.tailAt {
		p.tail, p.tailAt = map[int]int{}, at
	}
	if want, ok := p.tail[symbols]; ok {
		return want
	}
	want := 0
	if n, ok := fec.ShardsFor(symbols, p.channel(), p.params()); ok {
		want = n - symbols
	}
	p.tail[symbols] = want
	return want
}

func (p *Path) sendSource(esi uint32, vector []byte) error {
	d := make([]byte, sourceHeader+len(vector))
	binary.BigEndian.PutUint32(d, p.take())
	d[4] = kindSource
	binary.BigEndian.PutUint32(d[5:], esi)
	copy(d[sourceHeader:], vector)
	_, err := p.put(d)
	return err
}

// sendRepair emits one repair over the newest count symbols, or over the whole
// window when count is zero.
func (p *Path) sendRepair(count int) error {
	repair, ok := p.encoder.Repair(p.nextRID, count)
	p.nextRID++
	if !ok {
		return nil
	}
	d := make([]byte, repairHeader+len(repair.Vector))
	binary.BigEndian.PutUint32(d, p.take())
	d[4] = kindRepair
	binary.BigEndian.PutUint32(d[5:], repair.RID)
	binary.BigEndian.PutUint32(d[9:], repair.First)
	binary.BigEndian.PutUint16(d[13:], uint16(repair.Count))
	copy(d[repairHeader:], repair.Vector)
	sent, err := p.put(d)
	if sent {
		p.repairs.Add(1)
	}
	return err
}

func (p *Path) take() uint32 {
	seq := p.nextSeq
	p.nextSeq++
	return seq
}

// untake returns a transmission sequence that was never transmitted.
//
// The peer measures the channel from the gaps between the sequences it
// receives, so a number spent on a datagram the carrier refused is a hole in
// its numbering that the wire never made. Charging the channel for a casualty
// of this endpoint's own transport is how a local failure becomes a measured
// erasure rate, and that rate sizes the parity which then becomes load on the
// path that was already failing. Only the send loop takes a sequence, and it
// takes the next one immediately after this, so handing the number back leaves
// the numbering describing exactly what went out.
func (p *Path) untake() { p.nextSeq-- }

// put hands one datagram to the carrier and reports whether it reached it.
func (p *Path) put(d []byte) (bool, error) {
	switch err := p.carrier.Send(d); {
	case err == nil:
		p.sent.Add(1)
		return true, nil
	case errors.Is(err, ErrDatagramTooLarge):
		// The path's estimate moved under us. Losing this datagram is cheaper
		// than losing the connection, and the next symbol is sized from the
		// carrier's revised limit. The symbol it carried is still lost -- the
		// session above re-issues it -- but it was lost here rather than on
		// the wire, so the peer must not be shown a gap for it.
		p.oversize.Add(1)
		p.untake()
		return false, nil
	default:
		p.untake()
		p.fail(err)
		return false, err
	}
}

func (p *Path) receiveLoop() {
	defer p.wg.Done()
	for {
		d, err := p.carrier.Receive()
		if err != nil {
			p.fail(err)
			return
		}
		for _, frame := range p.onDatagram(d) {
			select {
			case p.received <- frame:
			case <-p.done:
				return
			}
		}
	}
}

// onDatagram takes one arrival and returns whatever frames it completed --
// frames it carried itself, frames an older symbol carried that it repaired,
// or none.
func (p *Path) onDatagram(d []byte) [][]byte {
	if len(d) < sourceHeader {
		return nil
	}
	seq := binary.BigEndian.Uint32(d)

	p.mu.Lock()
	defer p.mu.Unlock()
	// Every arrival measures the channel, including one carrying nothing new:
	// the gaps between transmission sequences are what loss is.
	p.arrivals.Add(1)
	p.estimator.Observe(uint64(seq))

	var delivered fec.Delivery
	var frames [][]byte
	switch d[4] {
	case kindSource:
		esi := binary.BigEndian.Uint32(d[5:])
		vector := d[sourceHeader:]
		p.sources.Add(1)
		delivered = p.decoder.Source(esi, vector)
		frames = p.assembler.arrived(esi, vector, frames)
	case kindRepair:
		if len(d) < repairHeader {
			return nil
		}
		count := int(binary.BigEndian.Uint16(d[13:]))
		// The count is two bytes on the wire and so can name a span of 65535,
		// which is far wider than protocol 1 permits and would ask this
		// receiver to solve over a system it has no obligation to hold. The
		// bound belongs here, before the symbol reaches the decoder, because
		// this is the last point that still knows the datagram came from a
		// peer rather than from this process.
		if count <= 0 || count > fec.MaxRepairWindow {
			p.malformed.Add(1)
			return nil
		}
		delivered = p.decoder.Repair(fec.RepairSymbol{
			RID:    binary.BigEndian.Uint32(d[5:]),
			First:  binary.BigEndian.Uint32(d[9:]),
			Count:  count,
			Vector: d[repairHeader:],
		})
	default:
		return nil
	}
	for _, r := range delivered.Recovered {
		frames = p.assembler.arrived(r.ESI, r.Vector, frames)
	}
	for _, esi := range delivered.Lost {
		p.assembler.lost(esi)
	}
	return frames
}

// assembler turns symbols back into frames.
//
// A symbol carrying whole frames needs nothing else, so its frames are
// delivered as it arrives -- out of order with respect to other symbols, which
// is what the session above already handles and what a stream could not have
// given it. A frame spread over several symbols waits for its own, and for
// nothing else.
type assembler struct {
	groups map[uint32]*fragmentGroup
	high   uint32
	seen   bool
	lostN  uint64
}

type fragmentGroup struct {
	parts [][]byte
	held  int
	bytes int
}

func (a *assembler) note(esi uint32) {
	if !a.seen {
		a.seen, a.high = true, esi
		return
	}
	if int32(esi-a.high) > 0 {
		a.high = esi
		a.prune()
	}
}

func (a *assembler) arrived(esi uint32, vector []byte, out [][]byte) [][]byte {
	a.note(esi)
	payload, index, count, ok := parseSymbol(vector)
	if !ok {
		return out
	}
	if count == 1 {
		return parseFrames(payload, out)
	}
	first := esi - uint32(index)
	group := a.groups[first]
	if group == nil {
		if a.groups == nil {
			a.groups = map[uint32]*fragmentGroup{}
		}
		group = &fragmentGroup{parts: make([][]byte, count)}
		a.groups[first] = group
	}
	if index >= len(group.parts) || group.parts[index] != nil {
		return out
	}
	group.parts[index] = append([]byte(nil), payload...)
	group.held++
	group.bytes += len(payload)
	if group.held < len(group.parts) {
		return out
	}
	delete(a.groups, first)
	frame := make([]byte, 0, group.bytes)
	for _, part := range group.parts {
		frame = append(frame, part...)
	}
	return append(out, frame)
}

// lost drops the frames that depended on a symbol nothing can still repair.
func (a *assembler) lost(esi uint32) {
	a.note(esi)
	a.lostN++
	for first, group := range a.groups {
		if int32(esi-first) >= 0 && int32(esi-first) < int32(len(group.parts)) {
			delete(a.groups, first)
		}
	}
}

// assemblerSlack is how far behind the newest symbol a partly-arrived frame is
// kept.
//
// The decoder normally says when a symbol is lost, and says it at the only
// moment that is certain: when no repair can still reach it. This covers the
// case it cannot -- a symbol erased before anything had arrived to establish
// that the stream had started, which the decoder has no evidence ever existed.
//
// It is the decoder's own minimum width rather than a number of its own,
// because a frame dropped here while the decoder could still repair its
// symbols would throw away a repair that had already arrived and been solved.
const assemblerSlack = fec.MinDecoderWidth

func (a *assembler) prune() {
	for first, group := range a.groups {
		if int32(a.high-(first+uint32(len(group.parts)))) > assemblerSlack {
			delete(a.groups, first)
		}
	}
}

func parseFrames(payload []byte, out [][]byte) [][]byte {
	for len(payload) >= frameHeader {
		size := binary.BigEndian.Uint32(payload)
		payload = payload[frameHeader:]
		// Compared as a uint64 rather than converted to int first. On a
		// 32-bit build int(uint32) wraps negative for anything past 2 GiB,
		// a negative size passes a `size > len(payload)` test, and the slice
		// below panics on a negative bound -- so four bytes off the wire
		// take down a receive loop that has no recover above it. The bound
		// is only accidentally safe on 64-bit, which is not a property to
		// leave a wire parser resting on.
		if uint64(size) > uint64(len(payload)) {
			break
		}
		out = append(out, append([]byte(nil), payload[:size]...))
		payload = payload[size:]
	}
	return out
}

func parseSymbol(vector []byte) ([]byte, int, int, bool) {
	if len(vector) < symbolHeader {
		return nil, 0, 0, false
	}
	length := int(binary.BigEndian.Uint16(vector))
	index := int(binary.BigEndian.Uint16(vector[2:]))
	count := int(binary.BigEndian.Uint16(vector[4:]))
	// A recovered symbol is padded to the length of the repair that recovered
	// it, so it is long enough rather than exactly long enough.
	if count < 1 || index >= count || symbolHeader+length > len(vector) {
		return nil, 0, 0, false
	}
	return vector[symbolHeader : symbolHeader+length], index, count, true
}

// symbolBytes is the configured datagram size, reduced to what the carrier
// accepts. The limit is not a constant: QUIC's estimate of what fits in a
// packet moves with the path, and a datagram over it is refused rather than
// fragmented.
func (p *Path) symbolBytes() int {
	size := p.cfg.SymbolBytes
	if sized, ok := p.carrier.(SizedCarrier); ok {
		if limit := sized.MaxDatagramBytes(); limit > 0 && limit < size {
			size = limit
		}
	}
	if floor := repairHeader + symbolHeader + frameHeader + 1; size < floor {
		size = floor
	}
	return size
}

// symbolPayload is how much of a frame one symbol carries. It leaves room for
// the larger of the two datagram headers, so that a repair covering a symbol
// fits on the wire as surely as the symbol itself did.
func (p *Path) symbolPayload() int {
	return p.symbolBytes() - repairHeader - symbolHeader
}

// channel is what is known about the direction this path sends into.
//
// The congestion controller on this connection measures it -- the erasure
// rate of the direction it sends into is exactly what its own acknowledgements
// reveal -- so the shared model has the answer before the first symbol is sent
// when the bidirectional path prewarm completed. The coded layer never infers
// its outbound direction from packets received in the reverse direction:
// those observations cannot distinguish physical erasure from congestion the
// peer caused by its sending rate.
func (p *Path) channel() lossmodel.Snapshot {
	if p.cfg.Path == nil {
		return lossmodel.Snapshot{BurstFactor: 1, ArrivalAfterLoss: 1}
	}
	state := p.cfg.Path.Current()
	// The measured erasure. There is no longer a separate floor to choose
	// wrongly between: the classifier that produced one is gone, and this is
	// what the path is doing. Floor is set to the same figure because the
	// snapshot type still carries the field for the estimator's own use.
	burst := state.BurstFactor
	if burst < 1 {
		burst = 1
	}
	return lossmodel.Snapshot{
		Loss: state.Erasure, Floor: state.Erasure, Recent: state.Erasure,
		BurstFactor: burst, ArrivalAfterLoss: 1 - state.Erasure,
		Samples: state.ObservedSamples, Decided: uint64(state.ObservedSamples),
	}
}

func (p *Path) params() fec.Params {
	return fec.Params{
		Class:           p.cfg.Class,
		ShardBytes:      p.symbolBytes(),
		RateBytesPerSec: p.rate(),
		RoundTrip:       p.roundTrip(),
	}
}

// rate is the sending rate the window is sized against.
func (p *Path) rate() float64 {
	if p.cfg.Path != nil {
		if share := p.cfg.Path.Current().Share; share > 0 {
			return share
		}
	}
	return float64(p.symbolBytes()) * 64 / p.roundTrip().Seconds()
}

// roundTrip is the path's own, where it has been measured, and the
// configured guess until then.
//
// The window is a round trip's worth of symbols, so this is what sizes it. A
// configured 300 ms against a measured 245 ms is a window a fifth too wide,
// which is a fifth further back than a repair can usefully reach -- and the
// model that measures the erasure this window is sized for has been measuring
// the round trip alongside it all along.
func (p *Path) roundTrip() time.Duration {
	if p.cfg.Path != nil {
		if rtt := p.cfg.Path.Current().RoundTrip; rtt > 0 {
			return rtt
		}
	}
	return p.cfg.RoundTrip
}

// codingTTL is how long a chosen code stands before it is chosen again. The
// path's erasure rate moves on the scale of seconds, and the estimate behind
// it is filtered over thousands of packets, so a fifth of a second is far
// finer than the input can justify.
const codingTTL = 200 * time.Millisecond

// coding is the window and repair rate the path is currently using.
//
// The window is the plan's block length, which is what a round trip's sending
// comes to: a repair reaching further back than that would arrive later than
// the retransmission it was meant to replace. The rate is not the plan's,
// though, because a window is not a block -- its repairs chain across
// neighbouring windows, so it reaches the same residual for less parity, and
// taking the block's rate would spend a fifth of the wire on a residual nobody
// asked for.
func (p *Path) coding() coding {
	now := time.Now().UnixNano()
	if at := p.codedAt.Load(); now-at < int64(codingTTL) {
		if stored := p.code.Load(); stored != nil {
			return *stored
		}
	}
	channel, params := p.channel(), p.params()
	plan := fec.Choose(channel, params)
	current := coding{plan: plan, capacity: initialWindow}
	if plan.Code && plan.K > 0 {
		current.capacity = min(plan.K, fec.MaxRepairWindow)
		current.rate = fec.WindowRate(current.capacity, channel, params)
	}
	p.code.Store(&current)
	p.codedAt.Store(now)
	return current
}

// Coding reports whether this path is currently worth sending bulk payload
// over.
//
// It is false on a path clean enough that parity costs more than it saves, and
// then bulk belongs on the stream instead: datagrams have no reliability of
// their own, so an uncoded lost frame waits for the session's re-issue where a
// stream would have retransmitted it in a round trip. Asking this rather than
// configuring it is what lets one build serve both a clean path and a 42%
// erasure channel without being told which it is on.
func (p *Path) Coding() bool { return p.coding().plan.Code }

// Stats reports what the path has done and what it believes.
type Stats struct {
	Snapshot lossmodel.Snapshot
	Plan     fec.Plan
	Window   int
	// Sent is datagrams put on the wire, of which Repairs carried no new data.
	Sent    uint64
	Repairs uint64
	// Recovered is symbols the code reconstructed; Lost is symbols that left
	// the window still missing, and whose frames the session must re-issue.
	Recovered uint64
	Lost      uint64
	// Arrived is datagrams this path received, of which Sources carried a
	// source symbol.
	//
	// They are here because Lost had no denominator without them. Sent counts
	// the direction this endpoint transmits into and Lost the direction it
	// receives, so "lost over sent" is not a rate and reaches ten on a
	// perfectly ordinary asymmetric flow. Erasure and Residual below are the
	// rates that can actually be read.
	Arrived  uint64
	Sources  uint64
	Oversize uint64
	// Malformed is datagrams rejected for breaking the protocol's bounds,
	// which is a peer problem rather than a path problem.
	Malformed uint64
}

// Stats reports what this path has done and what it believes.
func (p *Path) Stats() Stats {
	p.mu.Lock()
	snapshot := p.estimator.Snapshot()
	recovered, lost := p.decoder.Recovered(), p.assembler.lostN
	p.mu.Unlock()
	current := coding{}
	if stored := p.code.Load(); stored != nil {
		current = *stored
	}
	return Stats{
		Snapshot: snapshot, Plan: current.plan, Window: current.capacity,
		Sent: p.sent.Load(), Repairs: p.repairs.Load(),
		Recovered: recovered, Lost: lost,
		Arrived: p.arrivals.Load(), Sources: p.sources.Load(),
		Oversize:  p.oversize.Load(),
		Malformed: p.malformed.Load(),
	}
}

// SourceSymbols is how many of the peer's source symbols this path has
// accounted for: those that arrived, those the code reconstructed, and those
// that left the window unrecovered. Every symbol the peer sent ends in exactly
// one of the three, which is what makes it a denominator.
func (s Stats) SourceSymbols() uint64 { return s.Sources + s.Recovered + s.Lost }

// Erasure is the share of source symbols that did not arrive, whether the code
// repaired them or not: the wire loss this receiver measured, in [0,1].
func (s Stats) Erasure() float64 {
	total := s.SourceSymbols()
	if total == 0 {
		return 0
	}
	return float64(s.Recovered+s.Lost) / float64(total)
}

// Residual is the share of source symbols the code could not repair, which is
// what the session above has to re-issue. It is in [0,1] by construction.
func (s Stats) Residual() float64 {
	total := s.SourceSymbols()
	if total == 0 {
		return 0
	}
	return float64(s.Lost) / float64(total)
}

func (p *Path) fail(err error) {
	if err != nil && !errors.Is(err, io.EOF) {
		wrapped := fmt.Errorf("coded: carrier: %w", err)
		p.err.CompareAndSwap(nil, &wrapped)
	}
	p.closeOnce.Do(func() { close(p.done) })
}

func (p *Path) failure() error {
	if stored := p.err.Load(); stored != nil {
		return *stored
	}
	return ErrClosed
}

// Close stops the path and its carrier.
func (p *Path) Close() error {
	p.closeOnce.Do(func() { close(p.done) })
	err := p.carrier.Close()
	p.wg.Wait()
	return err
}
