#!/usr/bin/env python3
"""Offline source/artifact integrity and actual generated-code checks."""
import hashlib
import itertools
import json
import math
from pathlib import Path
root = Path(__file__).resolve().parent
out = root / "results"
manifest = json.loads((out / "provenance.json").read_text())
for path, digest in manifest["sha256"].items():
    assert hashlib.sha256((root / path).read_bytes()).hexdigest() == digest, path
data = json.loads((out / "results.json").read_text())
expected = {(m,n,layout,tile) for (m,n),layout,tile in itertools.product(
    [(1024,4096),(1003,4093)], ["contiguous","transposed","strided_columns"], [16,32,64])}
assert len(data["rows"]) == 18
assert {(r["m"],r["n"],r["layout"],r["tile"]) for r in data["rows"]} == expected
for row in data["rows"]:
    assert row["correctness"] == "bitwise_equal_to_torch_transpose"
    assert len(row["samples_us"]) == data["method"]["trials"]
    assert all(math.isfinite(x) and x>0 for x in row["samples_us"])
    for stage in ["ttir","ttgir","llir","ptx","cubin"]:
        assert (out / row["code_files"][stage]).stat().st_size > 0
assert len(data["edge_checks"]) == 27 and all(x["passed"] for x in data["edge_checks"])
prefix = out / "code/m1024-n4096-contiguous-t32-w4"
assert "ttg.convert_layout" in prefix.with_suffix(".ttgir").read_text()
assert "ldmatrix.sync" in prefix.with_suffix(".ptx").read_text()
assert "LDSM" in prefix.with_suffix(".sass").read_text()
other = out / "code/m1024-n4096-transposed-t32-w4.ttgir"
assert "ttg.convert_layout" not in other.read_text()
print("Verified hashes, 18 timing cases, 27 edge checks, and IR/PTX/SASS evidence.")
