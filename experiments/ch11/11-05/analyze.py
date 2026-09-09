import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
r=json.loads((ROOT/'results/run-v1/raw.json').read_text());assert r['status']=='passed'
assert r['source_sha256']==hashlib.sha256((ROOT/'run.py').read_bytes()).hexdigest()
assert len(r['records'])==9
reports=[]
for x in r['records']:
    if x['mode']=='wide-limit-recheck':
        assert x['correct'] and x['result']['digest']==r['reference']['digest'];continue
    assert x['timed_out'] and x['worker_running_at_feedback']
    assert x['wait_start_s']<=x['feedback_s']<x['release_observed_s']
    if x['mode']=='thread-wait-timeout':
        assert x['result']['digest']==r['reference']['digest']
        assert x['result']['end_s']>x['feedback_s']
    else:assert x['returncode']<0 and not x['stdout_tail']
    reports.append(dict(trial=x['trial'],mode=x['mode'],feedback_wait_ms=1000*(x['feedback_s']-x['wait_start_s']),after_feedback_to_release_ms=1000*(x['release_observed_s']-x['feedback_s'])))
s=dict(status='passed',trials=3,records=reports,rechecks_passed=3,medians={m:statistics.median(x['after_feedback_to_release_ms'] for x in reports if x['mode']==m) for m in ['thread-wait-timeout','process-terminate-and-reap']},scope='Real controlled CPU work, release is observed completion/reaped child, not CPU allocation accounting. Short timeout is not incorrect-result proof.')
(ROOT/'results/summary.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s,indent=2))
