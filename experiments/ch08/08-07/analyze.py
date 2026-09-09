import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'results';e=json.loads((R/'environment.json').read_text());t=json.loads((R/'tasks.json').read_text())
assert hashlib.sha256((P/'run.py').read_bytes()).hexdigest()==e['run_sha256']
assert json.loads((R/'completion.json').read_text())==dict(completed=True,short=4,long=10)
answers={x['id']:x['answer'] for x in t['tasks']}
def check(row):
 assert row['passed']==(row['text'].strip()==answers[row['task']])
 assert row['begin_ns']<=row['events'][0]['t_ns']<=row['events'][-1]['t_ns']<=row['end_ns']
 assert row['finish_reason'] in ['stop','length']
 assert row['events'][-1]['generation_tokens']<=64
 assert len(row['cache'])==36
 return dict(task=row['task'],passed=row['passed'],text=row['text'],finish_reason=row['finish_reason'],generation_tokens=row['events'][-1]['generation_tokens'],ttft_s=row['ttft_s'],generation_s=row['elapsed_s'])
short=[json.loads(x) for x in (R/'short.jsonl').read_text().splitlines()];assert len(short)==4
short_summary=[check(r) for r in short];cases=[]
for trial,slots in json.loads((R/'plan.json').read_text()):
 case=R/f'{trial}-{slots}slots';ready=json.loads((case/'ready.json').read_text());rows=json.loads((case/'outputs.json').read_text());assert len(rows)==len(ready['caches'])==slots
 for i,c in enumerate(ready['caches']):
  assert len(c)==36
  for layer in c:
   assert layer['offset']==8191 and layer['type']=='KVCache'
   assert len(layer['state'])==2
   assert all(s['shape']==[1,8,8191,128] for s in layer['state'])
   assert all(s['dtype'] in ['mlx.core.float16','mlx.core.bfloat16'] for s in layer['state'])
   assert layer['nbytes']>=sum(s['nbytes'] for s in layer['state'])
  chunks=[x for x in ready['chunks'] if x['task']==rows[i]['task']]
  assert sum(x['count'] for x in chunks)==8191
  assert [x['offset'] for x in chunks]==list(range(0,8191,512))
  assert rows[i]['input_ids']==t['prompts'][rows[i]['task']]['long'][-1:]
 cases.append(dict(trial=trial,slots=slots,ready_prefill_s=(ready['ready_ns']-ready['begin_ns'])/1e9,kv_bytes=sum(c['nbytes'] for cache in ready['caches'] for c in cache),logical_kv_bytes=sum(s['nbytes'] for cache in ready['caches'] for c in cache for s in c['state']),memory=ready['memory'],outputs=[check(r) for r in rows]))
result=dict(load_s=e['load_s'],short=short_summary,cases=cases,passed=sum(r['passed'] for r in short)+sum(x['passed'] for c in cases for x in c['outputs']),requests=14)
(R/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
