package mobilecore

import (
	"runtime/debug"

	"github.com/bojieli/queqiao/internal/pep"
)

// mobileResourceLimits is the fixed hardware-style capacity plan for one
// tunnel process. The dominant retransmit and reassembly arenas are shared
// between every flow. The remaining per-flow buffers are deliberately tiny
// and their aggregate is bounded by maxSessions, so every term in the memory
// envelope has a fixed endpoint-wide ceiling.
type mobileResourceLimits struct {
	name               string
	goMemoryLimit      int64
	maxSessions        int
	maxPendingOpens    int
	chunkSize          int
	streamWindow       uint64
	connectionWindow   uint64
	maxIncomingStreams int64
	memory             pep.MemoryLimits
}

// iosProcessMemoryCap is the whole-process ceiling iOS enforces on a
// NEPacketTunnelProvider. Crossing it is not a soft failure: jetsam SIGKILLs
// the extension with reason "per-process-limit", so the provider never runs
// stopTunnel, never records a diagnostic, and leaves its network settings
// installed — the VPN keeps showing connected while no packets move.
const iosProcessMemoryCap = 50 * 1024 * 1024

// iosNonHeapHeadroom is what the Go limit must leave unclaimed inside that
// ceiling. SetMemoryLimit governs Go-owned memory only, while the resident text
// pages of the statically linked Go and gVisor code, runtime metadata,
// goroutine and thread stacks, the Swift packet bridge, and CoreFoundation are
// all charged to the same process.
const iosNonHeapHeadroom = 20 * 1024 * 1024

var iosResourceLimits = mobileResourceLimits{
	// Sized against iosProcessMemoryCap, not against the heap alone. At 40 MiB
	// the runtime collected continuously against a limit the process could not
	// honour — whole minutes at 130-200% CPU — and was killed anyway 12 to 21
	// minutes into a session.
	name: "ios-fixed-28m", goMemoryLimit: 28 * 1024 * 1024,
	// Session admission is intentionally independent from the payload arenas
	// below.  A session mostly owns a small state machine; retained bytes are
	// charged to the shared budgets, so raising this ceiling does not multiply
	// the amount of data the process may keep in memory.
	maxSessions: 1024, maxPendingOpens: 128, chunkSize: 16 * 1024,
	streamWindow: 64 * 1024, connectionWindow: 2 * 1024 * 1024, maxIncomingStreams: 32,
	memory: pep.MemoryLimits{
		SendBudgetBytes: 3 * 1024 * 1024, ReceiveBudgetBytes: 3 * 1024 * 1024,
		MaxFlowSendBytes: 1024 * 1024, MaxFlowReceiveBytes: 1024 * 1024,
		MaxFlowOutstanding: 64, MaxFlowReceiveFrames: 128,
		EventQueueFrames: 2, LaneWriteQueueFrames: 4, LaneInteractiveReserve: 1,
		FrameReadBufferBytes: 8 * 1024, MaxUDPPacketBytes: 4 * 1024, MaxBulkConnections: 1,
	},
}

var androidResourceLimits = mobileResourceLimits{
	name: "android-fixed-72m", goMemoryLimit: 72 * 1024 * 1024,
	maxSessions: 128, maxPendingOpens: 32, chunkSize: 16 * 1024,
	streamWindow: 1024 * 1024, connectionWindow: 4 * 1024 * 1024, maxIncomingStreams: 64,
	memory: pep.MemoryLimits{
		SendBudgetBytes: 8 * 1024 * 1024, ReceiveBudgetBytes: 8 * 1024 * 1024,
		MaxFlowSendBytes: 2 * 1024 * 1024, MaxFlowReceiveBytes: 2 * 1024 * 1024,
		MaxFlowOutstanding: 128, MaxFlowReceiveFrames: 256,
		EventQueueFrames: 4, LaneWriteQueueFrames: 4, LaneInteractiveReserve: 1,
		FrameReadBufferBytes: 8 * 1024, MaxUDPPacketBytes: 4 * 1024, MaxBulkConnections: 2,
	},
}

func applyRuntimeLimits(limits mobileResourceLimits) {
	// SetMemoryLimit is a safety backstop around all Go-owned memory, including
	// gVisor and quic-go. Exact payload admission is enforced by the budgets;
	// this soft runtime limit catches allocations outside those audited paths.
	debug.SetMemoryLimit(limits.goMemoryLimit)
	debug.SetGCPercent(50)
}
