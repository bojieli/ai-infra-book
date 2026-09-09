package protocol

import (
	"bytes"
	"encoding/binary"
	"errors"
	"io"
	"testing"
)

func TestFirstPublicWireVersion(t *testing.T) {
	if Version != 1 {
		t.Fatalf("wire version = %d, want first public version 1", Version)
	}
}

type shortWriter struct {
	max int
	b   bytes.Buffer
}

func (w *shortWriter) Write(p []byte) (int, error) {
	if len(p) > w.max {
		p = p[:w.max]
	}
	return w.b.Write(p)
}

type zeroWriter struct{}

func (zeroWriter) Write([]byte) (int, error) { return 0, nil }

func TestFrameRoundTrip(t *testing.T) {
	var sid [16]byte
	for i := range sid {
		sid[i] = byte(i + 1)
	}
	want := Frame{Header: Header{Version: Version, Type: TypeData, SessionID: sid, FlowID: 7, Sequence: 4096, Class: ClassBulk}, Payload: []byte("payload")}
	want.Header.PayloadLen = uint32(len(want.Payload))
	var b bytes.Buffer
	if err := WriteFrame(&b, want); err != nil {
		t.Fatal(err)
	}
	got, err := ReadFrame(&b)
	if err != nil {
		t.Fatal(err)
	}
	if got.Header != want.Header || !bytes.Equal(got.Payload, want.Payload) {
		t.Fatalf("got %#v, want %#v", got, want)
	}
}

func TestWriteFrameHandlesShortWrites(t *testing.T) {
	var sid [16]byte
	f := Frame{Header: Header{Version: Version, Type: TypeData, SessionID: sid, FlowID: 7, Sequence: 3, Class: ClassBulk}, Payload: []byte("short writes are valid")}
	var w shortWriter
	w.max = 3
	if err := WriteFrame(&w, f); err != nil {
		t.Fatalf("WriteFrame: %v", err)
	}
	got, err := ReadFrame(bytes.NewReader(w.b.Bytes()))
	if err != nil {
		t.Fatalf("ReadFrame: %v", err)
	}
	if !bytes.Equal(got.Payload, f.Payload) || got.Header.Sequence != f.Header.Sequence {
		t.Fatalf("round trip mismatch: %#v", got)
	}
}

func TestWriteFrameRejectsZeroProgressWriter(t *testing.T) {
	var sid [16]byte
	f := Frame{Header: Header{Version: Version, Type: TypeClose, SessionID: sid, Class: ClassNew}}
	if err := WriteFrame(zeroWriter{}, f); !errors.Is(err, io.ErrShortWrite) {
		t.Fatalf("expected io.ErrShortWrite, got %v", err)
	}
}

func TestDecodeRejectsOversizedPayloadBeforeAllocation(t *testing.T) {
	var raw [HeaderSize]byte
	raw[0], raw[1], raw[2], raw[3] = Magic0, Magic1, Version, byte(TypeData)
	raw[38], raw[39], raw[40], raw[41] = 0x7f, 0xff, 0xff, 0xff
	if _, err := DecodeHeader(raw[:]); err == nil {
		t.Fatal("expected oversized payload error")
	}
}

// The payload limit is a property of protocol 1 rather than of a deployment,
// so the boundary itself is part of the contract: exactly MaxPayload must be
// accepted by every receiver, and one byte more must be refused by every
// receiver. A build that moved either side of this line would be unable to
// discover the disagreement, because version 1 negotiates nothing.
func TestPayloadLimitBoundaryIsFixedByTheProtocol(t *testing.T) {
	if MaxPayload != 128*1024 {
		t.Fatalf("protocol 1 payload limit changed to %d; this is a wire break", MaxPayload)
	}
	for _, tc := range []struct {
		name   string
		length uint32
		accept bool
	}{
		{"at the limit", MaxPayload, true},
		{"one byte over", MaxPayload + 1, false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			var raw [HeaderSize]byte
			raw[0], raw[1], raw[2], raw[3] = Magic0, Magic1, Version, byte(TypeData)
			binary.BigEndian.PutUint64(raw[22:30], 1)
			binary.BigEndian.PutUint32(raw[38:42], tc.length)
			_, err := DecodeHeader(raw[:])
			if tc.accept && err != nil {
				t.Fatalf("receiver refused a legal %d-byte payload: %v", tc.length, err)
			}
			if !tc.accept && err == nil {
				t.Fatalf("receiver accepted an illegal %d-byte payload", tc.length)
			}
		})
	}
}

// The limit exists to cover the largest frame the protocol can require, which
// is a PACKET carrying a maximum UDP datagram to a maximum-length destination.
// A limit below that bound is not a smaller buffer, it is an inability to
// deliver legal traffic, and that is exactly the failure a configurable limit
// produced on the mobile profiles.
func TestPayloadLimitCoversTheLargestLegalFrame(t *testing.T) {
	// The PACKET payload is a two-byte destination length, the destination,
	// then the datagram. internal/session owns the encoding; these numbers are
	// restated rather than imported because the payload limit has to be a
	// property of the envelope, not of whatever the session layer happens to
	// put in it. internal/conformance checks the two against each other.
	const (
		destinationLengthPrefix = 2
		maxDestination          = 255
		maxUDPDatagram          = 65507
		largestRequired         = destinationLengthPrefix + maxDestination + maxUDPDatagram
	)
	if MaxPayload < largestRequired {
		t.Fatalf("payload limit %d cannot carry the largest legal PACKET (%d bytes)", MaxPayload, largestRequired)
	}
}

func TestDecodeRejectsReservedBits(t *testing.T) {
	var raw [HeaderSize]byte
	raw[0], raw[1], raw[2], raw[3] = Magic0, Magic1, Version, byte(TypeClose)
	raw[43] = 1
	if _, err := DecodeHeader(raw[:]); err == nil {
		t.Fatal("expected reserved-bit error")
	}
}

func TestDecodeRejectsUnknownFlags(t *testing.T) {
	var raw [HeaderSize]byte
	h := Header{Version: Version, Type: TypeData, Flags: 1 << 15, FlowID: 1, Class: ClassNew}
	if err := h.Encode(raw[:]); err == nil {
		t.Fatal("Encode unexpectedly accepted unknown flags")
	}
	// Exercise the decoder independently of Encode's validation.
	raw[0], raw[1], raw[2], raw[3] = Magic0, Magic1, Version, byte(TypeData)
	binary.BigEndian.PutUint16(raw[4:6], 1<<15)
	binary.BigEndian.PutUint64(raw[22:30], 1)
	if _, err := DecodeHeader(raw[:]); err == nil {
		t.Fatal("DecodeHeader accepted unknown flags")
	}
}

func TestReserveControlFlagIsScopedToOpenAndJoin(t *testing.T) {
	var raw [HeaderSize]byte
	open := Header{Version: Version, Type: TypeOpen, Flags: FlagReserveControl, FlowID: 1, Class: ClassNew}
	if err := open.Encode(raw[:]); err != nil {
		t.Fatalf("OPEN reserve flag rejected: %v", err)
	}
	join := Header{Version: Version, Type: TypeJoin, Flags: FlagReserveControl, FlowID: 1, Class: ClassBulk}
	if err := join.Encode(raw[:]); err != nil {
		t.Fatalf("JOIN control replacement flag rejected: %v", err)
	}
	data := Header{Version: Version, Type: TypeData, Flags: FlagReserveControl, FlowID: 1, Class: ClassBulk}
	if err := data.Encode(raw[:]); err == nil {
		t.Fatal("DATA unexpectedly accepted reserve-control flag")
	}
}

func TestAckRangesRoundTrip(t *testing.T) {
	ranges := [][2]uint64{{100, 200}, {300, 400}}
	payload, err := EncodeAckRanges(ranges)
	if err != nil {
		t.Fatal(err)
	}
	decoded, err := DecodeAckRanges(payload, 50)
	if err != nil {
		t.Fatal(err)
	}
	if len(decoded) != len(ranges) || decoded[0] != ranges[0] || decoded[1] != ranges[1] {
		t.Fatalf("decoded %v, want %v", decoded, ranges)
	}
}

// A peer that reports overlapping, unordered, empty, or below-cumulative
// ranges is either broken or trying to make the sender release bytes it must
// keep, which would turn a lane failure into silent corruption.
func TestAckRangesRejectMalformedInput(t *testing.T) {
	valid, err := EncodeAckRanges([][2]uint64{{100, 200}})
	if err != nil {
		t.Fatal(err)
	}
	for name, test := range map[string]struct {
		payload    []byte
		cumulative uint64
	}{
		"misaligned":       {append(append([]byte(nil), valid...), 0x01), 0},
		"below cumulative": {valid, 150},
	} {
		if _, err := DecodeAckRanges(test.payload, test.cumulative); err == nil {
			t.Fatalf("%s was accepted", name)
		}
	}
	overlapping, err := EncodeAckRanges([][2]uint64{{100, 200}, {150, 300}})
	if err != nil {
		t.Fatal(err)
	}
	if _, err := DecodeAckRanges(overlapping, 0); err == nil {
		t.Fatal("overlapping ranges were accepted")
	}
	unordered, err := EncodeAckRanges([][2]uint64{{300, 400}})
	if err != nil {
		t.Fatal(err)
	}
	unordered = append(unordered, make([]byte, AckRangeSize)...)
	if _, err := DecodeAckRanges(unordered, 0); err == nil {
		t.Fatal("an empty trailing range was accepted")
	}
	if _, err := EncodeAckRanges([][2]uint64{{200, 100}}); err == nil {
		t.Fatal("an inverted range was encoded")
	}
	tooMany := make([][2]uint64, MaxAckRanges+1)
	for i := range tooMany {
		tooMany[i] = [2]uint64{uint64(i) * 10, uint64(i)*10 + 5}
	}
	if _, err := EncodeAckRanges(tooMany); err == nil {
		t.Fatal("an unbounded range list was encoded")
	}
}

// The flag is meaningful only on an acknowledgement; allowing it elsewhere
// would let a peer attach an unvalidated payload to any frame type.
func TestAckRangesFlagIsRejectedOnOtherFrameTypes(t *testing.T) {
	var raw [HeaderSize]byte
	header := Header{Version: Version, Type: TypeData, Flags: FlagAckRanges}
	if err := header.Encode(raw[:]); err == nil {
		t.Fatal("the range flag was accepted on a data frame")
	}
	header.Type = TypeAck
	header.Flags = FlagAckRanges | FlagAckDown
	if err := header.Encode(raw[:]); err != nil {
		t.Fatalf("the range flag was rejected on an acknowledgement: %v", err)
	}
}

// A peer speaking a different version must be refused at the first frame.
//
// This is the whole value of the version byte: two builds whose framing agrees
// but whose lower layers do not would otherwise handshake, exchange control
// frames successfully, and lose all their bulk data to a substrate that parses
// it as something else. That failure is invisible from either end -- the
// session simply re-issues forever -- where this one names itself.
func TestAPeerOfAnotherVersionIsRefused(t *testing.T) {
	var raw [HeaderSize]byte
	header := Header{Version: Version, Type: TypeData, Class: ClassBulk}
	if err := header.Encode(raw[:]); err != nil {
		t.Fatal(err)
	}
	if _, err := DecodeHeader(raw[:]); err != nil {
		t.Fatalf("this build refused its own framing: %v", err)
	}
	for _, other := range []byte{Version - 1, Version + 1} {
		raw[2] = other
		_, err := DecodeHeader(raw[:])
		if err == nil {
			t.Fatalf("a frame of version %d was accepted by version %d", other, Version)
		}
		var mismatch UnsupportedVersionError
		if !errors.As(err, &mismatch) {
			t.Fatalf("version %d failed ambiguously: %v", other, err)
		}
		if mismatch.Peer != other || mismatch.Local != Version {
			t.Fatalf("version mismatch = %+v, want peer %d local %d", mismatch, other, Version)
		}
	}
}
