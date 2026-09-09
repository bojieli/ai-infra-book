package pathmodel

import (
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

// A path is a chain of segments, and only one of them is the bottleneck.
//
// PathModel answers what one endpoint pair is doing, which is the right
// question when every flow crosses the same difficult segment and nothing
// beyond it matters. That is the deployment this project was built for, and on
// it the endpoint pair and the bottleneck are the same thing.
//
// They stop being the same thing as soon as flows go to different places. A
// host calling three services in two regions shares its uplink, its egress
// gateway and the first stretch of backbone with all of them, and shares
// nothing else with any of them. Modelling that as one path per destination
// makes every destination rediscover the shared segment; modelling it as one
// path for everything makes a congested peering point to one region throttle
// traffic to another.
//
// Neither is wrong so much as both are the same mistake at different
// granularities: assuming the answer instead of measuring it. What is actually
// true is a tree rooted at the egress, and a flow's budget is set by the
// tightest node along its own root-to-leaf path.
//
// The tree is built from the node type rather than replacing it. Each node is
// an ordinary PathModel measuring the traffic that crosses it, so a chain of
// one behaves exactly as a single model does today, and every existing caller
// is on that path unchanged.

// Key names where a flow goes, at the three granularities that are cheap to
// know before the flow starts.
//
// Empty fields are skipped rather than treated as a distinct group, so a
// caller that knows only the endpoint pair gets a chain of one and today's
// behaviour exactly.
type Key struct {
	// Egress identifies the local side: the uplink or source interface. It is
	// shared by every flow this host sends, whatever the destination.
	Egress string
	// Group is the destination's region, autonomous system, or prefix --
	// whatever granularity the deployment has reason to believe is shared. The
	// plan this implements bootstraps it statically and refines it by
	// correlating congestion signals; this is the bootstrap.
	Group string
	// Dest is the endpoint pair itself, the most specific granularity and the
	// one the existing model is keyed by.
	Dest string
}

// chainKeys renders the root-to-leaf node keys, most general first. Each level
// includes the levels above it so that two destinations in different groups
// never share a leaf key.
func (k Key) chainKeys() []string {
	var out []string
	if k.Egress != "" {
		out = append(out, "egress|"+k.Egress)
	}
	if k.Group != "" {
		out = append(out, "group|"+k.Egress+"|"+k.Group)
	}
	if k.Dest != "" {
		out = append(out, "dest|"+k.Egress+"|"+k.Group+"|"+k.Dest)
	}
	return out
}

// confidentSamples is how much evidence a node needs before its estimate may
// constrain a flow.
//
// It is the same hundred the path prewarm sends, chosen for the same reason: a
// loss proportion measured from ten packets has a standard error near fifteen
// points at the rates this project sees, and a hundred brings it under five. A
// node below this bar is not silent -- it still contributes what it has seen to
// the pool -- it simply may not be the reason a flow is slowed down.
const confidentSamples = 100

// Chain is one flow's view of the tree: the nodes it crosses, root first.
type Chain struct {
	nodes []*PathModel
	keys  []string
	// group is the destination grouping this chain belongs to, empty when the
	// caller named no group. It is what the correlator records against, since
	// the question it answers is which groups share a bottleneck.
	group string
	// regroup says whether this chain may act on the correlator's evidence.
	// It is off unless a deployment asks for it, because merging two groups
	// re-parents the budget of every flow that follows and that should be a
	// policy rather than a side effect of measurement.
	regroup bool
}

// Nodes is how many segments this chain distinguishes. A chain of one is the
// single-model case.
func (c *Chain) Nodes() int {
	if c == nil {
		return 0
	}
	return len(c.nodes)
}

// Leaf is the most specific node, which is the one a caller wanting today's
// behaviour should use directly.
func (c *Chain) Leaf() *PathModel {
	if c == nil || len(c.nodes) == 0 {
		return nil
	}
	return c.nodes[len(c.nodes)-1]
}

// Report records an observation against every node the flow crosses, and
// returns what the chain as a whole permits.
//
// Every node hears the report because every node carried the traffic. What
// differs is what each is entitled to conclude: the leaf saw the whole path,
// so its erasure is the total, while an ancestor pools across destinations and
// therefore measures only what they have in common.
func (c *Chain) Report(member Member, o Observation) State {
	if c == nil || len(c.nodes) == 0 {
		return State{}
	}
	states := make([]State, len(c.nodes))
	for i, n := range c.nodes {
		states[i] = n.Report(member, o)
	}
	out := combine(states)
	c.recordCongestion(out)
	return out
}

// recordCongestion feeds this chain's group to the correlator, and acts on
// what it has gathered when the deployment allows it.
//
// The signal is the leaf's view rather than an ancestor's: what a flow to this
// destination actually experienced. RTT inflation is measured against this
// group's own minimum, because two groups of different lengths are being
// compared for whether they move together rather than for which is longer.
func (c *Chain) recordCongestion(s State) {
	// The group check is a fast path rather than a correctness one: Observe
	// rejects an empty group itself, and this avoids taking the leaf's lock on
	// every report from the single-node chains that are the common case.
	if c.group == "" || len(c.nodes) == 0 {
		return
	}
	leaf := c.nodes[len(c.nodes)-1]
	leaf.mu.Lock()
	floor := leaf.knowledge.roundTrip
	leaf.mu.Unlock()
	inflation := 0.0
	if floor > 0 && s.RoundTrip > floor {
		inflation = (s.RoundTrip - floor).Seconds()
	}
	sharedCorrelator.Observe(c.group, time.Now(), Signal{
		LossRate: s.Erasure, RTTInflation: inflation,
	})
	if c.regroup {
		maybeRegroup()
	}
}

// Current is what the chain already knows, without contributing to it.
func (c *Chain) Current() State {
	if c == nil || len(c.nodes) == 0 {
		return State{}
	}
	states := make([]State, len(c.nodes))
	for i, n := range c.nodes {
		states[i] = n.Current()
	}
	return combine(states)
}

// combine reduces a root-to-leaf sequence of node states to the one a flow
// should act on.
//
// The rules differ per field because the fields mean different things along a
// path, and applying one rule to all of them is how a hierarchy becomes worse
// than no hierarchy.
//
//   - Share and Seed take the minimum. A flow may not exceed the tightest
//     segment it crosses, and the tightest is whichever that turns out to be.
//   - Erasure and BurstFactor take the maximum. Erasure accumulates along a
//     path: a leaf that has seen more than its ancestors is measuring its own
//     tail as well as the shared part, and an ancestor that has seen more than
//     a barely-measured leaf is better evidence about the part they share.
//     Sizing a code for the smaller of the two is how a flow ends up carrying
//     no parity into a channel that erases.
//   - RoundTrip takes the maximum. Each node measures the flows crossing it,
//     and a leaf traverses everything its ancestors do plus its own tail, so
//     the longest is the one that describes this flow's path.
//   - ObservedSamples takes the maximum, because it is a statement about how
//     much is known rather than a constraint.
func combine(states []State) State {
	var out State
	for _, s := range states {
		if s.Erasure > out.Erasure {
			out.Erasure = s.Erasure
		}
		if s.BurstFactor > out.BurstFactor {
			out.BurstFactor = s.BurstFactor
		}
		if s.ObservedSamples > out.ObservedSamples {
			out.ObservedSamples = s.ObservedSamples
		}
		if s.RoundTrip > out.RoundTrip {
			out.RoundTrip = s.RoundTrip
		}
		// A node that has not measured enough may not be the reason a flow is
		// capped. Without this rule the first flow to a new destination is
		// throttled by a leaf that has seen nothing, which is the failure this
		// tree exists to avoid rather than to introduce at a finer grain.
		if s.ObservedSamples < confidentSamples {
			continue
		}
		if s.Share > 0 && (out.Share == 0 || s.Share < out.Share) {
			out.Share = s.Share
		}
		if s.Seed > 0 && (out.Seed == 0 || s.Seed < out.Seed) {
			out.Seed = s.Seed
		}
	}
	if out.BurstFactor < 1 {
		out.BurstFactor = 1
	}
	// A chain that constrained nothing still seeds from whatever any node
	// knows, because a seed is not a ceiling: starting a lane from a
	// well-measured ancestor's rate is strictly better than starting it from
	// zero, even when no node is confident enough to impose a cap.
	if out.Seed == 0 {
		for _, s := range states {
			if s.Seed > 0 && (out.Seed == 0 || s.Seed < out.Seed) {
				out.Seed = s.Seed
			}
		}
	}
	return out
}

var (
	treeMu sync.Mutex
	tree   = make(map[string]*PathModel)
	// groupAlias re-parents one group onto another, which is how the evidence
	// a Correlator produces is acted on. It is separate from the node map so
	// that merging two groups does not have to move the measurements already
	// recorded under either: both names simply resolve to one node from the
	// next chain onward.
	groupAlias = make(map[string]string)
)

// MergeGroups declares that two destination groups sit behind one bottleneck,
// so that flows to either pool what they learn about the segment they share.
//
// This is the action half of the discovery the plan describes; Correlator
// produces the evidence. They are separate because the evidence is the hard
// part and applying it is a map assignment, and because a topology change
// re-parents every subsequent flow's budget -- which is a decision a caller
// should make under a policy it can be held to, not a side effect of
// measurement.
//
// Merging is transitive and idempotent: merging c into b when b is already
// merged into a puts all three under a.
func MergeGroups(a, b string) {
	if a == "" || b == "" || a == b {
		return
	}
	treeMu.Lock()
	defer treeMu.Unlock()
	rootA, rootB := resolveAliasLocked(a), resolveAliasLocked(b)
	if rootA == rootB {
		return
	}
	// The lexicographically smaller name is kept so that merging in either
	// order reaches the same tree, which a correlator reporting pairs in an
	// arbitrary order otherwise would not.
	keep, drop := rootA, rootB
	if drop < keep {
		keep, drop = drop, keep
	}
	groupAlias[drop] = keep
}

// SplitGroup undoes a merge for one group, for when the correlation that
// justified it decays.
func SplitGroup(group string) {
	treeMu.Lock()
	defer treeMu.Unlock()
	delete(groupAlias, group)
}

// resolveAliasLocked follows the alias chain to the group a name now belongs
// to. It is bounded by the chain length rather than trusted to terminate,
// because a cycle here would hang every flow rather than mis-size one.
func resolveAliasLocked(group string) string {
	for i := 0; i < 16; i++ {
		next, ok := groupAlias[group]
		if !ok || next == group {
			return group
		}
		group = next
	}
	return group
}

// GroupOf reports which group a name resolves to after merges.
func GroupOf(group string) string {
	treeMu.Lock()
	defer treeMu.Unlock()
	return resolveAliasLocked(group)
}

// SharedChain returns the chain of models a flow to this key crosses.
//
// Nodes are created on demand and shared by every flow that crosses them,
// which is the whole point: the second destination in a group inherits what
// the first measured about the segment they share.
func SharedChain(k Key) *Chain {
	return sharedChain(k, false)
}

// SharedChainRegrouping is SharedChain for a deployment that has asked for the
// tree's shape to follow the evidence rather than the static hierarchy it was
// bootstrapped from.
func SharedChainRegrouping(k Key) *Chain {
	return sharedChain(k, true)
}

func sharedChain(k Key, regroup bool) *Chain {
	group := k.Group
	if k.Group != "" {
		k.Group = GroupOf(k.Group)
	}
	keys := k.chainKeys()
	if len(keys) == 0 {
		return &Chain{}
	}
	c := &Chain{nodes: make([]*PathModel, 0, len(keys)), keys: keys,
		group: group, regroup: regroup}
	treeMu.Lock()
	defer treeMu.Unlock()
	for _, key := range keys {
		m, ok := tree[key]
		if !ok {
			m = NewPathModel()
			tree[key] = m
		}
		c.nodes = append(c.nodes, m)
	}
	return c
}

// NodeReport is one node's state, for the operator asking why a flow is being
// held where it is.
type NodeReport struct {
	Key     string
	Members int
	State   State
	// Binding reports whether this node is the one setting the chain's Share.
	// A hierarchical model that cannot say which segment is responsible is a
	// hierarchical model that cannot be debugged, and the whole reason for
	// building it was to stop assuming the answer.
	Binding bool
}

// Inspect renders the chain root-first, naming the node that binds.
func (c *Chain) Inspect() []NodeReport {
	if c == nil {
		return nil
	}
	out := make([]NodeReport, 0, len(c.nodes))
	combined := c.Current()
	for i, n := range c.nodes {
		s := n.Current()
		out = append(out, NodeReport{
			Key: c.keys[i], Members: n.Members(), State: s,
			Binding: combined.Share > 0 && s.Share == combined.Share &&
				s.ObservedSamples >= confidentSamples,
		})
	}
	return out
}

// InspectTree renders every node the process knows, sorted, for diagnostics.
func InspectTree() []NodeReport {
	treeMu.Lock()
	keys := make([]string, 0, len(tree))
	for k := range tree {
		keys = append(keys, k)
	}
	nodes := make([]*PathModel, len(keys))
	sort.Strings(keys)
	for i, k := range keys {
		nodes[i] = tree[k]
	}
	treeMu.Unlock()

	out := make([]NodeReport, 0, len(keys))
	for i, k := range keys {
		out = append(out, NodeReport{
			Key: k, Members: nodes[i].Members(), State: nodes[i].Current(),
		})
	}
	return out
}

// ForgetTree drops every node whose key begins with prefix, which is how an
// uplink change discards what was measured about the network that is gone
// without discarding what is known about destinations reached another way.
func ForgetTree(prefix string) {
	treeMu.Lock()
	defer treeMu.Unlock()
	for k := range tree {
		if prefix == "" || strings.Contains(k, prefix) {
			delete(tree, k)
		}
	}
}

// ResetTree drops every node. It exists for tests, for the same reason Reset
// does: in a process where every path is loopback, models that could not
// affect each other on a real network share one key here.
func ResetTree() {
	treeMu.Lock()
	defer treeMu.Unlock()
	tree = make(map[string]*PathModel)
	groupAlias = make(map[string]string)
}

// Model is what a consumer needs from a path: what is known, and a way to
// contribute to it.
//
// A single node and a chain of them both satisfy it, which is what lets the
// hierarchy be introduced without every consumer learning about hierarchies.
// A consumer asks what it is allowed to do and reports what it saw; whether
// the answer came from one segment or from the tightest of several is the
// model's business.
type Model interface {
	Report(Member, Observation) State
	Current() State
}

var (
	_ Model = (*PathModel)(nil)
	_ Model = (*Chain)(nil)
)

// sharedCorrelator gathers the evidence for which groups share a bottleneck.
// It is process-wide for the same reason the node map is: the question is
// about paths, not about whichever flow happened to ask.
var sharedCorrelator = NewCorrelator()

// Correlation is the coefficient above which two groups are treated as one
// segment.
//
// It is high on purpose. Merging is close to irreversible in practice -- the
// evidence that would justify splitting again is gathered under the merged
// budget, which is the budget that hides the difference -- so the bar to merge
// has to be higher than the bar to have left them apart. At 0.8 on differenced
// short-window signals, two groups have to get worse and better together
// within a fifth of a second, repeatedly.
const mergeCorrelation = 0.8

// regroupInterval bounds how often the evidence is acted on. Correlation is
// computed over ten seconds of buckets, so re-deciding faster than that reads
// the same data twice and pays for it.
const regroupInterval = 30 * time.Second

var lastRegroup atomic.Int64

// maybeRegroup applies the correlator's suggestions at a bounded cadence.
//
// It merges and does not split. Splitting on decayed correlation sounds
// symmetric and is not: once two groups share a node they share a budget, so
// the congestion signal that would distinguish them is exactly what the shared
// budget smooths away. Undoing a merge is left to SplitGroup and to an
// operator who has a reason.
func maybeRegroup() {
	now := time.Now().UnixNano()
	last := lastRegroup.Load()
	if time.Duration(now-last) < regroupInterval {
		return
	}
	if !lastRegroup.CompareAndSwap(last, now) {
		return
	}
	for _, m := range sharedCorrelator.SuggestMerges(mergeCorrelation) {
		MergeGroups(m.A, m.B)
	}
}

// SharedCorrelator exposes the gathered evidence, for an operator asking why
// two groups were joined.
func SharedCorrelator() *Correlator { return sharedCorrelator }
