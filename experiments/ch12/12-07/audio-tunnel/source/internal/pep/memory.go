package pep

import (
	"fmt"

	"github.com/bojieli/queqiao/internal/memlimit"
)

// MemoryLimits turns the transport's multiplicative per-flow buffering into
// fixed endpoint budgets. A nil *MemoryLimits keeps the throughput-oriented
// server defaults. Mobile clients provide an explicit profile.
type MemoryLimits struct {
	// SendBudgetBytes and ReceiveBudgetBytes are shared by all flows. Send
	// reservations block source reads; receive reservations fail only the flow
	// that cannot retain an out-of-order frame, avoiding a cross-lane deadlock.
	SendBudgetBytes    int64
	ReceiveBudgetBytes int64

	MaxFlowSendBytes       int
	MaxFlowReceiveBytes    uint64
	MaxFlowOutstanding     int
	MaxFlowReceiveFrames   int
	EventQueueFrames       int
	LaneWriteQueueFrames   int
	LaneInteractiveReserve int
	FrameReadBufferBytes   int
	MaxUDPPacketBytes      int
	MaxBulkConnections     int
}

type flowMemoryLimits struct {
	maxSendBytes       int
	maxReceiveBytes    uint64
	maxOutstanding     int
	maxReceiveFrames   int
	eventQueue         int
	laneWriteQueue     int
	laneControlReserve int
	frameReadBuffer    int
	maxUDPPacketBytes  int
	maxBulkConnections int
}

func defaultFlowMemoryLimits() flowMemoryLimits {
	return flowMemoryLimits{
		maxSendBytes: maxFlowOutstandingBytes, maxReceiveBytes: maxReassemblyBytes,
		maxOutstanding: maxFlowOutstandingChunks, maxReceiveFrames: maxReassemblyFrames,
		eventQueue: maxLaneEvents, laneWriteQueue: maxLaneWriteQueue,
		laneControlReserve: maxLaneInteractiveReserve, frameReadBuffer: frameReadBuffer,
		maxUDPPacketBytes:  65535,
		maxBulkConnections: isolatedBulkConns,
	}
}

func resolveMemoryLimits(configured *MemoryLimits, chunkSize int) (flowMemoryLimits, *memlimit.Budget, *memlimit.Budget, error) {
	limits := defaultFlowMemoryLimits()
	if configured == nil {
		return limits, nil, nil, nil
	}
	if configured.MaxFlowSendBytes > 0 {
		limits.maxSendBytes = configured.MaxFlowSendBytes
	}
	if configured.MaxFlowReceiveBytes > 0 {
		limits.maxReceiveBytes = configured.MaxFlowReceiveBytes
	}
	if configured.MaxFlowOutstanding > 0 {
		limits.maxOutstanding = configured.MaxFlowOutstanding
	}
	if configured.MaxFlowReceiveFrames > 0 {
		limits.maxReceiveFrames = configured.MaxFlowReceiveFrames
	}
	if configured.EventQueueFrames > 0 {
		limits.eventQueue = configured.EventQueueFrames
	}
	if configured.LaneWriteQueueFrames > 0 {
		limits.laneWriteQueue = configured.LaneWriteQueueFrames
	}
	if configured.LaneInteractiveReserve > 0 {
		limits.laneControlReserve = configured.LaneInteractiveReserve
	}
	if configured.FrameReadBufferBytes > 0 {
		limits.frameReadBuffer = configured.FrameReadBufferBytes
	}
	if configured.MaxUDPPacketBytes > 0 {
		limits.maxUDPPacketBytes = configured.MaxUDPPacketBytes
	}
	if configured.MaxBulkConnections > 0 {
		limits.maxBulkConnections = configured.MaxBulkConnections
	}

	if chunkSize <= 0 || limits.maxSendBytes < chunkSize {
		return flowMemoryLimits{}, nil, nil, fmt.Errorf("per-flow send memory must hold at least one %d-byte chunk", chunkSize)
	}
	if configured.SendBudgetBytes < int64(chunkSize) {
		return flowMemoryLimits{}, nil, nil, fmt.Errorf("shared send memory must hold at least one %d-byte chunk", chunkSize)
	}
	if configured.ReceiveBudgetBytes <= 0 {
		return flowMemoryLimits{}, nil, nil, fmt.Errorf("shared receive memory must be positive")
	}
	if int64(limits.maxSendBytes) > configured.SendBudgetBytes {
		return flowMemoryLimits{}, nil, nil, fmt.Errorf("per-flow send memory exceeds the shared send budget")
	}
	if limits.maxReceiveBytes > uint64(configured.ReceiveBudgetBytes) {
		return flowMemoryLimits{}, nil, nil, fmt.Errorf("per-flow receive memory exceeds the shared receive budget")
	}
	if limits.maxReceiveBytes == 0 || limits.maxOutstanding < 1 || limits.maxReceiveFrames < 1 {
		return flowMemoryLimits{}, nil, nil, fmt.Errorf("flow memory limits must be positive")
	}
	if limits.eventQueue < 1 || limits.eventQueue > maxLaneEvents {
		return flowMemoryLimits{}, nil, nil, fmt.Errorf("event queue must be between 1 and %d frames", maxLaneEvents)
	}
	if limits.laneWriteQueue < 2 || limits.laneWriteQueue > maxLaneWriteQueue {
		return flowMemoryLimits{}, nil, nil, fmt.Errorf("lane write queue must be between 2 and %d frames", maxLaneWriteQueue)
	}
	if limits.laneControlReserve < 1 || limits.laneControlReserve >= limits.laneWriteQueue {
		return flowMemoryLimits{}, nil, nil, fmt.Errorf("lane control reserve must be smaller than the write queue")
	}
	if limits.frameReadBuffer < 512 || limits.frameReadBuffer > frameReadBuffer {
		return flowMemoryLimits{}, nil, nil, fmt.Errorf("frame read buffer must be between 512 and %d bytes", frameReadBuffer)
	}
	if limits.maxUDPPacketBytes < 1280 || limits.maxUDPPacketBytes > 65535 {
		return flowMemoryLimits{}, nil, nil, fmt.Errorf("UDP packet buffer must be between 1280 and 65535 bytes")
	}
	if limits.maxBulkConnections < 1 || limits.maxBulkConnections > isolatedBulkConns {
		return flowMemoryLimits{}, nil, nil, fmt.Errorf("bulk connection limit must be between 1 and %d", isolatedBulkConns)
	}
	return limits, memlimit.New(configured.SendBudgetBytes), memlimit.New(configured.ReceiveBudgetBytes), nil
}

// MemoryStats exposes exact retained-payload accounting. It deliberately does
// not claim to be whole-process RSS; platform and transport runtimes also own
// bounded buffers outside these budgets.
type MemoryStats struct {
	Send    memlimit.Snapshot `json:"send"`
	Receive memlimit.Snapshot `json:"receive"`
}
