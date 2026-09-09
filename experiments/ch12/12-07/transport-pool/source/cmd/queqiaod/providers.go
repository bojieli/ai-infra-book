package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net"
	"os"
	"os/signal"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/limiter"
	"github.com/bojieli/queqiao/internal/metrics"
	"github.com/bojieli/queqiao/internal/pep"
)

type providerManifest struct {
	Version   int                     `json:"version"`
	Providers []providerManifestEntry `json:"providers"`
}

type providerManifestEntry struct {
	Name    string `json:"name"`
	Profile string `json:"profile"`
	Listen  string `json:"listen"`
}

type providerClientConfig struct {
	name, profilePath, listen string
	profile                   identity.ClientProfile
}

type providerClientRuntime struct {
	config   providerClientConfig
	client   *pep.Client
	listener net.Listener
	logger   *slog.Logger
}

type providerServeResult struct {
	name string
	err  error
}

// decodeProviderManifest reads the version with a permissive pass before the
// strict one. Decoding strictly first would report an unrecognised field from a
// newer manifest as an unknown-field error, pointing the operator at a field
// name instead of at the version they need to downgrade or upgrade.
func decodeProviderManifest(data []byte) (providerManifest, error) {
	var envelope struct {
		Version int `json:"version"`
	}
	if err := json.Unmarshal(data, &envelope); err != nil {
		return providerManifest{}, fmt.Errorf("decode provider manifest: %w", err)
	}
	if envelope.Version != 1 {
		return providerManifest{}, fmt.Errorf("unsupported provider manifest version %d", envelope.Version)
	}
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.DisallowUnknownFields()
	var manifest providerManifest
	if err := decoder.Decode(&manifest); err != nil {
		return providerManifest{}, fmt.Errorf("decode provider manifest: %w", err)
	}
	var trailing any
	if err := decoder.Decode(&trailing); !errors.Is(err, io.EOF) {
		return providerManifest{}, errors.New("provider manifest contains trailing data")
	}
	return manifest, nil
}

func loadProviderClients(manifestPath string) ([]providerClientConfig, error) {
	manifestPath, err := filepath.Abs(manifestPath)
	if err != nil {
		return nil, fmt.Errorf("resolve provider manifest path: %w", err)
	}
	data, err := os.ReadFile(manifestPath)
	if err != nil {
		return nil, fmt.Errorf("read provider manifest %q: %w", manifestPath, err)
	}
	manifest, err := decodeProviderManifest(data)
	if err != nil {
		return nil, err
	}
	if len(manifest.Providers) == 0 {
		return nil, errors.New("provider manifest must contain at least one provider")
	}

	configs := make([]providerClientConfig, 0, len(manifest.Providers))
	names := make(map[string]struct{}, len(manifest.Providers))
	listeners := make(map[string]struct{}, len(manifest.Providers))
	profilePaths := make(map[string]struct{}, len(manifest.Providers))
	for i, entry := range manifest.Providers {
		if entry.Name == "" || entry.Name != strings.TrimSpace(entry.Name) || len(entry.Name) > 128 {
			return nil, fmt.Errorf("provider %d has an invalid name", i+1)
		}
		if _, exists := names[entry.Name]; exists {
			return nil, fmt.Errorf("duplicate provider name %q", entry.Name)
		}
		names[entry.Name] = struct{}{}

		listen, err := normalizeProviderListener(entry.Listen)
		if err != nil {
			return nil, fmt.Errorf("provider %q listen address: %w", entry.Name, err)
		}
		if _, exists := listeners[listen]; exists {
			return nil, fmt.Errorf("duplicate provider listener %q", listen)
		}
		listeners[listen] = struct{}{}

		if entry.Profile == "" {
			return nil, fmt.Errorf("provider %q profile path is required", entry.Name)
		}
		profilePath := entry.Profile
		if !filepath.IsAbs(profilePath) {
			profilePath = filepath.Join(filepath.Dir(manifestPath), profilePath)
		}
		// filepath.Abs cleans its result, so no separate Clean is needed.
		profilePath, err = filepath.Abs(profilePath)
		if err != nil {
			return nil, fmt.Errorf("resolve provider %q profile path: %w", entry.Name, err)
		}
		if _, exists := profilePaths[profilePath]; exists {
			return nil, fmt.Errorf("duplicate provider profile path %q", profilePath)
		}
		profilePaths[profilePath] = struct{}{}
		configs = append(configs, providerClientConfig{
			name: entry.Name, profilePath: profilePath, listen: listen,
		})
	}

	// Distinct paths can still name one enrolled device: a copied profile, a
	// symlink, a hard link. Running both would put two clients on a single
	// device certificate and leave two renewal loops racing to save one
	// identity into two files, so compare the loaded identity rather than the
	// file. Reading each profile once also closes the window a separate stat
	// pass would leave between the check and the read.
	devices := make(map[string]string, len(configs))
	for i := range configs {
		profile, err := identity.LoadClientProfile(configs[i].profilePath)
		if err != nil {
			return nil, fmt.Errorf("load provider %q profile %q: %w", configs[i].name, configs[i].profilePath, err)
		}
		if profile.ProviderID != "" && profile.DeviceID != "" {
			device := profile.ProviderID + "/" + profile.DeviceID
			if previous, exists := devices[device]; exists {
				return nil, fmt.Errorf("provider %q uses the same enrolled device as provider %q; enroll a separate device for each provider entry", configs[i].name, previous)
			}
			devices[device] = configs[i].name
		}
		configs[i].profile = profile
	}
	return configs, nil
}

func normalizeProviderListener(address string) (string, error) {
	host, portText, err := net.SplitHostPort(address)
	if err != nil {
		return "", errors.New("must be a TCP host:port address")
	}
	ip := net.ParseIP(host)
	if ip == nil || !ip.IsLoopback() {
		return "", errors.New("must use a literal loopback IP; SOCKS has no remote authentication")
	}
	// Port 0 would bind whatever the kernel handed out, which no proxy client
	// can be configured against.
	port, err := strconv.Atoi(portText)
	if err != nil || port < 1 || port > 65535 {
		return "", errors.New("must use a numeric port between 1 and 65535")
	}
	return net.JoinHostPort(ip.String(), strconv.Itoa(port)), nil
}

func newRuntimeClient(profile identity.ClientProfile, listen string, opts runtimeOptions, logger *slog.Logger, registry *metrics.Registry, sessionLimit *pep.SessionLimit, budget *limiter.Budget) (*pep.Client, error) {
	credentials, err := profile.Credentials()
	if err != nil {
		return nil, err
	}
	return pep.NewClient(pep.ClientConfig{
		ListenAddr: listen, RemoteAddr: profile.Endpoint, LocalAddress: opts.localAddress,
		Credentials: credentials, ChunkSize: opts.chunkSize,
		DialTimeout: opts.dialTimeout, HandshakeTimeout: opts.handshakeTimeout,
		FlowIdleTimeout: opts.flowIdleTimeout, FlowMaxLifetime: opts.flowMaxLifetime,
		MaxSessions: opts.maxSessions, SessionLimit: sessionLimit, MaxPendingOpens: opts.maxPendingOpens, Transport: pep.TransportKind(opts.transport),
		TCPFallbackLanes: opts.tcpFallbackLanes, EnableQUICPool: opts.quicPool,
		WaitForOpenAcknowledgement: opts.waitForOpenAck, UDPOnStream: opts.udpOnStream,
		Congestion: pep.CongestionControlKind(opts.congestion), BrutalBytesPerSec: opts.brutalBytesPerSec,
		AdaptiveMinBytesSec: opts.adaptiveMinBytesSec, AdaptiveMaxBytesSec: opts.adaptiveMaxBytesSec,
		AggregateBytesPerSec: opts.aggregateBytesPerSec, InteractiveReserveBytesPerSec: opts.interactiveReserveBytesPerSec,
		Profile:            opts.resolvedProfile,
		FlowMetadataSocket: opts.flowMetadataSocket,
		Budget:             budget,
		FallbackDelay:      opts.fallbackDelay, FallbackGrace: opts.fallbackGrace,
		UDPFailureThreshold: opts.udpFailureThreshold, UDPCooldown: opts.udpCooldown,
		HopPortCount: profile.HopPortCount,
		Metrics:      registry, Logger: logger,
	})
}

// renewClientProfile refreshes a device certificate which is close to expiry.
// A gateway which cannot be reached is not an error: the current identity is
// still valid, and the maintenance loop will try again. A profile which was
// renewed but could not be written is returned with its error so the caller can
// decide, and the fresh identity is returned rather than the stale one so a
// caller which continues does so on the better certificate.
func renewClientProfile(ctx context.Context, profilePath string, profile identity.ClientProfile, opts runtimeOptions, logger *slog.Logger) (identity.ClientProfile, error) {
	needs, err := profile.NeedsRenewal(time.Now(), 7*24*time.Hour)
	if err != nil {
		return profile, fmt.Errorf("check device identity lifetime: %w", err)
	}
	if !needs {
		return profile, nil
	}
	renewed, err := identity.RenewProfileWithOptions(ctx, profile, identity.DialOptions{Timeout: opts.handshakeTimeout, LocalAddress: opts.localAddress})
	if err != nil {
		logger.Warn("automatic certificate renewal failed; continuing with current valid identity", "error", err)
		return profile, nil
	}
	if err := renewed.Save(profilePath); err != nil {
		return renewed, fmt.Errorf("save renewed profile %q: %w", profilePath, err)
	}
	logger.Info("device identity renewed")
	return renewed, nil
}

func runProviderClients(manifestPath string, noAutoRenew bool, opts runtimeOptions, logger *slog.Logger) error {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	return runProviderClientsContext(ctx, manifestPath, noAutoRenew, opts, logger)
}

// logProviderRuntimeConfiguration records the process-wide controls once and
// then only what differs per provider. Repeating the whole record per provider
// would print the shared session budget once per listener and read as if each
// provider owned that many sessions.
func logProviderRuntimeConfiguration(logger *slog.Logger, opts runtimeOptions, configs []providerClientConfig, limits []*pep.SessionLimit) {
	shared := opts
	// There is no single listener in this mode; each provider logs its own.
	shared.listen = ""
	logRuntimeConfiguration(logger, shared, true)
	for i := range configs {
		logger.LogAttrs(context.Background(), slog.LevelInfo, "provider configuration",
			slog.Int("config_schema", 1),
			slog.String("provider", configs[i].name),
			slog.String("listen", configs[i].listen),
			slog.Int("reserved_sessions", limits[i].Reserved()),
		)
	}
}

func runProviderClientsContext(ctx context.Context, manifestPath string, noAutoRenew bool, opts runtimeOptions, logger *slog.Logger) error {
	configs, err := loadProviderClients(manifestPath)
	if err != nil {
		return err
	}
	registry := metrics.New()
	sessionLimits, err := pep.NewSharedSessionLimits(opts.maxSessions, len(configs))
	if err != nil {
		return err
	}
	// One budget for the process. A budget per provider would offer the
	// configured aggregate rate once per provider onto a single uplink.
	budget := pep.NewAggregateBudget(opts.aggregateBytesPerSec, opts.interactiveReserveBytesPerSec)

	loggers := make([]*slog.Logger, len(configs))
	for i := range configs {
		loggers[i] = logger.With("provider", configs[i].name, "listener", configs[i].listen)
	}

	// Bind every listener before the first gateway dial. Startup renewal can
	// block for a handshake timeout, and holding a healthy provider's listener
	// down while an unrelated provider's gateway times out is the outage a
	// multi-provider client exists to avoid.
	listeners := make([]net.Listener, 0, len(configs))
	closeListeners := func() {
		for _, listener := range listeners {
			_ = listener.Close()
		}
	}
	for i := range configs {
		listener, err := pep.ListenLocal(ctx, configs[i].listen)
		if err != nil {
			closeListeners()
			return fmt.Errorf("bind provider %q listener %q: %w", configs[i].name, configs[i].listen, err)
		}
		listeners = append(listeners, listener)
	}
	logger.Info("all provider listeners bound", "providers", len(configs))

	// Renew concurrently so an unreachable gateway costs the process one
	// handshake timeout rather than one per provider.
	if !noAutoRenew {
		var wg sync.WaitGroup
		for i := range configs {
			wg.Add(1)
			go func() {
				defer wg.Done()
				profile, err := renewClientProfile(ctx, configs[i].profilePath, configs[i].profile, opts, loggers[i])
				if err != nil {
					loggers[i].Error("provider identity maintenance failed; continuing", "error", err)
				}
				configs[i].profile = profile
			}()
		}
		wg.Wait()
	}

	runtimes := make([]providerClientRuntime, 0, len(configs))
	for i := range configs {
		client, err := newRuntimeClient(configs[i].profile, configs[i].listen, opts, loggers[i], registry, sessionLimits[i], budget)
		if err != nil {
			closeListeners()
			return fmt.Errorf("configure provider %q: %w", configs[i].name, err)
		}
		runtimes = append(runtimes, providerClientRuntime{
			config: configs[i], client: client, listener: listeners[i], logger: loggers[i],
		})
	}
	logProviderRuntimeConfiguration(logger, opts, configs, sessionLimits)

	stopMetrics, err := serveMetrics(opts.metricsListen, registry, logger)
	if err != nil {
		closeListeners()
		return err
	}
	defer stopMetrics()
	serveCtx, cancelServe := context.WithCancel(ctx)
	defer cancelServe()
	stopTelemetry := startTelemetryLog(serveCtx, opts.telemetryLogInterval, registry, logger)
	defer stopTelemetry()

	results := make(chan providerServeResult, len(runtimes))
	for i := range runtimes {
		runtime := &runtimes[i]
		if !noAutoRenew {
			go maintainClientIdentity(serveCtx, runtime.config.profilePath, runtime.config.profile, runtime.client, opts.handshakeTimeout, opts.localAddress, runtime.logger)
		}
		go func() {
			results <- providerServeResult{name: runtime.config.name, err: runtime.client.ServeListener(serveCtx, runtime.listener)}
		}()
	}
	return waitProviderClients(serveCtx, cancelServe, results, len(runtimes), logger)
}

func waitProviderClients(ctx context.Context, cancel context.CancelFunc, results <-chan providerServeResult, remaining int, logger *slog.Logger) error {
	var firstErr error
	for remaining > 0 {
		result := <-results
		remaining--
		if result.err == nil {
			if ctx.Err() != nil {
				// Cancellation may be this process shutting down or a sibling
				// which already failed. Either way the stop is recorded, so a
				// provider is never dropped silently from the operator's log.
				logger.Info("provider client stopped during shutdown", "provider", result.name)
				continue
			}
			result.err = errors.New("listener stopped unexpectedly")
		}
		logger.Error("provider client stopped", "provider", result.name, "error", result.err)
		if firstErr == nil {
			firstErr = fmt.Errorf("provider %q stopped: %w", result.name, result.err)
			cancel()
		}
	}
	return firstErr
}
