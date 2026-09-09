"""Derive observed batch latency, throughput and scheduler occupancy."""
import hashlib,json,statistics
from pathlib import Path
root=Path(__file__).parent;r=root/'results'
env=json.loads((r/'environment.json').read_text())
assert env['source_sha256']==hashlib.sha256((root/'run.py').read_bytes()).hexdigest()
assert env['input_sha256']==hashlib.sha256((r/'inputs.json').read_bytes()).hexdigest()
inputs=json.loads((r/'inputs.json').read_text())['requests']
requests=[json.loads(x) for x in (r/'requests.jsonl').read_text().splitlines()]
batches=[json.loads(x) for x in (r/'batches.jsonl').read_text().splitlines()]
assert len(batches)==32
byrun={}
for x in requests:byrun.setdefault(x['run_id'],[]).append(x)
# Scheduler snapshots are recorded on each observed iteration; report sampled
# active/occupied-block values, not entire GPU memory or inferred DRAM bytes.
stats={}
for line in (r/'engine-stats.jsonl').open():
 x=json.loads(line);stats.setdefault(x['run_id'],[]).append(x)
result=[];tokenrefs={};differences=[]
for b in batches:
 rows=byrun[b['run_id']];assert len(rows)==b['batch']
 ttft=[];latency=[];per_token=[];hits=[]
 for x in rows:
  i=int(x['id'].rsplit('-r',1)[1]);ids=inputs[b['kind']][i]
  assert x['input_tokens']==len(ids)==(2048 if b['kind']=='short' else 8192)
  assert x['input_sha256']==hashlib.sha256(json.dumps(ids).encode()).hexdigest()
  assert len(x['output_ids'])==256 and x['events'][-1][1]==256
  assert all(a[0]<=c[0] and a[1]<=c[1] for a,c in zip(x['events'],x['events'][1:]))
  assert x['cached_tokens']==(0 if b['kind']=='short' else 6144),(b['run_id'],x['cached_tokens'])
  hits.append(x['cached_tokens'])
  first=next(e[0] for e in x['events'] if e[1]>0)
  ttft.append(first-x['start_s']);latency.append(x['end_s']-x['start_s'])
  per_token.append((x['events'][-1][0]-first)/255)
  key=(b['kind'],i)
  if b['trial']!='warm':
   if key in tokenrefs and tokenrefs[key]!=x['output_ids']:
    ref=tokenrefs[key];diff=next(j for j,(u,v) in enumerate(zip(ref,x['output_ids'])) if u!=v)
    differences.append(dict(run_id=b['run_id'],request=i,first_difference=diff))
   else:tokenrefs.setdefault(key,x['output_ids'])
 s=stats.get(b['run_id'],[])
 duration=b['end_s']-b['start_s']
 result.append(dict(**b,duration_s=duration,output_tokens=256*b['batch'],output_tokens_per_s=256*b['batch']/duration,
  median_ttft_ms=statistics.median(ttft)*1000,max_ttft_ms=max(ttft)*1000,
  median_request_s=statistics.median(latency),median_time_per_output_ms=statistics.median(per_token)*1000,
  max_running_observed=max(x['scheduler']['num_running_reqs'] for x in s),
  preemptions_observed=sum((x['iteration'] or {}).get('num_preempted_reqs',0) for x in s),
  full_batch_decode_iterations=sum(1 for x in s if x['iteration'] and
      x['iteration']['num_generation_tokens']==b['batch'] and
      x['iteration']['prompt_token_stats']['computed']==0),
  max_kv_usage_observed=max(x['scheduler']['kv_cache_usage'] for x in s),cached_tokens=sum(hits)))
formal=[x for x in result if x['trial']!='warm'];assert len(formal)==24
summary=[]
for kind in ['short','prefix']:
 for batch in [1,4,16,64]:
  rows=[x for x in formal if x['kind']==kind and x['batch']==batch];assert len(rows)==3
  summary.append(dict(kind=kind,batch=batch,**{k:statistics.median(x[k] for x in rows) for k in ['output_tokens_per_s','median_ttft_ms','median_request_s','median_time_per_output_ms']},
    throughput_min=min(x['output_tokens_per_s'] for x in rows),throughput_max=max(x['output_tokens_per_s'] for x in rows),
    max_running_observed=max(x['max_running_observed'] for x in rows),max_kv_usage_observed=max(x['max_kv_usage_observed'] for x in rows),
    preemptions_observed=sum(x['preemptions_observed'] for x in rows),
    full_batch_decode_iterations=sum(x['full_batch_decode_iterations'] for x in rows)))
(r/'summary.json').write_text(json.dumps(dict(summary=summary,batches=result,output_differences= differences,
  scope='Batch throughput includes measured prefill and forced 256-token output, excludes long-prefix seeding and initialization. Warmups excluded. TPOT is request first-to-last delivery divided by 255, not a pooled ITL percentile.'),indent=2)+'\n')
for x in summary:print(json.dumps(x))
print('Output sequences differing from first observed same-input reference:',len(differences))
