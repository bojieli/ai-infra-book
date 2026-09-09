package pep

import (
	"errors"
	"net"
	"testing"
)

// The per-platform codes are covered by TestThisPlatformsSocketCodesAreClassified,
// which reads them from this platform's sample list. What is left here is the
// part that is the same everywhere: a closed socket counts, and an ordinary
// error does not.
func TestExpectedHalfCloseError(t *testing.T) {
	if !expectedHalfCloseError(net.ErrClosed) {
		t.Fatal("a closed socket was not treated as a benign half-close")
	}
	if expectedHalfCloseError(errors.New("unrelated application error")) {
		t.Fatal("unrelated error was treated as a benign half-close")
	}
}
