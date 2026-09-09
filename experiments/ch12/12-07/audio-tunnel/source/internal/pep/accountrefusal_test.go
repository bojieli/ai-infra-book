package pep

import (
	"bytes"
	"encoding/json"
	"log/slog"
	"net"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/metrics"
	"github.com/bojieli/queqiao/internal/protocol"
	"github.com/bojieli/queqiao/internal/session"
)

// An account whose limit was set too low produced a client reporting resets
// and a gateway reporting nothing: no record at any level, and no counter to
// check. The refusal had to be diagnosed from the peer, which is the one place
// that cannot see which limit was hit or whose account hit it.
//
// Every refusal must now reach an operator reading at the default level, be
// counted by reason, and name in the RESET which of the two limits refused.
func TestAccountRefusalsAreVisibleCountedAndNamed(t *testing.T) {
	for _, test := range []struct {
		name    string
		limits  identity.AccountLimits
		devices int
		// prime is how many flows to admit before the one that is refused.
		prime   int
		refuser int
		reason  metrics.AccountRefusal
		code    session.ResetCode
		message string
	}{
		{
			name: "flow limit", limits: identity.AccountLimits{MaxFlows: 1}, devices: 1,
			prime: 1, refuser: 0, reason: metrics.AccountRefusalFlowLimit,
			code: session.ResetFlowLimit, message: "account flow limit reached",
		},
		{
			name: "client limit", limits: identity.AccountLimits{MaxClients: 1}, devices: 2,
			prime: 1, refuser: 1, reason: metrics.AccountRefusalClientLimit,
			code: session.ResetFlowLimit, message: "account device limit reached",
		},
	} {
		t.Run(test.name, func(t *testing.T) {
			server, principals := admissionFixture(t, test.limits, test.devices)
			var records bytes.Buffer
			registry := metrics.New()
			server.cfg.Logger = slog.New(slog.NewJSONHandler(&records, &slog.HandlerOptions{Level: slog.LevelInfo}))
			server.metrics = registry

			for i := 0; i < test.prime; i++ {
				if refusal := server.admitAccountFlow(principals[0]); refusal != nil {
					t.Fatalf("priming flow %d refused: %v", i, refusal)
				}
			}
			principal := principals[test.refuser]
			refusal := server.admitAccountFlow(principal)
			if refusal == nil {
				t.Fatal("the flow that should have been refused was admitted")
			}
			if refusal.reason != test.reason {
				t.Fatalf("reason = %s, want %s", refusal.reason, test.reason)
			}

			local, remote := net.Pipe()
			t.Cleanup(func() { _ = local.Close(); _ = remote.Close() })
			var sessionID [16]byte
			go server.refuseAccountFlow(newFrameConn(local), sessionID, 1, principal, refusal)

			response, err := newFrameConn(remote).Read()
			if err != nil {
				t.Fatal(err)
			}
			if response.Header.Type != protocol.TypeReset {
				t.Fatalf("response = %d, want RESET", response.Header.Type)
			}
			if len(response.Payload) == 0 || session.ResetCode(response.Payload[0]) != test.code {
				t.Fatalf("reset payload = %q, want code %d", response.Payload, test.code)
			}
			if got := string(response.Payload[1:]); got != test.message {
				t.Fatalf("reset message = %q, want %q", got, test.message)
			}
			if got := registry.Snapshot().AccountAdmissionRefusals[test.reason]; got != 1 {
				t.Fatalf("%s counter = %d, want 1", test.reason, got)
			}
			var record map[string]any
			if err := json.Unmarshal(bytes.TrimSpace(records.Bytes()), &record); err != nil {
				t.Fatalf("no record at info level: %v (%q)", err, records.String())
			}
			if record["msg"] != "account flow open refused" || record["reason"] != test.reason.String() || record["level"] != "WARN" {
				t.Fatalf("record = %#v", record)
			}
			// The account is the only thing an operator can act on, and one
			// record has to be readable on its own.
			if record["account"] != principal.AccountID || record["total"] != float64(1) {
				t.Fatalf("record = %#v", record)
			}
		})
	}
}

// A revoked device used to be answered with the flow-limit message, which
// sends whoever reads it looking for a quota that is not the problem.
func TestUnauthorizedDeviceIsNotReportedAsALimit(t *testing.T) {
	server, principals := admissionFixture(t, identity.AccountLimits{}, 1)
	principal := principals[0]
	account, ok := server.cfg.Credentials.Store.FindAccount(principal.AccountID)
	if !ok {
		t.Fatal("fixture account is missing")
	}
	if err := server.cfg.Credentials.Store.SetAccountEnabled(account.ID, false); err != nil {
		t.Fatal(err)
	}
	refusal := server.admitAccountFlow(principal)
	if refusal == nil {
		t.Fatal("a disabled account was admitted")
	}
	if refusal.reason != metrics.AccountRefusalUnauthorized || refusal.code != session.ResetAuthentication {
		t.Fatalf("refusal = %+v, want an authentication refusal", refusal)
	}
}

// A storm of refusals from one account must not suppress the record of a
// different reason, and must not suppress lane-join records either.
func TestAccountAndLaneJoinRefusalsDoNotSuppressEachOther(t *testing.T) {
	var accountLog, laneLog recordLimiter
	now := time.Now()
	if write, _, _ := accountLog.due(metrics.AccountRefusalFlowLimit, now); !write {
		t.Fatal("the first account refusal was not written")
	}
	if write, _, _ := accountLog.due(metrics.AccountRefusalFlowLimit, now); write {
		t.Fatal("a repeated account refusal was written inside the interval")
	}
	if write, _, _ := accountLog.due(metrics.AccountRefusalClientLimit, now); !write {
		t.Fatal("a client-limit refusal was hidden by a flow-limit storm")
	}
	if write, _, _ := laneLog.due(metrics.LaneJoinUnknownSession, now); !write {
		t.Fatal("a lane-join refusal was hidden by an account refusal storm")
	}
}
