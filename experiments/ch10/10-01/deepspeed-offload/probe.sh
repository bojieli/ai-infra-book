#!/bin/sh
set -eu
export CUDA_HOME=/home/ubuntu/ai-infra-book-experiments/tools/flashinfer-cuda130/nvidia/cu13
export MAX_JOBS=4 OMP_NUM_THREADS=4
export TORCH_EXTENSIONS_DIR=/home/ubuntu/ai-infra-book-experiments/ch10/10-01/deepspeed-offload/setup/torch-extensions
exec /home/ubuntu/ai-infra-book-experiments/tools/deepspeed018-venv/bin/python "$(dirname "$0")/probe.py"
