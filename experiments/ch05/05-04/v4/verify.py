import hashlib,json
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parent;torch.set_num_threads(1)
d=json.loads((ROOT/'results/first/results.json').read_text());observations=[]
for f,h in d['source_hashes'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
for r in d['rows']:
 t=r['t'];z=torch.load(ROOT/f'results/first/t{t}-tensors.pt',weights_only=True)
 g=z['g'].double().clamp(max=10);u=z['u'].double().clamp(-10,10);w=z['w'].double()
 ideal=(g*torch.sigmoid(g)*u*w).bfloat16().float()
 # Negative controls intentionally violate the source's two material boundaries.
 wrongg=z['g'].double().clamp(-10,10)
 wrongclip=(wrongg*torch.sigmoid(wrongg)*u*w).bfloat16()
 early=(g*torch.sigmoid(g)*u).bfloat16().double().mul(w).bfloat16()
 assert not torch.equal(wrongclip,z['reference'])
 assert not torch.equal(early,z['reference'])
 for name,y in z['outputs'].items():
  torch.testing.assert_close(y.float(),ideal,atol=.125,rtol=.02)
  v=r['paths'][name];assert int((y!=z['reference']).sum())==v['different_elements']
  assert len(v['eager_us'])==len(v['graph_us'])==11
 observations.append(dict(t=t,symmetric_gate_clip_differences=int((wrongclip!=z['reference']).sum()),early_bf16_differences=int((early!=z['reference']).sum()),fp64_reference_max_abs_difference=float((ideal-z['reference'].float()).abs().max())))
print(json.dumps(observations,indent=2))
