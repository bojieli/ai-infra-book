import hashlib,json,statistics
from pathlib import Path
R=Path(__file__).resolve().parent;out=R/'results'
for f,h in json.loads((out/'execution.json').read_text())['source_hashes'].items():assert hashlib.sha256((R/f).read_bytes()).hexdigest()==h
raw=[json.loads(l) for l in (out/'requests.jsonl').read_text().splitlines()];assert len(raw)==12
flush=[json.loads(l) for l in (out/'flush-events.jsonl').read_text().splitlines()];assert len(flush)==3
locations={};finished=set()
for worker in [0,1]:
 for p in (out/f'worker{worker}-requests').glob('*.log'):
  for line in p.read_text().splitlines():
   if '{' not in line:continue
   e=json.loads(line[line.index('{'):]);rid=e.get('rid','')
   if not rid.startswith('book909i-'):continue
   if e.get('event')=='request.received':
    assert rid not in locations;locations[rid]=worker
   if e.get('event')=='request.finished':finished.add(rid)
for worker in [0,1]:assert (out/f'worker{worker}.log').read_text().count('Cache flushed successfully!')==6
rows=[];outputs=[]
for trial in range(3):
 reg=json.loads((out/f'registration-trial{trial}.jsonl').read_text().splitlines()[-1]);assert len(reg['workers'])==2 and all(w['is_healthy'] for w in reg['workers'])
 rr=[r for r in raw if r['trial']==trial];assert [r['stage'] for r in rr]==['cold','warm','after_flush','rewarm']
 f=flush[trial];assert f['trial']==trial and rr[1]['end_s']<f['start_s']<f['end_s']<rr[2]['start_s']
 assert set(f['responses'])=={'31091','31092'}
 for r in rr:
  rid=r['rid'];m=r['response']['meta_info'];assert m['id']==rid and rid in locations and rid in finished
  assert m['prompt_tokens']==3136 and m['completion_tokens']==1 and m['num_retractions']==0
  outputs.append(r['response'].get('output_ids',r['response'].get('text')))
  rows.append(dict(trial=trial,stage=r['stage'],worker=locations[rid],cached_tokens=m['cached_tokens'],elapsed_s=r['end_s']-r['start_s']))
assert all(o==outputs[0] for o in outputs)
report=dict(status='observations_verified',rows=rows,all_outputs_equal=True,stages=[dict(stage=s,cached_tokens=[r['cached_tokens'] for r in rows if r['stage']==s],median_s=statistics.median(r['elapsed_s'] for r in rows if r['stage']==s)) for s in ['cold','warm','after_flush','rewarm']],flush_responses=flush)
(R/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
