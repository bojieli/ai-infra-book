// Command queqiaobench runs queqiao and a TUIC-shaped reference proxy over an
// identical, deterministic emulated WAN path and reports goodput and latency.
//
// The live China-US link that this project targets moves between roughly 0%
// and 50% packet loss within minutes, which makes sequential live A/B trials
// unable to separate a transport regression from a path window. This harness
// therefore runs both stacks in one process against a seeded path emulator, so
// a difference between the two rows is attributable to the transports.
//
// Live-path campaigns remain necessary and are not replaced by this tool; it
// is the fast, repeatable inner loop.
package main

import (
	"context"
	"crypto/ecdsa"
	"crypto/ed25519"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"errors"
	"flag"
	"fmt"
	"io"
	"log/slog"
	"math/big"
	"net"
	"os"
	"path/filepath"
	"runtime/pprof"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/bojieli/queqiao/internal/baseline"
	"github.com/bojieli/queqiao/internal/extproxy"
	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/pathsim"
	"github.com/bojieli/queqiao/internal/pep"
)

type options struct {
	stacks       string
	rttMillis    int
	lossPercent  float64
	lossBurst    float64
	lossUp       float64
	jitterMillis float64
	wanderMillis float64
	rateMbits    float64
	perFlowMbits float64
	queueBytes   int
	seed         int64
	bytes        int64
	trials       int
	flows        string
	congestion   string
	brutalMbits  float64
	chunkSize    int
	quicPool     bool
	timeout      time.Duration
	cpuProfile   string
	verbose      bool
	latency      bool
	interactive  bool
	singBox      string
	kcptunClient string
	kcptunServer string
	kcp          extproxy.KCPParams
	jsonOut      string
	gate         bool
	contend      string
	tolerance    float64
}

func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintf(os.Stderr, "queqiaobench: %v\n", err)
		os.Exit(1)
	}
}

func run(args []string) error {
	var opts options
	fs := flag.NewFlagSet("queqiaobench", flag.ContinueOnError)
	fs.StringVar(&opts.stacks, "stacks", "baseline,queqiao", "comma-separated stacks to measure")
	fs.IntVar(&opts.rttMillis, "rtt", 200, "emulated round-trip time in milliseconds")
	fs.Float64Var(&opts.lossPercent, "loss", 0, "per-packet loss percentage in each direction")
	fs.Float64Var(&opts.lossBurst, "loss-burst", 0, "mean loss burst length in packets (0 or 1 gives independent loss)")
	fs.Float64Var(&opts.lossUp, "loss-up", 0, "client-to-server loss percentage, overriding --loss for that direction")
	fs.Float64Var(&opts.jitterMillis, "jitter", 0, "maximum extra per-packet delay in milliseconds, which also reorders")
	fs.Float64Var(&opts.wanderMillis, "delay-wander", 0, "amplitude in milliseconds of a correlated random walk on the one-way delay; unlike --jitter this varies the round trip without reordering, which is what a long-haul path does")
	fs.Float64Var(&opts.rateMbits, "rate", 100, "bottleneck rate in Mbit/s in each direction (0 disables)")
	fs.Float64Var(&opts.perFlowMbits, "per-flow-rate", 0, "per-source-address rate in Mbit/s, modelling per-flow policing (0 disables)")
	fs.IntVar(&opts.queueBytes, "queue", 0, "bottleneck queue in bytes (0 selects one BDP)")
	fs.Int64Var(&opts.seed, "seed", 1, "path emulator seed")
	fs.Int64Var(&opts.bytes, "bytes", 10<<20, "object size per flow in bytes")
	fs.IntVar(&opts.trials, "trials", 3, "trials per stack")
	fs.StringVar(&opts.flows, "flows", "1", "comma-separated concurrent flow counts")
	fs.StringVar(&opts.congestion, "congestion", "bbr-tuic", "congestion controller for both stacks")
	fs.Float64Var(&opts.brutalMbits, "brutal-rate", 0, "queqiao fixed send rate in Mbit/s when --congestion=brutal")
	fs.IntVar(&opts.chunkSize, "chunk", 0, "queqiao data frame size in bytes (0 selects the default)")
	fs.BoolVar(&opts.quicPool, "quic-pool", true, "enable the queqiao pooled QUIC connection")
	fs.DurationVar(&opts.timeout, "timeout", 120*time.Second, "per-trial timeout")
	fs.StringVar(&opts.cpuProfile, "cpuprofile", "", "write a CPU profile to this path")
	fs.BoolVar(&opts.verbose, "verbose", false, "log transport diagnostics")
	fs.BoolVar(&opts.latency, "latency", false, "also measure small-request latency")
	fs.BoolVar(&opts.interactive, "interactive", false, "issue small requests during the bulk transfer and report their latency")
	fs.StringVar(&opts.singBox, "sing-box", "", "path to a sing-box binary, enabling the tuic and hysteria2 stacks")
	fs.StringVar(&opts.kcptunClient, "kcptun-client", "", "path to a kcptun client binary, enabling the kcptun stack")
	fs.StringVar(&opts.kcptunServer, "kcptun-server", "", "path to a kcptun server binary, which kcptun ships separately from its client")
	// A fixed code rate is chosen in advance rather than measured, so it is
	// the parameter a kcptun comparison has to be swept over rather than the
	// one it can leave at a default. The rest are here for the same reason:
	// an unstated window is an unreproducible measurement.
	fs.StringVar(&opts.kcp.Mode, "kcptun-mode", "", "kcptun latency preset: normal, fast, fast2 or fast3 (default fast)")
	fs.IntVar(&opts.kcp.DataShards, "kcptun-datashard", 0, "kcptun FEC data shards (default 10)")
	fs.IntVar(&opts.kcp.ParityShards, "kcptun-parityshard", 0, "kcptun FEC parity shards, the fixed code rate to sweep (default 3)")
	fs.IntVar(&opts.kcp.SendWindow, "kcptun-sndwnd", 0, "kcptun send window in packets (default 128)")
	fs.IntVar(&opts.kcp.ReceiveWindow, "kcptun-rcvwnd", 0, "kcptun receive window in packets (default 512)")
	fs.StringVar(&opts.jsonOut, "json", "", "also write the full result set to this path as JSON")
	fs.StringVar(&opts.contend, "contend", "", "two stacks to run concurrently on one shared bottleneck, e.g. queqiao,baseline; reports each one's share of the link")
	fs.BoolVar(&opts.gate, "gate", false, "exit non-zero when queqiao is worse than the reference beyond --tolerance")
	fs.Float64Var(&opts.tolerance, "tolerance", 0.10, "fractional goodput shortfall allowed by --gate")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if opts.trials <= 0 || opts.bytes <= 0 {
		return errors.New("trials and bytes must be positive")
	}

	if opts.cpuProfile != "" {
		file, err := os.Create(opts.cpuProfile)
		if err != nil {
			return err
		}
		defer file.Close()
		if err := pprof.StartCPUProfile(file); err != nil {
			return err
		}
		defer pprof.StopCPUProfile()
	}

	flowCounts, err := parseCounts(opts.flows)
	if err != nil {
		return err
	}
	pathCfg := pathsim.Config{
		OneWayDelay:            time.Duration(opts.rttMillis) * time.Millisecond / 2,
		LossRate:               opts.lossPercent / 100,
		LossBurstPackets:       opts.lossBurst,
		UpstreamLossRate:       opts.lossUp / 100,
		DelayJitter:            time.Duration(opts.jitterMillis * float64(time.Millisecond)),
		DelayWander:            time.Duration(opts.wanderMillis * float64(time.Millisecond)),
		RateBytesPerSec:        uint64(opts.rateMbits * 1e6 / 8),
		PerFlowRateBytesPerSec: uint64(opts.perFlowMbits * 1e6 / 8),
		QueueBytes:             opts.queueBytes,
		Seed:                   opts.seed,
	}

	origin, err := newOrigin(opts.bytes)
	if err != nil {
		return err
	}
	defer origin.Close()

	fmt.Printf("# path rtt=%dms loss=%.2f%% burst=%.1f rate=%.1fMbit/s per_flow=%.1fMbit/s queue=%s seed=%d object=%s congestion=%s\n",
		opts.rttMillis, opts.lossPercent, opts.lossBurst, opts.rateMbits, opts.perFlowMbits, humanQueue(pathCfg), opts.seed,
		humanBytes(opts.bytes), opts.congestion)
	fmt.Printf("stack\tflows\ttrial\tseconds\tmbits_per_sec\tcomplete\tnote\n")

	report := Report{
		SchemaVersion: 1,
		Source:        describeSource(),
		Arguments:     append([]string(nil), args...),
		Path:          describePath(opts, pathCfg),
	}
	if opts.contend != "" {
		report.Contention, err = measureContention(opts, pathCfg, origin)
		if err != nil {
			return err
		}
		if opts.jsonOut != "" {
			return writeReport(opts.jsonOut, report)
		}
		return nil
	}

	for _, stack := range strings.Split(opts.stacks, ",") {
		stack = strings.TrimSpace(stack)
		if stack == "" {
			continue
		}
		for _, flows := range flowCounts {
			for trial := 1; trial <= opts.trials; trial++ {
				// Each trial gets a fresh emulator and fresh proxy processes so
				// no trial inherits another trial's congestion state or queue.
				result := measure(stack, opts, pathCfg, origin, flows, trial)
				fmt.Printf("%s\t%d\t%d\t%.3f\t%.3f\t%d\t%s\n",
					stack, flows, trial, result.seconds, result.mbitsPerSec, boolInt(result.complete), result.note)
				report.Trials = append(report.Trials, TrialRecord{
					Stack: stack, Flows: flows, Trial: trial,
					Seconds: round3(result.seconds), MbitsPerSec: round3(result.mbitsPerSec),
					Complete: result.complete, Note: result.note, Interactive: result.interactive,
				})
			}
		}
	}
	report.Summary = summarize(report.Trials)
	printSummary(report.Summary)

	if opts.latency {
		report.Latency, err = measureLatency(opts, pathCfg, origin)
		if err != nil {
			return err
		}
	}
	if opts.jsonOut != "" {
		if err := writeReport(opts.jsonOut, report); err != nil {
			return err
		}
	}
	if opts.gate {
		return gateReport(report.Summary, opts.tolerance)
	}
	return nil
}

type trialResult struct {
	seconds     float64
	mbitsPerSec float64
	complete    bool
	note        string
	interactive *InteractiveReport
}

func measure(stack string, opts options, pathCfg pathsim.Config, origin *origin, flows, trial int) trialResult {
	ctx, cancel := context.WithTimeout(context.Background(), opts.timeout)
	defer cancel()

	// Seeding per trial keeps trials independent while remaining reproducible
	// for a given (seed, trial) pair.
	cfg := pathCfg
	cfg.Seed = pathCfg.Seed + int64(trial)*1000

	harness, err := startStack(ctx, stack, opts, cfg)
	if err != nil {
		return trialResult{note: "setup: " + err.Error()}
	}
	defer harness.Close()

	// One warm-up request establishes the QUIC connection so the measured
	// transfer reflects steady-state transport behavior for both stacks. TUIC
	// keeps a persistent connection, so charging queqiao for a cold handshake
	// and not TUIC would be the wrong comparison; handshake cost is reported
	// separately by the latency mode.
	if err := warmUp(ctx, harness.socks, origin); err != nil {
		return trialResult{note: "warmup: " + err.Error()}
	}

	var wg sync.WaitGroup
	results := make([]int64, flows)
	errs := make([]error, flows)
	// The scheduler's whole purpose is that a bulk transfer must not push
	// interactive latency past its budget, so measure that directly rather
	// than inferring it from throughput.
	probeStop := make(chan struct{})
	probeDone := make(chan []requestStages, 1)
	if opts.interactive {
		go func() { probeDone <- probeInteractive(ctx, harness.socks, origin, probeStop) }()
	}
	started := time.Now()
	for i := range flows {
		wg.Add(1)
		go func(index int) {
			defer wg.Done()
			n, fetchErr := fetch(ctx, harness.socks, origin.addr, opts.bytes)
			results[index], errs[index] = n, fetchErr
		}(i)
	}
	wg.Wait()
	elapsed := time.Since(started)
	var probes []requestStages
	if opts.interactive {
		close(probeStop)
		probes = <-probeDone
	}

	var total int64
	complete := true
	note := ""
	for i := range flows {
		total += results[i]
		if errs[i] != nil {
			complete = false
			if note == "" {
				note = errs[i].Error()
			}
		} else if results[i] != opts.bytes {
			complete = false
			if note == "" {
				note = fmt.Sprintf("short body %d", results[i])
			}
		}
	}
	up, down := harness.relay.Stats()
	if note == "" {
		// Loss and tail drop are separated because they mean opposite things
		// about the sender: ambient loss is the path's, a tail drop is the
		// sender's own overshoot of a queue. Reporting only the delivered
		// fraction hides which one a change moved.
		note = fmt.Sprintf("up=%d/%d,lost=%d,tail=%d down=%d/%d,lost=%d,tail=%d",
			up.PacketsOut, up.PacketsIn, up.PacketsLost, up.PacketsDropped,
			down.PacketsOut, down.PacketsIn, down.PacketsLost, down.PacketsDropped)
		// How many source addresses the path saw, which is how many buckets a
		// per-source policer applied. Lanes only multiply a per-source
		// allowance if they arrive from different sources, so a striping
		// number is uninterpretable without this.
		if counter, ok := harness.relay.(interface{ Sources() int }); ok {
			note += fmt.Sprintf(" sources=%d", counter.Sources())
		}
	}
	var interactive *InteractiveReport
	if opts.interactive {
		interactive = summarizeProbeReport(probes)
		note = summarizeProbes(probes) + " " + note
	}
	return trialResult{
		seconds:     elapsed.Seconds(),
		mbitsPerSec: float64(total) * 8 / elapsed.Seconds() / 1e6,
		complete:    complete,
		note:        note,
		interactive: interactive,
	}
}

// probeInteractive issues one small request at a time until stopped, and
// returns each request's latency. Failures are recorded as the elapsed time so
// a stalled probe cannot be silently dropped from the distribution.
func probeInteractive(ctx context.Context, socksAddr string, o *origin, stop <-chan struct{}) []requestStages {
	var samples []requestStages
	ticker := time.NewTicker(250 * time.Millisecond)
	defer ticker.Stop()
	for {
		select {
		case <-stop:
			return samples
		case <-ctx.Done():
			return samples
		case <-ticker.C:
		}
		_, stages, err := fetchTimed(ctx, socksAddr, o.smallAddr, o.smallSize)
		if err != nil && ctx.Err() != nil {
			return samples
		}
		samples = append(samples, stages)
	}
}

// summarizeProbeReport is the structured form of summarizeProbes.
func summarizeProbeReport(samples []requestStages) *InteractiveReport {
	if len(samples) == 0 {
		return nil
	}
	quantile := func(pick func(requestStages) time.Duration, q float64) float64 {
		values := make([]time.Duration, len(samples))
		for i, sample := range samples {
			values[i] = pick(sample)
		}
		sort.Slice(values, func(i, j int) bool { return values[i] < values[j] })
		return round3(float64(values[int(q*float64(len(values)-1))].Microseconds()) / 1000)
	}
	total := func(s requestStages) time.Duration { return s.Total }
	return &InteractiveReport{
		Samples:        len(samples),
		P50Millis:      quantile(total, 0.5),
		P95Millis:      quantile(total, 0.95),
		MaxMillis:      quantile(total, 1),
		ConnectP95:     quantile(func(s requestStages) time.Duration { return s.Connect }, 0.95),
		FirstByteP95Ms: quantile(func(s requestStages) time.Duration { return s.FirstByte }, 0.95),
	}
}

func summarizeProbes(samples []requestStages) string {
	if len(samples) == 0 {
		return "interactive=none"
	}
	quantile := func(pick func(requestStages) time.Duration, q float64) float64 {
		values := make([]time.Duration, len(samples))
		for i, sample := range samples {
			values[i] = pick(sample)
		}
		sort.Slice(values, func(i, j int) bool { return values[i] < values[j] })
		return float64(values[int(q*float64(len(values)-1))].Microseconds()) / 1000
	}
	total := func(s requestStages) time.Duration { return s.Total }
	connect := func(s requestStages) time.Duration { return s.Connect }
	first := func(s requestStages) time.Duration { return s.FirstByte }
	return fmt.Sprintf("interactive_n=%d p50=%.0fms p95=%.0fms max=%.0fms connect_p95=%.0fms firstbyte_p95=%.0fms",
		len(samples), quantile(total, 0.5), quantile(total, 0.95), quantile(total, 1),
		quantile(connect, 0.95), quantile(first, 0.95))
}

func measureLatency(opts options, pathCfg pathsim.Config, origin *origin) ([]LatencyRecord, error) {
	fmt.Printf("\nstack\ttrial\tconnect_ms\trequest_ms\tnote\n")
	var records []LatencyRecord
	for _, stack := range strings.Split(opts.stacks, ",") {
		stack = strings.TrimSpace(stack)
		if stack == "" {
			continue
		}
		for trial := 1; trial <= opts.trials; trial++ {
			ctx, cancel := context.WithTimeout(context.Background(), opts.timeout)
			cfg := pathCfg
			cfg.Seed = pathCfg.Seed + int64(trial)*1000
			harness, err := startStack(ctx, stack, opts, cfg)
			if err != nil {
				fmt.Printf("%s\t%d\t\t\tsetup: %v\n", stack, trial, err)
				records = append(records, LatencyRecord{Stack: stack, Trial: trial, Note: "setup: " + err.Error()})
				cancel()
				continue
			}
			// Cold request: includes the outer handshake for both stacks.
			coldStart := time.Now()
			_, coldErr := fetch(ctx, harness.socks, origin.smallAddr, origin.smallSize)
			cold := time.Since(coldStart)
			// Warm request: the outer connection already exists.
			warmStart := time.Now()
			_, warmErr := fetch(ctx, harness.socks, origin.smallAddr, origin.smallSize)
			warm := time.Since(warmStart)
			note := ""
			if coldErr != nil {
				note = "cold: " + coldErr.Error()
			} else if warmErr != nil {
				note = "warm: " + warmErr.Error()
			}
			coldMillis := round3(float64(cold.Microseconds()) / 1000)
			warmMillis := round3(float64(warm.Microseconds()) / 1000)
			fmt.Printf("%s\t%d\t%.1f\t%.1f\t%s\n", stack, trial, coldMillis, warmMillis, note)
			records = append(records, LatencyRecord{
				Stack: stack, Trial: trial, ColdMillis: coldMillis, WarmMillis: warmMillis,
				Complete: note == "", Note: note,
			})
			harness.Close()
			cancel()
		}
	}
	return records, nil
}

// ---------------------------------------------------------------- harness ---

// pathRelay is whichever emulator carries this stack: the UDP relay for
// QUIC-based transports, the TCP relay for stream-based ones.
type pathRelay interface {
	LocalAddr() string
	Stats() (pathsim.Stats, pathsim.Stats)
	Close() error
}

type harness struct {
	socks  string
	relay  pathRelay
	closes []func()
}

func (h *harness) Close() {
	for i := len(h.closes) - 1; i >= 0; i-- {
		h.closes[i]()
	}
}

func startStack(ctx context.Context, stack string, opts options, pathCfg pathsim.Config) (*harness, error) {
	return startStackOn(ctx, stack, opts, pathCfg, nil)
}

// startStackOn attaches the stack to a shared bottleneck when one is supplied,
// so two transports can be measured while contending for one link rather than
// one after the other on private ones.
func startStackOn(ctx context.Context, stack string, opts options, pathCfg pathsim.Config, shared *pathsim.Bottleneck) (*harness, error) {
	certificate, roots, err := selfSignedCertificate()
	if err != nil {
		return nil, err
	}
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	if opts.verbose {
		logger = slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelDebug}))
	}
	// A stream-based transport needs the TCP relay; everything else is carried
	// by the UDP one.
	if kind := extproxy.Kind(stack); kind.Transport() == "tcp" && stack != "baseline" && stack != "queqiao" {
		return startTCPStack(ctx, kind, opts, pathCfg, logger)
	}

	serverPacket, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		return nil, err
	}
	var relay *pathsim.Relay
	if shared != nil {
		relay, err = shared.Attach("127.0.0.1:0", serverPacket.LocalAddr().String(), pathCfg)
	} else {
		relay, err = pathsim.New("127.0.0.1:0", serverPacket.LocalAddr().String(), pathCfg)
	}
	if err != nil {
		_ = serverPacket.Close()
		return nil, err
	}
	socksListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		_ = relay.Close()
		_ = serverPacket.Close()
		return nil, err
	}
	h := &harness{socks: socksListener.Addr().String(), relay: relay}
	h.closes = append(h.closes, func() { _ = socksListener.Close() }, func() { _ = relay.Close() }, func() { _ = serverPacket.Close() })

	switch stack {
	case "baseline", "tuic":
		token := make([]byte, 32)
		if _, err := rand.Read(token); err != nil {
			h.Close()
			return nil, err
		}
		server, err := baseline.NewServer(baseline.ServerConfig{
			ListenAddr: serverPacket.LocalAddr().String(), Certificate: certificate,
			Token: token, Transport: baseline.TUICTransport(),
			Congestion:        baseline.CongestionKind(opts.congestion),
			BrutalBytesPerSec: uint64(opts.brutalMbits * 1e6 / 8), Logger: logger,
		})
		if err != nil {
			h.Close()
			return nil, err
		}
		client, err := baseline.NewClient(baseline.ClientConfig{
			ListenAddr: h.socks, RemoteAddr: relay.LocalAddr(), ServerName: "queqiao.test",
			RootCAs: roots, Token: token, Transport: baseline.TUICTransport(),
			Congestion:        baseline.CongestionKind(opts.congestion),
			BrutalBytesPerSec: uint64(opts.brutalMbits * 1e6 / 8), Logger: logger,
		})
		if err != nil {
			h.Close()
			return nil, err
		}
		go func() { _ = server.Serve(ctx, serverPacket) }()
		go func() { _ = client.ServeListener(ctx, socksListener) }()
		h.closes = append(h.closes, client.Close)
	case "queqiao":
		identityDir, err := os.MkdirTemp("", "queqiaobench-identity-")
		if err != nil {
			h.Close()
			return nil, err
		}
		h.closes = append(h.closes, func() { _ = os.RemoveAll(identityDir) })
		serverIdentity, clientIdentity, err := benchmarkCredentials(filepath.Join(identityDir, "provider"), relay.LocalAddr())
		if err != nil {
			h.Close()
			return nil, err
		}
		server, err := pep.NewServer(pep.ServerConfig{
			ListenAddr: serverPacket.LocalAddr().String(), Credentials: serverIdentity,
			DestinationPolicy: pep.DestinationPolicy{AllowPrivate: true}, EnableQUIC: true, ChunkSize: opts.chunkSize,
			Congestion: pep.CongestionControlKind(opts.congestion), BrutalBytesPerSec: uint64(opts.brutalMbits * 1e6 / 8),
			Logger: logger,
		})
		if err != nil {
			h.Close()
			return nil, err
		}
		client, err := pep.NewClient(pep.ClientConfig{
			ListenAddr: h.socks, RemoteAddr: relay.LocalAddr(), Credentials: clientIdentity,
			Transport: pep.TransportQUIC, ChunkSize: opts.chunkSize,
			EnableQUICPool:    opts.quicPool,
			Congestion:        pep.CongestionControlKind(opts.congestion),
			BrutalBytesPerSec: uint64(opts.brutalMbits * 1e6 / 8),
			Logger:            logger,
		})
		if err != nil {
			h.Close()
			return nil, err
		}
		go func() { _ = server.ServePacketConn(ctx, serverPacket) }()
		go func() { _ = client.ServeListener(ctx, socksListener) }()
	default:
		kind := extproxy.Kind(stack)
		if kind.Transport() != "udp" {
			h.Close()
			return nil, fmt.Errorf("stack %q is not carried by the UDP path emulator", stack)
		}
		clientBinary, serverBinary, err := externalBinaries(kind, opts)
		if err != nil {
			h.Close()
			return nil, err
		}
		// The third-party implementation needs its TLS material on disk, and
		// the SOCKS listener has to be free for it to bind itself.
		workDir, err := os.MkdirTemp("", "queqiaobench-"+stack+"-")
		if err != nil {
			h.Close()
			return nil, err
		}
		certPath, keyPath, err := writeCertificateFiles(workDir)
		if err != nil {
			h.Close()
			_ = os.RemoveAll(workDir)
			return nil, err
		}
		// A tunnel stack forwards a port rather than proxying, so the harness
		// runs the SOCKS5 endpoint it forwards to. It sits beyond the
		// emulator, so its own dial is loopback and is not measured.
		socksTarget := ""
		if kind.NeedsSOCKSTarget() {
			target, err := extproxy.StartSOCKSTarget(ctx)
			if err != nil {
				h.Close()
				_ = os.RemoveAll(workDir)
				return nil, err
			}
			socksTarget = target.Address()
			h.closes = append(h.closes, func() { _ = target.Close() })
		}
		// The external implementation binds these itself, so the harness has to
		// release the addresses it reserved. Without this the server silently
		// fails to bind and every request fails at SOCKS with a general error.
		serverAddr := serverPacket.LocalAddr().String()
		_ = serverPacket.Close()
		socksAddr := h.socks
		_ = socksListener.Close()
		pair, err := extproxy.Start(ctx, extproxy.Config{
			Kind: kind, Binary: clientBinary, ServerBinary: serverBinary,
			ServerListen: serverAddr, ClientRemote: relay.LocalAddr(),
			SOCKSListen: socksAddr, CertificatePath: certPath, KeyPath: keyPath,
			Congestion: externalCongestion(opts.congestion), WorkDir: workDir,
			SOCKSTarget: socksTarget, KCP: opts.kcp,
		})
		if err != nil {
			h.Close()
			_ = os.RemoveAll(workDir)
			return nil, err
		}
		h.closes = append(h.closes, pair.Close, func() { _ = os.RemoveAll(workDir) })
	}
	return h, nil
}

func benchmarkCredentials(directory, endpoint string) (identity.ServerCredentials, identity.ClientCredentials, error) {
	now := time.Now()
	provider, err := identity.InitProvider(directory, "benchmark", endpoint, now)
	if err != nil {
		return identity.ServerCredentials{}, identity.ClientCredentials{}, err
	}
	account, err := provider.Store.AddAccount("benchmark", time.Time{}, identity.AccountLimits{}, now)
	if err != nil {
		return identity.ServerCredentials{}, identity.ClientCredentials{}, err
	}
	_, invitation, err := provider.CreateInvitation(account.ID, time.Hour, now)
	if err != nil {
		return identity.ServerCredentials{}, identity.ClientCredentials{}, err
	}
	publicKey, privateKey, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		return identity.ServerCredentials{}, identity.ClientCredentials{}, err
	}
	_, device, err := provider.Store.ConsumeInvite(invitation.Token, "benchmark", publicKey, now)
	if err != nil {
		return identity.ServerCredentials{}, identity.ClientCredentials{}, err
	}
	certificatePEM, err := provider.IssueDevice(account.ID, device.ID, publicKey, now)
	if err != nil {
		return identity.ServerCredentials{}, identity.ClientCredentials{}, err
	}
	keyDER, err := x509.MarshalPKCS8PrivateKey(privateKey)
	if err != nil {
		return identity.ServerCredentials{}, identity.ClientCredentials{}, err
	}
	keyPEM := pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: keyDER})
	certificate, err := tls.X509KeyPair(certificatePEM, keyPEM)
	if err != nil {
		return identity.ServerCredentials{}, identity.ClientCredentials{}, err
	}
	return provider.ServerCredentials(), identity.ClientCredentials{
		ProviderID: provider.Metadata.ProviderID, GatewayID: provider.Metadata.GatewayID,
		Certificate: certificate, Root: provider.RootCert, RootPin: provider.Metadata.RootPin,
	}, nil
}

// externalCongestion maps this project's controller names onto the names the
// third-party implementations use. Only the shared ones are meaningful; an
// unknown name falls back to the implementation's own default so a comparison
// never silently runs an unintended controller.
func externalCongestion(name string) string {
	switch name {
	case "bbr", "bbr-tuic":
		return "bbr"
	case "reno":
		return "new_reno"
	default:
		return "bbr"
	}
}

// ----------------------------------------------------------------- origin ---

// origin is a local HTTP-free byte source. Using a raw TCP responder rather
// than net/http keeps the measurement free of HTTP parsing overhead and makes
// the expected byte count exact.
type origin struct {
	listener      net.Listener
	smallListener net.Listener
	addr          string
	smallAddr     string
	smallSize     int64
	size          int64
}

func newOrigin(size int64) (*origin, error) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return nil, err
	}
	smallListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		_ = listener.Close()
		return nil, err
	}
	o := &origin{
		listener: listener, smallListener: smallListener,
		addr: listener.Addr().String(), smallAddr: smallListener.Addr().String(),
		size: size, smallSize: 1024,
	}
	go o.serve(listener, size)
	go o.serve(smallListener, o.smallSize)
	return o, nil
}

func (o *origin) serve(listener net.Listener, size int64) {
	payload := make([]byte, 64*1024)
	for i := range payload {
		payload[i] = byte(i)
	}
	for {
		conn, err := listener.Accept()
		if err != nil {
			return
		}
		go func() {
			defer conn.Close()
			// Wait for the one-byte request so the response is not sent before
			// the client is ready; this mirrors an HTTP request/response.
			var request [1]byte
			if _, err := io.ReadFull(conn, request[:]); err != nil {
				return
			}
			remaining := size
			for remaining > 0 {
				chunk := int64(len(payload))
				if chunk > remaining {
					chunk = remaining
				}
				n, err := conn.Write(payload[:chunk])
				if err != nil {
					return
				}
				remaining -= int64(n)
			}
		}()
	}
}

func (o *origin) Close() {
	_ = o.listener.Close()
	_ = o.smallListener.Close()
}

// ------------------------------------------------------------------ SOCKS ---

func warmUp(ctx context.Context, socksAddr string, o *origin) error {
	_, err := fetch(ctx, socksAddr, o.smallAddr, o.smallSize)
	return err
}

func fetch(ctx context.Context, socksAddr, destination string, expect int64) (int64, error) {
	received, _, err := fetchTimed(ctx, socksAddr, destination, expect)
	return received, err
}

// requestStages breaks one request into the parts a transport controls
// separately, so a latency regression can be attributed to flow setup, to the
// first byte, or to the transfer itself rather than only observed in total.
type requestStages struct {
	Connect   time.Duration // SOCKS CONNECT acknowledged
	FirstByte time.Duration // first response byte after the request was written
	Total     time.Duration
}

func fetchTimed(ctx context.Context, socksAddr, destination string, expect int64) (int64, requestStages, error) {
	var stages requestStages
	started := time.Now()
	dialer := &net.Dialer{}
	conn, err := dialer.DialContext(ctx, "tcp", socksAddr)
	if err != nil {
		return 0, stages, err
	}
	defer conn.Close()
	if deadline, ok := ctx.Deadline(); ok {
		_ = conn.SetDeadline(deadline)
	}
	if err := socksConnect(conn, destination); err != nil {
		return 0, stages, err
	}
	stages.Connect = time.Since(started)
	if _, err := conn.Write([]byte{'g'}); err != nil {
		return 0, stages, err
	}
	var first [1]byte
	if _, err := io.ReadFull(conn, first[:]); err != nil {
		return 0, stages, err
	}
	stages.FirstByte = time.Since(started)
	received, err := io.Copy(io.Discard, io.LimitReader(conn, expect-1))
	received++
	stages.Total = time.Since(started)
	if err != nil {
		return received, stages, err
	}
	if received != expect {
		return received, stages, fmt.Errorf("received %d of %d bytes", received, expect)
	}
	return received, stages, nil
}

func socksConnect(conn net.Conn, destination string) error {
	host, port, err := net.SplitHostPort(destination)
	if err != nil {
		return err
	}
	portNumber, err := parsePort(port)
	if err != nil {
		return err
	}
	if _, err := conn.Write([]byte{5, 1, 0}); err != nil {
		return err
	}
	var method [2]byte
	if _, err := io.ReadFull(conn, method[:]); err != nil {
		return err
	}
	if method[0] != 5 || method[1] != 0 {
		return errors.New("SOCKS5 method negotiation failed")
	}
	request := []byte{5, 1, 0, 3, byte(len(host))}
	request = append(request, host...)
	request = append(request, byte(portNumber>>8), byte(portNumber))
	if _, err := conn.Write(request); err != nil {
		return err
	}
	var reply [4]byte
	if _, err := io.ReadFull(conn, reply[:]); err != nil {
		return err
	}
	if reply[1] != 0 {
		return fmt.Errorf("SOCKS5 connect failed with code %d", reply[1])
	}
	var skip int
	switch reply[3] {
	case 1:
		skip = 4 + 2
	case 4:
		skip = 16 + 2
	case 3:
		var length [1]byte
		if _, err := io.ReadFull(conn, length[:]); err != nil {
			return err
		}
		skip = int(length[0]) + 2
	default:
		return errors.New("unsupported SOCKS5 bound address type")
	}
	if _, err := io.CopyN(io.Discard, conn, int64(skip)); err != nil {
		return err
	}
	return nil
}

// ------------------------------------------------------------------ utils ---

func parsePort(port string) (int, error) {
	value := 0
	if port == "" {
		return 0, errors.New("empty port")
	}
	for _, r := range port {
		if r < '0' || r > '9' {
			return 0, fmt.Errorf("invalid port %q", port)
		}
		value = value*10 + int(r-'0')
	}
	if value == 0 || value > 65535 {
		return 0, fmt.Errorf("port %q out of range", port)
	}
	return value, nil
}

func parseCounts(spec string) ([]int, error) {
	parts := strings.Split(spec, ",")
	counts := make([]int, 0, len(parts))
	for _, part := range parts {
		part = strings.TrimSpace(part)
		if part == "" {
			continue
		}
		value, err := parsePort(part)
		if err != nil {
			return nil, fmt.Errorf("invalid flow count %q", part)
		}
		counts = append(counts, value)
	}
	if len(counts) == 0 {
		return nil, errors.New("no flow counts provided")
	}
	sort.Ints(counts)
	return counts, nil
}

func boolInt(v bool) int {
	if v {
		return 1
	}
	return 0
}

func humanBytes(n int64) string {
	switch {
	case n >= 1<<20:
		return fmt.Sprintf("%dMiB", n>>20)
	case n >= 1<<10:
		return fmt.Sprintf("%dKiB", n>>10)
	default:
		return fmt.Sprintf("%dB", n)
	}
}

func humanQueue(cfg pathsim.Config) string {
	if cfg.QueueBytes > 0 {
		return humanBytes(int64(cfg.QueueBytes))
	}
	return "1BDP"
}

func selfSignedCertificate() (tls.Certificate, *x509.CertPool, error) {
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		return tls.Certificate{}, nil, err
	}
	template := &x509.Certificate{
		SerialNumber: big.NewInt(1),
		Subject:      pkix.Name{CommonName: "queqiao.test"},
		DNSNames:     []string{"queqiao.test"},
		NotBefore:    time.Now().Add(-time.Minute),
		NotAfter:     time.Now().Add(time.Hour),
		KeyUsage:     x509.KeyUsageDigitalSignature | x509.KeyUsageKeyEncipherment,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
	}
	der, err := x509.CreateCertificate(rand.Reader, template, template, &key.PublicKey, key)
	if err != nil {
		return tls.Certificate{}, nil, err
	}
	keyDER, err := x509.MarshalPKCS8PrivateKey(key)
	if err != nil {
		return tls.Certificate{}, nil, err
	}
	certPEM := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})
	keyPEM := pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: keyDER})
	certificate, err := tls.X509KeyPair(certPEM, keyPEM)
	if err != nil {
		return tls.Certificate{}, nil, err
	}
	roots := x509.NewCertPool()
	if !roots.AppendCertsFromPEM(certPEM) {
		return tls.Certificate{}, nil, errors.New("append benchmark certificate")
	}
	return certificate, roots, nil
}

// writeCertificateFiles emits a self-signed pair for a third-party
// implementation, which needs its TLS material as files. The client trusts
// exactly this certificate, so no verification bypass is involved.
func writeCertificateFiles(dir string) (certPath, keyPath string, err error) {
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		return "", "", err
	}
	template := &x509.Certificate{
		SerialNumber: big.NewInt(1),
		Subject:      pkix.Name{CommonName: "queqiao.test"},
		DNSNames:     []string{"queqiao.test"},
		NotBefore:    time.Now().Add(-time.Minute),
		NotAfter:     time.Now().Add(24 * time.Hour),
		KeyUsage:     x509.KeyUsageDigitalSignature | x509.KeyUsageKeyEncipherment,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
	}
	der, err := x509.CreateCertificate(rand.Reader, template, template, &key.PublicKey, key)
	if err != nil {
		return "", "", err
	}
	keyDER, err := x509.MarshalPKCS8PrivateKey(key)
	if err != nil {
		return "", "", err
	}
	certPath = filepath.Join(dir, "cert.pem")
	keyPath = filepath.Join(dir, "key.pem")
	if err := os.WriteFile(certPath, pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der}), 0o600); err != nil {
		return "", "", err
	}
	if err := os.WriteFile(keyPath, pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: keyDER}), 0o600); err != nil {
		return "", "", err
	}
	return certPath, keyPath, nil
}

// externalBinaries picks the programs one external stack needs, and says which
// flag is missing when it has not been given them.
//
// The registry names the implementation, so a stack added later asks for its
// own binary rather than for the one the first four happened to use, and an
// implementation shipping one program per side asks for both.
func externalBinaries(kind extproxy.Kind, opts options) (client, server string, err error) {
	switch implementation := kind.Implementation(); implementation {
	case "sing-box":
		if opts.singBox == "" {
			return "", "", fmt.Errorf("stack %q requires a sing-box binary (--sing-box)", kind)
		}
		return opts.singBox, "", nil
	case "kcptun":
		if opts.kcptunClient == "" || opts.kcptunServer == "" {
			return "", "", fmt.Errorf("stack %q requires --kcptun-client and --kcptun-server: kcptun ships one program per side", kind)
		}
		return opts.kcptunClient, opts.kcptunServer, nil
	case "":
		return "", "", fmt.Errorf("stack %q is not a transport this benchmark knows", kind)
	default:
		return "", "", fmt.Errorf("stack %q needs a %s binary, and this benchmark has no flag for one", kind, implementation)
	}
}

// startTCPStack runs a stream-based transport over the TCP relay. Loss is not
// available there: a userspace relay carries a byte stream and cannot drop a
// segment, so the caller is told rather than given a silently lossless result.
func startTCPStack(ctx context.Context, kind extproxy.Kind, opts options, pathCfg pathsim.Config, logger *slog.Logger) (*harness, error) {
	clientBinary, serverBinary, err := externalBinaries(kind, opts)
	if err != nil {
		return nil, err
	}
	if pathCfg.LossRate > 0 || pathCfg.UpstreamLossRate > 0 {
		return nil, fmt.Errorf("stack %q is TCP based and cannot be measured under emulated loss; "+
			"run it with --loss 0 and compare delay and bandwidth only", kind)
	}
	// Reserve a port for the external server, then release it so the external
	// process can bind it itself.
	serverProbe, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return nil, err
	}
	serverAddr := serverProbe.Addr().String()
	_ = serverProbe.Close()

	relay, err := pathsim.NewTCP("127.0.0.1:0", serverAddr, pathCfg)
	if err != nil {
		return nil, err
	}
	socksProbe, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		_ = relay.Close()
		return nil, err
	}
	socksAddr := socksProbe.Addr().String()
	_ = socksProbe.Close()

	h := &harness{socks: socksAddr, relay: relay}
	h.closes = append(h.closes, func() { _ = relay.Close() })

	workDir, err := os.MkdirTemp("", "queqiaobench-"+string(kind)+"-")
	if err != nil {
		h.Close()
		return nil, err
	}
	certPath, keyPath, err := writeCertificateFiles(workDir)
	if err != nil {
		h.Close()
		_ = os.RemoveAll(workDir)
		return nil, err
	}
	pair, err := extproxy.Start(ctx, extproxy.Config{
		Kind: kind, Binary: clientBinary, ServerBinary: serverBinary,
		ServerListen: serverAddr, ClientRemote: relay.LocalAddr(),
		SOCKSListen: socksAddr, CertificatePath: certPath, KeyPath: keyPath,
		WorkDir: workDir, KCP: opts.kcp,
	})
	if err != nil {
		h.Close()
		_ = os.RemoveAll(workDir)
		return nil, err
	}
	h.closes = append(h.closes, pair.Close, func() { _ = os.RemoveAll(workDir) })
	return h, nil
}

// measureContention runs two stacks at the same time through one shared
// bottleneck and reports what fraction of the link each took.
//
// This is the measurement a transport meant to win a contended link needs, and
// no sequential benchmark can supply it: running one stack and then the other
// answers which is faster alone. Both flows start together and are given the
// same object, so the share is read directly off the goodput and the slower one
// is still carrying traffic while the faster one finishes.
func measureContention(opts options, pathCfg pathsim.Config, origin *origin) ([]ContentionRecord, error) {
	stacks := strings.Split(opts.contend, ",")
	if len(stacks) != 2 {
		return nil, errors.New("--contend needs exactly two stacks")
	}
	for i := range stacks {
		stacks[i] = strings.TrimSpace(stacks[i])
	}
	fmt.Printf("# contention on one shared bottleneck: %s vs %s\n", stacks[0], stacks[1])
	fmt.Printf("trial\t%s\t%s\tshare_%s\tratio\n", stacks[0], stacks[1], stacks[0])
	var shares []float64
	var records []ContentionRecord
	for trial := 1; trial <= opts.trials; trial++ {
		cfg := pathCfg
		cfg.Seed = pathCfg.Seed + int64(trial)*1000
		shared := pathsim.NewBottleneck(cfg)

		ctx, cancel := context.WithTimeout(context.Background(), opts.timeout)
		harnesses := make([]*harness, len(stacks))
		failure := ""
		for i, stack := range stacks {
			h, err := startStackOn(ctx, stack, opts, cfg, shared)
			if err != nil {
				fmt.Printf("%d\tsetup %s: %v\n", trial, stack, err)
				failure = fmt.Sprintf("setup %s: %v", stack, err)
				break
			}
			harnesses[i] = h
			if err := warmUp(ctx, h.socks, origin); err != nil {
				fmt.Printf("%d\twarmup %s: %v\n", trial, stack, err)
				failure = fmt.Sprintf("warmup %s: %v", stack, err)
				break
			}
		}
		record := ContentionRecord{Trial: trial, StackA: stacks[0], StackB: stacks[1], Note: failure}
		if failure == "" {
			rates := make([]float64, len(stacks))
			transferErrors := make([]error, len(stacks))
			var wg sync.WaitGroup
			for i := range stacks {
				wg.Add(1)
				go func(i int) {
					defer wg.Done()
					started := time.Now()
					n, err := fetch(ctx, harnesses[i].socks, origin.addr, opts.bytes)
					elapsed := time.Since(started)
					if err == nil && n == opts.bytes && elapsed > 0 {
						rates[i] = float64(n) * 8 / elapsed.Seconds() / 1e6
					} else if err != nil {
						transferErrors[i] = err
					} else {
						transferErrors[i] = fmt.Errorf("received %d of %d bytes", n, opts.bytes)
					}
				}(i)
			}
			wg.Wait()
			total := rates[0] + rates[1]
			share, ratio := 0.0, 0.0
			if total > 0 {
				share = rates[0] / total
			}
			if rates[1] > 0 {
				ratio = rates[0] / rates[1]
			}
			record.MbitsA, record.MbitsB = round3(rates[0]), round3(rates[1])
			record.ShareA, record.RatioAToB = round3(share), round3(ratio)
			if transferErrors[0] == nil && transferErrors[1] == nil {
				record.Complete = true
				shares = append(shares, share)
			} else {
				record.Note = fmt.Sprintf("%s: %v; %s: %v", stacks[0], transferErrors[0], stacks[1], transferErrors[1])
			}
			fmt.Printf("%d\t%.2f\t%.2f\t%.3f\t%.2f\n", trial, rates[0], rates[1], share, ratio)
		}
		records = append(records, record)
		for _, h := range harnesses {
			if h != nil {
				h.Close()
			}
		}
		cancel()
	}
	if len(shares) > 0 {
		sort.Float64s(shares)
		fmt.Printf("\nmedian share of the bottleneck taken by %s: %.3f (0.5 is an even split)\n",
			stacks[0], shares[len(shares)/2])
	}
	return records, nil
}
