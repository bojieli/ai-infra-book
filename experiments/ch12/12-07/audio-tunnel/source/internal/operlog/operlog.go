// Package operlog provides queqiaod's bounded, durable operational log.
package operlog

import (
	"errors"
	"fmt"
	"io"
	"log/slog"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
)

const (
	DefaultMaxSizeBytes = int64(32 * 1024 * 1024)
	DefaultMaxBackups   = 5
	DisabledPath        = "none"
)

// Config describes one process-wide operational log. Path may be "auto" to
// select the platform location or "none" to explicitly use the console only.
type Config struct {
	Role       string
	Path       string
	Level      string
	Format     string
	Console    io.Writer
	MaxBytes   int64
	MaxBackups int
}

// Sink owns the file behind a Logger. Close it only after all goroutines that
// can log have stopped.
type Sink struct {
	path   string
	writer *rotatingWriter
}

func (s *Sink) Path() string { return s.path }

func (s *Sink) Close() error {
	if s == nil || s.writer == nil {
		return nil
	}
	return s.writer.Close()
}

// ResolvePath turns an operator value into the absolute file actually used.
func ResolvePath(value, role string) (string, error) {
	if value == DisabledPath {
		return "", nil
	}
	if value == "" || value == "auto" {
		return DefaultPath(role)
	}
	if value == "~" || strings.HasPrefix(value, "~/") || strings.HasPrefix(value, `~\`) {
		home, err := os.UserHomeDir()
		if err != nil {
			return "", fmt.Errorf("locate home directory: %w", err)
		}
		value = filepath.Join(home, strings.TrimLeft(value[1:], `/\`))
	}
	resolved, err := filepath.Abs(value)
	if err != nil {
		return "", fmt.Errorf("resolve log path: %w", err)
	}
	return filepath.Clean(resolved), nil
}

// DefaultPath returns a stable per-user path. Production system services set
// an explicit /var/log path because their service account and write policy are
// deployment decisions, while an interactive process must work unprivileged.
func DefaultPath(role string) (string, error) {
	if override := os.Getenv("QUEQIAO_LOG_DIR"); override != "" {
		return defaultPathAt(override, role)
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("locate home directory for logs: %w", err)
	}
	var directory string
	switch runtime.GOOS {
	case "darwin":
		directory = filepath.Join(home, "Library", "Logs", "Queqiao")
	case "windows":
		directory = os.Getenv("LOCALAPPDATA")
		if directory == "" {
			directory = filepath.Join(home, "AppData", "Local")
		}
		directory = filepath.Join(directory, "Queqiao", "Logs")
	default:
		directory = os.Getenv("XDG_STATE_HOME")
		if directory == "" {
			directory = filepath.Join(home, ".local", "state")
		}
		directory = filepath.Join(directory, "queqiao")
	}
	return defaultPathAt(directory, role)
}

func defaultPathAt(directory, role string) (string, error) {
	switch role {
	case "client", "server":
	default:
		return "", fmt.Errorf("unsupported log role %q", role)
	}
	resolved, err := filepath.Abs(directory)
	if err != nil {
		return "", fmt.Errorf("resolve log directory: %w", err)
	}
	return filepath.Join(resolved, role+".log"), nil
}

// Open constructs a structured logger that writes each record once to the
// rotating file and optionally once to a console/journal stream.
func Open(config Config) (*slog.Logger, *Sink, error) {
	path, err := ResolvePath(config.Path, config.Role)
	if err != nil {
		return nil, nil, err
	}
	level, err := parseLevel(config.Level)
	if err != nil {
		return nil, nil, err
	}
	if config.Format != "json" && config.Format != "text" {
		return nil, nil, fmt.Errorf("unsupported log format %q; want json or text", config.Format)
	}
	if config.MaxBytes <= 0 {
		return nil, nil, errors.New("log maximum size must be positive")
	}
	if config.MaxBackups < 0 || config.MaxBackups > 100 {
		return nil, nil, errors.New("log maximum backups must be between 0 and 100")
	}

	var fileWriter *rotatingWriter
	writers := make([]io.Writer, 0, 2)
	if config.Console != nil {
		writers = append(writers, config.Console)
	}
	if path != "" {
		fileWriter, err = openRotating(path, config.MaxBytes, config.MaxBackups)
		if err != nil {
			return nil, nil, err
		}
		writers = append(writers, fileWriter)
	}
	if len(writers) == 0 {
		return nil, nil, errors.New("file logging is disabled and no console log is enabled")
	}
	output := writers[0]
	if len(writers) > 1 {
		output = io.MultiWriter(writers...)
	}
	options := &slog.HandlerOptions{Level: level}
	var handler slog.Handler
	if config.Format == "json" {
		handler = slog.NewJSONHandler(output, options)
	} else {
		handler = slog.NewTextHandler(output, options)
	}
	logger := slog.New(handler).With("service", "queqiaod", "role", config.Role, "pid", os.Getpid())
	return logger, &Sink{path: path, writer: fileWriter}, nil
}

func parseLevel(value string) (slog.Level, error) {
	switch strings.ToLower(value) {
	case "debug":
		return slog.LevelDebug, nil
	case "info":
		return slog.LevelInfo, nil
	case "warn", "warning":
		return slog.LevelWarn, nil
	case "error":
		return slog.LevelError, nil
	default:
		return 0, fmt.Errorf("unsupported log level %q", value)
	}
}

type rotatingWriter struct {
	mu         sync.Mutex
	path       string
	maxBytes   int64
	maxBackups int
	file       *os.File
	size       int64
	closed     bool
}

func openRotating(path string, maxBytes int64, maxBackups int) (*rotatingWriter, error) {
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return nil, fmt.Errorf("create log directory %q: %w", filepath.Dir(path), err)
	}
	w := &rotatingWriter{path: path, maxBytes: maxBytes, maxBackups: maxBackups}
	if err := w.openFile(); err != nil {
		return nil, err
	}
	return w, nil
}

func (w *rotatingWriter) openFile() error {
	file, err := os.OpenFile(w.path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o600)
	if err != nil {
		return fmt.Errorf("open runtime log %q: %w", w.path, err)
	}
	if err := file.Chmod(0o600); err != nil {
		_ = file.Close()
		return fmt.Errorf("secure runtime log %q: %w", w.path, err)
	}
	info, err := file.Stat()
	if err != nil {
		_ = file.Close()
		return fmt.Errorf("inspect runtime log %q: %w", w.path, err)
	}
	w.file, w.size = file, info.Size()
	return nil
}

func (w *rotatingWriter) Write(payload []byte) (int, error) {
	w.mu.Lock()
	defer w.mu.Unlock()
	if w.closed || w.file == nil {
		return 0, os.ErrClosed
	}
	if w.size > 0 && w.size+int64(len(payload)) > w.maxBytes {
		if err := w.rotate(); err != nil {
			return 0, err
		}
	}
	n, err := w.file.Write(payload)
	w.size += int64(n)
	return n, err
}

func (w *rotatingWriter) rotate() error {
	if err := errors.Join(w.file.Sync(), w.file.Close()); err != nil {
		_ = w.openFile()
		return fmt.Errorf("flush runtime log before rotation: %w", err)
	}
	w.file = nil
	if w.maxBackups == 0 {
		if err := os.Remove(w.path); err != nil && !errors.Is(err, os.ErrNotExist) {
			_ = w.openFile()
			return fmt.Errorf("remove full runtime log: %w", err)
		}
	} else {
		oldest := fmt.Sprintf("%s.%d", w.path, w.maxBackups)
		if err := os.Remove(oldest); err != nil && !errors.Is(err, os.ErrNotExist) {
			_ = w.openFile()
			return fmt.Errorf("remove oldest runtime log: %w", err)
		}
		for index := w.maxBackups - 1; index >= 1; index-- {
			from := fmt.Sprintf("%s.%d", w.path, index)
			to := fmt.Sprintf("%s.%d", w.path, index+1)
			if err := os.Rename(from, to); err != nil && !errors.Is(err, os.ErrNotExist) {
				_ = w.openFile()
				return fmt.Errorf("shift runtime log backup: %w", err)
			}
		}
		if err := os.Rename(w.path, w.path+".1"); err != nil && !errors.Is(err, os.ErrNotExist) {
			_ = w.openFile()
			return fmt.Errorf("rotate runtime log: %w", err)
		}
	}
	if err := w.openFile(); err != nil {
		return err
	}
	w.size = 0
	return nil
}

func (w *rotatingWriter) Close() error {
	w.mu.Lock()
	defer w.mu.Unlock()
	if w.closed {
		return nil
	}
	w.closed = true
	if w.file == nil {
		return nil
	}
	err := errors.Join(w.file.Sync(), w.file.Close())
	w.file = nil
	return err
}
