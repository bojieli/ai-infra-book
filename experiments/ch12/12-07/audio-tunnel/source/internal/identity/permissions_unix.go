//go:build !windows

package identity

import (
	"fmt"
	"os"
)

func checkPrivateDirectoryPermissions(info os.FileInfo) error {
	if !info.IsDir() || info.Mode().Perm()&0o077 != 0 {
		return fmt.Errorf("permissions are %s; want a directory with mode 700 or stricter (run chmod 700 on it)", info.Mode())
	}
	return nil
}

func checkPrivatePermissions(info os.FileInfo) error {
	if !info.Mode().IsRegular() || info.Mode().Perm()&0o077 != 0 {
		return fmt.Errorf("permissions are %s; want a regular file mode 600 or stricter", info.Mode())
	}
	return nil
}
