//go:build linux

package userfaultfd

import (
	"context"
	"errors"
	"fmt"
	"math/rand"
	"sync"
	"sync/atomic"
	"syscall"
	"time"
	"unsafe"

	"github.com/RoaringBitmap/roaring/v2"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/trace"
	"go.uber.org/zap"
	"golang.org/x/sync/errgroup"
	"golang.org/x/sys/unix"

	"github.com/e2b-dev/infra/packages/orchestrator/pkg/sandbox/block"
	"github.com/e2b-dev/infra/packages/orchestrator/pkg/sandbox/uffd/fdexit"
	"github.com/e2b-dev/infra/packages/orchestrator/pkg/sandbox/uffd/memory"
	"github.com/e2b-dev/infra/packages/shared/pkg/logger"
	"github.com/e2b-dev/infra/packages/shared/pkg/storage/header"
)

var tracer = otel.Tracer("github.com/e2b-dev/infra/packages/orchestrator/pkg/sandbox/uffd/userfaultfd")

const maxRequestsInProgress = 4096

// maxWPResolvesInProgress bounds the dedicated WP-resolve pool. A plain
// resolve is a single ioctl; a resolve that captures into a CoW window also
// copies one page (read + unlocked sink write), so during a window the bound
// additionally caps concurrent page copies. It still mainly guards against
// pathological fault storms.
const maxWPResolvesInProgress = 256

// wpResolveRetryDelay paces the redispatch of a WP resolve that hit
// mmap_changing, bounding the serve loop's self-wake spin while an address-
// space change (madvise batch) is in flight.
const wpResolveRetryDelay = 250 * time.Microsecond

// wpResolveErrEscalation is the number of consecutive failed unprotects OF
// THE SAME PAGE (reset by that page resolving) after which the handler stops
// treating the failure as transient and fails the serve loop: the wake→
// re-fault retry would otherwise livelock the guest writer forever on a
// deterministic failure. Per-page, not global: a burst of concurrent
// transient failures across different pages (each writer woken, each
// recovering on re-fault) must not be mistaken for a livelock.
const wpResolveErrEscalation = 8

const (
	// sliceMaxRetries is the number of times to retry source.Slice() after the initial attempt.
	// Total attempts = sliceMaxRetries + 1.
	sliceMaxRetries = 3
	// sliceRetryBaseDelay is the initial backoff delay before the first retry.
	// Subsequent retries double the delay (exponential backoff), capped at sliceRetryMaxDelay.
	sliceRetryBaseDelay = 50 * time.Millisecond
	// sliceRetryMaxDelay is the maximum backoff delay between retries.
	sliceRetryMaxDelay = 500 * time.Millisecond
)

// errWPResolveAgain reports that a WP resolve hit EAGAIN (the address space
// is changing, mmap_changing); the caller re-queues the fault via the
// deferred queue instead of retrying in place — a worker sleeping under
// settleRequests.RLock would block the REMOVE batch whose completion clears
// the condition.
var errWPResolveAgain = errors.New("uffd WP resolve: address space changing")

var ErrUnexpectedEventType = errors.New("unexpected event type")

// ErrClosed reports that the userfaultfd was already closed (sandbox
// teardown) and the requested operation was skipped.
var ErrClosed = errors.New("userfaultfd is closed")

func hasEvent(revents, event int16) bool {
	return revents&event != 0
}

// PageReader is the data source UFFD pulls page contents from on a fault.
type PageReader interface {
	ReadAt(ctx context.Context, p []byte, off int64) (int, error)
}

// pagePool returns HugepageSize-sized scratch buffers shared across all UFFD
// instances. 4 KiB-page UFFDs allocate per fault instead.
var pagePool = sync.Pool{
	New: func() any {
		buf := make([]byte, header.HugepageSize)

		return &buf
	},
}

type Userfaultfd struct {
	fd Fd

	src         PageReader
	ma          *memory.Mapping
	pageSize    uintptr
	pageTracker *block.Tracker

	// settleRequests guards the pageTracker / prefetchTracker. Workers take
	// RLock for the lookup→install→SetRange sequence; the REMOVE batch takes
	// Lock so a concurrent worker can't overwrite a removed state. The lock
	// cannot order a batch against an install that completed while the batch
	// WAITED, so a batch may record Removed for a page a racing reinstall
	// already re-populated — the WP resolve's presence probe disambiguates
	// that reading against the kernel.
	settleRequests sync.RWMutex

	// readSerial serializes serve-loop iterations (read+apply) with snapshot-time
	// Export. Workers do NOT touch this lock — it must remain disjoint from
	// settleRequests so readEvents can always drain the kernel UFFD queue and
	// unblock madvise even when settleRequests.RLock is held by an in-flight
	// worker. See TestNoMadviseDeadlockWithInflightCopy.
	readSerial sync.Mutex

	prefetchTracker *block.PrefetchTracker

	// defaultCopyMode overrides UFFDIO_COPY mode for all faults when non-zero.
	defaultCopyMode CULong

	wg errgroup.Group

	// wgWP is a dedicated pool for write-protect resolves. WP resolves are
	// microsecond ioctls, but the shared pool's MISSING workers can hold a
	// slot through seconds of source-read backoff — a full pool would then
	// queue guest writes to already-present pages behind slow fetches.
	wgWP errgroup.Group

	// wakeupPipe is a self-pipe that wakes the poll loop after a worker
	// defers a fault, so a deferred fault isn't orphaned waiting for the
	// next unrelated UFFD event.
	wakeupPipe [2]int

	// testFaultHook is set only by SetTestFaultHook in test builds.
	testFaultHook atomic.Pointer[func(uintptr, faultPhase)]

	// closed is set by Close() under settleRequests.Lock(). Prefault() checks
	// it under settleRequests.RLock() so it never calls UFFDIO_COPY on a fd
	// that has already been closed (and potentially recycled by the OS).
	closed bool

	// Cumulative demand-fault serve counters, read via ServeStats(). They
	// mirror the orchestrator.sandbox.uffd.serve metric but as a per-handler
	// snapshot, so a caller can sample "how many pages did this guest need so
	// far" at a point in time (e.g. the moment envd init returns). Prefaults
	// bypass the serve loop and are not counted here. See recordServeStats.
	servedPages       atomic.Int64 // faults resolved (installed or already-present)
	servedSourcePages atomic.Int64 // subset installed from the source (page_class=new)
	servedBytes       atomic.Int64 // bytes installed into the guest (new + zero)

	// genBucket tags this sandbox's serve/prefault metrics with its snapshot
	// generation range, so fault latency can be cut by chain depth.
	genBucket generationBucket

	// wpFaultsResolved counts synchronous userfault write-protect faults resolved
	// (non-zero only when paired with a sync-WP Firecracker that omits WP_ASYNC).
	wpFaultsResolved atomic.Int64

	// wpResolveErrPages counts consecutive failed unprotects per page
	// (entry removed when that page resolves). A transient failure
	// self-heals via wake→re-fault; a deterministic one re-fails the SAME
	// page repeatedly, so a per-page streak reaching wpResolveErrEscalation
	// escalates to a serve-loop exit. wpResolveErrPending gates the success
	// path: it stays lock-free until at least one failure is outstanding.
	wpResolveErrMu      sync.Mutex
	wpResolveErrPages   map[uintptr]int32
	wpResolveErrPending atomic.Int32

	// cowWindow, when set, owns pre-image capture for an in-flight deferred
	// memory export: WP resolves for its pages copy the pause-time content to
	// the export sink BEFORE unprotecting (see resolveWriteProtect). Installed
	// by BeginCoWExport while the guest is paused; cleared by EndCoWExport.
	cowWindow atomic.Pointer[CoWWindow]

	logger logger.Logger
}

// NewStateOnly builds a handler around an existing page tracker with NO
// userfaultfd behind it, for tests and tooling that exercise the state-export
// surface (ExportPageStates, PageSize, Logger, WPFaultsResolved). Serving,
// prefaulting or resolving faults on a state-only handler would ioctl a zero
// fd and must not be attempted.
func NewStateOnly(tracker *block.Tracker, pageSize uintptr, lg logger.Logger) *Userfaultfd {
	return &Userfaultfd{
		pageSize:    pageSize,
		pageTracker: tracker,
		logger:      lg,
	}
}

// faultPhase identifies the worker fault hook call site (test-only).
type faultPhase uint8

const (
	faultPhaseBeforeRLock faultPhase = iota
	faultPhaseBeforeFaultPage
	// faultPhaseBeforePrefaultRLock fires inside Prefault(), before acquiring
	// settleRequests.RLock. Used by TestPrefaultConcurrentWithClose to park
	// Prefault here, call Close() concurrently, and verify the closed flag is
	// checked after the RLock is acquired.
	faultPhaseBeforePrefaultRLock
)

// faultOutcome is the terminal classification of a faultPage call.
type faultOutcome uint8

const (
	// faultInstalled: page was installed by this call.
	faultInstalled faultOutcome = iota
	// faultAlreadyPresent: no install by this call — the page was already
	// mapped (EEXIST), e.g. a concurrent worker or a prefault won the race.
	faultAlreadyPresent
	// faultDeferred: soft failure (EAGAIN); the caller must retry later.
	faultDeferred
	// faultDiscarded: no install happened and retry is pointless
	// (e.g. ESRCH — the faulting thread is gone).
	faultDiscarded
)

// NewUserfaultfdFromFd creates a new userfaultfd instance. Page size is
// taken from the FC-registered regions; all regions must agree. generation is
// the snapshot's pause/resume cycle count (Metadata.Generation), used only to
// tag this instance's metrics.
func NewUserfaultfdFromFd(fd uintptr, src PageReader, m *memory.Mapping, generation uint64, logger logger.Logger) (*Userfaultfd, error) {
	if len(m.Regions) == 0 {
		return nil, errors.New("memory mapping has no regions")
	}
	pageSize := m.Regions[0].PageSize
	if pageSize != header.PageSize && pageSize != header.HugepageSize {
		return nil, fmt.Errorf("unsupported page size: %d", pageSize)
	}
	for _, r := range m.Regions[1:] {
		if r.PageSize != pageSize {
			return nil, fmt.Errorf("region page size mismatch: %d != %d for region %d", r.PageSize, pageSize, r.BaseHostVirtAddr)
		}
	}

	var wakeupPipe [2]int
	if err := syscall.Pipe2(wakeupPipe[:], syscall.O_NONBLOCK|syscall.O_CLOEXEC); err != nil {
		return nil, fmt.Errorf("failed to create wakeup pipe: %w", err)
	}

	u := &Userfaultfd{
		fd:              Fd(fd),
		src:             src,
		pageSize:        pageSize,
		pageTracker:     block.NewTracker(),
		prefetchTracker: block.NewPrefetchTracker(int64(pageSize)),
		ma:              m,
		wakeupPipe:      wakeupPipe,
		genBucket:       bucketForGeneration(generation),
		logger:          logger,
	}
	u.wg.SetLimit(maxRequestsInProgress)
	u.wgWP.SetLimit(maxWPResolvesInProgress)

	return u, nil
}

// Logger returns this handler's logger, already tagged with the sandbox ID.
func (u *Userfaultfd) Logger() logger.Logger {
	return u.logger
}

// WPFaultsResolved returns the number of synchronous write-protect faults
// this handler has resolved — non-zero only when the paired Firecracker
// registered guest memory for sync WP delivery.
func (u *Userfaultfd) WPFaultsResolved() int64 {
	return u.wpFaultsResolved.Load()
}

// ExportPageStates returns snapshots of the tracker's dirty and empty
// (zero ∪ removed) page-index bitmaps after draining in-flight serve-loop
// iterations and workers. Clean pages appear in NEITHER set: their content
// matches the source, so a snapshot diff inherits them from the parent
// layer. Lock order matches the serve loop to avoid AB-BA inversion.
func (u *Userfaultfd) ExportPageStates() (dirty, empty *roaring.Bitmap) {
	u.readSerial.Lock()
	defer u.readSerial.Unlock()

	u.settleRequests.Lock()
	defer u.settleRequests.Unlock()

	return u.pageTracker.Export()
}

func (u *Userfaultfd) readEvents(ctx context.Context) ([]*UffdRemove, []*UffdPagefault, error) {
	buf := make([]byte, unsafe.Sizeof(UffdMsg{}))

	var removes []*UffdRemove
	var pagefaults []*UffdPagefault

	for {
		n, err := syscall.Read(int(u.fd), buf)
		if errors.Is(err, syscall.EINTR) {
			u.logger.Debug(ctx, "uffd: interrupted read. Reading again")

			continue
		}

		if errors.Is(err, syscall.EAGAIN) {
			break
		}

		if err != nil {
			return nil, nil, fmt.Errorf("failed reading uffd: %w", err)
		}

		if n == 0 {
			break
		}

		msg := (*UffdMsg)(unsafe.Pointer(&buf[0]))

		event := getMsgEvent(msg)
		arg := getMsgArg(msg)

		switch event {
		case UFFD_EVENT_PAGEFAULT:
			v := *(*UffdPagefault)(unsafe.Pointer(&arg[0]))
			pagefaults = append(pagefaults, &v)
		case UFFD_EVENT_REMOVE:
			v := *(*UffdRemove)(unsafe.Pointer(&arg[0]))
			removes = append(removes, &v)
		default:
			return nil, nil, ErrUnexpectedEventType
		}
	}

	return removes, pagefaults, nil
}

func (u *Userfaultfd) Serve(
	ctx context.Context,
	fdExit *fdexit.FdExit,
) error {
	var deferred deferredFaults

	// Workers spawned via the pools may still be running when an error path
	// returns early. Drain them before returning so a worker can't outlive
	// Serve and race with Close() on wakeupPipe / the uffd fd. Then wake any
	// fault still parked in the deferred queue: the kernel never redelivers
	// it, so a guest thread blocked on it would otherwise have no retry
	// signal until the uffd itself closes. The wake makes it re-fault; if
	// this handler is gone the close releases it.
	defer func() {
		_ = u.wg.Wait()
		_ = u.wgWP.Wait()
		for _, pf := range deferred.drain() {
			addr := getPagefaultAddress(pf)
			_ = u.fd.wake(addr&^(u.pageSize-1), u.pageSize)
		}
	}()

	pollFds := []unix.PollFd{
		{Fd: int32(u.fd), Events: unix.POLLIN},
		{Fd: fdExit.Reader(), Events: unix.POLLIN},
		{Fd: int32(u.wakeupPipe[0]), Events: unix.POLLIN},
	}

	emptyDrainCounter := newCounterReporter(u.logger, "uffd: empty drain (spurious wakeup) (accumulated)")
	defer emptyDrainCounter.Close(ctx)

	noDataCounter := newCounterReporter(u.logger, "uffd: no data in fd (accumulated)")
	defer noDataCounter.Close(ctx)

	exitFdErrorCounter := newCounterReporter(u.logger, "uffd: exit fd poll errors (accumulated)")
	defer exitFdErrorCounter.Close(ctx)

	uffdErrorCounter := newCounterReporter(u.logger, "uffd: uffd fd poll errors (accumulated)")
	defer uffdErrorCounter.Close(ctx)

	pollErrorEvents := map[int16]string{
		unix.POLLHUP:  "POLLHUP",
		unix.POLLERR:  "POLLERR",
		unix.POLLNVAL: "POLLNVAL",
	}

	for {
		if _, err := unix.Poll(
			pollFds,
			-1,
		); err != nil {
			if err == unix.EINTR {
				u.logger.Debug(ctx, "uffd: interrupted polling, going back to polling")

				continue
			}

			if err == unix.EAGAIN {
				u.logger.Debug(ctx, "uffd: eagain during polling, going back to polling")

				continue
			}

			u.logger.Error(ctx, "UFFD serve polling error", zap.Error(err))

			return fmt.Errorf("failed polling: %w", err)
		}

		exitFd := pollFds[1]
		if hasEvent(exitFd.Revents, unix.POLLIN) {
			errMsg := errors.Join(u.wg.Wait(), u.wgWP.Wait())
			if errMsg != nil {
				u.logger.Warn(ctx, "UFFD fd exit error while waiting for goroutines to finish", zap.Error(errMsg))

				return fmt.Errorf("failed to handle uffd: %w", errMsg)
			}

			return nil
		}

		for event, name := range pollErrorEvents {
			if hasEvent(exitFd.Revents, event) {
				exitFdErrorCounter.Increase(name)
			}
		}

		wakeupFired := hasEvent(pollFds[2].Revents, unix.POLLIN)
		if wakeupFired {
			u.drainWakeupPipe()
		}

		uffdFd := pollFds[0]

		for event, name := range pollErrorEvents {
			if hasEvent(uffdFd.Revents, event) {
				uffdErrorCounter.Increase(name)
			}
		}

		var removes []*UffdRemove
		var pagefaults []*UffdPagefault

		if hasEvent(uffdFd.Revents, unix.POLLIN) {
			// readSerial keeps Export from interleaving between read and
			// SetRange(Zero) in the same serve-loop iteration. It does
			// NOT couple readEvents to settleRequests — workers don't take
			// readSerial, so a worker holding settleRequests.RLock can
			// never block this read. See TestNoMadviseDeadlockWithInflightCopy.
			u.readSerial.Lock()

			var err error
			removes, pagefaults, err = u.readEvents(ctx)
			if err != nil {
				u.readSerial.Unlock()
				u.logger.Error(ctx, "uffd: read error", zap.Error(err))

				return fmt.Errorf("failed to read: %w", err)
			}

			if len(removes) > 0 {
				u.settleRequests.Lock()
				for _, rm := range removes {
					// rm.start (inclusive) and rm.end (exclusive) are page-aligned
					// to u.pageSize for the registered VMA (UFFD invariant), so
					// startOff is a multiple of pageSize and length is an integer
					// number of pages — both divisions below are exact, and
					// SetRange's half-open [startIdx, endIdx) lines up with the
					// half-open [rm.start, rm.end).
					startOff, err := u.ma.GetOffset(uintptr(rm.start))
					if err != nil {
						u.logger.Error(ctx, "UFFD REMOVE: failed to map start address",
							zap.Uintptr("start", uintptr(rm.start)), zap.Error(err))

						continue
					}

					startIdx := uint32(header.BlockIdx(startOff, int64(u.pageSize)))
					endIdx := startIdx + uint32(uint64(rm.end-rm.start)/uint64(u.pageSize))
					u.pageTracker.SetRange(startIdx, endIdx, block.Removed)

					// Corruption tripwire: a REMOVE zapping a window page
					// whose pre-image is not captured yet destroys content
					// the export still owes. This must not happen — free-page
					// reporting is paused for the window's lifetime — so any
					// hit means the pause has a hole: fail the export cleanly
					// (the checkpoint errors; the sandbox keeps running)
					// instead of shipping a silently corrupt snapshot.
					if w := u.cowWindow.Load(); w != nil && w.Overlaps(startIdx, endIdx) {
						u.logger.Error(ctx, "uffd REMOVE overlaps CoW-window pages; canceling export",
							zap.Uint32("start_idx", startIdx), zap.Uint32("end_idx", endIdx))
						// The reason label is what separates a hole in the
						// FPR pause (systemic) from ordinary I/O failures.
						recordCoWCancel(ctx, "remove_tripwire")
						w.Cancel(fmt.Errorf("REMOVE zapped window pages [%d, %d)", startIdx, endIdx))
					}
				}
				u.settleRequests.Unlock()
			}

			u.readSerial.Unlock()
		} else if !wakeupFired {
			// Only treat as "no data" when poll returned without any known
			// source — a wakeupPipe self-wake (worker deferred) is expected.
			noDataCounter.Increase("POLLIN")
		}

		pagefaults = append(deferred.drain(), pagefaults...)

		if len(pagefaults) == 0 {
			if len(removes) == 0 {
				emptyDrainCounter.Increase("EMPTY_DRAIN")
			}

			continue
		}

		emptyDrainCounter.Log(ctx)
		noDataCounter.Log(ctx)

		for _, pf := range pagefaults {
			if pf.flags&UFFD_PAGEFAULT_FLAG_MINOR != 0 {
				return errors.New("unexpected MINOR pagefault event, closing UFFD")
			}

			addr := getPagefaultAddress(pf)
			offset, err := u.ma.GetOffset(addr)
			if err != nil {
				u.logger.Error(ctx, "UFFD serve got mapping error", zap.Error(err))

				return fmt.Errorf("failed to map: %w", err)
			}

			if pf.flags&UFFD_PAGEFAULT_FLAG_WP != 0 {
				// Synchronous WP fault: the guest wrote a write-protected present
				// page (the paired sync-WP Firecracker build registers guest RAM
				// without WP_ASYNC). Clear the protection so the write proceeds;
				// dirtiness is not recorded here — the kernel's WP-bit clear is
				// what the pagemap read at pause observes. With a WP_ASYNC
				// Firecracker these events are never delivered, so this path is
				// inert.
				//
				// The stall clock starts here, before the worker-pool dispatch,
				// so the recorded latency is what the blocked guest write
				// actually observes (including any queueing behind slow
				// MISSING serves).
				start := time.Now()
				u.wgWP.Go(func() error {
					err := u.resolveWriteProtect(ctx, addr, offset, fdExit.SignalExit, start)
					if errors.Is(err, errWPResolveAgain) {
						// mmap_changing (e.g. a REMOVE batch in flight):
						// retry via the deferred queue like MISSING EAGAINs
						// rather than blocking a worker under
						// settleRequests.RLock, which the REMOVE batch needs
						// to make progress. The short sleep damps the
						// redispatch: with no other events pending, the
						// self-wake would otherwise spin the serve loop at
						// full speed for as long as mmap_changing stays set
						// (e.g. a multi-second balloon drain).
						time.Sleep(wpResolveRetryDelay)
						deferred.push(pf)
						u.signalWakeup()

						return nil
					}

					return err
				})

				continue
			}

			u.wg.Go(func() error {
				// Record serve latency / installed bytes / fault count once
				// per serve attempt, tagged by page class and outcome. Begun
				// before the RLock so the latency covers lock wait + faultPage
				// for this attempt. Note: a deferred fault is re-served (and
				// re-timed) by a later worker, so the guest's full stall —
				// including the deferred-queue wait — can exceed any single
				// recorded serve.
				sw := serveTimer.Begin()
				pclass := pageClassUnknown
				result := faultResultInstalled
				var servedBytes int64
				defer func() {
					sw.RecordRaw(ctx, servedBytes, serveAttrs[u.genBucket][pclass][result])
					u.recordServeStats(pclass, result, servedBytes)
				}()

				if h := u.testFaultHook.Load(); h != nil {
					(*h)(addr, faultPhaseBeforeRLock)
				}

				// RLock spans the lookup→faultPage→setState sequence so a
				// concurrent REMOVE batch (settleRequests.Lock) can't slip in
				// between the state read and the install.
				u.settleRequests.RLock()
				defer u.settleRequests.RUnlock()

				var source PageReader

				idx := uint32(header.BlockIdx(offset, int64(u.pageSize)))

				state := u.pageTracker.Get(idx)
				switch state {
				case block.Dirty, block.Clean:
					// Pages must not be swappable for this short-circuit to
					// hold: only UFFD_EVENT_REMOVE moves a page out of
					// Dirty/Clean, and it records Removed.
					pclass = pageClassResident
					result = faultResultPresent

					return nil
				case block.Zero, block.Removed:
					// Zero-fill. Removed is the expected state here (a REMOVE
					// zapped the page and it reads back as zeros); Zero means
					// installed-zero and should not MISSING-fault, but is
					// served identically for safety. We still owe the kernel
					// an ack for the original MISSING fault or the faulting
					// thread stays blocked.
					pclass = pageClassZero
				case block.NotPresent:
					pclass = pageClassNew
					source = u.src
				default:
					result = faultResultError

					return fmt.Errorf("unexpected block.State: %#v", state)
				}

				var accessType block.AccessType
				if pf.flags&UFFD_PAGEFAULT_FLAG_WRITE == 0 {
					accessType = block.Read
				} else {
					accessType = block.Write
				}

				if h := u.testFaultHook.Load(); h != nil {
					(*h)(addr, faultPhaseBeforeFaultPage)
				}

				outcome, err := u.faultPage(
					ctx,
					addr,
					offset,
					accessType,
					source,
					fdExit.SignalExit,
				)
				if err != nil {
					result = faultResultError

					return err
				}

				switch outcome {
				case faultInstalled, faultAlreadyPresent:
					if outcome == faultInstalled {
						// A page was installed (zero-filled or pulled from
						// source) by this serve, so count its bytes. On
						// faultAlreadyPresent a concurrent worker or prefault
						// copied the page — record it as "present" with no
						// bytes so the bytes counter stays attributable.
						servedBytes = int64(u.pageSize)
					} else {
						result = faultResultPresent
					}
					// Tracker bookkeeping. Write access installs mode-0
					// (unprotected): Dirty, unconditional — top of the lattice.
					// Read access installs WP-armed, so record the content
					// class: Clean for source content (the diff inherits it
					// from the parent until a WP fault promotes it), Zero for
					// a zero-fill (a reinstalled Removed page becomes an
					// installed zero page again, so a later write can promote
					// it — promotions skip Removed, which means "zapped,
					// absent"). MarkInstalled never downgrades: on a lost
					// install race (EEXIST) the winner already recorded the
					// state, and a suspended worker must not overwrite a
					// concurrent WP-fault promotion to Dirty. Under WP-async
					// the pause-time pagemap readout catches later writes
					// instead.
					switch {
					case accessType == block.Write:
						u.pageTracker.SetRange(idx, idx+1, block.Dirty)
					case source != nil:
						u.pageTracker.MarkInstalled(idx, idx+1, block.Clean)
					default:
						u.pageTracker.MarkInstalled(idx, idx+1, block.Zero)
					}
					u.prefetchTracker.Add(offset, accessType)
				case faultDeferred:
					result = faultResultDeferred
					deferred.push(pf)
					u.signalWakeup()
				case faultDiscarded:
					// No install happened (ESRCH); retry would be pointless.
					result = faultResultDiscarded
				default:
					result = faultResultError

					return fmt.Errorf("unexpected faultOutcome: %#v", outcome)
				}

				return nil
			})
		}
	}
}

// resolveWriteProtect handles a synchronous userfault write-protect fault:
// the guest wrote a write-protected, present page. It clears the protection,
// which also wakes the blocked writer, and promotes the page to Dirty in the
// tracker — this is the write signal the tracker-based dirty source relies
// on. The promotion is safe against the REMOVE race that used to keep the
// tracker read-only here: MarkWritten skips Removed pages (a stale WP fault
// racing a REMOVE batch must not tag an absent page Dirty, or the reinstall
// fault would short-circuit without installing or waking), and the state
// split in the tracker makes Removed distinguishable from an installed zero
// page, whose promotion is required (a written page exported as Empty is
// content loss). Both this worker and the REMOVE batch run under
// settleRequests, so the two cannot interleave; either order yields the
// correct final state. Returns errWPResolveAgain on EAGAIN so the caller
// defers the fault (re-served and re-timed like a deferred MISSING fault);
// nothing is promoted then — the blocked writer's store has not happened.
// The copy-before-unprotect (background memory export) lands later.
//
// A failed unprotect is self-healing as long as the writer can be woken: it
// re-faults and the resolve retries (a REMOVEd page re-faults MISSING and is
// served normally), so that case is logged but does not fail the handler — a
// transient hiccup the guest already recovered from must not surface as a
// sandbox failure at teardown. Two cases escalate to onFailure (the serve
// exit signal) and a returned error: the wake ALSO failing (guest thread
// stranded mid-write with no retry signal, mirroring the MISSING path's
// data-fetch failure), and wpResolveErrEscalation consecutive failures of
// the same page (a deterministic failure that the retry loop would
// otherwise turn into an unbounded fault/wake livelock).
func (u *Userfaultfd) resolveWriteProtect(ctx context.Context, addr uintptr, offset int64, onFailure func() error, start time.Time) error {
	outcome := wpResolveOK
	defer func() {
		attrs := wpResolveAttrs[u.genBucket][outcome]
		wpResolveDuration.Record(ctx, time.Since(start).Microseconds(), attrs)
		wpResolveCount.Add(ctx, 1, attrs)
	}()

	u.settleRequests.RLock()
	defer u.settleRequests.RUnlock()

	if u.closed {
		outcome = wpResolveClosed

		return nil
	}

	alignedAddr := addr &^ (u.pageSize - 1)
	idx := uint32(header.BlockIdx(offset, int64(u.pageSize)))

	// A Removed reading here is ambiguous: either a REMOVE zapped the page
	// after this fault queued (the fault is stale; the page is gone), or a
	// REMOVE batch that waited on the serve lock recorded Removed AFTER a
	// racing reinstall had already re-populated and re-armed the page (the
	// tracker is stale; the page is present). Unprotecting is wrong for the
	// first case (it would strip a concurrent reinstall's fresh arm) and
	// wake-only is wrong for the second (the page stays armed and tracker-
	// Removed forever: every retried write re-faults into this same path —
	// a livelock, since a present page never MISSING-faults and nothing
	// else transitions it out of Removed). Only the kernel can tell the
	// cases apart, so probe it: a zero-page COPY|MODE_WP|DONTWAKE either
	// installs (page truly absent → it is now the armed zero page REMOVE
	// semantics promise; record Zero and wake, the retried write WP-faults
	// and promotes normally) or returns EEXIST (page present → the tracker
	// is what's stale; fall through to unprotect and promote through
	// MarkWrittenPresent). Transitions INTO Removed take the settleRequests
	// write lock, so the probe verdict cannot go stale for the rest of the
	// resolve. Probed BEFORE the CoW window: the truly-absent verdict
	// carries no pre-image obligation (the stalled write never landed, and
	// a REMOVE overlapping an uncaptured window page has already tripped
	// the serve loop's cancel); the present verdict falls through to the
	// window capture below like any other resolve.
	presenceVerified := false
	var err error
	if u.pageTracker.Get(idx) == block.Removed {
		probeErr := u.fd.copy(alignedAddr, u.pageSize, header.EmptyHugePage[:u.pageSize], UFFDIO_COPY_MODE_WP|UFFDIO_COPY_MODE_DONTWAKE)
		switch {
		case probeErr == nil:
			u.pageTracker.MarkInstalled(idx, idx+1, block.Zero)
			outcome = wpResolveStale
			if wakeErr := u.fd.wake(alignedAddr, u.pageSize); wakeErr != nil {
				var signalErr error
				if onFailure != nil {
					signalErr = onFailure()
				}

				return fmt.Errorf("uffd stale WP resolve at %#x stranded the writer: %w",
					addr, errors.Join(wakeErr, signalErr))
			}

			return nil
		case errors.Is(probeErr, unix.EEXIST):
			presenceVerified = true
		case errors.Is(probeErr, syscall.EAGAIN):
			outcome = wpResolveDeferred

			return errWPResolveAgain
		default:
			// Fed into the shared failure handling below (wake → re-fault,
			// per-page escalation), same as a failed unprotect.
			err = fmt.Errorf("stale-WP presence probe: %w", probeErr)
		}
	}

	// CoW window: capture the page's pre-image into the export sink BEFORE
	// clearing the protection — the faulting writer is still blocked, so the
	// bytes copied are the pause-time content by construction. Outside the
	// window (or after its cancel) this is a no-op and the resolve is
	// tracking-only. Blocking here (a claim wait is bounded by one page copy)
	// happens under settleRequests.RLock; that is acceptable because a live
	// window excludes free-page reporting, so no REMOVE batch is waiting.
	cow := false
	if err == nil {
		if w := u.cowWindow.Load(); w != nil {
			handled, copyErr := w.EnsureCopied(ctx, idx)
			if copyErr != nil {
				// Only a dead ctx interrupts a claim wait: the serve loop is
				// tearing down and the pre-image is not guaranteed captured,
				// so do not unprotect. The window is canceled with the
				// teardown.
				outcome = wpResolveError

				return fmt.Errorf("uffd WP resolve at %#x: CoW pre-image wait: %w", addr, copyErr)
			}
			cow = handled
		}

		// mode 0 = clear write-protection + wake the faulting thread (no
		// DONTWAKE).
		err = u.fd.writeProtectRange(alignedAddr, u.pageSize, u.pageSize, 0)
	}
	if errors.Is(err, syscall.EAGAIN) {
		// Deferred: record the attempt under its own outcome so a fault
		// bouncing off mmap_changing repeatedly stays diagnosable; the
		// eventual re-serve records the resolution separately. A captured
		// pre-image stays captured; the re-served resolve's EnsureCopied
		// takes the lock-free fast path.
		outcome = wpResolveDeferred

		return errWPResolveAgain
	}
	if err != nil {
		// Not promoted on any failure path: the write has not happened, and
		// whichever path completes it records the page Dirty.
		wakeErr := u.fd.wake(alignedAddr, u.pageSize)
		outcome = wpResolveError
		streak := u.recordWPResolveFailure(alignedAddr)
		if wakeErr == nil && streak < wpResolveErrEscalation {
			u.logger.Error(ctx, "uffd WP resolve failed; writer woken to re-fault",
				zap.Uintptr("addr", addr), zap.Int32("consecutive_failures", streak), zap.Error(err))

			return nil
		}

		var signalErr error
		if onFailure != nil {
			signalErr = onFailure()
		}
		if wakeErr != nil {
			return fmt.Errorf("uffd WP resolve at %#x stranded the writer: %w",
				addr, errors.Join(err, wakeErr, signalErr))
		}

		return fmt.Errorf("uffd WP resolve of page %#x failed %d consecutive times (deterministic failure, not retrying): %w",
			alignedAddr, streak, errors.Join(err, signalErr))
	}

	u.clearWPResolveFailure(alignedAddr)

	// The protection is cleared and the writer is waking: promote the page to
	// Dirty. Still under settleRequests.RLock, so a REMOVE batch cannot slip
	// between the clear and the promotion. Ordering vs the window's
	// Dirty→Clean rebaseline: EnsureCopied returned before this point, and
	// the rebaseline happens inside the copy, so this promotion always lands
	// after it — the write is dirty for the NEXT interval. When the presence
	// probe proved a Removed reading stale, promote THROUGH it —
	// MarkWritten's Removed-skip is for genuinely absent pages, which the
	// probe has just excluded.
	var prev block.State
	if presenceVerified {
		prev = u.pageTracker.MarkWrittenPresent(idx)
	} else {
		prev = u.pageTracker.MarkWritten(idx)
	}
	wpPromoteCount.Add(ctx, 1, wpPromoteAttrs[u.genBucket][prev])

	if cow {
		outcome = wpResolveOKCoW
	}
	u.wpFaultsResolved.Add(1)

	return nil
}

// recordWPResolveFailure bumps the consecutive-failure streak for one page
// and returns it. Streaks are per page: only the same page failing again and
// again indicates the deterministic fault/wake livelock the escalation
// exists for.
func (u *Userfaultfd) recordWPResolveFailure(alignedAddr uintptr) int32 {
	u.wpResolveErrMu.Lock()
	defer u.wpResolveErrMu.Unlock()

	if u.wpResolveErrPages == nil {
		u.wpResolveErrPages = make(map[uintptr]int32)
	}
	u.wpResolveErrPages[alignedAddr]++
	u.wpResolveErrPending.Store(int32(len(u.wpResolveErrPages)))

	return u.wpResolveErrPages[alignedAddr]
}

// clearWPResolveFailure drops the page's failure streak after a successful
// resolve. The pending gate keeps the common all-successes path lock-free.
func (u *Userfaultfd) clearWPResolveFailure(alignedAddr uintptr) {
	if u.wpResolveErrPending.Load() == 0 {
		return
	}

	u.wpResolveErrMu.Lock()
	defer u.wpResolveErrMu.Unlock()

	if _, ok := u.wpResolveErrPages[alignedAddr]; ok {
		delete(u.wpResolveErrPages, alignedAddr)
		u.wpResolveErrPending.Store(int32(len(u.wpResolveErrPages)))
	}
}

func (u *Userfaultfd) faultPage(
	ctx context.Context,
	addr uintptr,
	offset int64,
	accessType block.AccessType,
	source PageReader,
	onFailure func() error,
) (outcome faultOutcome, err error) {
	span := trace.SpanFromContext(ctx)

	// Named returns so a recovered panic produces a fatal error: the bare
	// zero values would otherwise look like a successful install
	// (faultInstalled) and a deterministic panic would loop forever.
	defer func() {
		if r := recover(); r != nil {
			u.logger.Error(ctx, "UFFD serve panic", zap.Any("pagesize", u.pageSize), zap.Any("panic", r))
			outcome = faultDiscarded
			err = fmt.Errorf("uffd serve panic: %v", r)
		}
	}()

	var writeErr error

	mode := u.defaultCopyMode
	if accessType == block.Read {
		mode = UFFDIO_COPY_MODE_WP
	}

	// nil source = zero-fill.
	switch {
	case source == nil && u.pageSize == header.PageSize && accessType == block.Write:
		// Write fault on a hole: plain zero-install, unprotected — the
		// write that faulted lands immediately and the page is recorded
		// Dirty.
		writeErr = u.fd.zero(addr, u.pageSize, 0)
	case source == nil:
		// Zero-fill via COPY of a zero buffer instead of UFFDIO_ZEROPAGE,
		// so read faults get install+write-protect in ONE atomic ioctl
		// (MODE_WP). The previous 4K sequence — ZEROPAGE(DONTWAKE) →
		// WRITEPROTECT → wake — had two windows that lose guest writes
		// under the tracker dirty source: another thread's write between
		// install and arm raises no UFFD event (the page is present and
		// unprotected), and an EAGAIN'd arm after a successful install was
		// never retried because the deferred re-serve hits EEXIST.
		writeErr = u.fd.copy(addr, u.pageSize, header.EmptyHugePage[:u.pageSize], mode)
	default:
		var b []byte
		if u.pageSize == header.HugepageSize {
			bufPtr := pagePool.Get().(*[]byte)
			defer pagePool.Put(bufPtr)
			b = (*bufPtr)[:u.pageSize]
		} else {
			b = make([]byte, u.pageSize)
		}

		// ReadAt retry holds settleRequests.RLock for up to ~2s of
		// exponential backoff, blocking any concurrent REMOVE batch.
		// Correctness holds (uffd FIFO drains the queued REMOVE before
		// the next same-page fault); if the blocking latency ever shows
		// up, move ReadAt outside the lock and re-check state before
		// UFFDIO_COPY.
		var dataErr error
		var attempt int

	retryLoop:
		for attempt = range sliceMaxRetries + 1 {
			var n int
			n, dataErr = source.ReadAt(ctx, b, offset)
			if dataErr == nil && int64(n) != int64(u.pageSize) {
				dataErr = fmt.Errorf("short read at %d: got %d, want %d", offset, n, u.pageSize)
			}
			if dataErr == nil {
				break
			}

			if attempt >= sliceMaxRetries || ctx.Err() != nil {
				break
			}

			u.logger.Warn(ctx, "UFFD serve read error, retrying",
				zap.Int("attempt", attempt+1),
				zap.Int("max_attempts", sliceMaxRetries+1),
				zap.Error(dataErr),
			)

			delay := min(sliceRetryBaseDelay<<attempt, sliceRetryMaxDelay)
			jitter := time.Duration(rand.Int63n(int64(delay) / 2))

			backoff := time.NewTimer(delay + jitter)

			select {
			case <-ctx.Done():
				backoff.Stop()

				dataErr = errors.Join(dataErr, ctx.Err())

				break retryLoop
			case <-backoff.C:
			}
		}

		if dataErr != nil {
			var signalErr error
			if onFailure != nil {
				signalErr = onFailure()
			}

			joinedErr := errors.Join(dataErr, signalErr)

			span.RecordError(joinedErr)
			u.logger.Error(ctx, "UFFD serve data fetch error after retries",
				zap.Int("attempts", attempt+1),
				zap.Error(joinedErr),
			)

			return faultDiscarded, fmt.Errorf("failed to read from source after %d attempts: %w", attempt+1, joinedErr)
		}
		writeErr = u.fd.copy(addr, u.pageSize, b, mode)
	}

	// EEXIST: page already mapped. Wake in case the install used DONTWAKE.
	if errors.Is(writeErr, unix.EEXIST) {
		span.SetAttributes(attribute.Bool("uffd.already_mapped", true))

		u.fd.wake(addr, u.pageSize) //nolint:errcheck // best-effort; thread may already be awake

		return faultAlreadyPresent, nil
	}

	// ESRCH: faulting thread exited during sandbox teardown. No install
	// happened, but retrying is pointless — the mm is going away.
	if errors.Is(writeErr, unix.ESRCH) {
		span.SetAttributes(attribute.Bool("uffd.process_exited", true))
		u.logger.Debug(ctx, "UFFD serve copy error: process no longer exists", zap.Error(writeErr))

		return faultDiscarded, nil
	}

	// EAGAIN: mmap_changing set mid-copy (concurrent madvise/mremap/fork) or
	// a partial copy (see classifyCopyResult). We defer the fault ourselves
	// via deferred.push(pf) + signalWakeup below; the kernel does not
	// auto-redeliver.
	if errors.Is(writeErr, unix.EAGAIN) {
		span.SetAttributes(attribute.Bool("uffd.copy_eagain", true))
		u.logger.Debug(ctx, "UFFD page write EAGAIN, deferring", zap.Uintptr("addr", addr))

		return faultDeferred, nil
	}

	if writeErr != nil {
		joinedErr := errors.Join(writeErr, safeInvoke(onFailure))

		span.RecordError(joinedErr)
		u.logger.Error(ctx, "UFFD serve uffdio copy error", zap.Error(joinedErr))

		return faultDiscarded, fmt.Errorf("failed uffdio copy: %w", joinedErr)
	}

	return faultInstalled, nil
}

func (u *Userfaultfd) PrefetchData() block.PrefetchData {
	// Hold Lock across the read — Lock; Unlock; Read leaves a window
	// where a worker can RLock and mutate prefetchTracker before we read.
	u.settleRequests.Lock()
	defer u.settleRequests.Unlock()

	return u.prefetchTracker.PrefetchData()
}

func (u *Userfaultfd) signalWakeup() {
	syscall.Write(u.wakeupPipe[1], []byte{1}) //nolint:errcheck // best-effort; pipe is non-blocking
}

func (u *Userfaultfd) drainWakeupPipe() {
	var buf [64]byte
	for {
		_, err := syscall.Read(u.wakeupPipe[0], buf[:])
		if err != nil {
			break
		}
	}
}

// PageSize returns the FC region page size driving this UFFD.
func (u *Userfaultfd) PageSize() int64 {
	return int64(u.pageSize)
}

func (u *Userfaultfd) Close() error {
	// Hold the write lock for the entire close sequence so that:
	//   (a) any Prefault() caller currently holding RLock finishes its
	//       UFFDIO_COPY before the fd number is freed and potentially
	//       recycled by the OS;
	//   (b) Close() is idempotent — a second call sees closed==true and
	//       returns immediately without touching already-freed fds.
	// In production Serve() drains all workers (u.wg.Wait) before
	// returning, so this Lock() is always uncontended when Close() fires.
	u.settleRequests.Lock()
	defer u.settleRequests.Unlock()

	if u.closed {
		return nil
	}
	u.closed = true

	syscall.Close(u.wakeupPipe[0])
	syscall.Close(u.wakeupPipe[1])

	return u.fd.close()
}
