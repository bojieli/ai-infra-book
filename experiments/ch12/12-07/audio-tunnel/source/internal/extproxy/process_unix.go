//go:build !windows

package extproxy

import (
	"os/exec"
	"syscall"
)

// setProcessGroup puts the launched implementation in a process group of its
// own, so the whole thing can be signalled: some of them spawn helpers.
func setProcessGroup(cmd *exec.Cmd) {
	cmd.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}
}

// terminateProcessGroup asks the group to exit, or forces it. The group is
// resolved on each call rather than once, because the process that named it
// may already have gone between the two: when it has, the signal falls back to
// the one process this harness can still name, which is a no-op if it is dead
// and the right thing if it is not.
func terminateProcessGroup(cmd *exec.Cmd, force bool) {
	signal := syscall.SIGTERM
	if force {
		signal = syscall.SIGKILL
	}
	if pgid, err := syscall.Getpgid(cmd.Process.Pid); err == nil {
		_ = syscall.Kill(-pgid, signal)
		return
	}
	if force {
		_ = cmd.Process.Kill()
		return
	}
	_ = cmd.Process.Signal(signal)
}
