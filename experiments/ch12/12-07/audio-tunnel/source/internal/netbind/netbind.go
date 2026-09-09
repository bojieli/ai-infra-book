// Package netbind resolves operator-friendly local-address specifications for
// connections that must bypass a host TUN route.
package netbind

import (
	"errors"
	"fmt"
	"net"
	"net/netip"
	"sort"
	"strings"
)

// Validate checks a literal IP, "auto", or "if:NAME" without requiring the
// interface to be present yet. Interface state can change between validation
// and a later dial, so Resolve repeats this check.
func Validate(spec string) error {
	if spec == "" || spec == "auto" {
		return nil
	}
	if strings.HasPrefix(spec, "if:") {
		if strings.TrimSpace(strings.TrimPrefix(spec, "if:")) == "" {
			return errors.New("interface name after if: must not be empty")
		}
		return nil
	}
	if _, err := netip.ParseAddr(spec); err != nil {
		return fmt.Errorf("%q is not auto, if:NAME, or an IP address: %w", spec, err)
	}
	return nil
}

type candidate struct {
	interfaceName string
	address       netip.Addr
}

// IsDynamic reports whether resolving spec depends on live interface state.
// Literal addresses are stable configuration; automatic and interface-bound
// specifications can disappear and reappear as links change.
func IsDynamic(spec string) bool {
	return spec == "auto" || strings.HasPrefix(spec, "if:")
}

// ResolveResult is the outcome of resolving a local-address spec.
type ResolveResult struct {
	Addr netip.Addr
	// InterfaceName is the name of the physical interface the address belongs
	// to. It is set for "if:NAME" and "auto" specs, and empty for a literal IP
	// (where the interface is inferred from routing, not specified by the
	// operator). Callers can pass this name to InterfaceControl to assert the
	// OS-level interface binding (IP_BOUND_IF / IPV6_BOUND_IF) that makes
	// NEAppProxyFlow.isBound true in macOS Network Extensions.
	InterfaceName string
}

// ResolveWithInterface is like Resolve but also returns the interface name.
func ResolveWithInterface(spec string) (ResolveResult, error) {
	addr, ifName, err := resolve(spec)
	return ResolveResult{Addr: addr, InterfaceName: ifName}, err
}

// Resolve returns the address selected by a literal IP, "if:NAME", or
// "auto". Automatic and interface modes deliberately consider only IPv4
// addresses on active, non-loopback, non-point-to-point interfaces. Excluding
// point-to-point interfaces prevents a Clash or other host TUN from being
// selected as the outer path. Ambiguity is reported instead of guessing.
func Resolve(spec string) (netip.Addr, error) {
	addr, _, err := resolve(spec)
	return addr, err
}

func resolve(spec string) (netip.Addr, string, error) {
	if err := Validate(spec); err != nil {
		return netip.Addr{}, "", err
	}
	if spec != "" && !IsDynamic(spec) {
		// Literal IP: interface is inferred from routing, not declared.
		addr, err := netip.ParseAddr(spec)
		return addr, "", err
	}

	wantedInterface := ""
	if strings.HasPrefix(spec, "if:") {
		wantedInterface = strings.TrimSpace(strings.TrimPrefix(spec, "if:"))
	}
	interfaces, err := net.Interfaces()
	if err != nil {
		return netip.Addr{}, "", fmt.Errorf("enumerate local interfaces: %w", err)
	}
	candidates := make([]candidate, 0, 2)
	for _, iface := range interfaces {
		if wantedInterface != "" && iface.Name != wantedInterface {
			continue
		}
		if iface.Flags&net.FlagUp == 0 || iface.Flags&(net.FlagLoopback|net.FlagPointToPoint) != 0 {
			continue
		}
		addresses, addressErr := iface.Addrs()
		if addressErr != nil {
			continue
		}
		for _, raw := range addresses {
			prefix, parseErr := netip.ParsePrefix(raw.String())
			if parseErr != nil {
				continue
			}
			address := prefix.Addr().Unmap()
			if !address.Is4() || address.IsLoopback() || address.IsLinkLocalUnicast() || address.IsMulticast() || address.IsUnspecified() {
				continue
			}
			candidates = append(candidates, candidate{interfaceName: iface.Name, address: address})
		}
	}
	if len(candidates) == 0 {
		if wantedInterface != "" {
			return netip.Addr{}, "", fmt.Errorf("interface %q has no active IPv4 address; check its name and network connection", wantedInterface)
		}
		return netip.Addr{}, "", errors.New("no active physical IPv4 address found; use --local-address with an interface name or IP address")
	}
	sort.Slice(candidates, func(i, j int) bool {
		if candidates[i].interfaceName != candidates[j].interfaceName {
			return candidates[i].interfaceName < candidates[j].interfaceName
		}
		return candidates[i].address.Less(candidates[j].address)
	})
	first := candidates[0]
	for _, other := range candidates[1:] {
		if other.address != first.address {
			return netip.Addr{}, "", fmt.Errorf("more than one physical IPv4 address is active (%s on %s and %s on %s); choose one with --local-address if:NAME", first.address, first.interfaceName, other.address, other.interfaceName)
		}
	}
	return first.address, first.interfaceName, nil
}
