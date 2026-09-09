"""Associate GPU kernels with CPU MoE scopes via launch correlation, not GPU time containment."""
import bisect,collections,gzip,hashlib,json,sys
from pathlib import Path
B=Path(__file__).absolute().parent
O=Path(sys.argv[1]) if len(sys.argv)>1 else B/'results';O.mkdir(parents=True,exist_ok=True)
with gzip.open(B/'trace.json.gz','rt') as f:t=json.load(f)
events=t['traceEvents']
scopes=sorted([e for e in events if e.get('cat')=='cpu_op' and e.get('name')=='vllm::moe_forward' and e.get('ph')=='X'],key=lambda e:e['ts'])
assert len({(e['pid'],e['tid']) for e in scopes})==1
assert all(a['ts']+a['dur']<=b['ts']+.001 for a,b in zip(scopes,scopes[1:]))
starts=[e['ts'] for e in scopes];launches={};cpu_ops={}
reductions=sorted([e for e in events if e.get('cat')=='cpu_op' and e.get('name')=='_moe_C::moe_sum' and e.get('ph')=='X'],key=lambda e:e['ts'])
reduction_starts=[e['ts'] for e in reductions]
for e in events:
    if e.get('cat')=='cpu_op' and e.get('ph')=='X' and 'External id' in e.get('args',{}):
        external=e['args']['External id'];assert external not in cpu_ops;cpu_ops[external]=e
    if e.get('cat') in ['cuda_runtime','cuda_driver'] and e.get('ph')=='X' and 'correlation' in e.get('args',{}):
        c=e['args']['correlation'];assert c not in launches;launches[c]=e
groups=[[] for e in scopes];unassigned=0;matched=0
for e in events:
    if e.get('cat')!='kernel' or e.get('ph')!='X':continue
    launch=launches.get(e['args']['correlation']);assert launch is not None
    assert launch['args'].get('External id')==e['args'].get('External id')
    matched+=1;i=bisect.bisect_right(starts,launch['ts'])-1
    if i<0:unassigned+=1;continue
    s=scopes[i]
    if (launch['pid'],launch['tid'])!=(s['pid'],s['tid']) or launch['ts']>s['ts']+s['dur']:
        unassigned+=1;continue
    assert launch['ts']+launch['dur']<=s['ts']+s['dur']+.002
    op=cpu_ops[e['args']['External id']]
    assert (op['pid'],op['tid'])==(launch['pid'],launch['tid'])
    assert op['ts']-.002<=launch['ts'] and launch['ts']+launch['dur']<=op['ts']+op['dur']+.002
    reduction_id=None
    if op['name']=='aten::sum':
        ri=bisect.bisect_right(reduction_starts,launch['ts'])-1;assert ri>=0
        parent=reductions[ri]
        assert (parent['pid'],parent['tid'])==(launch['pid'],launch['tid'])
        assert s['ts']<=parent['ts']<=op['ts']+.002
        assert op['ts']+op['dur']<=parent['ts']+parent['dur']+.002<=s['ts']+s['dur']+.004
        reduction_id=parent['args']['External id']
    groups[i].append(dict(name=e['name'],duration_us=e['dur'],gpu_ts=e['ts'],stream=e['args']['stream'],
                          correlation=e['args']['correlation'],launch_ts=launch['ts'],external_id=e['args'].get('External id'),
                          cpu_operator=op['name'],moe_sum_parent_external_id=reduction_id))
totals=collections.Counter();counts=collections.Counter();rows=[];operator_counts=collections.Counter();operator_durations=collections.Counter()
links=[]
for s,g in zip(scopes,groups):
    g.sort(key=lambda e:e['launch_ts']);gemms=[e for e in g if e['name']=='fused_moe_kernel'];assert len(gemms)==2
    assert gemms[0]['stream']==gemms[1]['stream']
    assert gemms[0]['gpu_ts']+gemms[0]['duration_us']<=gemms[1]['gpu_ts']+.002
    parts={'first_expert_gemm':gemms[0]['duration_us'],'second_expert_gemm':gemms[1]['duration_us'],
           'other_moe_kernels':sum(e['duration_us'] for e in g if e['name']!='fused_moe_kernel')}
    for k,v in parts.items():totals[k]+=v
    counts.update(e['name'] for e in g)
    for e in g:
        phase=e['cpu_operator']
        if e is gemms[0]:phase='first_expert_gemm'
        elif e is gemms[1]:phase='second_expert_gemm'
        elif e['moe_sum_parent_external_id'] is not None:phase='final_moe_sum'
        operator_counts[phase]+=1;operator_durations[phase]+=e['duration_us']
        links.append(dict(moe_external_id=s['args']['External id'],phase=phase,**e))
    rows.append(dict(cpu_external_id=s['args']['External id'],cpu_ts=s['ts'],cpu_duration_us=s['dur'],
                     input_dims=s['args'].get('Input Dims'),kernel_count=len(g),gemms=gemms,kernel_duration_us=parts))
(O/'scopes.json').write_text(json.dumps(rows,separators=(',',':'))+'\n')
with (O/'kernel-links.jsonl.gz').open('wb') as raw:
    with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as zipped:
        for link in links:zipped.write((json.dumps(link,separators=(',',':'))+'\n').encode())
assert sum(operator_counts.values())==sum(counts.values())
assert operator_counts['final_moe_sum']==len(scopes)
j=dict(trace_sha256=hashlib.sha256((B/'trace.json.gz').read_bytes()).hexdigest(),moe_scopes=len(scopes),
       correlated_kernel_count=matched,moe_kernel_count=sum(counts.values()),kernels_outside_moe_scope=unassigned,
       duration_sums_us=dict(totals),moe_kernel_name_counts=dict(counts),
       disjoint_operator_kernel_counts=dict(operator_counts),disjoint_operator_kernel_duration_us=dict(operator_durations),
       meaning='Two ordered expert GEMM launches per CPU MoE scope; source identifies gate/up then down projection.',
       limitations=['Every MoE kernel is linked to a CPU operator, but mm/copy/fill roles are not further inferred; no network dispatch timing.',
                    'GPU timing attribution uses matched runtime launch inside the CPU scope, not overlapping GPU timestamps.',
                    'Profiler overhead and asynchronous timing remain; duration sums are not end-to-end latency.',
                    'Logical single-device operations, not expert-parallel network dispatch.'])
(O/'analysis.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps({k:v for k,v in j.items() if k not in ['moe_kernel_name_counts','limitations']}))
