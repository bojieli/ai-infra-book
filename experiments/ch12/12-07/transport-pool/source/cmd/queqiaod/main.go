package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"io"
	"log/slog"
	"net"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"runtime"
	"runtime/debug"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/metrics"
	"github.com/bojieli/queqiao/internal/netbind"
	"github.com/bojieli/queqiao/internal/operlog"
	"github.com/bojieli/queqiao/internal/pep"
	"github.com/bojieli/queqiao/internal/profile"
	"github.com/bojieli/queqiao/internal/protocol"
)

var (
	version   = "dev"
	commit    = "unknown"
	buildDate = "unknown"
)

func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintf(os.Stderr, "queqiaod: %v\n", err)
		os.Exit(1)
	}
}

func run(args []string) error {
	if len(args) == 0 {
		return errors.New("a command is required: provider, enroll, client, service, server, doctor, segments, logs, or version")
	}
	switch args[0] {
	case "version", "--version", "-version":
		if len(args) != 1 {
			return errors.New("version takes no arguments")
		}
		fmt.Printf("queqiaod %s commit=%s built=%s go=%s wire=%d\n", version, commit, buildDate, goVersion(), protocol.Version)
		return nil
	case "provider":
		return runProvider(args[1:])
	case "enroll":
		return runEnroll(args[1:])
	case "client":
		return runClient(args[1:])
	case "server":
		return runServer(args[1:])
	case "doctor":
		return runDoctorCommand(args[1:])
	case "segments":
		return runSegmentsCommand(args[1:])
	case "logs":
		return runLogs(args[1:])
	case "service":
		return runService(args[1:])
	default:
		return fmt.Errorf("unknown command %q; want provider, enroll, client, service, server, doctor, segments, logs, or version", args[0])
	}
}

func newFlagSet(name string) *flag.FlagSet {
	fs := flag.NewFlagSet(name, flag.ContinueOnError)
	fs.SetOutput(os.Stderr)
	return fs
}

// flagWasSet reports whether the operator named this flag, as opposed to it
// holding its default. A limit the operator did not name must keep its current
// value rather than being reset to a default.
func flagWasSet(fs *flag.FlagSet, name string) bool {
	set := false
	fs.Visit(func(f *flag.Flag) {
		if f.Name == name {
			set = true
		}
	})
	return set
}

// describeLimit renders a limit for an operator, spelling out what zero means
// instead of printing a zero that reads like "none allowed".
func describeLimit(value int, unlimited string) string {
	if value == 0 {
		return fmt.Sprintf("0 (%s)", unlimited)
	}
	return fmt.Sprintf("%d", value)
}

func requireNoArguments(fs *flag.FlagSet) error {
	if fs.NArg() != 0 {
		return fmt.Errorf("unexpected arguments: %s", strings.Join(fs.Args(), " "))
	}
	return nil
}

func runProvider(args []string) error {
	if len(args) == 0 {
		return errors.New("provider command is required: init, add-user, list-users, set-user-limits, invite, list-invites, revoke-invite, list-devices, revoke-device, enable-user, or disable-user")
	}
	switch args[0] {
	case "init":
		fs := newFlagSet("provider init")
		state := fs.String("state", "", "new provider state directory")
		name := fs.String("name", "", "provider display name")
		endpoint := fs.String("endpoint", "", "public gateway host:port")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		if err := requireNoArguments(fs); err != nil {
			return err
		}
		if *state == "" || *name == "" || *endpoint == "" {
			return errors.New("--state, --name, and --endpoint are required")
		}
		provider, err := identity.InitProvider(*state, *name, *endpoint, time.Now())
		if err != nil {
			return err
		}
		fmt.Printf("Provider %q initialized.\nID: %s\nGateway: %s\nState: %s\n", provider.Metadata.Name, provider.Metadata.ProviderID, provider.Metadata.Endpoint, provider.Directory)
		return nil
	case "add-user":
		fs := newFlagSet("provider add-user")
		state := fs.String("state", "", "provider state directory")
		name := fs.String("name", "", "unique user name")
		expiresIn := fs.Duration("expires-in", 0, "optional account lifetime (0 never expires)")
		maxFlows := fs.Int("max-flows", identity.DefaultAccountMaxFlows, "concurrent proxied flows for this user (0 uses the gateway limit)")
		maxClients := fs.Int("max-clients", identity.DefaultAccountMaxClients, "concurrent devices for this user (0 allows every enrolled device)")
		maxSessions := fs.Int("max-sessions", 0, "deprecated name for --max-flows")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		if err := requireNoArguments(fs); err != nil {
			return err
		}
		provider, err := loadProviderRequired(*state)
		if err != nil {
			return err
		}
		var expires time.Time
		if *expiresIn < 0 {
			return errors.New("--expires-in cannot be negative")
		}
		if *expiresIn > 0 {
			expires = time.Now().Add(*expiresIn)
		}
		limits := identity.AccountLimits{MaxFlows: *maxFlows, MaxClients: *maxClients}
		if flagWasSet(fs, "max-sessions") {
			if flagWasSet(fs, "max-flows") {
				return errors.New("--max-sessions is the former name of --max-flows; set only one")
			}
			fmt.Fprintln(os.Stderr, "queqiaod: --max-sessions is deprecated and renamed --max-flows. It counts concurrent flows, not devices: one flow is one TCP connection or one UDP association, and a browser needs hundreds. Use --max-clients to limit devices.")
			limits.MaxFlows = *maxSessions
		}
		account, err := provider.Store.AddAccount(*name, expires, limits, time.Now())
		if err != nil {
			return err
		}
		fmt.Printf("User %q created.\nID: %s\nFlows: %s\nClients: %s\n",
			account.Name, account.ID, describeLimit(account.MaxFlows, "gateway limit"), describeLimit(account.MaxClients, "every enrolled device"))
		return nil
	case "list-users":
		fs := newFlagSet("provider list-users")
		state := fs.String("state", "", "provider state directory")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		if err := requireNoArguments(fs); err != nil {
			return err
		}
		provider, err := loadProviderRequired(*state)
		if err != nil {
			return err
		}
		fmt.Println("ID\tNAME\tENABLED\tEXPIRES\tMAX_FLOWS\tMAX_CLIENTS")
		for _, account := range provider.Store.Accounts() {
			expires := account.ExpiresAt
			if expires == "" {
				expires = "never"
			}
			fmt.Printf("%s\t%s\t%t\t%s\t%d\t%d\n", account.ID, account.Name, account.Enabled, expires, account.MaxFlows, account.MaxClients)
		}
		return nil
	case "set-user-limits":
		fs := newFlagSet("provider set-user-limits")
		state := fs.String("state", "", "provider state directory")
		user := fs.String("user", "", "user name or ID")
		maxFlows := fs.Int("max-flows", 0, "concurrent proxied flows for this user, unchanged if not given (0 uses the gateway limit)")
		maxClients := fs.Int("max-clients", 0, "concurrent devices for this user, unchanged if not given (0 allows every enrolled device)")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		if err := requireNoArguments(fs); err != nil {
			return err
		}
		if !flagWasSet(fs, "max-flows") && !flagWasSet(fs, "max-clients") {
			return errors.New("set at least one of --max-flows or --max-clients")
		}
		provider, err := loadProviderRequired(*state)
		if err != nil {
			return err
		}
		account, ok := provider.Store.FindAccount(*user)
		if !ok {
			return errors.New("unknown user")
		}
		// An unnamed limit keeps its current value. Correcting one limit is
		// the common case, and defaulting the other to this build's default
		// would silently rewrite a policy the operator did not mention.
		limits := account.Limits()
		if flagWasSet(fs, "max-flows") {
			limits.MaxFlows = *maxFlows
		}
		if flagWasSet(fs, "max-clients") {
			limits.MaxClients = *maxClients
		}
		if err := provider.Store.SetAccountLimits(account.ID, limits); err != nil {
			return err
		}
		fmt.Printf("User %q limits updated.\nFlows: %s\nClients: %s\n",
			account.Name, describeLimit(limits.MaxFlows, "gateway limit"), describeLimit(limits.MaxClients, "every enrolled device"))
		return nil
	case "invite":
		fs := newFlagSet("provider invite")
		state := fs.String("state", "", "provider state directory")
		user := fs.String("user", "", "user name or ID")
		expiresIn := fs.Duration("expires-in", 24*time.Hour, "one-time invitation lifetime (maximum 7d)")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		if err := requireNoArguments(fs); err != nil {
			return err
		}
		provider, err := loadProviderRequired(*state)
		if err != nil {
			return err
		}
		uri, _, err := provider.CreateInvitation(*user, *expiresIn, time.Now())
		if err != nil {
			return err
		}
		// stdout is intentionally only the importable value, making it safe to
		// pipe into a QR encoder or provider portal.
		fmt.Println(uri)
		return nil
	case "list-invites":
		fs := newFlagSet("provider list-invites")
		state := fs.String("state", "", "provider state directory")
		user := fs.String("user", "", "optional user name or ID")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		if err := requireNoArguments(fs); err != nil {
			return err
		}
		provider, err := loadProviderRequired(*state)
		if err != nil {
			return err
		}
		accountID := ""
		if *user != "" {
			account, ok := provider.Store.FindAccount(*user)
			if !ok {
				return errors.New("unknown user")
			}
			accountID = account.ID
		}
		fmt.Println("ID\tACCOUNT_ID\tCREATED\tEXPIRES")
		for _, invitation := range provider.Store.Invites(accountID, time.Now()) {
			fmt.Printf("%s\t%s\t%s\t%s\n", invitation.ID, invitation.AccountID, invitation.CreatedAt, invitation.ExpiresAt)
		}
		return nil
	case "revoke-invite":
		fs := newFlagSet("provider revoke-invite")
		state := fs.String("state", "", "provider state directory")
		invitation := fs.String("invite", "", "outstanding invitation ID")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		if err := requireNoArguments(fs); err != nil {
			return err
		}
		provider, err := loadProviderRequired(*state)
		if err != nil {
			return err
		}
		if err := provider.Store.RevokeInvite(*invitation); err != nil {
			return err
		}
		fmt.Printf("Invitation %s revoked.\n", *invitation)
		return nil
	case "list-devices":
		fs := newFlagSet("provider list-devices")
		state := fs.String("state", "", "provider state directory")
		user := fs.String("user", "", "optional user name or ID")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		if err := requireNoArguments(fs); err != nil {
			return err
		}
		provider, err := loadProviderRequired(*state)
		if err != nil {
			return err
		}
		accountID := ""
		if *user != "" {
			account, ok := provider.Store.FindAccount(*user)
			if !ok {
				return errors.New("unknown user")
			}
			accountID = account.ID
		}
		fmt.Println("ID\tACCOUNT_ID\tNAME\tENABLED\tCREATED\tREVOKED")
		for _, device := range provider.Store.Devices(accountID) {
			revoked := device.RevokedAt
			if revoked == "" {
				revoked = "-"
			}
			fmt.Printf("%s\t%s\t%s\t%t\t%s\t%s\n", device.ID, device.AccountID, device.Name, device.Enabled, device.CreatedAt, revoked)
		}
		return nil
	case "revoke-device":
		fs := newFlagSet("provider revoke-device")
		state := fs.String("state", "", "provider state directory")
		device := fs.String("device", "", "device ID")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		if err := requireNoArguments(fs); err != nil {
			return err
		}
		provider, err := loadProviderRequired(*state)
		if err != nil {
			return err
		}
		if err := provider.Store.RevokeDevice(*device, time.Now()); err != nil {
			return err
		}
		fmt.Printf("Device %s revoked.\n", *device)
		return nil
	case "enable-user", "disable-user":
		fs := newFlagSet("provider " + args[0])
		state := fs.String("state", "", "provider state directory")
		user := fs.String("user", "", "user name or ID")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		if err := requireNoArguments(fs); err != nil {
			return err
		}
		provider, err := loadProviderRequired(*state)
		if err != nil {
			return err
		}
		account, ok := provider.Store.FindAccount(*user)
		if !ok {
			return errors.New("unknown user")
		}
		enabled := args[0] == "enable-user"
		if err := provider.Store.SetAccountEnabled(account.ID, enabled); err != nil {
			return err
		}
		fmt.Printf("User %q enabled=%t.\n", account.Name, enabled)
		return nil
	default:
		return fmt.Errorf("unknown provider command %q", args[0])
	}
}

func loadProviderRequired(state string) (*identity.Provider, error) {
	if strings.TrimSpace(state) == "" {
		return nil, errors.New("--state is required")
	}
	return identity.LoadProvider(state)
}

func runEnroll(args []string) error {
	fs := newFlagSet("enroll")
	inviteFlag := fs.String("invite", "", "one-time queqiao:// invitation URI")
	profilePath := fs.String("profile", "", "output client profile (default: user config directory)")
	deviceName := fs.String("device-name", "", "device label shown to the provider")
	timeout := fs.Duration("timeout", 15*time.Second, "enrollment timeout")
	localAddress := fs.String("local-address", "auto", "outer source: auto, IP, or if:NAME (bypasses host TUN routes)")
	// The share URI is the natural first argument users paste. The standard Go
	// flag parser stops at that positional value, so lift it out first to allow
	// the equally natural `enroll URI --profile PATH` spelling as well as flags
	// before the URI and the explicit --invite form.
	positionalInvitation := ""
	parseArgs := args
	if len(args) > 0 && !strings.HasPrefix(args[0], "-") {
		positionalInvitation = args[0]
		parseArgs = args[1:]
	}
	if err := fs.Parse(parseArgs); err != nil {
		return err
	}
	if fs.NArg() > 1 {
		return errors.New("enroll accepts at most one invitation URI")
	}
	invitationText := *inviteFlag
	if positionalInvitation != "" {
		if invitationText != "" {
			return errors.New("provide the invitation as either --invite or one argument, not both")
		}
		invitationText = positionalInvitation
	}
	if fs.NArg() == 1 {
		if invitationText != "" {
			return errors.New("provide the invitation as either --invite or one argument, not both")
		}
		invitationText = fs.Arg(0)
	}
	if invitationText == "" {
		return errors.New("an invitation URI is required")
	}
	if err := netbind.Validate(*localAddress); err != nil {
		return fmt.Errorf("invalid --local-address: %w", err)
	}
	invitation, err := identity.ParseInvitation(invitationText, time.Now())
	if err != nil {
		return err
	}
	if *deviceName == "" {
		*deviceName, _ = os.Hostname()
		if strings.TrimSpace(*deviceName) == "" {
			*deviceName = "device"
		}
	}
	if *profilePath == "" {
		configDir, err := os.UserConfigDir()
		if err != nil {
			return fmt.Errorf("locate user configuration directory: %w", err)
		}
		*profilePath = filepath.Join(configDir, "queqiao", invitation.ProviderID+".json")
	}
	if _, err := os.Stat(*profilePath); err == nil {
		return fmt.Errorf("profile already exists: %s", *profilePath)
	} else if !errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("inspect profile path: %w", err)
	}
	if err := os.MkdirAll(filepath.Dir(*profilePath), 0o700); err != nil {
		return fmt.Errorf("create profile directory: %w", err)
	}
	pendingPath := *profilePath + ".enrolling"
	var draft identity.EnrollmentDraft
	if _, err := os.Stat(pendingPath); err == nil {
		draft, err = identity.LoadEnrollmentDraft(pendingPath)
		if err != nil {
			return fmt.Errorf("load interrupted enrollment %s: %w", pendingPath, err)
		}
		if draft.Invitation != invitation || draft.DeviceName != *deviceName {
			return fmt.Errorf("%s belongs to another invitation or device name; finish or remove it explicitly", pendingPath)
		}
	} else if !errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("inspect interrupted enrollment: %w", err)
	} else {
		draft, err = identity.NewEnrollmentDraft(invitation, *deviceName)
		if err != nil {
			return err
		}
		if err := draft.Save(pendingPath); err != nil {
			return fmt.Errorf("save recoverable enrollment draft: %w", err)
		}
	}
	ctx, cancel := context.WithTimeout(context.Background(), *timeout)
	defer cancel()
	profile, err := draft.EnrollWithOptions(ctx, identity.DialOptions{Timeout: *timeout, LocalAddress: *localAddress})
	if err != nil {
		return err
	}
	if err := profile.SaveNew(*profilePath); err != nil {
		return fmt.Errorf("save enrolled profile: %w", err)
	}
	if err := os.Remove(pendingPath); err != nil && !errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("profile was saved successfully at %s, but the completed draft %s still contains private credentials and must be removed: %w", *profilePath, pendingPath, err)
	}
	fmt.Printf("Enrolled %q as device %q.\nProfile: %s\nSOCKS: queqiaod client --profile %q\nService: queqiaod service install --profile %q\n", profile.Name, profile.DeviceName, *profilePath, *profilePath, *profilePath)
	return nil
}

type runtimeOptions struct {
	listen, localAddress, transport, tcpCongestion, pathProfile     string
	maxSessions, maxPendingOpens, tcpFallbackLanes                  int
	chunkSize                                                       int
	dialTimeout, handshakeTimeout, flowIdleTimeout, flowMaxLifetime time.Duration
	quicPool, waitForOpenAck, udpOnStream                           bool
	flowMetadataSocket                                              string
	classHints                                                      repeatedFlag
	// resolvedProfile is the deployment policy, parsed once at flag time so
	// that an unknown name fails before anything starts rather than being
	// silently replaced by the default.
	resolvedProfile                                             profile.Profile
	congestion                                                  string
	brutalBytesPerSec, adaptiveMinBytesSec, adaptiveMaxBytesSec uint64
	aggregateBytesPerSec, interactiveReserveBytesPerSec         uint64
	fallbackDelay, fallbackGrace, udpCooldown                   time.Duration
	udpFailureThreshold                                         int
	hopPortCount                                                int
	allowPrivate                                                bool
	logLevel, logFile, logFormat                                string
	jsonLogs                                                    bool
	logStderr                                                   bool
	logMaxSizeMiB                                               int64
	logMaxBackups                                               int
	telemetryLogInterval                                        time.Duration
	metricsListen                                               string
}

func bindRuntimeFlags(fs *flag.FlagSet, opts *runtimeOptions, client bool) {
	defaultListen := ":443"
	defaultMaxSessions := 4096
	if client {
		// 12080 rather than the conventional 1080: deploy/clash-queqiao.yaml
		// and the deployment guide both point Clash at that port, and a
		// default that disagrees with the profile shipped beside it turns
		// every unconfigured start into a silent no-route.
		defaultListen, defaultMaxSessions = "127.0.0.1:12080", 2048
	}
	fs.StringVar(&opts.listen, "listen", defaultListen, "listen address")
	fs.IntVar(&opts.maxSessions, "max-sessions", defaultMaxSessions, "global concurrent-session limit")
	fs.IntVar(&opts.chunkSize, "chunk-size", 32*1024, "stream data frame size")
	fs.DurationVar(&opts.dialTimeout, "dial-timeout", 10*time.Second, "dial timeout")
	// 30s, matching the default NewClient applies when nothing is configured:
	// a first handshake on an erasing path takes about five seconds at 42%
	// loss, and the flag used to silently override the safer library default
	// with ten, making that first connection a coin flip.
	fs.DurationVar(&opts.handshakeTimeout, "handshake-timeout", 30*time.Second, "TLS, protocol, and SOCKS handshake timeout")
	fs.DurationVar(&opts.flowIdleTimeout, "flow-idle-timeout", 30*time.Minute, "flow idle timeout")
	fs.DurationVar(&opts.flowMaxLifetime, "flow-max-lifetime", 24*time.Hour, "maximum flow lifetime")
	fs.StringVar(&opts.transport, "transport", string(pep.TransportAuto), "transport: auto, quic, or tcp")
	fs.IntVar(&opts.tcpFallbackLanes, "tcp-fallback-lanes", 0, "TCP lanes per bulk flow (0 uses role default)")
	fs.BoolVar(&opts.udpOnStream, "udp-on-stream", false, "carry UDP packets on streams instead of QUIC datagrams")
	fs.IntVar(&opts.hopPortCount, "hop-port-count", 0, "number of UDP ports to listen on for port hopping (0/1 = disabled)")
	fs.StringVar(&opts.congestion, "congestion", string(pep.CongestionErasure), "QUIC congestion controller")
	fs.Uint64Var(&opts.brutalBytesPerSec, "brutal-bytes-per-sec", 0, "Brutal fixed byte rate")
	fs.Uint64Var(&opts.adaptiveMinBytesSec, "adaptive-min-bytes-per-sec", 64*1024, "Adaptive minimum byte rate")
	fs.Uint64Var(&opts.adaptiveMaxBytesSec, "adaptive-max-bytes-per-sec", 200*1024*1024, "Adaptive maximum byte rate")
	fs.Uint64Var(&opts.aggregateBytesPerSec, "aggregate-bytes-per-sec", 0, "optional aggregate byte budget")
	fs.Uint64Var(&opts.interactiveReserveBytesPerSec, "interactive-reserve-bytes-per-sec", 0, "interactive portion of aggregate budget")
	fs.StringVar(&opts.logLevel, "log-level", "info", "debug, info, warn, or error")
	fs.StringVar(&opts.logFile, "log-file", "auto", "runtime log path; auto selects the platform location, none disables the file")
	fs.StringVar(&opts.logFormat, "log-format", "json", "runtime log format: json or text")
	fs.BoolVar(&opts.jsonLogs, "json-logs", false, "deprecated alias for --log-format=json")
	fs.BoolVar(&opts.logStderr, "log-stderr", true, "also write runtime logs to stderr or the service journal")
	fs.Int64Var(&opts.logMaxSizeMiB, "log-max-size-mib", operlog.DefaultMaxSizeBytes/(1024*1024), "rotate the runtime log after this many MiB")
	fs.IntVar(&opts.logMaxBackups, "log-max-backups", operlog.DefaultMaxBackups, "number of rotated runtime logs to retain")
	fs.DurationVar(&opts.telemetryLogInterval, "telemetry-log-interval", 5*time.Second, "structured performance snapshot interval while state changes (0 disables)")
	fs.StringVar(&opts.metricsListen, "metrics-listen", "", "optional metrics listen address")
	if client {
		fs.StringVar(&opts.localAddress, "local-address", "auto", "outer source: auto, IP, or if:NAME")
		fs.IntVar(&opts.maxPendingOpens, "max-pending-opens", 256, "concurrent remote flow opens")
		fs.BoolVar(&opts.quicPool, "quic-pool", true, "reuse a persistent QUIC connection")
		fs.StringVar(&opts.pathProfile, "path-profile", "", "deployment this client runs in: "+strings.Join(profile.Names(), ", ")+" (default is the supported access-link profile)")
		fs.StringVar(&opts.flowMetadataSocket, "flow-metadata-socket", "", "local capture agent socket to ask what produced each flow, so its class is known before it carries anything; empty disables the lookup")
		fs.Var(&opts.classHints, "class-hint", "declare the class a flow starts in from what produced it, as <match>=<interactive|bulk>; repeatable, first match wins, and it does nothing without --flow-metadata-socket")
		fs.BoolVar(&opts.waitForOpenAck, "wait-for-open-ack", false, "wait for destination confirmation before answering SOCKS")
		fs.DurationVar(&opts.fallbackDelay, "fallback-delay", 300*time.Millisecond, "delay before preparing TCP fallback")
		fs.DurationVar(&opts.fallbackGrace, "fallback-grace", 2*time.Second, "time a ready TCP fallback waits for QUIC")
		fs.IntVar(&opts.udpFailureThreshold, "udp-failure-threshold", 3, "UDP failures before cooldown")
		fs.DurationVar(&opts.udpCooldown, "udp-cooldown", 30*time.Second, "UDP cooldown after repeated failure")
	} else {
		fs.StringVar(&opts.tcpCongestion, "tcp-congestion", "system", "server TCP congestion controller")
		fs.StringVar(&opts.pathProfile, "path-profile", "", "deployment this gateway serves: "+strings.Join(profile.Names(), ", ")+" (default is the supported access-link profile)")
		fs.BoolVar(&opts.allowPrivate, "allow-private-destinations", false, "allow private and link-local destinations")
	}
}

// resolveProfile parses the deployment profile once, so an unknown name is a
// startup failure rather than a silent fallback to a policy the operator did
// not ask for.
func resolveProfile(opts *runtimeOptions) error {
	p, err := profile.ByName(opts.pathProfile)
	if err != nil {
		return err
	}
	opts.resolvedProfile = p
	return nil
}

func validateRuntime(opts runtimeOptions, client bool) error {
	if opts.listen == "" || opts.maxSessions < 1 || opts.maxSessions > 1<<16 {
		return errors.New("listen address and max-sessions (1-65536) are required")
	}
	if client {
		host, _, err := net.SplitHostPort(opts.listen)
		ip := net.ParseIP(host)
		if err != nil || ip == nil || !ip.IsLoopback() {
			return errors.New("client --listen must use a literal loopback IP; SOCKS has no remote authentication")
		}
	}
	// The receive limit is protocol.MaxPayload and is not configurable: two
	// peers that disagree about it are mutually unintelligible in one direction
	// with no negotiation to discover it. Only the sending chunk is a choice,
	// and it must stay inside what the wire allows.
	if opts.chunkSize <= 0 || opts.chunkSize > protocol.MaxPayload {
		return fmt.Errorf("--chunk-size must be between 1 and %d bytes", protocol.MaxPayload)
	}
	if opts.transport != string(pep.TransportAuto) && opts.transport != string(pep.TransportQUIC) && opts.transport != string(pep.TransportTCP) {
		return errors.New("--transport must be auto, quic, or tcp")
	}
	if opts.tcpFallbackLanes < 0 || opts.tcpFallbackLanes > 16 {
		return errors.New("--tcp-fallback-lanes must be between 0 and 16")
	}
	if opts.flowIdleTimeout <= 0 || opts.flowMaxLifetime <= 0 || opts.flowIdleTimeout > opts.flowMaxLifetime {
		return errors.New("flow idle timeout must be positive and no longer than flow lifetime")
	}
	if opts.dialTimeout <= 0 || opts.handshakeTimeout <= 0 {
		return errors.New("dial and handshake timeouts must be positive")
	}
	// The reserve is withheld from bulk traffic, so it has to leave some of
	// the budget behind: a reserve equal to the whole of it would stop bulk
	// entirely rather than slow it down.
	if opts.aggregateBytesPerSec == 0 && opts.interactiveReserveBytesPerSec != 0 ||
		opts.aggregateBytesPerSec != 0 && opts.interactiveReserveBytesPerSec >= opts.aggregateBytesPerSec {
		return errors.New("invalid aggregate/interactive byte budget")
	}
	if opts.adaptiveMinBytesSec == 0 || opts.adaptiveMaxBytesSec < opts.adaptiveMinBytesSec {
		return errors.New("invalid adaptive byte-rate bounds")
	}
	if opts.congestion == string(pep.CongestionBrutal) && opts.brutalBytesPerSec == 0 {
		return errors.New("--brutal-bytes-per-sec is required with brutal congestion")
	}
	if opts.logFormat != "json" && opts.logFormat != "text" {
		return errors.New("--log-format must be json or text")
	}
	switch strings.ToLower(opts.logLevel) {
	case "debug", "info", "warn", "warning", "error":
	default:
		return errors.New("--log-level must be debug, info, warn, or error")
	}
	if opts.logFile == operlog.DisabledPath && !opts.logStderr {
		return errors.New("--log-file=none requires --log-stderr=true")
	}
	if opts.logMaxSizeMiB < 1 || opts.logMaxSizeMiB > 10*1024 {
		return errors.New("--log-max-size-mib must be between 1 and 10240")
	}
	if opts.logMaxBackups < 0 || opts.logMaxBackups > 100 {
		return errors.New("--log-max-backups must be between 0 and 100")
	}
	if opts.telemetryLogInterval < 0 || opts.telemetryLogInterval > 0 && opts.telemetryLogInterval < time.Second {
		return errors.New("--telemetry-log-interval must be 0 or at least 1s")
	}
	if client && (opts.maxPendingOpens < 1 || opts.maxPendingOpens > 1<<16) {
		return errors.New("--max-pending-opens must be between 1 and 65536")
	}
	if client && (opts.fallbackDelay < 0 || opts.fallbackGrace <= 0 || opts.udpFailureThreshold < 1 || opts.udpCooldown <= 0) {
		return errors.New("invalid fallback settings")
	}
	if client {
		if err := netbind.Validate(opts.localAddress); err != nil {
			return fmt.Errorf("invalid --local-address: %w", err)
		}
	}
	return nil
}

func runClient(args []string) (returnErr error) {
	fs := newFlagSet("client")
	profilePath := fs.String("profile", "", "imported client profile")
	providersPath := fs.String("providers", "", "multi-provider manifest")
	noAutoRenew := fs.Bool("no-auto-renew", false, "disable certificate renewal before expiry")
	var opts runtimeOptions
	bindRuntimeFlags(fs, &opts, true)
	if err := fs.Parse(args); err != nil {
		return err
	}
	if opts.jsonLogs {
		opts.logFormat = "json"
	}
	if err := requireNoArguments(fs); err != nil {
		return err
	}
	if err := resolveProfile(&opts); err != nil {
		return err
	}
	hints, err := profile.ParseClassHints(opts.classHints)
	if err != nil {
		return err
	}
	opts.resolvedProfile.ClassHints = hints
	if len(hints) > 0 && opts.flowMetadataSocket == "" {
		return errors.New("--class-hint needs --flow-metadata-socket: without an agent to ask, nothing declares a class")
	}
	if *profilePath != "" && *providersPath != "" {
		return errors.New("--profile and --providers are mutually exclusive")
	}
	if *profilePath == "" && *providersPath == "" {
		return errors.New("either --profile or --providers is required; import each provider invitation first with `queqiaod enroll INVITATION`")
	}
	listenSet := false
	fs.Visit(func(f *flag.Flag) {
		if f.Name == "listen" {
			listenSet = true
		}
	})
	if *providersPath != "" && listenSet {
		return errors.New("--listen cannot be used with --providers; set each listener in the manifest")
	}
	if err := validateRuntime(opts, true); err != nil {
		return err
	}
	logger, logSink, err := openRuntimeLogger(opts, "client")
	if err != nil {
		return err
	}
	defer finishRuntimeLog(logger, logSink, "client", &returnErr)
	if *providersPath != "" {
		return runProviderClients(*providersPath, *noAutoRenew, opts, logger)
	}
	logRuntimeConfiguration(logger, opts, true)
	profile, err := identity.LoadClientProfile(*profilePath)
	if err != nil {
		return fmt.Errorf("load client profile %q: %w", *profilePath, err)
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	if !*noAutoRenew {
		profile, err = renewClientProfile(ctx, *profilePath, profile, opts, logger)
		if err != nil {
			return err
		}
	}
	client, err := newRuntimeClient(profile, opts.listen, opts, logger, nil, nil, nil)
	if err != nil {
		return err
	}
	stopTelemetry := startTelemetryLog(ctx, opts.telemetryLogInterval, client.Metrics(), logger)
	defer stopTelemetry()
	if !*noAutoRenew {
		go maintainClientIdentity(ctx, *profilePath, profile, client, opts.handshakeTimeout, opts.localAddress, logger)
	}
	stopMetrics, err := serveMetrics(opts.metricsListen, client.Metrics(), logger)
	if err != nil {
		return err
	}
	defer stopMetrics()
	return client.Serve(ctx)
}

func runServer(args []string) (returnErr error) {
	fs := newFlagSet("server")
	state := fs.String("state", "", "provider state directory")
	var opts runtimeOptions
	bindRuntimeFlags(fs, &opts, false)
	if err := fs.Parse(args); err != nil {
		return err
	}
	if opts.jsonLogs {
		opts.logFormat = "json"
	}
	if err := requireNoArguments(fs); err != nil {
		return err
	}
	if err := validateRuntime(opts, false); err != nil {
		return err
	}
	logger, logSink, err := openRuntimeLogger(opts, "server")
	if err != nil {
		return err
	}
	defer finishRuntimeLog(logger, logSink, "server", &returnErr)
	logRuntimeConfiguration(logger, opts, false)
	provider, err := loadProviderRequired(*state)
	if err != nil {
		return err
	}
	service := &identity.EnrollmentService{Provider: provider}
	// An unknown profile name is refused rather than ignored. Starting on a
	// different policy than the operator asked for is the failure the profile
	// package exists to prevent, and it would be invisible in the logs.
	serverProfile, err := profile.ByName(opts.pathProfile)
	if err != nil {
		return err
	}
	logger.Info("path profile selected", "profile", serverProfile.Name,
		"level", string(serverProfile.Level), "evidence", serverProfile.Evidence)
	server, err := pep.NewServer(pep.ServerConfig{
		ListenAddr: opts.listen, Credentials: provider.ServerCredentials(), Enrollment: service,
		ChunkSize:        opts.chunkSize,
		HandshakeTimeout: opts.handshakeTimeout, FlowIdleTimeout: opts.flowIdleTimeout,
		FlowMaxLifetime: opts.flowMaxLifetime, MaxSessions: opts.maxSessions,
		DestinationPolicy: pep.DestinationPolicy{AllowPrivate: opts.allowPrivate, DialTimeout: opts.dialTimeout},
		EnableTCP:         opts.transport == string(pep.TransportTCP) || opts.transport == string(pep.TransportAuto),
		EnableQUIC:        opts.transport == string(pep.TransportQUIC) || opts.transport == string(pep.TransportAuto),
		TCPFallbackLanes:  opts.tcpFallbackLanes, TCPCongestion: opts.tcpCongestion,
		Congestion: pep.CongestionControlKind(opts.congestion), BrutalBytesPerSec: opts.brutalBytesPerSec,
		AdaptiveMinBytesSec: opts.adaptiveMinBytesSec, AdaptiveMaxBytesSec: opts.adaptiveMaxBytesSec,
		AggregateBytesPerSec: opts.aggregateBytesPerSec, InteractiveReserveBytesPerSec: opts.interactiveReserveBytesPerSec,
		Logger: logger, UDPOnStream: opts.udpOnStream, Profile: serverProfile,
		HopPortCount: opts.hopPortCount,
	})
	if err != nil {
		return err
	}
	stopMetrics, err := serveMetrics(opts.metricsListen, server.Metrics(), logger)
	if err != nil {
		return err
	}
	defer stopMetrics()
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	stopTelemetry := startTelemetryLog(ctx, opts.telemetryLogInterval, server.Metrics(), logger)
	defer stopTelemetry()
	go maintainGatewayIdentity(ctx, provider, logger)
	return server.Serve(ctx)
}

const identityMaintenanceInterval = time.Hour

func maintainClientIdentity(ctx context.Context, profilePath string, profile identity.ClientProfile, client *pep.Client, timeout time.Duration, localAddress string, logger *slog.Logger) {
	ticker := time.NewTicker(identityMaintenanceInterval)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			needs, err := profile.NeedsRenewal(time.Now(), 7*24*time.Hour)
			if err != nil {
				logger.Error("check device identity lifetime", "error", err)
				continue
			}
			if !needs {
				continue
			}
			renewed, err := identity.RenewProfileWithOptions(ctx, profile, identity.DialOptions{Timeout: timeout, LocalAddress: localAddress})
			if err != nil {
				logger.Warn("automatic certificate renewal failed; will retry", "error", err)
				continue
			}
			if err := renewed.Save(profilePath); err != nil {
				logger.Error("save renewed device identity; will retry", "error", err)
				continue
			}
			credentials, err := renewed.Credentials()
			if err != nil {
				logger.Error("load renewed device identity", "error", err)
				continue
			}
			if err := client.UpdateCredentials(credentials); err != nil {
				logger.Error("activate renewed device identity", "error", err)
				continue
			}
			profile = renewed
			logger.Info("device identity renewed")
		case <-ctx.Done():
			return
		}
	}
}

func maintainGatewayIdentity(ctx context.Context, provider *identity.Provider, logger *slog.Logger) {
	ticker := time.NewTicker(identityMaintenanceInterval)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			renewed, err := provider.RenewGatewayIdentity(time.Now(), 7*24*time.Hour)
			if err != nil {
				logger.Error("automatic gateway identity renewal failed; will retry", "error", err)
			} else if renewed {
				logger.Info("gateway identity renewed")
			}
		case <-ctx.Done():
			return
		}
	}
}

func openRuntimeLogger(opts runtimeOptions, role string) (*slog.Logger, *operlog.Sink, error) {
	var console io.Writer
	if opts.logStderr {
		console = os.Stderr
	}
	logger, sink, err := operlog.Open(operlog.Config{
		Role: role, Path: opts.logFile, Level: opts.logLevel, Format: opts.logFormat,
		Console: console, MaxBytes: opts.logMaxSizeMiB * 1024 * 1024, MaxBackups: opts.logMaxBackups,
	})
	if err != nil {
		return nil, nil, err
	}
	path := sink.Path()
	if path == "" {
		path = "disabled"
	}
	logger.Info("runtime logging initialized",
		"log_file", path, "log_format", opts.logFormat, "log_level", opts.logLevel,
		"log_max_size_mib", opts.logMaxSizeMiB, "log_max_backups", opts.logMaxBackups,
		"telemetry_interval", opts.telemetryLogInterval,
		"version", version, "commit", commit, "wire_protocol", protocol.Version)
	return logger, sink, nil
}

// logRuntimeConfiguration records the non-secret controls needed to reproduce
// a performance result. Identity files and provider state paths are excluded;
// the role-specific listener and transport behavior are not.
func logRuntimeConfiguration(logger *slog.Logger, opts runtimeOptions, client bool) {
	attrs := []slog.Attr{
		slog.Int("config_schema", 1),
		slog.String("listen", opts.listen),
		slog.String("transport", opts.transport),
		slog.String("congestion", opts.congestion),
		slog.Int("max_sessions", opts.maxSessions),
		slog.Uint64("max_payload_bytes", uint64(protocol.MaxPayload)),
		slog.Int("chunk_size_bytes", opts.chunkSize),
		slog.Int("tcp_fallback_lanes", opts.tcpFallbackLanes),
		slog.Bool("udp_on_stream", opts.udpOnStream),
		slog.Duration("dial_timeout", opts.dialTimeout),
		slog.Duration("handshake_timeout", opts.handshakeTimeout),
		slog.Duration("flow_idle_timeout", opts.flowIdleTimeout),
		slog.Duration("flow_max_lifetime", opts.flowMaxLifetime),
		slog.Uint64("aggregate_bytes_per_second", opts.aggregateBytesPerSec),
		slog.Uint64("interactive_reserve_bytes_per_second", opts.interactiveReserveBytesPerSec),
		slog.String("metrics_listen", opts.metricsListen),
	}
	if client {
		attrs = append(attrs,
			slog.String("local_address", opts.localAddress),
			slog.Int("max_pending_opens", opts.maxPendingOpens),
			slog.Bool("quic_pool", opts.quicPool),
			slog.String("path_profile", opts.resolvedProfile.Name),
			slog.String("path_profile_level", string(opts.resolvedProfile.Level)),
			slog.Bool("wait_for_open_ack", opts.waitForOpenAck),
			slog.Duration("fallback_delay", opts.fallbackDelay),
			slog.Duration("fallback_grace", opts.fallbackGrace),
		)
	} else {
		attrs = append(attrs,
			slog.String("tcp_congestion", opts.tcpCongestion),
			slog.Bool("allow_private_destinations", opts.allowPrivate),
		)
	}
	logger.LogAttrs(context.Background(), slog.LevelInfo, "runtime configuration", attrs...)
}

func finishRuntimeLog(logger *slog.Logger, sink *operlog.Sink, role string, returnErr *error) {
	if *returnErr != nil && !errors.Is(*returnErr, context.Canceled) {
		logger.Error("runtime stopped with error", "error", *returnErr)
	} else {
		logger.Info("runtime stopped", "reason", "shutdown")
	}
	if err := sink.Close(); err != nil && *returnErr == nil {
		*returnErr = fmt.Errorf("close %s runtime log: %w", role, err)
	}
}

// startTelemetryLog writes a stable, flat metrics record immediately, while a
// flow is active, whenever counters change, and once more at shutdown. The
// names match /metrics so one parser can consume both surfaces.
func startTelemetryLog(ctx context.Context, interval time.Duration, registry *metrics.Registry, logger *slog.Logger) func() {
	if interval == 0 || registry == nil || logger == nil {
		return func() {}
	}
	previous := registry.Snapshot()
	logPerformanceSnapshot(logger, previous, interval)
	stop := make(chan struct{})
	done := make(chan struct{})
	var stopOnce sync.Once
	go func() {
		defer close(done)
		ticker := time.NewTicker(interval)
		defer ticker.Stop()
		for {
			select {
			case <-ticker.C:
				current := registry.Snapshot()
				if current != previous || current.ActiveFlows > 0 {
					logPerformanceSnapshot(logger, current, interval)
					previous = current
				}
			case <-ctx.Done():
				current := registry.Snapshot()
				if current != previous {
					logPerformanceSnapshot(logger, current, interval)
				}
				return
			case <-stop:
				current := registry.Snapshot()
				if current != previous {
					logPerformanceSnapshot(logger, current, interval)
				}
				return
			}
		}
	}()
	return func() {
		stopOnce.Do(func() { close(stop) })
		<-done
	}
}

func logPerformanceSnapshot(logger *slog.Logger, s metrics.Snapshot, interval time.Duration) {
	logger.LogAttrs(context.Background(), slog.LevelInfo, "performance snapshot",
		slog.Int("telemetry_schema", 1), slog.String("type", "metrics"),
		slog.Float64("sample_interval_seconds", interval.Seconds()),
		slog.Int64("queqiao_active_flows", s.ActiveFlows),
		slog.Int64("queqiao_flows_started_total", s.FlowsStarted),
		slog.Int64("queqiao_flows_completed_total", s.FlowsCompleted),
		slog.Int64("queqiao_flows_failed_total", s.FlowsFailed),
		slog.Uint64("queqiao_bytes_up_total", s.BytesUp),
		slog.Uint64("queqiao_bytes_down_total", s.BytesDown),
		slog.Uint64("queqiao_lane_failures_total", s.LaneFailures),
		slog.Uint64("queqiao_lane_replacements_total", s.LaneReplacements),
		slog.Uint64("queqiao_fallbacks_total", s.Fallbacks),
		slog.Uint64("queqiao_udp_path_unavailable_total", s.UDPPathUnavailable),
		slog.Uint64("queqiao_endpoint_transport_races_failed_total", s.EndpointTransportRaceFailures),
		slog.Uint64("queqiao_udp_transient_send_errors_total", s.TransientUDPSendErrors),
		slog.Uint64("queqiao_udp_association_reconnects_total", s.UDPAssociationReconnects),
		slog.Uint64("queqiao_udp_association_rescue_failures_total", s.UDPAssociationRescueFailures),
		slog.Uint64("queqiao_completion_timeouts_total", s.CompletionTimeouts),
		slog.Uint64("queqiao_flow_timeouts_total", s.FlowTimeouts),
		slog.Uint64("queqiao_authorization_refresh_failures_total", s.AuthorizationRefreshFailures),
		slog.Uint64("queqiao_authorization_reloads_total", s.AuthorizationReloads),
		slog.Uint64("queqiao_authorization_consecutive_refresh_failures", s.AuthorizationConsecutiveRefreshFailures),
		slog.Int64("queqiao_authorization_last_good_timestamp_seconds", s.AuthorizationLastGoodUnix),
		slog.Int64("queqiao_replay_bytes_in_use", s.ReplayBytesInUse),
		slog.Uint64("queqiao_bulk_isolations_total", s.BulkIsolations),
		slog.Uint64("queqiao_lane_reinjections_total", s.Reinjections),
		slog.Int64("queqiao_quic_lanes", s.QUICLanes),
		slog.Float64("queqiao_quic_latest_rtt_seconds", s.QUICLatestRTT.Seconds()),
		slog.Float64("queqiao_quic_smoothed_rtt_seconds", s.QUICSmoothedRTT.Seconds()),
		slog.Uint64("queqiao_quic_bytes_sent", s.QUICBytesSent),
		slog.Uint64("queqiao_quic_bytes_received", s.QUICBytesReceived),
		slog.Uint64("queqiao_quic_packets_sent", s.QUICPacketsSent),
		slog.Uint64("queqiao_quic_packets_received", s.QUICPacketsReceived),
		slog.Uint64("queqiao_quic_loss_observed_packets_total", s.QUICLossObservedPackets),
		slog.Uint64("queqiao_quic_observations_expired_total", s.QUICObservationsExpired),
		slog.String("queqiao_quic_controller_kind", s.QUICControllerKind),
		slog.Uint64("queqiao_quic_controller_mode", uint64(s.QUICControllerMode)),
		slog.Uint64("queqiao_quic_controller_max_bandwidth_bytes_per_second", s.QUICControllerMaxBandwidth),
		slog.Uint64("queqiao_quic_controller_latest_sample_bytes_per_second", s.QUICControllerLatestSample),
		slog.Uint64("queqiao_quic_controller_latest_ack_rate_bytes_per_second", s.QUICControllerLatestAckRate),
		slog.Uint64("queqiao_quic_controller_latest_send_rate_bytes_per_second", s.QUICControllerLatestSendRate),
		slog.Uint64("queqiao_quic_controller_samples_total", s.QUICControllerSamples),
		slog.Uint64("queqiao_quic_controller_non_app_limited_samples_total", s.QUICControllerNonAppSamples),
		slog.Uint64("queqiao_quic_controller_app_limited_samples_total", s.QUICControllerAppSamples),
		slog.Uint64("queqiao_quic_controller_state_misses_total", s.QUICControllerStateMisses),
		slog.Uint64("queqiao_quic_controller_zero_samples_total", s.QUICControllerZeroSamples),
		slog.Uint64("queqiao_quic_controller_round", s.QUICControllerRound),
		slog.Uint64("queqiao_quic_controller_pacing_rate_bytes_per_second", s.QUICControllerPacingRate),
		slog.Uint64("queqiao_quic_controller_congestion_window_bytes", s.QUICControllerCongestionWindow),
		slog.Uint64("queqiao_quic_controller_bytes_in_flight", s.QUICControllerBytesInFlight),
		slog.Uint64("queqiao_quic_controller_bytes_lost", s.QUICControllerBytesLost),
		slog.Uint64("queqiao_quic_controller_packets_lost", s.QUICControllerPacketsLost),
		slog.Float64("queqiao_quic_controller_min_rtt_seconds", s.QUICControllerMinRTT.Seconds()),
		slog.Float64("queqiao_erasure_ratio_send", s.QUICErasureSend),
		slog.Float64("queqiao_delay_brake_ratio", s.QUICDelayBrake),
		slog.Uint64("queqiao_quic_sample_mean_bytes_per_second", s.QUICSampleMean),
		slog.Uint64("queqiao_quic_sample_max_bytes_per_second", s.QUICSampleMax),
		slog.Uint64("queqiao_quic_sample_max_delivered_bytes", s.QUICSampleDelivered),
		slog.Float64("queqiao_quic_sample_max_interval_seconds", s.QUICSampleInterval.Seconds()),
		slog.Uint64("queqiao_coded_symbols_arrived_total", s.QUICCodedSources),
		slog.Uint64("queqiao_coded_symbols_recovered_total", s.QUICCodedRecovered),
		slog.Uint64("queqiao_coded_symbols_lost_total", s.QUICCodedLost),
		slog.Float64("queqiao_erasure_ratio_receive", s.ReceiveErasure()),
		slog.Float64("queqiao_erasure_residual_ratio_receive", s.ReceiveResidual()),
		slog.Bool("queqiao_quic_controller_in_recovery", s.QUICControllerInRecovery),
		// A refused lane join is a peer's flow about to fail. Flat names,
		// one per reason, matching the labelled /metrics series.
		slog.Uint64("queqiao_lane_join_refused_invalid_identity_total", s.LaneJoinRefusals[metrics.LaneJoinInvalidIdentity]),
		slog.Uint64("queqiao_lane_join_refused_unknown_session_total", s.LaneJoinRefusals[metrics.LaneJoinUnknownSession]),
		slog.Uint64("queqiao_lane_join_refused_flow_mismatch_total", s.LaneJoinRefusals[metrics.LaneJoinFlowMismatch]),
		slog.Uint64("queqiao_lane_join_refused_principal_mismatch_total", s.LaneJoinRefusals[metrics.LaneJoinPrincipalMismatch]),
		slog.Uint64("queqiao_lane_join_refused_invalid_control_replacement_total", s.LaneJoinRefusals[metrics.LaneJoinInvalidControlReplacement]),
		slog.Uint64("queqiao_lane_join_refused_lane_unavailable_total", s.LaneJoinRefusals[metrics.LaneJoinLaneUnavailable]),
		slog.Uint64("queqiao_class_transitions_0_total", s.ClassTransitions[0]),
		slog.Uint64("queqiao_class_transitions_1_total", s.ClassTransitions[1]),
		slog.Uint64("queqiao_class_transitions_2_total", s.ClassTransitions[2]),
		// The stall watchdog and its parallel rescue. rescue wins are flat,
		// one per attempt slot, matching the labelled /metrics series; a win
		// above slot zero is a sprayed dial beating the established strategy.
		slog.Uint64("queqiao_flow_stalls_detected_total", s.FlowStallsDetected),
		slog.Uint64("queqiao_stall_spare_attaches_total", s.StallSpareAttaches),
		slog.Uint64("queqiao_lane_rescue_attempts_total", s.LaneRescueAttempts),
		slog.Uint64("queqiao_lane_rescue_wins_0_total", s.LaneRescueWins[0]),
		slog.Uint64("queqiao_lane_rescue_wins_1_total", s.LaneRescueWins[1]),
		slog.Uint64("queqiao_lane_rescue_wins_2_total", s.LaneRescueWins[2]),
		slog.Uint64("queqiao_lane_grace_extensions_total", s.LaneGraceExtensions),
	)
}

func runLogs(args []string) error {
	roles := []string{"client", "server"}
	if len(args) > 1 {
		return errors.New("usage: queqiaod logs [client|server]")
	}
	if len(args) == 1 {
		if args[0] != "client" && args[0] != "server" {
			return errors.New("usage: queqiaod logs [client|server]")
		}
		roles = []string{args[0]}
	}
	for _, role := range roles {
		path, err := operlog.DefaultPath(role)
		if err != nil {
			return err
		}
		status := "not created yet"
		// path is produced by operlog.DefaultPath from a fixed role. Its only
		// variable directory is the local user's explicit QUEQIAO_LOG_DIR;
		// listing that user's chosen log is the purpose of this command.
		if info, err := os.Stat(path); err == nil { // #nosec G703 -- constrained by DefaultPath and fixed roles above.
			status = fmt.Sprintf("%d bytes", info.Size())
		} else if !errors.Is(err, os.ErrNotExist) {
			status = err.Error()
		}
		fmt.Printf("%s log\n  file: %s\n  status: %s\n", role, path, status)
		if runtime.GOOS == "windows" {
			fmt.Printf("  read: Get-Content -Tail 200 -Wait %q\n", path)
		} else {
			fmt.Printf("  read: tail -n 200 -f %q\n", path)
		}
	}
	return nil
}

func goVersion() string {
	if info, ok := debug.ReadBuildInfo(); ok {
		return info.GoVersion
	}
	return "unknown"
}

func serveMetrics(addr string, handler http.Handler, logger *slog.Logger) (func(), error) {
	if addr == "" {
		return func() {}, nil
	}
	listener, err := net.Listen("tcp", addr)
	if err != nil {
		return nil, fmt.Errorf("listen metrics endpoint: %w", err)
	}
	mux := http.NewServeMux()
	mux.Handle("/metrics", handler)
	server := &http.Server{Handler: mux, ReadHeaderTimeout: 5 * time.Second, IdleTimeout: 30 * time.Second}
	go func() {
		if err := server.Serve(listener); err != nil && !errors.Is(err, http.ErrServerClosed) {
			logger.Error("metrics endpoint stopped", "error", err)
		}
	}()
	return func() {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		_ = server.Shutdown(ctx)
	}, nil
}

// repeatedFlag collects a flag given more than once, in the order it was
// given, because for class hints that order is the policy: first match wins.
type repeatedFlag []string

func (r *repeatedFlag) String() string { return strings.Join(*r, ",") }

func (r *repeatedFlag) Set(v string) error {
	*r = append(*r, v)
	return nil
}
