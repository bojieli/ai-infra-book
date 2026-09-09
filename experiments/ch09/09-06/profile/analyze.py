"""Audit native outputs and summarize raw profiler events without phase guesses."""
import collections,gzip,hashlib,json,sys
from pathlib import Path
import numpy as np
B=Path(__file__).absolute().parent
O=Path(sys.argv[1]) if len(sys.argv)>1 else B/'results';O.mkdir(parents=True,exist_ok=True)
root=B/'runs/trace-001';out=root/'output'
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(l) for l in p.read_text().splitlines()]
sup=read(root/'supervisor.json');assert sup['exit_code']==0 and sup['reason'] is None and not sup['leftovers']
assert read(out/'environment.json')['driver_sha256']==hashlib.sha256((B/'run.py').read_bytes()).hexdigest()
old=rows(B/'reference/requests.jsonl');new=rows(out/'requests.jsonl');assert len(old)==len(new)==4
quality=[]
for a,b in zip(old,new):
    assert a['id']==b['id'] and a['prompt_ids']==b['prompt_ids']
    assert a['output_ids']==b['output_ids'] and a['text']==b['text'] and a['finish_reason']==b['finish_reason']=='stop'
    x=np.load(B/'reference'/a['route_file'],allow_pickle=False);y=np.load(out/b['route_file'],allow_pickle=False)
    assert np.array_equal(x,y)
    quality.append(dict(id=a['id'],output_ids_exact=True,route_ids_exact=True,route_shape=list(y.shape)))
traces=[]
for p in sorted((out/'traces').glob('*.json.gz')):
    with gzip.open(p,'rt') as f:trace=json.load(f)
    cats=collections.Counter();kernels={};moe_cpu={};count=0;start=None;end=None
    for e in trace['traceEvents']:
        count+=1;cat=e.get('cat','');cats[cat]+=1
        if e.get('ph')!='X':continue
        duration=e.get('dur',0)
        assert duration>=0
        if cat=='kernel':
            name=e['name'];r=kernels.setdefault(name,dict(count=0,sum_duration_us=0));r['count']+=1;r['sum_duration_us']+=duration
            start=e['ts'] if start is None else min(start,e['ts']);end=e['ts']+duration if end is None else max(end,e['ts']+duration)
        elif cat=='cpu_op' and any(word in e.get('name','').lower() for word in ['moe','expert','dispatch','combine']):
            r=moe_cpu.setdefault(e['name'],dict(count=0,sum_duration_us=0));r['count']+=1;r['sum_duration_us']+=duration
    traces.append(dict(file=str(p.relative_to(B)),compressed_bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        events=count,categories=dict(cats),kernel_count=sum(v['count'] for v in kernels.values()),
        kernel_sum_duration_us=sum(v['sum_duration_us'] for v in kernels.values()),
        kernel_first_ts=start,kernel_last_end_ts=end,kernels=kernels,moe_named_cpu_ops=moe_cpu,
        trace_schema=trace.get('schemaVersion'),device_properties=trace.get('deviceProperties')))
    del trace
resources=rows(root/'resources.jsonl')
j=dict(quality=quality,traces=traces,resources=dict(wall_s=sup['wall_s'],gpu_peak_mib=max(x['gpu_mib'] for x in resources),rss_sum_peak_bytes=max(x['rss_bytes'] for x in resources)),
    limitations=['Profiler changes execution timing; includes export in guard wall time.',
                 'CPU operator scopes can nest; their durations must not be added as disjoint phases.',
                 'Kernel duration sums may overlap across streams; not elapsed time or utilization.',
                 'Name matches do not prove dispatch/GEMM/combine attribution. No multi-device communication measurement.'])
(O/'analysis.json').write_text(json.dumps(j,indent=2)+'\n')
print(json.dumps(dict(quality_pairs=len(quality),traces=[{k:t[k] for k in ['events','kernel_count','kernel_sum_duration_us','compressed_bytes']} for t in traces])))
