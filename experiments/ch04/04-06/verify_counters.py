import hashlib,json
from analyze_counters import ROOT,analyze
manifest=json.loads((ROOT/'results/counter-manifest.json').read_text())
for name,digest in manifest.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
assert analyze()==json.loads((ROOT/'results/projection-traffic.json').read_text())
print(f'PASS: {len(manifest)} sealed files; 4 reports, units, source/input hashes and numerical observations')
