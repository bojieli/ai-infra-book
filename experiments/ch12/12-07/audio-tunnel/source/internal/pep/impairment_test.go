package pep

import (
	"runtime"
	"testing"
)

// requireStableImpairmentClock keeps wall-clock pathsim campaigns on hosts
// whose delayed-packet scheduler can reproduce their configured RTT.
//
// Both hosted Windows runners consistently stretched a configured 300 ms RTT
// to 0.9-3.8 seconds once the coded path was active. That changes which QUIC
// timers fire and, on the 42% channel, can consume a two-minute application
// deadline without exercising a deterministic loss sequence. The same Windows
// binaries still run the portable coded-path, conformance, socket-error, and
// native archive smoke tests; the high-erasure wall-clock campaigns run on
// Linux and macOS, including under the race detector.
func requireStableImpairmentClock(t *testing.T) {
	t.Helper()
	if runtime.GOOS == "windows" {
		t.Skip("hosted Windows timers do not preserve pathsim's high-erasure wall-clock model")
	}
}
