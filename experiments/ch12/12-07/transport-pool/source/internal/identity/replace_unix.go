//go:build !windows

package identity

import "os"

func replaceFile(source, destination string) error { return os.Rename(source, destination) }
