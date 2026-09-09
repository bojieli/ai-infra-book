package pathseg

import (
	"strings"
	"testing"
)

// The request arrives over ssh from another machine, so it is bounded here
// rather than trusted. A far side that asked for a million probes at a
// microsecond apart would be a packet flood wearing a diagnostic's clothes.
func TestDecodeAgentRequestBoundsWhatItWasAsked(t *testing.T) {
	req, err := DecodeAgentRequest(strings.NewReader(
		`{"references":["a:443"],"count":100000,"interval_ms":0,"timeout_ms":-5,"establish_count":900}`))
	if err != nil {
		t.Fatal(err)
	}
	if req.Count != 50 {
		t.Fatalf("count %d, want the default", req.Count)
	}
	if req.IntervalMS != 100 {
		t.Fatalf("interval %d, want the default", req.IntervalMS)
	}
	if req.TimeoutMS != 2000 {
		t.Fatalf("timeout %d, want the default", req.TimeoutMS)
	}
	if req.EstablishCount != 3 {
		t.Fatalf("establish count %d, want the default", req.EstablishCount)
	}
}

func TestDecodeAgentRequestCapsTheReferenceList(t *testing.T) {
	var sb strings.Builder
	sb.WriteString(`{"references":[`)
	for i := 0; i < 40; i++ {
		if i > 0 {
			sb.WriteString(",")
		}
		sb.WriteString(`"h:443"`)
	}
	sb.WriteString(`]}`)
	req, err := DecodeAgentRequest(strings.NewReader(sb.String()))
	if err != nil {
		t.Fatal(err)
	}
	if len(req.References) != 16 {
		t.Fatalf("%d references survived the cap", len(req.References))
	}
}

func TestDecodeAgentRequestRejectsARequestWithNothingToMeasure(t *testing.T) {
	if _, err := DecodeAgentRequest(strings.NewReader(`{"count":10}`)); err == nil {
		t.Fatal("a request naming no references was accepted")
	}
	if _, err := DecodeAgentRequest(strings.NewReader(`not json`)); err == nil {
		t.Fatal("a non-JSON request was accepted")
	}
}
