import argparse, hashlib, json, statistics
from pathlib import Path
P = Path(__file__).resolve().parent
ap = argparse.ArgumentParser(); ap.add_argument('--results', default=str(P/'results')); args=ap.parse_args()
R = Path(args.results)
env = json.loads((R/'environment.json').read_text())
assert env['run_sha256'] == hashlib.sha256((P/'run.py').read_bytes()).hexdigest()
assert json.loads((R/'completion.json').read_text())['completed']
rows = [json.loads(line) for rank in range(4) for line in (R/f'rank{rank}.jsonl').read_text().splitlines()]
assert len(rows) == len(env['plan'])*4 == 780
assert len({r['pid'] for r in rows}) == 4
out=[]
for index, plan in enumerate(env['plan']):
    group = sorted([r for r in rows if r['index']==index], key=lambda r:r['rank'])
    assert [r['rank'] for r in group] == list(range(4))
    n, d, trial, warmup = plan
    for r in group:
        assert [r['bytes'],r['requested_delay_s'],r['trial'],r['warmup']] == plan
        assert r['correct'] and r['minimum']==r['maximum']==10+4*(trial%13)
        assert r['start_ns'] <= r['ready_ns'] <= r['done_ns']
    origin=min(r['start_ns'] for r in group)
    earliest=min(group,key=lambda r:r['ready_ns']); latest=max(group,key=lambda r:r['ready_ns'])
    end=max(r['done_ns'] for r in group)
    out.append(dict(index=index,bytes=n,delay_s=d,trial=trial,warmup=warmup,
                    completion_ms=(end-origin)/1e6,
                    arrival_spread_ms=(latest['ready_ns']-earliest['ready_ns'])/1e6,
                    post_last_arrival_ms=(end-latest['ready_ns'])/1e6,
                    first_arriver_api_ms=(earliest['done_ns']-earliest['ready_ns'])/1e6,
                    last_arriver_api_ms=(latest['done_ns']-latest['ready_ns'])/1e6,
                    first_rank=earliest['rank'],last_rank=latest['rank'],
                    ranks=[dict(rank=r['rank'],start_ms=(r['start_ns']-origin)/1e6,
                                ready_ms=(r['ready_ns']-origin)/1e6,done_ms=(r['done_ns']-origin)/1e6) for r in group]))
summary=[]
keys=['completion_ms','arrival_spread_ms','post_last_arrival_ms','first_arriver_api_ms','last_arriver_api_ms']
for n in env['sizes_bytes']:
    for d in env['delays_s']:
        g=[r for r in out if not r['warmup'] and r['bytes']==n and r['delay_s']==d]
        assert len(g)==20
        summary.append(dict(bytes=n,delay_s=d,count=len(g),**{k:dict(median=statistics.median(r[k] for r in g),minimum=min(r[k] for r in g),maximum=max(r[k] for r in g)) for k in keys}))
(R/'groups.json').write_text(json.dumps(out,indent=2)+'\n')
(R/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print('Verified 780 rank results, 195 groups including 15 warmup groups.')
for s in summary:
    print(s['bytes'],s['delay_s'],*[round(s[k]['median'],3) for k in keys])
