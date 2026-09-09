package identity

import (
	"crypto/ed25519"
	"crypto/sha256"
	"crypto/subtle"
	"crypto/tls"
	"crypto/x509"
	"encoding/base64"
	"errors"
	"fmt"
	"net/url"
	"strings"
	"time"
)

const (
	EnrollmentALPN = "queqiao-enroll/1"
	RenewalALPN    = "queqiao-renew/1"
)

type ServerCredentials struct {
	ProviderID        string
	GatewayID         string
	Certificate       tls.Certificate
	CertificateSource func() tls.Certificate
	Root              *x509.Certificate
	Store             *Store
}

type ClientCredentials struct {
	ProviderID  string
	GatewayID   string
	Certificate tls.Certificate
	Root        *x509.Certificate
	RootPin     string
}

func (p *Provider) ServerCredentials() ServerCredentials {
	return ServerCredentials{
		ProviderID: p.Metadata.ProviderID, GatewayID: p.Metadata.GatewayID,
		Certificate: p.GatewayCertificate(), CertificateSource: p.GatewayCertificate,
		Root: p.RootCert, Store: p.Store,
	}
}

func (c ServerCredentials) currentCertificate() tls.Certificate {
	if c.CertificateSource != nil {
		return c.CertificateSource()
	}
	return c.Certificate
}

func (c ServerCredentials) Validate() error {
	if !validID(c.ProviderID) || !validID(c.GatewayID) || c.Root == nil || c.Store == nil {
		return errors.New("incomplete server identity")
	}
	certificate := c.currentCertificate()
	if len(certificate.Certificate) < 2 || certificate.PrivateKey == nil {
		return errors.New("server identity has no gateway certificate chain or private key")
	}
	if providerID(c.Root) != c.ProviderID {
		return errors.New("server provider identity does not match root")
	}
	if err := validatePinnedRoot(c.Root); err != nil {
		return err
	}
	leaf, err := verifyTLSCertificate(certificate, c.Root, x509.ExtKeyUsageServerAuth, time.Now())
	if err != nil {
		return fmt.Errorf("verify server identity: %w", err)
	}
	want := gatewayURI(c.ProviderID, c.GatewayID).String()
	if len(leaf.URIs) != 1 || leaf.URIs[0].String() != want {
		return errors.New("server gateway certificate identity does not match configuration")
	}
	return nil
}

func (c ClientCredentials) Validate(now time.Time) error {
	if !validID(c.ProviderID) || !validID(c.GatewayID) || c.Root == nil || c.RootPin == "" {
		return errors.New("incomplete client identity")
	}
	if RootPin(c.Root) != c.RootPin || providerID(c.Root) != c.ProviderID {
		return errors.New("client provider root does not match profile")
	}
	if err := validatePinnedRoot(c.Root); err != nil {
		return err
	}
	if len(c.Certificate.Certificate) < 2 || c.Certificate.PrivateKey == nil {
		return errors.New("client identity has no device certificate chain or private key")
	}
	leaf, err := x509.ParseCertificate(c.Certificate.Certificate[0])
	if err != nil {
		return fmt.Errorf("parse client certificate: %w", err)
	}
	intermediates := x509.NewCertPool()
	for _, raw := range c.Certificate.Certificate[1:] {
		cert, parseErr := x509.ParseCertificate(raw)
		if parseErr != nil {
			return fmt.Errorf("parse client certificate chain: %w", parseErr)
		}
		if !cert.Equal(c.Root) {
			intermediates.AddCert(cert)
		}
	}
	roots := x509.NewCertPool()
	roots.AddCert(c.Root)
	if _, err := leaf.Verify(x509.VerifyOptions{
		Roots: roots, Intermediates: intermediates, CurrentTime: nowOrTime(now),
		KeyUsages: []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth},
	}); err != nil {
		return fmt.Errorf("verify client identity: %w", err)
	}
	principal, err := PrincipalFromCertificate(leaf)
	if err != nil {
		return err
	}
	if principal.ProviderID != c.ProviderID {
		return errors.New("client certificate belongs to another provider")
	}
	return nil
}

func validatePinnedRoot(root *x509.Certificate) error {
	if root == nil || !root.IsCA || !root.BasicConstraintsValid || root.KeyUsage&x509.KeyUsageCertSign == 0 ||
		root.MaxPathLen != 1 || root.CheckSignatureFrom(root) != nil {
		return errors.New("provider root is not a self-signed CA")
	}
	if _, ok := root.PublicKey.(ed25519.PublicKey); !ok {
		return errors.New("provider root does not use Ed25519")
	}
	return nil
}

func verifyTLSCertificate(certificate tls.Certificate, root *x509.Certificate, usage x509.ExtKeyUsage, now time.Time) (*x509.Certificate, error) {
	if len(certificate.Certificate) < 2 || certificate.PrivateKey == nil {
		return nil, errors.New("certificate chain or private key is missing")
	}
	leaf, err := x509.ParseCertificate(certificate.Certificate[0])
	if err != nil {
		return nil, err
	}
	intermediates := x509.NewCertPool()
	for _, raw := range certificate.Certificate[1:] {
		cert, err := x509.ParseCertificate(raw)
		if err != nil {
			return nil, err
		}
		if !cert.Equal(root) {
			intermediates.AddCert(cert)
		}
	}
	roots := x509.NewCertPool()
	roots.AddCert(root)
	if _, err := leaf.Verify(x509.VerifyOptions{
		Roots: roots, Intermediates: intermediates, CurrentTime: nowOrTime(now), KeyUsages: []x509.ExtKeyUsage{usage},
	}); err != nil {
		return nil, err
	}
	return leaf, nil
}

// ServerTLSConfig selects an enrollment-only TLS profile only when the peer
// offers exactly that ALPN. All normal data connections require a valid device
// certificate and current authorization before TLS completes.
func ServerTLSConfig(credentials ServerCredentials, dataALPN string, allowEnrollment bool) (*tls.Config, error) {
	if err := credentials.Validate(); err != nil {
		return nil, err
	}
	if dataALPN == "" || dataALPN == EnrollmentALPN {
		return nil, errors.New("invalid data ALPN")
	}
	roots := x509.NewCertPool()
	roots.AddCert(credentials.Root)
	getCertificate := func(*tls.ClientHelloInfo) (*tls.Certificate, error) {
		current := credentials.currentCertificate()
		return &current, nil
	}
	data := &tls.Config{
		MinVersion: tls.VersionTLS13, GetCertificate: getCertificate,
		NextProtos: []string{dataALPN}, ClientAuth: tls.RequireAndVerifyClientCert,
		ClientCAs: roots,
	}
	data.VerifyConnection = func(state tls.ConnectionState) error {
		principal, err := PrincipalFromTLS(state)
		if err != nil {
			return err
		}
		if principal.ProviderID != credentials.ProviderID {
			return errors.New("device belongs to another provider")
		}
		_, err = credentials.Store.Authorize(principal, time.Now())
		return err
	}
	if !allowEnrollment {
		return data, nil
	}
	enrollment := &tls.Config{
		MinVersion: tls.VersionTLS13, GetCertificate: getCertificate,
		NextProtos: []string{EnrollmentALPN}, ClientAuth: tls.NoClientCert,
	}
	renewal := data.Clone()
	renewal.NextProtos = []string{RenewalALPN}
	base := data.Clone()
	base.NextProtos = []string{dataALPN, EnrollmentALPN, RenewalALPN}
	base.GetConfigForClient = func(hello *tls.ClientHelloInfo) (*tls.Config, error) {
		if len(hello.SupportedProtos) == 1 && hello.SupportedProtos[0] == EnrollmentALPN {
			return enrollment, nil
		}
		if len(hello.SupportedProtos) == 1 && hello.SupportedProtos[0] == RenewalALPN {
			return renewal, nil
		}
		return data, nil
	}
	return base, nil
}

func RenewalTLSConfig(credentials ClientCredentials) (*tls.Config, error) {
	if err := credentials.Validate(time.Now()); err != nil {
		return nil, err
	}
	return pinnedClientTLSConfig(credentials.RootPin, credentials.ProviderID, credentials.GatewayID, RenewalALPN, []tls.Certificate{credentials.Certificate}), nil
}

func ClientTLSConfig(credentials ClientCredentials, dataALPN string) (*tls.Config, error) {
	if err := credentials.Validate(time.Now()); err != nil {
		return nil, err
	}
	return pinnedClientTLSConfig(credentials.RootPin, credentials.ProviderID, credentials.GatewayID, dataALPN, []tls.Certificate{credentials.Certificate}), nil
}

func EnrollmentTLSConfig(rootPin, providerID, gatewayID string) *tls.Config {
	return pinnedClientTLSConfig(rootPin, providerID, gatewayID, EnrollmentALPN, nil)
}

// pinnedClientTLSConfig deliberately performs custom verification because a
// Queqiao gateway is identified by a provider URI rather than a DNS name. The
// scary standard-library field is never user-configurable: VerifyConnection
// always pins the exact provider root, validates the chain and serverAuth EKU,
// and checks the expected gateway URI.
func pinnedClientTLSConfig(rootPin, expectedProvider, expectedGateway, alpn string, certificates []tls.Certificate) *tls.Config {
	return &tls.Config{
		MinVersion: tls.VersionTLS13, InsecureSkipVerify: true, // replaced below, never bypassed
		Certificates: certificates, NextProtos: []string{alpn},
		VerifyConnection: func(state tls.ConnectionState) error {
			return verifyGateway(state, rootPin, expectedProvider, expectedGateway, time.Now())
		},
	}
}

func verifyGateway(state tls.ConnectionState, rootPin, expectedProvider, expectedGateway string, now time.Time) error {
	if state.Version != tls.VersionTLS13 {
		return errors.New("gateway did not negotiate TLS 1.3")
	}
	if len(state.PeerCertificates) < 2 {
		return errors.New("gateway did not provide a complete provider chain")
	}
	var pinnedRoot *x509.Certificate
	for _, cert := range state.PeerCertificates[1:] {
		if constantTextEqual(RootPin(cert), rootPin) {
			pinnedRoot = cert
			break
		}
	}
	if pinnedRoot == nil || !pinnedRoot.IsCA {
		return errors.New("gateway chain does not contain the pinned provider root")
	}
	if providerID(pinnedRoot) != expectedProvider {
		return errors.New("gateway provider identity mismatch")
	}
	roots := x509.NewCertPool()
	roots.AddCert(pinnedRoot)
	intermediates := x509.NewCertPool()
	for _, cert := range state.PeerCertificates[1:] {
		if !cert.Equal(pinnedRoot) {
			intermediates.AddCert(cert)
		}
	}
	leaf := state.PeerCertificates[0]
	if _, err := leaf.Verify(x509.VerifyOptions{
		Roots: roots, Intermediates: intermediates, CurrentTime: now,
		KeyUsages: []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
	}); err != nil {
		return fmt.Errorf("verify gateway certificate: %w", err)
	}
	want := gatewayURI(expectedProvider, expectedGateway).String()
	if len(leaf.URIs) != 1 || leaf.URIs[0].String() != want {
		return fmt.Errorf("gateway identity mismatch: expected %s", want)
	}
	return nil
}

func PrincipalFromTLS(state tls.ConnectionState) (Principal, error) {
	if len(state.PeerCertificates) == 0 {
		return Principal{}, errors.New("client certificate is required")
	}
	return PrincipalFromCertificate(state.PeerCertificates[0])
}

func PrincipalFromCertificate(cert *x509.Certificate) (Principal, error) {
	if cert == nil || len(cert.URIs) != 1 {
		return Principal{}, errors.New("device certificate has no unique Queqiao identity")
	}
	u := cert.URIs[0]
	if u.Scheme != "queqiao" || u.Host == "" {
		return Principal{}, errors.New("device certificate identity is malformed")
	}
	parts := strings.Split(strings.Trim(u.EscapedPath(), "/"), "/")
	if len(parts) != 4 || parts[0] != "account" || parts[2] != "device" {
		return Principal{}, errors.New("device certificate identity is malformed")
	}
	accountID, err := url.PathUnescape(parts[1])
	if err != nil || !validID(accountID) {
		return Principal{}, errors.New("device account identity is malformed")
	}
	deviceID, err := url.PathUnescape(parts[3])
	if err != nil || !validID(deviceID) {
		return Principal{}, errors.New("device identity is malformed")
	}
	publicKey, ok := cert.PublicKey.(ed25519.PublicKey)
	if !ok || len(publicKey) != ed25519.PublicKeySize {
		return Principal{}, errors.New("device certificate does not use Ed25519")
	}
	if !validID(u.Host) {
		return Principal{}, errors.New("device provider identity is malformed")
	}
	return Principal{ProviderID: u.Host, AccountID: accountID, DeviceID: deviceID, PublicKey: append(ed25519.PublicKey(nil), publicKey...)}, nil
}

func DeviceKeyID(publicKey ed25519.PublicKey) string {
	sum := sha256.Sum256(publicKey)
	return base64.RawURLEncoding.EncodeToString(sum[:12])
}

func constantTextEqual(a, b string) bool {
	return len(a) == len(b) && subtle.ConstantTimeCompare([]byte(a), []byte(b)) == 1
}
