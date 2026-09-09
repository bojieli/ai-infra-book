#!/bin/bash
# Not executed by this CPU-only worker. Run only on an authorized four-GPU host.
set -u
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1 CUBLAS_WORKSPACE_CONFIG=:4096:8
run="results/gpu-$(date -u +%Y%m%dT%H%M%SZ)-$$"
mkdir -p "$run"
python -m pip freeze > "$run/pip-freeze.txt" 2>&1
nvidia-smi -q > "$run/nvidia-smi.txt" 2>&1
ps -axo pid,ppid,pcpu,rss,comm > "$run/coexistence.txt"
python -m torch.distributed.run --standalone --nproc_per_node=4 gpu_handoff.py --output "$run" > "$run/stdout.log" 2> "$run/stderr.log"
code=$?
printf '%s\n' "$code" > "$run/exit_code.txt"
exit "$code"
