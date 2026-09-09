package netbind

import (
	"context"
	"net"
	"net/netip"
	"strings"
	"syscall"
)

// ResolverFor returns a resolver whose own sockets carry the same interface
// binding as a data socket built for spec, plus any extra control the caller
// applies to its data sockets.
//
// A local-address spec exists so the outer path bypasses a host TUN route, and
// InterfaceControl asserts that at the kernel level so a transparent proxy
// honouring NEAppProxyFlow.isBound leaves those sockets alone. That covers the
// sockets the caller creates. It does not cover the ones the resolver creates
// on the caller's behalf: net.Dialer applies LocalAddr and Control to the
// connection it dials, never to the lookup that turned a name into the address
// it dials to. So a client bound to a physical interface still asks its
// question over an unbound socket.
//
// When capture redirects port 53, that unbound question is claimed and sent to
// the proxy, and a client whose own endpoint is named rather than numbered
// cannot answer it: the name has to resolve before the datapath exists, and the
// datapath has to exist before the name resolves. Binding the resolver removes
// the cycle at its only unguarded end.
//
// The returned resolver is deliberately scoped to bootstrap lookups — the
// gateway endpoint — rather than installed globally. PreferGo is required for
// Dial to be honoured at all: the cgo resolver answers inside libSystem and
// never calls it, so without PreferGo the binding is silently dropped. That
// has a cost, which is why the scope is narrow. The pure resolver reads
// /etc/resolv.conf rather than the platform's own configuration, so it does
// not see split-horizon rules a system resolver would apply. A gateway
// endpoint is a public name reached over a specific interface, which is
// exactly the lookup least likely to want those rules; every other name in
// the process keeps the resolver it had.
//
// An empty spec has nothing to bind to and yields net.DefaultResolver, which is
// the previous behaviour.
func ResolverFor(spec string, extra func(string, string, syscall.RawConn) error) (*net.Resolver, error) {
	if spec == "" {
		return net.DefaultResolver, nil
	}
	result, err := ResolveWithInterface(spec)
	if err != nil {
		return nil, err
	}
	return ResolverForResult(result, extra), nil
}

// ResolverForResult is ResolverFor for a caller that has already resolved the
// spec. Dialing a lane resolves it to build the socket's own binding, and
// resolving an "auto" or "if:NAME" spec enumerates the host's interfaces, so a
// caller on a dial path should pass what it already has rather than pay for
// that a second time on every connection.
func ResolverForResult(result ResolveResult, extra func(string, string, syscall.RawConn) error) *net.Resolver {
	control := composeControls(InterfaceControl(result.InterfaceName), extra)
	local := result.Addr
	return &net.Resolver{
		// Without this the cgo resolver answers and never calls Dial, so the
		// binding this function exists to apply would be silently dropped.
		PreferGo: true,
		Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
			dialer := &net.Dialer{Control: control}
			if addr, ok := localAddrFor(network, address, local); ok {
				dialer.LocalAddr = addr
			}
			return dialer.DialContext(ctx, network, address)
		},
	}
}

// localAddrFor returns the source address to bind for one nameserver dial, and
// whether to bind at all.
//
// A source address of the wrong family cannot carry the query, and a resolver
// list routinely mixes families. Binding only on a match keeps the IPv4 case
// bound and lets an IPv6 nameserver still be reached over the interface
// binding, which is the part capture actually reads.
func localAddrFor(network, address string, local netip.Addr) (net.Addr, bool) {
	if !local.IsValid() {
		return nil, false
	}
	host, _, err := net.SplitHostPort(address)
	if err != nil {
		return nil, false
	}
	target, err := netip.ParseAddr(host)
	if err != nil || target.Is4() != local.Is4() {
		return nil, false
	}
	switch {
	case strings.HasPrefix(network, "udp"):
		return &net.UDPAddr{IP: local.AsSlice()}, true
	case strings.HasPrefix(network, "tcp"):
		return &net.TCPAddr{IP: local.AsSlice()}, true
	default:
		return nil, false
	}
}

// composeControls returns a control function that calls a then b, or nil when
// neither is set.
func composeControls(a, b func(string, string, syscall.RawConn) error) func(string, string, syscall.RawConn) error {
	switch {
	case a == nil:
		return b
	case b == nil:
		return a
	}
	return func(network, address string, conn syscall.RawConn) error {
		if err := a(network, address, conn); err != nil {
			return err
		}
		return b(network, address, conn)
	}
}
