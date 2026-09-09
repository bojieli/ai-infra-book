"""Audit realized arrivals/completions; no queue simulation or nominal-rate fit."""
import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent;P=ROOT/'results/arrival-v1'
def lines(name):return [json.loads(s) for s in (P/name).read_text().splitlines()]
def p95(values):return sorted(values)[math.ceil(.95*len(values))-1]
env=json.loads((P/'environment.json').read_text());assert env['status']=='passed'
for f,h in env['source_hashes'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
workloads=json.loads((ROOT/'workloads.json').read_text());inputs=json.loads((ROOT/'inputs.json').read_text());stats=lines('scheduler.jsonl');reports=[];outputs={}
for mode,expected in workloads.items():
    rows=lines(f'{mode}-requests.jsonl');dispatch=lines(f'{mode}-dispatch.jsonl');assert len(rows)==len(dispatch)==480
    assert sorted(r['index'] for r in rows)==sorted(r['index'] for r in dispatch)==list(range(480))
    mapping={r['index']:r for r in rows}
    for d in dispatch:
        assert d['actual_dispatch_s']==mapping[d['index']]['actual_dispatch_s']
        assert abs(d['lag_s']-(d['actual_dispatch_s']-d['arrival_s']))<1e-9
    delays=[];latency=[];ttft=[];waits=[];diff=[]
    for specification in expected:
        r=mapping[specification['index']]
        for k,v in specification.items():assert r[k]==v
        ids=inputs[r['kind']][r['task_index']];assert len(ids)==(8192 if r['kind']=='A' else 1024)
        assert hashlib.sha256(json.dumps(ids).encode()).hexdigest()==r['input_sha256']
        assert len(r['output_ids'])==r['output_tokens'] and r['cached_tokens'] in [0,None]
        events=r['events'];assert events[-1][1]==r['output_tokens']
        assert all(a[0]<=b[0] and a[1]<=b[1] for a,b in zip(events,events[1:]))
        first=next(e[0] for e in events if e[1]>0)
        delays.append(r['actual_dispatch_s']-r['arrival_s']);latency.append(r['end_s']-r['actual_dispatch_s']);ttft.append(first-r['actual_dispatch_s'])
        wait=r['metrics']['scheduled_ts']-r['metrics']['queued_ts'];assert wait>=0;waits.append(wait)
        key=(r['kind'],r['task_index'])
        if mode=='uniform':outputs[key]=r['output_ids']
        elif outputs[key]!=r['output_ids']:diff.append(dict(kind=r['kind'],task_index=r['task_index']))
    bins=[dict(start_s=t,end_s=t+10,dispatched=sum(t<=r['actual_dispatch_s']<t+10 for r in rows),completed=sum(t<=r['end_s']<t+10 for r in rows),outstanding_at_end=sum(r['actual_dispatch_s']<=t+10<r['end_s'] for r in rows)) for t in range(0,120,10)]
    groups=[]
    for window in [0,1]:
        subset=[r for r in rows if window*60<=r['arrival_s']<(window+1)*60]
        a=sum(r['kind']=='A' for r in subset);b=len(subset)-a
        assert (a,b)==((120,120) if mode=='uniform' else (216,24) if window==0 else (24,216))
        groups.append(dict(planned_window=window,A=a,B=b,
            actual_dispatches_in_window=sum(window*60<=r['actual_dispatch_s']<(window+1)*60 for r in rows),
            completed_at_window_end=sum(r['end_s']<=(window+1)*60 for r in rows)))
    sampled=[s for s in stats if s['case']==mode];assert sampled
    complete=next(c for c in env['cases'] if c['mode']==mode);assert complete['completed']==480
    reports.append(dict(mode=mode,latency_p95_s=p95(latency),ttft_p95_s=p95(ttft),initial_queue_wait_p95_s=p95(waits),
        dispatch_lag_p95_s=p95(delays),dispatch_lag_max_s=max(delays),last_dispatch_s=max(r['actual_dispatch_s'] for r in rows),
        final_completion_s=max(r['end_s'] for r in rows),drain_after120_s=max(0,max(r['end_s'] for r in rows)-120),
        outstanding_at120=sum(r['actual_dispatch_s']<=120<r['end_s'] for r in rows),
        sampled_waiting_peak=max(s['waiting'] for s in sampled),sampled_running_peak=max(s['running'] for s in sampled),
        sampled_kv_usage_peak=max(s['kv_usage'] for s in sampled),preemptions=complete['preemptions'],windows=groups,ten_second_windows=bins,
        differing_outputs_from_uniform=diff))
result=dict(status='passed',reports=reports,
    scope='960 real requests with fixed output work. Nearest-rank p95 over480 requests per case; one run each. Queue wait is initial scheduled minus queued timestamps and excludes subsequent preemption waits. KV/running/waiting peaks sampled at10Hz plus preemption events. Same request multiset; chronological request mixture differs. Synthetic repeated token prompts, not ServeGen sampled clients or quality workload.')
(ROOT/'results/summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
