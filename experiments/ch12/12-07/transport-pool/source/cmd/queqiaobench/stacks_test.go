package main

import (
	"strings"
	"testing"

	"github.com/bojieli/queqiao/internal/extproxy"
)

// Each stack asks for the implementation it actually needs. Before there was a
// registry every external stack asked for sing-box, which is the wrong thing
// to tell somebody running a transport that ships its own programs.
func TestEachStackAsksForItsOwnImplementation(t *testing.T) {
	opts := options{singBox: "/bin/sing-box", kcptunClient: "/bin/kcptun-client", kcptunServer: "/bin/kcptun-server"}
	for _, test := range []struct {
		kind           extproxy.Kind
		client, server string
	}{
		{kind: extproxy.TUIC, client: "/bin/sing-box"},
		{kind: extproxy.Hysteria2, client: "/bin/sing-box"},
		{kind: extproxy.VLESSTCP, client: "/bin/sing-box"},
		{kind: extproxy.KCPTun, client: "/bin/kcptun-client", server: "/bin/kcptun-server"},
	} {
		t.Run(string(test.kind), func(t *testing.T) {
			client, server, err := externalBinaries(test.kind, opts)
			if err != nil {
				t.Fatal(err)
			}
			if client != test.client || server != test.server {
				t.Fatalf("binaries = %q and %q, want %q and %q", client, server, test.client, test.server)
			}
		})
	}
}

// A missing binary has to name what is missing. "requires --sing-box" for a
// kcptun run sends the operator to install the wrong thing.
func TestAMissingBinaryNamesTheOneItNeeds(t *testing.T) {
	for _, test := range []struct {
		name string
		kind extproxy.Kind
		opts options
		want []string
	}{
		{name: "no sing-box", kind: extproxy.TUIC, want: []string{"sing-box"}},
		{
			name: "no kcptun at all", kind: extproxy.KCPTun,
			want: []string{"--kcptun-client", "--kcptun-server", "one program per side"},
		},
		{
			name: "only the kcptun client", kind: extproxy.KCPTun,
			opts: options{kcptunClient: "/bin/kcptun-client"},
			want: []string{"--kcptun-server"},
		},
		{name: "not a transport", kind: extproxy.Kind("wireguard"), want: []string{"not a transport"}},
	} {
		t.Run(test.name, func(t *testing.T) {
			_, _, err := externalBinaries(test.kind, test.opts)
			if err == nil {
				t.Fatal("a stack was started with no implementation")
			}
			for _, want := range test.want {
				if !strings.Contains(err.Error(), want) {
					t.Fatalf("error %q does not mention %q", err, want)
				}
			}
		})
	}
}

// kcptun is carried by the packet emulator, like the other UDP stacks, and it
// is the first stack that needs a SOCKS5 endpoint of the harness's own.
func TestKCPTunIsAUDPTunnel(t *testing.T) {
	if got := extproxy.KCPTun.Transport(); got != "udp" {
		t.Fatalf("kcptun transport = %q, want udp", got)
	}
	if !extproxy.KCPTun.NeedsSOCKSTarget() {
		t.Fatal("kcptun does not ask the harness for a SOCKS5 target")
	}
	for _, proxy := range []extproxy.Kind{extproxy.TUIC, extproxy.Hysteria2, extproxy.VLESSTCP, extproxy.VLESSWebSocket} {
		if proxy.NeedsSOCKSTarget() {
			t.Fatalf("%s asks for a SOCKS5 target it does not need", proxy)
		}
	}
}
