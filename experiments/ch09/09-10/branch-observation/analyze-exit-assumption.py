"""Standalone standard-library analysis of original events; never infer hit from gets."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    plan=read(R/'results/plan.json');base=read(R/'baseline.json');config=read(R/'config.json');ref=read(R/'reference.json');source=read(R/'source-manifest.json')
    for f,h in plan['source_sha256'].items():assert sha(R/f)==h,f
    for f,h in base['sha256'].items():assert sha(R/f)==h,f
    assert read(R/'results/source-after.json')==source['sha256']
    assert read(R/'results/execution.json')['status']=='completed'
    assert read(R/'controller-exit.json')['exit_code']==0
    groups=[];chains=[];key_evidence=[]
    for c in plan['order']:
        name=f"{c['trial']}-native-{c['count']}";out=R/'results'/name
        coord=read(out/'coordinator.json');assert coord['exit_code']==0 and coord['error'] is None
        info=read(out/'server-info.json')
        for k,v in config.items():assert info[k]==v,(name,k)
        assert info['max_total_num_tokens']==4096
        assert info['internal_states'] and all(s['memory_usage']['token_capacity']==4096 for s in info['internal_states'])
        prep=read(out/'cache-preparation.json');assert prep['files_verified']==65 and prep['manifest_sha256']==sha(R/'cache-manifest.json')
        rows=read(out/'requests.json');assert len(rows)==c['count'] and sorted(r['index'] for r in rows)==list(range(c['count']))
        owned={int(k) for k in read(out/'owned-processes.json')['processes']}
        events=[]
        for p in out.glob('events.*.jsonl'):
            seq=0
            for line in p.open():
                e=json.loads(line);assert e['seq']==seq+1;seq=e['seq'];events.append(e)
        events.sort(key=lambda e:(e['monotonic_ns'],e['pid'],e['seq']))
        installed={e['pid'] for e in events if e['event']=='installed'}
        assert installed and installed<=owned
        for pid in installed:
            assert any(e['event']=='observer_exit' and e['pid']==pid for e in events), ('Missing clean observer exit',pid)
        for e in events:
            assert e['pid'] in installed
            if e['event']=='installed':assert e['source_sha256']==source['sha256'] and e['observer_sha256']==sha(R/'observer.py')
        trace=[e for e in events if e['event']=='trace'];assert trace
        assert not [e for e in trace if e['phase']=='exception'], 'Observed exception requires inspection'
        assert read(out/'release-wait.json')[-1]['live']==[] and read(out/'release-wait.json')[-1]['gpu_pids']==[]
        peak=max(x['own_MiB'] for x in read(out/'resource-samples.json'));assert peak<=24576
        first=min(rows,key=lambda x:x['end_s']);api_id=first['response']['meta_info'].get('id')
        for row in sorted(rows,key=lambda x:x['end_s']):
            rid=row['request_id'];meta=row['response']['meta_info']
            assert row['output_ids']==ref['output_ids'] and row['response']['text']==ref['text'] and row['passed']
            assert len(row['output_ids'])==16
            reqevents=[e for e in trace if e.get('request_id')==rid]
            returns=[e for e in reqevents if e['phase']=='return']
            rate=[e for e in returns if e['method']=='prefetch_rate_limited']
            progress=[e for e in returns if e['method']=='check_prefetch_progress']
            prefetch=[e for e in returns if e['method']=='prefetch_from_storage']
            pop=[e for e in returns if e['method']=='pop_prefetch_loaded_tokens']
            init=[e for e in returns if e['method']=='init_next_round_input']
            batch=[e for e in trace if e['method']=='prepare_for_extend' and e['phase'] in ('call','return') and any(r['rid']==rid for r in e.get('batch_reqs',[]))]
            def point(e):return {'pid':e['pid'],'seq':e['seq'],'monotonic_ns':e['monotonic_ns'],'line':e['line'],'method':e['method'],'phase':e['phase']}
            chain=dict(group=name,rid=rid,api_id=meta.get('id'),exact_api_association=meta.get('id')==rid,first_completed=row is first,cached_tokens=meta.get('cached_tokens'),cached_tokens_details=meta.get('cached_tokens_details'),completed_ns=int(row['end_s']*1e9),rate=[dict(**point(e),limited=e['return'],controller=e['controller']) for e in rate],prefetch=[dict(**point(e),ongoing_present=e.get('ongoing_present'),operation=e.get('ongoing_operation')) for e in prefetch],progress=[dict(**point(e),result=e['return'],ongoing_present=e.get('ongoing_present'),locals=e['locals']) for e in progress],pop=[dict(**point(e),loaded=e['return']) for e in pop],init=[dict(**point(e),req=e.get('req')) for e in init],prefill=[dict(**point(e),req=next(r for r in e['batch_reqs'] if r['rid']==rid)) for e in batch])
            chain['evidence_complete']=bool(rate and prefetch and progress and pop and init and batch and chain['exact_api_association'])
            # A specific observed path, not a reconstruction from file IO.
            chain['observed_rate_skip_zero_prefill']=bool(chain['evidence_complete'] and any(e['return'] is True for e in rate) and any(e.get('ongoing_present') is False for e in prefetch) and any(e['line']==1361 and e['return'] is True for e in progress) and any(e['return']==0 for e in pop) and any(x['phase']=='call' and x['req']['prefix_indices_len']==0 and x['req']['host_hit_length']==0 for x in chain['prefill']))
            chains.append(chain)
        fc=next(x for x in chains if x['group']==name and x['first_completed'])
        # Retain actual storage prefix keys by request, without recounting gets.
        reqkeys={}
        for e in trace:
            op=e.get('operation') or e.get('ongoing_operation')
            if op and len(op.get('hash_value',[]))==64:
                reqkeys[op['request_id']]=op['hash_value']
        expected=1 if c['count']==1 else 4
        assert len(reqkeys)==expected,(name,reqkeys.keys())
        assert len({tuple(v) for v in reqkeys.values()})==1
        key_evidence.append(dict(group=name,request_hash_keys=reqkeys))
        if c['count']==8:
            assert fc['rid']=='native-4' and fc['observed_rate_skip_zero_prefill']
            prefill_ns=next(e['monotonic_ns'] for e in fc['prefill'] if e['phase']=='call')
            for i in range(4):
                other=next(x for x in chains if x['group']==name and x['rid']==f'native-{i}')
                assert any(e['result'] is False and e['line']==1374 and e['monotonic_ns']<prefill_ns for e in other['progress'])
            sequence=[fc['rate'][0]['monotonic_ns'],fc['prefetch'][0]['monotonic_ns'],fc['progress'][0]['monotonic_ns'],fc['pop'][0]['monotonic_ns'],prefill_ns,fc['completed_ns']]
            assert sequence==sorted(sequence),sequence
        groups.append(dict(**c,group=name,first_completed_rid=first['request_id'],first_api_id=api_id,first_cached_tokens=first['response']['meta_info'].get('cached_tokens'),first_observed_rate_skip_zero_prefill=fc['observed_rate_skip_zero_prefill'],evidence_complete=all(x['evidence_complete'] for x in chains if x['group']==name),installed_pids=sorted(installed),event_pids=sorted({e['pid'] for e in trace}),event_count=len(events),peak_gpu_MiB=peak,actual_pool_tokens=4096))
    assert len(chains)==18
    result=dict(status='passed',requests=len(chains),groups=groups,scope='Bounded branch observation only; timing perturbed by tracing; sealed experiments unchanged')
    (R/'prefix-key-evidence.json').write_text(json.dumps(key_evidence,indent=2)+'\n')
    (R/'request-chains.json').write_text(json.dumps(chains,indent=2)+'\n');(R/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
