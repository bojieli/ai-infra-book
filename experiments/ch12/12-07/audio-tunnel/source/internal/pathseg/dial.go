package pathseg

import (
	"context"
	"fmt"
	"net"

	"golang.org/x/net/proxy"
)

// dialThrough opens one connection, optionally through a local SOCKS5 listener.
//
// The tunnelled arm and the direct arm go through this one function so that
// the only difference between them is the proxy, and not two dialers that
// happen to time slightly different things.
//
// A name is resolved by whoever dials it: locally on the direct arm, at the
// gateway on the tunnelled one. That asymmetry is deliberate and is the same
// one queqiaod doctor relies on -- an anycast name resolves to whatever is near
// whoever asked, so resolving once here and handing both arms the same address
// would hide the case where the gateway reaches a different machine entirely.
// Callers that want the arms pinned to one machine resolve first and pass
// EstablishOptions.Address.
func dialThrough(ctx context.Context, target, socksAddr string, dialer *net.Dialer) (net.Conn, error) {
	if socksAddr == "" {
		return dialer.DialContext(ctx, "tcp", target)
	}
	d, err := proxy.SOCKS5("tcp", socksAddr, nil, dialer)
	if err != nil {
		return nil, err
	}
	cd, ok := d.(proxy.ContextDialer)
	if !ok {
		return nil, fmt.Errorf("socks5 dialer for %s does not honour a context", socksAddr)
	}
	return cd.DialContext(ctx, "tcp", target)
}
