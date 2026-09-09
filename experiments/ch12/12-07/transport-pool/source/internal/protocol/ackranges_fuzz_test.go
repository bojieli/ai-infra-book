package protocol

import "testing"

// An ACK's range list is how a peer tells the sender which bytes it may stop
// retaining. A malformed list is one thing; a well-formed list that overlaps,
// runs backwards, or reaches below what was already acknowledged cumulatively
// is the interesting case, because each of those asks the sender to release
// bytes on evidence it should not accept.
func FuzzDecodeAckRangesNeverPanics(f *testing.F) {
	encoded, err := EncodeAckRanges([][2]uint64{{10, 20}, {30, 40}})
	if err != nil {
		f.Fatal(err)
	}
	f.Add(encoded, uint64(0))
	f.Add(encoded, uint64(15))
	f.Add(make([]byte, AckRangeSize*(MaxAckRanges+1)), uint64(0))
	f.Add([]byte{1, 2, 3}, uint64(0))
	f.Add([]byte{}, ^uint64(0))
	f.Fuzz(func(t *testing.T, payload []byte, cumulative uint64) {
		ranges, err := DecodeAckRanges(payload, cumulative)
		if err != nil {
			return
		}
		if len(ranges) > MaxAckRanges {
			t.Fatalf("accepted %d ranges against a limit of %d", len(ranges), MaxAckRanges)
		}
		previous := cumulative
		for _, r := range ranges {
			if r[0] >= r[1] {
				t.Fatalf("accepted an empty or inverted range %v", r)
			}
			if r[0] < previous {
				t.Fatalf("accepted range %v starting below %d", r, previous)
			}
			previous = r[1]
		}
		// What decoded has to re-encode, because the sender's own ACKs are
		// built by the encoder and read by this decoder on the far side.
		again, err := EncodeAckRanges(ranges)
		if err != nil {
			t.Fatalf("decoded %v and could not re-encode it: %v", ranges, err)
		}
		if len(again) != len(payload) {
			t.Fatalf("re-encoding %v gave %d bytes against %d", ranges, len(again), len(payload))
		}
	})
}
