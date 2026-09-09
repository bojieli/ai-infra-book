import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest()
d=json.loads((root/'results/raw.json').read_text());source=(root/'page.bin').read_bytes()
assert sha(source)==d['fixture_sha256'];assert sha((root/'run.py').read_bytes())==d['run_sha256'];assert sha((root/'results/hicache_storage.py.snapshot').read_bytes())==d['backend_sha256']
assert len(d['cases'])==7
for r in d['cases']:
 case=r['case'];files=list((root/'results'/case).glob('*.bin'))
 if case=='missing':assert not files
 else:assert len(files)==1 and sha(files[0].read_bytes())==r['after_sha256']
 expected=source
 if case in ['missing','model_identity_changed']:expected=bytes(len(source))
 elif case=='truncated':expected=source[:-2]+bytes(2)
 elif case in ['bitflip','set_existing_corrupt']:expected=bytes([source[0]^1])+source[1:]
 assert sha(expected)==r['target_sha256'],case
 assert r['target_equals_reference']==(expected==source)
 assert r['before_sha256']==r['after_sha256']
print('Verified 7 backend observations, target byte hashes, files and source')
