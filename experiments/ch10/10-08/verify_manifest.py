#!/usr/bin/env python3
"""Read-only artifact integrity check; optionally verify remote model and patch."""
import argparse,hashlib,json,pathlib
ap=argparse.ArgumentParser();ap.add_argument('--private',type=pathlib.Path);a=ap.parse_args()
r=pathlib.Path(__file__).resolve().parent;m=json.loads((r/'manifest.json').read_text())
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
 return h.hexdigest()
for x in m['files']:
 p=r/x['path']
 if 'symlink_target' in x:assert p.is_symlink() and str(p.readlink())==x['symlink_target'],str(p)
 else:assert p.stat().st_size==x['bytes'] and digest(p)==x['sha256'],str(p)
expected={x['path'] for x in m['files']}|{'manifest.json'}
actual={str(p.relative_to(r)) for p in r.rglob('*') if p.is_file() or p.is_symlink()}
assert actual==expected,dict(extra=list(actual-expected),missing=list(expected-actual))
if a.private:
 for x in m['model']['files']:
  p=a.private/'model'/x['path'];assert p.stat().st_size==x['bytes'] and digest(p)==x['sha256'],str(p)
 src=a.private/'verl-project-verl-d040717'
 for x in json.loads((r/'patch/sources.json').read_text()):assert digest(src/x['path'])==x['patched_sha256'],x['path']
 assert digest(src/'uv.lock')==m['source']['lock_sha256']
 assert digest(a.private/'verl-source.tar.gz')==m['source']['archive_sha256']
print(json.dumps(dict(status='verified',files=len(m['files']),manifest_sha256=digest(r/'manifest.json'),remote_model_and_patch_verified=bool(a.private))))
