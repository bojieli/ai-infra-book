package identity

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

// A refresh that finds no change still read the file. Treating only a change
// as evidence of a readable store would report every quiet gateway as one
// that had lost its authorization state.
func TestLastGoodAtAdvancesOnAnUnchangedRefresh(t *testing.T) {
	provider := testProvider(t, "127.0.0.1:443", time.Now())
	store := provider.Store
	first := store.LastGoodAt()
	if first.IsZero() {
		t.Fatal("a freshly initialized store reports it has never been read")
	}
	time.Sleep(10 * time.Millisecond)
	changed, err := store.Refresh()
	if err != nil {
		t.Fatal(err)
	}
	if changed {
		t.Fatal("an untouched store reported a change")
	}
	if !store.LastGoodAt().After(first) {
		t.Fatal("an unchanged but successful read did not count as a read")
	}
}

// The point of the timestamp: while the store cannot be read, the snapshot in
// force keeps getting older, and that has to be observable. Before this, a
// gateway three days into an outage was indistinguishable from one that had
// missed a single tick.
func TestLastGoodAtHoldsWhileRefreshFails(t *testing.T) {
	provider := testProvider(t, "127.0.0.1:443", time.Now())
	store := provider.Store
	account, err := store.AddAccount("alice", time.Time{}, AccountLimits{}, time.Now())
	if err != nil {
		t.Fatal(err)
	}
	lastGood := store.LastGoodAt()
	if err := os.Remove(filepath.Join(provider.Directory, authorizationFile)); err != nil {
		t.Fatal(err)
	}
	for i := 0; i < 3; i++ {
		if _, err := store.Refresh(); err == nil {
			t.Fatal("refresh succeeded against a removed store")
		}
	}
	if got := store.LastGoodAt(); !got.Equal(lastGood) {
		t.Fatalf("a failed refresh moved the last-good mark from %s to %s", lastGood, got)
	}
	// The previous snapshot must still be in force; that is what makes the
	// outage invisible to established devices and worth reporting.
	if found, ok := store.FindAccount(account.ID); !ok || !found.Enabled {
		t.Fatal("a failed refresh disarmed the last known-good state")
	}
}

// Recovery has to move the mark again, or a store that started working would
// still look stale forever.
func TestLastGoodAtAdvancesAgainAfterRecovery(t *testing.T) {
	provider := testProvider(t, "127.0.0.1:443", time.Now())
	store := provider.Store
	path := filepath.Join(provider.Directory, authorizationFile)
	saved, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	lastGood := store.LastGoodAt()
	if err := os.Remove(path); err != nil {
		t.Fatal(err)
	}
	if _, err := store.Refresh(); err == nil {
		t.Fatal("refresh succeeded against a removed store")
	}
	time.Sleep(10 * time.Millisecond)
	if err := os.WriteFile(path, saved, 0o600); err != nil {
		t.Fatal(err)
	}
	if _, err := store.Refresh(); err != nil {
		t.Fatal(err)
	}
	if !store.LastGoodAt().After(lastGood) {
		t.Fatal("the last-good mark did not advance after the store became readable again")
	}
}
