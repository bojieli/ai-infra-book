//go:build linux

package main

import (
	"fmt"

	"github.com/bojieli/queqiao/internal/profile"
)

// hostChecks reports the kernel settings the measurements assumed.
//
// tcp_slow_start_after_idle is the one that matters most and it is the one
// nothing else will tell you about. Linux defaults it to 1, which throws the
// congestion window away after any idle gap longer than a retransmission
// timeout, so a connection held open across a pause is open without being
// warm. Measured on the path this profile was built for, a 300KB burst on an
// idle connection took 941ms with the default and 209ms without it, and a real
// speech upload went from 789.9ms to 241ms.
//
// It is reported rather than recommended, because it helps in one direction and
// hurts in the other. On a direction that erases, restoring the window hands
// the controller more in flight for a multiplicative decrease to take away: the
// same synthesis download measured 827.7ms cold and 2281.2ms warm with this set.
// A local check cannot know which direction carries the caller's bytes, so it
// says what the setting is and what it does, and leaves the choice where the
// traffic is known.
func hostChecks(p profile.Profile) []check {
	out := make([]check, 0, 2)
	if value, err := readSysctl("net/ipv4/tcp_slow_start_after_idle"); err != nil {
		out = append(out, check{Name: "tcp_slow_start_after_idle", Status: "warn", Detail: err.Error()})
	} else if value == "0" {
		out = append(out, check{Name: "tcp_slow_start_after_idle", Status: "pass",
			Detail: "0, so a held-open connection keeps its window across a pause. That is " +
				"worth 4.5x on a burst into a clean direction, and costs 2.8x on one that " +
				"erases, so confirm which way your traffic goes"})
	} else {
		out = append(out, check{Name: "tcp_slow_start_after_idle", Status: "warn",
			Detail: "1, the kernel default. Every idle gap past an RTO throws the congestion " +
				"window away, so a connection held open across a pause is open without being " +
				"warm. Setting it to 0 was worth 4.5x on a burst into a clean direction; on a " +
				"direction that erases it made a download 2.8x slower, so set it for the " +
				"direction your traffic actually sends into"})
	}
	if value, err := readSysctl("net/ipv4/tcp_congestion_control"); err == nil {
		out = append(out, check{Name: "tcp_congestion_control", Status: "pass",
			Detail: fmt.Sprintf("%s, for traffic that does not go through the tunnel", value)})
	}
	return out
}
