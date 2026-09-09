import json,hashlib,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
assert hashlib.sha256((ROOT/'prediction.json').read_bytes()).hexdigest()==(ROOT/'prediction.sha256').read_text().strip()
reports=[];all_outputs=[]
for budget in [256,512]:
 r=json.loads((ROOT/f'results/budget{budget}/raw.json').read_text());assert r['status']=='passed'
 for f,h in r['source_hashes'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
 assert len(r['records'])==5 and r['config']['max_num_batched_tokens']==budget
 lat=[];events=[];counts=[]
 for trial in r['records']:
  assert len(trial['steps'])==1
  active=[x for x in trial['steps'][0] if x['total_scheduled_tokens']]
  assert len(active)==8192//budget
  ids=set()
  for i,x in enumerate(active):
   assert x['total_scheduled_tokens']==budget and len(x['per_request_scheduled_tokens'])==1
   rid=next(iter(x['per_request_scheduled_tokens']));ids.add(rid)
   assert x['per_request_scheduled_tokens'][rid]==budget and x['prior_scheduled_tokens'][rid]==i*budget
  assert len(ids)==1 and trial['output']['cached_tokens'] in (0,None)
  assert len(trial['output']['output_ids'])==1
  all_outputs.append(trial['output']['output_ids']);lat.append(trial['output']['client_elapsed_s']);events.append(sum(x['event_ms'] for x in active));counts.append(len(active))
 reports.append(dict(budget=budget,client_s=lat,client_median_s=statistics.median(lat),sum_active_execute_event_ms=events,prefill_chunks=counts))
assert all(x==all_outputs[0] for x in all_outputs)
ratio=reports[0]['client_median_s']/reports[1]['client_median_s']
s=dict(status='passed',reports=reports,measured_ratio256_over512=ratio,quantitative_prediction_supported=ratio>=1.10,measured_preference=512 if ratio>=1 else 256,output_ids=all_outputs[0],scope='New instrumented paired configurations, fixed engine order256 then512, five requests each. Threshold sealed in prediction before run; prior512 results known. Not uninstrumented deployment or mixed-service policy proof.')
(ROOT/'results/summary.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s,indent=2))
