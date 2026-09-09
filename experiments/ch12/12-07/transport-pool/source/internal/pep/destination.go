package pep

import (
	"context"
	"errors"
	"fmt"
	"net"
	"net/netip"
	"strconv"
	"time"
)

type DestinationPolicy struct {
	AllowPrivate bool
	DialTimeout  time.Duration
}

var additionallyForbidden = []netip.Prefix{
	netip.MustParsePrefix("0.0.0.0/8"),
	netip.MustParsePrefix("100.64.0.0/10"),
	netip.MustParsePrefix("192.0.0.0/24"),
	netip.MustParsePrefix("192.0.2.0/24"),
	netip.MustParsePrefix("192.88.99.0/24"),
	netip.MustParsePrefix("198.18.0.0/15"),
	netip.MustParsePrefix("198.51.100.0/24"),
	netip.MustParsePrefix("203.0.113.0/24"),
	netip.MustParsePrefix("240.0.0.0/4"),
	// IPv4-translation prefixes can encode a private IPv4 destination in an
	// address that netip classifies as global IPv6. Reject them at this layer
	// instead of relying on every NAT64 or 6to4 relay to enforce RFC filtering.
	netip.MustParsePrefix("64:ff9b::/96"),
	netip.MustParsePrefix("64:ff9b:1::/48"),
	netip.MustParsePrefix("2002::/16"),
	// Current IANA non-global special-purpose ranges that otherwise satisfy
	// IsGlobalUnicast. Loopback, ULA, link-local, and multicast are handled by
	// the standard netip predicates below.
	netip.MustParsePrefix("100::/64"),
	netip.MustParsePrefix("100:0:0:1::/64"),
	netip.MustParsePrefix("2001:2::/48"),
	netip.MustParsePrefix("2001:10::/28"),
	netip.MustParsePrefix("2001:db8::/32"),
	netip.MustParsePrefix("3fff::/20"),
	netip.MustParsePrefix("5f00::/16"),
}

func (p DestinationPolicy) DialContext(ctx context.Context, destination string) (net.Conn, error) {
	host, port, err := parseDestination(destination)
	if err != nil {
		return nil, err
	}
	timeout := p.DialTimeout
	if timeout <= 0 {
		timeout = 10 * time.Second
	}
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	var addresses []net.IPAddr
	if parsed := net.ParseIP(host); parsed != nil {
		addresses = []net.IPAddr{{IP: parsed}}
	} else {
		addresses, err = net.DefaultResolver.LookupIPAddr(ctx, host)
		if err != nil {
			return nil, errors.New("destination resolution failed")
		}
	}
	if len(addresses) == 0 {
		return nil, errors.New("destination did not resolve")
	}

	dialer := net.Dialer{Timeout: timeout, KeepAlive: 30 * time.Second}
	var lastErr error
	for _, candidate := range addresses {
		if !p.AllowPrivate && !publicDestinationIP(candidate.IP) {
			lastErr = errors.New("destination address is not public")
			continue
		}
		address := net.JoinHostPort(candidate.IP.String(), strconv.Itoa(port))
		conn, dialErr := dialer.DialContext(ctx, "tcp", address)
		if dialErr == nil {
			return conn, nil
		}
		lastErr = dialErr
	}
	if lastErr == nil {
		lastErr = errors.New("destination unavailable")
	}
	return nil, fmt.Errorf("destination unavailable: %w", lastErr)
}

// ResolveUDPAddr validates and resolves a destination using exactly the same
// public-address policy as TCP CONNECT. It deliberately returns a concrete
// address: the server performs DNS resolution at the US egress and does not
// let the client influence a later DNS rebinding or private-address hop.
func (p DestinationPolicy) ResolveUDPAddr(ctx context.Context, destination string) ([]*net.UDPAddr, error) {
	host, port, err := parseDestination(destination)
	if err != nil {
		return nil, err
	}
	timeout := p.DialTimeout
	if timeout <= 0 {
		timeout = 10 * time.Second
	}
	resolveCtx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()
	var addresses []net.IPAddr
	if parsed := net.ParseIP(host); parsed != nil {
		addresses = []net.IPAddr{{IP: parsed}}
	} else {
		addresses, err = net.DefaultResolver.LookupIPAddr(resolveCtx, host)
		if err != nil {
			return nil, errors.New("destination resolution failed")
		}
	}
	result := make([]*net.UDPAddr, 0, len(addresses))
	for _, candidate := range addresses {
		if !p.AllowPrivate && !publicDestinationIP(candidate.IP) {
			continue
		}
		result = append(result, &net.UDPAddr{IP: append(net.IP(nil), candidate.IP...), Port: port})
	}
	if len(result) == 0 {
		return nil, errors.New("destination address is not public or did not resolve")
	}
	return result, nil
}

func parseDestination(destination string) (string, int, error) {
	host, portText, err := net.SplitHostPort(destination)
	if err != nil || host == "" {
		return "", 0, errors.New("invalid destination")
	}
	port, err := strconv.Atoi(portText)
	if err != nil || port < 1 || port > 65535 {
		return "", 0, errors.New("invalid destination port")
	}
	return host, port, nil
}

func publicDestinationIP(ip net.IP) bool {
	addr, ok := netip.AddrFromSlice(ip)
	if !ok {
		return false
	}
	addr = addr.Unmap()
	if !addr.IsGlobalUnicast() || addr.IsPrivate() || addr.IsLoopback() || addr.IsLinkLocalUnicast() || addr.IsLinkLocalMulticast() || addr.IsMulticast() || addr.IsUnspecified() {
		return false
	}
	for _, prefix := range additionallyForbidden {
		if prefix.Contains(addr) {
			return false
		}
	}
	return true
}
