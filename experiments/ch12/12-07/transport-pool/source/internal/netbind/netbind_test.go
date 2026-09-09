package netbind

import (
	"strings"
	"testing"
)

func TestValidate(t *testing.T) {
	for _, spec := range []string{"", "auto", "if:en0", "192.0.2.10", "2001:db8::10"} {
		if err := Validate(spec); err != nil {
			t.Errorf("Validate(%q): %v", spec, err)
		}
	}
	for _, spec := range []string{"not-an-address", "if:", "if:   "} {
		if err := Validate(spec); err == nil {
			t.Errorf("Validate(%q) unexpectedly succeeded", spec)
		}
	}
}

func TestResolveLiteral(t *testing.T) {
	got, err := Resolve("192.0.2.10")
	if err != nil {
		t.Fatal(err)
	}
	if got.String() != "192.0.2.10" {
		t.Fatalf("resolved literal = %s", got)
	}
}

func TestIsDynamic(t *testing.T) {
	for _, spec := range []string{"auto", "if:en0"} {
		if !IsDynamic(spec) {
			t.Errorf("IsDynamic(%q) = false", spec)
		}
	}
	for _, spec := range []string{"", "192.0.2.10", "2001:db8::10"} {
		if IsDynamic(spec) {
			t.Errorf("IsDynamic(%q) = true", spec)
		}
	}
}

func TestResolveAutoReportsOperationalState(t *testing.T) {
	// A CI host may have no physical IPv4 interface or more than one. Either
	// result must be bounded and actionable; success must select IPv4.
	got, err := Resolve("auto")
	if err != nil {
		if !strings.Contains(err.Error(), "IPv4") && !strings.Contains(err.Error(), "physical") {
			t.Fatalf("unexpected auto-resolution error: %v", err)
		}
		return
	}
	if !got.Is4() {
		t.Fatalf("auto selected non-IPv4 address %s", got)
	}
}
