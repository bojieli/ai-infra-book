package routerule

import (
	"fmt"
	"net/netip"
	"strconv"
	"strings"
)

// Problem is a line that did not become a rule, and why.
//
// Parsing reports rather than drops. A rule list is a security boundary --
// every line in it is somebody saying "this must not take the tunnel", or
// "this must" -- and a parser that skips what it does not understand turns a
// typo into traffic going somewhere the user did not intend, silently and for
// as long as the file lives. The caller decides whether to refuse the list or
// to run it and show what was lost; it cannot decide either without being told.
type Problem struct {
	Line   int
	Text   string
	Reason string
}

func (p Problem) String() string {
	return fmt.Sprintf("line %d: %s: %s", p.Line, p.Reason, p.Text)
}

// Parse reads a rule list.
//
// The accepted form is one rule per line, `TYPE,VALUE,ACTION`, with FINAL
// taking `FINAL,ACTION` because it has nothing to match on. Blank lines and
// lines beginning with # or ; are ignored, as is anything after a trailing
// `,no-resolve`, which is recorded rather than rejected. Type and action names
// are case-insensitive; a comma inside a value is not supported by any tool
// using this syntax and is not supported here.
//
// A list with problems still returns the rules that parsed, in order. That is
// what lets a caller show "these 4 lines of your 900 did not load" instead of
// refusing the file, and it is why Problem carries the line number.
func Parse(text string) (*Set, []Problem) {
	var (
		rules    []Rule
		problems []Problem
	)
	for i, raw := range strings.Split(text, "\n") {
		line := strings.TrimSpace(raw)
		if line == "" || strings.HasPrefix(line, "#") || strings.HasPrefix(line, ";") {
			continue
		}
		rule, err := parseLine(line)
		if err != nil {
			problems = append(problems, Problem{Line: i + 1, Text: line, Reason: err.Error()})
			continue
		}
		rules = append(rules, rule)
	}
	return &Set{rules: rules}, problems
}

func parseLine(line string) (Rule, error) {
	fields := strings.Split(line, ",")
	for i := range fields {
		fields[i] = strings.TrimSpace(fields[i])
	}
	kind, err := parseKind(fields[0])
	if err != nil {
		return Rule{}, err
	}
	rule := Rule{Kind: kind}

	if kind == KindFinal {
		// FINAL,PROXY -- and FINAL,PROXY,dns-failed and similar tails exist in
		// the wild, so anything past the action is ignored rather than refused.
		if len(fields) < 2 {
			return Rule{}, fmt.Errorf("FINAL needs an action")
		}
		if rule.Action, err = parseAction(fields[1]); err != nil {
			return Rule{}, err
		}
		return rule, nil
	}

	if len(fields) < 3 {
		return Rule{}, fmt.Errorf("expected TYPE,VALUE,ACTION")
	}
	value := fields[1]
	if value == "" {
		return Rule{}, fmt.Errorf("%s needs a value", kind)
	}
	if rule.Action, err = parseAction(fields[2]); err != nil {
		return Rule{}, err
	}
	for _, option := range fields[3:] {
		switch strings.ToLower(option) {
		case "no-resolve":
			rule.NoResolve = true
		case "":
		default:
			return Rule{}, fmt.Errorf("unknown option %q", option)
		}
	}

	switch kind {
	case KindDomain, KindDomainSuffix, KindDomainKeyword:
		rule.Domain = normalizeDomain(value)
		if rule.Domain == "" {
			return Rule{}, fmt.Errorf("%s needs a name", kind)
		}
	case KindIPCIDR:
		prefix, err := parsePrefix(value)
		if err != nil {
			return Rule{}, err
		}
		rule.Prefix = prefix
	case KindGeoIP:
		rule.Country = strings.ToUpper(value)
	case KindDstPort:
		port, err := strconv.ParseUint(value, 10, 16)
		if err != nil || port == 0 {
			return Rule{}, fmt.Errorf("%q is not a port", value)
		}
		rule.Port = uint16(port)
	}
	return rule, nil
}

// parsePrefix accepts a block, and also a bare address, which the lists in
// circulation use for a single host. Masked() is applied so that a rule written
// 192.168.1.5/24 -- which netip rejects as having bits set below the mask --
// still means the /24 the author meant rather than failing the whole file.
func parsePrefix(value string) (netip.Prefix, error) {
	if prefix, err := netip.ParsePrefix(value); err == nil {
		return prefix.Masked(), nil
	}
	addr, err := netip.ParseAddr(value)
	if err != nil {
		return netip.Prefix{}, fmt.Errorf("%q is not an address or block", value)
	}
	addr = unmap(addr)
	return netip.PrefixFrom(addr, addr.BitLen()), nil
}

func parseKind(name string) (Kind, error) {
	switch strings.ToUpper(name) {
	case "DOMAIN":
		return KindDomain, nil
	case "DOMAIN-SUFFIX":
		return KindDomainSuffix, nil
	case "DOMAIN-KEYWORD":
		return KindDomainKeyword, nil
	case "IP-CIDR", "IP-CIDR6", "IP6-CIDR":
		// One kind, three spellings. The tools split them because their
		// matchers were written per family; netip is not, and a v6 block in an
		// IP-CIDR rule matches v6 addresses whatever the line called itself.
		return KindIPCIDR, nil
	case "GEOIP":
		return KindGeoIP, nil
	case "DST-PORT", "PORT":
		return KindDstPort, nil
	case "FINAL", "MATCH":
		return KindFinal, nil
	default:
		return 0, fmt.Errorf("unknown rule type %q", name)
	}
}

func parseAction(name string) (Action, error) {
	switch strings.ToUpper(name) {
	case "PROXY", "QUEQIAO":
		return Proxy, nil
	case "DIRECT":
		return Direct, nil
	case "REJECT", "REJECT-DROP":
		return Reject, nil
	default:
		// A named proxy group is the one thing this deliberately will not
		// guess at. Queqiao has one tunnel, so a line naming a group cannot be
		// honoured, and quietly reading it as PROXY would send traffic through
		// the one tunnel a multi-group file was written to keep off it.
		return 0, fmt.Errorf("unknown action %q: this client has one tunnel, so only PROXY, DIRECT and REJECT", name)
	}
}

// Format renders a rule back to the line syntax, so that a list can be shown
// and stored in the form the user typed it.
func (r Rule) Format() string {
	var value string
	switch r.Kind {
	case KindFinal:
		return fmt.Sprintf("FINAL,%s", r.Action)
	case KindDomain, KindDomainSuffix, KindDomainKeyword:
		value = r.Domain
	case KindIPCIDR:
		value = r.Prefix.String()
	case KindGeoIP:
		value = r.Country
	case KindDstPort:
		value = strconv.Itoa(int(r.Port))
	}
	line := fmt.Sprintf("%s,%s,%s", r.Kind, value, r.Action)
	if r.NoResolve {
		line += ",no-resolve"
	}
	return line
}
