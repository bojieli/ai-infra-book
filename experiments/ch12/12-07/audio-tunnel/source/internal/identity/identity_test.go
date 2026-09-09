package identity

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"encoding/pem"
	"errors"
	"net"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"testing"
	"time"
)

func testProvider(t *testing.T, endpoint string, now time.Time) *Provider {
	t.Helper()
	provider, err := InitProvider(filepath.Join(t.TempDir(), "provider"), "Example Provider", endpoint, now)
	if err != nil {
		t.Fatal(err)
	}
	return provider
}

func localProfile(t *testing.T, provider *Provider, account Account, deviceName string, issued time.Time) ClientProfile {
	t.Helper()
	_, invitation, err := provider.CreateInvitation(account.ID, time.Hour, time.Now())
	if err != nil {
		t.Fatal(err)
	}
	publicKey, privateKey, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	_, device, err := provider.Store.ConsumeInvite(invitation.Token, deviceName, publicKey, time.Now())
	if err != nil {
		t.Fatal(err)
	}
	certificate, err := provider.IssueDevice(account.ID, device.ID, publicKey, issued)
	if err != nil {
		t.Fatal(err)
	}
	return ClientProfile{
		Version: ProfileVersion, Name: provider.Metadata.Name,
		ProviderID: provider.Metadata.ProviderID, Endpoint: provider.Metadata.Endpoint,
		GatewayID: provider.Metadata.GatewayID, RootPin: provider.Metadata.RootPin,
		RootCertificate: string(encodeCertificate(provider.RootCert)),
		AccountID:       account.ID, DeviceID: device.ID, DeviceName: deviceName,
		DeviceCertificate: string(certificate), DevicePrivateKey: encodeProfilePrivateKey(privateKey),
		CreatedAt: issued.UTC().Format(time.RFC3339),
	}
}

func TestProviderStateIsPinnedPrivateAndCannotBeReinitialized(t *testing.T) {
	directory := filepath.Join(t.TempDir(), "provider")
	provider, err := InitProvider(directory, "Example", "127.0.0.1:443", time.Now())
	if err != nil {
		t.Fatal(err)
	}
	if _, err := InitProvider(directory, "Replacement", "127.0.0.1:443", time.Now()); err == nil {
		t.Fatal("provider trust root was silently replaced")
	}
	loaded, err := LoadProvider(directory)
	if err != nil {
		t.Fatal(err)
	}
	if loaded.Metadata.ProviderID != provider.Metadata.ProviderID || loaded.Metadata.RootPin != provider.Metadata.RootPin {
		t.Fatal("reloaded provider identity changed")
	}
	for _, name := range []string{rootKeyFile, gatewayCAKeyFile, deviceCAKeyFile, gatewayCertFile, providerFile, authorizationFile} {
		info, err := os.Stat(filepath.Join(directory, name))
		if err != nil {
			t.Fatal(err)
		}
		if err := checkPrivatePermissions(info); err != nil {
			t.Fatalf("%s is not private: %v", name, err)
		}
	}
}

func TestProviderRejectsPublicStateDirectoryOnUnix(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("Windows privacy is enforced through DACLs, not FileMode permission bits")
	}
	provider := testProvider(t, "127.0.0.1:443", time.Now())
	if err := os.Chmod(provider.Directory, 0o755); err != nil {
		t.Fatal(err)
	}
	_, err := LoadProvider(provider.Directory)
	if err == nil {
		t.Fatal("provider accepted a state directory readable by other users")
	}
	if !strings.Contains(err.Error(), "chmod 700") {
		t.Fatalf("permission error is not actionable: %v", err)
	}
}

func TestProviderRejectsMismatchedIssuerPrivateKey(t *testing.T) {
	provider := testProvider(t, "127.0.0.1:443", time.Now())
	wrongKey, err := os.ReadFile(filepath.Join(provider.Directory, gatewayCAKeyFile))
	if err != nil {
		t.Fatal(err)
	}
	if err := writeFileAtomic(filepath.Join(provider.Directory, deviceCAKeyFile), wrongKey, 0o600); err != nil {
		t.Fatal(err)
	}
	if _, err := LoadProvider(provider.Directory); err == nil {
		t.Fatal("provider accepted an issuer certificate with an unrelated private key")
	}
}

func TestInvitationIsCompactStrictExpiringAndOneTime(t *testing.T) {
	now := time.Now()
	provider := testProvider(t, "127.0.0.1:443", now)
	account, err := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{MaxFlows: 2}, now)
	if err != nil {
		t.Fatal(err)
	}
	uri, invitation, err := provider.CreateInvitation(account.ID, time.Hour, now)
	if err != nil {
		t.Fatal(err)
	}
	if len(uri) > 2048 || strings.Contains(uri, "PRIVATE") || strings.Contains(uri, "CERTIFICATE") {
		t.Fatalf("invitation is not a compact bearer URI: length=%d", len(uri))
	}
	parsed, err := ParseInvitation(uri, now)
	if err != nil || parsed != invitation {
		t.Fatalf("parse invitation: %v", err)
	}
	if _, err := ParseInvitation(uri, now.Add(2*time.Hour)); err == nil {
		t.Fatal("expired invitation was accepted")
	}

	var successes int
	var mu sync.Mutex
	var wg sync.WaitGroup
	for range 12 {
		wg.Add(1)
		go func() {
			defer wg.Done()
			publicKey, _, _ := ed25519.GenerateKey(rand.Reader)
			if _, _, err := provider.Store.ConsumeInvite(invitation.Token, "device", publicKey, now); err == nil {
				mu.Lock()
				successes++
				mu.Unlock()
			}
		}()
	}
	wg.Wait()
	if successes != 1 {
		t.Fatalf("concurrent one-time invitation succeeded %d times", successes)
	}
}

func TestIssuerFailureDoesNotConsumeInvitation(t *testing.T) {
	now := time.Now()
	provider := testProvider(t, "127.0.0.1:443", now)
	account, _ := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{}, now)
	_, invitation, _ := provider.CreateInvitation(account.ID, time.Hour, now)
	publicKey, _, _ := ed25519.GenerateKey(rand.Reader)
	if _, _, _, err := provider.Store.EnrollDevice(invitation.Token, "laptop", publicKey, now, func(Account, Device) ([]byte, error) {
		return nil, errors.New("issuer unavailable")
	}); err == nil {
		t.Fatal("issuer failure was accepted")
	}
	if _, _, _, err := provider.Store.EnrollDevice(invitation.Token, "laptop", publicKey, now, func(account Account, device Device) ([]byte, error) {
		return provider.IssueDevice(account.ID, device.ID, publicKey, now)
	}); err != nil {
		t.Fatalf("issuer failure consumed invitation: %v", err)
	}
}

func TestInterruptedEnrollmentIsIdempotentOnlyForTheSameClientKey(t *testing.T) {
	now := time.Now()
	provider := testProvider(t, "127.0.0.1:443", now)
	account, _ := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{}, now)
	_, invitation, _ := provider.CreateInvitation(account.ID, time.Hour, now)
	publicKey, _, _ := ed25519.GenerateKey(rand.Reader)
	issue := func(account Account, device Device) ([]byte, error) {
		return provider.IssueDevice(account.ID, device.ID, publicKey, now)
	}
	_, first, _, err := provider.Store.EnrollDevice(invitation.Token, "laptop", publicKey, now, issue)
	if err != nil {
		t.Fatal(err)
	}
	_, second, _, err := provider.Store.EnrollDevice(invitation.Token, "laptop", publicKey, now, issue)
	if err != nil || second.ID != first.ID {
		t.Fatalf("same-key retry was not idempotent: device=%s/%s err=%v", first.ID, second.ID, err)
	}
	otherKey, _, _ := ed25519.GenerateKey(rand.Reader)
	if _, _, _, err := provider.Store.EnrollDevice(invitation.Token, "laptop", otherKey, now, nil); err == nil {
		t.Fatal("consumed invitation accepted a different client key")
	}
}

func TestConsumedInvitationRecoversAfterItsOriginalExpiry(t *testing.T) {
	now := time.Now().UTC().Truncate(time.Second)
	provider := testProvider(t, "127.0.0.1:443", now)
	account, _ := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{}, now)
	_, invitation, _ := provider.CreateInvitation(account.ID, time.Minute, now)
	publicKey, _, _ := ed25519.GenerateKey(rand.Reader)
	issue := func(account Account, device Device) ([]byte, error) {
		return provider.IssueDevice(account.ID, device.ID, publicKey, now)
	}
	_, first, _, err := provider.Store.EnrollDevice(invitation.Token, "laptop", publicKey, now, issue)
	if err != nil {
		t.Fatal(err)
	}
	retryTime := now.Add(2 * time.Minute)
	_, second, _, err := provider.Store.EnrollDevice(invitation.Token, "laptop", publicKey, retryTime, issue)
	if err != nil || second.ID != first.ID {
		t.Fatalf("exact interrupted retry after expiry failed: device=%s/%s err=%v", first.ID, second.ID, err)
	}
	draft := EnrollmentDraft{
		Version: EnrollmentDraftVersion, Invitation: invitation, DeviceName: "laptop",
	}
	_, draftKey, _ := ed25519.GenerateKey(rand.Reader)
	draft.DevicePrivateKey = encodeProfilePrivateKey(draftKey)
	if _, err := draft.privateKey(); err != nil {
		t.Fatalf("recoverable draft rejected only because invitation expired: %v", err)
	}
	otherKey, _, _ := ed25519.GenerateKey(rand.Reader)
	if _, _, _, err := provider.Store.EnrollDevice(invitation.Token, "laptop", otherKey, retryTime, nil); err == nil {
		t.Fatal("expired consumed invitation accepted another key")
	}
}

func TestProviderCanListAndRevokeOutstandingInvitations(t *testing.T) {
	now := time.Now().UTC().Truncate(time.Second)
	provider := testProvider(t, "127.0.0.1:443", now)
	account, _ := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{}, now)
	record, token, err := provider.Store.CreateInvite(account.ID, time.Hour, now)
	if err != nil {
		t.Fatal(err)
	}
	listed := provider.Store.Invites(account.ID, now)
	if len(listed) != 1 || listed[0].ID != record.ID || listed[0].TokenHash != "" {
		t.Fatalf("outstanding invitation listing leaked or omitted data: %+v", listed)
	}
	if err := provider.Store.RevokeInvite(record.ID); err != nil {
		t.Fatal(err)
	}
	publicKey, _, _ := ed25519.GenerateKey(rand.Reader)
	if _, _, err := provider.Store.ConsumeInvite(token, "laptop", publicKey, now); err == nil {
		t.Fatal("revoked invitation was consumed")
	}
}

func TestEnrollmentDraftPreservesKeyAcrossRestart(t *testing.T) {
	provider := testProvider(t, "127.0.0.1:443", time.Now())
	account, _ := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{}, time.Now())
	_, invitation, _ := provider.CreateInvitation(account.ID, time.Hour, time.Now())
	draft, err := NewEnrollmentDraft(invitation, "laptop")
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "profile.enrolling")
	if err := draft.Save(path); err != nil {
		t.Fatal(err)
	}
	loaded, err := LoadEnrollmentDraft(path)
	if err != nil {
		t.Fatal(err)
	}
	firstKey, _ := draft.privateKey()
	secondKey, _ := loaded.privateKey()
	if !firstKey.Equal(secondKey) || loaded.Invitation != invitation || loaded.DeviceName != "laptop" {
		t.Fatal("enrollment draft changed across save/load")
	}
}

func TestProfilesAreSelfContainedStrictAndPrivate(t *testing.T) {
	now := time.Now()
	provider := testProvider(t, "127.0.0.1:443", now)
	account, _ := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{}, now)
	profile := localProfile(t, provider, account, "laptop", now)
	path := filepath.Join(t.TempDir(), "profile.json")
	if err := profile.Save(path); err != nil {
		t.Fatal(err)
	}
	info, _ := os.Stat(path)
	// Windows reports synthetic 0666 permission bits even when the inherited
	// DACL is private; checkPrivatePermissions covers its meaningful checks.
	if runtime.GOOS != "windows" && info.Mode().Perm()&0o077 != 0 {
		t.Fatalf("profile permissions = %03o", info.Mode().Perm())
	}
	loaded, err := LoadClientProfile(path)
	if err != nil {
		t.Fatal(err)
	}
	if loaded.Endpoint != provider.Metadata.Endpoint {
		t.Fatal("profile did not carry endpoint")
	}
	if err := os.Chmod(path, 0o644); err != nil {
		t.Fatal(err)
	}
	if _, err := LoadClientProfile(path); err == nil && runtime.GOOS != "windows" {
		t.Fatal("world-readable private profile was accepted")
	}

	data, _ := json.Marshal(profile)
	data = append(data, []byte("{}")...)
	strictPath := filepath.Join(t.TempDir(), "trailing.json")
	if err := os.WriteFile(strictPath, data, 0o600); err != nil {
		t.Fatal(err)
	}
	if _, err := LoadClientProfile(strictPath); err == nil {
		t.Fatal("profile with trailing JSON was accepted")
	}
	profile.RootPin = base64.RawURLEncoding.EncodeToString(make([]byte, 32))
	if _, err := profile.Credentials(); err == nil {
		t.Fatal("profile with substituted root pin was accepted")
	}
}

func tlsHandshake(t *testing.T, serverConfig, clientConfig *tls.Config) error {
	t.Helper()
	serverRaw, clientRaw := net.Pipe()
	defer serverRaw.Close()
	defer clientRaw.Close()
	server := tls.Server(serverRaw, serverConfig)
	client := tls.Client(clientRaw, clientConfig)
	deadline := time.Now().Add(3 * time.Second)
	_ = server.SetDeadline(deadline)
	_ = client.SetDeadline(deadline)
	serverResult := make(chan error, 1)
	go func() { serverResult <- server.Handshake() }()
	clientErr := client.Handshake()
	serverErr := <-serverResult
	if clientErr != nil {
		return clientErr
	}
	return serverErr
}

func TestMutualTLSRequiresAnAuthorizedDeviceAndPinnedGateway(t *testing.T) {
	now := time.Now()
	provider := testProvider(t, "127.0.0.1:443", now)
	account, _ := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{}, now)
	profile := localProfile(t, provider, account, "laptop", now)
	clientCredentials, _ := profile.Credentials()
	serverConfig, err := ServerTLSConfig(provider.ServerCredentials(), "queqiao/1", false)
	if err != nil {
		t.Fatal(err)
	}
	clientConfig, _ := ClientTLSConfig(clientCredentials, "queqiao/1")
	if err := tlsHandshake(t, serverConfig, clientConfig); err != nil {
		t.Fatalf("authorized mutual TLS failed: %v", err)
	}
	withoutDevice := EnrollmentTLSConfig(provider.Metadata.RootPin, provider.Metadata.ProviderID, provider.Metadata.GatewayID)
	withoutDevice.NextProtos = []string{"queqiao/1"}
	if err := tlsHandshake(t, serverConfig, withoutDevice); err == nil {
		t.Fatal("client without a device certificate was accepted")
	}
	wrongGateway := clientCredentials
	wrongGateway.GatewayID = strings.Repeat("a", 32)
	wrongGatewayConfig, err := ClientTLSConfig(wrongGateway, "queqiao/1")
	if err != nil {
		t.Fatal(err)
	}
	if err := tlsHandshake(t, serverConfig, wrongGatewayConfig); err == nil {
		t.Fatal("gateway with the wrong pinned URI identity was accepted")
	}
	if err := provider.Store.RevokeDevice(profile.DeviceID, time.Now()); err != nil {
		t.Fatal(err)
	}
	if err := tlsHandshake(t, serverConfig, clientConfig); err == nil {
		t.Fatal("revoked device was accepted")
	}
	other := testProvider(t, "127.0.0.1:443", now)
	wrongPin := clientCredentials
	wrongPin.Root, wrongPin.RootPin, wrongPin.ProviderID = other.RootCert, other.Metadata.RootPin, other.Metadata.ProviderID
	wrongConfig, _ := ClientTLSConfig(wrongPin, "queqiao/1")
	if wrongConfig != nil && tlsHandshake(t, serverConfig, wrongConfig) == nil {
		t.Fatal("gateway was accepted under another provider root")
	}
}

func TestEnrollmentEndToEndAndReplayFails(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	provider := testProvider(t, listener.Addr().String(), time.Now())
	account, _ := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{}, time.Now())
	uri, invitation, err := provider.CreateInvitation(account.ID, time.Hour, time.Now())
	if err != nil {
		t.Fatal(err)
	}
	if _, err := ParseInvitation(uri, time.Now()); err != nil {
		t.Fatal(err)
	}
	serverConfig, _ := ServerTLSConfig(provider.ServerCredentials(), "queqiao/1", true)
	service := EnrollmentService{Provider: provider}
	serveOne := func() {
		raw, acceptErr := listener.Accept()
		if acceptErr != nil {
			return
		}
		defer raw.Close()
		conn := tls.Server(raw, serverConfig)
		_ = conn.SetDeadline(time.Now().Add(3 * time.Second))
		if conn.Handshake() == nil {
			_, _ = service.Serve(conn)
		}
	}
	go serveOne()
	profile, err := EnrollWithOptions(context.Background(), invitation, "laptop", DialOptions{Timeout: 3 * time.Second, LocalAddress: "127.0.0.1"})
	if err != nil {
		t.Fatal(err)
	}
	if _, err := profile.Credentials(); err != nil {
		t.Fatalf("enrolled profile is invalid: %v", err)
	}
	go serveOne()
	if _, err := Enroll(context.Background(), invitation, "other device", 3*time.Second); err == nil {
		t.Fatal("invitation replay enrolled another device")
	}
}

func TestEnrollmentRejectsInvalidLocalAddressBeforeDial(t *testing.T) {
	provider := testProvider(t, "127.0.0.1:443", time.Now())
	account, _ := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{}, time.Now())
	_, invitation, err := provider.CreateInvitation(account.ID, time.Hour, time.Now())
	if err != nil {
		t.Fatal(err)
	}
	draft, err := NewEnrollmentDraft(invitation, "laptop")
	if err != nil {
		t.Fatal(err)
	}
	_, err = draft.EnrollWithOptions(context.Background(), DialOptions{Timeout: time.Second, LocalAddress: "if:"})
	if err == nil || !strings.Contains(err.Error(), "--local-address") || !strings.Contains(err.Error(), "interface name") {
		t.Fatalf("invalid source produced unhelpful error: %v", err)
	}
}

func TestEnrollmentExplainsProtocolALPNMismatch(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	provider := testProvider(t, listener.Addr().String(), time.Now())
	account, _ := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{}, time.Now())
	_, invitation, err := provider.CreateInvitation(account.ID, time.Hour, time.Now())
	if err != nil {
		t.Fatal(err)
	}
	serverConfig := &tls.Config{
		Certificates: []tls.Certificate{provider.GatewayCert},
		MinVersion:   tls.VersionTLS13,
		MaxVersion:   tls.VersionTLS13,
		NextProtos:   []string{"not-queqiao"},
	}
	go func() {
		raw, acceptErr := listener.Accept()
		if acceptErr != nil {
			return
		}
		defer raw.Close()
		_ = tls.Server(raw, serverConfig).Handshake()
	}()
	_, err = EnrollWithOptions(context.Background(), invitation, "laptop", DialOptions{Timeout: 3 * time.Second, LocalAddress: "127.0.0.1"})
	if err == nil || !strings.Contains(err.Error(), "does not support Queqiao enrollment") || !strings.Contains(err.Error(), "protocol 1") {
		t.Fatalf("ALPN mismatch produced unhelpful error: %v", err)
	}
}

func TestRenewalPreservesDeviceAndRejectsRevocation(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	provider := testProvider(t, listener.Addr().String(), time.Now().Add(-24*24*time.Hour))
	account, _ := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{}, time.Now())
	profile := localProfile(t, provider, account, "laptop", time.Now().Add(-24*24*time.Hour))
	needs, err := profile.NeedsRenewal(time.Now(), 7*24*time.Hour)
	if err != nil || !needs {
		t.Fatalf("near-expiry profile needs renewal=%t err=%v", needs, err)
	}
	serverConfig, _ := ServerTLSConfig(provider.ServerCredentials(), "queqiao/1", true)
	service := EnrollmentService{Provider: provider}
	serveRenewal := func() {
		raw, acceptErr := listener.Accept()
		if acceptErr != nil {
			return
		}
		defer raw.Close()
		conn := tls.Server(raw, serverConfig)
		_ = conn.SetDeadline(time.Now().Add(3 * time.Second))
		if conn.Handshake() == nil {
			principal, principalErr := PrincipalFromTLS(conn.ConnectionState())
			if principalErr == nil {
				_, _ = service.Renew(conn, principal)
			}
		}
	}
	go serveRenewal()
	renewed, err := RenewProfileWithOptions(context.Background(), profile, DialOptions{Timeout: 3 * time.Second, LocalAddress: "127.0.0.1"})
	if err != nil {
		t.Fatal(err)
	}
	if renewed.DeviceID != profile.DeviceID || renewed.DevicePrivateKey != profile.DevicePrivateKey || renewed.DeviceCertificate == profile.DeviceCertificate {
		t.Fatal("renewal changed the device identity/key or failed to rotate the certificate")
	}
	if err := provider.Store.RevokeDevice(profile.DeviceID, time.Now()); err != nil {
		t.Fatal(err)
	}
	go serveRenewal()
	if _, err := RenewProfile(context.Background(), renewed, 3*time.Second); err == nil {
		t.Fatal("revoked device renewed its certificate")
	}
}

func TestAuthorizationRefreshKeepsLastKnownGoodState(t *testing.T) {
	now := time.Now()
	provider := testProvider(t, "127.0.0.1:443", now)
	account, _ := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{}, now)
	reader, err := NewStore(filepath.Join(provider.Directory, authorizationFile))
	if err != nil || reader.Load() != nil {
		t.Fatal(err)
	}
	if err := provider.Store.SetAccountEnabled(account.ID, false); err != nil {
		t.Fatal(err)
	}
	changed, err := reader.Refresh()
	if err != nil || !changed {
		t.Fatalf("refresh changed=%t err=%v", changed, err)
	}
	if refreshed, _ := reader.FindAccount(account.ID); refreshed.Enabled {
		t.Fatal("refresh did not adopt revocation")
	}
	if err := os.WriteFile(filepath.Join(provider.Directory, authorizationFile), []byte("{"), 0o600); err != nil {
		t.Fatal(err)
	}
	if _, err := reader.Refresh(); err == nil {
		t.Fatal("malformed authorization replacement was accepted")
	}
	if refreshed, _ := reader.FindAccount(account.ID); refreshed.Enabled {
		t.Fatal("malformed refresh replaced last known-good state")
	}
}

func TestAuthorizationStoreRejectsUnknownAndInconsistentFields(t *testing.T) {
	provider := testProvider(t, "127.0.0.1:443", time.Now())
	path := filepath.Join(provider.Directory, authorizationFile)
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	unknown := bytes.Replace(data, []byte(`"version": 1,`), []byte(`"version": 1, "unexpected": true,`), 1)
	if bytes.Equal(unknown, data) {
		t.Fatal("test did not alter authorization JSON")
	}
	if err := os.WriteFile(path, unknown, 0o600); err != nil {
		t.Fatal(err)
	}
	store, _ := NewStore(path)
	if err := store.Load(); err == nil {
		t.Fatal("authorization store accepted an unknown field")
	}
}

// A provider state written before the flow limit was renamed still calls it
// max_sessions. The store rejects unknown fields and keeps the last known-good
// state when a replacement will not decode, so failing to read the old name
// would not degrade gracefully: it would leave a running gateway pinned to
// stale authorization and a provider CLI unable to load the state at all.
func TestLegacyMaxSessionsIsReadAsTheFlowLimit(t *testing.T) {
	provider := testProvider(t, "127.0.0.1:443", time.Now())
	path := filepath.Join(provider.Directory, authorizationFile)
	if _, err := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{MaxFlows: 16}, time.Now()); err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	legacy := bytes.Replace(data, []byte(`"max_flows"`), []byte(`"max_sessions"`), 1)
	if bytes.Equal(legacy, data) {
		t.Fatal("test did not rewrite the flow limit to its old name")
	}
	if err := os.WriteFile(path, legacy, 0o600); err != nil {
		t.Fatal(err)
	}
	store, _ := NewStore(path)
	if err := store.Load(); err != nil {
		t.Fatalf("state naming the flow limit max_sessions did not load: %v", err)
	}
	account, ok := store.FindAccount("alice")
	if !ok || account.MaxFlows != 16 {
		t.Fatalf("legacy limit read as %d, want 16", account.MaxFlows)
	}
	// The old name is compatibility on read only. Saving must write the
	// current one so the store has a single spelling of the limit.
	if err := store.SetAccountEnabled(account.ID, false); err != nil {
		t.Fatal(err)
	}
	saved, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if bytes.Contains(saved, []byte(`"max_sessions"`)) {
		t.Fatal("saving rewrote the flow limit under its old name")
	}
	if !bytes.Contains(saved, []byte(`"max_flows"`)) {
		t.Fatal("saving dropped the flow limit")
	}
}

// Both spellings at once is a state nobody can have written on purpose, and
// guessing which one the operator meant is guessing at a security policy.
func TestConflictingFlowLimitSpellingsAreRejected(t *testing.T) {
	provider := testProvider(t, "127.0.0.1:443", time.Now())
	path := filepath.Join(provider.Directory, authorizationFile)
	if _, err := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{MaxFlows: 16}, time.Now()); err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	both := bytes.Replace(data, []byte(`"max_flows": 16`), []byte(`"max_flows": 16, "max_sessions": 8`), 1)
	if bytes.Equal(both, data) {
		t.Fatal("test did not add the conflicting field")
	}
	if err := os.WriteFile(path, both, 0o600); err != nil {
		t.Fatal(err)
	}
	store, _ := NewStore(path)
	if err := store.Load(); err == nil {
		t.Fatal("a store naming two different flow limits was accepted")
	}
}

// An operator who set a limit too low must be able to correct it in place. The
// alternative is deleting the account, which deletes every device enrolled
// against it.
func TestSetAccountLimitsIsAdoptedByAReader(t *testing.T) {
	now := time.Now()
	provider := testProvider(t, "127.0.0.1:443", now)
	account, err := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{MaxFlows: 16, MaxClients: 2}, now)
	if err != nil {
		t.Fatal(err)
	}
	reader, err := NewStore(filepath.Join(provider.Directory, authorizationFile))
	if err != nil || reader.Load() != nil {
		t.Fatal(err)
	}
	if err := provider.Store.SetAccountLimits(account.ID, AccountLimits{MaxFlows: 0, MaxClients: 8}); err != nil {
		t.Fatal(err)
	}
	changed, err := reader.Refresh()
	if err != nil || !changed {
		t.Fatalf("refresh changed=%t err=%v", changed, err)
	}
	updated, _ := reader.FindAccount(account.ID)
	if updated.MaxFlows != 0 || updated.MaxClients != 8 {
		t.Fatalf("limits after refresh = %+v, want flows 0 and clients 8", updated.Limits())
	}
	if err := provider.Store.SetAccountLimits(account.ID, AccountLimits{MaxFlows: -1}); err == nil {
		t.Fatal("a negative flow limit was accepted")
	}
	if err := provider.Store.SetAccountLimits("unknown", AccountLimits{}); err == nil {
		t.Fatal("limits were set on an unknown account")
	}
}

func TestIndependentProviderProcessesDoNotLoseConcurrentUpdates(t *testing.T) {
	path := filepath.Join(t.TempDir(), "authorization.json")
	first, _ := NewStore(path)
	if err := first.Initialize(); err != nil {
		t.Fatal(err)
	}
	second, _ := NewStore(path)
	if err := second.Load(); err != nil {
		t.Fatal(err)
	}
	start := make(chan struct{})
	results := make(chan error, 2)
	for index, store := range []*Store{first, second} {
		index, store := index, store
		go func() {
			<-start
			_, err := store.AddAccount([]string{"alice", "bob"}[index], time.Time{}, AccountLimits{}, time.Now())
			results <- err
		}()
	}
	close(start)
	for range 2 {
		if err := <-results; err != nil {
			t.Fatal(err)
		}
	}
	loaded, _ := NewStore(path)
	if err := loaded.Load(); err != nil {
		t.Fatal(err)
	}
	if accounts := loaded.Accounts(); len(accounts) != 2 {
		t.Fatalf("concurrent provider updates retained %d accounts, want 2", len(accounts))
	}
}

func TestCertificateRolesCannotBeSwapped(t *testing.T) {
	provider := testProvider(t, "127.0.0.1:443", time.Now())
	leaves := provider.GatewayCert.Certificate
	if len(leaves) == 0 {
		t.Fatal("missing gateway leaf")
	}
	gateway, _ := x509.ParseCertificate(leaves[0])
	if _, err := PrincipalFromCertificate(gateway); err == nil {
		t.Fatal("gateway certificate was parsed as a device principal")
	}
	block, _ := pem.Decode(encodeCertificate(provider.RootCert))
	root, _ := x509.ParseCertificate(block.Bytes)
	if _, err := PrincipalFromCertificate(root); err == nil {
		t.Fatal("provider root was parsed as a device principal")
	}
}

func TestGatewayRenewalIsVisibleToExistingTLSConfiguration(t *testing.T) {
	now := time.Now().UTC().Truncate(time.Second)
	provider := testProvider(t, "127.0.0.1:443", now)
	account, _ := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{}, now)
	profile := localProfile(t, provider, account, "laptop", now)
	clientCredentials, err := profile.Credentials()
	if err != nil {
		t.Fatal(err)
	}
	serverConfig, err := ServerTLSConfig(provider.ServerCredentials(), "queqiao/1", false)
	if err != nil {
		t.Fatal(err)
	}
	before := append([]byte(nil), provider.GatewayCertificate().Certificate[0]...)
	renewed, err := provider.RenewGatewayIdentity(now.Add(time.Second), 31*24*time.Hour)
	if err != nil || !renewed {
		t.Fatalf("force gateway renewal: renewed=%t err=%v", renewed, err)
	}
	after := provider.GatewayCertificate().Certificate[0]
	if bytes.Equal(before, after) {
		t.Fatal("gateway renewal retained the old leaf")
	}
	clientConfig, err := ClientTLSConfig(clientCredentials, "queqiao/1")
	if err != nil {
		t.Fatal(err)
	}
	if err := tlsHandshake(t, serverConfig, clientConfig); err != nil {
		t.Fatalf("TLS config created before renewal did not serve the renewed identity: %v", err)
	}
}
