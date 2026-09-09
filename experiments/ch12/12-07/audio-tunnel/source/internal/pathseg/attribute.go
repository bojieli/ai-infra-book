package pathseg

import (
	"fmt"
	"sort"
	"strings"
)

// Attribution turns a set of legs into the statement an operator can act on:
// which segment is at fault, and therefore whether this transport is the answer
// to it.
//
// The reasoning is a shared-element argument over legs measured in the same
// minutes. A client reaching its gateway and the same client reaching an
// unfiltered destination near itself share the client's own access link and
// nothing else. A gateway reaching an unfiltered destination near itself shares
// nothing with either. So a leg that is lossy while the legs it shares nothing
// with are clean has localised the fault to the part only it traverses, and a
// pair of lossy legs localises it to the part they share.
//
// The reference destinations are what make that argument valid, and choosing
// them is not a detail. A probe from a filtered network to a filtered
// destination measures the filter, and reading that as a lossy access link
// would blame the client's ISP for a policy decision made elsewhere: on the
// path this project exists for, a client in China probing a blocked host would
// report near-total loss on a first mile that is in perfect health. So each
// vantage point is measured against a destination that is local and unfiltered
// *from that vantage* -- a Chinese anchor from a Chinese client, a global one
// from a gateway outside -- and a vantage's local health is taken from its best
// reference rather than its average. A reference that is clean proves the
// access link works; a reference that is not, next to one that is, is evidence
// about filtering or international transit, which is a finding of its own and
// never a fault charged to the link.
type Attribution struct {
	Headline string    `json:"headline"`
	Findings []Finding `json:"findings"`
}

// Finding is one statement about one segment.
type Finding struct {
	Segment  string `json:"segment"`
	Severity string `json:"severity"`
	Summary  string `json:"summary"`
	Detail   string `json:"detail,omitempty"`
}

// Severities, ordered by how much they should move an operator.
const (
	SeverityOK    = "ok"
	SeverityNote  = "note"
	SeverityWarn  = "warn"
	SeverityFault = "fault"
)

// Segment names, which are the vocabulary the whole report speaks.
const (
	SegmentClientAccess  = "client-to-internet"
	SegmentLongHaul      = "client-to-gateway"
	SegmentGatewayEgress = "gateway-to-internet"
	SegmentDestination   = "destination"
	SegmentTunnel        = "tunnel"
)

// Thresholds separating a clean segment from a degraded one from a broken one.
//
// They are round numbers rather than measured constants, chosen to sit either
// side of the difference that matters: an ordinary Internet segment loses well
// under half a percent, and the erasure that motivated this project ran from
// fourteen to forty-five percent. Anything between is degraded and worth
// naming without being called a fault on its own.
const (
	CleanLoss = 0.005
	LossyLoss = 0.02
)

// reading is a leg together with the figure a verdict should read off it.
//
// The distinction it carries is load-bearing. An echo leg counts packets, so
// its loss rate is a loss rate. An establishment leg counts connections, and on
// a path erasing a fifth of everything almost every connection still completes
// -- TCP simply retransmits -- so its failure rate is near zero and reading it
// as loss would report a badly damaged path as clean. What an establishment leg
// can see is the cost of that retransmission, which is why the tail stands in
// for loss wherever no echo socket was available.
type reading struct {
	Leg   Leg
	Value float64
	Proxy bool
}

func read(l Leg) reading {
	if l.Method == "icmp" {
		return reading{Leg: l, Value: l.Loss}
	}
	value := l.Loss
	if l.TailRate > value {
		value = l.TailRate
	}
	return reading{Leg: l, Value: value, Proxy: true}
}

// proxyNote says so wherever a verdict rested on the stand-in rather than on a
// counted loss rate, because the two are not the same measurement and a reader
// acting on the figure should know which they have.
func (r reading) proxyNote() string {
	if !r.Proxy {
		return ""
	}
	return fmt.Sprintf(" This leg had no echo socket, so the figure is the share of connections that "+
		"paid a retransmission timeout (%s of %d) rather than a counted loss rate.",
		percent(r.Value), r.Leg.Sent)
}

// Evidence is everything one run measured.
type Evidence struct {
	// Gateway is the client's own path to the gateway. It is the long haul,
	// first mile included, and it is measured with both instruments for the
	// same reason an anchor is: a gateway that answers echo but refuses a
	// handshake is being blocked, not lost.
	Gateway Reference `json:"gateway"`
	// ClientReferences and GatewayReferences are each vantage point's local,
	// unfiltered anchors. They are what turn a lossy leg into a located one.
	ClientReferences  []Reference `json:"client_references,omitempty"`
	GatewayReferences []Reference `json:"gateway_references,omitempty"`
	// Direct and Tunneled are the destinations the operator actually cares
	// about, reached both ways, index for index.
	Direct   []Leg `json:"direct,omitempty"`
	Tunneled []Leg `json:"tunneled,omitempty"`

	// Tunnel is the client's own account of the segment it sits on, which no
	// external probe can match, and Remote is the gateway's account of the
	// same segment from the other end.
	Tunnel TunnelView `json:"tunnel"`
	Remote TunnelView `json:"remote_tunnel"`

	// GatewayVantage records whether anything was measured from the gateway at
	// all, because a report that cannot see the far side has to say so rather
	// than let silence read as health.
	GatewayVantage bool `json:"gateway_vantage"`
}

// Attribute reduces the evidence to findings, worst first.
func Attribute(e Evidence) Attribution {
	var a Attribution
	clientLocal, clientKnown := bestReference(e.ClientReferences)
	gatewayLocal, gatewayKnown := bestReference(e.GatewayReferences)

	a.Findings = append(a.Findings, clientAccessFinding(clientLocal, clientKnown, e.ClientReferences))
	a.Findings = append(a.Findings, longHaulFinding(e, clientLocal, clientKnown))
	a.Findings = append(a.Findings, gatewayEgressFinding(e, gatewayLocal, gatewayKnown))
	a.Findings = append(a.Findings, filteringFindings(e)...)
	a.Findings = append(a.Findings, destinationFindings(e)...)

	sort.SliceStable(a.Findings, func(i, j int) bool {
		return severityRank(a.Findings[i].Severity) > severityRank(a.Findings[j].Severity)
	})
	a.Headline = headline(a.Findings)
	return a
}

func headline(findings []Finding) string {
	var faults, warns []string
	for _, f := range findings {
		switch f.Severity {
		case SeverityFault:
			faults = append(faults, f.Segment)
		case SeverityWarn:
			warns = append(warns, f.Segment)
		}
	}
	switch {
	case len(faults) == 1:
		return "The fault is on the " + faults[0] + " segment."
	case len(faults) > 1:
		return "More than one segment is at fault: " + strings.Join(faults, ", ") + "."
	case len(warns) > 0:
		return "No segment is clearly at fault; " + strings.Join(warns, ", ") + " is degraded."
	default:
		return "Every segment that could be measured is clean."
	}
}

// clientAccessFinding reads the client's own link off its best local anchor.
//
// The best rather than the mean, because these anchors are not repeated
// measurements of one thing. One clean anchor is proof the access link carries
// traffic; a second anchor that is not clean says something about that anchor's
// path, and averaging the two would turn evidence of health into a fault.
func clientAccessFinding(best reading, known bool, all []Reference) Finding {
	f := Finding{Segment: SegmentClientAccess}
	if !known {
		f.Severity = SeverityNote
		f.Summary = "not measured"
		f.Detail = "No local reference answered from this client, so its own access link was not " +
			"established as healthy and nothing below can be charged to it or cleared of it. " +
			"Name a destination that is local and unfiltered here with --client-reference."
		if len(all) > 0 {
			f.Detail += " Tried: " + strings.Join(referenceNames(all), ", ") + "."
		}
		return f
	}
	switch {
	case best.Value >= LossyLoss:
		f.Severity = SeverityFault
		f.Summary = fmt.Sprintf("losing %s to %s, a destination that should be local to this client",
			percent(best.Value), best.Leg.To)
		f.Detail = "An unfiltered anchor near the client is the one leg whose loss cannot be blamed on " +
			"distance, transit, or filtering. Loss here is the client's own access network, and no " +
			"transport can repair a first mile: every other segment measured below crosses this one " +
			"and inherits it. " + patternNote(best.Leg) + best.proxyNote()
	case best.Value > CleanLoss:
		f.Severity = SeverityWarn
		f.Summary = fmt.Sprintf("losing %s to %s", percent(best.Value), best.Leg.To)
		f.Detail = "Slight loss on a local anchor. It is small enough to be the anchor rather than the " +
			"link, and large enough that it should be ruled out before any figure below is trusted." +
			best.proxyNote()
	default:
		f.Severity = SeverityOK
		f.Summary = fmt.Sprintf("clean: %s to %s at %s", percent(best.Value), best.Leg.To, rtt(best.Leg))
		f.Detail = "The client's own access network carries traffic without loss, so any loss measured " +
			"further out belongs further out." + best.proxyNote()
	}
	return f
}

// longHaulFinding reports the segment this transport actually carries.
//
// It prefers the tunnel's own figures over the echo probe, and says which it
// used. The transport measured that segment on the real four-tuple at the real
// rate and in each direction separately; the echo probe offers a few packets a
// second and cannot tell the directions apart. Where the path erases one
// direction and not the other -- which is the case this project was built
// around -- only the first of those two instruments can see it.
func longHaulFinding(e Evidence, clientLocal reading, clientKnown bool) Finding {
	f := Finding{Segment: SegmentLongHaul}
	firstMile := clientKnown && clientLocal.Value >= LossyLoss

	if e.Tunnel.ReceiveSignificant() || e.Tunnel.SendSignificant() {
		down, up := e.Tunnel.ReceiveErasure, e.Tunnel.SendErasure
		worst := down
		dir := "downstream (gateway to client)"
		if up > worst {
			worst, dir = up, "upstream (client to gateway)"
		}
		summary := fmt.Sprintf("the tunnel measures %s erasure downstream and %s upstream, at %.0fms minimum round trip",
			percent(down), percent(up), e.Tunnel.MinRTTMS)
		detail := fmt.Sprintf("Measured by the running transport itself on the live session, which is the "+
			"only instrument here that separates the two directions. Of the downstream erasure, %s was left "+
			"unrepaired after coding and cost a further round trip. ", percent(e.Tunnel.ReceiveResidual))
		switch {
		case worst >= LossyLoss && firstMile:
			f.Severity = SeverityWarn
			f.Summary = summary
			f.Detail = detail + "The client's own access link is also lossy, and this segment crosses it, " +
				"so this figure is the two together rather than the long haul alone. Fix the access link " +
				"first and measure again."
		case worst >= LossyLoss:
			f.Severity = SeverityFault
			f.Summary = summary
			f.Detail = detail + "The client's local anchor is clean, so this is the long haul rather than " +
				"the first mile, and it is the one segment this transport exists to repair. The " + dir +
				" direction is the worse of the two."
		case worst > CleanLoss:
			f.Severity = SeverityWarn
			f.Summary = summary
			f.Detail = detail + "Low but not nil; the code should be absorbing it."
		default:
			f.Severity = SeverityOK
			f.Summary = summary
			f.Detail = detail + "The segment this transport carries is not where the loss is."
		}
		if e.Remote.Present {
			f.Detail += remoteCrossCheck(e)
		}
		return f
	}

	// No live tunnel to read, so fall back to probing the gateway, which is a
	// round-trip figure and has to be labelled as one.
	gw, gwOK := e.Gateway.Health()
	if !gwOK {
		f.Severity = SeverityNote
		f.Summary = "not measured"
		f.Detail = "The tunnel published no usable erasure figures" + idleNote(e.Tunnel) +
			", and the gateway did not answer probes" + blockedNote(e.Gateway.Echo) +
			". Start the client with --metrics-listen and re-run, which reads the segment " +
			"directly rather than probing it."
		return f
	}
	r := read(gw)
	summary := fmt.Sprintf("%s loss to the gateway at %s, round trip", percent(r.Value), rtt(gw))
	detail := "Measured with " + gw.Method + " probes, which cannot separate upstream from downstream. " +
		"On a path that erases one direction and not the other this understates the bad direction by " +
		"half. Run the client with --metrics-listen for a per-direction figure. " + patternNote(gw) +
		r.proxyNote()
	switch {
	case r.Value >= LossyLoss && firstMile:
		f.Severity, f.Summary, f.Detail = SeverityWarn, summary, detail+
			" The client's access link is lossy too, and this leg crosses it, so the two are not yet separated."
	case r.Value >= LossyLoss:
		f.Severity, f.Summary, f.Detail = SeverityFault, summary, detail+
			" The client's local anchor is clean, so this is the long haul rather than the first mile."
	case r.Value > CleanLoss:
		f.Severity, f.Summary, f.Detail = SeverityWarn, summary, detail
	default:
		f.Severity, f.Summary, f.Detail = SeverityOK, summary, detail
	}
	return f
}

// remoteCrossCheck compares the two ends' accounts of one segment.
//
// The client infers what it sent and lost from acknowledgements; the gateway
// counts what actually arrived. Where they disagree materially, one of them is
// wrong about the segment they share, and an operator should know that before
// acting on either.
func remoteCrossCheck(e Evidence) string {
	if !e.Remote.ReceiveSignificant() {
		return ""
	}
	note := fmt.Sprintf(" The gateway's own metrics put the erasure it receives -- the client's upstream -- "+
		"at %s, against the %s the client inferred from acknowledgements.",
		percent(e.Remote.ReceiveErasure), percent(e.Tunnel.SendErasure))
	if absDiff(e.Remote.ReceiveErasure, e.Tunnel.SendErasure) > LossyLoss {
		note += " Those disagree by more than the threshold this report uses, and the gateway's figure is " +
			"the counted one. Note that a gateway serving several clients publishes their sum, so this " +
			"comparison only holds where this client is the only one on it."
	}
	return note
}

// gatewayEgressFinding reports the segment past the gateway, which is the one
// this transport ends before and cannot do anything about.
func gatewayEgressFinding(e Evidence, best reading, known bool) Finding {
	f := Finding{Segment: SegmentGatewayEgress}
	if !e.GatewayVantage {
		f.Severity = SeverityNote
		f.Summary = "not measured; no vantage point on the gateway"
		f.Detail = "Everything above was measured from the client, which cannot see what the gateway's own " +
			"transit does. Pass --ssh to measure it from there instead of inferring it by subtraction. " +
			"Until then a clean report above does not rule this segment out."
		return f
	}
	if !known {
		f.Severity = SeverityNote
		f.Summary = "not measured; no reference answered from the gateway"
		f.Detail = "The gateway was reachable but none of its local anchors answered, so its transit was " +
			"not established as healthy. Name one that is local and unfiltered there with --gateway-reference."
		return f
	}
	switch {
	case best.Value >= LossyLoss:
		f.Severity = SeverityFault
		f.Summary = fmt.Sprintf("the gateway loses %s to %s, a destination that should be local to it",
			percent(best.Value), best.Leg.To)
		f.Detail = "This is the gateway's own transit, past the point where this transport ends. Nothing in " +
			"the tunnel repairs it: coding, pacing and lane recovery all stop at the gateway, and traffic " +
			"leaves it as ordinary packets. This is a question for the gateway's provider, or a reason to " +
			"move the gateway. " + patternNote(best.Leg) + best.proxyNote()
	case best.Value > CleanLoss:
		f.Severity = SeverityWarn
		f.Summary = fmt.Sprintf("the gateway loses %s to %s", percent(best.Value), best.Leg.To)
		f.Detail = "Small, but it is past the point this transport can repair, so it passes through to every " +
			"flow undiminished." + best.proxyNote()
	default:
		f.Severity = SeverityOK
		f.Summary = fmt.Sprintf("clean: %s to %s at %s", percent(best.Value), best.Leg.To, rtt(best.Leg))
		f.Detail = "The gateway's own transit carries traffic without loss, so loss seen through the tunnel " +
			"was not introduced past the gateway."
	}
	return f
}

// filteringFindings reports anchors that disagree with each other from one
// vantage point.
//
// This is the finding the reference design exists to make possible. One anchor
// clean and another blocked, from the same place in the same minutes, is not a
// statement about a link -- the link demonstrably carries traffic -- it is a
// statement about the route to the second anchor, and on the path this project
// was built for that is usually a filter rather than a fault. Reporting it as
// loss would be the single most misleading thing this tool could do.
func filteringFindings(e Evidence) []Finding {
	var out []Finding
	for _, v := range []struct {
		vantage string
		refs    []Reference
	}{{"client", e.ClientReferences}, {"gateway", e.GatewayReferences}} {
		best, ok := bestReference(v.refs)
		if !ok || best.Value >= LossyLoss {
			continue
		}
		var filtered, degraded []string
		for _, r := range v.refs {
			health, ok := r.Health()
			if ok && health.Name == best.Leg.Name {
				continue
			}
			switch {
			case r.Filtered():
				filtered = append(filtered, r.Target)
			case !ok || read(health).Value >= LossyLoss:
				degraded = append(degraded, fmt.Sprintf("%s (%s)", r.Target, describeReference(r)))
			}
		}
		if len(filtered) > 0 {
			out = append(out, Finding{
				Segment:  SegmentDestination,
				Severity: SeverityNote,
				Summary: fmt.Sprintf("from the %s, %s answers echo but refuses a handshake",
					v.vantage, strings.Join(filtered, ", ")),
				Detail: "That pair of outcomes is filtering, not loss: the address is reachable at the " +
					"packet level and the connection is prevented from completing. It is counted against " +
					"no segment, and it is the condition a tunnel exists to route around rather than a " +
					"fault a tunnel could repair.",
			})
		}
		if len(degraded) > 0 {
			out = append(out, Finding{
				Segment:  SegmentDestination,
				Severity: SeverityNote,
				Summary: fmt.Sprintf("from the %s, %s is clean but %s is not",
					v.vantage, best.Leg.To, strings.Join(degraded, ", ")),
				Detail: "One anchor answering cleanly from this vantage point proves its link carries " +
					"traffic, so the anchors that did not are evidence about the route to them -- " +
					"filtering, or international transit -- and not about the link. This difference is " +
					"not counted as loss on any segment above.",
			})
		}
	}
	return out
}

func describeReference(r Reference) string {
	health, ok := r.Health()
	switch {
	case !ok && r.Error != "":
		return r.Error
	case !ok:
		return "no reply"
	default:
		return percent(read(health).Value) + " loss"
	}
}

// destinationFindings compare each destination reached directly against the
// same destination reached through the tunnel.
//
// This is the only part of the report that answers "is the tunnel worth it for
// this", and it is deliberately separate from the segment findings: a direct
// arm that fails where the tunnelled arm succeeds is not a fault anywhere, it
// is the tunnel doing the job it was deployed for.
func destinationFindings(e Evidence) []Finding {
	var out []Finding
	for i, direct := range e.Direct {
		if i >= len(e.Tunneled) {
			break
		}
		tunneled := e.Tunneled[i]
		f := Finding{Segment: SegmentTunnel}
		switch {
		case !direct.Usable() && tunneled.Usable():
			f.Severity = SeverityOK
			f.Summary = fmt.Sprintf("%s: unreachable directly, %s through the tunnel", direct.To, rtt(tunneled))
			f.Detail = "The direct arm did not establish at all while the tunnelled arm did. That is the " +
				"case this deployment exists for, and it is not loss on any segment."
		case direct.Usable() && !tunneled.Usable():
			f.Severity = SeverityFault
			f.Summary = fmt.Sprintf("%s: reachable directly, not through the tunnel", direct.To)
			f.Detail = "A destination the gateway cannot open is a gateway problem rather than a path one. " +
				"Check the gateway's own resolver and egress policy for this name."
		case !direct.Usable() && !tunneled.Usable():
			f.Severity = SeverityWarn
			f.Summary = fmt.Sprintf("%s: neither arm reached it", direct.To)
			f.Detail = "Nothing here distinguishes a destination that is down from one both paths are " +
				"blocked from."
		case tunneled.P50MS > 2*direct.P50MS && tunneled.P50MS-direct.P50MS > 5:
			f.Severity = SeverityWarn
			f.Summary = fmt.Sprintf("%s: %s direct against %s tunnelled", direct.To, rtt(direct), rtt(tunneled))
			f.Detail = "The tunnel costs more than twice the direct establishment for this destination, so " +
				"it is served closer to this client than the gateway is. queqiaod doctor --destination " +
				"examines that placement question properly, with the arms alternated."
		default:
			f.Severity = SeverityOK
			f.Summary = fmt.Sprintf("%s: %s direct against %s tunnelled", direct.To, rtt(direct), rtt(tunneled))
			f.Detail = "The tunnel is not costing this destination a detour."
		}
		out = append(out, f)
	}
	return out
}

// patternNote says whether the loss clustered, which decides what to do about
// it. Independent loss at a steady rate is an erasure channel and backing off
// does not make it drop less; loss in runs is a queue or a policer, and backing
// off is exactly the response.
func patternNote(l Leg) string {
	if l.Sent == 0 || l.Loss == 0 {
		return ""
	}
	if l.BurstFactor >= 2 {
		return fmt.Sprintf("The loss clustered (burst factor %.1f, longest run %d), which is the signature "+
			"of a queue or a policer rather than an erasure channel.", l.BurstFactor, l.LongestBurst)
	}
	return fmt.Sprintf("The loss was near-independent (burst factor %.1f), which is an erasure channel "+
		"rather than congestion: sending slower will not make it drop less.", l.BurstFactor)
}

func idleNote(v TunnelView) string {
	if !v.Present {
		return " (no metrics endpoint was read)"
	}
	return fmt.Sprintf(" (the session has carried %d coded symbols and %d packets, below the floor this "+
		"report will quote a ratio from)", v.CodedSymbols, v.PacketsSent)
}

func blockedNote(l Leg) string {
	if l.Blocked {
		return " (every probe was unanswered, which is filtering as often as it is loss)"
	}
	if l.Error != "" {
		return " (" + l.Error + ")"
	}
	return ""
}

// bestReference returns the healthiest anchor, which is how a vantage point's
// own link is read: one clean anchor proves the link carries traffic, and the
// others describe their own routes rather than that link. Taking the mean
// instead would let one filtered anchor convict a healthy access network.
func bestReference(refs []Reference) (reading, bool) {
	var best reading
	found := false
	for _, r := range refs {
		health, ok := r.Health()
		if !ok {
			continue
		}
		candidate := read(health)
		if !found || candidate.Value < best.Value {
			best, found = candidate, true
		}
	}
	return best, found
}

func referenceNames(refs []Reference) []string {
	out := make([]string, 0, len(refs))
	for _, r := range refs {
		out = append(out, r.Target)
	}
	return out
}

func severityRank(s string) int {
	switch s {
	case SeverityFault:
		return 3
	case SeverityWarn:
		return 2
	case SeverityNote:
		return 1
	default:
		return 0
	}
}

func percent(v float64) string { return fmt.Sprintf("%.1f%%", v*100) }

func rtt(l Leg) string {
	switch {
	case l.Arrived == 0:
		return "no samples"
	case l.P50MS > 0:
		return fmt.Sprintf("%.1fms", l.P50MS)
	case l.MeanMS > 0:
		return fmt.Sprintf("%.1fms mean", l.MeanMS)
	default:
		return "no timing"
	}
}

func absDiff(a, b float64) float64 {
	if a > b {
		return a - b
	}
	return b - a
}
