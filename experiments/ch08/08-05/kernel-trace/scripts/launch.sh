#!/bin/bash
set -u
cd /home/ubuntu/ai-infra-book-experiments/ch08/08-05/kernel-trace || exit 90
mkdir -p raw
name="$1"
shift
if [ -e "raw/$name.log" ]; then exit 91; fi
PYTHONDONTWRITEBYTECODE=1 /home/ubuntu/vllm023-venv/bin/python scripts/run_engine.py "$@" > "raw/$name.log" 2>&1
rc=$?
echo "$rc" > "raw/$name.exit"
nvidia-smi > "raw/$name.post-gpu.txt"
exit "$rc"
