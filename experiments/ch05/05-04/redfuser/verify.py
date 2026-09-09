import gzip,hashlib,json
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parent;torch.set_num_threads(1)
summary=[]
for folder in ['cuda128','attention']:
 d=json.loads((ROOT/f'results/{folder}/results.json').read_text())
 for f,h in d['source_hashes'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
 for r in d['rows']:
  with gzip.open(ROOT/f"results/{folder}/{r['case']}.pt.gz",'rb') as f:z=torch.load(f,weights_only=True)
  out=z['output'];assert hashlib.sha256(out.view(torch.uint8).numpy().tobytes()).hexdigest()==r['output_sha256']
  if folder=='cuda128':
   ref=z['global_scale_reference'];assert int(torch.isfinite(out).sum())==r['finite_elements']
   assert int((out!=ref[:,None]).sum())==r['different_from_global']
   if r['case']=='zero_input':assert torch.isnan(out).all() and (ref==0).all()
   else:assert (out==r['output_min']).all() and (ref==r['global_scale_reference_min']).all()
  else:
   expected=float((z['scores'].softmax(0)*z['values']).sum());assert expected==r['expected_fp64']
   assert (out==r['output_min']).all();assert abs(float(out.flatten()[0])-expected)<.001
  tr=json.loads((ROOT/f"results/{folder}/{r['case']}-trace.json").read_text());kernels=[x['name'] for x in tr['traceEvents'] if x.get('cat')=='kernel'];assert kernels
  summary.append(dict(group=folder,case=r['case'],kernel_count=len(kernels),kernels=kernels,output_elements=out.numel()))
print(json.dumps(summary,indent=2))
