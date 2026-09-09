package main

import (
	"bytes"
	"mime"
	"mime/multipart"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestBuildBodyRaw(t *testing.T) {
	dir := t.TempDir()
	p := filepath.Join(dir, "body.json")
	if err := os.WriteFile(p, []byte(`{"input":"hi"}`), 0o600); err != nil {
		t.Fatal(err)
	}
	w, err := buildBody(p, "", "application/json", nil)
	if err != nil {
		t.Fatal(err)
	}
	if got := string(w.body); got != `{"input":"hi"}` {
		t.Fatalf("body = %q, want the file verbatim", got)
	}
	if w.contentType != "application/json" {
		t.Fatalf("contentType = %q, want it left as given", w.contentType)
	}
}

// A multipart body has to be assembled the way an OpenAI-shaped audio endpoint
// expects it, because a transcription request that the server rejects measures
// nothing.
func TestBuildBodyMultipart(t *testing.T) {
	dir := t.TempDir()
	p := filepath.Join(dir, "speech.wav")
	payload := bytes.Repeat([]byte{0xAB}, 4096)
	if err := os.WriteFile(p, payload, 0o600); err != nil {
		t.Fatal(err)
	}
	w, err := buildBody(p, "file", "", []string{"model=sensevoice"})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.HasPrefix(w.contentType, "multipart/form-data") {
		t.Fatalf("contentType = %q, want multipart", w.contentType)
	}
	_, params, err := mime.ParseMediaType(w.contentType)
	if err != nil {
		t.Fatal(err)
	}
	r := multipart.NewReader(bytes.NewReader(w.body), params["boundary"])
	form, err := r.ReadForm(1 << 20)
	if err != nil {
		t.Fatal(err)
	}
	if got := form.Value["model"]; len(got) != 1 || got[0] != "sensevoice" {
		t.Fatalf("model field = %v, want [sensevoice]", got)
	}
	fh := form.File["file"]
	if len(fh) != 1 {
		t.Fatalf("file parts = %d, want 1", len(fh))
	}
	if fh[0].Size != int64(len(payload)) {
		t.Fatalf("file size = %d, want %d", fh[0].Size, len(payload))
	}
	if fh[0].Filename != "speech.wav" {
		t.Fatalf("filename = %q, want the basename", fh[0].Filename)
	}
}

func TestBuildBodyRejectsBadFormValue(t *testing.T) {
	dir := t.TempDir()
	p := filepath.Join(dir, "a.wav")
	if err := os.WriteFile(p, []byte("x"), 0o600); err != nil {
		t.Fatal(err)
	}
	if _, err := buildBody(p, "file", "", []string{"novalue"}); err == nil {
		t.Fatal("want an error for a form value with no =")
	}
}

// Percentiles are read straight off a sorted copy, and the caller must not see
// its own slice reordered.
func TestPctOfDoesNotReorderCaller(t *testing.T) {
	v := []float64{9, 1, 5}
	if got := pctOf(v, 50); got != 5 {
		t.Fatalf("p50 = %v, want 5", got)
	}
	if v[0] != 9 {
		t.Fatalf("caller slice was reordered: %v", v)
	}
	if got := pctOf(nil, 50); got != 0 {
		t.Fatalf("p50 of nothing = %v, want 0", got)
	}
}

func TestRepeatedValue(t *testing.T) {
	var r repeatedValue
	if err := r.Set("a=1"); err != nil {
		t.Fatal(err)
	}
	if err := r.Set("b=2"); err != nil {
		t.Fatal(err)
	}
	if r.String() != "a=1,b=2" {
		t.Fatalf("String() = %q, want the flags in order", r.String())
	}
}
