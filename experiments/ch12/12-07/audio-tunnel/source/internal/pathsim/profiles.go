package pathsim

import "time"

// Named configurations for the paths this project has characterised.
//
// A test that hand-writes a delay and a loss rate is testing whatever the
// author guessed. These are the measured figures, with the document that
// produced them named beside each, so a test that fails against one is failing
// against a path that exists.

// DCLongHaul is the China-US datacenter path of
// docs/PATH-CHARACTER-DC-20260826.md.
//
// Its defining feature is the asymmetry: 14% memoryless erasure downstream and
// nothing at all upstream, at a 200ms round trip with no capacity constraint
// until 333 Mbit/s. That combination is what makes it a coding path rather
// than a congestion one -- the loss carries no information about the rate, so
// backing off cannot relieve it, and the return channel that would carry a
// retransmission request is clean.
func DCLongHaul() Config {
	return Config{
		OneWayDelay: 100 * time.Millisecond,
		// The measured spread was 199-207ms with an mdev of 0.58ms at one
		// packet per second, which is a path doing no queueing at all.
		DelayJitter: 3 * time.Millisecond,
		LossRate:    0.14,
		// Zero of 41,663 datagrams were lost upstream at 50 Mbit/s.
		UpstreamClean: true,
		// Measured burst factor 1.00-1.03 across three decades of offered
		// rate: the loss is independent, which is the whole reason a code
		// repairs it cheaply.
		LossBurstPackets: 1,
		// The delivered knee was 333 Mbit/s; below it, delivery scaled
		// linearly with offered rate.
		RateBytesPerSec: 333 * 1000 * 1000 / 8,
		MTU:             1500,
		Seed:            20260826,
	}
}

// DCLongHaulClean is the same path with the erasure removed, for separating
// what a change does about loss from what it does about a long round trip.
func DCLongHaulClean() Config {
	c := DCLongHaul()
	c.LossRate = 0
	return c
}

// WANAccessLink is the hotel-Wi-Fi case of docs/PATH-CHARACTER-20260813.md:
// the deployment this project was built for, where erasure is far heavier and
// the capacity far smaller.
func WANAccessLink() Config {
	return Config{
		OneWayDelay:      90 * time.Millisecond,
		DelayJitter:      10 * time.Millisecond,
		LossRate:         0.42,
		LossBurstPackets: 1.8,
		RateBytesPerSec:  14 * 1000 * 1000 / 8,
		MTU:              1500,
		Seed:             20260813,
	}
}
