package mobilecore

import (
	"encoding/binary"
	"io"
	"net"
	"net/netip"
	"strings"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/routerule"
)

func rulesFrom(t *testing.T, text string) *routerule.Set {
	t.Helper()
	set, problems := routerule.Parse(text)
	if len(problems) != 0 {
		t.Fatalf("test rule list did not parse: %v", problems)
	}
	return set
}

// query builds a standard A or AAAA question, so the resolver is tested against
// the wire form rather than against its own parser.
func query(name string, qtype uint16) []byte {
	message := make([]byte, dnsHeaderLen)
	binary.BigEndian.PutUint16(message[0:2], 0x1234)
	binary.BigEndian.PutUint16(message[2:4], 0x0100) // standard query, recursion desired
	binary.BigEndian.PutUint16(message[4:6], 1)
	for _, label := range strings.Split(name, ".") {
		message = append(message, byte(len(label)))
		message = append(message, label...)
	}
	message = append(message, 0)
	message = binary.BigEndian.AppendUint16(message, qtype)
	return binary.BigEndian.AppendUint16(message, dnsClassIN)
}

func TestAQuestionIsReadOffTheWire(t *testing.T) {
	question, err := parseDNSQuestion(query("WWW.Example.COM", dnsTypeA))
	if err != nil {
		t.Fatalf("parsing a standard query: %v", err)
	}
	if question.name != "www.example.com" {
		t.Errorf("name is %q, want it lowered to www.example.com", question.name)
	}
	if question.qtype != dnsTypeA || question.class != dnsClassIN {
		t.Errorf("type/class are %d/%d, want %d/%d", question.qtype, question.class, dnsTypeA, dnsClassIN)
	}
}

// A compression pointer in a question is not something a resolver emits, and
// following one is where DNS parsers acquire their loops. Refuse rather than
// chase, and let the flow fall through to the tunnel untouched.
func TestACompressedOrMalformedQuestionIsRefused(t *testing.T) {
	for _, test := range []struct {
		name    string
		message []byte
	}{
		{"a pointer where a length belongs", append(query("a.example.com", dnsTypeA)[:dnsHeaderLen], 0xC0, 0x0C)},
		{"shorter than a header", []byte{1, 2, 3}},
		{"a response rather than a query", func() []byte {
			m := query("a.example.com", dnsTypeA)
			binary.BigEndian.PutUint16(m[2:4], 0x8180)
			return m
		}()},
		{"two questions", func() []byte {
			m := query("a.example.com", dnsTypeA)
			binary.BigEndian.PutUint16(m[4:6], 2)
			return m
		}()},
		{"a label running past the end", append(query("a.example.com", dnsTypeA)[:dnsHeaderLen], 40, 'a', 'b')},
	} {
		if _, err := parseDNSQuestion(test.message); err == nil {
			t.Errorf("%s: parsed without complaint", test.name)
		}
	}
}

// The handle is what makes a name rule possible, so the same name has to come
// back to the same address and a different name to a different one.
func TestAHandleIsStableAndReversible(t *testing.T) {
	dns := newFakeDNS()
	first, ok := dns.Handle("example.com")
	if !ok {
		t.Fatal("no handle for a plain name")
	}
	again, _ := dns.Handle("Example.COM.")
	if first != again {
		t.Errorf("the same name got two handles, %s and %s", first, again)
	}
	other, _ := dns.Handle("example.org")
	if other == first {
		t.Errorf("two names share the handle %s", first)
	}
	if !dns.Holds(first) {
		t.Errorf("%s is not recognised as belonging to the pool", first)
	}
	name, ok := dns.Name(first)
	if !ok || name != "example.com" {
		t.Errorf("%s reversed to %q/%v, want example.com", first, name, ok)
	}
	if _, ok := dns.Name(netip.MustParseAddr("8.8.8.8")); ok {
		t.Error("an ordinary address reversed to a name")
	}
}

// An answer has to be one an ordinary resolver will accept: the question echoed
// back, the response bit set, one A record, and the handle in it.
func TestTheAnswerCarriesTheHandle(t *testing.T) {
	dns := newFakeDNS()
	handle, _ := dns.Handle("example.com")
	request := query("example.com", dnsTypeA)
	question, err := parseDNSQuestion(request)
	if err != nil {
		t.Fatalf("parsing: %v", err)
	}
	response := answerWithAddress(request, question, handle)

	if binary.BigEndian.Uint16(response[0:2]) != binary.BigEndian.Uint16(request[0:2]) {
		t.Error("the transaction ID was not echoed")
	}
	if binary.BigEndian.Uint16(response[2:4])&0x8000 == 0 {
		t.Error("the response bit is not set, so a resolver will ignore this")
	}
	if got := binary.BigEndian.Uint16(response[6:8]); got != 1 {
		t.Fatalf("the answer count is %d, want 1", got)
	}
	record := response[question.queryEnd:]
	if record[0] != 0xC0 || record[1] != dnsHeaderLen {
		t.Error("the answer does not point at the question's name")
	}
	if got := binary.BigEndian.Uint16(record[2:4]); got != dnsTypeA {
		t.Errorf("record type is %d, want A", got)
	}
	if got := binary.BigEndian.Uint16(record[10:12]); got != 4 {
		t.Fatalf("record length is %d, want 4", got)
	}
	var address [4]byte
	copy(address[:], record[12:16])
	if netip.AddrFrom4(address) != handle {
		t.Errorf("the record carries %s, want the handle %s", netip.AddrFrom4(address), handle)
	}
}

// An AAAA question for a name whose handle is v4 is answered with no records
// rather than left silent, so the client asks for A now instead of waiting out
// a timeout.
func TestAnAAAAQuestionIsAnsweredEmptyRatherThanIgnored(t *testing.T) {
	request := query("example.com", dnsTypeAAAA)
	question, err := parseDNSQuestion(request)
	if err != nil {
		t.Fatalf("parsing: %v", err)
	}
	response := answerEmpty(request, question)
	if binary.BigEndian.Uint16(response[2:4])&0x8000 == 0 {
		t.Error("the response bit is not set")
	}
	if binary.BigEndian.Uint16(response[2:4])&0x000F != 0 {
		t.Error("the response carries an error code; NOERROR with no answer is what no record of this type looks like")
	}
	if got := binary.BigEndian.Uint16(response[6:8]); got != 0 {
		t.Errorf("answer count is %d, want 0", got)
	}
}

// The whole path: a name is looked up, gets a handle, and a connection to that
// handle is decided by a rule written about the name.
func TestAConnectionToAHandleIsDecidedByName(t *testing.T) {
	dns := newFakeDNS()
	r := newRouter(rulesFrom(t, "DOMAIN-SUFFIX,example.com,DIRECT\nFINAL,PROXY"), dns)

	handle, _ := dns.Handle("www.example.com")
	verdict := r.route(netip.AddrPortFrom(handle, 443))
	if verdict.action != routerule.Direct {
		t.Errorf("a flow to the handle for www.example.com got %s, want DIRECT", verdict.action)
	}
	if verdict.host != "www.example.com" {
		t.Errorf("the flow carries host %q, want the name", verdict.host)
	}
	if verdict.target() != "www.example.com:443" {
		t.Errorf("target is %q, want the name and port", verdict.target())
	}
}

// A proxied flow to a handle must dial by name. The handle means nothing off
// this device, and sending it to the gateway asks it to connect to a
// benchmarking address on its own network.
func TestAProxiedFlowToAHandleDialsByName(t *testing.T) {
	dns := newFakeDNS()
	r := newRouter(rulesFrom(t, "FINAL,PROXY"), dns)
	handle, _ := dns.Handle("example.org")
	verdict := r.route(netip.AddrPortFrom(handle, 80))
	if verdict.action != routerule.Proxy {
		t.Fatalf("got %s, want PROXY", verdict.action)
	}
	if verdict.host == "" {
		t.Fatal("a proxied flow to a handle has no name to dial, so the handle would go on the wire")
	}
	request, err := socksDomainRequest(socksConnect, verdict.host, verdict.addr.Port())
	if err != nil {
		t.Fatalf("building the request: %v", err)
	}
	if request[3] != socksDomain {
		t.Errorf("address type is %d, want the domain form %d", request[3], socksDomain)
	}
	if got := string(request[5 : 5+int(request[4])]); got != "example.org" {
		t.Errorf("the request names %q, want example.org", got)
	}
}

// A handle the map has forgotten is refused. There is nothing to dial: the
// address is not a destination and the name is gone, so anything other than a
// refusal is a connection to 198.18.x.y.
func TestAForgottenHandleIsRefused(t *testing.T) {
	dns := newFakeDNS()
	r := newRouter(rulesFrom(t, "FINAL,PROXY"), dns)
	unallocated := netip.MustParseAddr("198.18.200.200")
	verdict := r.route(netip.AddrPortFrom(unallocated, 443))
	if verdict.action != routerule.Reject || !verdict.stale {
		t.Errorf("got %s (stale=%v), want a refusal", verdict.action, verdict.stale)
	}
	if r.snapshot().Stale != 1 {
		t.Error("the refusal was not counted, so an operator cannot see it happening")
	}
}

// A flow to a literal address is decided by address rules, and carries no name
// to dial by.
func TestAFlowToALiteralAddressIsDecidedByAddress(t *testing.T) {
	r := newRouter(rulesFrom(t, "IP-CIDR,203.0.113.0/24,DIRECT\nFINAL,PROXY"), newFakeDNS())
	verdict := r.route(netip.MustParseAddrPort("203.0.113.9:443"))
	if verdict.action != routerule.Direct {
		t.Errorf("got %s, want DIRECT", verdict.action)
	}
	if verdict.host != "" {
		t.Errorf("a literal address produced host %q, want none", verdict.host)
	}
	if verdict.target() != "203.0.113.9:443" {
		t.Errorf("target is %q", verdict.target())
	}
}

// With no rules loaded, everything takes the tunnel. This is the state every
// existing installation is in, and it has to keep behaving exactly as it did.
func TestWithNoRulesEverythingTakesTheTunnel(t *testing.T) {
	r := newRouter(nil, newFakeDNS())
	if r.active() {
		t.Error("a router with no rules reports itself active")
	}
	for _, address := range []string{"203.0.113.9:443", "8.8.8.8:53"} {
		verdict := r.route(netip.MustParseAddrPort(address))
		if verdict.action != routerule.Proxy {
			t.Errorf("%s got %s with no rules loaded, want PROXY", address, verdict.action)
		}
	}
}

// The counters are what make routing answerable from outside. Zero rules with
// traffic flowing is a different fault from a loaded list whose DIRECT count
// never moves.
func TestTheSnapshotSeparatesEachOutcome(t *testing.T) {
	dns := newFakeDNS()
	r := newRouter(rulesFrom(t, `
DOMAIN-SUFFIX,blocked.example,REJECT
DOMAIN-SUFFIX,direct.example,DIRECT
FINAL,PROXY
`), dns)
	blocked, _ := dns.Handle("blocked.example")
	direct, _ := dns.Handle("direct.example")
	proxied, _ := dns.Handle("elsewhere.example")
	r.route(netip.AddrPortFrom(blocked, 443))
	r.route(netip.AddrPortFrom(direct, 443))
	r.route(netip.AddrPortFrom(proxied, 443))
	r.route(netip.MustParseAddrPort("8.8.8.8:443"))

	got := r.snapshot()
	if got.Rules != 3 {
		t.Errorf("rules loaded is %d, want 3", got.Rules)
	}
	if got.Rejected != 1 || got.Directed != 1 || got.Proxied != 2 {
		t.Errorf("outcomes are reject=%d direct=%d proxy=%d, want 1/1/2",
			got.Rejected, got.Directed, got.Proxied)
	}
	if got.Named != 3 {
		t.Errorf("named flows is %d, want the 3 that went through a handle", got.Named)
	}
}

// The session API is what the clients call, so its report has to say what
// loaded and what did not.
func TestSetRoutingRulesReportsWhatItLoaded(t *testing.T) {
	session := &Session{}
	report := session.SetRoutingRules("DOMAIN-SUFFIX,example.com,DIRECT\nNOT-A-RULE\nFINAL,PROXY")
	if !strings.Contains(report, `"loaded":2`) {
		t.Errorf("report does not say two rules loaded: %s", report)
	}
	if !strings.Contains(report, "line 2") {
		t.Errorf("report does not name the line that failed: %s", report)
	}
	if session.RoutingRuleCount() != 2 {
		t.Errorf("count is %d, want 2", session.RoutingRuleCount())
	}
	if session.boundRules() == nil {
		t.Fatal("no bound rule set after loading rules")
	}
	// Clearing returns the tunnel to carrying everything.
	session.SetRoutingRules("")
	if session.RoutingRuleCount() != 0 || session.boundRules() != nil {
		t.Error("an empty list did not clear the rules")
	}
}

// A GEOIP rule is answered from a set the client installed, and only for the
// country it was installed as.
func TestSetCountrySetBacksGeoIPRules(t *testing.T) {
	session := &Session{}
	blob := packCountrySet(t, "223.5.5.0/24")
	if err := session.SetCountrySet("cn", blob); err != nil {
		t.Fatalf("installing the set: %v", err)
	}
	session.SetRoutingRules("GEOIP,CN,DIRECT\nFINAL,PROXY")
	rules := session.boundRules()
	if got, _, _ := rules.Match(routerule.Flow{Addr: netip.MustParseAddr("223.5.5.5")}); got != routerule.Direct {
		t.Errorf("a Chinese address got %s, want DIRECT", got)
	}
	if got, _, _ := rules.Match(routerule.Flow{Addr: netip.MustParseAddr("8.8.8.8")}); got != routerule.Proxy {
		t.Errorf("an address outside the set got %s, want PROXY", got)
	}
	if err := session.SetCountrySet("CN", []byte("not a route set")); err == nil {
		t.Error("a malformed set installed without complaint")
	}
}

func packCountrySet(t *testing.T, prefixes ...string) []byte {
	t.Helper()
	blob := []byte{0x51, 0x51, 0x47, 0x4F, 1, 0, 0, 0}
	blob = binary.BigEndian.AppendUint32(blob, uint32(len(prefixes)))
	blob = binary.BigEndian.AppendUint32(blob, 0)
	for _, text := range prefixes {
		prefix := netip.MustParsePrefix(text)
		address := prefix.Addr().As4()
		blob = append(blob, address[:]...)
		blob = append(blob, byte(prefix.Bits()))
	}
	return blob
}

// Nothing that arrives on port 53 may be swallowed. The resolver reads a
// datagram to look at it, and everything it will not answer has to come back so
// the caller can forward it: a query shape this parser does not cover, and any
// non-DNS use of the port, must behave exactly as it did before the resolver
// existed. TestPacketFlowCallbackForwardsIPv4UDP sends precisely that and was
// broken by an earlier version of this code.
func TestTheResolverHandsBackWhatItWillNotAnswer(t *testing.T) {
	for _, test := range []struct {
		name     string
		datagram []byte
	}{
		{"not DNS at all", []byte("packet-flow")},
		{"a query type this does not answer", query("example.com", 15 /* MX */)},
		{"a response rather than a query", func() []byte {
			m := query("example.com", dnsTypeA)
			binary.BigEndian.PutUint16(m[2:4], 0x8180)
			return m
		}()},
	} {
		stack := &packetStack{route: newRouter(nil, newFakeDNS()), log: func(string, string) {}}
		inner := &recordingConn{read: test.datagram}
		handled, pending := stack.serveDNS(inner)
		if handled {
			t.Errorf("%s: reported as handled, so it would be dropped", test.name)
		}
		if string(pending) != string(test.datagram) {
			t.Errorf("%s: handed back %q, want the datagram unchanged", test.name, pending)
		}
		if len(inner.written) != 0 {
			t.Errorf("%s: answered something it does not understand", test.name)
		}
	}
}

// And a query it does answer is answered, and not forwarded as well.
func TestTheResolverAnswersAQueryItUnderstands(t *testing.T) {
	stack := &packetStack{route: newRouter(nil, newFakeDNS()), log: func(string, string) {}}
	inner := &recordingConn{read: query("example.com", dnsTypeA)}
	handled, pending := stack.serveDNS(inner)
	if !handled || pending != nil {
		t.Fatalf("handled=%v pending=%v, want it answered and nothing forwarded", handled, pending)
	}
	if len(inner.written) == 0 {
		t.Fatal("nothing was written back to the flow")
	}
	if binary.BigEndian.Uint16(inner.written[6:8]) != 1 {
		t.Error("the answer carries no record")
	}
}

// recordingConn is one datagram in, whatever is written out.
type recordingConn struct {
	net.Conn
	read    []byte
	done    bool
	written []byte
}

func (c *recordingConn) Read(p []byte) (int, error) {
	if c.done {
		return 0, io.EOF
	}
	c.done = true
	return copy(p, c.read), nil
}

func (c *recordingConn) Write(p []byte) (int, error) {
	c.written = append(c.written, p...)
	return len(p), nil
}

func (c *recordingConn) SetReadDeadline(time.Time) error  { return nil }
func (c *recordingConn) SetWriteDeadline(time.Time) error { return nil }

// The pool size is written as a constant, so nothing derives it from the
// prefix at run time. This is what stops the two drifting apart.
func TestThePoolSizeMatchesItsPrefix(t *testing.T) {
	prefix := netip.MustParsePrefix(fakeDNSPrefix)
	if prefix.Bits() != fakeDNSPoolBits {
		t.Fatalf("%s is a /%d, but the constant says /%d", fakeDNSPrefix, prefix.Bits(), fakeDNSPoolBits)
	}
	if want := uint64(1) << (32 - prefix.Bits()); want != uint64(fakeDNSPoolSize) {
		t.Errorf("the pool holds %d addresses, but the constant says %d", want, fakeDNSPoolSize)
	}
}
