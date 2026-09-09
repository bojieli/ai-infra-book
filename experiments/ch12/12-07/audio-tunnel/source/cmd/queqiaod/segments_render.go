package main

import (
	"fmt"
	"io"
	"regexp"
	"strconv"
	"strings"
	"text/tabwriter"

	"github.com/bojieli/queqiao/internal/pathseg"
)

// pingSummary and pingTiming match the two lines every ping(8) worth parsing
// prints, across iputils and the BSD family: the counts, and the timing.
//
// Only the summary is available this way. ping -q reports what happened but not
// in what order, so a run parsed from it has a loss rate and no loss pattern,
// and the difference between an erasure channel and a policer -- which is the
// difference between compensating and backing off -- cannot be read from it at
// all. That is the cost of the fallback, and the report says so where it is used.
var (
	pingSummary = regexp.MustCompile(`(\d+) packets transmitted, (\d+)( packets)? received`)
	pingTiming  = regexp.MustCompile(`(?:rtt|round-trip) min/avg/max(?:/[a-z]+)? = ([0-9.]+)/([0-9.]+)/([0-9.]+)`)
)

func parsePingSummary(out, target string) (pathseg.Leg, error) {
	leg := pathseg.Leg{Name: "echo:" + target, To: target, Method: "ping-summary"}
	m := pingSummary.FindStringSubmatch(out)
	if m == nil {
		return leg, fmt.Errorf("could not read a ping summary from the gateway's output")
	}
	sent, err := strconv.Atoi(m[1])
	if err != nil {
		return leg, err
	}
	received, err := strconv.Atoi(m[2])
	if err != nil {
		return leg, err
	}
	leg.Sent, leg.Arrived = sent, received
	if sent > 0 {
		leg.Loss = float64(sent-received) / float64(sent)
	}
	if received == 0 {
		leg.Blocked = true
		return leg, nil
	}
	if t := pingTiming.FindStringSubmatch(out); t != nil {
		min, _ := strconv.ParseFloat(t[1], 64)
		avg, _ := strconv.ParseFloat(t[2], 64)
		max, _ := strconv.ParseFloat(t[3], 64)
		leg.MinMS, leg.MeanMS, leg.P99MS = min, avg, max
	}
	return leg, nil
}

func renderSegments(w io.Writer, r segmentReport) {
	fmt.Fprintf(w, "queqiao path segment profile — queqiaod %s\n", r.Version)
	fmt.Fprintf(w, "  started        %s (took %.1fs)\n", r.StartedAt.Format("2006-01-02T15:04:05Z"), r.ElapsedS)
	fmt.Fprintf(w, "  gateway        %s\n", r.Gateway)
	if r.SSHTarget != "" {
		host := r.RemoteHost
		if host == "" {
			host = "unnamed"
		}
		fmt.Fprintf(w, "  far vantage    ssh %s (%s)\n", r.SSHTarget, host)
	} else {
		fmt.Fprintf(w, "  far vantage    none. Pass --ssh to measure the gateway's own transit instead of\n")
		fmt.Fprintf(w, "                 leaving it unexamined\n")
	}
	fmt.Fprintf(w, "  window         %d echo probes at %dms per leg\n", r.Probes, r.IntervalMS)

	fmt.Fprintf(w, "\nVERDICT  %s\n\n", r.Attribution.Headline)
	for _, f := range r.Attribution.Findings {
		fmt.Fprintf(w, "  %-6s %s\n", strings.ToUpper(f.Severity), f.Segment)
		fmt.Fprintf(w, "         %s\n", f.Summary)
		for _, line := range wrap(f.Detail, 84) {
			fmt.Fprintf(w, "         %s\n", line)
		}
		fmt.Fprintln(w)
	}

	fmt.Fprintln(w, "legs")
	rows, problems := legRows(r.Evidence)
	tw := tabwriter.NewWriter(w, 0, 0, 2, ' ', 0)
	fmt.Fprintln(tw, "  vantage\ttarget\tinstrument\tsent\tloss\tmin\ttypical\tp99\tburst")
	for _, row := range rows {
		fmt.Fprintln(tw, row)
	}
	_ = tw.Flush()
	// A leg that failed has no figures, and threading its error through the
	// table would widen a numeric column to the width of a sentence and make
	// every measured row unreadable. The reason it failed still has to appear,
	// so it appears here instead of being dropped.
	if len(problems) > 0 {
		fmt.Fprintln(w, "\n  not measured")
		for _, p := range problems {
			fmt.Fprintf(w, "    %s\n", p)
		}
	}

	if r.Evidence.Tunnel.Present {
		renderTunnel(w, "tunnel, as the running client measures it", r.Evidence.Tunnel)
	}
	if r.Evidence.Remote.Present {
		renderTunnel(w, "tunnel, as the gateway measures it", r.Evidence.Remote)
	}

	if len(r.Notes) > 0 {
		fmt.Fprintln(w, "\nnotes")
		for _, n := range r.Notes {
			lines := wrap(n, 84)
			for i, line := range lines {
				prefix := "  - "
				if i > 0 {
					prefix = "    "
				}
				fmt.Fprintf(w, "%s%s\n", prefix, line)
			}
		}
	}
}

func legRows(e pathseg.Evidence) (rows, problems []string) {
	add := func(vantage string, refs ...pathseg.Reference) {
		for _, ref := range refs {
			if ref.Error != "" {
				problems = append(problems, fmt.Sprintf("%s -> %s: %s", vantage, ref.Target, ref.Error))
				continue
			}
			for _, leg := range []pathseg.Leg{ref.Echo, ref.Establish} {
				switch {
				case leg.Sent == 0 && leg.Error != "":
					problems = append(problems, fmt.Sprintf("%s -> %s (%s): %s",
						vantage, ref.Target, legMethod(leg), leg.Error))
				case leg.Sent == 0:
					continue
				default:
					rows = append(rows, legRow(vantage, ref.Target, leg))
				}
			}
		}
	}
	add("client", e.Gateway)
	add("client", e.ClientReferences...)
	add("gateway", e.GatewayReferences...)
	for i := range e.Direct {
		rows = append(rows, legRow("client direct", e.Direct[i].To, e.Direct[i]))
		if i < len(e.Tunneled) {
			rows = append(rows, legRow("via tunnel", e.Tunneled[i].To, e.Tunneled[i]))
		}
	}
	return rows, problems
}

// legMethod names the instrument even for a leg that never produced a sample,
// so a failure can be told apart from the other instrument's failure.
func legMethod(leg pathseg.Leg) string {
	if leg.Method == "" {
		return "probe"
	}
	return leg.Method
}

func legRow(vantage, target string, leg pathseg.Leg) string {
	loss := fmt.Sprintf("%.1f%%", leg.Loss*100)
	if leg.Blocked {
		// A leg that got nothing back has not measured total loss, it has
		// measured nothing, and printing 100% would make the strongest claim
		// in the table out of the weakest evidence.
		loss = "no reply"
	}
	typical := "-"
	switch {
	case leg.P50MS > 0:
		typical = fmt.Sprintf("%.1f", leg.P50MS)
	case leg.MeanMS > 0:
		typical = fmt.Sprintf("%.1f avg", leg.MeanMS)
	}
	burst := "-"
	if leg.Loss > 0 && leg.BurstFactor > 0 {
		burst = fmt.Sprintf("%.1f", leg.BurstFactor)
	}
	return fmt.Sprintf("  %s\t%s\t%s\t%d\t%s\t%s\t%s\t%s\t%s",
		vantage, target, leg.Method, leg.Sent, loss,
		optional(leg.MinMS), typical, optional(leg.P99MS), burst)
}

func optional(v float64) string {
	if v == 0 {
		return "-"
	}
	return fmt.Sprintf("%.1f", v)
}

func renderTunnel(w io.Writer, title string, v pathseg.TunnelView) {
	fmt.Fprintf(w, "\n%s\n", title)
	fmt.Fprintf(w, "  lanes %d, active flows %d, min rtt %.1fms, smoothed %.1fms\n",
		v.Lanes, v.ActiveFlows, v.MinRTTMS, v.SmoothedRTTMS)
	fmt.Fprintf(w, "  erasure        receive %.1f%% (residual %.1f%%)   send %.1f%%\n",
		v.ReceiveErasure*100, v.ReceiveResidual*100, v.SendErasure*100)
	fmt.Fprintf(w, "  measured over  %d coded symbols, %d packets sent\n", v.CodedSymbols, v.PacketsSent)
	if !v.ReceiveSignificant() {
		fmt.Fprintf(w, "  the session has not carried enough to make those ratios meaningful; drive traffic\n")
		fmt.Fprintf(w, "  through it and run this again\n")
	}
	if v.Fallbacks > 0 || v.LaneFailures > 0 || v.FlowStalls > 0 || v.PortHops > 0 {
		fmt.Fprintf(w, "  events         %d fallbacks, %d lane failures, %d flow stalls, %d port hops\n",
			v.Fallbacks, v.LaneFailures, v.FlowStalls, v.PortHops)
	}
}

// wrap breaks detail text at a column so a terminal shows a paragraph rather
// than one very long line.
func wrap(s string, width int) []string {
	if s == "" {
		return nil
	}
	var lines []string
	var line strings.Builder
	for _, word := range strings.Fields(s) {
		if line.Len() > 0 && line.Len()+1+len(word) > width {
			lines = append(lines, line.String())
			line.Reset()
		}
		if line.Len() > 0 {
			line.WriteByte(' ')
		}
		line.WriteString(word)
	}
	if line.Len() > 0 {
		lines = append(lines, line.String())
	}
	return lines
}
