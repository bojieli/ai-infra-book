"""Verify sealed raw files and regenerate temporal assertions."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root=Path(__file__).parent
manifest=json.loads((root/'results/raw-manifest.json').read_text())
for name,record in manifest.items():
    path=root/'results'/name
    assert path.stat().st_size==record['bytes'],name
    assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256'],name
subprocess.run([sys.executable,str(root/'analyze.py')],check=True,stdout=subprocess.DEVNULL)
print('Verified sealed checkpoint/event files, staging and commit ordering, normal snapshot isolation, and SIGKILL recovery boundary.')
