//go:build !windows

package identity

import (
	"fmt"
	"os"
	"path/filepath"

	"golang.org/x/sys/unix"
)

func lockFile(path string) (func(), error) {
	file, err := os.OpenFile(path, os.O_CREATE|os.O_RDWR, 0o600)
	if err != nil {
		return nil, fmt.Errorf("open authorization lock: %w", err)
	}
	// The lock is created on first use and never removed, and beginWrite takes
	// it before reading the store. A lock left behind by a privileged run would
	// therefore refuse every later write by the service account, so give it the
	// same owner as the state directory it guards.
	if err := adoptOwnerOf(path, filepath.Dir(path)); err != nil {
		_ = file.Close()
		return nil, err
	}
	if err := unix.Flock(int(file.Fd()), unix.LOCK_EX); err != nil {
		_ = file.Close()
		return nil, fmt.Errorf("lock authorization store: %w", err)
	}
	return func() {
		_ = unix.Flock(int(file.Fd()), unix.LOCK_UN)
		_ = file.Close()
	}, nil
}
