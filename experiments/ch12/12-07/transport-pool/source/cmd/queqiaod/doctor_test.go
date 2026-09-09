package main

import (
	"context"
	"net"
	"strings"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/profile"
)

// An experimental profile qualified on one path is a different claim from the
// default one, and the difference should not live only in a document that the
// operator installing it may never open.
func TestDoctorSaysWhenAProfileIsExperimental(t *testing.T) {
	dc, err := profile.ByName("dc-long-haul")
	if err != nil {
		t.Fatal(err)
	}
	got := checkProfile(dc)
	if got.Status != "warn" {
		t.Fatalf("an experimental profile reported %q", got.Status)
	}
	for _, want := range []string{"experimental", dc.Precondition, dc.Evidence} {
		if !strings.Contains(got.Detail, want) {
			t.Fatalf("the report omits %q: %s", want, got.Detail)
		}
	}

	supported, err := profile.ByName("wan-shared-bottleneck")
	if err != nil {
		t.Fatal(err)
	}
	if got := checkProfile(supported); got.Status != "pass" {
		t.Fatalf("the supported profile reported %q: %s", got.Status, got.Detail)
	}
}

func TestDoctorReportsAnUnreachableGateway(t *testing.T) {
	// Port 1 on loopback, which nothing listens on and which refuses fast.
	ctx, cancel := context.WithTimeout(t.Context(), 3*time.Second)
	defer cancel()
	var failed bool
	for _, c := range checkReachable(ctx, "127.0.0.1:1") {
		if c.Name == "gateway_tcp" && c.Status == "fail" {
			failed = true
		}
	}
	if !failed {
		t.Fatal("a gateway that refuses the connection was not reported as a failure")
	}
}

func TestDoctorReachesAListeningGateway(t *testing.T) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = ln.Close() }()
	ctx, cancel := context.WithTimeout(t.Context(), 3*time.Second)
	defer cancel()
	for _, c := range checkReachable(ctx, ln.Addr().String()) {
		if c.Name == "gateway_tcp" && c.Status != "pass" {
			t.Fatalf("a listening gateway reported %q: %s", c.Status, c.Detail)
		}
	}
}

// A misspelled profile has to stop the run rather than silently check the
// default one, which is the same rule the client and the installer follow.
func TestDoctorRefusesAnUnknownProfile(t *testing.T) {
	err := runDoctorCommand([]string{"--path-profile", "dc-long-hual"})
	if err == nil {
		t.Fatal("an unknown profile was accepted")
	}
	if !strings.Contains(err.Error(), "dc-long-haul") {
		t.Fatalf("the error does not name the alternatives: %v", err)
	}
}

func TestTrimTrailingNewline(t *testing.T) {
	if got := string(trimTrailingNewline([]byte("0\n"))); got != "0" {
		t.Fatalf("got %q", got)
	}
	if got := string(trimTrailingNewline([]byte("cubic \t\r\n"))); got != "cubic" {
		t.Fatalf("got %q", got)
	}
	if got := string(trimTrailingNewline(nil)); got != "" {
		t.Fatalf("got %q", got)
	}
}
