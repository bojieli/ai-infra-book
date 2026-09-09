package conformance

import (
	"bytes"
	"encoding/hex"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/fec"
	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/protocol"
	"github.com/bojieli/queqiao/internal/session"
)

func decodeHex(t *testing.T, name, s string) []byte {
	t.Helper()
	raw, err := hex.DecodeString(s)
	if err != nil {
		t.Fatalf("%s: vector hex is malformed: %v", name, err)
	}
	return raw
}

// TestLimitsMatchTheVectors is the check the rest depend on. Every other test
// in this file reads bytes out of the file and hands them to this build; this
// one reads the numbers those bytes were derived from, so a limit that moved
// without the vectors moving fails here rather than as a confusing byte
// mismatch three sections down.
func TestLimitsMatchTheVectors(t *testing.T) {
	got, want := limitVector(), loadVectors(t).Limits
	if got != want {
		t.Fatalf("protocol 1 limits changed.\n build: %+v\nvector: %+v", got, want)
	}
	// The relationship that motivates the payload limit, stated rather than
	// assumed: a receiver that cannot hold the largest legal PACKET cannot
	// carry a maximum-size UDP reply, which is a live failure and not a
	// smaller buffer.
	if uint32(want.MaxPacketPayload) > want.MaxPayload {
		t.Fatalf("payload limit %d cannot carry the largest legal PACKET (%d bytes)", want.MaxPayload, want.MaxPacketPayload)
	}
	if want.MaxPacketPayload != want.MaxDestinationLength+want.MaxUDPDatagram+2 {
		t.Fatalf("the PACKET bound %d is not its own parts", want.MaxPacketPayload)
	}
	// A receiver must be able to admit a full-span repair with newer symbols
	// already behind it, or the widest repair a conforming sender may build is
	// one it can never use.
	if want.MinDecoderWidth < 2*want.MaxRepairWindow {
		t.Fatalf("decoder width %d cannot hold a %d-symbol repair and what follows it", want.MinDecoderWidth, want.MaxRepairWindow)
	}
}

func TestFrameHeaderVectors(t *testing.T) {
	vectors := loadVectors(t)
	if vectors.Protocol != int(protocol.Version) {
		t.Fatalf("vectors describe protocol %d, this build speaks %d", vectors.Protocol, protocol.Version)
	}
	for _, v := range vectors.FrameHeaders.Accept {
		t.Run("accept/"+v.Name, func(t *testing.T) {
			raw := decodeHex(t, v.Name, v.Hex)
			if len(raw) != protocol.HeaderSize {
				t.Fatalf("header is %d bytes, protocol 1 headers are %d", len(raw), protocol.HeaderSize)
			}
			h, err := protocol.DecodeHeader(raw)
			if err != nil {
				t.Fatalf("a header protocol 1 requires was refused: %v", err)
			}
			if int(h.Type) != v.Type || int(h.Flags) != v.Flags || h.FlowID != v.FlowID ||
				h.Sequence != v.Sequence || h.PayloadLen != v.PayloadLen || int(h.Class) != v.Class {
				t.Fatalf("decoded %+v, vector says type=%d flags=%d flow=%d seq=%d len=%d class=%d",
					h, v.Type, v.Flags, v.FlowID, v.Sequence, v.PayloadLen, v.Class)
			}
			if got := hex.EncodeToString(h.SessionID[:]); got != v.SessionID {
				t.Fatalf("session id %s, vector says %s", got, v.SessionID)
			}
			// Re-encoding must reproduce the vector exactly: a header with one
			// canonical spelling is what lets a receiver reject the others.
			out := make([]byte, protocol.HeaderSize)
			if err := h.Encode(out); err != nil {
				t.Fatalf("this build cannot re-encode a header it accepted: %v", err)
			}
			if !bytes.Equal(out, raw) {
				t.Fatalf("re-encoded %x, vector is %x", out, raw)
			}
		})
	}
	for _, v := range vectors.FrameHeaders.Reject {
		t.Run("reject/"+v.Name, func(t *testing.T) {
			if _, err := protocol.DecodeHeader(decodeHex(t, v.Name, v.Hex)); err == nil {
				t.Fatalf("accepted a header protocol 1 forbids (%s)", v.Why)
			}
		})
	}
}

func TestAckRangeVectors(t *testing.T) {
	for _, v := range loadVectors(t).AckRanges {
		t.Run(v.Name, func(t *testing.T) {
			payload := decodeHex(t, v.Name, v.Hex)
			got, err := protocol.DecodeAckRanges(payload, v.Cumulative)
			if v.Reject {
				if err == nil {
					t.Fatalf("accepted an acknowledgement protocol 1 forbids (%s)", v.Why)
				}
				return
			}
			if err != nil {
				t.Fatalf("refused a legal acknowledgement: %v", err)
			}
			if len(got) != len(v.Ranges) {
				t.Fatalf("decoded %d ranges, vector has %d", len(got), len(v.Ranges))
			}
			for i := range got {
				if got[i] != v.Ranges[i] {
					t.Fatalf("range %d decoded %v, vector says %v", i, got[i], v.Ranges[i])
				}
			}
			if len(v.Ranges) == 0 {
				return
			}
			out, err := protocol.EncodeAckRanges(v.Ranges)
			if err != nil {
				t.Fatalf("this build cannot re-encode ranges it accepted: %v", err)
			}
			if !bytes.Equal(out, payload) {
				t.Fatalf("re-encoded %x, vector is %x", out, payload)
			}
		})
	}
}

func TestDestinationVectors(t *testing.T) {
	for _, v := range loadVectors(t).Destinations {
		t.Run(v.Name, func(t *testing.T) {
			encoded, err := session.EncodeDestination(v.Input)
			if v.Reject {
				if err == nil {
					t.Fatalf("accepted a destination protocol 1 forbids (%s)", v.Why)
				}
				return
			}
			if err != nil {
				t.Fatalf("refused a legal destination: %v", err)
			}
			if got := hex.EncodeToString(encoded); got != v.Hex {
				t.Fatalf("encoded %s, vector is %s", got, v.Hex)
			}
			canonical, err := session.DecodeDestination(encoded)
			if err != nil {
				t.Fatalf("this build refused its own encoding: %v", err)
			}
			if canonical != v.Canonical {
				t.Fatalf("canonicalized to %q, vector says %q", canonical, v.Canonical)
			}
			// Canonicalization has to be idempotent, or a destination has as
			// many spellings as the number of times it is passed along.
			again, err := session.EncodeDestination(canonical)
			if err != nil || !bytes.Equal(again, encoded) {
				t.Fatalf("re-encoding the canonical form gave %x, %v", again, err)
			}
		})
	}
}

func TestUDPVectors(t *testing.T) {
	v := loadVectors(t).UDP

	if got := hex.EncodeToString(session.UDPAssociationMarker); got != v.AssociationMarkerHex {
		t.Fatalf("association marker %s, vector is %s", got, v.AssociationMarkerHex)
	}

	for _, o := range v.ResumeOpens {
		t.Run("resume-open/"+o.Name, func(t *testing.T) {
			payload := decodeHex(t, o.Name, o.Hex)
			token, ok := session.DecodeUDPResumeOpen(payload)
			if o.Reject {
				if ok {
					t.Fatalf("accepted a resume open protocol 1 forbids (%s)", o.Why)
				}
				return
			}
			if !ok {
				t.Fatal("refused a legal resume open")
			}
			if got := hex.EncodeToString(token); got != o.Canonical {
				t.Fatalf("token %s, vector says %q", got, o.Canonical)
			}
		})
	}

	for _, g := range v.ResumeGrants {
		t.Run("resume-grant/"+g.Name, func(t *testing.T) {
			payload := decodeHex(t, g.Name, g.Hex)
			_, token, ok := session.DecodeUDPResumeGrant(payload)
			if g.Reject {
				if ok {
					t.Fatalf("accepted a resume grant protocol 1 forbids (%s)", g.Why)
				}
				return
			}
			if !ok {
				t.Fatal("refused a legal resume grant")
			}
			if got := hex.EncodeToString(token[:]); got != g.Canonical {
				t.Fatalf("token %s, vector says %s", got, g.Canonical)
			}
		})
	}

	for _, p := range v.Packets {
		t.Run("packet/"+p.Name, func(t *testing.T) {
			want := decodeHex(t, p.Name, p.Hex)
			payload := decodeHex(t, p.Name, p.PayloadHex)
			encoded, err := session.EncodeUDPPacket(p.Destination, payload)
			if err != nil {
				t.Fatalf("refused a legal packet: %v", err)
			}
			if !bytes.Equal(encoded, want) {
				t.Fatalf("encoded %x, vector is %x", encoded, want)
			}
			destination, datagram, err := session.DecodeUDPPacket(want)
			if err != nil {
				t.Fatalf("refused the vector's own packet: %v", err)
			}
			if destination != p.Destination || !bytes.Equal(datagram, payload) {
				t.Fatalf("decoded %q/%x, vector says %q/%x", destination, datagram, p.Destination, payload)
			}
		})
	}

	for _, r := range v.RejectPackets {
		t.Run("reject-packet/"+r.Name, func(t *testing.T) {
			if _, _, err := session.DecodeUDPPacket(decodeHex(t, r.Name, r.Hex)); err == nil {
				t.Fatalf("accepted a packet protocol 1 forbids (%s)", r.Why)
			}
		})
	}
}

func TestResetVectors(t *testing.T) {
	for _, v := range loadVectors(t).ResetPayloads {
		t.Run(v.Name, func(t *testing.T) {
			want := decodeHex(t, v.Name, v.Hex)
			got := session.ResetPayload(session.ResetCode(v.Code), v.Message)
			if !bytes.Equal(got, want) {
				t.Fatalf("encoded %x, vector is %x", got, want)
			}
			if len(want) == 0 || int(want[0]) != v.Code {
				t.Fatalf("payload does not lead with code %d: %x", v.Code, want)
			}
			if string(want[1:]) != v.Message {
				t.Fatalf("payload message %q, vector says %q", want[1:], v.Message)
			}
		})
	}
}

// TestCoefficientVectors is the reason this package exists. The row is derived
// on both ends and never sent, so an implementation that computes it
// differently is not detectably wrong on the wire: its repairs arrive intact
// and simply fail to solve, which is what a lossy path looks like.
func TestCoefficientVectors(t *testing.T) {
	for _, v := range loadVectors(t).FECCoefficients {
		t.Run(v.Name(), func(t *testing.T) {
			want := decodeHex(t, v.Name(), v.CoefficientsHex)
			got := fec.WindowCoefficients(v.RID, v.Count)
			if !bytes.Equal(got, want) {
				t.Fatalf("repair %d coefficients over %d symbols:\n  build %x\n vector %x", v.RID, v.Count, got, want)
			}
			for i, c := range got {
				if c == 0 {
					t.Fatalf("coefficient %d of repair %d is zero, which drops the symbol it should cover", i, v.RID)
				}
			}
		})
	}
}

// TestRepairVectors checks the whole encode step, then closes the loop by
// erasing a symbol and requiring the repair to bring it back. The second half
// is what catches a field arithmetic error that the coefficient row alone
// would not.
func TestRepairVectors(t *testing.T) {
	for _, v := range loadVectors(t).FECRepairs {
		t.Run(v.Name, func(t *testing.T) {
			symbols := make([][]byte, 0, len(v.SymbolsHex))
			for _, s := range v.SymbolsHex {
				symbols = append(symbols, decodeHex(t, v.Name, s))
			}
			encoder := fec.NewWindowEncoder(len(symbols))
			esis := make([]uint32, 0, len(symbols))
			for _, s := range symbols {
				esis = append(esis, encoder.Add(s))
			}
			repair, ok := encoder.Repair(v.RID, v.Count)
			if !ok {
				t.Fatal("this build produced no repair where the vector has one")
			}
			if repair.Count != v.Count || repair.First != v.First {
				t.Fatalf("repair spans [%d,+%d), vector says [%d,+%d)", repair.First, repair.Count, v.First, v.Count)
			}
			if got := hex.EncodeToString(repair.Vector); got != v.VectorHex {
				t.Fatalf("repair vector:\n  build %s\n vector %s", got, v.VectorHex)
			}

			// Erase the first symbol the repair covers and require it back.
			erased := v.First
			decoder := fec.NewWindowDecoder()
			for i, esi := range esis {
				if esi == erased {
					continue
				}
				decoder.Source(esi, symbols[i])
			}
			delivery := decoder.Repair(fec.RepairSymbol{
				RID: v.RID, First: v.First, Count: v.Count,
				Vector: decodeHex(t, v.Name, v.VectorHex),
			})
			var recovered []byte
			for _, r := range delivery.Recovered {
				if r.ESI == erased {
					recovered = r.Vector
				}
			}
			if recovered == nil {
				t.Fatalf("the repair did not recover the symbol it covers; this is what a coefficient disagreement looks like from the outside")
			}
			want := symbols[indexOfESI(t, esis, erased)]
			if len(recovered) < len(want) || !bytes.Equal(recovered[:len(want)], want) {
				t.Fatalf("recovered %x, want %x", recovered, want)
			}
			// A repair is as wide as the widest symbol it covers; shorter ones
			// come back zero-extended rather than truncated.
			for _, b := range recovered[len(want):] {
				if b != 0 {
					t.Fatalf("recovered %x has non-zero padding past the %d-byte symbol", recovered, len(want))
				}
			}
		})
	}
}

func indexOfESI(t *testing.T, esis []uint32, esi uint32) int {
	t.Helper()
	for i, e := range esis {
		if e == esi {
			return i
		}
	}
	t.Fatalf("the vector's repair covers symbol %d, which it does not contain", esi)
	return -1
}

func TestInvitationVector(t *testing.T) {
	v := loadVectors(t).Invitation
	at, err := time.Parse(time.RFC3339, v.ParsedAt)
	if err != nil {
		t.Fatalf("vector has an unparseable validation instant: %v", err)
	}
	got, err := identity.ParseInvitation(v.URI, at)
	if err != nil {
		t.Fatalf("refused the vector's enrollment URI: %v", err)
	}
	want := identity.Invitation{
		Version: v.Version, ProviderName: v.ProviderName, ProviderID: v.ProviderID,
		Endpoint: v.Endpoint, GatewayID: v.GatewayID, RootPin: v.RootPin,
		Token: v.Token, ExpiresAt: v.ExpiresAt,
	}
	if got != want {
		t.Fatalf("parsed %+v, vector says %+v", got, want)
	}
	// An invitation is a bearer credential with a deadline, so the deadline is
	// part of the format rather than a policy the parser may skip.
	expires, err := time.Parse(time.RFC3339, v.ExpiresAt)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := identity.ParseInvitation(v.URI, expires); err == nil {
		t.Fatal("accepted an invitation at its own expiry")
	}
}
