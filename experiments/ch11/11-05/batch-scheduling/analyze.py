import hashlib,json,statistics
from pathlib import Path
R=Path(__file__).resolve().parent;out=R/'results';execution=json.loads((out/'execution.json').read_text());assert hashlib.sha256((R/'run.py').read_bytes()).hexdigest()==execution['source_sha256']
raw=[json.loads(l) for l in (out/'raw.jsonl').read_text().splitlines()];assert len(raw)==9
assert {(r['trial'],r['policy']) for r in raw}=={(t,p) for t in range(3) for p in ['fixed_quota','fifo','batch_A_first']}
refs=json.loads((out/'references.json').read_text());rows=[];details=[]
for r in raw:
 jobs=sorted(r['tasks'],key=lambda j:j['dispatch_s']);assert {j['id'] for j in jobs}=={'A0','A1','A2','B0','B1','B2'}
 for i,j in enumerate(jobs):
  w=j['result'];arrival=r['start_s']+j['arrival_s']
  assert arrival<=j['dispatch_s']<=w['compile_start_s']<=w['compile_end_s']<=w['work_start_s']<=w['work_end_s']<=j['feedback_s']<=j['release_s']
  assert j['exit_code']==0 and w['digest']==refs[str(j['iterations'])]['digest'] and w['cpu_s']>0
  busy=[x for x in jobs[:i] if x['release_s']>j['dispatch_s']];assert len(busy)<2
  eligible=[x for x in jobs[i:] if r['start_s']+x['arrival_s']<=j['dispatch_s']]
  if r['policy']=='fixed_quota':
   assert all(x['batch']!=j['batch'] for x in busy)
   eligible=[x for x in eligible if x['batch'] not in {b['batch'] for b in busy}]
  best=min(eligible,key=lambda x:(x['batch']!='A',x['sequence']) if r['policy']=='batch_A_first' else (x['arrival_s'],x['sequence']))
  assert best['id']==j['id']
  details.append(dict(trial=r['trial'],policy=r['policy'],id=j['id'],queue_s=j['dispatch_s']-arrival,process_startup_s=w['compile_start_s']-j['dispatch_s'],compile_s=w['compile_end_s']-w['compile_start_s'],work_s=w['work_end_s']-w['work_start_s'],feedback_after_work_s=j['feedback_s']-w['work_end_s'],release_after_feedback_s=j['release_s']-j['feedback_s']))
 rows.append(dict(trial=r['trial'],policy=r['policy'],dispatch_order=[j['id'] for j in jobs],batch_feedback_s={b:max(j['feedback_s'] for j in jobs if j['batch']==b)-r['start_s'] for b in ['A','B']},all_release_s=max(j['release_s'] for j in jobs)-r['start_s'],cpu_s=sum(j['result']['cpu_s'] for j in jobs)))
report=dict(status='verified',runs=rows,task_timings=details,medians={p:dict(A_feedback_s=statistics.median(x['batch_feedback_s']['A'] for x in rows if x['policy']==p),B_feedback_s=statistics.median(x['batch_feedback_s']['B'] for x in rows if x['policy']==p),all_release_s=statistics.median(x['all_release_s'] for x in rows if x['policy']==p),cpu_s=statistics.median(x['cpu_s'] for x in rows if x['policy']==p)) for p in ['fixed_quota','fifo','batch_A_first']})
assert len(execution['children'])==54 and all(p['exit_code']==0 for p in execution['children'])
(R/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['medians'],indent=2))
