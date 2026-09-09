package identity

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/base64"
	"errors"
	"net"
	"os"
	"path/filepath"
	"testing"
	"time"
)

// attemptEnrollment runs one enrollment over an in-memory pipe and returns
// what the gateway recorded alongside what the client was told.
func attemptEnrollment(t *testing.T, provider *Provider, token string) (EnrollmentResult, enrollmentResponse, error) {
	t.Helper()
	publicKey, _, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	serverConn, clientConn := net.Pipe()
	defer clientConn.Close()
	type served struct {
		result EnrollmentResult
		err    error
	}
	done := make(chan served, 1)
	go func() {
		defer serverConn.Close()
		result, serveErr := EnrollmentService{Provider: provider}.Serve(serverConn)
		done <- served{result, serveErr}
	}()
	_ = clientConn.SetDeadline(time.Now().Add(5 * time.Second))
	request := enrollmentRequest{
		Version: InvitationVersion, Token: token, DeviceName: "laptop",
		PublicKey: base64.RawURLEncoding.EncodeToString(publicKey),
	}
	if err := writeEnrollmentJSON(clientConn, request); err != nil {
		t.Fatal(err)
	}
	var response enrollmentResponse
	if raw, err := readEnrollmentMessage(clientConn); err == nil {
		if err := decodeStrictJSON(raw, &response); err != nil {
			t.Fatal(err)
		}
	}
	outcome := <-done
	return outcome.result, response, outcome.err
}

func mintInvitation(t *testing.T, provider *Provider) string {
	t.Helper()
	account, err := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{}, time.Now())
	if err != nil {
		t.Fatal(err)
	}
	_, invitation, err := provider.CreateInvitation(account.ID, time.Hour, time.Now())
	if err != nil {
		t.Fatal(err)
	}
	return invitation.Token
}

// The failure this whole change exists to prevent: a gateway that cannot read
// its own authorization store must not report that as a bad invitation. Every
// enrollment fails identically in both cases, so the wire message and the
// recorded outcome are the only things that can tell an operator which of the
// two is happening.
func TestEnrollmentSeparatesStoreOutageFromRejection(t *testing.T) {
	provider := testProvider(t, "127.0.0.1:443", time.Now())
	token := mintInvitation(t, provider)
	if err := os.Remove(filepath.Join(provider.Directory, authorizationFile)); err != nil {
		t.Fatal(err)
	}
	result, response, err := attemptEnrollment(t, provider, token)
	if result.Outcome != EnrollmentUnavailable {
		t.Fatalf("outcome is %q; want %q", result.Outcome, EnrollmentUnavailable)
	}
	if !errors.Is(err, ErrStoreUnavailable) {
		t.Fatalf("error %v does not identify an unavailable store", err)
	}
	if response.Error == "" {
		t.Fatal("client was told nothing")
	}
	// The client must not be told its invitation was judged, because it was not.
	if response.Error == "invitation is invalid, expired, or already used" {
		t.Fatalf("store outage was reported to the client as a bad invitation: %q", response.Error)
	}
}

// The other half: a real refusal must stay a refusal, and must not be
// attributed to the store. Otherwise the split above would just move the lie.
func TestEnrollmentRejectionIsNotBlamedOnTheStore(t *testing.T) {
	provider := testProvider(t, "127.0.0.1:443", time.Now())
	mintInvitation(t, provider)
	var bogus [32]byte
	if _, err := rand.Read(bogus[:]); err != nil {
		t.Fatal(err)
	}
	result, response, err := attemptEnrollment(t, provider, base64.RawURLEncoding.EncodeToString(bogus[:]))
	if result.Outcome != EnrollmentRejected {
		t.Fatalf("outcome is %q; want %q", result.Outcome, EnrollmentRejected)
	}
	if errors.Is(err, ErrStoreUnavailable) {
		t.Fatalf("a readable store was reported as unavailable: %v", err)
	}
	if response.Error != "invitation is invalid, expired, or already used" {
		t.Fatalf("client message is %q", response.Error)
	}
}

// A malformed request never reaches an invitation, so it must not be recorded
// as one being refused.
func TestEnrollmentMalformedTokenIsNotAnInvitationVerdict(t *testing.T) {
	provider := testProvider(t, "127.0.0.1:443", time.Now())
	mintInvitation(t, provider)
	result, _, _ := attemptEnrollment(t, provider, "not-base64url-32-bytes")
	if result.Outcome != EnrollmentRejected {
		t.Fatalf("outcome is %q; want %q", result.Outcome, EnrollmentRejected)
	}
}

// An acceptance has to carry the identifiers an operator needs to tie the new
// device to an account, since nothing else in the log will name it.
func TestEnrollmentAcceptanceCarriesIdentifiers(t *testing.T) {
	provider := testProvider(t, "127.0.0.1:443", time.Now())
	token := mintInvitation(t, provider)
	result, response, err := attemptEnrollment(t, provider, token)
	if err != nil {
		t.Fatal(err)
	}
	if result.Outcome != EnrollmentAccepted {
		t.Fatalf("outcome is %q; want %q", result.Outcome, EnrollmentAccepted)
	}
	if result.AccountID == "" || result.DeviceID == "" {
		t.Fatalf("acceptance is unattributable: %+v", result)
	}
	if result.DeviceName != "laptop" {
		t.Fatalf("device name is %q", result.DeviceName)
	}
	if response.DeviceCertificate == "" {
		t.Fatal("client received no certificate")
	}
}

// A rejected attempt must not carry anything the caller chose, so that a
// stranger cannot write into this gateway's log by attempting enrollments.
func TestRejectedEnrollmentCarriesNoCallerText(t *testing.T) {
	provider := testProvider(t, "127.0.0.1:443", time.Now())
	mintInvitation(t, provider)
	var bogus [32]byte
	if _, err := rand.Read(bogus[:]); err != nil {
		t.Fatal(err)
	}
	result, _, _ := attemptEnrollment(t, provider, base64.RawURLEncoding.EncodeToString(bogus[:]))
	if result.DeviceName != "" || result.AccountID != "" || result.DeviceID != "" {
		t.Fatalf("refused attempt carried caller-supplied detail: %+v", result)
	}
}
