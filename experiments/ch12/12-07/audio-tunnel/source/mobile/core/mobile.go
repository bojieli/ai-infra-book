package mobilecore

import (
	"bytes"
	"context"
	"crypto/x509"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net"
	"net/netip"
	"runtime"
	"runtime/debug"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"time"

	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/metrics"
	"github.com/bojieli/queqiao/internal/pep"
	"github.com/bojieli/queqiao/internal/routerule"
	"github.com/bojieli/queqiao/internal/socks5"
)

const (
	StateStopped  = "stopped"
	StateStarting = "starting"
	StateRunning  = "running"
	StateStopping = "stopping"
	StateFailed   = "failed"
)

// Protector is implemented by Android's VpnService. Protect must synchronously
// exempt fd from the VPN before the socket is bound or connected.
type Protector interface {
	Protect(fd int64) bool
}

// Observer receives serialized lifecycle and diagnostic callbacks. Callbacks
// can arrive on arbitrary Go threads; platform implementations must marshal UI
// changes onto their main thread.
type Observer interface {
	OnStateChanged(state string)
	OnLog(level, message string)
	// OnProfileUpdated must durably replace the platform's encrypted profile.
	// Returning false leaves the current in-memory certificate active and
	// causes renewal to be retried on the next maintenance interval.
	OnProfileUpdated(profileJSON string) bool
}

// Session owns exactly one mobile tunnel. A Session may be restarted after it
// has fully stopped, but Start and Stop are serialized and idempotent.
type Session struct {
	opMu      sync.Mutex
	mu        sync.Mutex
	state     string
	observer  Observer
	protector Protector
	cancel    context.CancelFunc
	listener  net.Listener
	packet    packetEngine
	client    *pep.Client
	metrics   *metrics.Registry
	done      chan struct{}
	runErr    error
	resources mobileResourceLimits
	mode      string
	// Copied into the maintenance goroutine when a run starts. Tests shorten
	// these on their own Session; keeping them per-session prevents one test
	// from changing the clock under a still-stopping session.
	identityMaintenanceInterval time.Duration
	identityRenewalLead         time.Duration

	// routing is the rule list and country set this session will start with.
	// They are set before Start and read when the packet engine is built, so a
	// running tunnel is never re-pointed underneath its own flows: changing
	// rules is a reconnect, which is what makes "what is this flow doing"
	// answerable from the rules that were loaded when it opened.
	ruleSet     atomic.Pointer[routerule.Set]
	countrySets sync.Map // code -> *routerule.Packed
}

func NewSession(observer Observer, protector Protector) *Session {
	return &Session{
		state:                       StateStopped,
		observer:                    observer,
		protector:                   protector,
		identityMaintenanceInterval: defaultIdentityMaintenanceInterval,
		identityRenewalLead:         defaultIdentityRenewalLead,
	}
}

// Start activates a full-device tunnel over a platform-provided TUN descriptor.
// packetOffset is normally 0; 4 is supported for callers that already own an
// Apple utun descriptor, though StartPacketFlow is the public-API iOS path.
func (s *Session) Start(profileJSON string, tunFD, packetOffset, mtu int64, requireSocketProtection bool) error {
	s.opMu.Lock()
	defer s.opMu.Unlock()
	if tunFD < 0 || packetOffset < 0 || packetOffset > 4 || mtu < 0 || mtu > maximumMTU {
		return errors.New("invalid tunnel descriptor configuration")
	}
	limits := androidResourceLimits
	return s.start(sessionOptions{
		profileJSON:             profileJSON,
		requireSocketProtection: requireSocketProtection,
		limits:                  limits,
		listenAddr:              privateListenAddr,
		mode:                    ModeTunnel,
		makePacketEngine: func(ctx context.Context, proxy socksClient, log func(string, string)) (packetEngine, error) {
			stack, err := newPacketStack(ctx, int(tunFD), int(packetOffset), int(mtu), limits.maxSessions, proxy, log)
			if err != nil {
				return nil, err
			}
			stack.useRules(s.boundRules())
			return stack, nil
		},
	})
}

// StartPacketFlow activates an iOS tunnel over NEPacketTunnelFlow callbacks.
// It avoids private utun descriptor access and takes ownership of packetIO
// after the packet engine has been created successfully.
func (s *Session) StartPacketFlow(profileJSON string, packetIO PacketIO, mtu int64) error {
	s.opMu.Lock()
	defer s.opMu.Unlock()
	if packetIO == nil || mtu < 0 || mtu > maximumMTU {
		return errors.New("invalid packet-flow configuration")
	}
	limits := iosResourceLimits
	return s.start(sessionOptions{
		profileJSON: profileJSON,
		limits:      limits,
		listenAddr:  privateListenAddr,
		mode:        ModeTunnel,
		makePacketEngine: func(ctx context.Context, proxy socksClient, log func(string, string)) (packetEngine, error) {
			stack, err := newPacketStackWithDevice(ctx, &callbackPacketDevice{packetIO: packetIO}, 0, int(mtu), limits.maxSessions, proxy, log)
			if err != nil {
				return nil, err
			}
			stack.useRules(s.boundRules())
			return stack, nil
		},
	})
}

// StartProxy activates export mode: a SOCKS5 listener on loopback and no packet
// tunnel at all. Another VPN app on the same device — v2rayNG, mihomo, sing-box
// — owns the TUN and the routing rules and treats this listener as one outbound
// among many, which is the same role Queqiao plays behind Clash on the desktop.
//
// listenAddr must be a loopback literal. On Android every installed app shares
// loopback, so username and password are mandatory: they are the only thing
// standing between this listener and any other app on the device. There is no
// Protector here, because without a VpnService of its own the app cannot call
// protect() — the consumer must instead exempt Queqiao's UID from its tunnel,
// or Queqiao's own uplink is captured by it and the path loops.
func (s *Session) StartProxy(profileJSON, listenAddr, username, password string) error {
	s.opMu.Lock()
	defer s.opMu.Unlock()
	auth := &socks5.Credentials{Username: username, Password: password}
	if err := auth.Validate(); err != nil {
		return err
	}
	return s.start(sessionOptions{
		profileJSON: profileJSON,
		limits:      androidResourceLimits,
		listenAddr:  listenAddr,
		auth:        auth,
		mode:        ModeProxy,
		makePacketEngine: func(context.Context, socksClient, func(string, string)) (packetEngine, error) {
			return nullPacketEngine{}, nil
		},
	})
}

// packetEngine is the part of a session that turns tunnel packets into SOCKS
// requests. Export mode has no tunnel and therefore no engine, so the lifecycle
// below is written against this interface rather than being made conditional in
// half a dozen places.
type packetEngine interface {
	start()
	Close() error
	metrics() any
	// done fires when the engine stops on its own. A session whose engine dies
	// must fail rather than keep a listener open with nothing behind it.
	done() <-chan struct{}
}

// nullPacketEngine is the export-mode engine. done never fires, so run blocks
// on the client alone, and metrics reports nothing rather than zeroes that
// would read as an idle tunnel.
type nullPacketEngine struct{}

func (nullPacketEngine) start()                {}
func (nullPacketEngine) Close() error          { return nil }
func (nullPacketEngine) metrics() any          { return nil }
func (nullPacketEngine) done() <-chan struct{} { return nil }

type packetStackFactory func(context.Context, socksClient, func(string, string)) (packetEngine, error)

// sessionOptions is what the exported entry points agree on before the shared
// startup path runs. It is a struct rather than a parameter list because the
// tunnel and export products differ in five independent ways, and a positional
// call would make it easy to pair, say, export mode's credentials with a real
// packet stack.
type sessionOptions struct {
	profileJSON             string
	requireSocketProtection bool
	limits                  mobileResourceLimits
	// listenAddr must be loopback; see validateLoopbackListenAddr.
	listenAddr string
	// auth is nil for the tunnel products, whose listener is on an ephemeral
	// loopback port that only this process knows.
	auth             *socks5.Credentials
	mode             string
	makePacketEngine packetStackFactory
}

// SetRoutingRules loads the rule list this session will start with, and reports
// what it made of it.
//
// The report is JSON: the number of rules loaded and every line that did not
// become one, with its number and the reason. A client is expected to show that
// rather than swallow it -- a rule list is somebody stating where their traffic
// may and may not go, and a line silently dropped is that statement not being
// enforced for as long as the file lives.
//
// An empty list clears the rules, which returns the tunnel to carrying
// everything. That is also what happens if this is never called.
func (s *Session) SetRoutingRules(text string) string {
	set, problems := routerule.Parse(text)
	if set.Len() == 0 && len(problems) == 0 {
		s.ruleSet.Store(nil)
	} else {
		s.ruleSet.Store(set)
	}
	report := struct {
		Loaded   int      `json:"loaded"`
		Problems []string `json:"problems,omitempty"`
	}{Loaded: set.Len()}
	for _, problem := range problems {
		report.Problems = append(report.Problems, problem.String())
	}
	encoded, err := json.Marshal(report)
	if err != nil {
		return `{"loaded":0,"problems":["could not encode the report"]}`
	}
	return string(encoded)
}

// SetCountrySet hands the core a packed country set for GEOIP rules to consult.
//
// The clients own the file -- it ships inside the iOS extension bundle and the
// Android assets -- so the bytes come in from there rather than being read
// here. A set that will not load is refused with a reason instead of being
// half-installed: a GEOIP rule with nothing behind it decides nothing, and an
// operator who thinks their China rule is live when it is not has the same
// problem this feature exists to remove.
func (s *Session) SetCountrySet(code string, blob []byte) error {
	packed, err := routerule.LoadPacked(code, blob)
	if err != nil {
		return fmt.Errorf("country set %s: %w", code, err)
	}
	s.countrySets.Store(packed.Code(), packed)
	return nil
}

// RoutingRuleCount reports how many rules are loaded, so a screen can say so
// without holding the list.
func (s *Session) RoutingRuleCount() int {
	if set := s.ruleSet.Load(); set != nil {
		return set.Len()
	}
	return 0
}

// boundRules pairs the loaded list with the country sets it may consult. It is
// called once, when the packet engine is built.
func (s *Session) boundRules() *routerule.Set {
	set := s.ruleSet.Load()
	if set == nil {
		return nil
	}
	return set.WithCountries(sessionCountries{session: s})
}

// sessionCountries answers a GEOIP rule from whichever sets the client
// installed. A code with no set installed answers false, which leaves the rule
// deciding nothing rather than deciding wrongly.
type sessionCountries struct{ session *Session }

func (c sessionCountries) Contains(code string, addr netip.Addr) bool {
	value, ok := c.session.countrySets.Load(strings.ToUpper(code))
	if !ok {
		return false
	}
	packed, ok := value.(*routerule.Packed)
	return ok && packed.Contains(code, addr)
}

// privateListenAddr is the tunnel products' listener: loopback, kernel-assigned
// port, never advertised. The packet engine learns the port from the listener.
const privateListenAddr = "127.0.0.1:0"

// Session modes, reported by MetricsJSON so a UI can tell a tunnel with no
// traffic apart from an export listener that has no packet counters by design.
const (
	ModeTunnel = "tunnel"
	ModeProxy  = "proxy"
)

// validateLoopbackListenAddr enforces in code the invariant that
// docs/KNOWN-LIMITATIONS.md states in prose: the SOCKS listener is never
// reachable off-host. A hostname is rejected rather than resolved, because
// resolution depends on state this process does not control and "localhost"
// has been made to point elsewhere before.
func validateLoopbackListenAddr(address string) error {
	host, port, err := net.SplitHostPort(address)
	if err != nil {
		return fmt.Errorf("invalid SOCKS listen address %q: %w", address, err)
	}
	ip := net.ParseIP(host)
	if ip == nil {
		return fmt.Errorf("SOCKS listen address %q must use an IP literal, not a hostname", address)
	}
	if !ip.IsLoopback() {
		return fmt.Errorf("SOCKS listen address %q must be on loopback", address)
	}
	number, err := net.LookupPort("tcp", port)
	if err != nil {
		return fmt.Errorf("invalid SOCKS listen port in %q: %w", address, err)
	}
	// Ports below 1024 are unreachable to an unprivileged Android app and a
	// request for one is a configuration mistake, not something to discover at
	// bind time as a permission error.
	if number != 0 && number < 1024 {
		return fmt.Errorf("SOCKS listen port %d is privileged", number)
	}
	return nil
}

func (s *Session) start(opts sessionOptions) error {
	if err := validateLoopbackListenAddr(opts.listenAddr); err != nil {
		return err
	}
	limits := opts.limits
	s.mu.Lock()
	if s.state != StateStopped {
		state := s.state
		s.mu.Unlock()
		return fmt.Errorf("cannot start tunnel while state is %s", state)
	}
	if opts.requireSocketProtection && s.protector == nil {
		s.mu.Unlock()
		return errors.New("socket protection is required for this tunnel")
	}
	s.state = StateStarting
	s.runErr = nil
	s.mu.Unlock()
	s.notifyState(StateStarting)
	applyRuntimeLimits(limits)

	profile, err := decodeProfile(opts.profileJSON)
	if err != nil {
		return s.startFailed(err)
	}
	credentials, err := profile.Credentials()
	if err != nil {
		return s.startFailed(err)
	}
	listener, err := net.Listen("tcp", opts.listenAddr)
	if err != nil {
		return s.startFailed(fmt.Errorf("open SOCKS listener on %s: %w", opts.listenAddr, err))
	}
	ctx, cancel := context.WithCancel(context.Background())
	registry := metrics.New()
	logger := slog.New(newObserverHandler(s.observer, slog.LevelInfo))
	client, err := pep.NewClient(pep.ClientConfig{
		// Leave source-address selection to the platform. Android's socket
		// protector must run before bind/connect; resolving and binding an
		// "auto" interface here would bypass that contract and can select the
		// VPN itself after its default route is installed.
		ListenAddr: listener.Addr().String(), RemoteAddr: profile.Endpoint, LocalAddress: "",
		SocketControl: s.socketControl(opts.requireSocketProtection), SOCKSAuth: opts.auth,
		Credentials: credentials,
		ChunkSize:   limits.chunkSize,
		DialTimeout: 10 * time.Second, HandshakeTimeout: 30 * time.Second,
		FlowIdleTimeout: 10 * time.Minute, FlowMaxLifetime: 6 * time.Hour,
		MaxSessions: limits.maxSessions, MaxPendingOpens: limits.maxPendingOpens, Transport: pep.TransportAuto,
		TCPFallbackLanes: 0, EnableQUICPool: true, WaitForOpenAcknowledgement: false,
		UDPOnStream: false, Congestion: pep.CongestionErasure,
		AdaptiveMinBytesSec: 64 * 1024, AdaptiveMaxBytesSec: 200 * 1024 * 1024,
		FallbackDelay: 300 * time.Millisecond, FallbackGrace: 2 * time.Second,
		UDPFailureThreshold: 3, UDPCooldown: 30 * time.Second,
		StreamReceiveWindow: limits.streamWindow, ConnectionReceiveWindow: limits.connectionWindow,
		MaxStreamReceiveWindow: limits.streamWindow, MaxConnectionReceiveWindow: limits.connectionWindow,
		MaxIncomingStreams: limits.maxIncomingStreams, MemoryLimits: &limits.memory,
		Metrics: registry, Logger: logger,
	})
	if err != nil {
		cancel()
		_ = listener.Close()
		return s.startFailed(err)
	}
	packet, err := opts.makePacketEngine(ctx,
		socksClient{address: listener.Addr().String(), handshakeTimeout: 10 * time.Second}, s.notifyLog)
	if err != nil {
		cancel()
		_ = listener.Close()
		return s.startFailed(err)
	}
	// The in-process packet engine dials the listener without credentials, so a
	// real engine behind an authenticating listener would deadlock every flow at
	// the greeting. The two are set together by construction above; this keeps a
	// future entry point from separating them.
	if _, exported := packet.(nullPacketEngine); opts.auth != nil && !exported {
		cancel()
		_ = listener.Close()
		_ = packet.Close()
		return s.startFailed(errors.New("SOCKS authentication cannot be combined with a packet engine"))
	}
	done := make(chan struct{})
	s.mu.Lock()
	if s.state != StateStarting {
		s.mu.Unlock()
		cancel()
		_ = listener.Close()
		_ = packet.Close()
		return errors.New("tunnel start was interrupted")
	}
	s.cancel, s.listener, s.packet, s.client, s.metrics, s.done = cancel, listener, packet, client, registry, done
	s.resources, s.mode = limits, opts.mode
	s.state = StateRunning
	s.mu.Unlock()

	packet.start()
	go s.maintainIdentity(
		ctx,
		profile,
		client,
		s.identityMaintenanceInterval,
		s.identityRenewalLead,
	)
	go s.run(ctx, cancel, client, listener, packet, done)
	s.notifyState(StateRunning)
	return nil
}

// How often the enrolled identity is checked, and how far ahead of expiry a
// renewal is attempted.
//
// NewSession copies these into each session. The lifecycle test can therefore
// drive a real renewal quickly without changing timing under another session's
// goroutine.
const (
	defaultIdentityMaintenanceInterval = time.Hour
	defaultIdentityRenewalLead         = 7 * 24 * time.Hour
)

func (s *Session) maintainIdentity(
	ctx context.Context,
	profile identity.ClientProfile,
	client *pep.Client,
	maintenanceInterval time.Duration,
	renewalLead time.Duration,
) {
	ticker := time.NewTicker(maintenanceInterval)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
		case <-ctx.Done():
			return
		}
		needsRenewal, err := profile.NeedsRenewal(time.Now(), renewalLead)
		if err != nil {
			s.notifyLog("error", fmt.Sprintf("check device identity lifetime: %v", err))
			continue
		}
		if !needsRenewal {
			continue
		}
		renewalContext, cancel := context.WithTimeout(ctx, 15*time.Second)
		renewed, err := identity.RenewProfile(renewalContext, profile, 15*time.Second)
		cancel()
		if err != nil {
			s.notifyLog("warning", fmt.Sprintf("automatic certificate renewal failed; will retry: %v", err))
			continue
		}
		credentials, err := renewed.Credentials()
		if err != nil {
			s.notifyLog("error", fmt.Sprintf("load renewed device identity: %v", err))
			continue
		}
		encoded, err := encodeJSON(renewed)
		if err != nil {
			s.notifyLog("error", fmt.Sprintf("encode renewed device identity: %v", err))
			continue
		}
		if !s.notifyProfileUpdated(encoded) {
			s.notifyLog("warning", "persist renewed device identity; will retry")
			continue
		}
		if err := client.UpdateCredentials(credentials); err != nil {
			s.notifyLog("error", fmt.Sprintf("activate renewed device identity: %v", err))
			continue
		}
		profile = renewed
		s.notifyLog("info", "device identity renewed")
	}
}

func (s *Session) run(ctx context.Context, cancel context.CancelFunc, client *pep.Client, listener net.Listener, packet packetEngine, done chan struct{}) {
	clientResult := make(chan error, 1)
	go func() { clientResult <- client.ServeListener(ctx, listener) }()
	var err error
	unexpected := false
	select {
	case err = <-clientResult:
		unexpected = ctx.Err() == nil
		if err == nil && unexpected {
			err = errors.New("queqiao client stopped unexpectedly")
		}
	case <-packet.done():
		unexpected = ctx.Err() == nil
		if unexpected {
			err = errors.New("packet engine stopped unexpectedly")
		}
		cancel()
		_ = listener.Close()
		clientErr := <-clientResult
		if err == nil {
			err = clientErr
		}
	}
	cancel()
	_ = listener.Close()
	packetErr := packet.Close()
	debug.FreeOSMemory()
	if packetErr != nil && unexpected {
		err = packetErr
	}
	if err != nil && unexpected {
		s.notifyLog("error", fmt.Sprintf("Queqiao client stopped: %v", err))
	}
	s.mu.Lock()
	if err != nil && unexpected {
		s.runErr = err
		s.state = StateFailed
	} else {
		s.state = StateStopped
	}
	state := s.state
	s.cancel, s.listener, s.packet, s.client, s.done = nil, nil, nil, nil, nil
	s.mu.Unlock()
	close(done)
	s.notifyState(state)
}

func (s *Session) Stop() error {
	s.opMu.Lock()
	defer s.opMu.Unlock()
	s.mu.Lock()
	switch s.state {
	case StateStopped:
		err := s.runErr
		s.mu.Unlock()
		return err
	case StateFailed:
		err := s.runErr
		s.state = StateStopped
		s.mu.Unlock()
		s.notifyState(StateStopped)
		return err
	case StateStopping:
		done := s.done
		s.mu.Unlock()
		if done != nil {
			<-done
		}
		return s.lastError()
	default:
		s.state = StateStopping
		cancel, listener, done := s.cancel, s.listener, s.done
		s.mu.Unlock()
		s.notifyState(StateStopping)
		if cancel != nil {
			cancel()
		}
		if listener != nil {
			_ = listener.Close()
		}
		if done != nil {
			<-done
		}
		return s.lastError()
	}
}

// ListenAddress is the address the SOCKS listener actually bound, which export
// mode needs because the port is normally left for the kernel to choose and the
// consumer app has to be told the result. It is empty when nothing is running.
func (s *Session) ListenAddress() string {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.listener == nil {
		return ""
	}
	return s.listener.Addr().String()
}

func (s *Session) State() string {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.state
}

func (s *Session) MetricsJSON() string {
	s.mu.Lock()
	state, registry, packet, client, resources := s.state, s.metrics, s.packet, s.client, s.resources
	mode, listener := s.mode, s.listener
	s.mu.Unlock()
	if mode == "" {
		mode = ModeTunnel
	}
	listen := ""
	if listener != nil {
		listen = listener.Addr().String()
	}
	var transport any = struct{}{}
	if registry != nil {
		transport = registry.Snapshot()
	}
	var packets any = struct{}{}
	if packet != nil {
		if snapshot := packet.metrics(); snapshot != nil {
			packets = snapshot
		}
	}
	var memoryStats runtime.MemStats
	runtime.ReadMemStats(&memoryStats)
	var payload any = struct{}{}
	if client != nil {
		payload = client.MemoryStats()
	}
	encoded, err := json.Marshal(struct {
		Version int    `json:"version"`
		State   string `json:"state"`
		// Mode tells a UI whether the absent packet counters mean "idle" or
		// "this product has no packet engine".
		Mode      string `json:"mode"`
		Listen    string `json:"listen,omitempty"`
		Packets   any    `json:"packets"`
		Transport any    `json:"transport"`
		Memory    any    `json:"memory"`
	}{Version: 2, State: state, Mode: mode, Listen: listen, Packets: packets, Transport: transport, Memory: struct {
		Profile   string `json:"profile"`
		GoLimit   int64  `json:"go_limit_bytes"`
		HeapAlloc uint64 `json:"heap_alloc_bytes"`
		HeapInuse uint64 `json:"heap_inuse_bytes"`
		Payload   any    `json:"payload"`
	}{
		Profile: resources.name, GoLimit: resources.goMemoryLimit,
		HeapAlloc: memoryStats.HeapAlloc, HeapInuse: memoryStats.HeapInuse, Payload: payload,
	}})
	if err != nil {
		return `{"version":2,"state":"failed"}`
	}
	return string(encoded)
}

func (s *Session) startFailed(err error) error {
	s.mu.Lock()
	s.state, s.runErr = StateStopped, err
	s.mu.Unlock()
	s.notifyLog("error", err.Error())
	s.notifyState(StateStopped)
	return err
}

func (s *Session) lastError() error {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.runErr
}

func (s *Session) socketControl(required bool) func(string, string, syscall.RawConn) error {
	if !required {
		return nil
	}
	return func(_, _ string, raw syscall.RawConn) error {
		var protectionErr error
		err := raw.Control(func(fd uintptr) {
			defer func() {
				if recovered := recover(); recovered != nil {
					protectionErr = fmt.Errorf("socket protector panicked: %v", recovered)
				}
			}()
			// File descriptors are signed C ints on every supported mobile OS;
			// reject an invalid value before crossing gomobile's int64 boundary.
			if fd > uintptr(1<<31-1) {
				protectionErr = errors.New("platform returned an out-of-range socket descriptor")
				return
			}
			if s.protector == nil || !s.protector.Protect(int64(fd)) {
				protectionErr = errors.New("platform refused to exempt Queqiao socket from VPN")
			}
		})
		return errors.Join(err, protectionErr)
	}
}

func (s *Session) notifyState(state string) {
	if s.observer == nil {
		return
	}
	defer func() { _ = recover() }()
	s.observer.OnStateChanged(state)
}

func (s *Session) notifyLog(level, message string) {
	if s.observer == nil {
		return
	}
	defer func() { _ = recover() }()
	s.observer.OnLog(level, message)
}

func (s *Session) notifyProfileUpdated(profileJSON string) (stored bool) {
	if s.observer == nil {
		return false
	}
	defer func() {
		if recover() != nil {
			stored = false
		}
	}()
	return s.observer.OnProfileUpdated(profileJSON)
}

// ValidateInvitation validates structure, pin and expiry without consuming the
// one-time invitation token.
func ValidateInvitation(invitationURI string) error {
	_, err := identity.ParseInvitation(invitationURI, time.Now())
	return err
}

// PrepareEnrollment creates the permanent Ed25519 key before the one-time
// token is sent. The caller must persist the returned draft securely before
// invoking CompleteEnrollment so a lost response can be retried safely.
func PrepareEnrollment(invitationURI, deviceName string) (string, error) {
	invitation, err := identity.ParseInvitation(invitationURI, time.Now())
	if err != nil {
		return "", err
	}
	draft, err := identity.NewEnrollmentDraft(invitation, deviceName)
	if err != nil {
		return "", err
	}
	return encodeJSON(draft)
}

func CompleteEnrollment(draftJSON string) (string, error) {
	var draft identity.EnrollmentDraft
	if err := decodeStrictJSON(draftJSON, &draft); err != nil {
		return "", fmt.Errorf("decode enrollment draft: %w", err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	profile, err := draft.Enroll(ctx, 15*time.Second)
	if err != nil {
		return "", err
	}
	return encodeJSON(profile)
}

func ValidateProfile(profileJSON string) error {
	_, err := decodeProfile(profileJSON)
	return err
}

func ProfileSummaryJSON(profileJSON string) (string, error) {
	profile, err := decodeProfile(profileJSON)
	if err != nil {
		return "", err
	}
	credentials, err := profile.Credentials()
	if err != nil {
		return "", err
	}
	leaf, err := x509.ParseCertificate(credentials.Certificate.Certificate[0])
	if err != nil {
		return "", err
	}
	return encodeJSON(struct {
		Version           int    `json:"version"`
		Name              string `json:"name"`
		Endpoint          string `json:"endpoint"`
		ProviderID        string `json:"provider_id"`
		GatewayID         string `json:"gateway_id"`
		AccountID         string `json:"account_id"`
		DeviceID          string `json:"device_id"`
		DeviceName        string `json:"device_name"`
		CertificateExpiry string `json:"certificate_expiry"`
	}{
		Version: 1, Name: profile.Name, Endpoint: profile.Endpoint,
		ProviderID: profile.ProviderID, GatewayID: profile.GatewayID,
		AccountID: profile.AccountID, DeviceID: profile.DeviceID,
		DeviceName: profile.DeviceName, CertificateExpiry: leaf.NotAfter.UTC().Format(time.RFC3339),
	})
}

const (
	defaultProfileProbeTimeout = 10 * time.Second
	minimumProfileProbeTimeout = time.Second
	maximumProfileProbeTimeout = 30 * time.Second
)

// ProbeProfileJSON performs a destination-free, mutually authenticated
// provider test and returns its selected transport and end-to-end setup
// latency. When a platform VPN is active, the probe follows that platform's
// routing policy and may measure a path through the active tunnel.
func ProbeProfileJSON(profileJSON string, timeoutMillis int64) (string, error) {
	timeout, err := profileProbeTimeout(timeoutMillis)
	if err != nil {
		return "", err
	}
	profile, err := decodeProfile(profileJSON)
	if err != nil {
		return "", err
	}
	credentials, err := profile.Credentials()
	if err != nil {
		return "", err
	}
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	client, err := pep.NewClient(pep.ClientConfig{
		ListenAddr: "127.0.0.1:0", RemoteAddr: profile.Endpoint,
		Credentials: credentials, Transport: pep.TransportAuto,
		DialTimeout: timeout, HandshakeTimeout: timeout,
		FallbackDelay: 300 * time.Millisecond, FallbackGrace: 2 * time.Second,
		EnableQUICPool: false, Congestion: pep.CongestionErasure,
		Logger: logger,
	})
	if err != nil {
		return "", err
	}
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	result, err := client.Probe(ctx)
	if err != nil {
		if errors.Is(ctx.Err(), context.DeadlineExceeded) {
			return "", fmt.Errorf("provider connection test timed out after %s", timeout)
		}
		return "", fmt.Errorf("provider connection test failed: %w", err)
	}
	latencyMillis := result.Latency.Milliseconds()
	if latencyMillis < 1 {
		latencyMillis = 1
	}
	return encodeJSON(struct {
		Version   int    `json:"version"`
		Transport string `json:"transport"`
		LatencyMS int64  `json:"latency_ms"`
	}{Version: 1, Transport: string(result.Transport), LatencyMS: latencyMillis})
}

func profileProbeTimeout(milliseconds int64) (time.Duration, error) {
	if milliseconds == 0 {
		return defaultProfileProbeTimeout, nil
	}
	if milliseconds < minimumProfileProbeTimeout.Milliseconds() ||
		milliseconds > maximumProfileProbeTimeout.Milliseconds() {
		return 0, fmt.Errorf("profile probe timeout must be between %s and %s", minimumProfileProbeTimeout, maximumProfileProbeTimeout)
	}
	return time.Duration(milliseconds) * time.Millisecond, nil
}

// ProfileNeedsRenewal returns 1 when renewal is due and 0 otherwise. An integer
// avoids Objective-C's collision between a Go boolean result and the BOOL used
// by gomobile to report NSError success.
func ProfileNeedsRenewal(profileJSON string) (int64, error) {
	profile, err := decodeProfile(profileJSON)
	if err != nil {
		return 0, err
	}
	needsRenewal, err := profile.NeedsRenewal(time.Now(), 7*24*time.Hour)
	if err != nil || !needsRenewal {
		return 0, err
	}
	return 1, nil
}

// RenewProfile must be called before establishing the platform VPN so its
// renewal socket follows the ordinary system route.
func RenewProfile(profileJSON string) (string, error) {
	profile, err := decodeProfile(profileJSON)
	if err != nil {
		return "", err
	}
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	renewed, err := identity.RenewProfile(ctx, profile, 15*time.Second)
	if err != nil {
		return "", err
	}
	return encodeJSON(renewed)
}

func Version() string {
	if info, ok := debug.ReadBuildInfo(); ok && info.Main.Version != "" && info.Main.Version != "(devel)" {
		return info.Main.Version
	}
	return "development"
}

// ReleaseMemory asks the Go runtime to return idle pages to the operating
// system. Platform memory-pressure callbacks use it as a best-effort response;
// correctness never depends on it because retained payloads have hard budgets.
func ReleaseMemory() {
	debug.FreeOSMemory()
}

func decodeProfile(encoded string) (identity.ClientProfile, error) {
	var profile identity.ClientProfile
	if err := decodeStrictJSON(encoded, &profile); err != nil {
		return identity.ClientProfile{}, fmt.Errorf("decode client profile: %w", err)
	}
	if _, err := profile.Credentials(); err != nil {
		return identity.ClientProfile{}, err
	}
	return profile, nil
}

func decodeStrictJSON(encoded string, destination any) error {
	if len(encoded) == 0 || len(encoded) > 256*1024 {
		return errors.New("JSON document is empty or exceeds 256 KiB")
	}
	decoder := json.NewDecoder(bytes.NewBufferString(encoded))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(destination); err != nil {
		return err
	}
	var trailing any
	if err := decoder.Decode(&trailing); !errors.Is(err, io.EOF) {
		return errors.New("JSON document contains trailing data")
	}
	return nil
}

func encodeJSON(value any) (string, error) {
	encoded, err := json.Marshal(value)
	if err != nil {
		return "", err
	}
	return string(encoded), nil
}

type observerHandler struct {
	observer Observer
	level    slog.Level
}

func newObserverHandler(observer Observer, level slog.Level) *observerHandler {
	return &observerHandler{observer: observer, level: level}
}

func (h *observerHandler) Enabled(_ context.Context, level slog.Level) bool { return level >= h.level }

func (h *observerHandler) Handle(_ context.Context, record slog.Record) error {
	if h.observer == nil {
		return nil
	}
	message := record.Message
	record.Attrs(func(attr slog.Attr) bool {
		if attr.Key == "error" {
			message += ": " + attr.Value.String()
		}
		return true
	})
	defer func() { _ = recover() }()
	h.observer.OnLog(record.Level.String(), message)
	return nil
}

func (h *observerHandler) WithAttrs(_ []slog.Attr) slog.Handler { return h }
func (h *observerHandler) WithGroup(_ string) slog.Handler      { return h }
