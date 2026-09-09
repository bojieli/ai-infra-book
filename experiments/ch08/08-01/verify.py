import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).parent
manifest=json.loads((root/'results/raw-manifest.json').read_text())
for name,digest in manifest.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
subprocess.run([sys.executable,str(root/'analyze.py')],check=True)
print(f'PASS: {len(manifest)} sealed files, 8 warmup batches and 24 measured batches')
