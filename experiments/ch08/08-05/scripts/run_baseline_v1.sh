#!/usr/bin/env bash
set -u
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.." || exit 90
if [ -e raw/ar.exit ]; then echo 'Refusing overwrite: AR already attempted'; exit 92; fi
VLLM_USE_V2_MODEL_RUNNER=0 /home/ubuntu/vllm023-venv/bin/python scripts/run_engine.py ar > raw/ar.log 2>&1
rc=$?
echo "$rc" > raw/ar.exit
nvidia-smi > raw/ar-post-gpu.txt
exit "$rc"
