//go:build !race

package pep

// raceDetectorEnabled reports whether this binary carries race instrumentation.
// See the //go:build race file for why a test scales a budget by it.
const raceDetectorEnabled = false
