#!/usr/bin/env python3
"""Compile and measure locally using only a C compiler and Python standard library."""
import hashlib
import json
import os
import platform
import shutil
import statistics
import subprocess
import time
from pathlib import Path

root = Path(__file__).resolve().parent
out = root / "results"
out.mkdir(exist_ok=True)
compiler = shutil.which(os.environ.get("CC", "clang"))
if not compiler:
    raise SystemExit("C compiler not found; set CC to clang or gcc")
version = subprocess.check_output([compiler, "--version"], text=True)
flags = ["-O3", "-std=c11", "-ffp-contract=off", "-Wall", "-Wextra"]
diagnostics = ["-Rpass=loop-vectorize", "-Rpass-missed=loop-vectorize"] if "clang" in version.lower() else []
command = [compiler, *flags, *diagnostics, str(root / "matmul.c"), "-o", str(out / "matmul"), "-lm"]
build = subprocess.run(command, text=True, capture_output=True)
(out / "compiler.log").write_text(build.stdout + build.stderr)
build.check_returncode()
start = time.time()
raw = subprocess.check_output([str(out / "matmul")], text=True)
(out / "raw.json").write_text(raw)
data = json.loads(raw)
data["environment"] = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start)),
                       "platform": platform.platform(), "machine": platform.machine(),
                       "compiler": version, "command": command, "thread_count": 1,
                       "affinity": "not pinned; OS may migrate the thread", "host_shared": True}
if platform.system() == "Darwin":
    data["environment"]["cpu"] = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
data["method"] = {"dtype": "float32", "reference": "independent float64 ijk accumulation",
                  "tolerance": "atol=1e-4, rtol=1e-5", "buffers": "hot reused row-major arrays; no cache flush",
                  "timing": "monotonic wall clock; output zeroing included; randomized candidate order in each trial",
                  "calibration": "at least 1, at most 10000 calls, target 15ms per candidate trial",
                  "scope": "execution measurements only; analytical access counts maintained by calculations/C25"}
for row in data["rows"]:
    row["median_us"] = statistics.median(row["samples_us"])
    row["min_us"], row["max_us"] = min(row["samples_us"]), max(row["samples_us"])
(out / "results.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
subprocess.run([compiler, *flags, "-S", str(root / "matmul.c"), "-o", str(out / "matmul.s")], check=True)
files = [root / "run.py", root / "matmul.c", out / "raw.json", out / "results.json", out / "compiler.log", out / "matmul.s"]
(out / "provenance.json").write_text(json.dumps({"sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}, indent=2)+"\n")
for row in data["rows"]:
    print(row["m"], row["k"], row["n"], row["method"], row["tile"], round(row["median_us"],3))
