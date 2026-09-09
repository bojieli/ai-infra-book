package pep

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"log/slog"
	"net"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/metrics"
	"github.com/bojieli/queqiao/internal/protocol"
	"github.com/bojieli/queqiao/internal/session"
)

// A gateway refusing session resumes looked healthy at the default log level,
// because the refusal was a Debug record: the only place the failure was
// diagnosable was the peer, which is where it is least useful. Every refusal
// reason must now reach an operator reading at info, and must be counted
// separately, because the three mean different things.
func TestLaneJoinRefusalsAreVisibleAndCountedByReason(t *testing.T) {
	owner := identity.Principal{ProviderID: "provider", AccountID: "account", DeviceID: "owner"}
	other := owner
	other.DeviceID = "other"

	for _, test := range []struct {
		name   string
		known  bool
		joiner identity.Principal
		laneID uint64
		flowID uint64
		reason metrics.LaneJoinRefusal
		level  string
	}{
		{name: "invalid identity", known: true, joiner: owner, laneID: 0, flowID: 1, reason: metrics.LaneJoinInvalidIdentity, level: "INFO"},
		{name: "unknown session", known: false, joiner: owner, laneID: 1, flowID: 1, reason: metrics.LaneJoinUnknownSession, level: "INFO"},
		{name: "flow mismatch", known: true, joiner: owner, laneID: 1, flowID: 9, reason: metrics.LaneJoinFlowMismatch, level: "WARN"},
		{name: "principal mismatch", known: true, joiner: other, laneID: 1, flowID: 1, reason: metrics.LaneJoinPrincipalMismatch, level: "WARN"},
	} {
		t.Run(test.name, func(t *testing.T) {
			flow := newIsolationTestFlow(t, false)
			var records bytes.Buffer
			registry := metrics.New()
			server := &Server{
				cfg:      ServerConfig{Logger: slog.New(slog.NewJSONHandler(&records, &slog.HandlerOptions{Level: slog.LevelInfo}))},
				sessions: map[[16]byte]*serverFlow{},
				metrics:  registry,
			}
			if test.known {
				server.sessions[flow.sessionID] = newServerFlow(flow, owner, TransportTCP, 1)
			}
			local, remote := net.Pipe()
			t.Cleanup(func() { _ = local.Close(); _ = remote.Close() })
			request := protocol.Frame{Header: protocol.Header{
				Version: protocol.Version, Type: protocol.TypeJoin, SessionID: flow.sessionID,
				FlowID: test.flowID, Class: protocol.ClassBulk,
			}}
			go server.handleLaneJoinOpen(context.Background(), local, newFrameConn(local), test.joiner, flow.sessionID, test.laneID, request)

			response, err := newFrameConn(remote).Read()
			if err != nil {
				t.Fatal(err)
			}
			if response.Header.Type != protocol.TypeReset {
				t.Fatalf("response = %d, want RESET", response.Header.Type)
			}
			if got := registry.Snapshot().LaneJoinRefusals[test.reason]; got != 1 {
				t.Fatalf("%s counter = %d, want 1", test.reason, got)
			}
			var record map[string]any
			if err := json.Unmarshal(bytes.TrimSpace(records.Bytes()), &record); err != nil {
				t.Fatalf("no record at info level: %v (%q)", err, records.String())
			}
			if record["msg"] != "lane join refused" || record["reason"] != test.reason.String() || record["level"] != test.level {
				t.Fatalf("record = %#v", record)
			}
			// One record has to be readable on its own.
			if record["total"] != float64(1) {
				t.Fatalf("record total = %#v, want 1", record["total"])
			}
		})
	}
}

// A JOIN admitted whose OPEN_OK cannot be written must not leave the staged
// lane behind: it counts against the flow's admission ceiling yet can never
// carry traffic, so one failed handshake would wedge the slot for the life
// of the flow.
func TestJoinLaneIsRemovedWhenOpenOKCannotBeWritten(t *testing.T) {
	owner := identity.Principal{ProviderID: "provider", AccountID: "account", DeviceID: "owner"}
	flow := newIsolationTestFlow(t, false)
	server := &Server{
		cfg:      ServerConfig{Logger: slog.New(slog.NewTextHandler(io.Discard, nil))},
		sessions: map[[16]byte]*serverFlow{flow.sessionID: newServerFlow(flow, owner, TransportTCP, 1)},
		metrics:  metrics.New(),
	}
	local, remote := net.Pipe()
	_ = remote.Close()
	t.Cleanup(func() { _ = local.Close() })
	request := protocol.Frame{Header: protocol.Header{
		Version: protocol.Version, Type: protocol.TypeJoin, SessionID: flow.sessionID,
		FlowID: flow.flowID, Class: protocol.ClassBulk,
	}}
	server.handleLaneJoinOpen(context.Background(), local, newFrameConn(local), owner, flow.sessionID, 1, request)
	if got := flow.laneCount(); got != 0 {
		t.Fatalf("lane whose OPEN_OK could not be written still consumes %d admission slots", got)
	}
}

// deadlineArmedConn is a peer that stopped reading: a write blocks until a
// write deadline is armed, which is what unblocks it with a timeout. Without
// the deadline the write would block for the life of the connection.
type deadlineArmedConn struct {
	net.Conn
	armed chan struct{}
	once  sync.Once
}

func (c *deadlineArmedConn) Write(p []byte) (int, error) {
	<-c.armed
	return 0, os.ErrDeadlineExceeded
}

func (c *deadlineArmedConn) SetWriteDeadline(deadline time.Time) error {
	if !deadline.IsZero() {
		c.once.Do(func() { close(c.armed) })
	}
	return c.Conn.SetWriteDeadline(deadline)
}

// The handshake deadline is already cleared when the OPEN_OK goes out, so the
// write carries its own bound: a peer that stops reading must not wedge the
// staged lane against the admission ceiling for longer than the admission
// timeout.
func TestBlockedOpenOKWriteFreesTheAdmissionSlot(t *testing.T) {
	owner := identity.Principal{ProviderID: "provider", AccountID: "account", DeviceID: "owner"}
	flow := newIsolationTestFlow(t, false)
	server := &Server{
		cfg:      ServerConfig{Logger: slog.New(slog.NewTextHandler(io.Discard, nil))},
		sessions: map[[16]byte]*serverFlow{flow.sessionID: newServerFlow(flow, owner, TransportTCP, 1)},
		metrics:  metrics.New(),
	}
	local, remote := net.Pipe()
	t.Cleanup(func() { _ = local.Close(); _ = remote.Close() })
	conn := &deadlineArmedConn{Conn: local, armed: make(chan struct{})}
	request := protocol.Frame{Header: protocol.Header{
		Version: protocol.Version, Type: protocol.TypeJoin, SessionID: flow.sessionID,
		FlowID: flow.flowID, Class: protocol.ClassBulk,
	}}
	server.handleLaneJoinOpen(context.Background(), conn, newFrameConn(conn), owner, flow.sessionID, 1, request)
	if got := flow.laneCount(); got != 0 {
		t.Fatalf("lane whose OPEN_OK timed out still consumes %d admission slots", got)
	}
}

// Refusals the peer cannot retry its way out of must not wear the transient
// capacity code: the client retries ResetFlowLimit forever by design, so a
// closed flow or a duplicate lane id answered with it would be retried for
// the flow's life. Only the genuine ceiling keeps the capacity answer.
func TestLaneJoinRefusalCodesMatchPermanence(t *testing.T) {
	owner := identity.Principal{ProviderID: "provider", AccountID: "account", DeviceID: "owner"}
	for _, test := range []struct {
		name    string
		prepare func(t *testing.T, flow *multipathFlow, session *serverFlow)
		laneID  uint64
		code    session.ResetCode
	}{
		{
			name: "duplicate lane id is a permanent protocol answer",
			prepare: func(t *testing.T, flow *multipathFlow, session *serverFlow) {
				// Headroom, so admission reaches the flow's duplicate check
				// rather than stopping at the ceiling first.
				session.maxLanes = 4
				if err := session.addLane(isolationLaneKind(t, 1, TransportTCP)); err != nil {
					t.Fatal(err)
				}
			},
			laneID: 1,
			code:   session.ResetProtocol,
		},
		{
			name: "closed flow is a permanent protocol answer",
			prepare: func(t *testing.T, flow *multipathFlow, session *serverFlow) {
				flow.closeAll()
			},
			laneID: 2,
			code:   session.ResetProtocol,
		},
		{
			name: "admission ceiling stays the transient capacity answer",
			prepare: func(t *testing.T, flow *multipathFlow, session *serverFlow) {
				// One young lane fills the budget of one, and eviction cannot
				// take it inside the rescue-race window.
				session.maxLanes = 1
				if err := session.addLane(isolationLaneKind(t, 1, TransportTCP)); err != nil {
					t.Fatal(err)
				}
			},
			laneID: 2,
			code:   session.ResetFlowLimit,
		},
	} {
		t.Run(test.name, func(t *testing.T) {
			flow := newIsolationTestFlow(t, false)
			serverSession := newServerFlow(flow, owner, TransportTCP, 1)
			server := &Server{
				cfg:      ServerConfig{Logger: slog.New(slog.NewTextHandler(io.Discard, nil))},
				sessions: map[[16]byte]*serverFlow{flow.sessionID: serverSession},
				metrics:  metrics.New(),
			}
			test.prepare(t, flow, serverSession)
			local, remote := net.Pipe()
			t.Cleanup(func() { _ = local.Close(); _ = remote.Close() })
			request := protocol.Frame{Header: protocol.Header{
				Version: protocol.Version, Type: protocol.TypeJoin, SessionID: flow.sessionID,
				FlowID: flow.flowID, Class: protocol.ClassBulk,
			}}
			go server.handleLaneJoinOpen(context.Background(), local, newFrameConn(local), owner, flow.sessionID, test.laneID, request)
			response, err := newFrameConn(remote).Read()
			if err != nil {
				t.Fatal(err)
			}
			if response.Header.Type != protocol.TypeReset {
				t.Fatalf("response = %d, want RESET", response.Header.Type)
			}
			if len(response.Payload) == 0 || session.ResetCode(response.Payload[0]) != test.code {
				t.Fatalf("refusal payload = %v, want reset code %d", response.Payload, test.code)
			}
		})
	}
}
