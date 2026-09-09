package conformance

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// TestTheSpecificationStatesTheLimitsThisBuildEnforces exists because two of
// the holes this package was written to close were spec-implementation drift
// rather than bugs: docs/PROTOCOL.md described a payload limit no build used,
// and left the repair window to "sender policy" while the receiver enforced
// bounds of its own.
//
// A prose document cannot be checked for meaning, but it can be checked for
// the numbers it is supposed to contain. This is coarse on purpose. It does
// not verify that the specification says the right thing about each value; it
// verifies that a value cannot be changed in Go without the document that
// makes it normative failing to mention it.
func TestTheSpecificationStatesTheLimitsThisBuildEnforces(t *testing.T) {
	path := filepath.Join("..", "..", "docs", "PROTOCOL.md")
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read the wire specification: %v", err)
	}
	spec := string(raw)
	limits := limitVector()

	for _, tc := range []struct {
		what  string
		value string
	}{
		{"header size", fmt.Sprint(limits.HeaderSize)},
		{"payload limit", fmt.Sprint(limits.MaxPayload)},
		{"ack range limit", fmt.Sprint(limits.MaxAckRanges)},
		{"destination length limit", fmt.Sprint(limits.MaxDestinationLength)},
		{"largest legal PACKET payload", fmt.Sprint(limits.MaxPacketPayload)},
		{"repair span limit", fmt.Sprint(limits.MaxRepairWindow)},
		{"minimum decoder width", fmt.Sprint(limits.MinDecoderWidth)},
		{"probe payload limit", fmt.Sprint(limits.MaxProbePayload)},
		{"probe frame limit", fmt.Sprint(limits.MaxProbeFrames)},
		{"probe byte limit", fmt.Sprint(limits.MaxProbeBytes)},
		{"data ALPN", limits.DataALPN},
		{"enrollment ALPN", limits.EnrollALPN},
		{"renewal ALPN", limits.RenewALPN},
	} {
		if !strings.Contains(spec, tc.value) {
			t.Errorf("docs/PROTOCOL.md does not mention the %s (%s) this build enforces", tc.what, tc.value)
		}
	}

	// The vectors are only normative if the specification says they are.
	if !strings.Contains(spec, "testdata/protocol1/vectors.json") {
		t.Error("docs/PROTOCOL.md does not point at the conformance vectors")
	}

	// The configurable payload limit is gone from the build. A document that
	// still offered it would be describing software that no longer exists,
	// which is the failure mode this whole package is about.
	for _, forbidden := range []string{"MAY configure a smaller limit", "max-payload"} {
		if strings.Contains(spec, forbidden) {
			t.Errorf("docs/PROTOCOL.md still describes %q, which version 1 does not have", forbidden)
		}
	}
}
