//go:build race

package pep

// raceDetectorEnabled reports whether this binary carries race instrumentation.
//
// It exists so a test can scale a wall-clock budget instead of skipping. Race
// instrumentation costs several times the CPU per operation, and these tests
// drive emulated paths whose deadlines are wall-clock: on the two-core hosted
// Windows runner internal/fec alone took 1,338 s under -race against 66 s
// without it. A budget that is generous untimed can be far too tight there.
const raceDetectorEnabled = true
