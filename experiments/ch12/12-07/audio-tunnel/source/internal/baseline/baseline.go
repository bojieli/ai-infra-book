// Package baseline implements a TUIC-shaped reference proxy on the same QUIC
// stack that queqiao uses.
//
// It exists purely as a measurement control. TUIC's data path is: one
// long-lived authenticated QUIC connection, one bidirectional stream per
// relayed TCP connection, a short `Connect` header carrying the destination,
// and then unframed byte copying in both directions. Reproducing exactly that
// shape in-process, over the identical quic-go fork and the identical
// congestion controllers, isolates "what does the TUIC design achieve here"
// from "what does the Go QUIC implementation achieve here", so a queqiao/TUIC
// gap can be attributed to queqiao's own framing, scheduling, and windows
// rather than to language or library differences.
//
// The transport windows follow TUIC's published defaults: a fixed 8 MiB
// stream receive window, a 16 MiB connection send window, and a 1200-byte
// initial packet size with MTU probing disabled.
package baseline

import (
	"context"
	"crypto/subtle"
	"crypto/tls"
	"crypto/x509"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net"
	"sync"
	"time"

	"github.com/apernet/quic-go"
	wancongestion "github.com/bojieli/queqiao/internal/congestion"
	"github.com/bojieli/queqiao/internal/socks5"
)

const (
	// ALPN is deliberately distinct from the queqiao ALPN so a misconfigured
	// benchmark cannot silently measure the wrong listener.
	ALPN = "queqiao-baseline/1"
	// tokenSize matches TUIC's 32-byte authentication token.
	tokenSize     = 32
	maxAddrLength = 255
)

// CongestionKind selects the sender for the baseline connection so it can be
// matched against a queqiao run.
type CongestionKind string

const (
	CongestionReno    CongestionKind = "reno"
	CongestionBBR     CongestionKind = "bbr"
	CongestionBBRTUIC CongestionKind = "bbr-tuic"
	// CongestionBrutal is not something TUIC offers. It exists here so a
	// controller can be held constant while the transport design varies:
	// otherwise a queqiao-with-Brutal versus reference-with-BBR result measures
	// the controller choice and says nothing about the transport.
	CongestionBrutal CongestionKind = "brutal"
)

// Transport mirrors TUIC's quinn transport knobs.
type Transport struct {
	SendWindow          uint64
	StreamReceiveWindow uint64
	InitialPacketSize   uint16
	MaxIdleTimeout      time.Duration
	KeepAlivePeriod     time.Duration
}

// TUICTransport returns TUIC's documented client defaults.
func TUICTransport() Transport {
	return Transport{
		SendWindow:          16 * 1024 * 1024,
		StreamReceiveWindow: 8 * 1024 * 1024,
		InitialPacketSize:   1200,
		MaxIdleTimeout:      15 * time.Second,
		KeepAlivePeriod:     5 * time.Second,
	}
}

func (t Transport) quicConfig() *quic.Config {
	if t.StreamReceiveWindow == 0 {
		t = TUICTransport()
	}
	if t.InitialPacketSize == 0 {
		t.InitialPacketSize = 1200
	}
	if t.MaxIdleTimeout == 0 {
		t.MaxIdleTimeout = 15 * time.Second
	}
	if t.KeepAlivePeriod == 0 {
		t.KeepAlivePeriod = 5 * time.Second
	}
	// quinn's stream_receive_window is a fixed limit with no ramp, so the
	// initial and maximum windows are set to the same value here. The
	// connection window is the send-window analogue: quinn's send_window
	// bounds how much unacknowledged connection data the sender will hold.
	return &quic.Config{
		HandshakeIdleTimeout:       10 * time.Second,
		MaxIdleTimeout:             t.MaxIdleTimeout,
		KeepAlivePeriod:            t.KeepAlivePeriod,
		InitialStreamReceiveWindow: t.StreamReceiveWindow,
		// Deliberately equal to the initial value: TUIC does not ramp its
		// receive window, and this reference's whole worth is that it is shaped
		// like TUIC. queqiao does ramp, which is a real advantage over TUIC and
		// must not be read as a scheduler advantage; see DESIGN-MULTIPATH 7.6.
		MaxStreamReceiveWindow:         t.StreamReceiveWindow,
		InitialConnectionReceiveWindow: t.SendWindow,
		MaxConnectionReceiveWindow:     t.SendWindow,
		MaxIncomingStreams:             1 << 12,
		MaxIncomingUniStreams:          0,
		DisablePathMTUDiscovery:        true,
		InitialPacketSize:              t.InitialPacketSize,
	}
}

func applyCongestion(conn *quic.Conn, kind CongestionKind, brutalBytesPerSecond uint64) {
	switch kind {
	case CongestionBBR:
		conn.SetCongestionControl(wancongestion.NewBBRSender(conn.InitialPacketSize()))
	case CongestionBBRTUIC:
		conn.SetCongestionControl(wancongestion.NewTUICBBRSender(conn.InitialPacketSize()))
	case CongestionBrutal:
		if brutalBytesPerSecond > 0 {
			conn.SetCongestionControl(wancongestion.NewBrutalSender(brutalBytesPerSecond, false))
		}
	}
}

// ---------------------------------------------------------------- server ---

type ServerConfig struct {
	ListenAddr  string
	Certificate tls.Certificate
	Token       []byte
	Transport   Transport
	Congestion  CongestionKind
	// BrutalBytesPerSec is required when Congestion is brutal.
	BrutalBytesPerSec uint64
	Logger            *slog.Logger
}

type Server struct {
	cfg ServerConfig
}

func NewServer(cfg ServerConfig) (*Server, error) {
	if len(cfg.Token) != tokenSize {
		return nil, fmt.Errorf("baseline token must be %d bytes", tokenSize)
	}
	if cfg.Logger == nil {
		cfg.Logger = slog.Default()
	}
	return &Server{cfg: cfg}, nil
}

func (s *Server) Serve(ctx context.Context, packet net.PacketConn) error {
	tlsCfg := &tls.Config{
		MinVersion:   tls.VersionTLS13,
		Certificates: []tls.Certificate{s.cfg.Certificate},
		NextProtos:   []string{ALPN},
	}
	listener, err := quic.Listen(packet, tlsCfg, s.cfg.Transport.quicConfig())
	if err != nil {
		return err
	}
	defer listener.Close()
	go func() {
		<-ctx.Done()
		_ = listener.Close()
	}()
	for {
		conn, acceptErr := listener.Accept(ctx)
		if acceptErr != nil {
			if ctx.Err() != nil {
				return nil
			}
			return acceptErr
		}
		applyCongestion(conn, s.cfg.Congestion, s.cfg.BrutalBytesPerSec)
		go s.serveConn(ctx, conn)
	}
}

func (s *Server) serveConn(ctx context.Context, conn *quic.Conn) {
	defer conn.CloseWithError(0, "baseline connection closed")
	authenticated := false
	for {
		stream, err := conn.AcceptStream(ctx)
		if err != nil {
			return
		}
		first := !authenticated
		authenticated = true
		go s.serveStream(ctx, stream, first)
	}
}

// serveStream reads the destination header and copies bytes. The first stream
// of a connection also carries the authentication token, mirroring TUIC's
// `Authenticate` command on the first multiplexed stream.
func (s *Server) serveStream(ctx context.Context, stream *quic.Stream, authenticate bool) {
	defer stream.Close()
	_ = stream.SetReadDeadline(time.Now().Add(30 * time.Second))
	if authenticate {
		var token [tokenSize]byte
		if _, err := io.ReadFull(stream, token[:]); err != nil {
			return
		}
		if subtle.ConstantTimeCompare(token[:], s.cfg.Token) != 1 {
			return
		}
	}
	var length [2]byte
	if _, err := io.ReadFull(stream, length[:]); err != nil {
		return
	}
	size := binary.BigEndian.Uint16(length[:])
	if size == 0 || size > maxAddrLength {
		return
	}
	addr := make([]byte, size)
	if _, err := io.ReadFull(stream, addr); err != nil {
		return
	}
	_ = stream.SetReadDeadline(time.Time{})
	destination, err := (&net.Dialer{Timeout: 10 * time.Second}).DialContext(ctx, "tcp", string(addr))
	if err != nil {
		return
	}
	defer destination.Close()
	relay(stream, destination)
}

// ---------------------------------------------------------------- client ---

type ClientConfig struct {
	ListenAddr string
	RemoteAddr string
	ServerName string
	RootCAs    *x509.CertPool
	Token      []byte
	Transport  Transport
	Congestion CongestionKind
	// BrutalBytesPerSec is required when Congestion is brutal.
	BrutalBytesPerSec uint64
	// LocalAddress binds the outer UDP socket to a specific local IP. On a
	// host running a TUN-mode proxy, an unbound socket is captured by the TUN
	// and the measurement would run through that tunnel rather than the path
	// under test. queqiao has the same option, and a comparison is only valid
	// when both sides use it identically.
	LocalAddress string
	// DialTimeout bounds one connection attempt. Zero selects a default.
	DialTimeout time.Duration
	Logger      *slog.Logger
}

// dialTimeout must be finite. A control that can hang indefinitely is worse
// than no control: during a lossy window one unbounded dial wedged this client
// for an entire campaign and made the transport under test look good for a
// reason that had nothing to do with it.
const defaultDialTimeout = 10 * time.Second

type Client struct {
	cfg ClientConfig

	// dialing serializes connection establishment without holding mu across
	// the dial itself, so a slow handshake cannot block every other request.
	dialing sync.Mutex
	mu      sync.Mutex
	conn    *quic.Conn
}

func NewClient(cfg ClientConfig) (*Client, error) {
	if len(cfg.Token) != tokenSize {
		return nil, fmt.Errorf("baseline token must be %d bytes", tokenSize)
	}
	if cfg.Logger == nil {
		cfg.Logger = slog.Default()
	}
	if cfg.DialTimeout <= 0 {
		cfg.DialTimeout = defaultDialTimeout
	}
	return &Client{cfg: cfg}, nil
}

func (c *Client) ServeListener(ctx context.Context, listener net.Listener) error {
	go func() {
		<-ctx.Done()
		_ = listener.Close()
	}()
	for {
		conn, err := listener.Accept()
		if err != nil {
			if ctx.Err() != nil {
				return nil
			}
			return err
		}
		go c.handle(ctx, conn)
	}
}

func (c *Client) Close() {
	c.mu.Lock()
	conn := c.conn
	c.conn = nil
	c.mu.Unlock()
	if conn != nil {
		_ = conn.CloseWithError(0, "baseline client closed")
	}
}

func (c *Client) handle(ctx context.Context, inner net.Conn) {
	defer inner.Close()
	request, err := socks5.ReadRequest(inner, nil)
	if err != nil {
		return
	}
	if request.Command != socks5.CommandConnect {
		_ = socks5.WriteReply(inner, socks5.ReplyCommandNotSupported, nil)
		return
	}
	stream, err := c.openStream(ctx, request.Destination)
	if err != nil {
		_ = socks5.WriteReply(inner, socks5.ReplyGeneralFailure, nil)
		return
	}
	defer stream.Close()
	if err := socks5.WriteReply(inner, socks5.ReplySucceeded, inner.LocalAddr()); err != nil {
		return
	}
	relay(stream, inner)
}

func (c *Client) openStream(ctx context.Context, destination string) (*quic.Stream, error) {
	if len(destination) > maxAddrLength {
		return nil, errors.New("destination address is too long")
	}
	conn, authenticate, err := c.connection(ctx)
	if err != nil {
		return nil, err
	}
	openCtx, cancel := context.WithTimeout(ctx, c.cfg.DialTimeout)
	defer cancel()
	stream, err := conn.OpenStreamSync(openCtx)
	if err != nil {
		// One retry on a dead pooled connection matches TUIC's reconnect
		// behavior and keeps a transient path failure from failing the trial.
		c.discard(conn)
		conn, authenticate, err = c.connection(ctx)
		if err != nil {
			return nil, err
		}
		if stream, err = conn.OpenStreamSync(openCtx); err != nil {
			return nil, err
		}
	}
	header := make([]byte, 0, tokenSize+2+len(destination))
	if authenticate {
		header = append(header, c.cfg.Token...)
	}
	header = binary.BigEndian.AppendUint16(header, uint16(len(destination)))
	header = append(header, destination...)
	if _, err := stream.Write(header); err != nil {
		_ = stream.Close()
		return nil, err
	}
	return stream, nil
}

func (c *Client) connection(ctx context.Context) (*quic.Conn, bool, error) {
	if conn := c.current(); conn != nil {
		return conn, false, nil
	}
	c.dialing.Lock()
	defer c.dialing.Unlock()
	// Another request may have established the connection while this one
	// waited for the dial lock.
	if conn := c.current(); conn != nil {
		return conn, false, nil
	}
	tlsCfg := &tls.Config{
		MinVersion: tls.VersionTLS13, ServerName: c.cfg.ServerName,
		NextProtos: []string{ALPN}, RootCAs: c.cfg.RootCAs,
	}
	dialCtx, cancel := context.WithTimeout(ctx, c.cfg.DialTimeout)
	defer cancel()
	conn, err := c.dial(dialCtx, tlsCfg)
	if err != nil {
		return nil, false, err
	}
	applyCongestion(conn, c.cfg.Congestion, c.cfg.BrutalBytesPerSec)
	c.mu.Lock()
	c.conn = conn
	c.mu.Unlock()
	return conn, true, nil
}

func (c *Client) current() *quic.Conn {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.conn != nil && c.conn.Context().Err() == nil {
		return c.conn
	}
	return nil
}

func (c *Client) dial(ctx context.Context, tlsCfg *tls.Config) (*quic.Conn, error) {
	if c.cfg.LocalAddress == "" {
		return quic.DialAddr(ctx, c.cfg.RemoteAddr, tlsCfg, c.cfg.Transport.quicConfig())
	}
	local, err := net.ResolveUDPAddr("udp", net.JoinHostPort(c.cfg.LocalAddress, "0"))
	if err != nil {
		return nil, fmt.Errorf("resolve local address: %w", err)
	}
	remote, err := net.ResolveUDPAddr("udp", c.cfg.RemoteAddr)
	if err != nil {
		return nil, fmt.Errorf("resolve remote address: %w", err)
	}
	packet, err := net.ListenUDP("udp", local)
	if err != nil {
		return nil, fmt.Errorf("bind local address: %w", err)
	}
	conn, err := quic.Dial(ctx, packet, remote, tlsCfg, c.cfg.Transport.quicConfig())
	if err != nil {
		_ = packet.Close()
		return nil, err
	}
	return conn, nil
}

func (c *Client) discard(conn *quic.Conn) {
	c.mu.Lock()
	if c.conn == conn {
		c.conn = nil
	}
	c.mu.Unlock()
	_ = conn.CloseWithError(0, "baseline connection replaced")
}

// ----------------------------------------------------------------- relay ---

type closeWriter interface{ CloseWrite() error }

// relay copies bytes in both directions and propagates half-close, which is
// what TUIC does with a QUIC stream's independent directions.
func relay(stream *quic.Stream, inner net.Conn) {
	var wg sync.WaitGroup
	wg.Add(2)
	go func() {
		defer wg.Done()
		_, _ = io.Copy(stream, inner)
		_ = stream.Close()
	}()
	go func() {
		defer wg.Done()
		_, _ = io.Copy(inner, stream)
		if cw, ok := inner.(closeWriter); ok {
			_ = cw.CloseWrite()
		}
	}()
	wg.Wait()
}
