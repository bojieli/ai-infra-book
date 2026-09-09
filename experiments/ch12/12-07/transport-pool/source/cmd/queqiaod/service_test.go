package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func testServiceConfig() serviceConfig {
	return serviceConfig{
		label:         defaultServiceLabel,
		unit:          defaultServiceUnit,
		binary:        "/home/alice/.queqiao/bin/queqiaod",
		providers:     "/home/alice/.config/queqiao/providers.json",
		listen:        "127.0.0.1:12080",
		localAddress:  "auto",
		metricsListen: "127.0.0.1:12090",
		logLevel:      "info",
	}
}

func TestServiceArgumentsUseProfileOrManifest(t *testing.T) {
	manifest := strings.Join(testServiceConfig().arguments(), " ")
	if !strings.Contains(manifest, "--providers /home/alice/.config/queqiao/providers.json") {
		t.Fatalf("manifest arguments missing --providers: %s", manifest)
	}
	if strings.Contains(manifest, "--listen") {
		t.Fatalf("a manifest carries its own listeners, so --listen must not appear: %s", manifest)
	}

	config := testServiceConfig()
	config.providers = ""
	config.profile = "/home/alice/.config/queqiao/hk.json"
	single := strings.Join(config.arguments(), " ")
	if !strings.Contains(single, "--profile /home/alice/.config/queqiao/hk.json") {
		t.Fatalf("single-profile arguments missing --profile: %s", single)
	}
	if !strings.Contains(single, "--listen 127.0.0.1:12080") {
		t.Fatalf("single-profile arguments missing --listen: %s", single)
	}
}

// The client's default listener and the port in deploy/clash-queqiao.yaml have
// to be the same number, or an unconfigured start silently routes nowhere.
func TestServiceDefaultListenMatchesClientDefault(t *testing.T) {
	var runtimeOpts runtimeOptions
	fs := newFlagSet("client")
	bindRuntimeFlags(fs, &runtimeOpts, true)
	if err := fs.Parse(nil); err != nil {
		t.Fatalf("parse: %v", err)
	}

	var service serviceConfig
	serviceFlags := newFlagSet("service install")
	bindServiceFlags(serviceFlags, &service)
	if err := serviceFlags.Parse(nil); err != nil {
		t.Fatalf("parse: %v", err)
	}
	if service.listen != runtimeOpts.listen {
		t.Fatalf("service default listen %q differs from client default %q", service.listen, runtimeOpts.listen)
	}
	if service.listen != "127.0.0.1:12080" {
		t.Fatalf("default listen is %q, want the Clash profile's 127.0.0.1:12080", service.listen)
	}
}

func TestRenderLaunchAgentQuotesEveryArgument(t *testing.T) {
	config := testServiceConfig()
	config.binary = "/Users/alice/Library/Application Support/q & r/queqiaod"
	rendered := renderLaunchAgent(config)

	if strings.Contains(rendered, "q & r") {
		t.Fatal("a bare ampersand would make the plist unparseable")
	}
	if !strings.Contains(rendered, "q &amp; r") {
		t.Fatalf("ampersand was not escaped:\n%s", rendered)
	}
	// launchd discards stderr unless a path is set, so the file is the only
	// surface there; the Linux unit must not carry the same flag.
	if !strings.Contains(rendered, "<string>--log-stderr=false</string>") {
		t.Fatalf("LaunchAgent should disable stderr logging:\n%s", rendered)
	}
	if !strings.Contains(rendered, "<key>RunAtLoad</key>\n  <true/>") {
		t.Fatalf("LaunchAgent must start at login:\n%s", rendered)
	}
	for _, required := range []string{"<string>client</string>", "<string>--providers</string>"} {
		if !strings.Contains(rendered, required) {
			t.Fatalf("missing %s in:\n%s", required, rendered)
		}
	}
}

func TestRenderSystemdUnitQuotesEveryArgument(t *testing.T) {
	config := testServiceConfig()
	config.providers = "/home/alice/my configs/providers.json"
	rendered := renderSystemdUnit(config)

	if !strings.Contains(rendered, `"/home/alice/my configs/providers.json"`) {
		t.Fatalf("a path containing a space must stay one argument:\n%s", rendered)
	}
	if strings.Contains(rendered, "--log-stderr=false") {
		t.Fatal("journald keeps stderr on Linux, so the flag must not appear")
	}
	if !strings.Contains(rendered, "WantedBy=default.target") {
		t.Fatalf("unit must be enablable for the user session:\n%s", rendered)
	}
	if !strings.Contains(rendered, "Restart=on-failure") {
		t.Fatalf("the client exits when a listener stops and must be restarted:\n%s", rendered)
	}
}

// The client resolves --local-address by reading this machine's interfaces,
// which needs AF_NETLINK. Without it the unit installs cleanly, binds its
// listener, and then fails every flow at run time - the worst shape a sandbox
// mistake can take, because nothing looks wrong until traffic is attempted.
func TestRenderSystemdUnitAllowsInterfaceEnumeration(t *testing.T) {
	config := testServiceConfig()
	config.localAddress = "if:enp6s0"
	rendered := renderSystemdUnit(config)

	families := ""
	for _, line := range strings.Split(rendered, "\n") {
		if strings.HasPrefix(line, "RestrictAddressFamilies=") {
			families = line
		}
	}
	if families == "" {
		t.Fatalf("unit does not restrict address families at all:\n%s", rendered)
	}
	if !strings.Contains(families, "AF_NETLINK") {
		t.Fatalf("--local-address cannot resolve without AF_NETLINK: %s", families)
	}
	// The restriction must still be a restriction.
	for _, refused := range []string{"AF_PACKET", "AF_RAW"} {
		if strings.Contains(families, refused) {
			t.Fatalf("%s must not be permitted: %s", refused, families)
		}
	}
}

func TestSystemdQuoteEscapesMetacharacters(t *testing.T) {
	got := systemdQuote(`a"b\c`)
	want := `"a\"b\\c"`
	if got != want {
		t.Fatalf("systemdQuote = %s, want %s", got, want)
	}
}

func TestServiceResolveRejectsConflictingSources(t *testing.T) {
	config := serviceConfig{label: defaultServiceLabel, unit: defaultServiceUnit, listen: "127.0.0.1:12080"}
	if err := config.resolve(); err == nil {
		t.Fatal("neither --profile nor --providers should be rejected")
	}

	config.profile = "/tmp/a.json"
	config.providers = "/tmp/b.json"
	if err := config.resolve(); err == nil {
		t.Fatal("--profile with --providers should be rejected")
	}

	config.profile = ""
	config.listen = "127.0.0.1:1081"
	if err := config.resolve(); err == nil {
		t.Fatal("--listen with --providers should be rejected")
	}
}

func TestServiceResolveRejectsUnsafeNames(t *testing.T) {
	for _, name := range []string{"../escape", "with/slash", "", "-leading"} {
		config := serviceConfig{label: name, unit: defaultServiceUnit, profile: "/tmp/a.json", listen: "127.0.0.1:12080"}
		if err := config.resolve(); err == nil {
			t.Fatalf("label %q became a file name without complaint", name)
		}
		config = serviceConfig{label: defaultServiceLabel, unit: name, profile: "/tmp/a.json", listen: "127.0.0.1:12080"}
		if err := config.resolve(); err == nil {
			t.Fatalf("service name %q became a file name without complaint", name)
		}
	}
}

// The datacenter profile had no supported way to reach an installed service.
// The flag existed on `queqiaod client` and nothing between the installer and
// the unit file carried it, so running it meant hand-editing a definition that
// the installer rewrites on every upgrade.
func TestServiceCarriesThePathProfile(t *testing.T) {
	config := testServiceConfig()
	if got := strings.Join(config.arguments(), " "); strings.Contains(got, "--path-profile") {
		t.Fatalf("an unset profile still reached the service: %s", got)
	}
	config.pathProfile = "dc-long-haul"
	got := strings.Join(config.arguments(), " ")
	if !strings.Contains(got, "--path-profile dc-long-haul") {
		t.Fatalf("the profile did not reach the service: %s", got)
	}
}

// A misspelled profile has to fail the install. The client refuses an unknown
// name rather than falling back to the default, so without this the failure
// lands at first start, on a service the installer has already reported as
// successfully installed.
func TestServiceResolveRejectsAnUnknownPathProfile(t *testing.T) {
	config := testServiceConfig()
	config.pathProfile = "dc-long-hual"
	err := config.resolve()
	if err == nil {
		t.Fatal("a misspelled profile installed cleanly")
	}
	if !strings.Contains(err.Error(), "dc-long-haul") {
		t.Fatalf("the error does not name the alternatives: %v", err)
	}
}

func TestServiceResolveAcceptsAKnownPathProfile(t *testing.T) {
	manifest := filepath.Join(t.TempDir(), "providers.json")
	if err := os.WriteFile(manifest, []byte("{}"), 0o600); err != nil {
		t.Fatal(err)
	}
	config := testServiceConfig()
	config.providers = manifest
	config.binary = os.Args[0]
	config.pathProfile = "dc-long-haul"
	if err := config.resolve(); err != nil {
		t.Fatalf("a known profile was rejected: %v", err)
	}
}
