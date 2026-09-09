import hashlib,json,statistics
from pathlib import Path
R=Path(__file__).resolve().parent;out=R/'results'
for f,h in json.loads((out/'execution.json').read_text())['source_hashes'].items():assert hashlib.sha256((R/f).read_bytes()).hexdigest()==h
raw=[json.loads(l) for l in (out/'requests.jsonl').read_text().splitlines()];assert len(raw)==24
prompts=json.loads((out/'prompts.json').read_text());assert len(prompts)==4
capture=[json.loads(l) for l in (out/'capture.jsonl').read_text().splitlines()];assert len(capture)==4
for i,c in enumerate(capture):
 assert c['prompt']==prompts[i] and len(c['messages'])==1+2*(i+1)
 assert c['messages'][-1]['content']==prompts[i]['response']['text']
 if i:assert c['messages'][:-2]==capture[i-1]['messages']
locations={};finished=set()
for worker in [0,1]:
 for p in (out/f'worker{worker}-requests').glob('*.log'):
  for line in p.read_text().splitlines():
   if '{' not in line:continue
   e=json.loads(line[line.index('{'):]);rid=e.get('rid','')
   if not rid.startswith('book909chat-'):continue
   if e.get('event')=='request.received':
    assert rid not in locations;locations[rid]=worker
   if e.get('event')=='request.finished':finished.add(rid)
rows=[];groups=[]
for trial in range(2):
 for policy in ['round_robin','cache_aware','power_of_two']:
  reg=json.loads((out/f'registration-{trial}-{policy}.jsonl').read_text().splitlines()[-1]);assert len(reg['workers'])==2 and all(w['is_healthy'] for w in reg['workers'])
  rr=[r for r in raw if r['trial']==trial and r['policy']==policy];assert [r['prompt_id'] for r in rr]==list(range(4))
  last={};details=[]
  for r in rr:
   rid=r['rid'];m=r['response']['meta_info'];i=r['prompt_id'];assert rid==m['id'] and rid in locations and rid in finished
   assert m['prompt_tokens']==len(prompts[i]['input_ids']) and m['num_retractions']==0 and 0<m['completion_tokens']<=96
   worker=locations[rid]
   d=dict(trial=trial,policy=policy,prompt_id=i,worker=worker,prompt_tokens=m['prompt_tokens'],cached_tokens=m['cached_tokens'],completion_tokens=m['completion_tokens'],finish_reason=m['finish_reason'],elapsed_s=r['end_s']-r['start_s'],previous_worker_completion_gap_s=r['start_s']-last[worker] if worker in last else None,text=r['response']['text'],matches_capture=r['response']['text']==prompts[i]['response']['text'])
   last[worker]=r['end_s'];details.append(d);rows.append(d)
  groups.append(dict(trial=trial,policy=policy,worker_sequence=[d['worker'] for d in details],request_hit_rate=sum(d['cached_tokens']>0 for d in details)/4,token_hit_rate=sum(d['cached_tokens'] for d in details)/sum(d['prompt_tokens'] for d in details),median_s=statistics.median(d['elapsed_s'] for d in details),matches_capture=sum(d['matches_capture'] for d in details)))
report=dict(status='observations_verified',groups=groups,rows=rows,capture=[dict(prompt_id=p['id'],prompt_tokens=len(p['input_ids']),text=p['response']['text'],meta=p['response']['meta_info'],previous_completion_gap_s=p['start_s']-prompts[i-1]['end_s'] if i else None) for i,p in enumerate(prompts)])
(R/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['groups'],indent=2));print(json.dumps(report['capture'],indent=2))
