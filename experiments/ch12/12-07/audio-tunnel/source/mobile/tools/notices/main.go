// Command notices creates the exact third-party notice file embedded in both
// mobile applications. It has no third-party dependencies of its own.
package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

type moduleInfo struct {
	Dir string
}

type dependency struct {
	reference string
	license   string
	source    string
}

func main() {
	coreDir := flag.String("core", "", "mobile core module directory")
	lockFile := flag.String("lock", "", "reviewed runtime dependency lock")
	outputFile := flag.String("output", "", "notice file to write")
	flag.Parse()
	if *coreDir == "" || *lockFile == "" || *outputFile == "" || flag.NArg() != 0 {
		fatal(errors.New("usage: notices -core DIR -lock FILE -output FILE"))
	}

	dependencies, err := readLock(*lockFile)
	if err != nil {
		fatal(err)
	}
	var output bytes.Buffer
	fmt.Fprintln(&output, "QUEQIAO MOBILE THIRD-PARTY NOTICES")
	fmt.Fprintln(&output)
	fmt.Fprintln(&output, "This file is generated from mobile/runtime-dependencies.lock.")
	fmt.Fprintln(&output, "The following modules are linked into the mobile core. Queqiao itself is MIT licensed.")
	for _, item := range dependencies {
		licenseText, err := readModuleLicense(*coreDir, item.reference)
		if err != nil {
			fatal(err)
		}
		fmt.Fprintln(&output)
		fmt.Fprintln(&output, "================================================================================")
		fmt.Fprintf(&output, "%s\nLicense: %s\nSource: %s\n", item.reference, item.license, item.source)
		fmt.Fprintln(&output, "--------------------------------------------------------------------------------")
		output.Write(bytes.TrimSpace(licenseText))
		fmt.Fprintln(&output)
	}
	if err := writeAtomic(*outputFile, output.Bytes()); err != nil {
		fatal(err)
	}
}

func readLock(name string) ([]dependency, error) {
	file, err := os.Open(name)
	if err != nil {
		return nil, err
	}
	defer file.Close()
	var result []dependency
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		fields := strings.Split(line, "|")
		if len(fields) != 3 || !strings.Contains(fields[0], "@") || !strings.HasPrefix(fields[2], "https://") {
			return nil, fmt.Errorf("invalid dependency lock entry %q", line)
		}
		result = append(result, dependency{reference: fields[0], license: fields[1], source: fields[2]})
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	if len(result) == 0 {
		return nil, errors.New("dependency lock is empty")
	}
	return result, nil
}

func readModuleLicense(coreDir, reference string) ([]byte, error) {
	command := exec.Command("go", "list", "-m", "-json", reference)
	command.Dir = coreDir
	raw, err := command.Output()
	if err != nil {
		return nil, fmt.Errorf("locate %s: %w", reference, err)
	}
	var info moduleInfo
	if err := json.Unmarshal(raw, &info); err != nil {
		return nil, fmt.Errorf("decode module directory for %s: %w", reference, err)
	}
	if info.Dir == "" {
		return nil, fmt.Errorf("module directory for %s is empty", reference)
	}
	matches, err := filepath.Glob(filepath.Join(info.Dir, "LICENSE*"))
	if err != nil || len(matches) != 1 {
		return nil, fmt.Errorf("%s must have exactly one top-level LICENSE file", reference)
	}
	content, err := os.ReadFile(matches[0])
	if err != nil {
		return nil, fmt.Errorf("read license for %s: %w", reference, err)
	}
	return content, nil
}

func writeAtomic(name string, content []byte) error {
	directory := filepath.Dir(name)
	if err := os.MkdirAll(directory, 0o755); err != nil {
		return err
	}
	temporary, err := os.CreateTemp(directory, ".third-party-notices.*")
	if err != nil {
		return err
	}
	temporaryName := temporary.Name()
	defer os.Remove(temporaryName)
	if err := temporary.Chmod(0o644); err != nil {
		temporary.Close()
		return err
	}
	if _, err := temporary.Write(content); err != nil {
		temporary.Close()
		return err
	}
	if err := temporary.Sync(); err != nil {
		temporary.Close()
		return err
	}
	if err := temporary.Close(); err != nil {
		return err
	}
	return os.Rename(temporaryName, name)
}

func fatal(err error) {
	fmt.Fprintln(os.Stderr, "notices:", err)
	os.Exit(1)
}
