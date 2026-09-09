import hashlib,json,sqlite3
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def union_ns(intervals):
    total=0;left=right=None
    for a,b in sorted(intervals):
        if right is None:left,right=a,b
        elif a<=right:right=max(right,b)
        else:total+=right-left;left,right=a,b
    return total+(right-left if right is not None else 0)
reports=[]
baseline=json.loads((ROOT/'results/paired-eager-v1/raw.json').read_text())
for mode in ['native','schedule']:
    path=ROOT/'profiles'/mode;run=json.loads((path/'run.json').read_text())
    for f,h in run['source_hashes'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
    assert run['request']['output_ids']==next(r['output_ids'] for r in baseline['requests'] if r['phase']=='measure' and r['mode']==mode)
    connection=sqlite3.connect(f'file:{path}.sqlite?mode=ro',uri=True);connection.row_factory=sqlite3.Row
    strings=dict(connection.execute('select id,value from StringIds'))
    outer=list(connection.execute("select start,end,text from NVTX_EVENTS where text like 'replacement-%'"));assert len(outer)==1
    start,end,label=outer[0]
    steps=[dict(r) for r in connection.execute("select start,end,text,globalTid from NVTX_EVENTS where text like 'model-step-%' order by start")]
    assert len(steps)==run['steps'][0]['model_steps']
    tables={r[0] for r in connection.execute("select name from sqlite_master where type='table'")}
    apis=defaultdict(list)
    for table in ['CUPTI_ACTIVITY_KIND_RUNTIME','CUPTI_ACTIVITY_KIND_DRIVER']:
        if table not in tables:continue
        for r in connection.execute(f'select * from {table} where start>=? and end<=?',(start,end)):
            apis[(r['globalTid']>>24,r['correlationId'])].append(dict(r))
    kernels=[]
    for r in connection.execute('select * from CUPTI_ACTIVITY_KIND_KERNEL where start>=? and end<=? order by start',(start,end)):
        title=strings[r['demangledName']]
        launch=apis[(r['globalPid']>>24,r['correlationId'])]
        matching={i for a in launch for i,s in enumerate(steps) if a['globalTid']==s['globalTid'] and s['start']<=a['start']<s['end']}
        assert len(matching)<=1
        step=next(iter(matching)) if matching else None
        swiglu=('act_and_mul_kernel' in title and 'silu_kernel' in title) if mode=='native' else title=='kernel'
        category='swiglu' if swiglu else 'attention' if 'attention' in title or 'reduce_segments' in title else 'cache_write' if 'reshape_and_cache' in title else 'other'
        kernels.append(dict(start_ns=r['start'],end_ns=r['end'],name=title,stream=r['streamId'],step=step,category=category,
            correlation_id=r['correlationId'],launch_matches=len(launch),registers_per_thread=r['registersPerThread']))
    copies=[]
    for table in ['CUPTI_ACTIVITY_KIND_MEMCPY','CUPTI_ACTIVITY_KIND_MEMSET']:
        if table in tables:copies.extend(dict(r) for r in connection.execute(f'select start,end from {table} where start>=? and end<=?',(start,end)))
    phase_rows=[]
    for i,s in enumerate(steps):
        group=[k for k in kernels if k['step']==i];hot=[k for k in group if k['category']=='swiglu']
        phase_rows.append(dict(step=i,nvtx=s,kernel_count=len(group),swiglu_count=len(hot),
            kernel_sum_ms=sum(k['end_ns']-k['start_ns'] for k in group)/1e6,
            swiglu_sum_ms=sum(k['end_ns']-k['start_ns'] for k in hot)/1e6,
            gpu_first_ns=min((k['start_ns'] for k in group),default=None),gpu_last_ns=max((k['end_ns'] for k in group),default=None)))
    hot=[k for k in kernels if k['category']=='swiglu']
    assert len(hot)==36*32,(mode,len(hot),sorted({k['name'] for k in kernels})[:20])
    assert [r['swiglu_count'] for r in phase_rows if r['kernel_count']]==[36]*32
    assert all(k['step'] is not None for k in hot)
    assert all(k['launch_matches']>0 for k in kernels)
    hot_intervals=[(k['start_ns'],k['end_ns']) for k in hot]
    other_intervals=[(k['start_ns'],k['end_ns']) for k in kernels if k['category']!='swiglu']+[(c['start'],c['end']) for c in copies]
    overlap_ms=(union_ns(hot_intervals)+union_ns(other_intervals)-union_ns(hot_intervals+other_intervals))/1e6
    grouped=defaultdict(lambda:dict(count=0,sum_ms=0))
    for k in kernels:
        grouped[k['category']]['count']+=1;grouped[k['category']]['sum_ms']+=(k['end_ns']-k['start_ns'])/1e6
    active=union_ns([(k['start_ns'],k['end_ns']) for k in kernels]+[(c['start'],c['end']) for c in copies])/1e6
    hot_ms=sum(k['end_ns']-k['start_ns'] for k in hot)/1e6;range_ms=(end-start)/1e6
    reports.append(dict(mode=mode,range_ms=range_ms,client_profiled_ms=run['request']['elapsed_s']*1000,
        kernel_count=len(kernels),kernel_sum_ms=sum(k['end_ns']-k['start_ns'] for k in kernels)/1e6,
        observed_gpu_activity_union_ms=active,range_without_observed_gpu_activity_ms=range_ms-active,
        swiglu_sum_ms=hot_ms,swiglu_fraction_of_range=hot_ms/range_ms,
        conditional_zero_cost_swiglu_speedup=range_ms/(range_ms-hot_ms),
        categories=dict(grouped),steps=phase_rows,kernels=kernels,
        kernels_outside_execute_model=sum(k['step'] is None for k in kernels),swiglu_overlap_other_observed_gpu_ms=overlap_ms,swiglu_streams=sorted({k['stream'] for k in hot}),sqlite_sha256=hashlib.sha256(Path(str(path)+'.sqlite').read_bytes()).hexdigest()))
    connection.close()
result=dict(status='passed',reports=reports,
    scope='Two instrumented requests, not latency benchmark repetitions. Phase uses same-thread CUDA launch correlation inside execute_model NVTX ranges. Last empty host call is retained. GPU gaps are unclassified and cannot be labeled CPU bottleneck from this trace alone. Conditional zero-cost bound holds other time fixed and uses summed hotspot time, not a validated critical-path counterfactual.')
(ROOT/'profiles/analysis.json').write_text(json.dumps(result,indent=2)+'\n')
for r in reports:print(json.dumps({k:v for k,v in r.items() if k not in ['kernels','steps']},indent=2));print('steps',[(s['step'],s['kernel_count'],s['swiglu_count'],round(s['swiglu_sum_ms'],4)) for s in r['steps']])
