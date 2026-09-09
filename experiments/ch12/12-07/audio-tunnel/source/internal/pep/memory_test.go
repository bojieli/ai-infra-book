package pep

import "testing"

func TestExplicitMemoryLimitsCreateSharedBudgets(t *testing.T) {
	configured := &MemoryLimits{
		SendBudgetBytes: 256 * 1024, ReceiveBudgetBytes: 512 * 1024,
		MaxFlowSendBytes: 128 * 1024, MaxFlowReceiveBytes: 256 * 1024,
		MaxFlowOutstanding: 8, MaxFlowReceiveFrames: 16,
		EventQueueFrames: 2, LaneWriteQueueFrames: 4, LaneInteractiveReserve: 1,
		FrameReadBufferBytes: 4096, MaxUDPPacketBytes: 2048, MaxBulkConnections: 1,
	}
	limits, send, receive, err := resolveMemoryLimits(configured, 16*1024)
	if err != nil {
		t.Fatal(err)
	}
	if limits.maxSendBytes != 128*1024 || limits.eventQueue != 2 || limits.maxBulkConnections != 1 {
		t.Fatalf("resolved limits = %+v", limits)
	}
	if got := send.Snapshot().Capacity; got != configured.SendBudgetBytes {
		t.Fatalf("send capacity = %d", got)
	}
	if got := receive.Snapshot().Capacity; got != configured.ReceiveBudgetBytes {
		t.Fatalf("receive capacity = %d", got)
	}
}

func TestMemoryLimitsRejectDeadlockingOrMultiplicativeSettings(t *testing.T) {
	valid := MemoryLimits{
		SendBudgetBytes: 64 * 1024, ReceiveBudgetBytes: 64 * 1024,
		MaxFlowSendBytes: 64 * 1024, MaxFlowReceiveBytes: 64 * 1024,
		MaxFlowOutstanding: 4, MaxFlowReceiveFrames: 4,
		EventQueueFrames: 1, LaneWriteQueueFrames: 2, LaneInteractiveReserve: 1,
		FrameReadBufferBytes: 4096, MaxUDPPacketBytes: 2048, MaxBulkConnections: 1,
	}
	for name, mutate := range map[string]func(*MemoryLimits){
		"send budget below chunk": func(l *MemoryLimits) { l.SendBudgetBytes = 1024 },
		"no receive budget":       func(l *MemoryLimits) { l.ReceiveBudgetBytes = 0 },
		"control consumes queue":  func(l *MemoryLimits) { l.LaneInteractiveReserve = 2 },
		"oversized event queue":   func(l *MemoryLimits) { l.EventQueueFrames = maxLaneEvents + 1 },
		"oversized bulk pool":     func(l *MemoryLimits) { l.MaxBulkConnections = isolatedBulkConns + 1 },
	} {
		t.Run(name, func(t *testing.T) {
			limits := valid
			mutate(&limits)
			if _, _, _, err := resolveMemoryLimits(&limits, 16*1024); err == nil {
				t.Fatal("invalid limits were accepted")
			}
		})
	}
}

func TestQUICWindowsCanBeHardCappedForMobile(t *testing.T) {
	windows := flowWindows{
		stream: 512 * 1024, connection: 2 * 1024 * 1024,
		maxStream: 512 * 1024, maxConnection: 2 * 1024 * 1024, maxStreams: 32,
		codedQueue: 2,
	}
	if err := windows.validate(); err != nil {
		t.Fatal(err)
	}
	config := quicConfig(windows)
	if config.InitialStreamReceiveWindow != config.MaxStreamReceiveWindow ||
		config.InitialConnectionReceiveWindow != config.MaxConnectionReceiveWindow ||
		config.MaxIncomingStreams != 32 || windows.codedQueue != 2 {
		t.Fatalf("QUIC config is not fixed: %+v", config)
	}
	windows.maxStream = 256 * 1024
	if err := windows.validate(); err == nil {
		t.Fatal("maximum below initial window was accepted")
	}
}
