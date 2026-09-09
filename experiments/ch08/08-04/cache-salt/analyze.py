import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
raw=json.loads((ROOT/'results/run-v2/raw.json').read_text());assert raw['status']=='passed'
for f,h in raw['source_hashes'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
rows=raw['records'];assert len(rows)==50
cold={'a-cold','b-cold','none-cold','mutated-a'};summary=[]
base=json.loads((ROOT/'inputs.json').read_text())
for trial in range(5):
    group=[r for r in rows if r['trial']==trial];assert len(group)==10
    assert len({r['case'] for r in group})==10
    normal=[r for r in group if not r['mutated']]
    assert all(r['output_ids']==normal[0]['output_ids'] for r in normal)
    for r in group:
        ids=base.copy();ids[0]=(4200 if r['mutated'] else 4100)+trial
        assert hashlib.sha256(json.dumps(ids).encode()).hexdigest()==r['input_sha256']
        assert len(ids)==r['input_tokens']==3136 and len(r['output_ids'])==1
        assert r['events'][-1][1]==1
        if r['case'] in cold:assert r['cached_tokens']==0
        else:assert 0<r['cached_tokens']<len(ids)
    warm=[r['cached_tokens'] for r in group if r['case'] not in cold];assert len(set(warm))==1
for case in dict.fromkeys(r['case'] for r in rows):
    group=[r for r in rows if r['case']==case]
    summary.append(dict(case=case,cached_tokens=[r['cached_tokens'] for r in group],ttft_ms=[1000*next(e[0] for e in r['events'] if e[1]>0) for r in group],elapsed_median_ms=1000*statistics.median(r['elapsed_s'] for r in group)))
result=dict(status='passed',requests=50,trials=5,cases=summary,scope='Actual fixed vLLM cache identity behavior; one token output, five altered leading tokens, same engine and fixed order. Not authentication, TTL, physical residency or online queue measurement.')
(ROOT/'results/summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
