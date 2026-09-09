// Package routerule decides what a flow does: take the tunnel, go direct, or
// be refused.
//
// It lives here rather than in either mobile client because both of them ask
// the same question at the same moment. The iOS packet tunnel and the Android
// debug VpnService both hand their packets to the userspace stack in
// mobile/core, and every flow that stack accepts arrives at one forwarder with
// a destination and, once DNS is intercepted, a name. One matcher there is one
// set of semantics to get right and one set of tests to keep it right; two
// would be a parity script and an argument about which is correct.
//
// The syntax is the one the rule files in circulation already use -- Clash,
// mihomo, sing-box, Shadowrocket all read a list of `TYPE,VALUE,ACTION` lines
// -- because the point of this is that a user can bring the list they already
// maintain. Where those tools disagree with each other this follows the
// majority and says so at the rule concerned.
package routerule

import (
	"net/netip"
	"strings"
)

// Action is what happens to a flow that matches.
type Action uint8

const (
	// Proxy sends the flow through the tunnel. It is the zero value because it
	// is what this transport exists to do: a flow nothing matched is a flow
	// nobody made a decision about, and carrying it is the choice that cannot
	// leak.
	Proxy Action = iota
	// Direct sends the flow out the ordinary interface.
	Direct
	// Reject refuses the flow without dialing anything.
	Reject
)

func (a Action) String() string {
	switch a {
	case Direct:
		return "DIRECT"
	case Reject:
		return "REJECT"
	default:
		return "PROXY"
	}
}

// Kind is what a rule matches on.
type Kind uint8

const (
	KindDomain Kind = iota
	KindDomainSuffix
	KindDomainKeyword
	KindIPCIDR
	KindGeoIP
	KindDstPort
	KindFinal
)

func (k Kind) String() string {
	switch k {
	case KindDomain:
		return "DOMAIN"
	case KindDomainSuffix:
		return "DOMAIN-SUFFIX"
	case KindDomainKeyword:
		return "DOMAIN-KEYWORD"
	case KindIPCIDR:
		return "IP-CIDR"
	case KindGeoIP:
		return "GEOIP"
	case KindDstPort:
		return "DST-PORT"
	default:
		return "FINAL"
	}
}

// Rule is one line of a rule list.
type Rule struct {
	Kind   Kind
	Action Action

	// Domain carries the name for the three name kinds, already lowered and
	// stripped of a trailing dot so that matching does no work per flow.
	Domain string
	// Prefix carries the block for IP-CIDR.
	Prefix netip.Prefix
	// Country carries the two-letter code for GEOIP, upper-cased.
	Country string
	// Port carries the destination port for DST-PORT.
	Port uint16

	// NoResolve is carried because the rule files in circulation set it and a
	// parser that rejected it would refuse lists that work everywhere else. It
	// says an address rule must not trigger a name lookup to be evaluated,
	// which is already true here: this matcher never resolves anything, it is
	// given what the flow already knows. Kept so a round trip through parse and
	// format does not silently rewrite a user's file.
	NoResolve bool
}

// Countries answers whether an address belongs to a country's registered
// space. The bundled set that scripts/generate_cn_geoip.py packs is one
// implementation; a test supplies another.
type Countries interface {
	// Contains reports whether addr is registered to the two-letter code,
	// which is upper-case. An unknown code reports false rather than an error:
	// a rule naming a set this build does not carry must not decide the flow.
	Contains(code string, addr netip.Addr) bool
}

// Flow is what is known about a connection at the moment the decision is made.
type Flow struct {
	// Domain is the name the flow was opened to, empty when it is not known.
	// It is known when DNS was intercepted and the destination is one of the
	// addresses handed out for a name; it is not known for a flow opened to a
	// literal address.
	Domain string
	// Addr is the destination address, invalid when the flow has a name that
	// has not been resolved yet.
	Addr netip.Addr
	// Port is the destination port.
	Port uint16
}

// Set is a parsed rule list, ready to match.
type Set struct {
	rules []Rule

	// The list is scanned in order, and that is not a placeholder for an index
	// that was not written. First match wins, so any structure that answers
	// faster has to answer with the earliest matching rule and not merely a
	// matching one -- an exact-name map consulted ahead of the scan gets that
	// wrong the moment a suffix rule sits above an exact rule for a name under
	// it, which is the ordinary shape of a real file.
	// TestTheExactIndexDoesNotOutrankAnEarlierRule caught exactly that and is
	// kept as the guard on whatever replaces this. Until a list large enough to
	// need one turns up, a scan of a few thousand rules once per flow -- not
	// once per packet -- is the honest cost.
	countries Countries
}

// Match returns the action for a flow and the rule that decided it.
//
// First match wins, which is what every tool using this syntax does, and is
// why a list is ordered rather than a set. A rule whose input the flow does not
// carry is skipped rather than treated as a miss: a name rule cannot speak
// about a flow with no name, and skipping it lets the same list serve the
// lookup that has a name and the connection that only has an address.
//
// A flow that matches nothing takes Proxy. A list that wants otherwise ends
// with FINAL, and every list in circulation does.
func (s *Set) Match(flow Flow) (Action, Rule, bool) {
	if s == nil {
		return Proxy, Rule{}, false
	}
	domain := normalizeDomain(flow.Domain)
	for _, rule := range s.rules {
		if !s.matches(rule, domain, flow) {
			continue
		}
		return rule.Action, rule, true
	}
	return Proxy, Rule{}, false
}

func (s *Set) matches(rule Rule, domain string, flow Flow) bool {
	switch rule.Kind {
	case KindFinal:
		return true
	case KindDomain:
		return domain != "" && domain == rule.Domain
	case KindDomainSuffix:
		if domain == "" {
			return false
		}
		// A suffix rule matches the name itself and anything under it, and
		// nothing else. Plain string suffix would take "notexample.com" for
		// "example.com", which is a different registrable name and in the
		// wrong direction: it sends somebody else's traffic where the user
		// pointed only their own.
		return domain == rule.Domain || strings.HasSuffix(domain, "."+rule.Domain)
	case KindDomainKeyword:
		return domain != "" && strings.Contains(domain, rule.Domain)
	case KindIPCIDR:
		return flow.Addr.IsValid() && rule.Prefix.IsValid() &&
			rule.Prefix.Contains(unmap(flow.Addr))
	case KindGeoIP:
		return flow.Addr.IsValid() && s.countries != nil &&
			s.countries.Contains(rule.Country, unmap(flow.Addr))
	case KindDstPort:
		return flow.Port != 0 && flow.Port == rule.Port
	default:
		return false
	}
}

// Rules returns the parsed list in order.
func (s *Set) Rules() []Rule {
	if s == nil {
		return nil
	}
	out := make([]Rule, len(s.rules))
	copy(out, s.rules)
	return out
}

// Len reports how many rules the set carries.
func (s *Set) Len() int {
	if s == nil {
		return 0
	}
	return len(s.rules)
}

// WithCountries returns the set bound to a country lookup. A set with none
// evaluates GEOIP rules as misses rather than refusing to build, so a build
// that ships without the packed set still runs every other rule in the file.
func (s *Set) WithCountries(c Countries) *Set {
	if s == nil {
		return nil
	}
	bound := *s
	bound.countries = c
	return &bound
}

// normalizeDomain lowers a name and drops the root dot, so that "EXAMPLE.com."
// and "example.com" are the same name. Rules are normalized once at parse time
// and flows once per decision.
func normalizeDomain(name string) string {
	name = strings.TrimSuffix(strings.ToLower(strings.TrimSpace(name)), ".")
	return name
}

// unmap flattens a v4-in-v6 address so that a v4 rule matches a flow the stack
// handed over in v6 form. Without it an IP-CIDR of 10.0.0.0/8 silently fails to
// match ::ffff:10.0.0.1, which is the same address.
func unmap(addr netip.Addr) netip.Addr {
	if addr.Is4In6() {
		return addr.Unmap()
	}
	return addr
}
