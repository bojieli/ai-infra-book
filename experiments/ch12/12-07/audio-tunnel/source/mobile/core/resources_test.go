package mobilecore

import (
	"encoding/json"
	"fmt"
	"testing"
)

func TestMobileResourceProfilesHaveFixedEndpointBudgets(t *testing.T) {
	for _, limits := range []mobileResourceLimits{iosResourceLimits, androidResourceLimits} {
		t.Run(limits.name, func(t *testing.T) {
			if limits.maxSessions <= 0 || limits.maxPendingOpens <= 0 || limits.maxPendingOpens > limits.maxSessions {
				t.Fatalf("invalid admission limits: %+v", limits)
			}
			if limits.memory.SendBudgetBytes <= 0 || limits.memory.ReceiveBudgetBytes <= 0 {
				t.Fatal("shared payload budgets are disabled")
			}
			if limits.memory.MaxFlowSendBytes > int(limits.memory.SendBudgetBytes) ||
				limits.memory.MaxFlowReceiveBytes > uint64(limits.memory.ReceiveBudgetBytes) {
				t.Fatal("one flow exceeds its endpoint-wide budget")
			}
			if limits.streamWindow != limits.connectionWindow && limits.streamWindow > limits.connectionWindow {
				t.Fatal("stream receive window exceeds connection window")
			}
		})
	}
	if iosResourceLimits.maxSessions < 1024 {
		t.Fatalf("iOS admission capacity = %d, want at least 1024", iosResourceLimits.maxSessions)
	}
}

// The iOS profile is bounded by the whole process, not by the Go heap. Jetsam
// enforces iosProcessMemoryCap with SIGKILL, and everything outside the Go heap
// is charged against the same ceiling, so the runtime limit has to stay far
// enough below it to leave that remainder room. Raising goMemoryLimit without
// redoing this arithmetic is how the extension came to be killed mid-session.
func TestIOSGoMemoryLimitLeavesHeadroomBelowTheProcessCap(t *testing.T) {
	headroom := iosProcessMemoryCap - iosResourceLimits.goMemoryLimit
	if headroom < iosNonHeapHeadroom {
		t.Fatalf(
			"iOS Go memory limit = %d bytes, leaving %d bytes of the %d byte process cap "+
				"for non-heap memory, want at least %d",
			iosResourceLimits.goMemoryLimit, headroom, iosProcessMemoryCap, iosNonHeapHeadroom,
		)
	}
	// The profile name is what a soak operator reads out of the metrics JSON, so
	// it must not keep advertising a limit the profile no longer carries.
	wantName := fmt.Sprintf("ios-fixed-%dm", iosResourceLimits.goMemoryLimit/(1024*1024))
	if iosResourceLimits.name != wantName {
		t.Fatalf("iOS profile name = %q, want %q", iosResourceLimits.name, wantName)
	}
}

func TestMetricsExposeTheSelectedMemoryEnvelope(t *testing.T) {
	session := &Session{state: StateStopped, resources: iosResourceLimits}
	var got struct {
		Version int `json:"version"`
		Memory  struct {
			Profile string `json:"profile"`
			GoLimit int64  `json:"go_limit_bytes"`
		} `json:"memory"`
	}
	if err := json.Unmarshal([]byte(session.MetricsJSON()), &got); err != nil {
		t.Fatal(err)
	}
	if got.Version != 2 || got.Memory.Profile != iosResourceLimits.name || got.Memory.GoLimit != iosResourceLimits.goMemoryLimit {
		t.Fatalf("metrics memory envelope = %+v", got)
	}
}
