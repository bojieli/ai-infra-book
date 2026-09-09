package session

import "testing"

func TestDestinationCanonicalization(t *testing.T) {
	for _, tc := range []struct {
		in, want string
	}{
		{"example.com:443", "example.com:443"},
		{"[2001:db8::1]:8443", "[2001:db8::1]:8443"},
	} {
		got, err := EncodeDestination(tc.in)
		if err != nil {
			t.Fatalf("EncodeDestination(%q): %v", tc.in, err)
		}
		if string(got) != tc.want {
			t.Fatalf("got %q, want %q", got, tc.want)
		}
	}
}

func TestDestinationRejectsInvalidInputs(t *testing.T) {
	for _, in := range []string{"", "example.com", "example.com:0", "example.com:65536", "example.com:notaport", "example.com:443/evil"} {
		if _, err := EncodeDestination(in); err == nil {
			t.Errorf("expected rejection for %q", in)
		}
	}
}
