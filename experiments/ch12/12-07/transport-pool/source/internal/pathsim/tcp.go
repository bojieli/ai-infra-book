package pathsim

import (
	"errors"
	"fmt"
	"math/rand"
	"net"
	"sync"
	"time"
)

// TCPRelay emulates a path for TCP-based transports: WebSocket, VLESS over
// TLS, Trojan, and anything else tunnelled over a stream.
//
// It applies propagation delay, a bottleneck rate, and a bounded buffer, and
// it deliberately does not apply packet loss. A userspace relay receives a
// byte stream, not segments: dropping bytes would corrupt the stream rather
// than trigger a retransmission, and the kernel's TCP stack — whose loss
// recovery is the interesting behaviour — sits below this relay where it
// cannot be reached. Emulating loss for these transports needs an IP-layer
// facility such as dummynet, which needs privilege this harness does not take.
//
// Comparing a TCP-based transport against a QUIC-based one under loss
// therefore requires a different tool. Comparing them at high delay and a
// shared bottleneck, which is what this provides, is still worth doing: it is
// where nested congestion control and per-connection setup cost show up.
type TCPRelay struct {
	cfg      Config
	target   string
	listener net.Listener

	upstream   direction
	downstream direction

	mu     sync.Mutex
	closed bool
	conns  map[net.Conn]struct{}

	wg   sync.WaitGroup
	done chan struct{}
}

// NewTCP starts a TCP relay on listen that forwards to target.
func NewTCP(listen, target string, cfg Config) (*TCPRelay, error) {
	if cfg.LossRate > 0 || cfg.UpstreamLossRate > 0 {
		return nil, errors.New("a TCP relay cannot emulate packet loss; see the note on TCPRelay")
	}
	cfg = cfg.withDefaults()
	listener, err := net.Listen("tcp", listen)
	if err != nil {
		return nil, fmt.Errorf("listen: %w", err)
	}
	r := &TCPRelay{
		cfg: cfg, target: target, listener: listener,
		conns: make(map[net.Conn]struct{}), done: make(chan struct{}),
	}
	r.upstream.rng = rand.New(rand.NewSource(cfg.Seed))
	r.downstream.rng = rand.New(rand.NewSource(cfg.Seed + 1))
	r.wg.Add(1)
	go r.accept()
	return r, nil
}

func (r *TCPRelay) LocalAddr() string { return r.listener.Addr().String() }

func (r *TCPRelay) Stats() (up, down Stats) { return r.upstream.stats(), r.downstream.stats() }

func (r *TCPRelay) Close() error {
	r.mu.Lock()
	if r.closed {
		r.mu.Unlock()
		return nil
	}
	r.closed = true
	close(r.done)
	conns := make([]net.Conn, 0, len(r.conns))
	for conn := range r.conns {
		conns = append(conns, conn)
	}
	r.conns = nil
	r.mu.Unlock()
	_ = r.listener.Close()
	for _, conn := range conns {
		_ = conn.Close()
	}
	r.wg.Wait()
	return nil
}

func (r *TCPRelay) accept() {
	defer r.wg.Done()
	for {
		client, err := r.listener.Accept()
		if err != nil {
			return
		}
		server, err := net.DialTimeout("tcp", r.target, 10*time.Second)
		if err != nil {
			_ = client.Close()
			continue
		}
		r.track(client)
		r.track(server)
		// Close the sockets only once both directions have finished. Closing
		// them when the first direction ends truncates the other: a tunnelled
		// protocol commonly half-closes its request side long before the
		// response has finished arriving, and hard-closing there cost a 4 MiB
		// transfer all but its first megabyte.
		var pair sync.WaitGroup
		pair.Add(2)
		r.wg.Add(3)
		go func() { defer r.wg.Done(); defer pair.Done(); r.pump(client, server, &r.upstream) }()
		go func() { defer r.wg.Done(); defer pair.Done(); r.pump(server, client, &r.downstream) }()
		go func() {
			defer r.wg.Done()
			pair.Wait()
			r.release(client)
			r.release(server)
		}()
	}
}

func (r *TCPRelay) track(conn net.Conn) {
	r.mu.Lock()
	defer r.mu.Unlock()
	if r.closed {
		_ = conn.Close()
		return
	}
	r.conns[conn] = struct{}{}
}

func (r *TCPRelay) release(conn net.Conn) {
	r.mu.Lock()
	if r.conns != nil {
		delete(r.conns, conn)
	}
	r.mu.Unlock()
	_ = conn.Close()
}

// pump copies one direction. Reading and delayed writing are separate stages
// on purpose: holding a chunk inline before reading the next one makes the
// relay strictly serial, so throughput collapses to one buffer per one-way
// delay regardless of the configured bottleneck rate. Measured at 100 ms with
// a 32 KiB buffer that capped a 100 Mbit/s path at about 5 Mbit/s.
//
// The queue is bounded, so a reader that outruns the bottleneck blocks, which
// is the backpressure a real bottleneck applies to a TCP sender once its
// buffer fills.
func (r *TCPRelay) pump(from, to net.Conn, d *direction) {
	type segment struct {
		data    []byte
		arrival time.Time
	}
	queue := make(chan segment, tcpRelayQueueDepth)
	writerDone := make(chan struct{})
	go func() {
		defer close(writerDone)
		for held := range queue {
			if wait := time.Until(held.arrival); wait > 0 {
				timer := time.NewTimer(wait)
				select {
				case <-timer.C:
				case <-r.done:
					timer.Stop()
					return
				}
			}
			if _, err := to.Write(held.data); err != nil {
				return
			}
			d.packetsOut.Add(1)
			d.bytesOut.Add(uint64(len(held.data)))
		}
		if closer, ok := to.(interface{ CloseWrite() error }); ok {
			_ = closer.CloseWrite()
		}
	}()

	for {
		buf := make([]byte, tcpRelaySegment)
		n, err := from.Read(buf)
		if n > 0 {
			d.packetsIn.Add(1)
			d.bytesIn.Add(uint64(n))
			arrival := d.scheduleStream(time.Now(), n, r.cfg)
			select {
			case queue <- segment{data: buf[:n], arrival: arrival}:
			case <-r.done:
				close(queue)
				<-writerDone
				return
			}
		}
		if err != nil {
			break
		}
	}
	close(queue)
	<-writerDone
}

const (
	// tcpRelaySegment is the read size. It is well below a bandwidth-delay
	// product so the queue, not the buffer, sets the pipelining depth.
	tcpRelaySegment = 16 * 1024
	// tcpRelayQueueDepth bounds in-flight chunks, providing backpressure in
	// place of the tail drop a packet relay would apply.
	tcpRelayQueueDepth = 512
)
