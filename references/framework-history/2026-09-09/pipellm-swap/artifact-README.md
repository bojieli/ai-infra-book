# PipeLLM

This repository is a prototype of paper **PipeLLM: Fast and Confidential Large Language Model Services with Speculative Pipelined Encryption** (https://arxiv.org/abs/2411.03357).

## Basic Steps

Before compiling PipeLLM, the hard-code filepaths and parameters in the source files should be modified.

Compile PipeLLM:

```bash
make -j $(nproc)
```

This would generate `libcrypto.so.3`.

To use PipeLLM, add this file to `LD_PRELOAD`:
```bash
export LD_PRELOAD=$(pwd)/libcrypto.so.3
export LD_LIBRARY_PATH=$(pwd)
```

Before running the first program, PipeLLM should get the pattern of the IV with:

```bash
./profile_iv.sh
```

## Use PipeLLM in CUDA Applications

Apart from the basic steps, the following should be done:

To use PipeLLM with applications compiled with `nvcc`, the applications should be recompiled adding `--cudart shared` flag (see `profile.sh` as an example).

## Use PipeLLM in Pytorch

Apart from the basic steps, the following should be done:

First, copy `$(pwd)/libcudart_static.a` to `/usr/local/cuda/lib64/` (please backup the original file first).

Next, compile pytorch from source.

## Use PipeLLM in conda environment

Apart from the basic steps, the following should be done:

* Move the `libcrypto.so.3` in the `lib` directory of the conda venv (possibly in `anaconda3/envs/vllm/lib`) to `libcrypto.so.4`
* Move the `libcrypto.so.3` in this repo to the `lib` directory of the conda venv.
