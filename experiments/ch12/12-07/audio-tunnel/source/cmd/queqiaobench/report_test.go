package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func trial(stack string, flows int, mbits float64, complete bool) TrialRecord {
	return TrialRecord{Stack: stack, Flows: flows, MbitsPerSec: mbits, Complete: complete}
}

// A median taken over completed trials alone rewards a transport for giving
// up. In a 35%-burst-loss block the reference completed 7 of 12 trials and
// queqiao 10 of 12, and reporting only successes made the transport that
// finished the hard trials look slower than the one that abandoned them. The
// headline statistic therefore has to include failures at their partial rate.
func TestSummaryCountsFailedTrials(t *testing.T) {
	trials := []TrialRecord{
		// Gives up on the hard trials, but is fast on the easy ones.
		trial("baseline", 1, 8, true), trial("baseline", 1, 8, true),
		trial("baseline", 1, 0.2, false), trial("baseline", 1, 0.2, false),
		// Finishes everything, more slowly on the hard trials.
		trial("queqiao", 1, 7, true), trial("queqiao", 1, 7, true),
		trial("queqiao", 1, 3, true), trial("queqiao", 1, 3, true),
	}
	summaries := summarize(trials)
	if len(summaries) != 2 {
		t.Fatalf("summaries = %d, want one per stack", len(summaries))
	}
	byStack := map[string]CellSummary{}
	for _, s := range summaries {
		byStack[s.Stack] = s
	}
	reference, subject := byStack["baseline"], byStack["queqiao"]
	if reference.MedianCompleteMbits <= subject.MedianCompleteMbits {
		t.Fatal("test data no longer reproduces the misleading completed-only comparison")
	}
	if subject.MedianMbits <= reference.MedianMbits {
		t.Fatalf("all-trial median: queqiao %.2f, reference %.2f; the transport that "+
			"finished every trial must not rank lower", subject.MedianMbits, reference.MedianMbits)
	}
	if reference.CompletionRate != 0.5 || subject.CompletionRate != 1 {
		t.Fatalf("completion rates = %.2f and %.2f, want 0.5 and 1", reference.CompletionRate, subject.CompletionRate)
	}
	if reference.WorstMbits != 0.2 {
		t.Fatalf("worst = %.2f, want the worst trial including failures", reference.WorstMbits)
	}
}

func TestGateFailsOnGoodputShortfall(t *testing.T) {
	summaries := summarize([]TrialRecord{
		trial("baseline", 1, 10, true), trial("baseline", 1, 10, true),
		trial("queqiao", 1, 8, true), trial("queqiao", 1, 8, true),
	})
	if err := gateReport(summaries, 0.10); err == nil {
		t.Fatal("a 20 percent shortfall passed a 10 percent tolerance")
	}
	if err := gateReport(summaries, 0.30); err != nil {
		t.Fatalf("a 20 percent shortfall failed a 30 percent tolerance: %v", err)
	}
}

// Completing fewer transfers is a regression even at identical goodput, so the
// gate must not be satisfiable by giving up on the hard trials.
func TestGateFailsOnCompletionShortfall(t *testing.T) {
	summaries := summarize([]TrialRecord{
		trial("baseline", 1, 10, true), trial("baseline", 1, 10, true),
		trial("queqiao", 1, 10, true), trial("queqiao", 1, 10, false),
	})
	if err := gateReport(summaries, 0.50); err == nil {
		t.Fatal("a completion-rate regression passed the gate")
	}
}

func TestGateRequiresBothStacks(t *testing.T) {
	summaries := summarize([]TrialRecord{trial("queqiao", 1, 10, true)})
	err := gateReport(summaries, 0.10)
	if err == nil || !strings.Contains(err.Error(), "both stacks") {
		t.Fatalf("gate error = %v, want a clear complaint about the missing reference", err)
	}
}

func TestGatePassesAtParity(t *testing.T) {
	summaries := summarize([]TrialRecord{
		trial("baseline", 1, 10, true), trial("baseline", 4, 20, true),
		trial("queqiao", 1, 10.5, true), trial("queqiao", 4, 19.5, true),
	})
	if err := gateReport(summaries, 0.10); err != nil {
		t.Fatalf("parity failed the gate: %v", err)
	}
}

func TestReportRoundTripsAsJSON(t *testing.T) {
	report := Report{
		SchemaVersion: 1,
		Arguments:     []string{"--rtt", "200", "--seed", "7"},
		Path:          PathReport{RTTMillis: 200, LossPercent: 1, RateMbits: 100, Seed: 7},
		Trials:        []TrialRecord{trial("queqiao", 1, 10, true)},
		Latency:       []LatencyRecord{{Stack: "queqiao", Trial: 1, ColdMillis: 210, WarmMillis: 201, Complete: true}},
	}
	report.Summary = summarize(report.Trials)
	path := filepath.Join(t.TempDir(), "report.json")
	if err := writeReport(path, report); err != nil {
		t.Fatal(err)
	}
	if err := writeReport(path, report); err != nil {
		t.Fatalf("rewriting an existing report: %v", err)
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var decoded Report
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatal(err)
	}
	if decoded.SchemaVersion != 1 || decoded.Path.Seed != 7 || len(decoded.Latency) != 1 {
		t.Fatalf("report lost reproducibility fields: %+v", decoded)
	}
}

func TestSourceProvenanceNamesTheCheckout(t *testing.T) {
	source := describeSource()
	if source.Revision == "" || source.CommitTime == "" {
		t.Fatalf("source provenance does not identify the checkout: %+v", source)
	}
	if source.GoVersion == "" || source.GOOS == "" || source.GOARCH == "" {
		t.Fatalf("source provenance does not identify the toolchain: %+v", source)
	}
}

func TestMedianHandlesEvenAndEmpty(t *testing.T) {
	if got := median(nil); got != 0 {
		t.Fatalf("median of nothing = %v, want 0", got)
	}
	if got := median([]float64{1, 3}); got != 2 {
		t.Fatalf("median of two values = %v, want their midpoint", got)
	}
	if got := median([]float64{1, 2, 3}); got != 2 {
		t.Fatalf("median of three values = %v, want 2", got)
	}
}

// A trial whose flow never started measures the path, not the transport's
// transfer behaviour, and carries no goodput. Counting it drags the median
// toward zero for whichever stack happened to run during a bad window, and
// makes the completion rate depend on setup luck.
func TestSetupFailuresAreSeparatedFromTransportFailures(t *testing.T) {
	trials := []TrialRecord{
		{Stack: "queqiao", Flows: 1, MbitsPerSec: 10, Complete: true},
		{Stack: "queqiao", Flows: 1, MbitsPerSec: 12, Complete: true},
		{Stack: "queqiao", Flows: 1, MbitsPerSec: 0, Note: "warmup: EOF"},
		{Stack: "queqiao", Flows: 1, MbitsPerSec: 0, Note: "setup: dial failed"},
	}
	summaries := summarize(trials)
	got := summaries[0]
	if got.SetupFailures != 2 {
		t.Fatalf("setup failures = %d, want 2", got.SetupFailures)
	}
	if got.CompletionRate != 1 {
		t.Fatalf("completion rate = %.2f, want 1 over the trials that actually ran", got.CompletionRate)
	}
	if got.MedianMbits != 11 {
		t.Fatalf("median = %.2f, want 11 with setup failures excluded", got.MedianMbits)
	}
	if got.WorstMbits != 10 {
		t.Fatalf("worst = %.2f, want the worst measured trial", got.WorstMbits)
	}
}

// A mid-transfer stall is a transport failure and must still count: it is
// exactly the behaviour the completion rate exists to expose.
func TestPartialTransferStillCountsAsFailure(t *testing.T) {
	trials := []TrialRecord{
		{Stack: "baseline", Flows: 1, MbitsPerSec: 8, Complete: true},
		{Stack: "baseline", Flows: 1, MbitsPerSec: 1, Note: "received 4118325 of 4194304 bytes"},
	}
	got := summarize(trials)[0]
	if got.SetupFailures != 0 {
		t.Fatalf("setup failures = %d, want a stalled transfer counted as a transport failure", got.SetupFailures)
	}
	if got.CompletionRate != 0.5 {
		t.Fatalf("completion rate = %.2f, want 0.5", got.CompletionRate)
	}
}

// Every trial failing setup must not produce a divide-by-zero or a fake
// completion rate.
func TestAllSetupFailuresDoNotPanic(t *testing.T) {
	got := summarize([]TrialRecord{
		{Stack: "queqiao", Flows: 1, Note: "warmup: EOF"},
		{Stack: "queqiao", Flows: 1, Note: "warmup: EOF"},
	})[0]
	if got.SetupFailures != 2 || got.CompletionRate != 0 || got.MedianMbits != 0 {
		t.Fatalf("all-setup-failure cell = %+v, want zeroes and two setup failures", got)
	}
}
