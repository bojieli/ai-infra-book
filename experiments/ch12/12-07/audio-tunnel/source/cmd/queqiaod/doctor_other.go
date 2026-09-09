//go:build !linux

package main

import "github.com/bojieli/queqiao/internal/profile"

// hostChecks has nothing to report away from Linux. The setting that matters
// is a Linux sysctl, and inventing an equivalent for a platform that does not
// have one would produce a check an operator could not act on.
func hostChecks(_ profile.Profile) []check {
	return []check{{Name: "host_tuning", Status: "warn",
		Detail: "the kernel settings this profile assumes are Linux sysctls; nothing was checked here"}}
}
