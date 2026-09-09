// Command queqiaoref runs the TUIC-shaped reference proxy as a standalone
// client or server so queqiao can be compared against it on a real link.
//
// It is a measurement control, not a product: it implements TUIC's data-path
// shape (one authenticated QUIC connection, one bidirectional stream per
// relayed TCP connection, unframed copying) on the same QUIC stack queqiao
// uses. Running both over the same path at the same time isolates the
// transport design from the language and library, which a comparison against a
// separately built native implementation cannot.
//
// It deliberately has no fallback, no UDP support, and no resource policy. Do
// not deploy it as a tunnel.
package main

import (
	"context"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/hex"
	"encoding/pem"
	"errors"
	"flag"
	"fmt"
	"log/slog"
	"math/big"
	"net"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/bojieli/queqiao/internal/baseline"
)

func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintf(os.Stderr, "queqiaoref: %v\n", err)
		os.Exit(1)
	}
}

func run(args []string) error {
	var (
		mode       string
		listen     string
		remote     string
		serverName string
		tokenHex   string
		tokenFile  string
		certFile   string
		keyFile    string
		rootCAFile string
		localAddr  string
		congestion string
		brutalRate uint64
		genCert    string
		logLevel   string
	)
	fs := flag.NewFlagSet("queqiaoref", flag.ContinueOnError)
	fs.StringVar(&mode, "mode", "", "server, client, or gencert")
	fs.StringVar(&listen, "listen", "", "server UDP address, or client SOCKS5 address")
	fs.StringVar(&remote, "remote", "", "client: reference server address")
	fs.StringVar(&serverName, "server-name", "queqiao.test", "TLS server name")
	fs.StringVar(&tokenHex, "token", "", "32-byte shared token, hex encoded")
	fs.StringVar(&tokenFile, "token-file", "", "file containing the hex-encoded token")
	fs.StringVar(&certFile, "tls-cert", "", "server certificate PEM")
	fs.StringVar(&keyFile, "tls-key", "", "server private key PEM")
	fs.StringVar(&rootCAFile, "root-ca", "", "client: PEM to trust")
	fs.StringVar(&localAddr, "local-address", "", "client: bind the outer UDP socket to this local IP")
	fs.StringVar(&congestion, "congestion", "bbr-tuic", "congestion controller: reno, bbr, bbr-tuic, or brutal")
	fs.Uint64Var(&brutalRate, "brutal-bytes-per-sec", 0, "fixed send rate in bytes/s when --congestion=brutal")
	fs.StringVar(&genCert, "gencert-prefix", "reference", "gencert: output prefix for PEM files")
	fs.StringVar(&logLevel, "log-level", "info", "debug, info, warn, or error")
	if err := fs.Parse(args); err != nil {
		return err
	}

	level := slog.LevelInfo
	switch strings.ToLower(logLevel) {
	case "debug":
		level = slog.LevelDebug
	case "warn":
		level = slog.LevelWarn
	case "error":
		level = slog.LevelError
	}
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: level}))

	if mode == "gencert" {
		return generateCertificate(genCert, serverName)
	}

	token, err := loadToken(tokenHex, tokenFile)
	if err != nil {
		return err
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	switch mode {
	case "server":
		if listen == "" || certFile == "" || keyFile == "" {
			return errors.New("server mode requires --listen, --tls-cert, and --tls-key")
		}
		certificate, err := tls.LoadX509KeyPair(certFile, keyFile)
		if err != nil {
			return fmt.Errorf("load certificate: %w", err)
		}
		server, err := baseline.NewServer(baseline.ServerConfig{
			ListenAddr: listen, Certificate: certificate, Token: token,
			Transport: baseline.TUICTransport(), Congestion: baseline.CongestionKind(congestion),
			BrutalBytesPerSec: brutalRate, Logger: logger,
		})
		if err != nil {
			return err
		}
		packet, err := net.ListenPacket("udp", listen)
		if err != nil {
			return fmt.Errorf("listen: %w", err)
		}
		defer packet.Close()
		logger.Info("reference server listening", "address", packet.LocalAddr().String(), "congestion", congestion)
		return server.Serve(ctx, packet)
	case "client":
		if listen == "" || remote == "" {
			return errors.New("client mode requires --listen and --remote")
		}
		var roots *x509.CertPool
		if rootCAFile != "" {
			pemBytes, err := os.ReadFile(rootCAFile)
			if err != nil {
				return fmt.Errorf("read root CA: %w", err)
			}
			roots = x509.NewCertPool()
			if !roots.AppendCertsFromPEM(pemBytes) {
				return errors.New("root CA file contained no certificate")
			}
		}
		client, err := baseline.NewClient(baseline.ClientConfig{
			ListenAddr: listen, RemoteAddr: remote, ServerName: serverName, RootCAs: roots,
			Token: token, Transport: baseline.TUICTransport(),
			Congestion: baseline.CongestionKind(congestion), BrutalBytesPerSec: brutalRate,
			LocalAddress: localAddr, Logger: logger,
		})
		if err != nil {
			return err
		}
		defer client.Close()
		listener, err := net.Listen("tcp", listen)
		if err != nil {
			return fmt.Errorf("listen: %w", err)
		}
		logger.Info("reference client listening", "socks5", listener.Addr().String(), "remote", remote, "congestion", congestion)
		return client.ServeListener(ctx, listener)
	default:
		return errors.New("--mode must be server, client, or gencert")
	}
}

func loadToken(hexToken, tokenFile string) ([]byte, error) {
	if tokenFile != "" {
		raw, err := os.ReadFile(tokenFile)
		if err != nil {
			return nil, fmt.Errorf("read token file: %w", err)
		}
		hexToken = strings.TrimSpace(string(raw))
	}
	if hexToken == "" {
		return nil, errors.New("a --token or --token-file is required")
	}
	token, err := hex.DecodeString(hexToken)
	if err != nil {
		return nil, fmt.Errorf("decode token: %w", err)
	}
	if len(token) != 32 {
		return nil, fmt.Errorf("token must be 32 bytes, got %d", len(token))
	}
	return token, nil
}

// generateCertificate writes a self-signed pair for an isolated measurement
// listener. The client trusts exactly this certificate, so the reference never
// needs a verification bypass.
func generateCertificate(prefix, serverName string) error {
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		return err
	}
	serial, err := rand.Int(rand.Reader, new(big.Int).Lsh(big.NewInt(1), 128))
	if err != nil {
		return err
	}
	template := &x509.Certificate{
		SerialNumber: serial,
		Subject:      pkix.Name{CommonName: serverName},
		DNSNames:     []string{serverName},
		NotBefore:    time.Now().Add(-time.Minute),
		NotAfter:     time.Now().Add(24 * time.Hour),
		KeyUsage:     x509.KeyUsageDigitalSignature | x509.KeyUsageKeyEncipherment,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
	}
	der, err := x509.CreateCertificate(rand.Reader, template, template, &key.PublicKey, key)
	if err != nil {
		return err
	}
	keyDER, err := x509.MarshalPKCS8PrivateKey(key)
	if err != nil {
		return err
	}
	certPath, keyPath := prefix+"-cert.pem", prefix+"-key.pem"
	if err := os.WriteFile(certPath, pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der}), 0o644); err != nil {
		return err
	}
	if err := os.WriteFile(keyPath, pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: keyDER}), 0o600); err != nil {
		return err
	}
	token := make([]byte, 32)
	if _, err := rand.Read(token); err != nil {
		return err
	}
	if err := os.WriteFile(prefix+"-token", []byte(hex.EncodeToString(token)+"\n"), 0o600); err != nil {
		return err
	}
	fmt.Printf("%s\n%s\n%s-token\n", certPath, keyPath, prefix)
	return nil
}
