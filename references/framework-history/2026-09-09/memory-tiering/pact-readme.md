# PACT: A Criticality-First Design for Tiered Memory

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

This repository contains the implementation and supporting components for our
ASPLOS 2026 paper **"PACT: A Criticality-First Design for Tiered Memory."**

**Overview.** Our **key insight** is that access frequency is a poor proxy for
performance: a page's true cost is its *criticality* - how much it stalls the
CPU - which depends on access pattern, memory-level parallelism (MLP), and tier
latency, not on how often it is touched. PACT therefore makes online,
page-granular performance criticality a first-class placement signal. Its **key
technical contributions** are: (1) **Per-page Access Criticality (PAC)**, a
metric that attributes per-tier CPU stall time to individual pages online,
estimated from an analytical model over just **four standard CPU performance
counters** with per-tier MLP decomposition from hardware queue-occupancy
counters; and (2) two **PAC-centric migration policies** - *eager demotion*,
which proactively frees fast-tier space, and *adaptive promotion*, which uses
statistical sampling with adaptive binning to identify high-PAC pages without
global sorting or hand-tuned thresholds. PACT realizes both as a lightweight
runtime that places pages by their true performance impact, transparently and
without application changes.

> **Note:** Compared to the PACT system presented in the paper at the ASPLOS'26
> conference, we have updated PACT with several performance improvements, most
> notably, we redesigned the multi-threaded sampling and migration into a
> coroutine-based scheme, and we added batched migration of memory pages. We
> also moved from a custom Linux 5.15 kernel to the built-in tiering support
> available in Linux 6.3. As such, PACT in this repo delivers better performance
> than the numbers reported in the paper.

## How PACT works

PACT is a **standalone userspace runtime**. It attaches to an unmodified,
already-running workload (no recompilation or library changes) and ranks the
workload's pages by **performance criticality (PAC)**: how many CPU stall cycles
each page is responsible for, *independent of how often it is accessed*. It then
drives the kernel's tiering interface to keep the most critical pages in fast
memory. Everything below runs on each ~20 ms cycle:

<p align="center">
  <img src="pact-arch.svg" alt="PACT architecture: per-cycle sample, score (PAC), bin, and migrate pipeline running as a single-core coroutine loop, with adaptive promotion of critical pages to the fast tier and eager, kernel-LRU demotion of cold pages to the slow tier" width="760">
</p>

<p align="center"><sub>PACT's per-cycle pipeline: sample → score (PAC) → bin → migrate, on a single-core coroutine loop.</sub></p>

1. **Sample** - PEBS records the pages the workload loads from the slow tier;
   CHA/uncore counters measure memory-level parallelism (MLP).
2. **Score** - each page's PAC ≈ the CPU stall cycles attributable to it,
   computed from per-tier LLC misses weighted by tier latency and divided by
   MLP: `LLC-stalls = k · LLC-misses / MLP`. High PAC means the page stalls the
   CPU, *independent of how often it is accessed*.
3. **Bin** - pages are grouped into PAC bins whose width self-tunes
   (Freedman–Diaconis) to the live PAC distribution, keeping promotion
   selective even under skewed (power-law) workloads.
4. **Migrate** - pages in the highest-criticality bin are promoted to the fast
   tier; cold pages fall back to the slow tier.

## Repository layout

```
PACT/
├── src/             # the PACT runtime (C source + Makefile)
├── setup/           # host bring-up - do this first
│   ├── kernel/      #   build/boot Linux 6.3 + the tierinit & kswapdrst modules
│   └── env/         #   uncore-freq pinning, CXL/NUMA layout, governor, THP/KSM off
├── run/             # run PACT on a workload (run-pact.sh, workloads.sh)
├── baselines/       # SOTA systems we compare against (TPP, NBT, Nomad, Colloid, Memtis, Soar/Alto)
└── modeling/        # PAC modeling scripts (Figure 3)
```

**`src/` is the PACT runtime - a standalone userspace process.** It performs
PEBS sampling, computes per-page performance criticality, and drives page
migration through the kernel's tiering interface entirely from user space. It
is **independent of the target workload**: it attaches to a running workload
and needs no source changes, recompilation, or library linking on the
workload's side. The `run/` scripts simply launch a workload and the `src/`
runtime side by side and pin them to separate cores.

The top-level directories follow the order you use them: **`setup/` → build
`src/` → `run/`**. `baselines/` and `modeling/` are independent and only needed
to reproduce specific paper results.

## Requirements

The artifact targets the same class of machine used in the paper:

- **Hardware:** an Intel server with a tiered memory layout - Skylake-X /
  Cascade Lake, Sapphire Rapids, or Emerald Rapids (see Limitations). The
  paper uses CloudLab `c220g5` (Skylake-X, 96 GB DRAM per socket, 2 NUMA
  nodes), with the remote NUMA node configured to emulate a slower (CXL-like)
  tier. PEBS and CHA uncore counters are required for PAC sampling.
- **Kernel:** vanilla **Linux 6.3** for PACT (built by
  [`setup/kernel/`](setup/kernel/)). Baselines use their own kernel versions -
  see [`baselines/`](baselines/).
- **Software:** `gcc`, `make`, `libnuma`, `numactl`, `vmtouch`, `gnuplot`
  (plotting), and `perf` (the PAC modeling scripts in [`modeling/`](modeling/)
  read counters via stock `perf stat`). The PACT runtime samples the PMU
  directly through `perf_event_open` and needs no external `perf` binary.
- **Privileges:** kernel install, module loading, and the environment-prep
  scripts require root.

> **Scope.** This is a single-node release. It reproduces the PAC modeling
> experiment end-to-end, builds the PACT runtime and all baseline kernels, and
> runs the single-command workloads. The paper's Redis-YCSB result uses a
> two-node SSH client/server harness that is not part of this release.

## Getting started

Follow these steps top to bottom on a fresh machine.

### 1. Set up the host - [`setup/`](setup/)

```bash
# 1a. Build, install, and boot vanilla Linux 6.3.
cd setup/kernel
./setup_kernel.sh            # clone + configure + build + install + update-grub
# reboot into 6.3, then build the modules:
./build_modules.sh           # builds tierinit.ko and kswapdrst.ko

# 1b. Shrink the fast tier (node 0) with a memmap= boot parameter, then reboot
#     again. This is what creates the fast/slow capacity split; without it the
#     whole workload fits in local DRAM and PACT is a no-op (see setup/README).
#     For a 1:1 split, node-0 usable DRAM = workload RSS / 2.
#     (example for a ~19.5 GB-RSS bc-kron on c220g5, node 0 ~95 GB -> ~10 GB:)
sudo sed -i 's/\(GRUB_CMDLINE_LINUX_DEFAULT="[^"]*\)"/\1 memmap=86G!2G"/' /etc/default/grub
sudo update-grub && sudo reboot

# 1c. Prepare the machine (uncore pinning, CXL/NUMA layout, governor,
#     disable turbo/THP/KSM/NUMA-balancing). Requires root. Re-run after
#     EVERY reboot, including the memmap reboot above.
cd ../env
sudo ./prepare_environment.sh
```

> **Required kernel modules.** Even on a vanilla 6.3 kernel, the tiering
> subsystem needs two out-of-tree modules to work: **`tierinit`** registers
> the far NUMA node as a slow tier and establishes demotion targets (without
> it there is no tier structure to migrate across), and **`kswapdrst`** keeps
> `kswapd` from permanently backing off so demotion does not stall.
> `run-pact.sh` loads both and refuses to start if either is missing. See
> [`setup/kernel/README.md`](setup/kernel/README.md).

See [`setup/README.md`](setup/README.md) for details: the fast-tier sizing
table for step 1b (`memmap=` for other RSS/ratio targets) and the
uncore-frequency tuning for step 1c.

### 2. Build the PACT runtime - [`src/`](src/)

The runtime is a self-contained userspace program with no workload-side
dependencies.

```bash
cd src
make                 # produces ./pact
make check-format    # optional: clang-format style check (needs clang-format >= 16)
```

See [`src/CODING_STYLE.md`](src/CODING_STYLE.md) for style conventions.

### 3. Run a workload - [`run/`](run/)

```bash
cd run
# Point the dataset paths in workloads.sh at your GAPBS / SPEC / Silo installs:
#   export GAPBS_DIR=/path/to/gapbs   SPEC_DIR=/path/to/cpu2017  ...
./run-pact.sh bc_kron_8t
```

`run-pact.sh` loads the kernel modules from `setup/kernel/`, optionally runs
the environment prep, then launches the workload under PACT. See
[`run/README.md`](run/README.md) for the full runner reference and the list of
predefined workloads.

#### Running PACT directly

PACT is a standalone binary that **attaches to an already-running, externally
CPU-pinned workload** by PID and runs as root (it needs PMU/PEBS access):

```bash
sudo ./src/pact --workload $(pgrep bc)
```

PACT exposes a set of **tuning knobs** that control its sampling, scoring, and
migration behavior and can affect overall performance. **The default values are
the ones we used in the paper**. A few of the most relevant knobs:

| Option | Meaning | Default |
|--------|---------|---------|
| `--workload PID` | target process to manage (pin it externally, e.g. `taskset`) | *required* |
| `--pebs-period N` | PEBS sample period (1 sample per N slow-tier load events) | `400` |
| `--max-migrations-per-cycle N` | pages promoted per ~20 ms cycle; higher = faster convergence to the critical set | `4096` |
| `--bin-count N` | number of PAC bins; only the top (highest-criticality) bin is promoted | `20` |
| `--monitor-cpu` / `--migration-cpu` | pin the event loop / migration thread to one dedicated core | `-1` (none) |

Run `./src/pact --help` for the full option list (cooling, timing intervals,
logging, diagnostics).

## Baseline tiering systems

[`baselines/`](baselines/) holds kernel patches and build scripts for TPP,
NBT, Nomad, Colloid-tpp, Memtis, and Soar/Alto, each with its own README
documenting the exact kernel tag and build steps.

## Limitations and future directions

This is a research artifact built to reproduce the paper's results. A few
constraints of the current implementation are worth knowing up front:

- **Intel server uarchs only (SKX, SPR, EMR).** PACT ships PMU descriptors for
  Skylake-X / Cascade Lake (e.g. CloudLab `c220g5`) and Sapphire Rapids /
  Emerald Rapids. The core DRD and CHA-TOR event encodings for all three are
  validated on real silicon; the SPR/EMR PAC latency constants (`k_dram`,
  `k_cxl`) currently reuse the SKX values pending per-uarch calibration, so
  absolute PAC magnitudes on SPR/EMR are approximate (tiering decisions, which
  depend on relative PAC, are unaffected). PACT **aborts on an unrecognized
  CPU** by default rather than produce invalid results; other
  microarchitectures (Granite Rapids, AMD) are not yet supported.
- **Two tiers, single node.** PACT assumes one fast tier (local DRAM) and one
  CXL-like slow tier on a 2-NUMA-node host. More than two tiers, multi-socket
  fan-out, and multi-node setups are out of scope for this release.
- **Hardware sampling required.** PAC profiling depends on PEBS plus CHA/uncore
  occupancy counters (read directly via `perf_event_open`), and the runtime must
  run as root.
- **Attaches to a running, pre-pinned workload.** PACT manages an existing
  process by PID; it does not launch or CPU-pin workloads itself (the `run/`
  scripts handle that around it).

Natural directions for future work (and good places to contribute): calibrating
the PAC model for additional CPUs, generalizing placement beyond two tiers,
alternative access-sampling backends, and a self-contained workload launcher.

**Contributions are welcome.** Issues and pull requests, whether bug fixes,
new platform calibrations, or documentation improvements, are appreciated.
Please keep changes consistent with [`src/CODING_STYLE.md`](src/CODING_STYLE.md)
and make sure `make` and `make check-format` pass before opening a PR.

## Citation

If you use this work, please cite our ASPLOS 2026 paper:

```bibtex
@InProceedings{pact.asplos26,
       author = {Hamid Hadian and Jinshu Liu and Hanchen Xu and Hansen Idden and Huaicheng Li},
        title = "{PACT: A Criticality-First Design for Tiered Memory}",
    booktitle = {Proceedings of the 31st ACM International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS)},
         year = {2026},
}
```

## Contact

**Maintainers:**
- Hamid Hadian - [hamidhadian@vt.edu](mailto:hamidhadian@vt.edu)
- Hanchen Xu - [hanry@vt.edu](mailto:hanry@vt.edu)
- Huaicheng Li - [huaicheng@vt.edu](mailto:huaicheng@vt.edu)

For questions about the research or implementation, please open an issue or
contact a maintainer.

## License

The PACT runtime is released under the [MIT License](LICENSE). Vendored
third-party headers, kernel patches (GPL-2.0), and documentation/data carry
their own licenses - see [LICENSE](LICENSE) and [NOTICE](NOTICE).
