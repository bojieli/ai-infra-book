package routerule

import (
	"encoding/binary"
	"net/netip"
	"os"
	"path/filepath"
	"testing"
)

// pack builds a set in the generator's format, so the reader is tested against
// the layout rather than against itself.
func pack(t *testing.T, v4 []netip.Prefix, v6 []netip.Prefix) []byte {
	t.Helper()
	blob := append([]byte{}, packedMagic...)
	blob = append(blob, packedVersion, 0, 0, 0)
	blob = binary.BigEndian.AppendUint32(blob, uint32(len(v4)))
	blob = binary.BigEndian.AppendUint32(blob, uint32(len(v6)))
	for _, prefix := range v4 {
		address := prefix.Addr().As4()
		blob = append(blob, address[:]...)
		blob = append(blob, byte(prefix.Bits()))
	}
	for _, prefix := range v6 {
		address := prefix.Addr().As16()
		blob = append(blob, address[:]...)
		blob = append(blob, byte(prefix.Bits()))
	}
	return blob
}

func TestThePackedSetAnswersForBothFamilies(t *testing.T) {
	blob := pack(t,
		[]netip.Prefix{
			netip.MustParsePrefix("1.0.1.0/24"),
			netip.MustParsePrefix("14.0.0.0/8"),
			netip.MustParsePrefix("223.255.252.0/23"),
		},
		[]netip.Prefix{netip.MustParsePrefix("2400:3200::/32")},
	)
	set, err := LoadPacked("cn", blob)
	if err != nil {
		t.Fatalf("loading the set: %v", err)
	}
	if set.Blocks() != 4 {
		t.Errorf("reported %d blocks, want 4", set.Blocks())
	}
	if set.Code() != "CN" {
		t.Errorf("code is %q, want it upper-cased to CN", set.Code())
	}

	for _, test := range []struct {
		address string
		want    bool
	}{
		{"1.0.1.0", true},    // first address of the first block
		{"1.0.1.255", true},  // last address of it
		{"1.0.2.0", false},   // one past it
		{"1.0.0.255", false}, // one before it
		{"14.203.9.1", true}, // inside the largest block
		{"223.255.253.7", true},
		{"223.255.254.0", false},
		{"8.8.8.8", false},
		{"2400:3200::1", true},
		{"2001:db8::1", false},
	} {
		got := set.Contains("CN", netip.MustParseAddr(test.address))
		if got != test.want {
			t.Errorf("Contains(%s) = %v, want %v", test.address, got, test.want)
		}
	}
}

// The search takes one candidate, which is only sound because the generator
// collapses the set. Each block's edges are where an off-by-one shows up, and
// an off-by-one here is traffic taking the wrong path silently.
func TestEveryBlockEdgeIsAnsweredExactly(t *testing.T) {
	prefixes := []netip.Prefix{
		netip.MustParsePrefix("10.0.0.0/8"),
		netip.MustParsePrefix("172.16.0.0/12"),
		netip.MustParsePrefix("192.168.0.0/16"),
	}
	set, err := LoadPacked("XX", pack(t, prefixes, nil))
	if err != nil {
		t.Fatalf("loading the set: %v", err)
	}
	for _, prefix := range prefixes {
		first := prefix.Masked().Addr()
		if !set.Contains("XX", first) {
			t.Errorf("%s: the network address %s reads as outside the set", prefix, first)
		}
		last := lastAddress(prefix)
		if !set.Contains("XX", last) {
			t.Errorf("%s: the broadcast address %s reads as outside the set", prefix, last)
		}
		if next := last.Next(); set.Contains("XX", next) {
			t.Errorf("%s: %s is one past the block and reads as inside it", prefix, next)
		}
		if before := first.Prev(); set.Contains("XX", before) {
			t.Errorf("%s: %s is one before the block and reads as inside it", prefix, before)
		}
	}
}

func lastAddress(prefix netip.Prefix) netip.Addr {
	addr := prefix.Masked().Addr()
	bytes := addr.As4()
	host := 32 - prefix.Bits()
	value := binary.BigEndian.Uint32(bytes[:])
	value |= (uint32(1) << host) - 1
	binary.BigEndian.PutUint32(bytes[:], value)
	return netip.AddrFrom4(bytes)
}

// An unsorted set cannot be binary-searched, and the failure is silent: it
// answers "no" for addresses it holds, which sends Chinese traffic through the
// tunnel while the toggle says it is direct. Refuse it at load.
func TestAnUnsortedSetIsRefusedRatherThanSearched(t *testing.T) {
	blob := pack(t, []netip.Prefix{
		netip.MustParsePrefix("14.0.0.0/8"),
		netip.MustParsePrefix("1.0.1.0/24"),
	}, nil)
	if _, err := LoadPacked("CN", blob); err == nil {
		t.Fatal("an out-of-order set loaded; it would answer no for addresses it holds")
	}
}

func TestAMalformedSetIsRefused(t *testing.T) {
	good := pack(t, []netip.Prefix{netip.MustParsePrefix("1.0.1.0/24")}, nil)
	for _, test := range []struct {
		name string
		blob []byte
	}{
		{"too short for a header", good[:8]},
		{"wrong magic", append([]byte{'X', 'X', 'X', 'X'}, good[4:]...)},
		{"truncated body", good[:len(good)-2]},
	} {
		if _, err := LoadPacked("CN", test.blob); err == nil {
			t.Errorf("%s: loaded without complaint", test.name)
		}
	}
	future := append([]byte{}, good...)
	future[4] = packedVersion + 1
	if _, err := LoadPacked("CN", future); err == nil {
		t.Error("a future format version loaded; the layout it describes is not this one")
	}
}

// A set loaded for one country must not answer for another, or a
// GEOIP,JP,DIRECT rule would be decided by the China set.
func TestASetOnlyAnswersForItsOwnCountry(t *testing.T) {
	set, err := LoadPacked("CN", pack(t, []netip.Prefix{netip.MustParsePrefix("1.0.1.0/24")}, nil))
	if err != nil {
		t.Fatalf("loading the set: %v", err)
	}
	inside := netip.MustParseAddr("1.0.1.5")
	if !set.Contains("cn", inside) {
		t.Error("the code comparison is case-sensitive; rule files write both")
	}
	if set.Contains("JP", inside) {
		t.Error("the China set answered a rule about Japan")
	}
}

// The file the iOS client ships is the one this has to read. If the generator's
// layout and this reader ever disagree, the toggle silently stops matching, so
// the real artifact is part of the test rather than only a hand-built fixture.
func TestTheBundledChinaSetLoadsAndHoldsChineseAddresses(t *testing.T) {
	path := filepath.Join("..", "..", "mobile", "ios", "PacketTunnel", "Resources", "cn-direct.bin")
	blob, err := os.ReadFile(path)
	if err != nil {
		t.Skipf("the bundled set is not in this checkout: %v", err)
	}
	set, err := LoadPacked("CN", blob)
	if err != nil {
		t.Fatalf("the set the iOS client ships does not load: %v", err)
	}
	if set.Blocks() < 1000 {
		t.Errorf("the bundled set holds %d blocks, which is too few to be the registry set", set.Blocks())
	}
	// Well-known Chinese addresses: Alibaba and Tencent public resolvers.
	for _, address := range []string{"223.5.5.5", "119.29.29.29"} {
		if !set.Contains("CN", netip.MustParseAddr(address)) {
			t.Errorf("%s reads as outside the China set", address)
		}
	}
	// Well-known addresses outside it.
	for _, address := range []string{"8.8.8.8", "1.1.1.1"} {
		if set.Contains("CN", netip.MustParseAddr(address)) {
			t.Errorf("%s reads as inside the China set", address)
		}
	}
}

// The whole point of the set is answering a GEOIP rule, so wire the two
// together once here rather than only testing them apart.
func TestAGeoIPRuleDecidesFromThePackedSet(t *testing.T) {
	set, err := LoadPacked("CN", pack(t, []netip.Prefix{netip.MustParsePrefix("223.5.5.0/24")}, nil))
	if err != nil {
		t.Fatalf("loading the set: %v", err)
	}
	rules := mustSet(t, "GEOIP,CN,DIRECT\nFINAL,PROXY").WithCountries(set)
	if got, _, _ := rules.Match(Flow{Addr: netip.MustParseAddr("223.5.5.5")}); got != Direct {
		t.Errorf("a Chinese address got %s, want DIRECT", got)
	}
	if got, _, _ := rules.Match(Flow{Addr: netip.MustParseAddr("8.8.8.8")}); got != Proxy {
		t.Errorf("an address outside the set got %s, want PROXY", got)
	}
}
