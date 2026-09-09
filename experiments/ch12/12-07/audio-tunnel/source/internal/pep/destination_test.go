package pep

import (
	"context"
	"net"
	"testing"
)

func TestPublicDestinationIP(t *testing.T) {
	for _, test := range []struct {
		ip     string
		public bool
	}{
		{"8.8.8.8", true},
		{"1.1.1.1", true},
		{"127.0.0.1", false},
		{"10.0.0.1", false},
		{"100.64.0.1", false},
		{"169.254.169.254", false},
		{"192.0.2.1", false},
		{"192.88.99.2", false},
		{"2001:4860:4860::8888", true},
		{"::1", false},
		{"64:ff9b::a00:1", false},
		{"64:ff9b:1::a00:1", false},
		{"100::1", false},
		{"100:0:0:1::1", false},
		{"2001:2::1", false},
		{"2001:10::1", false},
		{"2001:db8::1", false},
		{"2002:a00:1::1", false},
		{"3fff::1", false},
		{"5f00::1", false},
	} {
		if got := publicDestinationIP(net.ParseIP(test.ip)); got != test.public {
			t.Errorf("publicDestinationIP(%s) = %v, want %v", test.ip, got, test.public)
		}
	}
}

func TestResolveUDPAddrUsesDestinationPolicy(t *testing.T) {
	addresses, err := (DestinationPolicy{}).ResolveUDPAddr(context.Background(), "8.8.8.8:53")
	if err != nil {
		t.Fatal(err)
	}
	if len(addresses) != 1 || !addresses[0].IP.Equal(net.ParseIP("8.8.8.8")) || addresses[0].Port != 53 {
		t.Fatalf("unexpected addresses %#v", addresses)
	}
	if _, err := (DestinationPolicy{}).ResolveUDPAddr(context.Background(), "127.0.0.1:53"); err == nil {
		t.Fatal("private UDP destination accepted")
	}
	if _, err := (DestinationPolicy{}).ResolveUDPAddr(context.Background(), "[64:ff9b::a00:1]:53"); err == nil {
		t.Fatal("NAT64-encoded private UDP destination accepted")
	}
	addresses, err = (DestinationPolicy{AllowPrivate: true}).ResolveUDPAddr(context.Background(), "127.0.0.1:53")
	if err != nil || len(addresses) != 1 {
		t.Fatalf("private destination with explicit allow failed: %v", err)
	}
}
