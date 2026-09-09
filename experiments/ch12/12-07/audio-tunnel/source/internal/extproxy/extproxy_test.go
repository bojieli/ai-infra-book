package extproxy

import (
	"encoding/json"
	"strings"
	"testing"
)

func configFor(t *testing.T, kind Kind) (server, client map[string]any) {
	t.Helper()
	serverAny, clientAny, err := buildConfigs(Config{
		Kind: kind, Binary: "sing-box",
		ServerListen: "127.0.0.1:11111", ClientRemote: "127.0.0.1:22222",
		SOCKSListen:     "127.0.0.1:33333",
		CertificatePath: "/tmp/cert.pem", KeyPath: "/tmp/key.pem",
	}.withDefaults())
	if err != nil {
		t.Fatalf("build %s config: %v", kind, err)
	}
	return serverAny.(map[string]any), clientAny.(map[string]any)
}

func firstInbound(t *testing.T, cfg map[string]any) map[string]any {
	t.Helper()
	return cfg["inbounds"].([]any)[0].(map[string]any)
}

func firstOutbound(t *testing.T, cfg map[string]any) map[string]any {
	t.Helper()
	return cfg["outbounds"].([]any)[0].(map[string]any)
}

// The server must bind the address the emulator forwards to, and the client
// must dial the emulator rather than the server. Getting these the wrong way
// round produces a working measurement that never touches the emulated path,
// which is worse than a failure because it looks like a result.
func TestClientDialsTheEmulatorAndServerBindsItsOwnAddress(t *testing.T) {
	for _, kind := range []Kind{TUIC, Hysteria2, VLESSTCP, VLESSWebSocket} {
		t.Run(string(kind), func(t *testing.T) {
			server, client := configFor(t, kind)
			inbound := firstInbound(t, server)
			if inbound["listen"] != "127.0.0.1" || inbound["listen_port"] != 11111 {
				t.Fatalf("server binds %v:%v, want the address the emulator forwards to",
					inbound["listen"], inbound["listen_port"])
			}
			outbound := firstOutbound(t, client)
			if outbound["server"] != "127.0.0.1" || outbound["server_port"] != 22222 {
				t.Fatalf("client dials %v:%v, want the emulator", outbound["server"], outbound["server_port"])
			}
			socks := firstInbound(t, client)
			if socks["type"] != "socks" || socks["listen_port"] != 33333 {
				t.Fatalf("client SOCKS inbound = %v, want the benchmark's address", socks)
			}
		})
	}
}

// The client must trust exactly the server's certificate. A measurement that
// disables verification would also accept a misdirected connection.
func TestClientPinsTheServerCertificateWithoutDisablingVerification(t *testing.T) {
	for _, kind := range []Kind{TUIC, Hysteria2, VLESSTCP, VLESSWebSocket} {
		t.Run(string(kind), func(t *testing.T) {
			server, client := configFor(t, kind)
			clientTLS := firstOutbound(t, client)["tls"].(map[string]any)
			if clientTLS["certificate_path"] != "/tmp/cert.pem" {
				t.Fatalf("client trusts %v, want the server certificate", clientTLS["certificate_path"])
			}
			if insecure, present := clientTLS["insecure"]; present && insecure == true {
				t.Fatal("client disables certificate verification")
			}
			serverTLS := firstInbound(t, server)["tls"].(map[string]any)
			if serverTLS["key_path"] != "/tmp/key.pem" {
				t.Fatalf("server key = %v", serverTLS["key_path"])
			}
			// The client must never be handed the private key.
			encoded, err := json.Marshal(client)
			if err != nil {
				t.Fatal(err)
			}
			if strings.Contains(string(encoded), "key_path") {
				t.Fatalf("client configuration references a private key: %s", encoded)
			}
		})
	}
}

// WebSocket must actually be configured as a transport on both ends, or
// "vless-ws" would silently measure plain VLESS and the comparison between
// them would be meaningless.
func TestWebSocketTransportIsConfiguredOnBothEnds(t *testing.T) {
	server, client := configFor(t, VLESSWebSocket)
	for name, cfg := range map[string]map[string]any{
		"server": firstInbound(t, server), "client": firstOutbound(t, client),
	} {
		transport, present := cfg["transport"].(map[string]any)
		if !present || transport["type"] != "ws" {
			t.Fatalf("%s has no WebSocket transport: %v", name, cfg["transport"])
		}
	}
	plainServer, plainClient := configFor(t, VLESSTCP)
	if _, present := firstInbound(t, plainServer)["transport"]; present {
		t.Fatal("plain VLESS server declares a transport")
	}
	if _, present := firstOutbound(t, plainClient)["transport"]; present {
		t.Fatal("plain VLESS client declares a transport")
	}
}

// Whether a transport runs over UDP decides which emulator can carry it, and
// a wrong answer would route a TCP transport through the packet relay.
func TestTransportClassification(t *testing.T) {
	for kind, want := range map[Kind]string{
		TUIC: "udp", Hysteria2: "udp", VLESSTCP: "tcp", VLESSWebSocket: "tcp",
	} {
		if got := kind.Transport(); got != want {
			t.Fatalf("%s transport = %q, want %q", kind, got, want)
		}
	}
}

func TestUnsupportedKindIsRejected(t *testing.T) {
	if _, _, err := buildConfigs(Config{Kind: "nonexistent"}.withDefaults()); err == nil {
		t.Fatal("an unknown transport was configured")
	}
}

func TestInvalidAddressesAreRejected(t *testing.T) {
	_, _, err := buildConfigs(Config{
		Kind: TUIC, ServerListen: "not-an-address", ClientRemote: "127.0.0.1:1",
		SOCKSListen: "127.0.0.1:2",
	}.withDefaults())
	if err == nil {
		t.Fatal("a malformed listen address was accepted")
	}
}

// planConfig is what the harness supplies for a stack: the addresses, the
// certificate, the work directory, a binary per side, and a SOCKS5 target for
// a stack that is a tunnel rather than a proxy.
func planConfig(kind Kind) Config {
	cfg := Config{
		Kind: kind, Binary: "/usr/local/bin/sing-box",
		ServerListen: "127.0.0.1:11111", ClientRemote: "127.0.0.1:22222",
		SOCKSListen:     "127.0.0.1:33333",
		CertificatePath: "/tmp/cert.pem", KeyPath: "/tmp/key.pem",
		WorkDir: "/tmp/bench",
	}
	if kind == KCPTun {
		cfg.Binary, cfg.ServerBinary = "/usr/local/bin/kcptun-client", "/usr/local/bin/kcptun-server"
	}
	if kind.NeedsSOCKSTarget() {
		cfg.SOCKSTarget = "127.0.0.1:44444"
	}
	return cfg
}

func planFor(t *testing.T, kind Kind) Launch {
	t.Helper()
	launch, err := Plan(planConfig(kind))
	if err != nil {
		t.Fatalf("plan %s: %v", kind, err)
	}
	return launch
}

// A stack answers two questions -- what to write and what to run -- and the
// harness owns everything else. That split is the contract a new transport is
// added against, so it is checked here rather than left to be discovered by
// whoever adds the next one.
func TestEveryRegisteredStackPlansBothSides(t *testing.T) {
	kinds := Kinds()
	if len(kinds) == 0 {
		t.Fatal("no stacks are registered")
	}
	for _, kind := range kinds {
		t.Run(string(kind), func(t *testing.T) {
			if transport := kind.Transport(); transport != "udp" && transport != "tcp" {
				t.Fatalf("transport = %q, want udp or tcp", transport)
			}
			if kind.Implementation() == "" {
				t.Fatal("no implementation is named, so a caller cannot be told what to install")
			}
			cfg := planConfig(kind)
			launch := planFor(t, kind)
			wantServer := cfg.ServerBinary
			if wantServer == "" {
				wantServer = cfg.Binary
			}
			if launch.ServerBinary != wantServer || launch.ClientBinary != cfg.Binary {
				t.Fatalf("binaries = %q and %q, want %q and %q",
					launch.ServerBinary, launch.ClientBinary, wantServer, cfg.Binary)
			}
			if len(launch.ServerArgs) == 0 || len(launch.ClientArgs) == 0 {
				t.Fatalf("launch = %+v, want arguments for both sides", launch)
			}
			// Every file a side is told to read must be one the plan also
			// writes, or the process starts against nothing.
			for _, args := range [][]string{launch.ServerArgs, launch.ClientArgs} {
				for _, arg := range args {
					if !strings.HasPrefix(arg, "/tmp/bench/") {
						continue
					}
					if _, ok := launch.Files[arg]; !ok {
						t.Fatalf("%q is passed to a process but never written: %v", arg, launch.Files)
					}
				}
			}
		})
	}
}

// The two errors a contributor meets first must say what is wrong.
func TestPlanRejectsAnUnknownStackAndAMissingBinary(t *testing.T) {
	if _, err := Plan(Config{Kind: "kcptun", Binary: "/bin/true", WorkDir: "/tmp"}); err == nil {
		t.Fatal("an unregistered stack was planned")
	} else if !strings.Contains(err.Error(), "kcptun") {
		t.Fatalf("error = %v, want the stack named", err)
	}
	if _, err := Plan(Config{Kind: TUIC, WorkDir: "/tmp"}); err == nil {
		t.Fatal("a stack was planned with no binary")
	} else if !strings.Contains(err.Error(), "sing-box") {
		t.Fatalf("error = %v, want the implementation named", err)
	}
}

// Kinds is what a caller lists stacks from, so its order must not depend on
// map iteration.
func TestKindsIsStablyOrdered(t *testing.T) {
	first := Kinds()
	for i := 0; i < 10; i++ {
		got := Kinds()
		if len(got) != len(first) {
			t.Fatalf("Kinds() length changed: %v then %v", first, got)
		}
		for j := range got {
			if got[j] != first[j] {
				t.Fatalf("Kinds() order changed: %v then %v", first, got)
			}
		}
	}
}
