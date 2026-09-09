#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
root=Path(__file__).resolve().parent
files=[*root.glob("*.py"),*root.glob("*.sh"),*root.glob("requirements.txt"),
       *[p for p in (root/"results").rglob("*") if p.is_file() and p.name!="provenance.json"]]
(root/"results/provenance.json").write_text(json.dumps({"sha256":{
    str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}},indent=2)+"\n")
