import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
rows=[]
for arm in ['first','strict']:
 folder=ROOT/'results'/arm;d=json.loads((folder/'results.json').read_text())
 assert d['environment']['source_sha256']==hashlib.sha256((ROOT/'run.py').read_bytes()).hexdigest()
 for r in d['rows']:
  for name,p in r['paths'].items():
   trace=json.loads((folder/f"t{r['t']}-{name}-trace.json").read_text())
   kernels=[e['name'] for e in trace['traceEvents'] if e.get('cat')=='kernel']
   assert kernels and len(p['samples_us'])==11
   rows.append(dict(arm=arm,t=r['t'],path=name,median_us=statistics.median(p['samples_us']),kernel_count=len(kernels),kernels=kernels,fp8_different_elements=p['fp8_different_elements'],max_scale_difference=p['max_scale_difference'],first_call_seconds=p['first_call_seconds']))
(ROOT/'results/summary.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Validated 12 recorded configurations and actual CUDA traces; numerical equivalence is not asserted')
