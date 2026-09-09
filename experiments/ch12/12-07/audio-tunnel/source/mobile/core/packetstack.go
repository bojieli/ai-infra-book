package mobilecore

import (
	"context"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"net"
	"net/netip"
	"os"
	"sync"
	"sync/atomic"
	"time"

	"golang.org/x/sys/unix"

	"github.com/bojieli/queqiao/internal/routerule"
	"gvisor.dev/gvisor/pkg/buffer"
	"gvisor.dev/gvisor/pkg/tcpip"
	"gvisor.dev/gvisor/pkg/tcpip/adapters/gonet"
	"gvisor.dev/gvisor/pkg/tcpip/header"
	"gvisor.dev/gvisor/pkg/tcpip/link/channel"
	"gvisor.dev/gvisor/pkg/tcpip/network/ipv4"
	"gvisor.dev/gvisor/pkg/tcpip/network/ipv6"
	"gvisor.dev/gvisor/pkg/tcpip/stack"
	"gvisor.dev/gvisor/pkg/tcpip/transport/tcp"
	"gvisor.dev/gvisor/pkg/tcpip/transport/udp"
	"gvisor.dev/gvisor/pkg/waiter"
)

const (
	defaultMTU         = 1280
	maximumMTU         = 9000
	defaultMaxSessions = 1024
	linkQueueLength    = 64
	// A bridge has two copy workers. Keeping each worker at 4 KiB means the
	// bridge contributes at most about 8 MiB for 1,024 active TCP sessions,
	// while the bounded transport and flow budgets provide backpressure for
	// larger transfers.
	copyBufferSize      = 4 * 1024
	udpPacketBufferSize = 4 * 1024
	udpIdleTimeout      = 2 * time.Minute
)

const (
	endpointBufferMinimum = 4 * 1024
	// gVisor allocates endpoint buffers per active socket. Small defaults keep
	// a large session count cheap. The endpoint is the sub-millisecond local
	// half of the bridge, so a fixed 8 KiB window still backpressures cleanly
	// without becoming the WAN flow's retained-data arena.
	endpointBufferDefault = 8 * 1024
	endpointBufferMaximum = 8 * 1024
)

type packetStack struct {
	ctx       context.Context
	cancel    context.CancelFunc
	tun       io.ReadWriteCloser
	offset    int
	mtu       int
	proxy     socksClient
	stack     *stack.Stack
	link      *channel.Endpoint
	admission chan struct{}
	log       func(level, message string)
	// route decides per flow whether the tunnel, the ordinary interface, or
	// nothing at all carries it. Never nil: a stack with no rules gets a
	// router that answers "tunnel" to everything, so the decision has one code
	// path rather than two.
	route *router

	wg        sync.WaitGroup
	closeOnce sync.Once
	firstErr  chan error
	// wg covers the two packet pumps; sessionWG covers forwarding callbacks.
	// Closing the packet engine must not return while a proxy socket or a gVisor
	// endpoint is still owned by an in-flight session.
	sessionWG sync.WaitGroup
	sessionMu sync.Mutex
	closing   atomic.Bool

	packetsIn       atomic.Uint64
	packetsOut      atomic.Uint64
	malformed       atomic.Uint64
	sessionRejected atomic.Uint64
}

type packetStackSnapshot struct {
	PacketsIn       uint64 `json:"packets_in"`
	PacketsOut      uint64 `json:"packets_out"`
	Malformed       uint64 `json:"malformed_packets"`
	SessionRejected uint64 `json:"sessions_rejected"`
	// Routing is how the rule list is behaving, and is reported even when no
	// list is loaded. Zero rules with traffic flowing is a different fault
	// from a loaded list whose DIRECT count never moves, and an operator
	// cannot tell them apart without seeing both numbers.
	Routing routerSnapshot `json:"routing"`
}

func newPacketStack(parent context.Context, tunFD, packetOffset, mtu, maxSessions int, proxy socksClient, log func(string, string)) (*packetStack, error) {
	if tunFD < 0 {
		return nil, errors.New("TUN file descriptor must be non-negative")
	}
	if err := validatePacketStackConfig(packetOffset, mtu, maxSessions); err != nil {
		return nil, err
	}
	duplicate, err := unix.Dup(tunFD)
	if err != nil {
		return nil, fmt.Errorf("duplicate TUN descriptor: %w", err)
	}
	if err := unix.SetNonblock(duplicate, true); err != nil {
		_ = unix.Close(duplicate)
		return nil, fmt.Errorf("configure TUN descriptor: %w", err)
	}
	return newPacketStackWithDevice(parent, os.NewFile(uintptr(duplicate), "queqiao-tun"), packetOffset, mtu, maxSessions, proxy, log)
}

func newPacketStackWithDevice(parent context.Context, device io.ReadWriteCloser, packetOffset, mtu, maxSessions int, proxy socksClient, log func(string, string)) (*packetStack, error) {
	if device == nil {
		return nil, errors.New("packet device is required")
	}
	if err := validatePacketStackConfig(packetOffset, mtu, maxSessions); err != nil {
		_ = device.Close()
		return nil, err
	}
	if mtu == 0 {
		mtu = defaultMTU
	}
	if maxSessions <= 0 {
		maxSessions = defaultMaxSessions
	}
	ctx, cancel := context.WithCancel(parent)
	p := &packetStack{
		ctx: ctx, cancel: cancel, tun: device,
		offset: packetOffset, mtu: mtu, proxy: proxy, admission: make(chan struct{}, maxSessions),
		log: log, firstErr: make(chan error, 1),
		route: newRouter(nil, newFakeDNS()),
	}
	if p.log == nil {
		p.log = func(string, string) {}
	}
	if err := p.initialize(); err != nil {
		_ = p.tun.Close()
		cancel()
		return nil, err
	}
	return p, nil
}

func validatePacketStackConfig(packetOffset, mtu, maxSessions int) error {
	if packetOffset != 0 && packetOffset != 4 {
		return errors.New("packet offset must be 0 or 4")
	}
	if mtu != 0 && (mtu < header.IPv6MinimumMTU || mtu > maximumMTU) {
		return fmt.Errorf("MTU must be between %d and %d", header.IPv6MinimumMTU, maximumMTU)
	}
	if maxSessions > 65535 {
		return errors.New("maximum session count exceeds 65535")
	}
	return nil
}

func (p *packetStack) initialize() error {
	// Configuration validation limits MTU to 9000 before initialization.
	linkMTU := uint32(p.mtu) // #nosec G115 -- validated to [1280, 9000].
	p.link = channel.New(linkQueueLength, linkMTU, "")
	p.stack = stack.New(stack.Options{
		NetworkProtocols:   []stack.NetworkProtocolFactory{ipv4.NewProtocol, ipv6.NewProtocol},
		TransportProtocols: []stack.TransportProtocolFactory{tcp.NewProtocol, udp.NewProtocol},
	})
	// gVisor's desktop defaults are generous per endpoint. With dozens of
	// mobile flows they become the dominant multiplicative allocation, so keep
	// TCP and generic socket buffers within a small, explicit range. Full
	// buffers naturally advertise a smaller TCP receive window and backpressure
	// the application instead of growing the process.
	if err := p.stack.SetTransportProtocolOption(tcp.ProtocolNumber, &tcpip.TCPSendBufferSizeRangeOption{
		Min: endpointBufferMinimum, Default: endpointBufferDefault, Max: endpointBufferMaximum,
	}); err != nil {
		return fmt.Errorf("bound TCP send buffers: %s", err)
	}
	if err := p.stack.SetTransportProtocolOption(tcp.ProtocolNumber, &tcpip.TCPReceiveBufferSizeRangeOption{
		Min: endpointBufferMinimum, Default: endpointBufferDefault, Max: endpointBufferMaximum,
	}); err != nil {
		return fmt.Errorf("bound TCP receive buffers: %s", err)
	}
	moderateReceive := tcpip.TCPModerateReceiveBufferOption(false)
	if err := p.stack.SetTransportProtocolOption(tcp.ProtocolNumber, &moderateReceive); err != nil {
		return fmt.Errorf("disable TCP receive-buffer growth: %s", err)
	}
	if err := p.stack.SetOption(tcpip.SendBufferSizeOption{
		Min: endpointBufferMinimum, Default: endpointBufferDefault, Max: endpointBufferMaximum,
	}); err != nil {
		return fmt.Errorf("bound socket send buffers: %s", err)
	}
	if err := p.stack.SetOption(tcpip.ReceiveBufferSizeOption{
		Min: endpointBufferMinimum, Default: endpointBufferDefault, Max: endpointBufferMaximum,
	}); err != nil {
		return fmt.Errorf("bound socket receive buffers: %s", err)
	}
	nicID := p.stack.NextNICID()
	if err := p.stack.CreateNIC(nicID, p.link); err != nil {
		return fmt.Errorf("create virtual network interface: %s", err)
	}
	if err := p.stack.SetPromiscuousMode(nicID, true); err != nil {
		return fmt.Errorf("enable virtual interface promiscuous mode: %s", err)
	}
	if err := p.stack.SetSpoofing(nicID, true); err != nil {
		return fmt.Errorf("enable virtual interface address spoofing: %s", err)
	}
	p.stack.SetRouteTable([]tcpip.Route{
		{Destination: header.IPv4EmptySubnet, NIC: nicID},
		{Destination: header.IPv6EmptySubnet, NIC: nicID},
	})
	tcpForwarder := tcp.NewForwarder(p.stack, 0, cap(p.admission), p.forwardTCP)
	udpForwarder := udp.NewForwarder(p.stack, p.forwardUDP)
	p.stack.SetTransportProtocolHandler(tcp.ProtocolNumber, tcpForwarder.HandlePacket)
	p.stack.SetTransportProtocolHandler(udp.ProtocolNumber, udpForwarder.HandlePacket)
	return nil
}

func (p *packetStack) start() {
	p.wg.Add(2)
	go p.pumpTUNToStack()
	go p.pumpStackToTUN()
}

func (p *packetStack) Close() error {
	p.closeOnce.Do(func() {
		p.sessionMu.Lock()
		p.closing.Store(true)
		p.sessionMu.Unlock()
		p.cancel()
		_ = p.tun.Close()
		p.link.Close()
		p.stack.Close()
	})
	p.wg.Wait()
	p.stack.Wait()
	p.sessionWG.Wait()
	select {
	case err := <-p.firstErr:
		return err
	default:
		return nil
	}
}

func (p *packetStack) fail(err error) {
	if err == nil || p.ctx.Err() != nil {
		return
	}
	select {
	case p.firstErr <- err:
	default:
	}
	p.log("error", err.Error())
	p.cancel()
	_ = p.tun.Close()
}

// done reports when the stack has stopped, so a session can fail rather than
// serve a listener with nothing behind it. metrics widens the typed snapshot to
// the packetEngine interface, which must also describe an engine that has no
// counters at all.
func (p *packetStack) done() <-chan struct{} { return p.ctx.Done() }

func (p *packetStack) metrics() any { return p.snapshot() }

func (p *packetStack) snapshot() packetStackSnapshot {
	return packetStackSnapshot{
		PacketsIn: p.packetsIn.Load(), PacketsOut: p.packetsOut.Load(),
		Malformed: p.malformed.Load(), SessionRejected: p.sessionRejected.Load(),
		Routing: p.route.snapshot(),
	}
}

func (p *packetStack) pumpTUNToStack() {
	defer p.wg.Done()
	packet := make([]byte, p.offset+p.mtu)
	for {
		n, err := p.tun.Read(packet)
		if err != nil {
			if p.ctx.Err() != nil || errors.Is(err, os.ErrClosed) {
				return
			}
			p.fail(fmt.Errorf("read TUN packet: %w", err))
			return
		}
		if n <= p.offset {
			p.malformed.Add(1)
			continue
		}
		payload := packet[p.offset:n]
		protocol, ok := packetProtocol(payload)
		if !ok || !p.validPlatformHeader(packet[:p.offset], protocol) {
			p.malformed.Add(1)
			continue
		}
		bufferCopy := append([]byte(nil), payload...)
		pkt := stack.NewPacketBuffer(stack.PacketBufferOptions{Payload: buffer.MakeWithData(bufferCopy)})
		p.link.InjectInbound(protocol, pkt)
		pkt.DecRef()
		p.packetsIn.Add(1)
	}
}

func (p *packetStack) pumpStackToTUN() {
	defer p.wg.Done()
	packet := make([]byte, p.offset+p.mtu)
	for {
		pkt := p.link.ReadContext(p.ctx)
		if pkt == nil {
			return
		}
		view := pkt.ToView()
		payload := view.AsSlice()
		protocol, ok := packetProtocol(payload)
		if !ok {
			p.malformed.Add(1)
			view.Release()
			pkt.DecRef()
			continue
		}
		if len(payload) > p.mtu {
			p.malformed.Add(1)
			view.Release()
			pkt.DecRef()
			continue
		}
		out := packet[:p.offset+len(payload)]
		if p.offset == 4 {
			family := uint32(unix.AF_INET)
			if protocol == ipv6.ProtocolNumber {
				family = unix.AF_INET6
			}
			binary.BigEndian.PutUint32(out[:4], family)
		}
		copy(out[p.offset:], payload)
		view.Release()
		pkt.DecRef()
		if err := writeFull(p.tun, out); err != nil {
			if p.ctx.Err() != nil || errors.Is(err, os.ErrClosed) {
				return
			}
			p.fail(fmt.Errorf("write TUN packet: %w", err))
			return
		}
		p.packetsOut.Add(1)
	}
}

func packetProtocol(packet []byte) (tcpip.NetworkProtocolNumber, bool) {
	if len(packet) == 0 {
		return 0, false
	}
	switch packet[0] >> 4 {
	case 4:
		return ipv4.ProtocolNumber, len(packet) >= header.IPv4MinimumSize
	case 6:
		return ipv6.ProtocolNumber, len(packet) >= header.IPv6MinimumSize
	default:
		return 0, false
	}
}

func (p *packetStack) validPlatformHeader(platform []byte, protocol tcpip.NetworkProtocolNumber) bool {
	if p.offset == 0 {
		return len(platform) == 0
	}
	if len(platform) != 4 {
		return false
	}
	family := binary.BigEndian.Uint32(platform)
	return family == unix.AF_INET && protocol == ipv4.ProtocolNumber ||
		family == unix.AF_INET6 && protocol == ipv6.ProtocolNumber
}

func (p *packetStack) acquire() bool {
	p.sessionMu.Lock()
	defer p.sessionMu.Unlock()
	if p.closing.Load() || p.ctx.Err() != nil {
		return false
	}
	select {
	case p.admission <- struct{}{}:
		if p.closing.Load() || p.ctx.Err() != nil {
			<-p.admission
			return false
		}
		p.sessionWG.Add(1)
		return true
	default:
		p.sessionRejected.Add(1)
		return false
	}
}

// useRules points this stack at a rule list, before it starts carrying
// anything. A nil list leaves the router answering "tunnel" to every flow,
// which is what a session with no rules does.
func (p *packetStack) useRules(rules *routerule.Set) {
	if p == nil {
		return
	}
	p.route = newRouter(rules, p.route.dnsResolver())
}

// dnsResolver returns the existing fake resolver, or a new one. The map has to
// survive a rule change within a session build, because a handle already handed
// to an application is a promise this process made.
func (r *router) dnsResolver() *fakeDNS {
	if r == nil || r.dns == nil {
		return newFakeDNS()
	}
	return r.dns
}

func (p *packetStack) release() { <-p.admission }

func (p *packetStack) forwardTCP(request *tcp.ForwarderRequest) {
	if !p.acquire() {
		request.Complete(true)
		return
	}
	defer p.sessionWG.Done()
	defer p.release()
	id := request.ID()
	destination, err := endpointAddress(id.LocalAddress, id.LocalPort)
	if err != nil {
		request.Complete(true)
		return
	}
	verdict := p.route.route(destination)
	if verdict.action == routerule.Reject {
		// Refused before anything is dialled. Completing with true sends a
		// reset, so the application fails now instead of waiting out a
		// connect timeout for a flow that was never going anywhere.
		request.Complete(true)
		if verdict.stale {
			p.log("debug", fmt.Sprintf("refused a flow to a forgotten name handle %s", destination))
		}
		return
	}
	outer, err := p.dialFor(verdict)
	if err != nil {
		request.Complete(true)
		level := "warning"
		if errors.Is(err, errSocksMethodUnavailable) {
			level = "debug"
		}
		p.log(level, fmt.Sprintf("TCP connection to %s failed: %v", verdict.target(), err))
		return
	}
	var queue waiter.Queue
	endpoint, tcpErr := request.CreateEndpoint(&queue)
	if tcpErr != nil {
		request.Complete(true)
		_ = outer.Close()
		return
	}
	request.Complete(false)
	inner := gonet.NewTCPConn(&queue, endpoint)
	bridgeTCP(p.ctx, inner, outer)
}

func (p *packetStack) forwardUDP(request *udp.ForwarderRequest) bool {
	if !p.acquire() {
		return false
	}
	go func() {
		defer p.sessionWG.Done()
		defer p.release()
		id := request.ID()
		destination, err := endpointAddress(id.LocalAddress, id.LocalPort)
		if err != nil {
			return
		}
		verdict := p.route.route(destination)
		if verdict.action == routerule.Reject {
			return
		}
		var queue waiter.Queue
		endpoint, udpErr := request.CreateEndpoint(&queue)
		if udpErr != nil {
			return
		}
		inner := gonet.NewUDPConn(&queue, endpoint)
		defer inner.Close()
		// A name lookup is answered here rather than forwarded, which is what
		// gives every rule below a name to match on. Anything this resolver
		// will not answer falls through to the tunnel exactly as before.
		var pending []byte
		if destination.Port() == dnsPort {
			handled, unanswered := p.serveDNS(inner)
			if handled {
				return
			}
			pending = unanswered
		}
		outer, err := p.proxy.dialUDP(p.ctx)
		if err != nil {
			level := "warning"
			if errors.Is(err, errSocksMethodUnavailable) {
				level = "debug"
			}
			p.log(level, fmt.Sprintf("UDP proxy association failed: %v", err))
			return
		}
		defer outer.Close()
		bridgeUDP(p.ctx, inner, outer, destination, pending)
	}()
	return true
}

// dnsPort is where a name lookup goes. Only UDP is intercepted: a resolver
// falling back to TCP is doing so because an answer did not fit, and the
// answers this hands out are one A record.
const dnsPort = 53

// dialFor opens the connection a decision calls for.
//
// The two paths differ in more than which socket they use. A proxied flow that
// carries a name sends the name, so the gateway resolves it from the vantage
// the flow is being sent to use. A direct flow resolves here, on the device,
// which is the whole point of having matched DIRECT.
func (p *packetStack) dialFor(verdict decision) (net.Conn, error) {
	if verdict.action == routerule.Direct {
		return dialDirect(p.ctx, verdict)
	}
	if verdict.host != "" {
		return p.proxy.dialTCPDomain(p.ctx, verdict.host, verdict.addr.Port())
	}
	return p.proxy.dialTCP(p.ctx, verdict.addr)
}

// serveDNS answers one lookup from the fake resolver and reports whether it
// did. A false return leaves the flow to the tunnel, unchanged, which is what
// happens for a query this does not understand or a type it cannot answer.
//
// One exchange per flow is deliberate. gVisor hands each UDP flow its own
// endpoint, resolvers open one per query, and a handler that stayed to wait for
// a second would hold a session slot for a client that had already moved on.
func (p *packetStack) serveDNS(inner net.Conn) (handled bool, pending []byte) {
	if p.route == nil || p.route.dns == nil {
		return false, nil
	}
	if err := inner.SetReadDeadline(time.Now().Add(dnsReadTimeout)); err != nil {
		return false, nil
	}
	buffer := make([]byte, maxDNSMessage)
	read, err := inner.Read(buffer)
	_ = inner.SetReadDeadline(time.Time{})
	if err != nil || read == 0 {
		return false, nil
	}
	datagram := buffer[:read]
	question, err := parseDNSQuestion(datagram)
	// Anything this will not answer is handed back so the caller forwards it
	// upstream, unchanged and to the destination it was addressed to. The
	// alternative -- dropping what has already been read off the flow -- turns
	// every query shape this parser does not cover, and every non-DNS use of
	// port 53, into a silent black hole. An existing test sends exactly that.
	if err != nil || question.class != dnsClassIN {
		return false, datagram
	}
	var response []byte
	switch question.qtype {
	case dnsTypeA:
		handle, ok := p.route.dns.Handle(question.name)
		if !ok {
			return false, datagram
		}
		response = answerWithAddress(datagram, question, handle)
	case dnsTypeAAAA:
		// The handles are v4. Saying "this name has no AAAA" is true of the
		// handle and makes the client ask for A immediately, where a silence
		// would make it wait.
		if _, ok := p.route.dns.Handle(question.name); !ok {
			return false, datagram
		}
		response = answerEmpty(datagram, question)
	default:
		return false, datagram
	}
	if err := inner.SetWriteDeadline(time.Now().Add(dnsWriteTimeout)); err != nil {
		return true, nil
	}
	if _, err := inner.Write(response); err != nil {
		p.log("debug", fmt.Sprintf("writing a DNS answer for %s failed: %v", question.name, err))
	}
	_ = inner.SetWriteDeadline(time.Time{})
	return true, nil
}

const (
	maxDNSMessage   = 1500
	dnsReadTimeout  = 5 * time.Second
	dnsWriteTimeout = 5 * time.Second
)

func endpointAddress(address tcpip.Address, port uint16) (netip.AddrPort, error) {
	raw := append([]byte(nil), (&address).AsSlice()...)
	addr, ok := netip.AddrFromSlice(raw)
	if !ok {
		return netip.AddrPort{}, errors.New("invalid network-stack address")
	}
	return netip.AddrPortFrom(addr.Unmap(), port), nil
}

func bridgeTCP(parent context.Context, left *gonet.TCPConn, right net.Conn) {
	ctx, cancel := context.WithCancel(parent)
	defer cancel()
	done := make(chan struct{}, 2)
	copySide := func(destination io.Writer, source io.Reader, closeDestination func() error, closeSource func() error) {
		_, _ = io.CopyBuffer(destination, source, make([]byte, copyBufferSize))
		_ = closeDestination()
		_ = closeSource()
		done <- struct{}{}
	}
	go copySide(right, left, func() error {
		if closer, ok := right.(interface{ CloseWrite() error }); ok {
			return closer.CloseWrite()
		}
		return right.Close()
	}, left.CloseRead)
	go copySide(left, right, left.CloseWrite, func() error {
		if closer, ok := right.(interface{ CloseRead() error }); ok {
			return closer.CloseRead()
		}
		return nil
	})
	waitForBridgeWorkers(ctx, done, 2, func() {
		_ = left.Close()
		_ = right.Close()
	})
}

// bridgeUDP carries a UDP flow. first, when not nil, is a datagram already read
// off the flow -- the resolver looked at it, would not answer it, and handed it
// back -- and is sent before anything else so the flow's ordering is what the
// application produced.
func bridgeUDP(parent context.Context, inner *gonet.UDPConn, outer *socksUDPAssociation, destination netip.AddrPort, first []byte) {
	ctx, cancel := context.WithCancel(parent)
	defer cancel()
	if len(first) > 0 {
		if err := outer.WriteTo(first, destination); err != nil {
			return
		}
	}
	done := make(chan struct{}, 2)
	refresh := func() {
		deadline := time.Now().Add(udpIdleTimeout)
		_ = inner.SetDeadline(deadline)
		_ = outer.SetDeadline(deadline)
	}
	refresh()
	go func() {
		defer func() { done <- struct{}{} }()
		buffer := make([]byte, udpPacketBufferSize)
		for {
			n, err := inner.Read(buffer)
			if err != nil || outer.WriteTo(buffer[:n], destination) != nil {
				return
			}
			refresh()
		}
	}()
	go func() {
		defer func() { done <- struct{}{} }()
		buffer := make([]byte, udpPacketBufferSize)
		for {
			n, err := outer.ReadFrom(buffer, destination)
			if err != nil || writeFull(inner, buffer[:n]) != nil {
				return
			}
			refresh()
		}
	}()
	waitForBridgeWorkers(ctx, done, 2, func() {
		_ = inner.Close()
		_ = outer.Close()
	})
}

// waitForBridgeWorkers closes both sides after the first EOF/error or upper
// layer cancellation, then gives every copy worker a chance to release its
// stack, socket, and working buffer before the session returns its admission
// slot. Network connections unblock on Close; the timeout is only a guard
// against a broken implementation supplied across a platform boundary.
func waitForBridgeWorkers(ctx context.Context, done <-chan struct{}, workers int, closeBoth func()) {
	completed := 0
	select {
	case <-ctx.Done():
	case <-done:
		completed++
	}
	closeBoth()
	if completed >= workers {
		return
	}
	timer := time.NewTimer(time.Second)
	defer timer.Stop()
	for completed < workers {
		select {
		case <-done:
			completed++
		case <-timer.C:
			return
		}
	}
}
