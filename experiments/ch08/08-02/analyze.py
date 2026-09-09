"""Validate and summarize raw AsyncLLM output delivery records."""
import argparse
import json
import math
from pathlib import Path
import statistics


def main():
    p=argparse.ArgumentParser()
    p.add_argument('directory',type=Path)
    args=p.parse_args()
    root=args.directory
    env=json.loads((root/'environment.json').read_text())
    requests={r['id']:r for r in json.loads((root/'requests.json').read_text())}
    groups={}
    for line in (root/'events.jsonl').read_text().splitlines():
        e=json.loads(line)
        groups.setdefault((e['trial'],e['id']),[]).append(e)
    assert len(groups)==env['completed_trials']*len(requests)
    rows=[]
    for (trial,rid),events in sorted(groups.items()):
        r=requests[rid]
        assert events[-1]['finished']
        assert events[-1]['finish_reason']=='length'
        assert sum(len(e['new_token_ids']) for e in events)==r['max_tokens']
        previous=0
        for e in events:
            previous+=len(e['new_token_ids'])
            assert e['cumulative_tokens']==previous
        active=[e for e in events if e['new_token_ids']]
        times=[e['delivered_s'] for e in active]
        assert times==sorted(times)
        deltas=[b-a for a,b in zip(times,times[1:])]
        rows.append(dict(trial=trial,id=rid,kind=r['kind'],prompt_tokens=len(r['prompt_token_ids']),
                         output_tokens=r['max_tokens'],arrival_lateness_ms=1000*(events[0]['submitted_s']-r['arrival_s']),
                         delivered_ttft_ms=1000*(times[0]-events[0]['submitted_s']),
                         delivered_e2e_ms=1000*(times[-1]-events[0]['submitted_s']),
                         median_output_event_gap_ms=1000*statistics.median(deltas) if deltas else None,
                         multi_token_events=sum(len(e['new_token_ids'])>1 for e in active),
                         output_token_ids=[t for e in active for t in e['new_token_ids']]))
        m=events[-1].get('engine_request_metrics')
        if m:
            assert 0<m['queued_ts']<=m['scheduled_ts']<=m['first_token_ts']<=m['last_token_ts']
            assert m['num_generation_tokens']==r['max_tokens']
            rows[-1].update(engine_queue_ms=1000*(m['scheduled_ts']-m['queued_ts']),
                            engine_prefill_ms=1000*(m['first_token_ts']-m['scheduled_ts']),
                            engine_mean_tpot_ms=1000*(m['last_token_ts']-m['first_token_ts'])/(r['max_tokens']-1))
    result=dict(scope='Client-side AsyncLLM delivery; event gaps are not engine token execution times or scheduler queue waiting.',requests=rows)
    if (root/'engine-stats.jsonl').exists():
        stats=[json.loads(line) for line in (root/'engine-stats.jsonl').read_text().splitlines()]
        sched=[s['scheduler'] for s in stats if s['scheduler']]
        finished=[r for s in stats if s['iteration'] for r in s['iteration']['finished_requests']
                  if (r['request_id'] or '').startswith('t')]
        assert len(finished)==len(rows)
        assert all(r['num_cached_tokens']==0 for r in finished)
        first_arrival=min(e['engine_request_metrics']['arrival_time']
                          for events in groups.values() for e in events
                          if e.get('engine_request_metrics'))
        iterations=[s['iteration'] for s in stats if s['iteration'] and
                    s['iteration']['iteration_timestamp']>=first_arrival]
        itl=[v for s in iterations for v in s['inter_token_latencies_iter']]
        expected_itl=sum(r['max_tokens']-1 for r in requests.values())*env['completed_trials']
        assert len(itl)==expected_itl,(len(itl),expected_itl)
        assert all(v>=0 for v in itl)
        total_decode=sum(e[-1]['engine_request_metrics']['last_token_ts']-
                         e[-1]['engine_request_metrics']['first_token_ts'] for e in groups.values())
        assert math.isclose(sum(itl),total_decode,rel_tol=1e-9,abs_tol=1e-7)
        ordered=sorted(itl)
        percentile=lambda q:1000*ordered[math.ceil(q*len(ordered))-1]
        result['engine']=dict(finished_requests=finished,
            inter_token_intervals_s=itl,
            itl_summary=dict(count=len(itl),median_ms=statistics.median(itl)*1000,
                             p95_ms=percentile(.95),p99_ms=percentile(.99),max_ms=max(itl)*1000,
                             percentile_method='nearest rank',
                             scope='EngineCore output timestamp differences per request, excluding first token and warmup; pooled over three trials. No speculation, exactly one engine token per step as checked by total interval count.'),
            observed_peak_kv_usage_fraction=max(s['kv_cache_usage'] for s in sched),
            observed_peak_waiting_requests=max(s['num_waiting_reqs'] for s in sched),
            kv_scope='Scheduler-reported occupied KV block fraction sampled at engine output updates, includes warmup; not total VRAM or allocation peak.')
    (root/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    for r in rows:
        print(f"trial={r['trial']} {r['id']} TTFT={r['delivered_ttft_ms']:.2f}ms E2E={r['delivered_e2e_ms']:.2f}ms merged_events={r['multi_token_events']}")


if __name__=='__main__':
    main()
