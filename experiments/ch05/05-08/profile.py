#!/usr/bin/env python3
"""Collect and export Nsight Systems data independently of the unprofiled timing run."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
root=Path(__file__).resolve().parent
out=root/"results"
out.mkdir(exist_ok=True)
nsys=os.environ.get("NSYS") or shutil.which("nsys")
if not nsys:raise SystemExit("Set NSYS to a recent Nsight Systems CLI executable")
command=[nsys,"profile","--trace=cuda,nvtx","--sample=none","--cpuctxsw=none",
         "--cuda-graph-trace=node","--capture-range=cudaProfilerApi","--capture-range-end=stop",
         "--force-overwrite=true","--output="+str(out/"timeline"),sys.executable,str(root/"run.py"),"--trace-only"]
with (out/"profile.log").open("w") as f:
    subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
subprocess.run([nsys,"export","--type=sqlite","--force-overwrite=true","--output="+str(out/"timeline.sqlite"),str(out/"timeline.nsys-rep")],check=True)
(out/"profile.json").write_text(json.dumps({"command":command,"version":subprocess.check_output([nsys,"--version"],text=True)},indent=2)+"\n")
