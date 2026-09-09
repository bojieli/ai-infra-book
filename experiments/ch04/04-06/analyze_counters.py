import csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results/projection-counters'
def analyze():
 c=json.loads((OUT/'collection.json').read_text())
 for name,digest in c['source_hashes'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
 formal=json.loads((ROOT/'results/projection-cuda/results.json').read_text());rows=[]
 for r in c['records']:
  raw=list(csv.DictReader((OUT/f"{r['label']}.csv").open()))
  for metric in c['metrics']:assert raw[0][metric]==('ns' if metric=='gpu__time_duration.sum' else 'byte')
  kernels=[]
  for line in raw:
   if not line['ID'].isdigit():continue
   kernels.append(dict(name=line['Kernel Name'],metrics={k:float(line[k].replace(',','')) for k in c['metrics']}))
  assert kernels
  observations=[json.loads(line) for line in (OUT/f"{r['label']}.log").read_text().splitlines() if line.startswith('{"m":')]
  assert observations
  for obs in observations:
   assert obs['m']==r['m'] and obs['mode']==r['mode']
   assert obs['weight_sha256']==formal['environment']['weight_sha256']
   f=next(x for x in formal['rows'] if x['m']==r['m']);assert obs['input_sha256']==f['input_sha256']
   assert obs['max_abs_error']==f['max_abs_error']
  totals={k:sum(x['metrics'][k] for x in kernels) for k in c['metrics']}
  rows.append(dict(m=r['m'],mode=r['mode'],kernels=kernels,totals=totals))
 assert len(rows)==4
 return dict(rows=rows,scope='Actual kernel-scoped DRAM and L2 request counters; not logical bytes. Instrumented replay is separate from formal batch timing. No MPS counter claim.')
if __name__=='__main__':
 d=analyze();(ROOT/'results/projection-traffic.json').write_text(json.dumps(d,indent=2)+'\n')
 for r in d['rows']:print(r['m'],r['mode'],len(r['kernels']),r['totals'])
