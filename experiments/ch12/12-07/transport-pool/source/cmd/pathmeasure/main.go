// Command pathmeasure asks what a stack achieves on a path, which is the
// question pathprobe deliberately refuses to answer.
//
// pathprobe sends open-loop and counts what arrives, so it describes the path
// and nothing else. That is the right instrument for finding an erasure floor
// or a capacity knee, and the wrong one for the question this project's
// datacenter work actually turns on: given a path that erases a seventh of
// what crosses it, what does an ordinary TCP connection do, and how much of
// the gap is the path's fault rather than the transport's?
//
// The two instruments together separate the two. Where pathprobe delivers 256
// Mbit/s at 300 offered and TCP delivers a fraction of a megabit over the same
// minutes, the difference is not the path. It is a congestion controller
// reading rate-independent erasure as congestion and backing off from a link
// that was never congested.
//
// Modes:
//
//	serve      sink TCP bytes, push them, or count a UDP blast
//	tcp        send for a duration and sample the kernel's account of why
//	fct        flow completion time for request-sized payloads, cold and warm
//	burst      repeated bursts on one connection, with the window at each step
//	udp        open-loop UDP in the upload direction
//	h2serve    an HTTP/2 sink whose flow-control windows are settable
//	h2proxy    terminate HTTP/2 locally with generous windows and stream onward
//	h2         upload over HTTP/2, to measure what those windows cost
//	load       many concurrent request flows, reporting the tail
//	frames     many concurrent frame streams, reporting per-message latency
//	ab         order-alternated A/B of two arms, pooled
//	workload   order-alternated A/B of a real HTTP request against both arms
//	stream     order-alternated A/B of a token stream, reporting the gaps
//	streamserve emit tokens at a fixed cadence, so the generator is not a variable
//	rtt        round-trip distribution
//
// Every mode can be pointed through a SOCKS5 proxy, so a tunnel and the path
// beneath it are measured by the same instrument rather than by two.
//
// The tcp mode is the latency-attribution instrument. Goodput alone cannot
// distinguish a small congestion window from a small receive window from an
// application with nothing to send, and those need different fixes; TCP_INFO
// names which one was binding in each interval.
package main

import (
	"bytes"
	"context"
	"crypto/tls"
	"encoding/binary"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"math"
	"net"
	"os"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	"net/http"
	"net/netip"

	"golang.org/x/net/http2"

	"github.com/bojieli/queqiao/internal/tcpinfo"
)

func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintf(os.Stderr, "pathmeasure: %v\n", err)
		os.Exit(1)
	}
}

func run(args []string) error {
	fs := flag.NewFlagSet("pathmeasure", flag.ContinueOnError)
	mode := fs.String("mode", "", "serve, tcp, fct, burst, udp, workload, or rtt")
	listen := fs.String("listen", ":12600", "serve: listen address")
	remote := fs.String("remote", "", "client: server address")
	seconds := fs.Float64("duration", 10, "client: seconds to run")
	cc := fs.String("cc", "", "tcp: congestion control for this socket (empty keeps the system default)")
	interval := fs.Float64("sample", 0.2, "tcp: seconds between TCP_INFO samples")
	bytesToSend := fs.Int64("bytes", 0, "tcp: stop after this many bytes instead of after --duration; the flow-completion measurement")
	jsonOut := fs.Bool("json", false, "emit samples as JSON lines rather than a table")
	count := fs.Int("count", 50, "rtt: probes to send")
	bursts := fs.Int("bursts", 5, "burst: number of bursts to send on one connection")
	idle := fs.Float64("idle", 2, "burst: seconds to idle between bursts")
	repeat := fs.Int("repeat", 1, "fct: repetitions per size")
	sizes := fs.String("sizes", "100KB,300KB,1MB,5MB", "fct: comma-separated payload sizes")
	aSpec := fs.String("a", "", "ab: first arm, either \"direct\" or \"socks5=host:port\"")
	bSpec := fs.String("b", "", "ab: second arm, same form as --a")
	rounds := fs.Int("rounds", 3, "ab: round pairs; each pair runs A-first once and B-first once")
	flows := fs.Int("flows", 16, "load/frames: concurrent flows or sessions")
	h2Window := fs.Int("h2-window", 0, "h2serve: SETTINGS_INITIAL_WINDOW_SIZE and the connection window, in bytes. 0 leaves the library default, which is the 64KB the RFC specifies")
	frames := fs.Int("frames", 100, "frames: messages per session")
	frameBytes := fs.Int("frame-bytes", 80, "frames: message size")
	frameEvery := fs.Float64("frame-interval", 0.02, "frames: seconds between messages")
	socks := fs.String("socks5", "", "reach the server through this SOCKS5 proxy, so the same instrument measures a tunnel and the path beneath it")
	rate := fs.Float64("rate", 10, "udp: offered rate in Mbit/s")
	payload := fs.Int("payload", 1200, "udp: datagram payload bytes")
	udpFrames := fs.Bool("udp-frames", false, "frames: carry messages over UDP rather than a stream, which is how voice actually travels and removes the head-of-line blocking a stream imposes on the frames behind a lost one")
	reverse := fs.Bool("reverse", false, "measure the download direction: the client connects, the server sends. The only way to measure the receive direction of a host that cannot accept inbound connections, which on real deployments is most of them")
	localAddr := fs.String("local-address", "", "bind the socket to this local IP, so a host TUN route does not carry the measurement through a tunnel to the very server being measured")
	url := fs.String("url", "", "workload: the endpoint to request")
	postFile := fs.String("post-file", "", "workload: file to send as the request body")
	formField := fs.String("form-field", "", "workload: send --post-file as a multipart field of this name rather than as a raw body")
	contentType := fs.String("content-type", "", "workload: Content-Type for a raw body; ignored when --form-field is set")
	reuse := fs.Bool("reuse", false, "workload: hold connections open between rounds, which is the long-lived bursty session rather than a cold one")
	spacing := fs.Float64("spacing", 0.8, "workload: seconds to wait between arms, so neither inherits the other's queue")
	var formValues repeatedValue
	fs.Var(&formValues, "form-value", "workload: an extra multipart field as key=value; repeatable")
	var headers repeatedValue
	fs.Var(&headers, "header", "workload: an extra request header as Name: value; repeatable")
	streamTokens := fs.Int("stream-tokens", 200, "streamserve: tokens to emit per response")
	streamInterval := fs.Float64("stream-interval", 0.03, "streamserve: seconds between tokens")
	streamTokenBytes := fs.Int("stream-token-bytes", 24, "streamserve: payload bytes per token")
	streamExpect := fs.Float64("stream-expect", 0, "stream: the generator's token interval in seconds. Given, the mode reports how far behind that schedule each token arrived, which is what a reader notices; a stall and its catch-up burst are invisible in the gap median")
	if err := fs.Parse(args); err != nil {
		return err
	}
	proxyAddr = *socks
	switch *mode {
	case "serve":
		return serve(*listen)
	case "tcp":
		if *remote == "" {
			return errors.New("tcp needs --remote")
		}
		return tcpRun(*remote, time.Duration(*seconds*float64(time.Second)), *cc,
			time.Duration(*interval*float64(time.Second)), *bytesToSend, *jsonOut, *localAddr)
	case "fct":
		if *remote == "" {
			return errors.New("fct needs --remote")
		}
		return fctRun(*remote, *sizes, *repeat, *cc, *localAddr, *reverse)
	case "burst":
		if *remote == "" {
			return errors.New("burst needs --remote")
		}
		return burstRun(*remote, *bursts, *bytesToSend,
			time.Duration(*idle*float64(time.Second)), *cc, *localAddr)
	case "h2proxy":
		if *remote == "" {
			return errors.New("h2proxy needs --remote")
		}
		return h2Proxy(*listen, *remote, *h2Window, *localAddr)
	case "h2serve":
		return h2Serve(*listen, *h2Window)
	case "h2":
		if *remote == "" {
			return errors.New("h2 needs --remote")
		}
		return h2Run(*remote, *sizes, *repeat, *localAddr)
	case "load":
		if *remote == "" {
			return errors.New("load needs --remote")
		}
		return loadRun(*remote, *sizes, *flows, *localAddr)
	case "frames":
		if *remote == "" {
			return errors.New("frames needs --remote")
		}
		if *udpFrames {
			return udpFramesRun(*remote, *flows, *frames, *frameBytes,
				time.Duration(*frameEvery*float64(time.Second)), *localAddr)
		}
		return framesRun(*remote, *flows, *frames, *frameBytes,
			time.Duration(*frameEvery*float64(time.Second)), *localAddr)
	case "ab":
		if *remote == "" || *aSpec == "" || *bSpec == "" {
			return errors.New("ab needs --remote, --a and --b")
		}
		return abRun(*remote, *aSpec, *bSpec, *rounds, *repeat, *sizes, *cc, *localAddr, *reverse)
	case "udp":
		if *remote == "" {
			return errors.New("udp needs --remote")
		}
		return udpUpRun(*remote, *rate, time.Duration(*seconds*float64(time.Second)), *payload, *localAddr)
	case "workload":
		if *url == "" {
			return fmt.Errorf("workload: --url is required")
		}
		w, err := buildBody(*postFile, *formField, *contentType, formValues)
		if err != nil {
			return fmt.Errorf("workload: %w", err)
		}
		w.headers = headers
		return workloadMode(*url, *aSpec, *bSpec, *rounds, *reuse, *localAddr, w,
			time.Duration(*spacing*float64(time.Second)))
	case "stream":
		if *url == "" {
			return fmt.Errorf("stream: --url is required")
		}
		w, err := buildBody(*postFile, *formField, *contentType, formValues)
		if err != nil {
			return fmt.Errorf("stream: %w", err)
		}
		w.headers = headers
		return streamMode(*url, *aSpec, *bSpec, *rounds, *reuse, *localAddr, w,
			time.Duration(*spacing*float64(time.Second)),
			time.Duration(*streamExpect*float64(time.Second)))
	case "streamserve":
		return streamServe(*listen, *streamTokens,
			time.Duration(*streamInterval*float64(time.Second)), *streamTokenBytes)
	case "rtt":
		if *remote == "" {
			return errors.New("rtt needs --remote")
		}
		return rttRun(*remote, *count, *localAddr)
	default:
		return errors.New("--mode must be serve, tcp, fct, burst, udp, ab, load, frames, h2serve, h2proxy, h2, or rtt")
	}
}

// The request header lets one connection express which direction is being
// measured. A host behind NAT or a cloud security group cannot accept inbound
// connections, and on real deployments that describes most clients -- so the
// receive direction can only be measured by having the client dial out and ask
// to be sent to. Since PR #52 found one live path erasing 3.8% in one
// direction and 19.9% in the other, measuring only the easy direction is not a
// simplification, it is half a measurement.
const (
	reqMagic    = 0x504d5351 // "PMSQ"
	reqHeader   = 16
	dirUpload   = 0 // client sends, server sinks
	dirDownload = 1 // server sends, client sinks
	// dirUDPUp asks the server to count a UDP blast the client is about to
	// send. The count returns over this TCP connection rather than over the
	// path being measured: a summary sent through a channel erasing a seventh
	// of what crosses it is lost precisely when the measurement matters most,
	// and a missing summary is then either an aborted run or, worse, replaced
	// by an estimate that makes loss read as zero.
	dirUDPUp = 2
	// dirEcho asks the server to return every message of a fixed size, which
	// is the streaming shape rather than the request one.
	dirEcho = 3
	// udpProbePort carries the blast. It is separate from the control port so
	// that a firewall permitting one and not the other is visible as a failed
	// probe rather than as a path that erases everything.
	udpProbePort = "12601"
)

func serve(addr string) error {
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		return err
	}
	// The same port carries a UDP echo, so the frame workload can be measured
	// over the carrier it actually uses without standing up a second service.
	if pc, perr := net.ListenPacket("udp", addr); perr == nil {
		go echoDatagrams(pc)
		fmt.Printf("pathmeasure UDP echo on %s\n", pc.LocalAddr())
	} else {
		fmt.Printf("pathmeasure UDP echo unavailable: %v\n", perr)
	}
	fmt.Printf("pathmeasure server on %s\n", ln.Addr())
	for {
		c, err := ln.Accept()
		if err != nil {
			return err
		}
		go serveConn(c)
	}
}

func serveConn(c net.Conn) {
	defer c.Close()
	hdr := make([]byte, reqHeader)
	// A peer that sends no header is an upload from an older client or from a
	// tool that just streams; treating a read failure as "sink it" keeps the
	// server useful for both.
	_ = c.SetReadDeadline(time.Now().Add(20 * time.Second))
	if _, err := io.ReadFull(c, hdr); err != nil {
		_ = c.SetReadDeadline(time.Time{})
		sink(c)
		return
	}
	_ = c.SetReadDeadline(time.Time{})
	if binary.LittleEndian.Uint32(hdr[0:4]) != reqMagic {
		sink(c)
		return
	}
	switch binary.LittleEndian.Uint32(hdr[4:8]) {
	case dirUpload:
		// A declared length lets the server acknowledge completion. Without an
		// acknowledgement from the peer, a client measuring an upload through
		// a proxy is timing how long its bytes took to reach the proxy's
		// buffer on loopback -- which is microseconds, and which makes any
		// tunnel look arbitrarily fast. The ack is the only definition of
		// "delivered" that survives an intermediary.
		n, ok := boundedLength(binary.LittleEndian.Uint64(hdr[8:16]))
		if !ok {
			sink(c)
			return
		}
		got, err := io.CopyN(io.Discard, c, n)
		if err != nil {
			fmt.Printf("upload short: %d of %d from %s: %v\n", got, n, c.RemoteAddr(), err)
			return
		}
		if _, err := c.Write([]byte{1}); err != nil {
			return
		}
		// Stay open: the client may send further payloads on this connection,
		// which is what makes the warm measurement warm.
		for {
			if _, err := io.ReadFull(c, hdr); err != nil {
				return
			}
			if binary.LittleEndian.Uint32(hdr[0:4]) != reqMagic {
				return
			}
			var ok bool
			if n, ok = boundedLength(binary.LittleEndian.Uint64(hdr[8:16])); !ok {
				return
			}
			if _, err := io.CopyN(io.Discard, c, n); err != nil {
				return
			}
			if _, err := c.Write([]byte{1}); err != nil {
				return
			}
		}
	case dirEcho:
		n, ok := boundedLength(binary.LittleEndian.Uint64(hdr[8:16]))
		if !ok || n > 1<<20 {
			return
		}
		size := int(n)
		buf := make([]byte, size)
		for {
			if _, err := io.ReadFull(c, buf); err != nil {
				return
			}
			if _, err := c.Write(buf); err != nil {
				return
			}
		}
	case dirUDPUp:
		// The session id is an opaque tag rather than a length, so it is
		// compared as the unsigned value it was written as.
		serveUDPCount(c, binary.LittleEndian.Uint64(hdr[8:16]))
	case dirDownload:
		n, ok := boundedLength(binary.LittleEndian.Uint64(hdr[8:16]))
		if !ok {
			return
		}
		buf := make([]byte, 256*1024)
		var sent int64
		for sent < n {
			w := buf
			if n-sent < int64(len(buf)) {
				w = buf[:n-sent]
			}
			k, err := c.Write(w)
			sent += int64(k)
			if err != nil {
				break
			}
		}
		fmt.Printf("pushed %d bytes to %s\n", sent, c.RemoteAddr())
	default:
		sink(c)
	}
}

func sink(c net.Conn) {
	start := time.Now()
	n, _ := io.Copy(io.Discard, c)
	el := time.Since(start).Seconds()
	mbit := 0.0
	if el > 0 {
		mbit = float64(n) * 8 / el / 1e6
	}
	fmt.Printf("received %d bytes in %.2fs = %.3f Mbit/s from %s\n",
		n, el, mbit, c.RemoteAddr())
}

func writeHeader(c net.Conn, dir uint32, n uint64) error {
	hdr := make([]byte, reqHeader)
	binary.LittleEndian.PutUint32(hdr[0:4], reqMagic)
	binary.LittleEndian.PutUint32(hdr[4:8], dir)
	binary.LittleEndian.PutUint64(hdr[8:16], n)
	_, err := c.Write(hdr)
	return err
}

// sample is one observation of the kernel's state plus enough context to say
// what changed since the previous one.
type sample struct {
	T             float64 `json:"t"`
	Bytes         int64   `json:"bytes"`
	GoodputMbit   float64 `json:"goodput_mbit"`
	CwndPackets   uint32  `json:"cwnd_pkts"`
	CwndBytes     uint64  `json:"cwnd_bytes"`
	InFlightBytes uint64  `json:"inflight_bytes"`
	SsthreshPkts  uint32  `json:"ssthresh_pkts"`
	RTTms         float64 `json:"rtt_ms"`
	MinRTTms      float64 `json:"min_rtt_ms"`
	PacingMbit    float64 `json:"pacing_mbit"`
	DeliveryMbit  float64 `json:"delivery_mbit"`
	AppLimited    bool    `json:"app_limited"`
	TotalRetrans  uint32  `json:"total_retrans"`
	RetransRate   float64 `json:"retrans_rate"`
	SndWndBytes   uint32  `json:"snd_wnd_bytes"`
	NotsentBytes  uint32  `json:"notsent_bytes"`
	CAState       uint8   `json:"ca_state"`
	Limiter       string  `json:"limiter"`
}

// proxyAddr is the SOCKS5 endpoint to reach the server through, empty for a
// direct connection. It is process-wide because every mode dials the same way
// and threading it through each signature would say nothing extra.
var proxyAddr string

// dialVia opens a connection to remote, through the SOCKS5 proxy if one is
// configured.
//
// Measuring a tunnel with the same instrument that measured the path beneath
// it is the only way the comparison means anything: a benchmark that uses one
// tool for the baseline and another for the tunnel is comparing two tools.
func dialVia(remote, localAddr string) (net.Conn, error) {
	d, err := dialer(localAddr)
	if err != nil {
		return nil, err
	}
	if proxyAddr == "" {
		return d.Dial("tcp", remote)
	}
	c, err := d.Dial("tcp", proxyAddr)
	if err != nil {
		return nil, fmt.Errorf("dial proxy %s: %w", proxyAddr, err)
	}
	if err := socks5Connect(c, remote); err != nil {
		_ = c.Close()
		return nil, err
	}
	return c, nil
}

// socks5Connect performs an unauthenticated CONNECT, which is what this
// project's client listener speaks.
func socks5Connect(c net.Conn, remote string) error {
	host, portStr, err := net.SplitHostPort(remote)
	if err != nil {
		return err
	}
	port, err := strconv.Atoi(portStr)
	if err != nil || port < 1 || port > 65535 {
		return fmt.Errorf("socks5: bad destination port %q", portStr)
	}
	_ = c.SetDeadline(time.Now().Add(20 * time.Second))
	defer func() { _ = c.SetDeadline(time.Time{}) }()
	if _, err := c.Write([]byte{5, 1, 0}); err != nil {
		return err
	}
	resp := make([]byte, 2)
	if _, err := io.ReadFull(c, resp); err != nil {
		return err
	}
	if resp[0] != 5 || resp[1] != 0 {
		return fmt.Errorf("socks5: server chose method %d", resp[1])
	}
	req := []byte{5, 1, 0}
	if ip := net.ParseIP(host); ip != nil && ip.To4() != nil {
		req = append(req, 1)
		req = append(req, ip.To4()...)
	} else if ip != nil {
		req = append(req, 4)
		req = append(req, ip.To16()...)
	} else {
		if len(host) > 255 {
			return fmt.Errorf("socks5: host too long")
		}
		req = append(req, 3, byte(len(host)))
		req = append(req, host...)
	}
	req = append(req, byte(port>>8), byte(port))
	if _, err := c.Write(req); err != nil {
		return err
	}
	head := make([]byte, 4)
	if _, err := io.ReadFull(c, head); err != nil {
		return err
	}
	if head[1] != 0 {
		return fmt.Errorf("socks5: CONNECT refused, reply %d", head[1])
	}
	var skip int
	switch head[3] {
	case 1:
		skip = 4
	case 4:
		skip = 16
	case 3:
		l := make([]byte, 1)
		if _, err := io.ReadFull(c, l); err != nil {
			return err
		}
		skip = int(l[0])
	default:
		return fmt.Errorf("socks5: unknown address type %d", head[3])
	}
	if _, err := io.ReadFull(c, make([]byte, skip+2)); err != nil {
		return err
	}
	return nil
}

// dialer builds a dialer bound to a chosen source address.
//
// This is not a convenience. A host running a TUN-mode proxy carries traffic
// for the default route through a tunnel, and on the machines this project is
// measured from that tunnel frequently terminates at the very server on the
// other end of the measurement. The result is a number describing the proxy,
// reported as though it described the path. Binding the source address to the
// physical interface is the only way to be sure which path was measured.
func dialer(localAddr string) (*net.Dialer, error) {
	d := &net.Dialer{Timeout: 15 * time.Second}
	if localAddr == "" {
		return d, nil
	}
	ip := net.ParseIP(localAddr)
	if ip == nil {
		return nil, fmt.Errorf("bad --local-address %q", localAddr)
	}
	d.LocalAddr = &net.TCPAddr{IP: ip}
	return d, nil
}

// tcpRun sends as fast as the stack allows and records why it was not faster.
//
// The payload is incompressible only in the sense that nothing in the path is
// expected to compress it; what matters is that the sender never becomes the
// constraint, so the write loop hands the kernel a large buffer repeatedly and
// lets the socket apply the backpressure. If the application were the limit,
// every sample would say so, which is precisely what the app_limited bit is
// for.
func tcpRun(remote string, dur time.Duration, cc string, every time.Duration, stopAfter int64, jsonOut bool, localAddr string) error {
	if _, err := dialer(localAddr); err != nil {
		return err
	}
	c, err := dialVia(remote, localAddr)
	if err != nil {
		return err
	}
	defer c.Close()
	tc, ok := c.(*net.TCPConn)
	if !ok {
		return errors.New("not a TCP connection")
	}
	if cc != "" {
		raw, err := tc.SyscallConn()
		if err != nil {
			return err
		}
		if err := tcpinfo.SetCongestionControl(raw, cc); err != nil {
			return fmt.Errorf("set congestion control %q: %w", cc, err)
		}
	}

	buf := make([]byte, 256*1024)
	for i := range buf {
		buf[i] = byte(i)
	}

	start := time.Now()
	var sent int64
	var prev tcpinfo.Info
	var samples []sample
	noKernelInfo := false
	// A write that fails ends the run early. Reporting the elapsed time
	// without reporting why it ended would turn a broken connection into a
	// throughput result, which is the failure mode this whole instrument
	// exists to avoid.
	var writeErr error
	done := make(chan struct{})
	deadline := start.Add(dur)

	go func() {
		defer close(done)
		for {
			if stopAfter > 0 && sent >= stopAfter {
				return
			}
			if stopAfter == 0 && time.Now().After(deadline) {
				return
			}
			w := buf
			if stopAfter > 0 && stopAfter-sent < int64(len(buf)) {
				w = buf[:stopAfter-sent]
			}
			n, err := tc.Write(w)
			sent += int64(n)
			if err != nil {
				writeErr = err
				return
			}
		}
	}()

	tick := time.NewTicker(every)
	defer tick.Stop()
loop:
	for {
		select {
		case <-done:
			break loop
		case <-tick.C:
			// A kernel without TCP_INFO costs the attribution, not the
			// measurement. Goodput, loss of the connection and wall time are
			// still observable from userspace, and a tool that refused to
			// report them because it could not also report the cause would be
			// useless on exactly the client machines whose paths matter.
			info, err := tcpinfo.Get(tc)
			if err != nil {
				if !errors.Is(err, errNoKernelInfo) && err.Error() != "tcpinfo: not supported on this platform" {
					return err
				}
				noKernelInfo = true
			}
			el := time.Since(start).Seconds()
			s := sample{
				T:             el,
				Bytes:         sent,
				GoodputMbit:   float64(info.BytesAcked) * 8 / el / 1e6,
				CwndPackets:   info.SndCwnd,
				CwndBytes:     info.CwndBytes(),
				InFlightBytes: info.BytesInFlight(),
				SsthreshPkts:  info.SndSsthresh,
				RTTms:         float64(info.RTT) / 1000,
				MinRTTms:      float64(info.MinRTT) / 1000,
				PacingMbit:    float64(info.PacingRate) * 8 / 1e6,
				DeliveryMbit:  float64(info.DeliveryRate) * 8 / 1e6,
				AppLimited:    info.AppLimited,
				TotalRetrans:  info.TotalRetrans,
				SndWndBytes:   info.SndWnd,
				NotsentBytes:  info.NotsentBytes,
				CAState:       info.CAState,
				Limiter:       info.Limiter(prev),
			}
			if info.BytesSent > 0 {
				s.RetransRate = float64(info.BytesRetrans) / float64(info.BytesSent)
			}
			samples = append(samples, s)
			prev = info
			if jsonOut {
				b, _ := json.Marshal(s)
				fmt.Println(string(b))
			}
		}
	}
	_ = tc.CloseWrite()
	elapsed := time.Since(start)
	if writeErr != nil {
		fmt.Printf("# RUN ENDED EARLY: write failed after %d bytes: %v\n", sent, writeErr)
	}

	final, ferr := tcpinfo.Get(tc)
	if !jsonOut {
		report(samples, sent, elapsed, cc, final, ferr, noKernelInfo)
	}
	return nil
}

// errNoKernelInfo marks the platforms that cannot answer the attribution
// question, so the caller can tell "this kernel does not offer TCP_INFO" apart
// from "this socket failed".
var errNoKernelInfo = tcpinfo.ErrUnsupportedSentinel

func report(samples []sample, sent int64, elapsed time.Duration, cc string, final tcpinfo.Info, ferr error, noKernelInfo bool) {
	if cc == "" {
		cc = "system default"
	}
	if noKernelInfo {
		fmt.Printf("# kernel offers no TCP_INFO here: goodput is measured, attribution is not\n")
	}
	fmt.Printf("# congestion control: %s\n", cc)
	fmt.Printf("# %d bytes offered in %.2fs = %.3f Mbit/s at the application\n",
		sent, elapsed.Seconds(), float64(sent)*8/elapsed.Seconds()/1e6)
	fmt.Printf("t\tgoodput\tcwnd_pkt\tcwnd_KB\tinflt_KB\trtt_ms\tpacing\tdelivery\tapplim\tretr%%\tlimiter\n")
	for _, s := range samples {
		fmt.Printf("%.1f\t%.3f\t%d\t%.1f\t%.1f\t%.1f\t%.2f\t%.2f\t%v\t%.2f\t%s\n",
			s.T, s.GoodputMbit, s.CwndPackets, float64(s.CwndBytes)/1024,
			float64(s.InFlightBytes)/1024, s.RTTms, s.PacingMbit, s.DeliveryMbit,
			s.AppLimited, s.RetransRate*100, s.Limiter)
	}
	if ferr == nil && !noKernelInfo {
		fmt.Printf("# final: acked=%d retrans_bytes=%d (%.2f%% of sent) total_retrans=%d min_rtt=%.1fms\n",
			final.BytesAcked, final.BytesRetrans,
			pct(final.BytesRetrans, final.BytesSent), final.TotalRetrans,
			float64(final.MinRTT)/1000)
		// The limiter histogram is the summary the phase gates in the
		// datacenter plan actually need: not how fast it went, but what it was
		// waiting on while it went that fast.
		hist := map[string]int{}
		for _, s := range samples {
			hist[s.Limiter]++
		}
		keys := make([]string, 0, len(hist))
		for k := range hist {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		fmt.Printf("# binding constraint by sample:")
		for _, k := range keys {
			fmt.Printf("  %s=%d/%d", k, hist[k], len(samples))
		}
		fmt.Println()
	}
}

func pct(a, b uint64) float64 {
	if b == 0 {
		return 0
	}
	return float64(a) / float64(b) * 100
}

// rttRun measures the round trip the way a request/response application
// experiences it: a small write, a small read, and the wall time between.
// This is deliberately not ICMP, which is separately rate-limited and
// separately prioritised on most of the paths this project cares about.
func rttRun(remote string, count int, localAddr string) error {
	if _, err := dialer(localAddr); err != nil {
		return err
	}
	var ms []float64
	for i := 0; i < count; i++ {
		start := time.Now()
		c, err := dialVia(remote, localAddr)
		if err != nil {
			continue
		}
		el := time.Since(start)
		_ = c.Close()
		ms = append(ms, float64(el.Microseconds())/1000)
		time.Sleep(50 * time.Millisecond)
	}
	if len(ms) == 0 {
		return errors.New("no successful handshakes")
	}
	sort.Float64s(ms)
	fmt.Printf("# TCP handshake round trip, %d/%d succeeded\n", len(ms), count)
	fmt.Printf("p50=%.1fms p90=%.1fms p99=%.1fms min=%.1fms max=%.1fms\n",
		q(ms, 0.50), q(ms, 0.90), q(ms, 0.99), ms[0], ms[len(ms)-1])
	return nil
}

func q(sorted []float64, p float64) float64 {
	if len(sorted) == 0 {
		return 0
	}
	i := int(p * float64(len(sorted)-1))
	return sorted[i]
}

// parseSize accepts the units a payload is actually discussed in.
func parseSize(s string) (int64, error) {
	mult := int64(1)
	switch {
	case strings.HasSuffix(s, "KB"):
		mult, s = 1024, strings.TrimSuffix(s, "KB")
	case strings.HasSuffix(s, "MB"):
		mult, s = 1024*1024, strings.TrimSuffix(s, "MB")
	case strings.HasSuffix(s, "B"):
		s = strings.TrimSuffix(s, "B")
	}
	v, err := strconv.ParseFloat(strings.TrimSpace(s), 64)
	if err != nil {
		return 0, fmt.Errorf("bad size %q", s)
	}
	return int64(v * float64(mult)), nil
}

// fctRun measures flow completion time, which is the metric this project's
// datacenter work is actually about.
//
// Throughput is the wrong number for a 300KB request. A connection that
// averages 90 Mbit/s over twenty seconds and one that delivers 300KB in 400ms
// describe different experiences of the same path, and only the second is what
// an inference call feels. Completion time also exposes the costs throughput
// averages away: the handshakes, and the round trips slow start spends
// climbing to a rate the flow never gets to use.
//
// Cold and warm are reported separately because the difference between them is
// the entire argument for connection reuse, and because a benchmark that
// silently reuses a connection reports a number no cold caller will ever see.
func fctRun(remote, sizes string, repeat int, cc, localAddr string, reverse bool) error {
	var list []int64
	for _, f := range strings.Split(sizes, ",") {
		n, err := parseSize(f)
		if err != nil {
			return err
		}
		list = append(list, n)
	}
	dirName := "upload (client -> server)"
	if reverse {
		dirName = "download (server -> client)"
	}
	fmt.Printf("# flow completion time to %s, %d repetition(s) per size, %s\n", remote, repeat, dirName)
	fmt.Printf("# cold includes the TCP handshake; warm reuses an established connection\n")
	fmt.Printf("size\tmode\tconnect_ms\ttransfer_ms\ttotal_ms\teff_Mbit\n")
	for _, n := range list {
		if reverse {
			for r := 0; r < repeat; r++ {
				cms, tms, err := oneDownload(remote, n, cc, localAddr)
				if err != nil {
					fmt.Printf("%s\tcold\tERROR: %v\n", human(n), err)
					continue
				}
				total := cms + tms
				fmt.Printf("%s\tcold\t%.1f\t%.1f\t%.1f\t%.2f\n",
					human(n), cms, tms, total, float64(n)*8/(total/1000)/1e6)
			}
			continue
		}
		for r := 0; r < repeat; r++ {
			cms, tms, err := oneFlow(remote, n, cc, localAddr, nil)
			if err != nil {
				fmt.Printf("%s\tcold\tERROR: %v\n", human(n), err)
				continue
			}
			total := cms + tms
			fmt.Printf("%s\tcold\t%.1f\t%.1f\t%.1f\t%.2f\n",
				human(n), cms, tms, total, float64(n)*8/(total/1000)/1e6)
		}
		// Warm: one connection, the same payload sent repeatedly, so the
		// handshake and whatever the window has learned are already paid for.
		if _, err := dialer(localAddr); err != nil {
			return err
		}
		c, err := dialVia(remote, localAddr)
		if err != nil {
			fmt.Printf("%s\twarm\tERROR: %v\n", human(n), err)
			continue
		}
		tc := c
		if cc != "" {
			if t, ok := c.(*net.TCPConn); ok {
				if raw, e := t.SyscallConn(); e == nil {
					_ = tcpinfo.SetCongestionControl(raw, cc)
				}
			}
		}
		for r := 0; r < repeat+1; r++ {
			_, tms, err := oneFlow("", n, cc, localAddr, tc)
			if err != nil {
				break
			}
			// The first warm iteration still pays for slow start, so it is
			// labelled rather than averaged in with the rest.
			label := "warm"
			if r == 0 {
				label = "warm-first"
			}
			fmt.Printf("%s\t%s\t0.0\t%.1f\t%.1f\t%.2f\n",
				human(n), label, tms, tms, float64(n)*8/(tms/1000)/1e6)
		}
		_ = tc.Close()
	}
	return nil
}

// oneFlow sends exactly n bytes, either on a fresh connection whose handshake
// it times, or on one handed to it.
func oneFlow(remote string, n int64, cc, localAddr string, existing net.Conn) (connectMS, transferMS float64, err error) {
	tc := existing
	if tc == nil {
		if _, derr := dialer(localAddr); derr != nil {
			return 0, 0, derr
		}
		t0 := time.Now()
		c, e := dialVia(remote, localAddr)
		if e != nil {
			return 0, 0, e
		}
		connectMS = float64(time.Since(t0).Microseconds()) / 1000
		tc = c
		defer tc.Close()
		if cc != "" {
			if t, ok := c.(*net.TCPConn); ok {
				if raw, e := t.SyscallConn(); e == nil {
					_ = tcpinfo.SetCongestionControl(raw, cc)
				}
			}
		}
	}
	buf := make([]byte, 64*1024)
	t1 := time.Now()
	// The length is declared first so the peer knows when to acknowledge.
	if e := writeHeader(tc, dirUpload, uint64(n)); e != nil {
		return connectMS, 0, e
	}
	var sent int64
	for sent < n {
		w := buf
		if n-sent < int64(len(buf)) {
			w = buf[:n-sent]
		}
		k, e := tc.Write(w)
		sent += int64(k)
		if e != nil {
			return connectMS, 0, e
		}
	}
	// Completion is when the peer says it has the bytes. Reading the local
	// socket's own accounting instead would time the send buffer, and through
	// a proxy would time loopback.
	ack := make([]byte, 1)
	_ = tc.SetReadDeadline(time.Now().Add(120 * time.Second))
	if _, e := io.ReadFull(tc, ack); e != nil {
		return connectMS, 0, fmt.Errorf("no completion ack: %w", e)
	}
	_ = tc.SetReadDeadline(time.Time{})
	transferMS = float64(time.Since(t1).Microseconds()) / 1000
	return connectMS, transferMS, nil
}

func human(n int64) string {
	switch {
	case n >= 1024*1024:
		return fmt.Sprintf("%dMB", n/(1024*1024))
	case n >= 1024:
		return fmt.Sprintf("%dKB", n/1024)
	}
	return fmt.Sprintf("%dB", n)
}

// burstRun is the demonstration that a long-lived connection does not stay
// warm.
//
// It sends a burst, idles, and sends the same burst again on the same
// connection, recording the congestion window and the app_limited bit at each
// step. The belief this tests is the most widely held wrong belief about
// keepalive: that a connection which has already carried traffic will carry
// the next burst at the rate it previously achieved. What the kernel actually
// does -- refuse to grow a window the application never filled, and on some
// controllers reset it outright after an idle period -- is visible here and
// nowhere in a throughput number.
func burstRun(remote string, bursts int, burstBytes int64, idle time.Duration, cc, localAddr string) error {
	if burstBytes <= 0 {
		burstBytes = 300 * 1024
	}
	if _, err := dialer(localAddr); err != nil {
		return err
	}
	c, err := dialVia(remote, localAddr)
	if err != nil {
		return err
	}
	defer c.Close()
	tc := c.(*net.TCPConn)
	if cc != "" {
		if raw, e := tc.SyscallConn(); e == nil {
			if e := tcpinfo.SetCongestionControl(raw, cc); e != nil {
				return e
			}
		}
	}
	ssai := "unknown"
	if b, e := os.ReadFile("/proc/sys/net/ipv4/tcp_slow_start_after_idle"); e == nil {
		ssai = strings.TrimSpace(string(b))
	}
	fmt.Printf("# %d bursts of %s on ONE connection, %v idle between, cc=%s\n",
		bursts, human(burstBytes), idle, cc)
	fmt.Printf("# tcp_slow_start_after_idle=%s\n", ssai)
	fmt.Printf("burst\telapsed_ms\tMbit\tcwnd_before\tcwnd_after\tssthresh\tapplim\tretrans\n")
	buf := make([]byte, 64*1024)
	for i := 0; i < bursts; i++ {
		before, _ := tcpinfo.Get(tc)
		t0 := time.Now()
		var sent int64
		for sent < burstBytes {
			w := buf
			if burstBytes-sent < int64(len(buf)) {
				w = buf[:burstBytes-sent]
			}
			k, e := tc.Write(w)
			sent += int64(k)
			if e != nil {
				return e
			}
		}
		info, e := tcpinfo.Get(tc)
		for e == nil && info.Unacked > 0 {
			time.Sleep(time.Millisecond)
			info, e = tcpinfo.Get(tc)
		}
		el := float64(time.Since(t0).Microseconds()) / 1000
		fmt.Printf("%d\t%.1f\t%.2f\t%d\t%d\t%d\t%v\t%d\n",
			i, el, float64(burstBytes)*8/(el/1000)/1e6,
			before.SndCwnd, info.SndCwnd, info.SndSsthresh,
			info.AppLimited, info.TotalRetrans)
		if i < bursts-1 {
			time.Sleep(idle)
		}
	}
	return nil
}

// oneDownload measures the receive direction: dial out, ask for n bytes, and
// time how long they take to arrive.
func oneDownload(remote string, n int64, cc, localAddr string) (connectMS, transferMS float64, err error) {
	d, derr := dialer(localAddr)
	if derr != nil {
		return 0, 0, derr
	}
	_ = d
	t0 := time.Now()
	c, e := dialVia(remote, localAddr)
	if e != nil {
		return 0, 0, e
	}
	defer c.Close()
	connectMS = float64(time.Since(t0).Microseconds()) / 1000
	if cc != "" {
		if tc, ok := c.(*net.TCPConn); ok {
			if raw, e := tc.SyscallConn(); e == nil {
				_ = tcpinfo.SetCongestionControl(raw, cc)
			}
		}
	}
	t1 := time.Now()
	if err := writeHeader(c, dirDownload, uint64(n)); err != nil {
		return connectMS, 0, err
	}
	got, rerr := io.CopyN(io.Discard, c, n)
	transferMS = float64(time.Since(t1).Microseconds()) / 1000
	if rerr != nil && got < n {
		return connectMS, transferMS, fmt.Errorf("received %d of %d: %w", got, n, rerr)
	}
	return connectMS, transferMS, nil
}

// The probe datagram carries a session and a sequence so the receiver can
// attribute a gap to this run rather than to whatever else reaches the port.
const (
	udpMagic  = 0x504d5544 // "PMUD"
	udpHdrLen = 16
)

// serveUDPCount receives one session's blast and reports what arrived back
// over the TCP control connection.
func serveUDPCount(c net.Conn, session uint64) {
	pc, err := net.ListenPacket("udp", ":"+udpProbePort)
	if err != nil {
		// The port is held by a concurrent run. Saying so is required: a zero
		// count returned here is indistinguishable from a path that erased
		// every datagram, and that is the more interesting result to fake.
		fmt.Fprintf(c, "ERROR %v\n", err)
		return
	}
	defer pc.Close()
	buf := make([]byte, 2048)
	var got, bytes, highest uint64
	_ = pc.SetReadDeadline(time.Now().Add(90 * time.Second))
	for {
		n, _, err := pc.ReadFrom(buf)
		if err != nil {
			break
		}
		if n < udpHdrLen || binary.LittleEndian.Uint32(buf[0:4]) != udpMagic {
			continue
		}
		if binary.LittleEndian.Uint64(buf[4:12]) != session {
			continue
		}
		if seq := uint64(binary.LittleEndian.Uint32(buf[12:16])); seq+1 > highest {
			highest = seq + 1
		}
		got++
		bytes += uint64(n)
		// Once traffic is flowing, a short gap means the sender has stopped,
		// so the report need not wait out the full timeout.
		_ = pc.SetReadDeadline(time.Now().Add(3 * time.Second))
	}
	fmt.Fprintf(c, "OK %d %d %d\n", got, bytes, highest)
}

// udpUpRun measures the send direction of a UDP path, which pathprobe cannot:
// its server is the sender by design, so it characterises the download.
//
// That asymmetry is not academic here. This project has now measured a path
// whose two directions differ by more than an order of magnitude, so
// characterising one and assuming the other is not an approximation -- it
// describes a different path.
func udpUpRun(remote string, rateMbit float64, dur time.Duration, payload int, localAddr string) error {
	host, _, err := net.SplitHostPort(remote)
	if err != nil {
		return err
	}
	d, err := dialer(localAddr)
	if err != nil {
		return err
	}
	_ = d
	ctl, err := dialVia(remote, localAddr)
	if err != nil {
		return err
	}
	defer ctl.Close()
	session := uint64(time.Now().UnixNano())
	if err := writeHeader(ctl, dirUDPUp, session); err != nil {
		return err
	}
	// Let the server bind its probe port before the blast starts, so early
	// datagrams are not counted as path loss.
	time.Sleep(300 * time.Millisecond)

	uconn, err := net.Dial("udp", net.JoinHostPort(host, udpProbePort))
	if err != nil {
		return err
	}
	defer uconn.Close()

	pkt := make([]byte, payload)
	binary.LittleEndian.PutUint32(pkt[0:4], udpMagic)
	binary.LittleEndian.PutUint64(pkt[4:12], session)

	perPkt := time.Duration(float64(payload) * 8 / (rateMbit * 1e6) * float64(time.Second))
	start := time.Now()
	deadline := start.Add(dur)
	var sent uint32
	next := start
	for time.Now().Before(deadline) {
		binary.LittleEndian.PutUint32(pkt[12:16], sent)
		if _, err := uconn.Write(pkt); err != nil {
			break
		}
		sent++
		next = next.Add(perPkt)
		if w := time.Until(next); w > 0 {
			time.Sleep(w)
		}
	}
	elapsed := time.Since(start)
	time.Sleep(500 * time.Millisecond) // let the tail arrive

	_ = ctl.SetReadDeadline(time.Now().Add(20 * time.Second))
	reply := make([]byte, 128)
	n, rerr := ctl.Read(reply)
	if rerr != nil {
		return fmt.Errorf("no count returned over the control connection: %w", rerr)
	}
	var got, bytes, highest uint64
	if _, err := fmt.Sscanf(string(reply[:n]), "OK %d %d %d", &got, &bytes, &highest); err != nil {
		return fmt.Errorf("bad reply %q", string(reply[:n]))
	}
	loss := 0.0
	if sent > 0 {
		loss = 100 * (1 - float64(got)/float64(sent))
	}
	fmt.Printf("# UDP upload (client -> server), %d-byte payloads, %.1fs\n", payload, elapsed.Seconds())
	fmt.Printf("offered_Mbit\tsent_pkts\tdelivered_pkts\tdelivered_Mbit\tloss_pct\n")
	fmt.Printf("%.1f\t%d\t%d\t%.2f\t%.1f\n",
		rateMbit, sent, got, float64(bytes)*8/elapsed.Seconds()/1e6, loss)
	return nil
}

// abRun compares two arms in the only way this project's paths support.
//
// A live long-haul path drifts on the scale of the measurement. Identical warm
// 300KB flows on the China-US path ranged from 250ms to 2906ms, and a
// comparison that runs the baseline and then the change, once, resolves the
// drift and reports it as the change: measured there, position in the sequence
// was worth 158ms and the policy under test was worth 2.4ms. Sorting by
// profile gave a 53% win that reversed when the order reversed.
//
// So every round pair runs A first and then B first, and the pooled medians are
// reported beside the order effect. If the order effect is the larger of the
// two, the comparison has not measured the change and the report says so
// rather than leaving the reader to notice.
func abRun(remote, aSpec, bSpec string, rounds, repeat int, sizes, cc, localAddr string, reverse bool) error {
	aProxy, err := parseArm(aSpec)
	if err != nil {
		return fmt.Errorf("--a: %w", err)
	}
	bProxy, err := parseArm(bSpec)
	if err != nil {
		return fmt.Errorf("--b: %w", err)
	}
	size, err := parseSize(strings.Split(sizes, ",")[0])
	if err != nil {
		return err
	}
	if repeat < 1 {
		repeat = 1
	}
	var aAll, bAll, firstAll, secondAll []float64
	dir := "upload, warm"
	if reverse {
		dir = "download, cold"
	}
	fmt.Printf("# A=%s  B=%s  %s x %d per arm per round, %d round pairs, %s\n",
		aSpec, bSpec, human(size), repeat, rounds, dir)
	for r := 0; r < rounds; r++ {
		for _, aFirst := range []bool{true, false} {
			first, second := aProxy, bProxy
			if !aFirst {
				first, second = bProxy, aProxy
			}
			fs := armSamples(remote, first, size, repeat, cc, localAddr, reverse)
			ss := armSamples(remote, second, size, repeat, cc, localAddr, reverse)
			firstAll = append(firstAll, fs...)
			secondAll = append(secondAll, ss...)
			if aFirst {
				aAll, bAll = append(aAll, fs...), append(bAll, ss...)
			} else {
				bAll, aAll = append(bAll, fs...), append(aAll, ss...)
			}
		}
	}
	fmt.Printf("\n# pooled across both orders\n")
	fmt.Printf("arm\tn\tmedian_ms\tp25\tp75\tmin\tmax\n")
	reportArm("A", aAll)
	reportArm("B", bAll)
	fmt.Printf("\n# the same samples sorted by position rather than by arm\n")
	reportArm("first", firstAll)
	reportArm("second", secondAll)
	effect := absDiff(median(aAll), median(bAll))
	order := absDiff(median(firstAll), median(secondAll))
	fmt.Printf("\n# arm effect %.1fms, order effect %.1fms\n", effect, order)
	if order >= effect {
		fmt.Printf("# ORDER DOMINATES: this comparison has not resolved the change.\n")
		fmt.Printf("# Either the arms do not differ, or the path drifted more than they do.\n")
	}
	return nil
}

// parseArm turns an arm spec into the proxy it dials through, empty for direct.
func parseArm(spec string) (string, error) {
	if spec == "direct" {
		return "", nil
	}
	if rest, ok := strings.CutPrefix(spec, "socks5="); ok && rest != "" {
		return rest, nil
	}
	return "", fmt.Errorf("want \"direct\" or \"socks5=host:port\", got %q", spec)
}

// armSamples runs one arm once: a fresh connection, then repeat warm flows on
// it. The connection is fresh each time so that neither arm inherits the
// other's warmth.
func armSamples(remote, proxy string, size int64, repeat int, cc, localAddr string, reverse bool) []float64 {
	saved := proxyAddr
	proxyAddr = proxy
	defer func() { proxyAddr = saved }()

	// The download arm dials per flow, because the receive direction is
	// measured by asking to be sent to and there is no warm equivalent that
	// both arms could share fairly.
	if reverse {
		out := make([]float64, 0, repeat)
		for i := 0; i < repeat; i++ {
			_, ms, err := oneDownload(remote, size, cc, localAddr)
			if err != nil {
				fmt.Printf("# download sample failed: %v\n", err)
				continue
			}
			out = append(out, ms)
		}
		return out
	}

	c, err := dialVia(remote, localAddr)
	if err != nil {
		fmt.Printf("# arm dial failed: %v\n", err)
		return nil
	}
	defer c.Close()
	if cc != "" {
		if t, ok := c.(*net.TCPConn); ok {
			if raw, e := t.SyscallConn(); e == nil {
				_ = tcpinfo.SetCongestionControl(raw, cc)
			}
		}
	}
	out := make([]float64, 0, repeat)
	for i := 0; i < repeat+1; i++ {
		_, ms, err := oneFlow("", size, cc, localAddr, c)
		if err != nil {
			break
		}
		// The first flow on a fresh connection still pays for the ramp, and
		// including it would measure the handshake in both arms rather than
		// the difference between them.
		if i > 0 {
			out = append(out, ms)
		}
	}
	return out
}

func reportArm(name string, v []float64) {
	if len(v) == 0 {
		fmt.Printf("%s\t0\t--\n", name)
		return
	}
	s := append([]float64(nil), v...)
	sort.Float64s(s)
	fmt.Printf("%s\t%d\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\n",
		name, len(s), median(s), q(s, 0.25), q(s, 0.75), s[0], s[len(s)-1])
}

func median(v []float64) float64 {
	if len(v) == 0 {
		return 0
	}
	s := append([]float64(nil), v...)
	sort.Float64s(s)
	n := len(s)
	if n%2 == 1 {
		return s[n/2]
	}
	return (s[n/2-1] + s[n/2]) / 2
}

func absDiff(a, b float64) float64 {
	if a > b {
		return a - b
	}
	return b - a
}

// quantiles reduces a sample set to the figures a tail is read from.
func quantiles(ms []float64) (p50, p90, p99, p999 float64) {
	if len(ms) == 0 {
		return 0, 0, 0, 0
	}
	s := append([]float64(nil), ms...)
	sort.Float64s(s)
	return q(s, 0.50), q(s, 0.90), q(s, 0.99), q(s, 0.999)
}

// loadRun starts every flow at once and reports how long each took.
//
// They start together on purpose. Staggering them measures a queue that never
// forms, and the case a gateway has to survive is sessions that all speak at
// once because their users did.
func loadRun(remote, sizes string, flows int, localAddr string) error {
	size, err := parseSize(strings.Split(sizes, ",")[0])
	if err != nil {
		return err
	}
	var mu sync.Mutex
	var got []float64
	var failed int
	var wg sync.WaitGroup
	start := make(chan struct{})
	begun := time.Now()
	for i := 0; i < flows; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			<-start
			_, tms, err := oneFlow(remote, size, "", localAddr, nil)
			mu.Lock()
			defer mu.Unlock()
			if err != nil {
				failed++
				return
			}
			got = append(got, tms)
		}()
	}
	close(start)
	wg.Wait()
	wall := time.Since(begun).Seconds()

	p50, p90, p99, _ := quantiles(got)
	fmt.Printf("# %d concurrent %s flows, started together\n", flows, human(size))
	fmt.Printf("completed\tfailed\tp50_ms\tp90_ms\tp99_ms\tp99/p50\twall_s\taggregate_Mbit\n")
	ratio := 0.0
	if p50 > 0 {
		ratio = p99 / p50
	}
	fmt.Printf("%d/%d\t%d\t%.1f\t%.1f\t%.1f\t%.2f\t%.1f\t%.2f\n",
		len(got), flows, failed, p50, p90, p99, ratio, wall,
		float64(len(got))*float64(size)*8/wall/1e6)
	return nil
}

// framesRun is the streaming shape: many sessions each sending a small message
// on a fixed cadence, measuring how long each message takes to come back.
//
// The number that matters is not the median, which the path floor dictates,
// but how far above that floor the tail sits -- because that is what a jitter
// buffer has to absorb, and a message past it has displaced the one behind it.
func framesRun(remote string, sessions, count, size int, every time.Duration, localAddr string) error {
	var mu sync.Mutex
	var got []float64
	var dropped int
	var wg sync.WaitGroup
	start := make(chan struct{})
	for i := 0; i < sessions; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			<-start
			c, err := dialVia(remote, localAddr)
			if err != nil {
				return
			}
			defer c.Close()
			if err := writeHeader(c, dirEcho, uint64(size)); err != nil {
				return
			}
			frame := make([]byte, size)
			reply := make([]byte, size)
			tick := time.NewTicker(every)
			defer tick.Stop()
			for f := 0; f < count; f++ {
				<-tick.C
				sent := time.Now()
				if _, err := c.Write(frame); err != nil {
					return
				}
				_ = c.SetReadDeadline(time.Now().Add(15 * time.Second))
				if _, err := io.ReadFull(c, reply); err != nil {
					mu.Lock()
					dropped++
					mu.Unlock()
					return
				}
				ms := float64(time.Since(sent).Microseconds()) / 1000
				mu.Lock()
				got = append(got, ms)
				mu.Unlock()
			}
		}()
	}
	close(start)
	wg.Wait()

	if len(got) == 0 {
		return errors.New("no message completed a round trip")
	}
	p50, p90, p99, p999 := quantiles(got)
	s := append([]float64(nil), got...)
	sort.Float64s(s)
	floor := s[0]

	// Lateness is counted against fixed thresholds rather than against each
	// arm's own floor.
	//
	// A relative bar sounds fairer and is not. Two arms whose medians differ
	// by 10ms get bars 10ms apart, so the arm with the lower median has more
	// room beneath its own bar and reports fewer late messages for that reason
	// alone -- which on a steep distribution can be most of the difference. A
	// listener does not have a relative bar; a frame is late when it is late.
	over := func(bar float64) float64 {
		n := 0
		for _, v := range got {
			if v > bar {
				n++
			}
		}
		return 100 * float64(n) / float64(len(got))
	}
	fmt.Printf("# %d sessions x %d messages of %dB every %v\n", sessions, count, size, every)
	fmt.Printf("delivered\tp50_ms\tp90_ms\tp99_ms\tp999_ms\tp99/p50\tfloor_ms\t>250ms\t>400ms\t>1s\n")
	fmt.Printf("%d\t%.1f\t%.1f\t%.1f\t%.1f\t%.2f\t%.1f\t%.2f%%\t%.2f%%\t%.2f%%\n",
		len(got), p50, p90, p99, p999, p99/p50, floor,
		over(250), over(400), over(1000))
	return nil
}

// HTTP/2 flow control is usually the largest single component of a slow upload
// and the one no TCP tuning reaches.
//
// SETTINGS_INITIAL_WINDOW_SIZE defaults to 65535 bytes, and the window is
// credit per round trip, so it is a hard throughput ceiling: 64KB per RTT is
// 936 KB/s at 70ms and 328 KB/s at 200ms, whatever the congestion window is
// doing. Two properties make it worse than it looks. It is advertised by the
// receiver, so for an upload the limit belongs to the server rather than to
// the client that is slow. And it applies to each new stream, so a connection
// that has been open for hours gives every fresh request the same 64KB.
//
// These two modes exist to put a number on that claim rather than asserting
// it, by running the same upload against a server that has raised its windows
// and one that has not.

// h2Serve sinks HTTP/2 request bodies, with the flow-control windows settable
// so the same binary provides both arms of the comparison.
func h2Serve(addr string, window int) error {
	h2s := &http2.Server{}
	if w, ok := windowSetting(window); ok {
		// Both windows, because they are separate. RFC 7540 6.9.2:
		// SETTINGS_INITIAL_WINDOW_SIZE changes stream windows only, and the
		// connection window is raised solely by WINDOW_UPDATE -- so a server
		// that sets the first and forgets the second is capped at 64KB across
		// every stream at once, which is the more common misconfiguration.
		h2s.MaxUploadBufferPerStream = w
		h2s.MaxUploadBufferPerConnection = w
	}
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		n, _ := io.Copy(io.Discard, r.Body)
		fmt.Fprintf(w, "%d", n)
	})
	fmt.Printf("pathmeasure h2 server on %s (window=%d, 0 means library default)\n", addr, window)
	return serveClearTextH2(addr, h2s, handler)
}

// serveClearTextH2 speaks HTTP/2 on a plain TCP listener.
//
// Both ends here use prior knowledge: the client dials TCP and sends the HTTP/2
// preface without asking. That is what h2c.NewHandler exists to detect and
// upgrade, so with prior knowledge on both sides we can hand each accepted
// connection straight to the HTTP/2 server. Doing it this way keeps the upload
// buffer sizes configurable, which is the whole point of these modes, without
// depending on a package that has been deprecated.
func serveClearTextH2(addr string, h2s *http2.Server, handler http.Handler) error {
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		return err
	}
	defer ln.Close()
	for {
		conn, err := ln.Accept()
		if err != nil {
			return err
		}
		go h2s.ServeConn(conn, &http2.ServeConnOpts{Handler: handler})
	}
}

// h2Run uploads a payload over HTTP/2 and times it, reusing one connection so
// that the handshake is paid once and what is left is the windows.
func h2Run(remote, sizes string, repeat int, localAddr string) error {
	var list []int64
	for _, f := range strings.Split(sizes, ",") {
		n, err := parseSize(f)
		if err != nil {
			return err
		}
		list = append(list, n)
	}
	d, err := dialer(localAddr)
	if err != nil {
		return err
	}
	transport := &http2.Transport{
		AllowHTTP: true,
		DialTLSContext: func(ctx context.Context, network, addr string, _ *tls.Config) (net.Conn, error) {
			return d.DialContext(ctx, network, addr)
		},
	}
	client := &http.Client{Transport: transport, Timeout: 5 * time.Minute}
	if repeat < 1 {
		repeat = 1
	}
	fmt.Printf("# HTTP/2 upload to %s, one connection reused\n", remote)
	fmt.Printf("size\titeration\tms\teff_Mbit\n")
	for _, n := range list {
		body := make([]byte, n)
		for i := 0; i < repeat; i++ {
			start := time.Now()
			req, err := http.NewRequest(http.MethodPost, "http://"+remote+"/", bytes.NewReader(body))
			if err != nil {
				return err
			}
			req.ContentLength = n
			resp, err := client.Do(req)
			if err != nil {
				fmt.Printf("%s\t%d\tERROR: %v\n", human(n), i, err)
				continue
			}
			_, _ = io.Copy(io.Discard, resp.Body)
			_ = resp.Body.Close()
			ms := float64(time.Since(start).Microseconds()) / 1000
			label := "warm"
			if i == 0 {
				label = "first"
			}
			fmt.Printf("%s\t%s\t%.1f\t%.2f\n", human(n), label, ms, float64(n)*8/(ms/1000)/1e6)
		}
	}
	return nil
}

// h2Proxy is the L7 ingress: it terminates HTTP/2 locally with generous
// windows and streams the body onward over its own connection.
//
// It exists for the case the receiver's window cannot be changed -- a
// third-party endpoint whose SETTINGS_INITIAL_WINDOW_SIZE is whatever it is.
// A window is credit per round trip, so its cost is proportional to the round
// trip it spans: 64KB over 200ms is 328 KB/s and over 1ms is 64 MB/s. Placing
// the ingress next to the endpoint leaves the small window in place and makes
// it irrelevant, without changing anything on the far side.
//
// Three properties have to hold or the translation costs more than it saves.
//
// The body is streamed rather than buffered. Copying a request into memory
// before forwarding it would add its whole transfer time to the latency, which
// on a long path is most of the latency there is.
//
// Backpressure propagates, because io.Copy between the two bodies reads only
// as fast as the write side accepts. A proxy that read ahead would grow an
// unbounded queue and turn its tail into a queueing problem.
//
// Cancellation propagates, by deriving the upstream request from the inbound
// request's context. When a caller disappears mid-request the work behind it
// stops, which on an inference endpoint is a cost question as much as a
// latency one.
//
// Terminating HTTP/2 inherits its attack surface -- HPACK decompression bombs,
// CONTINUATION floods, stream-reset storms. This uses the hardened
// implementation in x/net rather than parsing frames itself, and it is a
// measurement instrument: do not put it in front of anything untrusted.
func h2Proxy(listen, remote string, window int, localAddr string) error {
	d, err := dialer(localAddr)
	if err != nil {
		return err
	}
	upstream := &http2.Transport{
		AllowHTTP: true,
		DialTLSContext: func(ctx context.Context, network, addr string, _ *tls.Config) (net.Conn, error) {
			return d.DialContext(ctx, network, addr)
		},
	}
	client := &http.Client{Transport: upstream}

	h2s := &http2.Server{}
	if w, ok := windowSetting(window); ok {
		h2s.MaxUploadBufferPerStream = w
		h2s.MaxUploadBufferPerConnection = w
	}
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		out, err := http.NewRequestWithContext(r.Context(), r.Method,
			"http://"+remote+r.URL.RequestURI(), r.Body)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadGateway)
			return
		}
		// ContentLength is carried across so the upstream can size its own
		// framing; -1 where the caller did not declare one, which is what
		// http.NewRequest already means by an unknown length.
		out.ContentLength = r.ContentLength
		for k, v := range r.Header {
			out.Header[k] = v
		}
		resp, err := client.Do(out)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadGateway)
			return
		}
		defer resp.Body.Close()
		for k, v := range resp.Header {
			w.Header()[k] = v
		}
		w.WriteHeader(resp.StatusCode)
		_, _ = io.Copy(w, resp.Body)
	})
	fmt.Printf("pathmeasure h2 ingress on %s -> %s (local window=%d)\n", listen, remote, window)
	return serveClearTextH2(listen, h2s, handler)
}

// boundedLength reads a length from a wire header and refuses anything that
// could not be a real payload.
//
// The value is attacker-controlled in the sense that anything can connect to
// this port and send sixteen bytes. Converting it straight to a signed length
// and handing it to io.CopyN would let a peer ask the server to read for as
// long as it likes. maxPayload is far above any measurement this tool takes
// and far below a length that could wrap.
func boundedLength(v uint64) (int64, bool) {
	if v == 0 || v > maxPayload {
		return 0, false
	}
	return int64(v), true
}

// maxPayload caps a single measured transfer at a gigabyte.
const maxPayload = 1 << 30

// windowSetting converts the flag to the int32 the HTTP/2 server takes.
//
// The flag is an int, so on a 64-bit host it can hold values the field cannot.
// A window larger than int32 is a typo rather than an intention, and silently
// truncating it would advertise a window nobody asked for.
func windowSetting(window int) (int32, bool) {
	if window <= 0 || window > math.MaxInt32 {
		return 0, false
	}
	return int32(window), true
}

// udpFramesRun measures the frame workload the way it actually travels.
//
// A voice stream is not carried on a reliable ordered bytestream, and
// measuring it as if it were reports a problem the application does not have.
// When one frame is lost on a stream, every frame behind it waits for the
// retransmission whether or not it arrived: measured across an emulated 14%
// path, the coded substrate repaired all but five of 2270 symbols and the p99
// was still 704ms, because those five stalled the frames queued behind them.
//
// Over UDP a lost frame is a lost frame. The ones after it are unaffected, the
// jitter buffer conceals the gap, and the tail is the path's rather than the
// transport's.
func udpFramesRun(remote string, sessions, count, size int, every time.Duration, localAddr string) error {
	var mu sync.Mutex
	var got []float64
	var lost int
	var wg sync.WaitGroup
	start := make(chan struct{})
	for i := 0; i < sessions; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			<-start
			conn, err := dialUDPVia(remote, localAddr)
			if err != nil {
				return
			}
			defer conn.Close()

			sentAt := make(map[uint32]time.Time, count)
			var smu sync.Mutex
			done := make(chan struct{})
			go func() {
				defer close(done)
				buf := make([]byte, size+64)
				for {
					_ = conn.SetReadDeadline(time.Now().Add(5 * time.Second))
					n, err := conn.Read(buf)
					if err != nil {
						return
					}
					if n < 4 {
						continue
					}
					seq := binary.LittleEndian.Uint32(buf[:4])
					smu.Lock()
					at, ok := sentAt[seq]
					delete(sentAt, seq)
					smu.Unlock()
					if !ok {
						continue
					}
					mu.Lock()
					got = append(got, float64(time.Since(at).Microseconds())/1000)
					mu.Unlock()
				}
			}()

			frame := make([]byte, size)
			tick := time.NewTicker(every)
			defer tick.Stop()
			for f := 0; f < count; f++ {
				<-tick.C
				binary.LittleEndian.PutUint32(frame[:4], uint32(f))
				smu.Lock()
				sentAt[uint32(f)] = time.Now()
				smu.Unlock()
				if _, err := conn.Write(frame); err != nil {
					break
				}
			}
			time.Sleep(2 * time.Second)
			_ = conn.Close()
			<-done
			smu.Lock()
			mu.Lock()
			lost += len(sentAt)
			mu.Unlock()
			smu.Unlock()
		}(i)
	}
	close(start)
	wg.Wait()

	if len(got) == 0 {
		return errors.New("no message came back over UDP")
	}
	p50, p90, p99, p999 := quantiles(got)
	s := append([]float64(nil), got...)
	sort.Float64s(s)
	over := func(bar float64) float64 {
		n := 0
		for _, v := range got {
			if v > bar {
				n++
			}
		}
		return 100 * float64(n) / float64(len(got))
	}
	fmt.Printf("# %d UDP sessions x %d messages of %dB every %v\n", sessions, count, size, every)
	fmt.Printf("delivered\tlost\tp50_ms\tp90_ms\tp99_ms\tp999_ms\tp99/p50\tfloor_ms\t>250ms\t>400ms\n")
	fmt.Printf("%d\t%d\t%.1f\t%.1f\t%.1f\t%.1f\t%.2f\t%.1f\t%.2f%%\t%.2f%%\n",
		len(got), lost, p50, p90, p99, p999, p99/p50, s[0], over(250), over(400))
	return nil
}

// udpConn is a UDP flow to one destination, either direct or through a SOCKS5
// association.
type udpConn struct {
	pc     net.PacketConn
	relay  net.Addr
	target netip.AddrPort
	// ctl holds the SOCKS5 control connection open. The association lives
	// exactly as long as it does, so dropping the reference would have the
	// proxy tear down the flow mid-measurement.
	ctl net.Conn
}

func (u *udpConn) Write(b []byte) (int, error) {
	if u.ctl == nil {
		return u.pc.WriteTo(b, u.relay)
	}
	// RFC 1928 request header: two reserved bytes, no fragment, then the
	// destination the datagram is for.
	hdr := []byte{0, 0, 0, 1}
	a4 := u.target.Addr().As4()
	hdr = append(hdr, a4[:]...)
	hdr = append(hdr, byte(u.target.Port()>>8), byte(u.target.Port()))
	if _, err := u.pc.WriteTo(append(hdr, b...), u.relay); err != nil {
		return 0, err
	}
	return len(b), nil
}

func (u *udpConn) Read(b []byte) (int, error) {
	buf := make([]byte, len(b)+512)
	n, _, err := u.pc.ReadFrom(buf)
	if err != nil {
		return 0, err
	}
	payload := buf[:n]
	if u.ctl != nil {
		// Strip the same header the proxy puts back on. Only IPv4 addresses
		// are produced by this tool, so only that form is decoded.
		if n < 10 || payload[3] != 1 {
			return 0, fmt.Errorf("short or non-IPv4 SOCKS5 UDP reply (%d bytes)", n)
		}
		payload = payload[10:]
	}
	return copy(b, payload), nil
}

func (u *udpConn) Close() error {
	if u.ctl != nil {
		_ = u.ctl.Close()
	}
	return u.pc.Close()
}

func (u *udpConn) SetReadDeadline(t time.Time) error { return u.pc.SetReadDeadline(t) }

// dialUDPVia opens a UDP flow, negotiating a SOCKS5 association when a proxy
// is configured.
//
// UDP ASSOCIATE is the reason this exists. A voice stream carried on a
// reliable ordered stream pays head-of-line blocking for every frame behind a
// lost one, which is a property of the carrier rather than of the path, and
// measuring it that way reports a problem the application does not have.
func dialUDPVia(remote, localAddr string) (*udpConn, error) {
	target, err := netip.ParseAddrPort(remote)
	if err != nil {
		return nil, fmt.Errorf("udp target %q: %w", remote, err)
	}
	pc, err := net.ListenPacket("udp", ":0")
	if err != nil {
		return nil, err
	}
	if proxyAddr == "" {
		return &udpConn{pc: pc, relay: net.UDPAddrFromAddrPort(target), target: target}, nil
	}

	d, err := dialer(localAddr)
	if err != nil {
		_ = pc.Close()
		return nil, err
	}
	ctl, err := d.Dial("tcp", proxyAddr)
	if err != nil {
		_ = pc.Close()
		return nil, err
	}
	relay, err := socks5Associate(ctl, pc.LocalAddr())
	if err != nil {
		_ = ctl.Close()
		_ = pc.Close()
		return nil, err
	}
	return &udpConn{pc: pc, relay: relay, target: target, ctl: ctl}, nil
}

// socks5Associate performs UDP ASSOCIATE and returns the relay endpoint the
// proxy wants datagrams sent to.
func socks5Associate(c net.Conn, local net.Addr) (net.Addr, error) {
	_ = c.SetDeadline(time.Now().Add(20 * time.Second))
	defer func() { _ = c.SetDeadline(time.Time{}) }()
	if _, err := c.Write([]byte{5, 1, 0}); err != nil {
		return nil, err
	}
	resp := make([]byte, 2)
	if _, err := io.ReadFull(c, resp); err != nil {
		return nil, err
	}
	if resp[0] != 5 || resp[1] != 0 {
		return nil, fmt.Errorf("socks5: server chose method %d", resp[1])
	}
	// The advertised source is where this client will send from. Zero is
	// permitted and means "whatever address you see", which is what a client
	// behind NAT has to say.
	ap, _ := netip.ParseAddrPort(local.String())
	req := []byte{5, 3, 0, 1, 0, 0, 0, 0}
	req = append(req, byte(ap.Port()>>8), byte(ap.Port()))
	if _, err := c.Write(req); err != nil {
		return nil, err
	}
	head := make([]byte, 4)
	if _, err := io.ReadFull(c, head); err != nil {
		return nil, err
	}
	if head[1] != 0 {
		return nil, fmt.Errorf("socks5: UDP ASSOCIATE refused, reply %d", head[1])
	}
	if head[3] != 1 {
		return nil, fmt.Errorf("socks5: relay address type %d is not IPv4", head[3])
	}
	rest := make([]byte, 6)
	if _, err := io.ReadFull(c, rest); err != nil {
		return nil, err
	}
	relayIP := netip.AddrFrom4([4]byte{rest[0], rest[1], rest[2], rest[3]})
	relayPort := uint16(rest[4])<<8 | uint16(rest[5])
	if relayIP.IsUnspecified() {
		// The proxy is telling us to keep using the address we reached it on.
		host, _, _ := net.SplitHostPort(c.RemoteAddr().String())
		if a, err := netip.ParseAddr(host); err == nil {
			relayIP = a
		}
	}
	return net.UDPAddrFromAddrPort(netip.AddrPortFrom(relayIP, relayPort)), nil
}

// echoDatagrams reflects each datagram to its sender, which is what the far
// side of a frame stream does.
func echoDatagrams(pc net.PacketConn) {
	defer pc.Close()
	buf := make([]byte, 2048)
	for {
		n, from, err := pc.ReadFrom(buf)
		if err != nil {
			return
		}
		if _, err := pc.WriteTo(buf[:n], from); err != nil {
			return
		}
	}
}
