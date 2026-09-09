package mobilecore

import (
	"context"
	"fmt"
	"net"
	"net/netip"
	"strconv"
	"sync/atomic"

	"github.com/bojieli/queqiao/internal/routerule"
)

// router decides what happens to each flow the stack accepts, and is the only
// place in this process that decides it.
//
// Without one, every flow takes the tunnel. That is still the answer whenever
// no list is loaded, and it is the answer for any flow a loaded list does not
// match: a transport whose failure mode is "traffic went out unprotected" is
// worse than one whose failure mode is "traffic took a slower path".
type router struct {
	rules *routerule.Set
	dns   *fakeDNS

	// counters are read by the telemetry snapshot. They are the only way to
	// tell a rule that never fired from a rule that was never loaded, which is
	// the question an operator asks first when routing looks wrong.
	proxied  atomic.Uint64
	directed atomic.Uint64
	rejected atomic.Uint64
	named    atomic.Uint64
	stale    atomic.Uint64
}

func newRouter(rules *routerule.Set, dns *fakeDNS) *router {
	return &router{rules: rules, dns: dns}
}

// active reports whether anything but the tunnel can happen. A router with no
// rules still runs -- the DNS handle map is useful on its own for telemetry --
// but it never diverts a flow.
func (r *router) active() bool {
	return r != nil && r.rules != nil && r.rules.Len() > 0
}

// decision is what to do with one flow, and what is known about it.
type decision struct {
	action routerule.Action
	rule   routerule.Rule
	// host is the name to dial when the destination was a fake handle. It is
	// empty for a flow opened to a literal address, in which case addr stands.
	host string
	addr netip.AddrPort
	// stale marks a flow to a handle the map has forgotten. Nothing can be
	// done with it -- the address is not a destination -- so it is refused.
	stale bool
}

// route resolves a destination into a decision.
func (r *router) route(destination netip.AddrPort) decision {
	out := decision{addr: destination, action: routerule.Proxy}
	addr := unmapAddr(destination.Addr())

	flow := routerule.Flow{Port: destination.Port()}
	if r != nil && r.dns != nil && r.dns.Holds(addr) {
		name, ok := r.dns.Name(addr)
		if !ok {
			// A handle the map no longer holds. The address is not routable
			// and the name is gone, so there is nothing to dial.
			out.stale = true
			out.action = routerule.Reject
			if r != nil {
				r.stale.Add(1)
			}
			return out
		}
		out.host = name
		flow.Domain = name
		if r != nil {
			r.named.Add(1)
		}
	} else {
		flow.Addr = addr
	}

	if r.active() {
		action, rule, _ := r.rules.Match(flow)
		out.action = action
		out.rule = rule
	}
	if r != nil {
		switch out.action {
		case routerule.Direct:
			r.directed.Add(1)
		case routerule.Reject:
			r.rejected.Add(1)
		default:
			r.proxied.Add(1)
		}
	}
	return out
}

// target renders what to dial, preferring the name over the handle.
func (d decision) target() string {
	if d.host != "" {
		return net.JoinHostPort(d.host, strconv.Itoa(int(d.addr.Port())))
	}
	return d.addr.String()
}

// dialDirect opens a connection outside the tunnel.
//
// The name is resolved here, by this device, which is the point: a name that
// matched DIRECT is one the user wants answered from where they are, and
// resolving it through the tunnel from the gateway's vantage is what produced
// the wrong answer in the first place.
func dialDirect(ctx context.Context, d decision) (net.Conn, error) {
	var dialer net.Dialer
	conn, err := dialer.DialContext(ctx, "tcp", d.target())
	if err != nil {
		return nil, fmt.Errorf("direct dial %s: %w", d.target(), err)
	}
	return conn, nil
}

type routerSnapshot struct {
	Rules    int    `json:"rules"`
	Proxied  uint64 `json:"proxied"`
	Directed uint64 `json:"directed"`
	Rejected uint64 `json:"rejected"`
	Named    uint64 `json:"named"`
	Stale    uint64 `json:"stale_handles"`
}

func (r *router) snapshot() routerSnapshot {
	if r == nil {
		return routerSnapshot{}
	}
	rules := 0
	if r.rules != nil {
		rules = r.rules.Len()
	}
	return routerSnapshot{
		Rules:    rules,
		Proxied:  r.proxied.Load(),
		Directed: r.directed.Load(),
		Rejected: r.rejected.Load(),
		Named:    r.named.Load(),
		Stale:    r.stale.Load(),
	}
}
