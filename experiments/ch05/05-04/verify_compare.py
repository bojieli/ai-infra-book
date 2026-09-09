import hashlib,json
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parent
torch.set_num_threads(1)
results=json.loads((ROOT/'results/compare/results.json').read_text())
for r in results['rows']:
 t=r['t'];a=torch.load(ROOT/f'results/compare/t{t}-tensors.pt',weights_only=True);b=torch.load(ROOT/f'results/first/t{t}-tensors.pt',weights_only=True)
 for k in ['g','u','reference_q','reference_s']:assert torch.equal(a[k].view(torch.uint8),b[k].view(torch.uint8))
 for name,(q,s) in a['outputs'].items():
  assert int((q.view(torch.uint8)!=a['reference_q'].view(torch.uint8)).sum())==r['paths'][name]['fp8_different_elements']
  assert torch.equal(s,a['reference_s'])
  torch.testing.assert_close(q.float()*s,a['reference_q'].float()*a['reference_s'],atol=.04,rtol=.15)
print('PASS: same original inputs and reference, saved outputs, FP8 differences and scales')
