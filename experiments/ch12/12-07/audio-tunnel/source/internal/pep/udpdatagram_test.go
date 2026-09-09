package pep

import (
	"context"
	"encoding/binary"
	"errors"
	"io"
	"log/slog"
	"net"
	"sync"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/coded"
	"github.com/bojieli/queqiao/internal/metrics"
	"github.com/bojieli/queqiao/internal/pathmodel"
	"github.com/bojieli/queqiao/internal/pathsim"
	"github.com/bojieli/queqiao/internal/protocol"
	"github.com/bojieli/queqiao/internal/socks5"
)

// A UDP packet's sequence number can no longer be required to be the next
// one, because the substrate it crosses does not promise that. What it can
// still decide is whether a packet has already been delivered, and the window
// has to answer that without letting a peer make it hold anything.
func TestThePacketWindowAdmitsReorderingOnceAndDuplicatesNever(t *testing.T) {
	var w packetWindow
	// In order.
	for seq := uint64(0); seq < 10; seq++ {
		if !w.admit(seq) {
			t.Fatalf("refused sequence %d arriving in order", seq)
		}
	}
	// Every one of those again.
	for seq := uint64(0); seq < 10; seq++ {
		if w.admit(seq) {
			t.Fatalf("admitted sequence %d twice", seq)
		}
	}
	// A gap is not an error: it is the loss the application asked for by
	// choosing UDP, and what follows it is delivered.
	if !w.admit(20) {
		t.Fatal("refused a sequence past a gap")
	}
	// What the gap skipped still arrives, once each, in any order.
	for _, seq := range []uint64{15, 11, 19, 12} {
		if !w.admit(seq) {
			t.Fatalf("refused reordered sequence %d", seq)
		}
		if w.admit(seq) {
			t.Fatalf("admitted reordered sequence %d twice", seq)
		}
	}
	// Advance well past the window, then reach back behind it. That is too
	// far to place: it cannot be told from one already delivered, so it is
	// dropped rather than guessed at.
	if !w.admit(500) {
		t.Fatal("refused a sequence past the window")
	}
	if w.admit(500 - packetWindowWidth) {
		t.Fatal("admitted a sequence a full window behind")
	}
	if !w.admit(500 - packetWindowWidth + 1) {
		t.Fatal("refused a sequence just inside the window")
	}
	// A jump the peer chooses is a jump, not a walk: the window moves to it
	// in one step and holds nothing extra for having done so.
	if !w.admit(1 << 40) {
		t.Fatal("refused a far sequence")
	}
	// Just below it is ordinary reordering and is still placed; a full window
	// below is not.
	if !w.admit(1<<40 - 1) {
		t.Fatal("refused a sequence reordered across a far jump")
	}
	if w.admit(1<<40 - packetWindowWidth) {
		t.Fatal("admitted a sequence a full window below a far jump")
	}
	if !w.admit(1<<40 + 1) {
		t.Fatal("refused the sequence after a far jump")
	}
}

func TestUDPFinalACKTakesPrecedenceOverFollowingEOF(t *testing.T) {
	local, peer := net.Pipe()
	defer local.Close()
	defer peer.Close()
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	frames, errs := udpFrames(ctx, newFrameConn(local), 7)
	finalACK := protocol.Frame{Header: protocol.Header{
		Version: protocol.Version, Type: protocol.TypeAck, Flags: protocol.FlagAckFinal,
		SessionID: [16]byte{1}, FlowID: 7,
	}}
	writeDone := make(chan error, 1)
	go func() {
		writeDone <- protocol.WriteFrame(peer, finalACK)
		_ = peer.Close()
	}()

	select {
	case got := <-frames:
		if got.Header.Type != protocol.TypeAck || got.Header.Flags != protocol.FlagAckFinal {
			t.Fatalf("terminal frame = type %d flags %x", got.Header.Type, got.Header.Flags)
		}
	case <-time.After(time.Second):
		t.Fatal("timed out waiting for final ACK")
	}
	if err := <-writeDone; err != nil {
		t.Fatal(err)
	}
	select {
	case err := <-errs:
		t.Fatalf("EOF raced ahead of the queued final ACK: %v", err)
	case <-time.After(25 * time.Millisecond):
	}
}

// pipeCarrier is a datagram carrier that delivers to itself, so a frameConn
// can be given a coded substrate without a QUIC connection behind it.
type pipeCarrier struct {
	mu     sync.Mutex
	closed bool
	frames chan []byte
}

func newPipeCarrier() *pipeCarrier { return &pipeCarrier{frames: make(chan []byte, 64)} }

func (c *pipeCarrier) Send(d []byte) error {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.closed {
		return errors.New("closed")
	}
	select {
	case c.frames <- append([]byte(nil), d...):
		return nil
	default:
		return errors.New("full")
	}
}

func (c *pipeCarrier) Receive() ([]byte, error) {
	d, ok := <-c.frames
	if !ok {
		return nil, io.EOF
	}
	return d, nil
}

func (c *pipeCarrier) Close() error {
	c.mu.Lock()
	defer c.mu.Unlock()
	if !c.closed {
		c.closed = true
		close(c.frames)
	}
	return nil
}

// The routing rule, stated directly: a data frame reaches the coded path only
// where parity is worth its bytes, and a UDP packet reaches it whenever it
// exists.
//
// They differ because they are there for different reasons. Data is coded for
// the parity, and where a retransmission is cheaper it belongs on the stream.
// A packet is on datagrams for the substrate -- not retransmitted, not
// blocking the one behind it -- which is as true on a clean path as a lossy
// one.
func TestAPacketTakesTheDatagramSubstrateWhateverTheDataDoes(t *testing.T) {
	carrier := newPipeCarrier()
	path := coded.New(carrier, coded.Config{})
	t.Cleanup(func() { _ = path.Close() })
	fc := newSplitFrameConn(nopCloser{io.Discard}, path)

	packet := protocol.Frame{Header: protocol.Header{Type: protocol.TypePacket}}
	data := protocol.Frame{Header: protocol.Header{Type: protocol.TypeData}}
	control := protocol.Frame{Header: protocol.Header{Type: protocol.TypeAck}}

	if !fc.bulkFrame(packet) {
		t.Error("a UDP packet did not take the datagram substrate")
	}
	if fc.bulkFrame(control) {
		t.Error("a control frame took the datagram substrate")
	}
	// This path has measured nothing, so it is not coding, and data belongs
	// on the stream -- while the packet above still does not.
	if path.Coding() != fc.bulkFrame(data) {
		t.Errorf("a data frame's substrate did not follow whether the path codes (coding=%v)", path.Coding())
	}

	// The control keeps packets on the stream, which is what makes the two
	// substrates comparable on one build.
	fc.setPacketsOnStream(true)
	if fc.bulkFrame(packet) {
		t.Error("--udp-on-stream did not keep the packet on the stream")
	}

	// A lane with no datagram substrate at all -- a TLS/TCP lane -- is
	// unchanged, which is the fallback the SOCKS contract rests on.
	plain := newSplitFrameConn(nopCloser{io.Discard}, nil)
	if plain.bulkFrame(packet) {
		t.Error("a lane without datagrams routed a packet to one")
	}
}

type nopCloser struct{ io.Writer }

func (nopCloser) Read([]byte) (int, error) { return 0, io.EOF }
func (nopCloser) Close() error             { return nil }

// The counters exist so an operator can tell an association that took the
// datagram substrate from one that fell back, which is otherwise invisible.
func TestPacketSubstratesAreCounted(t *testing.T) {
	carrier := newPipeCarrier()
	path := coded.New(carrier, coded.Config{})
	t.Cleanup(func() { _ = path.Close() })
	fc := newSplitFrameConn(nopCloser{io.Discard}, path)

	packet := protocol.Frame{Header: protocol.Header{Version: protocol.Version, Type: protocol.TypePacket}}
	if err := fc.Write(packet); err != nil {
		t.Fatal(err)
	}
	fc.setPacketsOnStream(true)
	if err := fc.Write(packet); err != nil {
		t.Fatal(err)
	}
	deadline := time.Now().Add(2 * time.Second)
	for {
		datagram, stream := fc.PacketSubstrates()
		if datagram == 1 && stream == 1 {
			return
		}
		if time.Now().After(deadline) {
			t.Fatalf("counted %d on datagrams and %d on the stream, want one each", datagram, stream)
		}
	}
}

// udpAssociationOver brings up a client and server across an emulated path
// and returns a SOCKS UDP association: the local socket to send on, the
// address to send to, and the destination that echoes.
func udpAssociationOver(t *testing.T, path pathsim.Config, onStream bool) (*net.UDPConn, *net.UDPAddr, *net.UDPAddr) {
	t.Helper()
	pathmodel.Reset()
	t.Cleanup(pathmodel.Reset)

	destination, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = destination.Close() })
	go func() {
		buf := make([]byte, 2048)
		for {
			n, addr, readErr := destination.ReadFromUDP(buf)
			if readErr != nil {
				return
			}
			_, _ = destination.WriteToUDP(buf[:n], addr)
		}
	}()

	certificate, roots := testCertificate(t)
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	packetConn, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	server, err := NewServer(ServerConfig{
		ListenAddr: "127.0.0.1:0", Credentials: certificate,
		DestinationPolicy: DestinationPolicy{AllowPrivate: true}, EnableQUIC: true, Logger: logger,
		Metrics: metrics.New(), HandshakeTimeout: 30 * time.Second, UDPOnStream: onStream,
	})
	if err != nil {
		t.Fatal(err)
	}
	relay, err := pathsim.New("127.0.0.1:0", packetConn.LocalAddr().String(), path)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = relay.Close() })

	clientListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	client, err := NewClient(ClientConfig{
		ListenAddr: clientListener.Addr().String(), RemoteAddr: relay.LocalAddr(),
		Credentials: roots, Transport: TransportQUIC,
		EnableQUICPool: true, Logger: logger,
		Metrics: metrics.New(), UDPOnStream: onStream,
	})
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	t.Cleanup(cancel)
	go func() { _ = server.ServePacketConn(ctx, packetConn) }()
	go func() { _ = client.ServeListener(ctx, clientListener) }()

	control, err := net.DialTimeout("tcp", clientListener.Addr().String(), 5*time.Second)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = control.Close() })
	_ = control.SetDeadline(time.Now().Add(60 * time.Second))
	if _, err := control.Write([]byte{5, 1, 0}); err != nil {
		t.Fatal(err)
	}
	var method [2]byte
	if _, err := io.ReadFull(control, method[:]); err != nil {
		t.Fatal(err)
	}
	if _, err := control.Write([]byte{5, socks5.CommandUDPAssociate, 0, 1, 0, 0, 0, 0, 0, 0}); err != nil {
		t.Fatal(err)
	}
	var reply [10]byte
	if _, err := io.ReadFull(control, reply[:]); err != nil {
		t.Fatal(err)
	}
	if reply[1] != socks5.ReplySucceeded {
		t.Fatalf("UDP associate failed: %v", reply)
	}
	_ = control.SetDeadline(time.Time{})

	bound := &net.UDPAddr{IP: net.IP(reply[4:8]), Port: int(binary.BigEndian.Uint16(reply[8:10]))}
	local, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = local.Close() })
	return local, bound, destination.LocalAddr().(*net.UDPAddr)
}

// socksUDPRequest wraps a payload for the SOCKS UDP relay.
func socksUDPRequest(to *net.UDPAddr, payload []byte) []byte {
	request := append([]byte{0, 0, 0, 1}, to.IP.To4()...)
	var port [2]byte
	binary.BigEndian.PutUint16(port[:], uint16(to.Port))
	return append(append(request, port[:]...), payload...)
}

// This is what the datagram substrate is for, and the only claim that matters
// enough to be a test rather than a measurement.
//
// A stream retransmits a lost packet and delivers in order, so every packet
// behind a lost one waits for it -- at this path's round trip, more than a
// second for a loss that the application would rather simply not have heard
// about. Over datagrams a lost packet is lost and the next one is not late.
//
// Both halves run the same code over the same seeded path; only the substrate
// differs, which is what --udp-on-stream exists for.
func TestALostUDPPacketDoesNotHoldUpTheOneBehindIt(t *testing.T) {
	if testing.Short() {
		t.Skip("brings up QUIC across an emulated lossy path twice")
	}
	const oneWay = 100 * time.Millisecond
	const packets = 24
	roundTrip := 2 * oneWay

	measure := func(onStream bool) (delivered int, worst time.Duration) {
		path := pathsim.Config{
			OneWayDelay: oneWay, RateBytesPerSec: uint64(25e6 / 8),
			PolicerRefillPeriod: 8 * time.Millisecond, LossRate: 0.15, Seed: 7,
		}
		local, bound, echo := udpAssociationOver(t, path, onStream)
		buf := make([]byte, 4096)
		for i := range packets {
			payload := []byte{byte(i), 'p', 'i', 'n', 'g'}
			start := time.Now()
			if _, err := local.WriteToUDP(socksUDPRequest(echo, payload), bound); err != nil {
				t.Fatal(err)
			}
			// One at a time, so what is measured is this packet's own
			// latency rather than a queue's.
			_ = local.SetReadDeadline(time.Now().Add(3 * time.Second))
			n, _, err := local.ReadFromUDP(buf)
			if err != nil {
				continue // lost, which over datagrams is allowed
			}
			if elapsed := time.Since(start); elapsed > worst {
				worst = elapsed
			}
			got, err := socks5.ReadUDPDatagram(buf[:n])
			if err != nil {
				t.Fatal(err)
			}
			if len(got.Payload) == 0 || got.Payload[0] != byte(i) {
				t.Fatalf("packet %d came back as %v", i, got.Payload)
			}
			delivered++
		}
		return delivered, worst
	}

	datagramDelivered, datagramWorst := measure(false)
	streamDelivered, streamWorst := measure(true)
	t.Logf("datagrams: %d of %d delivered, worst %v; stream: %d of %d, worst %v (round trip %v)",
		datagramDelivered, packets, datagramWorst.Round(time.Millisecond),
		streamDelivered, packets, streamWorst.Round(time.Millisecond), roundTrip)

	if datagramDelivered == 0 {
		t.Fatal("no packet crossed the datagram substrate at all")
	}
	// A packet that arrives at all arrives about a round trip after it was
	// sent. Anything much past that waited for a retransmission it should
	// never have been behind.
	if datagramWorst > 2*roundTrip {
		t.Errorf("the worst delivered packet took %v against a round trip of %v, so it "+
			"waited for one that was lost", datagramWorst.Round(time.Millisecond), roundTrip)
	}
	if streamWorst <= datagramWorst {
		t.Errorf("the stream's worst packet was %v against the datagram substrate's %v; "+
			"the two substrates are not behaving differently, so this is not measuring what it claims",
			streamWorst.Round(time.Millisecond), datagramWorst.Round(time.Millisecond))
	}
}
