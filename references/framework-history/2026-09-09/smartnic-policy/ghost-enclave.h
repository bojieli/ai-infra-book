// Copyright 2021 Google LLC
//
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file or at
// https://developers.google.com/open-source/licenses/bsd

// An Enclave represents the domain being managed by this process via ghOSt
// policy APIs.  It encapsulates the collection of a topology, active Agents,
// Schedulers, and (pending) Channels/IPC coordination.
//
// A CPU may only be associated with a single enclave, however, it is possible
// that a system is partitioned so that more than one enclave may simultaneously
// exist on a host.
//
// Enclaves are intended to both coordinate the initialization of ghOSt
// abstractions and to encapsulate dependence on an underlying physical host.
// Enclaves are intended to support simulated machine implementations, executing
// against a virtual/software ghOSt ABI, for offline testing.
#ifndef GHOST_LIB_ENCLAVE_H_
#define GHOST_LIB_ENCLAVE_H_

#include <list>

#include "absl/synchronization/mutex.h"
#include "lib/channel.h"
#include "lib/ghost.h"
#include "lib/topology.h"

namespace ghost {

class RunRequest;
class Agent;
class Scheduler;

// Options for how the kernel generates MSG_CPU_TICKs
enum class CpuTickConfig {
  kNoTicks,
  kAllTicks,
};

// Contains the configuration for an Agent, including the topology, the list of
// cpus, etc.  Pass this to FullAgent.
class AgentConfig {
 public:
  Topology* topology_;
  // If enclave_fd_ is set, then cpus_ is ignored.
  CpuList cpus_;
  int numa_node_ = 0;
  int enclave_fd_ = -1;
  CpuTickConfig tick_config_ = CpuTickConfig::kNoTicks;
  int stderr_fd_ = 2;
  // Default to false to avoid initialization overhead of mlock (e.g., agent
  // upgrade/restart may be slower due to mlock of the stacks of all agents). If
  // a scheduler has a performance benefit from using mlock, then it can opt-in
  // by setting this option to true.
  bool mlockall_ = false;

  explicit AgentConfig(Topology* topology = nullptr,
                       CpuList cpus = MachineTopology()->EmptyCpuList())
      : topology_(topology), cpus_(std::move(cpus)) {}
  virtual ~AgentConfig() {}
};

class Enclave {
 public:
  Enclave(const AgentConfig config);
  virtual ~Enclave();

  // Gets the run request for `cpu`.
  virtual RunRequest* GetRunRequest(const Cpu& cpu) = 0;

  // Submits 'req', waits for it to complete, and checks its return status. If
  // the commit succeeded, returns 'true'. Returns 'false' otherwise. Look at
  // the request itself to get the failure reason (req->state()).
  //
  // Note that this method should not be called for non-inline commits (i.e.,
  // commits performed on remote CPUs rather than the submitting CPU). This
  // method spins until the commit completes, so the system does not benefit
  // from the performance advantage of non-inline commits if this method is
  // called. Call 'SubmitRunRequest' instead.
  virtual bool CommitRunRequest(RunRequest* req) = 0;

  // Submits 'req' so the kernel may commit it, but neither waits for the commit
  // to complete nor checks its return status. Use this to submit non-inline
  // commits so that the agent may perform other work and periodically check if
  // the commit has finished rather than calling
  // 'CommitRunRequest'/'CompleteRunRequest' and spinning until the commits
  // finish.
  virtual void SubmitRunRequest(RunRequest* req) = 0;

  // Waits for 'req' to be committed by the kernel (but does not submit 'req' if
  // it has not yet been submitted) and checks its return status. If the commit
  // succeeded, returns 'true'. Returns 'false' otherwise. Look at the request
  // itself to get the failure reason (req->state()).
  //
  // Note that this method should not be called for non-inline commits (i.e.,
  // commits performed on remote CPUs rather than the submitting CPU). This
  // method spins until the commit completes, so the system does not benefit
  // from the performance advantage of non-inline commits if this method is
  // called. Call 'SubmitRunRequest' instead.
  virtual bool CompleteRunRequest(RunRequest* req) = 0;

  // The agent calls this when it wants to yield its CPU without scheduling a
  // task on its own CPU.
  virtual void LocalYieldRunRequest(const RunRequest* req,
                                    BarrierToken agent_barrier, int flags) = 0;

  // Ping agent on the CPU that corresponds to `req`. Ping may fail if there is
  // no agent associated with that CPU.
  //
  // Returns `true` on success and `false` otherwise.
  virtual bool PingRunRequest(const RunRequest* req) = 0;

  // Enclave implementations may provide more efficient batch-dispatch methods.
  //
  // Commit all open transactions on cpus specified in 'cpu_list'.
  // Returns true if all txns committed successfully and false otherwise.
  virtual bool CommitRunRequests(const CpuList& cpu_list);

  // Submits all open transactions on cpus specified in 'cpu_list' for commit,
  // but neither waits for them to commit nor checks their return status.
  virtual void SubmitRunRequests(const CpuList& cpu_list);

  // Commit on all CPUs in the 'cpu_list' as a sync-group transaction.
  //
  // A successful sync-group transaction guarantees the following:
  // - txns from distinct sync-groups do not overlap in execution timeline.
  // - either all CPUs in the sync-group commit successfully or none at all.
  //
  // Returns 'true' on success and 'false' otherwise.
  virtual bool CommitSyncRequests(const CpuList& cpu_list) = 0;

  // Submits transactions in 'cpu_list' for a sync commit.
  // Returns 'true' if the sync group was successful and 'false' otherwise.
  // On success the kernel releases ownership of all txns in the sync group.
  virtual bool SubmitSyncRequests(const CpuList& cpu_list) = 0;

  virtual Agent* GetAgent(const Cpu& cpu) = 0;

  // Runs l on every non-agent, ghost-task status word.
  virtual void ForEachTaskStatusWord(
      std::function<void(ghost_status_word* sw, uint32_t region_id,
                         uint32_t idx)>
          l) = 0;

  virtual void AdvertiseOnline() { is_online_ = true; }
  virtual bool IsOnline() { return is_online_; }
  virtual void PrepareToExit() { is_online_ = false; }
  // If there was an old agent attached to the enclave, this blocks until that
  // agent exits.
  virtual void WaitForOldAgent() = 0;
  virtual void InsertBpfPrograms() {}
  virtual void DisableMyBpfProgLoad() {}
  // LocalEnclaves have a ctl fd, which various agent functions use.
  virtual int GetCtlFd() { return -1; }
  virtual int GetDirFd() { return -1; }
  virtual void SetRunnableTimeout(absl::Duration d) {}
  virtual void SetCommitAtTick(bool enabled) {}
  virtual void SetDeliverAgentRunnability(bool enabled) {}
  virtual void SetDeliverCpuAvailability(bool enabled) {}
  virtual void SetDeliverTicks(bool enabled) {}
  virtual void SetWakeOnWakerCpu(bool enabled) {}
  virtual void SetLiveDangerously(bool enabled) {}
  virtual void DiscoverTasks() {}

  // REQUIRES: Must be called by an implementation when all Schedulers and
  // Agents have been constructed.
  //
  // We implement a diamond-shaped initialization pattern here as there are
  // co-dependencies between agents and schedulers which this greatly simplifies
  // the arrangement of.  For example:
  //   (a) A scheduler might want agent status words (for CPU readiness)
  //   (b) The agent in turn wants the scheduler that it needs to interact with.
  //
  // We observe that (b) is an _initialization_ dependency and (a) is a
  // _runtime_ dependency.  This provides a sequence point for both sides to
  // synchronize in the transition between these, that is coordinated with the
  // start of actual execution.
  //
  // NOTE: For testability, implementations should minimize the complexity of
  // direct Agent<->Scheduler interaction, this reduces the friction to
  // executing in a simulated environment.
  //
  // Invokes, in order:
  //   1. Wait for all Agents to be attached (e.g. there is an agent for every
  //      enclave_cpu).
  //   2. this->DerivedReady()
  //   3. Scheduler::EnclaveReady() for all attached schedulers.
  //   4. Agent::EnclaveReady() for all attached agents.
  // [ Invocation order within a category is arbitrary. ]
  void Ready();

  Topology* topology() const { return topology_; }
  const CpuList* cpus() const { return &enclave_cpus_; }
  virtual std::unique_ptr<Channel> MakeChannel(int elems, int node,
                                               const CpuList& cpulist) = 0;

  // Specializations for Attach and Detach must invoke the base method.
  // Note: Invoked by the actual thread associated with the Agent, prior to
  // invoking specialization.
  virtual void AttachAgent(const Cpu& cpu, Agent* agent);
  virtual void DetachAgent(Agent* agent);

 protected:
  const AgentConfig config_;
  Topology* topology_;
  CpuList enclave_cpus_;

  virtual void AttachScheduler(Scheduler* scheduler);
  virtual void DetachScheduler(Scheduler* scheduler);

  // May be overridden by implementations for Enclave late-initialization.
  // See Ready() for more details.
  virtual void DerivedReady() {}

 private:
  absl::Mutex mu_;
  std::list<Scheduler*> schedulers_ ABSL_GUARDED_BY(mu_);
  std::list<Agent*> agents_ ABSL_GUARDED_BY(mu_);
  bool is_online_ = false;

  friend class Scheduler;
};

// Sentinel value indicating that transaction is not owned.
inline constexpr int kSyncGroupNotOwned = -1;

// Options supplied when opening a transaction.
//
// N.B. ideally this would be nested within RunRequest but that bumps into
// an obscure corner of the language specification (yaqs/5211539845152768).
//
// Fixing this requires either:
// 1. Unnesting the options struct definition (done here).
// 2. Defining a default constructor explicitly (non-starter because designated
// initializers can only be used with aggregates; see go/totw/172 for details).
struct RunRequestOptions {
  // `target` is copied directly into txn->gtid and identifies the task
  // to run next on the cpu associated with the RunRequest.
  Gtid target = Gtid(0);

  // `target_barrier` is copied directly into txn->task_barrier and is used
  // by the kernel to ensure that the agent has consumed the latest message
  // associated with the task.
  BarrierToken target_barrier = StatusWord::NullBarrierToken();

  // `agent_barrier` is copied directly into txn->agent_barrier and is used
  // by the kernel to ensure that the agent has consumed all notifications
  // posted to it. This barrier is checked only for local commits and the
  // default `NullBarrierToken()` is legal value for remote commits.
  BarrierToken agent_barrier = StatusWord::NullBarrierToken();

  // `commit_flags` is copied directly into txn->commit_flags and controls
  // how a transaction is committed.
  int commit_flags = 0;

  // `run_flags` is copied directly into txn->run_flags to control a variety of
  // side-effects when the task either gets oncpu (e.g. `NEED_L1D_FLUSH`) or
  // offcpu (e.g. `RTLA_ON_IDLE`). The specific values and their effects are
  // defined in the ghost uapi header.
  int run_flags = 0;

  // If `sync_group_owner` != `kSyncGroupNotOwned` then caller wants
  // ownership of the transaction. In this case `RunRequest::Open`
  // will wait until the current owner relinquishes ownership.
  int sync_group_owner = kSyncGroupNotOwned;

  // If true, then the RunRequest is allowed to observe GHOST_TXN_TARGET_ONCPU.
  // Setting this requires that sync_group_owner is also being set, since we
  // must prevent RunRequest state from getting clobbered.
  bool allow_txn_target_on_cpu = false;
};

// RunRequest implements a transactional GhostHelper()->Run() API.  This
// enables:
//  1. Asynchronous and Batch dispatch.  A RunRequest may be asynchronously
//     invoked once opened.  Allowing amortization versus synchronous
//     transmission.
//  2. Submission may occur against a simulated ghOSt ABI, allowing for offline
//     testing.  The actual implementation of RunRequest submission is
//     implemented by an Enclave.
class RunRequest {
 public:
  RunRequest() : cpu_(Cpu::UninitializedType::kUninitialized) {}
  virtual ~RunRequest() {}

  void Init(Enclave* enclave, const Cpu& cpu) {
    enclave_ = enclave;
    cpu_ = cpu;
  }

  // Opens a transaction for later commit (sync or async depending on the
  // value of `commit_flags`).
  //
  // N.B. when used to assert sync_group ownership the caller must ensure
  // that no other agent will try to simultaneously grab ownership of the
  // transaction (for e.g. serializing via a lock).
  virtual void Open(const RunRequestOptions& options) = 0;

  // A specialization for the Run(0) case.  Please prefer this versus Open() as
  // we reserve the right to change how these requests are structured.
  //
  // This API should be used to preempt (aka unschedule) a ghost task
  // running on a remote cpu. The transaction may be committed at any
  // time after it is opened including asynchronously from the timer
  // tick or sched IPI handlers.
  //
  // Note that this is a no-op if remote cpu is running a non-ghost task.
  virtual void OpenUnschedule() = 0;

  // Returns true and releases ownership if the transaction was aborted.
  // Returns false otherwise.
  virtual bool Abort() = 0;

  // Agent must call LocalYield when it has nothing to do.
  //
  // global-agent model: satellite agents call this API so the global-agent can
  // schedule ghost tasks on remote cpus.
  //
  // per-cpu model: agents call this API when they have no tasks to schedule
  // or when yielding to another sched_class (ref: RTLA_ON_IDLE).
  //
  // REQUIRES: Must be called by the agent of cpu().
  // TODO: This could locally submit when there's a READY transaction.
  void LocalYield(const BarrierToken agent_barrier, const int flags) {
    enclave_->LocalYieldRunRequest(this, agent_barrier, flags);
  }

  // Ping() and queued-runs could interact with each other (when Ping clobbers
  // the transaction) so use the GhostHelper()->Run() based ping to sidestep the
  // issue.
  //
  // TODO: revisit when agent is able to to arbitrate txn ownership.
  bool Ping() { return enclave_->PingRunRequest(this); }

  // REQUIRES: Clients should use State() and not errno to interact with
  // results.  It is likely that this function stops returning information via
  // errno.
  bool Commit() { return enclave_->CommitRunRequest(this); }

  void Submit() { return enclave_->SubmitRunRequest(this); }

  Cpu cpu() const { return cpu_; }

  virtual ghost_txn_state state() const = 0;
  virtual bool open() const { return is_open(state()); }
  virtual bool claimed() const { return is_claimed(state()); }
  virtual bool committed() const { return is_committed(state()); }
  virtual bool failed() const { return is_failed(state()); }
  virtual bool succeeded() const { return is_succeeded(state()); }
  virtual absl::Time commit_time() const = 0;

  // These are helper functions for the state-checking functions above. These
  // are useful because the caller may only want to call `state()` once since
  // that function does an atomic read and its value may change between
  // successive calls (e.g., in `is_failed()`).
  static bool is_open(ghost_txn_state state) {
    return state == GHOST_TXN_READY;
  }
  static bool is_claimed(ghost_txn_state state) {
    return state >= 0 && state < MAX_CPUS;
  }
  static bool is_committed(ghost_txn_state state) { return state < 0; }
  static bool is_failed(ghost_txn_state state) {
    return is_committed(state) && state != GHOST_TXN_COMPLETE;
  }
  static bool is_succeeded(ghost_txn_state state) {
    return state == GHOST_TXN_COMPLETE;
  }

  // Returns the owner of the sync_group from the associated txn.
  virtual int32_t sync_group_owner_get() const = 0;

  // Updates owner of the sync_group in the associated txn.
  virtual void sync_group_owner_set(int32_t owner) = 0;

  // Attempts to take ownership of the sync_group, if not already taken.
  virtual bool sync_group_take_ownership(int32_t owner) = 0;

  // Returns true if the txn has a valid sync_group owner and false otherwise.
  virtual bool sync_group_owned() const = 0;

  // Returns the transaction's agent_barrier field.
  virtual BarrierToken agent_barrier() const = 0;

  // Returns the transaction's gtid field.
  virtual Gtid target() const = 0;

  // Returns the transaction's task_barrier field.
  virtual BarrierToken target_barrier() const = 0;

  // Returns the transaction's commit_flags field.
  virtual int commit_flags() const = 0;

  // Returns the transaction's run_flags field.
  virtual int run_flags() const = 0;

  virtual bool allow_txn_target_on_cpu() const = 0;

  virtual uint64_t cpu_seqnum() const = 0;

  static std::string StateToString(ghost_txn_state state);

 protected:
  Enclave* enclave_ = nullptr;
  Cpu cpu_;
};

class LocalRunRequest : public RunRequest {
 public:
  LocalRunRequest() : RunRequest() {}

  void Init(Enclave* enclave, const Cpu& cpu, ghost_txn* txn) {
    RunRequest::Init(enclave, cpu);

    CHECK_EQ(txn->cpu, cpu_.id());
    txn_ = txn;
  }

  void Open(const RunRequestOptions& options) override;
  void OpenUnschedule() override {
    // Make sure agent is preempting a remote cpu.
    CHECK_NE(cpu_.id(), sched_getcpu());
    Open(RunRequestOptions());
  }

  bool Abort() override;

  ghost_txn_state state() const override {
    return txn_->state.load(std::memory_order_acquire);
  }
  absl::Time commit_time() const override {
    // Do a relaxed load of `txn_->commit_time` since this should be done after
    // the acquire load to the txn state.
    return absl::FromUnixNanos(READ_ONCE(txn_->commit_time));
  }

  // Returns the owner of the sync_group from the associated txn.
  int32_t sync_group_owner_get() const override {
    return txn_->u.sync_group_owner.load(std::memory_order_acquire);
  }

  // Updates owner of the sync_group in the associated txn.
  void sync_group_owner_set(int32_t owner) override {
    txn_->u.sync_group_owner.store(owner, std::memory_order_release);
  }

  // Attempts to take ownership of the sync_group, if not already taken.
  // Uses the weak form of CAS, so this may fail spuriously (it is expected to
  // be used in a loop).
  bool sync_group_take_ownership(int32_t owner) override {
    int32_t no_owner = kSyncGroupNotOwned;
    return txn_->u.sync_group_owner.compare_exchange_weak(
        no_owner, owner, std::memory_order_acq_rel);
  }

  // Returns true if the txn has a valid sync_group owner and false otherwise.
  bool sync_group_owned() const override {
    return sync_group_owner_get() != kSyncGroupNotOwned;
  }

  // Returns the transaction's agent_barrier field.
  BarrierToken agent_barrier() const override { return txn_->agent_barrier; }

  // Returns the transaction's gtid field.
  Gtid target() const override { return Gtid(txn_->gtid); }

  // Returns the transaction's task_barrier field.
  BarrierToken target_barrier() const override { return txn_->task_barrier; }

  // Returns the transaction's commit_flags field.
  int commit_flags() const override { return txn_->commit_flags; }

  // Returns the transaction's run_flags field.
  int run_flags() const override { return txn_->run_flags; }

  bool allow_txn_target_on_cpu() const override {
    return allow_txn_target_on_cpu_;
  }

  uint64_t cpu_seqnum() const override { return txn_->cpu_seqnum; }

  ghost_txn* txn() { return txn_; }

 private:
  ghost_txn* txn_ = nullptr;
  bool allow_txn_target_on_cpu_ = false;
};

// An Enclave supporting execution on the local physical host.
class LocalEnclave final : public Enclave {
 public:
  LocalEnclave(AgentConfig config);
  ~LocalEnclave() final;

  LocalRunRequest* GetRunRequest(const Cpu& cpu) final {
    return &cpus_[cpu.id()].req;
  }

  bool CommitRunRequest(RunRequest* req) final;
  void SubmitRunRequest(RunRequest* req) final;
  bool CompleteRunRequest(RunRequest* req) final;
  void LocalYieldRunRequest(const RunRequest* req, BarrierToken agent_barrier,
                            int flags) final;
  bool PingRunRequest(const RunRequest* req) final;

  bool CommitRunRequests(const CpuList& cpu_list) final;
  void SubmitRunRequests(const CpuList& cpu_list) final;
  bool CommitSyncRequests(const CpuList& cpu_list) final;
  bool SubmitSyncRequests(const CpuList& cpu_list) final;

  std::unique_ptr<Channel> MakeChannel(int elems, int node,
                                       const CpuList& cpulist) {
    return std::make_unique<LocalChannel>(elems, node, cpulist);
  }

  Agent* GetAgent(const Cpu& cpu) final { return rep(cpu)->agent; }
  void AttachAgent(const Cpu& cpu, Agent* agent) final;
  void DetachAgent(Agent* agent) final;

  int GetNrTasks() { return LocalEnclave::GetNrTasks(dir_fd_); }
  int GetAbiVersion() { return LocalEnclave::GetAbiVersion(dir_fd_); }

  void SetRunnableTimeout(absl::Duration d) final {
    WriteEnclaveTunable(dir_fd_, "runnable_timeout",
                        std::to_string(ToInt64Milliseconds(d)));
  }

  void SetCommitAtTick(bool enabled) final {
    WriteEnclaveTunable(dir_fd_, "commit_at_tick",
                        BoolToTunableString(enabled));
  }

  void SetDeliverAgentRunnability(bool enabled) final {
    WriteEnclaveTunable(dir_fd_, "deliver_agent_runnability",
                        BoolToTunableString(enabled));
  }

  void SetDeliverCpuAvailability(bool enabled) final {
    WriteEnclaveTunable(dir_fd_, "deliver_cpu_availability",
                        BoolToTunableString(enabled));
  }

  void SetDeliverTicks(bool enabled) final {
    WriteEnclaveTunable(dir_fd_, "deliver_ticks",
                        BoolToTunableString(enabled));
  }

  void SetWakeOnWakerCpu(bool enabled) final {
    WriteEnclaveTunable(dir_fd_, "wake_on_waker_cpu",
                        BoolToTunableString(enabled));
  }

  void SetLiveDangerously(bool enabled) final {
    WriteEnclaveTunable(dir_fd_, "live_dangerously",
                        BoolToTunableString(enabled));
  }

  // The kernel will send a task_new for every task in the enclave
  void DiscoverTasks() final {
    WriteEnclaveTunable(dir_fd_, "ctl", "discover tasks");
  }

  // Runs l on every non-agent, ghost-task status word.
  void ForEachTaskStatusWord(
      const std::function<void(ghost_status_word* sw, uint32_t region_id,
                               uint32_t idx)>
          l) final;

  void AdvertiseOnline() final;
  void PrepareToExit() final;

  // If there was an old agent attached to the enclave (i.e. holding a RW fd on
  // agent_online), this blocks until that FD is closed.
  void WaitForOldAgent() final;
  void InsertBpfPrograms() final;

  // Permanently disables the ability to load BPF programs for the calling
  // process.
  void DisableMyBpfProgLoad() final {
    std::string cmd = "disable my bpf_prog_load";
    CHECK_EQ(write(ctl_fd_, cmd.c_str(), cmd.length()), cmd.length());
  }

  int GetCtlFd() final { return ctl_fd_; }
  int GetDirFd() final { return dir_fd_; }

  static int MakeNextEnclave();
  static int GetEnclaveDirectory(int ctl_fd);
  static void WriteEnclaveTunable(int dir_fd, absl::string_view tunable_path,
                                  absl::string_view tunable_value);
  static std::string ReadEnclaveTunable(int dir_fd,
                                        absl::string_view tunable_path);
  static int GetCpuDataRegion(int dir_fd);
  // Waits on an enclave's agent_online until the value of the file was 'until'
  // (either 0 or 1) at some point in time.
  static void WaitForAgentOnlineValue(int dir_fd, int until);
  static int GetNrTasks(int dir_fd);
  static int GetAbiVersion(int dir_fd);
  static void DestroyEnclave(int ctl_fd);
  static void DestroyAllEnclaves();

 private:
  void CommonInit();
  void BuildCpuReps();
  void AttachToExistingEnclave();
  void CreateAndAttachToEnclave();
  // Releases ownership of txns associated with cpus in `cpu_list`.
  void ReleaseSyncRequests(const CpuList& cpu_list);

  struct CpuRep {
    Agent* agent;
    LocalRunRequest req;
  } ABSL_CACHELINE_ALIGNED;

  CpuRep* rep(const Cpu& cpu) { return &cpus_[cpu.id()]; }
  std::string BoolToTunableString(bool b) { return b ? "1" : "0"; }

  CpuRep cpus_[MAX_CPUS];
  ghost_cpu_data* data_region_ = nullptr;
  size_t data_region_size_ = 0;
  bool destroy_when_destructed_;
  int dir_fd_ = -1;
  int ctl_fd_ = -1;
  int agent_online_fd_ = -1;
};

}  // namespace ghost

#endif  // GHOST_LIB_ENCLAVE_H_
