import hashlib,json
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parent
d=json.loads((ROOT/'results/capture/capture.json').read_text());assert d['installed']==[{'layers':36}]
for name,h in d['source_hashes'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h
records=d['records'][0];assert len(records)==72
assert sorted(r['layer'] for r in records)==sorted(list(range(36))*2)
for layer in range(36):
 rows=[r for r in records if r['layer']==layer];assert [r['input_shape'] for r in rows]==[[7239,24576],[1,24576]]
 assert [r['output_shape'] for r in rows]==[[7239,12288],[1,12288]]
for r in records:
 if r['layer']!=0:continue
 p=ROOT/'results/capture/tensors'/Path(r['file']).name;assert hashlib.sha256(p.read_bytes()).hexdigest()==r['file_sha256']
 tensors=torch.load(p,weights_only=True);x,y=tensors['input'],tensors['reference']
 assert list(x.shape)==r['input_shape'] and list(y.shape)==r['output_shape']
 assert hashlib.sha256(x.view(torch.uint8).numpy().tobytes()).hexdigest()==r['input_sha256']
 assert torch.isfinite(x).all() and torch.isfinite(y).all()
print('PASS: 72 actual layer invocations; two complete native input/output tensors, source and data hashes')
