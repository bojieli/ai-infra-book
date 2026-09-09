//go:build windows

package extproxy

import (
	"os/exec"
	"strconv"
	"syscall"
)

// setProcessGroup asks Windows for a new process group. There is no Setpgid
// here; this flag is what makes the launched implementation and its helpers
// addressable as a tree rather than as one process.
func setProcessGroup(cmd *exec.Cmd) {
	cmd.SysProcAttr = &syscall.SysProcAttr{CreationFlags: syscall.CREATE_NEW_PROCESS_GROUP}
}

// terminateProcessGroup kills the tree through taskkill, because Windows has
// no signal a process group can be asked to exit on and Go's own Kill reaches
// only the process it started. Leaving a helper behind is the failure this
// guards against: it holds the port and contaminates every later trial.
//
// If taskkill is unavailable the harness still stops the one process it named,
// which is weaker than the Unix path and is the reason this is documented
// rather than presented as equivalent.
func terminateProcessGroup(cmd *exec.Cmd, force bool) {
	args := []string{"/PID", strconv.Itoa(cmd.Process.Pid), "/T"}
	if force {
		args = append(args, "/F")
	}
	if err := exec.Command("taskkill", args...).Run(); err == nil {
		return
	}
	if force {
		_ = cmd.Process.Kill()
	}
}
