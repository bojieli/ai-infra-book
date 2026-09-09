package coded

import (
	"fmt"
	"math/rand"
	"sync"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/fec"
	"github.com/bojieli/queqiao/internal/pathmodel"
)

// refusingPipe is a carrier that refuses some datagrams outright, which is what
// a QUIC connection does when its estimate of what fits in a packet moves under
// a symbol already sized against the old one.
type refusingPipe struct {
	*lossyPipe
	mu      sync.Mutex
	every   int
	offered int
	refused int
}

func (p *refusingPipe) Send(d []byte) error {
	p.mu.Lock()
	p.offered++
	refuse := p.every > 0 && p.offered%p.every == 0
	if refuse {
		p.refused++
	}
	p.mu.Unlock()
	if refuse {
		return fmt.Errorf("%w: %d bytes offered, 0 accepted", ErrDatagramTooLarge, len(d))
	}
	return p.lossyPipe.Send(d)
}

func (p *refusingPipe) refusals() int {
	p.mu.Lock()
	defer p.mu.Unlock()
	return p.refused
}

// A datagram this endpoint never managed to transmit is not something the path
// did. Charging it to the channel raises the measured erasure rate, which sizes
// more parity, which is more load on the path that was already failing -- so
// the number a refused datagram took must not become a gap in what the peer
// receives.
func TestARefusedDatagramIsNotMeasuredAsWireLoss(t *testing.T) {
	pa, pb := newPipes(11, 0)
	refusing := &refusingPipe{lossyPipe: pa, every: 7}
	cfg := Config{SymbolBytes: 1100, RoundTrip: 60 * time.Millisecond, Path: measuredPath(0.2)}
	sender, receiver := New(refusing, cfg), New(pb, cfg)
	t.Cleanup(func() { sender.Close(); receiver.Close() })

	done := make(chan struct{})
	go func() {
		defer close(done)
		for {
			if _, err := receiver.Receive(); err != nil {
				return
			}
		}
	}()

	rng := rand.New(rand.NewSource(12))
	frame := make([]byte, 900)
	for i := 0; i < 400; i++ {
		rng.Read(frame)
		if err := sender.Send(frame); err != nil {
			t.Fatalf("send %d: %v", i, err)
		}
	}
	// The receiver decides a sequence number once the newest is a reorder
	// tolerance past it, so give the last symbols time to arrive and settle.
	deadline := time.Now().Add(5 * time.Second)
	var stats Stats
	for time.Now().Before(deadline) {
		stats = receiver.Stats()
		if stats.Snapshot.Decided > 200 {
			break
		}
		time.Sleep(10 * time.Millisecond)
	}

	if refusing.refusals() == 0 {
		t.Fatal("the carrier refused nothing, so this proves nothing")
	}
	if stats.Snapshot.Decided == 0 {
		t.Fatal("the receiver decided no sequence numbers")
	}
	if stats.Snapshot.Loss != 0 {
		t.Fatalf("wire loss = %.4f after %d local refusals and no channel erasure (decided %d)",
			stats.Snapshot.Loss, refusing.refusals(), stats.Snapshot.Decided)
	}
	if sent := sender.Stats().Sent; sent == 0 {
		t.Fatal("nothing was sent")
	}
}

// A refusal still costs the symbol it carried. That casualty belongs to the
// session above, which re-issues it -- it is only the channel measurement it
// must stay out of.
func TestARefusedDatagramStillCostsItsSymbol(t *testing.T) {
	pa, pb := newPipes(13, 0)
	refusing := &refusingPipe{lossyPipe: pa, every: 3}
	// No parity, so a refused symbol has nothing to repair it and the receive
	// side must account for it as a casualty rather than silently.
	cfg := Config{SymbolBytes: 1100, RoundTrip: 60 * time.Millisecond, Path: pathmodel.NewPathModel()}
	sender, receiver := New(refusing, cfg), New(pb, cfg)
	t.Cleanup(func() { sender.Close(); receiver.Close() })

	arrived := 0
	done := make(chan struct{})
	go func() {
		defer close(done)
		for {
			if _, err := receiver.Receive(); err != nil {
				return
			}
			arrived++
		}
	}()

	// More symbols than the decoder's window, or nothing is ever evicted and
	// no casualty is ever accounted for.
	frame := make([]byte, 900)
	for i := 0; i < 3*fec.MinDecoderWidth; i++ {
		if err := sender.Send(frame); err != nil {
			t.Fatalf("send %d: %v", i, err)
		}
	}
	deadline := time.Now().Add(5 * time.Second)
	var stats Stats
	for time.Now().Before(deadline) {
		stats = receiver.Stats()
		if stats.Lost > 0 {
			break
		}
		time.Sleep(10 * time.Millisecond)
	}
	if stats.Lost == 0 {
		t.Fatal("a symbol that never left is not accounted for anywhere")
	}
	if stats.Snapshot.Loss != 0 {
		t.Fatalf("wire loss = %.4f, want the casualty charged to the session and not to the channel", stats.Snapshot.Loss)
	}
}

// Lost had no denominator: Sent counts the direction this endpoint transmits
// into and Lost the direction it receives, so an operator comparing them saw
// "lost is ten times sent" and concluded the accounting was impossible.
func TestReceiveDirectionRatesStayRates(t *testing.T) {
	for _, test := range []struct {
		name              string
		stats             Stats
		erasure, residual float64
	}{
		{name: "nothing received", stats: Stats{Sent: 116796}},
		{
			name:    "asymmetric flow",
			stats:   Stats{Sent: 100, Sources: 60, Recovered: 20, Lost: 20},
			erasure: 0.4, residual: 0.2,
		},
		{name: "everything lost", stats: Stats{Lost: 50}, erasure: 1, residual: 1},
	} {
		t.Run(test.name, func(t *testing.T) {
			if got := test.stats.Erasure(); got != test.erasure {
				t.Fatalf("erasure = %v, want %v", got, test.erasure)
			}
			if got := test.stats.Residual(); got != test.residual {
				t.Fatalf("residual = %v, want %v", got, test.residual)
			}
			if got := test.stats.Erasure(); got < 0 || got > 1 {
				t.Fatalf("erasure = %v is not a rate", got)
			}
		})
	}
}
