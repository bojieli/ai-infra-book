#!/usr/bin/env python3
"""Disassemble the actual cubins using nvdisasm bundled with the measured Triton."""
import hashlib
import json
import subprocess
from pathlib import Path
import triton

root = Path(__file__).resolve().parent
out = root / "results"
tool = Path(triton.__file__).resolve().parent / "backends/nvidia/bin/nvdisasm"
record = {"tool": str(tool), "version": subprocess.check_output([str(tool), "--version"], text=True), "files": []}
for p in sorted((out / "code").glob("*.cubin")):
    text = subprocess.check_output([str(tool), "-c", str(p)], text=True)
    target = p.with_suffix(".sass")
    target.write_text(text)
    record["files"].append(str(target.relative_to(root)))
(out / "disassembly.json").write_text(json.dumps(record, indent=2) + "\n")
manifest = json.loads((out / "provenance.json").read_text())
for p in [Path(__file__), out / "disassembly.json", *(out / "code").glob("*.sass")]:
    manifest["sha256"][str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
(out / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")
print("Disassembled", len(record["files"]), "cubins")
