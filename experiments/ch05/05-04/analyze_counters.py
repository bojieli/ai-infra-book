import csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results/counters'
def analyze():
 c=json.loads((OUT/'collection.json').read_text());formal=json.loads((ROOT/'results/compare/results.json').read_text())
 for name,h in c['source_hashes'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h
 rows=[]
 for r in c['records']:
  data=list(csv.DictReader((OUT/f"{r['label']}.csv").open()));units=data[0]
  for k in ['dram__bytes_op_read.sum','dram__bytes_op_write.sum','lts__t_bytes.sum']:assert units[k]=='byte'
  assert units['gpu__time_duration.sum']=='ns'
  kernels=[]
  for v in data:
   if not v['ID'].isdigit():continue
   kernels.append(dict(name=v['Kernel Name'],metrics={k:float(v[k].replace(',','')) for k in c['metrics']}))
  assert kernels
  logs=[json.loads(s) for s in (OUT/f"{r['label']}.log").read_text().splitlines() if s.startswith('{"t":')]
  assert logs
  f=next(x for x in formal['rows'] if x['t']==r['m'])['paths'][r['mode']]
  for log in logs:
   assert log['different_fp8_elements']==f['fp8_different_elements'] and log['scale_difference']==f['max_scale_difference']==0
  rows.append(dict(t=r['m'],path=r['mode'],kernels=kernels,register_unit=units['launch__registers_per_thread'],
   totals={k:sum(x['metrics'][k] for x in kernels) for k in c['metrics'] if k!='launch__registers_per_thread'},
   registers_per_thread=[x['metrics']['launch__registers_per_thread'] for x in kernels],input_sha256=logs[0]['input_sha256']))
 for t in [1,1024]:assert len({r['input_sha256'] for r in rows if r['t']==t})==1
 return rows
if __name__=='__main__':
 rows=analyze();(ROOT/'results/traffic.json').write_text(json.dumps(rows,indent=2)+'\n')
 for r in rows:print(r['t'],r['path'],len(r['kernels']),r['totals'],r['registers_per_thread'])
