// Copyright 2021 Google LLC
//
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file or at
// https://developers.google.com/open-source/licenses/bsd

#include "lib/enclave.h"

#include <sys/epoll.h>
#include <sys/mman.h>

#include <filesystem>
#include <fstream>
#include <regex>  // NOLINT: no RE2; ghost limits itself to absl

#include "absl/base/attributes.h"
#include "absl/strings/numbers.h"
#include "bpf/user/agent.h"
#include "lib/agent.h"
#include "lib/scheduler.h"

namespace ghost {

Enclave::Enclave(AgentConfig config)
    : config_(config),
      topology_(config.topology_),
      enclave_cpus_(config.cpus_) {}
Enclave::~Enclave() {}

void Enclave::Ready() {
  auto ready = [this]() {
    mu_.AssertHeld();
    return agents_.size() == enclave_cpus_.Size();
  };

  mu_.LockWhen(absl::Condition(&ready));

  DerivedReady();

  if (!schedulers_.empty()) {
    // There can be only one default queue, so take the first scheduler's
    // default.
    // There are tests that have agents, but do not have a scheduler.  Those
    // must call SetEnclaveDefault() manually.
    CHECK(schedulers_.front()->GetDefaultChannel().SetEnclaveDefault());
  }

  InsertBpfPrograms();
  DisableMyBpfProgLoad();

  // On the topic of multithreaded Discovery: the main issue is that global
  // schedulers can't handle concurrent discovery and scheduling.  For instance,
  // they use the SingleThreadMallocTaskAllocator and probably have other
  // scheduler-specific assumptions.  If they ever can handle concurrency, then
  // we can move DiscoverTasks elsewhere - perhaps the schedulers themselves can
  // call DiscoverTasks from e.g. a non-global-agent.
  //
  // Even per-cpu agents can't easily handle concurrent Discovery.  Consider the
  // lifetime of a Task.  The only agent task that is allowed to muck with Task
  // is whoever handles the queue that the task is associated to.  For example,
  // what happens when we receive a TaskDead?  We want to call ~Task().  But you
  // can't do that if another thread - including the Discoverer - is accessing
  // it.  So long as we have this assumption (queue owner -> can muck with
  // Task), we cannot do concurrent discovery.
  //
  // As another case, consider what happens when the Discoverer finds a task
  // that is in the process of departing while another thread is handling
  // messages.  If the Discoverer calls ~Task(), then the thread that called
  // GetTask has an unreference-counted reference!  If we knew that there were
  // *no* messages for the task, then we could call ~Task().  But we can't be
  // sure of that: it's possible that task was new and used our new agent's
  // default channel - so we'll eventually get those messages.
  //
  // As a final consideration, take EDF: we need to scrape the PrioTable before
  // scheduling.  It's easiest to scrape after discovery completes, so that
  // scheduler won't practically be able to schedule during discovery.
  //
  // Without redesigning Tasks and the way schedulers work, we'll have to stick
  // to non-concurrent discovery and scheduling.  We'd probably need something
  // like a kref and RCU too.
  //
  // Right now we're single threaded.  All Agents are in WaitForEnclaveReady,
  // which is triggered by agent->EnclaveReady() below (not
  // scheduler->EnclaveReady()).  That means we can't schedule until Discovery
  // is complete, which may take time.
  for (auto scheduler : schedulers_) scheduler->DiscoverTasks();

  for (auto scheduler : schedulers_) scheduler->EnclaveReady();

  // We could use agents_ here, but this allows extra checking.
  for (const Cpu& cpu : enclave_cpus_) {
    Agent* agent = GetAgent(cpu);
    CHECK_NE(agent, nullptr);  // Every Enclave CPU should have an agent.
    agent->EnclaveReady();
  }
  mu_.Unlock();

  AdvertiseOnline();
}

void Enclave::AttachAgent(const Cpu& cpu, Agent* agent) {
  absl::MutexLock h(&mu_);
  agents_.push_back(agent);
}

void Enclave::DetachAgent(Agent* agent) {
  absl::MutexLock h(&mu_);
  agents_.remove(agent);
}

void Enclave::AttachScheduler(Scheduler* scheduler) {
  absl::MutexLock h(&mu_);
  schedulers_.push_back(scheduler);
}

void Enclave::DetachScheduler(Scheduler* scheduler) {
  absl::MutexLock h(&mu_);
  schedulers_.remove(scheduler);
}

bool Enclave::CommitRunRequests(const CpuList& cpu_list) {
  SubmitRunRequests(cpu_list);

  bool success = true;
  for (const Cpu& cpu : cpu_list) {
    RunRequest* req = GetRunRequest(cpu);
    if (!CompleteRunRequest(req)) success = false;
  }
  return success;
}

void Enclave::SubmitRunRequests(const CpuList& cpu_list) {
  for (const Cpu& cpu : cpu_list) {
    RunRequest* req = GetRunRequest(cpu);
    SubmitRunRequest(req);
  }
}

// Reads bytes from fd and returns a string.  Suitable for sysfs.
std::string ReadString(int fd) {
  char buf[4096];
  char* p;
  char* end = buf + sizeof(buf);
  ssize_t amt = 1;
  for (p = buf; amt > 0 && p < end; p += amt) {
    amt = read(fd, p, end - p);
    CHECK_GE(amt, 0);
  }
  CHECK_EQ(amt, 0);
  return std::string(buf, p - buf);
}

void LocalEnclave::ForEachTaskStatusWord(
    const std::function<void(ghost_status_word* sw, uint32_t region_id,
                             uint32_t idx)>
        l) {
  // TODO: Need to support more than one SW region.
  StatusWordTable* tbl = GhostHelper()->GetGlobalStatusWordTable();
  CHECK_NE(tbl, nullptr);
  tbl->ForEachTaskStatusWord(l);
}

// Makes the next available enclave from ghostfs.  Returns the FD for the ctl
// file in whichever enclave directory we get.
// static
int LocalEnclave::MakeNextEnclave() {
  int top_ctl = open(absl::StrCat(GhostHelper()->kGhostfsMount, "/ctl").c_str(),
                     O_WRONLY);
  if (top_ctl < 0) {
    return -1;
  }
  int id = 1;

  while (true) {
    std::string cmd = absl::StrCat("create ", id, " ", GHOST_VERSION);
    if (write(top_ctl, cmd.c_str(), cmd.length()) == cmd.length()) {
      break;
    }
    if (errno == EEXIST) {
      id++;
      continue;
    }
    close(top_ctl);
    return -1;
  }
  close(top_ctl);

  return open(
      absl::StrCat(GhostHelper()->kGhostfsMount, "/enclave_", id, "/ctl")
          .c_str(),
      O_RDWR);
}

// Open the directory containing our ctl_fd, sufficient for openat calls
// (O_PATH).  For example, if you have the ctl for enclave 314, open
// "/sys/fs/ghost/enclave_314".  The ctl file tells you the enclave ID.
// static
int LocalEnclave::GetEnclaveDirectory(int ctl_fd) {
  CHECK_GE(ctl_fd, 0);
  lseek(ctl_fd, 0, SEEK_SET);
  // 20 for the u64 in ascii, 2 for 0x, 1 for \0, 9 in case of a mistake.
  constexpr int kU64InAsciiBytes = 20 + 2 + 1 + 9;
  char buf[kU64InAsciiBytes] = {0};
  CHECK_GT(read(ctl_fd, buf, sizeof(buf)), 0);
  uint64_t id;
  CHECK(absl::SimpleAtoi(buf, &id));
  return open(
      absl::StrCat(GhostHelper()->kGhostfsMount, "/enclave_", id).c_str(),
      O_PATH);
}

// static
void LocalEnclave::WriteEnclaveTunable(int dir_fd,
                                       absl::string_view tunable_path,
                                       absl::string_view tunable_value) {
  int tunable_fd = openat(dir_fd, std::string(tunable_path).c_str(), O_RDWR);
  CHECK_GE(tunable_fd, 0);
  CHECK_EQ(write(tunable_fd, tunable_value.data(), tunable_value.length()),
           tunable_value.length());
  close(tunable_fd);
}

// static
std::string LocalEnclave::ReadEnclaveTunable(int dir_fd,
                                             absl::string_view tunable_path) {
  int tunable_fd = openat(dir_fd, std::string(tunable_path).c_str(), O_RDONLY);
  CHECK_GE(tunable_fd, 0);
  std::string val = ReadString(tunable_fd);
  close(tunable_fd);
  return val;
}

// static
int LocalEnclave::GetCpuDataRegion(int dir_fd) {
  CHECK_GE(dir_fd, 0);
  return openat(dir_fd, "cpu_data", O_RDWR);
}

// Waits on an enclave's agent_online until the value of the file was 'until'
// (either 0 or 1) at some point in time.
//
// If the value is already 'until', then we will return immediately.  There is
// no guarantee that an edge occurred, where the value of agent_online changed.
//
// We also might never witness agent_online == until.  We only know that we saw
// one_or_zero != until, and we epoll_waited.  (agent_online's value is either
// one or zero.)
//
// epoll_wait will return if the value changed between the first and second
// calls to epoll_wait.  That change may be before we read.  Either way, we know
// there was a change at some point since we entered this function, and at some
// point the value we read was not equal to until.  Since there are only two
// values for agent_online, we know at some point agent_online == until.
//
// static
void LocalEnclave::WaitForAgentOnlineValue(int dir_fd, int until) {
  epoll_event ep_ev;
  int epfd;
  int fd = openat(dir_fd, "agent_online", O_RDONLY);

  CHECK(until == 0 || until == 1);
  CHECK_GE(fd, 0);
  epfd = epoll_create(1);
  CHECK_GE(epfd, 0);
  ep_ev.events = EPOLLIN | EPOLLET | EPOLLPRI;
  CHECK_EQ(epoll_ctl(epfd, EPOLL_CTL_ADD, fd, &ep_ev), 0);

  // We epoll before reading, since the first epoll_wait will return, even if
  // the file hasn't changed since epoll_ctl
  while (epoll_wait(epfd, &ep_ev, sizeof(ep_ev), -1) != 1) {
    // EINTR is ok - it will happen for signals (e.g. ctl-z)
    CHECK_EQ(errno, EINTR);
  }

  char buf[20];
  memset(buf, 0, sizeof(buf));
  CHECK_GT(read(fd, buf, sizeof(buf) - 1), 0);
  int one_or_zero;
  CHECK(absl::SimpleAtoi(buf, &one_or_zero));
  if (one_or_zero != until) {
    while (epoll_wait(epfd, &ep_ev, sizeof(ep_ev), -1) != 1) {
      CHECK_EQ(errno, EINTR);
    }
    // At this point, the value of agent_online might be 1 or 0.  All we know is
    // that it changed at some point after our first epoll_wait.
  }

  close(epfd);
  close(fd);
}

// static
int LocalEnclave::GetNrTasks(int dir_fd) {
  int fd = openat(dir_fd, "status", O_RDONLY);
  CHECK_GE(fd, 0);
  const std::string status_lines = ReadString(fd);
  close(fd);
  std::istringstream s(status_lines);
  std::string line;
  while (std::getline(s, line)) {
    std::smatch matches;
    if (std::regex_match(line, matches, std::regex("^nr_tasks ([0-9]+)$"))) {
      // matches[1] corresponds to [0-9]+
      if (matches.size() != 2) {
        return -1;
      }
      std::ssub_match digits = matches[1];
      int nr_tasks;
      CHECK(absl::SimpleAtoi(digits.str(), &nr_tasks));
      return nr_tasks;
    }
  }
  return -1;
}

// static
int LocalEnclave::GetAbiVersion(int dir_fd) {
  int fd = openat(dir_fd, "abi_version", O_RDONLY);
  CHECK_GE(fd, 0);

  int version;
  if (!absl::SimpleAtoi(ReadString(fd), &version)) {
    version = 0;  // invalid abi version.
  }

  close(fd);
  return version;
}

// static
void LocalEnclave::DestroyEnclave(int ctl_fd) {
  constexpr const char kCommand[] = "destroy";
  ssize_t msg_sz = sizeof(kCommand) - 1;  // No need for the \0
  // It's possible to get an error if the enclave is concurrently destroyed.
  IGNORE_RETURN_VALUE(write(ctl_fd, kCommand, msg_sz));
}

// static
void LocalEnclave::DestroyAllEnclaves() {
  std::error_code ec;
  auto f =
      std::filesystem::directory_iterator(GhostHelper()->kGhostfsMount, ec);
  auto end = std::filesystem::directory_iterator();
  for (/* f */; !ec && f != end; f.increment(ec)) {
    if (std::regex_match(f->path().filename().string(),
                         std::regex("^enclave_.*"))) {
      int ctl = open((f->path() / "ctl").string().c_str(), O_RDWR);
      // If there is a concurrent destroyer, we could see the enclave directory
      // but fail to open ctl.
      if (ctl >= 0) {
        LocalEnclave::DestroyEnclave(ctl);
        close(ctl);
      }
    }
  }
}

void LocalEnclave::CommonInit() {
  // Bug out if we already have a non-default global enclave.  We shouldn't have
  // more than one enclave per process at a time, at least not until we have
  // fully moved away from default enclaves.
  CHECK_EQ(GhostHelper()->GetGlobalEnclaveCtlFd(), -1);
  CHECK_EQ(GhostHelper()->GetGlobalEnclaveDirFd(), -1);
  GhostHelper()->SetGlobalEnclaveFds(ctl_fd_, dir_fd_);

  CHECK_EQ(GetAbiVersion(), GHOST_VERSION);

  int data_fd = LocalEnclave::GetCpuDataRegion(dir_fd_);
  CHECK_GE(data_fd, 0);
  data_region_size_ = GetFileSize(data_fd);
  data_region_ = static_cast<ghost_cpu_data*>(
      mmap(/*addr=*/nullptr, data_region_size_, PROT_READ | PROT_WRITE,
           MAP_SHARED, data_fd, /*offset=*/0));
  close(data_fd);
  CHECK_NE(data_region_, MAP_FAILED);

  GhostHelper()->SetGlobalStatusWordTable(
      new LocalStatusWordTable(dir_fd_, /*id=*/0, config_.numa_node_));
}

// Initialize a CpuRep for each cpu in enclaves_cpus_ (aka, cpus()).
void LocalEnclave::BuildCpuReps() {
  cpu_set_t cpuset = topology_->ToCpuSet(*cpus());

  for (int i = 0; i < topology_->num_cpus(); ++i) {
    if (!CPU_ISSET(i, &cpuset)) {
      continue;
    }
    ghost_txn* txn = &data_region_[i].txn;
    Cpu cpu = topology_->cpu(txn->cpu);
    CpuRep* rep = &cpus_[cpu.id()];
    rep->req.Init(this, cpu, txn);
    rep->agent = nullptr;
  }
}

// We are attaching to an existing enclave, given the fd for the directory to
// e.g. /sys/fs/ghost/enclave_123/.  We use the cpus that already belong to the
// enclave.
void LocalEnclave::AttachToExistingEnclave() {
  destroy_when_destructed_ = false;

  CHECK_GE(dir_fd_, 0);

  ctl_fd_ = openat(dir_fd_, "ctl", O_RDWR);
  CHECK_GE(ctl_fd_, 0);

  CommonInit();

  int cpulist_fd = openat(dir_fd_, "cpulist", O_RDONLY);
  CHECK_GE(cpulist_fd, 0);
  std::string cpulist = ReadString(cpulist_fd);
  enclave_cpus_ = topology_->ParseCpuStr(cpulist);
  close(cpulist_fd);
}

// We are creating a new enclave.  We attempt to allocate enclave_cpus.
void LocalEnclave::CreateAndAttachToEnclave() {
  destroy_when_destructed_ = true;

  // Note that if you CHECK fail in this function, the LocalEnclave dtor won't
  // run, and you'll leak the enclave.  Closing the fd isn't enough; you need to
  // explicitly DestroyEnclave().  Given that enclaves are supposed to persist
  // past agent death, this is somewhat OK.
  ctl_fd_ = LocalEnclave::MakeNextEnclave();
  CHECK_GE(ctl_fd_, 0);

  dir_fd_ = LocalEnclave::GetEnclaveDirectory(ctl_fd_);
  CHECK_GE(dir_fd_, 0);

  CommonInit();

  int cpumask_fd = openat(dir_fd_, "cpumask", O_RDWR);
  CHECK_GE(cpumask_fd, 0);
  std::string cpumask = enclave_cpus_.CpuMaskStr();
  // Note that if you ask for more cpus than the kernel knows about, i.e. more
  // than nr_cpu_ids, it may silently succeed.  The kernel only checks the cpus
  // it knows about.  However, since this cpumask was constructed from a
  // topology, there should not be more than nr_cpu_ids.
  constexpr int kMaxRetries = 10;
  int retries = 0;
  do {
    int ret = write(cpumask_fd, cpumask.c_str(), cpumask.length());
    if (ret == cpumask.length()) {
      break;
    }
    // go/kcl/466292 always defers enclave destruction to a CFS task.
    // This sometimes causes failures in unit tests because enclave
    // destruction from a prior test races with enclave creation in
    // the next one.
    //
    // Fix this by retrying a finite number of times as long as the
    // reason for failure matches the race described above (EBUSY).
    CHECK_EQ(ret, -1);
    CHECK_EQ(errno, EBUSY);
    absl::SleepFor(absl::Milliseconds(50));
  } while (++retries < kMaxRetries);
  CHECK_LT(retries, kMaxRetries);

  close(cpumask_fd);
}

LocalEnclave::LocalEnclave(AgentConfig config)
    : Enclave(config), dir_fd_(config.enclave_fd_) {
  if (dir_fd_ == -1) {
    CreateAndAttachToEnclave();
  } else {
    AttachToExistingEnclave();
  }

  BuildCpuReps();

  if (config_.tick_config_ == CpuTickConfig::kAllTicks) {
      SetDeliverTicks(true);
  }
  CHECK_EQ(agent_bpf_init(), 0);
}

LocalEnclave::~LocalEnclave() {
  PrepareToExit();
  (void)munmap(data_region_, data_region_size_);
  if (destroy_when_destructed_) {
    LocalEnclave::DestroyEnclave(ctl_fd_);
  }
  close(ctl_fd_);
  close(dir_fd_);
  // agent_test has some cases where it creates new enclaves within the same
  // process, so reset the global enclave ghost variables
  GhostHelper()->SetGlobalEnclaveFds(-1, -1);
  delete GhostHelper()->GetGlobalStatusWordTable();
  GhostHelper()->SetGlobalStatusWordTable(nullptr);
}

void LocalEnclave::InsertBpfPrograms() {
  int ret;
  do {
    ret = agent_bpf_insert_registered(ctl_fd_);
  } while (ret && errno == EBUSY);
  CHECK_EQ(ret, 0);
}

bool LocalEnclave::CommitRunRequests(const CpuList& cpu_list) {
  SubmitRunRequests(cpu_list);

  bool success = true;
  for (const Cpu& cpu : cpu_list) {
    RunRequest* req = GetRunRequest(cpu);
    if (!CompleteRunRequest(req)) success = false;
  }
  return success;
}

void LocalEnclave::SubmitRunRequests(const CpuList& cpu_list) {
  cpu_set_t cpus = topology()->ToCpuSet(cpu_list);
  CHECK_EQ(GhostHelper()->Commit(cpus), 0);
}

bool LocalEnclave::CommitSyncRequests(const CpuList& cpu_list) {
  if (SubmitSyncRequests(cpu_list)) {
    // The sync group committed successfully. The kernel has already released
    // ownership of transactions that were part of the sync group.
    return true;
  }

  // Commit failed so we expect (and CHECK) that this flips to true after
  // calling CompleteRunRequest on cpus in `cpu_list`.
  bool failure_detected = false;
  for (const Cpu& cpu : cpu_list) {
    RunRequest* req = GetRunRequest(cpu);
    if (!CompleteRunRequest(req)) {
      // Cannot bail early even though the return value has been finalized
      // because we must call CompleteRunRequest() on all cpus in the list.
      failure_detected = true;
    }
  }
  CHECK(failure_detected);

  ReleaseSyncRequests(cpu_list);

  return false;
}

bool LocalEnclave::SubmitSyncRequests(const CpuList& cpu_list) {
  cpu_set_t cpus = topology()->ToCpuSet(cpu_list);
  int ret = GhostHelper()->SyncCommit(cpus);
  CHECK(ret == 0 || ret == 1);
  return ret;
}

void LocalEnclave::ReleaseSyncRequests(const CpuList& cpu_list) {
  for (const Cpu& cpu : cpu_list) {
    RunRequest* req = GetRunRequest(cpu);
    CHECK(req->committed());
    CHECK(req->sync_group_owned());
    req->sync_group_owner_set(kSyncGroupNotOwned);
  }
}

bool LocalEnclave::CommitRunRequest(RunRequest* req) {
  SubmitRunRequest(req);
  return CompleteRunRequest(req);
}

void LocalEnclave::SubmitRunRequest(RunRequest* req) {
  GHOST_DPRINT(2, stderr, "COMMIT(%d): %s %d", req->cpu().id(),
               req->target().describe(), req->target_barrier());

  if (req->open()) {
    CHECK_EQ(GhostHelper()->Commit(req->cpu()), 0);
  } else {
    // Request already picked up by target CPU for commit.
  }
}

bool LocalEnclave::CompleteRunRequest(RunRequest* req) {
  // If request was picked up asynchronously then wait for the commit.
  //
  // N.B. we must do this even if we call GhostHelper()->Commit() because the
  // the request could be committed asynchronously even in that case.
  while (!req->committed()) {
    Pause();
  }

  ghost_txn_state state = req->state();

  if (state == GHOST_TXN_COMPLETE) {
    return true;
  }

  // The following failures are expected:
  switch (state) {
    // task is dead (agent preempted a task and ran it again subsequently
    // while racing with task exit).
    case GHOST_TXN_TARGET_NOT_FOUND:
      break;

    // stale task or agent barriers.
    case GHOST_TXN_TARGET_STALE:
    case GHOST_TXN_AGENT_STALE:
      break;

    // target CPU's agent is exiting
    case GHOST_TXN_NO_AGENT:
      // If we ever shrink enclaves at runtime, we'll need to modify this check.
      if (IsOnline()) {
        GHOST_ERROR("TXN failed with NO_AGENT, but we are still online!");
      }
      break;

    // target CPU is running a higher priority sched_class.
    case GHOST_TXN_CPU_UNAVAIL:
      break;

    // txn poisoned due to sync-commit failure.
    case GHOST_TXN_POISONED:
      break;

    // txn aborted.
    case GHOST_TXN_ABORTED:
      break;

    // target already on cpu
    case GHOST_TXN_TARGET_ONCPU:
      if (req->allow_txn_target_on_cpu()) {
        break;
      }
      ABSL_FALLTHROUGH_INTENDED;

    default:
      GHOST_ERROR("unexpected state after commit: %s",
                  RunRequest::StateToString(state));
      return false;  // ERROR needs no-return annotation.
  }
  return false;
}

void LocalEnclave::LocalYieldRunRequest(const RunRequest* req,
                                        BarrierToken agent_barrier, int flags) {
  DCHECK_EQ(sched_getcpu(), req->cpu().id());
  int error =
      GhostHelper()->Run(Gtid(0), agent_barrier, StatusWord::NullBarrierToken(),
                         req->cpu(), flags);
  // Sanity check why we failed.
  //   ESTALE: old barrier / missed message
  //   ENODEV: enclave is being destroyed (a kernfs ioctl errno)
  if (error != 0) {
    CHECK(errno == ESTALE || errno == ENODEV);
  }
}

bool LocalEnclave::PingRunRequest(const RunRequest* req) {
  const int run_flags = 0;
  int rc = GhostHelper()->Run(Gtid(GHOST_AGENT_GTID),
                              StatusWord::NullBarrierToken(),  // agent_barrier
                              StatusWord::NullBarrierToken(),  // task_barrier
                              req->cpu(), run_flags);
  return rc == 0;
}

void LocalEnclave::AttachAgent(const Cpu& cpu, Agent* agent) {
  CHECK_EQ(rep(cpu)->agent, nullptr);
  rep(cpu)->agent = agent;
  Enclave::AttachAgent(cpu, agent);
}

void LocalEnclave::DetachAgent(Agent* agent) {
  rep(agent->cpu())->agent = nullptr;
  Enclave::DetachAgent(agent);
}

void LocalEnclave::AdvertiseOnline() {
  // There can be only one open, writable file for agent_online, per enclave.
  // As long as this FD (and any dups) are held open, the system will believe
  // there is an agent capable of scheduling this enclave.
  agent_online_fd_ = openat(dir_fd_, "agent_online", O_RDWR);
  CHECK_GE(agent_online_fd_, 0);

  Enclave::AdvertiseOnline();
}

// We have a bunch of open FDs for enclave resources, such as agent_online and
// any inserted BPF programs.  The next agent taking over the enclave needs to
// wait until these FDs are closed, so it behooves us to close the FDs early
// instead of waiting on the kernel to close them, which takes O(nr_cpus) ms.
//
// Make sure this is idempotent: TerminateAgentTasks() calls this as an
// optimization, but ~LocalEnclave does too to ensure destruction.
void LocalEnclave::PrepareToExit() {
  Enclave::PrepareToExit();
  // Relying on close(), at least for agent_online, to provide a write memory
  // barrier after PrepareToExit, such that any reader who sees agent_online
  // closed will see IsOnline as false (which was set in PrepareToExit).
  //
  // An external observer can see the enclave file agent_online == 0 (read() on
  // agent_online), then contact the Agent, which must see IsOnline == false.
  close(agent_online_fd_);
  agent_online_fd_ = -1;
  agent_bpf_destroy();
}

void LocalEnclave::WaitForOldAgent() {
  WaitForAgentOnlineValue(dir_fd_, /*until=*/0);
}

// static
std::string RunRequest::StateToString(ghost_txn_state state) {
  switch (state) {
    case GHOST_TXN_COMPLETE:
      return "GHOST_TXN_COMPLETE";
    case GHOST_TXN_ABORTED:
      return "GHOST_TXN_ABORTED";
    case GHOST_TXN_TARGET_ONCPU:
      return "GHOST_TXN_TARGET_ONCPU";
    case GHOST_TXN_TARGET_STALE:
      return "GHOST_TXN_TARGET_STALE";
    case GHOST_TXN_TARGET_NOT_FOUND:
      return "GHOST_TXN_TARGET_NOT_FOUND";
    case GHOST_TXN_TARGET_NOT_RUNNABLE:
      return "GHOST_TXN_TARGET_NOT_RUNNABLE";
    case GHOST_TXN_AGENT_STALE:
      return "GHOST_TXN_AGENT_STALE";
    case GHOST_TXN_CPU_OFFLINE:
      return "GHOST_TXN_CPU_OFFLINE";
    case GHOST_TXN_CPU_UNAVAIL:
      return "GHOST_TXN_CPU_UNAVAIL";
    case GHOST_TXN_INVALID_FLAGS:
      return "GHOST_TXN_INVALID_FLAGS";
    case GHOST_TXN_INVALID_TARGET:
      return "GHOST_TXN_INVALID_TARGET";
    case GHOST_TXN_NOT_PERMITTED:
      return "GHOST_TXN_NOT_PERMITTED";
    case GHOST_TXN_INVALID_CPU:
      return "GHOST_TXN_INVALID_CPU";
    case GHOST_TXN_NO_AGENT:
      return "GHOST_TXN_NO_AGENT";
    case GHOST_TXN_UNSUPPORTED_VERSION:
      return "GHOST_TXN_UNSUPPORTED_VERSION";
    case GHOST_TXN_POISONED:
      return "GHOST_TXN_POISONED";
    case GHOST_TXN_READY:
      return "GHOST_TXN_READY";
    default: {
      // Note that the topology may have fewer than `MAX_CPUS` CPUs, so a
      // "SUCCESSFUL_COMMIT" below could actually be an error case. For example,
      // if the state is `75` and the toplogy only has 64 CPUs, then
      // "SUCCESSFUL_COMMIT_ON_CPU_75" will be returned because `MAX_CPUS` is
      // `512` but this state is actually an unexpected state.
      if (state >= 0 && state < MAX_CPUS) {
        return absl::StrCat("SUCCESSFUL_COMMIT_ON_CPU_", state);
      } else {
        return absl::StrCat("UNKNOWN_COMMIT_STATE_", state);
      }
    }
  }
}

void LocalRunRequest::Open(const RunRequestOptions& options) {
  // Wait for current owner to relinquish ownership of the sync_group txn.
  // NOTE: We must acquire ownership of the sync group first, before we modify
  // any transaction fields. This serves as a pseudo-lock to avoid transaction
  // fields getting clobbered by BPF (e.g. via bpf_sync_commit).
  if (options.sync_group_owner != kSyncGroupNotOwned) {
    while (true) {
      int32_t current_owner = sync_group_owner_get();

      if (current_owner == kSyncGroupNotOwned) {
        if (sync_group_take_ownership(options.sync_group_owner)) {
          break;
        }
      } else if (current_owner != options.sync_group_owner) {
        Pause();
      } else {
        break;
      }
    }
    CHECK(sync_group_owned());
  } else {
    CHECK(!sync_group_owned());
  }

  // We do not allow transaction clobbering.
  //
  // Once a transaction is opened it must be committed (sync or async) before
  // opening it again. We rely on the caller doing a Submit() which guarantees a
  // commit-barrier on the transaction.
  CHECK(committed());

  txn_->agent_barrier = options.agent_barrier;
  txn_->gtid = options.target.id();
  txn_->task_barrier = options.target_barrier;
  txn_->run_flags = options.run_flags;
  txn_->commit_flags = options.commit_flags;
  allow_txn_target_on_cpu_ = options.allow_txn_target_on_cpu;
  if (allow_txn_target_on_cpu_) CHECK(sync_group_owned());
  txn_->state.store(GHOST_TXN_READY, std::memory_order_release);
}

bool LocalRunRequest::Abort() {
  ghost_txn_state expected = txn_->state.load(std::memory_order_relaxed);
  if (expected == GHOST_TXN_READY) {
    // We do a compare exchange since we may race with the kernel trying to
    // commit this transaction.
    const bool aborted = txn_->state.compare_exchange_strong(
        expected, GHOST_TXN_ABORTED, std::memory_order_release);
    if (aborted && sync_group_owned()) {
      sync_group_owner_set(kSyncGroupNotOwned);
    }
    return aborted;
  }
  // This transaction has either been claimed (on its way to being committed)
  // or committed.
  return false;
}

}  // namespace ghost
