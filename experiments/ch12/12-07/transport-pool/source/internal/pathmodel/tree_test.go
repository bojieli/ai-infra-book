package pathmodel

import (
	"testing"
	"time"
)

// report drives a node to a known state: two members, so a share exists at
// all, with enough observed samples to be believed.
// Members are process-global and monotonic in production
// (nextErasureMemberID), which matters here: ancestor nodes are shared, so two
// chains reusing the same member id would overwrite each other's reports on
// every node they have in common. The helper takes a base so each caller
// occupies its own ids.
func feed(c *Chain, base Member, delivered, erasure, observed float64, rtt time.Duration) State {
	var last State
	for _, m := range []Member{base, base + 1} {
		last = c.Report(m, Observation{
			Erasure: erasure, BurstFactor: 1, ObservedSamples: observed,
			Delivered: delivered, RoundTrip: rtt,
		})
	}
	return last
}

// A caller that names only the endpoint pair must get exactly what it gets
// today. This is the property that lets the tree be introduced without every
// existing deployment becoming an experiment.
func TestChainOfOneMatchesASingleModel(t *testing.T) {
	ResetTree()
	chain := SharedChain(Key{Dest: "peer-a"})
	if chain.Nodes() != 1 {
		t.Fatalf("chain has %d nodes, want 1", chain.Nodes())
	}
	single := NewPathModel()

	var fromChain, fromSingle State
	for _, m := range []Member{1, 2} {
		o := Observation{Erasure: 0.14, BurstFactor: 1.2, ObservedSamples: 500,
			Delivered: 1 << 20, RoundTrip: 200 * time.Millisecond}
		fromChain = chain.Report(m, o)
		fromSingle = single.Report(m, o)
	}
	if fromChain.Share != fromSingle.Share || fromChain.Seed != fromSingle.Seed {
		t.Errorf("share/seed diverged: chain %v/%v single %v/%v",
			fromChain.Share, fromChain.Seed, fromSingle.Share, fromSingle.Seed)
	}
	if fromChain.Erasure != fromSingle.Erasure || fromChain.RoundTrip != fromSingle.RoundTrip {
		t.Errorf("erasure/rtt diverged: chain %v/%v single %v/%v",
			fromChain.Erasure, fromChain.RoundTrip, fromSingle.Erasure, fromSingle.RoundTrip)
	}
}

// The deployment this project was built for: one segment is the bottleneck for
// every destination. The shared node must be what binds, so that two
// destinations do not each get the whole of it.
func TestSharedSegmentBindsWhenItIsTheBottleneck(t *testing.T) {
	ResetTree()
	a := SharedChain(Key{Egress: "wan0", Group: "us-east", Dest: "svc-a"})
	b := SharedChain(Key{Egress: "wan0", Group: "us-east", Dest: "svc-b"})
	if a.Nodes() != 3 {
		t.Fatalf("chain has %d nodes, want 3", a.Nodes())
	}
	// Each destination delivers a modest rate; the egress carries both, so its
	// aggregate is the larger figure and its share the tighter constraint per
	// member.
	feed(a, 10, 1<<20, 0.05, 1000, 200*time.Millisecond)
	got := feed(b, 20, 1<<20, 0.05, 1000, 200*time.Millisecond)

	if got.Share <= 0 {
		t.Fatal("no share was set with two well-measured destinations")
	}
	inspect := a.Inspect()
	var bindingKey string
	for _, n := range inspect {
		if n.Binding {
			bindingKey = n.Key
		}
	}
	if bindingKey == "" {
		t.Fatalf("no node reported itself binding: %+v", inspect)
	}
}

// A destination nobody has measured must not throttle the flow that is about
// to measure it. Without this the tree introduces, at a finer grain, exactly
// the failure it was built to remove.
func TestUnmeasuredLeafDoesNotCapTheFlow(t *testing.T) {
	ResetTree()
	// A well-measured ancestor: two members, a high delivered rate, plenty of
	// samples. It is entitled to constrain.
	known := SharedChain(Key{Egress: "wan0", Group: "us-east", Dest: "known"})
	feed(known, 30, 8<<20, 0.02, 5000, 100*time.Millisecond)

	// A fresh destination in the same group. It has two members, so it does
	// produce a share, and that share is tiny because it has barely sent
	// anything -- but it has almost no samples behind it, so it must not be
	// what caps the flow. This is the case the confidence rule exists for: a
	// node with a number is not the same as a node with evidence.
	fresh := SharedChain(Key{Egress: "wan0", Group: "us-east", Dest: "brand-new"})
	var got State
	for _, m := range []Member{7, 8} {
		got = fresh.Report(m, Observation{
			Erasure: 0, BurstFactor: 1, ObservedSamples: 3,
			Delivered: 4096, RoundTrip: 100 * time.Millisecond,
		})
	}
	if fresh.Leaf().Current().Share <= 0 {
		t.Fatal("test does not exercise the rule: the leaf produced no share")
	}
	// The ancestors carry megabytes per second and the fresh leaf a few
	// kilobytes, so the two possible answers differ by three orders of
	// magnitude. Comparing against the ancestor rather than against a
	// recomputed leaf figure keeps the assertion about which node won.
	ancestor := fresh.nodes[0].Current().Share
	if ancestor <= 0 {
		t.Fatal("the shared ancestor produced no share")
	}
	if got.Share > 0 && got.Share < ancestor/10 {
		t.Errorf("an unmeasured leaf capped the flow at %v; the measured ancestor allowed %v",
			got.Share, ancestor)
	}
	// It should still inherit a seed from what the group already knows, since
	// a seed is not a ceiling.
	if got.Seed <= 0 {
		t.Error("a fresh destination inherited no seed from its measured group")
	}
}

// The confidence rule is about evidence, not about size: once a node has
// measured enough, a genuinely small share must bind even though it is small.
// Otherwise the rule would silently disable the tree's whole purpose.
func TestWellMeasuredNarrowLeafDoesCapTheFlow(t *testing.T) {
	ResetTree()
	known := SharedChain(Key{Egress: "wan0", Group: "us-east", Dest: "known"})
	feed(known, 30, 8<<20, 0.02, 5000, 100*time.Millisecond)

	narrow := SharedChain(Key{Egress: "wan0", Group: "us-east", Dest: "narrow"})
	got := feed(narrow, 40, 4096, 0.02, 5000, 100*time.Millisecond)

	ancestor := narrow.nodes[0].Current().Share
	if ancestor <= 0 {
		t.Fatal("the shared ancestor produced no share to be constrained below")
	}
	if got.Share <= 0 {
		t.Fatal("a well-measured narrow leaf imposed no constraint at all")
	}
	// The leaf delivers three orders of magnitude less than the ancestor, so a
	// chain that let the ancestor win would be off by about that much.
	if got.Share > ancestor/10 {
		t.Errorf("chain share %v is not constrained by the narrow leaf (ancestor allows %v)",
			got.Share, ancestor)
	}
}

// Ancestor nodes are shared, so two destinations must not overwrite each
// other's contributions there. This is a statement about the member ids
// callers allocate, and it is load-bearing: production ids are monotonic
// across the process, and a caller that restarted them per destination would
// make every group node report only its most recent member.
func TestSharedAncestorsPoolDistinctMembers(t *testing.T) {
	ResetTree()
	a := SharedChain(Key{Egress: "wan0", Group: "g", Dest: "a"})
	b := SharedChain(Key{Egress: "wan0", Group: "g", Dest: "b"})
	feed(a, 100, 1<<20, 0.1, 1000, time.Millisecond)
	feed(b, 200, 1<<20, 0.1, 1000, time.Millisecond)
	if got := a.nodes[0].Members(); got != 4 {
		t.Errorf("the shared egress node pooled %d members, want 4 from two destinations", got)
	}
	if got := a.Leaf().Members(); got != 2 {
		t.Errorf("a leaf pooled %d members, want its own 2", got)
	}
}

// Erasure accumulates along a path, so the chain must never report less than
// any node on it. Reporting the minimum, or only the leaf's, is how a flow
// ends up carrying no parity into a channel that is erasing -- the failure
// docs/CONTROL-REDESIGN.md was written about, reintroduced one level up.
func TestErasureIsNeverUnderReported(t *testing.T) {
	ResetTree()
	c := SharedChain(Key{Egress: "wan0", Group: "cn", Dest: "peer"})
	// The shared segment is known to erase; the leaf has barely looked and
	// happens to have seen a clean sample.
	c.nodes[0].Report(1, Observation{Erasure: 0.40, BurstFactor: 2, ObservedSamples: 5000, Delivered: 1 << 20})
	got := c.Report(2, Observation{Erasure: 0.0, BurstFactor: 1, ObservedSamples: 4, Delivered: 1 << 20})
	if got.Erasure < 0.39 {
		t.Errorf("chain erasure %v, want the shared segment's 0.40", got.Erasure)
	}
	// The shared segment's burst factor is pooled by sample weight, so a
	// handful of clean leaf samples pull it fractionally below 2 rather than
	// replacing it. What matters is that it stays near the measured figure
	// instead of collapsing to the leaf's 1.
	if got.BurstFactor < 1.99 {
		t.Errorf("chain burst factor %v, want the shared segment's ~2", got.BurstFactor)
	}
}

// A leaf that has measured more erasure than its ancestors is measuring its
// own tail as well as the shared part, and that total is what its code has to
// survive.
func TestLeafErasureAboveTheSharedSegmentIsKept(t *testing.T) {
	ResetTree()
	c := SharedChain(Key{Egress: "wan0", Group: "g", Dest: "bad-tail"})
	c.nodes[0].Report(1, Observation{Erasure: 0.05, BurstFactor: 1, ObservedSamples: 5000, Delivered: 1 << 20})
	got := c.Report(2, Observation{Erasure: 0.30, BurstFactor: 1, ObservedSamples: 5000, Delivered: 1 << 20})
	if got.Erasure < 0.29 {
		t.Errorf("chain erasure %v, want the leaf's 0.30", got.Erasure)
	}
}

// The leaf traverses everything its ancestors do plus its own tail, so the
// longest round trip on the chain is the one describing this flow.
func TestRoundTripDescribesTheWholePath(t *testing.T) {
	ResetTree()
	c := SharedChain(Key{Egress: "wan0", Group: "g", Dest: "far"})
	c.nodes[0].Report(1, Observation{ObservedSamples: 100, BurstFactor: 1,
		Delivered: 1 << 20, RoundTrip: 20 * time.Millisecond})
	got := c.Report(2, Observation{ObservedSamples: 100, BurstFactor: 1,
		Delivered: 1 << 20, RoundTrip: 200 * time.Millisecond})
	if got.RoundTrip != 200*time.Millisecond {
		t.Errorf("chain round trip %v, want 200ms", got.RoundTrip)
	}
}

// Destinations in different groups must not share a leaf key, or one group's
// measurements would be attributed to another's destination of the same name.
func TestGroupsDoNotCollideOnDestinationNames(t *testing.T) {
	ResetTree()
	a := SharedChain(Key{Egress: "wan0", Group: "us-east", Dest: "api"})
	b := SharedChain(Key{Egress: "wan0", Group: "eu-west", Dest: "api"})
	if a.Leaf() == b.Leaf() {
		t.Fatal("same-named destinations in different groups shared a leaf")
	}
	if a.nodes[0] != b.nodes[0] {
		t.Error("destinations behind one egress did not share the egress node")
	}
	if a.nodes[1] == b.nodes[1] {
		t.Error("destinations in different groups shared a group node")
	}
}

// An empty key is not a distinct group: a caller who knows only some levels
// gets a shorter chain, not a chain with a node named "".
func TestEmptyLevelsAreSkippedRatherThanNamed(t *testing.T) {
	ResetTree()
	if got := SharedChain(Key{Dest: "d"}).Nodes(); got != 1 {
		t.Errorf("dest-only chain has %d nodes, want 1", got)
	}
	if got := SharedChain(Key{Egress: "e", Dest: "d"}).Nodes(); got != 2 {
		t.Errorf("egress+dest chain has %d nodes, want 2", got)
	}
	if got := SharedChain(Key{}).Nodes(); got != 0 {
		t.Errorf("empty key produced %d nodes, want 0", got)
	}
	// An empty chain must be safe to use rather than a panic waiting for the
	// first caller who has no key yet.
	var empty *Chain
	if s := empty.Report(1, Observation{}); s.Share != 0 {
		t.Error("a nil chain returned a constraint")
	}
	if empty.Nodes() != 0 || empty.Leaf() != nil {
		t.Error("a nil chain misreported itself")
	}
}

// Forgetting an uplink must discard what was measured about the network that
// is gone without discarding destinations reached another way.
func TestForgetTreeDropsOnlyTheNamedUplink(t *testing.T) {
	ResetTree()
	feed(SharedChain(Key{Egress: "wifi", Group: "g", Dest: "d"}), 60, 1<<20, 0.1, 500, time.Millisecond)
	feed(SharedChain(Key{Egress: "cell", Group: "g", Dest: "d"}), 70, 1<<20, 0.1, 500, time.Millisecond)
	ForgetTree("wifi")
	for _, n := range InspectTree() {
		if n.Key == "" {
			continue
		}
		if contains(n.Key, "wifi") {
			t.Errorf("node %q survived forgetting its uplink", n.Key)
		}
	}
	var sawCell bool
	for _, n := range InspectTree() {
		if contains(n.Key, "cell") {
			sawCell = true
		}
	}
	if !sawCell {
		t.Error("forgetting one uplink discarded another")
	}
}

func contains(s, sub string) bool {
	for i := 0; i+len(sub) <= len(s); i++ {
		if s[i:i+len(sub)] == sub {
			return true
		}
	}
	return false
}

// Inspect exists so an operator can ask which segment is holding a flow. A
// hierarchy that cannot answer that is a hierarchy that cannot be debugged.
func TestInspectNamesEveryNodeRootFirst(t *testing.T) {
	ResetTree()
	c := SharedChain(Key{Egress: "wan0", Group: "us-east", Dest: "svc"})
	feed(c, 50, 1<<20, 0.1, 1000, 50*time.Millisecond)
	got := c.Inspect()
	if len(got) != 3 {
		t.Fatalf("Inspect returned %d nodes, want 3", len(got))
	}
	if got[0].Key[:6] != "egress" {
		t.Errorf("first node is %q, want the egress", got[0].Key)
	}
	if got[2].Key[:4] != "dest" {
		t.Errorf("last node is %q, want the destination", got[2].Key)
	}
	for _, n := range got {
		if n.Members == 0 {
			t.Errorf("node %q reports no members after being fed", n.Key)
		}
	}
}

// When no node has measured enough to constrain anything, the chain must still
// hand a joining lane a rate to start from. A seed is not a ceiling, and
// starting from a poorly-measured neighbour's figure is strictly better than
// starting from zero -- on a channel that erases, rediscovering the path from
// nothing is the same ramp that costs a loss-based controller the path in the
// first place.
func TestSeedSurvivesWhenNoNodeIsConfident(t *testing.T) {
	ResetTree()
	c := SharedChain(Key{Egress: "wan0", Group: "g", Dest: "d"})
	var got State
	for _, m := range []Member{300, 301} {
		got = c.Report(m, Observation{
			Erasure: 0.1, BurstFactor: 1, ObservedSamples: 5, // far below confidentSamples
			Delivered: 1 << 20, RoundTrip: 50 * time.Millisecond,
		})
	}
	if got.Share != 0 {
		t.Errorf("share %v was imposed with no confident node", got.Share)
	}
	if got.Seed <= 0 {
		t.Error("no seed offered although every node had a delivered rate")
	}
}

// Consumers hold the Model interface now, and a nil *PathModel stored in an
// interface is not equal to nil. A caller's own `if path != nil` guard
// therefore does not fire, so the model itself has to survive being nil rather
// than turning a caller's oversight into a crash inside the transport.
func TestNilModelsAreInertRatherThanFatal(t *testing.T) {
	var node *PathModel
	var chain *Chain
	for _, m := range []Model{node, chain} {
		if got := m.Report(1, Observation{Delivered: 1 << 20}); got != (State{}) {
			t.Errorf("a nil model returned %+v", got)
		}
		if got := m.Current(); got != (State{}) {
			t.Errorf("a nil model reported %+v", got)
		}
	}
	if node.Members() != 0 {
		t.Error("a nil node reported members")
	}
}

// The deployment the tree is for: one client reaching several providers over
// one uplink. The uplink node must pool across them, so the second provider
// starts from what the first measured about the shared segment, while their
// own peers stay separate.
func TestProvidersShareTheUplinkAndNotEachOther(t *testing.T) {
	ResetTree()
	one := SharedChain(Key{Egress: "203.0.113.7", Dest: "203.0.113.7->198.51.100.1"})
	two := SharedChain(Key{Egress: "203.0.113.7", Dest: "203.0.113.7->198.51.100.2"})
	if one.nodes[0] != two.nodes[0] {
		t.Fatal("two providers over one uplink did not share the uplink node")
	}
	if one.Leaf() == two.Leaf() {
		t.Fatal("two providers shared a peer node")
	}
	// The first provider measures the uplink.
	feed(one, 400, 4<<20, 0.08, 4000, 30*time.Millisecond)
	// The second arrives knowing nothing of its own.
	got := two.Report(500, Observation{BurstFactor: 1, ObservedSamples: 1, Delivered: 1024})
	if got.Seed <= 0 {
		t.Error("a newly reached provider inherited nothing from the shared uplink")
	}
	if got.Erasure < 0.07 {
		t.Errorf("erasure %v: the new provider did not inherit the uplink's measured 0.08", got.Erasure)
	}
}

// Merging is how the evidence a Correlator produces becomes a tree that
// reflects the path rather than somebody's belief about it.
func TestMergedGroupsShareANode(t *testing.T) {
	ResetTree()
	before := SharedChain(Key{Egress: "e", Group: "us-east-1", Dest: "a"})
	other := SharedChain(Key{Egress: "e", Group: "us-east-2", Dest: "b"})
	if before.nodes[1] == other.nodes[1] {
		t.Fatal("distinct groups shared a node before any merge")
	}
	MergeGroups("us-east-1", "us-east-2")
	afterA := SharedChain(Key{Egress: "e", Group: "us-east-1", Dest: "a"})
	afterB := SharedChain(Key{Egress: "e", Group: "us-east-2", Dest: "b"})
	if afterA.nodes[1] != afterB.nodes[1] {
		t.Error("merged groups did not share a node")
	}
	// The peers stay distinct: merging says they share a segment, not that
	// they are the same destination.
	if afterA.Leaf() == afterB.Leaf() {
		t.Error("merging groups also merged their destinations")
	}
}

// A correlator reports pairs in whatever order it found them, so merging must
// reach the same tree either way round, and must be transitive.
func TestMergeIsOrderIndependentAndTransitive(t *testing.T) {
	ResetTree()
	MergeGroups("b", "a")
	MergeGroups("c", "b")
	if got := GroupOf("c"); got != "a" {
		t.Errorf("GroupOf(c) = %q, want a after transitive merge", got)
	}
	if GroupOf("a") != GroupOf("b") || GroupOf("b") != GroupOf("c") {
		t.Errorf("merged groups resolve differently: %q %q %q",
			GroupOf("a"), GroupOf("b"), GroupOf("c"))
	}
	ResetTree()
	MergeGroups("a", "b")
	MergeGroups("b", "c")
	if got := GroupOf("c"); got != "a" {
		t.Errorf("reversed merge order gave GroupOf(c) = %q, want a", got)
	}
}

func TestSplitUndoesAMerge(t *testing.T) {
	ResetTree()
	MergeGroups("x", "y")
	if GroupOf("y") != "x" {
		t.Fatalf("merge did not take: %q", GroupOf("y"))
	}
	SplitGroup("y")
	if GroupOf("y") != "y" {
		t.Errorf("after split, GroupOf(y) = %q", GroupOf("y"))
	}
}

// A cycle in the alias map must not hang a flow. It should not be reachable
// through MergeGroups, which is why the bound is a guard rather than a policy.
func TestAliasResolutionIsBounded(t *testing.T) {
	ResetTree()
	treeMu.Lock()
	groupAlias["p"] = "q"
	groupAlias["q"] = "p"
	treeMu.Unlock()
	done := make(chan string, 1)
	go func() { done <- GroupOf("p") }()
	select {
	case <-done:
	case <-time.After(2 * time.Second):
		t.Fatal("alias resolution did not terminate on a cycle")
	}
}

// The correlator has to be fed by ordinary reporting, or the evidence it
// gathers is only ever what a test put there.
func TestReportingFeedsTheCorrelator(t *testing.T) {
	ResetTree()
	ResetCorrelator()
	c := SharedChain(Key{Egress: "e", Group: "us-east", Dest: "svc"})
	feed(c, 800, 1<<20, 0.12, 1000, 40*time.Millisecond)
	if got := SharedCorrelator().Groups(); len(got) != 1 || got[0] != "us-east" {
		t.Errorf("correlator groups = %v, want [us-east]", got)
	}
}

// A chain that names no group records nothing, because the question the
// correlator answers is about groups.
func TestAGrouplessChainRecordsNothing(t *testing.T) {
	ResetTree()
	ResetCorrelator()
	c := SharedChain(Key{Dest: "peer"})
	feed(c, 900, 1<<20, 0.12, 1000, 40*time.Millisecond)
	if got := SharedCorrelator().Groups(); len(got) != 0 {
		t.Errorf("correlator groups = %v, want none", got)
	}
}

// Acting on the evidence is opt-in. A deployment that did not ask keeps the
// static hierarchy it was given, however strongly two groups correlate.
func TestRegroupingIsOptIn(t *testing.T) {
	ResetTree()
	ResetCorrelator()
	lastRegroup.Store(0)
	// Two groups whose congestion moves together, reported through ordinary
	// chains that did not ask to regroup.
	a := SharedChain(Key{Egress: "e", Group: "alpha", Dest: "a"})
	b := SharedChain(Key{Egress: "e", Group: "beta", Dest: "b"})
	for i := 0; i < 40; i++ {
		spike := 0.0
		if i%5 == 0 {
			spike = 0.3
		}
		now := base.Add(time.Duration(i) * bucketWidth)
		SharedCorrelator().Observe("alpha", now, Signal{LossRate: spike})
		SharedCorrelator().Observe("beta", now, Signal{LossRate: spike})
	}
	feed(a, 1000, 1<<20, 0.1, 500, time.Millisecond)
	feed(b, 1100, 1<<20, 0.1, 500, time.Millisecond)
	if GroupOf("beta") != "beta" {
		t.Error("a chain that did not opt in regrouped anyway")
	}

	// The same evidence, through a chain that did ask.
	lastRegroup.Store(0)
	c := SharedChainRegrouping(Key{Egress: "e", Group: "alpha", Dest: "a"})
	feed(c, 1200, 1<<20, 0.1, 500, time.Millisecond)
	if GroupOf("beta") == "beta" {
		t.Error("a regrouping chain did not act on strongly correlated groups")
	}
}

// Merging is rate limited, because the evidence is gathered over ten seconds
// and re-deciding faster than that reads the same buckets twice.
func TestRegroupingIsRateLimited(t *testing.T) {
	ResetTree()
	ResetCorrelator()
	lastRegroup.Store(time.Now().UnixNano())
	for i := 0; i < 40; i++ {
		now := base.Add(time.Duration(i) * bucketWidth)
		spike := 0.0
		if i%5 == 0 {
			spike = 0.3
		}
		SharedCorrelator().Observe("x", now, Signal{LossRate: spike})
		SharedCorrelator().Observe("y", now, Signal{LossRate: spike})
	}
	c := SharedChainRegrouping(Key{Egress: "e", Group: "x", Dest: "d"})
	feed(c, 1300, 1<<20, 0.1, 500, time.Millisecond)
	if GroupOf("y") != "y" {
		t.Error("a merge happened inside the rate limit")
	}
}
