import hashlib,json
from analyze_projection import ROOT,analyze
manifest=json.loads((ROOT/'results/projection-manifest.json').read_text())
for name,digest in manifest.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
assert analyze()==json.loads((ROOT/'results/projection-summary.json').read_text())
print(f'PASS: {len(manifest)} sealed files, same inputs, FP64 reference, 8 configurations and 88 batches')
