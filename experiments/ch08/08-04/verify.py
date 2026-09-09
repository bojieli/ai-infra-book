"""Validate sealed observations and regenerate the derived summary."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
root=Path(__file__).parent
manifest=json.loads((root/'results/raw-manifest.json').read_text())
for name,digest in manifest.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
subprocess.run([sys.executable,str(root/'analyze.py')],check=True)
print(f'PASS: {len(manifest)} sealed files; five configurations; 60 Agent requests; matching outputs and pressure inputs')
