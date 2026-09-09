package pep

import (
	"bytes"
	"encoding/json"
	"errors"
	"log/slog"
	"testing"

	"github.com/bojieli/queqiao/internal/identity"
)

func enrollmentRecorder(t *testing.T) (*Server, *bytes.Buffer) {
	t.Helper()
	var records bytes.Buffer
	server := &Server{cfg: ServerConfig{
		Logger: slog.New(slog.NewJSONHandler(&records, &slog.HandlerOptions{Level: slog.LevelInfo})),
	}}
	return server, &records
}

func decodeRecords(t *testing.T, raw *bytes.Buffer) []map[string]any {
	t.Helper()
	out := []map[string]any{}
	for _, line := range bytes.Split(bytes.TrimSpace(raw.Bytes()), []byte("\n")) {
		if len(line) == 0 {
			continue
		}
		var record map[string]any
		if err := json.Unmarshal(line, &record); err != nil {
			t.Fatalf("undecodable record %q: %v", line, err)
		}
		out = append(out, record)
	}
	return out
}

// An outcome's level is the whole point of recording it separately: a store
// this gateway cannot open is an outage its operator must act on, while a
// spent invitation is the enrolling user's problem. Reporting both the same
// way is what the record was added to stop.
func TestEnrollmentOutcomesAreRecordedAtTheirOwnLevel(t *testing.T) {
	for _, test := range []struct {
		name    string
		outcome identity.EnrollmentOutcome
		level   string
	}{
		{"rejected", identity.EnrollmentRejected, "WARN"},
		{"store unavailable", identity.EnrollmentUnavailable, "ERROR"},
		{"malformed", identity.EnrollmentMalformed, "INFO"},
	} {
		t.Run(test.name, func(t *testing.T) {
			server, records := enrollmentRecorder(t)
			server.recordEnrollment("enrollment", identity.EnrollmentResult{Outcome: test.outcome}, errors.New("cause"))
			written := decodeRecords(t, records)
			if len(written) != 1 {
				t.Fatalf("wrote %d records, want 1", len(written))
			}
			record := written[0]
			if record["msg"] != "enrollment refused" || record["level"] != test.level {
				t.Fatalf("record = %#v", record)
			}
			if record["outcome"] != string(test.outcome) || record["total"] != float64(1) {
				t.Fatalf("record = %#v", record)
			}
			if record["error"] != "cause" {
				t.Fatalf("the underlying cause was dropped: %#v", record)
			}
		})
	}
}

// A device joining a provider is a rare, durable change to who can use this
// gateway. It must never be summarized away by the rate limiter, however many
// arrive together.
func TestAcceptedEnrollmentsAreNeverSuppressed(t *testing.T) {
	server, records := enrollmentRecorder(t)
	const accepted = 20
	for i := 0; i < accepted; i++ {
		server.recordEnrollment("enrollment", identity.EnrollmentResult{
			Outcome: identity.EnrollmentAccepted, AccountID: "account", DeviceID: "device", DeviceName: "laptop",
		}, nil)
	}
	written := decodeRecords(t, records)
	if len(written) != accepted {
		t.Fatalf("wrote %d records for %d acceptances", len(written), accepted)
	}
	first := written[0]
	if first["msg"] != "enrollment accepted" || first["level"] != "INFO" {
		t.Fatalf("record = %#v", first)
	}
	if first["account_id"] != "account" || first["device_id"] != "device" || first["device_name"] != "laptop" {
		t.Fatalf("acceptance did not name what it created: %#v", first)
	}
}

// A refusal storm must collapse to one readable record carrying its own size,
// and must not take the record of a different outcome down with it.
func TestRefusedEnrollmentStormStaysOneReadableRecord(t *testing.T) {
	server, records := enrollmentRecorder(t)
	const storm = 50
	for i := 0; i < storm; i++ {
		server.recordEnrollment("enrollment", identity.EnrollmentResult{Outcome: identity.EnrollmentRejected}, nil)
	}
	server.recordEnrollmentAdmission("enrollment")
	written := decodeRecords(t, records)
	if len(written) != 2 {
		t.Fatalf("wrote %d records for a storm plus one admission refusal, want 2", len(written))
	}
	if written[0]["outcome"] != string(identity.EnrollmentRejected) || written[0]["total"] != float64(1) {
		t.Fatalf("record = %#v", written[0])
	}
	// The admission refusal is this gateway's own answer and is rate limited
	// apart from anything the store said.
	if written[1]["outcome"] != admissionRefused.String() || written[1]["level"] != "WARN" {
		t.Fatalf("record = %#v", written[1])
	}
	if written[1]["total"] != float64(1) {
		t.Fatalf("admission refusals share a budget with enrollment outcomes: %#v", written[1])
	}
}

// A stranger's attempt must not be able to write a name of their choosing into
// this gateway's log.
func TestRefusedEnrollmentRecordsNothingTheClientChose(t *testing.T) {
	server, records := enrollmentRecorder(t)
	server.recordEnrollment("enrollment", identity.EnrollmentResult{Outcome: identity.EnrollmentRejected}, nil)
	if bytes.Contains(records.Bytes(), []byte("device_name")) {
		t.Fatalf("a refused enrollment carried a client-chosen name: %s", records.String())
	}
}
