package coded

import (
	"context"
	"sync/atomic"
	"testing"
	"time"

	"github.com/apernet/quic-go"
	wancongestion "github.com/bojieli/queqiao/internal/congestion"
	"github.com/bojieli/queqiao/internal/pathsim"
)

// datagramRate measures what a controller can actually push across the path,
// open loop: the sender offers datagrams as fast as the controller will let it
// and the receiver counts what arrives.
func datagramRate(t *testing.T, cfg pathsim.Config, set func(*quic.Conn), seconds float64) (offered, delivered float64) {
	t.Helper()
	client, server := quicPairWithout(t, cfg)
	if set != nil {
		set(client)
	}
	var received atomic.Int64
	go func() {
		for {
			d, err := server.ReceiveDatagram(context.Background())
			if err != nil {
				return
			}
			received.Add(int64(len(d)))
		}
	}()
	payload := make([]byte, 1200)
	var sent int64
	deadline := time.Now().Add(time.Duration(seconds * float64(time.Second)))
	for time.Now().Before(deadline) {
		if err := client.SendDatagram(payload); err != nil {
			time.Sleep(time.Millisecond)
			continue
		}
		sent++
	}
	time.Sleep(time.Second)
	return float64(sent) * 1200 * 8 / seconds / 1e6, float64(received.Load()) * 8 / seconds / 1e6
}

// A loss-responsive controller gives this path away, and that is the finding
// the whole design rests on. The erasure channel is not congestion: backing
// off does not reduce it, so a controller that backs off from it converges on
// nothing while the path sits idle.
//
// Measured across the emulated path at 20 seconds each:
//
//	default (Reno/Cubic)      0.09 Mbit/s delivered
//	BBR-TUIC                  5.6
//	Brutal, told 25 Mbit/s   14.03
//	erasure                  10.6
//
// Brutal is the bound rather than a competitor: it reaches the path only by
// ignoring loss entirely and pacing at a rate a human typed in, which is the
// one thing this transport is not allowed to require.
func TestTheErasureControllerReachesThePathOthersGiveAway(t *testing.T) {
	if testing.Short() {
		t.Skip("brings up QUIC across an emulated 300 ms path, several times")
	}
	const seconds = 8

	_, stock := datagramRate(t, liveChannel(), nil, seconds)
	_, tuic := datagramRate(t, liveChannel(), func(c *quic.Conn) {
		c.SetCongestionControl(wancongestion.NewTUICBBRSender(c.InitialPacketSize()))
	}, seconds)
	offered, erasure := datagramRate(t, liveChannel(), func(c *quic.Conn) {
		c.SetCongestionControl(wancongestion.NewErasureSender(c.InitialPacketSize()))
	}, seconds)

	t.Logf("delivered across the erasure channel: stock %.2f, bbr-tuic %.2f, erasure %.2f Mbit/s "+
		"(erasure offered %.1f Mbit/s against a 25 Mbit/s bottleneck)", stock, tuic, erasure, offered)

	// The channel's capacity is 25 x 0.58 = 14.5 Mbit/s. Half of it is a low
	// bar deliberately: this asserts the regime, not a tuning.
	if erasure < 7 {
		t.Errorf("erasure controller delivered %.2f Mbit/s of a 14.5 Mbit/s capacity", erasure)
	}
	// Correct RTT samples raised BBR-TUIC from the old bug's roughly 1 Mbit/s
	// to about 5.6 without changing the erasure controller's roughly 10.6.
	// Keep asserting a clearly different regime without encoding the obsolete
	// two-to-one ratio against the broken baseline.
	if erasure < 1.5*tuic {
		t.Errorf("erasure controller delivered %.2f Mbit/s against BBR-TUIC's %.2f; "+
			"the whole point is that it does not read the channel as congestion", erasure, tuic)
	}
}

// A clean path must not be made worse. On a path with no loss floor the
// correction is one and the suppression never triggers, so this has to come
// out where the stock controller does.
func TestTheErasureControllerDoesNotHarmACleanPath(t *testing.T) {
	if testing.Short() {
		t.Skip("brings up QUIC across an emulated 300 ms path")
	}
	lossless := pathsim.Config{
		OneWayDelay: 150 * time.Millisecond, RateBytesPerSec: uint64(25e6 / 8),
		PolicerRefillPeriod: 8 * time.Millisecond, Seed: 23,
	}
	_, stock := datagramRate(t, lossless, nil, 6)
	_, erasure := datagramRate(t, lossless, func(c *quic.Conn) {
		c.SetCongestionControl(wancongestion.NewErasureSender(c.InitialPacketSize()))
	}, 6)
	t.Logf("lossless path: stock %.2f, erasure %.2f Mbit/s", stock, erasure)
	if erasure < 0.8*stock {
		t.Errorf("erasure controller delivered %.2f Mbit/s on a clean path against the stock %.2f",
			erasure, stock)
	}
}
