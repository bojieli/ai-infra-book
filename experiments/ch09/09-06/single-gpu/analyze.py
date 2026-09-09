"""Offline raw ID/quality audit. No physical placement or communication model."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
B=Path(__file__).absolute().parent
out=Path(sys.argv[1]) if len(sys.argv)>1 else B/'results';out.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(p.read_text())
def strict(text):
    def pairs(kvs):
        obj={}
        for k,v in kvs:
            if k in obj:raise ValueError('duplicate JSON key')
            obj[k]=v
        return obj
    try:return json.loads(text,object_pairs_hook=pairs)
    except ValueError:return None
checks=0
def check(ok):
    global checks
    assert ok;checks+=1
cfg=read(B/'model-config.json')['text_config'];layers=cfg['num_hidden_layers'];experts=cfg['num_experts'];topk=cfg['num_experts_per_tok']
check((layers,experts,topk)==(48,128,8))
conditions={};resources={};configs={}
for mode in ['native','control']:
    root=B/'runs'/(mode+'-001');output=root/'output'
    env=read(output/'environment.json');configs[mode]=env['config']
    check(hashlib.sha256((root/'executed-run.py').read_bytes()).hexdigest()==env['driver_sha256'])
    supervisor=read(root/'supervisor.json');check(supervisor['exit_code']==0 and supervisor['reason'] is None and not supervisor['leftovers'])
    records=[json.loads(l) for l in (root/'resources.jsonl').read_text().splitlines()]
    resources[mode]=dict(wall_s=supervisor['wall_s'],own_gpu_peak_mib=max(r['gpu_mib'] for r in records),
                        own_process_rss_sum_peak_bytes=max(r['rss_bytes'] for r in records),
                        system_available_min_bytes=min(r['mem_available_bytes'] for r in records))
    rows=[json.loads(l) for l in (output/'requests.jsonl').read_text().splitlines()]
    cases=read(output/'cases.json');check(len(rows)==len(cases)==4)
    check([r['id'] for r in rows]==[r['id'] for r in cases])
    for r,c in zip(rows,cases):
        check(r['prompt_ids']==c['input_ids']);check(r['finish_reason']=='stop')
        check(r['output_ids'][-1] in ([cfg['eos_token_id']] if isinstance(cfg['eos_token_id'],int) else cfg['eos_token_id']))
        r['correct']=strict(r['text'])==c['expected']
    conditions[mode]=rows
ca=dict(configs['native']);cb=dict(configs['control']);ca.pop('enable_return_routed_experts');cb.pop('enable_return_routed_experts');check(ca==cb)
counts=[];case_rows=[]
for a,b in zip(conditions['native'],conditions['control']):
    check(a['prompt_ids']==b['prompt_ids']);check(a['output_ids']==b['output_ids']);check(a['text']==b['text'])
    check(b['route_file'] is None)
    ids=np.load(B/'runs/native-001/output'/a['route_file'],allow_pickle=False)
    check(ids.dtype==np.uint8);check(ids.shape==(len(a['prompt_ids'])+len(a['output_ids'])-1,layers,topk))
    check(bool(np.all(ids<experts)));check(bool(np.all(np.diff(np.sort(ids,axis=-1),axis=-1)>0)))
    per=[]
    for label,part in [('prompt',ids[:len(a['prompt_ids'])]),('continuation',ids[len(a['prompt_ids']):])]:
        hist=np.stack([np.bincount(part[:,l,:].reshape(-1),minlength=experts) for l in range(layers)])
        check(bool(np.all(hist.sum(axis=1)==len(part)*topk)))
        counts.append(hist)
        per.append(dict(stage=label,tokens=len(part),assignments=int(hist.sum()),
                        max_single_expert_assignments_per_token=float(hist.max()/len(part))))
    case_rows.append(dict(id=a['id'],prompt_tokens=len(a['prompt_ids']),output_tokens=len(a['output_ids']),
                          route_shape=list(ids.shape),correct=a['correct'],output_ids_exact_control=True,stages=per))
np.save(out/'counts.npy',np.stack(counts),allow_pickle=False)
report=dict(model='Qwen3-VL-30B-A3B-Instruct-FP8 text-only variant',layers=layers,experts=experts,topk=topk,
            cases=case_rows,quality_correct=sum(r['correct'] for r in conditions['native']),quality_denominator=4,
            paired_output_exact=4,route_assignment_total=sum(s['assignments'] for r in case_rows for s in r['stages']),
            resources=resources,checks=checks,
            scope='Actual single-device logical router IDs; no routing weights, dispatch/GEMM/combine timing, replica placement or DBO comparison.',
            performance='Single cold-order capture then control; JIT observed. Wall times are not a capture-overhead estimate or serving benchmark.')
(out/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
