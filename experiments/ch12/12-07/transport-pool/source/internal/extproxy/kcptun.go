package extproxy

import (
	"fmt"
	"strconv"
)

// kcptun is a tunnel, not a proxy, and that is the whole of what makes its
// integration different.
//
// The client listens on a local TCP port and forwards it over KCP to the
// server, which forwards to one target address. There is no SOCKS5 anywhere in
// that pair, so the harness runs a SOCKS5 server as the server's target and the
// client's local port becomes the endpoint the benchmark speaks to:
//
//	benchmark -> [kcptun client :SOCKSListen] -> emulator -> [kcptun server]
//	          -> [harness SOCKS5 target] -> destination
//
// Which means the measured path crosses the emulator exactly once, as it does
// for every other stack, and the two extra hops are loopback.
func kcpTunLaunch(cfg Config) (Launch, error) {
	if cfg.ServerBinary == "" {
		return Launch{}, fmt.Errorf("%s ships one program per side and needs both", cfg.Kind)
	}
	p := cfg.KCP
	// Held identical on both sides. kcptun negotiates none of this: a client
	// and server disagreeing about the code rate or the key simply fail to
	// carry anything, and the benchmark would report a transport that cannot
	// connect rather than one that is slow.
	shared := []string{
		"-key", p.Key,
		"-crypt", p.Crypt,
		"-mode", p.Mode,
		"-mtu", strconv.Itoa(p.MTU),
		"-datashard", strconv.Itoa(p.DataShards),
		"-parityshard", strconv.Itoa(p.ParityShards),
		"-sndwnd", strconv.Itoa(p.SendWindow),
		"-rcvwnd", strconv.Itoa(p.ReceiveWindow),
		// The benchmark's payload is a repeating byte ramp, which snappy
		// compresses to almost nothing. Left on, this stack would report the
		// compressor's rate rather than the path's, and it would beat every
		// other stack by an order of magnitude while carrying no more bytes.
		"-nocomp",
	}
	client := append([]string{"-l", cfg.SOCKSListen, "-r", cfg.ClientRemote}, shared...)
	server := append([]string{"-l", cfg.ServerListen, "-t", cfg.SOCKSTarget}, shared...)
	return Launch{
		ClientBinary: cfg.Binary,
		ServerBinary: cfg.ServerBinary,
		ClientArgs:   client,
		ServerArgs:   server,
	}, nil
}
