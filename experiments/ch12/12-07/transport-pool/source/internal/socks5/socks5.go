// Package socks5 implements the bounded SOCKS5 surface used by the local
// agent. It supports TCP CONNECT and UDP ASSOCIATE with either no
// authentication or RFC 1929 username/password; BIND and every other
// authentication method are rejected explicitly.
package socks5

import (
	"crypto/subtle"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"net"
	"strconv"
)

const (
	version5             = 5
	methodNone           = 0
	methodUserPass       = 2
	methodNoneAcceptable = 0xff

	// userPassVersion is the RFC 1929 sub-negotiation version, which is
	// independent of the SOCKS version in the surrounding exchange.
	userPassVersion = 1
	userPassSuccess = 0
	userPassFailure = 1

	maxUserPassFieldLength = 255

	CommandConnect      = 1
	CommandUDPAssociate = 3

	ReplySucceeded              = 0
	ReplyGeneralFailure         = 1
	ReplyConnectionNotAllowed   = 2
	ReplyNetworkUnreachable     = 3
	ReplyHostUnreachable        = 4
	ReplyConnectionRefused      = 5
	ReplyTTLExpired             = 6
	ReplyCommandNotSupported    = 7
	ReplyAddressTypeUnsupported = 8
)

// WriteMethodUnavailable sends the RFC 1928 method-selection response used
// when a listener cannot admit a new client. It must be sent during greeting
// negotiation, before a request reply; writing ReplyGeneralFailure here would
// make the first request byte look like an authentication method (0x01) to a
// client that is still waiting for the two-byte method response.
func WriteMethodUnavailable(w io.Writer) error {
	return writeFull(w, []byte{version5, methodNoneAcceptable})
}

type Request struct {
	Command     byte
	Destination string
}

// Credentials is one RFC 1929 username/password pair. A nil *Credentials
// selects no-authentication; a non-nil one makes username/password the only
// acceptable method, so a client that offers no-authentication is rejected
// rather than silently downgraded.
type Credentials struct {
	Username string
	Password string
}

// Validate reports whether the pair fits the RFC 1929 wire encoding. Both
// fields are length-prefixed with a single byte, and an empty username cannot
// be distinguished from an absent one by a peer.
func (c *Credentials) Validate() error {
	if c == nil {
		return nil
	}
	if c.Username == "" {
		return errors.New("SOCKS5 username must not be empty")
	}
	if len(c.Username) > maxUserPassFieldLength {
		return fmt.Errorf("SOCKS5 username exceeds %d bytes", maxUserPassFieldLength)
	}
	if len(c.Password) > maxUserPassFieldLength {
		return fmt.Errorf("SOCKS5 password exceeds %d bytes", maxUserPassFieldLength)
	}
	return nil
}

// matches compares a presented pair without a data-dependent branch. Both
// fields are always compared so the running time does not reveal which one
// differed.
func (c *Credentials) matches(username, password string) bool {
	user := subtle.ConstantTimeCompare([]byte(c.Username), []byte(username))
	pass := subtle.ConstantTimeCompare([]byte(c.Password), []byte(password))
	return user&pass == 1
}

type UDPDatagram struct {
	Destination string
	Payload     []byte
}

// ReadRequest performs method negotiation, any required authentication, and
// then reads one request. Passing nil credentials preserves the
// no-authentication behaviour used by the loopback desktop listener.
func ReadRequest(rw io.ReadWriter, credentials *Credentials) (Request, error) {
	if err := credentials.Validate(); err != nil {
		return Request{}, err
	}
	if err := negotiateMethod(rw, credentials); err != nil {
		return Request{}, err
	}

	var header [4]byte
	if _, err := io.ReadFull(rw, header[:]); err != nil {
		return Request{}, fmt.Errorf("read request header: %w", err)
	}
	if header[0] != version5 || header[2] != 0 {
		return Request{}, errors.New("invalid SOCKS5 request header")
	}
	if header[1] != CommandConnect && header[1] != CommandUDPAssociate {
		_ = WriteReply(rw, ReplyCommandNotSupported, nil)
		return Request{}, errors.New("only SOCKS5 CONNECT and UDP ASSOCIATE are supported")
	}
	host, err := readHost(rw, header[3])
	if err != nil {
		_ = WriteReply(rw, ReplyAddressTypeUnsupported, nil)
		return Request{}, err
	}
	var portBytes [2]byte
	if _, err := io.ReadFull(rw, portBytes[:]); err != nil {
		return Request{}, fmt.Errorf("read destination port: %w", err)
	}
	port := binary.BigEndian.Uint16(portBytes[:])
	if port == 0 && header[1] == CommandConnect {
		_ = WriteReply(rw, ReplyAddressTypeUnsupported, nil)
		return Request{}, errors.New("destination port must not be zero")
	}
	return Request{Command: header[1], Destination: net.JoinHostPort(host, strconv.Itoa(int(port)))}, nil
}

// negotiateMethod selects exactly one method and completes it. The required
// method is decided by the listener's configuration, never by what the client
// prefers, so an unauthenticated client cannot negotiate authentication away.
func negotiateMethod(rw io.ReadWriter, credentials *Credentials) error {
	required := byte(methodNone)
	if credentials != nil {
		required = methodUserPass
	}

	var greeting [2]byte
	if _, err := io.ReadFull(rw, greeting[:]); err != nil {
		return fmt.Errorf("read greeting: %w", err)
	}
	if greeting[0] != version5 || greeting[1] == 0 {
		return errors.New("invalid SOCKS5 greeting")
	}
	methods := make([]byte, int(greeting[1]))
	if _, err := io.ReadFull(rw, methods); err != nil {
		return fmt.Errorf("read methods: %w", err)
	}
	found := false
	for _, method := range methods {
		if method == required {
			found = true
			break
		}
	}
	if !found {
		_, _ = rw.Write([]byte{version5, methodNoneAcceptable})
		if required == methodUserPass {
			return errors.New("client did not offer username/password authentication")
		}
		return errors.New("client did not offer no-authentication method")
	}
	if err := writeFull(rw, []byte{version5, required}); err != nil {
		return fmt.Errorf("write method selection: %w", err)
	}
	if credentials == nil {
		return nil
	}
	return authenticate(rw, credentials)
}

// authenticate runs the RFC 1929 sub-negotiation. A failed exchange still
// receives a well-formed failure reply so a misconfigured client reports an
// authentication error rather than a protocol error.
func authenticate(rw io.ReadWriter, credentials *Credentials) error {
	var prefix [2]byte
	if _, err := io.ReadFull(rw, prefix[:]); err != nil {
		return fmt.Errorf("read authentication header: %w", err)
	}
	if prefix[0] != userPassVersion {
		_ = writeFull(rw, []byte{userPassVersion, userPassFailure})
		return errors.New("unsupported SOCKS5 authentication version")
	}
	if prefix[1] == 0 {
		_ = writeFull(rw, []byte{userPassVersion, userPassFailure})
		return errors.New("empty SOCKS5 username")
	}
	username := make([]byte, int(prefix[1]))
	if _, err := io.ReadFull(rw, username); err != nil {
		return fmt.Errorf("read username: %w", err)
	}
	var passwordLength [1]byte
	if _, err := io.ReadFull(rw, passwordLength[:]); err != nil {
		return fmt.Errorf("read password length: %w", err)
	}
	password := make([]byte, int(passwordLength[0]))
	if _, err := io.ReadFull(rw, password); err != nil {
		return fmt.Errorf("read password: %w", err)
	}
	if !credentials.matches(string(username), string(password)) {
		_ = writeFull(rw, []byte{userPassVersion, userPassFailure})
		return errors.New("SOCKS5 authentication rejected")
	}
	if err := writeFull(rw, []byte{userPassVersion, userPassSuccess}); err != nil {
		return fmt.Errorf("write authentication reply: %w", err)
	}
	return nil
}

const (
	udpHeaderSize = 4 // RSV(2), FRAG(1), ATYP(1)
	// Maximum UDP payload before IP fragmentation. SOCKS5 adds a destination
	// header around it, so the request remains within the UDP protocol bound.
	maxUDPDatagramSize = 65507
	maxUDPDomainLength = 255
)

// ReadUDPDatagram parses the RFC 1928 UDP request header. Fragmentation is
// deliberately rejected: the PEP packet itself is bounded and fragmentation
// must not create an unbounded per-association reassembly state.
func ReadUDPDatagram(packet []byte) (UDPDatagram, error) {
	if len(packet) < udpHeaderSize+2 || len(packet) > maxUDPDatagramSize {
		return UDPDatagram{}, errors.New("invalid SOCKS5 UDP datagram length")
	}
	if packet[0] != 0 || packet[1] != 0 {
		return UDPDatagram{}, errors.New("invalid SOCKS5 UDP reserved bytes")
	}
	if packet[2] != 0 {
		return UDPDatagram{}, errors.New("fragmented SOCKS5 UDP datagrams are unsupported")
	}
	host, used, err := readHostBytes(packet[udpHeaderSize:], packet[3])
	if err != nil {
		return UDPDatagram{}, err
	}
	portOffset := udpHeaderSize + used
	if portOffset+2 > len(packet) {
		return UDPDatagram{}, io.ErrUnexpectedEOF
	}
	port := binary.BigEndian.Uint16(packet[portOffset : portOffset+2])
	if port == 0 {
		return UDPDatagram{}, errors.New("SOCKS5 UDP destination port must not be zero")
	}
	return UDPDatagram{
		Destination: net.JoinHostPort(host, strconv.Itoa(int(port))),
		Payload:     append([]byte(nil), packet[portOffset+2:]...),
	}, nil
}

func WriteUDPDatagram(w io.Writer, destination string, payload []byte) error {
	if len(payload) > maxUDPDatagramSize {
		return fmt.Errorf("UDP payload exceeds %d bytes", maxUDPDatagramSize)
	}
	host, portText, err := net.SplitHostPort(destination)
	if err != nil || host == "" {
		return errors.New("invalid UDP destination")
	}
	port, err := strconv.Atoi(portText)
	if err != nil || port < 1 || port > 65535 {
		return errors.New("invalid UDP destination port")
	}
	address, err := encodeHost(host)
	if err != nil {
		return err
	}
	packet := make([]byte, 0, udpHeaderSize+len(address)+2+len(payload))
	packet = append(packet, 0, 0, 0)
	packet = append(packet, address...)
	var portBytes [2]byte
	binary.BigEndian.PutUint16(portBytes[:], uint16(port))
	packet = append(packet, portBytes[:]...)
	packet = append(packet, payload...)
	return writeFull(w, packet)
}

func readHost(r io.Reader, addressType byte) (string, error) {
	switch addressType {
	case 1:
		var ip [4]byte
		if _, err := io.ReadFull(r, ip[:]); err != nil {
			return "", fmt.Errorf("read IPv4 address: %w", err)
		}
		return net.IP(ip[:]).String(), nil
	case 3:
		var length [1]byte
		if _, err := io.ReadFull(r, length[:]); err != nil {
			return "", fmt.Errorf("read domain length: %w", err)
		}
		if length[0] == 0 {
			return "", errors.New("empty domain name")
		}
		domain := make([]byte, int(length[0]))
		if _, err := io.ReadFull(r, domain); err != nil {
			return "", fmt.Errorf("read domain name: %w", err)
		}
		return string(domain), nil
	case 4:
		var ip [16]byte
		if _, err := io.ReadFull(r, ip[:]); err != nil {
			return "", fmt.Errorf("read IPv6 address: %w", err)
		}
		return net.IP(ip[:]).String(), nil
	default:
		return "", fmt.Errorf("unsupported SOCKS5 address type %d", addressType)
	}
}

func readHostBytes(packet []byte, addressType byte) (string, int, error) {
	switch addressType {
	case 1:
		if len(packet) < 4 {
			return "", 0, io.ErrUnexpectedEOF
		}
		return net.IP(packet[:4]).String(), 4, nil
	case 3:
		if len(packet) < 1 {
			return "", 0, io.ErrUnexpectedEOF
		}
		length := int(packet[0])
		if length == 0 || length > maxUDPDomainLength || len(packet) < 1+length {
			return "", 0, errors.New("invalid SOCKS5 UDP domain")
		}
		return string(packet[1 : 1+length]), 1 + length, nil
	case 4:
		if len(packet) < 16 {
			return "", 0, io.ErrUnexpectedEOF
		}
		return net.IP(packet[:16]).String(), 16, nil
	default:
		return "", 0, fmt.Errorf("unsupported SOCKS5 UDP address type %d", addressType)
	}
}

func encodeHost(host string) ([]byte, error) {
	if ip := net.ParseIP(host); ip != nil {
		if ip4 := ip.To4(); ip4 != nil {
			return append([]byte{1}, ip4...), nil
		}
		if ip16 := ip.To16(); ip16 != nil {
			return append([]byte{4}, ip16...), nil
		}
	}
	if len(host) == 0 || len(host) > maxUDPDomainLength || len(host) > 255 {
		return nil, errors.New("invalid SOCKS5 UDP domain length")
	}
	return append([]byte{3, byte(len(host))}, []byte(host)...), nil
}

func WriteReply(w io.Writer, code byte, bound net.Addr) error {
	ip := net.IPv4zero
	port := 0
	switch address := bound.(type) {
	case *net.TCPAddr:
		if address != nil {
			ip = address.IP
			port = address.Port
		}
	case *net.UDPAddr:
		if address != nil {
			ip = address.IP
			port = address.Port
		}
	}
	var response []byte
	if ip4 := ip.To4(); ip4 != nil {
		response = make([]byte, 10)
		response[0], response[1], response[2], response[3] = version5, code, 0, 1
		copy(response[4:8], ip4)
		binary.BigEndian.PutUint16(response[8:10], uint16(port))
	} else {
		response = make([]byte, 22)
		response[0], response[1], response[2], response[3] = version5, code, 0, 4
		copy(response[4:20], ip.To16())
		binary.BigEndian.PutUint16(response[20:22], uint16(port))
	}
	return writeFull(w, response)
}

func writeFull(w io.Writer, p []byte) error {
	for len(p) > 0 {
		n, err := w.Write(p)
		if n > 0 {
			p = p[n:]
		}
		if err != nil {
			return err
		}
		if n == 0 {
			return io.ErrShortWrite
		}
	}
	return nil
}
