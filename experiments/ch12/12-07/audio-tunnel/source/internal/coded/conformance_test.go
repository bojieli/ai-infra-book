package coded

import (
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/bojieli/queqiao/internal/conformance"
	"github.com/bojieli/queqiao/internal/fec"
)

// TestCodedDatagramVectors replays the committed protocol-1 datagram vectors
// against the parser that faces the wire.
//
// It lives in this package rather than in internal/conformance because the
// only thing worth testing here is the receive path itself, which is not
// exported: a vector checked against a reimplementation of the parser proves
// that the reimplementation is right.
func TestCodedDatagramVectors(t *testing.T) {
	raw, err := os.ReadFile(filepath.Join("..", "..", "testdata", "protocol1", "vectors.json"))
	if err != nil {
		t.Fatalf("read protocol-1 vectors: %v", err)
	}
	var file conformance.File
	if err := json.Unmarshal(raw, &file); err != nil {
		t.Fatalf("parse protocol-1 vectors: %v", err)
	}
	if file.Limits.MaxRepairWindow != fec.MaxRepairWindow {
		t.Fatalf("vectors bound a repair at %d symbols, this build at %d", file.Limits.MaxRepairWindow, fec.MaxRepairWindow)
	}

	for _, v := range file.CodedDatagrams {
		t.Run(v.Name, func(t *testing.T) {
			datagram, err := hex.DecodeString(v.Hex)
			if err != nil {
				t.Fatalf("vector hex is malformed: %v", err)
			}
			carrier, _ := newPipes(1, 0)
			path := New(carrier, Config{})
			defer path.Close()

			before := path.Stats().Malformed
			frames := path.onDatagram(datagram)
			after := path.Stats().Malformed

			// A refused datagram delivers nothing upward. Whether it is
			// counted as a peer disagreeing about the wire or simply dropped
			// is this implementation's business; handing its contents to the
			// session above would not be.
			if v.Reject {
				if len(frames) != 0 {
					t.Fatalf("a datagram protocol 1 forbids delivered %d frames (%s)", len(frames), v.Why)
				}
				return
			}
			if after != before {
				t.Fatal("a legal datagram was counted as malformed")
			}
			if len(frames) != len(v.Frames) {
				t.Fatalf("delivered %d frames, vector says %d", len(frames), len(v.Frames))
			}
			for i, f := range frames {
				if got := hex.EncodeToString(f); got != v.Frames[i] {
					t.Fatalf("frame %d delivered %s, vector says %s", i, got, v.Frames[i])
				}
			}
		})
	}
}

// TestARepairPastTheLegalSpanIsRefusedAtTheWire pins the specific bound the
// vectors describe, at the specific place it has to hold: the count is two
// bytes on the wire and so can claim a span of 65535, and the receiver's
// obligation stops at 256.
func TestARepairPastTheLegalSpanIsRefusedAtTheWire(t *testing.T) {
	for _, tc := range []struct {
		name      string
		count     int
		malformed bool
	}{
		{"one symbol", 1, false},
		{"the widest legal span", fec.MaxRepairWindow, false},
		{"one past the widest legal span", fec.MaxRepairWindow + 1, true},
		{"the widest span the field can name", 0xFFFF, true},
		{"no symbols at all", 0, true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			carrier, _ := newPipes(1, 0)
			path := New(carrier, Config{})
			defer path.Close()

			d := make([]byte, repairHeader+4)
			d[4] = kindRepair
			d[13], d[14] = byte(tc.count>>8), byte(tc.count)
			path.onDatagram(d)

			if got := path.Stats().Malformed != 0; got != tc.malformed {
				t.Fatalf("a repair claiming %d symbols was counted malformed = %v, want %v", tc.count, got, tc.malformed)
			}
		})
	}
}
