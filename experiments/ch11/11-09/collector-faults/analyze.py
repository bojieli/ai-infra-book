import collections,hashlib,json,sqlite3
from pathlib import Path
R=Path(__file__).resolve().parent;out=R/'results';execution=json.loads((out/'execution.json').read_text())
assert hashlib.sha256((R/'run.py').read_bytes()).hexdigest()==execution['run_sha256']
rows=[]
for trial in range(2):
 for name in ['memory_crash','file_crash','file_ack_loss']:
  c=out/f'{trial}-{name}';r=json.loads((c/'record.json').read_text());assert r['trial']==trial and r['name']==name
  assert len(r['accepted'])==len(r['work'])==6 and all(a['status']==200 for a in r['accepted'])
  assert all(e['value']==333283335000 and e['cpu_s']>0 for e in r['work'])
  work={e['event_id']:e for e in r['work']};assert len(work)==6
  assert len({e['task_id'] for e in r['work']})==5
  assert sorted(e['attempt_id'] for e in r['work'] if e['task_id']=='task-0')==[0,1]
  with sqlite3.connect(c/'backend.sqlite') as db:
   events=db.execute('select event_id,body from events order by event_id').fetchall();deliveries=db.execute('select event_id,time_s,committed,body from deliveries').fetchall()
  assert [list(e) for e in events]==r['unique_events'] and [list(d) for d in deliveries]==r['deliveries']
  assert all(json.loads(body)==work[eid] for eid,body in events)
  counts=collections.Counter(eid for eid,ts,commit,body in deliveries if commit)
  assert len(counts)==len(events)
  if name=='memory_crash':assert r['before_probe']==0 and len(events)==1
  else:assert r['before_probe']==5 and len(events)==6
  if name=='file_ack_loss':assert sum(counts.values())==7 and max(counts.values())==2
  else:assert r['lifecycle'][0]['action']=='SIGKILL' and r['lifecycle'][0]['exit_code']==-9
  assert r['lifecycle'][-1]['exit_code']==0
  sizes={str(p.relative_to(c)):p.stat().st_size for p in (c/'storage-after-kill').rglob('*') if p.is_file()} if name!='file_ack_loss' else {}
  if name=='file_crash':assert sum(sizes.values())>0
  rows.append(dict(trial=trial,condition=name,accepted_events=6,old_events_recovered=r['before_probe'],unique_committed_events=len(events),delivery_attempts=len(deliveries),committed_delivery_attempts=sum(counts.values()),duplicate_committed_deliveries=sum(counts.values())-len(events),actual_tool_executions=len(work),logical_tasks=5,actual_tool_cpu_s=sum(e['cpu_s'] for e in r['work']),storage_after_kill_bytes=sizes))
report=dict(status='verified',rows=rows,limits='Process SIGKILL, local filesystem and HTTP only; receiver acceptance is not end-to-end commit. SQLite unique event_id performs deduplication, not Collector. No prices, MiB capacity sweep or network throughput claim.')
(R/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
