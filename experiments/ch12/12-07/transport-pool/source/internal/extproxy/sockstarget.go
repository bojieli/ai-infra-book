package extproxy

import (
	"context"
	"errors"
	"io"
	"net"
	"sync"
	"time"

	"github.com/bojieli/queqiao/internal/socks5"
)

// SOCKSTarget is the SOCKS5 endpoint a tunnel stack forwards to.
//
// A proxy stack needs nothing like this: its own server is where a destination
// is dialled. A tunnel carries one port and knows nothing about destinations,
// so something on the far side has to speak SOCKS5 and dial. This is the
// smallest thing that does, and it is deliberately in-process: an external
// SOCKS5 server would be a third implementation in the measurement whose
// version, buffering and congestion settings nobody recorded.
//
// It sits beyond the emulator, so its own dial is loopback and adds no
// measured delay.
type SOCKSTarget struct {
	listener net.Listener
	wg       sync.WaitGroup
	closeOne sync.Once
}

// StartSOCKSTarget begins accepting on loopback. Close stops it and waits for
// the connections it is relaying, so a finished trial leaves nothing behind to
// contend with the next one.
func StartSOCKSTarget(ctx context.Context) (*SOCKSTarget, error) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return nil, err
	}
	target := &SOCKSTarget{listener: listener}
	target.wg.Add(1)
	go target.accept(ctx)
	return target, nil
}

// Address is what the tunnel's server should forward to.
func (t *SOCKSTarget) Address() string {
	if t == nil {
		return ""
	}
	return t.listener.Addr().String()
}

func (t *SOCKSTarget) accept(ctx context.Context) {
	defer t.wg.Done()
	go func() {
		<-ctx.Done()
		_ = t.listener.Close()
	}()
	for {
		conn, err := t.listener.Accept()
		if err != nil {
			return
		}
		t.wg.Add(1)
		go func() {
			defer t.wg.Done()
			t.serve(ctx, conn)
		}()
	}
}

func (t *SOCKSTarget) serve(ctx context.Context, conn net.Conn) {
	defer func() { _ = conn.Close() }()
	// The handshake is bounded: a tunnel that dies mid-negotiation must not
	// leave a goroutine holding a connection for the rest of the campaign.
	_ = conn.SetDeadline(time.Now().Add(30 * time.Second))
	request, err := socks5.ReadRequest(conn, nil)
	if err != nil {
		return
	}
	if request.Command != socks5.CommandConnect {
		// UDP association would have to be relayed back through the tunnel,
		// which carries one TCP port and cannot. Refusing is the honest
		// answer; the benchmark's UDP measurements do not use this path.
		_ = socks5.WriteReply(conn, socks5.ReplyCommandNotSupported, nil)
		return
	}
	dialer := net.Dialer{Timeout: 10 * time.Second}
	destination, err := dialer.DialContext(ctx, "tcp", request.Destination)
	if err != nil {
		_ = socks5.WriteReply(conn, socks5.ReplyHostUnreachable, nil)
		return
	}
	defer func() { _ = destination.Close() }()
	if err := socks5.WriteReply(conn, socks5.ReplySucceeded, destination.LocalAddr()); err != nil {
		return
	}
	// The transfer itself is unbounded in time: it is what the benchmark is
	// measuring, and a deadline here would cap the slowest stack's result at
	// the deadline rather than reporting it.
	_ = conn.SetDeadline(time.Time{})
	relay(conn, destination)
}

// relay copies in both directions and returns when either is finished. A
// half-close is forwarded where the connection supports it, so a destination
// that answers and stops is not held open by a client that has not.
func relay(client, destination net.Conn) {
	var wg sync.WaitGroup
	wg.Add(2)
	go func() {
		defer wg.Done()
		_, _ = io.Copy(destination, client)
		closeWrite(destination)
	}()
	go func() {
		defer wg.Done()
		_, _ = io.Copy(client, destination)
		closeWrite(client)
	}()
	wg.Wait()
}

func closeWrite(conn net.Conn) {
	type writeCloser interface{ CloseWrite() error }
	if half, ok := conn.(writeCloser); ok {
		_ = half.CloseWrite()
		return
	}
	_ = conn.Close()
}

// Close stops accepting and waits for the relays in flight.
func (t *SOCKSTarget) Close() error {
	if t == nil {
		return nil
	}
	var err error
	t.closeOne.Do(func() {
		err = t.listener.Close()
		t.wg.Wait()
	})
	if errors.Is(err, net.ErrClosed) {
		return nil
	}
	return err
}
