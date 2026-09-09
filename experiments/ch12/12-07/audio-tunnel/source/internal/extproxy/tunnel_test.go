package extproxy

import (
	"context"
	"encoding/binary"
	"errors"
	"io"
	"net"
	"os"
	"strconv"
	"strings"
	"testing"
	"time"
)

// kcptun is a tunnel: its client listens on a local TCP port and its server
// forwards to one address, and neither speaks SOCKS5. Getting either end of
// that wiring wrong produces a benchmark that measures something other than
// the emulated path, so the plan is checked rather than assumed.
func TestKCPTunTunnelsSOCKSAcrossTheEmulatedPath(t *testing.T) {
	launch := planFor(t, KCPTun)

	client := argMap(t, launch.ClientArgs)
	if client["-l"] != "127.0.0.1:33333" {
		t.Fatalf("client listens on %q, want the benchmark's SOCKS address", client["-l"])
	}
	if client["-r"] != "127.0.0.1:22222" {
		t.Fatalf("client dials %q, want the emulator", client["-r"])
	}
	server := argMap(t, launch.ServerArgs)
	if server["-l"] != "127.0.0.1:11111" {
		t.Fatalf("server binds %q, want the address the emulator forwards to", server["-l"])
	}
	if server["-t"] != "127.0.0.1:44444" {
		t.Fatalf("server forwards to %q, want the harness SOCKS5 target", server["-t"])
	}
	if launch.ClientBinary != "/usr/local/bin/kcptun-client" || launch.ServerBinary != "/usr/local/bin/kcptun-server" {
		t.Fatalf("binaries = %q and %q, want one program per side", launch.ClientBinary, launch.ServerBinary)
	}

	// The two ends negotiate none of this. A disagreement over the code rate
	// or the key does not degrade the measurement, it stops the tunnel
	// carrying anything, and the benchmark would report a transport that
	// cannot connect rather than one that is slow.
	for _, flag := range []string{"-key", "-crypt", "-mode", "-mtu", "-datashard", "-parityshard", "-sndwnd", "-rcvwnd"} {
		if client[flag] == "" {
			t.Fatalf("%s is not set on the client", flag)
		}
		if client[flag] != server[flag] {
			t.Fatalf("%s = %q on the client and %q on the server", flag, client[flag], server[flag])
		}
	}
	// The benchmark's payload is a repeating byte ramp. With compression left
	// on, this stack would report snappy's rate rather than the path's.
	for side, args := range map[string][]string{"client": launch.ClientArgs, "server": launch.ServerArgs} {
		if !hasFlag(args, "-nocomp") {
			t.Fatalf("%s does not disable compression: %v", side, args)
		}
	}
}

// The parity ratio is the parameter a comparison against a fixed-rate code has
// to be swept over, so it has to reach the process.
func TestKCPTunCarriesTheConfiguredParityAndWindows(t *testing.T) {
	cfg := planConfig(KCPTun)
	cfg.KCP = KCPParams{Mode: "fast3", DataShards: 20, ParityShards: 15, SendWindow: 1024, ReceiveWindow: 2048, MTU: 1200}
	launch, err := Plan(cfg)
	if err != nil {
		t.Fatal(err)
	}
	client := argMap(t, launch.ClientArgs)
	for flag, want := range map[string]string{
		"-mode": "fast3", "-datashard": "20", "-parityshard": "15",
		"-sndwnd": "1024", "-rcvwnd": "2048", "-mtu": "1200",
	} {
		if client[flag] != want {
			t.Fatalf("%s = %q, want %q", flag, client[flag], want)
		}
	}
	// Encryption stays on by default: every other stack here runs under TLS,
	// and turning it off would measure a transport nobody deploys.
	if client["-crypt"] != "aes" {
		t.Fatalf("crypt = %q, want the implementation's own default", client["-crypt"])
	}
}

// A tunnel with nowhere to forward would fail every trial at SOCKS with a
// general error that says nothing about why, so it is refused up front.
func TestATunnelWithoutATargetOrASecondBinaryIsRefused(t *testing.T) {
	cfg := planConfig(KCPTun)
	cfg.SOCKSTarget = ""
	if _, err := Plan(cfg); err == nil || !strings.Contains(err.Error(), "SOCKS5 target") {
		t.Fatalf("error = %v, want a refusal naming the missing target", err)
	}
	cfg = planConfig(KCPTun)
	cfg.ServerBinary = ""
	if _, err := Plan(cfg); err == nil || !strings.Contains(err.Error(), "one program per side") {
		t.Fatalf("error = %v, want a refusal naming the missing server binary", err)
	}
	if !KCPTun.NeedsSOCKSTarget() {
		t.Fatal("kcptun does not declare that it needs a SOCKS5 target")
	}
	if TUIC.NeedsSOCKSTarget() {
		t.Fatal("a proxy stack asks for a SOCKS5 target it does not need")
	}
	if KCPTun.Transport() != "udp" {
		t.Fatalf("kcptun transport = %q, want the packet emulator", KCPTun.Transport())
	}
}

// The target is what makes a tunnel usable by a benchmark that speaks only
// SOCKS5, so it has to actually negotiate and relay.
func TestSOCKSTargetDialsWhatItIsAskedFor(t *testing.T) {
	origin := startEchoOrigin(t)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	target, err := StartSOCKSTarget(ctx)
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = target.Close() }()

	conn, err := net.DialTimeout("tcp", target.Address(), 5*time.Second)
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = conn.Close() }()
	if err := socksConnect(conn, origin); err != nil {
		t.Fatal(err)
	}
	if _, err := conn.Write([]byte("queqiao")); err != nil {
		t.Fatal(err)
	}
	echoed := make([]byte, len("queqiao"))
	if _, err := io.ReadFull(conn, echoed); err != nil {
		t.Fatal(err)
	}
	if string(echoed) != "queqiao" {
		t.Fatalf("echo = %q", echoed)
	}
}

// The three-process shape a tunnel needs, driven end to end: Start launches
// both sides with the arguments and environment the plan asked for, waits
// until the SOCKS endpoint accepts, relays through the harness target to a
// destination, and leaves nothing running afterwards.
//
// The tunnel here is this test binary re-executed, because the point being
// checked is the harness's half of the contract rather than any particular
// implementation's wire.
func TestATunnelStackRunsEndToEnd(t *testing.T) {
	if testing.Short() {
		t.Skip("launches processes")
	}
	origin := startEchoOrigin(t)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	target, err := StartSOCKSTarget(ctx)
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = target.Close() }()

	// The addresses the harness would have reserved and released.
	tunnelServer, socksListen := reserveAddress(t), reserveAddress(t)
	pair, err := Start(ctx, Config{
		Kind: stubTunnel, Binary: os.Args[0],
		ServerBinary: os.Args[0],
		ServerListen: tunnelServer, ClientRemote: tunnelServer,
		SOCKSListen: socksListen, SOCKSTarget: target.Address(),
		WorkDir: t.TempDir(),
	})
	if err != nil {
		t.Fatalf("start the tunnel pair: %v", err)
	}

	conn, err := net.DialTimeout("tcp", socksListen, 5*time.Second)
	if err != nil {
		pair.Close()
		t.Fatalf("the SOCKS endpoint did not accept: %v\n%s", err, pair.Logs())
	}
	if err := socksConnect(conn, origin); err != nil {
		_ = conn.Close()
		pair.Close()
		t.Fatalf("SOCKS through the tunnel: %v\n%s", err, pair.Logs())
	}
	if _, err := conn.Write([]byte("through")); err != nil {
		t.Fatal(err)
	}
	echoed := make([]byte, len("through"))
	if _, err := io.ReadFull(conn, echoed); err != nil {
		t.Fatalf("read through the tunnel: %v\n%s", err, pair.Logs())
	}
	if string(echoed) != "through" {
		t.Fatalf("echo = %q", echoed)
	}
	_ = conn.Close()

	pair.Close()
	// A leaked proxy process holds its ports and silently contaminates every
	// later trial, so teardown is part of the contract rather than tidiness.
	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		probe, err := net.DialTimeout("tcp", socksListen, 200*time.Millisecond)
		if err != nil {
			return
		}
		_ = probe.Close()
		time.Sleep(50 * time.Millisecond)
	}
	t.Fatal("the tunnel's SOCKS endpoint is still accepting after Close")
}

// stubTunnel is a tunnel stack whose implementation is this test binary. It is
// registered here rather than in the package so nothing outside the test can
// select it.
const stubTunnel Kind = "stub-tunnel"

func init() {
	stacks[stubTunnel] = stack{
		transport: "tcp", implementation: "stub", socksTarget: true,
		launch: func(cfg Config) (Launch, error) {
			helper := []string{"-test.run=^TestStubTunnelHelper$", "-test.timeout=0"}
			return Launch{
				ServerArgs: helper, ClientArgs: helper,
				ServerEnv: []string{
					stubTunnelListen + "=" + cfg.ServerListen,
					stubTunnelForward + "=" + cfg.SOCKSTarget,
				},
				ClientEnv: []string{
					stubTunnelListen + "=" + cfg.SOCKSListen,
					stubTunnelForward + "=" + cfg.ClientRemote,
				},
			}, nil
		},
	}
}

const (
	stubTunnelListen  = "QUEQIAO_STUB_TUNNEL_LISTEN"
	stubTunnelForward = "QUEQIAO_STUB_TUNNEL_FORWARD"
)

// TestStubTunnelHelper is one end of the stub tunnel when the environment says
// so, and nothing at all otherwise.
func TestStubTunnelHelper(t *testing.T) {
	listen, forward := os.Getenv(stubTunnelListen), os.Getenv(stubTunnelForward)
	if listen == "" || forward == "" {
		t.Skip("not running as a stub tunnel process")
	}
	listener, err := net.Listen("tcp", listen)
	if err != nil {
		t.Fatalf("stub tunnel listen %s: %v", listen, err)
	}
	defer func() { _ = listener.Close() }()
	for {
		conn, err := listener.Accept()
		if err != nil {
			return
		}
		go func() {
			defer func() { _ = conn.Close() }()
			onward, err := net.DialTimeout("tcp", forward, 5*time.Second)
			if err != nil {
				return
			}
			defer func() { _ = onward.Close() }()
			relay(conn, onward)
		}()
	}
}

// startEchoOrigin is the destination a measured connection ends at.
func startEchoOrigin(t *testing.T) string {
	t.Helper()
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = listener.Close() })
	go func() {
		for {
			conn, err := listener.Accept()
			if err != nil {
				return
			}
			go func() {
				defer func() { _ = conn.Close() }()
				_, _ = io.Copy(conn, conn)
			}()
		}
	}()
	return listener.Addr().String()
}

// reserveAddress takes a loopback port and releases it, which is what the
// harness does before an external implementation binds it itself.
func reserveAddress(t *testing.T) string {
	t.Helper()
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	address := listener.Addr().String()
	_ = listener.Close()
	return address
}

// socksConnect performs an unauthenticated SOCKS5 CONNECT.
func socksConnect(conn net.Conn, destination string) error {
	if err := conn.SetDeadline(time.Now().Add(10 * time.Second)); err != nil {
		return err
	}
	defer func() { _ = conn.SetDeadline(time.Time{}) }()
	if _, err := conn.Write([]byte{5, 1, 0}); err != nil {
		return err
	}
	method := make([]byte, 2)
	if _, err := io.ReadFull(conn, method); err != nil {
		return err
	}
	if method[0] != 5 || method[1] != 0 {
		return errors.New("no-authentication was not selected")
	}
	host, portText, err := net.SplitHostPort(destination)
	if err != nil {
		return err
	}
	port, err := strconv.Atoi(portText)
	if err != nil {
		return err
	}
	address := net.ParseIP(host).To4()
	if address == nil {
		return errors.New("the test destination is not IPv4")
	}
	request := []byte{5, 1, 0, 1}
	request = append(request, address...)
	request = binary.BigEndian.AppendUint16(request, uint16(port))
	if _, err := conn.Write(request); err != nil {
		return err
	}
	reply := make([]byte, 10)
	if _, err := io.ReadFull(conn, reply); err != nil {
		return err
	}
	if reply[1] != 0 {
		return errors.New("SOCKS5 reply " + strconv.Itoa(int(reply[1])))
	}
	return nil
}

func argMap(t *testing.T, args []string) map[string]string {
	t.Helper()
	values := map[string]string{}
	for i := 0; i < len(args); i++ {
		if !strings.HasPrefix(args[i], "-") {
			continue
		}
		if i+1 < len(args) && !strings.HasPrefix(args[i+1], "-") {
			values[args[i]] = args[i+1]
			i++
			continue
		}
		values[args[i]] = "true"
	}
	return values
}

func hasFlag(args []string, flag string) bool {
	for _, arg := range args {
		if arg == flag {
			return true
		}
	}
	return false
}
