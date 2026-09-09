"""Verify actual native child-process storage events and unchanged outputs."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(R/'results/plan.json');base=read(R/'baseline.json')['source_sha256']
for name,h in plan['source_sha256'].items():assert sha(R/name)==h,name
for name in ['config.json','inputs.json','reference.json','cache-manifest.json','server.py']:
 assert sha(R/name)==base[name],name
assert read(R/'results/execution.json')==dict(status='completed',groups=4)
config=read(R/'config.json');ref=read(R/'reference.json');rows=[];requests=0
for c in plan['order']:
 p=R/'results'/f"{c['trial']}-{c['entry']}-{c['count']}"
 coord=read(p/'coordinator.json');assert coord['exit_code']==0 and not coord['timed_out']
 info=read(p/'server-info.json');assert all(info[k]==v for k,v in config.items())
 assert info['max_total_num_tokens']==4096
 assert all(s['memory_usage']['token_capacity']==4096 for s in info['internal_states']) and info['internal_states']
 prep=read(p/'cache-preparation.json');assert prep['files_verified']==65 and prep['source_manifest_sha256']==sha(R/'cache-manifest.json')
 rr=read(p/'requests.json');assert len(rr)==c['count'];requests+=len(rr)
 assert sorted(r['index'] for r in rr)==list(range(c['count']))
 for r in rr:
  assert r['output_ids']==ref['output_ids'] and r['response']['text']==ref['text'] and r['passed']
  assert r['sent_s']<=r['end_s']
 installed=[json.loads(s) for s in (p/'storage.jsonl.installed.jsonl').read_text().splitlines()]
 events=[json.loads(s) for s in (p/'storage.jsonl').read_text().splitlines()]
 gets=[e for e in events if e['method']=='get'];assert gets, 'No actual native get observations'
 owned=set(read(p/'owned-processes.json')['pids']);install_pids={x['pid'] for x in installed}
 assert all(e['pid'] in install_pids and e['pid'] in owned and e['start_s']<=e['end_s'] for e in events)
 first=min(rr,key=lambda r:r['end_s']);meta=first['response']['meta_info']
 rows.append(dict(**c,first_completed_index=first['index'],first_cached_tokens=meta.get('cached_tokens'),first_cached_details=meta.get('cached_tokens_details'),get_count=len(gets),successful_gets=sum(e['success'] for e in gets),unique_keys=len({e['key'] for e in gets}),file_bytes_sum=sum(e['bytes'] for e in gets),worker_pid=coord['pid'],installed_pids=sorted(install_pids),get_pids=sorted({e['pid'] for e in gets}),actual_pool_tokens=4096))
assert requests==18 and len(rows)==4
out=dict(status='passed',requests=requests,groups=rows,scope='Actual native storage instrumentation; no performance or root-cause claim')
(R/'summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
