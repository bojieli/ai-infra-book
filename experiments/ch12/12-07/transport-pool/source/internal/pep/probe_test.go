package pep

import (
	"context"
	"crypto/x509"
	"io"
	"log/slog"
	"net"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/metrics"
)

func TestClientProbeAuthenticatesProviderWithoutOpeningFlow(t *testing.T) {
	for _, transport := range []TransportKind{TransportTCP, TransportQUIC} {
		t.Run(string(transport), func(t *testing.T) {
			serverCredentials, clientCredentials := testCertificate(t)
			logger := slog.New(slog.NewTextHandler(io.Discard, nil))
			serverMetrics := metrics.New()
			server, err := NewServer(ServerConfig{
				ListenAddr: "127.0.0.1:0", Credentials: serverCredentials,
				EnableTCP: transport == TransportTCP, EnableQUIC: transport == TransportQUIC,
				Logger: logger, Metrics: serverMetrics,
			})
			if err != nil {
				t.Fatal(err)
			}

			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			serverResult := make(chan error, 1)
			var endpoint string
			if transport == TransportTCP {
				listener, listenErr := net.Listen("tcp", "127.0.0.1:0")
				if listenErr != nil {
					t.Fatal(listenErr)
				}
				defer listener.Close()
				endpoint = listener.Addr().String()
				go func() { serverResult <- server.ServeListener(ctx, listener) }()
			} else {
				packetConn, listenErr := net.ListenPacket("udp", "127.0.0.1:0")
				if listenErr != nil {
					t.Fatal(listenErr)
				}
				defer packetConn.Close()
				endpoint = packetConn.LocalAddr().String()
				go func() { serverResult <- server.ServePacketConn(ctx, packetConn) }()
			}

			client, err := NewClient(ClientConfig{
				ListenAddr: "127.0.0.1:0", RemoteAddr: endpoint,
				Credentials: clientCredentials, Transport: transport,
				EnableQUICPool: false, Logger: logger,
			})
			if err != nil {
				t.Fatal(err)
			}
			probeContext, probeCancel := context.WithTimeout(ctx, 5*time.Second)
			result, err := client.Probe(probeContext)
			probeCancel()
			if err != nil {
				t.Fatal(err)
			}
			if result.Transport != transport {
				t.Fatalf("probe transport %q, want %q", result.Transport, transport)
			}
			if result.Latency <= 0 || result.Latency > 5*time.Second {
				t.Fatalf("invalid probe latency %v", result.Latency)
			}
			if snapshot := serverMetrics.Snapshot(); snapshot.FlowsStarted != 0 {
				t.Fatalf("probe opened a destination flow: %+v", snapshot)
			}

			cancel()
			if err := <-serverResult; err != nil {
				t.Fatalf("server shutdown: %v", err)
			}
		})
	}
}

func TestClientProbeRejectsRevokedDevice(t *testing.T) {
	serverCredentials, clientCredentials := testCertificate(t)
	leaf, err := x509.ParseCertificate(clientCredentials.Certificate.Certificate[0])
	if err != nil {
		t.Fatal(err)
	}
	principal, err := identity.PrincipalFromCertificate(leaf)
	if err != nil {
		t.Fatal(err)
	}
	if err := serverCredentials.Store.RevokeDevice(principal.DeviceID, time.Now()); err != nil {
		t.Fatal(err)
	}

	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	server, err := NewServer(ServerConfig{
		ListenAddr: "127.0.0.1:0", Credentials: serverCredentials,
		EnableTCP: true, Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	ctx, cancel := context.WithCancel(context.Background())
	serverResult := make(chan error, 1)
	go func() { serverResult <- server.ServeListener(ctx, listener) }()

	client, err := NewClient(ClientConfig{
		ListenAddr: "127.0.0.1:0", RemoteAddr: listener.Addr().String(),
		Credentials: clientCredentials, Transport: TransportTCP, Logger: logger,
	})
	if err != nil {
		t.Fatal(err)
	}
	probeContext, probeCancel := context.WithTimeout(ctx, 2*time.Second)
	_, probeErr := client.Probe(probeContext)
	probeCancel()
	if probeErr == nil {
		t.Fatal("revoked device unexpectedly authenticated")
	}

	cancel()
	if err := <-serverResult; err != nil {
		t.Fatalf("server shutdown: %v", err)
	}
}
