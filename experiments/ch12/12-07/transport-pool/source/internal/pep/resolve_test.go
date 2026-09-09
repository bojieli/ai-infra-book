package pep

import (
	"context"
	"net"
	"testing"
)

func TestResolveUDPAddrTakesLiteralAddressesWithoutALookup(t *testing.T) {
	// A numbered endpoint needs no resolver at all, and must not be made to
	// depend on one: this is the path every literal-endpoint provider takes.
	for _, remote := range []string{"203.0.113.7:12540", "[2001:db8::1]:12540"} {
		addr, err := resolveUDPAddr(context.Background(), remote, net.DefaultResolver)
		if err != nil {
			t.Fatalf("%s: %v", remote, err)
		}
		if got := addr.String(); got != remote {
			t.Errorf("resolved %s to %s", remote, got)
		}
	}
}

func TestResolveUDPAddrReportsAMalformedEndpoint(t *testing.T) {
	if _, err := resolveUDPAddr(context.Background(), "no-port-here", net.DefaultResolver); err == nil {
		t.Error("an endpoint without a port must be reported")
	}
}
