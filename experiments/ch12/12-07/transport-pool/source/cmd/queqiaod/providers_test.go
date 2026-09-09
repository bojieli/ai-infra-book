package main

import (
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/x509"
	"encoding/binary"
	"encoding/json"
	"encoding/pem"
	"errors"
	"io"
	"log/slog"
	"net"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/pep"
)

func writeProviderManifest(t *testing.T, directory string, manifest providerManifest) string {
	t.Helper()
	data, err := json.Marshal(manifest)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(directory, "providers.json")
	if err := os.WriteFile(path, data, 0o600); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestProviderManifestRejectsDuplicateIdentityAndListeners(t *testing.T) {
	directory := t.TempDir()
	for name, entries := range map[string][]providerManifestEntry{
		"name": {
			{Name: "same", Profile: "one.json", Listen: "127.0.0.1:1081"},
			{Name: "same", Profile: "two.json", Listen: "127.0.0.1:1082"},
		},
		"listener": {
			{Name: "one", Profile: "one.json", Listen: "[::1]:1081"},
			{Name: "two", Profile: "two.json", Listen: "[0:0:0:0:0:0:0:1]:1081"},
		},
		"profile": {
			{Name: "one", Profile: "same.json", Listen: "127.0.0.1:1081"},
			{Name: "two", Profile: "same.json", Listen: "127.0.0.1:1082"},
		},
	} {
		t.Run(name, func(t *testing.T) {
			path := writeProviderManifest(t, directory, providerManifest{Version: 1, Providers: entries})
			if _, err := loadProviderClients(path); err == nil || !strings.Contains(err.Error(), "duplicate") {
				t.Fatalf("duplicate %s was not rejected: %v", name, err)
			}
		})
	}
}

func TestProviderManifestIsStrictAndRequiresLoopback(t *testing.T) {
	directory := t.TempDir()
	path := filepath.Join(directory, "providers.json")
	if err := os.WriteFile(path, []byte(`{"version":1,"unknown":true,"providers":[]}`), 0o600); err != nil {
		t.Fatal(err)
	}
	if _, err := loadProviderClients(path); err == nil || !strings.Contains(err.Error(), "unknown") {
		t.Fatalf("unknown manifest field was accepted: %v", err)
	}
	for _, address := range []string{"0.0.0.0:1080", "localhost:1080", "127.0.0.1:http", "127.0.0.1:0", "127.0.0.1:65536"} {
		if _, err := normalizeProviderListener(address); err == nil {
			t.Errorf("unsafe provider listener %q was accepted", address)
		}
	}
}

func TestTwoProviderClientsReachIndependentGateways(t *testing.T) {
	directory := t.TempDir()
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))

	destination, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer destination.Close()
	go echoProviderTestDestination(destination)

	servers := make([]*pep.Server, 2)
	stopServers := make([]context.CancelFunc, 2)
	defer func() {
		for _, stop := range stopServers {
			if stop != nil {
				stop()
			}
		}
	}()
	profiles := make([]string, 2)
	for i := range servers {
		gatewayListener, err := net.Listen("tcp", "127.0.0.1:0")
		if err != nil {
			t.Fatal(err)
		}
		provider, profile := providerTestProfile(t, directory, i, gatewayListener.Addr().String())
		profiles[i] = profile
		servers[i], err = pep.NewServer(pep.ServerConfig{
			ListenAddr: gatewayListener.Addr().String(), Credentials: provider.ServerCredentials(),
			EnableTCP: true, DestinationPolicy: pep.DestinationPolicy{AllowPrivate: true}, Logger: logger,
		})
		if err != nil {
			t.Fatal(err)
		}
		serverCtx, stopServer := context.WithCancel(context.Background())
		stopServers[i] = stopServer
		go func(server *pep.Server, listener net.Listener) {
			_ = server.ServeListener(serverCtx, listener)
		}(servers[i], gatewayListener)
	}

	clientAddresses := []string{unusedProviderTestAddress(t), unusedProviderTestAddress(t)}
	manifestPath := writeProviderManifest(t, directory, providerManifest{Version: 1, Providers: []providerManifestEntry{
		{Name: "one", Profile: filepath.Base(profiles[0]), Listen: clientAddresses[0]},
		{Name: "two", Profile: filepath.Base(profiles[1]), Listen: clientAddresses[1]},
	}})
	opts := parseRuntimeForTest(t, true, "--transport", "tcp", "--local-address", "127.0.0.1", "--telemetry-log-interval", "0")
	clientCtx, stopClients := context.WithCancel(context.Background())
	// Deferred as well as called below: a t.Fatalf between here and the
	// explicit stop would otherwise leave both SOCKS listeners bound for the
	// rest of the test binary and turn one failure into a cascade.
	defer stopClients()
	clientDone := make(chan error, 1)
	go func() { clientDone <- runProviderClientsContext(clientCtx, manifestPath, true, opts, logger) }()

	for i, address := range clientAddresses {
		runProviderTestFlow(t, address, destination.Addr().String())
		deadline := time.Now().Add(5 * time.Second)
		for servers[i].Metrics().Snapshot().FlowsCompleted == 0 && time.Now().Before(deadline) {
			time.Sleep(10 * time.Millisecond)
		}
		if servers[i].Metrics().Snapshot().FlowsCompleted != 1 {
			t.Fatalf("provider %d did not carry its SOCKS flow", i+1)
		}
		if i == 0 && servers[1].Metrics().Snapshot().FlowsStarted != 0 {
			t.Fatal("first provider SOCKS port sent traffic through the second gateway")
		}
		if i == 0 {
			stopServers[0]()
		}
	}
	stopClients()
	select {
	case err := <-clientDone:
		if err != nil {
			t.Fatalf("multi-provider client shutdown failed: %v", err)
		}
	case <-time.After(10 * time.Second):
		t.Fatal("multi-provider client did not close all listeners and pools")
	}
}

func TestProviderStartupClosesPreviouslyBoundListenersOnFailure(t *testing.T) {
	directory := t.TempDir()
	_, firstProfile := providerTestProfile(t, directory, 0, "127.0.0.1:1")
	_, secondProfile := providerTestProfile(t, directory, 1, "127.0.0.1:2")
	firstAddress := unusedProviderTestAddress(t)
	occupied, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer occupied.Close()
	manifestPath := writeProviderManifest(t, directory, providerManifest{Version: 1, Providers: []providerManifestEntry{
		{Name: "one", Profile: filepath.Base(firstProfile), Listen: firstAddress},
		{Name: "two", Profile: filepath.Base(secondProfile), Listen: occupied.Addr().String()},
	}})
	opts := parseRuntimeForTest(t, true, "--transport", "tcp", "--telemetry-log-interval", "0")
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	if err := runProviderClientsContext(context.Background(), manifestPath, true, opts, logger); err == nil || !strings.Contains(err.Error(), "bind provider") {
		t.Fatalf("occupied provider listener did not fail startup: %v", err)
	}
	rebound, err := net.Listen("tcp", firstAddress)
	if err != nil {
		t.Fatalf("first provider listener was not rolled back: %v", err)
	}
	_ = rebound.Close()
}

func TestProviderRuntimeStopCancelsSiblingClients(t *testing.T) {
	for _, test := range []struct {
		name     string
		firstErr error
		want     string
	}{
		{name: "listener error", firstErr: errors.New("accept failed"), want: "accept failed"},
		{name: "unexpected clean stop", want: "listener stopped unexpectedly"},
	} {
		t.Run(test.name, func(t *testing.T) {
			ctx, cancel := context.WithCancel(context.Background())
			results := make(chan providerServeResult, 2)
			done := make(chan error, 1)
			logger := slog.New(slog.NewTextHandler(io.Discard, nil))
			go func() { done <- waitProviderClients(ctx, cancel, results, 2, logger) }()

			results <- providerServeResult{name: "one", err: test.firstErr}
			select {
			case <-ctx.Done():
			case <-time.After(time.Second):
				t.Fatal("first stopped provider did not cancel its sibling")
			}
			results <- providerServeResult{name: "two"}
			select {
			case err := <-done:
				if err == nil || !strings.Contains(err.Error(), `provider "one" stopped`) || !strings.Contains(err.Error(), test.want) {
					t.Fatalf("runtime stop error = %v, want provider and cause", err)
				}
			case <-time.After(time.Second):
				t.Fatal("provider supervisor did not finish after sibling shutdown")
			}
		})
	}
}

func providerTestProfile(t *testing.T, directory string, index int, endpoint string) (*identity.Provider, string) {
	t.Helper()
	now := time.Now()
	provider, err := identity.InitProvider(filepath.Join(directory, "provider-"+string(rune('a'+index))), "Provider", endpoint, now)
	if err != nil {
		t.Fatal(err)
	}
	account, err := provider.Store.AddAccount("user", time.Time{}, identity.AccountLimits{}, now)
	if err != nil {
		t.Fatal(err)
	}
	_, invitation, err := provider.CreateInvitation(account.ID, time.Hour, now)
	if err != nil {
		t.Fatal(err)
	}
	publicKey, privateKey, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	_, device, err := provider.Store.ConsumeInvite(invitation.Token, "device", publicKey, now)
	if err != nil {
		t.Fatal(err)
	}
	certificate, err := provider.IssueDevice(account.ID, device.ID, publicKey, now)
	if err != nil {
		t.Fatal(err)
	}
	privateDER, err := x509.MarshalPKCS8PrivateKey(privateKey)
	if err != nil {
		t.Fatal(err)
	}
	profile := identity.ClientProfile{
		Version: identity.ProfileVersion, Name: provider.Metadata.Name,
		ProviderID: provider.Metadata.ProviderID, Endpoint: endpoint,
		GatewayID: provider.Metadata.GatewayID, RootPin: provider.Metadata.RootPin,
		RootCertificate: string(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: provider.RootCert.Raw})),
		AccountID:       account.ID, DeviceID: device.ID, DeviceName: "device",
		DeviceCertificate: string(certificate),
		DevicePrivateKey:  string(pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: privateDER})),
		CreatedAt:         now.UTC().Format(time.RFC3339),
	}
	path := filepath.Join(directory, "profile-"+string(rune('a'+index))+".json")
	if err := profile.SaveNew(path); err != nil {
		t.Fatal(err)
	}
	return provider, path
}

func unusedProviderTestAddress(t *testing.T) string {
	t.Helper()
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	address := listener.Addr().String()
	if err := listener.Close(); err != nil {
		t.Fatal(err)
	}
	return address
}

func echoProviderTestDestination(listener net.Listener) {
	for {
		conn, err := listener.Accept()
		if err != nil {
			return
		}
		go func() {
			defer conn.Close()
			_, _ = io.Copy(conn, conn)
		}()
	}
}

func runProviderTestFlow(t *testing.T, socksAddress, destination string) {
	t.Helper()
	deadline := time.Now().Add(10 * time.Second)
	var conn net.Conn
	var err error
	for time.Now().Before(deadline) {
		conn, err = net.DialTimeout("tcp", socksAddress, 100*time.Millisecond)
		if err == nil {
			break
		}
		time.Sleep(20 * time.Millisecond)
	}
	if err != nil {
		t.Fatalf("connect to SOCKS listener %s: %v", socksAddress, err)
	}
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(10 * time.Second))
	if _, err := conn.Write([]byte{5, 1, 0}); err != nil {
		t.Fatal(err)
	}
	var method [2]byte
	if _, err := io.ReadFull(conn, method[:]); err != nil || method != [2]byte{5, 0} {
		t.Fatalf("SOCKS method negotiation failed: %v, %v", method, err)
	}
	host, portText, err := net.SplitHostPort(destination)
	if err != nil {
		t.Fatal(err)
	}
	port, err := net.LookupPort("tcp", portText)
	if err != nil {
		t.Fatal(err)
	}
	request := []byte{5, 1, 0, 1}
	request = append(request, net.ParseIP(host).To4()...)
	request = binary.BigEndian.AppendUint16(request, uint16(port))
	if _, err := conn.Write(request); err != nil {
		t.Fatal(err)
	}
	var reply [10]byte
	if _, err := io.ReadFull(conn, reply[:]); err != nil || reply[1] != 0 {
		t.Fatalf("SOCKS connect failed: %x, %v", reply, err)
	}
	payload := []byte("provider-isolation")
	if _, err := conn.Write(payload); err != nil {
		t.Fatal(err)
	}
	got := make([]byte, len(payload))
	if _, err := io.ReadFull(conn, got); err != nil || string(got) != string(payload) {
		t.Fatalf("SOCKS payload round trip failed: %q, %v", got, err)
	}
}

func TestProviderManifestRejectsOneDeviceUnderTwoNames(t *testing.T) {
	for name, clone := range map[string]func(t *testing.T, source, target string){
		"copy": func(t *testing.T, source, target string) {
			data, err := os.ReadFile(source)
			if err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(target, data, 0o600); err != nil {
				t.Fatal(err)
			}
		},
		"symlink": func(t *testing.T, source, target string) {
			if err := os.Symlink(source, target); err != nil {
				t.Skipf("symlinks unavailable: %v", err)
			}
		},
		"hardlink": func(t *testing.T, source, target string) {
			if err := os.Link(source, target); err != nil {
				t.Skipf("hard links unavailable: %v", err)
			}
		},
	} {
		t.Run(name, func(t *testing.T) {
			directory := t.TempDir()
			_, profile := providerTestProfile(t, directory, 0, "127.0.0.1:1")
			duplicate := filepath.Join(directory, "duplicate.json")
			clone(t, profile, duplicate)
			manifestPath := writeProviderManifest(t, directory, providerManifest{Version: 1, Providers: []providerManifestEntry{
				{Name: "one", Profile: filepath.Base(profile), Listen: "127.0.0.1:1081"},
				{Name: "two", Profile: filepath.Base(duplicate), Listen: "127.0.0.1:1082"},
			}})
			if _, err := loadProviderClients(manifestPath); err == nil || !strings.Contains(err.Error(), "same enrolled device") {
				t.Fatalf("one device under two provider names was accepted: %v", err)
			}
		})
	}
}

func TestProviderManifestReportsUnsupportedVersionBeforeUnknownFields(t *testing.T) {
	directory := t.TempDir()
	path := filepath.Join(directory, "providers.json")
	// A manifest from a future build carries fields this build has never heard
	// of. The operator needs to be told the version is wrong, not the name of
	// whichever new field happened to be decoded first.
	if err := os.WriteFile(path, []byte(`{"version":2,"providers":[],"routing":"latency"}`), 0o600); err != nil {
		t.Fatal(err)
	}
	if _, err := loadProviderClients(path); err == nil || !strings.Contains(err.Error(), "unsupported provider manifest version 2") {
		t.Fatalf("future manifest version was misreported: %v", err)
	}
}

func TestProviderClientsShareOneAggregateBudgetAndSessionBudget(t *testing.T) {
	directory := t.TempDir()
	_, first := providerTestProfile(t, directory, 0, "127.0.0.1:1")
	_, second := providerTestProfile(t, directory, 1, "127.0.0.1:2")
	manifestPath := writeProviderManifest(t, directory, providerManifest{Version: 1, Providers: []providerManifestEntry{
		{Name: "one", Profile: filepath.Base(first), Listen: unusedProviderTestAddress(t)},
		{Name: "two", Profile: filepath.Base(second), Listen: unusedProviderTestAddress(t)},
	}})
	configs, err := loadProviderClients(manifestPath)
	if err != nil {
		t.Fatal(err)
	}
	opts := parseRuntimeForTest(t, true, "--transport", "tcp", "--aggregate-bytes-per-sec", "1000000", "--max-sessions", "8")
	limits, err := pep.NewSharedSessionLimits(opts.maxSessions, len(configs))
	if err != nil {
		t.Fatal(err)
	}
	budget := pep.NewAggregateBudget(opts.aggregateBytesPerSec, opts.interactiveReserveBytesPerSec)
	if budget == nil {
		t.Fatal("aggregate budget was not built from the runtime options")
	}
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	clients := make([]*pep.Client, len(configs))
	for i := range configs {
		clients[i], err = newRuntimeClient(configs[i].profile, configs[i].listen, opts, logger, nil, limits[i], budget)
		if err != nil {
			t.Fatal(err)
		}
	}
	// Two providers must not each be handed the whole session budget. Budget
	// sharing itself is asserted in the pep package, which can see the field.
	for i := range clients {
		if clients[i] == nil {
			t.Fatalf("provider %d client was not built", i)
		}
	}
	if limits[0].Reserved() != 2 || limits[1].Reserved() != 2 {
		t.Fatalf("session reservations = %d and %d, want the shared budget divided", limits[0].Reserved(), limits[1].Reserved())
	}
}
