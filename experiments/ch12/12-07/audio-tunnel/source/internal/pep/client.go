package pep

import (
	"context"
	"crypto/x509"
	"encoding/binary"
	"errors"
	"fmt"
	"log/slog"
	"net"
	"sync"
	"sync/atomic"
	"syscall"
	"time"

	"github.com/apernet/quic-go"
	"github.com/bojieli/queqiao/internal/classifier"
	wancongestion "github.com/bojieli/queqiao/internal/congestion"
	"github.com/bojieli/queqiao/internal/flowmeta"
	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/limiter"
	"github.com/bojieli/queqiao/internal/memlimit"
	"github.com/bojieli/queqiao/internal/metrics"
	"github.com/bojieli/queqiao/internal/portmux"
	"github.com/bojieli/queqiao/internal/profile"
	"github.com/bojieli/queqiao/internal/protocol"
	"github.com/bojieli/queqiao/internal/session"
	"github.com/bojieli/queqiao/internal/socks5"
)

// A peer that accepts a replacement stream and immediately closes it must not
// cause an endless replacement storm while the application waits for a final
// FIN. Recovery is deliberately finite; the logical flow then fails closed
// and the caller can retry.
const (
	maxTCPFallbackLanes      = 16
	defaultClientMaxSessions = 2048
	defaultMaxPendingOpens   = 256
	flowOpenRetryBaseDelay   = 500 * time.Millisecond

	maxLaneRecoveryAttempts = 8
	laneRecoveryResetAfter  = 5 * time.Minute
	// laneJoinCapacityTCPCommit is how many consecutive capacity answers a
	// recovery path takes before it stops believing the answer is transient.
	// One or two in a row are the ordinary losers of a rescue race; at three
	// the likelier reading is an admission slot wedged on the peer, and the
	// AUTO TCP commit -- deliberately suppressed for a fresh answer, since a
	// QUIC sibling may already hold the lane -- becomes the flow's escape.
	laneJoinCapacityTCPCommit = 3
	// A rejected speculative lane must not be reopened on every scheduler tick.
	// The backoff is intentionally shorter than a normal bulk request timeout,
	// but long enough to collect a fresh throughput/RTT sample on the surviving
	// control lane before trying another independent QUIC path.
	minLaneProbeBackoff  = 10 * time.Second
	maxLaneProbeBackoff  = 60 * time.Second
	maxLaneProbeAttempts = 4
	// laneDecisionInterval spaces the lane probe's samples. It bounds how fast
	// the search can converge: a baseline costs two decisions and judging a
	// probed lane costs three more, so a flow reaches its second bulk lane
	// about five intervals after it is classified as bulk. Shorter intervals
	// make each goodput sample noisier -- at a 200ms RTT, 500ms is roughly two
	// round trips of evidence -- and the probe's bias against striping is what
	// keeps that noise from producing false positives.
	laneDecisionInterval = 500 * time.Millisecond
	// Start the authenticated join slightly before the classifier's final bulk
	// transition. The lane is attached but carries no NEW/interactive DATA, so
	// this only overlaps its lossy QUIC handshake with the tail of classification.
	bulkLanePrewarmBytes = 64 * 1024
	bulkLanePrewarmAge   = 500 * time.Millisecond
	bulkLaneAsymmetry    = 8
)

type ClientConfig struct {
	ListenAddr   string
	RemoteAddr   string
	LocalAddress string
	// SocketControl is invoked after an outer socket is created and before it
	// is bound or connected. Mobile VPN clients use it to exempt Queqiao's own
	// TCP and UDP sockets from the virtual interface. A failure aborts the dial;
	// silently continuing would route the tunnel through itself.
	SocketControl func(network, address string, conn syscall.RawConn) error
	// SOCKSAuth optionally requires RFC 1929 username/password on the local
	// SOCKS5 listener. It is nil for the loopback-private listener used by the
	// desktop agent and the mobile packet tunnel, and set when the listener is
	// reachable by other applications on the same host, as in Android export
	// mode where loopback is shared across every installed app.
	SOCKSAuth   *socks5.Credentials
	Credentials identity.ClientCredentials
	// Profile names the deployment this client is running in, and carries the
	// policy that differs between deployments. The zero value is the supported
	// access-link profile, so a caller that does not choose gets the behaviour
	// the published measurements describe.
	Profile profile.Profile
	// FlowMetadataSocket is a local capture agent's lookup socket. Empty
	// disables the lookup and is the default: a deployment without an agent
	// behaves exactly as it did before this existed.
	FlowMetadataSocket string
	// FlowMetadataTimeout bounds one lookup. It runs on the accept path, so an
	// agent that has wedged costs a flow a millisecond rather than its
	// handshake.
	FlowMetadataTimeout time.Duration
	ChunkSize           int
	DialTimeout         time.Duration
	HandshakeTimeout    time.Duration
	FlowIdleTimeout     time.Duration
	FlowMaxLifetime     time.Duration
	MaxSessions         int
	// SessionLimit optionally shares admission across several clients in one
	// process. Nil gives this client its own MaxSessions-sized limit.
	SessionLimit *SessionLimit
	// Budget optionally shares the aggregate byte budget across several
	// clients in one process. Nil derives a private budget from
	// AggregateBytesPerSec, which paces this client alone; a multi-provider
	// process must share one budget or it offers the configured total once
	// per provider.
	Budget *limiter.Budget
	// MaxPendingOpens bounds flows that are still establishing their remote
	// transport. Keeping this separate from MaxSessions prevents a failed
	// endpoint and its retries from occupying every healthy-flow slot.
	MaxPendingOpens int
	Transport       TransportKind
	// TCPFallbackLanes is the number of independent TLS/TCP connections used
	// for a classified bulk flow. Values above one never affect QUIC.
	TCPFallbackLanes int
	// EnableQUICPool keeps one persistent QUIC connection for initial and
	// control streams, and is what makes opening a flow cost nothing.
	//
	// Without it every flow dials its own connection, and so pays a handshake
	// and a congestion ramp from the initial window before it carries a byte.
	// Measured live on a 38% erasure path, a small flow cost 0.64 s, 1.11 s and
	// 14.77 s on three attempts unpooled -- the last being a handshake that
	// lost packets -- against 0.302, 0.292 and 0.300 pooled, which is one round
	// trip and nothing else.
	//
	// It was opt-in because bulk on a pooled connection to a Reno peer measured
	// worse than an independent lane. That reason has gone: the peer runs the
	// erasure controller, the scheduler already moves classified bulk off the
	// pooled connection onto lanes of its own, and bulk measured the same
	// either way (0.85-1.15 MB/s pooled against 0.86-1.02 unpooled).
	EnableQUICPool bool
	// WaitForOpenAcknowledgement makes a flow wait for OPEN_OK before telling
	// the application its connection is up. It is off by default, so a flow on
	// a connection that is already established costs no round trips at all.
	//
	// Waiting costs exactly one round trip per flow, and an application opens
	// a flow far more often than it opens a connection. Measured across an
	// emulated 300 ms path, a first flow costs 922 ms -- a QUIC handshake, an
	// authentication exchange and an open -- and every flow after it cost 306
	// ms, which is one round trip of pure waiting on a pool that was already
	// up. That is the cost this removes: request bytes now leave with the open
	// rather than a round trip behind it.
	//
	// What is given up is the ability to answer SOCKS with a precise failure.
	// The flow reader still validates the eventual OPEN_OK and propagates a
	// typed RESET, so an unreachable destination becomes a connection that
	// opens and then closes rather than one that never opens. Set this when a
	// caller needs the distinction more than it needs the round trip.
	WaitForOpenAcknowledgement bool
	// UDPOnStream keeps SOCKS UDP packets on the lane's control stream even
	// where the QUIC connection negotiated datagrams. It is the control for
	// measuring the datagram substrate against the one it replaced, and both
	// endpoints must be set the same way for the comparison to mean anything.
	UDPOnStream                   bool
	Congestion                    CongestionControlKind
	BrutalBytesPerSec             uint64
	AdaptiveMinBytesSec           uint64
	AdaptiveMaxBytesSec           uint64
	AggregateBytesPerSec          uint64
	InteractiveReserveBytesPerSec uint64
	// StreamReceiveWindow and ConnectionReceiveWindow override the QUIC
	// receive windows. Zero selects the defaults, which match TUIC.
	StreamReceiveWindow     uint64
	ConnectionReceiveWindow uint64
	// Maximum windows disable quic-go's otherwise large receive-window growth.
	// Zero keeps the high-throughput defaults. Resource-constrained clients set
	// initial and maximum to the same bounded values.
	MaxStreamReceiveWindow     uint64
	MaxConnectionReceiveWindow uint64
	MaxIncomingStreams         int64
	// MemoryLimits is required by resource-constrained clients. Nil retains
	// the throughput-oriented defaults used by servers and desktop clients.
	MemoryLimits *MemoryLimits
	Metrics      *metrics.Registry
	// FallbackDelay is when AUTO starts connecting its warm-standby TCP
	// candidate. It is not a deadline for QUIC and not a transport-selection
	// race.
	FallbackDelay time.Duration
	// FallbackGrace is how long a ready TCP standby waits for QUIC. Expiry may
	// serve the current flow over TCP, but it is neutral UDP evidence. With a
	// pool, the QUIC attempt continues in the background so later flows can
	// return to the preferred transport.
	FallbackGrace       time.Duration
	UDPFailureThreshold int
	UDPCooldown         time.Duration
	// HopPortCount enables reactive UDP port hopping to evade per-port GFW
	// blocking. 0 and 1 both mean disabled. Values ≥ 2 cause the client to
	// maintain a pool of that many ports derived from the provider ID and hop
	// reactively when sustained zero-receive loss is detected.
	HopPortCount int
	Logger       *slog.Logger
}

type Client struct {
	// flowMeta asks a local capture agent what produced a flow. Nil when no
	// agent is configured, which is the default.
	flowMeta      *flowmeta.Lookup
	cfg           ClientConfig
	udpHealth     *udpHealth
	budget        *limiter.Budget
	sessionLimit  *SessionLimit
	sendMemory    *memlimit.Budget
	receiveMemory *memlimit.Budget
	memoryLimits  flowMemoryLimits
	metrics       *metrics.Registry

	credentialsMu sync.RWMutex
	credentials   identity.ClientCredentials

	// One QUIC generation can carry many independent PEP streams. A generation
	// is replaced as a unit: all callers wait on the same in-flight dial, so a
	// dead shared connection causes one handshake rather than one handshake per
	// affected flow. The dial has a client lifetime of its own and is not
	// cancelled merely because the first flow waiting for it goes away.
	quicMu         sync.Mutex
	quicGeneration *controlQUICGeneration
	quicDial       *controlQUICDial
	quicEpoch      uint64
	// transientUDPLogNS rate-limits an otherwise synchronized burst of local
	// route errors while still counting every suppressed send in metrics.
	transientUDPLogNS atomic.Int64
	// hopWalk is the client-wide hop port selection state, built lazily on
	// the first hop-enabled dial so all dials share one walk.
	hopWalkOnce sync.Once
	hopWalk     *portmux.HopWalk
	// openFlowForTest stands in for one flow-open attempt, so the retry policy
	// can be tested without a network that loses things on demand.
	openFlowForTest func() (*openedFlow, error)
	// flowOpenRetryDelayForTest makes retry timing deterministic without
	// weakening the production jitter shared by concurrent callers.
	flowOpenRetryDelayForTest func(failedAttempt int) time.Duration
	// dialPipelinedFlowForTest isolates the cold-flow transport race from the
	// network in state-machine tests.
	dialPipelinedFlowForTest func(context.Context, TransportKind, []byte) (*openedFlow, error)
	// dialAuthenticatedLaneForTest isolates the pooled transport race. The
	// production path still goes through dialAuthenticatedLane; tests can make
	// TCP ready before QUIC without relying on scheduler timing or live loss.
	dialAuthenticatedLaneForTest func(context.Context, TransportKind) (*authenticatedLane, error)
	// disableStallWatchdogForTest keeps the flow stall watchdog off, so tests
	// that pin exact dial counts see only the recovery they injected, not
	// rescue rounds the watchdog starts on a slow runner.
	disableStallWatchdogForTest bool

	// quicPoolActive counts flows currently sharing the pooled control
	// connection. A bulk flow only needs to move off it when another flow
	// would otherwise queue behind its congestion window.
	quicPoolActive atomic.Int64
	// bulkMu protects a bounded set of pre-authenticated secondary QUIC
	// connections used only for fast lane joins. Keeping them separate from
	// the control pool preserves the control lane's congestion state while
	// avoiding a fresh QUIC handshake at the bulk-promotion boundary.
	//
	// Each connection carries at most one lane at a time. Multiplexing several
	// lanes of one flow onto a single connection would give them one 4-tuple
	// and one congestion controller, which is what a single TUIC connection
	// already provides: measured on a path that polices per source address,
	// striping over a shared connection produced no gain at all. A connection
	// is retained after its lane is released so a later flow still skips the
	// handshake.
	bulkMu    sync.Mutex
	bulkConns []*bulkConn

	// pendingOpens admits only bounded remote setup work. It is deliberately
	// non-blocking: callers beyond the bound are rejected promptly, release
	// their total-session slot, and leave capacity for established flows.
	pendingOpens chan struct{}
}

// SessionLimit bounds concurrent local SOCKS sessions across one or more
// clients. Admission is deliberately non-blocking so an overloaded listener
// can reject promptly instead of accumulating unauthenticated local sockets.
//
// A limit may hold a private reservation as well as a share of a pool common
// to every client. The reservation is what keeps a quiet provider able to
// admit new flows while a busy sibling holds most of the common pool: a
// failover target which cannot accept a session is not a failover target.
type SessionLimit struct {
	reserved chan struct{}
	shared   chan struct{}
}

// sessionSlot returns one admitted session to the pool it came from.
type sessionSlot struct {
	pool chan struct{}
}

func (s sessionSlot) release() {
	if s.pool != nil {
		<-s.pool
	}
}

func NewSessionLimit(max int) (*SessionLimit, error) {
	if max < 1 || max > maxConfiguredSessions {
		return nil, fmt.Errorf("maximum sessions must be between 1 and %d", maxConfiguredSessions)
	}
	return &SessionLimit{shared: make(chan struct{}, max)}, nil
}

// NewSharedSessionLimits divides max across clients so their combined
// admission never exceeds max while each client keeps a private reservation.
// Half the budget is reserved in equal shares and half stays common, so an
// idle provider can still burst into capacity its siblings are not using. When
// max is too small to reserve a slot per client the whole budget stays common.
func NewSharedSessionLimits(max, clients int) ([]*SessionLimit, error) {
	if clients < 1 {
		return nil, errors.New("shared session limits require at least one client")
	}
	if max < 1 || max > maxConfiguredSessions {
		return nil, fmt.Errorf("maximum sessions must be between 1 and %d", maxConfiguredSessions)
	}
	reserve := max / (2 * clients)
	shared := make(chan struct{}, max-reserve*clients)
	limits := make([]*SessionLimit, clients)
	for i := range limits {
		limits[i] = &SessionLimit{shared: shared}
		if reserve > 0 {
			limits[i].reserved = make(chan struct{}, reserve)
		}
	}
	return limits, nil
}

// Reserved reports the slots this limit holds for its own client alone.
func (l *SessionLimit) Reserved() int {
	if l == nil {
		return 0
	}
	return cap(l.reserved)
}

// acquire takes the private reservation first so a client's own capacity is
// never spent on a sibling. A nil limit admits: callers which never configured
// one are unlimited rather than dead.
func (l *SessionLimit) acquire() (sessionSlot, bool) {
	if l == nil {
		return sessionSlot{}, true
	}
	if l.reserved != nil {
		select {
		case l.reserved <- struct{}{}:
			return sessionSlot{pool: l.reserved}, true
		default:
		}
	}
	select {
	case l.shared <- struct{}{}:
		return sessionSlot{pool: l.shared}, true
	default:
		return sessionSlot{}, false
	}
}

// bulkConn is one pre-authenticated secondary QUIC connection reserved for
// bulk lane joins.
type bulkConn struct {
	conn       *quic.Conn
	packet     net.PacketConn
	controller wancongestion.TelemetryProvider
	busy       bool
	idleTimer  *time.Timer
}

// controlQUICGeneration owns exactly one shared connection and the packet
// socket beneath it. Keeping ownership in one object makes generation checks
// precise: a late failure from an old stream can retire its own generation but
// can never close the healthy generation which replaced it.
type controlQUICGeneration struct {
	id         uint64
	conn       *quic.Conn
	packet     net.PacketConn
	controller wancongestion.TelemetryProvider
	closeOnce  sync.Once
}

func (g *controlQUICGeneration) close(reason string) {
	if g == nil {
		return
	}
	g.closeOnce.Do(func() {
		if g.conn != nil {
			_ = g.conn.CloseWithError(0, reason)
		}
		if g.packet != nil {
			_ = g.packet.Close()
		}
	})
}

// controlQUICDial is the singleflight state for one prospective generation.
// done publishes generation and err to every waiter.
type controlQUICDial struct {
	epoch      uint64
	done       chan struct{}
	cancel     context.CancelFunc
	generation *controlQUICGeneration
	err        error
	superseded bool
}

func (b *bulkConn) close(reason string) {
	if b.idleTimer != nil {
		b.idleTimer.Stop()
		b.idleTimer = nil
	}
	if b.conn != nil {
		_ = b.conn.CloseWithError(0, reason)
	}
	if b.packet != nil {
		_ = b.packet.Close()
	}
}

const bulkPoolIdleTimeout = 30 * time.Second
const defaultFallbackGrace = 2 * time.Second

func NewClient(cfg ClientConfig) (*Client, error) {
	if cfg.ListenAddr == "" || cfg.RemoteAddr == "" {
		return nil, errors.New("client listen and remote addresses are required")
	}
	if err := validateLocalAddressSpec(cfg.LocalAddress); err != nil {
		return nil, err
	}
	if err := cfg.SOCKSAuth.Validate(); err != nil {
		return nil, err
	}
	if err := cfg.Credentials.Validate(time.Now()); err != nil {
		return nil, fmt.Errorf("client identity: %w", err)
	}
	// ChunkSize is a sending policy: how much of a byte stream one DATA frame
	// carries. It is not a receive limit -- protocol.MaxPayload is, and it is
	// fixed by the wire version -- so an out-of-range value is corrected to the
	// default rather than allowed to produce frames the peer must reject.
	if cfg.ChunkSize <= 0 || cfg.ChunkSize > protocol.MaxPayload {
		cfg.ChunkSize = defaultChunkSize
	}
	if cfg.DialTimeout <= 0 {
		cfg.DialTimeout = 10 * time.Second
	}
	if cfg.HandshakeTimeout <= 0 {
		// Long enough for the first connection to an erasing path. The QUIC
		// handshake alone takes about five seconds at 42% loss -- its packets
		// are large, they are lost as often as anything else, and the probe
		// timeouts that recover them double -- and this bound has to cover
		// that and the session's own exchange after it. At ten seconds the
		// first connection was a coin flip, and it is the one connection every
		// flow afterwards is built on.
		cfg.HandshakeTimeout = 30 * time.Second
	}
	if cfg.FlowIdleTimeout <= 0 {
		cfg.FlowIdleTimeout = defaultFlowIdleTimeout
	}
	if cfg.FlowMaxLifetime <= 0 {
		cfg.FlowMaxLifetime = defaultFlowMaxLifetime
	}
	if cfg.FlowIdleTimeout > cfg.FlowMaxLifetime {
		return nil, errors.New("flow idle timeout cannot exceed maximum lifetime")
	}
	if cfg.MaxSessions <= 0 {
		cfg.MaxSessions = defaultClientMaxSessions
	}
	if cfg.MaxSessions > maxConfiguredSessions {
		return nil, fmt.Errorf("maximum sessions must not exceed %d", maxConfiguredSessions)
	}
	if cfg.SessionLimit == nil {
		limit, err := NewSessionLimit(cfg.MaxSessions)
		if err != nil {
			return nil, err
		}
		cfg.SessionLimit = limit
	} else if cfg.SessionLimit.shared == nil {
		return nil, errors.New("shared session limit is not initialized")
	}
	if cfg.MaxPendingOpens <= 0 {
		cfg.MaxPendingOpens = defaultMaxPendingOpens
	}
	if cfg.MaxPendingOpens > maxConfiguredSessions {
		return nil, fmt.Errorf("maximum pending opens must not exceed %d", maxConfiguredSessions)
	}
	if cfg.Logger == nil {
		cfg.Logger = slog.Default()
	}
	if cfg.Metrics == nil {
		cfg.Metrics = metrics.New()
	}
	if cfg.Transport == "" {
		cfg.Transport = TransportAuto
	}
	if cfg.Transport != TransportAuto && cfg.Transport != TransportQUIC && cfg.Transport != TransportTCP {
		return nil, fmt.Errorf("unsupported client transport %q", cfg.Transport)
	}
	if cfg.TCPFallbackLanes == 0 {
		cfg.TCPFallbackLanes = 1
	}
	if cfg.TCPFallbackLanes < 1 || cfg.TCPFallbackLanes > maxTCPFallbackLanes {
		return nil, fmt.Errorf("TCP fallback lanes must be between 1 and %d", maxTCPFallbackLanes)
	}
	if cfg.Congestion == "" {
		cfg.Congestion = defaultCongestion()
	}
	if cfg.Congestion != CongestionReno && cfg.Congestion != CongestionBBR && cfg.Congestion != CongestionBBRTUIC && cfg.Congestion != CongestionErasure && cfg.Congestion != CongestionAdaptive && cfg.Congestion != CongestionBrutal {
		return nil, fmt.Errorf("unsupported QUIC congestion controller %q", cfg.Congestion)
	}
	if cfg.Congestion == CongestionBrutal && cfg.BrutalBytesPerSec == 0 {
		return nil, errors.New("brutal congestion requires a positive per-lane byte rate")
	}
	if cfg.AdaptiveMinBytesSec == 0 {
		cfg.AdaptiveMinBytesSec = defaultAdaptiveMinBytesPerSec
	}
	if cfg.AdaptiveMaxBytesSec == 0 {
		cfg.AdaptiveMaxBytesSec = defaultAdaptiveMaxBytesPerSec
	}
	if cfg.AdaptiveMaxBytesSec < cfg.AdaptiveMinBytesSec {
		return nil, errors.New("adaptive maximum byte rate cannot be below its minimum")
	}
	if cfg.AggregateBytesPerSec == 0 && cfg.InteractiveReserveBytesPerSec != 0 {
		return nil, errors.New("interactive reserve requires an aggregate byte budget")
	}
	// The reserve is withheld from bulk traffic, so a reserve equal to the
	// whole budget leaves bulk not merely slow but unable to send a byte: the
	// budget has no bulk capacity to admit against and refuses every bulk
	// request outright. Require the reserve to leave something behind.
	if cfg.AggregateBytesPerSec != 0 && cfg.InteractiveReserveBytesPerSec >= cfg.AggregateBytesPerSec {
		return nil, errors.New("interactive reserve must leave bulk capacity below the aggregate byte budget")
	}
	// A caller may supply one budget shared by several clients, so that a
	// multi-provider process paces to the configured total instead of offering
	// that total once per provider. The chunk cap below is then measured
	// against the shared budget, which is the one these flows will admit
	// against.
	budget := cfg.Budget
	if budget == nil {
		budget = NewAggregateBudget(cfg.AggregateBytesPerSec, cfg.InteractiveReserveBytesPerSec)
		cfg.Budget = budget
	}
	// Before resolveMemoryLimits: the per-flow send budget is checked against
	// the chunk size, and the chunk that has to fit there is the corrected one.
	cfg.ChunkSize = chunkSizeForBudget(cfg.ChunkSize, budget)
	if cfg.FallbackDelay <= 0 {
		cfg.FallbackDelay = 300 * time.Millisecond
	}
	if cfg.FallbackGrace <= 0 {
		cfg.FallbackGrace = defaultFallbackGrace
	}
	if err := (flowWindows{
		stream: cfg.StreamReceiveWindow, connection: cfg.ConnectionReceiveWindow,
		maxStream: cfg.MaxStreamReceiveWindow, maxConnection: cfg.MaxConnectionReceiveWindow,
		maxStreams: cfg.MaxIncomingStreams,
	}).validate(); err != nil {
		return nil, err
	}
	memoryLimits, sendMemory, receiveMemory, err := resolveMemoryLimits(cfg.MemoryLimits, cfg.ChunkSize)
	if err != nil {
		return nil, err
	}
	// A misspelled class name fails here rather than matching nothing at
	// runtime, where it would be indistinguishable from a rule whose workload
	// never appeared.
	if err := cfg.Profile.ValidateHints(); err != nil {
		return nil, fmt.Errorf("client profile: %w", err)
	}
	return &Client{
		flowMeta: flowmeta.New(cfg.FlowMetadataSocket, cfg.FlowMetadataTimeout),
		cfg:      cfg, udpHealth: newUDPHealth(cfg.UDPFailureThreshold, cfg.UDPCooldown),
		credentials: cfg.Credentials, budget: budget,
		metrics: cfg.Metrics, sessionLimit: cfg.SessionLimit, pendingOpens: make(chan struct{}, cfg.MaxPendingOpens),
		sendMemory: sendMemory, receiveMemory: receiveMemory, memoryLimits: memoryLimits,
	}, nil
}

func (c *Client) MemoryStats() MemoryStats {
	return MemoryStats{Send: c.sendMemory.Snapshot(), Receive: c.receiveMemory.Snapshot()}
}

func (c *Client) currentCredentials() identity.ClientCredentials {
	c.credentialsMu.RLock()
	defer c.credentialsMu.RUnlock()
	return c.credentials
}

// UpdateCredentials installs a renewed certificate for future handshakes.
// Trust domain, account, device, and public key are immutable: changing any of
// them requires importing a new profile and constructing a new client.
func (c *Client) UpdateCredentials(updated identity.ClientCredentials) error {
	if err := updated.Validate(time.Now()); err != nil {
		return fmt.Errorf("updated client identity: %w", err)
	}
	c.credentialsMu.Lock()
	defer c.credentialsMu.Unlock()
	current := c.credentials
	if updated.ProviderID != current.ProviderID || updated.GatewayID != current.GatewayID || updated.RootPin != current.RootPin {
		return errors.New("updated client identity changes the provider or gateway")
	}
	currentLeaf, err := x509.ParseCertificate(current.Certificate.Certificate[0])
	if err != nil {
		return fmt.Errorf("parse current device identity: %w", err)
	}
	updatedLeaf, err := x509.ParseCertificate(updated.Certificate.Certificate[0])
	if err != nil {
		return fmt.Errorf("parse updated device identity: %w", err)
	}
	currentPrincipal, err := identity.PrincipalFromCertificate(currentLeaf)
	if err != nil {
		return err
	}
	updatedPrincipal, err := identity.PrincipalFromCertificate(updatedLeaf)
	if err != nil {
		return err
	}
	if currentPrincipal.ProviderID != updatedPrincipal.ProviderID ||
		currentPrincipal.AccountID != updatedPrincipal.AccountID ||
		currentPrincipal.DeviceID != updatedPrincipal.DeviceID ||
		!currentPrincipal.PublicKey.Equal(updatedPrincipal.PublicKey) {
		return errors.New("updated client identity changes the device principal or key")
	}
	c.credentials = updated
	return nil
}

func (c *Client) fallbackGrace() time.Duration {
	if c.cfg.FallbackGrace <= 0 {
		return defaultFallbackGrace
	}
	return c.cfg.FallbackGrace
}

func (c *Client) windows() flowWindows {
	return flowWindows{
		stream: c.cfg.StreamReceiveWindow, connection: c.cfg.ConnectionReceiveWindow,
		maxStream: c.cfg.MaxStreamReceiveWindow, maxConnection: c.cfg.MaxConnectionReceiveWindow,
		maxStreams: c.cfg.MaxIncomingStreams, codedQueue: c.memoryLimits.eventQueue,
	}
}

func (c *Client) Serve(ctx context.Context) error {
	listener, err := ListenLocal(ctx, c.cfg.ListenAddr)
	if err != nil {
		return fmt.Errorf("listen on local SOCKS5 address: %w", err)
	}
	return c.ServeListener(ctx, listener)
}

// ListenLocal binds a local SOCKS5 listener. Serve and any caller which binds
// ahead of ServeListener share it so both get identical socket options.
func ListenLocal(ctx context.Context, address string) (net.Listener, error) {
	lc := net.ListenConfig{KeepAlive: 30 * time.Second}
	return lc.Listen(ctx, "tcp", address)
}

// NewAggregateBudget builds one byte budget several clients can share, so a
// process running many clients paces to the configured total instead of
// offering that total once per client. A zero rate means unpaced.
func NewAggregateBudget(totalBytesPerSec, reserveBytesPerSec uint64) *limiter.Budget {
	return limiter.New(limiter.Config{
		TotalBytesPerSec: totalBytesPerSec, ReserveBytesPerSec: reserveBytesPerSec,
	})
}

// Metrics exposes aggregate counters for an optional operator endpoint.
func (c *Client) Metrics() *metrics.Registry { return c.metrics }

func (c *Client) admitPendingOpen() bool {
	if c.pendingOpens == nil {
		return true
	}
	select {
	case c.pendingOpens <- struct{}{}:
		return true
	default:
		return false
	}
}

func (c *Client) releasePendingOpen() {
	if c.pendingOpens != nil {
		<-c.pendingOpens
	}
}

// ServeListener is primarily useful for tests and service managers which
// provide an already-bound socket. The listener is closed when the context is
// cancelled or the method returns.
func (c *Client) ServeListener(ctx context.Context, listener net.Listener) error {
	defer listener.Close()
	defer c.closeQUICPool()

	// Readiness includes the first bounded path measurement. Starting it in a
	// background watcher made the first accepted flow race the prewarm and
	// usually become the traffic which discovered the path after all. Capture
	// the route first so the watcher can still detect a change which happens
	// during this measurement.
	uplink := c.currentUplink()
	c.prewarmPath(ctx)
	// A route can change during a long lossy handshake. Reconcile once before
	// publishing readiness; otherwise the listener accepts flows for up to one
	// polling interval using the pool and path model the prewarm just measured
	// on an uplink which is already gone.
	if current := c.currentUplink(); current != "" {
		if uplink != "" && current != uplink {
			c.cfg.Logger.Info("uplink changed during path prewarm", "from", uplink, "to", current)
			c.onUplinkChanged(ctx)
		}
		uplink = current
	}
	// A later change of uplink is a change of path, and nothing else will say so.
	go c.watchUplink(ctx, uplink)

	var wg sync.WaitGroup
	go func() {
		<-ctx.Done()
		_ = listener.Close()
	}()
	c.cfg.Logger.Info("local SOCKS5 listener ready", "address", listener.Addr().String(), "remote", c.cfg.RemoteAddr)
	for {
		conn, acceptErr := listener.Accept()
		if acceptErr != nil {
			if ctx.Err() != nil || errors.Is(acceptErr, net.ErrClosed) {
				wg.Wait()
				return nil
			}
			var temporary interface{ Temporary() bool }
			if errors.As(acceptErr, &temporary) && temporary.Temporary() {
				continue
			}
			return fmt.Errorf("accept local connection: %w", acceptErr)
		}
		if slot, admitted := c.sessionLimit.acquire(); admitted {
			wg.Add(1)
			go func() {
				defer wg.Done()
				defer slot.release()
				c.handleLocal(ctx, conn)
			}()
		} else {
			// The client may still be waiting for the two-byte SOCKS greeting
			// response. A request-level reply starts with 0x05, 0x01 and is then
			// misread as "unsupported authentication method 0x01" by the mobile
			// packet engine. Send the protocol-level method rejection instead.
			_ = socks5.WriteMethodUnavailable(conn)
			_ = conn.Close()
			c.cfg.Logger.Debug("local session limit reached")
		}
	}
}

// closeQUICPool is called when the local agent stops. It is safe to call more
// than once and closes the packet socket owned by a locally-bound QUIC dial.
func (c *Client) closeQUICPool() {
	c.closeControlQUICPool("queqiao client pool reset")
	c.closeBulkQUICPool("queqiao bulk pool stopped")
}

func (c *Client) closeControlQUICPool(reason string) {
	c.quicMu.Lock()
	c.quicEpoch++
	generation, dial := c.quicGeneration, c.quicDial
	c.quicGeneration, c.quicDial = nil, nil
	c.quicMu.Unlock()
	if dial != nil {
		dial.cancel()
	}
	if generation != nil {
		generation.close(reason)
	}
}

func (c *Client) closeBulkQUICPool(reason string) {
	c.bulkMu.Lock()
	bulkConns := c.bulkConns
	c.bulkConns = nil
	c.bulkMu.Unlock()
	for _, entry := range bulkConns {
		entry.close(reason)
	}
}

func (c *Client) handleLocal(ctx context.Context, inner net.Conn) {
	defer inner.Close()
	// This deadline bounds the local exchange only: reading a SOCKS request
	// from an application on loopback, which owes nothing to the network.
	//
	// It used to stay set across the remote flow open as well, and the two
	// have nothing in common but this line. Opening a flow takes as long as
	// the path does -- across the measured 42% erasure channel it took 11
	// seconds -- so a bound chosen for a loopback read expired while the flow
	// was being established, and the client closed the application's
	// connection after both ends had opened it successfully. The application
	// saw EOF from a flow that was working.
	_ = inner.SetDeadline(time.Now().Add(c.cfg.HandshakeTimeout))
	req, err := socks5.ReadRequest(inner, c.cfg.SOCKSAuth)
	if err != nil {
		c.cfg.Logger.Debug("SOCKS5 negotiation failed", "error", err)
		return
	}
	// The request is in hand, so nothing local is outstanding. What follows is
	// the network's business and is bounded by the flow open's own machinery.
	_ = inner.SetDeadline(time.Time{})
	if req.Command == socks5.CommandUDPAssociate {
		c.handleUDPAssociate(ctx, inner)
		return
	}
	if !c.admitPendingOpen() {
		_ = socks5.WriteReply(inner, socks5.ReplyGeneralFailure, nil)
		c.cfg.Logger.Warn("local pending-open limit reached")
		return
	}
	flowOpenStarted := time.Now()
	flow, err := c.openFlowWithRetries(ctx, req.Destination)
	c.releasePendingOpen()
	if err != nil {
		_ = socks5.WriteReply(inner, socks5.ReplyHostUnreachable, nil)
		c.cfg.Logger.Warn("remote flow open failed", "error", err)
		return
	}
	c.cfg.Logger.Debug("local flow opened", "transport", flow.kind, "duration", time.Since(flowOpenStarted))
	flowSession := newMultipathFlowWithMemory(ctx, inner, flow.sessionID, flow.flowID, c.cfg.ChunkSize, protocol.FlagAckUp, protocol.FlagAckDown, c.budget, c.metrics, c.cfg.Logger, c.memoryLimits, c.sendMemory, c.receiveMemory, c.classifierConfig())
	flowSession.stallWatchdogDisabled = c.disableStallWatchdogForTest
	c.declareClass(ctx, inner, flowSession)
	flowSession.ackRanges.Store(true)
	flowSession.idleTimeout = c.cfg.FlowIdleTimeout
	flowSession.maxLifetime = c.cfg.FlowMaxLifetime
	flowSession.openAckPending = flow.openPending
	if flow.openPending {
		flowSession.requireOpenConfirmation()
	}
	flowSession.tcpStriping.Store(flow.kind == TransportTCP && c.cfg.TCPFallbackLanes > 1)
	flowSession.reserveControlLane = flow.reserveControl
	flowSession.controlLaneShared = func() bool { return c.quicPoolActive.Load() > 1 }
	if err := flowSession.addLane(&mpLane{
		id: flow.laneID, kind: flow.kind, fc: flow.fc,
		control: flow.reserveControl && flow.kind == TransportQUIC,
	}); err != nil {
		_ = flow.fc.Close()
		flowSession.closeAll()
		return
	}
	// Writing the reply is local again, so it is bounded again.
	_ = inner.SetDeadline(time.Now().Add(c.cfg.HandshakeTimeout))
	if err := socks5.WriteReply(inner, socks5.ReplySucceeded, nil); err != nil {
		flowSession.closeAll()
		return
	}
	_ = inner.SetDeadline(time.Time{})
	go c.manageLanes(ctx, flowSession, flow.sessionID, flow.flowID, flow.kind)
	c.metrics.FlowStarted()
	stats, err := flowSession.run(ctx)
	// A peer may close the last outer lane immediately after the application
	// bytes and FIN exchange complete. Both direction flags are the same
	// correctness proof used by the server tombstone path; classify a late
	// socket EOF as a completed logical flow rather than a transport failure.
	flowComplete := err == nil || (ctx.Err() == nil && flowSession.finSent.Load() && flowSession.remoteFinSeen.Load())
	c.metrics.FlowFinished(stats.BytesSent, stats.BytesRead, !flowComplete && err != nil && !errors.Is(err, context.Canceled))
	codedFrames, streamFrames := flowSession.dataSubstrates()
	substrate, hasCoded := flowSession.codedSubstrate()
	logFields := []any{"session_id", fmt.Sprintf("%x", flowSession.sessionID), "flow_id", flowSession.flowID,
		"transport", flow.kind, "bytes_up", stats.BytesSent, "bytes_down", stats.BytesRead,
		"duration", stats.Ended.Sub(stats.Started), "lane_bytes", stats.LaneBytes,
		// Where the payload went, which is what tells a flow that was coded
		// for its first second from one that was coded throughout.
		"data_coded", codedFrames, "data_stream", streamFrames,
		"coded_substrate", codedSubstrateFields(substrate, hasCoded),
		"class", classifier.Class(flowSession.class.Load())}
	logFields = append(logFields, codedSubstrateLogFields(substrate, hasCoded)...)
	logFields = append(logFields, flowSession.replacementLogFields()...)
	if !flowComplete && err != nil && !errors.Is(err, context.Canceled) {
		c.cfg.Logger.Warn("local flow ended with error", append(logFields, "error", err)...)
		return
	}
	c.cfg.Logger.Info("local flow complete", logFields...)
}

type openedFlow struct {
	fc             *frameConn
	outer          streamConn
	sessionID      [16]byte
	flowID         uint64
	laneID         uint64
	kind           TransportKind
	openPending    bool
	reserveControl bool
	tcpStriping    bool
}

type authenticatedLane struct {
	fc             *frameConn
	outer          streamConn
	sessionID      [16]byte
	kind           TransportKind
	laneID         uint64
	reserveControl bool
	tcpStriping    bool
}

func (c *Client) openFlow(ctx context.Context, destination string) (*openedFlow, error) {
	// TLS has already authenticated the device when the first application frame
	// is sent, so OPEN never waits on a second security handshake.
	if !c.cfg.EnableQUICPool {
		return c.openInitialFlow(ctx, destination)
	}
	return c.openFlowMode(ctx, destination, false)
}

// openInitialFlow establishes a dedicated mutually authenticated connection
// and sends OPEN as its first application frame. AUTO preserves the normal UDP
// preference and prepares a delayed TCP standby behind the QUIC candidate.
func (c *Client) openInitialFlow(ctx context.Context, destination string) (*openedFlow, error) {
	payload, err := session.EncodeDestination(destination)
	if err != nil {
		return nil, err
	}
	if c.cfg.Transport == TransportTCP {
		return c.dialPipelinedCandidate(ctx, TransportTCP, payload)
	}
	if c.cfg.Transport == TransportQUIC {
		return c.dialPipelinedCandidate(ctx, TransportQUIC, payload)
	}
	if c.cfg.Transport != TransportAuto {
		return nil, fmt.Errorf("unsupported transport %q", c.cfg.Transport)
	}
	if !c.udpHealth.allow(time.Now()) {
		c.metrics.Fallback()
		return c.dialPipelinedCandidate(ctx, TransportTCP, payload)
	}
	return c.racePipelinedFlow(ctx, payload)
}

func (c *Client) dialPipelinedCandidate(ctx context.Context, kind TransportKind, payload []byte) (*openedFlow, error) {
	if c.dialPipelinedFlowForTest != nil {
		return c.dialPipelinedFlowForTest(ctx, kind, payload)
	}
	return c.dialPipelinedFlow(ctx, kind, payload)
}

func (c *Client) dialPipelinedFlow(ctx context.Context, kind TransportKind, payload []byte) (*openedFlow, error) {
	sessionID, err := session.NewSessionID()
	if err != nil {
		return nil, err
	}
	flowID, err := randomFlowID()
	if err != nil {
		return nil, err
	}
	lane, err := c.dialLaneMode(ctx, kind, sessionID, 0, false)
	if err != nil {
		return nil, err
	}
	fail := func(err error) (*openedFlow, error) {
		_ = lane.fc.Close()
		return nil, err
	}
	_ = lane.outer.SetDeadline(time.Now().Add(handshakeBound(lane.outer, c.cfg.HandshakeTimeout)))
	if err := lane.fc.Write(protocol.Frame{
		Header:  protocol.Header{Version: protocol.Version, Type: protocol.TypeOpen, SessionID: sessionID, FlowID: flowID, Class: protocol.ClassNew},
		Payload: payload,
	}); err != nil {
		return fail(fmt.Errorf("send pipelined flow open: %w", err))
	}
	if !c.cfg.WaitForOpenAcknowledgement {
		_ = lane.outer.SetDeadline(time.Time{})
		return &openedFlow{
			fc: lane.fc, outer: lane.outer, sessionID: sessionID, flowID: flowID,
			laneID: lane.laneID, kind: lane.kind, openPending: true,
			tcpStriping: kind == TransportTCP && c.cfg.TCPFallbackLanes > 1,
		}, nil
	}
	openAck, err := lane.fc.Read()
	if err != nil {
		return fail(fmt.Errorf("read pipelined flow acknowledgement: %w", err))
	}
	if openAck.Header.SessionID != sessionID || openAck.Header.FlowID != flowID {
		return fail(peerResponse(errors.New("pipelined flow acknowledgement identity mismatch")))
	}
	if openAck.Header.Type == protocol.TypeReset {
		return fail(peerResponse(errDestinationUnavailable))
	}
	if openAck.Header.Type != protocol.TypeOpenOK || len(openAck.Payload) != 0 {
		return fail(peerResponse(errors.New("invalid pipelined flow acknowledgement")))
	}
	_ = lane.outer.SetDeadline(time.Time{})
	return &openedFlow{
		fc: lane.fc, outer: lane.outer, sessionID: sessionID, flowID: flowID,
		laneID: lane.laneID, kind: lane.kind,
		tcpStriping: kind == TransportTCP && c.cfg.TCPFallbackLanes > 1,
	}, nil
}

func (c *Client) racePipelinedFlow(ctx context.Context, payload []byte) (*openedFlow, error) {
	raceCtx, cancel := context.WithCancel(ctx)
	defer cancel()
	quicResult := make(chan openedFlowResult, 1)
	go func() {
		flow, err := c.dialPipelinedCandidate(raceCtx, TransportQUIC, payload)
		quicResult <- openedFlowResult{flow: flow, err: err}
	}()
	timer := time.NewTimer(c.cfg.FallbackDelay)
	defer timer.Stop()
	select {
	case result := <-quicResult:
		quicEvidence := classifyQUICPathEvidence(result.err)
		if quicEvidence == quicPathAvailable {
			// A peer response proves the QUIC path worked even when the
			// destination or protocol operation itself was refused.
			c.udpHealth.observe(quicEvidence, time.Now())
			return result.flow, result.err
		}
		if ctx.Err() != nil {
			return nil, ctx.Err()
		}
		tcpFlow, tcpErr := c.dialPipelinedCandidate(ctx, TransportTCP, payload)
		tcpEvidence := classifyQUICPathEvidence(tcpErr)
		c.observeUDPPath(differentialQUICPathEvidence(quicEvidence, tcpEvidence), result.err)
		c.metrics.Fallback()
		if tcpEvidence != quicPathAvailable {
			c.reportEndpointTransportRaceFailure(result.err, tcpErr)
		}
		return tcpFlow, tcpErr
	case <-timer.C:
	case <-ctx.Done():
		closeLateFlow(quicResult)
		return nil, ctx.Err()
	}
	tcpResult := make(chan openedFlowResult, 1)
	go func() {
		flow, err := c.dialPipelinedCandidate(raceCtx, TransportTCP, payload)
		tcpResult <- openedFlowResult{flow: flow, err: err}
	}()
	var quicErr, tcpErr error
	var tcpReady *openedFlow
	var standbyTimer *time.Timer
	var standbyC <-chan time.Time
	defer func() {
		if standbyTimer != nil {
			standbyTimer.Stop()
		}
	}()
	quicEvidence := quicPathNeutral
	for quicResult != nil || tcpResult != nil {
		select {
		case result := <-quicResult:
			quicResult = nil
			quicEvidence = classifyQUICPathEvidence(result.err)
			if quicEvidence == quicPathAvailable {
				c.udpHealth.observe(quicEvidence, time.Now())
				cancel()
				closeOpenedFlow(tcpReady)
				closeLateFlow(tcpResult)
				return result.flow, result.err
			}
			quicErr = result.err
			if tcpReady != nil {
				c.observeUDPPath(differentialQUICPathEvidence(quicEvidence, quicPathAvailable), quicErr)
				c.metrics.Fallback()
				cancel()
				return tcpReady, nil
			}
		case result := <-tcpResult:
			tcpResult = nil
			tcpEvidence := classifyQUICPathEvidence(result.err)
			if tcpEvidence == quicPathAvailable {
				// TCP is a warm standby, not an equal race winner. A
				// still-pending QUIC handshake has said nothing about UDP
				// reachability, and on the target path TCP can authenticate
				// first yet carry bulk data a thousand times more slowly.
				// Keep the ready TCP flow bounded by the QUIC dial's own
				// timeout and commit it only after QUIC explicitly fails.
				if result.err == nil && quicResult != nil {
					tcpReady = result.flow
					standbyTimer = time.NewTimer(c.fallbackGrace())
					standbyC = standbyTimer.C
					continue
				}
				c.observeUDPPath(differentialQUICPathEvidence(quicEvidence, tcpEvidence), quicErr)
				c.metrics.Fallback()
				cancel()
				closeLateFlow(quicResult)
				return result.flow, result.err
			}
			tcpErr = result.err
		case <-standbyC:
			// The preference window is an application-latency bound, not
			// evidence that UDP is blocked. This cold, unpooled flow cannot
			// reuse a late connection, so retire its QUIC candidate without
			// changing endpoint health.
			standbyC = nil
			c.metrics.Fallback()
			c.cfg.Logger.Debug("QUIC preference window elapsed; using TCP without penalizing UDP health",
				"endpoint", c.cfg.RemoteAddr, "grace", c.fallbackGrace())
			cancel()
			closeLateFlow(quicResult)
			return tcpReady, nil
		case <-ctx.Done():
			closeOpenedFlow(tcpReady)
			closeLateFlow(quicResult)
			closeLateFlow(tcpResult)
			return nil, ctx.Err()
		}
	}
	c.reportEndpointTransportRaceFailure(quicErr, tcpErr)
	return nil, fmt.Errorf("QUIC failed (%v); TCP fallback failed (%v)", quicErr, tcpErr)
}

type openedFlowResult struct {
	flow *openedFlow
	err  error
}

// observeUDPPath keeps the existing health state and makes its operational
// meaning explicit. A negative observation is only produced in AUTO after
// QUIC explicitly fails and TCP reaches the same endpoint. A merely pending
// QUIC handshake is neutral: transport setup latency is not a throughput or
// reachability verdict. TCP preserves correctness, but it is a degraded path
// on the high-RTT links this transport targets and must not be silent.
func (c *Client) observeUDPPath(evidence quicPathEvidence, quicErr error) {
	if c.udpHealth != nil {
		c.udpHealth.observe(evidence, time.Now())
	}
	if evidence != quicPathUnavailable {
		return
	}
	if c.metrics != nil {
		c.metrics.UDPPathUnavailable()
	}
	if c.cfg.Logger == nil {
		return
	}
	fields := []any{
		"endpoint", c.cfg.RemoteAddr,
		"fallback", TransportTCP,
	}
	if quicErr != nil {
		fields = append(fields, "quic_error", quicErr)
	}
	c.cfg.Logger.Warn("UDP path explicitly failed; TCP fallback is degraded", fields...)
}

const transientUDPSendLogInterval = 5 * time.Second

// hopDialConfig builds the port-hopping configuration for this client's QUIC
// dials from ClientConfig. A zero HopPortCount returns a zero hopDialConfig,
// which disables port hopping in dialQUICConnection. All dials share one
// HopWalk so port selection persists across connection attempts.
func (c *Client) hopDialConfig() hopDialConfig {
	if c.cfg.HopPortCount < 2 {
		return hopDialConfig{}
	}
	c.hopWalkOnce.Do(func() {
		c.hopWalk = portmux.NewHopWalk(c.cfg.HopPortCount)
	})
	return hopDialConfig{
		portCount:  c.cfg.HopPortCount,
		providerID: c.cfg.Credentials.ProviderID,
		walk:       c.hopWalk,
		metrics:    c.cfg.Metrics,
		logger:     c.cfg.Logger,
	}
}

func (c *Client) observeTransientUDPSendFailure(err error) {
	if c.metrics != nil {
		c.metrics.TransientUDPSendError()
	}
	if c.cfg.Logger == nil {
		return
	}
	now := time.Now()
	previous := c.transientUDPLogNS.Load()
	if previous != 0 && now.Sub(time.Unix(0, previous)) < transientUDPSendLogInterval {
		return
	}
	if !c.transientUDPLogNS.CompareAndSwap(previous, now.UnixNano()) {
		return
	}
	c.cfg.Logger.Warn("transient UDP send failure treated as packet loss",
		"endpoint", c.cfg.RemoteAddr, "error", err)
}

// reportEndpointTransportRaceFailure is the complement of observeUDPPath: TCP
// did not establish a usable control path either, so this is an endpoint-wide
// failure rather than evidence against UDP alone.
func (c *Client) reportEndpointTransportRaceFailure(quicErr, tcpErr error) {
	if c.metrics != nil {
		c.metrics.EndpointTransportRaceFailure()
	}
	if c.cfg.Logger != nil {
		c.cfg.Logger.Warn("configured endpoint failed on both transports",
			"endpoint", c.cfg.RemoteAddr,
			"quic_error", quicErr,
			"tcp_error", tcpErr,
		)
	}
}

func closeLateFlow(ch <-chan openedFlowResult) {
	if ch == nil {
		return
	}
	go func() {
		result := <-ch
		closeOpenedFlow(result.flow)
	}()
}

func closeOpenedFlow(flow *openedFlow) {
	if flow != nil && flow.fc != nil {
		_ = flow.fc.Close()
	}
}

// errDestinationUnavailable is the peer saying it could not reach the
// destination. It is the answer to the application's question, not a failure
// to ask it, so it is never retried.
var errDestinationUnavailable = errors.New("remote destination unavailable")

// flowOpenAttempts is how many times a flow open is tried before the
// application is told the destination is unreachable.
//
// On a path that erases 42% of packets an attempt is sometimes simply lost --
// a handshake packet goes missing and the probe timeouts that would recover it
// run past the bound. Reporting that as an unreachable destination is a lie
// about the destination, and the application's own retry is a fresh TCP
// connection and a fresh SOCKS negotiation for something this layer could have
// tried again itself.
const flowOpenAttempts = 3

// flowOpenRetryDelay uses equal jitter: every retry waits at least half of an
// exponentially growing window, while concurrent callers spread across the
// other half instead of forming another synchronized connection wave.
func flowOpenRetryDelay(failedAttempt int) time.Duration {
	if failedAttempt < 1 {
		failedAttempt = 1
	}
	window := flowOpenRetryBaseDelay << min(failedAttempt-1, 4)
	half := window / 2
	return half + randomDuration(half)
}

func (c *Client) waitBeforeFlowOpenRetry(ctx context.Context, failedAttempt int) error {
	delay := flowOpenRetryDelay(failedAttempt)
	if c.flowOpenRetryDelayForTest != nil {
		delay = c.flowOpenRetryDelayForTest(failedAttempt)
	}
	if delay <= 0 {
		return nil
	}
	timer := time.NewTimer(delay)
	defer timer.Stop()
	select {
	case <-timer.C:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

// openFlowWithRetries asks again when the path lost the asking.
//
// Only a transport failure is retried. A peer that answered -- with a reset,
// because the destination refused or does not exist -- has told the
// application something true, and asking again would only delay it.
func (c *Client) openFlowWithRetries(ctx context.Context, destination string) (*openedFlow, error) {
	var err error
	for attempt := 1; attempt <= flowOpenAttempts; attempt++ {
		var flow *openedFlow
		flow, err = c.openOnce(ctx, destination)
		if err == nil {
			if attempt > 1 {
				c.cfg.Logger.Debug("flow opened after a lost attempt", "attempts", attempt)
			}
			return flow, nil
		}
		if peerResponded(err) || ctx.Err() != nil {
			return nil, err
		}
		c.cfg.Logger.Debug("flow open attempt failed", "attempt", attempt, "error", err)
		if attempt < flowOpenAttempts {
			if waitErr := c.waitBeforeFlowOpenRetry(ctx, attempt); waitErr != nil {
				return nil, waitErr
			}
		}
	}
	return nil, err
}

// openOnce is one attempt, indirected so a test can stand in for the network.
func (c *Client) openOnce(ctx context.Context, destination string) (*openedFlow, error) {
	if c.openFlowForTest != nil {
		return c.openFlowForTest()
	}
	return c.openFlow(ctx, destination)
}

func (c *Client) openFlowMode(ctx context.Context, destination string, _ bool) (*openedFlow, error) {
	payload, err := session.EncodeDestination(destination)
	if err != nil {
		return nil, err
	}
	lane, err := c.chooseAuthenticatedLane(ctx)
	if err != nil {
		return nil, err
	}
	fail := func(err error) (*openedFlow, error) {
		_ = lane.fc.Close()
		return nil, err
	}
	_ = lane.outer.SetDeadline(time.Now().Add(handshakeBound(lane.outer, c.cfg.HandshakeTimeout)))
	flowID, err := randomFlowID()
	if err != nil {
		return fail(err)
	}
	openFlags := uint16(0)
	if lane.reserveControl {
		openFlags |= protocol.FlagReserveControl
	}
	if err := lane.fc.Write(protocol.Frame{
		Header:  protocol.Header{Version: protocol.Version, Type: protocol.TypeOpen, Flags: openFlags, SessionID: lane.sessionID, FlowID: flowID, Class: protocol.ClassNew},
		Payload: payload,
	}); err != nil {
		return fail(fmt.Errorf("send flow open: %w", err))
	}
	if !c.cfg.WaitForOpenAcknowledgement {
		_ = lane.outer.SetDeadline(time.Time{})
		return &openedFlow{
			fc: lane.fc, outer: lane.outer, sessionID: lane.sessionID, flowID: flowID,
			laneID: lane.laneID, kind: lane.kind, openPending: true, reserveControl: lane.reserveControl,
			tcpStriping: lane.tcpStriping,
		}, nil
	}
	response, err := lane.fc.Read()
	if err != nil {
		return fail(fmt.Errorf("read flow open acknowledgement: %w", err))
	}
	if response.Header.SessionID != lane.sessionID || response.Header.FlowID != flowID {
		return fail(peerResponse(errors.New("flow open acknowledgement identity mismatch")))
	}
	if response.Header.Type == protocol.TypeReset {
		return fail(peerResponse(errDestinationUnavailable))
	}
	if response.Header.Type != protocol.TypeOpenOK || len(response.Payload) != 0 {
		return fail(peerResponse(errors.New("invalid flow open acknowledgement")))
	}
	_ = lane.outer.SetDeadline(time.Time{})
	return &openedFlow{
		fc: lane.fc, outer: lane.outer, sessionID: lane.sessionID, flowID: flowID,
		laneID: lane.laneID, kind: lane.kind, reserveControl: lane.reserveControl,
		tcpStriping: lane.tcpStriping,
	}, nil
}

func resetCode(payload []byte) session.ResetCode {
	if len(payload) == 0 {
		return 0
	}
	return session.ResetCode(payload[0])
}

func encodeLaneID(laneID uint64) []byte {
	var payload [8]byte
	binary.BigEndian.PutUint64(payload[:], laneID)
	return payload[:]
}

func (c *Client) dialAuthenticatedLane(ctx context.Context, kind TransportKind) (*authenticatedLane, error) {
	sessionID, err := session.NewSessionID()
	if err != nil {
		return nil, err
	}
	return c.dialLane(ctx, kind, sessionID, 0)
}

func (c *Client) dialJoinLane(ctx context.Context, kind TransportKind, sessionID [16]byte, laneID uint64) (*authenticatedLane, error) {
	return c.dialLaneMode(ctx, kind, sessionID, laneID, false)
}

func (c *Client) dialLane(ctx context.Context, kind TransportKind, sessionID [16]byte, laneID uint64) (*authenticatedLane, error) {
	return c.dialLaneMode(ctx, kind, sessionID, laneID, c.cfg.EnableQUICPool)
}

// dialLaneMode uses the shared QUIC stream pool only for a flow's initial
// control stream. Additional lanes are independent QUIC connections: they
// provide true bulk capacity and independent loss paths, while the pooled
// control stream remains available for short/interactive traffic.
func (c *Client) dialLaneMode(ctx context.Context, kind TransportKind, sessionID [16]byte, laneID uint64, pooled bool) (*authenticatedLane, error) {
	dialStarted := time.Now()
	var outer streamConn
	var err error
	reserveControl := false
	switch kind {
	case TransportTCP:
		outer, err = dialTCP(ctx, c.cfg.RemoteAddr, c.currentCredentials(), c.cfg.DialTimeout, c.cfg.LocalAddress, c.cfg.SocketControl)
	case TransportQUIC:
		ccfg := congestionConfig{
			hierarchicalPath: c.cfg.Profile.HierarchicalPath,
			discoverGrouping: c.cfg.Profile.DiscoverGrouping,
			kind:             c.cfg.Congestion, brutalBytesPerSecond: c.cfg.BrutalBytesPerSec,
			adaptiveMinBytesPerSec: c.cfg.AdaptiveMinBytesSec, adaptiveMaxBytesPerSec: c.cfg.AdaptiveMaxBytesSec,
		}
		if pooled {
			outer, err = c.dialPooledQUICLane(ctx, ccfg)
			reserveControl = true
		} else {
			outer, err = dialQUIC(ctx, c.cfg.RemoteAddr, c.currentCredentials(), c.cfg.DialTimeout, c.cfg.LocalAddress, c.cfg.SocketControl, c.observeTransientUDPSendFailure, ccfg, c.windows(), c.hopDialConfig())
		}
	default:
		return nil, fmt.Errorf("cannot dial transport %q", kind)
	}
	if err != nil {
		return nil, transportError(kind, err)
	}
	outerReady := time.Now()
	_ = outer.SetDeadline(time.Now().Add(handshakeBound(outer, c.cfg.HandshakeTimeout)))
	fc := newFrameConnLimited(outer, c.memoryLimits.frameReadBuffer, c.memoryLimits.eventQueue)
	fc.setPacketsOnStream(c.cfg.UDPOnStream)
	_ = outer.SetDeadline(time.Time{})
	c.cfg.Logger.Debug("outer lane authenticated", "transport", kind, "dial_duration", outerReady.Sub(dialStarted), "pooled", pooled)
	return &authenticatedLane{
		fc: fc, outer: outer, sessionID: sessionID, kind: kind, laneID: laneID,
		reserveControl: reserveControl,
		tcpStriping:    kind == TransportTCP && c.cfg.TCPFallbackLanes > 1,
	}, nil
}

// dialPooledQUICLane opens a stream on the current shared QUIC generation.
// Connection creation is singleflight, while stream opens are concurrent:
// after an outage one handshake rebuilds the pool and every surviving logical
// flow opens its own replacement stream on it.
func (c *Client) dialPooledQUICLane(ctx context.Context, ccfg congestionConfig) (streamConn, error) {
	dialCtx := ctx
	var cancel context.CancelFunc
	if c.cfg.DialTimeout > 0 {
		dialCtx, cancel = context.WithTimeout(ctx, c.cfg.DialTimeout)
		defer cancel()
	}
	generation, err := c.acquireControlQUICGeneration(dialCtx, ccfg)
	if err != nil {
		return nil, err
	}
	stream, err := generation.conn.OpenStreamSync(dialCtx)
	if err != nil {
		if generation.conn.Context().Err() != nil {
			c.retireControlQUICGeneration(generation, "queqiao pooled connection failed")
		}
		return nil, err
	}
	// Track how many flows share the control connection. Bulk isolation is
	// only worth its cost when there is something to protect.
	c.quicPoolActive.Add(1)
	outer := &controlPoolStreamConn{
		quicStreamConn: &quicStreamConn{stream: stream, conn: generation.conn, controller: generation.controller, closeConn: false, bulk: connBulkPath(generation.conn, c.memoryLimits.eventQueue)},
		owner:          c, generation: generation,
	}
	return outer, nil
}

func (c *Client) acquireControlQUICGeneration(ctx context.Context, ccfg congestionConfig) (*controlQUICGeneration, error) {
	for {
		// Never create a client-owned background dial on behalf of work that is
		// already gone. This also closes the shutdown race where a waiter wakes
		// after its old epoch was superseded and would otherwise start one last
		// connection before noticing cancellation below.
		if err := ctx.Err(); err != nil {
			return nil, err
		}
		c.quicMu.Lock()
		if generation := c.quicGeneration; generation != nil && generation.conn.Context().Err() == nil {
			c.quicMu.Unlock()
			return generation, nil
		}
		stale := c.quicGeneration
		c.quicGeneration = nil
		attempt := c.quicDial
		if attempt == nil {
			c.quicEpoch++
			dialCtx, cancel := context.WithCancel(context.Background())
			attempt = &controlQUICDial{epoch: c.quicEpoch, done: make(chan struct{}), cancel: cancel}
			c.quicDial = attempt
			go c.runControlQUICDial(dialCtx, attempt, ccfg)
		}
		c.quicMu.Unlock()
		if stale != nil {
			stale.close("queqiao stale pooled connection")
		}

		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-attempt.done:
		}
		if attempt.superseded {
			continue
		}
		if attempt.err != nil {
			return nil, attempt.err
		}
		if attempt.generation != nil {
			return attempt.generation, nil
		}
		// A path reset can supersede an in-flight dial. Its waiters retry against
		// the new epoch instead of inheriting a connection bound to the old path.
	}
}

func (c *Client) runControlQUICDial(ctx context.Context, attempt *controlQUICDial, ccfg congestionConfig) {
	conn, packet, err := dialQUICConnection(ctx, c.cfg.RemoteAddr, c.currentCredentials(), c.cfg.DialTimeout, c.cfg.LocalAddress, c.cfg.SocketControl, c.observeTransientUDPSendFailure, c.windows(), c.hopDialConfig())
	var generation *controlQUICGeneration
	if err == nil {
		generation = &controlQUICGeneration{
			id: attempt.epoch, conn: conn, packet: packet,
			controller: configureQUICController(conn, ccfg),
		}
	}

	c.quicMu.Lock()
	current := c.quicDial == attempt && c.quicEpoch == attempt.epoch
	if current {
		c.quicDial = nil
		if err == nil {
			c.quicGeneration = generation
			attempt.generation = generation
		} else {
			attempt.err = err
		}
	}
	c.quicMu.Unlock()
	if !current && generation != nil {
		generation.close("queqiao superseded pooled connection")
	}
	if !current {
		attempt.superseded = true
	}
	close(attempt.done)
}

func (c *Client) retireControlQUICGeneration(generation *controlQUICGeneration, reason string) {
	if generation == nil {
		return
	}
	c.quicMu.Lock()
	if c.quicGeneration == generation {
		c.quicGeneration = nil
	}
	c.quicMu.Unlock()
	generation.close(reason)
}

// laneJoinResult carries an asynchronous lane join back to the decision loop.
type laneJoinResult struct {
	lane *mpLane
	id   uint64
	err  error
	// replacement distinguishes a join opened because the flow has no lane
	// left from one opened to widen a healthy bundle. Only the first is a
	// replacement attempt, and the result arrives too late to tell by looking
	// at the flow: by then it may have recovered or died.
	replacement bool
}

// errLaneJoinRejected reports that the peer answered a lane join and refused
// it, as opposed to the join failing to complete. The distinction decides two
// things: a refusal is not evidence that UDP is unhealthy -- the handshake
// completed and the peer replied, so marking the transport down here would
// eventually push unrelated flows onto the TCP fallback -- and it is a policy
// answer that will not change during this flow, so the search should stop
// rather than back off and retry. A peer pinned to a lower lane ceiling than
// this endpoint is the ordinary way to reach it.
var errLaneJoinRejected = errors.New("lane join rejected")

// errLaneJoinCapacity is a refusal by the peer's own lane admission ceiling,
// in contrast to errLaneJoinRejected's permanent answers about the session.
// It says nothing about the session and nothing about the path: the flow the
// lane would join is alive, and the answer can change as lanes come and go,
// so it neither ends a rescue round early nor marks the session unresumable.
// The ordinary way to reach it is several rescue JOINs racing the peer's
// lane cap, where all but the first admitted are supposed to lose.
var errLaneJoinCapacity = errors.New("lane join refused by peer lane capacity")

// errLaneJoinTCPMode is the peer saying the flow has already committed to
// TCP fallback, so a QUIC lane can never be admitted to it. It stays an
// errLaneJoinRejected -- a configuration-pinned QUIC client has no TCP commit
// to make and must fail the flow fast as before -- but an AUTO recovery path
// matches it specifically to commit to TCP at once instead of spending its
// replacement grace on QUIC retries the peer has already ruled out.
var errLaneJoinTCPMode = fmt.Errorf("%w: flow switched to TCP fallback", errLaneJoinRejected)

// errBulkConnectionLimit is a scheduling answer, not a transport failure.
// The caller keeps the flow on its pooled control connection when every
// isolation slot is occupied. Falling back to a dedicated connection here
// would silently bypass the descriptor and handshake budget this limit exists
// to enforce.
var errBulkConnectionLimit = errors.New("bulk lane connection limit reached")

func dedicatedBulkFallbackAllowed(err error) bool {
	return err != nil &&
		!errors.Is(err, errBulkConnectionLimit) &&
		!errors.Is(err, context.Canceled) &&
		!errors.Is(err, context.DeadlineExceeded)
}

func (c *Client) openJoinLane(ctx context.Context, kind TransportKind, sessionID [16]byte, flowID, laneID uint64) (*mpLane, error) {
	if kind != TransportQUIC && kind != TransportTCP {
		return nil, fmt.Errorf("unsupported join transport %q", kind)
	}
	if kind == TransportQUIC && c.cfg.EnableQUICPool {
		if lane, poolErr := c.openPooledJoinLane(ctx, sessionID, flowID, laneID); poolErr == nil {
			return lane, nil
		} else if !dedicatedBulkFallbackAllowed(poolErr) {
			return nil, poolErr
		} else {
			c.cfg.Logger.Debug("pooled lane join unavailable; using dedicated lane", "error", poolErr)
		}
	}
	lane, err := c.dialJoinLane(ctx, kind, sessionID, laneID)
	if err != nil {
		return nil, err
	}
	return c.completeLaneJoin(lane, flowID, 0)
}

// openControlPoolJoinLane restores the control role on the one replacement
// generation shared by every affected flow. It is intentionally separate from
// openPooledJoinLane: that pool gives a bulk flow an exclusive congestion
// controller, while this pool is the multiplexed control failure domain being
// rebuilt.
func (c *Client) openControlPoolJoinLane(ctx context.Context, sessionID [16]byte, flowID, laneID uint64) (*mpLane, error) {
	lane, err := c.dialLaneMode(ctx, TransportQUIC, sessionID, laneID, true)
	if err != nil {
		return nil, err
	}
	return c.completeLaneJoin(lane, flowID, protocol.FlagReserveControl)
}

func (c *Client) completeLaneJoin(lane *authenticatedLane, flowID uint64, flags uint16) (*mpLane, error) {
	_ = lane.outer.SetDeadline(time.Now().Add(handshakeBound(lane.outer, c.cfg.HandshakeTimeout)))
	if err := lane.fc.Write(protocol.Frame{Header: protocol.Header{
		Version: protocol.Version, Type: protocol.TypeJoin, Flags: flags,
		SessionID: lane.sessionID, FlowID: flowID, Class: protocol.ClassBulk,
	}, Payload: encodeLaneID(lane.laneID)}); err != nil {
		_ = lane.fc.Close()
		return nil, err
	}
	response, err := lane.fc.Read()
	if err != nil {
		_ = lane.fc.Close()
		return nil, err
	}
	if response.Header.Type == protocol.TypeReset && response.Header.SessionID == lane.sessionID && response.Header.FlowID == flowID {
		_ = lane.fc.Close()
		if len(response.Payload) > 1 {
			switch session.ResetCode(response.Payload[0]) {
			case session.ResetFlowLimit:
				return nil, fmt.Errorf("%w: %s", errLaneJoinCapacity, string(response.Payload[1:]))
			case session.ResetTransport:
				return nil, fmt.Errorf("%w: %s", errLaneJoinTCPMode, string(response.Payload[1:]))
			}
			return nil, fmt.Errorf("%w: %s", errLaneJoinRejected, string(response.Payload[1:]))
		}
		return nil, errLaneJoinRejected
	}
	if response.Header.Type != protocol.TypeOpenOK || response.Header.SessionID != lane.sessionID || response.Header.FlowID != flowID || len(response.Payload) != 0 {
		_ = lane.fc.Close()
		return nil, errors.New("invalid lane join acknowledgement")
	}
	_ = lane.outer.SetDeadline(time.Time{})
	return &mpLane{
		id: lane.laneID, kind: lane.kind, fc: lane.fc,
		tcpStriping: lane.tcpStriping,
		control:     flags&protocol.FlagReserveControl != 0,
	}, nil
}

// openPooledJoinLane uses a bounded, separately authenticated QUIC connection
// for bulk streams. Mutual TLS authenticates the connection; the JOIN frame
// only identifies the existing flow and lane and cannot change its principal.
func (c *Client) openPooledJoinLane(ctx context.Context, sessionID [16]byte, flowID, laneID uint64) (*mpLane, error) {
	started := time.Now()
	outer, err := c.openBulkPoolStream(ctx)
	if err != nil {
		return nil, err
	}
	fc := newFrameConnLimited(outer, c.memoryLimits.frameReadBuffer, c.memoryLimits.eventQueue)
	fc.setPacketsOnStream(c.cfg.UDPOnStream)
	lane, err := c.completeLaneJoin(&authenticatedLane{
		fc: fc, outer: outer, sessionID: sessionID, kind: TransportQUIC, laneID: laneID,
	}, flowID, 0)
	if err != nil {
		return nil, err
	}
	c.cfg.Logger.Debug("bulk lane joined", "lane", laneID, "duration", time.Since(started))
	return lane, nil
}

// openBulkPoolStream reserves one secondary connection and opens its lane
// stream. Connections are created lazily, so one-shot and interactive-only
// clients pay no extra QUIC handshake, and each is reserved exclusively for
// the lane it carries so concurrent lanes keep independent 4-tuples and
// congestion state.
func (c *Client) openBulkPoolStream(ctx context.Context) (streamConn, error) {
	started := time.Now()
	dialCtx := ctx
	var cancel context.CancelFunc
	if c.cfg.DialTimeout > 0 {
		dialCtx, cancel = context.WithTimeout(ctx, c.cfg.DialTimeout)
		defer cancel()
	}
	entry, err := c.reserveBulkConn(dialCtx)
	if err != nil {
		return nil, err
	}
	stream, err := entry.conn.OpenStreamSync(dialCtx)
	if err != nil {
		c.releaseBulkConn(entry, entry.conn.Context().Err() != nil)
		return nil, err
	}
	c.cfg.Logger.Debug("bulk pool stream opened", "duration", time.Since(started), "connections", c.bulkConnCount())
	return &bulkPoolStreamConn{
		quicStreamConn: &quicStreamConn{stream: stream, conn: entry.conn, controller: entry.controller, closeConn: false, bulk: connBulkPath(entry.conn, c.memoryLimits.eventQueue)},
		owner:          c, entry: entry,
	}, nil
}

// reserveBulkConn returns an idle authenticated connection, or establishes a
// new one when every existing connection is already carrying a lane.
func (c *Client) reserveBulkConn(ctx context.Context) (*bulkConn, error) {
	c.bulkMu.Lock()
	live := c.bulkConns[:0]
	for _, entry := range c.bulkConns {
		if entry.conn.Context().Err() != nil && !entry.busy {
			entry.close("queqiao stale bulk pool")
			continue
		}
		live = append(live, entry)
	}
	c.bulkConns = live
	for _, entry := range c.bulkConns {
		if !entry.busy && entry.conn.Context().Err() == nil {
			entry.busy = true
			if entry.idleTimer != nil {
				entry.idleTimer.Stop()
				entry.idleTimer = nil
			}
			c.bulkMu.Unlock()
			return entry, nil
		}
	}
	if len(c.bulkConns) >= c.maxBulkConns() {
		c.bulkMu.Unlock()
		return nil, errBulkConnectionLimit
	}
	c.bulkMu.Unlock()

	// The handshake is deliberately performed without the pool mutex so that
	// one slow secondary handshake cannot block every other lane join.
	entry, err := c.dialBulkConn(ctx)
	if err != nil {
		return nil, err
	}
	c.bulkMu.Lock()
	if len(c.bulkConns) >= c.maxBulkConns() {
		c.bulkMu.Unlock()
		entry.close("queqiao bulk pool limit reached")
		return nil, errBulkConnectionLimit
	}
	entry.busy = true
	c.bulkConns = append(c.bulkConns, entry)
	c.bulkMu.Unlock()
	return entry, nil
}

// isolatedBulkConns bounds the secondary connections one client may hold.
//
// It is a count of concurrently isolated bulk flows, not of lanes. A flow's
// data lives on one lane, so a flow needs at most one of these -- but several
// bulk flows can be in flight at once, and each has to have its own or
// isolation is a queue rather than a policy. Capping this at one during the
// striping excision would have let exactly one bulk flow at a time leave the
// shared connection, which is the case the eight-flow live measurement is
// about.
//
// Eight is what the lane ceiling used to permit and is a bound on descriptors
// and handshakes rather than a tuning choice; a ninth concurrent bulk flow
// stays on the pooled connection, which is where it started.
const isolatedBulkConns = 8

func (c *Client) maxBulkConns() int { return c.memoryLimits.maxBulkConnections }

func (c *Client) bulkConnCount() int {
	c.bulkMu.Lock()
	defer c.bulkMu.Unlock()
	return len(c.bulkConns)
}

func (c *Client) dialBulkConn(ctx context.Context) (*bulkConn, error) {
	started := time.Now()
	conn, packet, err := dialQUICConnection(ctx, c.cfg.RemoteAddr, c.currentCredentials(), c.cfg.DialTimeout, c.cfg.LocalAddress, c.cfg.SocketControl, c.observeTransientUDPSendFailure, c.windows(), c.hopDialConfig())
	if err != nil {
		return nil, err
	}
	entry := &bulkConn{conn: conn, packet: packet}
	entry.controller = configureQUICController(conn, congestionConfig{
		hierarchicalPath: c.cfg.Profile.HierarchicalPath,
		kind:             c.cfg.Congestion, brutalBytesPerSecond: c.cfg.BrutalBytesPerSec,
		adaptiveMinBytesPerSec: c.cfg.AdaptiveMinBytesSec, adaptiveMaxBytesPerSec: c.cfg.AdaptiveMaxBytesSec,
	})
	c.cfg.Logger.Debug("bulk QUIC pool authenticated", "duration", time.Since(started))
	return entry, nil
}

// controlPoolStreamConn keeps the count of flows sharing the pooled control
// connection accurate, which is what decides whether a bulk flow should move
// off it.
type controlPoolStreamConn struct {
	*quicStreamConn
	owner      *Client
	generation *controlQUICGeneration
	once       sync.Once
}

func (s *controlPoolStreamConn) transportFailed(err error) {
	if s.generation == nil {
		return
	}
	// A QUIC connection can remain superficially open after one of its streams
	// has stopped making progress. In that state Context().Err() is still nil,
	// so keeping the generation makes every later flow reuse the same poisoned
	// pool. A real I/O timeout is sufficient evidence to retire the generation;
	// ordinary per-stream EOFs and application closes must not evict it.
	if s.generation.conn.Context().Err() != nil || pooledTransportTimedOut(err) {
		s.owner.retireControlQUICGeneration(s.generation, "queqiao pooled connection failed")
	}
}

func pooledTransportTimedOut(err error) bool {
	if errors.Is(err, context.DeadlineExceeded) {
		return true
	}
	var timeout interface{ Timeout() bool }
	return errors.As(err, &timeout) && timeout.Timeout()
}

func (s *controlPoolStreamConn) Close() error {
	err := s.quicStreamConn.Close()
	s.once.Do(func() {
		if remaining := s.owner.quicPoolActive.Add(-1); remaining < 0 {
			s.owner.quicPoolActive.Store(0)
		}
	})
	return err
}

type bulkPoolStreamConn struct {
	*quicStreamConn
	owner *Client
	entry *bulkConn
	once  sync.Once
}

func (s *bulkPoolStreamConn) Close() error {
	err := s.quicStreamConn.Close()
	s.once.Do(func() { s.owner.releaseBulkConn(s.entry, s.entry.conn.Context().Err() != nil) })
	return err
}

// releaseBulkConn returns a connection to the idle set, or discards it when
// its transport is already dead. An idle connection is retained briefly so a
// following flow can skip the handshake, then closed.
func (c *Client) releaseBulkConn(entry *bulkConn, dead bool) {
	c.bulkMu.Lock()
	entry.busy = false
	if dead {
		remaining := c.bulkConns[:0]
		for _, existing := range c.bulkConns {
			if existing != entry {
				remaining = append(remaining, existing)
			}
		}
		c.bulkConns = remaining
		c.bulkMu.Unlock()
		entry.close("queqiao bulk pool failed")
		return
	}
	if entry.idleTimer != nil {
		entry.idleTimer.Stop()
	}
	entry.idleTimer = time.AfterFunc(bulkPoolIdleTimeout, func() { c.expireBulkConn(entry) })
	c.bulkMu.Unlock()
}

func (c *Client) expireBulkConn(entry *bulkConn) {
	c.bulkMu.Lock()
	if entry.busy {
		c.bulkMu.Unlock()
		return
	}
	remaining := c.bulkConns[:0]
	found := false
	for _, existing := range c.bulkConns {
		if existing == entry {
			found = true
			continue
		}
		remaining = append(remaining, existing)
	}
	c.bulkConns = remaining
	c.bulkMu.Unlock()
	if found {
		entry.close("queqiao bulk pool idle")
	}
}

func bulkLaneBudget(reserveControl bool) (bulk, controlReserve int) {
	if reserveControl {
		return 1, 1
	}
	return 1, 0
}

func (c *Client) manageLanes(ctx context.Context, flow *multipathFlow, sessionID [16]byte, flowID uint64, initialKind TransportKind) {
	if initialKind == TransportTCP {
		if c.cfg.TCPFallbackLanes > 1 {
			c.manageTCPBundle(ctx, flow, sessionID, flowID)
		}
		return
	}
	if initialKind != TransportQUIC {
		return
	}
	c.manageQUICLanes(ctx, flow, sessionID, flowID)
}

func (c *Client) manageQUICLanes(ctx context.Context, flow *multipathFlow, sessionID [16]byte, flowID uint64) {
	_, controlReserve := bulkLaneBudget(flow.reserveControlLane)
	manageCtx, manageCancel := context.WithCancel(ctx)
	defer manageCancel()
	// This goroutine is the only thing that opens a replacement lane for this
	// flow. When it returns -- budget spent, context gone, or handed off to the
	// bundle manager below, which marks the flow again when it returns in turn
	// -- the flow's replacement grace is waiting for something nobody will
	// send, and it should stop rather than leave the application in silence.
	defer flow.noteReplacementAbandoned()
	go func() {
		select {
		case <-flow.doneChan():
			manageCancel()
		case <-manageCtx.Done():
		}
	}()
	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop()
	joins := make(chan laneJoinResult, 1)
	joinPending := false
	isolated := false
	var lastDecision time.Time
	var recoveryBackoff time.Duration
	var nextRecovery time.Time
	recoveryAttempts := 0
	var lastRecoveryAttempt time.Time
	var isolationBlockedUntil time.Time
	var isolationBackoff time.Duration
	isolationAttempts := 0
	var stallBackoff time.Duration
	var nextStallRescue time.Time
	for {
		select {
		case <-flow.doneChan():
			return
		case <-manageCtx.Done():
			return
		case <-flow.stallSignals():
			// The watchdog suspects the lane, not declares it dead: the flow
			// still has one, so this is a rescue beside the existing lane,
			// not a replacement for a lost one. A flow with no lane at all is
			// the outage path below, which owns that case.
			if flow.doneChanClosed() {
				return
			}
			if len(flow.healthyLanes()) == 0 {
				continue
			}
			now := time.Now()
			if now.Before(nextStallRescue) {
				continue
			}
			if err := c.runRescueRound(manageCtx, flow, sessionID, flowID); err != nil {
				if manageCtx.Err() != nil || flow.doneChanClosed() {
					return
				}
				if errors.Is(err, errLaneJoinRejected) {
					// As below: the peer's answer is permanent, so stop.
					flow.resumeRefused.Store(true)
					c.cfg.Logger.Debug("peer cannot resume this association", "flow_id", flowID, "error", err)
					return
				}
				if errors.Is(err, errLaneJoinCapacity) && flow.laneCapacityRefusals() >= maxLaneRecoveryAttempts {
					// The ceiling answer is transient only while lanes
					// genuinely come and go. This many consecutive refusals
					// without one successful round is a wedged admission slot
					// the peer cannot see, so the flow fails fast here exactly
					// as it does for a permanent refusal, and the application
					// reconnects on a fresh flow.
					flow.resumeRefused.Store(true)
					c.cfg.Logger.Debug("peer lane capacity answer persisted; giving up on this association", "flow_id", flowID, "refusals", flow.laneCapacityRefusals())
					return
				}
				if !errors.Is(err, context.Canceled) && !errors.Is(err, context.DeadlineExceeded) {
					c.cfg.Logger.Warn("stall rescue unavailable", "flow_id", flowID, "error", err)
				}
				if stallBackoff == 0 {
					stallBackoff = time.Second
				} else if stallBackoff < 15*time.Second {
					stallBackoff *= 2
					if stallBackoff > 15*time.Second {
						stallBackoff = 15 * time.Second
					}
				}
				nextStallRescue = time.Now().Add(stallBackoff)
			} else {
				// A fresh lane must prove itself before the next round of
				// dials; the watchdog will re-signal if the stall is real.
				stallBackoff = 0
				nextStallRescue = time.Now().Add(time.Second)
			}
		case <-ticker.C:
			// The remote completion watcher can close its lanes just before
			// this scheduler tick. Both FIN directions are already known at
			// that point, so joining a tombstoned/unknown session would only
			// create noisy warnings and transient UDP-health penalties.
			if flow.finSent.Load() && flow.remoteFinSeen.Load() {
				flow.closeAll()
				return
			}
			for draining := true; draining; {
				select {
				case result := <-joins:
					joinPending = false
					switch {
					case result.err != nil:
						if manageCtx.Err() != nil || flow.doneChanClosed() {
							return
						}
						if errors.Is(result.err, errLaneJoinRejected) || errors.Is(result.err, errLaneJoinCapacity) {
							// The peer's ceiling, not a broken path. Keep the
							// flow where it is.
							isolated = true
							c.cfg.Logger.Debug("peer refused lane join; flow stays on the shared connection", "lane", result.id, "error", result.err)
							break
						}
						if errors.Is(result.err, errBulkConnectionLimit) {
							c.cfg.Logger.Debug("bulk isolation capacity occupied; flow stays on the shared connection", "lane", result.id)
						} else {
							c.cfg.Logger.Warn("bulk isolation lane unavailable", "lane", result.id, "error", result.err)
						}
						if isolationBackoff == 0 {
							isolationBackoff = minLaneProbeBackoff
						} else if isolationBackoff < maxLaneProbeBackoff {
							isolationBackoff *= 2
							if isolationBackoff > maxLaneProbeBackoff {
								isolationBackoff = maxLaneProbeBackoff
							}
						}
						isolationBlockedUntil = time.Now().Add(isolationBackoff)
					default:
						if err := flow.addLane(result.lane); err != nil {
							_ = result.lane.fc.Close()
							break
						}
						isolated = true
						if controlReserve > 0 && flow.laneCount() == controlReserve+1 {
							// The flow's first bulk lane is what moves it off
							// the shared control connection, which is what
							// keeps interactive traffic out of a bulk
							// congestion window. Count it so an operator can
							// see the policy act.
							c.metrics.BulkIsolated()
						}
					}
				default:
					draining = false
				}
			}
			snapshot := flow.snapshot()
			now := time.Now()
			if snapshot.HealthyLanes == 0 {
				if flow.doneChanClosed() {
					return
				}
				if recoveryAttempts >= maxLaneRecoveryAttempts {
					// Say so once, at the level a failing flow is reported at:
					// from here the flow fails immediately rather than waiting
					// out a grace nothing will arrive during.
					c.cfg.Logger.Info("lane recovery abandoned", "attempts", recoveryAttempts, "flow_id", flowID)
					return
				}
				if !nextRecovery.IsZero() && now.Before(nextRecovery) {
					continue
				}
				recoveryAttempts++
				lastRecoveryAttempt = now
				flow.noteReplacementAttempt()
				if err := c.runRescueRound(manageCtx, flow, sessionID, flowID); err != nil {
					flow.noteReplacementFailure()
					if errors.Is(err, errLaneJoinRejected) {
						// The peer answered, and its answer was that it does
						// not hold this session. That does not change: a
						// session identifier is random and is never reissued.
						// Retrying it spends the flow's whole replacement
						// grace learning the same thing, so record the refusal
						// and let the flow fail now.
						flow.resumeRefused.Store(true)
						c.cfg.Logger.Debug("peer cannot resume this association", "flow_id", flowID, "error", err)
						return
					}
					if !errors.Is(err, context.Canceled) && !errors.Is(err, context.DeadlineExceeded) {
						// The flow this belongs to is the whole point of the
						// line: a gateway record saying a flow failed with no
						// replacement cannot be told from one where none was
						// tried unless the attempts can be found by flow.
						c.cfg.Logger.Warn("lane recovery unavailable", "flow_id", flowID,
							"attempt", recoveryAttempts, "error", err)
					}
					if recoveryBackoff == 0 {
						recoveryBackoff = time.Second
					} else if recoveryBackoff < 15*time.Second {
						recoveryBackoff *= 2
						if recoveryBackoff > 15*time.Second {
							recoveryBackoff = 15 * time.Second
						}
					}
					nextRecovery = now.Add(recoveryBackoff)
				} else {
					// A replacement that succeeds its handshake can still fail
					// immediately. Keep a bounded exponential delay between all
					// attempts, not only failed handshakes.
					if recoveryBackoff == 0 {
						recoveryBackoff = time.Second
					}
					nextRecovery = now.Add(recoveryBackoff)
					if recoveryBackoff < 15*time.Second {
						recoveryBackoff *= 2
						if recoveryBackoff > 15*time.Second {
							recoveryBackoff = 15 * time.Second
						}
					}
				}
				continue
			}
			// A replacement that survives one 500-ms scheduler tick is not yet
			// stable. Reset the lifetime budget only after a sustained healthy
			// dwell; otherwise accept-then-close peers can bypass the cap by
			// keeping each replacement alive very briefly.
			if recoveryAttempts > 0 && !lastRecoveryAttempt.IsZero() && time.Since(lastRecoveryAttempt) >= laneRecoveryResetAfter {
				recoveryAttempts = 0
				recoveryBackoff = 0
				nextRecovery = time.Time{}
				lastRecoveryAttempt = time.Time{}
			}
			// Once a TCP rescue lane is installed, keep the session on it.
			if hasTCPLane(flow) {
				retired := flow.retireLanesExcept(TransportTCP)
				c.cfg.Logger.Info("flow handed off to TCP fallback", "retired_quic_lanes", retired, "tcp_lanes", flow.laneCount())
				if c.cfg.TCPFallbackLanes > 1 {
					c.manageTCPBundle(manageCtx, flow, sessionID, flowID)
				}
				return
			}
			// Everything below is isolation, and it is over once it has
			// happened: a QUIC flow's data lives on one lane, so there is never
			// a second QUIC data lane to open.
			if isolated || controlReserve == 0 || joinPending {
				continue
			}
			// Isolation earns its cost only while another flow shares the
			// control connection. A bulk transfer alone on it has nothing to
			// protect, and moving it would spend a handshake and a fresh
			// congestion window for no benefit: measured on an otherwise idle
			// path that costs about 8% of bulk goodput.
			if c.quicPoolActive.Load() <= 1 {
				continue
			}
			if snapshot.Class != classifier.ClassBulk && !shouldPrewarmBulkLane(snapshot) {
				continue
			}
			// Do not consume the decision interval while the flow is still NEW
			// or INTERACTIVE. The classifier may cross its bulk byte/age
			// boundary just after such a tick.
			if !lastDecision.IsZero() && now.Sub(lastDecision) < laneDecisionInterval {
				continue
			}
			lastDecision = now
			if isolationAttempts >= maxLaneProbeAttempts || flow.doneChanClosed() ||
				now.Before(isolationBlockedUntil) {
				continue
			}
			laneID, err := flow.allocateJoinID()
			if err != nil {
				return
			}
			isolationAttempts++
			joinPending = true
			// Open the lane off the decision loop. On a saturated path the
			// join's own handshake queues behind the flow's data and has been
			// measured taking several seconds; doing it inline would leave the
			// flow blind to a lane failure meanwhile.
			go func() {
				lane, err := c.openJoinLane(manageCtx, TransportQUIC, sessionID, flowID, laneID)
				select {
				case joins <- laneJoinResult{lane: lane, id: laneID, err: err}:
				case <-manageCtx.Done():
					if lane != nil {
						_ = lane.fc.Close()
					}
				}
			}()
		}
	}
}

// manageTCPBundle maintains a bounded group of independent reliable paths for
// a TCP-only flow. Extra lanes are opened only after bulk classification (or
// its asymmetric-download prewarm), but one lane is always recoverable. The
// expansion failure budget is deliberately separate from zero-lane recovery:
// an endpoint refusing lane 16 must not prevent a later replacement of the
// one connection the flow still needs to remain alive.
func (c *Client) manageTCPBundle(ctx context.Context, flow *multipathFlow, sessionID [16]byte, flowID uint64) {
	manageCtx, cancel := context.WithCancel(ctx)
	defer cancel()
	// As in manageQUICLanes: once this returns, nothing will open another lane
	// for the flow, and its replacement grace has nothing left to wait for.
	defer flow.noteReplacementAbandoned()
	go func() {
		select {
		case <-flow.doneChan():
			cancel()
		case <-manageCtx.Done():
		}
	}()

	ticker := time.NewTicker(250 * time.Millisecond)
	defer ticker.Stop()
	joins := make(chan laneJoinResult, maxTCPFallbackLanes)
	pending := 0
	bundleFailures := 0
	recoveryAttempts := 0
	var lastRecoveryAttempt time.Time
	bundleDisabled := false
	// bundleCapacityBlockedUntil pauses widening after the peer answers a
	// bundle join with its lane ceiling. The ceiling answer is transient by
	// design -- lanes come and go -- so the pause expires with the recovery
	// cooldown and a successful join clears it, rather than one refusal
	// disabling widening for the flow's life.
	var bundleCapacityBlockedUntil time.Time
	activated := false
	var nextAttempt time.Time
	var retryBackoff time.Duration
	var lastFailure time.Time
	observedLaneFailures := flow.laneFailureCount()

	launch := func(replacement bool) bool {
		laneID, err := flow.allocateJoinID()
		if err != nil {
			return false
		}
		if replacement {
			flow.noteReplacementAttempt()
		}
		pending++
		go func() {
			lane, joinErr := c.openJoinLane(manageCtx, TransportTCP, sessionID, flowID, laneID)
			select {
			case joins <- laneJoinResult{lane: lane, id: laneID, err: joinErr, replacement: replacement}:
			case <-manageCtx.Done():
				if lane != nil {
					_ = lane.fc.Close()
				}
			}
		}()
		return true
	}

	for {
		select {
		case <-flow.doneChan():
			return
		case <-manageCtx.Done():
			return
		case result := <-joins:
			if pending > 0 {
				pending--
			}
			if result.err != nil {
				if result.replacement {
					flow.noteReplacementFailure()
				}
				if manageCtx.Err() != nil || flow.doneChanClosed() {
					return
				}
				if errors.Is(result.err, errLaneJoinRejected) {
					bundleDisabled = true
					if flow.laneCount() == 0 {
						flow.resumeRefused.Store(true)
						return
					}
					c.cfg.Logger.Debug("peer refused TCP bundle lane", "lane", result.id, "error", result.err)
					continue
				}
				if errors.Is(result.err, errLaneJoinCapacity) {
					// The peer's lane ceiling, not a lost session: stop
					// widening for the cooldown, but the lanes the bundle
					// has stay valid.
					bundleCapacityBlockedUntil = time.Now().Add(laneRecoveryResetAfter)
					c.cfg.Logger.Debug("peer lane capacity reached for TCP bundle", "lane", result.id, "error", result.err)
					continue
				}
				bundleFailures++
				lastFailure = time.Now()
				if retryBackoff == 0 {
					retryBackoff = time.Second
				} else if retryBackoff < 15*time.Second {
					retryBackoff *= 2
					if retryBackoff > 15*time.Second {
						retryBackoff = 15 * time.Second
					}
				}
				nextAttempt = time.Now().Add(retryBackoff)
				if bundleFailures >= maxLaneRecoveryAttempts {
					bundleDisabled = true
				}
				c.cfg.Logger.Warn("TCP bundle lane unavailable", "lane", result.id, "error", result.err, "failures", bundleFailures)
				continue
			}
			if err := flow.addLane(result.lane); err != nil {
				_ = result.lane.fc.Close()
				continue
			}
			if flow.remoteFinSeen.Load() && flow.laneCount() > 1 {
				// The peer has no more bytes to send. This join was launched before
				// its FIN arrived and is no longer useful; keep one reliable lane
				// for a possible upload half-close, but do not resurrect the bundle.
				flow.closeFailedLane(result.lane)
				continue
			}
			c.cfg.Logger.Debug("TCP bundle lane joined", "lane", result.id, "lanes", flow.laneCount())
			// A fresh lane just proved the ceiling has room again.
			bundleCapacityBlockedUntil = time.Time{}
		case <-ticker.C:
		}

		if flow.finSent.Load() && flow.remoteFinSeen.Load() {
			flow.closeAll()
			return
		}
		// A fully closed local application has sent CLOSE_ABORT and explicitly
		// declared that it will neither read nor write more bytes. Replacing the
		// lane after the server acts on that marker can only resurrect a flow
		// which is already complete.
		if flow.localAbortSent.Load() || (flow.localClosed.Load() && flow.remoteFinSeen.Load()) {
			return
		}
		flow.refreshClass()
		now := time.Now()
		failures := flow.laneFailureCount()
		if failures > observedLaneFailures {
			bundleFailures += int(failures - observedLaneFailures)
			observedLaneFailures = failures
			lastFailure = now
			if bundleFailures >= maxLaneRecoveryAttempts {
				bundleDisabled = true
			}
		}
		if bundleFailures > 0 && !lastFailure.IsZero() && now.Sub(lastFailure) >= laneRecoveryResetAfter {
			bundleFailures = 0
			bundleDisabled = false
			retryBackoff = 0
			nextAttempt = time.Time{}
			lastFailure = time.Time{}
		}

		snapshot := flow.snapshot()
		healthy := tcpLaneCount(flow)
		if healthy == 0 {
			if pending != 0 || recoveryAttempts >= maxLaneRecoveryAttempts || now.Before(nextAttempt) {
				continue
			}
			recoveryAttempts++
			lastRecoveryAttempt = now
			launch(true)
			continue
		}
		// An accept-then-close peer must not reset the replacement budget on
		// every successful handshake. Only a lane that remains healthy for a
		// sustained dwell proves recovery, matching the QUIC rescue policy.
		if recoveryAttempts > 0 && !lastRecoveryAttempt.IsZero() && now.Sub(lastRecoveryAttempt) >= laneRecoveryResetAfter {
			recoveryAttempts = 0
			lastRecoveryAttempt = time.Time{}
		}
		if flow.remoteFinSeen.Load() {
			continue
		}
		if c.cfg.TCPFallbackLanes <= 1 || !flow.tcpStriping.Load() || bundleDisabled || now.Before(bundleCapacityBlockedUntil) {
			continue
		}
		if snapshot.Class != classifier.ClassBulk && !shouldPrewarmBulkLane(snapshot) {
			continue
		}
		if !activated {
			activated = true
			flow.tcpStriping.Store(true)
			c.cfg.Logger.Info("TCP fallback striping activated", "target_lanes", c.cfg.TCPFallbackLanes)
		}
		if now.Before(nextAttempt) {
			continue
		}
		missing := c.cfg.TCPFallbackLanes - healthy - pending
		for range missing {
			// Widening a bundle that already has a healthy lane is not a
			// replacement, and counting it as one would bury the flows that
			// have nothing left in the ordinary run of bulk transfers.
			if !launch(false) {
				break
			}
		}
	}
}

func tcpLaneCount(flow *multipathFlow) int {
	count := 0
	for _, lane := range flow.healthyLanes() {
		if lane.kind == TransportTCP {
			count++
		}
	}
	return count
}

// hasTCPLane reports whether the flow has been rescued onto TLS/TCP. Once it
// has, the session stays there: mixing a reliable stream lane with a QUIC one
// compounds head-of-line blocking and makes the fallback less predictable.
func hasTCPLane(flow *multipathFlow) bool {
	for _, lane := range flow.healthyLanes() {
		if lane.kind == TransportTCP {
			return true
		}
	}
	return false
}

func shouldPrewarmBulkLane(snapshot flowSnapshot) bool {
	if snapshot.Elapsed < bulkLanePrewarmAge || snapshot.Bytes < bulkLanePrewarmBytes {
		return false
	}
	smaller, larger := snapshot.BytesUp, snapshot.BytesDown
	if smaller > larger {
		smaller, larger = larger, smaller
	}
	if smaller == 0 {
		return larger >= bulkLanePrewarmBytes
	}
	return larger/smaller >= bulkLaneAsymmetry
}

// rescueAttempt is one dial+JOIN strategy in a parallel rescue round.
type rescueAttempt func(ctx context.Context) (*mpLane, error)

// openParallelRescue runs a round of concurrent dial+JOIN attempts and
// installs the first lane whose JOIN completes. It exists because the rescue
// it replaces was one serialized handshake racing the flow's replacement
// grace: on a path erasing a third of packets, a single handshake is a coin
// flip repeated slowly, while several independent handshakes fail together
// only when the path truly carries nothing.
//
// Attempt zero is the established recovery strategy unchanged -- for a pooled
// flow that is the shared control generation (whose dial stays singleflight:
// every affected flow coalesces onto it, and the racers below never touch
// that generation's state), and for AUTO it keeps the bounded QUIC window
// followed by exactly one committed TCP JOIN. The remaining attempts are
// independent dedicated QUIC dials. Each one draws the next walked hop port,
// so with port hopping configured they spray across the pool; without it they
// dial the same single port, where the value is independent handshakes with
// independent retransmission schedules rather than port diversity. The TCP
// fallback's conditions are untouched: a TCP commit can still only come from
// attempt zero, on the same terms openRecoveryLane always had.
// runRescueRound executes one parallel rescue round under the flow's
// in-flight guard: the stall watchdog stays silent for the round, and any
// request it managed to queue just before the guard engaged is dropped
// afterwards, because the round has just changed the state that request
// described.
func (c *Client) runRescueRound(ctx context.Context, flow *multipathFlow, sessionID [16]byte, flowID uint64) error {
	flow.rescueInFlight.Store(true)
	err := c.openParallelRescue(ctx, flow, sessionID, flowID)
	flow.rescueInFlight.Store(false)
	// The capacity streak is kept per round rather than per attempt: a round
	// is the unit the peer's ceiling answer is believed or doubted on, and
	// the attempts inside one round race exactly because only one of them is
	// supposed to win.
	if errors.Is(err, errLaneJoinCapacity) {
		flow.noteLaneCapacityRefusal()
	} else {
		flow.resetLaneCapacityRefusals()
	}
	select {
	case <-flow.stallSignals():
	default:
	}
	return err
}

func (c *Client) openParallelRescue(ctx context.Context, flow *multipathFlow, sessionID [16]byte, flowID uint64) error {
	// As in openRecoveryLane: a completed flow must not keep dialing. Only
	// attempt zero checks this itself; the sprayed racers rely on the guard
	// here.
	if flow.finSent.Load() && flow.remoteFinSeen.Load() {
		return context.Canceled
	}
	attempts := make([]rescueAttempt, 0, metrics.RescueAttemptSlots)
	attempts = append(attempts, func(ctx context.Context) (*mpLane, error) {
		return c.openRecoveryLane(ctx, flow, sessionID, flowID)
	})
	if c.cfg.Transport != TransportTCP {
		for len(attempts) < metrics.RescueAttemptSlots {
			attempts = append(attempts, func(ctx context.Context) (*mpLane, error) {
				return c.openSprayedQUICRescueJoin(ctx, flow, sessionID, flowID)
			})
		}
	}
	lane, winner, err := c.raceRescueAttempts(ctx, flow, attempts)
	if err != nil {
		return err
	}
	if err := c.installRecoveryLane(flow, lane); err != nil {
		return err
	}
	c.cfg.Logger.Info("lane rescue joined", "flow", flowID, "winning_attempt", winner, "attempts", len(attempts), "lane", lane.id)
	return nil
}

// openSprayedQUICRescueJoin is one independent QUIC dial+JOIN for the
// parallel rescue: its own connection, its own handshake retransmission
// schedule, and -- through the shared hop walk -- the next port in a shuffled
// permutation of the hop pool, which makes concurrent attempts uniform over
// the available ports without repeating one.
func (c *Client) openSprayedQUICRescueJoin(ctx context.Context, flow *multipathFlow, sessionID [16]byte, flowID uint64) (*mpLane, error) {
	laneID, err := flow.allocateJoinID()
	if err != nil {
		return nil, err
	}
	lane, err := c.dialJoinLane(ctx, TransportQUIC, sessionID, laneID)
	if err != nil {
		return nil, err
	}
	return c.completeLaneJoin(lane, flowID, 0)
}

// raceRescueAttempts runs a rescue round: every attempt starts together, the
// first successful JOIN wins, and the losers' contexts are cancelled at once.
// Losing lanes are closed wherever they surface -- an attempt finishing after
// the race was decided closes its own lane, and the drain collects any that
// completed in the window before the cancellation reached them.
//
// The race is deliberately not transactional with the server, which admits
// JOINs in arrival order while the winner here is the first finisher. What
// keeps a late losing JOIN from evicting the winner's server side at the
// lane ceiling is the server: a lane is unevictable while its JOIN handshake
// is in flight and for one path-detection budget afterwards, so the loser is
// refused by capacity instead (see retireOldestLane), and a capacity refusal
// is exactly the per-attempt failure errLaneJoinCapacity carries back here.
// Past that window no role or seniority shields a lane from a newer rescue.
func (c *Client) raceRescueAttempts(ctx context.Context, flow *multipathFlow, attempts []rescueAttempt) (*mpLane, int, error) {
	raceCtx, cancel := context.WithCancel(ctx)
	defer cancel()
	// As in openRecoveryLane: a rescue handshake must not outlive its flow.
	go func() {
		select {
		case <-flow.doneChan():
			cancel()
		case <-raceCtx.Done():
		}
	}()
	type result struct {
		lane    *mpLane
		attempt int
		err     error
	}
	results := make(chan result, len(attempts))
	for i, attempt := range attempts {
		c.metrics.LaneRescueAttempt()
		go func(i int, attempt rescueAttempt) {
			lane, err := attempt(raceCtx)
			if err == nil && lane != nil && raceCtx.Err() != nil {
				// Finished after the race was decided: close it here rather
				// than trusting the drain to see it.
				_ = lane.fc.Close()
				lane = nil
				err = context.Canceled
			}
			results <- result{lane: lane, attempt: i, err: err}
		}(i, attempt)
	}
	drain := func(pending int) {
		for ; pending > 0; pending-- {
			if loser := <-results; loser.lane != nil {
				_ = loser.lane.fc.Close()
			}
		}
	}
	pending := len(attempts)
	var firstErr error
	for pending > 0 {
		r := <-results
		pending--
		if r.err == nil && r.lane != nil {
			cancel()
			go drain(pending)
			c.metrics.LaneRescueWin(r.attempt)
			return r.lane, r.attempt, nil
		}
		if errors.Is(r.err, errLaneJoinRejected) && (!errors.Is(r.err, errLaneJoinTCPMode) || r.attempt == 0) {
			// The peer answered, and its answer does not change between
			// attempts: a session identifier is random and is never reissued.
			// Cancel the rest of the round rather than learn it twice more.
			// A sprayed attempt's TCP-mode refusal is the one exemption: that
			// answer is actionable, and only attempt zero can act on it with a
			// TCP commit, so it must not cancel the round attempt zero is
			// still running. When attempt zero itself reports it there is no
			// commit to wait for, and the round ends like any rejection.
			cancel()
			go drain(pending)
			return nil, -1, r.err
		}
		if firstErr == nil {
			firstErr = r.err
		}
	}
	if firstErr == nil {
		firstErr = errors.New("lane rescue ran no attempts")
	}
	return nil, -1, firstErr
}

// openRecoveryLane dials one replacement lane following the established
// recovery strategy and returns it uninstalled; the parallel rescue installs
// only the round's winner. The strategy itself is unchanged: the pooled
// control generation first for a pooled flow, the bounded QUIC window and
// single committed TCP JOIN for AUTO, the plain join otherwise.
func (c *Client) openRecoveryLane(ctx context.Context, flow *multipathFlow, sessionID [16]byte, flowID uint64) (*mpLane, error) {
	// A replacement handshake must not outlive its logical flow. Without this
	// bound, a dead UDP flow can keep dialing a session that the server has
	// already unregistered after the application completed.
	recoveryCtx, cancel := context.WithCancel(ctx)
	defer cancel()
	if flow.finSent.Load() && flow.remoteFinSeen.Load() {
		return nil, context.Canceled
	}
	go func() {
		select {
		case <-flow.doneChan():
			cancel()
		case <-recoveryCtx.Done():
		}
	}()
	laneID, err := flow.allocateJoinID()
	if err != nil {
		return nil, err
	}
	var lane *mpLane
	// A flow opened on the shared control pool should be repaired on the next
	// shared generation first. Every affected flow waits on the same one dial,
	// then sends an independent authenticated JOIN stream; the logical flow and
	// its destination socket remain intact.
	if flow.reserveControlLane && c.cfg.EnableQUICPool {
		quicCtx := recoveryCtx
		var quicCancel context.CancelFunc
		if c.cfg.Transport == TransportAuto {
			// Recovery is sequential rather than a transport race. A TCP JOIN is
			// an irreversible server-side handoff which retires QUIC, so racing
			// both JOINs could let the nominal loser change the flow underneath
			// the winner. Give the coalesced QUIC generation a bounded window,
			// then commit exactly once to TCP.
			quicCtx, quicCancel = context.WithTimeout(recoveryCtx, c.fallbackGrace())
		}
		lane, err = c.openControlPoolJoinLane(quicCtx, sessionID, flowID, laneID)
		if quicCancel != nil {
			quicCancel()
		}
		if err == nil {
			return lane, nil
		}
		if recoveryCtx.Err() != nil || flow.doneChanClosed() {
			return nil, context.Canceled
		}
		if errors.Is(err, errLaneJoinCapacity) {
			// The peer is alive and at its lane ceiling, which in a rescue
			// race usually means a sibling attempt already holds the lane.
			// Falling back here -- an ordinary QUIC join, or the AUTO TCP
			// commit -- would burn another handshake on an answer that
			// cannot change, and could even hand the flow to TCP while a
			// QUIC sibling wins.
			//
			// The suppression ends once the answer repeats: consecutive
			// capacity refusals with no successful round between them mark a
			// wedged admission slot rather than a lost race, and then the
			// AUTO TCP commit is the flow's remaining escape. A
			// configuration-pinned QUIC client has no TCP commit to make and
			// keeps the transient reading to the last.
			if c.cfg.Transport != TransportAuto || flow.laneCapacityRefusals() < laneJoinCapacityTCPCommit-1 {
				return nil, err
			}
		}
		if errors.Is(err, errLaneJoinTCPMode) {
			// The peer says the flow already lives on TCP fallback. An AUTO
			// client commits at once rather than spending the replacement
			// grace on QUIC retries the peer has ruled out; a
			// configuration-pinned QUIC client has no TCP commit to make, and
			// the refusal propagates as the permanent answer it is.
			if c.cfg.Transport != TransportAuto {
				return nil, err
			}
			lane, err = c.openJoinLane(recoveryCtx, TransportTCP, sessionID, flowID, laneID)
		} else if c.cfg.Transport == TransportQUIC {
			// Protocol-v1 development peers predating control-role JOINs reject the flag.
			// One ordinary QUIC join preserves rolling-upgrade recovery; a new
			// peer which genuinely lost the session rejects this one as well.
			lane, err = c.openJoinLane(recoveryCtx, TransportQUIC, sessionID, flowID, laneID)
		} else {
			// The fallback is counted where the TCP lane is installed, not
			// here: in a parallel rescue round this commit races sprayed
			// QUIC dials, and when one of those wins the flow never touches
			// TCP at all.
			c.cfg.Logger.Debug("shared QUIC generation recovery unavailable; committing flow to TCP",
				"flow", flowID, "error", err)
			lane, err = c.openJoinLane(recoveryCtx, TransportTCP, sessionID, flowID, laneID)
		}
	} else {
		kind := TransportQUIC
		if c.cfg.Transport == TransportAuto {
			// An unpooled flow has no shared generation to reuse. Its one safe
			// recovery is the existing authenticated TCP handoff.
			kind = TransportTCP
		}
		lane, err = c.openJoinLane(recoveryCtx, kind, sessionID, flowID, laneID)
	}
	if err != nil {
		if recoveryCtx.Err() != nil || flow.doneChanClosed() {
			return nil, context.Canceled
		}
		return nil, err
	}
	return lane, nil
}

func (c *Client) installRecoveryLane(flow *multipathFlow, lane *mpLane) error {
	if err := flow.addLane(lane); err != nil {
		_ = lane.fc.Close()
		return err
	}
	if lane.kind == TransportTCP {
		// The handoff is real only now: the lane won its rescue round and
		// will actually carry the flow.
		c.metrics.Fallback()
		if c.cfg.TCPFallbackLanes > 1 {
			flow.tcpStriping.Store(lane.tcpStriping)
		}
	}
	c.metrics.LaneReplacement()
	return nil
}

func (c *Client) chooseAuthenticatedLane(ctx context.Context) (*authenticatedLane, error) {
	switch c.cfg.Transport {
	case TransportTCP:
		return c.dialAuthenticatedCandidate(ctx, TransportTCP)
	case TransportQUIC:
		return c.dialAuthenticatedCandidate(ctx, TransportQUIC)
	case TransportAuto:
		if !c.udpHealth.allow(time.Now()) {
			c.metrics.Fallback()
			return c.dialAuthenticatedCandidate(ctx, TransportTCP)
		}
		return c.raceUDPAndTCP(ctx)
	default:
		return nil, fmt.Errorf("unsupported transport %q", c.cfg.Transport)
	}
}

func (c *Client) dialAuthenticatedCandidate(ctx context.Context, kind TransportKind) (*authenticatedLane, error) {
	if c.dialAuthenticatedLaneForTest != nil {
		return c.dialAuthenticatedLaneForTest(ctx, kind)
	}
	return c.dialAuthenticatedLane(ctx, kind)
}

type laneResult struct {
	lane *authenticatedLane
	err  error
}

func (c *Client) raceUDPAndTCP(ctx context.Context) (*authenticatedLane, error) {
	raceCtx, cancel := context.WithCancel(ctx)
	keepQUICAttempt := false
	defer func() {
		if !keepQUICAttempt {
			cancel()
		}
	}()
	quicResult := make(chan laneResult, 1)
	go func() {
		lane, err := c.dialAuthenticatedCandidate(raceCtx, TransportQUIC)
		quicResult <- laneResult{lane: lane, err: err}
	}()
	timer := time.NewTimer(c.cfg.FallbackDelay)
	defer timer.Stop()
	select {
	case result := <-quicResult:
		if result.err == nil {
			c.udpHealth.observe(quicPathAvailable, time.Now())
			return result.lane, nil
		}
		if ctx.Err() != nil {
			return nil, ctx.Err()
		}
		tcpLane, tcpErr := c.dialAuthenticatedCandidate(ctx, TransportTCP)
		tcpEvidence := quicPathNeutral
		if tcpErr == nil {
			tcpEvidence = quicPathAvailable
		}
		c.observeUDPPath(differentialQUICPathEvidence(classifyQUICPathEvidence(result.err), tcpEvidence), result.err)
		c.metrics.Fallback()
		if tcpErr != nil {
			c.reportEndpointTransportRaceFailure(result.err, tcpErr)
		}
		return tcpLane, tcpErr
	case <-timer.C:
	case <-ctx.Done():
		closeLateLane(quicResult)
		return nil, ctx.Err()
	}

	tcpResult := make(chan laneResult, 1)
	go func() {
		lane, err := c.dialAuthenticatedCandidate(raceCtx, TransportTCP)
		tcpResult <- laneResult{lane: lane, err: err}
	}()
	var quicErr, tcpErr error
	var tcpReady *authenticatedLane
	var standbyTimer *time.Timer
	var standbyC <-chan time.Time
	defer func() {
		if standbyTimer != nil {
			standbyTimer.Stop()
		}
	}()
	quicEvidence := quicPathNeutral
	for quicResult != nil || tcpResult != nil {
		select {
		case result := <-quicResult:
			quicResult = nil
			if result.err == nil {
				c.udpHealth.observe(quicPathAvailable, time.Now())
				cancel()
				closeAuthenticatedLane(tcpReady)
				closeLateLane(tcpResult)
				return result.lane, nil
			}
			quicErr = result.err
			quicEvidence = classifyQUICPathEvidence(result.err)
			if tcpReady != nil {
				c.observeUDPPath(differentialQUICPathEvidence(quicEvidence, quicPathAvailable), quicErr)
				c.metrics.Fallback()
				cancel()
				return tcpReady, nil
			}
		case result := <-tcpResult:
			tcpResult = nil
			if result.err == nil {
				if quicResult != nil {
					tcpReady = result.lane
					standbyTimer = time.NewTimer(c.fallbackGrace())
					standbyC = standbyTimer.C
					continue
				}
				c.observeUDPPath(differentialQUICPathEvidence(quicEvidence, quicPathAvailable), quicErr)
				c.metrics.Fallback()
				cancel()
				return result.lane, nil
			}
			tcpErr = result.err
		case <-standbyC:
			standbyC = nil
			c.metrics.Fallback()
			c.cfg.Logger.Debug("QUIC preference window elapsed; using TCP without penalizing UDP health",
				"endpoint", c.cfg.RemoteAddr, "grace", c.fallbackGrace())
			if c.cfg.EnableQUICPool {
				// The current request has its bounded answer, while the one
				// coalesced pool dial keeps running. Its eventual success
				// restores QUIC for later flows; an explicit failure is the
				// conservative evidence the cooldown requires.
				keepQUICAttempt = true
				c.finishLatePooledQUIC(quicResult, cancel)
			} else {
				cancel()
				closeLateLane(quicResult)
			}
			return tcpReady, nil
		case <-ctx.Done():
			closeAuthenticatedLane(tcpReady)
			closeLateLane(quicResult)
			closeLateLane(tcpResult)
			return nil, ctx.Err()
		}
	}
	c.reportEndpointTransportRaceFailure(quicErr, tcpErr)
	return nil, fmt.Errorf("QUIC failed (%v); TCP fallback failed (%v)", quicErr, tcpErr)
}

func (c *Client) finishLatePooledQUIC(ch <-chan laneResult, cancel context.CancelFunc) {
	go func() {
		defer cancel()
		result := <-ch
		if result.err == nil {
			c.udpHealth.observe(quicPathAvailable, time.Now())
		} else {
			c.observeUDPPath(
				differentialQUICPathEvidence(classifyQUICPathEvidence(result.err), quicPathAvailable),
				result.err,
			)
		}
		closeAuthenticatedLane(result.lane)
	}()
}

func closeLateLane(ch <-chan laneResult) {
	if ch == nil {
		return
	}
	go func() {
		result := <-ch
		closeAuthenticatedLane(result.lane)
	}()
}

func closeAuthenticatedLane(lane *authenticatedLane) {
	if lane != nil && lane.fc != nil {
		_ = lane.fc.Close()
	}
}

// classifierConfig is the flow-classification policy this client's profile
// asks for. It is read per flow rather than cached so that a profile chosen at
// startup is visible in every flow the process creates, including ones opened
// long afterwards.
func (c *Client) classifierConfig() classifier.Config {
	if c.cfg.Profile.Classifier.BulkBytes == 0 {
		return profile.Default().Classifier
	}
	return c.cfg.Profile.Classifier
}

// declareClass asks the local capture agent what opened this connection, and
// applies whatever class the profile declares for it.
//
// It runs on the accept path, so everything about it is bounded and optional:
// no agent, an agent that has forgotten the flow, a process that exited, or a
// profile with no matching hint all leave the flow exactly as it would have
// been. What it buys is the first second, which is the window the classifier
// cannot cover and which a request shorter than it spends entirely inside.
func (c *Client) declareClass(ctx context.Context, inner net.Conn, flow *multipathFlow) {
	if !c.flowMeta.Enabled() || len(c.cfg.Profile.ClassHints) == 0 {
		return
	}
	port, ok := flowmeta.SourcePortOf(inner.RemoteAddr())
	if !ok {
		return
	}
	proc, err := c.flowMeta.BySourcePort(ctx, port)
	if err != nil {
		// A lookup failure is not a flow failure. It is logged at debug
		// because on a host with no agent it would otherwise be logged for
		// every connection.
		c.cfg.Logger.Debug("flow attribution unavailable", "error", err, "source_port", port)
		return
	}
	identity := proc.Identity()
	if identity == "" {
		return
	}
	class, ok := c.cfg.Profile.HintedClass(identity)
	if !ok {
		c.cfg.Logger.Debug("flow attributed with no matching hint", "identity", identity)
		return
	}
	flow.classifier.Declare(class)
	flow.class.Store(uint32(protocol.Class(class)))
	// Counted like any other transition. A declared class never passes through
	// Observe, so without this the whole mechanism is invisible in telemetry:
	// an operator reading class_transitions would see zero and conclude the
	// hints never fired, which is indistinguishable from them not being
	// configured.
	if c.metrics != nil {
		c.metrics.ClassTransition(int(class))
	}
	c.cfg.Logger.Debug("flow class declared from attribution",
		"identity", identity, "class", class)
}
