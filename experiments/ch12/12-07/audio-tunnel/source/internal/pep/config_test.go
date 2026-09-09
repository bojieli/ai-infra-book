package pep

import (
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"fmt"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/bojieli/queqiao/internal/identity"
	"github.com/bojieli/queqiao/internal/limiter"
	"github.com/bojieli/queqiao/internal/protocol"
)

func TestClientRejectsUnserviceableConfiguration(t *testing.T) {
	_, credentials := testCertificate(t)
	base := ClientConfig{ListenAddr: "127.0.0.1:0", RemoteAddr: "127.0.0.1:1", Credentials: credentials}
	for name, mutate := range map[string]func(*ClientConfig){
		"too many sessions":      func(c *ClientConfig) { c.MaxSessions = maxConfiguredSessions + 1 },
		"too many pending opens": func(c *ClientConfig) { c.MaxPendingOpens = maxConfiguredSessions + 1 },
		"invalid local address":  func(c *ClientConfig) { c.LocalAddress = "not-an-address" },
		"empty local interface":  func(c *ClientConfig) { c.LocalAddress = "if:" },
		"too many TCP lanes":     func(c *ClientConfig) { c.TCPFallbackLanes = maxTCPFallbackLanes + 1 },
		"adaptive bounds":        func(c *ClientConfig) { c.AdaptiveMinBytesSec = 2; c.AdaptiveMaxBytesSec = 1 },
		"reserve without budget": func(c *ClientConfig) {
			c.InteractiveReserveBytesPerSec = 1
		},
		"reserve above budget": func(c *ClientConfig) {
			c.AggregateBytesPerSec = 1
			c.InteractiveReserveBytesPerSec = 2
		},
		"reserve consumes whole budget": func(c *ClientConfig) {
			c.AggregateBytesPerSec = 2
			c.InteractiveReserveBytesPerSec = 2
		},
		"idle exceeds lifetime": func(c *ClientConfig) {
			c.FlowIdleTimeout = 2 * time.Second
			c.FlowMaxLifetime = time.Second
		},
	} {
		t.Run(name, func(t *testing.T) {
			cfg := base
			mutate(&cfg)
			if _, err := NewClient(cfg); err == nil {
				t.Fatal("invalid configuration was accepted")
			}
		})
	}
}

func TestClientAdmissionDefaultsAndPendingOpenBound(t *testing.T) {
	_, credentials := testCertificate(t)
	client, err := NewClient(ClientConfig{
		ListenAddr: "127.0.0.1:0", RemoteAddr: "127.0.0.1:1", Credentials: credentials,
	})
	if err != nil {
		t.Fatal(err)
	}
	if client.cfg.MaxSessions != defaultClientMaxSessions {
		t.Fatalf("client default sessions = %d, want %d", client.cfg.MaxSessions, defaultClientMaxSessions)
	}
	if client.cfg.MaxPendingOpens != defaultMaxPendingOpens || cap(client.pendingOpens) != defaultMaxPendingOpens {
		t.Fatalf("client default pending opens = %d/%d, want %d", client.cfg.MaxPendingOpens, cap(client.pendingOpens), defaultMaxPendingOpens)
	}

	client.pendingOpens = make(chan struct{}, 2)
	for admitted := 0; admitted < 2; admitted++ {
		if !client.admitPendingOpen() {
			t.Fatalf("configured pending-open capacity stopped after %d admissions", admitted)
		}
	}
	if client.admitPendingOpen() {
		t.Fatal("pending-open capacity was exceeded")
	}
	client.releasePendingOpen()
	if !client.admitPendingOpen() {
		t.Fatal("released pending-open capacity was not reusable")
	}
}

func TestClientSessionLimitCanBeShared(t *testing.T) {
	_, credentials := testCertificate(t)
	limit, err := NewSessionLimit(1)
	if err != nil {
		t.Fatal(err)
	}
	clients := make([]*Client, 2)
	for i := range clients {
		clients[i], err = NewClient(ClientConfig{
			ListenAddr: "127.0.0.1:0", RemoteAddr: "127.0.0.1:1",
			Credentials: credentials, SessionLimit: limit,
		})
		if err != nil {
			t.Fatal(err)
		}
	}
	slot, admitted := clients[0].sessionLimit.acquire()
	if !admitted {
		t.Fatal("first client was not admitted")
	}
	if _, admitted := clients[1].sessionLimit.acquire(); admitted {
		t.Fatal("second client exceeded the shared session limit")
	}
	slot.release()
	sibling, admitted := clients[1].sessionLimit.acquire()
	if !admitted {
		t.Fatal("released shared session slot was not reusable")
	}
	sibling.release()
}

func TestSharedSessionLimitsReserveCapacityPerClient(t *testing.T) {
	limits, err := NewSharedSessionLimits(8, 2)
	if err != nil {
		t.Fatal(err)
	}
	if limits[0].Reserved() != 2 || limits[1].Reserved() != 2 {
		t.Fatalf("reservations = %d and %d, want 2 each", limits[0].Reserved(), limits[1].Reserved())
	}
	// The first client drains its own reservation and then the common pool.
	var held []sessionSlot
	for range 6 {
		slot, admitted := limits[0].acquire()
		if !admitted {
			t.Fatalf("greedy client was capped at %d sessions, want its reservation plus the common pool", len(held))
		}
		held = append(held, slot)
	}
	if _, admitted := limits[0].acquire(); admitted {
		t.Fatal("greedy client exceeded the combined limit")
	}
	// Its sibling still has its own reservation, which is the whole point: a
	// failover target which cannot accept a session is not a failover target.
	for i := range 2 {
		if _, admitted := limits[1].acquire(); !admitted {
			t.Fatalf("reserved slot %d was consumed by the busy sibling", i+1)
		}
	}
	if _, admitted := limits[1].acquire(); admitted {
		t.Fatal("sibling exceeded its reservation while the common pool was empty")
	}
	for _, slot := range held {
		slot.release()
	}
}

func TestSharedSessionLimitsStayCommonWhenTooSmallToReserve(t *testing.T) {
	limits, err := NewSharedSessionLimits(3, 4)
	if err != nil {
		t.Fatal(err)
	}
	for i, limit := range limits {
		if limit.Reserved() != 0 {
			t.Fatalf("client %d reserved %d slots from a budget too small to divide", i, limit.Reserved())
		}
	}
	admitted := 0
	for _, limit := range limits {
		if _, ok := limit.acquire(); ok {
			admitted++
		}
	}
	if admitted != 3 {
		t.Fatalf("admitted %d sessions, want the whole common budget of 3", admitted)
	}
}

func TestNewClientRejectsUninitializedSharedSessionLimit(t *testing.T) {
	_, credentials := testCertificate(t)
	_, err := NewClient(ClientConfig{
		ListenAddr: "127.0.0.1:0", RemoteAddr: "127.0.0.1:1",
		Credentials: credentials, SessionLimit: &SessionLimit{},
	})
	if err == nil || !strings.Contains(err.Error(), "not initialized") {
		t.Fatalf("uninitialized shared session limit was accepted: %v", err)
	}
}

func TestClientsCanShareOneAggregateBudget(t *testing.T) {
	_, credentials := testCertificate(t)
	budget := NewAggregateBudget(1<<20, 0)
	if budget == nil {
		t.Fatal("aggregate budget was not built")
	}
	clients := make([]*Client, 2)
	for i := range clients {
		client, err := NewClient(ClientConfig{
			ListenAddr: "127.0.0.1:0", RemoteAddr: "127.0.0.1:1",
			Credentials: credentials, AggregateBytesPerSec: 1 << 20, Budget: budget,
		})
		if err != nil {
			t.Fatal(err)
		}
		clients[i] = client
	}
	if clients[0].budget != budget || clients[1].budget != budget {
		t.Fatal("clients did not share the supplied aggregate budget")
	}
}

func TestClientCredentialUpdateCannotChangeIdentity(t *testing.T) {
	_, credentials := testCertificate(t)
	client, err := NewClient(ClientConfig{
		ListenAddr: "127.0.0.1:0", RemoteAddr: "127.0.0.1:1", Credentials: credentials,
	})
	if err != nil {
		t.Fatal(err)
	}
	if err := client.UpdateCredentials(credentials); err != nil {
		t.Fatalf("same-device credential refresh failed: %v", err)
	}
	_, other := testCertificate(t)
	if err := client.UpdateCredentials(other); err == nil {
		t.Fatal("credential update changed the client trust domain and device")
	}
}

func TestCodedDataGetsOneReliableSafetyCopyBeforeOpenConfirmation(t *testing.T) {
	frameConn := &frameConn{}
	unconfirmed := true
	frameConn.setOpenSafetyPolicy(func() bool { return unconfirmed })
	data := protocol.Frame{Header: protocol.Header{Type: protocol.TypeData}}
	if !frameConn.needsOpenSafetyCopy(data) {
		t.Fatal("first pre-confirmation coded frame had no reliable safety copy")
	}
	if frameConn.needsOpenSafetyCopy(data) {
		t.Fatal("pre-confirmation safety copy was not bounded to one frame")
	}
	frameConn.setOpenSafetyPolicy(func() bool { return false })
	if frameConn.needsOpenSafetyCopy(data) {
		t.Fatal("confirmed flow retained an unnecessary safety copy")
	}
}

// admissionFixture is an account with limits and the given number of enrolled
// devices, plus a server holding only the admission state under test.
func admissionFixture(t *testing.T, limits identity.AccountLimits, devices int) (*Server, []identity.Principal) {
	t.Helper()
	store, err := identity.NewStore(filepath.Join(t.TempDir(), "authorization.json"))
	if err != nil || store.Initialize() != nil {
		t.Fatal(err)
	}
	now := time.Now()
	account, err := store.AddAccount("alice", time.Time{}, limits, now)
	if err != nil {
		t.Fatal(err)
	}
	principals := make([]identity.Principal, 0, devices)
	for i := 0; i < devices; i++ {
		publicKey, _, _ := ed25519.GenerateKey(rand.Reader)
		_, token, _ := store.CreateInvite(account.ID, time.Hour, now)
		_, device, err := store.ConsumeInvite(token, fmt.Sprintf("device-%d", i), publicKey, now)
		if err != nil {
			t.Fatal(err)
		}
		principals = append(principals, identity.Principal{AccountID: account.ID, DeviceID: device.ID, PublicKey: publicKey})
	}
	server := &Server{
		cfg:          ServerConfig{Credentials: identity.ServerCredentials{Store: store}},
		accountUsage: make(map[string]*accountUsage),
	}
	return server, principals
}

func TestPerUserFlowLimitSpansDevicesAndReleases(t *testing.T) {
	server, principals := admissionFixture(t, identity.AccountLimits{MaxFlows: 1}, 2)
	laptop, phone := principals[0], principals[1]
	if refusal := server.admitAccountFlow(laptop); refusal != nil {
		t.Fatalf("first flow refused: %v", refusal)
	}
	if refusal := server.admitAccountFlow(laptop); refusal != errAccountFlowLimit {
		t.Fatalf("second flow refusal = %v, want the flow limit", refusal)
	}
	// The limit is the account's, not the device's: a second device does not
	// get its own allowance.
	if refusal := server.admitAccountFlow(phone); refusal != errAccountFlowLimit {
		t.Fatalf("another device's flow refusal = %v, want the flow limit", refusal)
	}
	server.releaseAccountFlow(laptop)
	if refusal := server.admitAccountFlow(phone); refusal != nil {
		t.Fatalf("released flow slot was not reusable: %v", refusal)
	}
	server.releaseAccountFlow(phone)
	if len(server.accountUsage) != 0 {
		t.Fatalf("account usage retained after every flow was released: %#v", server.accountUsage)
	}
}

// The limit an operator reaches for when they mean "this account is for N
// devices" must count devices. A device that opens a page's worth of
// connections is still one device, and this is the property that makes the
// client limit usable where a flow limit is not.
func TestPerUserClientLimitCountsDevicesNotFlows(t *testing.T) {
	server, principals := admissionFixture(t, identity.AccountLimits{MaxClients: 1}, 2)
	laptop, phone := principals[0], principals[1]
	for i := 0; i < 200; i++ {
		if refusal := server.admitAccountFlow(laptop); refusal != nil {
			t.Fatalf("flow %d from the only admitted device refused: %v", i, refusal)
		}
	}
	if refusal := server.admitAccountFlow(phone); refusal != errAccountClientLimit {
		t.Fatalf("second device refusal = %v, want the client limit", refusal)
	}
	// The slot frees only when the device stops holding flows entirely.
	for i := 0; i < 199; i++ {
		server.releaseAccountFlow(laptop)
	}
	if refusal := server.admitAccountFlow(phone); refusal != errAccountClientLimit {
		t.Fatalf("second device admitted while the first still held a flow: %v", refusal)
	}
	server.releaseAccountFlow(laptop)
	if refusal := server.admitAccountFlow(phone); refusal != nil {
		t.Fatalf("device slot was not reusable once released: %v", refusal)
	}
}

// A refused open must leave nothing behind. Otherwise an account that is
// refused repeatedly accumulates state for flows it never got.
func TestRefusedFlowLeavesNoAccountState(t *testing.T) {
	server, principals := admissionFixture(t, identity.AccountLimits{MaxClients: 1}, 2)
	if refusal := server.admitAccountFlow(principals[0]); refusal != nil {
		t.Fatalf("first flow refused: %v", refusal)
	}
	server.releaseAccountFlow(principals[0])
	if refusal := server.admitAccountFlow(principals[1]); refusal != nil {
		t.Fatalf("device slot was not free after release: %v", refusal)
	}
	server.releaseAccountFlow(principals[1])
	if len(server.accountUsage) != 0 {
		t.Fatalf("account usage retained: %#v", server.accountUsage)
	}
}

// Zero means "no per-account limit", not "no flows".
func TestZeroAccountLimitsAdmitEverything(t *testing.T) {
	server, principals := admissionFixture(t, identity.AccountLimits{}, 3)
	for i := 0; i < 50; i++ {
		for _, principal := range principals {
			if refusal := server.admitAccountFlow(principal); refusal != nil {
				t.Fatalf("unlimited account refused a flow: %v", refusal)
			}
		}
	}
}

func TestTUICAlignedCongestionConfigurationIsAccepted(t *testing.T) {
	_, credentials := testCertificate(t)
	base := ClientConfig{
		ListenAddr: "127.0.0.1:0", RemoteAddr: "127.0.0.1:1",
		Credentials: credentials, Congestion: CongestionBBRTUIC,
	}
	if _, err := NewClient(base); err != nil {
		t.Fatalf("bbr-tuic configuration rejected: %v", err)
	}
}

func TestServerRejectsUnserviceableConfiguration(t *testing.T) {
	credentials, _ := testCertificate(t)
	base := ServerConfig{ListenAddr: "127.0.0.1:0", Credentials: credentials}
	for name, mutate := range map[string]func(*ServerConfig){
		"too many sessions": func(c *ServerConfig) { c.MaxSessions = maxConfiguredSessions + 1 },
		"adaptive bounds":   func(c *ServerConfig) { c.AdaptiveMinBytesSec = 2; c.AdaptiveMaxBytesSec = 1 },
		"too many TCP lanes": func(c *ServerConfig) {
			c.TCPFallbackLanes = maxTCPFallbackLanes + 1
		},
		"invalid TCP congestion name": func(c *ServerConfig) { c.TCPCongestion = "bbr;no" },
		"reserve without budget": func(c *ServerConfig) {
			c.InteractiveReserveBytesPerSec = 1
		},
		"reserve above budget": func(c *ServerConfig) {
			c.AggregateBytesPerSec = 1
			c.InteractiveReserveBytesPerSec = 2
		},
		"reserve consumes whole budget": func(c *ServerConfig) {
			c.AggregateBytesPerSec = 2
			c.InteractiveReserveBytesPerSec = 2
		},
		"idle exceeds lifetime": func(c *ServerConfig) {
			c.FlowIdleTimeout = 2 * time.Second
			c.FlowMaxLifetime = time.Second
		},
	} {
		t.Run(name, func(t *testing.T) {
			cfg := base
			mutate(&cfg)
			if _, err := NewServer(cfg); err == nil {
				t.Fatal("invalid configuration was accepted")
			}
		})
	}
}

func TestTCPFallbackRoleDefaultsAreConservativeAtTheClient(t *testing.T) {
	serverCredentials, clientCredentials := testCertificate(t)
	client, err := NewClient(ClientConfig{
		ListenAddr: "127.0.0.1:0", RemoteAddr: "127.0.0.1:1", Credentials: clientCredentials,
	})
	if err != nil {
		t.Fatal(err)
	}
	if client.cfg.TCPFallbackLanes != 1 {
		t.Fatalf("client default TCP lanes = %d, want conservative one", client.cfg.TCPFallbackLanes)
	}

	server, err := NewServer(ServerConfig{
		ListenAddr: "127.0.0.1:0", Credentials: serverCredentials,
	})
	if err != nil {
		t.Fatal(err)
	}
	if server.cfg.TCPFallbackLanes != maxTCPFallbackLanes {
		t.Fatalf("server default TCP lane ceiling = %d, want %d", server.cfg.TCPFallbackLanes, maxTCPFallbackLanes)
	}
}

func TestTCPFallbackCongestionNameNormalization(t *testing.T) {
	for input, want := range map[string]string{"": "system", " SYSTEM ": "system", " BBR ": "bbr", "bbr2": "bbr2"} {
		got, err := normalizeTCPCongestion(input)
		if err != nil {
			t.Fatalf("normalize %q: %v", input, err)
		}
		if got != want {
			t.Fatalf("normalize %q = %q, want %q", input, got, want)
		}
	}
}

func TestQUICConnectionsHaveAnAdmissionBound(t *testing.T) {
	credentials, _ := testCertificate(t)
	server, err := NewServer(ServerConfig{
		ListenAddr: "127.0.0.1:0", Credentials: credentials, MaxSessions: 2,
	})
	if err != nil {
		t.Fatal(err)
	}
	if !server.admitConnection() {
		t.Fatal("the first configured connection slot was not admitted")
	}
	if !server.admitConnection() {
		t.Fatal("the configured connection capacity was not admitted")
	}
	if server.admitConnection() {
		t.Fatal("an unauthenticated QUIC connection exceeded the admission bound")
	}
	server.releaseConnection()
	if !server.admitConnection() {
		t.Fatal("released QUIC connection capacity was not reusable")
	}
}

func TestServerQUICStreamCapacitySupportsMobileSessions(t *testing.T) {
	config := quicServerConfig(flowWindows{})
	if config.MaxIncomingStreams < 1024 {
		t.Fatalf("server QUIC stream capacity = %d, want at least 1024", config.MaxIncomingStreams)
	}
}

// A chunk larger than the aggregate budget's burst can never be admitted: the
// budget refuses it outright rather than pacing it, the DATA frame carrying it
// fails to enqueue, and the lane that was carrying it is failed and retired.
// The configured chunk size is corrected to what the budget can carry so that
// an operator's rate limit slows the endpoint down instead of taking its lanes
// apart.
func TestChunkSizeIsCappedByAggregateBurst(t *testing.T) {
	serverCredentials, clientCredentials := testCertificate(t)
	// 128 KiB chunks against 64 KiB/s: a quarter-second burst is well under
	// the 64 KiB floor, so the floor is the ceiling and every chunk as
	// configured would have been refused.
	const rate = 64 * 1024
	newEndpoints := func(t *testing.T, aggregate uint64) (int, *limiter.Budget, int, *limiter.Budget) {
		t.Helper()
		client, err := NewClient(ClientConfig{
			ListenAddr: "127.0.0.1:0", RemoteAddr: "127.0.0.1:1", Credentials: clientCredentials,
			ChunkSize: protocol.MaxPayload, AggregateBytesPerSec: aggregate,
		})
		if err != nil {
			t.Fatal(err)
		}
		server, err := NewServer(ServerConfig{
			ListenAddr: "127.0.0.1:0", Credentials: serverCredentials,
			ChunkSize: protocol.MaxPayload, AggregateBytesPerSec: aggregate,
		})
		if err != nil {
			t.Fatal(err)
		}
		return client.cfg.ChunkSize, client.budget, server.cfg.ChunkSize, server.budget
	}

	clientChunk, clientBudget, serverChunk, serverBudget := newEndpoints(t, rate)
	for name, endpoint := range map[string]struct {
		chunkSize int
		budget    *limiter.Budget
	}{
		"client": {clientChunk, clientBudget},
		"server": {serverChunk, serverBudget},
	} {
		t.Run(name, func(t *testing.T) {
			if endpoint.chunkSize >= protocol.MaxPayload {
				t.Fatalf("chunk size %d was not capped by the aggregate burst", endpoint.chunkSize)
			}
			// A cap, not a collapse: a budget that admits bulk at all admits a
			// whole 64 KiB frame of it, so the correction never leaves the
			// endpoint sending uselessly small chunks.
			if endpoint.chunkSize < 64*1024 {
				t.Fatalf("chunk size %d narrowed below the burst floor", endpoint.chunkSize)
			}
			if err := endpoint.budget.Wait(context.Background(), endpoint.chunkSize, false); err != nil {
				t.Fatalf("a full chunk was not admitted by its own budget: %v", err)
			}
		})
	}

	// Without a budget there is nothing to fit inside, and the chunk size the
	// operator asked for is the one they get.
	unpacedClient, _, unpacedServer, _ := newEndpoints(t, 0)
	if unpacedClient != protocol.MaxPayload || unpacedServer != protocol.MaxPayload {
		t.Fatalf("unpaced chunk sizes = %d/%d, want %d", unpacedClient, unpacedServer, protocol.MaxPayload)
	}
}

func TestSharedBudgetCapsChunkSizeForEveryClient(t *testing.T) {
	_, credentials := testCertificate(t)
	// Small enough that the burst floor, not the configured chunk, decides.
	const aggregate = 100 << 10
	budget := NewAggregateBudget(aggregate, 0)
	shared := make([]*Client, 2)
	for i := range shared {
		client, err := NewClient(ClientConfig{
			ListenAddr: "127.0.0.1:0", RemoteAddr: "127.0.0.1:1", Credentials: credentials,
			ChunkSize: protocol.MaxPayload, AggregateBytesPerSec: aggregate, Budget: budget,
		})
		if err != nil {
			t.Fatal(err)
		}
		shared[i] = client
	}
	// The cap has to come from the budget the flows will really admit against.
	// Measuring it against a budget each client built for itself would let a
	// shared budget admit chunks it then refuses outright, retiring lanes.
	solo, err := NewClient(ClientConfig{
		ListenAddr: "127.0.0.1:0", RemoteAddr: "127.0.0.1:1", Credentials: credentials,
		ChunkSize: protocol.MaxPayload, AggregateBytesPerSec: aggregate,
	})
	if err != nil {
		t.Fatal(err)
	}
	want := solo.cfg.ChunkSize
	if want >= protocol.MaxPayload {
		t.Fatalf("aggregate %d did not cap the chunk size, so this test proves nothing", aggregate)
	}
	for i, client := range shared {
		if client.budget != budget {
			t.Fatalf("client %d did not use the shared budget", i)
		}
		if client.cfg.ChunkSize != want {
			t.Fatalf("client %d chunk size = %d, want %d from the shared budget", i, client.cfg.ChunkSize, want)
		}
		if client.cfg.ChunkSize > budget.MaxRequest(false) {
			t.Fatalf("client %d chunk size %d exceeds what the shared budget admits", i, client.cfg.ChunkSize)
		}
	}
}
