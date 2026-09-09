#!/usr/bin/env bash
set -u
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.." || exit 90
PY=/home/ubuntu/vllm023-venv/bin/python
if [ "$(cat raw/ar.exit 2>/dev/null)" != 0 ]; then echo 'AR must complete successfully first'; exit 91; fi
for mode in dflash-7 dflash-15; do
 if [ -e "raw/$mode.exit" ]; then echo "Refusing overwrite: $mode already attempted"; exit 92; fi
 "$PY" scripts/run_engine.py "$mode" > "raw/$mode.log" 2>&1
 rc=$?
 echo "$rc" > "raw/$mode.exit"
 nvidia-smi > "raw/$mode-post-gpu.txt"
 if [ "$rc" != 0 ]; then exit "$rc"; fi
done
