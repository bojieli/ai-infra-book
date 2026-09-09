// Package profile names the deployments this transport is known to fit, and
// carries the policy each one needs.
//
// The project's promise has always been specific: it helps when many flows
// cross one difficult segment whose behaviour has been measured. Widening that
// promise to a second regime is only honest if the second regime is stated as
// precisely as the first, with its own measurements and its own admitted
// limits -- otherwise two sharp claims become one vague one, which is how every
// general-purpose accelerator stopped being able to say who it was for.
//
// A profile is therefore a named bundle of a precondition, the measurements
// that justify it, a release level, and the policy constants that differ. It is
// deliberately not a configuration file of tunables: a deployment picks the
// deployment it is, not each knob independently, and a knob whose value is only
// correct in one regime belongs to that regime rather than to the reader.
package profile

import (
	"fmt"
	"sort"
	"strings"
	"time"

	"github.com/bojieli/queqiao/internal/classifier"
)

// Level is how much a profile has been qualified. It exists per profile rather
// than per release so that an experimental regime cannot borrow the confidence
// of a stable one by sharing a version number with it.
type Level string

const (
	// LevelSupported is the deployment the published measurements describe.
	LevelSupported Level = "supported"
	// LevelExperimental means the mechanisms run but the regime has not been
	// qualified across enough paths to claim a result.
	LevelExperimental Level = "experimental"
)

// Profile is one named deployment shape.
type Profile struct {
	Name string
	// Precondition states what must be true for this profile to apply, in a
	// form a reader can check and find false. A profile whose precondition
	// cannot fail is not a precondition.
	Precondition string
	// Evidence names the characterisation document that justifies the
	// constants below. A profile without one has not earned them.
	Evidence string
	Level    Level
	// Classifier is the flow classification policy. It differs between regimes
	// because what counts as bulk differs: on a shared access link, bulk is
	// whatever would starve an interactive flow, and on a datacenter leg
	// carrying only requests there is no bulk to protect anything from.
	Classifier classifier.Config
	// HierarchicalPath models the path as a chain of segments -- the uplink,
	// then the peer -- rather than as one endpoint pair, and lets a flow do
	// only what the tighter segment permits.
	//
	// It is off for the access-link profile because that deployment has one
	// peer, so the two models are identical by construction and the extra node
	// would measure nothing while changing the numbers the published results
	// were taken with.
	HierarchicalPath bool
	// DiscoverGrouping lets the tree's shape follow measured evidence instead
	// of the static hierarchy it starts from: groups whose congestion arrives
	// and leaves together are merged into one segment.
	//
	// It requires HierarchicalPath, and it is off by default even there.
	// Merging re-parents the budget of every flow that follows, and it is
	// close to irreversible in practice, because the evidence that would
	// justify splitting again is gathered under the shared budget that hides
	// the difference.
	DiscoverGrouping bool
	// ClassHints declare what a flow is from what produced it, before any of
	// it has been carried.
	//
	// The classifier needs about a second of traffic to decide, and a request
	// that finishes in 200ms spends its whole life inside that second. A hint
	// removes the window rather than shortening it.
	//
	// Each entry matches a substring of the identity the capture agent
	// reported -- the executable path, the pod UID, the container, the systemd
	// unit -- and names the class a flow from it starts in. First match wins,
	// so order them most specific first.
	//
	// A hint is a starting point and not a promise. Once a flow is running the
	// classifier judges it on what it actually does, so a process declared
	// interactive that turns out to be moving a checkpoint is still demoted.
	ClassHints []ClassHint
}

// ClassHint maps something the capture agent knows to the class a flow from it
// begins in.
type ClassHint struct {
	// Match is a substring of the reported identity. Substring rather than a
	// pattern language because the thing being matched is a path or an
	// identifier, and every deployment that needed more than this would need
	// something different.
	Match string
	// Class is "interactive" or "bulk". Anything else is a configuration
	// error rather than a default, since a misspelling that silently did
	// nothing would be indistinguishable from a rule that never matched.
	Class string
}

// HintedClass returns the class declared for an identity, and whether one was.
func (p Profile) HintedClass(identity string) (classifier.Class, bool) {
	if identity == "" {
		return 0, false
	}
	for _, h := range p.ClassHints {
		if h.Match == "" || !strings.Contains(identity, h.Match) {
			continue
		}
		switch h.Class {
		case "interactive":
			return classifier.ClassInteractive, true
		case "bulk":
			return classifier.ClassBulk, true
		}
	}
	return 0, false
}

// ValidateHints reports a hint naming a class that does not exist, so a
// misspelling fails at startup rather than quietly matching nothing.
func (p Profile) ValidateHints() error {
	for i, h := range p.ClassHints {
		if strings.TrimSpace(h.Match) == "" {
			return fmt.Errorf("class hint %d has an empty match", i)
		}
		if h.Class != "interactive" && h.Class != "bulk" {
			return fmt.Errorf("class hint %d for %q names class %q; want interactive or bulk",
				i, h.Match, h.Class)
		}
	}
	return nil
}

// wanSharedBottleneck is the deployment this project was built for and the one
// its published results describe: a client and a trusted gateway whose shared
// segment is the dominant bottleneck for every flow crossing it.
func wanSharedBottleneck() Profile {
	return Profile{
		Name: "wan-shared-bottleneck",
		Precondition: "many application flows share one client-to-gateway " +
			"segment, and that segment is the dominant bottleneck for all of them",
		Evidence:   "docs/PATH-CHARACTER-20260813.md",
		Level:      LevelSupported,
		Classifier: classifier.DefaultConfig(),
	}
}

// dcLongHaul is a long leg between two hosts the same operator runs, carrying
// request/response traffic whose payloads are hundreds of kilobytes.
//
// Two things differ from the access-link case and both follow from the same
// observation: there is no bulk traffic here to protect anything from. Every
// flow is a latency-critical burst, so a classifier that demotes the largest
// of them is not protecting an interactive flow, it is penalising the only
// kind of flow present. Measured on the China-US datacenter path, that
// demotion cost a factor of two on repeated megabyte requests while every
// other case gained between five and seventeen times.
func dcLongHaul() Profile {
	c := classifier.DefaultConfig()
	// Bulk has to mean something different here, and the thresholds have to say
	// what.
	//
	// On an access link, 128KB is a reasonable place to start suspecting that a
	// flow will starve an interactive one, because the link is small. On a
	// datacenter leg, 128KB is one ordinary request. Bulk on this profile is a
	// checkpoint pull or a model download -- tens of megabytes, sustained over
	// many seconds -- and the thresholds are set so that a five-megabyte
	// inference request cannot be mistaken for one.
	c.BulkBytes = 32 << 20
	c.BulkMinimumAge = 10 * time.Second
	// Thresholds alone would still latch on a long-lived connection that has
	// carried enough requests to add up. A request that goes quiet between
	// bursts is a caller waiting on a response, whatever its running total, so
	// an observed idle disqualifies the flow permanently. On the access-link
	// profile the veto stays off: there a slow bulk transfer still needs to
	// unlock lanes, and its slowness is the path's doing rather than the
	// application's.
	c.BulkIdleGapVeto = 1 * time.Second
	// Two episodes rather than one. A single stall is an event; two is a
	// pattern, and only the pattern says this flow is a caller rather than a
	// transfer. With one, a checkpoint pull that paused once inside its first
	// 32MB spent the rest of its life classified interactive: coded, and
	// holding a single lane. The margin protecting the case this veto exists
	// for is unaffected, because a session of request-sized exchanges reaches
	// the byte floor after roughly ninety of them and produces its second
	// episode on the second one.
	c.BulkIdleGapVetoEpisodes = 2
	return Profile{
		Name:             "dc-long-haul",
		HierarchicalPath: true,
		DiscoverGrouping: true,
		Precondition: "both endpoints are operated by the same party, the leg " +
			"between them is long, and every flow on it is a latency-critical " +
			"request rather than a transfer seeking throughput",
		Evidence:   "docs/PATH-CHARACTER-DC-20260826.md",
		Level:      LevelExperimental,
		Classifier: c,
	}
}

var all = map[string]func() Profile{
	"wan-shared-bottleneck": wanSharedBottleneck,
	"dc-long-haul":          dcLongHaul,
}

// Default is the profile a deployment gets when it does not choose, and it is
// the one whose measurements are published. A new regime must be asked for.
func Default() Profile { return wanSharedBottleneck() }

// ByName resolves a profile, listing the alternatives when it cannot. An
// unknown profile is an error rather than a fallback to the default: silently
// running a different policy than the operator named is the failure this
// package exists to prevent.
func ByName(name string) (Profile, error) {
	if strings.TrimSpace(name) == "" {
		return Default(), nil
	}
	f, ok := all[name]
	if !ok {
		return Profile{}, fmt.Errorf("unknown profile %q; known profiles are %s",
			name, strings.Join(Names(), ", "))
	}
	return f(), nil
}

// Names lists every profile, sorted, for help text and error messages.
func Names() []string {
	out := make([]string, 0, len(all))
	for k := range all {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

// ParseClassHints reads hints from the repeatable command-line form,
// "<match>=<class>", where class is interactive or bulk.
//
// The separator is the last "=" rather than the first, because the match is
// usually an identity fragment that contains one: "path=/app/voice" is the
// common case and splitting on the first would leave a match of "path" and a
// class of "/app/voice=interactive".
func ParseClassHints(specs []string) ([]ClassHint, error) {
	out := make([]ClassHint, 0, len(specs))
	for _, spec := range specs {
		i := strings.LastIndex(spec, "=")
		if i <= 0 || i == len(spec)-1 {
			return nil, fmt.Errorf("class hint %q: want <match>=<interactive|bulk>", spec)
		}
		h := ClassHint{Match: strings.TrimSpace(spec[:i]), Class: strings.TrimSpace(spec[i+1:])}
		out = append(out, h)
	}
	p := Profile{ClassHints: out}
	if err := p.ValidateHints(); err != nil {
		return nil, err
	}
	return out, nil
}
