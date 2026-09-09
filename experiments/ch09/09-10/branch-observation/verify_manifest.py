import hashlib,json
from pathlib import Path
r=Path(__file__).resolve().parent;m=json.loads((r/'manifest.json').read_text())
for f,v in m['files'].items():
 p=r/f;assert p.stat().st_size==v['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256'],f
assert m['total_bytes']<1024**3
print('Verified',len(m['files']),'files,',m['total_bytes'],'bytes; duplicate remote fixture directories excluded')
