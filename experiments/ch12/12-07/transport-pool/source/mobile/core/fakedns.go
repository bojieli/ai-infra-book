package mobilecore

import (
	"encoding/binary"
	"errors"
	"net/netip"
	"strings"
	"sync"
)

// fakeDNS answers name lookups from a reserved address range and remembers
// which name it handed each address to.
//
// It exists because of where the decision has to be made. The userspace stack
// hands this process IP packets, so a flow arrives at the forwarder carrying a
// destination address and nothing else, and a rule written DOMAIN-SUFFIX can
// never fire against it. docs/KNOWN-LIMITATIONS.md records what that costs
// today: the bundled China set matches addresses, DNS resolves through the
// tunnel from the gateway's vantage, and a Chinese domain that answers with an
// overseas CDN address takes the tunnel while the toggle says direct.
//
// So the lookup is answered here, from a range that means nothing to anybody
// else, and the address handed back becomes the name's handle for as long as
// the flow needs it. When the connection arrives the address is looked up, the
// name comes back, and the rule list sees what the user actually typed into
// their browser.
//
// The range is 198.18.0.0/15, which RFC 2544 reserves for benchmarking and
// which every tool doing this uses for the same reason: it is routable-looking
// enough that applications accept it and reserved enough that a packet reaching
// a real network with it is already a bug. Nothing is ever sent to these
// addresses -- they are a lookup key that happens to fit in an A record.
type fakeDNS struct {
	mu sync.Mutex

	base    netip.Addr
	size    uint32
	next    uint32
	byName  map[string]netip.Addr
	byAddr  map[netip.Addr]string
	order   []string // insertion order, for eviction
	enabled bool
}

// fakeDNSRange is the pool. /15 is 131072 addresses, which is far more names
// than a device has live at once; the eviction below is a bound on the map
// rather than something expected to run.
const (
	fakeDNSPrefix = "198.18.0.0/15"
	// fakeDNSPoolBits is the prefix length above, and fakeDNSPoolSize how many
	// addresses that holds. Both are constants rather than arithmetic on the
	// parsed prefix: the prefix is a literal, so the calculation never had an
	// input that could vary, and deriving it meant converting a bit count no
	// caller can influence. TestThePoolSizeMatchesItsPrefix keeps the two from
	// drifting apart.
	fakeDNSPoolBits = 15
	fakeDNSPoolSize = uint32(1) << (32 - fakeDNSPoolBits)
	fakeDNSCapacity = 8192
	// fakeDNSTTL is what the answer claims, in seconds. It is short because the
	// mapping is only meaningful to this process: a client that caches it past
	// a tunnel restart would hold an address whose name has been forgotten.
	fakeDNSTTL = 1
)

func newFakeDNS() *fakeDNS {
	prefix := netip.MustParsePrefix(fakeDNSPrefix)
	return &fakeDNS{
		base:    prefix.Masked().Addr(),
		size:    fakeDNSPoolSize,
		next:    2, // skip the network address and the one after it
		byName:  make(map[string]netip.Addr),
		byAddr:  make(map[netip.Addr]string),
		enabled: true,
	}
}

// Prefix reports the pool, so the tunnel can route it and the rule engine can
// recognise an address as a handle rather than a destination.
func (f *fakeDNS) Prefix() netip.Prefix { return netip.MustParsePrefix(fakeDNSPrefix) }

// Handle returns the address standing in for a name, allocating one if this is
// the first time the name has been seen.
func (f *fakeDNS) Handle(name string) (netip.Addr, bool) {
	name = normalizeName(name)
	if name == "" {
		return netip.Addr{}, false
	}
	f.mu.Lock()
	defer f.mu.Unlock()
	if addr, ok := f.byName[name]; ok {
		return addr, true
	}
	if len(f.order) >= fakeDNSCapacity {
		// Oldest first. A name whose flows are still open loses its handle,
		// which ends those flows rather than misrouting them: the address no
		// longer resolves to a name, and a flow to an unknown handle is
		// refused rather than sent somewhere arbitrary.
		oldest := f.order[0]
		f.order = f.order[1:]
		if addr, ok := f.byName[oldest]; ok {
			delete(f.byAddr, addr)
		}
		delete(f.byName, oldest)
	}
	addr := f.base
	for i := uint32(0); i < f.size; i++ {
		candidate := addAddr(f.base, f.next)
		f.next = (f.next + 1) % f.size
		if f.next < 2 {
			f.next = 2
		}
		if _, taken := f.byAddr[candidate]; !taken {
			addr = candidate
			break
		}
	}
	f.byName[name] = addr
	f.byAddr[addr] = name
	f.order = append(f.order, name)
	return addr, true
}

// Name returns the name an address was handed to, if it was handed to one.
func (f *fakeDNS) Name(addr netip.Addr) (string, bool) {
	f.mu.Lock()
	defer f.mu.Unlock()
	name, ok := f.byAddr[unmapAddr(addr)]
	return name, ok
}

// Holds reports whether an address belongs to the pool at all, whether or not
// it is currently allocated. A packet to an unallocated pool address is a stale
// client cache, and refusing it is better than dialing 198.18.x.y.
func (f *fakeDNS) Holds(addr netip.Addr) bool {
	return f.Prefix().Contains(unmapAddr(addr))
}

func addAddr(base netip.Addr, offset uint32) netip.Addr {
	raw := base.As4()
	value := binary.BigEndian.Uint32(raw[:]) + offset
	binary.BigEndian.PutUint32(raw[:], value)
	return netip.AddrFrom4(raw)
}

func unmapAddr(addr netip.Addr) netip.Addr {
	if addr.Is4In6() {
		return addr.Unmap()
	}
	return addr
}

func normalizeName(name string) string {
	return strings.TrimSuffix(strings.ToLower(strings.TrimSpace(name)), ".")
}

// The wire format below is only as much DNS as this needs: read the question
// from a query, and write an answer to it. Anything it cannot parse or does not
// handle is forwarded upstream unchanged, so a query type this does not know
// about behaves exactly as it did before this existed.

const (
	dnsTypeA     = 1
	dnsTypeAAAA  = 28
	dnsClassIN   = 1
	dnsHeaderLen = 12
	dnsMaxName   = 255
)

var errNotAQuery = errors.New("not a single-question DNS query")

type dnsQuestion struct {
	name     string
	qtype    uint16
	class    uint16
	queryEnd int
}

// parseDNSQuestion reads the one question out of a standard query. Compression
// pointers are refused rather than followed: a pointer in a question is not
// something a resolver emits, and following one is where DNS parsers get their
// loops.
func parseDNSQuestion(message []byte) (dnsQuestion, error) {
	if len(message) < dnsHeaderLen {
		return dnsQuestion{}, errNotAQuery
	}
	flags := binary.BigEndian.Uint16(message[2:4])
	if flags&0x8000 != 0 { // a response, not a query
		return dnsQuestion{}, errNotAQuery
	}
	if binary.BigEndian.Uint16(message[4:6]) != 1 { // exactly one question
		return dnsQuestion{}, errNotAQuery
	}
	var (
		labels []string
		offset = dnsHeaderLen
	)
	for {
		if offset >= len(message) {
			return dnsQuestion{}, errNotAQuery
		}
		length := int(message[offset])
		if length == 0 {
			offset++
			break
		}
		if length&0xC0 != 0 {
			return dnsQuestion{}, errNotAQuery
		}
		offset++
		if offset+length > len(message) {
			return dnsQuestion{}, errNotAQuery
		}
		labels = append(labels, string(message[offset:offset+length]))
		offset += length
	}
	if offset+4 > len(message) {
		return dnsQuestion{}, errNotAQuery
	}
	name := strings.Join(labels, ".")
	if len(name) > dnsMaxName {
		return dnsQuestion{}, errNotAQuery
	}
	return dnsQuestion{
		name:     normalizeName(name),
		qtype:    binary.BigEndian.Uint16(message[offset : offset+2]),
		class:    binary.BigEndian.Uint16(message[offset+2 : offset+4]),
		queryEnd: offset + 4,
	}, nil
}

// answerWithAddress builds a response carrying one A record. The question
// section is copied from the query rather than re-encoded, so the name in the
// answer is byte-identical to the one asked about.
func answerWithAddress(query []byte, question dnsQuestion, addr netip.Addr) []byte {
	response := make([]byte, 0, question.queryEnd+16)
	response = append(response, query[:question.queryEnd]...)
	// QR=1, RD copied from the query, RA=1.
	flags := uint16(0x8000) | uint16(0x0080)
	if binary.BigEndian.Uint16(query[2:4])&0x0100 != 0 {
		flags |= 0x0100
	}
	binary.BigEndian.PutUint16(response[2:4], flags)
	binary.BigEndian.PutUint16(response[6:8], 1) // one answer
	binary.BigEndian.PutUint16(response[8:10], 0)
	binary.BigEndian.PutUint16(response[10:12], 0)

	response = append(response, 0xC0, dnsHeaderLen) // pointer to the question's name
	response = binary.BigEndian.AppendUint16(response, dnsTypeA)
	response = binary.BigEndian.AppendUint16(response, dnsClassIN)
	response = binary.BigEndian.AppendUint32(response, fakeDNSTTL)
	response = binary.BigEndian.AppendUint16(response, 4)
	value := addr.As4()
	return append(response, value[:]...)
}

// answerEmpty builds a response with no records, used for a question this
// answers by name but cannot answer with an A record -- an AAAA query for a
// name whose handle is v4. NOERROR with no answer is what a name with no
// record of that type looks like, and it makes the client ask for A instead of
// waiting for a timeout.
func answerEmpty(query []byte, question dnsQuestion) []byte {
	response := make([]byte, 0, question.queryEnd)
	response = append(response, query[:question.queryEnd]...)
	flags := uint16(0x8000) | uint16(0x0080)
	if binary.BigEndian.Uint16(query[2:4])&0x0100 != 0 {
		flags |= 0x0100
	}
	binary.BigEndian.PutUint16(response[2:4], flags)
	binary.BigEndian.PutUint16(response[6:8], 0)
	binary.BigEndian.PutUint16(response[8:10], 0)
	binary.BigEndian.PutUint16(response[10:12], 0)
	return response
}
