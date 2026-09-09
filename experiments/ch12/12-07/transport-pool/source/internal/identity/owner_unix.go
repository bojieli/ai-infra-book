//go:build !windows

package identity

import (
	"fmt"
	"os"
	"path/filepath"
	"syscall"
)

// adoptOwnerOf gives path the ownership that reference already carries, or the
// ownership of reference's directory when reference does not exist yet.
//
// Private state is installed by renaming a freshly created file over the
// target, so the installed file is always a new inode owned by whoever ran the
// process. The gateway runs as a dedicated service account while provider
// maintenance runs from an administrator's shell, and Refresh is documented to
// adopt changes written by those separate CLI processes. Without this step a
// single privileged `queqiaod provider add-user` hands authorization.json to
// root, and the gateway - which re-reads it once a second and on every
// enrollment - can no longer open its own state. Callers restore the mode
// themselves; only ownership needs carrying across the replace.
func adoptOwnerOf(path, reference string) error {
	// Only a privileged process can write into another account's 0700 state
	// directory, so only a privileged process can perform this transfer. An
	// unprivileged run already creates files as the account that owns the
	// directory, and would fail these chown calls with EPERM.
	if os.Geteuid() != 0 {
		return nil
	}
	uid, gid, ok, err := ownerOf(reference)
	if err != nil || !ok {
		return err
	}
	info, err := os.Stat(path)
	if err != nil {
		return fmt.Errorf("inspect state file ownership: %w", err)
	}
	if stat, ok := info.Sys().(*syscall.Stat_t); ok && int(stat.Uid) == uid && int(stat.Gid) == gid {
		return nil
	}
	if err := os.Chown(path, uid, gid); err != nil {
		return fmt.Errorf("preserve state ownership uid %d gid %d: %w", uid, gid, err)
	}
	return nil
}

// ownerOf reports the uid and gid that private state beside reference should
// carry, falling back to the containing directory when reference is absent.
// The final boolean is false on platforms that do not expose POSIX ownership.
func ownerOf(reference string) (int, int, bool, error) {
	info, err := os.Lstat(reference)
	if err != nil {
		if !os.IsNotExist(err) {
			return 0, 0, false, fmt.Errorf("inspect state ownership: %w", err)
		}
		if info, err = os.Stat(filepath.Dir(reference)); err != nil {
			return 0, 0, false, fmt.Errorf("inspect state directory ownership: %w", err)
		}
	}
	stat, ok := info.Sys().(*syscall.Stat_t)
	if !ok {
		return 0, 0, false, nil
	}
	return int(stat.Uid), int(stat.Gid), true, nil
}
