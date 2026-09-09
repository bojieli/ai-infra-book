// Package portmux implements UDP port-hopping for QUIC connections.
//
// When the GFW or an ISP blocks a specific UDP port for a window of time,
// the client detects the loss and hops to a different pre-agreed port.
// The server listens on all ports simultaneously and treats packets from
// any of those ports as belonging to the same QUIC connection. QUIC
// identifies connections by connection ID, not by the 5-tuple, so the
// server's QUIC stack never observes the port change.
//
// Port transparency is achieved by bidirectional address rewriting:
//   - Outgoing (client → server): destination port rewritten primary → current hop port.
//   - Incoming (server → client): source port rewritten any hop port → primary port.
//
// Neither connection migration nor reconnection occurs. The server simply
// begins receiving QUIC packets on a new socket, and the QUIC connection ID
// ensures they land on the right connection.
package portmux

import (
	"context"
	"crypto/sha256"
	"encoding/binary"
	"fmt"
	"net"
	"sync"
	"sync/atomic"
	"time"
)

// HopPorts derives a reproducible, collision-free set of count UDP ports for
// the given provider and primary port. The primary port is always first;
// the remaining count−1 ports are pseudo-randomly distributed across
// [1024, 65535) using SHA-256 so both client and server independently reach
// the same list from the same inputs.
//
// The derivation key is providerID + NUL + "queqiao-hop-v1" + NUL + counter
// encoded big-endian. Using SHA-256 rather than a simple modulus avoids
// clustering ports in a blockable consecutive range.
func HopPorts(providerID string, primaryPort, count int) []int {
	if count <= 1 {
		return []int{primaryPort}
	}

	// Pre-build the stable prefix of the hash input to avoid rebuilding it
	// inside the loop.
	prefix := make([]byte, 0, len(providerID)+17)
	prefix = append(prefix, providerID...)
	prefix = append(prefix, 0) // NUL separator
	prefix = append(prefix, "queqiao-hop-v1"...)
	prefix = append(prefix, 0) // NUL separator

	seen := make(map[int]bool, count)
	ports := make([]int, 0, count)
	ports = append(ports, primaryPort)
	seen[primaryPort] = true

	var counter [4]byte
	for i := 0; len(ports) < count; i++ {
		binary.BigEndian.PutUint32(counter[:], uint32(i))
		h := sha256.New()
		h.Write(prefix)
		h.Write(counter[:])
		sum := h.Sum(nil)
		// Map the first two bytes to [1024, 65535).
		raw := binary.BigEndian.Uint16(sum[:2])
		port := 1024 + int(raw)%(65535-1024)
		if !seen[port] {
			seen[port] = true
			ports = append(ports, port)
		}
	}
	return ports
}

// ClientPortMux wraps a single UDP socket with bidirectional port rewriting so
// that port hops are invisible to quic-go. It implements net.PacketConn and
// net.Conn so it composes cleanly with the existing tolerateTransientRouteErrors
// wrapper.
//
// It deliberately does NOT implement quic.OOBCapablePacketConn. quic-go binds
// OOB-capable conns with ipv4.NewPacketConn and reads them with recvmmsg
// directly on the raw file descriptor, bypassing ReadMsgUDP: hop-port source
// addresses would never be normalised back to the primary port, the
// send/receive counters would never move, and the HopController would fire on
// phantom zero-receive. The plain ReadFrom/WriteTo path keeps the rewriting
// and counters exact, at the cost of ECN/GSO/batched I/O on hop-enabled
// sockets — a fair trade on the hostile paths hopping exists for.
//
// Thread safety: all exported methods are safe for concurrent use. Hop() is
// the only writer of currentIdx and is called at most once per cooldown
// window.
type ClientPortMux struct {
	conn        *net.UDPConn
	primaryAddr *net.UDPAddr
	ports       []int
	currentIdx  atomic.Int32

	// sendCount and recvCount are incremented on every outgoing / incoming
	// datagram respectively. HopController samples them to detect zero-receive
	// windows indicative of per-port GFW blocking.
	sendCount atomic.Uint64
	recvCount atomic.Uint64

	// ctx/cancel signal the HopController goroutine to stop when the socket
	// is closed.
	ctx       context.Context
	cancel    context.CancelFunc
	closeOnce sync.Once
}

// NewClientPortMux creates a mux on conn. primaryAddr must match ports[0].
// The mux starts on the primary port; call HopController.Run to begin loss
// monitoring.
func NewClientPortMux(conn *net.UDPConn, primaryAddr *net.UDPAddr, ports []int) *ClientPortMux {
	ctx, cancel := context.WithCancel(context.Background())
	return &ClientPortMux{
		conn:        conn,
		primaryAddr: primaryAddr,
		ports:       ports,
		ctx:         ctx,
		cancel:      cancel,
	}
}

// Context returns a context that is cancelled when Close is called.
// HopController uses this to know when to stop its monitoring goroutine.
func (m *ClientPortMux) Context() context.Context { return m.ctx }

// Ports returns the full ordered port list. The caller must not modify it.
func (m *ClientPortMux) Ports() []int { return m.ports }

// PrimaryAddr returns the primary (quic-go-visible) peer address.
func (m *ClientPortMux) PrimaryAddr() *net.UDPAddr { return m.primaryAddr }

// CurrentPort returns the currently active hop port.
func (m *ClientPortMux) CurrentPort() int {
	return m.ports[m.currentIdx.Load()]
}

// CurrentIndex returns the port-list index the mux is currently sending to.
func (m *ClientPortMux) CurrentIndex() int32 {
	return m.currentIdx.Load()
}

// Hop atomically switches to ports[idx], returning the old and new ports.
// The caller (HopController) is responsible for bounds-checking idx.
func (m *ClientPortMux) Hop(idx int32) (fromPort, toPort int) {
	old := m.currentIdx.Swap(idx)
	return m.ports[old], m.ports[idx]
}

// SendCount and RecvCount are the total datagram counts since the mux was
// created. HopController takes snapshots to compute the rate over a window.
func (m *ClientPortMux) SendCount() uint64 { return m.sendCount.Load() }
func (m *ClientPortMux) RecvCount() uint64 { return m.recvCount.Load() }

// hopTarget rewrites addr to target the current hop port when it matches the
// primary address. It returns addr unchanged for any other destination.
func (m *ClientPortMux) hopTarget(addr net.Addr) net.Addr {
	u, ok := addr.(*net.UDPAddr)
	if !ok {
		return addr
	}
	hopPort := m.ports[m.currentIdx.Load()]
	if u.Port == m.primaryAddr.Port && hopPort != m.primaryAddr.Port {
		return &net.UDPAddr{IP: u.IP, Port: hopPort, Zone: u.Zone}
	}
	return addr
}

// normSrc rewrites the source address of an incoming packet from any hop port
// back to the primary port so quic-go sees a stable peer address.
func (m *ClientPortMux) normSrc(addr *net.UDPAddr) *net.UDPAddr {
	if addr == nil || addr.Port == m.primaryAddr.Port {
		return addr
	}
	if !addr.IP.Equal(m.primaryAddr.IP) {
		return addr
	}
	// Linear scan is fine: port lists are small (≤100 elements).
	for _, p := range m.ports {
		if p == addr.Port {
			return &net.UDPAddr{IP: addr.IP, Port: m.primaryAddr.Port, Zone: addr.Zone}
		}
	}
	return addr
}

// — net.PacketConn —

func (m *ClientPortMux) ReadFrom(b []byte) (int, net.Addr, error) {
	n, addr, err := m.conn.ReadFrom(b)
	if err == nil {
		m.recvCount.Add(1)
		if u, ok := addr.(*net.UDPAddr); ok {
			addr = m.normSrc(u)
		}
	}
	return n, addr, err
}

func (m *ClientPortMux) WriteTo(b []byte, addr net.Addr) (int, error) {
	m.sendCount.Add(1)
	return m.conn.WriteTo(b, m.hopTarget(addr))
}

func (m *ClientPortMux) Close() error {
	var err error
	m.closeOnce.Do(func() {
		m.cancel()
		err = m.conn.Close()
	})
	return err
}

func (m *ClientPortMux) LocalAddr() net.Addr           { return m.conn.LocalAddr() }
func (m *ClientPortMux) SetDeadline(t time.Time) error { return m.conn.SetDeadline(t) }
func (m *ClientPortMux) SetReadDeadline(t time.Time) error {
	return m.conn.SetReadDeadline(t)
}
func (m *ClientPortMux) SetWriteDeadline(t time.Time) error {
	return m.conn.SetWriteDeadline(t)
}

// — net.Conn (required by transientRoutePacketConn's type assertion) —

func (m *ClientPortMux) Read(b []byte) (int, error)  { return m.conn.Read(b) }
func (m *ClientPortMux) Write(b []byte) (int, error) { return m.conn.Write(b) }
func (m *ClientPortMux) RemoteAddr() net.Addr        { return m.primaryAddr }

func (m *ClientPortMux) SetReadBuffer(bytes int) error {
	return m.conn.SetReadBuffer(bytes)
}

// — ServerPortMux —

// serverPacket carries one UDP datagram received by any of the server's
// listening sockets.
type serverPacket struct {
	data []byte
	src  *net.UDPAddr
	conn *net.UDPConn // socket the datagram arrived on
}

// ServerPortMux listens on N UDP ports simultaneously and presents them as a
// single net.PacketConn to quic.Listen. It remembers which socket each client
// address most recently used and routes responses back through that socket so
// the client's address-rewriting stays consistent.
//
// Like ClientPortMux it deliberately does NOT implement
// quic.OOBCapablePacketConn: quic-go would read the primary socket directly
// with recvmmsg, racing this mux's reader goroutines for primary packets and
// never touching the merged queue the hop-port sockets feed. Every packet the
// listener processes must come through ReadFrom.
//
// Thread safety: all exported methods are safe for concurrent use.
type ServerPortMux struct {
	primary     *net.UDPConn
	secondaries []*net.UDPConn
	// skipped records hop ports the host refused, so a degraded pool is
	// visible in the log rather than silently narrower than configured.
	skipped []int
	// incoming is the merged receive queue. It is sized large enough to absorb
	// bursts across all sockets without a secondary blocking a primary read.
	incoming  chan serverPacket
	routes    sync.Map // string(client addr) → *net.UDPConn
	done      chan struct{}
	closeOnce sync.Once
	wg        sync.WaitGroup
}

// NewServerPortMux binds additional sockets on ports[1:] on the same IP as
// primary, starts per-socket reader goroutines, and returns the multiplexed
// PacketConn. primary must already be bound to ports[0].
//
// A hop port that cannot be bound is skipped rather than fatal, and the caller
// can read which ones with SkippedPorts. The pool is derived from a hash over
// the provider identity, so it is only a matter of time before a derivation
// lands on a port the host will not hand out: Windows carves dynamic exclusion
// ranges out of [1024, 65535) for WinNAT and Hyper-V and refuses them with a
// permissions error, Linux has ip_local_reserved_ports, and on any host
// another service may already hold one. Refusing to start a gateway because
// one of several hop ports is unavailable trades a working deployment for a
// slightly wider pool, which is the wrong way round -- hopping is best-effort
// by construction, and a client that hops to a port this server could not bind
// sees the same silence it sees from a blocked port and hops again.
//
// Losing every hop port is different, and still an error. It means hopping is
// entirely non-functional rather than degraded, which an operator who asked
// for it needs to be told rather than left to infer from traffic that never
// evades anything.
//
// On error, any successfully opened extra sockets are closed before returning.
func NewServerPortMux(primary *net.UDPConn, ports []int) (*ServerPortMux, error) {
	primaryAddr, ok := primary.LocalAddr().(*net.UDPAddr)
	if !ok {
		return nil, fmt.Errorf("server portmux: primary socket has non-UDP local address")
	}

	secondaries := make([]*net.UDPConn, 0, len(ports)-1)
	var skipped []int
	var lastErr error
	for _, port := range ports[1:] {
		addr := &net.UDPAddr{IP: primaryAddr.IP, Port: port}
		conn, err := net.ListenUDP("udp", addr)
		if err != nil {
			skipped = append(skipped, port)
			lastErr = err
			continue
		}
		secondaries = append(secondaries, conn)
	}
	if len(ports) > 1 && len(secondaries) == 0 {
		return nil, fmt.Errorf("server portmux: no hop port could be bound, last error on %d: %w",
			skipped[len(skipped)-1], lastErr)
	}

	// Buffer depth: 4096 slots shared across all sockets. At 1500 B/packet
	// this is ~6 MB peak, bounded by the OS receive buffers in practice.
	m := &ServerPortMux{
		primary:     primary,
		secondaries: secondaries,
		skipped:     skipped,
		incoming:    make(chan serverPacket, 4096),
		done:        make(chan struct{}),
	}

	m.wg.Add(1)
	go m.readSocket(m.primary)
	for _, sec := range secondaries {
		m.wg.Add(1)
		go m.readSocket(sec)
	}

	return m, nil
}

// SkippedPorts returns the hop ports this host would not bind. The caller must
// not modify it.
func (m *ServerPortMux) SkippedPorts() []int { return m.skipped }

// readSocket copies datagrams from one listening socket into the merged
// incoming queue, tagging each with the socket it arrived on so replies can
// take the same path back.
func (m *ServerPortMux) readSocket(conn *net.UDPConn) {
	defer m.wg.Done()
	buf := make([]byte, 1500)
	for {
		n, addr, err := conn.ReadFrom(buf)
		if err != nil {
			return
		}
		src, _ := addr.(*net.UDPAddr)
		data := make([]byte, n)
		copy(data, buf[:n])
		pkt := serverPacket{data: data, src: src, conn: conn}
		select {
		case m.incoming <- pkt:
		case <-m.done:
			return
		}
	}
}

// pickConn returns the socket most recently used by addr, falling back to the
// primary socket if no mapping exists.
func (m *ServerPortMux) pickConn(addr *net.UDPAddr) *net.UDPConn {
	if v, ok := m.routes.Load(addr.String()); ok {
		return v.(*net.UDPConn)
	}
	return m.primary
}

// — net.PacketConn —

// ReadFrom returns the next datagram from the merged receive queue and updates
// the routing table so responses go back through the correct socket. Closing
// the mux unblocks it, since quic-go's read loop parks here.
func (m *ServerPortMux) ReadFrom(b []byte) (int, net.Addr, error) {
	select {
	case pkt, ok := <-m.incoming:
		if !ok {
			return 0, nil, net.ErrClosed
		}
		n := copy(b, pkt.data)
		m.routes.Store(pkt.src.String(), pkt.conn)
		return n, pkt.src, nil
	case <-m.done:
		return 0, nil, net.ErrClosed
	}
}

func (m *ServerPortMux) WriteTo(b []byte, addr net.Addr) (int, error) {
	u, ok := addr.(*net.UDPAddr)
	if !ok {
		return 0, fmt.Errorf("server portmux: WriteTo addr is not *net.UDPAddr")
	}
	return m.pickConn(u).WriteTo(b, addr)
}

func (m *ServerPortMux) Close() error {
	var err error
	m.closeOnce.Do(func() {
		close(m.done)
		err = m.primary.Close()
		for _, s := range m.secondaries {
			if e := s.Close(); e != nil && err == nil {
				err = e
			}
		}
		m.wg.Wait()
	})
	return err
}

func (m *ServerPortMux) LocalAddr() net.Addr {
	return m.primary.LocalAddr()
}

func (m *ServerPortMux) SetDeadline(t time.Time) error {
	if err := m.primary.SetDeadline(t); err != nil {
		return err
	}
	for _, s := range m.secondaries {
		if err := s.SetDeadline(t); err != nil {
			return err
		}
	}
	return nil
}

func (m *ServerPortMux) SetReadDeadline(t time.Time) error {
	if err := m.primary.SetReadDeadline(t); err != nil {
		return err
	}
	for _, s := range m.secondaries {
		if err := s.SetReadDeadline(t); err != nil {
			return err
		}
	}
	return nil
}

func (m *ServerPortMux) SetWriteDeadline(t time.Time) error {
	if err := m.primary.SetWriteDeadline(t); err != nil {
		return err
	}
	for _, s := range m.secondaries {
		if err := s.SetWriteDeadline(t); err != nil {
			return err
		}
	}
	return nil
}

func (m *ServerPortMux) SetReadBuffer(bytes int) error {
	return m.primary.SetReadBuffer(bytes)
}
