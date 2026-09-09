#!/bin/sh
set -eu
BOOK_FLASHINFER_ENV=/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv
BOOK_FLASHINFER_CUDA=/home/ubuntu/ai-infra-book-experiments/tools/flashinfer-cuda130/nvidia/cu13
export CUDA_HOME="$BOOK_FLASHINFER_CUDA"
export PATH="$CUDA_HOME/bin:$PATH"
exec "$BOOK_FLASHINFER_ENV/bin/python" "$(dirname "$0")/run.py" "$@"
