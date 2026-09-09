package main

import (
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"net"
	"os"
	"runtime"
	"strings"
	"time"

	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/profile"
)

// doctor answers the two questions a deployment gets wrong before it exists:
// whether this host is in the state the measurements assumed, and whether this
// gateway sits on the useful side of this client's path to the destinations it
// actually calls.
//
// The host half exists because the deployment guide's first instruction is to
// do the free things first, and on a clean path direction those are worth as
// much as the transport. Measured on the China-US path the datacenter profile
// was built for, a client that reuses its connection and sets
// tcp_slow_start_after_idle=0 takes a real 355KB inference upload to 240.9ms,
// against 236.5ms through the tunnel in the same minutes. Both are within ten
// milliseconds of the floor a 197ms round trip and a 30ms model impose, so on a
// warm connection over a clean direction the two are the same answer and the
// config line is the cheaper way to get it. An operator who deploys without
// doing that is paying for a tunnel to reach a figure a sysctl already reached,
// and nothing in the system told them.
//
// Those figures replace the 225.8ms and 295.0ms this comment used to quote.
// The originals were medians across eight audio files labelled with the size of
// whichever request ran last, which pulled the median below the floor that size
// has on a 200ms path, and correcting them reversed the sign of the difference.
// See docs/PATH-CHARACTER-DC-20260826.md, "Re-measured with one fixed file".
//
// The placement half exists because no host check can reach it and no document
// can answer it for a particular destination. This transport improves the
// client-to-gateway segment and nothing past it, so a gateway sited on the
// wrong side of the traffic's real bottleneck lengthens the path while every
// local check still passes. See doctor_probe.go for what is measured and why
// it stops at connection establishment.
//
// So the checks are the preconditions rather than the plumbing. Whether the
// gateway answers matters less than whether the host is in the state the
// measurements assumed and whether the gateway is where the traffic needs it,
// because a gateway that does not answer is obvious and neither of the other
// two is.

type check struct {
	Name   string `json:"name"`
	Status string `json:"status"`
	Detail string `json:"detail"`
}

type report struct {
	Version      string             `json:"version"`
	OS           string             `json:"os"`
	Arch         string             `json:"arch"`
	Profile      string             `json:"path_profile"`
	CheckedAt    time.Time          `json:"checked_at"`
	OK           bool               `json:"ok"`
	Checks       []check            `json:"checks"`
	Gateway      *latency           `json:"gateway_rtt,omitempty"`
	Destinations []destinationProbe `json:"destinations,omitempty"`
}

func runDoctorCommand(args []string) error {
	fs := flag.NewFlagSet("doctor", flag.ContinueOnError)
	profilePath := fs.String("profile", "", "client profile to check, for the gateway endpoint")
	pathProfile := fs.String("path-profile", "", "path profile to check against, empty for the default")
	endpoint := fs.String("endpoint", "", "gateway host:port, when no client profile is available")
	socksAddr := fs.String("socks", "127.0.0.1:12080", "local SOCKS5 listener to compare destinations through")
	rounds := fs.Int("rounds", 5, "round pairs per destination; each pair runs both arms in both orders")
	asJSON := fs.Bool("json", false, "emit the report as JSON")
	timeout := fs.Duration("timeout", 10*time.Second, "per-check timeout")
	var destinations stringList
	fs.Var(&destinations, "destination", "destination host:port to check this gateway's placement against; repeat for several")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *rounds < 1 {
		return errors.New("--rounds must be at least 1")
	}

	selected, err := profile.ByName(*pathProfile)
	if err != nil {
		return err
	}
	r := report{
		Version: version, OS: runtime.GOOS, Arch: runtime.GOARCH,
		Profile: selected.Name, CheckedAt: time.Now().UTC(), OK: true,
	}
	r.Checks = append(r.Checks, checkProfile(selected))
	r.Checks = append(r.Checks, hostChecks(selected)...)

	target := *endpoint
	if target == "" && *profilePath != "" {
		p, loadErr := identity.LoadClientProfile(*profilePath)
		if loadErr != nil {
			r.Checks = append(r.Checks, check{Name: "client_profile", Status: "fail", Detail: loadErr.Error()})
		} else {
			r.Checks = append(r.Checks, check{Name: "client_profile", Status: "pass",
				Detail: fmt.Sprintf("%s via %s", p.Name, p.Endpoint)})
			target = p.Endpoint
		}
	}
	if target != "" {
		ctx, cancel := context.WithTimeout(context.Background(), *timeout)
		r.Checks = append(r.Checks, checkReachable(ctx, target)...)
		r.Checks = append(r.Checks, measureGateway(ctx, target, *rounds, &r)...)
		cancel()
	} else {
		r.Checks = append(r.Checks, check{Name: "gateway", Status: "warn",
			Detail: "no --profile or --endpoint given, so nothing was dialled"})
	}

	if len(destinations) > 0 {
		r.Checks = append(r.Checks, measureDestinations(destinations, *socksAddr, *rounds, *timeout, &r)...)
	}

	for _, c := range r.Checks {
		if c.Status == "fail" {
			r.OK = false
		}
	}
	if *asJSON {
		encoder := json.NewEncoder(os.Stdout)
		encoder.SetIndent("", "  ")
		if err := encoder.Encode(r); err != nil {
			return err
		}
	} else {
		printReport(r)
	}
	if !r.OK {
		return errors.New("one or more checks failed")
	}
	return nil
}

// measureGateway records the round trip every tunnelled flow pays before it
// reaches anything. It is reported for its own sake and kept on the report so
// that a destination probe can subtract it and leave the gateway's own hop.
func measureGateway(ctx context.Context, endpoint string, rounds int, r *report) []check {
	got, err := probeGateway(ctx, endpoint, rounds)
	if err != nil {
		return []check{{Name: "gateway_rtt", Status: "warn",
			Detail: fmt.Sprintf("no round trip could be measured: %v", err)}}
	}
	r.Gateway = &got
	return []check{{Name: "gateway_rtt", Status: "pass",
		Detail: fmt.Sprintf("%s, paid once per flow setup before the destination is reached", got)}}
}

// measureDestinations runs the placement comparison for each destination named.
//
// Each destination gets its own timeout budget rather than sharing one, because
// a first destination that is slow to answer should delay the report rather
// than silently truncate the samples of the ones behind it.
func measureDestinations(targets []string, socksAddr string, rounds int, timeout time.Duration, r *report) []check {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	listener := checkSOCKSListener(ctx, socksAddr)
	cancel()
	out := []check{listener}
	if listener.Status != "pass" {
		return out
	}
	for _, t := range targets {
		// Two arms, two orders, plus the discarded warm-up, each of which may
		// have to time out on its own before the next is tried.
		budget := timeout * time.Duration(4*rounds+2)
		ctx, cancel := context.WithTimeout(context.Background(), budget)
		gateway := latency{}
		if r.Gateway != nil {
			gateway = *r.Gateway
		}
		p := probeDestination(ctx, t, socksAddr, rounds, gateway)
		cancel()
		r.Destinations = append(r.Destinations, p)
		out = append(out, checkPlacement(p))
	}
	return out
}

func printReport(r report) {
	fmt.Printf("queqiao doctor  profile=%s  %s/%s\n\n", r.Profile, r.OS, r.Arch)
	for _, c := range r.Checks {
		mark := "ok  "
		switch c.Status {
		case "fail":
			mark = "FAIL"
		case "warn":
			mark = "warn"
		}
		// The pad is a minimum, not a maximum: a name longer than it still
		// prints in full and the detail wraps from wherever that left the
		// cursor, so no check is renamed to fit a column.
		width := detailColumn
		if len(c.Name) > width {
			width = len(c.Name)
		}
		fmt.Printf("  %s  %-*s %s\n", mark, detailColumn, c.Name,
			indentWrap(c.Detail, markColumns+width+1, markColumns+detailColumn+1, 78))
	}
	for _, d := range r.Destinations {
		printDestination(d)
	}
	fmt.Println()
	if r.OK {
		fmt.Println("No failures. A pass here is a host in the state the measurements assumed and a")
		fmt.Println("gateway placed where the destinations checked can use it, not a promise about")
		fmt.Println("the path: run cmd/pathprobe to learn what the path does.")
		return
	}
	fmt.Println("Something above will not behave the way the deployment guide assumes.")
}

// printDestination puts the samples beside the verdict, because a reader who
// disagrees with the verdict should be able to see what produced it without
// re-running the command with --json.
func printDestination(d destinationProbe) {
	handshake := "connect only"
	if d.TLS {
		handshake = "connect and TLS handshake"
	}
	fmt.Printf("\ndestination  %s  (%s)\n", d.Target, handshake)
	fmt.Printf("  arm       n   min_ms   p50_ms   p99_ms\n")
	printArm("direct", d.Direct)
	printArm("tunnel", d.Tunneled)
	if d.Direct.N > 0 && d.Tunneled.N > 0 {
		fmt.Printf("  # arm effect %.1fms, order effect %.1fms\n", d.ArmEffect, d.OrderEffect)
	}
	if d.Decomposed {
		fmt.Printf("  # tunnelled = %.1fms to the gateway + %.1fms onward (derived, not measured)\n",
			d.GatewayLeg, d.FarLeg)
	}
}

func printArm(name string, l latency) {
	if l.N == 0 {
		fmt.Printf("  %-8s  0       --       --       --\n", name)
		return
	}
	fmt.Printf("  %-8s %2d %8.1f %8.1f %8.1f\n", name, l.N, l.Min, l.P50, l.P99)
}

// markColumns is the width of the two-space, four-character, two-space status
// prefix each check line begins with, and detailColumn is the width the check
// name is padded to after it. A detail begins one column past the name.
const (
	markColumns  = 8
	detailColumn = 24
)

// indentWrap folds a long detail into the column its first line started in.
//
// The details carry the reasoning an operator needs in order to act on a
// check, so they are long by design; a terminal that folds them at column zero
// puts that reasoning underneath the check names, where it reads as a separate
// check. firstCol and indent are given separately because a check whose name
// overruns the pad starts its detail further right than the block it wraps
// into.
func indentWrap(s string, firstCol, indent, width int) string {
	// A minimum usable width. A name long enough to push the first line under
	// it gives that line up entirely and the detail starts on the next one,
	// because a four-column ribbon down the right margin is worse to read than
	// one wasted line.
	const minWidth = 20
	budget := func(col int) int {
		if n := width - col; n >= minWidth {
			return n
		}
		return minWidth
	}
	limit := budget(firstCol)
	var out strings.Builder
	line := 0
	for i, word := range strings.Fields(s) {
		switch {
		case i == 0 && width-firstCol < minWidth:
			out.WriteString("\n" + strings.Repeat(" ", indent) + word)
			limit, line = budget(indent), len(word)
		case i == 0:
			out.WriteString(word)
			line = len(word)
		case line+1+len(word) <= limit:
			out.WriteString(" " + word)
			line += 1 + len(word)
		default:
			out.WriteString("\n" + strings.Repeat(" ", indent) + word)
			limit, line = budget(indent), len(word)
		}
	}
	return out.String()
}

// checkProfile reports what was selected and how far it has been qualified,
// because an experimental profile qualified on one path is a different claim
// from the default one and the difference should not live only in a document.
func checkProfile(p profile.Profile) check {
	status := "pass"
	detail := fmt.Sprintf("%s (%s)", p.Name, p.Level)
	if p.Level != profile.LevelSupported {
		status = "warn"
		detail = fmt.Sprintf("%s is %s. Precondition: %s. Evidence: %s",
			p.Name, p.Level, p.Precondition, p.Evidence)
	}
	return check{Name: "path_profile", Status: status, Detail: detail}
}

// checkReachable dials the gateway both ways the transport can use it. A host
// where QUIC is blocked and TCP is not still works, on the fallback, and an
// operator seeing the latency that implies should be told which one they got.
func checkReachable(ctx context.Context, endpoint string) []check {
	out := make([]check, 0, 2)
	var dialer net.Dialer
	conn, err := dialer.DialContext(ctx, "tcp", endpoint)
	if err != nil {
		out = append(out, check{Name: "gateway_tcp", Status: "fail", Detail: err.Error()})
	} else {
		_ = conn.Close()
		out = append(out, check{Name: "gateway_tcp", Status: "pass", Detail: endpoint})
	}
	// A UDP dial does not prove the far side answers, only that the local
	// stack has a route and nothing refused the socket outright. Saying so is
	// better than implying a handshake that did not happen.
	udp, err := dialer.DialContext(ctx, "udp", endpoint)
	if err != nil {
		out = append(out, check{Name: "gateway_udp", Status: "warn",
			Detail: fmt.Sprintf("%v; the transport would fall back to TCP", err)})
	} else {
		_ = udp.Close()
		out = append(out, check{Name: "gateway_udp", Status: "pass",
			Detail: "a route exists; this does not prove the gateway answered"})
	}
	return out
}

// readSysctl is a file read rather than a shell out, so it behaves the same
// under a service manager that gives the process no PATH.
func readSysctl(name string) (string, error) {
	data, err := os.ReadFile("/proc/sys/" + name)
	if err != nil {
		return "", err
	}
	return string(trimTrailingNewline(data)), nil
}

func trimTrailingNewline(b []byte) []byte {
	for len(b) > 0 && (b[len(b)-1] == '\n' || b[len(b)-1] == '\r' || b[len(b)-1] == ' ' || b[len(b)-1] == '\t') {
		b = b[:len(b)-1]
	}
	return b
}
