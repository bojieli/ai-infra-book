import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'results';e=json.loads((R/'environment.json').read_text());t=json.loads((R/'tasks.json').read_text())
assert hashlib.sha256((P/'run.py').read_bytes()).hexdigest()==e['run_sha256']
assert json.loads((R/'completion.json').read_text())==dict(completed=True,long=8)
answers={x['id']:x['answer'] for x in t['tasks']};expected=['lookup-a','integer-b'];summary=[]
for trial,slots in json.loads((R/'plan.json').read_text()):
 p=R/f'{trial}-{slots}slots';ready=json.loads((p/'ready.json').read_text());rows=json.loads((p/'outputs.json').read_text());after=json.loads((p/'after.json').read_text());chunks=[json.loads(x) for x in (p/'chunks.jsonl').read_text().splitlines()]
 assert [r['task'] for r in rows]==expected
 assert len(ready)==(2 if slots==1 else 1)
 for snap in ready:
  assert len(snap['caches'])==slots
  for c in snap['caches']:
   assert len(c)==36
   for layer in c:
    assert layer['offset']==32767 and layer['type']=='KVCache'
    assert len(layer['state'])==2
    assert all(s['shape']==[1,8,32767,128] for s in layer['state'])
    assert all(s['dtype']=='mlx.core.bfloat16' for s in layer['state'])
    assert layer['nbytes']>=sum(s['nbytes'] for s in layer['state'])
 for task in expected:
  cs=[c for c in chunks if c['task']==task];assert sum(c['count'] for c in cs)==32767
  assert [c['offset'] for c in cs]==list(range(0,32767,512))
  assert all(c['start_ns']<c['end_ns'] for c in cs)
  assert len(t['prompts'][task]['long'])==32768
 for row in rows:
  assert row['input_ids']==t['prompts'][row['task']]['long'][-1:]
  assert row['passed']==(row['text'].strip()==answers[row['task']])
  assert row['begin_ns']<=row['events'][0]['t_ns']<=row['events'][-1]['t_ns']<=row['end_ns']
  assert row['finish_reason'] in ['stop','length'] and row['events'][-1]['generation_tokens']<=64
 summary.append(dict(trial=trial,slots=slots,task_mix=expected,elapsed_s=(after['end_ns']-after['begin_ns'])/1e9,
  prefill_s=sum((s['ready_ns']-s['begin_ns'])/1e9 for s in ready),
  max_ready_kv_bytes=max(sum(c['nbytes'] for cache in s['caches'] for c in cache) for s in ready),
  max_ready_active_bytes=max(s['memory']['active'] for s in ready),
  max_ready_peak_bytes=max(s['memory']['peak'] for s in ready),
  outputs=[dict(task=r['task'],text=r['text'],passed=r['passed'],finish_reason=r['finish_reason'],continuation_ttft_s=r['ttft_s'],continuation_s=r['elapsed_s']) for r in rows]))
# Exact inputs are shared across slots/trials by construction; compare outputs without assuming equality.
comparison={task:[dict(trial=c['trial'],slots=c['slots'],text=next(r['text'] for r in c['outputs'] if r['task']==task)) for c in summary] for task in expected}
result=dict(cases=summary,passed=sum(r['passed'] for c in summary for r in c['outputs']),requests=8,matched_output_comparison=comparison)
(R/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
