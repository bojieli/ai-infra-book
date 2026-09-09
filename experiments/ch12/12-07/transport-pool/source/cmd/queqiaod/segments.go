package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"os"
	"os/exec"
	"strings"
	"time"

	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/pathseg"
)

// The segments command answers the question a slow deployment actually raises,
// which none of the existing instruments answers: not how bad the path is, but
// whose fault it is.
//
// queqiaod doctor checks preconditions and gateway placement. cmd/pathprobe
// finds a capacity knee and an erasure floor. cmd/pathmeasure says what a stack
// achieves. All three describe a path end to end, so a deployment that is
// losing a seventh of what crosses it learns that it is losing a seventh and
// nothing about where. The three candidates need different responses and only
// one of them is this project's problem: a lossy first mile is the client's
// ISP, a lossy gateway transit is past the point where this transport stops,
// and a lossy long haul between them is the one thing coding and pacing repair.
//
// The separation comes from measuring the same minutes from two vantage points
// against anchors chosen so that each leg's loss can only have come from one
// place. See internal/pathseg for the shared-element argument that makes the
// legs add up, and why the anchors have to be local and unfiltered at the
// vantage point that probes them.
//
// The gateway vantage point is optional and the report is honest about what it
// cannot conclude without one: with only the client's side measured, a clean
// report does not clear the gateway's transit, it merely never looked at it.

// defaultReferences are deliberately one Chinese and one global anchor, used
// unchanged at both ends.
//
// A probe from a filtered network to a filtered destination measures the
// filter. Read as loss it would convict a healthy access link of the worst
// fault this report can report, which on the path this project was built for is
// not a hypothetical: a client in China probing a blocked host sees near-total
// loss on a first mile in perfect health.
//
// Rather than guess where a vantage point is -- which needs a geolocation table
// that would then be wrong somewhere -- both anchors are probed from both ends
// and each end's link is judged by whichever answered cleanly. One clean anchor
// proves the link carries traffic. That makes the defaults correct in both
// directions without knowing which side of the filter anything is on, and it
// makes the disagreement between the two anchors a finding in its own right
// rather than noise to be averaged away.
var defaultReferences = []string{"baidu.com:443", "www.google.com:443"}

type segmentOptions struct {
	endpoint     string
	socks        string
	metrics      string
	localAddress string

	clientRefs   stringList
	gatewayRefs  stringList
	destinations stringList

	sshTarget     string
	sshOptions    stringList
	remoteBinary  string
	remoteMetrics string

	count          int
	establishCount int
	interval       time.Duration
	timeout        time.Duration
	pin            bool
	quiet          bool
}

// segmentReport is the whole run, and the JSON form is the whole run too. A
// report that printed more than it serialised would make the machine-readable
// output the lesser of the two, which is the wrong way round for something
// whose results are meant to be attached to a bug.
type segmentReport struct {
	Version     string              `json:"version"`
	StartedAt   time.Time           `json:"started_at"`
	ElapsedS    float64             `json:"elapsed_seconds"`
	Gateway     string              `json:"gateway_endpoint,omitempty"`
	SSHTarget   string              `json:"ssh_target,omitempty"`
	RemoteHost  string              `json:"remote_hostname,omitempty"`
	Probes      int                 `json:"probes"`
	IntervalMS  int                 `json:"interval_ms"`
	Evidence    pathseg.Evidence    `json:"evidence"`
	Attribution pathseg.Attribution `json:"attribution"`
	Notes       []string            `json:"notes,omitempty"`
}

func runSegmentsCommand(args []string) error {
	fs := newFlagSet("segments")
	agent := fs.Bool("agent", false,
		"run the far-side half of a profile: read a request on stdin, measure, write the result on stdout. "+
			"This is what --ssh invokes on the gateway; it is not normally run by hand")
	profilePath := fs.String("profile", "", "client profile to read the gateway endpoint from")
	asJSON := fs.Bool("json", false, "emit the report as JSON")

	var opts segmentOptions
	fs.StringVar(&opts.endpoint, "endpoint", "", "gateway host:port, when no client profile is available")
	fs.StringVar(&opts.socks, "socks", "127.0.0.1:12080", "local SOCKS5 listener, for the tunnelled arm")
	fs.StringVar(&opts.metrics, "metrics", "",
		"the running client's metrics URL, such as http://127.0.0.1:19090/metrics. This is the only "+
			"per-direction measurement of the client-to-gateway segment there is; without it that "+
			"segment is reduced to a round-trip probe")
	fs.StringVar(&opts.localAddress, "local-address", "",
		"bind probes to this local IP, so a host TUN route does not carry a direct measurement through "+
			"the very tunnel being measured")
	fs.Var(&opts.clientRefs, "client-reference",
		"a destination that is local and unfiltered from the client, to establish its own link; repeat for several")
	fs.Var(&opts.gatewayRefs, "gateway-reference",
		"the same for the gateway, whose local and unfiltered destinations are usually different ones")
	fs.Var(&opts.destinations, "destination",
		"a destination you actually care about, compared direct against tunnelled; repeat for several")
	fs.StringVar(&opts.sshTarget, "ssh", "",
		"ssh into the gateway to measure its own transit, instead of inferring it by subtraction. "+
			"Takes anything ssh takes, such as user@host or a Host alias from ssh_config")
	fs.Var(&opts.sshOptions, "ssh-option", "extra argument to pass to ssh; repeat for several")
	fs.StringVar(&opts.remoteBinary, "remote-binary", "queqiaod",
		"path to queqiaod on the gateway, which runs the far half of the measurement")
	fs.StringVar(&opts.remoteMetrics, "remote-metrics", "",
		"the gateway's metrics URL as reachable from the gateway itself, such as http://127.0.0.1:19090/metrics")
	fs.IntVar(&opts.count, "count", 50, "echo probes per leg")
	fs.IntVar(&opts.establishCount, "establish-count", 3, "connections per leg, the reachability instrument")
	fs.DurationVar(&opts.interval, "interval", 100*time.Millisecond, "time between probes")
	fs.DurationVar(&opts.timeout, "timeout", 2*time.Second, "how long to wait for a straggler after the last probe")
	fs.BoolVar(&opts.quiet, "quiet", false,
		"do not report progress while measuring. Progress goes to stderr, so it never contaminates "+
			"--json on stdout; this is for a log that should hold only the result")
	fs.BoolVar(&opts.pin, "pin-addresses", false,
		"make the gateway measure the addresses this client resolved, rather than resolving for itself. "+
			"Pins the comparison to one machine, at the cost of hiding a name that resolves differently "+
			"at each end -- which is itself worth knowing")
	if err := fs.Parse(args); err != nil {
		return err
	}

	if *agent {
		return runSegmentsAgent(os.Stdin, os.Stdout)
	}
	if opts.count < 1 {
		return errors.New("--count must be at least 1")
	}
	if opts.interval <= 0 {
		return errors.New("--interval must be positive")
	}
	if len(opts.clientRefs) == 0 {
		opts.clientRefs = defaultReferences
	}
	if len(opts.gatewayRefs) == 0 {
		opts.gatewayRefs = defaultReferences
	}
	if opts.endpoint == "" && *profilePath != "" {
		p, err := identity.LoadClientProfile(*profilePath)
		if err != nil {
			return fmt.Errorf("read client profile: %w", err)
		}
		opts.endpoint = p.Endpoint
	}
	if opts.endpoint == "" {
		return errors.New("the gateway is not known: pass --endpoint or --profile")
	}

	report, err := profileSegments(context.Background(), opts)
	if err != nil {
		return err
	}
	if *asJSON {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}
	renderSegments(os.Stdout, report)
	return nil
}

// runSegmentsAgent is the far half. It writes JSON on stdout and nothing else,
// because stdout is a pipe back through ssh; anything friendly printed here
// would arrive as a parse error on the other end.
func runSegmentsAgent(in io.Reader, out io.Writer) error {
	req, err := pathseg.DecodeAgentRequest(in)
	if err != nil {
		return fmt.Errorf("read the measurement request: %w", err)
	}
	budget := time.Duration(req.Count)*time.Duration(req.IntervalMS)*time.Millisecond*
		time.Duration(len(req.References)) + 2*time.Minute
	ctx, cancel := context.WithTimeout(context.Background(), budget)
	defer cancel()
	resp := pathseg.RunAgent(ctx, req, version)
	return json.NewEncoder(out).Encode(resp)
}

// progress narrates a run while it happens.
//
// A profile takes tens of seconds per leg and minutes once --ssh and several
// destinations are involved, all of it spent waiting on probes that produce no
// output. Silence for that long is indistinguishable from a hang, and an
// operator who cannot tell the difference kills the run and never sees the
// verdict.
//
// It writes to stderr so that --json on stdout stays machine-readable with the
// narration still visible, which is the arrangement that needs no flag to be
// safe in a pipeline.
type progress struct {
	w     io.Writer
	on    bool
	step  int
	total int
}

func (p *progress) notef(format string, args ...any) {
	if !p.on {
		return
	}
	fmt.Fprintf(p.w, "  "+format+"\n", args...)
}

// begin announces a leg and returns the function that closes it out, so the
// two halves of one line cannot drift apart.
func (p *progress) begin(vantage, target string) func(string) {
	if !p.on {
		return func(string) {}
	}
	p.step++
	started := time.Now()
	fmt.Fprintf(p.w, "  [%d/%d] %s -> %-28s ", p.step, p.total, vantage, target)
	return func(result string) {
		fmt.Fprintf(p.w, "%-24s (%.1fs)\n", result, time.Since(started).Seconds())
	}
}

// summarizeReference is the one-line form of a finished leg, which is the
// figure the verdict will rest on rather than a restatement of the request.
func summarizeReference(r pathseg.Reference) string {
	if r.Error != "" {
		return "failed"
	}
	health, ok := r.Health()
	switch {
	case !ok:
		return "no reply"
	case r.Filtered():
		return "echo ok, handshake refused"
	case health.Loss > 0:
		return fmt.Sprintf("%.1f%% loss, %.0fms", health.Loss*100, health.P50MS)
	default:
		return fmt.Sprintf("clean, %.0fms", health.P50MS)
	}
}

func profileSegments(ctx context.Context, opts segmentOptions) (segmentReport, error) {
	started := time.Now()
	report := segmentReport{
		Version: version, StartedAt: started.UTC(), Gateway: opts.endpoint,
		SSHTarget: opts.sshTarget, Probes: opts.count,
		IntervalMS: int(opts.interval / time.Millisecond),
	}

	// One budget for the whole run, sized from what was asked for rather than
	// from a constant, so a long run is not cut off in the middle and a short
	// one does not sit waiting on a hung ssh.
	legs := len(opts.clientRefs) + len(opts.destinations) + 1
	budget := time.Duration(legs)*(time.Duration(opts.count)*opts.interval+opts.timeout) + 3*time.Minute
	ctx, cancel := context.WithTimeout(ctx, budget)
	defer cancel()

	perLeg := time.Duration(opts.count)*opts.interval + opts.timeout
	prog := &progress{w: os.Stderr, on: !opts.quiet, total: 1 + len(opts.clientRefs) + len(opts.destinations)}
	prog.notef("profiling %s: %d legs from the client at about %.0fs each",
		opts.endpoint, prog.total, perLeg.Seconds())

	cfg := pathseg.ProbeConfig{
		Count: opts.count, Interval: opts.interval, Timeout: opts.timeout,
		EstablishCount: opts.establishCount, LocalAddress: opts.localAddress,
	}

	// The far side starts first and runs while the near side measures, so both
	// vantage points cover the same minutes. This is not an optimisation. The
	// path this project was built for moves between roughly zero and seventeen
	// percent loss within minutes, so two legs measured one after the other can
	// differ by more than any fault would move them, and the whole
	// shared-element argument rests on the legs being comparable.
	type remoteResult struct {
		resp  pathseg.AgentResponse
		notes []string
	}
	remote := make(chan remoteResult, 1)
	if opts.sshTarget != "" {
		req := pathseg.AgentRequest{
			References: opts.gatewayRefs, Count: opts.count,
			IntervalMS:     int(opts.interval / time.Millisecond),
			TimeoutMS:      int(opts.timeout / time.Millisecond),
			EstablishCount: opts.establishCount, MetricsURL: opts.remoteMetrics,
		}
		prog.notef("gateway vantage: ssh %s, %d legs running alongside these",
			opts.sshTarget, len(opts.gatewayRefs))
		go func() {
			resp, notes := measureFromGateway(ctx, opts, req)
			remote <- remoteResult{resp, notes}
		}()
	}

	var e pathseg.Evidence
	e.Gateway = measureWithProgress(ctx, "client", []string{opts.endpoint}, cfg, prog)[0]
	e.ClientReferences = measureWithProgress(ctx, "client", opts.clientRefs, cfg, prog)

	if opts.metrics != "" {
		view, err := pathseg.FetchMetrics(ctx, opts.metrics)
		if err != nil {
			prog.notef("metrics: %s could not be read", opts.metrics)
			report.Notes = append(report.Notes, fmt.Sprintf(
				"the client's metrics at %s could not be read (%v), so the client-to-gateway segment "+
					"falls back to a round-trip probe that cannot separate the two directions",
				opts.metrics, err))
		} else {
			e.Tunnel = view
			prog.notef("metrics: %.1f%% receive erasure, %.1f%% send, over %d coded symbols",
				view.ReceiveErasure*100, view.SendErasure*100, view.CodedSymbols)
		}
	} else {
		report.Notes = append(report.Notes,
			"no --metrics URL was given. The running client publishes the per-direction erasure of the "+
				"client-to-gateway segment on --metrics-listen, and it is a better measurement of that "+
				"segment than anything this command can probe from outside")
	}

	e.Direct, e.Tunneled = compareDestinations(ctx, opts, prog)

	if opts.sshTarget != "" {
		if len(opts.destinations) == 0 {
			prog.notef("waiting for the gateway's legs to finish")
		}
		select {
		case res := <-remote:
			prog.notef("gateway vantage: %d legs returned", len(res.resp.References))
			report.Notes = append(report.Notes, res.notes...)
			report.RemoteHost = res.resp.Hostname
			e.GatewayReferences = res.resp.References
			for i := range e.GatewayReferences {
				e.GatewayReferences[i].Echo.From = "gateway"
				e.GatewayReferences[i].Establish.From = "gateway"
			}
			e.Remote = res.resp.Metrics
			e.GatewayVantage = len(res.resp.References) > 0
			if res.resp.MetricsError != "" {
				report.Notes = append(report.Notes,
					"the gateway's metrics could not be read: "+res.resp.MetricsError)
			}
		case <-ctx.Done():
			report.Notes = append(report.Notes, "the gateway-side measurement did not finish in time")
		}
	}

	report.Evidence = e
	report.Attribution = pathseg.Attribute(e)
	report.ElapsedS = time.Since(started).Round(time.Millisecond).Seconds()
	return report, nil
}

// measureWithProgress drives the anchor loop here rather than inside the
// package, so that each leg is announced before it is waited on.
func measureWithProgress(ctx context.Context, vantage string, targets []string,
	cfg pathseg.ProbeConfig, prog *progress) []pathseg.Reference {
	out := make([]pathseg.Reference, 0, len(targets))
	for _, target := range targets {
		done := prog.begin(vantage, target)
		r := pathseg.MeasureReference(ctx, target, cfg)
		r.Echo.From, r.Establish.From = vantage, vantage
		done(summarizeReference(r))
		out = append(out, r)
	}
	return out
}

// compareDestinations compares each destination direct against tunnelled, one
// establishment at a time with the arms alternated.
//
// The alternation is not optional. This project has already paid for the
// lesson: on the characterised path, position in the test sequence was worth
// 158ms where the policy under test was worth 2.4ms, and running one arm to
// completion before the other produced a 53% win that reversed when the order
// flipped. Running each arm as a block here would measure the path's drift and
// call it the tunnel's contribution.
func compareDestinations(ctx context.Context, opts segmentOptions, prog *progress) (direct, tunneled []pathseg.Leg) {
	for _, target := range opts.destinations {
		done := prog.begin("client", target)
		var d, t pathseg.Sequence
		for round := 0; round < opts.establishCount; round++ {
			one := func(socks string) pathseg.Sequence {
				return pathseg.Establish(ctx, pathseg.EstablishOptions{
					Target: withDefaultPort(target), LocalAddress: opts.localAddress,
					SOCKS: socks, Count: 1, Timeout: opts.timeout + 3*time.Second,
				})
			}
			first, second := "", opts.socks
			directFirst := round%2 == 0
			if !directFirst {
				first, second = opts.socks, ""
			}
			a, b := one(first), one(second)
			if !directFirst {
				a, b = b, a
			}
			d.Arrived, d.RTTs = append(d.Arrived, a.Arrived...), append(d.RTTs, a.RTTs...)
			t.Arrived, t.RTTs = append(t.Arrived, b.Arrived...), append(t.RTTs, b.RTTs...)
		}
		dl := pathseg.Summarize("direct:"+target, "client", target, "tcp-connect", d)
		tl := pathseg.Summarize("tunnelled:"+target, "client", target, "tcp-connect", t)
		done(fmt.Sprintf("%s direct, %s tunnelled", establishSummary(dl), establishSummary(tl)))
		direct = append(direct, dl)
		tunneled = append(tunneled, tl)
	}
	return direct, tunneled
}

func establishSummary(l pathseg.Leg) string {
	if !l.Usable() {
		return "unreachable"
	}
	return fmt.Sprintf("%.0fms", l.P50MS)
}

// splitHostForResolve returns the host part of a reference, which may or may
// not carry a port.
func splitHostForResolve(target string) (string, bool) {
	if h, _, err := net.SplitHostPort(target); err == nil {
		return h, true
	}
	return target, false
}

func withDefaultPort(target string) string {
	if _, _, err := net.SplitHostPort(target); err == nil {
		return target
	}
	return net.JoinHostPort(target, "443")
}

// measureFromGateway runs the far half over ssh.
//
// It shells out to the system ssh rather than speaking the protocol itself, so
// that the operator's own config, agent, keys and known_hosts decide what
// happens. A diagnostic tool is the last place that should grow its own idea of
// how to authenticate to a host, and no key material passes through this
// process as a result.
func measureFromGateway(ctx context.Context, opts segmentOptions, req pathseg.AgentRequest) (pathseg.AgentResponse, []string) {
	payload, err := json.Marshal(req)
	if err != nil {
		return pathseg.AgentResponse{}, []string{"could not encode the gateway request: " + err.Error()}
	}
	remote := shellQuote(opts.remoteBinary) + " segments --agent"
	out, stderr, err := runSSH(ctx, opts, bytes.NewReader(payload), remote)
	if err == nil {
		var resp pathseg.AgentResponse
		if jsonErr := json.Unmarshal(out, &resp); jsonErr == nil && len(resp.References) > 0 {
			var notes []string
			if resp.Version != version {
				notes = append(notes, fmt.Sprintf(
					"the gateway runs queqiaod %s and this client runs %s; both ends measured with their "+
						"own build", resp.Version, version))
			}
			return resp, notes
		}
	}

	// The remote binary is missing, too old, or not on the path. Fall back to
	// ping, and say so: the fallback gives up the one property that made the
	// two vantage points comparable, which is that they ran the same code.
	notes := []string{fmt.Sprintf(
		"%s on the gateway could not run the agent (%s), so its legs were measured with ping instead. "+
			"That loses the per-packet order, so no loss pattern is reported for them, and the two "+
			"vantage points are no longer running one instrument. Install a matching queqiaod there, "+
			"or point --remote-binary at it",
		opts.remoteBinary, firstLine(stderr, err))}
	refs, pingNotes := measureFromGatewayWithPing(ctx, opts, req)
	return pathseg.AgentResponse{References: refs}, append(notes, pingNotes...)
}

func measureFromGatewayWithPing(ctx context.Context, opts segmentOptions, req pathseg.AgentRequest) ([]pathseg.Reference, []string) {
	var refs []pathseg.Reference
	var notes []string
	// iputils refuses an interval below 200ms to an unprivileged caller, and a
	// run that is refused measures nothing at all, so the fallback slows down
	// rather than failing.
	interval := time.Duration(req.IntervalMS) * time.Millisecond
	if interval < 200*time.Millisecond {
		interval = 200 * time.Millisecond
	}
	for _, target := range req.References {
		host := target
		if h, _, err := net.SplitHostPort(target); err == nil {
			host = h
		}
		cmd := fmt.Sprintf("ping -n -q -c %d -i %.1f %s", req.Count, interval.Seconds(), shellQuote(host))
		out, stderr, err := runSSH(ctx, opts, nil, cmd)
		ref := pathseg.Reference{Target: target}
		if err != nil && len(out) == 0 {
			ref.Error = firstLine(stderr, err)
			notes = append(notes, fmt.Sprintf("ping to %s from the gateway failed: %s", target, ref.Error))
			refs = append(refs, ref)
			continue
		}
		leg, parseErr := parsePingSummary(string(out), target)
		if parseErr != nil {
			ref.Error = parseErr.Error()
		}
		leg.From, leg.To = "gateway", target
		ref.Echo = leg
		refs = append(refs, ref)
	}
	return refs, notes
}

func runSSH(ctx context.Context, opts segmentOptions, stdin io.Reader, remote string) ([]byte, string, error) {
	// BatchMode is not a hardening choice but a correctness one: stdin carries
	// the measurement request, so ssh has nowhere to read a password from and a
	// prompt would hang until the run's deadline rather than fail.
	//
	// The operator's own options go first because ssh takes the first value it
	// obtains for any parameter, so anything set here before them could not be
	// overridden from the command line.
	args := append([]string{}, opts.sshOptions...)
	args = append(args, "-o", "BatchMode=yes", "-o", "ConnectTimeout=10")
	args = append(args, opts.sshTarget, "--", remote)
	// #nosec G204 -- ssh is a fixed program name, and its arguments are this
	// operator's own flags rather than anything read from the network. The
	// remote command is shell-quoted because ssh runs it through a shell.
	cmd := exec.CommandContext(ctx, "ssh", args...)
	cmd.Stdin = stdin
	var stdout, stderr bytes.Buffer
	cmd.Stdout, cmd.Stderr = &stdout, &stderr
	err := cmd.Run()
	return stdout.Bytes(), stderr.String(), err
}

// shellQuote wraps a value so that the remote shell sees it as one word. ssh
// hands the command to a shell on the far side, so a path with a space in it
// would otherwise arrive as two arguments.
func shellQuote(s string) string {
	return "'" + strings.ReplaceAll(s, "'", `'\''`) + "'"
}

func firstLine(stderr string, err error) string {
	for _, line := range strings.Split(stderr, "\n") {
		if trimmed := strings.TrimSpace(line); trimmed != "" {
			return trimmed
		}
	}
	if err != nil {
		return err.Error()
	}
	return "no output"
}
