//go:build windows

package identity

import (
	"errors"
	"os"
)

// Windows does not expose ACLs through FileMode permission bits. Reject
// non-regular/reparse-point inputs here; installers and the user profile
// directory are responsible for their Windows DACL.
func checkPrivateDirectoryPermissions(info os.FileInfo) error {
	if !info.IsDir() || info.Mode()&os.ModeSymlink != 0 {
		return errors.New("private state is not a regular directory")
	}
	return nil
}

func checkPrivatePermissions(info os.FileInfo) error {
	if !info.Mode().IsRegular() || info.Mode()&os.ModeSymlink != 0 {
		return errors.New("private state is not a regular file")
	}
	return nil
}
