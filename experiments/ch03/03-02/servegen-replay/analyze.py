"""Audit realized arrivals/completions; no queue simulation or nominal-rate fit."""
import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent;P=ROOT/'results/replay-v1'
def lines(name):return [json.loads(s) for s in (P/name).read_text().splitlines()]
def p95(values):return sorted(values)[math.ceil(.95*len(values))-1]
env=json.loads((P/'environment.json').read_text());assert env['status']=='passed'
for f,h in env['source_hashes'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
provenance=json.loads((ROOT/'input-provenance.json').read_text())
assert hashlib.sha256((ROOT/'source-requests.json').read_bytes()).hexdigest()==provenance['source_sha256']
source=json.loads((ROOT/'source-requests.json').read_text());assert len(source)==480
workloads=json.loads((ROOT/'workloads.json').read_text());inputs=json.loads((ROOT/'inputs.json').read_text());stats=lines('scheduler.jsonl');reports=[];outputs={}
for mode,expected in workloads.items():
    rows=lines(f'{mode}-requests.jsonl');dispatch=lines(f'{mode}-dispatch.jsonl');assert len(rows)==len(dispatch)==480
    assert sorted(r['index'] for r in rows)==sorted(r['index'] for r in dispatch)==list(range(480))
    mapping={r['index']:r for r in rows}
    for d in dispatch:
        assert d['actual_dispatch_s']==mapping[d['index']]['actual_dispatch_s']
        assert abs(d['lag_s']-(d['actual_dispatch_s']-d['arrival_s']))<1e-9
    assert [r['arrival_s'] for r in expected]==[r['timestamp'] for r in source]
    assert sorted((int(r['kind']),r['input_tokens'],r['output_tokens']) for r in expected)==[(r['request_id'],r['data']['input_tokens'],r['data']['output_tokens']) for r in source]
    delays=[];latency=[];ttft=[];waits=[];diff=[]
    for specification in expected:
        r=mapping[specification['index']]
        for k,v in specification.items():assert r[k]==v
        ids=inputs[r['kind']][r['task_index']];assert len(ids)==r['input_tokens']
        assert hashlib.sha256(json.dumps(ids).encode()).hexdigest()==r['input_sha256']
        assert len(r['output_ids'])==r['output_tokens'] and r['cached_tokens'] in [0,None]
        events=r['events'];assert events[-1][1]==r['output_tokens']
        assert all(a[0]<=b[0] and a[1]<=b[1] for a,b in zip(events,events[1:]))
        first=next(e[0] for e in events if e[1]>0)
        delays.append(r['actual_dispatch_s']-r['arrival_s']);latency.append(r['end_s']-r['actual_dispatch_s']);ttft.append(first-r['actual_dispatch_s'])
        wait=r['metrics']['scheduled_ts']-r['metrics']['queued_ts'];assert wait>=0;waits.append(wait)
        key=(r['kind'],r['task_index'])
        if mode=='original':outputs[key]=r['output_ids']
        elif outputs[key]!=r['output_ids']:diff.append(dict(kind=r['kind'],task_index=r['task_index']))
    bins=[dict(start_s=t,end_s=t+10,dispatched=sum(t<=r['actual_dispatch_s']<t+10 for r in rows),completed=sum(t<=r['end_s']<t+10 for r in rows),outstanding_at_end=sum(r['actual_dispatch_s']<=t+10<r['end_s'] for r in rows)) for t in range(0,120,10)]
    sampled=[s for s in stats if s['case']==mode];assert sampled
    complete=next(c for c in env['cases'] if c['mode']==mode);assert complete['completed']==480
    reports.append(dict(mode=mode,latency_p95_s=p95(latency),ttft_p95_s=p95(ttft),initial_queue_wait_p95_s=p95(waits),
        dispatch_lag_p95_s=p95(delays),dispatch_lag_max_s=max(delays),last_dispatch_s=max(r['actual_dispatch_s'] for r in rows),
        final_completion_s=max(r['end_s'] for r in rows),drain_after120_s=max(0,max(r['end_s'] for r in rows)-120),
        outstanding_at120=sum(r['actual_dispatch_s']<=120<r['end_s'] for r in rows),
        sampled_waiting_peak=max(s['waiting'] for s in sampled),sampled_running_peak=max(s['running'] for s in sampled),
        sampled_kv_usage_peak=max(s['kv_usage'] for s in sampled),preemptions=complete['preemptions'],ten_second_windows=bins,
        differing_outputs_from_original=diff))
result=dict(status='passed',reports=reports,
    scope='960 real requests from pinned ServeGen lengths and arrivals; original vs intact-pair temporal permutation, one run each. Synthetic valid tokens, forced output length, no quality or production prefix claim. Nearest-rank p95; initial queue only; sampled occupancy.')
(ROOT/'results/summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
