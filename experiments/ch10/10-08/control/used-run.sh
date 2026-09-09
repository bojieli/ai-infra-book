#!/usr/bin/env bash
set -euo pipefail
export VERLRL_ROOT=/home/ubuntu/ai-infra-book-experiments/experiments/ch10/10-08
export VERLRL_PRIVATE=/home/ubuntu/ai-infra-book-experiments/tools/verl-private
export VERLRL_SOURCE="$VERLRL_PRIVATE/verl-project-verl-d040717"
export PATH="$VERLRL_SOURCE/.venv/bin:$PATH"
export VERLRL_RUN=${VERLRL_RUN:-run_$(date -u +%Y%m%dT%H%M%SZ)}
if [ -e "$VERLRL_ROOT/$VERLRL_RUN/stdout.log" ]; then echo "Refusing to overwrite existing run: $VERLRL_RUN" >&2; exit 2; fi
export VERLRL_OBSERVE="$VERLRL_ROOT/$VERLRL_RUN/observations"
export PYTHONPATH="$VERLRL_ROOT:$VERLRL_SOURCE"
export TMPDIR="$VERLRL_PRIVATE/t" VERLRL_IPC="$VERLRL_PRIVATE/i"
export HF_HOME="$VERLRL_PRIVATE/hf" XDG_CACHE_HOME="$VERLRL_PRIVATE/cache" TRITON_CACHE_DIR="$VERLRL_PRIVATE/triton" VLLM_CACHE_ROOT="$VERLRL_PRIVATE/vllm-cache" TORCH_HOME="$VERLRL_PRIVATE/torch-cache" FLASHINFER_WORKSPACE_BASE="$VERLRL_PRIVATE/flashinfer"
export CUDA_HOME=/home/ubuntu/ai-infra-book-experiments/tools/flashinfer-cuda130/nvidia/cu13
export PATH="$CUDA_HOME/bin:$PATH"
export CUDA_VISIBLE_DEVICES=0 PYTHONUNBUFFERED=1 HYDRA_FULL_ERROR=1 VERL_USE_UV=0 WANDB_MODE=disabled
export MALLOC_ARENA_MAX=2 MALLOC_TRIM_THRESHOLD_=65536 MALLOC_MMAP_THRESHOLD_=65536
export RAY_USAGE_STATS_ENABLED=0 RAY_DEDUP_LOGS=0
mkdir -p "$TMPDIR" "$VERLRL_IPC" "$VERLRL_OBSERVE" "$XDG_CACHE_HOME"
cd "$VERLRL_PRIVATE"
exec /usr/bin/python3 "$VERLRL_ROOT/watchdog.py" --out "$VERLRL_ROOT/$VERLRL_RUN" --private "$VERLRL_PRIVATE" --gpu --seconds 1200 -- python "$VERLRL_ROOT/launch.py"
