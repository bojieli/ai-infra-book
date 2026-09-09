import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent;out=R/'results';env=json.loads((out/'environment.json').read_text())
for f,h in env['source_hashes'].items():assert hashlib.sha256((R/f).read_bytes()).hexdigest()==h
raw=[json.loads(l) for l in (out/'raw.jsonl').read_text().splitlines()];assert len(raw)==6
independent={r['request_id']:r for r in json.loads((out/'independent.json').read_text())}
rows=[];paths=[]
for trial in range(2):
 rr={r['stage']:r for r in raw if r['trial']==trial};assert set(rr)=={'initial','restart','continue'}
 first=rr['initial'];assert not first['result']['passed']
 assert rr['restart']['messages']==first['messages'] and rr['restart']['input_ids']==first['input_ids'] and rr['restart']['initial_code']==first['initial_code']
 cont=rr['continue'];assert cont['messages'][:-2]==first['messages'] and cont['messages'][-2]['content']==first['output_text'] and cont['initial_code']==first['final_code']
 assert cont['messages'][-1]['content']=='Tests failed. Repair using this feedback and return the same JSON schema. Tool result: '+json.dumps(first['result'])
 for stage,r in rr.items():
  assert r['cached_tokens'] in [0,None] and r['setup_start_s']<=r['setup_end_s']<=r['start_s']<=r['model_end_s']<=r['done_s']
  assert r['final_code']==(out/r['request_id']/'intervals.py').read_text()
  v=json.loads(r['result']['validation']['stdout']);assert r['result']['passed']==(r['result']['validation']['returncode']==0 and v['passed'])
  check=independent[r['request_id']];assert check['returncode']==0;full=json.loads(check['stdout']);assert full['cases']==1013 and full['passed']==1013-len(full['failures'])
  rows.append(dict(trial=trial,stage=stage,input_tokens=len(r['input_ids']),output_tokens=len(r['output_ids']),attempt_s=r['done_s']-r['setup_start_s'],visible_passed=sum(c['passed'] for c in v['cases']),visible_total=len(v['cases']),independent_passed=full['passed'],independent_total=full['cases'],passed=r['result']['passed'],finish_reason=r['finish_reason']))
 for stage in ['restart','continue']:
  r=rr[stage];paths.append(dict(trial=trial,path=stage,total_input_tokens=len(first['input_ids'])+len(r['input_ids']),total_output_tokens=len(first['output_ids'])+len(r['output_ids']),work_segments_s=first['done_s']-first['setup_start_s']+r['done_s']-r['setup_start_s'],fee=None,passed=r['result']['passed'],limits='Sum of measured attempt segments; excludes intervening branch and is not uninterrupted end-to-end elapsed.'))
report=dict(status='verified',requests=rows,paths=paths,limits='One known repair task, two trials; file workspace reset/continuation only, no VM recovery or provider costs.')
(R/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
