"""Read-only hashes of existing model and installed source; no model loading."""
import hashlib,importlib.metadata,json
from pathlib import Path
B=Path(__file__).resolve().parent
meta=json.loads((B/'model-identity.json').read_text());root=Path(meta['snapshot']);files=0
for n,v in meta['files'].items():
 p=root/n;h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 assert p.stat().st_size==v['bytes'] and h.hexdigest()==v['sha256'],n;files+=1
source=Path(importlib.metadata.distribution('mlx-lm').locate_file('mlx_lm'))
for n,h in json.loads((B/'installed-source-sha.json').read_text()).items():assert hashlib.sha256((source/n).read_bytes()).hexdigest()==h,n
print(json.dumps(dict(model_files_sha256_passed=files,installed_sources_passed=3,model_loaded=False)))
