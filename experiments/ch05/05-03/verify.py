#!/usr/bin/env python3
"""Offline integrity and raw counter/coverage checks, not a new GPU run."""
import csv
import hashlib
import json
import math
from pathlib import Path
root=Path(__file__).resolve().parent
out=root/"results"
for name,digest in json.loads((out/"provenance.json").read_text())["sha256"].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
data=json.loads((out/"results.json").read_text())
assert len(data["rows"])==10
assert {(r["n"],r["backend"]) for r in data["rows"]}=={(n,b) for n in [128,257,512,2048,8192] for b in ["math","flash"]}
for r in data["rows"]:
    assert r["correctness"]=="passed"
    assert r["peak_increment_bytes"]>=r["output_bytes"]
    for key in ["eager_samples_us","graph_samples_us"]:
        assert len(r[key])==data["method"]["trials"]
        assert all(math.isfinite(v) and v>0 for v in r[key])
assert len(data["edge_checks"])==18
assert {(r["n"],r["qk_scale"],r["backend"]) for r in data["edge_checks"]}=={(n,s,b) for n in [1,17,129] for s in [0.,1.,6.] for b in ["math","flash"]}
assert all(r["passed"] and r["first_position_exact"] for r in data["edge_checks"])
traffic=json.loads((out/"traffic.json").read_text())
assert len(traffic["rows"])==6
for r in traffic["rows"]:
    raw=[v for v in csv.DictReader((out/r["source_csv"]).open()) if v["ID"].isdigit()]
    assert len(raw)==r["kernel_count"]
    for metric,total in r["totals"].items():
        assert math.isfinite(total) and total>=0
        assert sum(float(v[metric].replace(",","")) for v in raw)==total
    assert (out/r["source_report"]).stat().st_size>0
    names=" ".join(v["Kernel Name"] for v in raw)
    if r["backend"]=="flash":assert "flash_fwd" in names
    else:assert "flash_fwd" not in names
print("Verified hashes, 10 timing/allocation cases, 18 edge checks, and 6 complete raw Nsight counter reports.")
