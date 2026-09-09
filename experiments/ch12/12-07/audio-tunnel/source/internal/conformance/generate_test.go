package conformance

import (
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"flag"
	"os"
	"path/filepath"
	"testing"

	"github.com/bojieli/queqiao/internal/fec"
	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/protocol"
	"github.com/bojieli/queqiao/internal/session"
)

var update = flag.Bool("update", false, "rewrite the committed protocol-1 vectors from this build")

// vectorPath is deliberately outside this package. The vectors describe the
// protocol, not this package's tests, and a second implementation should be
// able to find them without reading Go.
func vectorPath() string {
	return filepath.Join("..", "..", "testdata", "protocol1", "vectors.json")
}

func loadVectors(t *testing.T) File {
	t.Helper()
	raw, err := os.ReadFile(vectorPath())
	if err != nil {
		t.Fatalf("read protocol-1 vectors: %v", err)
	}
	var f File
	if err := json.Unmarshal(raw, &f); err != nil {
		t.Fatalf("parse protocol-1 vectors: %v", err)
	}
	return f
}

// TestVectorsAreCurrent regenerates the committed vectors only when asked, and
// otherwise checks that this build still produces them byte for byte.
//
// The asymmetry is the point. Regenerating on every run would make the file a
// mirror of whatever the code does, which agrees with any change including a
// wire break. Failing here means either this build changed the wire, in which
// case the protocol version has to move with it, or the file was edited by
// hand, in which case one of the two is wrong.
func TestVectorsAreCurrent(t *testing.T) {
	encoded, err := json.MarshalIndent(generate(t), "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	encoded = append(encoded, '\n')
	if *update {
		if err := os.WriteFile(vectorPath(), encoded, 0o644); err != nil {
			t.Fatal(err)
		}
		t.Log("protocol-1 vectors rewritten")
		return
	}
	committed, err := os.ReadFile(vectorPath())
	if err != nil {
		t.Fatalf("read protocol-1 vectors: %v", err)
	}
	if string(committed) != string(encoded) {
		t.Fatalf("this build no longer produces the committed protocol-1 vectors.\n"+
			"If the wire genuinely changed, protocol.Version must change with it and the\n"+
			"data ALPN with that. If it did not, this is a regression. Only once one of\n"+
			"those two is true, run:\n    go test ./internal/conformance -update\n"+
			"committed %d bytes, this build %d bytes", len(committed), len(encoded))
	}
}

func generate(t *testing.T) File {
	t.Helper()
	return File{
		Protocol: int(protocol.Version),
		Note: "Frozen conformance vectors for queqiao wire protocol 1. Every credential-shaped " +
			"value here is synthetic. Regenerating this file is a wire change: protocol.Version " +
			"and the data ALPN must move with it.",
		FrameHeaders:    frameHeaderVectors(t),
		AckRanges:       ackRangeVectors(t),
		Destinations:    destinationVectors(t),
		UDP:             udpVectors(t),
		ResetPayloads:   resetVectors(),
		FECCoefficients: coefficientVectors(),
		FECRepairs:      repairVectors(t),
		CodedDatagrams:  datagramVectors(),
		Invitation:      invitationVector(t),
		Limits:          limitVector(),
	}
}

func vectorSession() [16]byte {
	var id [16]byte
	for i := range id {
		id[i] = byte(0x10 + i)
	}
	return id
}

func encodeHeader(t *testing.T, h protocol.Header) string {
	t.Helper()
	raw := make([]byte, protocol.HeaderSize)
	if err := h.Encode(raw); err != nil {
		t.Fatalf("encode header %+v: %v", h, err)
	}
	return hex.EncodeToString(raw)
}

func frameHeaderVectors(t *testing.T) FrameHeaderVectors {
	t.Helper()
	sid := vectorSession()
	accepted := []struct {
		name string
		h    protocol.Header
	}{
		{"open", protocol.Header{Version: protocol.Version, Type: protocol.TypeOpen, SessionID: sid, FlowID: 0x0102030405060708, PayloadLen: 16, Class: protocol.ClassNew}},
		{"open reserving the control lane", protocol.Header{Version: protocol.Version, Type: protocol.TypeOpen, Flags: protocol.FlagReserveControl, SessionID: sid, FlowID: 1, PayloadLen: 16, Class: protocol.ClassNew}},
		{"open ok", protocol.Header{Version: protocol.Version, Type: protocol.TypeOpenOK, SessionID: sid, FlowID: 1, Class: protocol.ClassNew}},
		{"join", protocol.Header{Version: protocol.Version, Type: protocol.TypeJoin, SessionID: sid, FlowID: 1, PayloadLen: 8, Class: protocol.ClassNew}},
		{"interactive data", protocol.Header{Version: protocol.Version, Type: protocol.TypeData, SessionID: sid, FlowID: 1, Sequence: 4096, PayloadLen: 1200, Class: protocol.ClassInteractive}},
		{"bulk data at the payload limit", protocol.Header{Version: protocol.Version, Type: protocol.TypeData, SessionID: sid, FlowID: 1, Sequence: 1 << 40, PayloadLen: protocol.MaxPayload, Class: protocol.ClassBulk}},
		{"cumulative ack upstream", protocol.Header{Version: protocol.Version, Type: protocol.TypeAck, Flags: protocol.FlagAckUp, SessionID: sid, FlowID: 1, Sequence: 8192, Class: protocol.ClassInteractive}},
		{"selective ack downstream", protocol.Header{Version: protocol.Version, Type: protocol.TypeAck, Flags: protocol.FlagAckDown | protocol.FlagAckRanges, SessionID: sid, FlowID: 1, Sequence: 8192, PayloadLen: 32, Class: protocol.ClassInteractive}},
		{"final ack", protocol.Header{Version: protocol.Version, Type: protocol.TypeAck, Flags: protocol.FlagAckUp | protocol.FlagAckFinal, SessionID: sid, FlowID: 1, Sequence: 8192, Class: protocol.ClassInteractive}},
		{"half close", protocol.Header{Version: protocol.Version, Type: protocol.TypeClose, Flags: protocol.FlagFin, SessionID: sid, FlowID: 1, Sequence: 8192, Class: protocol.ClassNew}},
		{"aborting close", protocol.Header{Version: protocol.Version, Type: protocol.TypeClose, Flags: protocol.FlagFin | protocol.FlagCloseAbort, SessionID: sid, FlowID: 1, Sequence: 8192, Class: protocol.ClassNew}},
		{"reset", protocol.Header{Version: protocol.Version, Type: protocol.TypeReset, SessionID: sid, FlowID: 1, PayloadLen: 20, Class: protocol.ClassNew}},
		{"packet", protocol.Header{Version: protocol.Version, Type: protocol.TypePacket, SessionID: sid, FlowID: 1, Sequence: 7, PayloadLen: 64, Class: protocol.ClassInteractive}},
		{"packet at the largest legal size", protocol.Header{Version: protocol.Version, Type: protocol.TypePacket, SessionID: sid, FlowID: 1, Sequence: 8, PayloadLen: session.MaxPacketPayload, Class: protocol.ClassInteractive}},
		{"probe", protocol.Header{Version: protocol.Version, Type: protocol.TypeProbe, SessionID: sid, FlowID: 0, Sequence: 99, PayloadLen: protocol.MaxProbePayload, Class: protocol.ClassNew}},
	}
	out := FrameHeaderVectors{}
	for _, a := range accepted {
		out.Accept = append(out.Accept, FrameHeaderVector{
			Name: a.name, Hex: encodeHeader(t, a.h),
			Type: int(a.h.Type), Flags: int(a.h.Flags),
			SessionID: hex.EncodeToString(a.h.SessionID[:]),
			FlowID:    a.h.FlowID, Sequence: a.h.Sequence,
			PayloadLen: a.h.PayloadLen, Class: int(a.h.Class),
		})
	}

	// The refusals are built by mutating one legal header, so each differs
	// from a header this build accepts in exactly the field under test.
	base := protocol.Header{Version: protocol.Version, Type: protocol.TypeData, SessionID: sid, FlowID: 1, Sequence: 16, PayloadLen: 8, Class: protocol.ClassInteractive}
	mutate := func(f func(raw []byte)) string {
		raw := make([]byte, protocol.HeaderSize)
		if err := base.Encode(raw); err != nil {
			t.Fatal(err)
		}
		f(raw)
		return hex.EncodeToString(raw)
	}
	out.Reject = []RejectVector{
		{"wrong magic", mutate(func(raw []byte) { raw[0] = 'X' }), "the first two bytes are not WO"},
		{"version 0", mutate(func(raw []byte) { raw[2] = 0 }), "a receiver speaks exactly one wire version and refuses every other"},
		{"version 2", mutate(func(raw []byte) { raw[2] = 2 }), "a future version is refused rather than partially understood"},
		{"frame type 0", mutate(func(raw []byte) { raw[3] = 0 }), "types are 1..9; there is no zero type"},
		{"frame type 10", mutate(func(raw []byte) { raw[3] = 10 }), "an unknown type is refused, never ignored"},
		{"class 3", mutate(func(raw []byte) { raw[42] = 3 }), "classes are 0..2"},
		{"reserved flag bit 6", mutate(func(raw []byte) { raw[5] |= 1 << 6 }), "bit 6 is reserved and must be zero"},
		{"reserved flag bit 8", mutate(func(raw []byte) { raw[4] |= 1 << 0 }), "bits 8..15 are reserved and must be zero"},
		{"ack-ranges flag on data", mutate(func(raw []byte) { raw[5] |= byte(protocol.FlagAckRanges) }), "the range flag is valid only on ACK"},
		{"reserve-control flag on data", mutate(func(raw []byte) { raw[5] |= byte(protocol.FlagReserveControl) }), "the reserve flag is valid only on OPEN and JOIN"},
		{"reserved byte 43 set", mutate(func(raw []byte) { raw[43] = 1 }), "the three trailing header bytes are reserved and must be zero"},
		{"reserved byte 44 set", mutate(func(raw []byte) { raw[44] = 1 }), "the three trailing header bytes are reserved and must be zero"},
		{"reserved byte 45 set", mutate(func(raw []byte) { raw[45] = 1 }), "the three trailing header bytes are reserved and must be zero"},
		{"payload one byte over the limit", mutate(func(raw []byte) {
			putUint32(raw[38:], protocol.MaxPayload+1)
		}), "131073 exceeds the fixed 131072-byte payload limit"},
		{"payload at the 32-bit maximum", mutate(func(raw []byte) {
			putUint32(raw[38:], 0xffffffff)
		}), "the length is refused before anything is allocated for it"},
	}
	return out
}

func ackRangeVectors(t *testing.T) []AckRangeVector {
	t.Helper()
	encode := func(ranges [][2]uint64) string {
		payload, err := protocol.EncodeAckRanges(ranges)
		if err != nil {
			t.Fatalf("encode ack ranges %v: %v", ranges, err)
		}
		return hex.EncodeToString(payload)
	}
	full := make([][2]uint64, protocol.MaxAckRanges)
	for i := range full {
		start := uint64(1000 + i*100)
		full[i] = [2]uint64{start, start + 50}
	}
	raw := func(ranges ...[2]uint64) string {
		payload := []byte(nil)
		for _, r := range ranges {
			payload = appendUint64(appendUint64(payload, r[0]), r[1])
		}
		return hex.EncodeToString(payload)
	}
	tooMany := make([][2]uint64, 0, protocol.MaxAckRanges+1)
	for i := 0; i <= protocol.MaxAckRanges; i++ {
		start := uint64(1000 + i*100)
		tooMany = append(tooMany, [2]uint64{start, start + 50})
	}
	return []AckRangeVector{
		{Name: "empty range list", Hex: "", Cumulative: 4096},
		{Name: "one range", Hex: encode([][2]uint64{{5000, 6000}}), Cumulative: 4096, Ranges: [][2]uint64{{5000, 6000}}},
		{Name: "three disjoint ranges", Hex: encode([][2]uint64{{5000, 6000}, {7000, 7500}, {9000, 9001}}), Cumulative: 4096, Ranges: [][2]uint64{{5000, 6000}, {7000, 7500}, {9000, 9001}}},
		{Name: "range list at the limit", Hex: encode(full), Cumulative: 0, Ranges: full},
		{Name: "range starting at the cumulative offset", Hex: encode([][2]uint64{{4096, 4097}}), Cumulative: 4096, Ranges: [][2]uint64{{4096, 4097}}},
		{Name: "misaligned payload", Hex: encode([][2]uint64{{5000, 6000}}) + "ff", Cumulative: 0, Reject: true, Why: "the payload is not a whole number of 16-byte ranges"},
		{Name: "inverted range", Hex: raw([2]uint64{6000, 5000}), Cumulative: 0, Reject: true, Why: "end must be greater than start"},
		{Name: "empty range", Hex: raw([2]uint64{5000, 5000}), Cumulative: 0, Reject: true, Why: "a range must cover at least one byte"},
		{Name: "range behind the cumulative offset", Hex: encode([][2]uint64{{100, 200}}), Cumulative: 4096, Reject: true, Why: "a range below the cumulative point is already implied by it"},
		{Name: "overlapping ranges", Hex: raw([2]uint64{5000, 6000}, [2]uint64{5500, 7000}), Cumulative: 0, Reject: true, Why: "ranges must be disjoint and increasing"},
		{Name: "descending ranges", Hex: raw([2]uint64{7000, 7500}, [2]uint64{5000, 6000}), Cumulative: 0, Reject: true, Why: "ranges must be disjoint and increasing"},
		{Name: "one range past the limit", Hex: raw(tooMany...), Cumulative: 0, Reject: true, Why: "an acknowledgement carries at most 16 ranges"},
	}
}

func destinationVectors(t *testing.T) []StringVector {
	t.Helper()
	encode := func(name, input string) StringVector {
		encoded, err := session.EncodeDestination(input)
		if err != nil {
			t.Fatalf("encode destination %q: %v", input, err)
		}
		canonical, err := session.DecodeDestination(encoded)
		if err != nil {
			t.Fatalf("decode destination %q: %v", input, err)
		}
		return StringVector{Name: name, Input: input, Canonical: canonical, Hex: hex.EncodeToString(encoded)}
	}
	return []StringVector{
		encode("hostname and port", "example.com:443"),
		encode("surrounding whitespace is trimmed", "  example.com:443  "),
		encode("a trailing newline is whitespace and is trimmed", "example.com:443\n"),
		encode("a leading-zero port is respelled", "example.com:00443"),
		encode("ipv4 literal", "203.0.113.7:8080"),
		encode("ipv6 literal keeps its brackets", "[2001:db8::1]:443"),
		encode("ipv6 zone identifier", "[fe80::1%25eth0]:443"),
		{Name: "empty", Input: "", Reject: true, Why: "a destination must name a host and a port"},
		{Name: "no port", Input: "example.com", Reject: true, Why: "the port is not optional"},
		{Name: "empty host", Input: ":443", Reject: true, Why: "a destination must name a host"},
		{Name: "newline inside the host", Input: "exam\nple.com:443", Reject: true, Why: "control characters cannot appear in a destination"},
		{Name: "embedded null", Input: "example.com\x00:443", Reject: true, Why: "control characters cannot appear in a destination"},
		{Name: "space inside the host", Input: "exam ple.com:443", Reject: true, Why: "control characters and spaces cannot appear in a destination"},
		{Name: "port zero", Input: "example.com:0", Reject: true, Why: "port 0 does not name a service"},
		{Name: "port out of range", Input: "example.com:70000", Reject: true, Why: "a port is a 16-bit number"},
		{Name: "non-numeric port", Input: "example.com:https", Reject: true, Why: "the port is a number, not a service name"},
		{Name: "over the length bound", Input: longDestination(), Reject: true, Why: "a destination is at most 255 bytes"},
	}
}

func longDestination() string {
	host := make([]byte, session.MaxDestinationLength)
	for i := range host {
		host[i] = 'a'
	}
	return string(host) + ":443"
}

func udpVectors(t *testing.T) UDPVectors {
	t.Helper()
	token := make([]byte, session.UDPResumeTokenSize)
	for i := range token {
		token[i] = byte(0xa0 + i)
	}
	var grantToken [session.UDPResumeTokenSize]byte
	copy(grantToken[:], token)

	resumeOpen, err := session.EncodeUDPResumeOpen(token)
	if err != nil {
		t.Fatal(err)
	}
	freshOpen, err := session.EncodeUDPResumeOpen(nil)
	if err != nil {
		t.Fatal(err)
	}

	packet := func(name, destination string, payload []byte) PacketVector {
		encoded, err := session.EncodeUDPPacket(destination, payload)
		if err != nil {
			t.Fatalf("encode packet for %q: %v", destination, err)
		}
		return PacketVector{
			Name: name, Destination: destination,
			PayloadHex: hex.EncodeToString(payload), Hex: hex.EncodeToString(encoded),
		}
	}

	return UDPVectors{
		AssociationMarkerHex: hex.EncodeToString(session.UDPAssociationMarker),
		ResumeOpens: []StringVector{
			{Name: "resume with a retained relay", Hex: hex.EncodeToString(resumeOpen), Canonical: hex.EncodeToString(token)},
			{Name: "resume asking for a fresh relay", Hex: hex.EncodeToString(freshOpen)},
			{Name: "resume marker with a short token", Hex: hex.EncodeToString(append(append([]byte(nil), session.UDPResumeMarker...), token[:3]...)), Reject: true, Why: "the token is exactly 0 or 16 bytes"},
			{Name: "resume marker with a long token", Hex: hex.EncodeToString(append(append([]byte(nil), session.UDPResumeMarker...), append(token, 0x00)...)), Reject: true, Why: "the token is exactly 0 or 16 bytes"},
			{Name: "association marker is not a resume marker", Hex: hex.EncodeToString(session.UDPAssociationMarker), Reject: true, Why: "the two markers differ in their last byte and mean different things"},
		},
		ResumeGrants: []StringVector{
			{Name: "granted the relay that was asked for", Hex: hex.EncodeToString(session.EncodeUDPResumeGrant(true, grantToken)), Canonical: hex.EncodeToString(grantToken[:])},
			{Name: "given a fresh relay instead", Hex: hex.EncodeToString(session.EncodeUDPResumeGrant(false, grantToken)), Canonical: hex.EncodeToString(grantToken[:])},
			{Name: "grant byte out of range", Hex: "02" + hex.EncodeToString(grantToken[:]), Reject: true, Why: "the first byte is 0 or 1"},
			{Name: "grant with a short token", Hex: "01" + hex.EncodeToString(grantToken[:8]), Reject: true, Why: "a grant is one byte plus a 16-byte token"},
		},
		Packets: []PacketVector{
			packet("small datagram to a hostname", "example.com:53", []byte{0xde, 0xad, 0xbe, 0xef}),
			packet("datagram to an ipv6 literal", "[2001:db8::1]:443", []byte{0x01, 0x02, 0x03}),
			packet("empty datagram", "203.0.113.7:9", nil),
		},
		RejectPackets: []RejectVector{
			{"truncated header", "00", "a PACKET payload is at least a two-byte destination length plus one byte"},
			{"zero destination length", "0000aabb", "the destination length must be non-zero"},
			{"destination length past the payload", "00ff6161", "the named destination does not fit in the payload"},
			{"destination longer than the bound", hex.EncodeToString(overlongPacketDestination()), "a destination is at most 255 bytes"},
		},
	}
}

func overlongPacketDestination() []byte {
	out := appendUint16(nil, uint16(session.MaxDestinationLength+1))
	for i := 0; i <= session.MaxDestinationLength; i++ {
		out = append(out, 'a')
	}
	return out
}

func resetVectors() []ResetVector {
	codes := []struct {
		name    string
		code    session.ResetCode
		message string
	}{
		{"protocol", session.ResetProtocol, "invalid flow open"},
		{"authentication", session.ResetAuthentication, "device is not authorized"},
		{"destination", session.ResetDestination, "destination unavailable"},
		{"flow limit", session.ResetFlowLimit, "account flow limit reached"},
		{"client limit", session.ResetFlowLimit, "account device limit reached"},
		{"transport", session.ResetTransport, "lane transport failed"},
		{"no message", session.ResetProtocol, ""},
	}
	out := make([]ResetVector, 0, len(codes))
	for _, c := range codes {
		out = append(out, ResetVector{
			Name: c.name, Code: int(c.code), Message: c.message,
			Hex: hex.EncodeToString(session.ResetPayload(c.code, c.message)),
		})
	}
	return out
}

// coefficientVectors is the table a second implementation cannot derive from
// prose without getting every shift, multiplier and modulus exactly right, and
// whose failure mode when it does not is silence.
func coefficientVectors() []CoefficientRow {
	rows := []struct {
		rid   uint32
		count int
	}{
		{0, 16}, {1, 16}, {2, 16}, {7, 32},
		{255, 16}, {256, 16}, {65535, 16},
		{0xdeadbeef, 32}, {0xffffffff, 16},
		{12345, fec.MaxRepairWindow},
	}
	out := make([]CoefficientRow, 0, len(rows))
	for _, r := range rows {
		out = append(out, CoefficientRow{
			RID: r.rid, Count: r.count,
			CoefficientsHex: hex.EncodeToString(fec.WindowCoefficients(r.rid, r.count)),
		})
	}
	return out
}

func repairVectors(t *testing.T) []RepairVector {
	t.Helper()
	build := func(name string, rid uint32, capacity int, symbols [][]byte, count int) RepairVector {
		e := fec.NewWindowEncoder(capacity)
		hexes := make([]string, 0, len(symbols))
		for _, s := range symbols {
			e.Add(s)
			hexes = append(hexes, hex.EncodeToString(s))
		}
		repair, ok := e.Repair(rid, count)
		if !ok {
			t.Fatalf("no repair produced for %q", name)
		}
		return RepairVector{
			Name: name, RID: rid, SymbolsHex: hexes,
			Count: repair.Count, First: repair.First,
			VectorHex: hex.EncodeToString(repair.Vector),
		}
	}
	return []RepairVector{
		build("one symbol", 1, 4, [][]byte{{0x01, 0x02, 0x03, 0x04}}, 1),
		build("four equal-length symbols", 3, 4, [][]byte{
			{0x00, 0x11, 0x22, 0x33}, {0x44, 0x55, 0x66, 0x77},
			{0x88, 0x99, 0xaa, 0xbb}, {0xcc, 0xdd, 0xee, 0xff},
		}, 4),
		// A repair is as long as the longest symbol it covers and the shorter
		// ones are zero-extended. Nothing on the wire says so, so both ends
		// have to agree about it from the specification alone.
		build("ragged symbol lengths", 9, 4, [][]byte{
			{0xa1}, {0xb1, 0xb2, 0xb3, 0xb4, 0xb5}, {0xc1, 0xc2},
		}, 3),
		build("a repair narrower than the window holds", 11, 8, [][]byte{
			{0x10, 0x20}, {0x30, 0x40}, {0x50, 0x60}, {0x70, 0x80},
		}, 2),
		build("a repair at the widest legal span", 13, fec.MaxRepairWindow, spanSymbols(fec.MaxRepairWindow), fec.MaxRepairWindow),
	}
}

// spanSymbols is a deterministic, non-uniform run of source symbols: uniform
// ones would let a decoder with the wrong coefficients still appear to solve.
func spanSymbols(n int) [][]byte {
	out := make([][]byte, n)
	for i := range out {
		out[i] = []byte{byte(i), byte(i * 7), byte(i*31 + 5), byte(255 - i)}
	}
	return out
}

func datagramVectors() []DatagramVector {
	// A symbol is itself framed: payload length, fragment index, fragment
	// count, then the bytes. A count of one means the payload is a run of
	// length-prefixed whole frames; anything more means it is one piece of a
	// single frame, carried raw.
	symbol := func(index, count int, payload []byte) []byte {
		v := appendUint16(nil, uint16(len(payload)))
		v = appendUint16(v, uint16(index))
		v = appendUint16(v, uint16(count))
		return append(v, payload...)
	}
	packed := func(frames ...[]byte) []byte {
		out := []byte(nil)
		for _, f := range frames {
			out = append(appendUint32(out, uint32(len(f))), f...)
		}
		return out
	}
	source := func(seq, esi uint32, vector []byte) string {
		d := appendUint32(nil, seq)
		d = append(d, 0)
		d = appendUint32(d, esi)
		return hex.EncodeToString(append(d, vector...))
	}
	repair := func(seq, rid, first uint32, count uint16, vector []byte) string {
		d := appendUint32(nil, seq)
		d = append(d, 1)
		d = appendUint32(d, rid)
		d = appendUint32(d, first)
		d = appendUint16(d, count)
		return hex.EncodeToString(append(d, vector...))
	}
	hexes := func(frames ...[]byte) []string {
		out := make([]string, 0, len(frames))
		for _, f := range frames {
			out = append(out, hex.EncodeToString(f))
		}
		return out
	}
	one := []byte{0xde, 0xad, 0xbe, 0xef}
	two := []byte{0x01, 0x02}
	return []DatagramVector{
		{Name: "source symbol carrying one whole frame", Kind: "source",
			Hex: source(0, 0, symbol(0, 1, packed(one))), Frames: hexes(one)},
		{Name: "source symbol packing two whole frames", Kind: "source",
			Hex: source(1, 1, symbol(0, 1, packed(one, two))), Frames: hexes(one, two)},
		{Name: "source symbol carrying nothing", Kind: "source",
			Hex: source(2, 2, symbol(0, 1, nil))},
		{Name: "source symbol, second fragment of three", Kind: "source",
			Hex: source(42, 41, symbol(1, 3, []byte{0xaa, 0xbb}))},
		{Name: "source symbol whose frame length runs past the symbol", Kind: "source",
			Hex: source(3, 3, symbol(0, 1, append(appendUint32(nil, 64), one...)))},
		{Name: "repair over sixteen symbols", Kind: "repair", Hex: repair(43, 7, 26, 16, []byte{0x11, 0x22, 0x33, 0x44})},
		{Name: "repair at the widest legal span", Kind: "repair", Hex: repair(44, 8, 0, uint16(fec.MaxRepairWindow), []byte{0x55})},
		{Name: "repair one symbol past the legal span", Kind: "repair", Hex: repair(45, 9, 0, uint16(fec.MaxRepairWindow+1), []byte{0x55}), Reject: true, Why: "a repair covers at most 256 symbols"},
		{Name: "repair covering nothing", Kind: "repair", Hex: repair(46, 10, 0, 0, []byte{0x55}), Reject: true, Why: "a repair covers at least one symbol"},
		{Name: "unknown datagram kind", Kind: "unknown", Hex: hex.EncodeToString(append(appendUint32(nil, 47), 9)), Reject: true, Why: "kinds are 0 and 1; anything else is refused rather than ignored"},
		{Name: "truncated source header", Kind: "source", Hex: hex.EncodeToString(append(appendUint32(nil, 48), 0, 0x00, 0x00)), Reject: true, Why: "the datagram ends inside the source header"},
		{Name: "truncated repair header", Kind: "repair", Hex: repair(49, 11, 0, 4, nil)[:26], Reject: true, Why: "the datagram ends inside the repair header"},
	}
}

// invitationVector is a complete enrollment URI. Every value in it is
// synthetic, and the timestamps are fixed: an invitation is only valid for
// seven days, so a vector that used the wall clock would be either unbuildable
// or unverifiable. ParsedAt is the instant the vector is to be validated at.
func invitationVector(t *testing.T) InvitationVector {
	t.Helper()
	const (
		parsedAt = "2026-01-01T00:00:00Z"
		expires  = "2026-01-05T00:00:00Z"
	)
	zeros := base64.RawURLEncoding.EncodeToString(make([]byte, 32))
	invitation := identity.Invitation{
		Version:      identity.InvitationVersion,
		ProviderName: "Example Provider",
		ProviderID:   "00000000000000000000000000000001",
		Endpoint:     "gateway.example.invalid:8443",
		GatewayID:    "00000000000000000000000000000002",
		RootPin:      zeros,
		Token:        zeros,
		ExpiresAt:    expires,
	}
	// Built here rather than through Invitation.URI, which validates against
	// the wall clock and so cannot produce a frozen vector. The encoding is
	// the same, and the round trip below is what actually holds it to that.
	body, err := json.Marshal(invitation)
	if err != nil {
		t.Fatal(err)
	}
	return InvitationVector{
		URI:          "queqiao://enroll/" + base64.RawURLEncoding.EncodeToString(body),
		Version:      invitation.Version,
		ProviderName: invitation.ProviderName, ProviderID: invitation.ProviderID,
		Endpoint: invitation.Endpoint, GatewayID: invitation.GatewayID,
		RootPin: invitation.RootPin, Token: invitation.Token,
		ExpiresAt: invitation.ExpiresAt, ParsedAt: parsedAt,
	}
}

func limitVector() LimitVector {
	return LimitVector{
		HeaderSize:           protocol.HeaderSize,
		Version:              int(protocol.Version),
		MaxPayload:           protocol.MaxPayload,
		MaxAckRanges:         protocol.MaxAckRanges,
		AckRangeSize:         protocol.AckRangeSize,
		MaxDestinationLength: session.MaxDestinationLength,
		MaxUDPDatagram:       session.MaxUDPDatagram,
		MaxPacketPayload:     session.MaxPacketPayload,
		UDPResumeTokenSize:   session.UDPResumeTokenSize,
		MaxRepairWindow:      fec.MaxRepairWindow,
		MinDecoderWidth:      fec.MinDecoderWidth,
		MaxProbePayload:      protocol.MaxProbePayload,
		MaxProbeFrames:       protocol.MaxProbeFrames,
		MaxProbeBytes:        protocol.MaxProbeBytes,
		DataALPN:             protocol.DataALPN,
		EnrollALPN:           identity.EnrollmentALPN,
		RenewALPN:            identity.RenewalALPN,
	}
}

func putUint32(dst []byte, v uint32) {
	dst[0], dst[1], dst[2], dst[3] = byte(v>>24), byte(v>>16), byte(v>>8), byte(v)
}

func appendUint16(dst []byte, v uint16) []byte { return append(dst, byte(v>>8), byte(v)) }

func appendUint32(dst []byte, v uint32) []byte {
	return append(dst, byte(v>>24), byte(v>>16), byte(v>>8), byte(v))
}

func appendUint64(dst []byte, v uint64) []byte {
	return appendUint32(appendUint32(dst, uint32(v>>32)), uint32(v))
}
