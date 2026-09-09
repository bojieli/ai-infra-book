import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent;P=ROOT/'results/apc-off-v1'
raw=json.loads((P/'raw.json').read_text());inputs=json.loads((ROOT/'followup-inputs.json').read_text())
assert raw['status']=='passed' and not raw['config']['enable_prefix_caching'] and raw['config']['disable_log_stats']
for f,h in raw['source_hashes'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
assert len(raw['batches'])==16 and len(raw['requests'])==136
assert [json.loads(l) for l in (P/'requests.jsonl').read_text().splitlines()]==raw['requests']
for short,long in zip(inputs['short'],inputs['long']):assert short==long[:2048] and len(long)==8192
formal=[];sequences={};differences=[]
for b in raw['batches']:
    rows=[r for r in raw['requests'] if (r['kind'],r['batch'],r['trial'])==(b['kind'],b['batch'],b['trial'])]
    assert len(rows)==b['batch'];ttft=[];tpot=[]
    for r in rows:
        ids=inputs[r['kind']][r['index']]
        assert len(ids)==r['input_tokens'] and hashlib.sha256(json.dumps(ids).encode()).hexdigest()==r['input_sha256']
        assert r['cached_tokens'] in [0,None] and len(r['output_ids'])==256
        events=r['events'];assert events[-1][1]==256
        assert all(a[0]<=c[0] and a[1]<=c[1] for a,c in zip(events,events[1:]))
        first=next(e[0] for e in events if e[1]>0);ttft.append((first-r['start_s'])*1000);tpot.append((events[-1][0]-first)/255*1000)
        if b['trial']!='warm':
            key=(r['kind'],r['index'])
            if key in sequences and sequences[key]!=r['output_ids']:differences.append(r['id'])
            else:sequences.setdefault(key,r['output_ids'])
    if b['trial']!='warm':formal.append(dict(kind=b['kind'],batch=b['batch'],trial=b['trial'],throughput=256*b['batch']/(b['end_s']-b['start_s']),ttft_ms=statistics.median(ttft),tpot_ms=statistics.median(tpot)))
assert len(formal)==12
summary=[]
for kind in ['short','long']:
    for batch in [1,16]:
        rows=[r for r in formal if (r['kind'],r['batch'])==(kind,batch)];assert sorted(r['trial'] for r in rows)==[0,1,2]
        summary.append(dict(kind=kind,batch=batch,**{k:statistics.median(r[k] for r in rows) for k in ['throughput','ttft_ms','tpot_ms']}))
out=dict(status='passed',rows=summary,batches=formal,formal_requests=102,
    output_difference_count=len(differences),output_differences=differences,
    raw_sha256=hashlib.sha256((P/'raw.json').read_bytes()).hexdigest(),
    scope='Same APC-off eager engine; nested prompt lengths, requested concurrency1/16. No per-step occupancy/preemption measurement in this lightweight run. TPOT is client delivery time, not GPU kernel duration. Output equality is numerical observation, not task quality.')
(ROOT/'results/followup-summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
