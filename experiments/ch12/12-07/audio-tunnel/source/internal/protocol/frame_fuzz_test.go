package protocol

import (
	"bytes"
	"testing"
)

func FuzzDecodeHeaderNeverPanics(f *testing.F) {
	seed := make([]byte, HeaderSize)
	seed[0], seed[1], seed[2], seed[3] = Magic0, Magic1, Version, byte(TypeData)
	f.Add(seed)
	f.Add([]byte("malformed"))
	f.Fuzz(func(t *testing.T, data []byte) {
		_, _ = DecodeHeader(data)
	})
}

func FuzzReadFrameIsBounded(f *testing.F) {
	seed := make([]byte, HeaderSize+3)
	seed[0], seed[1], seed[2], seed[3] = Magic0, Magic1, Version, byte(TypeData)
	seed[38], seed[39], seed[40], seed[41] = 0, 0, 0, 3
	f.Add(seed)
	f.Fuzz(func(t *testing.T, data []byte) {
		_, _ = ReadFrame(bytes.NewReader(data))
	})
}
