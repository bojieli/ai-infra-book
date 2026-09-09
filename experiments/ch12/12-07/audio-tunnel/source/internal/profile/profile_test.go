package profile

import (
	"strings"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/classifier"
)

// The default must stay the profile whose published measurements describe it.
// A deployment that does not choose gets the behaviour the README claims, and
// changing that silently would invalidate every result in the comparison table.
func TestDefaultIsTheSupportedAccessLinkProfile(t *testing.T) {
	d := Default()
	if d.Name != "wan-shared-bottleneck" {
		t.Fatalf("default profile is %q", d.Name)
	}
	if d.Level != LevelSupported {
		t.Errorf("default profile level is %q, want supported", d.Level)
	}
	if d.Classifier != classifier.DefaultConfig() {
		t.Error("default profile does not carry the documented classifier config")
	}
}

// An unknown name must fail. Falling back to the default would run a different
// policy than the operator asked for, and nothing in the logs would say so --
// which is the precise failure this package exists to prevent.
func TestUnknownProfileIsRefusedAndListsTheAlternatives(t *testing.T) {
	_, err := ByName("dc-longhaul") // plausible typo
	if err == nil {
		t.Fatal("an unknown profile name was accepted")
	}
	for _, want := range Names() {
		if !strings.Contains(err.Error(), want) {
			t.Errorf("error does not mention known profile %q: %v", want, err)
		}
	}
}

func TestEmptyNameSelectsTheDefault(t *testing.T) {
	p, err := ByName("")
	if err != nil {
		t.Fatalf("empty name rejected: %v", err)
	}
	if p.Name != Default().Name {
		t.Errorf("empty name gave %q", p.Name)
	}
}

// Every profile has to state a precondition a reader can find false, and name
// the measurements that justify its constants. A profile without either is a
// set of tuned numbers with no argument behind them, which is what the
// admission rule exists to keep out.
func TestEveryProfileStatesItsPreconditionAndEvidence(t *testing.T) {
	for _, name := range Names() {
		p, err := ByName(name)
		if err != nil {
			t.Fatalf("%s: %v", name, err)
		}
		if len(p.Precondition) < 40 {
			t.Errorf("%s: precondition is too thin to falsify: %q", name, p.Precondition)
		}
		if !strings.HasPrefix(p.Evidence, "docs/") {
			t.Errorf("%s: evidence %q does not name a characterisation document", name, p.Evidence)
		}
		if p.Classifier.BulkBytes == 0 || p.Classifier.NewBytes == 0 {
			t.Errorf("%s: incomplete classifier config would silently fall back", name)
		}
	}
}

// The datacenter profile's whole purpose is that one request is not a
// transfer. If its threshold ever drops back to the access-link value, the
// regression this profile was created to fix returns.
func TestDatacenterProfileDoesNotCallOneRequestBulk(t *testing.T) {
	p, err := ByName("dc-long-haul")
	if err != nil {
		t.Fatal(err)
	}
	if p.Level != LevelExperimental {
		t.Errorf("dc-long-haul level is %q; it has been qualified on one path", p.Level)
	}
	if p.Classifier.BulkBytes <= 8<<20 {
		t.Errorf("BulkBytes is %d: a multi-megabyte request would classify as a transfer",
			p.Classifier.BulkBytes)
	}
	if p.Classifier.BulkIdleGapVeto == 0 {
		t.Error("the idle veto is off, so repeated requests can still accumulate into bulk")
	}
	if classifier.DefaultConfig().BulkIdleGapVeto != 0 {
		t.Error("the veto leaked into the access-link default, changing published behaviour")
	}
}

// The access-link profile must keep the flat model. Its published results were
// measured on it, and on a deployment with one peer the tree adds a node that
// measures nothing while changing the numbers.
func TestOnlyTheDatacenterProfileUsesTheHierarchy(t *testing.T) {
	if Default().HierarchicalPath {
		t.Error("the default profile enabled the hierarchical path model")
	}
	dc, err := ByName("dc-long-haul")
	if err != nil {
		t.Fatal(err)
	}
	if !dc.HierarchicalPath {
		t.Error("the datacenter profile did not enable the hierarchical path model")
	}
}

// Discovering the grouping needs a hierarchy to rearrange, so a profile that
// asks for one without the other is a configuration that cannot do what it
// says.
func TestGroupingDiscoveryRequiresAHierarchy(t *testing.T) {
	for _, name := range Names() {
		p, err := ByName(name)
		if err != nil {
			t.Fatal(err)
		}
		if p.DiscoverGrouping && !p.HierarchicalPath {
			t.Errorf("%s discovers grouping without a hierarchy to apply it to", name)
		}
	}
	if Default().DiscoverGrouping {
		t.Error("the default profile rearranges its own tree")
	}
}

// The command-line form has to survive the match containing an "=", which the
// common case does: "path=/app/voice" is an identity fragment, not a
// key-value pair this parser should split on.
func TestParseClassHintsSplitsOnTheLastSeparator(t *testing.T) {
	got, err := ParseClassHints([]string{
		"path=/app/checkpoint-sync=bulk",
		"path=/app/=interactive",
		"unit=voice.service=interactive",
	})
	if err != nil {
		t.Fatal(err)
	}
	want := []ClassHint{
		{Match: "path=/app/checkpoint-sync", Class: "bulk"},
		{Match: "path=/app/", Class: "interactive"},
		{Match: "unit=voice.service", Class: "interactive"},
	}
	if len(got) != len(want) {
		t.Fatalf("parsed %d hints, want %d: %+v", len(got), len(want), got)
	}
	for i := range want {
		if got[i] != want[i] {
			t.Errorf("hint %d = %+v, want %+v", i, got[i], want[i])
		}
	}
	// Order is preserved, because first match wins and the operator ordered them.
	p := Profile{ClassHints: got}
	if c, ok := p.HintedClass("path=/app/checkpoint-sync pod=x"); !ok || c.String() != "bulk" {
		t.Errorf("the specific rule did not win: %v %v", c, ok)
	}
}

func TestParseClassHintsRejectsNonsense(t *testing.T) {
	for _, bad := range []string{"", "=bulk", "path=/app/=", "path=/app/=nonsense", "noseparator"} {
		if _, err := ParseClassHints([]string{bad}); err == nil {
			t.Errorf("accepted %q", bad)
		}
	}
}

// The classifier's own tests build the datacenter config by hand, because that
// package cannot import this one. That copy silently went stale through one
// change already: a field was added here and those tests kept passing against
// the old value, so the shipping profile was never the thing under test.
//
// This asserts behaviour rather than a field list, because a field list goes
// stale the same way. Each case is a workload this profile is expected to
// carry, run through the classifier the profile actually ships.
func TestDatacenterProfileMatchesWhatItsTestsAssume(t *testing.T) {
	p, err := ByName("dc-long-haul")
	if err != nil {
		t.Fatal(err)
	}

	// The case that was wrong: one pause inside the first BulkBytes
	// disqualified a transfer permanently.
	t.Run("a transfer that stalls once is still a transfer", func(t *testing.T) {
		c := classifier.New(p.Classifier)
		var got uint64
		age := 11 * time.Second
		var cls classifier.Class
		for i := range 60 {
			got += 4 << 20
			age += time.Second
			since := 5 * time.Millisecond
			if i == 2 {
				since = 1500 * time.Millisecond
			}
			cls = c.Observe(classifier.Observation{
				BytesDown: got, DownRate: 100 << 20,
				Age: age, SinceLastPayload: since,
			})
		}
		if cls != classifier.ClassBulk {
			t.Fatalf("a 240MB pull that paused once at 12MB classified %v, want bulk. "+
				"Interactive here means coded and one lane, for the whole transfer.", cls)
		}
	})

	// The case the veto exists for. Every exchange is a burst and then a wait,
	// and no number of them may add up to a transfer.
	t.Run("a session of requests never adds up to a transfer", func(t *testing.T) {
		c := classifier.New(p.Classifier)
		o := classifier.Observation{Age: 2 * time.Second, UpRate: 20 << 20, Bidirectional: true}
		for i := range 120 {
			o.BytesUp += 1 << 20
			o.Age += 2 * time.Second
			o.SinceLastPayload = 10 * time.Millisecond
			if got := c.Observe(o); got == classifier.ClassBulk {
				t.Fatalf("exchange %d classified bulk at %d bytes", i, o.BytesUp)
			}
			o.SinceLastPayload = 2 * time.Second
			if got := c.Observe(o); got == classifier.ClassBulk {
				t.Fatalf("exchange %d classified bulk while the caller waited", i)
			}
		}
	})

	// A model streaming tokens: too fast to look idle, too slow to look like a
	// transfer. The recent-rate test is the only thing separating the two.
	t.Run("a token stream is interactive", func(t *testing.T) {
		c := classifier.New(p.Classifier)
		o := classifier.Observation{
			BytesUp: 1 << 10, Age: 4 * time.Second, SinceLastPayload: 30 * time.Millisecond,
			DownRate: 800, Bidirectional: true, SmallBidirectionalBursts: true,
		}
		var cls classifier.Class
		for range 30 {
			o.BytesDown += 800
			o.Age += time.Second
			cls = c.Observe(o)
		}
		if cls != classifier.ClassInteractive {
			t.Fatalf("a token stream classified %v, want interactive", cls)
		}
	})
}
