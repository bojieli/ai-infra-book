import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
r=json.loads((root/'results/supervisor.json').read_text())
for f,h in r['source_hashes'].items():assert hashlib.sha256((root/f).read_bytes()).hexdigest()==h,f
life=[json.loads(l) for l in (root/'results/lifecycle.jsonl').read_text().splitlines()]
trace=[json.loads(l) for l in (root/'results/storage.jsonl').read_text().splitlines()]
assert [e['event'] for e in life]==['initializing','ready','request_start']
assert [e['event'] for e in trace]==['begin','exception']
assert trace[1]['type']=='OSError' and 'Short read' in trace[1]['message']
assert r['reason']=='request_observation_expired' and r['request_observed_s']>=60
assert r['exit_before_cleanup'] is None and r['members_before_cleanup']
assert not r['members_after_cleanup']
assert r['original_bytes']-r['truncated_bytes']==2
assert r['truncated_sha256']==r['final_truncated_file_sha256']
assert hashlib.sha256((root/'truncated-page.bin').read_bytes()).hexdigest()==r['truncated_sha256']
log=(root/'results/engine.log').read_text();assert 'prefetch_io_aux_func' in log and 'OSError: Short read' in log
print(json.dumps(dict(status='observations_verified',request_observed_s=r['request_observed_s'],exit_code=r['exit_code'],members_after_cleanup=r['members_after_cleanup'])))
