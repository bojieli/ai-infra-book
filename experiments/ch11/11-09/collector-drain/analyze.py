import hashlib,json,sqlite3,statistics
from pathlib import Path
R=Path(__file__).resolve().parent;OUT=R/'results'
for f,h in json.loads((OUT/'execution.json').read_text())['source_hashes'].items():assert hashlib.sha256((R/f).read_bytes()).hexdigest()==h
reports=[];curves={}
for c in sorted(OUT.iterdir()):
 if not c.is_dir():continue
 run=json.loads((c/'execution.json').read_text());source=[json.loads(l) for l in (c/'source.jsonl').read_text().splitlines()];backend=[json.loads(l) for l in (c/'backend.jsonl').read_text().splitlines()]
 assert len(source)==120 and [r['id'] for r in source]==list(range(120));assert all(r['ack']['status']==200 for r in source)
 with sqlite3.connect(c/'backend.sqlite') as db:stored=dict(db.execute('select id,body from events'))
 assert len(stored)==120
 for s in source:assert json.loads(stored[s['id']])==s['event'] and len(s['event']['padding'].encode())==2048
 committed={};duplicate=0
 for b in backend:
  assert b['end_s']>=b['start_s']
  if b['success']:
   assert b['start_s']>=run['restore_s']
   for e in b['events']:
    assert e==source[e['event_id']]['event']
    if e['event_id'] in committed:duplicate+=1
    else:committed[e['event_id']]=b['end_s']
  else:assert b['start_s']<run['restore_s']
 assert len(committed)==120 and run['exit_code']==0
 events=sorted([(s['dispatch_s'],1,s['id']) for s in source]+[(t,-1,i) for i,t in committed.items()]);outstanding=0;curve=[];first_empty=None
 for t,delta,i in events:
  outstanding+=delta;assert outstanding>=0
  curve.append(dict(t_s=t-run['start_s'],outstanding=outstanding))
  if not outstanding and t>=run['restore_s'] and first_empty is None:first_empty=t
 assert outstanding==0
 old=[s['id'] for s in source if s['dispatch_s']<run['restore_s']]
 last=max(committed.values());prod=run['production_end_s'];backlog_stop=sum(s['dispatch_s']<=prod<committed[s['id']] for s in source)
 reports.append(dict(condition=c.name,trial=run['trial'],injected_service_delay_s=run['delay_s'],accepted=120,unique_committed=120,duplicate_commits=duplicate,pre_recovery_events=len(old),old_backlog_last_commit_after_recovery_s=max(committed[i] for i in old)-run['restore_s'],first_empty_after_recovery_s=first_empty-run['restore_s'],first_empty_during_production=first_empty<prod,production_end_s=prod-run['start_s'],outstanding_at_production_end=backlog_stop,final_commit_s=last-run['start_s'],drain_after_production_s=max(0,last-prod),max_dispatch_lateness_s=max(s['dispatch_s']-s['planned_s'] for s in source),max_outstanding=max(x['outstanding'] for x in curve)))
 curves[c.name]=curve
report=dict(status='verified',conditions=reports,limits='Actual local HTTP/Collector/file queue/SQLite with injected backend service delay; outstanding includes transport and in-flight work, not Collector internal queue metric.')
(R/'summary.json').write_text(json.dumps(report,indent=2)+'\n');(R/'curves.json').write_text(json.dumps(curves,indent=2)+'\n');print(json.dumps(report,indent=2))
