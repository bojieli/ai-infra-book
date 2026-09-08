# Install

## Prerequisite

Make sure GCC and NVCC is installed on your system. 
You can install GCC via `apt install build-essential`.
For NVCC, please refer to [CUDA-12.9 Installation Guide](https://developer.nvidia.com/cuda-12-9-0-download-archive).

## Clone repository

```bash
git clone https://github.com/Terra-Flux/PolyRL.git --recursive
cd polyrl
```

## Create conda environment

PolyRL requires `uv` to install local packages.
```bash
conda create -n polyrl python=3.12 uv
conda activate polyrl
```

> ***Note***: If `libnuma` is not installed in your environment, install via `conda install -c conda-forge numactl`. 

## Install Rust

PolyRL rollout manager is implemented in Rust for better performance. 
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

## Install dependencies

- SGLang:

```bash
uv pip install sglang==0.5.5
```

- Flash Attention (Recommended mm_backend by SGLang):

```bash
uv pip install flash-attn --no-build-isolation
```

- VeRL

```bash
cd 3rdparty/verl
uv pip install -e .
cd ../..
```

## Install PolyRL

```bash
uv pip install -e .
```
