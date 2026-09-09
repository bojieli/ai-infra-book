#!/bin/bash
set -u
cd "$(dirname "$0")"
PYTHON=${PYTHON:-../../tools/collective-cpu-venv/bin/python}
run="results/cpu-$(date -u +%Y%m%dT%H%M%SZ)-$$"
mkdir -p "$run"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
ps -axo pid,ppid,pcpu,rss,comm > "$run/coexistence.txt"
"$PYTHON" probe_cpu.py > "$run/stdout.json" 2> "$run/stderr.log"
code=$?
printf '%s\n' "$code" > "$run/exit_code.txt"
printf '%s\n' "$PYTHON probe_cpu.py" > "$run/command.txt"
cat "$run/stdout.json"
exit "$code"
