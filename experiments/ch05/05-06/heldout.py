import argparse,hashlib,json
from pathlib import Path
import torch
import schedule
from evaluate_v2 import native
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise RuntimeError('Use fresh output file')
selection=json.loads((ROOT/'results/schedule-summary.json').read_text())['selected_schedule'];protocol=json.loads((ROOT/'protocol.json').read_text())
data=torch.load(ROOT/'results/capture/tensors/layer0-call0.pt',weights_only=True)['input'];cases={f'heldout-{t}':data[:t].contiguous() for t in protocol['heldout_shapes']}
values=torch.tensor([-80,-20,-10,-1,0,1,10,20,80],dtype=torch.bfloat16)
boundary=values.repeat(7*24576//9+1)[:7*24576].reshape(7,24576);cases['boundary-values']=boundary;cases['all-zero']=torch.zeros((1,24576),dtype=torch.bfloat16)
rows=[]
for label,cpu in cases.items():
 x=cpu.cuda();ref=native(x);y=schedule.run(x,selection['block'],selection['warps'])
 status='passed';error=None
 try:
  torch.testing.assert_close(y,ref,atol=protocol['atol'],rtol=protocol['rtol']);assert torch.equal(x.cpu(),cpu)
  assert y.untyped_storage().data_ptr()!=x.untyped_storage().data_ptr()
 except Exception as e:status='failed';error=repr(e)
 negative=None
 if torch.any(ref.abs()>1):
  try:torch.testing.assert_close(torch.zeros_like(ref),ref,atol=protocol['atol'],rtol=protocol['rtol']);negative=False
  except AssertionError:negative=True
  assert negative
 rows.append(dict(case=label,shape=list(x.shape),status=status,error=error,max_abs_error=float((y.float()-ref.float()).abs().max()),different_elements=int((y!=ref).sum()),zero_candidate_rejected=negative,input_sha256=hashlib.sha256(cpu.view(torch.uint8).numpy().tobytes()).hexdigest()))
a.output.write_text(json.dumps(dict(selection=selection,rows=rows,protocol_sha256=hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),selection_sha256=hashlib.sha256((ROOT/'results/schedule-summary.json').read_bytes()).hexdigest()),indent=2)+'\n')
print([(r['case'],r['status']) for r in rows])
