#!/bin/sh
set -eu
ulimit -c 0
BOOK_SGLANG_ENV=/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv
export CUDA_HOME="$BOOK_SGLANG_ENV/lib/python3.10/site-packages/nvidia/cu13"
export PATH="$CUDA_HOME/bin:$PATH"
export TVM_FFI_CACHE_DIR="$PWD/jit-cache-cu13-v2"
exec "$BOOK_SGLANG_ENV/bin/python" run_device_prefix.py "$@"
