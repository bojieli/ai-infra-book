import hashlib,json
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parent
torch.set_num_threads(1)
checks=json.loads((ROOT/'results/rounding-check/check.json').read_text())
z=torch.load(ROOT/'results/rounding-check/tensors.pt',weights_only=True)
assert torch.equal(z['actual_bits'],z['expected_bits'])
assert torch.equal(z['input'].bfloat16().float().view(torch.int32),z['expected_bits'])
assert z['input'].numel()==checks['elements'] and torch.isfinite(z['input']).all()
assert hashlib.sha256(z['input'].numpy().tobytes()).hexdigest()==checks['input_sha256']
results=json.loads((ROOT/'results/round/results.json').read_text());summary=[]
for r in results['rows']:
 t=r['t'];new=torch.load(ROOT/f'results/round/t{t}-tensors.pt',weights_only=True);old=torch.load(ROOT/f'results/first/t{t}-tensors.pt',weights_only=True)
 for name in ['g','u','reference_q','reference_s']:
  a,b=new[name],old[name]
  assert torch.equal(a.view(torch.uint8),b.view(torch.uint8)),(t,name)
 ideal=(new['g'].double()*torch.sigmoid(new['g'].double())*new['u'].double()).bfloat16().float()
 ideal_s=(ideal.abs().amax(-1,keepdim=True)/448.).clamp_min(1e-8)
 ideal_q=(ideal/ideal_s).clamp(-448,448).to(torch.float8_e4m3fn)
 ideal_deq=ideal_q.float()*ideal_s
 for name,(q,s) in new['outputs'].items():
  diff=int((q.view(torch.uint8)!=old['reference_q'].view(torch.uint8)).sum())
  scale=float((s-old['reference_s']).abs().max());assert diff==r['paths'][name]['fp8_different_elements']
  assert scale==r['paths'][name]['max_scale_difference']
  deq=q.float()*s
  torch.testing.assert_close(deq,ideal_deq,atol=.04,rtol=.15)
  summary.append(dict(t=t,path=name,different_fp8_elements=diff,max_scale_difference=scale,
   fp64_expression_reference_max_abs_difference=float((deq-ideal_deq).abs().max()),
   fp64_expression_reference_rmse=float(((deq.double()-ideal_deq.double()).square().mean()).sqrt())))
print(json.dumps(dict(rounding_cases=checks['elements'],original_inputs_and_reference_identical=True,outputs=summary),indent=2))
