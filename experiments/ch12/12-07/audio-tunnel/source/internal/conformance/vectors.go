// Package conformance holds the protocol-1 test vectors and the checks that
// hold this implementation to them.
//
// A wire specification that only exists as prose and as one implementation is
// two specifications that happen to agree today. Some of protocol 1 is not
// recoverable from prose at all: the repair coefficients are generated on both
// ends from a bespoke integer mixer rather than transmitted, so a second
// implementation that reads docs/PROTOCOL.md and gets one shift or one
// multiplier wrong produces a decoder whose equations are simply wrong. That
// failure is silent. Every repair it receives fails to recover anything, the
// symbols time out of the window, and the flow reports erasures -- so the
// implementer sees a lossy path, the operator sees a lossy path, and neither
// sees a coefficient.
//
// The vectors are the fixed point that makes those failures loud. They are a
// committed artifact rather than something regenerated on each run: a test that
// compares an implementation against itself agrees with whatever it does.
// Regenerating them is therefore an explicit act (go test -update) and, for
// anything already published, a wire break that requires a new protocol
// version.
package conformance

import "fmt"

// File is the whole vector document.
type File struct {
	Protocol int    `json:"protocol"`
	Note     string `json:"note"`

	FrameHeaders    FrameHeaderVectors `json:"frame_headers"`
	AckRanges       []AckRangeVector   `json:"ack_ranges"`
	Destinations    []StringVector     `json:"destinations"`
	UDP             UDPVectors         `json:"udp"`
	ResetPayloads   []ResetVector      `json:"reset_payloads"`
	FECCoefficients []CoefficientRow   `json:"fec_coefficients"`
	FECRepairs      []RepairVector     `json:"fec_repairs"`
	CodedDatagrams  []DatagramVector   `json:"coded_datagrams"`
	Invitation      InvitationVector   `json:"invitation"`
	Limits          LimitVector        `json:"limits"`
}

// FrameHeaderVectors separates the headers every implementation must accept
// from the ones every implementation must refuse. The second list is the more
// useful of the two: an implementation that accepts what it should refuse is
// interoperable right up to the moment somebody sends it the refusal case.
type FrameHeaderVectors struct {
	Accept []FrameHeaderVector `json:"accept"`
	Reject []RejectVector      `json:"reject"`
}

// FrameHeaderVector is one 46-byte header and the fields it decodes to.
type FrameHeaderVector struct {
	Name       string `json:"name"`
	Hex        string `json:"hex"`
	Type       int    `json:"type"`
	Flags      int    `json:"flags"`
	SessionID  string `json:"session_id"`
	FlowID     uint64 `json:"flow_id"`
	Sequence   uint64 `json:"sequence"`
	PayloadLen uint32 `json:"payload_len"`
	Class      int    `json:"class"`
}

// RejectVector is input a conforming receiver must refuse. Why is prose for a
// human reading a failure, not a string any implementation has to produce.
type RejectVector struct {
	Name string `json:"name"`
	Hex  string `json:"hex"`
	Why  string `json:"why"`
}

// AckRangeVector is one acknowledgement payload: the cumulative offset it is
// read against, the ranges it carries, and whether it is legal at all.
type AckRangeVector struct {
	Name       string      `json:"name"`
	Hex        string      `json:"hex"`
	Cumulative uint64      `json:"cumulative"`
	Ranges     [][2]uint64 `json:"ranges,omitempty"`
	Reject     bool        `json:"reject,omitempty"`
	Why        string      `json:"why,omitempty"`
}

// StringVector is a text input, what it canonicalizes to, and its encoding.
// A destination that two implementations canonicalize differently is a
// destination they disagree about the identity of.
type StringVector struct {
	Name      string `json:"name"`
	Input     string `json:"input"`
	Canonical string `json:"canonical,omitempty"`
	Hex       string `json:"hex,omitempty"`
	Reject    bool   `json:"reject,omitempty"`
	Why       string `json:"why,omitempty"`
}

// UDPVectors covers the datagram control plane: the markers that distinguish
// an association from a destination, and the PACKET payload layout.
type UDPVectors struct {
	AssociationMarkerHex string         `json:"association_marker_hex"`
	ResumeOpens          []StringVector `json:"resume_opens"`
	ResumeGrants         []StringVector `json:"resume_grants"`
	Packets              []PacketVector `json:"packets"`
	RejectPackets        []RejectVector `json:"reject_packets"`
}

// PacketVector is one PACKET payload: a destination and a datagram.
type PacketVector struct {
	Name        string `json:"name"`
	Destination string `json:"destination"`
	PayloadHex  string `json:"payload_hex"`
	Hex         string `json:"hex"`
}

// ResetVector is one RESET payload: a code and its human-readable reason.
type ResetVector struct {
	Name    string `json:"name"`
	Code    int    `json:"code"`
	Message string `json:"message"`
	Hex     string `json:"hex"`
}

// CoefficientRow is one repair identity and the multipliers it applies to the
// first Count symbols of its window, as hex.
//
// This is the vector a second implementation is most likely to need and least
// likely to derive correctly from prose.
type CoefficientRow struct {
	RID             uint32 `json:"rid"`
	Count           int    `json:"count"`
	CoefficientsHex string `json:"coefficients_hex"`
}

// Name identifies a row in test output. A row has no name of its own in the
// file because its identity is entirely (rid, count).
func (c CoefficientRow) Name() string {
	return fmt.Sprintf("repair %d over %d symbols", c.RID, c.Count)
}

// RepairVector is a complete encode step: source symbols in, one repair out.
// It checks the field arithmetic as well as the coefficients.
type RepairVector struct {
	Name       string   `json:"name"`
	RID        uint32   `json:"rid"`
	SymbolsHex []string `json:"symbols_hex"`
	Count      int      `json:"count"`
	First      uint32   `json:"first"`
	VectorHex  string   `json:"vector_hex"`
}

// DatagramVector is one coded datagram exactly as it appears on the wire, and
// what a receiver must have delivered upward once it has taken it.
//
// Frames is as much of the vector as the bytes are. A symbol carries either a
// run of length-prefixed whole frames or one piece of a fragmented frame, and
// which it is is carried only by the fragment count -- so an implementation
// that reads the two the same way parses every datagram successfully and
// delivers garbage. An empty Frames on an accepted datagram is a claim too:
// a receiver must not hand up a frame it has only part of.
type DatagramVector struct {
	Name   string   `json:"name"`
	Kind   string   `json:"kind"`
	Hex    string   `json:"hex"`
	Frames []string `json:"frames,omitempty"`
	Reject bool     `json:"reject,omitempty"`
	Why    string   `json:"why,omitempty"`
}

// InvitationVector is one enrollment URI and the fields it carries. Every
// value in it is obviously synthetic: the vectors are a public artifact, and a
// vector holding anything that looked like a real credential would be one.
type InvitationVector struct {
	URI          string `json:"uri"`
	Version      int    `json:"version"`
	ProviderName string `json:"provider_name"`
	ProviderID   string `json:"provider_id"`
	Endpoint     string `json:"endpoint"`
	GatewayID    string `json:"gateway_id"`
	RootPin      string `json:"root_pin"`
	Token        string `json:"token"`
	ExpiresAt    string `json:"expires_at"`
	ParsedAt     string `json:"parsed_at"`
}

// LimitVector restates the numbers protocol 1 fixes, so that an implementation
// can check them without reading them out of prose.
type LimitVector struct {
	HeaderSize           int    `json:"header_size"`
	Version              int    `json:"version"`
	MaxPayload           uint32 `json:"max_payload"`
	MaxAckRanges         int    `json:"max_ack_ranges"`
	AckRangeSize         int    `json:"ack_range_size"`
	MaxDestinationLength int    `json:"max_destination_length"`
	MaxUDPDatagram       int    `json:"max_udp_datagram"`
	MaxPacketPayload     int    `json:"max_packet_payload"`
	UDPResumeTokenSize   int    `json:"udp_resume_token_size"`
	MaxRepairWindow      int    `json:"max_repair_window"`
	MinDecoderWidth      int    `json:"min_decoder_width"`
	MaxProbePayload      int    `json:"max_probe_payload"`
	MaxProbeFrames       int    `json:"max_probe_frames"`
	MaxProbeBytes        int    `json:"max_probe_bytes"`
	DataALPN             string `json:"data_alpn"`
	EnrollALPN           string `json:"enroll_alpn"`
	RenewALPN            string `json:"renew_alpn"`
}
