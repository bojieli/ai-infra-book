// Package flowmeta asks the local capture agent what produced a flow.
//
// A proxy protocol carries a destination and nothing else. The agent that
// captured the connection knows more: the calling process, and on a host
// running containers the pod or container it belongs to. That information
// exists before the first byte moves, which is the one thing inference cannot
// offer.
//
// The classifier this feeds needs about a second of traffic to decide what a
// flow is. A request that completes in 200ms is finished before then, so its
// whole life is spent in whatever class the flow started in. Declaring the
// class removes that window rather than shortening it.
//
// Everything here is optional and advisory. A deployment with no agent gets an
// empty lookup and the behaviour it had before this existed; an agent that has
// forgotten a flow, or a process that exited between capture and lookup, gives
// the same. Nothing fails because attribution is absent.
package flowmeta

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"net/http"
	"strconv"
	"strings"
	"time"
)

// Workload is what the agent resolved a process's cgroup to. Fields it could
// not determine are empty rather than guessed: a pod's namespace and name live
// in the API server, so only the UID travels.
type Workload struct {
	Kind        string `json:"kind"`
	PodUID      string `json:"pod_uid,omitempty"`
	ContainerID string `json:"container_id,omitempty"`
	Unit        string `json:"unit,omitempty"`
	Cgroup      string `json:"cgroup,omitempty"`
}

// Process is the agent's account of what opened a flow.
type Process struct {
	PID       int32    `json:"PID"`
	Path      string   `json:"Path"`
	SigningID string   `json:"SigningID"`
	CgroupID  uint64   `json:"CgroupID"`
	Workload  Workload `json:"Workload"`
}

type entry struct {
	Process Process   `json:"process"`
	Expires time.Time `json:"expires"`
}

// Identity renders what is known as one line, which is what a class hint is
// matched against and what a log line carries.
//
// The executable path comes first because it is the part an operator writing a
// rule actually recognises. A pod UID is a fact about a flow and not a name
// anybody chose.
func (p Process) Identity() string {
	parts := make([]string, 0, 3)
	if p.Path != "" {
		parts = append(parts, "path="+p.Path)
	}
	switch {
	case p.Workload.PodUID != "" && p.Workload.ContainerID != "":
		parts = append(parts, "pod="+p.Workload.PodUID, "container="+p.Workload.ContainerID)
	case p.Workload.PodUID != "":
		parts = append(parts, "pod="+p.Workload.PodUID)
	case p.Workload.ContainerID != "":
		parts = append(parts, "container="+p.Workload.ContainerID)
	case p.Workload.Unit != "":
		parts = append(parts, "unit="+p.Workload.Unit)
	}
	if len(parts) == 0 {
		return ""
	}
	return strings.Join(parts, " ")
}

// Empty reports whether the agent knew nothing about this flow.
func (p Process) Empty() bool { return p.Identity() == "" }

// Lookup asks a capture agent over its local Unix socket.
type Lookup struct {
	client  *http.Client
	timeout time.Duration
}

// ErrDisabled is returned by a nil Lookup, so a caller that never configured
// one does not have to guard every call site.
var ErrDisabled = errors.New("flowmeta: no capture agent configured")

// New builds a lookup against the agent's socket.
//
// The timeout is deliberately short. This runs on the path of accepting a
// connection, so an agent that has wedged must cost a flow a millisecond of
// delay rather than the whole handshake: attribution is worth having and not
// worth waiting for.
func New(socketPath string, timeout time.Duration) *Lookup {
	if socketPath == "" {
		return nil
	}
	if timeout <= 0 {
		timeout = 50 * time.Millisecond
	}
	return &Lookup{
		timeout: timeout,
		client: &http.Client{
			Timeout: timeout,
			Transport: &http.Transport{
				DialContext: func(ctx context.Context, _, _ string) (net.Conn, error) {
					var d net.Dialer
					return d.DialContext(ctx, "unix", socketPath)
				},
				DisableKeepAlives: false,
				MaxIdleConns:      4,
			},
		},
	}
}

// Enabled reports whether this lookup will do anything.
func (l *Lookup) Enabled() bool { return l != nil }

// BySourcePort asks what opened the connection arriving from this loopback
// port.
//
// The source port is the key because it is what both sides can agree on
// without either trusting the other's account: the agent recorded it when it
// captured the connect, and the listener sees it on accept.
func (l *Lookup) BySourcePort(ctx context.Context, port uint16) (Process, error) {
	if l == nil {
		return Process{}, ErrDisabled
	}
	ctx, cancel := context.WithTimeout(ctx, l.timeout)
	defer cancel()
	req, err := http.NewRequestWithContext(ctx, http.MethodGet,
		"http://tunless/v1/flow?source_port="+strconv.Itoa(int(port)), nil)
	if err != nil {
		return Process{}, err
	}
	resp, err := l.client.Do(req)
	if err != nil {
		return Process{}, err
	}
	defer resp.Body.Close()
	if resp.StatusCode == http.StatusNotFound {
		// The agent does not know this flow. That is ordinary: a connection
		// the agent did not capture, or one it has already forgotten.
		return Process{}, nil
	}
	if resp.StatusCode != http.StatusOK {
		return Process{}, fmt.Errorf("flowmeta: agent returned %s", resp.Status)
	}
	var e entry
	if err := json.NewDecoder(resp.Body).Decode(&e); err != nil {
		return Process{}, fmt.Errorf("flowmeta: decode: %w", err)
	}
	return e.Process, nil
}

// SourcePortOf pulls the port out of an accepted connection's remote address.
func SourcePortOf(addr net.Addr) (uint16, bool) {
	switch a := addr.(type) {
	case *net.TCPAddr:
		if a.Port > 0 && a.Port <= 65535 {
			return uint16(a.Port), true
		}
	}
	_, portStr, err := net.SplitHostPort(addr.String())
	if err != nil {
		return 0, false
	}
	p, err := strconv.ParseUint(portStr, 10, 16)
	if err != nil || p == 0 {
		return 0, false
	}
	return uint16(p), true
}
