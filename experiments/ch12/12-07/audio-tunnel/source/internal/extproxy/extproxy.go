// Package extproxy launches third-party proxy implementations so queqiao can be
// measured against them under the same emulated path.
//
// The in-tree reference in internal/baseline deliberately reproduces TUIC's
// data-path shape on queqiao's own QUIC stack, which isolates the transport
// design from the language and library. That is a useful control and a weak
// claim: it is not TUIC, and it says nothing about the other transports people
// actually deploy. This package closes that gap by driving real
// implementations - sing-box for TUIC and Hysteria2, and any binary that can be
// configured to expose SOCKS5 and dial a given server address.
//
// Each transport is a pair of processes: a server bound to a local address that
// the path emulator forwards to, and a client exposing SOCKS5 that dials the
// emulator. Nothing here is used by queqiaod; this is measurement scaffolding.
package extproxy

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"os"
	"sort"
	"time"
)

// Kind names a third-party transport this package can configure.
type Kind string

const (
	// TUIC is the protocol queqiao's in-tree reference imitates. Measuring
	// against the real implementation is the only way to claim parity with it.
	TUIC Kind = "tuic"
	// Hysteria2 is the other widely deployed QUIC-based transport for this
	// kind of path, and its congestion control is deliberately not loss
	// responsive.
	Hysteria2 Kind = "hysteria2"
	// VLESSWebSocket and VLESSTCP are TCP-based. They cannot be compared under
	// emulated packet loss, because a userspace relay carries a byte stream
	// and cannot drop a segment; see the TCP note in docs/BENCHMARKING.md.
	VLESSWebSocket Kind = "vless-ws"
	VLESSTCP       Kind = "vless-tcp"
	// KCPTun is a fixed-rate erasure-coded transport, which is the comparison
	// queqiao's own coding most needs: both spend parity to avoid a round
	// trip, and they choose how much of it in opposite ways. It is also the
	// first stack here that is a tunnel rather than a proxy; see SOCKSTarget.
	KCPTun Kind = "kcptun"
)

// Launch is what a stack asks the harness to run for one measured pair.
//
// The harness owns the path, the addresses, the certificate, the work
// directory and the process lifetime. A stack owns exactly two answers: what
// to write, and what to run. Keeping those apart is what lets a transport be
// added without touching Start -- sing-box takes a JSON file per side, an
// implementation configured entirely by flags returns no files at all, and one
// shipping separate client and server programs names a binary per side.
type Launch struct {
	// Files is configuration written before either process starts, keyed by
	// path and marshalled as JSON. Build the paths from Config.WorkDir, which
	// the caller creates and removes.
	Files map[string]any
	// ServerBinary and ClientBinary default to Config.Binary, which is the
	// usual case: one implementation serving both sides.
	ServerBinary, ClientBinary string
	// ServerArgs and ClientArgs are what each side is run with.
	ServerArgs, ClientArgs []string
	// ServerEnv and ClientEnv are added to the environment each side
	// inherits, for an implementation that takes configuration that way. A
	// credential belongs here rather than in the arguments, which every other
	// process on the machine can read.
	ServerEnv, ClientEnv []string
}

// stack is one third-party transport this package can measure.
type stack struct {
	// transport is the relay that can carry it, "udp" or "tcp". It decides
	// whether the packet emulator can carry the stack at all: a userspace
	// relay cannot drop a segment out of a byte stream, so a TCP transport
	// cannot be measured under emulated loss. See docs/BENCHMARKING.md.
	transport string
	// implementation is the program that provides it, which is what a caller
	// missing its path has to be told to supply.
	implementation string
	// socksTarget marks a tunnel rather than a proxy. A proxy is the SOCKS5
	// endpoint itself; a tunnel only forwards a local port, so the harness has
	// to run a SOCKS5 server on the far side for it to forward to, and the
	// tunnel's own local port becomes the endpoint the benchmark speaks to.
	socksTarget bool
	launch      func(Config) (Launch, error)
}

// stacks is the registry a new transport is added to. Everything else in this
// package is written against the registry rather than against sing-box.
var stacks = map[Kind]stack{
	TUIC:           {transport: "udp", implementation: "sing-box", launch: singBoxLaunch},
	Hysteria2:      {transport: "udp", implementation: "sing-box", launch: singBoxLaunch},
	VLESSTCP:       {transport: "tcp", implementation: "sing-box", launch: singBoxLaunch},
	VLESSWebSocket: {transport: "tcp", implementation: "sing-box", launch: singBoxLaunch},
	KCPTun:         {transport: "udp", implementation: "kcptun", socksTarget: true, launch: kcpTunLaunch},
}

// Kinds lists the transports this package can launch, in a stable order.
func Kinds() []Kind {
	kinds := make([]Kind, 0, len(stacks))
	for kind := range stacks {
		kinds = append(kinds, kind)
	}
	sort.Slice(kinds, func(i, j int) bool { return kinds[i] < kinds[j] })
	return kinds
}

// Transport reports whether a kind runs over UDP, which decides whether the
// UDP path emulator can carry it. An unregistered kind is reported as TCP,
// which is the conservative answer: it keeps an unknown name away from the
// packet relay rather than measuring it there.
func (k Kind) Transport() string {
	if s, ok := stacks[k]; ok {
		return s.transport
	}
	return "tcp"
}

// Implementation names the program that provides a kind, so a caller that was
// not given its path can say which one is missing.
func (k Kind) Implementation() string {
	return stacks[k].implementation
}

// NeedsSOCKSTarget reports whether the harness must run a SOCKS5 server on the
// server side for this stack to forward to. It is true for a tunnel, which
// carries a port rather than proxying, and false for a proxy, which is the
// endpoint itself.
func (k Kind) NeedsSOCKSTarget() bool { return stacks[k].socksTarget }

// Config describes one measured pair.
type Config struct {
	Kind Kind
	// Binary is the implementation to run, and the client side of it where an
	// implementation ships one program per side.
	Binary string
	// ServerBinary is the server-side program for an implementation that
	// ships two, as kcptun does. Empty means Binary serves both sides.
	ServerBinary string
	// ServerListen is the address the server binds; the emulator forwards to it.
	ServerListen string
	// ClientRemote is the emulator address the client dials.
	ClientRemote string
	// SOCKSListen is where the client exposes SOCKS5 for the benchmark.
	SOCKSListen string
	// CertificatePath and KeyPath are the server's TLS material. The client
	// trusts exactly CertificatePath, so no verification bypass is needed.
	CertificatePath string
	KeyPath         string
	// Congestion selects the controller where the implementation exposes one.
	Congestion string
	// WorkDir holds generated configuration. The caller owns its lifetime.
	WorkDir string
	// Credential is the shared secret: a password for TUIC and Hysteria2.
	Credential string
	// UUID identifies the user for TUIC and VLESS.
	UUID string
	// SOCKSTarget is the SOCKS5 endpoint a tunnel's server forwards to. The
	// harness runs it; see Kind.NeedsSOCKSTarget.
	SOCKSTarget string
	// KCP configures a KCP-based stack.
	KCP KCPParams
}

// KCPParams is the configuration of a KCP-based stack.
//
// Every field is set explicitly rather than left to the implementation's
// default, because these are the code rate and the windows -- which is where
// such a transport's behaviour is actually decided -- and a measurement that
// does not state them cannot be reproduced or compared. The defaults below are
// kcptun's own, so an unswept run is at least the configuration its users get.
type KCPParams struct {
	// Mode is the latency-against-throughput preset: normal, fast, fast2 or
	// fast3.
	Mode string
	// DataShards and ParityShards are the FEC ratio, fixed for the whole run.
	// Queqiao sizes its parity from the erasure it measures and revises it
	// while a flow runs, so one ratio here is a comparison against one guess:
	// sweep it. See docs/BENCHMARKING.md.
	DataShards, ParityShards int
	// SendWindow and ReceiveWindow are in KCP packets, and on a long-haul
	// lossy path they are the congestion control in practice.
	SendWindow, ReceiveWindow int
	MTU                       int
	// Crypt and Key are the transport's own encryption. It stays on, because
	// every other stack here runs under TLS and turning it off would measure a
	// transport nobody deploys.
	Crypt, Key string
}

func (p KCPParams) withDefaults() KCPParams {
	if p.Mode == "" {
		p.Mode = "fast"
	}
	if p.DataShards <= 0 {
		p.DataShards = 10
	}
	if p.ParityShards < 0 {
		p.ParityShards = 0
	}
	if p.ParityShards == 0 {
		p.ParityShards = 3
	}
	if p.SendWindow <= 0 {
		p.SendWindow = 128
	}
	if p.ReceiveWindow <= 0 {
		p.ReceiveWindow = 512
	}
	if p.MTU <= 0 {
		p.MTU = 1350
	}
	if p.Crypt == "" {
		p.Crypt = "aes"
	}
	if p.Key == "" {
		p.Key = "queqiao-benchmark-credential"
	}
	return p
}

func (c Config) withDefaults() Config {
	if c.Congestion == "" {
		c.Congestion = "bbr"
	}
	if c.Credential == "" {
		c.Credential = "queqiao-benchmark-credential"
	}
	if c.UUID == "" {
		c.UUID = "8c9dbf4a-3e2b-4a1c-9f6d-5b7e0a1c2d3e"
	}
	c.KCP = c.KCP.withDefaults()
	return c
}

// Pair is a running server and client. Close stops both.
type Pair struct {
	server *process
	client *process
}

func (p *Pair) Close() {
	if p == nil {
		return
	}
	// Stop the client first so it does not log connection errors while the
	// server is going away.
	p.client.stop()
	p.server.stop()
}

// Logs returns whatever the two processes wrote, which is the only diagnostic
// available when a third-party implementation refuses a configuration.
func (p *Pair) Logs() string {
	if p == nil {
		return ""
	}
	return "server:\n" + p.server.output() + "\nclient:\n" + p.client.output()
}

// Start launches the pair and waits until the client's SOCKS port accepts
// connections, so a benchmark never measures a process that is still starting.
func Start(ctx context.Context, cfg Config) (*Pair, error) {
	cfg = cfg.withDefaults()
	launch, err := Plan(cfg)
	if err != nil {
		return nil, err
	}
	for _, binary := range []string{launch.ServerBinary, launch.ClientBinary} {
		if _, err := os.Stat(binary); err != nil {
			return nil, fmt.Errorf("proxy binary: %w", err)
		}
	}
	for path, value := range launch.Files {
		if err := writeJSON(path, value); err != nil {
			return nil, err
		}
	}

	server, err := startProcess(ctx, launch.ServerBinary, launch.ServerEnv, launch.ServerArgs...)
	if err != nil {
		return nil, err
	}
	// The server has to be listening before the client dials, or the client
	// backs off and the first measured request pays that delay.
	if err := waitForListener(ctx, cfg.ServerListen, cfg.Kind.Transport(), 10*time.Second); err != nil {
		server.stop()
		return nil, fmt.Errorf("%s server did not listen: %w\n%s", cfg.Kind, err, server.output())
	}
	client, err := startProcess(ctx, launch.ClientBinary, launch.ClientEnv, launch.ClientArgs...)
	if err != nil {
		server.stop()
		return nil, err
	}
	// SOCKS5 is the contract with the benchmark: whatever the transport is,
	// the measured client is a SOCKS5 endpoint at this address, and it is
	// ready when that address accepts a connection.
	if err := waitForListener(ctx, cfg.SOCKSListen, "tcp", 10*time.Second); err != nil {
		client.stop()
		server.stop()
		return nil, fmt.Errorf("%s client did not listen: %w\n%s", cfg.Kind, err, client.output())
	}
	return &Pair{server: server, client: client}, nil
}

// Plan resolves what a stack would write and run, without running it. Start
// uses it, and a test can read it to check a stack's wiring without needing
// the implementation installed.
func Plan(cfg Config) (Launch, error) {
	cfg = cfg.withDefaults()
	registered, ok := stacks[cfg.Kind]
	if !ok {
		return Launch{}, fmt.Errorf("unsupported transport %q", cfg.Kind)
	}
	if cfg.Binary == "" {
		return Launch{}, fmt.Errorf("a %s binary is required for %s", registered.implementation, cfg.Kind)
	}
	if registered.socksTarget && cfg.SOCKSTarget == "" {
		// A tunnel forwards to whatever address it is given. Left empty it
		// would forward to nothing, and every trial would fail at SOCKS with a
		// general error that says nothing about why.
		return Launch{}, fmt.Errorf("%s is a tunnel and needs a SOCKS5 target to forward to", cfg.Kind)
	}
	launch, err := registered.launch(cfg)
	if err != nil {
		return Launch{}, err
	}
	if launch.ServerBinary == "" {
		launch.ServerBinary = cfg.Binary
	}
	if launch.ClientBinary == "" {
		launch.ClientBinary = cfg.Binary
	}
	if len(launch.ServerArgs) == 0 || len(launch.ClientArgs) == 0 {
		return Launch{}, fmt.Errorf("%s launch plan is missing a side", cfg.Kind)
	}
	return launch, nil
}

func writeJSON(path string, value any) error {
	encoded, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(encoded, '\n'), 0o600)
}

// waitForListener polls until the address accepts a connection. A UDP listener
// cannot be probed this way, so for UDP the check is that the process is still
// alive after a short settle.
func waitForListener(ctx context.Context, address, transport string, timeout time.Duration) error {
	deadline := time.Now().Add(timeout)
	if transport == "udp" {
		select {
		case <-time.After(250 * time.Millisecond):
			return nil
		case <-ctx.Done():
			return ctx.Err()
		}
	}
	for time.Now().Before(deadline) {
		conn, err := net.DialTimeout("tcp", address, 500*time.Millisecond)
		if err == nil {
			_ = conn.Close()
			return nil
		}
		select {
		case <-time.After(50 * time.Millisecond):
		case <-ctx.Done():
			return ctx.Err()
		}
	}
	return errors.New("timed out")
}
