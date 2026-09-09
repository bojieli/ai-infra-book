import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
out=ROOT/'results';execution=json.loads((out/'execution.json').read_text())
for f,h in execution['source_hashes'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
requests=[json.loads(l) for l in (out/'requests.jsonl').read_text().splitlines()];assert len(requests)==36
prompts=json.loads((out/'prompts.json').read_text());assert len(prompts)==12
locations={}
for worker in [0,1]:
 for p in (out/f'worker{worker}-requests').glob('*.log'):
  for line in p.read_text().splitlines():
   if '{' not in line:continue
   e=json.loads(line[line.index('{'):])
   if e.get('event')=='request.received':
    rid=e['rid']
    if rid.startswith('book909-'):
     assert rid not in locations,rid;locations[rid]=worker
summary=[];outputs={}
def percentile(values,p):
 vals=sorted(values);x=(len(vals)-1)*p;i=int(x);return vals[i]+(vals[min(i+1,len(vals)-1)]-vals[i])*(x-i)
for policy in ['round_robin','cache_aware','power_of_two']:
 rows=[r for r in requests if r['policy']==policy];assert len(rows)==12
 registration=json.loads((out/f'registration-{policy}.jsonl').read_text().splitlines()[-1]);assert len(registration['workers'])==2 and all(w['is_healthy'] for w in registration['workers'])
 details=[];last={}
 for r in rows:
  m=r['response']['meta_info'];rid=m['id'];assert rid==r['rid'];assert rid in locations
  assert m['prompt_tokens']==len(prompts[r['prompt_id']]['input_ids']);assert m['completion_tokens']==1 and m['num_retractions']==0
  worker=locations[rid];details.append(dict(prompt_id=r['prompt_id'],worker=worker,prompt_tokens=m['prompt_tokens'],cached_tokens=m['cached_tokens'],elapsed_s=r['end_s']-r['start_s'],previous_worker_request_gap_s=r['start_s']-last[worker] if worker in last else None));last[worker]=r['end_s']
  generated=r['response'].get('output_ids',r['response'].get('text'));outputs.setdefault(r['prompt_id'],[]).append(generated)
 total=sum(d['prompt_tokens'] for d in details);cached=sum(d['cached_tokens'] for d in details)
 summary.append(dict(policy=policy,requests=len(rows),total_prompt_tokens=total,total_cached_tokens=cached,token_weighted_hit_rate=cached/total,request_hit_rate=sum(d['cached_tokens']>0 for d in details)/len(rows),worker_sequence=[d['worker'] for d in details],client_elapsed_median_s=statistics.median(d['elapsed_s'] for d in details),client_elapsed_sample_p95_s=percentile([d['elapsed_s'] for d in details],.95),details=details))
assert all(len(v)==3 and v[0]==v[1]==v[2] for v in outputs.values())
(ROOT/'summary.json').write_text(json.dumps(dict(status='verified',policies=summary,outputs_match_across_policies=True),indent=2)+'\n');print(json.dumps([{k:v for k,v in s.items() if k!='details'} for s in summary]))
