//go:build windows

package identity

// Windows does not express access through POSIX ownership. A file created in
// the state directory inherits that directory's DACL, which the installer and
// the service account own, so there is nothing to carry across a replace.
func adoptOwnerOf(path, reference string) error { return nil }
