import hashlib,json
from analyze import ROOT,analyze
manifest=json.loads((ROOT/'results/raw-manifest.json').read_text())
for name,digest in manifest.items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
assert analyze()==json.loads((ROOT/'results/summary.json').read_text())
build=json.loads((ROOT/'results/mac/build.json').read_text())
assert build['source_sha256']==hashlib.sha256((ROOT/'mac.swift').read_bytes()).hexdigest()
print(f'PASS: {len(manifest)} sealed files; both platforms, all configurations and summary')
