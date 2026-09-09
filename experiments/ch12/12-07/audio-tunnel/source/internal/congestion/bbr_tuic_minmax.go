package congestion

import (
	"time"

	"github.com/apernet/quic-go/monotime"
)

// tuicMinMax is the constant-space, three-sample max filter used by TUIC's
// quinn-congestions BBR implementation, with one correction.
//
// The original clock is a packet-timed round number rather than wall time,
// which makes the filter insensitive to ACK coalescing and gives it a bounded
// ten-round memory. That is the right clock while rounds advance. It stops
// being a clock when they do not.
//
// A round advances when a packet sent in the previous round is acknowledged,
// so a connection with nothing to send advances no rounds. Measured on a live
// gateway, 99.98% of samples were application limited and the round counter
// moved 220 times in 24 hours -- about nine an hour, which turns a ten-round
// memory into sixty-six minutes of wall time. One burst through a token bucket
// therefore latched the bandwidth estimate for the better part of an hour: the
// gateway held 519 Mbit/s against a measured sustained 17.6, and paced and
// sized its congestion window from that.
//
// The filter now expires a sample on rounds or on wall time, whichever comes
// first. The two express the same intent -- a bandwidth estimate should not
// outlive the window in which a path change ought to be believed -- and the
// time bound is what keeps the round bound honest when rounds stall.
//
// Expiry is driven by arriving samples rather than by reading the estimate: a
// sample that has outlived its window is replaced by the next one, and get
// returns what is stored. A lane that carried a burst and then went silent
// therefore keeps its figure until it sends again. That is harmless for the
// lane, whose estimate only governs what it puts on the wire, but it is not
// harmless for a trace: queqiao_quic_controller_max_bandwidth_bytes_per_second
// folds the maximum across lanes, so one idle lane can report a peak the path
// has not sustained for minutes. Reading the metric as the path's bandwidth is
// the same mistake this filter was fixed for, one level up.
type tuicMinMax struct {
	window uint64
	// timeWindow is how long a sample may stand in wall time. It is derived
	// from the measured round trip rather than configured, because "ten
	// rounds" and "the time ten rounds takes" are the same statement on a path
	// whose rounds are advancing; see setRoundTrip.
	timeWindow time.Duration
	samples    [3]tuicMinMaxSample
}

type tuicMinMaxSample struct {
	round uint64
	at    monotime.Time
	value uint64
}

const (
	// tuicMinMaxWindow is the filter's memory in rounds. It is untyped so that
	// deriving a duration from it needs no conversion from the uint64 the
	// round arithmetic uses.
	tuicMinMaxWindow = 10
	// minBandwidthTimeWindow keeps a spuriously small round-trip sample from
	// collapsing the filter's memory to nothing. Below this the round window
	// binds first in any case, because samples cannot arrive faster than the
	// path returns them.
	minBandwidthTimeWindow = time.Second
	// maxBandwidthTimeWindow bounds the worst case on a very long path. It is
	// the same figure, and the same reasoning, as pathmodel's bottleneck
	// window: long enough to survive a probe cycle, short enough that a path
	// which genuinely narrowed is believed within a few seconds.
	maxBandwidthTimeWindow = 10 * time.Second
)

func newTUICMinMax() tuicMinMax {
	return tuicMinMax{window: tuicMinMaxWindow, timeWindow: maxBandwidthTimeWindow}
}

func (m *tuicMinMax) get() uint64 { return m.samples[0].value }

func (m *tuicMinMax) reset() {
	m.samples = [3]tuicMinMaxSample{}
}

// setRoundTrip derives the wall-clock memory from the path's measured minimum
// round trip: the time the filter's own round window would take to pass if
// rounds were advancing normally.
//
// Deriving it rather than configuring it is what keeps the correction honest
// on paths nobody has measured yet. A 226 ms path gets 2.3 seconds, a
// millisecond LAN gets the one-second floor and never notices because its
// rounds advance far faster than that, and a satellite path is held to the ten
// second ceiling rather than being allowed to remember a burst for a minute.
func (m *tuicMinMax) setRoundTrip(rtt time.Duration) {
	if rtt <= 0 {
		return
	}
	// Clamp before multiplying rather than after. The round trip is a
	// measurement, and a large enough one overflows the product before either
	// bound could be applied to it -- which would set the memory from a sign
	// bit instead of from the path.
	if rtt >= maxBandwidthTimeWindow/tuicMinMaxWindow {
		m.timeWindow = maxBandwidthTimeWindow
		return
	}
	window := tuicMinMaxWindow * rtt
	if window < minBandwidthTimeWindow {
		window = minBandwidthTimeWindow
	}
	m.timeWindow = window
}

// stale reports whether the standing estimate has outlived its wall-clock
// window.
//
// The bandwidth sampler asks before deciding whether an application-limited
// sample may be recorded. Ordinarily it may not lower the estimate -- a sender
// that had nothing to send has learned nothing about what the path could have
// carried -- but that rule assumes there is a live estimate to protect. Once
// the standing one has expired there is nothing to protect, and refusing the
// only samples on offer would leave the filter holding a value it has already
// decided not to trust, or empty it and collapse the connection.
func (m *tuicMinMax) stale(now monotime.Time) bool {
	if m.samples[0].value == 0 {
		return false
	}
	return m.expired(m.samples[0], now)
}

func (m *tuicMinMax) expired(sample tuicMinMaxSample, now monotime.Time) bool {
	if sample.at.IsZero() || now.IsZero() || m.timeWindow <= 0 {
		return false
	}
	return now.Sub(sample.at) > m.timeWindow
}

func (m *tuicMinMax) updateMax(round uint64, now monotime.Time, value uint64) {
	if value == 0 {
		return
	}
	current := tuicMinMaxSample{round: round, at: now, value: value}
	oldest := m.samples[2]
	// A round counter is monotonic in normal operation. The explicit round
	// comparison also makes the filter safe if a test or a timeout resets it.
	windowExpired := round >= oldest.round && round-oldest.round > m.window
	// The wall-clock test is against the standing estimate rather than the
	// oldest sample: it is the estimate that is being trusted, and it is the
	// one that outlived its window on the live path.
	if m.samples[0].value == 0 || value >= m.samples[0].value || windowExpired || m.expired(m.samples[0], now) {
		m.samples = [3]tuicMinMaxSample{current, current, current}
		return
	}
	if value >= m.samples[1].value {
		m.samples[2] = current
		m.samples[1] = current
	} else if value >= m.samples[2].value {
		m.samples[2] = current
	}
	m.subWindowUpdate(current)
}

func (m *tuicMinMax) subWindowUpdate(sample tuicMinMaxSample) {
	if sample.round < m.samples[0].round {
		return
	}
	delta := sample.round - m.samples[0].round
	if delta > m.window {
		m.samples[0] = m.samples[1]
		m.samples[1] = m.samples[2]
		m.samples[2] = sample
		if sample.round >= m.samples[0].round && sample.round-m.samples[0].round > m.window {
			m.samples[0] = m.samples[1]
			m.samples[1] = m.samples[2]
			m.samples[2] = sample
		}
	} else if m.samples[1].value == m.samples[0].value &&
		sample.round >= m.samples[1].round && sample.round-m.samples[1].round > m.window/4 {
		m.samples[2] = sample
		m.samples[1] = sample
	} else if m.samples[2].value == m.samples[1].value &&
		sample.round >= m.samples[2].round && sample.round-m.samples[2].round > m.window/2 {
		m.samples[2] = sample
	}
}
