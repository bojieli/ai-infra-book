import argparse,hashlib,json,statistics
from pathlib import Path
R=Path(__file__).resolve().parent

def main(out):
 e=json.loads((out/'environment.json').read_text());assert e['source_sha256']==hashlib.sha256((R/'run.py').read_bytes()).hexdigest()
 c=json.loads((out/'completion.json').read_text());assert c['done']
 rows=json.loads((out/'raw.json').read_text());assert [r['m'] for r in rows]==([1,8] if e['smoke'] else [1,8,64,512]);assert c['shapes']==len(rows)
 result=[]
 for r in rows:
  assert r['integer_exact'] and r['padded_m']==max(32,r['m']);assert r['k']==2048 and r['n']==768
  assert all(x['passed'] and x['relative_l2_to_original_fp32']<=.02 for x in r['checks'].values())
  assert json.loads((out/f"integer-check-m{r['m']}.json").read_text())['exact']
  stages=sorted(set(x['stage'] for x in r['samples']));assert len(stages)==6
  metrics={}
  for stage in stages:
   samples=[x for x in r['samples'] if x['stage']==stage];assert sorted(x['trial'] for x in samples)==list(range(1 if e['smoke'] else 9));assert all(x['device_ms']>0 and x['wall_ms']>0 for x in samples)
   metrics[stage]={k:dict(median=statistics.median(x[k] for x in samples),min=min(x[k] for x in samples),max=max(x[k] for x in samples)) for k in ['device_ms','wall_ms']}
  trace=None
  if not e['smoke']:
   t=json.loads((out/f"trace-m{r['m']}.json").read_text());events=t['traceEvents'];names=[x.get('name') for x in events];assert 'int8_direct_e2e' in names and 'int8_dequant_bf16_e2e' in names
   kernels=[x for x in events if x.get('cat')=='kernel'];assert kernels
   trace=dict(kernel_events=len(kernels),kernel_names=sorted(set(x['name'] for x in kernels)),note='Separate instrumented run; no tensor-core or actual traffic inference from operator name.')
  result.append(dict(m=r['m'],checks=r['checks'],storage_bytes=r['storage_bytes'],stages=metrics,trace=trace))
 (out/'summary.json').write_text(json.dumps(dict(smoke=e['smoke'],rows=result,scope='Random expert-shaped matrix, GPU-resident inputs; no model quality or cold-memory claim'),indent=2)+'\n');print('Verified',len(rows),'shapes')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
