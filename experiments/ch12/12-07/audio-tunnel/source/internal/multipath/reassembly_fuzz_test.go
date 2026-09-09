package multipath

import (
	"testing"
)

func FuzzReassemblerNeverPanics(f *testing.F) {
	f.Add(uint64(0), []byte("abc"), false)
	f.Add(uint64(3), []byte(nil), true)
	f.Fuzz(func(t *testing.T, sequence uint64, payload []byte, final bool) {
		r := NewReassembler(Config{MaxBufferedBytes: 1 << 16, MaxBufferedFrames: 64})
		if len(payload) > 1<<16 {
			payload = payload[:1<<16]
		}
		_, _, _ = r.Insert(Segment{Sequence: sequence, Payload: payload, Final: final})
	})
}
