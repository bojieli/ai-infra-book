package operlog

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

func TestOpenWritesStructuredFileAndConsole(t *testing.T) {
	directory := t.TempDir()
	path := filepath.Join(directory, "nested", "client.log")
	var console bytes.Buffer
	logger, sink, err := Open(Config{
		Role: "client", Path: path, Level: "info", Format: "json", Console: &console,
		MaxBytes: 1024 * 1024, MaxBackups: 2,
	})
	if err != nil {
		t.Fatal(err)
	}
	logger.Info("runtime logging initialized", "answer", 42)
	if err := sink.Close(); err != nil {
		t.Fatal(err)
	}
	payload, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if string(payload) != console.String() {
		t.Fatalf("file and console differ:\nfile=%s\nconsole=%s", payload, console.String())
	}
	var record map[string]any
	if err := json.Unmarshal(bytes.TrimSpace(payload), &record); err != nil {
		t.Fatal(err)
	}
	if record["service"] != "queqiaod" || record["role"] != "client" || record["msg"] != "runtime logging initialized" || record["answer"] != float64(42) {
		t.Fatalf("unexpected structured record: %#v", record)
	}
	if runtime.GOOS != "windows" {
		info, err := os.Stat(path)
		if err != nil {
			t.Fatal(err)
		}
		if info.Mode().Perm() != 0o600 {
			t.Fatalf("log mode = %o, want 600", info.Mode().Perm())
		}
	}
}

func TestRotationBoundsFilesAndPreservesNewestRecords(t *testing.T) {
	path := filepath.Join(t.TempDir(), "server.log")
	logger, sink, err := Open(Config{Role: "server", Path: path, Level: "info", Format: "text", MaxBytes: 220, MaxBackups: 2})
	if err != nil {
		t.Fatal(err)
	}
	for index := 0; index < 30; index++ {
		logger.Info("rotation record", "index", index, "padding", strings.Repeat("x", 40))
	}
	if err := sink.Close(); err != nil {
		t.Fatal(err)
	}
	for _, candidate := range []string{path, path + ".1", path + ".2"} {
		if _, err := os.Stat(candidate); err != nil {
			t.Fatalf("expected bounded log %s: %v", candidate, err)
		}
	}
	if _, err := os.Stat(path + ".3"); !os.IsNotExist(err) {
		t.Fatalf("unexpected backup beyond retention: %v", err)
	}
	current, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Contains(current, []byte("index=29")) {
		t.Fatalf("current log does not contain newest record: %s", current)
	}
}

func TestDefaultPathCanBeMadeDeterministic(t *testing.T) {
	directory := t.TempDir()
	t.Setenv("QUEQIAO_LOG_DIR", directory)
	for _, role := range []string{"client", "server"} {
		path, err := DefaultPath(role)
		if err != nil {
			t.Fatal(err)
		}
		if path != filepath.Join(directory, role+".log") {
			t.Fatalf("%s path = %q", role, path)
		}
	}
}

func TestInvalidLoggingConfigurationIsRejected(t *testing.T) {
	for _, config := range []Config{
		{Role: "client", Path: DisabledPath, Level: "info", Format: "json", MaxBytes: 1, MaxBackups: 1},
		{Role: "client", Path: "auto", Level: "verbose", Format: "json", MaxBytes: 1, MaxBackups: 1},
		{Role: "client", Path: "auto", Level: "info", Format: "xml", MaxBytes: 1, MaxBackups: 1},
		{Role: "client", Path: "auto", Level: "info", Format: "json", MaxBytes: 0, MaxBackups: 1},
	} {
		if _, _, err := Open(config); err == nil {
			t.Fatalf("invalid config accepted: %+v", config)
		}
	}
}
