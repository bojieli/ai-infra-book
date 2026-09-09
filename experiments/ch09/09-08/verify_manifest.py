import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
d=json.loads((root/'manifest.json').read_text())
for name,item in d['files'].items():
 b=(root/name).read_bytes();assert len(b)==item['bytes'],name;assert hashlib.sha256(b).hexdigest()==item['sha256'],name
print(f"Verified {len(d['files'])} files")
