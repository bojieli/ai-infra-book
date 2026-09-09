import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
raw=json.loads((ROOT/'results/step-audit-v1/raw.json').read_text())
formal=json.loads((ROOT/'results/apc-off-v1/raw.json').read_text())
for f,h in raw['source_hashes'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
assert len(raw['records'])==4
rows=[]
for r in raw['records']:
    steps=r['steps'][0];assert len(r['outputs'])==r['batch']
    for out in r['outputs']:
        expected=next(q for q in formal['requests'] if q['kind']==r['kind'] and q['batch']==r['batch'] and q['index']==out['index'] and q['trial']==0)
        assert out['output_ids']==expected['output_ids'] and out['cached_tokens'] in [0,None]
    for s in steps:
        assert sum(s['per_request_scheduled_tokens'].values())==s['total_scheduled_tokens']
        assert s['event_ms']>=0 and s['host_s']>=0
    full=[s for s in steps if len(s['per_request_scheduled_tokens'])==r['batch'] and all(t==1 for t in s['per_request_scheduled_tokens'].values())]
    assert full
    rows.append(dict(kind=r['kind'],batch=r['batch'],all_model_calls=len(steps),
        full_batch_one_token_calls=len(full),full_batch_event_median_ms=statistics.median(s['event_ms'] for s in full),
        full_batch_host_median_ms=statistics.median(s['host_s']*1000 for s in full),
        empty_calls=sum(s['total_scheduled_tokens']==0 for s in steps),
        other_nonempty_calls=sum(s['total_scheduled_tokens']>0 for s in steps)-len(full)))
summary=dict(status='passed',rows=rows,
    scope='Separate audit; full-batch one-token scheduler calls selected from actual metadata. CUDA events bracket execute_model only and include host submission gaps. Client TPOT includes other phases and is from another run, so do not subtract these medians to label CPU overhead.')
(ROOT/'results/step-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
