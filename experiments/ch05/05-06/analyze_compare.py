"""Validate coverage and summarize paired measurements without reselection."""
import hashlib
import json
from pathlib import Path
import statistics
ROOT=Path(__file__).resolve().parent
path=ROOT/'results/interleaved-v1';raw=json.loads((path/'raw.json').read_text())
assert raw['status']=='passed' and len(raw['samples'])==132
for f,h in raw['source_hashes'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
assert hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest()==raw['protocol_sha256']
assert hashlib.sha256((ROOT/'results/schedule-summary.json').read_bytes()).hexdigest()==raw['selection_sha256']
rows=[]
for t in [1,7239]:
    for mode in ['eager','graph']:
        grouped={}
        for name in ['native','compiled','schedule']:
            samples=sorted([r for r in raw['samples'] if (r['t'],r['mode'],r['name'])==(t,mode,name)],key=lambda r:r['trial'])
            assert [r['trial'] for r in samples]==list(range(11))
            grouped[name]=[r['event_us'] for r in samples]
            rows.append(dict(t=t,mode=mode,name=name,median_event_us=statistics.median(grouped[name]),
                min_event_us=min(grouped[name]),max_event_us=max(grouped[name]),median_wall_us=statistics.median(r['wall_us'] for r in samples)))
        for baseline in ['native','compiled']:
            delta=[b-s for b,s in zip(grouped[baseline],grouped['schedule'])]
            rows.append(dict(t=t,mode=mode,comparison=baseline+' minus selected schedule',
                paired_median_saving_us=statistics.median(delta),positive_trials=sum(d>0 for d in delta),trials=len(delta),paired_deltas_us=delta))
for profile in raw['profiles']:
    events=json.loads((path/profile['trace']).read_text())['traceEvents']
    kernels=[e for e in events if e.get('cat')=='kernel']
    assert len(kernels)==len(profile['kernels'])>0
    assert [e['name'] for e in kernels]==[e['name'] for e in profile['kernels']]
assert len(raw['profiles'])==len(raw['correctness'])==6
result=dict(status='passed',sample_count=132,rows=rows,
    kernels=[dict(t=p['t'],name=p['name'],count=len(p['kernels'])) for p in raw['profiles']],
    scope='11 paired trials per shape/mode. Positive counts describe this run, not independent-run confidence or exclusive execution.',
    raw_sha256=hashlib.sha256((path/'raw.json').read_bytes()).hexdigest())
(ROOT/'results/interleaved-summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
