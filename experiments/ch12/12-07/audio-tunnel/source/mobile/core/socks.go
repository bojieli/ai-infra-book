// Package mobilecore provides the shared, platform-neutral Queqiao mobile
// runtime. It deliberately implements its SOCKS client locally instead of
// embedding a general-purpose proxy or tun2socks implementation.
package mobilecore

import (
	"bufio"
	"context"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"net"
	"net/netip"
	"strconv"
	"time"
)

const (
	socksVersion      = 5
	socksNoAuth       = 0
	socksConnect      = 1
	socksUDPAssociate = 3
	socksIPv4         = 1
	socksDomain       = 3
	socksIPv6         = 4
	socksSucceeded    = 0
	maxUDPPacket      = 64 * 1024
)

var errSocksMethodUnavailable = errors.New("local SOCKS server rejected authentication methods")

type socksClient struct {
	address          string
	handshakeTimeout time.Duration
}

func (c socksClient) dialTCP(ctx context.Context, destination netip.AddrPort) (net.Conn, error) {
	conn, reader, err := c.dialControl(ctx)
	if err != nil {
		return nil, err
	}
	request, err := socksRequest(socksConnect, destination)
	if err != nil {
		_ = conn.Close()
		return nil, err
	}
	if err := writeFull(conn, request); err != nil {
		_ = conn.Close()
		return nil, fmt.Errorf("write SOCKS CONNECT: %w", err)
	}
	if _, err := readSocksReply(reader); err != nil {
		_ = conn.Close()
		return nil, fmt.Errorf("read SOCKS CONNECT reply: %w", err)
	}
	if err := conn.SetDeadline(time.Time{}); err != nil {
		_ = conn.Close()
		return nil, err
	}
	return conn, nil
}

// dialTCPDomain opens a connection naming the destination rather than
// addressing it.
//
// A flow the fake resolver answered carries a handle out of 198.18.0.0/15,
// which means something only inside this process. Sending that to the gateway
// would ask it to connect to a benchmarking address on its own network. SOCKS5
// carries a domain form for exactly this, and using it also puts the name
// resolution at the far end, which is where a proxied flow wants it: the
// gateway resolves from its own vantage, which is the vantage the flow is
// being sent to use.
func (c socksClient) dialTCPDomain(ctx context.Context, host string, port uint16) (net.Conn, error) {
	conn, reader, err := c.dialControl(ctx)
	if err != nil {
		return nil, err
	}
	request, err := socksDomainRequest(socksConnect, host, port)
	if err != nil {
		_ = conn.Close()
		return nil, err
	}
	if err := writeFull(conn, request); err != nil {
		_ = conn.Close()
		return nil, fmt.Errorf("write SOCKS CONNECT: %w", err)
	}
	if _, err := readSocksReply(reader); err != nil {
		_ = conn.Close()
		return nil, fmt.Errorf("read SOCKS CONNECT reply: %w", err)
	}
	if err := conn.SetDeadline(time.Time{}); err != nil {
		_ = conn.Close()
		return nil, err
	}
	return conn, nil
}

func (c socksClient) dialUDP(ctx context.Context) (*socksUDPAssociation, error) {
	control, reader, err := c.dialControl(ctx)
	if err != nil {
		return nil, err
	}
	fail := func(err error) (*socksUDPAssociation, error) {
		_ = control.Close()
		return nil, err
	}
	request, err := socksRequest(socksUDPAssociate, netip.AddrPortFrom(netip.IPv4Unspecified(), 0))
	if err != nil {
		return fail(err)
	}
	if err := writeFull(control, request); err != nil {
		return fail(fmt.Errorf("write SOCKS UDP ASSOCIATE: %w", err))
	}
	relay, err := readSocksReply(reader)
	if err != nil {
		return fail(fmt.Errorf("read SOCKS UDP ASSOCIATE reply: %w", err))
	}
	if relay.host == "0.0.0.0" || relay.host == "::" || relay.host == "" {
		host, _, splitErr := net.SplitHostPort(control.RemoteAddr().String())
		if splitErr != nil {
			return fail(fmt.Errorf("resolve SOCKS relay host: %w", splitErr))
		}
		relay.host = host
	}
	relayAddress := net.JoinHostPort(relay.host, strconv.Itoa(int(relay.port)))
	udp, err := (&net.Dialer{}).DialContext(ctx, "udp", relayAddress)
	if err != nil {
		return fail(fmt.Errorf("connect SOCKS UDP relay: %w", err))
	}
	if err := control.SetDeadline(time.Time{}); err != nil {
		_ = udp.Close()
		return fail(err)
	}
	return &socksUDPAssociation{control: control, packet: udp}, nil
}

func (c socksClient) dialControl(ctx context.Context) (net.Conn, *bufio.Reader, error) {
	timeout := c.handshakeTimeout
	if timeout <= 0 {
		timeout = 10 * time.Second
	}
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()
	conn, err := (&net.Dialer{}).DialContext(ctx, "tcp", c.address)
	if err != nil {
		return nil, nil, fmt.Errorf("connect local SOCKS server: %w", err)
	}
	deadline, ok := ctx.Deadline()
	if ok {
		_ = conn.SetDeadline(deadline)
	}
	fail := func(err error) (net.Conn, *bufio.Reader, error) {
		_ = conn.Close()
		return nil, nil, err
	}
	if err := writeFull(conn, []byte{socksVersion, 1, socksNoAuth}); err != nil {
		return fail(fmt.Errorf("write SOCKS greeting: %w", err))
	}
	var response [2]byte
	if _, err := io.ReadFull(conn, response[:]); err != nil {
		return fail(fmt.Errorf("read SOCKS greeting: %w", err))
	}
	if response[0] != socksVersion {
		return fail(fmt.Errorf("SOCKS server returned version %#02x", response[0]))
	}
	if response[1] == 0xff {
		return fail(fmt.Errorf("%w: no offered method was accepted", errSocksMethodUnavailable))
	}
	if response[1] != socksNoAuth {
		// The packet engine owns the listener it is dialing and deliberately
		// offers no authentication. In particular, do not pretend that GSSAPI
		// (0x01) or username/password (0x02) succeeded: proceeding would leave
		// the connection positioned at the wrong protocol boundary and the next
		// error would be reported as a misleading TCP/UDP proxy failure.
		return fail(fmt.Errorf("SOCKS server selected unsupported authentication method %#02x", response[1]))
	}
	return conn, bufio.NewReaderSize(conn, 512), nil
}

type socksAddress struct {
	host string
	port uint16
}

func socksRequest(command byte, destination netip.AddrPort) ([]byte, error) {
	address, err := appendSocksAddr(nil, destination)
	if err != nil {
		return nil, err
	}
	request := make([]byte, 0, 3+len(address))
	request = append(request, socksVersion, command, 0)
	return append(request, address...), nil
}

// socksDomainRequest builds a request whose destination is a name. The length
// is a single byte on the wire, so a name that cannot be expressed is refused
// here rather than truncated into a request for a different host.
func socksDomainRequest(command byte, host string, port uint16) ([]byte, error) {
	if host == "" {
		return nil, errors.New("SOCKS destination name is empty")
	}
	if len(host) > 255 {
		return nil, fmt.Errorf("SOCKS destination name is %d bytes, over the 255 the wire allows", len(host))
	}
	request := make([]byte, 0, 7+len(host))
	// #nosec G115 -- the length is refused above if it exceeds 255, which is
	// the whole reason that check is there rather than a truncation here.
	request = append(request, socksVersion, command, 0, socksDomain, byte(len(host)))
	request = append(request, host...)
	return binary.BigEndian.AppendUint16(request, port), nil
}

func appendSocksAddr(dst []byte, address netip.AddrPort) ([]byte, error) {
	if !address.IsValid() {
		return nil, errors.New("invalid destination address")
	}
	addr := address.Addr().Unmap()
	if addr.Is4() {
		bytes := addr.As4()
		dst = append(dst, socksIPv4)
		dst = append(dst, bytes[:]...)
	} else if addr.Is6() {
		bytes := addr.As16()
		dst = append(dst, socksIPv6)
		dst = append(dst, bytes[:]...)
	} else {
		return nil, errors.New("SOCKS destination must be IPv4 or IPv6")
	}
	return binary.BigEndian.AppendUint16(dst, address.Port()), nil
}

func readSocksReply(reader io.Reader) (socksAddress, error) {
	var header [3]byte
	if _, err := io.ReadFull(reader, header[:]); err != nil {
		return socksAddress{}, err
	}
	if header[0] != socksVersion || header[2] != 0 {
		return socksAddress{}, errors.New("malformed SOCKS reply")
	}
	if header[1] != socksSucceeded {
		return socksAddress{}, fmt.Errorf("SOCKS request failed with reply %#x", header[1])
	}
	return readSocksAddr(reader)
}

func readSocksAddr(reader io.Reader) (socksAddress, error) {
	var atyp [1]byte
	if _, err := io.ReadFull(reader, atyp[:]); err != nil {
		return socksAddress{}, err
	}
	var host string
	switch atyp[0] {
	case socksIPv4:
		var raw [4]byte
		if _, err := io.ReadFull(reader, raw[:]); err != nil {
			return socksAddress{}, err
		}
		host = netip.AddrFrom4(raw).String()
	case socksIPv6:
		var raw [16]byte
		if _, err := io.ReadFull(reader, raw[:]); err != nil {
			return socksAddress{}, err
		}
		host = netip.AddrFrom16(raw).String()
	case socksDomain:
		var length [1]byte
		if _, err := io.ReadFull(reader, length[:]); err != nil {
			return socksAddress{}, err
		}
		if length[0] == 0 {
			return socksAddress{}, errors.New("SOCKS reply contains an empty domain")
		}
		raw := make([]byte, int(length[0]))
		if _, err := io.ReadFull(reader, raw); err != nil {
			return socksAddress{}, err
		}
		host = string(raw)
	default:
		return socksAddress{}, fmt.Errorf("unsupported SOCKS address type %#x", atyp[0])
	}
	var port [2]byte
	if _, err := io.ReadFull(reader, port[:]); err != nil {
		return socksAddress{}, err
	}
	return socksAddress{host: host, port: binary.BigEndian.Uint16(port[:])}, nil
}

type socksUDPAssociation struct {
	control net.Conn
	packet  net.Conn
}

func (a *socksUDPAssociation) Close() error {
	packetErr := a.packet.Close()
	controlErr := a.control.Close()
	return errors.Join(packetErr, controlErr)
}

func (a *socksUDPAssociation) SetDeadline(deadline time.Time) error {
	return a.packet.SetDeadline(deadline)
}

func (a *socksUDPAssociation) WriteTo(payload []byte, destination netip.AddrPort) error {
	if len(payload) > maxUDPPacket {
		return fmt.Errorf("UDP payload is too large: %d bytes", len(payload))
	}
	header, err := appendSocksAddr([]byte{0, 0, 0}, destination)
	if err != nil {
		return err
	}
	packet := make([]byte, len(header)+len(payload))
	copy(packet, header)
	copy(packet[len(header):], payload)
	return writeFull(a.packet, packet)
}

func (a *socksUDPAssociation) ReadFrom(payload []byte, expected netip.AddrPort) (int, error) {
	// The caller chooses its bounded datagram capacity. Reserving 64 KiB here
	// for every active UDP flow multiplied memory even though a 1,280-byte TUN
	// normally carries sub-1,232-byte payloads.
	packet := make([]byte, len(payload)+22)
	n, err := a.packet.Read(packet)
	if err != nil {
		return 0, err
	}
	if n < 4 || packet[0] != 0 || packet[1] != 0 || packet[2] != 0 {
		return 0, errors.New("malformed or fragmented SOCKS UDP packet")
	}
	reader := bytesReader(packet[3:n])
	source, err := readSocksAddr(&reader)
	if err != nil {
		return 0, fmt.Errorf("parse SOCKS UDP source: %w", err)
	}
	parsed, err := netip.ParseAddrPort(net.JoinHostPort(source.host, strconv.Itoa(int(source.port))))
	if err != nil || parsed != expected {
		return 0, errors.New("SOCKS UDP source does not match the associated destination")
	}
	if reader.Len() > len(payload) {
		return 0, io.ErrShortBuffer
	}
	return reader.Read(payload)
}

type bytesReader []byte

func (r *bytesReader) Read(p []byte) (int, error) {
	if len(*r) == 0 {
		return 0, io.EOF
	}
	n := copy(p, *r)
	*r = (*r)[n:]
	return n, nil
}

func (r *bytesReader) Len() int { return len(*r) }

func writeFull(writer io.Writer, data []byte) error {
	for len(data) != 0 {
		n, err := writer.Write(data)
		if err != nil {
			return err
		}
		if n <= 0 || n > len(data) {
			return io.ErrShortWrite
		}
		data = data[n:]
	}
	return nil
}
