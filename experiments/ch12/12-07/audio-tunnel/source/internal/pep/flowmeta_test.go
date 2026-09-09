package pep

import (
	"context"
	"encoding/json"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/classifier"
	"github.com/bojieli/queqiao/internal/flowmeta"
	"github.com/bojieli/queqiao/internal/metrics"
	"github.com/bojieli/queqiao/internal/profile"
	"github.com/bojieli/queqiao/internal/protocol"
	"io"
	"log/slog"
)

// fakeAgent serves the capture agent's contract: a Unix socket answering
// GET /v1/flow?source_port=N with what opened that flow.
//
// It speaks the real wire shape rather than calling into a shared type,
// because the two projects are separate repositories and the thing that can
// break between them is exactly the encoding.
func fakeAgent(t *testing.T, byPort map[uint16]map[string]any) string {
	t.Helper()
	// Not t.TempDir(): it embeds the test's name, and a Unix socket path is
	// capped near 104 bytes on macOS and 108 on Linux. A long test name pushed
	// this over, the listen failed, and the skip made the one test that checks
	// the wire contract between two repositories disappear quietly.
	dir, err := os.MkdirTemp("", "qq")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = os.RemoveAll(dir) })
	sock := filepath.Join(dir, "a.sock")
	ln, err := net.Listen("unix", sock)
	if err != nil {
		t.Fatalf("listen on %s (%d bytes): %v", sock, len(sock), err)
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/v1/flow", func(w http.ResponseWriter, r *http.Request) {
		port := r.URL.Query().Get("source_port")
		var key uint16
		if _, err := fmtSscan(port, &key); err != nil {
			http.Error(w, "bad port", http.StatusBadRequest)
			return
		}
		proc, ok := byPort[key]
		if !ok {
			http.NotFound(w, r)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]any{
			"process": proc,
			"expires": time.Now().Add(time.Minute),
		})
	})
	srv := &http.Server{Handler: mux}
	go func() { _ = srv.Serve(ln) }()
	t.Cleanup(func() {
		_ = srv.Close()
		_ = os.Remove(sock)
	})
	return sock
}

func fmtSscan(s string, out *uint16) (int, error) {
	v, err := strconv.ParseUint(s, 10, 16)
	if err != nil {
		return 0, err
	}
	*out = uint16(v)
	return 1, nil
}

func contains(s, sub string) bool { return strings.Contains(s, sub) }

// A lookup returns what the agent reported, in the shape the agent sends it.
func TestFlowMetaReadsTheAgentsWireShape(t *testing.T) {
	sock := fakeAgent(t, map[uint16]map[string]any{
		4242: {
			"PID": 991, "Path": "/app/voice-gateway", "SigningID": "", "CgroupID": 77,
			"Workload": map[string]any{
				"kind":         "kubernetes",
				"pod_uid":      "1a2b3c4d-5e6f-7081-92a3-b4c5d6e7f809",
				"container_id": "9f8e7d6c5b4a39281706152433425160",
				"cgroup":       "/kubepods.slice/...",
			},
		},
	})
	l := flowmeta.New(sock, time.Second)
	got, err := l.BySourcePort(context.Background(), 4242)
	if err != nil {
		t.Fatal(err)
	}
	if got.Path != "/app/voice-gateway" {
		t.Errorf("path = %q", got.Path)
	}
	if got.Workload.PodUID != "1a2b3c4d-5e6f-7081-92a3-b4c5d6e7f809" {
		t.Errorf("pod uid = %q", got.Workload.PodUID)
	}
	id := got.Identity()
	for _, want := range []string{"path=/app/voice-gateway", "pod=1a2b3c4d", "container=9f8e7d6c"} {
		if !contains(id, want) {
			t.Errorf("identity %q lacks %q", id, want)
		}
	}
}

// A flow the agent does not know is ordinary, not an error: a connection it
// never captured, or one it has already forgotten.
func TestAnUnknownFlowIsNotAnError(t *testing.T) {
	sock := fakeAgent(t, map[uint16]map[string]any{})
	l := flowmeta.New(sock, time.Second)
	got, err := l.BySourcePort(context.Background(), 1234)
	if err != nil {
		t.Fatalf("unknown flow returned an error: %v", err)
	}
	if !got.Empty() {
		t.Errorf("unknown flow returned %+v", got)
	}
}

// No agent at all is the default, and it must cost nothing rather than fail.
func TestNoAgentIsInert(t *testing.T) {
	var l *flowmeta.Lookup = flowmeta.New("", time.Second)
	if l.Enabled() {
		t.Fatal("an empty socket path produced an enabled lookup")
	}
	if _, err := l.BySourcePort(context.Background(), 1); err == nil {
		t.Error("a disabled lookup did not say so")
	}
}

// An agent that has wedged costs a flow its timeout and nothing more. This is
// on the accept path, so the bound is the point.
func TestAWedgedAgentIsBounded(t *testing.T) {
	dir, err := os.MkdirTemp("", "qq")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = os.RemoveAll(dir) })
	sock := filepath.Join(dir, "w.sock")
	ln, err := net.Listen("unix", sock)
	if err != nil {
		t.Fatalf("listen on %s: %v", sock, err)
	}
	defer ln.Close()
	go func() {
		for {
			c, err := ln.Accept()
			if err != nil {
				return
			}
			_ = c // accept and never answer
		}
	}()
	l := flowmeta.New(sock, 80*time.Millisecond)
	start := time.Now()
	if _, err := l.BySourcePort(context.Background(), 1); err == nil {
		t.Error("a wedged agent returned success")
	}
	if elapsed := time.Since(start); elapsed > time.Second {
		t.Errorf("a wedged agent held the accept path for %v", elapsed)
	}
}

// The profile turns an identity into a class, and the first matching hint
// wins so a specific rule can precede a general one.
func TestClassHintsMatchMostSpecificFirst(t *testing.T) {
	p := profile.Profile{ClassHints: []profile.ClassHint{
		{Match: "path=/app/checkpoint-sync", Class: "bulk"},
		{Match: "path=/app/", Class: "interactive"},
	}}
	if got, ok := p.HintedClass("path=/app/voice-gateway pod=abc"); !ok || got != classifier.ClassInteractive {
		t.Errorf("voice gateway hinted %v ok=%v", got, ok)
	}
	if got, ok := p.HintedClass("path=/app/checkpoint-sync pod=abc"); !ok || got != classifier.ClassBulk {
		t.Errorf("checkpoint sync hinted %v ok=%v", got, ok)
	}
	if _, ok := p.HintedClass("path=/usr/bin/curl"); ok {
		t.Error("an unmatched identity produced a hint")
	}
	if _, ok := p.HintedClass(""); ok {
		t.Error("an empty identity produced a hint")
	}
}

// A misspelled class fails at startup. Left to runtime it would be
// indistinguishable from a rule whose workload never appeared.
func TestAMisspelledHintFailsEarly(t *testing.T) {
	bad := profile.Profile{ClassHints: []profile.ClassHint{{Match: "x", Class: "interactve"}}}
	if err := bad.ValidateHints(); err == nil {
		t.Error("a misspelled class was accepted")
	}
	empty := profile.Profile{ClassHints: []profile.ClassHint{{Match: "  ", Class: "bulk"}}}
	if err := empty.ValidateHints(); err == nil {
		t.Error("an empty match was accepted")
	}
	good := profile.Profile{ClassHints: []profile.ClassHint{{Match: "x", Class: "bulk"}}}
	if err := good.ValidateHints(); err != nil {
		t.Errorf("a valid hint was rejected: %v", err)
	}
}

// A declared class is counted like any other transition. Without that the
// whole mechanism is invisible in telemetry: an operator reading
// class_transitions sees zero and concludes the hints never fired, which is
// indistinguishable from them not being configured at all.
func TestADeclaredClassIsCounted(t *testing.T) {
	reg := metrics.New()
	c := &Client{cfg: ClientConfig{
		Logger: slog.New(slog.NewTextHandler(io.Discard, nil)),
		Profile: profile.Profile{ClassHints: []profile.ClassHint{
			{Match: "path=/app/voice", Class: "interactive"},
		}},
		FlowMetadataSocket: fakeAgent(t, map[uint16]map[string]any{
			5555: {"PID": 1, "Path": "/app/voice", "Workload": map[string]any{"kind": "unknown"}},
		}),
	}, metrics: reg}
	c.flowMeta = flowmeta.New(c.cfg.FlowMetadataSocket, time.Second)

	inner, peer := net.Pipe()
	defer inner.Close()
	defer peer.Close()
	flow := newMultipathFlow(context.Background(), inner, [16]byte{1}, 1, 64*1024,
		protocol.FlagAckUp, protocol.FlagAckDown, nil, reg, nil)

	c.declareClass(context.Background(), &portConn{Conn: inner, port: 5555}, flow)

	if got := classifier.Class(flow.class.Load()); got != classifier.ClassInteractive {
		t.Errorf("flow class = %v, want interactive", got)
	}
	if n := reg.Snapshot().ClassTransitions[1]; n != 1 {
		t.Errorf("interactive transitions = %d, want 1", n)
	}
}

// An unmatched identity leaves the flow and the counters alone.
func TestAnUnmatchedIdentityCountsNothing(t *testing.T) {
	reg := metrics.New()
	c := &Client{cfg: ClientConfig{
		Logger: slog.New(slog.NewTextHandler(io.Discard, nil)),
		Profile: profile.Profile{ClassHints: []profile.ClassHint{
			{Match: "path=/app/voice", Class: "interactive"},
		}},
		FlowMetadataSocket: fakeAgent(t, map[uint16]map[string]any{
			5555: {"PID": 1, "Path": "/usr/bin/curl", "Workload": map[string]any{"kind": "unknown"}},
		}),
	}, metrics: reg}
	c.flowMeta = flowmeta.New(c.cfg.FlowMetadataSocket, time.Second)

	inner, peer := net.Pipe()
	defer inner.Close()
	defer peer.Close()
	flow := newMultipathFlow(context.Background(), inner, [16]byte{1}, 1, 64*1024,
		protocol.FlagAckUp, protocol.FlagAckDown, nil, reg, nil)

	c.declareClass(context.Background(), &portConn{Conn: inner, port: 5555}, flow)

	if got := classifier.Class(flow.class.Load()); got != classifier.ClassNew {
		t.Errorf("an unmatched flow was classified %v", got)
	}
	for i, n := range reg.Snapshot().ClassTransitions {
		if n != 0 {
			t.Errorf("class %d counted %d transitions for an unmatched identity", i, n)
		}
	}
}

// portConn reports a chosen source port, which is what the lookup is keyed by.
type portConn struct {
	net.Conn
	port int
}

func (p *portConn) RemoteAddr() net.Addr {
	return &net.TCPAddr{IP: net.IPv4(127, 0, 0, 1), Port: p.port}
}
