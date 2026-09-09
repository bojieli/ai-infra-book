import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
base=ROOT.parent/'truncated-request'
reference=json.loads((ROOT.parent/'results/producer-v6/raw.json').read_text())['requests'][0]['response']['output_ids']
baseline_cfg=json.loads((base/'config.json').read_text())
reports=[]
for policy,path in [('wait_complete',base),('timeout',ROOT/'timeout'),('best_effort',ROOT/'best_effort')]:
 sup=json.loads((path/'results/supervisor.json').read_text());cfg=json.loads((path/'config.json').read_text())
 assert cfg=={**baseline_cfg,'hicache_storage_prefetch_policy':policy}
 for f,h in sup['source_hashes'].items():assert hashlib.sha256((path/f).read_bytes()).hexdigest()==h
 assert sup['original_bytes']-sup['truncated_bytes']==2
 assert sup['final_truncated_file_sha256']==sup['truncated_sha256']
 assert not sup['members_after_cleanup']
 life=[json.loads(l) for l in (path/'results/lifecycle.jsonl').read_text().splitlines()]
 tracefile=path/'results/storage.jsonl';trace=[json.loads(l) for l in tracefile.read_text().splitlines()] if tracefile.exists() else []
 gets=[x for x in trace if x['method']=='get' and x['event']=='begin'];exceptions=[x for x in trace if x['event']=='exception'];ret=[x for x in life if x['event']=='request_return'];start=next(x['time_s'] for x in life if x['event']=='request_start')
 if policy=='wait_complete':assert not ret and sup['reason']=='request_observation_expired'
 else:
  assert len(ret)==1 and sup['exit_code']==0
  assert ret[0]['response']['output_ids']==reference
  assert ret[0]['response']['meta_info']['cached_tokens']==0
  assert any(x['event']=='shutdown_end' for x in life)
 reports.append(dict(policy=policy,completed=bool(ret),elapsed_s=ret[0]['time_s']-start if ret else None,observation_s=sup['request_observed_s'],get_calls=len(gets),exceptions=[dict(type=x['type'],message=x['message'],after_request_s=x['end_s']-start) for x in exceptions],output_matches_reference=ret[0]['response']['output_ids']==reference if ret else None,cached_tokens=ret[0]['response']['meta_info']['cached_tokens'] if ret else None,corrupt_file_unchanged=True,exit_code=sup['exit_code'],truncated_sha256=sup['truncated_sha256']))
assert len({r['truncated_sha256'] for r in reports})==1
assert reports[1]['get_calls']>=1 and reports[1]['exceptions']
(ROOT/'summary.json').write_text(json.dumps(dict(status='observations_verified',cases=reports),indent=2)+'\n');print(json.dumps(reports))
