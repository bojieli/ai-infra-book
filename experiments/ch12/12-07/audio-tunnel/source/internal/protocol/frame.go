// Package protocol defines the versioned, bounded queqiao frame envelope.
package protocol

import (
	"encoding/binary"
	"errors"
	"fmt"
	"io"
)

const (
	Magic0 = byte('W')
	Magic1 = byte('O')
	// Version is the framing this build speaks, and the only thing that stops
	// two builds that disagree from appearing to work.
	//
	// Version 1 is the first public wire contract. Earlier development wire
	// numbers were never released. Every connection is authenticated by
	// provider-issued mutual TLS before a frame is accepted, and streams begin
	// directly with OPEN or JOIN.
	Version    = byte(1)
	HeaderSize = 46
	// DataALPN is the application protocol negotiated for the data plane. It
	// carries the wire version because that is what makes the versioning
	// fail-closed: there is no capability exchange to discover a disagreement
	// after the fact, so two builds that speak different framing must fail to
	// negotiate rather than connect and then misunderstand each other.
	DataALPN = "queqiao/1"
	// MaxPayload is the frame payload limit for protocol 1. It is a constant
	// of the wire, not a deployment setting: a receiver MUST accept a payload
	// this large and MUST reject a larger one, in both directions.
	//
	// A configurable receive limit was the alternative, and it does not work
	// without negotiation. Version 1 has no capability exchange, so two peers
	// configured differently are mutually unintelligible in exactly one
	// direction, and the symptom -- a frame the sender considers legal being
	// refused as malformed -- names neither the setting nor the peer that
	// holds it.
	//
	// The value is derived rather than round. The largest frame version 1 can
	// require is a PACKET carrying a maximum UDP datagram to a maximum-length
	// destination: 2 + 255 + 65507 = 65764 bytes. Everything else is smaller
	// by construction (a destination OPEN is at most 255, an ACK at most 256,
	// a PROBE at most 1200), and DATA is chunked by the sender to whatever it
	// chooses below this. 128 KiB clears the PACKET bound with room to spare
	// while staying small enough that a phone can hold one per in-flight
	// frame without a memory profile of its own.
	MaxPayload = 128 * 1024
	// MaxProbePayload, MaxProbeFrames and MaxProbeBytes bound a path-probe
	// exchange. They are wire constants rather than one side's private policy
	// because the exchange is an echo: the receiver returns every frame it
	// accepts, so these limits are the only thing keeping a probe from being
	// an amplifier, and the sender needs the same numbers to tell a short echo
	// that hit the budget from a peer that is not conforming.
	MaxProbePayload = 1200
	MaxProbeFrames  = 128
	MaxProbeBytes   = 128 * 1024
	// FlagFin marks that the sender has reached EOF for one application-byte
	// direction. It is carried on CLOSE with the final logical byte offset, so
	// it remains ordered with respect to preceding DATA frames.
	FlagFin uint16 = 1 << 0
	// FlagAckFinal marks an acknowledgement as final for the flow.
	FlagAckFinal uint16 = 1 << 1
	// FlagAckUp and FlagAckDown identify which byte direction an ACK covers.
	// They are needed because one framed lane carries both directions.
	FlagAckUp   uint16 = 1 << 2
	FlagAckDown uint16 = 1 << 3
	// FlagCloseAbort marks a FIN as a full application-side close rather than
	// a half-close. It lets the peer release a keep-alive destination when the
	// local socket was already closed after consuming its response.
	FlagCloseAbort uint16 = 1 << 4
	// FlagReserveControl asks the peer to reserve a control/rescue role. On
	// OPEN, lane zero begins in that role. On JOIN, the new lane replaces that
	// role after a pooled connection generation has expired.
	FlagReserveControl uint16 = 1 << 5
	// FlagAckRanges is valid only on ACK. The payload carries byte ranges the
	// receiver already holds out of order, beyond the cumulative sequence.
	//
	// A striped flow's sender otherwise learns only the contiguous receive
	// point, which sits behind whatever the slowest lane has not delivered, so
	// its retention window has to cover the whole reorder span. Protocol v1
	// requires both peers to understand it.
	FlagAckRanges uint16 = 1 << 7
	knownFlags           = FlagFin | FlagAckFinal | FlagAckUp | FlagAckDown | FlagCloseAbort | FlagReserveControl | FlagAckRanges
)

type Type byte

const (
	TypeOpen Type = iota + 1
	TypeOpenOK
	// TypeJoin attaches an independently mutually authenticated lane to an
	// existing flow. Its payload is exactly one non-zero big-endian lane ID.
	TypeJoin
	TypeData
	TypeAck
	TypeClose
	TypeReset
	// TypePacket carries one bounded SOCKS UDP datagram. It is intentionally
	// distinct from TypeData: packet payloads preserve datagram boundaries and
	// are not inserted into the byte-stream reassembler.
	TypePacket
	// TypeProbe carries bounded padding used after an uplink change to measure
	// both sending directions before a user's first flow. It is authenticated
	// by TLS, never names or opens a destination, and is echoed one-for-one so
	// it cannot amplify traffic.
	TypeProbe
)

func (t Type) valid() bool { return t >= TypeOpen && t <= TypeProbe }

type Class byte

const (
	ClassNew Class = iota
	ClassInteractive
	ClassBulk
)

type Header struct {
	Version    byte
	Type       Type
	Flags      uint16
	SessionID  [16]byte
	FlowID     uint64
	Sequence   uint64
	PayloadLen uint32
	Class      Class
}

type Frame struct {
	Header  Header
	Payload []byte
}

// UnsupportedVersionError identifies a peer that speaks a different wire
// protocol. Keep this distinct from malformed headers: operators need to know
// that a coordinated client/server upgrade is required, rather than chase a
// network or credential failure.
type UnsupportedVersionError struct {
	Peer  byte
	Local byte
}

func (e UnsupportedVersionError) Error() string {
	return fmt.Sprintf("unsupported wire version %d (this build speaks %d)", e.Peer, e.Local)
}

func reserveControlFlagValid(t Type, flags uint16) bool {
	return flags&FlagReserveControl == 0 || t == TypeOpen || t == TypeJoin
}

func ackRangesFlagValid(t Type, flags uint16) bool {
	return flags&FlagAckRanges == 0 || t == TypeAck
}

// MaxAckRanges bounds one acknowledgement's range list, so a peer cannot make
// the receiver allocate or the sender iterate without limit.
const MaxAckRanges = 16

// AckRangeSize is the encoded width of one range: two big-endian uint64s.
const AckRangeSize = 16

// EncodeAckRanges serializes received byte ranges for an ACK payload.
func EncodeAckRanges(ranges [][2]uint64) ([]byte, error) {
	if len(ranges) > MaxAckRanges {
		return nil, fmt.Errorf("acknowledgement carries %d ranges, limit is %d", len(ranges), MaxAckRanges)
	}
	payload := make([]byte, 0, len(ranges)*AckRangeSize)
	for _, r := range ranges {
		if r[0] >= r[1] {
			return nil, errors.New("acknowledgement range is empty or inverted")
		}
		payload = binary.BigEndian.AppendUint64(payload, r[0])
		payload = binary.BigEndian.AppendUint64(payload, r[1])
	}
	return payload, nil
}

// DecodeAckRanges parses an ACK payload. Ranges must be non-empty, strictly
// increasing, and disjoint: a peer that sends overlapping or unordered ranges
// is either broken or trying to make the sender release bytes it should retain.
func DecodeAckRanges(payload []byte, cumulative uint64) ([][2]uint64, error) {
	if len(payload)%AckRangeSize != 0 {
		return nil, errors.New("acknowledgement range payload is misaligned")
	}
	count := len(payload) / AckRangeSize
	if count > MaxAckRanges {
		return nil, fmt.Errorf("acknowledgement carries %d ranges, limit is %d", count, MaxAckRanges)
	}
	ranges := make([][2]uint64, 0, count)
	previousEnd := cumulative
	for i := range count {
		start := binary.BigEndian.Uint64(payload[i*AckRangeSize:])
		end := binary.BigEndian.Uint64(payload[i*AckRangeSize+8:])
		if start >= end {
			return nil, errors.New("acknowledgement range is empty or inverted")
		}
		if start < previousEnd {
			return nil, errors.New("acknowledgement ranges overlap or are unordered")
		}
		previousEnd = end
		ranges = append(ranges, [2]uint64{start, end})
	}
	return ranges, nil
}

func (h Header) Encode(dst []byte) error {
	if len(dst) < HeaderSize {
		return io.ErrShortBuffer
	}
	if h.Version != Version || !h.Type.valid() || h.Class > ClassBulk || h.Flags&^knownFlags != 0 || !reserveControlFlagValid(h.Type, h.Flags) || !ackRangesFlagValid(h.Type, h.Flags) {
		return errors.New("invalid frame header")
	}
	if h.PayloadLen > MaxPayload {
		return errors.New("payload exceeds the protocol limit")
	}
	dst[0], dst[1], dst[2], dst[3] = Magic0, Magic1, h.Version, byte(h.Type)
	binary.BigEndian.PutUint16(dst[4:6], h.Flags)
	copy(dst[6:22], h.SessionID[:])
	binary.BigEndian.PutUint64(dst[22:30], h.FlowID)
	binary.BigEndian.PutUint64(dst[30:38], h.Sequence)
	binary.BigEndian.PutUint32(dst[38:42], h.PayloadLen)
	dst[42] = byte(h.Class)
	dst[43], dst[44], dst[45] = 0, 0, 0
	return nil
}

// Validate checks a decoded header against the version-1 rules. Keeping this
// separate from Encode makes it possible for callers to validate a decoded
// frame before handing it to a flow state machine.
func (h Header) Validate() error {
	if h.Version != Version || !h.Type.valid() || h.Class > ClassBulk {
		return errors.New("invalid frame header")
	}
	if h.Flags&^knownFlags != 0 || !reserveControlFlagValid(h.Type, h.Flags) || !ackRangesFlagValid(h.Type, h.Flags) {
		return errors.New("unknown frame flags")
	}
	if h.PayloadLen > MaxPayload {
		return fmt.Errorf("payload length %d exceeds the protocol limit %d", h.PayloadLen, MaxPayload)
	}
	return nil
}

func DecodeHeader(src []byte) (Header, error) {
	if len(src) < HeaderSize {
		return Header{}, io.ErrUnexpectedEOF
	}
	if src[0] != Magic0 || src[1] != Magic1 {
		return Header{}, errors.New("invalid frame magic")
	}
	if src[2] != Version {
		return Header{}, UnsupportedVersionError{Peer: src[2], Local: Version}
	}
	h := Header{
		Version: src[2], Type: Type(src[3]), Flags: binary.BigEndian.Uint16(src[4:6]),
		FlowID: binary.BigEndian.Uint64(src[22:30]), Sequence: binary.BigEndian.Uint64(src[30:38]),
		PayloadLen: binary.BigEndian.Uint32(src[38:42]), Class: Class(src[42]),
	}
	copy(h.SessionID[:], src[6:22])
	if err := h.Validate(); err != nil {
		return Header{}, fmt.Errorf("unsupported frame header: %w", err)
	}
	if src[43] != 0 || src[44] != 0 || src[45] != 0 {
		return Header{}, errors.New("non-zero reserved bits")
	}
	return h, nil
}

func ReadFrame(r io.Reader) (Frame, error) {
	var raw [HeaderSize]byte
	if _, err := io.ReadFull(r, raw[:]); err != nil {
		return Frame{}, err
	}
	h, err := DecodeHeader(raw[:])
	if err != nil {
		return Frame{}, err
	}
	payload := make([]byte, h.PayloadLen)
	if _, err := io.ReadFull(r, payload); err != nil {
		return Frame{}, err
	}
	return Frame{Header: h, Payload: payload}, nil
}

// ParseFrame decodes one frame that already sits whole in memory.
//
// A datagram substrate delivers a frame complete or not at all, so there is
// nothing to read incrementally and no reader to hold. Requiring one would
// mean wrapping every arrival in a bytes.Reader for the sake of an interface
// it does not need.
//
// It is an error for the slice to hold anything after the frame: the caller
// framed it, so a trailing byte means the framing disagrees with the parse.
func ParseFrame(b []byte) (Frame, error) {
	if len(b) < HeaderSize {
		return Frame{}, io.ErrUnexpectedEOF
	}
	h, err := DecodeHeader(b[:HeaderSize])
	if err != nil {
		return Frame{}, err
	}
	rest := b[HeaderSize:]
	if uint64(len(rest)) != uint64(h.PayloadLen) {
		return Frame{}, fmt.Errorf("frame payload is %d bytes, header declares %d", len(rest), h.PayloadLen)
	}
	payload := make([]byte, len(rest))
	copy(payload, rest)
	return Frame{Header: h, Payload: payload}, nil
}

// AppendFrame serializes one frame into dst and returns the extended slice.
//
// The header and payload must reach the transport in a single write. When they
// were written separately, a QUIC sender that happened to be idle could
// packetize the 46-byte header into its own datagram, adding roughly one extra
// packet per data frame on the wire; on a lossy path that inflates both the
// byte count and the number of packets exposed to loss.
func AppendFrame(dst []byte, f Frame) ([]byte, error) {
	if uint64(len(f.Payload)) > MaxPayload {
		return dst, errors.New("payload exceeds the protocol limit")
	}
	f.Header.PayloadLen = uint32(len(f.Payload))
	start := len(dst)
	dst = append(dst, make([]byte, HeaderSize)...)
	if err := f.Header.Encode(dst[start:]); err != nil {
		return dst[:start], err
	}
	return append(dst, f.Payload...), nil
}

func WriteFrame(w io.Writer, f Frame) error {
	buf, err := AppendFrame(make([]byte, 0, HeaderSize+len(f.Payload)), f)
	if err != nil {
		return err
	}
	return writeFull(w, buf)
}

// writeFull is intentionally local rather than relying on a particular
// transport. io.Writer is allowed to perform a short successful write, which
// is common for rate-limited or instrumented writers and must not corrupt the
// frame stream.
func writeFull(w io.Writer, p []byte) error {
	for len(p) > 0 {
		n, err := w.Write(p)
		if n > 0 {
			p = p[n:]
		}
		if err != nil {
			return err
		}
		if n == 0 {
			return io.ErrShortWrite
		}
	}
	return nil
}
