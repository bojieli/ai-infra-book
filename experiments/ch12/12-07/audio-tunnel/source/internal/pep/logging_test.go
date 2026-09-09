package pep

import (
	"testing"

	"github.com/bojieli/queqiao/internal/coded"
	"github.com/bojieli/queqiao/internal/fec"
	"github.com/bojieli/queqiao/internal/lossmodel"
)

func TestCodedSubstrateLogFieldsExposePlanAndEstimator(t *testing.T) {
	stats := coded.Stats{
		Snapshot: lossmodel.Snapshot{Samples: 800, Loss: .31, Floor: .27, BurstFactor: 1.4, Memoryless: false, Reordered: 4, Decided: 900},
		Plan:     fec.Plan{Code: true, K: 80, N: 120, Rate: 2.0 / 3, Residual: .001, LossCoded: .27, EffectiveBurst: 1.4, Why: "sized for the loss floor"},
		Window:   80, Sent: 1200, Repairs: 400, Recovered: 210, Lost: 7, Oversize: 2,
		Arrived: 1000, Sources: 783,
	}
	values := map[string]any{}
	fields := codedSubstrateLogFields(stats, true)
	for index := 0; index < len(fields); index += 2 {
		values[fields[index].(string)] = fields[index+1]
	}
	for key, want := range map[string]any{
		"fec_available": true, "fec_sent_total": uint64(1200), "fec_repairs_total": uint64(400),
		"fec_recovered_total": uint64(210), "fec_residual_lost_total": uint64(7),
		"fec_plan_k": 80, "fec_plan_n": 120, "fec_code_rate": 2.0 / 3,
		"fec_observed_loss": .31, "fec_erasure_floor": .27, "fec_burst_factor": 1.4,
		"fec_reason": "sized for the loss floor", "fec_decided_total": uint64(900),
		"fec_arrived_total": uint64(1000), "fec_source_symbols_total": uint64(1000),
		// The receive direction's own rates, which is what "lost" needed to be
		// readable at all: 217 of 1000 source symbols did not arrive, and 7 of
		// them were still missing when the window moved on.
		"fec_receive_erasure": 0.217, "fec_receive_residual_loss": 0.007,
	} {
		if values[key] != want {
			t.Fatalf("%s = %#v, want %#v", key, values[key], want)
		}
	}
}

func TestUnavailableCodedSubstrateHasNoInventedCounters(t *testing.T) {
	fields := codedSubstrateLogFields(coded.Stats{}, false)
	if len(fields) != 2 || fields[0] != "fec_available" || fields[1] != false {
		t.Fatalf("unavailable fields = %#v", fields)
	}
}
