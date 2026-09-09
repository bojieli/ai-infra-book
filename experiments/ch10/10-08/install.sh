#!/usr/bin/env bash
set -euo pipefail
export VERLRL_ROOT=/home/ubuntu/ai-infra-book-experiments/experiments/ch10/10-08
export VERLRL_PRIVATE=/home/ubuntu/ai-infra-book-experiments/tools/verl-private
export VERLRL_SOURCE="$VERLRL_PRIVATE/verl-project-verl-d040717"
export UV_CACHE_DIR="$VERLRL_PRIVATE/uv-cache" UV_PYTHON_INSTALL_DIR="$VERLRL_PRIVATE/python" UV_LINK_MODE=hardlink UV_CONCURRENT_DOWNLOADS=2 UV_CONCURRENT_BUILDS=1
mkdir -p "$VERLRL_PRIVATE"
cd "$VERLRL_PRIVATE"
if [ ! -d "$VERLRL_SOURCE" ]; then
  curl -fL --max-time 90 https://api.github.com/repos/verl-project/verl/tarball/d040717b21af2e23e8e789a3e354cff2394ae2de -o verl-source.tar.gz
  tar -xzf verl-source.tar.gz
fi
cd "$VERLRL_SOURCE"
# Reproduce only in the private environment. Do not regenerate uv.lock.
python3 "$VERLRL_ROOT/watchdog.py" --out "$VERLRL_ROOT/install-$(date -u +%Y%m%dT%H%M%SZ)" --private "$VERLRL_PRIVATE" -- /home/ubuntu/.local/bin/uv sync --frozen --extra vllm --extra fsdp --python 3.12
# Fixed, hashed compatibility override on top of the untouched upstream lock.
taskset -c 12-15 "$VERLRL_SOURCE/.venv/bin/python" "$VERLRL_ROOT/apply_numpy_override.py"
python3 "$VERLRL_ROOT/watchdog.py" --out "$VERLRL_ROOT/prepare-$(date -u +%Y%m%dT%H%M%SZ)" --private "$VERLRL_PRIVATE" -- "$VERLRL_SOURCE/.venv/bin/python" "$VERLRL_ROOT/prepare.py"
python3 "$VERLRL_ROOT/patch_observe.py"
