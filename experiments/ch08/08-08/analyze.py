import hashlib,json,math,re,statistics
from pathlib import Path
root=Path(__file__).parent;r=root/'results';reports=[];allrows={};envs={}
def unique_object(pairs):
 d={}
 for k,v in pairs:
  if k in d:raise ValueError('Duplicate JSON key')
  d[k]=v
 return d
for name in ['bf16','fp8']:
 p=r/name;env=json.loads((p/'environment.json').read_text());envs[name]=env
 for filename,digest in env['hashes'].items():assert hashlib.sha256((root/filename).read_bytes()).hexdigest()==digest
 assert hashlib.sha256((p/'inputs.json').read_bytes()).hexdigest()==env['input_sha256']
 inp=json.loads((p/'inputs.json').read_text());tasks={t['id']:t for t in inp['tasks']};assert len(tasks)==8
 for task in tasks.values():
  records=dict(re.findall(r'^(k\d{4}) = (\d{6})$',task['messages'][1]['content'],re.MULTILINE))
  assert len(records)==task['rows']
  assert all(records[k]==v for k,v in task['expected'].items())
 rows=[json.loads(x) for x in (p/'requests.jsonl').read_text().splitlines()]
 batches=[json.loads(x) for x in (p/'batches.jsonl').read_text().splitlines()]
 assert len(rows)==97 and len(batches)==24
 snaps=json.loads((p/'kv-snapshots.json').read_text())
 assert len(snaps['after_calibration'])==len(snaps['after'])==1
 before=snaps['before'][0];cal=snaps['after_calibration'][0];after=snaps['after'][0]
 assert len(cal['scales'])==36 and cal['scales']==after['scales']
 assert all(not a['calculate'] and math.isfinite(a['k']) and math.isfinite(a['v']) and a['k']>0 and a['v']>0 for a in cal['scales'])
 assert all(a['backend']=='TritonAttentionImpl' for a in cal['scales'])
 if name=='fp8':assert snaps['armed_layers']==[36] and cal['scales']!=before['scales']
 evaluated=[]
 for b in batches:
  group=[x for x in rows if x['id'].startswith(b['id']+'-')];assert len(group)==4
  assert len({x['task_id'] for x in group})==4
  for x in group:
   expected=tasks[x['task_id']]['expected']
   try:parsed=json.loads(x['text'],object_pairs_hook=unique_object);correct=parsed==expected
   except (ValueError,TypeError):parsed=None;correct=False
   if x['mode']=='fixed':assert len(x['output_ids'])==64 and x['finish_reason']=='length'
   first=next(e[0] for e in x['events'] if e[1]>0);tokens=len(x['output_ids'])
   evaluated.append(dict(id=x['id'],task_id=x['task_id'],mode=x['mode'],trial=b['trial'],rows=b['rows'],concurrency=b['concurrency'],
     prompt_tokens=len(tasks[x['task_id']]['prompt_token_ids']),output_tokens=tokens,finish_reason=x['finish_reason'],
     strict_correct=correct if x['mode']=='natural' else None,parsed=parsed if x['mode']=='natural' else None,
     latency_s=x['end_s']-x['start_s'],ttft_ms=(first-x['start_s'])*1000,
     average_output_interval_ms=(x['events'][-1][0]-first)*1000/(tokens-1) if tokens>1 else None))
 formal=[x for x in evaluated if x['trial']!='warm'];assert len(formal)==64
 summary=[]
 for n in [128,512]:
  for concurrency in [1,4]:
   for mode in ['natural','fixed']:
    group=[x for x in formal if (x['rows'],x['concurrency'],x['mode'])==(n,concurrency,mode)];assert len(group)==8
    runs=[b for b in batches if (b['rows'],b['concurrency'],b['mode'])==(n,concurrency,mode) and b['trial']!='warm']
    summary.append(dict(rows=n,concurrency=concurrency,mode=mode,requests=8,
      correct=sum(x['strict_correct'] is True for x in group) if mode=='natural' else None,
      truncated=sum(x['finish_reason']=='length' for x in group),output_tokens=sum(x['output_tokens'] for x in group),
      median_latency_s=statistics.median(x['latency_s'] for x in group),median_ttft_ms=statistics.median(x['ttft_ms'] for x in group),
      median_output_interval_ms=statistics.median(x['average_output_interval_ms'] for x in group if x['average_output_interval_ms'] is not None),
      output_tokens_per_s=sum(x['output_tokens'] for x in group)/sum(b['end_s']-b['start_s'] for b in runs)))
 reports.append(dict(name=name,summary=summary,requests=evaluated,unique_kv_storage_bytes=cal['unique_kv_storage_bytes'],
    kv_tensors=cal['kv_tensors'],cuda_allocated_after_calibration=cal['cuda_allocated'],cuda_peak_allocated_after_run=after['cuda_peak_allocated'],
    scales_unchanged_during_measurement=True))
 allrows[name]={x['id']:x for x in rows if x['id'][0].isdigit()}
expected=dict(envs['bf16']['config']);expected['kv_cache_dtype']='fp8_e4m3';assert envs['fp8']['config']==expected
assert envs['fp8']['input_sha256']==envs['bf16']['input_sha256']
differences=[];repeat_differences={}
for name,rows in allrows.items():
 repeat_differences[name]=[key for key,a in rows.items() if key.startswith('0-') and
    a['output_ids']!=rows['1-'+key[2:]]['output_ids']]
assert allrows['bf16'].keys()==allrows['fp8'].keys()
for key,a in allrows['bf16'].items():
 b=allrows['fp8'][key]
 if a['output_ids']!=b['output_ids']:
  differences.append(dict(id=key,bf16_tokens=len(a['output_ids']),fp8_tokens=len(b['output_ids']),
      first_difference=next((i for i,(u,v) in enumerate(zip(a['output_ids'],b['output_ids'])) if u!=v),min(len(a['output_ids']),len(b['output_ids'])))))
(r/'summary.json').write_text(json.dumps(dict(configurations=reports,output_differences=differences,repeat_output_differences=repeat_differences,
 scope='Eight distinct synthetic retrieval tasks, repeated across concurrency and modes. Same BF16 weights and Triton backend. Natural generation quality assessed separately from forced-length timing; no retries performed.'),indent=2)+'\n')
for report in reports:
 print(report['name'],'KVstorage',report['unique_kv_storage_bytes'],'first tensor',report['kv_tensors'][0])
 for x in report['summary']:print(json.dumps(x))
print('Different output sequences',len(differences))
