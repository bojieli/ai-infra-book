package routerule

import (
	"net/netip"
	"strings"
	"testing"
)

// fixedCountries answers from a literal table, so the matcher's behaviour is
// tested without the packed resource the clients ship.
type fixedCountries map[string][]netip.Prefix

func (f fixedCountries) Contains(code string, addr netip.Addr) bool {
	for _, prefix := range f[code] {
		if prefix.Contains(addr) {
			return true
		}
	}
	return false
}

func mustSet(t *testing.T, text string) *Set {
	t.Helper()
	set, problems := Parse(text)
	if len(problems) != 0 {
		t.Fatalf("unexpected problems parsing the list: %v", problems)
	}
	return set
}

func addr(t *testing.T, s string) netip.Addr {
	t.Helper()
	a, err := netip.ParseAddr(s)
	if err != nil {
		t.Fatalf("bad test address %q: %v", s, err)
	}
	return a
}

// First match wins, which is the whole reason a rule list is ordered. Getting
// this backwards makes every list in circulation mean something else, because
// they are all written with the specific exceptions above the general sweep.
func TestTheFirstMatchDecides(t *testing.T) {
	set := mustSet(t, `
# The shape every real list has: an exception, then the sweep it sits above.
DOMAIN-SUFFIX,internal.example.com,PROXY
DOMAIN-SUFFIX,example.com,DIRECT
FINAL,PROXY
`)
	for _, test := range []struct {
		domain string
		want   Action
	}{
		{"internal.example.com", Proxy},
		{"host.internal.example.com", Proxy},
		{"example.com", Direct},
		{"www.example.com", Direct},
		{"elsewhere.net", Proxy},
	} {
		got, _, _ := set.Match(Flow{Domain: test.domain})
		if got != test.want {
			t.Errorf("%s got %s, want %s", test.domain, got, test.want)
		}
	}
}

// A suffix rule names a place in the tree, not a string ending. The difference
// is somebody else's traffic: notexample.com is a different registrable name
// from example.com, and a plain HasSuffix sends it wherever the user pointed
// only their own.
func TestASuffixRuleStopsAtALabelBoundary(t *testing.T) {
	set := mustSet(t, "DOMAIN-SUFFIX,example.com,DIRECT\nFINAL,PROXY")

	if got, _, _ := set.Match(Flow{Domain: "notexample.com"}); got != Proxy {
		t.Errorf("notexample.com matched a rule for example.com and got %s", got)
	}
	if got, _, _ := set.Match(Flow{Domain: "a.example.com"}); got != Direct {
		t.Errorf("a.example.com is under example.com and got %s", got)
	}
}

// The same list has to serve two different moments: the lookup, which has a
// name and no address, and the connection, which may have only an address. A
// rule whose input the flow does not carry is skipped, not counted as a miss.
func TestARuleIsSkippedWhenTheFlowCannotAnswerIt(t *testing.T) {
	set := mustSet(t, `
DOMAIN-SUFFIX,example.com,REJECT
IP-CIDR,10.0.0.0/8,DIRECT
FINAL,PROXY
`)
	// An address with no name must not be caught by the name rule.
	got, rule, _ := set.Match(Flow{Addr: addr(t, "10.1.2.3")})
	if got != Direct || rule.Kind != KindIPCIDR {
		t.Errorf("an address-only flow got %s from %s, want DIRECT from IP-CIDR", got, rule.Kind)
	}
	// A name with no address must not be caught by the address rule.
	got, rule, _ = set.Match(Flow{Domain: "www.example.com"})
	if got != Reject || rule.Kind != KindDomainSuffix {
		t.Errorf("a name-only flow got %s from %s, want REJECT from DOMAIN-SUFFIX", got, rule.Kind)
	}
}

// The stack hands v4 flows over in v4-in-v6 form, and a rule file writes v4
// blocks in v4 form. Without unmapping, 10.0.0.0/8 silently fails to match
// ::ffff:10.0.0.1, which is the same address, and the flow takes the tunnel a
// user had explicitly kept it off.
func TestAMappedAddressMatchesAnIPv4Rule(t *testing.T) {
	set := mustSet(t, "IP-CIDR,10.0.0.0/8,DIRECT\nFINAL,PROXY")
	mapped := netip.AddrFrom16(addr(t, "10.1.2.3").As16())
	if !mapped.Is4In6() {
		t.Fatalf("test set-up did not produce a v4-in-v6 address: %s", mapped)
	}
	if got, _, _ := set.Match(Flow{Addr: mapped}); got != Direct {
		t.Errorf("%s got %s, want DIRECT: it is the same address as 10.1.2.3", mapped, got)
	}
}

// A flow nothing matched takes the tunnel. The alternative -- defaulting to
// direct -- makes a list that fails to load, or one whose FINAL line was
// mistyped, put traffic on the open path, which is the one failure this
// transport must not have.
func TestAnUnmatchedFlowTakesTheTunnel(t *testing.T) {
	set := mustSet(t, "DOMAIN,example.com,DIRECT")
	got, _, matched := set.Match(Flow{Domain: "elsewhere.net"})
	if got != Proxy || matched {
		t.Errorf("an unmatched flow got %s (matched=%v), want PROXY and no rule", got, matched)
	}
	var empty *Set
	if got, _, _ := empty.Match(Flow{Domain: "anything"}); got != Proxy {
		t.Errorf("a nil set got %s, want PROXY", got)
	}
}

func TestGeoIPMatchesTheRegisteredSet(t *testing.T) {
	set := mustSet(t, "GEOIP,CN,DIRECT\nFINAL,PROXY").WithCountries(fixedCountries{
		"CN": {netip.MustParsePrefix("223.5.5.0/24")},
	})
	if got, _, _ := set.Match(Flow{Addr: addr(t, "223.5.5.5")}); got != Direct {
		t.Errorf("a registered CN address got %s, want DIRECT", got)
	}
	if got, _, _ := set.Match(Flow{Addr: addr(t, "8.8.8.8")}); got != Proxy {
		t.Errorf("an address outside the set got %s, want PROXY", got)
	}
}

// A build that ships without the packed set must still run the rest of the
// file. Treating a GEOIP rule as a match when there is nothing to match
// against would decide flows from a set this build does not have.
func TestGeoIPWithNoSetLoadedDecidesNothing(t *testing.T) {
	set := mustSet(t, "GEOIP,CN,DIRECT\nIP-CIDR,203.0.113.0/24,REJECT\nFINAL,PROXY")
	got, rule, _ := set.Match(Flow{Addr: addr(t, "203.0.113.9")})
	if got != Reject || rule.Kind != KindIPCIDR {
		t.Errorf("got %s from %s; the GEOIP rule with no set behind it should have "+
			"been skipped, leaving the IP-CIDR rule to decide", got, rule.Kind)
	}
}

// Parsing reports what it could not read instead of dropping it. A rule list is
// somebody stating where their traffic may and may not go, and a silently
// skipped line is that statement not being enforced for as long as the file
// lives.
func TestABadLineIsReportedAndTheRestStillLoads(t *testing.T) {
	set, problems := Parse(`
DOMAIN-SUFFIX,example.com,DIRECT
NOT-A-TYPE,whatever,DIRECT
IP-CIDR,not-an-address,DIRECT
DOMAIN-SUFFIX,short.example
FINAL,PROXY
`)
	if set.Len() != 2 {
		t.Errorf("loaded %d rules, want the 2 that were valid", set.Len())
	}
	if len(problems) != 3 {
		t.Fatalf("reported %d problems, want 3: %v", len(problems), problems)
	}
	for _, want := range []int{3, 4, 5} {
		found := false
		for _, p := range problems {
			if p.Line == want {
				found = true
			}
		}
		if !found {
			t.Errorf("no problem reported for line %d: %v", want, problems)
		}
	}
}

// A line naming a proxy group is refused rather than read as PROXY. Such a file
// was written for a client with several outbounds, and quietly collapsing them
// onto this one tunnel routes through it exactly the traffic the group existed
// to route elsewhere.
func TestANamedProxyGroupIsRefusedRatherThanAssumed(t *testing.T) {
	_, problems := Parse("DOMAIN-SUFFIX,example.com,my-hong-kong-group")
	if len(problems) != 1 {
		t.Fatalf("a named group produced %d problems, want 1: %v", len(problems), problems)
	}
	if !strings.Contains(problems[0].Reason, "one tunnel") {
		t.Errorf("the reason does not say why: %q", problems[0].Reason)
	}
}

// The syntax in circulation is not one syntax. These spellings all appear in
// files users already maintain, and refusing them means refusing the list the
// feature exists to accept.
func TestTheSpellingsInCirculationAreAccepted(t *testing.T) {
	set, problems := Parse(`
# comment
; also a comment
domain-suffix,Example.COM.,direct
IP-CIDR6,2001:db8::/32,REJECT
IP-CIDR,203.0.113.7,DIRECT
GEOIP,cn,DIRECT,no-resolve
PORT,443,PROXY
MATCH,PROXY
`)
	if len(problems) != 0 {
		t.Fatalf("rejected lines that tools in circulation write: %v", problems)
	}
	if set.Len() != 6 {
		t.Fatalf("loaded %d rules, want 6", set.Len())
	}
	rules := set.Rules()
	if rules[0].Domain != "example.com" {
		t.Errorf("the name was not normalized: %q", rules[0].Domain)
	}
	if got := rules[2].Prefix.String(); got != "203.0.113.7/32" {
		t.Errorf("a bare address became %s, want a /32 host route", got)
	}
	if !rules[3].NoResolve {
		t.Error("no-resolve was parsed away rather than recorded")
	}
	if rules[5].Kind != KindFinal {
		t.Errorf("MATCH did not read as FINAL, got %s", rules[5].Kind)
	}
}

// A block written with bits below the mask is what the author meant, not a
// reason to fail their whole file.
func TestABlockWithHostBitsSetIsMasked(t *testing.T) {
	set := mustSet(t, "IP-CIDR,192.168.1.5/24,DIRECT\nFINAL,PROXY")
	if got := set.Rules()[0].Prefix.String(); got != "192.168.1.0/24" {
		t.Errorf("got %s, want the 192.168.1.0/24 the line meant", got)
	}
	if got, _, _ := set.Match(Flow{Addr: addr(t, "192.168.1.200")}); got != Direct {
		t.Errorf("an address in the block got %s, want DIRECT", got)
	}
}

// A stored list has to survive being shown to the user and read back.
func TestARuleRoundTripsThroughItsOwnSyntax(t *testing.T) {
	const text = `DOMAIN,example.com,DIRECT
DOMAIN-SUFFIX,example.org,PROXY
DOMAIN-KEYWORD,analytics,REJECT
IP-CIDR,10.0.0.0/8,DIRECT,no-resolve
GEOIP,CN,DIRECT
DST-PORT,853,REJECT
FINAL,PROXY`
	set := mustSet(t, text)
	var lines []string
	for _, rule := range set.Rules() {
		lines = append(lines, rule.Format())
	}
	if got := strings.Join(lines, "\n"); got != text {
		t.Errorf("round trip changed the list:\n%s\n---want---\n%s", got, text)
	}
}

// The exact-name index is an optimisation, and an optimisation that changes an
// answer is a bug. First match still wins across the two paths: a suffix rule
// above an exact rule for a name under it has to keep deciding.
func TestTheExactIndexDoesNotOutrankAnEarlierRule(t *testing.T) {
	set := mustSet(t, `
DOMAIN-SUFFIX,example.com,DIRECT
DOMAIN,www.example.com,REJECT
FINAL,PROXY
`)
	got, rule, _ := set.Match(Flow{Domain: "www.example.com"})
	if got != Direct || rule.Kind != KindDomainSuffix {
		t.Errorf("got %s from %s; the DOMAIN-SUFFIX rule is first in the file and "+
			"has to decide, whatever the index makes convenient", got, rule.Kind)
	}
}
