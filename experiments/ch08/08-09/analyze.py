import argparse,json,hashlib,re,math,statistics
from pathlib import Path
ROOT=Path(__file__).absolute().parent
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,default=ROOT/'runs/service-001');p.add_argument('--out',type=Path,default=ROOT/'analysis.json');a=p.parse_args()
protocol=json.loads((a.run/'protocol.json').read_text());inputs=json.loads((a.run/'inputs.json').read_text());tasks={t['id']:t for t in inputs['tasks']};raw=[json.loads(x) for x in (a.run/'requests.jsonl').read_text().splitlines()];groups=[json.loads(x) for x in (a.run/'groups.jsonl').read_text().splitlines()];complete=json.loads((a.run/'completion.json').read_text());checks=0
assert complete==dict(groups=21,formal_requests=336,warmup_requests=8)
assert hashlib.sha256((a.run/'inputs.json').read_bytes()).hexdigest()==protocol['input_sha256']
for t in tasks.values():
 found=dict(re.findall(r'^(k\d{4}) = (\d{6})$',t['messages'][1]['content'],re.M));assert len(found)==t['rows'] and all(found[k]==v for k,v in t['expected'].items());checks+=1
assert len(raw)==344 and len(groups)==21 and len({r['id'] for r in raw})==344

def unique(pairs):
 d={}
 for k,v in pairs:
  if k in d:raise ValueError('duplicate key')
  d[k]=v
 return d

def quantile(values,q):
 v=sorted(values);return v[max(0,math.ceil(q*len(v))-1)]
rows=[];reports=[]
for g,planned in zip(groups,protocol['groups']):
 assert all(g[k]==v for k,v in planned.items());checks+=1
 subset=[r for r in raw if r['group']==g['id']];assert len(subset)==16
 for i,tid in enumerate(g['tasks']):
  r=next(r for r in subset if r['id']==g['id']+f'-{i}');assert r['task_id']==tid
  assert abs(r['intended_arrival_s']-(g['start_s']+(i/g['rate'] if g['rate'] is not None else 0)))<1e-6
  assert g['start_s']<=r['actual_arrival_s']<=r['submitted_s']<=r['end_s']<=g['end_s'] and r['cached_tokens']==0
  try:correct=json.loads(r['text'],object_pairs_hook=unique)==tasks[tid]['expected'] and r['finish_reason']=='stop'
  except (ValueError,TypeError):correct=False
  first=next(t for t,n in r['events'] if n>0);lat=r['end_s']-r['intended_arrival_s'];qualified=correct and lat<=protocol['slo_completion_s']
  rows.append(dict(group=g['id'],id=r['id'],task_id=tid,correct=correct,qualified=qualified,latency_s=lat,ttft_s=first-r['intended_arrival_s'],application_queue_s=r['submitted_s']-r['actual_arrival_s'],arrival_lateness_s=r['actual_arrival_s']-r['intended_arrival_s'],engine_time_in_queue_s=r['metrics']['scheduled_ts']-r['metrics']['queued_ts'],normal_stop=r['finish_reason']=='stop',output_tokens=len(r['output_ids'])))
  assert r['metrics']['scheduled_ts']>=r['metrics']['queued_ts'] and not r['metrics']['is_corrupted']
  checks+=5
 if g['service']=='serial':
  admitted=sorted(subset,key=lambda r:r['submitted_s']);assert all(x['end_s']<=y['submitted_s'] for x,y in zip(admitted,admitted[1:]));checks+=1
 before=g['energy_before'];after=g['energy_after'];assert before['gpu_uuid']==after['gpu_uuid'] and before['cpu_path']==after['cpu_path']
 gpu=(after['gpu_energy_mj']-before['gpu_energy_mj'])/1000;assert gpu>=0
 assert before['cpu_max_energy_range_uj']==after['cpu_max_energy_range_uj']
 assert all(0<=e['cpu_package_energy_uj']<e['cpu_max_energy_range_uj'] for e in [before,after])
 delta=after['cpu_package_energy_uj']-before['cpu_package_energy_uj'];wrapped=delta<0
 cpu=(delta%before['cpu_max_energy_range_uj'])/1e6
 assert before['gpu_read_end_ns']/1e9<=g['start_s'] and after['gpu_read_start_ns']/1e9>=g['end_s']
 assert before['cpu_read_end_ns']/1e9<=g['start_s'] and after['cpu_read_start_ns']/1e9>=g['end_s'];checks+=4
 q=[r for r in rows if r['group']==g['id']];elapsed=g['end_s']-g['start_s'];good=sum(r['qualified'] for r in q)
 reports.append(dict(id=g['id'],rep=g['rep'],service=g['service'],rate=g['rate'],requests=16,correct=sum(r['correct'] for r in q),qualified=good,normal_stop=sum(r['normal_stop'] for r in q),wall_s=elapsed,completed_per_s=16/elapsed,quality_goodput_per_s=sum(r['correct'] for r in q)/elapsed,slo_goodput_per_s=good/elapsed,p95_latency_s=quantile([r['latency_s'] for r in q],.95),p95_ttft_s=quantile([r['ttft_s'] for r in q],.95),max_application_queue_s=max(r['application_queue_s'] for r in q),max_arrival_lateness_s=max(r['arrival_lateness_s'] for r in q),gpu_gross_j=gpu,cpu_package_gross_j=cpu,cpu_counter_wrapped_once=wrapped,component_gross_j_per_qualified=(gpu+cpu)/good if good else None,gpu_energy_window_s=((after['gpu_read_start_ns']+after['gpu_read_end_ns'])-(before['gpu_read_start_ns']+before['gpu_read_end_ns']))/2e9,cpu_energy_window_s=((after['cpu_read_start_ns']+after['cpu_read_end_ns'])-(before['cpu_read_start_ns']+before['cpu_read_end_ns']))/2e9))
stats=[json.loads(x) for x in (a.run/'stats.jsonl').read_text().splitlines()]
formal=[r for r in raw if r['group']!='warm']
variants={tid:len({tuple(r['output_ids']) for r in formal if r['task_id']==tid}) for tid in tasks}
assert all(n==1 for n in variants.values());checks+=8
result=dict(checks=checks,formal_requests=336,unique_tasks=8,output_variants_per_task=variants,scheduler_samples=len(stats),observed_max_running=max(s["scheduler"]["num_running_reqs"] for s in stats),observed_max_waiting=max(s["scheduler"]["num_waiting_reqs"] for s in stats),observed_max_kv_usage=max(s["scheduler"]["kv_cache_usage"] for s in stats),observed_preemptions=sum(s["iteration"]["num_preempted_reqs"] for s in stats if s["iteration"]),normal_stop=sum(r['normal_stop'] for r in rows),correct=sum(r['correct'] for r in rows),qualified=sum(r['qualified'] for r in rows),groups=reports,rows=rows,whole_machine_energy_j=None,monetary_cost=None,scope='Observed shared GPU and CPU-package counter differences, not exclusive job or wall energy. Deterministic arrivals, 3 repetitions, fixed finite 16-task windows; no steady-state capacity or cross-device optimum claim.')
a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['rows','groups']}));print(json.dumps(reports))
