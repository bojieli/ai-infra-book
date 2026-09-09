package tcpinfo

import (
	"encoding/binary"
	"testing"
)

// buildInfo lays out a struct tcp_info the way the kernel does, so the test
// exercises the offset table against a known encoding rather than against
// itself. A test that built the bytes by calling Parse's own constants could
// not fail if every offset were wrong by the same amount.
func buildInfo(set func(b []byte)) []byte {
	b := make([]byte, wantLen)
	set(b)
	return b
}

func TestParseReadsEachFieldFromItsKernelOffset(t *testing.T) {
	b := buildInfo(func(b []byte) {
		b[0] = 1                                           // state ESTABLISHED
		b[1] = 3                                           // ca_state recovery
		b[7] = 0x1                                         // delivery_rate_app_limited
		binary.LittleEndian.PutUint32(b[16:], 1448)        // snd_mss
		binary.LittleEndian.PutUint32(b[24:], 42)          // unacked
		binary.LittleEndian.PutUint32(b[68:], 200_000)     // rtt us
		binary.LittleEndian.PutUint32(b[80:], 223)         // snd_cwnd
		binary.LittleEndian.PutUint32(b[100:], 909)        // total_retrans
		binary.LittleEndian.PutUint32(b[148:], 185_900)    // min_rtt us
		binary.LittleEndian.PutUint64(b[104:], 12_500_000) // pacing_rate
		binary.LittleEndian.PutUint64(b[160:], 9_800_000)  // delivery_rate
		binary.LittleEndian.PutUint64(b[176:], 77)         // rwnd_limited
		binary.LittleEndian.PutUint64(b[208:], 1_316_232)  // bytes_retrans
		binary.LittleEndian.PutUint32(b[228:], 65535)      // snd_wnd
	})
	got := Parse(b)

	for _, c := range []struct {
		name string
		got  uint64
		want uint64
	}{
		{"state", uint64(got.State), 1},
		{"ca_state", uint64(got.CAState), 3},
		{"snd_mss", uint64(got.SndMSS), 1448},
		{"unacked", uint64(got.Unacked), 42},
		{"rtt", uint64(got.RTT), 200_000},
		{"snd_cwnd", uint64(got.SndCwnd), 223},
		{"total_retrans", uint64(got.TotalRetrans), 909},
		{"min_rtt", uint64(got.MinRTT), 185_900},
		{"pacing_rate", got.PacingRate, 12_500_000},
		{"delivery_rate", got.DeliveryRate, 9_800_000},
		{"rwnd_limited", got.RwndLimited, 77},
		{"bytes_retrans", got.BytesRetrans, 1_316_232},
		{"snd_wnd", uint64(got.SndWnd), 65535},
	} {
		if c.got != c.want {
			t.Errorf("%s = %d, want %d", c.name, c.got, c.want)
		}
	}
	if !got.AppLimited {
		t.Error("app_limited not read from bit 0 of byte 7")
	}
}

// The app-limited bit shares its byte with fastopen_client_fail. Reading the
// whole byte instead of the low bit would make any fastopen failure look like
// an application-limited sample, which is the one flag this project's rate
// estimates must not get wrong.
func TestAppLimitedIgnoresItsNeighbourBits(t *testing.T) {
	notLimited := Parse(buildInfo(func(b []byte) { b[7] = 0x6 }))
	if notLimited.AppLimited {
		t.Error("fastopen_client_fail bits were read as app_limited")
	}
	limited := Parse(buildInfo(func(b []byte) { b[7] = 0x7 }))
	if !limited.AppLimited {
		t.Error("app_limited missed when neighbour bits are also set")
	}
}

// An older kernel returns a shorter struct. Parse must report the fields it
// has rather than refusing, because the fields present are the reason for
// asking and a hard failure here would make the tool useless on exactly the
// hosts whose paths are hardest to measure.
func TestParseTruncatedKeepsWhatIsPresent(t *testing.T) {
	full := buildInfo(func(b []byte) {
		binary.LittleEndian.PutUint32(b[80:], 223)
		binary.LittleEndian.PutUint64(b[160:], 9_800_000)
	})
	short := Parse(full[:104]) // stops before pacing_rate
	if short.SndCwnd != 223 {
		t.Errorf("cwnd = %d, want 223 from a truncated buffer", short.SndCwnd)
	}
	if short.DeliveryRate != 0 {
		t.Errorf("delivery_rate = %d, want 0 when absent", short.DeliveryRate)
	}
	if short.Truncated != 104 {
		t.Errorf("Truncated = %d, want 104", short.Truncated)
	}
}

func TestBytesInFlightAndCwndUseTheSameUnits(t *testing.T) {
	i := Parse(buildInfo(func(b []byte) {
		binary.LittleEndian.PutUint32(b[16:], 1448)
		binary.LittleEndian.PutUint32(b[24:], 10)
		binary.LittleEndian.PutUint32(b[80:], 100)
	}))
	if got, want := i.BytesInFlight(), uint64(14480); got != want {
		t.Errorf("BytesInFlight = %d, want %d", got, want)
	}
	if got, want := i.CwndBytes(), uint64(144800); got != want {
		t.Errorf("CwndBytes = %d, want %d", got, want)
	}
}

// Limiter is the summary every phase gate reads, so each branch is pinned.
// The ordering matters: a connection can be both application limited and
// nearly cwnd-limited, and reporting the window in that case would blame the
// transport for an application that had nothing to send.
func TestLimiterNamesTheBindingConstraint(t *testing.T) {
	base := func(f func(b []byte)) Info {
		return Parse(buildInfo(func(b []byte) {
			binary.LittleEndian.PutUint32(b[16:], 1448)
			f(b)
		}))
	}
	prev := Info{}

	rwnd := base(func(b []byte) { binary.LittleEndian.PutUint64(b[176:], 5) })
	if got := rwnd.Limiter(prev); got != "receiver-window" {
		t.Errorf("rwnd-limited reported as %q", got)
	}

	sndbuf := base(func(b []byte) { binary.LittleEndian.PutUint64(b[184:], 5) })
	if got := sndbuf.Limiter(prev); got != "send-buffer" {
		t.Errorf("sndbuf-limited reported as %q", got)
	}

	app := base(func(b []byte) {
		b[7] = 0x1
		binary.LittleEndian.PutUint32(b[24:], 100) // also looks cwnd-limited
		binary.LittleEndian.PutUint32(b[80:], 100)
	})
	if got := app.Limiter(prev); got != "application" {
		t.Errorf("an application-limited sample that also fills its window reported as %q, want application", got)
	}

	cwnd := base(func(b []byte) {
		binary.LittleEndian.PutUint32(b[24:], 100)
		binary.LittleEndian.PutUint32(b[80:], 100)
	})
	if got := cwnd.Limiter(prev); got != "congestion-window" {
		t.Errorf("cwnd-limited reported as %q", got)
	}

	idle := base(func(b []byte) {
		binary.LittleEndian.PutUint32(b[24:], 1)
		binary.LittleEndian.PutUint32(b[80:], 100)
	})
	if got := idle.Limiter(prev); got != "unattributed" {
		t.Errorf("an unconstrained sample reported as %q", got)
	}
}

// A cumulative counter that has not moved since the previous sample says
// nothing about this interval. Reading the absolute value instead of the
// increment would report every connection that was ever receiver-limited as
// receiver-limited forever.
func TestLimiterUsesIncrementsNotTotals(t *testing.T) {
	prev := Parse(buildInfo(func(b []byte) { binary.LittleEndian.PutUint64(b[176:], 500) }))
	now := Parse(buildInfo(func(b []byte) {
		binary.LittleEndian.PutUint32(b[16:], 1448)
		binary.LittleEndian.PutUint64(b[176:], 500) // unchanged
		binary.LittleEndian.PutUint32(b[24:], 100)
		binary.LittleEndian.PutUint32(b[80:], 100)
	}))
	if got := now.Limiter(prev); got != "congestion-window" {
		t.Errorf("a stale rwnd total was read as this interval's constraint: %q", got)
	}
}
