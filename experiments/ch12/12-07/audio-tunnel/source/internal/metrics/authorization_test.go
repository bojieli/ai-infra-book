package metrics

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

// Authorization store health had no metric at all, so an outage that refused
// every enrollment was invisible to monitoring while the flow counters stayed
// healthy. These four series are what an alert can be built on.
func TestAuthorizationCountersAreExported(t *testing.T) {
	registry := New()
	lastGood := time.Unix(1700000000, 0)
	registry.AuthorizationRefreshed(lastGood, true)
	registry.AuthorizationRefreshFailed(1)
	registry.AuthorizationRefreshFailed(2)
	registry.AuthorizationRefreshFailed(3)

	snapshot := registry.Snapshot()
	if snapshot.AuthorizationRefreshFailures != 3 {
		t.Fatalf("failures=%d; want 3", snapshot.AuthorizationRefreshFailures)
	}
	if snapshot.AuthorizationConsecutiveRefreshFailures != 3 {
		t.Fatalf("consecutive=%d; want 3", snapshot.AuthorizationConsecutiveRefreshFailures)
	}
	if snapshot.AuthorizationReloads != 1 {
		t.Fatalf("reloads=%d; want 1", snapshot.AuthorizationReloads)
	}
	if snapshot.AuthorizationLastGoodUnix != lastGood.Unix() {
		t.Fatalf("last good=%d; want %d", snapshot.AuthorizationLastGoodUnix, lastGood.Unix())
	}

	recorder := httptest.NewRecorder()
	registry.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/metrics", nil))
	body := recorder.Body.String()
	for _, want := range []string{
		"queqiao_authorization_refresh_failures_total 3",
		"queqiao_authorization_reloads_total 1",
		"queqiao_authorization_consecutive_refresh_failures 3",
		"queqiao_authorization_last_good_timestamp_seconds 1700000000",
	} {
		if !strings.Contains(body, want) {
			t.Fatalf("exposition is missing %q", want)
		}
	}
}

// A recovery has to clear the consecutive gauge, or an alert built on it would
// never resolve.
func TestAuthorizationRecoveryClearsTheConsecutiveGauge(t *testing.T) {
	registry := New()
	registry.AuthorizationRefreshFailed(7)
	if registry.Snapshot().AuthorizationConsecutiveRefreshFailures != 7 {
		t.Fatal("consecutive gauge did not record the run")
	}
	registry.AuthorizationRefreshed(time.Unix(1700000001, 0), false)
	snapshot := registry.Snapshot()
	if snapshot.AuthorizationConsecutiveRefreshFailures != 0 {
		t.Fatalf("consecutive=%d after recovery; want 0", snapshot.AuthorizationConsecutiveRefreshFailures)
	}
	// An unchanged reload is still a successful read, not a reload.
	if snapshot.AuthorizationReloads != 0 {
		t.Fatalf("reloads=%d; want 0", snapshot.AuthorizationReloads)
	}
	if snapshot.AuthorizationRefreshFailures != 1 {
		t.Fatalf("the cumulative failure count must not be reset by recovery: %d", snapshot.AuthorizationRefreshFailures)
	}
}
