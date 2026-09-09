// Command queqiaopack builds the distributable queqiaod archives.
//
// It deliberately owns archive creation instead of delegating it to the host's
// tar and zip programs. That gives every file a fixed timestamp, owner, mode,
// and order, so identical source and metadata produce identical artifacts.
package main

import (
	"archive/tar"
	"archive/zip"
	"compress/gzip"
	"context"
	"crypto/sha256"
	"debug/buildinfo"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"sort"
	"strings"
	"time"

	"github.com/bojieli/queqiao/internal/protocol"
)

var defaultTargets = []target{
	{goos: "linux", goarch: "amd64"},
	{goos: "linux", goarch: "arm64"},
	{goos: "darwin", goarch: "amd64"},
	{goos: "darwin", goarch: "arm64"},
	{goos: "windows", goarch: "amd64"},
	{goos: "windows", goarch: "arm64"},
}

var safeMetadata = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9._+~-]*$`)
var fullCommit = regexp.MustCompile(`^[0-9a-f]{40}$`)
var goDirective = regexp.MustCompile(`(?m)^go ([0-9]+\.[0-9]+\.[0-9]+)$`)

type target struct {
	goos   string
	goarch string
}

func (t target) String() string { return t.goos + "/" + t.goarch }

type config struct {
	repoRoot  string
	outputDir string
	version   string
	commit    string
	buildDate time.Time
	targets   []target
}

type archiveFile struct {
	name string
	mode int64
	data []byte
}

type linkedModule struct {
	Path           string
	Version        string
	Sum            string
	ReplacePath    string
	ReplaceVersion string
	ReplaceSum     string
	LicenseID      string
	Dir            string
}

type moduleLocation struct {
	Path string
	Dir  string
}

type cdxBOM struct {
	Schema       string          `json:"$schema"`
	BOMFormat    string          `json:"bomFormat"`
	SpecVersion  string          `json:"specVersion"`
	SerialNumber string          `json:"serialNumber"`
	Version      int             `json:"version"`
	Metadata     cdxMetadata     `json:"metadata"`
	Components   []cdxComponent  `json:"components,omitempty"`
	Dependencies []cdxDependency `json:"dependencies,omitempty"`
}

type cdxMetadata struct {
	Timestamp string       `json:"timestamp"`
	Component cdxComponent `json:"component"`
}

type cdxComponent struct {
	Type       string             `json:"type"`
	BOMRef     string             `json:"bom-ref"`
	Group      string             `json:"group,omitempty"`
	Name       string             `json:"name"`
	Version    string             `json:"version,omitempty"`
	Hashes     []cdxHash          `json:"hashes,omitempty"`
	Licenses   []cdxLicenseChoice `json:"licenses,omitempty"`
	Properties []cdxProperty      `json:"properties,omitempty"`
}

type cdxHash struct {
	Algorithm string `json:"alg"`
	Content   string `json:"content"`
}

type cdxLicenseChoice struct {
	License cdxLicense `json:"license"`
}

type cdxLicense struct {
	ID string `json:"id"`
}

type cdxProperty struct {
	Name  string `json:"name"`
	Value string `json:"value"`
}

type cdxDependency struct {
	Ref       string   `json:"ref"`
	DependsOn []string `json:"dependsOn"`
}

func main() {
	if err := run(context.Background(), os.Args[1:]); err != nil {
		fmt.Fprintf(os.Stderr, "queqiaopack: %v\n", err)
		os.Exit(1)
	}
}

func run(ctx context.Context, args []string) error {
	fs := flag.NewFlagSet("queqiaopack", flag.ContinueOnError)
	fs.SetOutput(os.Stderr)
	var cfg config
	var buildDate, targets string
	fs.StringVar(&cfg.repoRoot, "repo", ".", "repository root")
	fs.StringVar(&cfg.outputDir, "output", "dist", "new output directory (must not already exist)")
	fs.StringVar(&cfg.version, "version", "", "release version, for example v0.1.0")
	fs.StringVar(&cfg.commit, "commit", "", "source commit")
	fs.StringVar(&buildDate, "build-date", "", "source commit time in RFC3339 form")
	fs.StringVar(&targets, "targets", targetList(defaultTargets), "comma-separated GOOS/GOARCH targets")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if fs.NArg() != 0 {
		return fmt.Errorf("unexpected arguments: %s", strings.Join(fs.Args(), " "))
	}
	if buildDate == "" {
		return errors.New("--build-date is required")
	}
	parsedDate, err := time.Parse(time.RFC3339, buildDate)
	if err != nil {
		return fmt.Errorf("parse --build-date: %w", err)
	}
	cfg.buildDate = parsedDate.UTC()
	cfg.targets, err = parseTargets(targets)
	if err != nil {
		return err
	}
	return packageRelease(ctx, cfg)
}

func packageRelease(ctx context.Context, cfg config) error {
	if !safeMetadata.MatchString(cfg.version) {
		return errors.New("--version is required and may contain only release-safe characters")
	}
	if !fullCommit.MatchString(cfg.commit) {
		return errors.New("--commit must be a full lowercase Git commit SHA")
	}
	if cfg.buildDate.IsZero() {
		return errors.New("--build-date is required")
	}
	if cfg.buildDate.Year() < 1980 {
		return errors.New("--build-date must be 1980 or later for ZIP compatibility")
	}
	if len(cfg.targets) == 0 {
		return errors.New("at least one target is required")
	}

	repoRoot, err := filepath.Abs(cfg.repoRoot)
	if err != nil {
		return fmt.Errorf("resolve repository root: %w", err)
	}
	if _, err := os.Stat(filepath.Join(repoRoot, "go.mod")); err != nil {
		return fmt.Errorf("repository root %q has no go.mod: %w", repoRoot, err)
	}
	if err := verifyReleaseToolchain(repoRoot); err != nil {
		return err
	}
	if err := verifySourceCheckout(ctx, repoRoot, cfg.commit, cfg.buildDate); err != nil {
		return err
	}
	outputDir, err := filepath.Abs(cfg.outputDir)
	if err != nil {
		return fmt.Errorf("resolve output directory: %w", err)
	}
	if _, err := os.Lstat(outputDir); err == nil {
		return fmt.Errorf("output directory %q already exists", outputDir)
	} else if !errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("inspect output directory: %w", err)
	}
	outputParent := filepath.Dir(outputDir)
	if err := os.MkdirAll(outputParent, 0o755); err != nil {
		return fmt.Errorf("create output parent: %w", err)
	}
	tempDir, err := os.MkdirTemp(outputParent, ".queqiaopack-")
	if err != nil {
		return fmt.Errorf("create temporary package directory: %w", err)
	}
	defer os.RemoveAll(tempDir)
	resultDir := filepath.Join(tempDir, "result")
	if err := os.Mkdir(resultDir, 0o755); err != nil {
		return err
	}

	documents, err := readDistributionFiles(repoRoot)
	if err != nil {
		return err
	}
	if err := downloadModuleSources(ctx, repoRoot); err != nil {
		return err
	}
	moduleDirs, err := listModuleDirs(ctx, repoRoot)
	if err != nil {
		return err
	}
	checksums := make(map[string][sha256.Size]byte, len(cfg.targets)*2)
	for _, target := range cfg.targets {
		artifacts, err := buildTarget(ctx, repoRoot, tempDir, resultDir, cfg, target, documents, moduleDirs)
		if err != nil {
			return err
		}
		for name, sum := range artifacts {
			checksums[name] = sum
		}
	}
	if err := writeChecksums(filepath.Join(resultDir, "SHA256SUMS"), checksums); err != nil {
		return err
	}
	if err := os.Rename(resultDir, outputDir); err != nil {
		return fmt.Errorf("publish package directory: %w", err)
	}
	fmt.Printf("wrote %d release archives, %d CycloneDX SBOMs, and SHA256SUMS to %s\n", len(cfg.targets), len(cfg.targets), outputDir)
	return nil
}

func verifyReleaseToolchain(repoRoot string) error {
	// repoRoot is the explicit repository selected for packaging; reading its
	// fixed go.mod is required to bind the release compiler version.
	data, err := os.ReadFile(filepath.Join(repoRoot, "go.mod")) // #nosec G304 -- fixed file in the selected release repository.
	if err != nil {
		return fmt.Errorf("read go.mod: %w", err)
	}
	match := goDirective.FindSubmatch(data)
	if match == nil {
		return errors.New("go.mod must declare a full patched Go version")
	}
	want := "go" + string(match[1])
	if runtime.Version() != want {
		return fmt.Errorf("packager toolchain is %s; go.mod requires %s", runtime.Version(), want)
	}
	return nil
}

// verifySourceCheckout binds the provenance written into BUILDINFO and the
// SBOM to the bytes that Go will actually compile. The release workflows make
// the same checks, but keeping the invariant in the packager prevents a local
// or future caller from producing credible-looking artifacts from a dirty or
// different checkout.
func verifySourceCheckout(ctx context.Context, repoRoot, commit string, buildDate time.Time) error {
	git := func(args ...string) ([]byte, error) {
		// #nosec G204 -- every call below supplies a fixed, reviewable Git
		// subcommand; no user-controlled value reaches the executable or argv.
		cmd := exec.CommandContext(ctx, "git", args...)
		cmd.Dir = repoRoot
		output, err := cmd.CombinedOutput()
		if err != nil {
			return nil, fmt.Errorf("git %s: %w\n%s", strings.Join(args, " "), err, output)
		}
		return output, nil
	}
	head, err := git("rev-parse", "--verify", "HEAD")
	if err != nil {
		return fmt.Errorf("inspect source commit: %w", err)
	}
	if strings.TrimSpace(string(head)) != commit {
		return fmt.Errorf("source checkout HEAD does not match --commit %s", commit)
	}
	dateText, err := git("show", "-s", "--format=%cI", "HEAD")
	if err != nil {
		return fmt.Errorf("inspect source commit time: %w", err)
	}
	commitDate, err := time.Parse(time.RFC3339, strings.TrimSpace(string(dateText)))
	if err != nil {
		return fmt.Errorf("parse source commit time: %w", err)
	}
	if !commitDate.Equal(buildDate) {
		return fmt.Errorf("--build-date does not match source commit time %s", commitDate.Format(time.RFC3339))
	}
	status, err := git("status", "--porcelain=v1", "--untracked-files=all", "--ignored=matching")
	if err != nil {
		return fmt.Errorf("inspect source worktree: %w", err)
	}
	if len(status) != 0 {
		return errors.New("source worktree is not clean; commit every release input before packaging")
	}
	return nil
}

func buildTarget(ctx context.Context, repoRoot, tempDir, resultDir string, cfg config, target target, documents []archiveFile, moduleDirs map[string]string) (map[string][sha256.Size]byte, error) {
	packageBase := fmt.Sprintf("queqiaod_%s_%s_%s", cfg.version, target.goos, target.goarch)
	binaryName := "queqiaod"
	if target.goos == "windows" {
		binaryName += ".exe"
	}
	buildDir := filepath.Join(tempDir, "build", target.goos+"-"+target.goarch)
	if err := os.MkdirAll(buildDir, 0o755); err != nil {
		return nil, err
	}
	binaryPath := filepath.Join(buildDir, binaryName)
	ldflags := strings.Join([]string{
		"-s", "-w",
		"-X=main.version=" + cfg.version,
		"-X=main.commit=" + cfg.commit,
		"-X=main.buildDate=" + cfg.buildDate.Format(time.RFC3339),
	}, " ")
	cmd := exec.CommandContext(ctx, "go", "build", "-trimpath", "-buildvcs=false", "-ldflags", ldflags, "-o", binaryPath, "./cmd/queqiaod")
	cmd.Dir = repoRoot
	cmd.Env = withEnv(releaseGoEnv(os.Environ()), map[string]string{
		"CGO_ENABLED": "0",
		"GOOS":        target.goos,
		"GOARCH":      target.goarch,
		"GOAMD64":     "v1",
		"GOARM64":     "v8.0",
	})
	if output, err := cmd.CombinedOutput(); err != nil {
		return nil, fmt.Errorf("build %s: %w\n%s", target, err, output)
	}
	binary, err := os.ReadFile(binaryPath)
	if err != nil {
		return nil, fmt.Errorf("read %s binary: %w", target, err)
	}
	binarySum := sha256.Sum256(binary)
	modules, err := readLinkedModules(binaryPath, moduleDirs)
	if err != nil {
		return nil, fmt.Errorf("read %s linked modules: %w", target, err)
	}
	sbom, err := renderCycloneDX(cfg, target, binarySum, modules)
	if err != nil {
		return nil, fmt.Errorf("render %s SBOM: %w", target, err)
	}
	licenses, err := renderThirdPartyLicenses(modules)
	if err != nil {
		return nil, fmt.Errorf("render %s third-party licenses: %w", target, err)
	}
	files := make([]archiveFile, 0, len(documents)+4)
	files = append(files, archiveFile{name: binaryName, mode: 0o755, data: binary})
	files = append(files, documents...)
	files = append(files, archiveFile{name: "SBOM.cdx.json", mode: 0o644, data: sbom})
	files = append(files, archiveFile{name: "THIRD_PARTY_LICENSES.txt", mode: 0o644, data: licenses})
	files = append(files, archiveFile{
		name: "BUILDINFO",
		mode: 0o644,
		data: []byte(fmt.Sprintf(
			"version=%s\ncommit=%s\nbuild_date=%s\ntarget=%s\ngo=%s\nwire_protocol=%d\nbinary_sha256=%x\n",
			cfg.version, cfg.commit, cfg.buildDate.Format(time.RFC3339), target, runtime.Version(), protocol.Version, binarySum,
		)),
	})
	sort.Slice(files, func(i, j int) bool { return files[i].name < files[j].name })

	extension := ".tar.gz"
	if target.goos == "windows" {
		extension = ".zip"
	}
	archiveName := packageBase + extension
	archivePath := filepath.Join(resultDir, archiveName)
	if target.goos == "windows" {
		err = writeZip(archivePath, packageBase, files, cfg.buildDate)
	} else {
		err = writeTarGzip(archivePath, packageBase, files, cfg.buildDate)
	}
	if err != nil {
		return nil, fmt.Errorf("archive %s: %w", target, err)
	}
	archive, err := os.ReadFile(archivePath)
	if err != nil {
		return nil, err
	}
	sbomName := packageBase + ".cdx.json"
	if err := os.WriteFile(filepath.Join(resultDir, sbomName), sbom, 0o644); err != nil {
		return nil, fmt.Errorf("write %s: %w", sbomName, err)
	}
	return map[string][sha256.Size]byte{
		archiveName: sha256.Sum256(archive),
		sbomName:    sha256.Sum256(sbom),
	}, nil
}

func readDistributionFiles(repoRoot string) ([]archiveFile, error) {
	names := []string{
		"CHANGELOG.md",
		"CONTRIBUTING.md",
		"LICENSE",
		"PRIVACY.md",
		"README.md",
		"SECURITY.md",
		"THIRD_PARTY_NOTICES.md",
		"assets/queqiao-icon.png",
		"docs/ARCHITECTURE.md",
		"docs/BENCHMARKING.md",
		"docs/CONTRIBUTING-NETWORK-EVIDENCE.md",
		"docs/DEPLOYING.md",
		"docs/DESIGN.md",
		"docs/FIELD-VALIDATION.md",
		"docs/KNOWN-LIMITATIONS.md",
		"docs/LOGGING.md",
		"docs/MOBILE.md",
		"docs/PATH-CHARACTER-20260813.md",
		"docs/PRODUCTION-DESIGN.md",
		"docs/PROTOCOL.md",
		"docs/README.md",
		"docs/RELEASE-CHECKLIST.md",
		"docs/RELEASING.md",
		"docs/ROADMAP.md",
		"docs/STATUS.md",
		"docs/VISION.md",
		"docs/archive/README.md",
		"docs/archive/2026-08-development/DESIGN-ERASURE.md",
		"docs/archive/2026-08-development/DESIGN-MULTIPATH.md",
		"docs/archive/2026-08-development/MEASUREMENTS-20260809.md",
		"docs/archive/2026-08-development/MEASUREMENTS-20260810.md",
		"docs/archive/2026-08-development/MEASUREMENTS-20260816.md",
		"docs/archive/2026-08-development/PERFORMANCE-20260812.md",
		"docs/archive/2026-08-development/PROFILE-20260811.md",
		"docs/archive/2026-08-development/PUBLIC-HISTORY-AUDIT-20260817.md",
		"docs/archive/2026-08-development/README.md",
		"docs/archive/2026-08-development/RELEASE-CANDIDATE-20260817.md",
		"docs/archive/2026-08-development/RELEASE-HARDENING-20260817.md",
		"docs/archive/2026-08-development/STALL-20260817.md",
		"docs/archive/2026-08-development/STATIC-SECURITY-AUDIT-20260817.md",
		"docs/archive/2026-08-development/TCP-FALLBACK-20260817.md",
		"docs/archive/2026-08-development/field-results/20260817-primary-high-port.md",
		"docs/field-results/README.md",
		"deploy/clash-queqiao.yaml",
		"deploy/install-client.sh",
		"deploy/install-server.sh",
		"deploy/queqiaod.service",
		"deploy/tune-server.sh",
		"internal/congestion/NOTICE",
	}
	// The deployment guide in this archive tells the operator to run these, and
	// they find the archive's own reviewed binary beside them, so they ship
	// executable. Unpacking a release is then the only prerequisite.
	executable := map[string]bool{
		"deploy/install-client.sh": true,
		"deploy/install-server.sh": true,
		"deploy/tune-server.sh":    true,
	}
	files := make([]archiveFile, 0, len(names))
	for _, name := range names {
		data, err := os.ReadFile(filepath.Join(repoRoot, filepath.FromSlash(name)))
		if err != nil {
			return nil, fmt.Errorf("read distribution file %s: %w", name, err)
		}
		mode := int64(0o644)
		if executable[name] {
			mode = 0o755
		}
		files = append(files, archiveFile{name: name, mode: mode, data: data})
	}
	return files, nil
}

// downloadModuleSources makes packaging independent of the state of Go's
// build cache. A cached compiled package is enough for go build, but licenses
// are read from dependency source trees, which the module cache may not have
// extracted yet.
func downloadModuleSources(ctx context.Context, repoRoot string) error {
	for _, arguments := range [][]string{{"mod", "download"}, {"mod", "verify"}} {
		// Both argument lists are fixed literals above; no caller input reaches
		// the executable or argv.
		cmd := exec.CommandContext(ctx, "go", arguments...) // #nosec G204 -- fixed Go subcommands.
		cmd.Dir = repoRoot
		cmd.Env = releaseGoEnv(os.Environ())
		if output, err := cmd.CombinedOutput(); err != nil {
			return fmt.Errorf("go %s: %w\n%s", strings.Join(arguments, " "), err, output)
		}
	}
	return nil
}

func listModuleDirs(ctx context.Context, repoRoot string) (map[string]string, error) {
	cmd := exec.CommandContext(ctx, "go", "list", "-m", "-json", "all")
	cmd.Dir = repoRoot
	cmd.Env = releaseGoEnv(os.Environ())
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("list module locations: %w", err)
	}
	decoder := json.NewDecoder(strings.NewReader(string(output)))
	dirs := make(map[string]string)
	for decoder.More() {
		var module moduleLocation
		if err := decoder.Decode(&module); err != nil {
			return nil, fmt.Errorf("decode module location: %w", err)
		}
		if module.Path != "" && module.Dir != "" {
			dirs[module.Path] = module.Dir
		}
	}
	return dirs, nil
}

func readLinkedModules(binaryPath string, moduleDirs map[string]string) ([]linkedModule, error) {
	info, err := buildinfo.ReadFile(binaryPath)
	if err != nil {
		return nil, err
	}
	if info.GoVersion != runtime.Version() {
		return nil, fmt.Errorf("linked binary Go version %s differs from packager %s", info.GoVersion, runtime.Version())
	}
	modules := make([]linkedModule, 0, len(info.Deps))
	for _, dependency := range info.Deps {
		module := linkedModule{
			Path: dependency.Path, Version: dependency.Version, Sum: dependency.Sum,
			LicenseID: moduleLicenseID(dependency.Path), Dir: moduleDirs[dependency.Path],
		}
		if dependency.Replace != nil {
			module.ReplacePath = dependency.Replace.Path
			module.ReplaceVersion = dependency.Replace.Version
			module.ReplaceSum = dependency.Replace.Sum
			if replacementDir := moduleDirs[dependency.Replace.Path]; replacementDir != "" {
				module.Dir = replacementDir
			}
			module.LicenseID = moduleLicenseID(dependency.Replace.Path)
		}
		if module.Dir == "" {
			return nil, fmt.Errorf("linked module %s has no source directory", dependency.Path)
		}
		if module.LicenseID == "NOASSERTION" {
			return nil, fmt.Errorf("linked module %s has no reviewed SPDX license classification", dependency.Path)
		}
		modules = append(modules, module)
	}
	sort.Slice(modules, func(i, j int) bool { return modules[i].Path < modules[j].Path })
	return modules, nil
}

func moduleLicenseID(modulePath string) string {
	switch modulePath {
	case "github.com/andybalholm/brotli", "github.com/apernet/quic-go":
		return "MIT"
	case "github.com/klauspost/compress", "github.com/refraction-networking/utls",
		"golang.org/x/crypto", "golang.org/x/net", "golang.org/x/sys":
		return "BSD-3-Clause"
	default:
		return "NOASSERTION"
	}
}

func renderCycloneDX(cfg config, target target, binarySum [sha256.Size]byte, modules []linkedModule) ([]byte, error) {
	rootRef := fmt.Sprintf("queqiaod@%s:%s", cfg.version, target)
	root := cdxComponent{
		Type: "application", BOMRef: rootRef, Group: "github.com/bojieli/queqiao",
		Name: "queqiaod", Version: cfg.version,
		Hashes:   []cdxHash{{Algorithm: "SHA-256", Content: fmt.Sprintf("%x", binarySum)}},
		Licenses: []cdxLicenseChoice{{License: cdxLicense{ID: "MIT"}}},
		Properties: []cdxProperty{
			{Name: "queqiao:commit", Value: cfg.commit},
			{Name: "queqiao:target", Value: target.String()},
			{Name: "queqiao:wire-protocol", Value: fmt.Sprint(protocol.Version)},
			{Name: "queqiao:go-version", Value: runtime.Version()},
		},
	}
	components := make([]cdxComponent, 0, len(modules))
	refs := make([]string, 0, len(modules))
	for _, module := range modules {
		ref := module.Path + "@" + module.Version
		properties := []cdxProperty{}
		if module.Sum != "" {
			properties = append(properties, cdxProperty{Name: "golang:module-sum", Value: module.Sum})
		}
		if module.ReplacePath != "" {
			properties = append(properties,
				cdxProperty{Name: "golang:replace-path", Value: module.ReplacePath},
				cdxProperty{Name: "golang:replace-version", Value: module.ReplaceVersion},
			)
			if module.ReplaceSum != "" {
				properties = append(properties, cdxProperty{Name: "golang:replace-sum", Value: module.ReplaceSum})
			}
		}
		component := cdxComponent{
			Type: "library", BOMRef: ref, Name: module.Path, Version: module.Version,
			Properties: properties,
		}
		if module.LicenseID != "NOASSERTION" {
			component.Licenses = []cdxLicenseChoice{{License: cdxLicense{ID: module.LicenseID}}}
		}
		components = append(components, component)
		refs = append(refs, ref)
	}
	serialInput := append([]byte("queqiao/cyclonedx/v1\x00"+cfg.version+"\x00"+cfg.commit+"\x00"+target.String()+"\x00"), binarySum[:]...)
	serialHash := sha256.Sum256(serialInput)
	serialHash[6] = serialHash[6]&0x0f | 0x80 // deterministic UUID version 8
	serialHash[8] = serialHash[8]&0x3f | 0x80
	serial := fmt.Sprintf("urn:uuid:%x-%x-%x-%x-%x", serialHash[0:4], serialHash[4:6], serialHash[6:8], serialHash[8:10], serialHash[10:16])
	bom := cdxBOM{
		Schema:    "http://cyclonedx.org/schema/bom-1.5.schema.json",
		BOMFormat: "CycloneDX", SpecVersion: "1.5", SerialNumber: serial, Version: 1,
		Metadata:     cdxMetadata{Timestamp: cfg.buildDate.Format(time.RFC3339), Component: root},
		Components:   components,
		Dependencies: []cdxDependency{{Ref: rootRef, DependsOn: refs}},
	}
	data, err := json.MarshalIndent(bom, "", "  ")
	if err != nil {
		return nil, err
	}
	return append(data, '\n'), nil
}

func renderThirdPartyLicenses(modules []linkedModule) ([]byte, error) {
	var output strings.Builder
	output.WriteString("QUEQIAO THIRD-PARTY LICENSES\n\n")
	output.WriteString("Generated from the exact modules linked into this binary.\n")
	for _, module := range modules {
		entries, err := os.ReadDir(module.Dir)
		if err != nil {
			return nil, fmt.Errorf("read %s: %w", module.Path, err)
		}
		var names []string
		for _, entry := range entries {
			upper := strings.ToUpper(entry.Name())
			if !entry.IsDir() && (strings.HasPrefix(upper, "LICENSE") || strings.HasPrefix(upper, "COPYING") || strings.HasPrefix(upper, "NOTICE")) {
				names = append(names, entry.Name())
			}
		}
		sort.Strings(names)
		if len(names) == 0 {
			return nil, fmt.Errorf("linked module %s has no root license file", module.Path)
		}
		output.WriteString("\n================================================================\n")
		fmt.Fprintf(&output, "%s %s\nSPDX license: %s\n", module.Path, module.Version, module.LicenseID)
		if module.ReplacePath != "" {
			fmt.Fprintf(&output, "Resolved replacement: %s %s\n", module.ReplacePath, module.ReplaceVersion)
		}
		for _, name := range names {
			license, err := os.ReadFile(filepath.Join(module.Dir, name))
			if err != nil {
				return nil, fmt.Errorf("read %s %s: %w", module.Path, name, err)
			}
			fmt.Fprintf(&output, "\n--- %s ---\n", name)
			output.Write(license)
			if len(license) == 0 || license[len(license)-1] != '\n' {
				output.WriteByte('\n')
			}
		}
	}
	return []byte(output.String()), nil
}

func writeTarGzip(path, root string, files []archiveFile, modTime time.Time) (returnErr error) {
	file, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	defer func() {
		if err := file.Close(); returnErr == nil && err != nil {
			returnErr = err
		}
	}()
	gz, err := gzip.NewWriterLevel(file, gzip.BestCompression)
	if err != nil {
		return err
	}
	gz.Header.ModTime = modTime
	gz.Header.OS = 255
	tw := tar.NewWriter(gz)
	for _, entry := range files {
		header := &tar.Header{
			Name:    root + "/" + entry.name,
			Mode:    entry.mode,
			Size:    int64(len(entry.data)),
			ModTime: modTime,
			Format:  tar.FormatGNU,
		}
		if err := tw.WriteHeader(header); err != nil {
			return err
		}
		if _, err := tw.Write(entry.data); err != nil {
			return err
		}
	}
	if err := tw.Close(); err != nil {
		return err
	}
	return gz.Close()
}

func writeZip(path, root string, files []archiveFile, modTime time.Time) (returnErr error) {
	file, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	defer func() {
		if err := file.Close(); returnErr == nil && err != nil {
			returnErr = err
		}
	}()
	zw := zip.NewWriter(file)
	for _, entry := range files {
		header := &zip.FileHeader{Name: root + "/" + entry.name, Method: zip.Deflate}
		header.SetMode(os.FileMode(entry.mode))
		header.Modified = modTime
		writer, err := zw.CreateHeader(header)
		if err != nil {
			return err
		}
		if _, err := writer.Write(entry.data); err != nil {
			return err
		}
	}
	return zw.Close()
}

func writeChecksums(path string, checksums map[string][sha256.Size]byte) error {
	names := make([]string, 0, len(checksums))
	for name := range checksums {
		names = append(names, name)
	}
	sort.Strings(names)
	var output strings.Builder
	for _, name := range names {
		fmt.Fprintf(&output, "%x  %s\n", checksums[name], name)
	}
	if err := os.WriteFile(path, []byte(output.String()), 0o644); err != nil {
		return fmt.Errorf("write SHA256SUMS: %w", err)
	}
	return nil
}

func parseTargets(value string) ([]target, error) {
	seen := make(map[string]bool)
	var targets []target
	for _, raw := range strings.Split(value, ",") {
		parts := strings.Split(strings.TrimSpace(raw), "/")
		if len(parts) != 2 || !safeMetadata.MatchString(parts[0]) || !safeMetadata.MatchString(parts[1]) {
			return nil, fmt.Errorf("invalid target %q; want GOOS/GOARCH", raw)
		}
		target := target{goos: parts[0], goarch: parts[1]}
		if !seen[target.String()] {
			seen[target.String()] = true
			targets = append(targets, target)
		}
	}
	if len(targets) == 0 {
		return nil, errors.New("at least one target is required")
	}
	return targets, nil
}

func targetList(targets []target) string {
	values := make([]string, len(targets))
	for i, target := range targets {
		values[i] = target.String()
	}
	return strings.Join(values, ",")
}

func withEnv(base []string, replacements map[string]string) []string {
	result := make([]string, 0, len(base)+len(replacements))
	for _, value := range base {
		key, _, found := strings.Cut(value, "=")
		if !found {
			continue
		}
		if _, replace := replacements[key]; !replace {
			result = append(result, value)
		}
	}
	keys := make([]string, 0, len(replacements))
	for key := range replacements {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	for _, key := range keys {
		result = append(result, key+"="+replacements[key])
	}
	return result
}

// releaseGoEnv prevents ambient per-user Go configuration, workspaces, build
// tags, overlays, experiments, or architecture levels from changing the bytes
// described by release provenance. Cache and module-download locations remain
// caller-selectable so CI can isolate them without affecting build semantics.
func releaseGoEnv(base []string) []string {
	return withEnv(base, map[string]string{
		"GOENV":        "off",
		"GOEXPERIMENT": "",
		"GOFIPS140":    "off",
		"GOFLAGS":      "-mod=readonly",
		"GOTOOLCHAIN":  runtime.Version(),
		"GOWORK":       "off",
	})
}
