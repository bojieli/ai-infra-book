

## Usage

The output files are in `rst` for each workload suite.
The data processing files are provided in `proc`.

### Steps

* Setup (Install packages and perf)
  ```
  ./setup.sh
  ```
* Go to a workload suite directory, (for example, cpu2017), run the 1st workload in the suite:
  ```
  sudo ./run.sh w.txt 1
  ```
  Run all workloads:
  ```
  sudo ./run.sh w.txt
  ```

* Collect the performance counters from the output files. 
`proc` provides a basic processing code for visualizing 
the slowdown breakdown.

  + Copy the `rst` to the directory where `update_data.py` and `process.py` is.
  + Generate data files in `csv`   
  ```
  python3 update_data.py
  ``` 
  + Process the data in `csv` and generate plots in `plots`
  ```
  python3 process.py
  ``` 

### Notes

* The `run.sh` files run each workload three ways: a weighted-interleave sweep across NUMA nodes `0` and `1` (`CXL-Interleave`), once local (NUMA node `0`, `L100`), and once remote (NUMA node `1`, `L0`).
The default remote NUMA node is set as `1`.
For the remote memory other than NUMA node `1` in multi-nodes servers, set `--membind 1` to other values.

* The `CXL-Interleave` sweep walks node0:node1 weights from `(P-1):1` down to `1:(P-1)`, where `P` is `INTERLEAVE_PARTITIONS` (default `10`, yielding 9 ratios). Weights are written to `/sys/devices/system/node/node{0,1}/access0/il_weight` and the workload (plus any `vmtouch` prefetch) is launched with `numactl -i 0,1`. Override per run, e.g.:
  ```
  sudo INTERLEAVE_PARTITIONS=5 ./run.sh w.txt 1   # 4 weight points
  ```
  Results land in `rst/<workload>/CXL-Interleave-<j>-<i>.{log,time,output,data,mem,sysinfo}`.

---

## Workload Suites

All suites share the same `run.sh` interface:
```bash
sudo ./run.sh w.txt        # run all workloads listed in w.txt
sudo ./run.sh w.txt <N>    # run only the Nth line of w.txt
```
Results are written to `rst/`.

### cpu2017 (SPEC CPU2017)

**Prerequisites:** SPEC CPU2017 installed and benchmarks built. `perf` and `/usr/bin/time` must be in PATH.

```bash
cd cpu2017
sudo ./run.sh w.txt 1
```

### dlrm (Deep Learning Recommendation Model)

**Prerequisites:** Install [MERCI](https://github.com/SNU-ARC/MERCI) at `/mnt/sda4` (default; edit `run.sh` to change).

```bash
cd dlrm
sudo ./run.sh w.txt 1
```

### gapbs (GAP Benchmark Suite)

**Prerequisites:** Install [GAPBS](https://github.com/sbeamer/gapbs) and download graph datasets. Edit the path variables near the top of `run.sh` if your installation differs from the defaults:
```bash
export GAPBS_DIR="/mnt/sda4/gapbs"
export GAPBS_GRAPH_DIR="/mnt/sda4/gapbs/benchmark/graphs"
```
`vmtouch` is also required (`apt install vmtouch`).

```bash
cd gapbs
sudo ./run.sh w.txt 1
```

### gpt-2 (GPT-2 Inference)

**Prerequisites:** GPT-2 model files placed under `/mnt/sda4/gpt-2/models` (edit `GPT2_MDL_DIR` in `run.sh` to change). `vmtouch` is required.

```bash
cd gpt-2
sudo ./run.sh w.txt 1
```

### parsec (PARSEC Benchmark Suite)

**Prerequisites:** Install system dependencies, then install PARSEC:
```bash
cd parsec
sudo bash pkgdep.sh          # install apt dependencies (gcc, libxmu6, …)
# install PARSEC separately and ensure parsecmgmt is in PATH
```
Each workload subdirectory contains a `cmd.sh` that `run.sh` invokes.

```bash
sudo ./run.sh w.txt 1
```

### pbbs (Problem Based Benchmark Suite)

**Prerequisites:** Build PBBS and generate input data:
```bash
cd pbbs/install_pbbsbench
./install.sh      # clone and compile PBBS (default path: /mnt/sda4)
./gendata.sh      # generate input data for each workload
```
Edit the path in `install.sh` if your base directory differs from `/mnt/sda4`. `vmtouch` is required.

```bash
cd pbbs
sudo ./run.sh w.txt 1
```

### phoronix (Phoronix Test Suite)

**Prerequisites:** Install and configure the Phoronix Test Suite:
```bash
cd phoronix
./install.sh                          # install phoronix-test-suite
sudo ./phoronix-test-suite batch-setup
# When prompted:
#   Save test results when in batch mode (Y/n): n
#   Run all test options (Y/n): n
```

Two workload lists are provided:
```bash
sudo ./run.sh w.txt 1          # workloads that use perf
sudo ./run_noop.sh w_noop.txt 1   # workloads that skip perf
```

### redis (Redis + YCSB)

**Prerequisites:** Follow the four setup steps:
```bash
cd redis

# 1. Edit paths.sh to match your machine:
#    REDIS_BASE_DIR, REDIS_DATA_DIR, YCSB_BASE_DIR,
#    REDIS_SERVER (server IP), REDIS_CLIENT (client IP)

# 2. Generate redis.conf from the template
./generate-conf.sh

# 3. Build Redis 6.2 and install system packages
cd install_redis
./install.sh      # compiles Redis into $REDIS_BASE_DIR
./pkgdep.sh       # installs system dependencies

# 4. Build YCSB
./ycsb.sh         # clones and builds YCSB into $YCSB_BASE_DIR
cd ..

# 5. Add Redis binaries to PATH
./create-link.sh
```

```bash
sudo ./run.sh w.txt 1
```

### xsbench (XSBench)

**Prerequisites:** Build XSBench and place the binary at `/mnt/sda4/XSBench/openmp-threading/XSBench` (edit `xsbench/cmd.sh` to change the path).

```bash
cd xsbench
sudo ./run.sh w.txt 1
```

