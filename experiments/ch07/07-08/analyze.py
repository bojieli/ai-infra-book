"""Reconstruct actual job durations and communication-phase drift."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics

def median(values):return statistics.median(values)
def quantile(values,q):
    values=sorted(values);pos=(len(values)-1)*q;lo=int(pos)
    return values[lo]+(values[min(lo+1,len(values)-1)]-values[lo])*(pos-lo)
def union(intervals):
    out=[]
    for begin,end in sorted(intervals):
        if out and begin<=out[-1][1]:out[-1][1]=max(out[-1][1],end)
        else:out.append([begin,end])
    return out
def intersect(a,b):
    i=j=0;total=0
    while i<len(a) and j<len(b):
        total+=max(0,min(a[i][1],b[j][1])-max(a[i][0],b[j][0]))
        if a[i][1]<b[j][1]:i+=1
        else:j+=1
    return total

def main(args):
    root=args.run;spec=json.loads((root/'protocol.json').read_text())
    completions=json.loads((root/'completion.json').read_text());results=[];checks=0
    for sup in completions:
        assert sup['reason'] is None and all(x==0 for x in sup['exit_codes']);checks+=1
        run=root/f'r{sup["rep"]}-{sup["condition"]}';jobs=[]
        for job in sup['jobs']:
            ranks=[]
            for rank in range(2):
                p=run/f'job{job}-rank{rank}'
                c=json.loads((p/'completion.json').read_text());steps=json.loads((p/'steps.json').read_text())
                comm=json.loads((p/'collectives.json').read_text())
                assert len(steps)==c['steps']==spec['steps'];checks+=1
                for i,s in enumerate(steps):
                    assert s['step']==i and c['start_ns']<=s['begin_ns']<=s['forward_ns']<=s['backward_ns']<=s['optimizer_ns']<=s['end_ns']<=c['end_ns'];checks+=1
                    events=[e for e in comm if e['step']==i]
                    assert events;checks+=1
                    for e in events:
                        assert s['backward_ns']<=e['begin_ns']<=e['future_done_ns']<=e['averaged_ns']<=s['optimizer_ns'];checks+=1
                    assert sum(e['bytes'] for e in events)==c['parameter_count']*4;checks+=1
                ranks.append(dict(completion=c,steps=steps,comm=comm))
            periods=[(b['begin_ns']-a['begin_ns'])/1e6 for a,b in zip(ranks[0]['steps'],ranks[0]['steps'][1:])]
            first_comm=[min(e['begin_ns'] for e in ranks[0]['comm'] if e['step']==s) for s in range(spec['steps'])]
            jobs.append(dict(job=job,start_ns=min(r['completion']['start_ns'] for r in ranks),
                end_ns=max(r['completion']['end_ns'] for r in ranks),
                rank0_step_period_ms=periods,period_median_ms=median(periods),
                period_p10_ms=quantile(periods,.1),period_p90_ms=quantile(periods,.9),
                rank0_first_comm_ns=first_comm,
                rank0_comm_union_ns=union([(e['begin_ns'],e['future_done_ns']) for e in ranks[0]['comm']]),
                rank0_losses=[s['loss'] for s in ranks[0]['steps']]))
        result=dict(rep=sup['rep'],condition=sup['condition'],jobs=jobs,release_ns=sup['release_ns'],
                    completion_from_release_ms=(max(j['end_ns'] for j in jobs)-sup['release_ns'])/1e6,
                    active_span_ms=(max(j['end_ns'] for j in jobs)-min(j['start_ns'] for j in jobs))/1e6)
        if len(jobs)==2:
            a,b=jobs
            result['start_skew_ms']=(b['start_ns']-a['start_ns'])/1e6
            result['same_step_comm_phase_delta_ms']=[(y-x)/1e6 for x,y in zip(a['rank0_first_comm_ns'],b['rank0_first_comm_ns'])]
            result['rank0_comm_interval_overlap_ms']=intersect(a['rank0_comm_union_ns'],b['rank0_comm_union_ns'])/1e6
        results.append(result)
    pairs=[]
    for rep in range(spec['repetitions']):
        entries={r['condition']:r for r in results if r['rep']==rep}
        pairs.append(dict(rep=rep,aligned_ms=entries['aligned']['completion_from_release_ms'],
             offset_ms=entries['offset-50ms']['completion_from_release_ms'],
             offset_over_aligned=entries['offset-50ms']['completion_from_release_ms']/entries['aligned']['completion_from_release_ms']))
    out=dict(checks=checks,results=results,pairs=pairs,
             median_offset_over_aligned=median(x['offset_over_aligned'] for x in pairs),
             scope='actual CPU DDP/Gloo loopback; callback intervals are not physical wire traffic or switch queue',
             phase_definition='job B minus A first rank-0 collective entry at same training-step index; no modulo or nearest-event matching')
    args.out.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'checks':checks,'pairs':pairs,'median_offset_over_aligned':out['median_offset_over_aligned']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
