# ghOSt: Fast &amp; Flexible User-Space Delegation of Linux Scheduling

ghOSt is a general-purpose delegation of scheduling policy implemented on top of
the Linux kernel. The ghOSt framework provides a rich API that receives
scheduling decisions for processes from userspace and actuates them as
transactions. Programmers can use any language or tools to develop policies,
which can be upgraded without a machine reboot. ghOSt supports policies for a
range of scheduling objectives, from µs-scale latency, to throughput, to energy
efficiency, and beyond, and incurs low overheads for scheduling actions. Many
policies are just a few hundred lines of code. Overall, ghOSt provides a
performant framework for delegation of thread scheduling policy to userspace
processes that enables policy optimization, non-disruptive upgrades, and fault
isolation.

[SOSP '21 Paper](https://dl.acm.org/doi/10.1145/3477132.3483542)\
[SOSP '21 Talk](https://youtu.be/j4ABe4dsbIY)

The ghOSt kernel is [here](https://www.github.com/google/ghost-kernel). You must
compile and run the userspace component on the ghOSt kernel.

This is not an officially supported Google product.

---

### Compilation

The ghOSt userspace component can be compiled on Ubuntu 20.04 or newer.

1\. We use the Google Bazel build system to compile the userspace components of
ghOSt. Go to the
[Bazel Installation Guide](https://docs.bazel.build/versions/main/install.html)
for instructions to install Bazel on your operating system.

2\. Install ghOSt dependencies:

```
sudo apt update
sudo apt install libnuma-dev libcap-dev libelf-dev libbfd-dev gcc clang-12 llvm zlib1g-dev python-is-python3
```

Note that ghOSt requires GCC 9 or newer and Clang 12 or newer.

3\. Compile the ghOSt userspace component. Run the following from the root of
the repository:

```
bazel build -c opt ...
```

`-c opt` tells Bazel to build the targets with optimizations turned on. `...`
tells Bazel to build all targets in the `BUILD` file and all `BUILD` files in
subdirectories, including the core ghOSt library, the eBPF code, the schedulers,
the unit tests, the experiments, and the scripts to run the experiments, along
with all of the dependencies for those targets. If you prefer to build
individual targets rather than all of them to save compile time, replace `...`
with an individual target name, such as `agent_shinjuku`.

---

### ghOSt Project Layout

- `bpf/user/`
  - ghOSt contains a suite of BPF tools to assist with debugging and performance
    optimization. The userspace components of these tools are in this directory.
- `experiments/`
  - The RocksDB and antagonist Shinjuku experiments (from our SOSP paper) and
    microbenchmarks. Use the Python scripts in `experiments/scripts/` to run the
    Shinjuku experiments.
- `kernel/`
  - Headers that have shared data structures used by both the kernel and
    userspace.
- `lib/`
  - The core ghOSt userspace library.
- `schedulers/`
  - ghOSt schedulers. These schedulers include:
    - `biff/`, Biff (bare-bones FIFO scheduler that schedules everything with
      BPF code)
    - `cfs/` CFS (ghOSt implementation of Linux Completely Fair Scheduler
      policy)
    - `edf/`, EDF (Earliest Deadline First)
    - `fifo/centralized/`, Centralized FIFO
    - `fifo/per_cpu/`, Per-CPU FIFO
    - `shinjuku/`, Shinjuku
    - `sol/`, Speed-of-Light (bare-bones centralized FIFO scheduler that runs as
      fast as possible)
- `shared/`
  - Classes to support shared-memory communication between a scheduler and
    another application(s). Generally, this communication is useful for the
    application to send scheduling hints to the scheduler.
- `tests/`
  - ghOSt unit tests.
- `third_party/`
  - `bpf/`
    - Contains the kernel BPF code for our suite of BPF tools (mentioned above).
      This kernel BPF code is licensed under GPLv2, so we must keep it in
      `third_party/`.
  - The rest of `third_party/` contains code from third-party developers and
    `BUILD` files to compile the code.
- `util/`
  -  Helper utilities for ghOSt. For example, `pushtosched` can be used to move
     a batch of kernel threads from the ghOSt scheduling class to
     `CFS (SCHED_OTHER)`.

---

### Running the ghOSt Tests

We include many different tests to ensure that both the ghOSt userspace code and
the ghOSt kernel code are working correctly. Some of these tests are in `tests/`
while others are in other subdirectories. To view all of the tests, run:
```
bazel query 'tests(//...)'
```

To build a test, such as `agent_test`, run:
```
bazel build -c opt agent_test
```

To run a test, launch the test binary directly:
```
bazel-bin/agent_test
```

Generally, Bazel encourages the use of `bazel test` when running tests. However,
`bazel test` sandboxes the tests so that they have read-only access to `/sys`
and are constrained in how long they can run for. However, the tests need write
access to `/sys/fs/ghost` to coordinate with the kernel and may take a long time
to complete. Thus, to avoid sandboxing, launch the test binaries directly (e.g.,
`bazel-bin/agent_test`).

---

### Running a ghOSt Scheduler

We will run the per-CPU FIFO ghOSt scheduler and use it to schedule Linux
pthreads.

1. Build the per-CPU FIFO scheduler:
```
bazel build -c opt fifo_per_cpu_agent
```

2. Build `simple_exp`, which launches a series of pthreads that run in ghOSt.
`simple_exp` is a collection of tests.
```
bazel build -c opt simple_exp
```

3. Launch the per-CPU FIFO ghOSt scheduler:
```
bazel-bin/fifo_per_cpu_agent --ghost_cpus 0-1
```
The scheduler launches ghOSt agents on CPUs (i.e., logical cores) 0 and 1 and
will therefore schedule ghOSt tasks onto CPUs 0 and 1. Adjust the `--ghost_cpus`
command line argument value as necessary. For example, if you have an 8-core
machine and you wish to schedule ghOSt tasks on all cores, then pass `0-7` to
`--ghost_cpus`.

4. Launch `simple_exp`:
```
bazel-bin/simple_exp
```
`simple_exp` will launch pthreads. These pthreads in turn will move themselves
into the ghOSt scheduling class and thus will be scheduled by the ghOSt
scheduler. When `simple_exp` has finished running all tests, it will exit.

5. Use `Ctrl-C` to send a `SIGINT` signal to `fifo_per_cpu_agent` to get it to
stop.

---

### Enclaves, Rebootless Upgrades, and Handling Scheduler Failures

ghOSt uses **enclaves** to group agents and the threads that they are
scheduling. An enclave contains a subset of CPUs (i.e., logical cores) in a
machine, the agents that embody those CPUs, and the threads in the ghOSt
scheduling class that the enclave agents can schedule onto the enclave CPUs. For
example, in the `fifo_per_cpu_agent` example above, an enclave is created that
contains CPUs 0 and 1, though the enclave can be configured to contain any
subset of CPUs in the machine, and even all of them. In the `fifo_per_cpu_agent`
example above, two per-CPU FIFO agents enter the enclave along with the
`simple_exp` threads when the `simple_exp` process is started.

Enclaves provide an easy way to partition the machine to support co-location of
policies and tenants, a particularly important feature as machines scale out
horizontally to contain hundreds of CPUs and new accelerators. Thus, multiple
enclaves can be constructed with *disjoint* sets of CPUs.

#### Rebootless Upgrades

ghOSt supports rebootless upgrades of scheduling policies, using an enclave to
encapsulate current thread and CPU state for a policy undergoing an upgrade.
When you want to upgrade a policy, the agents in the new process that you launch
attempt to attach to the existing enclave, waiting for the old agents running in
the enclave to exit. Once the old agents exit, the new agents take over the
enclave and begin scheduling.

#### Handling Scheduler Failures

ghOSt also recovers from scheduler failures (e.g., crashes, malfunctions, etc.)
without triggering a kernel panic or machine reboot. To recover from a scheduler
failure, you should generally destroy the failed scheduler's enclave and then
launch the scheduler again. Destroying an enclave will kill the malfunctioning
agents if necessary and will move the threads in the ghOSt scheduling class to
CFS (Linux Completely Fair Scheduler) so that they can continue to be scheduled
until you potentially pull them into ghOSt again.

To see all enclaves that currently exist in ghOSt, use `ls` to list them via
`ghostfs`:
```
$ ls /sys/fs/ghost
ctl  enclave_1	version
```

To kill an enclave, such as `enclave_1` above, run the following command,
replacing `enclave_1` with the name of the enclave:
```
echo destroy > /sys/fs/ghost/enclave_1/ctl
```

To kill all enclaves (which is generally useful in development), run the
following command:
```
for i in /sys/fs/ghost/enclave_*/ctl; do echo destroy > $i; done
```
