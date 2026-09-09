package mobilecore

import (
	"testing"
	"time"
)

func TestProfileProbeTimeoutBounds(t *testing.T) {
	for _, test := range []struct {
		name         string
		milliseconds int64
		want         time.Duration
		wantError    bool
	}{
		{name: "default", milliseconds: 0, want: 10 * time.Second},
		{name: "minimum", milliseconds: 1_000, want: time.Second},
		{name: "maximum", milliseconds: 30_000, want: 30 * time.Second},
		{name: "below minimum", milliseconds: 999, wantError: true},
		{name: "above maximum", milliseconds: 30_001, wantError: true},
		{name: "negative", milliseconds: -1, wantError: true},
		{name: "overflow input", milliseconds: int64(^uint64(0) >> 1), wantError: true},
	} {
		t.Run(test.name, func(t *testing.T) {
			got, err := profileProbeTimeout(test.milliseconds)
			if test.wantError {
				if err == nil {
					t.Fatalf("profileProbeTimeout(%d) unexpectedly succeeded", test.milliseconds)
				}
				return
			}
			if err != nil {
				t.Fatal(err)
			}
			if got != test.want {
				t.Fatalf("profileProbeTimeout(%d) = %v, want %v", test.milliseconds, got, test.want)
			}
		})
	}
}
