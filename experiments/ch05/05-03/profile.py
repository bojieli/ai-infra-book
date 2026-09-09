#!/usr/bin/env python3
"""Collect actual SM120 DRAM/L2 counters; never substitute logical tensor sizes."""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
root=Path(__file__).resolve().parent
out=root/"results/counters"
out.mkdir(parents=True,exist_ok=True)
p=argparse.ArgumentParser()
p.add_argument("--sudo",action="store_true",help="Use existing passwordless sudo for restricted GPU counters")
p.add_argument("--resume",action="store_true",help="Reuse reports from this same unchanged run.py after an export interruption")
args=p.parse_args()
ncu=os.environ.get("NCU") or shutil.which("ncu")
if not ncu:raise SystemExit("Set NCU to Nsight Compute 2026.2.1 executable")
metrics=["dram__bytes_op_read.sum","dram__bytes_op_write.sum","lts__t_bytes.sum","gpu__time_duration.sum"]
records=[]
for n in [512,2048,8192]:
    for backend in ["math","flash"]:
        label=f"n{n}-{backend}"
        prefix=["sudo","-n","env","PYTHONPATH="+os.pathsep.join(x for x in sys.path if x)] if args.sudo else []
        command=prefix+[ncu,"--target-processes","application-only","--profile-from-start","off",
            "--replay-mode","application","--cache-control","none","--clock-control","none",
            "--metrics",",".join(metrics),"--force-overwrite","--export",str(out/label),
            sys.executable,str(root/"run.py"),"--profile-only","--length",str(n),"--backend",backend]
        reused=args.resume and (out/f"{label}.ncu-rep").is_file()
        if not reused:
            with (out/f"{label}.log").open("w") as f:
                subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
        with (out/f"{label}.csv").open("w") as f:
            subprocess.run([ncu,"--import",str(out/f"{label}.ncu-rep"),"--page","raw","--csv","--print-units","base"],stdout=f,check=True)
        records.append({"n":n,"backend":backend,"command":command,"report":f"{label}.ncu-rep","csv":f"{label}.csv","reused_report":reused})
        print("Captured",label,flush=True)
(out/"collection.json").write_text(json.dumps({"version":subprocess.check_output([ncu,"--version"],text=True),
    "metrics":metrics,"cache_control":"none","clock_control":"none","replay":"application",
    "scope":"One eager operator after five warmups; counters from instrumented application replay; no claim of exclusive GPU or cold-cache traffic",
    "records":records},indent=2)+"\n")
