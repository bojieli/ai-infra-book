# Performance Predictability in Heterogeneous Memory

Artifact for the ASPLOS '26 paper — **[Performance Predictability in Heterogeneous Memory](https://dl.acm.org/doi/10.1145/3779212.3790201)**.

## Overview

```
   ____    _    __  __ ____  
  / ___|  / \  |  \/  |  _ \ 
 | |     / _ \ | |\/| | |_) |
 | |___ / ___ \| |  | |  __/ 
  \____/_/   \_\_|  |_|_|    

```

> CAMP: Causal Analytical Memory Prediction
CAMP is a principled framework for accurately predicting application slowdown on heterogeneous memory systems combining DRAM and CXL. Using at most 12 hardware performance counters, it decomposes slowdown into three orthogonal components (demand reads, cache/prefetching, and stores). It can predict CXL/NUMA slowdown with requiring only a DRAM baseline run for latency-bound workloads. It also provides a closed-form model for weighted DRAM–CXL interleaving.

This repository contains the artifact code for reproducing the experiments in the paper. It is organized into two directories corresponding to the two CAMP models.

## Repository Structure

```
CAMP-Private/
├── prof/                # CXL slowdown prediction (DRAM run → predict CXL-induced stalls)
│   ├── <suite>/         # One directory per workload suite
│   ├── microbenchmarks/ # Calibration prediction models
│   └── proc/            # Data processing & model fitting (update_data.py, param.py, prof.py)
└── interleave/          # Weighted interleaving prediction (DRAM:CXL ratio sweep)
    ├── <suite>/         # One directory per workload suite
    ├── proc/            # Data processing & prediction (update_data.py, prof.py, pred.py)
    └── kernel-patch/    # Linux kernel patch for dynamic interleave weight control
```

- **`prof/`** — Implements the **CXL slowdown prediction model**. Runs each workload in DRAM-only mode (local node 0) — plus a CXL run for bandwidth-bound workloads — and uses the captured PMU signals to analytically decompose and predict CXL-induced slowdown. Microbenchmarks in `microbenchmarks/` calibrate prediction model coefficients via `param.py`.

- **`interleave/`** — Implements the **weighted interleaving prediction model**. Sweeps DRAM:CXL interleaving ratios (plus all-DRAM `L100` and all-CXL `L0` endpoints) by writing weights to `/sys/devices/system/node/node{0,1}/access0/il_weight` via the included kernel patch, then provides a closed-form model for performance at any interleaving ratio.

## System Requirements

- Linux with CXL/NUMA support and Intel PMU
- `perf`, `numactl`, `vmtouch`, `libgfortran5`, `libxmu6`
- `sudo` access (required for NUMA configuration, CPU frequency control, and perf events)
- Per-suite prerequisites listed in the [Workload Suites](#workload-suites) section

## Setup

Install common dependencies from either experiment directory:

```bash
./setup.sh
```

For `interleave/` experiments, apply the kernel patch once to enable the `il_weight` sysfs knobs:

```bash
cd interleave/kernel-patch
patch -p1 < interleave.patch   # apply to your kernel source, then rebuild
```

## Usage

### Slowdown Prediction (`prof/`)

1. Run a workload suite (e.g., `cpu2017`):
   ```bash
   cd prof/cpu2017
   sudo ./run.sh w.txt          # run all workloads
   sudo ./run.sh w.txt 1        # run only workload #1
   ```

2. Run microbenchmarks to calibrate the model:
   ```bash
   cd prof/microbenchmarks
   sudo ./run.sh w.txt
   ```

3. Calibrate model coefficients:
   ```bash
   cd prof/proc
   python3 update_data.py       # parse perf output → csv/
   python3 param.py             # fit slowdown model → params.txt
   ```

4. Analyze slowdown decomposition:
   ```bash
   python3 prof.py              # generate plots/ with per-component breakdown
   ```

### Weighted Interleaving Prediction (`interleave/`)

1. Run a workload suite with the interleaving sweep:
   ```bash
   cd interleave/cpu2017
   sudo ./run.sh w.txt          # run all workloads (default: 9 interleaving ratios + L100 + L0)
   sudo ./run.sh w.txt 1        # run only workload #1
   ```

   Override the sweep resolution (default `INTERLEAVE_PARTITIONS=10` yields 9 ratio points):
   ```bash
   sudo INTERLEAVE_PARTITIONS=5 ./run.sh w.txt 1   # 4 weight points
   ```

2. Post-process results:
   ```bash
   cd interleave/proc
   python3 update_data.py       # parse perf output → csv/all_data.csv
   python3 prof.py              # measured slowdown breakdown → plots/
   python3 pred.py              # predicted vs. measured + best-ratio report → plots/
   ```

## Workload Suites

All suites share the same `run.sh` interface. See `interleave/README.md` for full per-suite setup instructions.

| Suite | Directory | Notes |
|-------|-----------|-------|
| SPEC CPU2017 | `cpu2017/` | Requires separate SPEC license and installation |
| PARSEC | `parsec/` | Built in-repo; install deps with `pkgdep.sh` |
| PBBS | `pbbs/` | Build with `install_pbbsbench/install.sh`; generate inputs with `gendata.sh` |
| GAPBS | `gapbs/` | Requires [GAPBS](https://github.com/sbeamer/gapbs) binary and graph datasets |
| DLRM | `dlrm/` | Requires [MERCI](https://github.com/SNU-ARC/MERCI) at `/mnt/sda4` |
| GPT-2 | `gpt-2/` | Model files (124M–1.5B) pre-staged at `/mnt/sda4/gpt-2/models` |
| Redis | `redis/` | Two-node client/server setup; build Redis 6.2 + YCSB via `install_redis/` |
| Phoronix | `phoronix/` | Install with `install.sh`; two scripts: `run.sh` and `run_noop.sh` |
| XSBench | `xsbench/` | Pre-built binary at `/mnt/sda4/XSBench/openmp-threading/XSBench` |

## Output Format

Raw results land in `rst/<workload>/` with the following extensions:

| Extension | Contents |
|-----------|----------|
| `.data` | `perf stat` hardware counter output |
| `.time` | Wall time, peak memory, context switches (`/usr/bin/time`) |
| `.log` | Full run log with metadata |
| `.output` | Program stdout/stderr |
| `.mem` | Per-node free memory over time |
| `.sysinfo` | Hardware/OS snapshot at run time |

Processed outputs:
- `csv/all_data.csv` (interleave) or `csv/mLOCAL.csv` + `csv/mNUMA.csv` (prof)
- `plots/<suite>__<workload>.png` — slowdown breakdown
- `plots/<suite>__<workload>__sd_*_pred.png` — predicted vs. measured per component

## Citation

```bibtex
@inproceedings{liu2026camp,
  title     = {Performance Predictability in Heterogeneous Memory},
  author    = {Liu, Jinshu and Xu, Hanchen and Berger, Daniel S. and Aguilera, Marcos K. and Li, Huaicheng},
  booktitle = {Proceedings of the 31st ACM International Conference on Architectural Support for Programming Languages and Operating Systems},
  series    = {ASPLOS '26},
  year      = {2026},
  doi       = {10.1145/3779212.3790201}
}
```

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
