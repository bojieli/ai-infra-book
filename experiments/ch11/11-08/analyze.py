import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent;out=R/'results';env=json.loads((out/'environment.json').read_text())
for f,h in env['source_hashes'].items():assert hashlib.sha256((R/f).read_bytes()).hexdigest()==h
raw=[json.loads(l) for l in (out/'raw.jsonl').read_text().splitlines()];assert len(raw)==6
assert {(r['trial'],r['thinking'],r['budget']) for r in raw}=={(t,k,b) for t in range(2) for k,b in [(True,100),(True,1000),(False,1000)]}
inputs={};rows=[]
for r in raw:
 key=r['thinking']
 if key in inputs:assert inputs[key]==r['input_ids']
 else:inputs[key]=r['input_ids']
 assert len(r['output_ids'])<=r['budget'] and r['cached_tokens'] in [0,None]
 assert r['start_s']<=r['model_end_s']<=r['validation_start_s']<=r['done_s']
 events=r['events'];assert events and all(b['time_s']>=a['time_s'] and b['token_count']>=a['token_count'] for a,b in zip(events,events[1:]));assert events[-1]['token_count']==len(r['output_ids'])
 first=next(e['time_s'] for e in events if e['token_count']>0)
 result=r['result'];passed=False
 if 'validation' in result:
  v=result['validation'];checks=json.loads(v['stdout']);passed=v['returncode']==0 and checks['passed']
  assert checks['passed']==all(c['passed'] for c in checks['cases'])
  assert hashlib.sha256((out/f"case{r['case_index']}"/'intervals.py').read_bytes()).hexdigest()==result['write']['sha256']
 assert passed==result['passed']
 rows.append(dict(case_index=r['case_index'],trial=r['trial'],thinking=r['thinking'],total_output_budget=r['budget'],input_tokens=len(r['input_ids']),output_tokens=len(r['output_ids']),finish_reason=r['finish_reason'],ttft_s=first-r['start_s'],answer_text_first_s=r['answer_first_s']-r['start_s'] if r['answer_first_s'] else None,model_s=r['model_end_s']-r['start_s'],attempt_s=r['done_s']-r['start_s'],verified_usable_s=r['done_s']-r['start_s'] if passed else None,passed=passed,fee=None,error=result.get('error')))
report=dict(status='observations_verified',rows=rows,limits='One known controlled task, two repetitions; total output budget not independent reasoning-token quota. No provider fee or general model quality claim.')
(R/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
