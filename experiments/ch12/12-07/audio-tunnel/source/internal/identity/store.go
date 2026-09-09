package identity

import (
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"reflect"
	"sort"
	"strings"
	"sync"
	"time"
)

// DefaultAccountMaxFlows and DefaultAccountMaxClients are the policy a new
// account is created with.
//
// The flow ceiling is deliberately generous. One flow is one TCP connection or
// one UDP association, and a browser opens roughly six per host across dozens
// of hosts to load a single page; with the default flow idle timeout, its
// keep-alive connections keep holding those slots long after the page
// finished. A flow ceiling low enough to be interesting as a quota is
// therefore low enough to break ordinary browsing, and it breaks it in the
// least legible way available: most sites load and a few do not. The quota an
// operator actually wants is a device count, which is what MaxClients is.
const (
	DefaultAccountMaxFlows   = 1024
	DefaultAccountMaxClients = 8
)

// maxAccountLimit bounds both per-account limits. A hand-edited store cannot
// name a policy larger than the gateway could ever admit.
const maxAccountLimit = 1 << 16

// AccountLimits is one account's admission policy.
type AccountLimits struct {
	// MaxFlows is how many proxied flows the account may hold at once. Zero
	// defers to the gateway-wide session ceiling.
	MaxFlows int
	// MaxClients is how many of the account's enrolled devices may be
	// carrying flows at once. A device counts once however many flows it
	// holds, so this is the limit that expresses "this account is for eight
	// devices". Zero admits every enrolled device.
	MaxClients int
}

func (l AccountLimits) validate() error {
	if l.MaxFlows < 0 || l.MaxFlows > maxAccountLimit {
		return fmt.Errorf("account max flows must be between 0 and %d", maxAccountLimit)
	}
	if l.MaxClients < 0 || l.MaxClients > maxAccountLimit {
		return fmt.Errorf("account max clients must be between 0 and %d", maxAccountLimit)
	}
	return nil
}

type Account struct {
	ID         string `json:"id"`
	Name       string `json:"name"`
	Enabled    bool   `json:"enabled"`
	ExpiresAt  string `json:"expires_at,omitempty"`
	MaxFlows   int    `json:"max_flows,omitempty"`
	MaxClients int    `json:"max_clients,omitempty"`
	CreatedAt  string `json:"created_at"`
}

// Limits is this account's admission policy.
func (a Account) Limits() AccountLimits {
	return AccountLimits{MaxFlows: a.MaxFlows, MaxClients: a.MaxClients}
}

// accountJSON is the on-disk shape of an account. max_sessions is the name
// MaxFlows was written under before there was a device limit beside it; it is
// still read so an existing provider state survives this upgrade in place, and
// it is never written back. Unknown fields stay rejected here exactly as the
// store's own decoder rejects them: Refresh keeps the last known-good state
// when a replacement will not decode, so a field this build does not
// understand must fail loudly rather than be silently dropped on the next
// save.
type accountJSON struct {
	ID         string `json:"id"`
	Name       string `json:"name"`
	Enabled    bool   `json:"enabled"`
	ExpiresAt  string `json:"expires_at,omitempty"`
	MaxFlows   int    `json:"max_flows,omitempty"`
	MaxClients int    `json:"max_clients,omitempty"`
	// LegacyMaxSessions is read-only compatibility; see the type comment.
	LegacyMaxSessions int    `json:"max_sessions,omitempty"`
	CreatedAt         string `json:"created_at"`
}

func (a *Account) UnmarshalJSON(data []byte) error {
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.DisallowUnknownFields()
	var raw accountJSON
	if err := decoder.Decode(&raw); err != nil {
		return err
	}
	if raw.LegacyMaxSessions != 0 {
		if raw.MaxFlows != 0 && raw.MaxFlows != raw.LegacyMaxSessions {
			return errors.New("account carries conflicting max_flows and legacy max_sessions")
		}
		raw.MaxFlows = raw.LegacyMaxSessions
	}
	*a = Account{
		ID: raw.ID, Name: raw.Name, Enabled: raw.Enabled, ExpiresAt: raw.ExpiresAt,
		MaxFlows: raw.MaxFlows, MaxClients: raw.MaxClients, CreatedAt: raw.CreatedAt,
	}
	return nil
}

type Device struct {
	ID        string `json:"id"`
	AccountID string `json:"account_id"`
	Name      string `json:"name"`
	PublicKey string `json:"public_key"`
	Enabled   bool   `json:"enabled"`
	CreatedAt string `json:"created_at"`
	RevokedAt string `json:"revoked_at,omitempty"`
}

type InviteRecord struct {
	ID         string `json:"id"`
	AccountID  string `json:"account_id"`
	TokenHash  string `json:"token_hash"`
	ExpiresAt  string `json:"expires_at"`
	CreatedAt  string `json:"created_at"`
	ConsumedAt string `json:"consumed_at,omitempty"`
	DeviceID   string `json:"device_id,omitempty"`
}

type storeData struct {
	Version  int                     `json:"version"`
	Accounts map[string]Account      `json:"accounts"`
	Devices  map[string]Device       `json:"devices"`
	Invites  map[string]InviteRecord `json:"invites"`
}

// Principal is the immutable identity established by mutual TLS. Authorization
// remains a Store decision, so disabling an account or device does not require
// issuing a deliberately long-lived certificate carrying mutable policy.
type Principal struct {
	ProviderID string
	AccountID  string
	DeviceID   string
	PublicKey  ed25519.PublicKey
}

type Authorization struct {
	Account Account
	Device  Device
}

// Store is a transactionally replaced, in-memory authorization snapshot with
// a JSON persistence backend. It contains public keys and hashed invitation
// tokens only; no client private key or reusable shared tunnel secret is ever
// written to provider state.
type Store struct {
	path string
	mu   sync.RWMutex
	data storeData
	// lastGoodAt is when data was last replaced by a complete snapshot read
	// from disk. It is the only way to say how old the authorization state
	// being enforced actually is: when a refresh fails the previous snapshot
	// stays in force indefinitely, and without a timestamp a gateway that has
	// been serving stale rules for three days is indistinguishable from one
	// that missed a single tick.
	lastGoodAt time.Time
}

// A consumed invitation is retained after its advertised expiry so a client
// that durably saved its key but lost the enrollment response can recover.
// Only an exact retry of the original name and public key is accepted, so the
// retention does not let the bearer enroll a second device.
const consumedInviteRecoveryWindow = 7 * 24 * time.Hour

func NewStore(path string) (*Store, error) {
	if strings.TrimSpace(path) == "" {
		return nil, errors.New("authorization store path is required")
	}
	return &Store{path: path}, nil
}

func emptyStoreData() storeData {
	return storeData{
		Version:  ProviderStateVersion,
		Accounts: make(map[string]Account), Devices: make(map[string]Device),
		Invites: make(map[string]InviteRecord),
	}
}

func (s *Store) Initialize() error {
	release, err := s.beginWrite(true)
	if err != nil {
		return err
	}
	defer release()
	if _, err := os.Stat(s.path); err == nil {
		return fmt.Errorf("authorization store already exists: %s", s.path)
	} else if !errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("inspect authorization store: %w", err)
	}
	s.data = emptyStoreData()
	if err := s.saveLocked(); err != nil {
		return err
	}
	// A store just written is in force and current; without this a freshly
	// initialized provider would report a snapshot it had never read.
	s.lastGoodAt = time.Now()
	return nil
}

func (s *Store) Load() error {
	decoded, err := readStoreData(s.path)
	if err != nil {
		return err
	}
	s.mu.Lock()
	s.data, s.lastGoodAt = decoded, time.Now()
	s.mu.Unlock()
	return nil
}

// Refresh atomically adopts authorization changes written by provider CLI
// processes. Atomic file replacement guarantees readers see either the old or
// new complete snapshot; a malformed replacement is rejected and the last
// known-good authorization state remains active.
func (s *Store) Refresh() (bool, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	decoded, err := readStoreData(s.path)
	if err != nil {
		return false, err
	}
	// Record the read, not the change. An unchanged file was still read
	// successfully, and treating that as staleness would report every quiet
	// gateway as one that had lost its store.
	s.lastGoodAt = time.Now()
	if reflect.DeepEqual(decoded, s.data) {
		return false, nil
	}
	s.data = decoded
	return true, nil
}

// LastGoodAt reports when the in-memory authorization snapshot was last read
// from disk, or the zero time if it never has been. Enrollment refreshes the
// same snapshot under its own lock, so this is the authority on the snapshot's
// age rather than anything the refresh loop can track on its own.
func (s *Store) LastGoodAt() time.Time {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.lastGoodAt
}

func readStoreData(path string) (storeData, error) {
	info, err := os.Lstat(path)
	if err != nil {
		return storeData{}, fmt.Errorf("inspect authorization store: %w", err)
	}
	if err := checkPrivatePermissions(info); err != nil {
		return storeData{}, fmt.Errorf("authorization store: %w", err)
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return storeData{}, fmt.Errorf("read authorization store: %w", err)
	}
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.DisallowUnknownFields()
	var decoded storeData
	if err := decoder.Decode(&decoded); err != nil {
		return storeData{}, fmt.Errorf("decode authorization store: %w", err)
	}
	var trailing any
	if err := decoder.Decode(&trailing); !errors.Is(err, io.EOF) {
		return storeData{}, errors.New("authorization store contains trailing data")
	}
	if err := validateStoreData(decoded); err != nil {
		return storeData{}, fmt.Errorf("invalid authorization store: %w", err)
	}
	return decoded, nil
}

// ErrStoreUnavailable marks a failure to reach the authorization store rather
// than a decision the store made.
//
// The two are indistinguishable to a caller that sees only an error string,
// but they belong to different people. A rejected invitation is the enrolling
// user's problem; a store that cannot be opened is the operator's. Reporting
// the second as the first is how a gateway outage reaches an administrator as
// a user complaining about a bad invitation.
var ErrStoreUnavailable = errors.New("authorization store is unavailable")

// beginWrite serializes writers across both goroutines and provider CLI
// processes, then refreshes from disk before mutation. This prevents two
// administrators, enrollment, and a running gateway from silently replacing
// one another's account/device changes.
func (s *Store) beginWrite(initialize bool) (func(), error) {
	unlockFile, err := lockFile(s.path + ".lock")
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrStoreUnavailable, err)
	}
	s.mu.Lock()
	release := func() {
		s.mu.Unlock()
		unlockFile()
	}
	if initialize {
		return release, nil
	}
	decoded, err := readStoreData(s.path)
	if err != nil {
		release()
		return nil, fmt.Errorf("%w: %w", ErrStoreUnavailable, err)
	}
	s.data, s.lastGoodAt = decoded, time.Now()
	return release, nil
}

func (s *Store) AddAccount(name string, expiresAt time.Time, limits AccountLimits, now time.Time) (Account, error) {
	name = strings.TrimSpace(name)
	if name == "" || len(name) > 128 {
		return Account{}, errors.New("account name must contain 1-128 characters")
	}
	if err := limits.validate(); err != nil {
		return Account{}, err
	}
	if now.IsZero() {
		now = time.Now()
	}
	id, err := randomID()
	if err != nil {
		return Account{}, err
	}
	release, err := s.beginWrite(false)
	if err != nil {
		return Account{}, err
	}
	defer release()
	for _, account := range s.data.Accounts {
		if strings.EqualFold(account.Name, name) {
			return Account{}, fmt.Errorf("account name already exists: %s", name)
		}
	}
	account := Account{
		ID: id, Name: name, Enabled: true,
		MaxFlows: limits.MaxFlows, MaxClients: limits.MaxClients,
		CreatedAt: now.UTC().Format(time.RFC3339),
	}
	if !expiresAt.IsZero() {
		if !expiresAt.After(now) {
			return Account{}, errors.New("account expiration must be in the future")
		}
		account.ExpiresAt = expiresAt.UTC().Format(time.RFC3339)
		if account.ExpiresAt == account.CreatedAt {
			return Account{}, errors.New("account expiration must be at least one second in the future")
		}
	}
	s.data.Accounts[id] = account
	if err := s.saveLocked(); err != nil {
		delete(s.data.Accounts, id)
		return Account{}, err
	}
	return account, nil
}

func (s *Store) SetAccountEnabled(accountID string, enabled bool) error {
	release, err := s.beginWrite(false)
	if err != nil {
		return err
	}
	defer release()
	account, ok := s.data.Accounts[accountID]
	if !ok {
		return errors.New("unknown account")
	}
	old := account
	account.Enabled = enabled
	s.data.Accounts[accountID] = account
	if err := s.saveLocked(); err != nil {
		s.data.Accounts[accountID] = old
		return err
	}
	return nil
}

// SetAccountLimits replaces one account's admission policy. The gateway adopts
// it from disk within a second, so an operator who set a limit too low to
// browse through can correct it without deleting the account and losing every
// device enrolled against it.
func (s *Store) SetAccountLimits(accountID string, limits AccountLimits) error {
	if err := limits.validate(); err != nil {
		return err
	}
	release, err := s.beginWrite(false)
	if err != nil {
		return err
	}
	defer release()
	account, ok := s.data.Accounts[accountID]
	if !ok {
		return errors.New("unknown account")
	}
	old := account
	account.MaxFlows, account.MaxClients = limits.MaxFlows, limits.MaxClients
	s.data.Accounts[accountID] = account
	if err := s.saveLocked(); err != nil {
		s.data.Accounts[accountID] = old
		return err
	}
	return nil
}

func (s *Store) FindAccount(value string) (Account, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	if account, ok := s.data.Accounts[value]; ok {
		return account, true
	}
	for _, account := range s.data.Accounts {
		if strings.EqualFold(account.Name, value) {
			return account, true
		}
	}
	return Account{}, false
}

func (s *Store) Accounts() []Account {
	s.mu.RLock()
	defer s.mu.RUnlock()
	out := make([]Account, 0, len(s.data.Accounts))
	for _, account := range s.data.Accounts {
		out = append(out, account)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Name < out[j].Name })
	return out
}

// CreateInvite returns the plaintext bearer token exactly once. Only its
// SHA-256 digest is retained. The token has 256 random bits, so a fast digest
// is appropriate and avoids creating an attacker-controlled password-hashing
// workload on the public enrollment path.
func (s *Store) CreateInvite(accountID string, ttl time.Duration, now time.Time) (InviteRecord, string, error) {
	if ttl < time.Second || ttl > 7*24*time.Hour {
		return InviteRecord{}, "", errors.New("invitation lifetime must be between one second and 7 days")
	}
	if now.IsZero() {
		now = time.Now()
	}
	var tokenBytes [32]byte
	if _, err := rand.Read(tokenBytes[:]); err != nil {
		return InviteRecord{}, "", fmt.Errorf("generate invitation token: %w", err)
	}
	token := base64.RawURLEncoding.EncodeToString(tokenBytes[:])
	hash := sha256.Sum256(tokenBytes[:])
	id, err := randomID()
	if err != nil {
		return InviteRecord{}, "", err
	}
	release, err := s.beginWrite(false)
	if err != nil {
		return InviteRecord{}, "", err
	}
	defer release()
	if s.pruneInvitesLocked(now) {
		if err := s.saveLocked(); err != nil {
			return InviteRecord{}, "", err
		}
	}
	account, ok := s.data.Accounts[accountID]
	if !ok || !account.Enabled {
		return InviteRecord{}, "", errors.New("account is unknown or disabled")
	}
	if expired(account.ExpiresAt, now) {
		return InviteRecord{}, "", errors.New("account has expired")
	}
	record := InviteRecord{
		ID: id, AccountID: accountID,
		TokenHash: base64.RawURLEncoding.EncodeToString(hash[:]),
		ExpiresAt: now.Add(ttl).UTC().Format(time.RFC3339), CreatedAt: now.UTC().Format(time.RFC3339),
	}
	s.data.Invites[id] = record
	if err := s.saveLocked(); err != nil {
		delete(s.data.Invites, id)
		return InviteRecord{}, "", err
	}
	return record, token, nil
}

// EnrollDevice atomically validates and consumes an invitation, creates the
// device record, and invokes issue before committing either mutation. The
// callback must not call Store methods. This ordering ensures an issuer or
// persistence failure never consumes the user's one-time invitation.
func (s *Store) EnrollDevice(token, deviceName string, publicKey ed25519.PublicKey, now time.Time, issue func(Account, Device) ([]byte, error)) (Account, Device, []byte, error) {
	if now.IsZero() {
		now = time.Now()
	}
	deviceName = strings.TrimSpace(deviceName)
	if deviceName == "" || len(deviceName) > 128 {
		return Account{}, Device{}, nil, errors.New("device name must contain 1-128 characters")
	}
	if len(publicKey) != ed25519.PublicKeySize {
		return Account{}, Device{}, nil, errors.New("invalid device public key")
	}
	tokenBytes, err := base64.RawURLEncoding.DecodeString(token)
	if err != nil || len(tokenBytes) != 32 {
		return Account{}, Device{}, nil, errors.New("invalid invitation")
	}
	hash := sha256.Sum256(tokenBytes)
	hashText := base64.RawURLEncoding.EncodeToString(hash[:])
	publicText := base64.RawURLEncoding.EncodeToString(publicKey)

	release, err := s.beginWrite(false)
	if err != nil {
		return Account{}, Device{}, nil, err
	}
	defer release()
	if s.pruneInvitesLocked(now) {
		if err := s.saveLocked(); err != nil {
			return Account{}, Device{}, nil, err
		}
	}
	var invite InviteRecord
	found := false
	for _, candidate := range s.data.Invites {
		if subtle.ConstantTimeCompare([]byte(candidate.TokenHash), []byte(hashText)) == 1 {
			invite = candidate
			found = true
			break
		}
	}
	if !found || invite.ConsumedAt == "" && expired(invite.ExpiresAt, now) {
		return Account{}, Device{}, nil, errors.New("invitation is invalid, expired, or already used")
	}
	account, ok := s.data.Accounts[invite.AccountID]
	if !ok || !account.Enabled || expired(account.ExpiresAt, now) {
		return Account{}, Device{}, nil, errors.New("invitation account is unavailable")
	}
	// A response can be lost after durable consumption. Repeating the exact
	// same enrollment key/name is idempotent and reissues only that device's
	// certificate; changing either field remains a replay failure.
	if invite.ConsumedAt != "" {
		device, ok := s.data.Devices[invite.DeviceID]
		if !ok || device.AccountID != account.ID || device.Name != deviceName ||
			subtle.ConstantTimeCompare([]byte(device.PublicKey), []byte(publicText)) != 1 {
			return Account{}, Device{}, nil, errors.New("invitation is already used")
		}
		var credential []byte
		if issue != nil {
			credential, err = issue(account, device)
			if err != nil {
				return Account{}, Device{}, nil, err
			}
		}
		return account, device, credential, nil
	}
	for _, existing := range s.data.Devices {
		if subtle.ConstantTimeCompare([]byte(existing.PublicKey), []byte(publicText)) == 1 {
			return Account{}, Device{}, nil, errors.New("device key is already registered")
		}
	}
	deviceID, err := randomID()
	if err != nil {
		return Account{}, Device{}, nil, err
	}
	device := Device{
		ID: deviceID, AccountID: account.ID, Name: deviceName, PublicKey: publicText,
		Enabled: true, CreatedAt: now.UTC().Format(time.RFC3339),
	}
	var credential []byte
	if issue != nil {
		credential, err = issue(account, device)
		if err != nil {
			return Account{}, Device{}, nil, err
		}
	}
	oldInvite := invite
	invite.ConsumedAt = now.UTC().Format(time.RFC3339)
	invite.DeviceID = device.ID
	s.data.Invites[invite.ID] = invite
	s.data.Devices[device.ID] = device
	if err := s.saveLocked(); err != nil {
		s.data.Invites[invite.ID] = oldInvite
		delete(s.data.Devices, device.ID)
		return Account{}, Device{}, nil, err
	}
	return account, device, credential, nil
}

// ConsumeInvite is the storage-only form used by administrative tooling. Live
// enrollment should use EnrollDevice so certificate issuance is part of the
// same fail-closed transaction.
func (s *Store) ConsumeInvite(token, deviceName string, publicKey ed25519.PublicKey, now time.Time) (Account, Device, error) {
	account, device, _, err := s.EnrollDevice(token, deviceName, publicKey, now, nil)
	return account, device, err
}

func (s *Store) Authorize(principal Principal, now time.Time) (Authorization, error) {
	if now.IsZero() {
		now = time.Now()
	}
	s.mu.RLock()
	defer s.mu.RUnlock()
	account, ok := s.data.Accounts[principal.AccountID]
	if !ok || !account.Enabled || expired(account.ExpiresAt, now) {
		return Authorization{}, errors.New("account is disabled or expired")
	}
	device, ok := s.data.Devices[principal.DeviceID]
	if !ok || device.AccountID != account.ID || !device.Enabled || device.RevokedAt != "" {
		return Authorization{}, errors.New("device is revoked or unknown")
	}
	want, err := base64.RawURLEncoding.DecodeString(device.PublicKey)
	if err != nil || subtle.ConstantTimeCompare(want, principal.PublicKey) != 1 {
		return Authorization{}, errors.New("device certificate key does not match registration")
	}
	return Authorization{Account: account, Device: device}, nil
}

func (s *Store) RevokeDevice(deviceID string, now time.Time) error {
	if now.IsZero() {
		now = time.Now()
	}
	release, err := s.beginWrite(false)
	if err != nil {
		return err
	}
	defer release()
	device, ok := s.data.Devices[deviceID]
	if !ok {
		return errors.New("unknown device")
	}
	old := device
	device.Enabled = false
	device.RevokedAt = now.UTC().Format(time.RFC3339)
	s.data.Devices[deviceID] = device
	if err := s.saveLocked(); err != nil {
		s.data.Devices[deviceID] = old
		return err
	}
	return nil
}

func (s *Store) Devices(accountID string) []Device {
	s.mu.RLock()
	defer s.mu.RUnlock()
	out := make([]Device, 0)
	for _, device := range s.data.Devices {
		if accountID == "" || device.AccountID == accountID {
			out = append(out, device)
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i].CreatedAt < out[j].CreatedAt })
	return out
}

// Invites returns only unconsumed invitations. Tokens are never returned;
// providers can inspect and revoke an outstanding invitation by its random ID
// without turning the authorization database into a credential export.
func (s *Store) Invites(accountID string, now time.Time) []InviteRecord {
	if now.IsZero() {
		now = time.Now()
	}
	s.mu.RLock()
	defer s.mu.RUnlock()
	out := make([]InviteRecord, 0)
	for _, invitation := range s.data.Invites {
		if invitation.ConsumedAt == "" && !expired(invitation.ExpiresAt, now) &&
			(accountID == "" || invitation.AccountID == accountID) {
			invitation.TokenHash = ""
			out = append(out, invitation)
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i].CreatedAt < out[j].CreatedAt })
	return out
}

func (s *Store) RevokeInvite(invitationID string) error {
	release, err := s.beginWrite(false)
	if err != nil {
		return err
	}
	defer release()
	invitation, ok := s.data.Invites[invitationID]
	if !ok || invitation.ConsumedAt != "" {
		return errors.New("unknown or already-used invitation")
	}
	delete(s.data.Invites, invitationID)
	if err := s.saveLocked(); err != nil {
		s.data.Invites[invitationID] = invitation
		return err
	}
	return nil
}

func (s *Store) saveLocked() error {
	if err := validateStoreData(s.data); err != nil {
		return fmt.Errorf("refuse invalid authorization state: %w", err)
	}
	data, err := json.MarshalIndent(s.data, "", "  ")
	if err != nil {
		return fmt.Errorf("encode authorization store: %w", err)
	}
	if err := writeFileAtomic(s.path, append(data, '\n'), 0o600); err != nil {
		return fmt.Errorf("%w: %w", ErrStoreUnavailable, err)
	}
	return nil
}

func expired(text string, now time.Time) bool {
	if text == "" {
		return false
	}
	when, err := time.Parse(time.RFC3339, text)
	return err != nil || !now.Before(when)
}

func (s *Store) pruneInvitesLocked(now time.Time) bool {
	changed := false
	for id, invitation := range s.data.Invites {
		remove := invitation.ConsumedAt == "" && expired(invitation.ExpiresAt, now)
		if invitation.ConsumedAt != "" {
			consumed, err := time.Parse(time.RFC3339, invitation.ConsumedAt)
			remove = err != nil || !now.Before(consumed.Add(consumedInviteRecoveryWindow))
		}
		if remove {
			delete(s.data.Invites, id)
			changed = true
		}
	}
	return changed
}

func validateStoreData(data storeData) error {
	if data.Version != ProviderStateVersion || data.Accounts == nil || data.Devices == nil || data.Invites == nil {
		return errors.New("unsupported version or missing collections")
	}
	accountNames := make(map[string]struct{}, len(data.Accounts))
	for id, account := range data.Accounts {
		if id != account.ID || !validID(id) {
			return errors.New("account map key and identity do not match")
		}
		if account.Name != strings.TrimSpace(account.Name) || account.Name == "" || len(account.Name) > 128 {
			return fmt.Errorf("account %s has an invalid name", id)
		}
		folded := strings.ToLower(account.Name)
		if _, duplicate := accountNames[folded]; duplicate {
			return errors.New("account names are not unique")
		}
		accountNames[folded] = struct{}{}
		created, err := parseStateTime(account.CreatedAt)
		if err != nil || account.Limits().validate() != nil {
			return fmt.Errorf("account %s has invalid policy or timestamps", id)
		}
		if account.ExpiresAt != "" {
			expires, parseErr := parseStateTime(account.ExpiresAt)
			if parseErr != nil || !expires.After(created) {
				return fmt.Errorf("account %s has invalid expiration", id)
			}
		}
	}
	deviceKeys := make(map[string]struct{}, len(data.Devices))
	for id, device := range data.Devices {
		if id != device.ID || !validID(id) || !validID(device.AccountID) {
			return errors.New("device map key or identity is invalid")
		}
		if _, ok := data.Accounts[device.AccountID]; !ok {
			return fmt.Errorf("device %s refers to an unknown account", id)
		}
		if device.Name != strings.TrimSpace(device.Name) || device.Name == "" || len(device.Name) > 128 {
			return fmt.Errorf("device %s has an invalid name", id)
		}
		publicKey, err := base64.RawURLEncoding.DecodeString(device.PublicKey)
		if err != nil || len(publicKey) != ed25519.PublicKeySize {
			return fmt.Errorf("device %s has an invalid public key", id)
		}
		if _, duplicate := deviceKeys[device.PublicKey]; duplicate {
			return errors.New("device public keys are not unique")
		}
		deviceKeys[device.PublicKey] = struct{}{}
		created, err := parseStateTime(device.CreatedAt)
		if err != nil {
			return fmt.Errorf("device %s has an invalid creation time", id)
		}
		if device.Enabled && device.RevokedAt != "" {
			return fmt.Errorf("device %s is both enabled and revoked", id)
		}
		if device.RevokedAt != "" {
			revoked, parseErr := parseStateTime(device.RevokedAt)
			if parseErr != nil || revoked.Before(created) {
				return fmt.Errorf("device %s has an invalid revocation time", id)
			}
		}
	}
	inviteHashes := make(map[string]struct{}, len(data.Invites))
	for id, invitation := range data.Invites {
		if id != invitation.ID || !validID(id) || !validID(invitation.AccountID) {
			return errors.New("invitation map key or identity is invalid")
		}
		if _, ok := data.Accounts[invitation.AccountID]; !ok {
			return fmt.Errorf("invitation %s refers to an unknown account", id)
		}
		digest, err := base64.RawURLEncoding.DecodeString(invitation.TokenHash)
		if err != nil || len(digest) != sha256.Size {
			return fmt.Errorf("invitation %s has an invalid token digest", id)
		}
		if _, duplicate := inviteHashes[invitation.TokenHash]; duplicate {
			return errors.New("invitation token digests are not unique")
		}
		inviteHashes[invitation.TokenHash] = struct{}{}
		created, createdErr := parseStateTime(invitation.CreatedAt)
		expires, expiresErr := parseStateTime(invitation.ExpiresAt)
		if createdErr != nil || expiresErr != nil || !expires.After(created) || expires.After(created.Add(7*24*time.Hour+time.Second)) {
			return fmt.Errorf("invitation %s has invalid timestamps", id)
		}
		if (invitation.ConsumedAt == "") != (invitation.DeviceID == "") {
			return fmt.Errorf("invitation %s has incomplete consumption state", id)
		}
		if invitation.ConsumedAt != "" {
			consumed, parseErr := parseStateTime(invitation.ConsumedAt)
			device, ok := data.Devices[invitation.DeviceID]
			if parseErr != nil || consumed.Before(created) || !ok || device.AccountID != invitation.AccountID {
				return fmt.Errorf("invitation %s has invalid consumption state", id)
			}
		}
	}
	return nil
}

func parseStateTime(value string) (time.Time, error) {
	if value == "" {
		return time.Time{}, errors.New("timestamp is empty")
	}
	return time.Parse(time.RFC3339, value)
}
