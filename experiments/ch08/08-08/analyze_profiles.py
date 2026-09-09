import hashlib,json,sqlite3
from collections import defaultdict
from pathlib import Path
root=Path(__file__).parent;out=root/'profiles';reports=[]
for path,digest in json.loads((out/'native/manifest.json').read_text()).items():
    assert hashlib.sha256((out/'native'/Path(path).name).read_bytes()).hexdigest()==digest
for name in ['bf16','fp8']:
    run=json.loads((out/name/'run.json').read_text())
    for file,digest in run['sources'].items():assert hashlib.sha256((root/file).read_bytes()).hexdigest()==digest
    base=root/'results'/name
    assert run['input_sha256']==hashlib.sha256((base/'inputs.json').read_bytes()).hexdigest()
    baseline=json.loads((base/'kv-snapshots.json').read_text())['after_calibration'][0]
    assert run['kv_before'][0]['scales']==baseline['scales']==run['kv_after'][0]['scales']
    assert run['request']['prompt_tokens']==7239 and len(run['request']['output_ids'])==2
    cfg=json.loads((base/'environment.json').read_text())['config'];cfg['worker_extension_cls']='trace_probe.TraceProbe'
    assert run['config']==cfg
    c=sqlite3.connect(f'file:{out/name}.sqlite?mode=ro',uri=True);c.row_factory=sqlite3.Row
    strings=dict(c.execute('select id,value from StringIds'))
    ranges=list(c.execute("select start,end,text from NVTX_EVENTS where text like 'kv-%'"));assert len(ranges)==1
    start,end,label=ranges[0];assert end>start
    kernels=[]
    for k in c.execute('select start,end,demangledName,streamId from CUPTI_ACTIVITY_KIND_KERNEL where start>=? and end<=? order by start',(start,end)):
        title=strings[k['demangledName']]
        category='cache_write' if 'reshape_and_cache' in title else 'attention' if 'attention' in title or 'reduce_segments' in title else 'other'
        kernels.append(dict(start_ns=k['start'],end_ns=k['end'],name=title,stream=k['streamId'],category=category))
    assert kernels
    grouped=defaultdict(lambda:dict(count=0,total_kernel_us=0))
    for k in kernels:
        grouped[k['name']]['count']+=1;grouped[k['name']]['total_kernel_us']+=(k['end_ns']-k['start_ns'])/1000
    apis=[dict(start_ns=a['start'],end_ns=a['end'],name=strings[a['nameId']]) for a in c.execute('select start,end,nameId from CUPTI_ACTIVITY_KIND_RUNTIME where start>=? and end<=? order by start',(start,end))]
    tables={r[0] for r in c.execute("select name from sqlite_master where type='table'")}
    copies=[dict(x) for x in c.execute('select start,end,bytes,copyKind from CUPTI_ACTIVITY_KIND_MEMCPY where start>=? and end<=?',(start,end))] if 'CUPTI_ACTIVITY_KIND_MEMCPY' in tables else []
    cache=[k for k in kernels if k['category']=='cache_write'];attention=[k for k in kernels if k['category']=='attention']
    assert len(cache)==72
    q_quant=[k for k in kernels if 'scaled_fp8_quant' in k['name']]
    assert len(q_quant)==(72 if name=='fp8' else 0)
    reports.append(dict(name=name,label=label,range_start_ns=start,range_end_ns=end,range_ms=(end-start)/1e6,
        kernel_count=len(kernels),cache_write_count=len(cache),attention_count=len(attention),q_quant_count=len(q_quant),
        cache_kernel_sum_us=sum(k['end_ns']-k['start_ns'] for k in cache)/1000,
        attention_kernel_sum_us=sum(k['end_ns']-k['start_ns'] for k in attention)/1000,
        kernel_groups=dict(grouped),kernels=kernels,apis=apis,copies=copies))
    c.close()
(out/'analysis.json').write_text(json.dumps(dict(configurations=reports,scope='Nsight capture of one 7239-token prefill plus one decode step. Kernel sums are profiled durations, not exclusive wall time or DRAM bytes.'),indent=2)+'\n')
for r in reports:
    print(r['name'],r['kernel_count'],'cache',r['cache_write_count'],'attention',r['attention_count'])
    for k,v in r['kernel_groups'].items():
        if 'cache' in k or 'attention' in k or 'reduce_segments' in k:print(k,v)
