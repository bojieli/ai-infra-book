package extproxy

import (
	"bytes"
	"context"
	"os"
	"os/exec"
	"sync"
	"time"
)

// process wraps one launched implementation. Its output is captured rather
// than discarded: when a third-party binary rejects a configuration, that text
// is the only explanation available.
type process struct {
	cmd  *exec.Cmd
	logs *lockedBuffer
	done chan struct{}
	once sync.Once
}

type lockedBuffer struct {
	mu  sync.Mutex
	buf bytes.Buffer
}

func (b *lockedBuffer) Write(p []byte) (int, error) {
	b.mu.Lock()
	defer b.mu.Unlock()
	return b.buf.Write(p)
}

func (b *lockedBuffer) String() string {
	b.mu.Lock()
	defer b.mu.Unlock()
	return b.buf.String()
}

func startProcess(ctx context.Context, binary string, env []string, args ...string) (*process, error) {
	cmd := exec.Command(binary, args...)
	if len(env) > 0 {
		// Added to the inherited environment rather than replacing it: an
		// implementation still needs PATH, HOME and the rest to run at all.
		cmd.Env = append(os.Environ(), env...)
	}
	logs := &lockedBuffer{}
	cmd.Stdout = logs
	cmd.Stderr = logs
	// A new process group lets the whole implementation be signalled, since
	// some of them spawn helpers. How that is asked for is the one thing
	// about this harness that differs by operating system.
	setProcessGroup(cmd)
	if err := cmd.Start(); err != nil {
		return nil, err
	}
	p := &process{cmd: cmd, logs: logs, done: make(chan struct{})}
	go func() {
		_ = cmd.Wait()
		close(p.done)
	}()
	go func() {
		select {
		case <-ctx.Done():
			p.stop()
		case <-p.done:
		}
	}()
	return p, nil
}

func (p *process) output() string {
	if p == nil {
		return ""
	}
	return p.logs.String()
}

// stop terminates the process group, escalating if it does not exit. A
// measurement harness that leaks proxy processes will silently contaminate
// every later trial by holding their ports.
func (p *process) stop() {
	if p == nil {
		return
	}
	p.once.Do(func() {
		if p.cmd.Process == nil {
			return
		}
		terminateProcessGroup(p.cmd, false)
		select {
		case <-p.done:
			return
		case <-time.After(3 * time.Second):
		}
		terminateProcessGroup(p.cmd, true)
		select {
		case <-p.done:
		case <-time.After(2 * time.Second):
		}
	})
}
