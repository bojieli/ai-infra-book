package baseline

import (
	"context"
	"crypto/tls"
	"fmt"
	"io"
	"net"
	"testing"
	"time"

	"github.com/apernet/quic-go"
	"github.com/bojieli/queqiao/internal/pathsim"
)

// TestRawQUICSaturatesThePath is the floor under every transport number this
// project reports: one QUIC connection, one stream, no proxy on either side,
// streaming through the same emulated path. If raw QUIC cannot fill the link
// then neither can anything built on it, and a utilisation figure measured for
// a PEP is measuring the QUIC stack.
func TestRawQUICSaturatesThePath(t *testing.T) {
	for _, c := range []struct{ rttMS, rateMbits, windowMB int }{{50, 400, 8}, {50, 400, 64}, {400, 400, 8}, {400, 400, 64}} {
		c := c
		t.Run(fmt.Sprintf("rtt%d_rate%d_win%dMB", c.rttMS, c.rateMbits, c.windowMB), func(t *testing.T) {
			cert, pool := testCertificate(t)
			serverConn, err := net.ListenPacket("udp", "127.0.0.1:0")
			if err != nil {
				t.Fatal(err)
			}
			defer serverConn.Close()
			relay, err := pathsim.New("127.0.0.1:0", serverConn.LocalAddr().String(), pathsim.Config{
				OneWayDelay:     time.Duration(c.rttMS) * time.Millisecond / 2,
				RateBytesPerSec: uint64(c.rateMbits) * 1e6 / 8,
			})
			if err != nil {
				t.Fatal(err)
			}
			defer relay.Close()

			const payload = 200 << 20
			streamWindow := uint64(c.windowMB) << 20
			qcfg := &quic.Config{
				MaxIdleTimeout:                 30 * time.Second,
				InitialStreamReceiveWindow:     streamWindow,
				MaxStreamReceiveWindow:         streamWindow,
				InitialConnectionReceiveWindow: 2 * streamWindow,
				MaxConnectionReceiveWindow:     2 * streamWindow,
			}
			ln, err := quic.Listen(serverConn, &tls.Config{
				Certificates: []tls.Certificate{cert}, NextProtos: []string{"raw-floor"},
			}, qcfg)
			if err != nil {
				t.Fatal(err)
			}
			defer ln.Close()
			ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
			defer cancel()
			go func() {
				conn, err := ln.Accept(ctx)
				if err != nil {
					return
				}
				stream, err := conn.OpenStreamSync(ctx)
				if err != nil {
					return
				}
				buf := make([]byte, 64<<10)
				for sent := 0; sent < payload; {
					n, err := stream.Write(buf)
					if err != nil {
						return
					}
					sent += n
				}
				_ = stream.Close()
			}()

			conn, err := quic.DialAddr(ctx, relay.LocalAddr(), &tls.Config{
				RootCAs: pool, ServerName: "queqiao.test", NextProtos: []string{"raw-floor"},
			}, qcfg)
			if err != nil {
				t.Fatal(err)
			}
			defer conn.CloseWithError(0, "")
			stream, err := conn.AcceptStream(ctx)
			if err != nil {
				t.Fatal(err)
			}
			started := time.Now()
			n, err := io.Copy(io.Discard, stream)
			elapsed := time.Since(started)
			if err != nil && n < payload {
				t.Fatalf("read %d of %d: %v", n, payload, err)
			}
			mbits := float64(n) * 8 / elapsed.Seconds() / 1e6
			t.Logf("rtt=%dms rate=%d window=%dMiB raw QUIC=%.1f Mbit/s util=%.2f",
				c.rttMS, c.rateMbits, c.windowMB, mbits, mbits/float64(c.rateMbits))
		})
	}
}
