package main

import (
	"os"
	"path/filepath"
	"runtime"
	"testing"
)

func TestReadLock(t *testing.T) {
	lock := filepath.Join(t.TempDir(), "runtime.lock")
	content := "# reviewed\nexample.com/module@v1.2.3|MIT|https://example.com/module\n"
	if err := os.WriteFile(lock, []byte(content), 0o600); err != nil {
		t.Fatal(err)
	}
	items, err := readLock(lock)
	if err != nil {
		t.Fatal(err)
	}
	if len(items) != 1 || items[0].reference != "example.com/module@v1.2.3" || items[0].license != "MIT" {
		t.Fatalf("unexpected parsed lock: %#v", items)
	}
}

func TestReadLockRejectsMalformedAndEmptyFiles(t *testing.T) {
	for name, content := range map[string]string{
		"empty":     "# no dependencies\n",
		"fields":    "example.com/module@v1|MIT\n",
		"reference": "example.com/module|MIT|https://example.com\n",
		"source":    "example.com/module@v1|MIT|http://example.com\n",
	} {
		t.Run(name, func(t *testing.T) {
			lock := filepath.Join(t.TempDir(), "runtime.lock")
			if err := os.WriteFile(lock, []byte(content), 0o600); err != nil {
				t.Fatal(err)
			}
			if _, err := readLock(lock); err == nil {
				t.Fatal("malformed lock was accepted")
			}
		})
	}
}

func TestWriteAtomicReplacesContentAndMode(t *testing.T) {
	output := filepath.Join(t.TempDir(), "legal", "notices.txt")
	if err := writeAtomic(output, []byte("first")); err != nil {
		t.Fatal(err)
	}
	if err := writeAtomic(output, []byte("second")); err != nil {
		t.Fatal(err)
	}
	content, err := os.ReadFile(output)
	if err != nil {
		t.Fatal(err)
	}
	if string(content) != "second" {
		t.Fatalf("notice content = %q", content)
	}
	info, err := os.Stat(output)
	if err != nil {
		t.Fatal(err)
	}
	// Windows does not expose Unix permission bits through os.Stat. Content
	// replacement is still covered there; the archive validator checks the
	// shipped notice mode independently for every release target.
	if runtime.GOOS != "windows" && info.Mode().Perm() != 0o644 {
		t.Fatalf("notice mode = %o", info.Mode().Perm())
	}
}
