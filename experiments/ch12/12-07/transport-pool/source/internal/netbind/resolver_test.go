package netbind

import (
	"context"
	"net"
	"net/netip"
	"testing"
	"time"
)

func TestResolverForWithoutASpecIsTheDefault(t *testing.T) {
	// Nothing to bind to, so nothing changes: callers that never asked for a
	// local address keep the resolver they always had.
	resolver, err := ResolverFor("", nil)
	if err != nil {
		t.Fatal(err)
	}
	if resolver != net.DefaultResolver {
		t.Error("an empty spec must not replace the default resolver")
	}
}

func TestResolverForRejectsASpecItCannotResolve(t *testing.T) {
	if _, err := ResolverFor("not-an-address", nil); err == nil {
		t.Error("an unresolvable spec must be reported, not silently ignored")
	}
}

func TestResolverForDialsFromTheBoundAddress(t *testing.T) {
	// The whole point of the helper: the socket that carries the question is
	// bound the same way the socket that will carry the data is.
	resolver, err := ResolverFor("127.0.0.1", nil)
	if err != nil {
		t.Fatal(err)
	}
	if !resolver.PreferGo {
		t.Fatal("without PreferGo the Dial hook is never called and nothing is bound")
	}
	server, err := net.ListenUDP("udp4", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	defer server.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	conn, err := resolver.Dial(ctx, "udp", server.LocalAddr().String())
	if err != nil {
		t.Fatal(err)
	}
	defer conn.Close()
	local := conn.LocalAddr().(*net.UDPAddr)
	if !local.IP.IsLoopback() {
		t.Errorf("dialed from %s, want the bound loopback address", local.IP)
	}
}

func TestLocalAddrForBindsOnlyWhatCanCarryTheQuery(t *testing.T) {
	v4 := netip.MustParseAddr("192.0.2.10")
	v6 := netip.MustParseAddr("2001:db8::1")

	if addr, ok := localAddrFor("udp", "198.51.100.1:53", v4); !ok {
		t.Error("a v4 source and a v4 nameserver must bind")
	} else if _, isUDP := addr.(*net.UDPAddr); !isUDP {
		t.Errorf("bound %T for a udp dial, want *net.UDPAddr", addr)
	}
	if addr, ok := localAddrFor("tcp", "198.51.100.1:53", v4); !ok {
		t.Error("a v4 source and a v4 nameserver must bind over tcp too")
	} else if _, isTCP := addr.(*net.TCPAddr); !isTCP {
		t.Errorf("bound %T for a tcp dial, want *net.TCPAddr", addr)
	}
	// A source of the wrong family cannot carry the query at all. Skipping the
	// bind still leaves the interface binding, which is the part capture reads.
	if _, ok := localAddrFor("udp", "[2001:db8::53]:53", v4); ok {
		t.Error("a v4 source must not be bound for a v6 nameserver")
	}
	if _, ok := localAddrFor("udp", "198.51.100.1:53", v6); ok {
		t.Error("a v6 source must not be bound for a v4 nameserver")
	}
	if _, ok := localAddrFor("unix", "/var/run/resolver", v4); ok {
		t.Error("only udp and tcp dials have an address to bind")
	}
	if _, ok := localAddrFor("udp", "not-host-port", v4); ok {
		t.Error("an unparseable nameserver address must not be bound")
	}
	if _, ok := localAddrFor("udp", "198.51.100.1:53", netip.Addr{}); ok {
		t.Error("an invalid source address must not be bound")
	}
}
