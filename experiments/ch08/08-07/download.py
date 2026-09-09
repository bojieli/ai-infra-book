import hashlib,json
from pathlib import Path
from huggingface_hub import snapshot_download
P=Path(__file__).resolve().parent
meta=json.loads((P/'model-source.json').read_text())
path=Path(snapshot_download(repo_id=meta['id'],revision=meta['sha']))
files={}
for f in sorted(path.rglob('*')):
 if f.is_file():
  h=hashlib.sha256()
  with f.open('rb') as stream:
   for block in iter(lambda:stream.read(8*1024**2),b''):h.update(block)
  files[str(f.relative_to(path))]=dict(bytes=f.stat().st_size,sha256=h.hexdigest())
for f in meta['siblings']:
 if 'lfs' in f:assert files[f['rfilename']]['sha256']==f['lfs']['sha256']
(P/'model-local.json').write_text(json.dumps(dict(repo_id=meta['id'],revision=meta['sha'],snapshot=str(path),files=files),indent=2)+'\n')
print(path)
