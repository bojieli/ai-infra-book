package congestion

import (
	"testing"
	"time"
)

// The sample shape has to survive the trip out of the controller.
//
// updateSampleShape stores four figures in atomics and snapshot builds the
// struct the rest of the process reads. A field written on one side and not
// read on the other produces a metric that is always zero, which is worse than
// a missing one: queqiao_quic_sample_max_bytes_per_second reads as "the widest
// sample was nothing" rather than as "nobody published this".
//
// This is asserted against the telemetry state directly rather than through a
// sender, because the defect is in the copy and a test that drives a sender
// would only find it if the sender happened to take a sample first.
func TestTheSampleShapeSurvivesTheSnapshot(t *testing.T) {
	var state telemetryState
	state.updateSampleShape(1_100, 9_400, 13_000, 37*time.Millisecond)

	got := state.snapshot()

	if got.SampleMean != 1_100 {
		t.Errorf("SampleMean = %d, want 1100", got.SampleMean)
	}
	if got.SampleMax != 9_400 {
		t.Errorf("SampleMax = %d, want 9400", got.SampleMax)
	}
	if got.SampleMaxDelivered != 13_000 {
		t.Errorf("SampleMaxDelivered = %d, want 13000", got.SampleMaxDelivered)
	}
	if got.SampleMaxInterval != 37*time.Millisecond {
		t.Errorf("SampleMaxInterval = %v, want 37ms", got.SampleMaxInterval)
	}
}
