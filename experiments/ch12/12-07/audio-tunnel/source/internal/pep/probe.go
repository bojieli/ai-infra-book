package pep

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/bojieli/queqiao/internal/protocol"
	"github.com/bojieli/queqiao/internal/session"
)

// ProbeResult describes one authenticated provider connection attempt.
// Latency includes name resolution, transport establishment, mutual TLS,
// certificate authorization, and Queqiao ALPN negotiation.
type ProbeResult struct {
	Transport TransportKind
	Latency   time.Duration
}

// Probe verifies that the configured provider accepts this device identity.
// It deliberately opens no destination. After mutual TLS it sends a bounded,
// intentionally invalid lane-join control frame and requires the protocol
// reset defined for that request. That round trip matters with TLS 1.3: a
// client can briefly consider its handshake complete before it observes the
// server rejecting a revoked certificate.
func (c *Client) Probe(ctx context.Context) (ProbeResult, error) {
	if ctx == nil {
		return ProbeResult{}, errors.New("probe context is required")
	}
	started := time.Now()
	lane, err := c.chooseAuthenticatedLane(ctx)
	if err != nil {
		return ProbeResult{}, fmt.Errorf("authenticate provider connection: %w", err)
	}
	defer closeAuthenticatedLane(lane)
	deadline := time.Now().Add(c.cfg.HandshakeTimeout)
	if contextDeadline, ok := ctx.Deadline(); ok && contextDeadline.Before(deadline) {
		deadline = contextDeadline
	}
	_ = lane.outer.SetDeadline(deadline)
	if err := lane.fc.Write(protocol.Frame{
		Header: protocol.Header{
			Version: protocol.Version, Type: protocol.TypeJoin,
			SessionID: lane.sessionID, FlowID: 0, Class: protocol.ClassBulk,
		},
		Payload: encodeLaneID(1),
	}); err != nil {
		return ProbeResult{}, fmt.Errorf("send provider control probe: %w", err)
	}
	response, err := lane.fc.Read()
	if err != nil {
		return ProbeResult{}, fmt.Errorf("read provider control probe: %w", err)
	}
	if response.Header.SessionID != lane.sessionID || response.Header.FlowID != 0 ||
		response.Header.Type != protocol.TypeReset || resetCode(response.Payload) != session.ResetProtocol {
		return ProbeResult{}, errors.New("provider returned an invalid control-probe response")
	}
	return ProbeResult{Transport: lane.kind, Latency: time.Since(started)}, nil
}
