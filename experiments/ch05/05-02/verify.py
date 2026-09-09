#!/usr/bin/env python3
"""Check recorded artifact integrity and coverage, not rerun GPU correctness."""
import hashlib
import json
import math
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = json.loads((root / "results/provenance.json").read_text())
for path, digest in manifest["sha256"].items():
    assert hashlib.sha256((root / path).read_bytes()).hexdigest() == digest, path
data = json.loads((root / "results/results.json").read_text())
expected = {(m, mode, block) for m in [1, 32, 1024]
            for mode in ["separate", "fused"] for block in [256, 1024, 4096]}
assert len(data["rows"]) == 18
assert {(r["tokens"], r["mode"], r["block"]) for r in data["rows"]} == expected
for row in data["rows"]:
    for name in ["samples_us", "graph_samples_us"]:
        assert len(row[name]) == data["method"]["trials"]
        assert all(math.isfinite(v) and v > 0 for v in row[name])
assert len(data["boundary_validation"]) == 9
assert all(r["fused_vs_separate"] == "bitwise_equal" for r in data["boundary_validation"])
print("Verified hashes, 18 timing cases and 9 recorded boundary checks.")
