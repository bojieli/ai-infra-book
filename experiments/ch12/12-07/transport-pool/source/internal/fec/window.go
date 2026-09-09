// Package fec repairs a path that erases packets, and decides how much repair
// to send.
//
// It exists because the path this project targets is an erasure channel rather
// than a congested one. About 38% of packets are dropped in the download
// direction independently of the sending rate
// (docs/archive/2026-08-development/DESIGN-ERASURE.md), and
// independent loss at that rate is cheap to repair and expensive in round
// trips to retransmit. On a memoryless channel with erasure probability p the
// capacity is (1-p) times the line rate whatever the scheme, so a code buys no
// bandwidth that retransmission does not -- what it buys is the round trip,
// and that is why it is worth having for a small exchange and not for a bulk
// transfer.
//
// Choose and WindowRate (rate.go) decide the window and the repair rate from
// what the path has been measured to do. The code itself is here, and it is a
// sliding window rather than a block.
//
// A block code has to choose (k, n) when it seals the block, which means it
// has to know the path before it has finished sending into it. Everything
// after that is fixed: if the erasure rate rises, the parity already on the
// wire is the parity the block gets, and a block that turns out to be
// under-protected is lost whole. The shared path model makes that first guess
// a good one, but it is still a guess made at the wrong moment.
//
// Here the source symbols are sent as they are produced, unaltered -- so a
// receiver that loses nothing does no work at all -- and repair symbols are
// emitted alongside them at whatever rate the path is currently measured to
// need. A repair is a random linear combination of the last few source
// symbols, so it is not tied to a block: one repair emitted now can recover an
// erasure that happened several symbols ago, and the decision of how many to
// emit is taken after the data rather than before it. Redundancy therefore
// always reflects what is known now.
//
// Two properties follow that a block code cannot have. The window is a
// continuous interleaver, so a burst that would exceed one block's parity is
// spread across every repair that covers it. And the overhead at small sizes
// is set by the window rather than by the transfer: protecting a single small
// symbol with a block code means sending it n times over, because there is
// nothing else in its block, where here it is covered by repairs that also
// cover its neighbours.
//
// Coefficients are drawn over GF(256), so an equation is degenerate with
// probability about 1/256 -- small enough that the count of repairs, not their
// independence, is what determines recovery.
package fec

// MaxRepairWindow is the widest span protocol 1 allows one repair symbol to
// cover, and therefore the widest a receiver has to be able to solve over.
//
// A sliding window has no block boundary, so nothing in the format itself
// stops a sender from covering an arbitrarily long span -- and a receiver with
// no stated bound has two bad options: allocate whatever the wire asks for, or
// pick a private limit and silently drop the repairs above it. The second is
// the worse of the two, because a discarded repair is indistinguishable from
// an erased one: the flow degrades exactly as if the path were worse, on a
// transport whose entire purpose is to measure how bad the path is.
//
// So the bound is stated rather than left to each implementation. 256 is not
// arbitrary: it is MaxShards, the number of distinct elements GF(256) offers,
// and it is already the ceiling Choose applies when it sizes the sender's
// window. A conforming sender therefore never wanted to exceed it, and a
// receiver can size its linear system once and be right for every peer.
const MaxRepairWindow = MaxShards

// MinDecoderWidth is the smallest receiver window that can admit every legal
// repair.
//
// It is twice MaxRepairWindow rather than equal to it because a repair names a
// span that must fit inside the window with the newer symbols that arrived
// while it was in flight; a window exactly as wide as the widest repair would
// have slid past the repair's oldest symbol by the time the repair landed, and
// would discard it for reaching behind the window -- which is precisely when
// the repair was needed.
const MinDecoderWidth = 2 * MaxRepairWindow

// RepairSymbol is a linear combination of the source symbols in one window.
// First and Count name the window so the receiver can regenerate the
// coefficients; RID seeds them.
type RepairSymbol struct {
	RID    uint32
	First  uint32
	Count  int
	Vector []byte
}

// RecoveredSymbol is a source symbol reconstructed from repairs.
type RecoveredSymbol struct {
	ESI    uint32
	Vector []byte
}

// Delivery is what one arrival produced: symbols recovered by it, and symbols
// that left the window still missing and so will never arrive.
type Delivery struct {
	Recovered []RecoveredSymbol
	Lost      []uint32
}

// windowCoefficient is the multiplier repair rid applies to the index'th
// source symbol of its window.
//
// It is generated rather than transmitted: a repair covering sixty-four
// symbols would otherwise carry sixty-four bytes of coefficients, which on
// this path is a twentieth of the packet. Both ends compute it from the
// repair's identity and the position, and the sequence only has to look random
// to a linear system, not to an adversary.
func windowCoefficient(rid uint32, index int) byte {
	x := rid*2654435761 + uint32(index)*2246822519
	x ^= x >> 15
	x *= 2654435761
	x ^= x >> 13
	x *= 2246822519
	x ^= x >> 16
	// Uniform over the 255 non-zero elements: a zero coefficient would drop a
	// symbol out of the combination it was meant to cover.
	return byte(x%255) + 1
}

// WindowCoefficients is the coefficient row repair rid applies to the count
// symbols of its window, lowest index first.
//
// This exists because the row is the one part of the wire format that is never
// on the wire. Two implementations that disagree about it still exchange
// well-formed datagrams; the repairs simply fail to solve, and the receiver
// reports the loss it would have reported on a bad path. That failure is
// indistinguishable from the condition the code exists to fix, so the row has
// to be pinned by a committed vector rather than by prose. See
// testdata/protocol1/vectors.json.
func WindowCoefficients(rid uint32, count int) []byte {
	if count <= 0 {
		return nil
	}
	row := make([]byte, count)
	for i := range row {
		row[i] = windowCoefficient(rid, i)
	}
	return row
}

// WindowEncoder retains the most recent source symbols so that a repair can be
// built from them at any time.
type WindowEncoder struct {
	// ring is indexed by the low bits of the symbol identifier, which is why
	// its length is a power of two: identifiers wrap at 2^32 and a ring whose
	// length does not divide that would renumber every slot when they do.
	ring  [][]byte
	mask  uint32
	first uint32
	next  uint32
	held  int
}

// NewWindowEncoder retains capacity source symbols.
func NewWindowEncoder(capacity int) *WindowEncoder {
	e := &WindowEncoder{}
	e.SetCapacity(capacity)
	return e
}

// SetCapacity changes how far back a repair may reach, keeping the newest
// symbols that still fit.
//
// It is expected to be called as the path is re-measured: the window is the
// sliding code's analogue of a block length, and the same round trip and rate
// that would have sized a block size this.
func (e *WindowEncoder) SetCapacity(capacity int) {
	// The span is bounded by what a receiver is required to solve over, not by
	// what this sender would like. Exceeding it would produce repairs a
	// conforming peer must discard, which costs the parity and the bandwidth
	// and delivers neither.
	if capacity > MaxRepairWindow {
		capacity = MaxRepairWindow
	}
	size := roundUpPowerOfTwo(capacity)
	if size == len(e.ring) {
		return
	}
	ring := make([][]byte, size)
	keep := e.held
	if keep > size {
		keep = size
	}
	first := e.next - uint32(keep)
	for i := 0; i < keep; i++ {
		esi := first + uint32(i)
		ring[esi&uint32(size-1)] = e.ring[esi&e.mask]
	}
	e.ring, e.mask, e.first, e.held = ring, uint32(size-1), first, keep
}

// Capacity is how many source symbols the window holds.
func (e *WindowEncoder) Capacity() int { return len(e.ring) }

// Held is how many it currently holds, which is less until it has filled.
func (e *WindowEncoder) Held() int { return e.held }

// Add takes a source symbol into the window and returns its identifier. The
// symbol is copied, because the window outlives the caller's buffer.
func (e *WindowEncoder) Add(vector []byte) uint32 {
	esi := e.next
	e.next++
	e.ring[esi&e.mask] = append([]byte(nil), vector...)
	if e.held < len(e.ring) {
		e.held++
	} else {
		e.first++
	}
	return esi
}

// Repair builds a repair symbol over the newest count source symbols, or over
// everything the window holds when count is zero or larger.
//
// Its length is the longest symbol it covers rather than a fixed symbol size,
// and that is why the span is worth choosing. A wide window is what makes the
// code tolerate bursts, but it also makes every repair as long as the largest
// symbol in it -- so protecting the tail of a small exchange over a window
// still holding a bulk transfer's symbols would cost a full packet each to
// repair a few dozen bytes. Repairs emitted as the stream runs cover
// everything; repairs emitted to protect a burst that has just ended cover the
// burst.
//
// Shorter symbols are zero-extended, which is exactly what the receiver does
// with them, so the two agree without saying so.
func (e *WindowEncoder) Repair(rid uint32, count int) (RepairSymbol, bool) {
	if e.held == 0 {
		return RepairSymbol{}, false
	}
	if count <= 0 || count > e.held {
		count = e.held
	}
	if count > MaxRepairWindow {
		count = MaxRepairWindow
	}
	first := e.next - uint32(count)
	vlen := 0
	for i := 0; i < count; i++ {
		if n := len(e.ring[(first+uint32(i))&e.mask]); n > vlen {
			vlen = n
		}
	}
	vector := make([]byte, vlen)
	for i := 0; i < count; i++ {
		addScaled(windowCoefficient(rid, i), e.ring[(first+uint32(i))&e.mask], vector)
	}
	return RepairSymbol{RID: rid, First: first, Count: count, Vector: vector}, true
}

// WindowDecoder reconstructs source symbols from the repairs that cover them.
//
// It holds one linear system, kept in reduced row echelon form so that a row
// with a single unknown left is a recovered symbol and nothing has to be
// searched for. Symbols that leave the window unrecovered are reported lost:
// no repair can still reach them, and the layer above would rather be told now
// than wait.
type WindowDecoder struct {
	slots []decoderSlot
	mask  uint32
	// lo and high bound the identifiers the window holds, and lo trails the
	// newest by the window's width rather than resting where the first arrival
	// happened to be. The difference matters at the start: if the first symbols
	// are erased, a window anchored on the first arrival can never admit them,
	// and every repair covering them is discarded for reaching behind it --
	// which is precisely when the repairs were needed.
	//
	// They are compared by wrapping subtraction, so they stay correct where the
	// identifier wraps.
	lo, high uint32
	// origin is the oldest identifier known to exist. Below it the window is
	// merely reaching into what has not started yet, and a symbol there is
	// absent rather than lost.
	origin  uint32
	started bool
	rows    []*windowRow

	recovered uint64
	lost      uint64
	discarded uint64
}

type decoderSlot struct {
	esi    uint32
	vector []byte
	live   bool
	known  bool
}

// windowRow is one equation: coefficients over the symbols the window holds,
// and the constant term they sum to.
type windowRow struct {
	pivot uint32
	coef  []byte
	data  []byte
}

// NewWindowDecoder starts a decoder. Its window grows to whatever the repairs
// it sees turn out to span.
func NewWindowDecoder() *WindowDecoder {
	d := &WindowDecoder{}
	d.resize(defaultDecoderWidth)
	return d
}

const (
	// decoderWidth is the receiver's window, and it is fixed rather than grown.
	//
	// It used to start at 64 and widen to twice the largest span it had seen,
	// which is too late by construction. A repair covering the sender's whole
	// window is legal at any moment, including the first repair of a stream --
	// the emission rate decides when one is sent, and at a few per cent parity
	// that is tens of symbols apart. By the time such a repair arrives, a
	// window that narrow has already sledded past the symbols it covers and
	// discarded their values, so widening on arrival buys slots for symbols the
	// decoder can no longer name. The equation then has more unknowns than the
	// repair has terms and recovers nothing.
	//
	// The symptom of that is indistinguishable from a worse path: the flow sees
	// unrepaired erasures, the estimator sees loss, and the answer is more
	// parity for a channel that was never the problem. So the window is sized
	// once, from what the protocol permits a sender to cover, and every legal
	// repair is usable when it lands.
	decoderWidth        = MinDecoderWidth
	defaultDecoderWidth = decoderWidth
	// maxDecoderWidth is the same bound seen from the memory side: the linear
	// system is at worst width rows of width coefficients and every symbol in
	// the window is a retained buffer, so a fixed width is also what makes that
	// footprint a property of this build rather than of what a peer asks for.
	maxDecoderWidth = decoderWidth
)

// Source records a source symbol that arrived intact.
func (d *WindowDecoder) Source(esi uint32, vector []byte) Delivery {
	var out Delivery
	if !d.admit(esi, &out) {
		return out
	}
	d.witness(esi)
	if s := &d.slots[esi&d.mask]; s.live && s.known && s.esi == esi {
		return out
	}
	// The caller's buffer is its own; the window keeps this until it slides
	// past, and every equation covering it reads it in the meantime.
	d.substitute(esi, append([]byte(nil), vector...), &out, false)
	d.harvest(&out)
	return out
}

// Repair records a repair symbol, which may complete any number of the
// symbols its window covers -- including ones missing since long before it.
func (d *WindowDecoder) Repair(r RepairSymbol) Delivery {
	var out Delivery
	if r.Count <= 0 || len(r.Vector) == 0 {
		return out
	}
	if r.Count > MaxRepairWindow {
		// A span wider than the protocol allows. Counting it as discarded
		// rather than silently ignoring it is the difference between an
		// operator seeing a non-conforming peer and seeing a path that erases.
		d.discarded++
		return out
	}
	// A repair covers symbols that may not have been seen yet, and the newest
	// of them determines where the window has to reach. It is also proof that
	// every symbol in its window exists, which is how a symbol erased before
	// anything had arrived comes to be known about at all.
	if !d.admit(r.First+uint32(r.Count-1), &out) {
		return out
	}
	d.witness(r.First)
	if int32(r.First-d.lo) < 0 {
		// Its oldest symbol has already left the window, so the equation refers
		// to something nothing can name any more. Using it without that term
		// would be worse than dropping it: the missing symbol is not zero.
		d.discarded++
		return out
	}
	coef := make([]byte, len(d.slots))
	for i := 0; i < r.Count; i++ {
		esi := r.First + uint32(i)
		if int32(esi-d.lo) < 0 || int32(esi-d.high) >= 0 {
			continue
		}
		coef[esi&d.mask] = windowCoefficient(r.RID, i)
	}
	d.insert(coef, append([]byte(nil), r.Vector...), &out)
	return out
}

// Recovered reports how many source symbols the decoder reconstructed.
func (d *WindowDecoder) Recovered() uint64 { return d.recovered }

// Lost reports how many source symbols left the window unrecovered.
func (d *WindowDecoder) Lost() uint64 { return d.lost }

// Discarded reports how many unusable symbols or equations were dropped.
func (d *WindowDecoder) Discarded() uint64 { return d.discarded }

// Width is how many symbol slots the window holds. It is fixed at
// MinDecoderWidth for the decoder's whole life, so a legal repair is never
// refused for arriving after the window had reason to be wide.
func (d *WindowDecoder) Width() int { return len(d.slots) }

// admit brings esi into the window, sliding it forward and reporting whatever
// falls off the back. It returns false for an identifier already behind the
// window, which is a duplicate or a straggler and in either case too late.
func (d *WindowDecoder) admit(esi uint32, out *Delivery) bool {
	width := uint32(len(d.slots))
	if !d.started {
		d.started, d.origin, d.high = true, esi, esi+1
		d.lo = d.high - width
		return true
	}
	if int32(esi-d.lo) < 0 {
		return false
	}
	if int32(esi-d.high) >= 0 {
		d.high = esi + 1
		// Identifiers leaving the window are walked, because each is a symbol
		// the layer above has to be told will never arrive. But the
		// identifier is the peer's to choose: one source symbol naming an ESI
		// 2^30 ahead of the window makes this a loop of 2^30 evictions, each
		// scanning the row set and appending a Lost entry, all of it under
		// the receiving path's lock. One datagram off the wire wedges the
		// receive loop and exhausts memory on the way.
		//
		// Only what was admitted can be held, and at most a window's worth
		// can be admitted, so a window of evictions covers every slot and
		// every row that could still refer to one. Past that the walk is
		// counting out identifiers that were never there, and the window is
		// moved to its new place in one step instead.
		walked := d.lo + width
		for ; d.high-d.lo > width && int32(d.lo-walked) < 0; d.lo++ {
			d.evict(d.lo, out)
		}
		if d.high-d.lo > width {
			d.lo = d.high - width
		}
	}
	return true
}

// witness records that an identifier is known to exist, which is what
// separates a symbol that was erased from one that has not been sent.
func (d *WindowDecoder) witness(esi uint32) {
	if d.started && int32(esi-d.origin) < 0 && int32(esi-d.lo) >= 0 {
		d.origin = esi
	}
}

// evict drops the oldest identifier and everything that depended on it. An
// equation that referred to a symbol nobody can name any longer is not an
// equation, and a symbol that leaves unknown is lost for good.
func (d *WindowDecoder) evict(esi uint32, out *Delivery) {
	index := esi & d.mask
	s := &d.slots[index]
	held := s.live && s.esi == esi
	// A symbol nothing ever held is exactly as lost as one held incomplete, and
	// the layer above needs to hear about both. Only identifiers below the
	// oldest known to exist are neither: there the window is reaching into what
	// had not started.
	if !(held && s.known) && int32(esi-d.origin) >= 0 {
		out.Lost = append(out.Lost, esi)
		d.lost++
	}
	if held {
		*s = decoderSlot{}
	}
	kept := d.rows[:0]
	for _, r := range d.rows {
		if r.coef[index] != 0 {
			d.discarded++
			continue
		}
		kept = append(kept, r)
	}
	d.rows = kept
}

// insert adds one equation to the system, reducing it against what is already
// known and then against the rows already held.
func (d *WindowDecoder) insert(coef, data []byte, out *Delivery) {
	for esi := d.lo; int32(esi-d.high) < 0; esi++ {
		index := esi & d.mask
		if coef[index] == 0 {
			continue
		}
		if s := &d.slots[index]; s.live && s.known {
			data = ensure(data, len(s.vector))
			addScaled(coef[index], s.vector, data)
			coef[index] = 0
		}
	}
	// Every held row has a pivot no other row touches, so one pass eliminates
	// all of them: reducing by one row cannot reintroduce another's pivot.
	for _, r := range d.rows {
		c := coef[r.pivot&d.mask]
		if c == 0 {
			continue
		}
		data = ensure(data, len(r.data))
		addScaled(c, r.data, data)
		mulSliceXor(c, r.coef, coef)
	}
	pivot, count := d.leading(coef)
	if count == 0 {
		// It said nothing the system did not already contain.
		d.discarded++
		return
	}
	if f := inv(coef[pivot&d.mask]); f != 1 {
		scaleBytes(f, coef)
		scaleBytes(f, data)
	}
	row := &windowRow{pivot: pivot, coef: coef, data: data}
	// Reduced form: clear this pivot from the rows already held, so that a row
	// with one unknown left is visible without solving for it.
	for _, r := range d.rows {
		c := r.coef[pivot&d.mask]
		if c == 0 {
			continue
		}
		r.data = ensure(r.data, len(row.data))
		addScaled(c, row.data, r.data)
		mulSliceXor(c, row.coef, r.coef)
	}
	d.rows = append(d.rows, row)
	d.harvest(out)
}

// harvest takes every row that has come down to one unknown, which makes its
// constant term that symbol. Recovering one can reduce another, so this
// repeats until nothing more falls out.
func (d *WindowDecoder) harvest(out *Delivery) {
	for progress := true; progress; {
		progress = false
		for i := 0; i < len(d.rows); i++ {
			r := d.rows[i]
			pivot, count := d.leading(r.coef)
			if count == 0 {
				d.rows = append(d.rows[:i], d.rows[i+1:]...)
				i--
				continue
			}
			if count > 1 {
				continue
			}
			// Removed before it is used: substituting the symbol rewrites every
			// held row, and this row's own data is the symbol.
			d.rows = append(d.rows[:i], d.rows[i+1:]...)
			i--
			d.substitute(pivot, r.data, out, true)
			progress = true
		}
	}
}

// substitute records a symbol as known and removes it from every equation that
// was waiting on it.
func (d *WindowDecoder) substitute(esi uint32, vector []byte, out *Delivery, recovered bool) {
	index := esi & d.mask
	s := &d.slots[index]
	if s.live && s.known && s.esi == esi {
		return
	}
	*s = decoderSlot{esi: esi, vector: vector, live: true, known: true}
	if recovered {
		out.Recovered = append(out.Recovered, RecoveredSymbol{ESI: esi, Vector: vector})
		d.recovered++
	}
	for _, r := range d.rows {
		c := r.coef[index]
		if c == 0 {
			continue
		}
		r.data = ensure(r.data, len(vector))
		addScaled(c, vector, r.data)
		r.coef[index] = 0
	}
}

// leading returns the oldest identifier this row still depends on, and how
// many it depends on altogether.
func (d *WindowDecoder) leading(coef []byte) (uint32, int) {
	var pivot uint32
	count := 0
	for esi := d.lo; int32(esi-d.high) < 0; esi++ {
		if coef[esi&d.mask] == 0 {
			continue
		}
		if count == 0 {
			pivot = esi
		}
		count++
	}
	return pivot, count
}

// resize re-indexes the window. Rows are carried across rather than dropped:
// their coefficients are held by identifier, and only the mapping to slots
// changes.
func (d *WindowDecoder) resize(width int) {
	size := roundUpPowerOfTwo(width)
	slots := make([]decoderSlot, size)
	mask := uint32(size - 1)
	if d.started {
		for esi := d.lo; int32(esi-d.high) < 0; esi++ {
			if s := d.slots[esi&d.mask]; s.live && s.esi == esi {
				slots[esi&mask] = s
			}
		}
	}
	for _, r := range d.rows {
		coef := make([]byte, size)
		for esi := d.lo; int32(esi-d.high) < 0; esi++ {
			coef[esi&mask] = r.coef[esi&d.mask]
		}
		r.coef = coef
	}
	d.slots, d.mask = slots, mask
	if d.started {
		// A wider window reaches further back, which is the point of widening it.
		d.lo = d.high - uint32(size)
	}
}

// ensure lengthens a constant term to cover a longer symbol.
//
// Equations of different lengths mix freely, and zero-extending the shorter is
// exact rather than approximate: a repair's length is the longest symbol its
// window held, so every symbol it combined is zero beyond that point, and so
// is their combination.
func ensure(data []byte, length int) []byte {
	if len(data) >= length {
		return data
	}
	return append(data, make([]byte, length-len(data))...)
}

// addScaled accumulates coefficient times in into out, over as much as they
// share. The rest of in is beyond what out claims to cover, and the rest of
// out is beyond where in has any bytes.
func addScaled(coefficient byte, in, out []byte) {
	n := min(len(in), len(out))
	mulSliceXor(coefficient, in[:n], out[:n])
}

func scaleBytes(factor byte, b []byte) {
	if factor == 1 {
		return
	}
	table := &gfMul[factor]
	for i := range b {
		b[i] = table[b[i]]
	}
}

func roundUpPowerOfTwo(n int) int {
	size := 1
	for size < n {
		size <<= 1
	}
	return size
}
