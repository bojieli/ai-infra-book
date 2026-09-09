package routerule

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"net/netip"
	"sort"
	"strings"
)

// Packed answers GEOIP rules from the fixed-width set that
// scripts/generate_cn_geoip.py produces from registry delegation data. It is
// the same file mobile/ios/PacketTunnel/Resources/cn-direct.bin, read by the
// same rules as mobile/ios/Shared/CountryRoutes.swift, and scripts/
// test_cn_geoip.py holds the generator's half of the contract.
//
// The blob is kept as bytes and searched in place rather than parsed into
// prefixes. The China set is about seven and a half thousand v4 blocks, which
// is a quarter of a megabyte once it is netip.Prefix values, and this has to
// stay resident to answer a rule on every flow -- unlike the Swift reader,
// which builds the routes once at connect and drops them. docs/MOBILE-MEMORY.md
// is the budget that makes the difference matter: the packet-tunnel extension
// shares a fixed profile with the Go runtime.
//
// The entries are fixed-width and the generator emits them sorted and
// collapsed, which is what makes a binary search over the raw bytes possible at
// all. Load verifies both properties rather than trusting them, because a set
// that is not sorted answers "no" for addresses it holds, and a GEOIP,CN,DIRECT
// rule that answers "no" sends Chinese traffic through the tunnel silently --
// the exact failure this feature exists to remove.
type Packed struct {
	code string
	v4   []byte
	v6   []byte
}

const (
	packedHeaderSize = 16
	packedV4Entry    = 5
	packedV6Entry    = 17
	packedVersion    = 1
)

var packedMagic = []byte{0x51, 0x51, 0x47, 0x4F} // "QQGO"

// LoadPacked reads a packed set and binds it to a two-letter country code. The
// file itself does not name the country it holds -- it is generated per country
// and shipped under a name that says which -- so the caller supplies it.
func LoadPacked(code string, blob []byte) (*Packed, error) {
	if len(blob) < packedHeaderSize {
		return nil, fmt.Errorf("route set is %d bytes, too short for a header", len(blob))
	}
	if !bytes.Equal(blob[:4], packedMagic) {
		return nil, fmt.Errorf("route set does not carry the expected header")
	}
	if blob[4] != packedVersion {
		return nil, fmt.Errorf("route set is format version %d, which this build cannot read", blob[4])
	}
	v4Count := int(binary.BigEndian.Uint32(blob[8:12]))
	v6Count := int(binary.BigEndian.Uint32(blob[12:16]))
	expected := packedHeaderSize + v4Count*packedV4Entry + v6Count*packedV6Entry
	if len(blob) != expected {
		return nil, fmt.Errorf("route set should be %d bytes but is %d", expected, len(blob))
	}
	v4End := packedHeaderSize + v4Count*packedV4Entry
	packed := &Packed{
		code: strings.ToUpper(code),
		v4:   blob[packedHeaderSize:v4End],
		v6:   blob[v4End:],
	}
	if err := packed.verifySorted(); err != nil {
		return nil, err
	}
	return packed, nil
}

func (p *Packed) verifySorted() error {
	for _, family := range []struct {
		name  string
		body  []byte
		width int
	}{{"IPv4", p.v4, packedV4Entry}, {"IPv6", p.v6, packedV6Entry}} {
		count := len(family.body) / family.width
		for i := 1; i < count; i++ {
			previous := family.body[(i-1)*family.width : (i-1)*family.width+family.width-1]
			current := family.body[i*family.width : i*family.width+family.width-1]
			if bytes.Compare(previous, current) >= 0 {
				return fmt.Errorf(
					"%s entries %d and %d are not in ascending order; a set that is not "+
						"sorted cannot be searched and would answer no for addresses it holds",
					family.name, i-1, i)
			}
		}
	}
	return nil
}

// Contains reports whether the address is in the set this file carries.
//
// A code other than the one loaded reports false. A rule naming a set the build
// does not ship must not decide the flow -- it falls through to whatever the
// list says next, which is the same thing that happens when no set is loaded at
// all.
func (p *Packed) Contains(code string, addr netip.Addr) bool {
	if p == nil || !strings.EqualFold(code, p.code) || !addr.IsValid() {
		return false
	}
	addr = unmap(addr)
	if addr.Is4() {
		key := addr.As4()
		return search(p.v4, packedV4Entry, key[:])
	}
	key := addr.As16()
	return search(p.v6, packedV6Entry, key[:])
}

// search finds the last block whose network address is at or below the target
// and asks whether it covers it. One candidate is enough because the generator
// collapses the set: no block in it contains another, so if the greatest
// network at or below the address does not cover it, none does.
func search(body []byte, width int, key []byte) bool {
	addrLen := width - 1
	count := len(body) / width
	if count == 0 {
		return false
	}
	// The first entry strictly above the target; the candidate is the one
	// before it.
	above := sort.Search(count, func(i int) bool {
		return bytes.Compare(body[i*width:i*width+addrLen], key) > 0
	})
	if above == 0 {
		return false
	}
	entry := body[(above-1)*width : above*width]
	network, ok := netip.AddrFromSlice(entry[:addrLen])
	if !ok {
		return false
	}
	prefix := netip.PrefixFrom(network, int(entry[addrLen]))
	if !prefix.IsValid() {
		return false
	}
	target, ok := netip.AddrFromSlice(key)
	if !ok {
		return false
	}
	return prefix.Contains(target)
}

// Blocks reports how many blocks the set carries, so a screen can say how heavy
// a toggle is without holding the prefixes.
func (p *Packed) Blocks() int {
	if p == nil {
		return 0
	}
	return len(p.v4)/packedV4Entry + len(p.v6)/packedV6Entry
}

// Code reports the country this set was loaded for.
func (p *Packed) Code() string {
	if p == nil {
		return ""
	}
	return p.code
}
