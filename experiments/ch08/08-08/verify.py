import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).parent
manifest=json.loads((root/'results/raw-manifest.json').read_text())
for name,digest in manifest.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
subprocess.run([sys.executable,str(root/'analyze.py')],check=True)
print(f'PASS: {len(manifest)} sealed files; identical inputs and controlled formats; actual KV snapshots and independent exact-answer checks')
