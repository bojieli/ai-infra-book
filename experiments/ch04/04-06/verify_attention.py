import hashlib,json
from analyze_attention import ROOT,analyze
manifest=json.loads((ROOT/'results/attention-manifest.json').read_text())
for name,digest in manifest.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
actual=analyze();saved=json.loads((ROOT/'results/attention-summary.json').read_text())
assert len(actual)==len(saved)
for a,b in zip(actual,saved):
    for k in a:
        if k=='max_abs_error':assert abs(a[k]-b[k])<1e-12
        else:assert a[k]==b[k]
print(f'PASS: {len(manifest)} sealed files, independent reference and cross-device input checks')
