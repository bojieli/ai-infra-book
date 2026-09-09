import hashlib,json,statistics
from pathlib import Path
P=Path(__file__).resolve().parent;root=P/'results';f=json.loads((P/'fixture.json').read_text())
env=json.loads((root/'environment.json').read_text()); assert json.loads((root/'completion.json').read_text())==dict(completed_cases=12,completed=True)
for n,h in env['source_hashes'].items():assert hashlib.sha256((P/n).read_bytes()).hexdigest()==h
out=[]
for trial,policy in env['plan']:
 r=json.loads((root/f'{trial}-{policy}'/'raw.json').read_text());assert len(r['rows'])==12
 launch={e['pid']:e for e in r['events'] if e['event']=='launch'}
 ready={e['pid']:e for e in r['events'] if e['event']=='ready'}
 destroy={e['pid']:e for e in r['events'] if e['event']=='destroy'}
 assert launch.keys()==ready.keys()==destroy.keys()
 for pid in launch:
  assert launch[pid]['t_ns']<=ready[pid]['t_ns']<=destroy[pid]['t_ns']<=destroy[pid]['end_ns']
  assert destroy[pid]['returncode']==0 and destroy[pid]['stderr']==''
 transitions={};previous=None;used=set()
 for row,source in zip(r['rows'],f['rounds']):
  assert row['turn']==source['turn'] and row['response']['reply']==source['tool_result'] and row['file_sha256']==source['file_sha256']
  assert row['call_ns']<=row['send_ns']<=row['response']['start_ns']<=row['response']['end_ns']<=row['received_ns']
  assert row['call_ns']-row['gap_start_ns']>=int(row['gap_s']*1e9)-100000
  if policy.startswith('predict'):
   pred=transitions.get(previous,previous or 'file');assert row['predicted']==pred and row['prediction_hit']==(pred==row['kind'])
  if previous is not None:transitions[previous]=row['kind']
  previous=row['kind'];used.add(row['worker_pid'])
 unused=set(launch)-used
 samples=r['samples'];pairs=[((s['start_ns']+s['end_ns'])/2,sum(x['rss_bytes'] for x in s['workers'])) for s in samples]
 integral=sum((b[0]-a[0])/1e9*(a[1]+b[1])/2 for a,b in zip(pairs,pairs[1:]))/1024**3
 out.append(dict(trial=trial,policy=policy,rounds=12,launches=len(launch),unused_preparations=len(unused),hits=sum(x['prediction_hit'] is True for x in r['rows']),
  completion_s=(r['work_done_ns']-r['origin_ns'])/1e9,total_with_cleanup_s=(r['end_ns']-r['origin_ns'])/1e9,
  call_wait_s=sum((x['received_ns']-x['call_ns'])/1e9 for x in r['rows']),
  sampled_peak_rss_mib=max((x[1] for x in pairs),default=0)/1024**2,sampled_gib_seconds=integral,
  unused_ready_residency_s=sum((destroy[p]['t_ns']-ready[p]['t_ns'])/1e9 for p in unused),
  max_sample_interval_ms=max((b[0]-a[0])/1e6 for a,b in zip(pairs,pairs[1:]))))
(root/'per-case.json').write_text(json.dumps(out,indent=2)+'\n')
metrics=['completion_s','total_with_cleanup_s','call_wait_s','launches','hits','unused_preparations','sampled_peak_rss_mib','sampled_gib_seconds','unused_ready_residency_s','max_sample_interval_ms']
summary=[dict(policy=p,**{k:statistics.median(r[k] for r in out if r['policy']==p) for k in metrics}) for p in ['resident','demand','predict-50ms','predict-fullgap']]
(root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
