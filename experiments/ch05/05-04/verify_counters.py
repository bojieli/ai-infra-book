import hashlib,json
from pathlib import Path
import torch
from analyze_counters import ROOT,analyze
manifest=json.loads((ROOT/'results/counter-manifest.json').read_text())
for f,h in manifest.items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h,f
rows=analyze();assert rows==json.loads((ROOT/'results/traffic.json').read_text())
for t in [1,1024]:
 d=torch.load(ROOT/f'results/compare/t{t}-tensors.pt',weights_only=True)
 h=hashlib.sha256(d['g'].view(torch.uint8).numpy().tobytes()+d['u'].view(torch.uint8).numpy().tobytes()).hexdigest()
 for r in rows:
  if r['t']==t:assert r['input_sha256']==h
print('PASS: sealed sources/reports, six captures, counter units, saved-input identity and numerical observations')
