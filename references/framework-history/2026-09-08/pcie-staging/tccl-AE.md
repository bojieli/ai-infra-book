# Artifact Evaluation

While the repository contains the full source codes for TCCL and the scripts to reproduce all evaluation results in the paper, the artifact also includes comparison baselines (NCCL and MSCCL) and benchmarks (nccl-tests and Megatron) to promote reproducibility of experimental results. This manual describes how the artifact can be obtained, necessary preprocessing steps, and how to conduct experiments using the scripts provided.

## How to access the artifact

Download the artifact as follows:
```shell
$ wget https://github.com/mcrl/tccl/releases/download/tccl-aec/tccl-aec.tar.gz
$ tar xf tccl-aec.tar.gz
```

## Installation

First, we should execute initialization scripts as follows:
```shell
$ source tccl-aec/setup_env.sh
$ source tccl-aec/setup_conda.sh
$ source tccl-aec/setup_dataset.sh
```

The script `setup_env.sh` sets necessary environment variables such as `TCCL_ROOT` used in the later steps. This script should be executed before any other scripts for each shell open.

The script `setup_conda.sh` creates a conda environment and installs PyTorch, Megatron, and their dependencies. The script `setup_dataset.sh` downloads and preprocesses the dataset for deep learning experiments. Both scripts need to be executed only once.

For the compilation of TCCL, follow [README](./README.md) or use the provided script:
```shell
$ $TCCL_SCRIPTS/compile_tccl.sh
$ ls $TCCL_ROOT/tools/build # pathfinder
... pathfinder ...
$ ls $TCCL_ROOT/build/lib # runtime
... libnccl.so ...
```

The comparison baselines and benchmarks are already built and included in the artifact. If you want to build them by yourselves, follow the below instructions.

### NCCL

You can download and build NCCL with the following commands:
```shell
$ wget https://github.com/NVIDIA/nccl/archive/refs/tags/v2.18.3-1.tar.gz
$ tar xf v2.18.3-1.tar.gz
$ cd nccl-2.18.3-1
$ make src.build
```

### MSCCL

You can download and build MSCCL with the following commands:
```shell
$ wget https://github.com/microsoft/msccl/archive/refs/tags/v0.7.4.tar.gz
$ tar xf v0.7.4.tar.gz
$ cd msccl-0.7.4
$ make src.build
```

### nccl-tests

You can download and build \texttt{nccl-tests} with the following commands:
```shell
$ wget https://github.com/NVIDIA/nccl-tests/archive/refs/tags/v2.13.8.tar.gz
$ tar xf v2.13.8.tar.gz
$ cd nccl-tests-2.13.8
$ make MPI=1 NCCL_HOME=path/to/nccl/build
```

### PyTorch

Unfortunately, PyTorch distributed with package managers, such as \texttt{conda} and \texttt{pip}, has NCCL statically linked to its binary. Thus, we should compile PyTorch from the source to use TCCL or MSCCL as communication backends. The following commands summarize the steps to compile, but you should check the official PyTorch repository for the latest instructions.

```shell
$ conda install cmake ninja -y
$ pip install regex packaging pybind11
$ wget https://github.com/pytorch/pytorch/releases/download/v2.0.1/pytorch-v2.0.1.tar.gz
$ cd pytorch-v2.0.1
$ pip install -r requirements.txt

$ # nvcc should be in PATH
$ export PATH=/usr/local/cuda/bin:$PATH
$ export CMAKE_PREFIX_PATH=${CONDA_PREFIX:-"$(dirname $(which conda))/../"}

$ # pytorch/tools and Megatron/tools conflict; remove pytorch/tools (Maybe patched in the recent version?)
$ rm tools/__init__.py
$ PYTORCH_BUILD_VERSION=2.0.1 PYTORCH_BUILD_NUMBER=0 USE_SYSTEM_NCCL=1 \
    NCCL_INCLUDE_DIR=$TCCL_AEC_ROOT/nccl-2.18.3-1/build/include \
    NCCL_LIB_DIR=$TCCL_AEC_ROOT/nccl-2.18.3-1/build/lib \
    TORCH_CUDA_ARCH_LIST="7.0;8.6" \
    python setup.py bdist_wheel
$ pip install $TCCL_AEC_ROOT/pytorch-v2.0.1/dist/torch-2.0.1-cp311-cp311-linux_x86_64.whl
```

### Megatron

```shell
$ wget https://github.com/NVIDIA/Megatron-LM/archive/refs/tags/23.05.tar.gz
$ tar xf 23.05.tar.gz
$ cd Megatron-LM-23.05

# Few patches
# 1. Fix Unsupported gpu architecture 'compute_90'
# in megatron/fused_kernels/__init__.py, comment out compute_90
# 2. Prevent recompilation of CUDA kernels
# Set os.environ["TORCH_CUDA_ARCH_LIST"] = "7.0;8.6" in megatron/fused_kernels/__init__.py
# 3. Error during BERT training
# Put "num_epochs=10" in megatron/data/dataset_utils.py:get_samples_mapping

$ pip install -e .
```

## Experiment workflow

Once you have built TCCL, you should execute the pathfinder to generate an XML file that contains communication path information. As the pathfinder is an MPI program that runs on multiple nodes, the launch command depends on the cluster environment. We provide three example scripts that launch the pathfinder on the clusters in the paper, which assume the cluster is managed by the SLURM workload manager. The pathfinding process can take several hours. Upon completion, you will find the XML files in the `tccl-aec/workspace` directory. `refs/xmls` directory includes XML files as references, so you can copy them instead. The scripts in the later steps will assume that XML files are properly placed in the workspace directory.

```shell
$ $TCCL_SCRIPTS/launch_pathfinder_amd_v100.sh 
$ $TCCL_SCRIPTS/launch_pathfinder_amd_3090.sh
$ $TCCL_SCRIPTS/launch_pathfinder_intel_v100.sh
(... each script takes a few hours ...)
$ ls $TCCL_AEC_ROOT/workspace
... amd_v100.xml amd_3090.xml intel_v100.xml ...
# Or copy our results into the workspace
$ cp $TCCL_AEC_ROOT/refs/xmls/* $TCCL_AEC_ROOT/workspace
```

You can test TCCL and the generated XML file as follows:
```shell
$ $TCCL_SCRIPTS/launch_test_amd_v100.sh
... NCCL INFO TCCL channel setup done ...
... Out of bounds values : 0 OK ...
```

The script will launch 2-node 8-GPU AllReduce with nccl-tests. If the installation was successful, the log will state that the TCCL channels have been created properly and there are no wrong values. You may compare the performance with NCCL by removing `NCCL_ALGO=TCCL` from the scripts.

To use TCCL in applications, replace the shared library of NCCL with that of TCCL using mechanisms such as `LD_PRELOAD`. Note that the shared library of TCCL is named `libnccl.so` to maximize compatibility. You should also set two environment variables: `TCCL_XML_FILE` and `NCCL_ALGO`. `TCCL_XML_FILE` should be the path to the XML file generated by the pathfinder. `NCCL_ALGO` should be set to TCCL to use the communication paths found by TCCL. Otherwise, it will fall back to NCCL's algorithms.

The following is an example of launching an MPI program with TCCL:
```shell
$ mpirun -x LD_PRELOAD=$TCCL_ROOT/build/lib/libnccl.so \
         -x TCCL_XML_FILE=amd_v100.xml \
         -x NCCL_ALGO=TCCL \
         (... other options ...) \
         ./myapp
```

## Evaluation and expected results

### Collective Communication Primitives

We provide a script `eval_cc.sh` to reproduce all data for the experiments on collective communication primitives. The script will generate scripts that launch nccl-tests with NCCL, MSCCL, and TCCL for all combinations of the clusters, the primitives, the number of nodes, and the number of GPUs used per node. Then, it launches all scripts and stores the outputs into the workspace directory.

```shell
$ $TCCL_SCRIPTS/eval_cc.sh 
$ ls $TCCL_AEC_ROOT/workspace/eval_cc_workspace
(... scripts and outputs ...)
# Or copy our results into the workspace
$ cp -r $TCCL_AEC_ROOT/refs/eval_cc_workspace $TCCL_AEC_ROOT/workspace
```

Another script, `organize_cc_result.sh`, will parse the outputs from the nccl-test and organize the measured bandwidths into a single CSV file. We also included our results to compare. You will get the results with an error within 5\%.

```shell
$ $TCCL_SCRIPTS/organize_cc_result.sh 
$ ls $TCCL_AEC_ROOT/workspace
... eval_cc_result.csv ...
# Compare with our result
$ ls $TCCL_AEC_ROOT/refs/*.csv
... eval_cc_result.csv ...
```

### Training DL Models

Similarly, we provide a script `eval_dl.sh` to reproduce all data for the experiments on training DL models. The script trains the deep learning models for a few iterations on each cluster with different parallelism.

```shell
$ $TCCL_SCRIPTS/eval_dl.sh 
$ ls $TCCL_AEC_ROOT/workspace/eval_dl_workspace
(... scripts and outputs ...)
# Or copy our results into the workspace
$ cp -r $TCCL_AEC_ROOT/refs/eval_dl_workspace $TCCL_AEC_ROOT/workspace
```

Another script, `organize_dl_result.sh`, will extract the execution time per iteration from the logs. We include our result to compare with and expect you to get the execution time with an error within 5\%.

```shell
$ $TCCL_SCRIPTS/organize_dl_result.sh 
$ ls $TCCL_AEC_ROOT/workspace
... eval_dl_result.csv ...
# Compare with our result
$ ls $TCCL_AEC_ROOT/refs/*.csv
... eval_dl_result.csv ...
```

### Troubleshoot

* Megatron-LM sometimes hangs on building CUDA kernels. If you encounter this issue, delete the `megatron/fused_kernels/build` directory and re-run the script.