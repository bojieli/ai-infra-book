//go:build !windows

package identity

import (
	"os"
	"path/filepath"
	"syscall"
	"testing"
	"time"
)

// A uid/gid pair that need not resolve to a real account: chown accepts bare
// numeric ids, which keeps the test independent of the host's user database.
const (
	testStateUID = 12345
	testStateGID = 12345
)

func requireRoot(t *testing.T) {
	t.Helper()
	if os.Geteuid() != 0 {
		t.Skip("ownership preservation is only observable when running as root")
	}
}

func ownerOfPath(t *testing.T, path string) (int, int) {
	t.Helper()
	info, err := os.Lstat(path)
	if err != nil {
		t.Fatal(err)
	}
	stat, ok := info.Sys().(*syscall.Stat_t)
	if !ok {
		t.Fatalf("no POSIX ownership for %s", path)
	}
	return int(stat.Uid), int(stat.Gid)
}

// A privileged provider command must not move the authorization store out of
// reach of the unprivileged gateway that reads it.
func TestWriteFileAtomicPreservesExistingOwner(t *testing.T) {
	requireRoot(t)
	path := filepath.Join(t.TempDir(), authorizationFile)
	if err := os.WriteFile(path, []byte("original\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := os.Chown(path, testStateUID, testStateGID); err != nil {
		t.Fatal(err)
	}
	if err := writeFileAtomic(path, []byte("replacement\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	uid, gid := ownerOfPath(t, path)
	if uid != testStateUID || gid != testStateGID {
		t.Fatalf("replace transferred the state file to uid %d gid %d", uid, gid)
	}
	info, err := os.Lstat(path)
	if err != nil {
		t.Fatal(err)
	}
	if info.Mode().Perm() != 0o600 {
		t.Fatalf("mode is %s; want 0600", info.Mode())
	}
	data, err := os.ReadFile(path)
	if err != nil || string(data) != "replacement\n" {
		t.Fatalf("contents are %q (err %v)", data, err)
	}
}

// A file created for the first time follows the directory it lives in, so a
// privileged init against an already-provisioned state directory stays usable.
func TestWriteFileAtomicAdoptsDirectoryOwnerForNewFile(t *testing.T) {
	requireRoot(t)
	directory := filepath.Join(t.TempDir(), "provider")
	if err := os.Mkdir(directory, 0o700); err != nil {
		t.Fatal(err)
	}
	if err := os.Chown(directory, testStateUID, testStateGID); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(directory, authorizationFile)
	if err := writeFileAtomic(path, []byte("{}\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	if uid, gid := ownerOfPath(t, path); uid != testStateUID || gid != testStateGID {
		t.Fatalf("new state file is owned by uid %d gid %d", uid, gid)
	}
}

// beginWrite takes the lock before it reads the store, and the lock is never
// removed, so a lock left behind by a privileged run would refuse every later
// write by the service account.
func TestLockFilePreservesDirectoryOwner(t *testing.T) {
	requireRoot(t)
	directory := filepath.Join(t.TempDir(), "provider")
	if err := os.Mkdir(directory, 0o700); err != nil {
		t.Fatal(err)
	}
	if err := os.Chown(directory, testStateUID, testStateGID); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(directory, authorizationFile+".lock")
	unlock, err := lockFile(path)
	if err != nil {
		t.Fatal(err)
	}
	unlock()
	if uid, gid := ownerOfPath(t, path); uid != testStateUID || gid != testStateGID {
		t.Fatalf("authorization lock is owned by uid %d gid %d", uid, gid)
	}
}

// The whole mixed-ownership sequence the gateway actually runs: an
// unprivileged service account provisions the state, a privileged
// administrator adds a user, and the service account must still be able to
// read and write what it owns.
func TestProviderMutationUnderRootKeepsStateReadableByOwner(t *testing.T) {
	requireRoot(t)
	now := time.Now()
	directory := filepath.Join(t.TempDir(), "provider")
	provider, err := InitProvider(directory, "Example Provider", "127.0.0.1:443", now)
	if err != nil {
		t.Fatal(err)
	}
	entries, err := os.ReadDir(directory)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.Chown(directory, testStateUID, testStateGID); err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		if err := os.Chown(filepath.Join(directory, entry.Name()), testStateUID, testStateGID); err != nil {
			t.Fatal(err)
		}
	}
	if _, err := provider.Store.AddAccount("alice", time.Time{}, AccountLimits{}, now); err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		name := entry.Name()
		if uid, gid := ownerOfPath(t, filepath.Join(directory, name)); uid != testStateUID || gid != testStateGID {
			t.Fatalf("%s is owned by uid %d gid %d after a privileged mutation", name, uid, gid)
		}
	}
}

// Unprivileged runs cannot cross accounts in a 0700 directory, so the helper
// stays out of the way rather than failing a chown it is not allowed to make.
func TestAdoptOwnerOfIsInertWithoutPrivilege(t *testing.T) {
	if os.Geteuid() == 0 {
		t.Skip("running as root; the privileged paths are covered elsewhere")
	}
	directory := t.TempDir()
	path := filepath.Join(directory, authorizationFile)
	if err := os.WriteFile(path, []byte("{}\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := adoptOwnerOf(path, directory); err != nil {
		t.Fatalf("unprivileged adoption returned %v", err)
	}
	if uid, gid := ownerOfPath(t, path); uid != os.Geteuid() || gid != os.Getegid() {
		t.Fatalf("unprivileged adoption changed ownership to uid %d gid %d", uid, gid)
	}
}
