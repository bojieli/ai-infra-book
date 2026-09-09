package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"os/exec"
	"runtime"
	"runtime/debug"
	"sort"
	"strings"

	"github.com/bojieli/queqiao/internal/pathsim"
)

// Report is the machine-readable result of one benchmark invocation. Its
// shape is deliberately stable: results are only useful for tracking a
// transport across commits if they can be diffed, and a text table cannot be.
type Report struct {
	SchemaVersion int                `json:"schema_version"`
	Source        SourceReport       `json:"source"`
	Arguments     []string           `json:"arguments"`
	Path          PathReport         `json:"path"`
	Trials        []TrialRecord      `json:"trials"`
	Summary       []CellSummary      `json:"summary"`
	Latency       []LatencyRecord    `json:"latency,omitempty"`
	Contention    []ContentionRecord `json:"contention,omitempty"`
}

// SourceReport makes a result attributable to the exact tree and toolchain
// that produced it. Arguments and the seeded PathReport supply the other half
// of reproducibility: what that binary was asked to measure.
type SourceReport struct {
	Revision   string         `json:"revision,omitempty"`
	CommitTime string         `json:"commit_time,omitempty"`
	Modified   bool           `json:"modified"`
	GoVersion  string         `json:"go_version"`
	GOOS       string         `json:"goos"`
	GOARCH     string         `json:"goarch"`
	Module     string         `json:"module,omitempty"`
	Version    string         `json:"version,omitempty"`
	Modules    []ModuleReport `json:"modules,omitempty"`
}

type ModuleReport struct {
	Path    string `json:"path"`
	Version string `json:"version,omitempty"`
	Sum     string `json:"sum,omitempty"`
	Replace string `json:"replace,omitempty"`
}

type PathReport struct {
	RTTMillis           int     `json:"rtt_ms"`
	LossPercent         float64 `json:"loss_percent"`
	UpstreamLossPercent float64 `json:"upstream_loss_percent,omitempty"`
	LossBurstPackets    float64 `json:"loss_burst_packets,omitempty"`
	JitterMillis        float64 `json:"jitter_ms,omitempty"`
	WanderMillis        float64 `json:"delay_wander_ms,omitempty"`
	RateMbits           float64 `json:"rate_mbits"`
	PerFlowMbits        float64 `json:"per_flow_mbits,omitempty"`
	QueueBytes          int     `json:"queue_bytes"`
	Seed                int64   `json:"seed"`
	ObjectBytes         int64   `json:"object_bytes"`
	Congestion          string  `json:"congestion"`
	ChunkSize           int     `json:"chunk_size,omitempty"`
	QUICPool            bool    `json:"quic_pool"`
}

type TrialRecord struct {
	Stack       string             `json:"stack"`
	Flows       int                `json:"flows"`
	Trial       int                `json:"trial"`
	Seconds     float64            `json:"seconds"`
	MbitsPerSec float64            `json:"mbits_per_sec"`
	Complete    bool               `json:"complete"`
	Note        string             `json:"note,omitempty"`
	Interactive *InteractiveReport `json:"interactive,omitempty"`
}

type LatencyRecord struct {
	Stack      string  `json:"stack"`
	Trial      int     `json:"trial"`
	ColdMillis float64 `json:"cold_ms"`
	WarmMillis float64 `json:"warm_ms"`
	Complete   bool    `json:"complete"`
	Note       string  `json:"note,omitempty"`
}

type ContentionRecord struct {
	Trial     int     `json:"trial"`
	StackA    string  `json:"stack_a"`
	StackB    string  `json:"stack_b"`
	MbitsA    float64 `json:"mbits_a"`
	MbitsB    float64 `json:"mbits_b"`
	ShareA    float64 `json:"share_a"`
	RatioAToB float64 `json:"ratio_a_to_b"`
	Complete  bool    `json:"complete"`
	Note      string  `json:"note,omitempty"`
}

// InteractiveReport records latency of small requests issued while the bulk
// transfer ran. Separating connect from first byte matters: they are different
// defects with different fixes.
type InteractiveReport struct {
	Samples        int     `json:"samples"`
	P50Millis      float64 `json:"p50_ms"`
	P95Millis      float64 `json:"p95_ms"`
	MaxMillis      float64 `json:"max_ms"`
	ConnectP95     float64 `json:"connect_p95_ms"`
	FirstByteP95Ms float64 `json:"first_byte_p95_ms"`
}

// CellSummary aggregates every trial of one (stack, flows) cell.
//
// The statistics deliberately include failed trials at their partial rate. A
// median taken over completions alone rewards a transport for giving up: in a
// 35%-burst-loss block the reference completed 7 of 12 trials and queqiao 10 of
// 12, and reporting only successes made the transport that finished the hard
// trials look slower than the one that abandoned them.
type CellSummary struct {
	Stack     string `json:"stack"`
	Flows     int    `json:"flows"`
	Trials    int    `json:"trials"`
	Completed int    `json:"completed"`
	// SetupFailures are trials whose flow never started, usually because the
	// warm-up request could not be established. They measure the path, not the
	// transport's transfer behavior, and carry no goodput, so they are counted
	// and reported but excluded from the goodput statistics and from the
	// completion rate. Leaving them in drags a median toward zero for whichever
	// stack happened to run during a bad window.
	SetupFailures  int     `json:"setup_failures,omitempty"`
	CompletionRate float64 `json:"completion_rate"`
	MedianMbits    float64 `json:"median_mbits_all_trials"`
	MeanMbits      float64 `json:"mean_mbits_all_trials"`
	WorstMbits     float64 `json:"worst_mbits_all_trials"`
	// MedianCompleteMbits is the median over completed trials only. It is
	// reported for continuity with older campaign notes and must never be
	// compared across stacks with different completion rates.
	MedianCompleteMbits float64            `json:"median_mbits_completed_only"`
	Interactive         *InteractiveReport `json:"interactive_median,omitempty"`
}

func describePath(opts options, cfg pathsim.Config) PathReport {
	return PathReport{
		RTTMillis: opts.rttMillis, LossPercent: opts.lossPercent,
		UpstreamLossPercent: opts.lossUp, LossBurstPackets: opts.lossBurst,
		JitterMillis: opts.jitterMillis, WanderMillis: opts.wanderMillis,
		RateMbits: opts.rateMbits, PerFlowMbits: opts.perFlowMbits,
		QueueBytes: cfg.QueueBytes, Seed: opts.seed, ObjectBytes: opts.bytes,
		Congestion: opts.congestion,
		ChunkSize:  opts.chunkSize, QUICPool: opts.quicPool,
	}
}

func describeSource() SourceReport {
	report := SourceReport{GoVersion: runtime.Version(), GOOS: runtime.GOOS, GOARCH: runtime.GOARCH}
	info, ok := debug.ReadBuildInfo()
	if ok {
		report.Module, report.Version = info.Main.Path, info.Main.Version
		for _, setting := range info.Settings {
			switch setting.Key {
			case "vcs.revision":
				report.Revision = setting.Value
			case "vcs.time":
				report.CommitTime = setting.Value
			case "vcs.modified":
				report.Modified = setting.Value == "true"
			}
		}
		for _, dependency := range info.Deps {
			module := ModuleReport{Path: dependency.Path, Version: dependency.Version, Sum: dependency.Sum}
			if dependency.Replace != nil {
				module.Replace = dependency.Replace.Path
				if dependency.Replace.Version != "" {
					module.Replace += "@" + dependency.Replace.Version
				}
			}
			report.Modules = append(report.Modules, module)
		}
	}
	// `go run` currently omits VCS build settings even in a checkout, and it is
	// how the documented harness is invoked. Ask that checkout directly rather
	// than silently emitting an unattributed report. A standalone installed
	// binary still uses the immutable settings embedded by `go build` above.
	if report.Revision == "" {
		if output, err := exec.Command("git", "rev-parse", "HEAD").Output(); err == nil {
			report.Revision = strings.TrimSpace(string(output))
		}
		if output, err := exec.Command("git", "show", "-s", "--format=%cI", "HEAD").Output(); err == nil {
			report.CommitTime = strings.TrimSpace(string(output))
		}
		if output, err := exec.Command("git", "status", "--porcelain=v1", "--untracked-files=normal").Output(); err == nil {
			report.Modified = len(output) != 0
		}
	}
	sort.Slice(report.Modules, func(i, j int) bool { return report.Modules[i].Path < report.Modules[j].Path })
	return report
}

func summarize(trials []TrialRecord) []CellSummary {
	type key struct {
		stack string
		flows int
	}
	grouped := map[key][]TrialRecord{}
	var order []key
	for _, trial := range trials {
		k := key{trial.Stack, trial.Flows}
		if _, seen := grouped[k]; !seen {
			order = append(order, k)
		}
		grouped[k] = append(grouped[k], trial)
	}
	summaries := make([]CellSummary, 0, len(order))
	for _, k := range order {
		group := grouped[k]
		all := make([]float64, 0, len(group))
		completed := make([]float64, 0, len(group))
		interactive := make([]InteractiveReport, 0, len(group))
		setupFailures := 0
		for _, trial := range group {
			if isSetupFailure(trial) {
				setupFailures++
				continue
			}
			all = append(all, trial.MbitsPerSec)
			if trial.Complete {
				completed = append(completed, trial.MbitsPerSec)
			}
			if trial.Interactive != nil {
				interactive = append(interactive, *trial.Interactive)
			}
		}
		sort.Float64s(all)
		sort.Float64s(completed)
		measured := len(all)
		summary := CellSummary{
			Stack: k.stack, Flows: k.flows, Trials: len(group), Completed: len(completed),
			SetupFailures:       setupFailures,
			MedianMbits:         round3(median(all)),
			MeanMbits:           round3(mean(all)),
			MedianCompleteMbits: round3(median(completed)),
		}
		if measured > 0 {
			summary.CompletionRate = round3(float64(len(completed)) / float64(measured))
			summary.WorstMbits = round3(all[0])
		}
		if len(interactive) > 0 {
			summary.Interactive = medianInteractive(interactive)
		}
		summaries = append(summaries, summary)
	}
	return summaries
}

// isSetupFailure reports whether a trial never reached the transfer stage.
func isSetupFailure(trial TrialRecord) bool {
	return !trial.Complete && (strings.HasPrefix(trial.Note, "warmup:") || strings.HasPrefix(trial.Note, "setup:"))
}

func medianInteractive(reports []InteractiveReport) *InteractiveReport {
	pick := func(get func(InteractiveReport) float64) float64 {
		values := make([]float64, len(reports))
		for i, report := range reports {
			values[i] = get(report)
		}
		sort.Float64s(values)
		return round3(median(values))
	}
	return &InteractiveReport{
		Samples:        len(reports),
		P50Millis:      pick(func(r InteractiveReport) float64 { return r.P50Millis }),
		P95Millis:      pick(func(r InteractiveReport) float64 { return r.P95Millis }),
		MaxMillis:      pick(func(r InteractiveReport) float64 { return r.MaxMillis }),
		ConnectP95:     pick(func(r InteractiveReport) float64 { return r.ConnectP95 }),
		FirstByteP95Ms: pick(func(r InteractiveReport) float64 { return r.FirstByteP95Ms }),
	}
}

func printSummary(summaries []CellSummary) {
	if len(summaries) == 0 {
		return
	}
	fmt.Printf("\nstack\tflows\tcomplete\tsetup_fail\tmedian_mbits\tmean_mbits\tworst_mbits\tinteractive_p50_ms\tinteractive_p95_ms\n")
	for _, s := range summaries {
		p50, p95 := "", ""
		if s.Interactive != nil {
			p50 = fmt.Sprintf("%.0f", s.Interactive.P50Millis)
			p95 = fmt.Sprintf("%.0f", s.Interactive.P95Millis)
		}
		fmt.Printf("%s\t%d\t%d/%d\t%d\t%.2f\t%.2f\t%.2f\t%s\t%s\n",
			s.Stack, s.Flows, s.Completed, s.Trials-s.SetupFailures, s.SetupFailures,
			s.MedianMbits, s.MeanMbits, s.WorstMbits, p50, p95)
	}
}

// gateReport fails when queqiao is materially worse than the reference in any
// cell measured for both, so a transport change can be rejected automatically
// rather than only noticed by someone reading a table.
func gateReport(summaries []CellSummary, tolerance float64) error {
	if tolerance < 0 {
		tolerance = 0
	}
	byCell := map[int]map[string]CellSummary{}
	for _, s := range summaries {
		if byCell[s.Flows] == nil {
			byCell[s.Flows] = map[string]CellSummary{}
		}
		byCell[s.Flows][s.Stack] = s
	}
	flows := make([]int, 0, len(byCell))
	for f := range byCell {
		flows = append(flows, f)
	}
	sort.Ints(flows)
	var failures []string
	compared := 0
	for _, f := range flows {
		reference, hasReference := byCell[f]["baseline"]
		subject, hasSubject := byCell[f]["queqiao"]
		if !hasReference || !hasSubject {
			continue
		}
		compared++
		if subject.CompletionRate < reference.CompletionRate {
			failures = append(failures, fmt.Sprintf(
				"%d flows: completed %.0f%% against the reference's %.0f%%",
				f, subject.CompletionRate*100, reference.CompletionRate*100))
		}
		floor := reference.MedianMbits * (1 - tolerance)
		if reference.MedianMbits > 0 && subject.MedianMbits < floor {
			failures = append(failures, fmt.Sprintf(
				"%d flows: median %.2f Mbit/s is below the %.2f floor (reference %.2f, tolerance %.0f%%)",
				f, subject.MedianMbits, floor, reference.MedianMbits, tolerance*100))
		}
	}
	if compared == 0 {
		return fmt.Errorf("gate requires both stacks; run with --stacks baseline,queqiao")
	}
	if len(failures) > 0 {
		for _, failure := range failures {
			fmt.Fprintf(os.Stderr, "gate: %s\n", failure)
		}
		return fmt.Errorf("gate failed in %d of %d compared cells", len(failures), compared)
	}
	fmt.Printf("\ngate: queqiao is within %.0f%% of the reference in all %d compared cells\n", tolerance*100, compared)
	return nil
}

func writeReport(path string, report Report) error {
	encoded, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(encoded, '\n'), 0o644)
}

func median(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	middle := len(values) / 2
	if len(values)%2 == 1 {
		return values[middle]
	}
	return (values[middle-1] + values[middle]) / 2
}

func mean(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	total := 0.0
	for _, value := range values {
		total += value
	}
	return total / float64(len(values))
}

func round3(value float64) float64 {
	if math.IsNaN(value) || math.IsInf(value, 0) {
		return 0
	}
	return math.Round(value*1000) / 1000
}
