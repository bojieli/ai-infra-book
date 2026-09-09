package pep

import (
	"context"
	"errors"
	"fmt"
	"net"
	"time"

	"github.com/bojieli/queqiao/internal/netbind"
	"github.com/bojieli/queqiao/internal/pathmodel"
	"github.com/bojieli/queqiao/internal/protocol"
)

// The path a client is on is not a property of the server. Moving from Wi-Fi
// to a cellular link, or bringing up a VPN, changes the erasure rate, the
// bottleneck and the minimum round trip all at once, and everything this
// transport sizes is sized from those three.
//
// Nothing in QUIC tells the application this happened. The connection either
// keeps working from a new address or dies, and in both cases the measurements
// behind it belong to a path that no longer exists. Carrying them forward is
// worse than having none: an erasure floor from a cellular link tells a
// Wi-Fi connection to spend two thirds of its bandwidth on parity it does not
// need, and a Wi-Fi floor tells a cellular one to send none of the parity it
// does.
//
// So the client watches which local address the kernel would use to reach the
// server, and treats a change as what it is: a different path, whose model
// starts empty and is filled by a connection opened for that purpose rather
// than by whichever flow happens to be first.
const (
	// uplinkPollInterval is how often the local address is checked. It costs a
	// socket that is opened, asked which route it was given, and closed
	// without sending anything, so this can be frequent enough to catch a
	// change before the user notices it.
	uplinkPollInterval = 2 * time.Second
)

// currentUplink is the local address an outer connection will use to reach
// the server.
//
// When an address or interface was configured, every TCP and QUIC dial is
// explicitly bound to it. Asking the unbound routing table in that case can
// produce a different answer (notably while a VPN owns the default route),
// causing the watcher to repeatedly discard a healthy pool. Re-resolving the
// configured spec preserves DHCP and interface-change detection while asking
// the same question as the real dial path.
//
// Without an explicit binding, dialling a UDP socket sends no packets: it
// binds the socket and asks the routing table which source address this
// destination gets.
func (c *Client) currentUplink() string {
	address, _ := c.currentUplinkState()
	return address
}

// currentUplinkState distinguishes an observed loss of a configured dynamic
// binding from an inconclusive route probe. That distinction matters when two
// networks assign the same private address: the address before and after the
// interruption is equal, but every connection and path measurement still
// belongs to the network which disappeared.
func (c *Client) currentUplinkState() (address string, unavailable bool) {
	if c.cfg.LocalAddress != "" {
		result, err := netbind.ResolveWithInterface(c.cfg.LocalAddress)
		if err != nil {
			// A literal address is immutable, while if:NAME and auto are resolved
			// from live interface state. Failure of the latter is positive
			// evidence that the bound uplink is currently unavailable.
			return "", netbind.IsDynamic(c.cfg.LocalAddress)
		}
		return result.Addr.String(), false
	}
	conn, err := (&net.Dialer{Control: c.cfg.SocketControl}).Dial("udp", c.cfg.RemoteAddr)
	if err != nil {
		// An unbound probe can fail for reasons unrelated to the local link
		// (resolution, endpoint syntax, or policy), so it remains inconclusive.
		return "", false
	}
	defer conn.Close()
	return addressHost(conn.LocalAddr()), false
}

type uplinkWatchState struct {
	known       string
	interrupted bool
}

// observe reports whether connections belonging to the previous path must be
// discarded. A definite unavailable interval is itself a path boundary, even
// if the address on the other side is textually identical. Inconclusive empty
// observations stay harmless and do not churn a healthy pool.
func (s *uplinkWatchState) observe(current string, unavailable bool) (from string, changed bool) {
	if current == "" {
		if unavailable {
			s.interrupted = true
		}
		return s.known, false
	}
	from = s.known
	changed = s.interrupted || current != s.known
	s.known = current
	s.interrupted = false
	return from, changed
}

// watchUplink notices the machine changing how it reaches the server.
func (c *Client) watchUplink(ctx context.Context, known string) {
	state := uplinkWatchState{known: known}
	ticker := time.NewTicker(uplinkPollInterval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
		}
		current, unavailable := c.currentUplinkState()
		from, changed := state.observe(current, unavailable)
		if !changed {
			continue
		}
		c.cfg.Logger.Info("uplink changed", "from", from, "to", current)
		c.onUplinkChanged(ctx)
	}
}

// onUplinkChanged abandons what belonged to the old path and measures the new
// one before anything needs it.
func (c *Client) onUplinkChanged(ctx context.Context) {
	// Reachability evidence belongs to the old uplink just as completely as
	// its congestion and erasure measurements do. Carrying a UDP cooldown onto
	// the new interface would suppress the very probe that can measure it.
	if c.udpHealth != nil {
		c.udpHealth.reset()
	}
	// The pooled connection is bound to the address that is gone. Even where
	// it survives by migrating, its congestion state, its erasure floor and
	// its bottleneck all describe the old path.
	c.closeQUICPool()
	c.prewarmPath(ctx)
}

// prewarmPath opens a connection for the sake of what opening one measures.
//
// The first flow on an unmeasured path is carried uncoded, because nothing yet
// knows the path erases -- and on the channel this targets that is the
// difference between a small exchange taking 618 ms and 1.9 s. Paying for the
// handshake here means the first flow the user actually asks for does not pay
// for it, in either the round trips or the ignorance.
func (c *Client) prewarmPath(ctx context.Context) {
	if c.cfg.Transport == TransportTCP {
		return
	}
	warm, cancel := context.WithTimeout(ctx, prewarmTimeout)
	defer cancel()

	// Prewarming is not a second transport policy. AUTO must use the same
	// delayed TCP standby and bounded QUIC preference as an application flow;
	// bypassing that decision made a TCP-only gateway hold the local listener
	// unready for the entire QUIC timeout. A selected TCP lane needs no erasure
	// measurement, while a selected QUIC lane is the path the flow will use.
	var lane *authenticatedLane
	var err error
	if c.cfg.Transport == TransportAuto {
		lane, err = c.chooseAuthenticatedLane(warm)
	} else {
		lane, err = c.dialAuthenticatedCandidate(warm, TransportQUIC)
	}
	if err != nil {
		c.cfg.Logger.Debug("path prewarm failed", "error", err)
		return
	}
	if lane.kind != TransportQUIC {
		_ = lane.fc.Close()
		return
	}
	// Mutual TLS completes before the stream is returned. When pooling is
	// enabled the connection stays pooled, so the first real flow inherits both
	// the handshake and the path measurement without another authentication
	// exchange.
	// The handshake alone is about ten packets, which is enough to notice that
	// a path erases and not enough to say how much, so the prewarm sends a
	// little more before letting go.
	c.probePath(lane)
	// The connection stays in the pool; only this lane's framing is done with.
	_ = lane.fc.Close()
}

const (
	// pathProbePackets is how much padding the prewarm sends to measure the
	// path with. The erasure floor is a proportion, and a proportion measured
	// from ten packets is a guess: at 40% loss, ten packets put its standard
	// error near fifteen points, and the code rate chosen from it would be
	// wrong by more than the parity it was choosing. A hundred brings that
	// under five.
	//
	// It is padding rather than something useful because there is nothing
	// useful to send yet -- that is what makes it a prewarm -- and it is a
	// hundred rather than a thousand because this runs when a phone changes
	// network, where the bytes are the user's.
	pathProbePackets = 100
	// pathProbeBudget bounds the probe in time as well as in packets, so a
	// path too slow to deliver them does not hold the prewarm open.
	pathProbeBudget = 3 * time.Second
)

// probePath sends enough traffic for the congestion controller to measure the
// path, and throws it away.
//
// The measurement is not of the padding's contents but of its transport
// acknowledgements. The server reflects the authenticated, destination-free
// sequence one-for-one, so each endpoint's controller measures the direction
// it actually sends into and publishes that evidence before a user flow is
// accepted.
func (c *Client) probePath(lane *authenticatedLane) {
	if lane == nil || lane.fc == nil {
		return
	}
	payload := make([]byte, probePayloadBytes)
	deadline := time.Now().Add(pathProbeBudget)
	_ = lane.outer.SetDeadline(deadline)
	sent := 0
	for sent < pathProbePackets && time.Now().Before(deadline) {
		frame := protocol.Frame{
			Header: protocol.Header{
				Version: protocol.Version, Type: protocol.TypeProbe,
				SessionID: lane.sessionID, FlowID: probeFlowID, Sequence: uint64(sent), Class: protocol.ClassNew,
			},
			Payload: payload,
		}
		if err := lane.fc.Write(frame); err != nil {
			return
		}
		sent++
	}
	// A half-close is the probe's delimiter. The authenticated gateway echoes
	// exactly the bounded padding it received, then closes its send direction;
	// reading that echo makes the connection carry enough server-to-client
	// traffic for the gateway's own controller to measure that direction.
	//
	// The echo is required rather than hoped for. Version 1 has no capability
	// negotiation and no compatibility window: a peer that speaks the ALPN and
	// completes mutual TLS has agreed to all of protocol 1, so a gateway that
	// accepts the probe and does not reflect it is not an older build to be
	// tolerated -- it is a peer whose behaviour this client cannot account for,
	// on a connection it was about to hand real traffic to.
	if closer, ok := lane.outer.(interface{ CloseWrite() error }); ok && sent > 0 {
		if err := closer.CloseWrite(); err == nil {
			if err := c.readPathProbeEchoes(lane, sent); err != nil {
				c.rejectProbePeer(lane, err)
				return
			}
		}
	}
	c.awaitMeasurement(lane, deadline)
}

// probeEchoViolation is a gateway that did not reflect the probe sequence
// protocol 1 requires it to reflect.
//
// It is kept distinct from a slow path because the two call for opposite
// responses. The probe rides the reliable control stream, so a short echo is
// never loss: either the budget expired, which is a measurement this client
// simply does not get, or the peer disagrees about the protocol, which is a
// connection it must not carry user traffic on.
type probeEchoViolation struct{ reason string }

func (e probeEchoViolation) Error() string { return e.reason }

// readPathProbeEchoes consumes the gateway's reflection of the probe sequence.
//
// Every field is checked against what was sent. A peer that returns the right
// number of frames with the wrong identity, ordering or size has not echoed
// the probe; it has sent something else that happens to arrive here, and the
// measurement drawn from it would describe traffic this client never sent.
func (c *Client) readPathProbeEchoes(lane *authenticatedLane, sent int) error {
	for sequence := 0; sequence < sent; sequence++ {
		frame, err := lane.fc.Read()
		if err != nil {
			// The probe is bounded in time as well as in packets. Running out
			// of budget on a slow path leaves the measurement incomplete, which
			// is the cost of bounding it, and says nothing about the peer.
			var timeout net.Error
			if errors.As(err, &timeout) && timeout.Timeout() {
				return nil
			}
			return probeEchoViolation{reason: fmt.Sprintf("gateway ended the probe echo after %d of %d frames: %v", sequence, sent, err)}
		}
		switch {
		case frame.Header.Type != protocol.TypeProbe:
			return probeEchoViolation{reason: fmt.Sprintf("gateway answered probe %d with frame type %d", sequence, frame.Header.Type)}
		case frame.Header.SessionID != lane.sessionID:
			return probeEchoViolation{reason: fmt.Sprintf("gateway echoed probe %d under a different session", sequence)}
		case frame.Header.FlowID != probeFlowID:
			return probeEchoViolation{reason: fmt.Sprintf("gateway echoed probe %d on flow %d", sequence, frame.Header.FlowID)}
		case frame.Header.Sequence != uint64(sequence):
			return probeEchoViolation{reason: fmt.Sprintf("gateway echoed probe sequence %d where %d was due", frame.Header.Sequence, sequence)}
		case frame.Header.Flags != 0 || frame.Header.Class != protocol.ClassNew:
			return probeEchoViolation{reason: fmt.Sprintf("gateway echoed probe %d with flags %#x class %d", sequence, frame.Header.Flags, frame.Header.Class)}
		case len(frame.Payload) != probePayloadBytes:
			return probeEchoViolation{reason: fmt.Sprintf("gateway echoed probe %d with %d payload bytes, %d were sent", sequence, len(frame.Payload), probePayloadBytes)}
		}
	}
	return nil
}

// rejectProbePeer discards the connection a non-conforming gateway answered on.
//
// The prewarm's whole purpose is to leave a measured, pooled connection behind
// for the first user flow. Leaving one behind whose peer just disagreed about
// the protocol would spend that flow on the disagreement instead, and the
// pooled connection would outlive the evidence that it is unsound. Dropping the
// pool costs one handshake and is recovered by the next dial.
func (c *Client) rejectProbePeer(lane *authenticatedLane, err error) {
	c.cfg.Logger.Warn("gateway violated the protocol-1 path probe contract", "error", err)
	if c.metrics != nil {
		c.metrics.PeerProtocolViolation()
	}
	_ = lane.fc.Close()
	c.closeQUICPool()
}

// awaitMeasurement waits for the answer the probe was asking for.
//
// Sending is not measuring. What the controller learns, it learns from the
// acknowledgements, which are a round trip behind the padding that provoked
// them -- so a prewarm that sent and returned would leave exactly the
// ignorance it was opened to remove, and the first flow would still be the one
// discovering the path.
func (c *Client) awaitMeasurement(lane *authenticatedLane, deadline time.Time) {
	keyed, ok := lane.outer.(interface{ pathIdentity() string })
	if !ok {
		return
	}
	model := pathmodel.Shared(keyed.pathIdentity())
	for time.Now().Before(deadline) {
		if model.Current().ObservedSamples >= pathProbePackets {
			return
		}
		time.Sleep(measurementPoll)
	}
}

// measurementPoll is short against a long-haul round trip, so the prewarm ends
// as soon as the answer arrives rather than on a schedule.
const measurementPoll = 20 * time.Millisecond

const (
	// probeFlowID is a flow identity no flow has. Real ones are random and
	// non-zero, and a peer that finds nobody subscribed to this simply drops
	// the frame, which is the whole handling it needs.
	probeFlowID = 0
	// probePayloadBytes fills a packet without exceeding one, so each frame
	// measures one packet's fate.
	probePayloadBytes = 1000
)

// prewarmTimeout bounds the measurement, which is worth having and not worth
// waiting for.
const prewarmTimeout = 20 * time.Second
