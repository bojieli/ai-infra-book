#!/usr/bin/env python3
"""Offline artifact integrity plus raw Nsight evidence and numerical-record coverage."""
import hashlib
import json
import math
import sqlite3
from pathlib import Path
root=Path(__file__).resolve().parent
out=root/"results"
for path,digest in json.loads((out/"provenance.json").read_text())["sha256"].items():
    assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
r=json.loads((out/"results.json").read_text())
base=["eager","fused","graph","fused_graph","fused_graph_copy"]
expected={(m,label) for m in [1,32,257] for label in base}
expected.update({(257,label) for label in ["graph_pad512","fused_graph_pad512"]})
expected.update({(32,f"{method}_micro{n}") for method in ["eager","fused_graph"] for n in [4,8]})
assert len(r["rows"])==21
assert {(x["tokens"],x["label"]) for x in r["rows"]}==expected
for row in r["rows"]:
    assert row["correctness"]=="passed"
    assert len(row["input_update_checks"])==3
    for key in ["samples_us","host_submit_samples_us"]:
        assert len(row[key])==r["method"]["trials"]
        assert all(math.isfinite(x) and x>0 for x in row[key])
    assert row["executed_tokens"]>=row["tokens"]
trace=json.loads((out/"trace-analysis.json").read_text())
spans={s["label"]:s for s in trace["ranges"]}
assert len(spans)==9
for label in ["graph","fused_graph"]:
    assert spans[label]["graph_launch_count"]==3
assert spans["graph"]["kernel_count"]==spans["eager"]["kernel_count"]
assert spans["fused_graph"]["kernel_count"]==spans["fused"]["kernel_count"]<spans["eager"]["kernel_count"]
assert spans["fused_graph_micro8"]["graph_launch_count"]==24
assert sum(x["bytes"] for x in spans["fused_graph_copy"]["copies"])==3*32*4096*2
c=sqlite3.connect(f"file:{out/'timeline.sqlite'}?mode=ro",uri=True)
for row in trace["ranges"]:
    count=c.execute("select count(*) from CUPTI_ACTIVITY_KIND_KERNEL where start>=? and end<=?",(row["start_ns"],row["end_ns"])).fetchone()[0]
    assert count==row["kernel_count"]
    assert row["uncovered_device_interval_us"]>=0
paper=json.loads((root/"sources/paper-case.json").read_text())
source=(root/"sources/mpk-v2.txt").read_text()
assert paper["evidence_kind"]=="author_report_not_this_experiment"
assert "14.5" in source and "12.5" in source and "Qwen3-8B running on an A100 GPU" in source
print("Verified artifacts, 21 timing cases, 63 recorded input-update checks, 9 raw trace ranges and separately labeled MPK evidence.")
