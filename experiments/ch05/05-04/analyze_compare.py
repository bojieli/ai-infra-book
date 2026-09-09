import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=ROOT/'results/compare';d=json.loads((p/'results.json').read_text())
assert d['environment']['source_sha256']==hashlib.sha256((ROOT/'compare.py').read_bytes()).hexdigest()
rows=[]
for r in d['rows']:
 for name,v in r['paths'].items():
  trace=json.loads((p/f"t{r['t']}-{name}-trace.json").read_text())
  kernels=[x['name'] for x in trace['traceEvents'] if x.get('cat')=='kernel']
  assert kernels and len(v['samples_us'])==len(v['graph_samples_us'])==11
  assert v['fp8_different_elements']==v['graph_fp8_different_elements']
  assert v['max_scale_difference']==v['graph_max_scale_difference']==0
  rows.append(dict(t=r['t'],path=name,eager_us=statistics.median(v['samples_us']),graph_us=statistics.median(v['graph_samples_us']),eager_kernel_count=len(kernels),different_fp8_elements=v['fp8_different_elements']))
(ROOT/'results/compare-summary.json').write_text(json.dumps(rows,indent=2)+'\n')
for r in rows:print(r)
