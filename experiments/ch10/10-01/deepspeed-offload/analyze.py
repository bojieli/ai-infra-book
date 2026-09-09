import argparse,hashlib,json,statistics
from pathlib import Path

ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path);args=ap.parse_args()
p=args.directory
env=json.loads((p/'environment.json').read_text())
assert hashlib.sha256((Path(__file__).parent/'run.py').read_bytes()).hexdigest()==env['source_sha']
done=json.loads((p/'completion.json').read_text())
rows=[json.loads(x) for x in (p/'records.jsonl').read_text().splitlines()]
assert done['completed'] and len(rows)==done['steps']
assert len(rows)==(12 if env['smoke'] else 42)
seen=set()
for r in rows:
    key=(r['phase'],r['policy'],r['trial'],r['step']);assert key not in seen;seen.add(key)
    assert r['gradient_exact'] and r['weight_transfer_exact']
    assert all(c['failing_elements']==0 for c in r['checks'].values())
    assert r['wall_ms']>=sum(r['stage_ms'].values())
    assert r['tensors']['host_grad']['pinned']
    assert r['tensors']['moment1']['device']=='cpu' and r['tensors']['moment2']['device']=='cpu'
    assert r['cuda_peak_allocated_bytes']<3*1024**3
for step in [1,2,3]:
    assert len({r['gradient_sha'] for r in rows if r['step']==step})==1
    # These paths have exactly the same optimizer and delivered gradients.
    for k in ['parameter_sha','moment1_sha','moment2_sha']:
        assert len({r[k] for r in rows if r['step']==step})==1
summary={'status':'verified', 'groups':done['groups'],'steps':len(rows),'shape':env['shape'],
         'max_parameter_abs':max(r['checks']['parameter']['max_abs'] for r in rows),
         'all_path_states_sha_equal':True,'formal':[]}
for policy in ['cpu_cast','gpu_cast']:
    for step in [1,2,3]:
        selected=[r for r in rows if r['phase']=='formal' and r['policy']==policy and r['step']==step]
        summary['formal'].append(dict(policy=policy,step=step,count=len(selected),
            wall_ms_median=statistics.median(r['wall_ms'] for r in selected),
            stage_ms_median={k:statistics.median(r['stage_ms'].get(k,0) for r in selected)
                for k in ['gpu_cast','D2H','cpu_cast','CPUAdam','weight_cpu_cast','weight_H2D']},
            cuda_peak_allocated_bytes_max=max(r['cuda_peak_allocated_bytes'] for r in selected)))
(p/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
if not env['smoke']:
    traces={}
    for policy in ['cpu_cast','gpu_cast']:
        filename=policy+'-trace.json'
        events=json.loads((p/filename).read_text())['traceEvents']
        pinned=[e for e in events if e.get('cat')=='gpu_memcpy' and 'Pinned' in e['name']]
        d=[e for e in pinned if 'DtoH' in e['name']];h=[e for e in pinned if 'HtoD' in e['name']]
        expected=(96 if policy=='cpu_cast' else 192)*1024**2
        assert len(d)==len(h)==3
        assert all(e['args']['bytes']==expected for e in d)
        assert all(e['args']['bytes']==96*1024**2 for e in h)
        traces[filename]={
            'D2H':[dict(bytes=e['args']['bytes'],dur_us=e['dur']) for e in d],
            'H2D':[dict(bytes=e['args']['bytes'],dur_us=e['dur']) for e in h],
            'scope':'Pinned offload transfers only; profiler also includes forward/backward and unscored validation transfers.'}
    (p/'trace-review.json').write_text(json.dumps(traces,indent=2)+'\n')
print(json.dumps(summary,indent=2))
