#!/usr/bin/env python3
"""Seal this standalone experiment after running, exporting, analyzing and plotting."""
import hashlib
import json
from pathlib import Path
root=Path(__file__).resolve().parent
paths=[*root.glob("*.py"),*root.glob("*.sh"),*root.glob("requirements.txt"),
       *[p for p in (root/"sources").rglob("*") if p.is_file()],
       *[p for p in (root/"results").rglob("*") if p.is_file() and p.name!="provenance.json"]]
(root/"results/provenance.json").write_text(json.dumps({"sha256":{
    str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}},indent=2)+"\n")
