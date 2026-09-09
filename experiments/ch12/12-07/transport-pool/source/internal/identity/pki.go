// Package identity implements Queqiao's provider trust domain, device
// identities, enrollment profiles, and TLS authentication.
//
// Users never handle X.509 objects directly. A provider root is the stable
// trust anchor carried by an invitation, gateway and device certificates are
// issued automatically, and every normal transport is mutually authenticated.
package identity

import (
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"errors"
	"fmt"
	"math/big"
	"net"
	"net/url"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"
)

const (
	ProviderStateVersion = 1
	defaultGatewayTTL    = 30 * 24 * time.Hour
	defaultDeviceTTL     = 30 * 24 * time.Hour
	certificateClockSkew = 5 * time.Minute
)

const (
	providerFile      = "provider.json"
	rootCertFile      = "provider-root.pem"
	rootKeyFile       = "provider-root-key.pem"
	gatewayCAFile     = "gateway-issuer.pem"
	gatewayCAKeyFile  = "gateway-issuer-key.pem"
	deviceCAFile      = "device-issuer.pem"
	deviceCAKeyFile   = "device-issuer-key.pem"
	gatewayCertFile   = "gateway-identity.pem"
	authorizationFile = "authorization.json"
)

type ProviderMetadata struct {
	Version    int    `json:"version"`
	Name       string `json:"name"`
	ProviderID string `json:"provider_id"`
	GatewayID  string `json:"gateway_id"`
	Endpoint   string `json:"endpoint"`
	RootPin    string `json:"root_pin"`
	CreatedAt  string `json:"created_at"`
}

// Provider is the provider-side identity and authorization state loaded by a
// gateway. RootKey is loaded for the single-node provider workflow. A larger
// deployment should move it offline after issuing the constrained gateway and
// device intermediates; ordinary enrollment uses only DeviceIssuerKey.
type Provider struct {
	Directory string
	Metadata  ProviderMetadata
	gatewayMu sync.RWMutex

	RootCert         *x509.Certificate
	RootKey          ed25519.PrivateKey
	GatewayIssuer    *x509.Certificate
	GatewayIssuerKey ed25519.PrivateKey
	DeviceIssuer     *x509.Certificate
	DeviceIssuerKey  ed25519.PrivateKey
	GatewayCert      tls.Certificate
	Store            *Store
}

// InitProvider creates a new provider trust domain and first gateway. The
// directory must not already exist, preventing an accidental reinitialization
// from silently replacing the trust anchor every enrolled client pins.
func InitProvider(directory, name, endpoint string, now time.Time) (*Provider, error) {
	if strings.TrimSpace(directory) == "" {
		return nil, errors.New("provider state directory is required")
	}
	name = strings.TrimSpace(name)
	endpoint = strings.TrimSpace(endpoint)
	if name == "" || len(name) > 128 {
		return nil, errors.New("provider name must contain 1-128 characters")
	}
	if err := validateEndpoint(endpoint); err != nil {
		return nil, err
	}
	if now.IsZero() {
		now = time.Now()
	}
	if _, err := os.Stat(directory); err == nil {
		return nil, fmt.Errorf("provider state directory already exists: %s", directory)
	} else if !errors.Is(err, os.ErrNotExist) {
		return nil, fmt.Errorf("inspect provider state directory: %w", err)
	}
	if err := os.MkdirAll(filepath.Dir(filepath.Clean(directory)), 0o700); err != nil {
		return nil, fmt.Errorf("create provider state parent directory: %w", err)
	}
	if err := os.Mkdir(directory, 0o700); err != nil {
		return nil, fmt.Errorf("create provider state directory: %w", err)
	}
	cleanup := true
	defer func() {
		if cleanup {
			_ = os.RemoveAll(directory)
		}
	}()
	fail := func(err error) (*Provider, error) {
		return nil, err
	}

	rootCert, rootKey, err := newRoot(name, now)
	if err != nil {
		return fail(err)
	}
	rootPin := RootPin(rootCert)
	providerID := providerID(rootCert)
	gatewayID, err := randomID()
	if err != nil {
		return fail(err)
	}
	gatewayIssuer, gatewayIssuerKey, err := newIssuer(rootCert, rootKey, name+" gateway issuer", providerID, "gateway-issuer", x509.ExtKeyUsageServerAuth, now)
	if err != nil {
		return fail(err)
	}
	deviceIssuer, deviceIssuerKey, err := newIssuer(rootCert, rootKey, name+" device issuer", providerID, "device-issuer", x509.ExtKeyUsageClientAuth, now)
	if err != nil {
		return fail(err)
	}
	gatewayCert, gatewayKey, err := newLeaf(gatewayIssuer, gatewayIssuerKey, gatewayURI(providerID, gatewayID), x509.ExtKeyUsageServerAuth, defaultGatewayTTL, now)
	if err != nil {
		return fail(err)
	}

	meta := ProviderMetadata{
		Version: ProviderStateVersion, Name: name, ProviderID: providerID,
		GatewayID: gatewayID, Endpoint: endpoint, RootPin: rootPin,
		CreatedAt: now.UTC().Format(time.RFC3339),
	}
	files := []struct {
		name string
		data []byte
		mode os.FileMode
	}{
		{providerFile, mustJSON(meta), 0o600},
		{rootCertFile, encodeCertificate(rootCert), 0o644},
		{rootKeyFile, encodePrivateKey(rootKey), 0o600},
		{gatewayCAFile, encodeCertificate(gatewayIssuer), 0o644},
		{gatewayCAKeyFile, encodePrivateKey(gatewayIssuerKey), 0o600},
		{deviceCAFile, encodeCertificate(deviceIssuer), 0o644},
		{deviceCAKeyFile, encodePrivateKey(deviceIssuerKey), 0o600},
		{gatewayCertFile, encodeTLSIdentity(gatewayCert, gatewayIssuer, rootCert, gatewayKey), 0o600},
	}
	for _, file := range files {
		if err := writeFileAtomic(filepath.Join(directory, file.name), file.data, file.mode); err != nil {
			return fail(err)
		}
	}
	store, err := NewStore(filepath.Join(directory, authorizationFile))
	if err != nil {
		return fail(err)
	}
	if err := store.Initialize(); err != nil {
		return fail(err)
	}
	provider, err := LoadProvider(directory)
	if err != nil {
		return nil, err
	}
	cleanup = false
	return provider, nil
}

func LoadProvider(directory string) (*Provider, error) {
	directoryInfo, err := os.Stat(directory)
	if err != nil {
		return nil, fmt.Errorf("inspect provider state directory: %w", err)
	}
	if err := checkPrivateDirectoryPermissions(directoryInfo); err != nil {
		return nil, fmt.Errorf("provider state directory %s is not private: %w", directory, err)
	}
	for _, name := range []string{providerFile, rootKeyFile, gatewayCAKeyFile, deviceCAKeyFile, gatewayCertFile, authorizationFile} {
		info, err := os.Lstat(filepath.Join(directory, name))
		if err != nil {
			return nil, fmt.Errorf("inspect private provider file %s: %w", name, err)
		}
		if err := checkPrivatePermissions(info); err != nil {
			return nil, fmt.Errorf("private provider file %s: %w", name, err)
		}
	}
	metaBytes, err := os.ReadFile(filepath.Join(directory, providerFile))
	if err != nil {
		return nil, fmt.Errorf("read provider metadata: %w", err)
	}
	var meta ProviderMetadata
	if err := decodeStrictJSON(metaBytes, &meta); err != nil {
		return nil, fmt.Errorf("decode provider metadata: %w", err)
	}
	if meta.Version != ProviderStateVersion || meta.Name == "" || len(meta.Name) > 128 || !validID(meta.ProviderID) || !validID(meta.GatewayID) {
		return nil, errors.New("invalid provider metadata")
	}
	if err := validateEndpoint(meta.Endpoint); err != nil {
		return nil, fmt.Errorf("invalid provider metadata: %w", err)
	}
	rootCert, err := readCertificate(filepath.Join(directory, rootCertFile))
	if err != nil {
		return nil, err
	}
	rootKey, err := readEd25519PrivateKey(filepath.Join(directory, rootKeyFile))
	if err != nil {
		return nil, err
	}
	gatewayIssuer, err := readCertificate(filepath.Join(directory, gatewayCAFile))
	if err != nil {
		return nil, err
	}
	gatewayIssuerKey, err := readEd25519PrivateKey(filepath.Join(directory, gatewayCAKeyFile))
	if err != nil {
		return nil, err
	}
	deviceIssuer, err := readCertificate(filepath.Join(directory, deviceCAFile))
	if err != nil {
		return nil, err
	}
	deviceIssuerKey, err := readEd25519PrivateKey(filepath.Join(directory, deviceCAKeyFile))
	if err != nil {
		return nil, err
	}
	unlockGateway, err := lockFile(filepath.Join(directory, gatewayCertFile) + ".lock")
	if err != nil {
		return nil, err
	}
	defer unlockGateway()
	gatewayIdentity, err := os.ReadFile(filepath.Join(directory, gatewayCertFile))
	if err != nil {
		return nil, fmt.Errorf("read gateway identity: %w", err)
	}
	gatewayCert, err := tls.X509KeyPair(gatewayIdentity, gatewayIdentity)
	if err != nil {
		return nil, fmt.Errorf("load gateway identity: %w", err)
	}
	if meta.RootPin != RootPin(rootCert) || meta.ProviderID != providerID(rootCert) {
		return nil, errors.New("provider metadata does not match root identity")
	}
	for name, pair := range map[string]struct {
		certificate *x509.Certificate
		privateKey  ed25519.PrivateKey
	}{
		"provider root":  {rootCert, rootKey},
		"gateway issuer": {gatewayIssuer, gatewayIssuerKey},
		"device issuer":  {deviceIssuer, deviceIssuerKey},
	} {
		if !certificateKeyMatches(pair.certificate, pair.privateKey) {
			return nil, fmt.Errorf("%s certificate and private key do not match", name)
		}
	}
	if err := verifyIssuer(gatewayIssuer, rootCert, meta.ProviderID, "gateway-issuer", x509.ExtKeyUsageServerAuth, nowOrTime(time.Now())); err != nil {
		return nil, fmt.Errorf("verify gateway issuer: %w", err)
	}
	if err := verifyIssuer(deviceIssuer, rootCert, meta.ProviderID, "device-issuer", x509.ExtKeyUsageClientAuth, nowOrTime(time.Now())); err != nil {
		return nil, fmt.Errorf("verify device issuer: %w", err)
	}
	leaf, err := x509.ParseCertificate(gatewayCert.Certificate[0])
	if err != nil {
		return nil, fmt.Errorf("parse gateway identity: %w", err)
	}
	if err := verifyGatewayCertificate(gatewayCert, rootCert, meta.ProviderID, meta.GatewayID, time.Now(), true); err != nil {
		return nil, err
	}
	if !leaf.NotAfter.After(time.Now().Add(7 * 24 * time.Hour)) {
		newCert, newKey, renewErr := newLeaf(gatewayIssuer, gatewayIssuerKey, gatewayURI(meta.ProviderID, meta.GatewayID), x509.ExtKeyUsageServerAuth, defaultGatewayTTL, time.Now())
		if renewErr != nil {
			return nil, fmt.Errorf("renew gateway identity: %w", renewErr)
		}
		gatewayIdentity = encodeTLSIdentity(newCert, gatewayIssuer, rootCert, newKey)
		gatewayCert, err = tls.X509KeyPair(gatewayIdentity, gatewayIdentity)
		if err != nil {
			return nil, fmt.Errorf("load renewed gateway identity: %w", err)
		}
		if err := verifyGatewayCertificate(gatewayCert, rootCert, meta.ProviderID, meta.GatewayID, time.Now(), false); err != nil {
			return nil, err
		}
		if err := writeFileAtomic(filepath.Join(directory, gatewayCertFile), gatewayIdentity, 0o600); err != nil {
			return nil, fmt.Errorf("save renewed gateway identity: %w", err)
		}
	}
	store, err := NewStore(filepath.Join(directory, authorizationFile))
	if err != nil {
		return nil, err
	}
	if err := store.Load(); err != nil {
		return nil, err
	}
	return &Provider{
		Directory: directory, Metadata: meta, RootCert: rootCert, RootKey: rootKey,
		GatewayIssuer: gatewayIssuer, GatewayIssuerKey: gatewayIssuerKey,
		DeviceIssuer: deviceIssuer, DeviceIssuerKey: deviceIssuerKey,
		GatewayCert: gatewayCert, Store: store,
	}, nil
}

func certificateKeyMatches(certificate *x509.Certificate, privateKey ed25519.PrivateKey) bool {
	publicKey, ok := certificate.PublicKey.(ed25519.PublicKey)
	return ok && len(privateKey) == ed25519.PrivateKeySize && publicKey.Equal(privateKey.Public())
}

// GatewayCertificate returns the current in-memory leaf chain. TLS configs
// created by ServerCredentials call this for every new handshake, so a
// renewal takes effect without interrupting established tunnels.
func (p *Provider) GatewayCertificate() tls.Certificate {
	p.gatewayMu.RLock()
	defer p.gatewayMu.RUnlock()
	return p.GatewayCert
}

// RenewGatewayIdentity reloads the on-disk identity under a cross-process
// lock and renews it when it enters the requested window. Multiple gateway or
// provider CLI processes can safely share one provider directory.
func (p *Provider) RenewGatewayIdentity(now time.Time, renewalWindow time.Duration) (bool, error) {
	if p == nil || p.Directory == "" {
		return false, errors.New("provider is not configured")
	}
	if now.IsZero() {
		now = time.Now()
	}
	if renewalWindow <= 0 {
		renewalWindow = 7 * 24 * time.Hour
	}
	path := filepath.Join(p.Directory, gatewayCertFile)
	unlock, err := lockFile(path + ".lock")
	if err != nil {
		return false, err
	}
	defer unlock()

	currentPEM, err := os.ReadFile(path)
	if err != nil {
		return false, fmt.Errorf("read gateway identity: %w", err)
	}
	current, err := tls.X509KeyPair(currentPEM, currentPEM)
	if err != nil {
		return false, fmt.Errorf("load gateway identity: %w", err)
	}
	if err := verifyGatewayCertificate(current, p.RootCert, p.Metadata.ProviderID, p.Metadata.GatewayID, now, true); err != nil {
		return false, err
	}
	leaf, _ := x509.ParseCertificate(current.Certificate[0])
	if leaf.NotAfter.After(now.Add(renewalWindow)) {
		p.gatewayMu.Lock()
		p.GatewayCert = current
		p.gatewayMu.Unlock()
		return false, nil
	}
	renewedLeaf, renewedKey, err := newLeaf(p.GatewayIssuer, p.GatewayIssuerKey,
		gatewayURI(p.Metadata.ProviderID, p.Metadata.GatewayID), x509.ExtKeyUsageServerAuth, defaultGatewayTTL, now)
	if err != nil {
		return false, fmt.Errorf("renew gateway identity: %w", err)
	}
	renewedPEM := encodeTLSIdentity(renewedLeaf, p.GatewayIssuer, p.RootCert, renewedKey)
	renewed, err := tls.X509KeyPair(renewedPEM, renewedPEM)
	if err != nil {
		return false, fmt.Errorf("load renewed gateway identity: %w", err)
	}
	if err := verifyGatewayCertificate(renewed, p.RootCert, p.Metadata.ProviderID, p.Metadata.GatewayID, now, false); err != nil {
		return false, err
	}
	if err := writeFileAtomic(path, renewedPEM, 0o600); err != nil {
		return false, fmt.Errorf("save renewed gateway identity: %w", err)
	}
	p.gatewayMu.Lock()
	p.GatewayCert = renewed
	p.gatewayMu.Unlock()
	return true, nil
}

func singleCertificateURI(certificate *x509.Certificate) string {
	if certificate == nil || len(certificate.URIs) != 1 {
		return ""
	}
	return certificate.URIs[0].String()
}

func verifyGatewayCertificate(certificate tls.Certificate, root *x509.Certificate, providerID, gatewayID string, now time.Time, allowExpired bool) error {
	if len(certificate.Certificate) == 0 {
		return errors.New("gateway identity has no leaf")
	}
	leaf, err := x509.ParseCertificate(certificate.Certificate[0])
	if err != nil {
		return fmt.Errorf("parse gateway identity: %w", err)
	}
	validationTime := now
	if allowExpired && !now.Before(leaf.NotAfter) {
		validationTime = leaf.NotAfter.Add(-time.Second)
	}
	verified, err := verifyTLSCertificate(certificate, root, x509.ExtKeyUsageServerAuth, validationTime)
	if err != nil {
		return fmt.Errorf("verify gateway identity: %w", err)
	}
	if got, want := singleCertificateURI(verified), gatewayURI(providerID, gatewayID).String(); got != want {
		return fmt.Errorf("gateway identity mismatch: got %q, want %q", got, want)
	}
	return nil
}

func newRoot(name string, now time.Time) (*x509.Certificate, ed25519.PrivateKey, error) {
	pub, key, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		return nil, nil, fmt.Errorf("generate provider root key: %w", err)
	}
	serial, err := randomSerial()
	if err != nil {
		return nil, nil, err
	}
	tmpl := &x509.Certificate{
		SerialNumber: serial,
		Subject:      pkix.Name{CommonName: name + " Queqiao provider root"},
		NotBefore:    now.Add(-certificateClockSkew), NotAfter: now.AddDate(10, 0, 0),
		KeyUsage:              x509.KeyUsageCertSign | x509.KeyUsageCRLSign,
		BasicConstraintsValid: true, IsCA: true, MaxPathLen: 1,
	}
	der, err := x509.CreateCertificate(rand.Reader, tmpl, tmpl, pub, key)
	if err != nil {
		return nil, nil, fmt.Errorf("create provider root: %w", err)
	}
	cert, err := x509.ParseCertificate(der)
	if err != nil {
		return nil, nil, fmt.Errorf("parse provider root: %w", err)
	}
	return cert, key, nil
}

func newIssuer(parent *x509.Certificate, parentKey ed25519.PrivateKey, commonName, providerID, role string, usage x509.ExtKeyUsage, now time.Time) (*x509.Certificate, ed25519.PrivateKey, error) {
	pub, key, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		return nil, nil, fmt.Errorf("generate %s key: %w", role, err)
	}
	serial, err := randomSerial()
	if err != nil {
		return nil, nil, err
	}
	uri, _ := url.Parse(fmt.Sprintf("queqiao://%s/%s", providerID, role))
	tmpl := &x509.Certificate{
		SerialNumber: serial, Subject: pkix.Name{CommonName: commonName}, URIs: []*url.URL{uri},
		NotBefore: now.Add(-certificateClockSkew), NotAfter: now.AddDate(5, 0, 0),
		KeyUsage:              x509.KeyUsageCertSign | x509.KeyUsageCRLSign | x509.KeyUsageDigitalSignature,
		ExtKeyUsage:           []x509.ExtKeyUsage{usage},
		BasicConstraintsValid: true, IsCA: true, MaxPathLenZero: true,
	}
	der, err := x509.CreateCertificate(rand.Reader, tmpl, parent, pub, parentKey)
	if err != nil {
		return nil, nil, fmt.Errorf("create %s: %w", role, err)
	}
	cert, err := x509.ParseCertificate(der)
	if err != nil {
		return nil, nil, fmt.Errorf("parse %s: %w", role, err)
	}
	return cert, key, nil
}

func newLeaf(parent *x509.Certificate, parentKey ed25519.PrivateKey, identity *url.URL, usage x509.ExtKeyUsage, ttl time.Duration, now time.Time) (*x509.Certificate, ed25519.PrivateKey, error) {
	pub, key, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		return nil, nil, fmt.Errorf("generate leaf key: %w", err)
	}
	serial, err := randomSerial()
	if err != nil {
		return nil, nil, err
	}
	notAfter := now.Add(ttl)
	if parent != nil && parent.NotAfter.Before(notAfter) {
		notAfter = parent.NotAfter
	}
	if !notAfter.After(now) {
		return nil, nil, errors.New("leaf issuer has expired")
	}
	tmpl := &x509.Certificate{
		SerialNumber: serial, Subject: pkix.Name{}, URIs: []*url.URL{identity},
		NotBefore: now.Add(-certificateClockSkew), NotAfter: notAfter,
		KeyUsage:    x509.KeyUsageDigitalSignature,
		ExtKeyUsage: []x509.ExtKeyUsage{usage}, BasicConstraintsValid: true,
	}
	der, err := x509.CreateCertificate(rand.Reader, tmpl, parent, pub, parentKey)
	if err != nil {
		return nil, nil, fmt.Errorf("create leaf certificate: %w", err)
	}
	cert, err := x509.ParseCertificate(der)
	if err != nil {
		return nil, nil, fmt.Errorf("parse leaf certificate: %w", err)
	}
	return cert, key, nil
}

func (p *Provider) IssueDevice(accountID, deviceID string, publicKey ed25519.PublicKey, now time.Time) ([]byte, error) {
	if !validID(accountID) || !validID(deviceID) {
		return nil, errors.New("invalid account or device identity")
	}
	if len(publicKey) != ed25519.PublicKeySize {
		return nil, errors.New("invalid Ed25519 device public key")
	}
	if now.IsZero() {
		now = time.Now()
	}
	serial, err := randomSerial()
	if err != nil {
		return nil, err
	}
	identity := deviceURI(p.Metadata.ProviderID, accountID, deviceID)
	notAfter := now.Add(defaultDeviceTTL)
	if p.DeviceIssuer.NotAfter.Before(notAfter) {
		notAfter = p.DeviceIssuer.NotAfter
	}
	if !notAfter.After(now) {
		return nil, errors.New("device issuer has expired")
	}
	tmpl := &x509.Certificate{
		SerialNumber: serial, Subject: pkix.Name{}, URIs: []*url.URL{identity},
		NotBefore: now.Add(-certificateClockSkew), NotAfter: notAfter,
		KeyUsage:    x509.KeyUsageDigitalSignature,
		ExtKeyUsage: []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth}, BasicConstraintsValid: true,
	}
	der, err := x509.CreateCertificate(rand.Reader, tmpl, p.DeviceIssuer, publicKey, p.DeviceIssuerKey)
	if err != nil {
		return nil, fmt.Errorf("issue device certificate: %w", err)
	}
	return append(encodeCertificateDER(der), encodeCertificate(p.DeviceIssuer)...), nil
}

func RootPin(cert *x509.Certificate) string {
	sum := sha256.Sum256(cert.Raw)
	return base64.RawURLEncoding.EncodeToString(sum[:])
}

func providerID(cert *x509.Certificate) string {
	sum := sha256.Sum256(cert.RawSubjectPublicKeyInfo)
	return hex.EncodeToString(sum[:16])
}

func gatewayURI(providerID, gatewayID string) *url.URL {
	u, _ := url.Parse(fmt.Sprintf("queqiao://%s/gateway/%s", providerID, gatewayID))
	return u
}

func deviceURI(providerID, accountID, deviceID string) *url.URL {
	u, _ := url.Parse(fmt.Sprintf("queqiao://%s/account/%s/device/%s", providerID, url.PathEscape(accountID), url.PathEscape(deviceID)))
	return u
}

func randomID() (string, error) {
	var raw [16]byte
	if _, err := rand.Read(raw[:]); err != nil {
		return "", fmt.Errorf("generate identity: %w", err)
	}
	return hex.EncodeToString(raw[:]), nil
}

func randomSerial() (*big.Int, error) {
	limit := new(big.Int).Lsh(big.NewInt(1), 128)
	serial, err := rand.Int(rand.Reader, limit)
	if err != nil {
		return nil, fmt.Errorf("generate certificate serial: %w", err)
	}
	if serial.Sign() == 0 {
		serial.SetInt64(1)
	}
	return serial, nil
}

func validateEndpoint(endpoint string) error {
	if endpoint == "" || len(endpoint) > 512 || endpoint != strings.TrimSpace(endpoint) {
		return errors.New("provider endpoint is required")
	}
	host, portText, err := net.SplitHostPort(endpoint)
	port, portErr := strconv.Atoi(portText)
	if err != nil || portErr != nil || strings.TrimSpace(host) == "" || port < 1 || port > 65535 {
		return fmt.Errorf("invalid provider endpoint %q", endpoint)
	}
	return nil
}

func validID(value string) bool {
	if len(value) != 32 || value != strings.ToLower(value) {
		return false
	}
	raw, err := hex.DecodeString(value)
	return err == nil && len(raw) == 16
}

func encodeCertificate(cert *x509.Certificate) []byte { return encodeCertificateDER(cert.Raw) }

func encodeCertificateDER(der []byte) []byte {
	return pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})
}

func encodeCertificateChain(leaf, issuer, root *x509.Certificate) []byte {
	out := encodeCertificate(leaf)
	out = append(out, encodeCertificate(issuer)...)
	return append(out, encodeCertificate(root)...)
}

func encodeTLSIdentity(leaf, issuer, root *x509.Certificate, key ed25519.PrivateKey) []byte {
	out := encodeCertificateChain(leaf, issuer, root)
	return append(out, encodePrivateKey(key)...)
}

func encodePrivateKey(key ed25519.PrivateKey) []byte {
	der, err := x509.MarshalPKCS8PrivateKey(key)
	if err != nil {
		panic(err)
	}
	return pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: der})
}

func readCertificate(path string) (*x509.Certificate, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read certificate %s: %w", path, err)
	}
	block, _ := pem.Decode(data)
	if block == nil || block.Type != "CERTIFICATE" {
		return nil, fmt.Errorf("%s does not contain a certificate", path)
	}
	cert, err := x509.ParseCertificate(block.Bytes)
	if err != nil {
		return nil, fmt.Errorf("parse certificate %s: %w", path, err)
	}
	return cert, nil
}

func readEd25519PrivateKey(path string) (ed25519.PrivateKey, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read private key %s: %w", path, err)
	}
	block, _ := pem.Decode(data)
	if block == nil || block.Type != "PRIVATE KEY" {
		return nil, fmt.Errorf("%s does not contain a PKCS#8 private key", path)
	}
	parsed, err := x509.ParsePKCS8PrivateKey(block.Bytes)
	if err != nil {
		return nil, fmt.Errorf("parse private key %s: %w", path, err)
	}
	key, ok := parsed.(ed25519.PrivateKey)
	if !ok {
		return nil, fmt.Errorf("%s is not an Ed25519 private key", path)
	}
	return key, nil
}

func verifyIssuedCertificate(cert, root *x509.Certificate, usage x509.ExtKeyUsage, now time.Time) error {
	roots := x509.NewCertPool()
	roots.AddCert(root)
	_, err := cert.Verify(x509.VerifyOptions{Roots: roots, CurrentTime: now, KeyUsages: []x509.ExtKeyUsage{usage}})
	return err
}

func verifyIssuer(certificate, root *x509.Certificate, expectedProvider, role string, usage x509.ExtKeyUsage, now time.Time) error {
	if err := verifyIssuedCertificate(certificate, root, usage, now); err != nil {
		return err
	}
	if !certificate.IsCA || !certificate.BasicConstraintsValid || !certificate.MaxPathLenZero ||
		certificate.KeyUsage&x509.KeyUsageCertSign == 0 {
		return errors.New("issuer CA constraints are invalid")
	}
	if _, ok := certificate.PublicKey.(ed25519.PublicKey); !ok {
		return errors.New("issuer does not use Ed25519")
	}
	want := fmt.Sprintf("queqiao://%s/%s", expectedProvider, role)
	if singleCertificateURI(certificate) != want {
		return errors.New("issuer role identity is invalid")
	}
	if len(certificate.ExtKeyUsage) != 1 || certificate.ExtKeyUsage[0] != usage {
		return errors.New("issuer extended key usage is invalid")
	}
	return nil
}

func writeFileAtomic(path string, data []byte, mode os.FileMode) error {
	dir := filepath.Dir(path)
	tmp, err := os.CreateTemp(dir, ".queqiao-*")
	if err != nil {
		return fmt.Errorf("create temporary state file: %w", err)
	}
	tmpName := tmp.Name()
	defer os.Remove(tmpName)
	if err := tmp.Chmod(mode); err != nil {
		_ = tmp.Close()
		return fmt.Errorf("set state file permissions: %w", err)
	}
	if _, err := tmp.Write(data); err != nil {
		_ = tmp.Close()
		return fmt.Errorf("write state file: %w", err)
	}
	if err := tmp.Sync(); err != nil {
		_ = tmp.Close()
		return fmt.Errorf("sync state file: %w", err)
	}
	if err := tmp.Close(); err != nil {
		return fmt.Errorf("close state file: %w", err)
	}
	// Carry the existing owner across the replace. The rename installs a new
	// inode owned by the calling process, which would otherwise move the file
	// out of reach of the service account that has to read it.
	if err := adoptOwnerOf(tmpName, path); err != nil {
		return err
	}
	if err := replaceFile(tmpName, path); err != nil {
		return fmt.Errorf("install state file: %w", err)
	}
	// Persist the directory entry as well as the file contents. Platforms that
	// do not support syncing directories safely ignore this best-effort step.
	if directory, err := os.Open(dir); err == nil {
		_ = directory.Sync()
		_ = directory.Close()
	}
	return nil
}

func mustJSON(value any) []byte {
	data, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		panic(err)
	}
	return append(data, '\n')
}

func nowOrTime(now time.Time) time.Time {
	if now.IsZero() {
		return time.Now()
	}
	return now
}
