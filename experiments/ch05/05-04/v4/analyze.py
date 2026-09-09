import json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
rows=[]
for r in json.loads((ROOT/'results/first/results.json').read_text())['rows']:
 for name,v in r['paths'].items():
  tr=json.loads((ROOT/f"results/first/t{r['t']}-{name}-trace.json").read_text())
  kernels=[e['name'] for e in tr['traceEvents'] if e.get('cat')=='kernel'];assert kernels
  rows.append(dict(t=r['t'],path=name,eager_us=statistics.median(v['eager_us']),graph_us=statistics.median(v['graph_us']),kernel_count=len(kernels),different_elements=v['different_elements'],kernels=kernels))
(ROOT/'results/summary.json').write_text(json.dumps(rows,indent=2)+'\n')
for r in rows:print({k:v for k,v in r.items() if k!='kernels'})
