"""Compare actual backend outputs and logical expert sets on identical positions."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
B=Path(__file__).absolute().parent
out=Path(sys.argv[1]) if len(sys.argv)>1 else B/'results';out.mkdir(parents=True,exist_ok=True)
checks=0
def check(ok):
    global checks
    assert ok;checks+=1
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(l) for l in p.read_text().splitlines()]
def strict(text):
    def pairs(items):
        d={}
        for k,v in items:
            if k in d:raise ValueError('duplicate')
            d[k]=v
        return d
    try:return json.loads(text,object_pairs_hook=pairs)
    except ValueError:return None
ref=B/'reference/output';new=B/'runs/marlin-001/output'
for item in read(B/'reference-origin.json'):
    check(hashlib.sha256((B/item['destination']).read_bytes()).hexdigest()==item['sha256'])
for item in read(B/'runtime-sources/sources.json'):
    check(hashlib.sha256((B/'runtime-sources'/item['path']).read_bytes()).hexdigest()==item['sha256'])
check(hashlib.sha256((B/'run.py').read_bytes()).hexdigest()==read(new/'environment.json')['driver_sha256'])
cfg0=read(ref/'environment.json')['config'];cfg1=read(new/'environment.json')['config'];kernel=cfg1.pop('kernel_config')
check(kernel=={'moe_backend':'marlin'});check(cfg0==cfg1)
supervisor=read(new.parent/'supervisor.json');check(supervisor['exit_code']==0 and supervisor['reason'] is None and not supervisor['leftovers'])
oldrows=rows(ref/'requests.jsonl');newrows=rows(new/'requests.jsonl');cases=read(new/'cases.json');check(len(oldrows)==len(newrows)==len(cases)==4)
report=[]
for a,b,c in zip(oldrows,newrows,cases):
    check(a['id']==b['id']==c['id']);check(a['prompt_ids']==b['prompt_ids']==c['input_ids'])
    check(a['finish_reason']==b['finish_reason']=='stop')
    inputs0=a['prompt_ids']+a['output_ids'][:-1];inputs1=b['prompt_ids']+b['output_ids'][:-1]
    prefix=0
    for x,y in zip(inputs0,inputs1):
        if x!=y:break
        prefix+=1
    ra=np.load(ref/a['route_file'],allow_pickle=False);rb=np.load(new/b['route_file'],allow_pickle=False)
    check(ra.shape==(len(inputs0),48,8));check(rb.shape==(len(inputs1),48,8))
    check(ra.dtype==rb.dtype==np.uint8);check(bool(np.all(rb<128)))
    check(bool(np.all(np.diff(np.sort(rb,axis=-1),axis=-1)>0)))
    stages=[]
    for label,start,end in [('prompt',0,len(a['prompt_ids'])),('continuation',len(a['prompt_ids']),prefix)]:
        x=ra[start:end];y=rb[start:end]
        same_order=np.all(x==y,axis=-1)
        same_set=np.all(np.sort(x,axis=-1)==np.sort(y,axis=-1),axis=-1)
        overlap=(x[:,:,:,None]==y[:,:,None,:]).any(axis=-1).sum(axis=-1)
        check(bool(np.all((overlap==8)==same_set)))
        stages.append(dict(stage=label,aligned_tokens=end-start,token_layer_rows=int(same_set.size),
                           ordered_rows_different=int((~same_order).sum()),expert_sets_different=int((~same_set).sum()),
                           expert_sets_different_by_layer=(~same_set).sum(axis=0).tolist(),
                           selected_experts_replaced=int((8-overlap).sum()),
                           mean_common_experts=float(overlap.mean()) if overlap.size else None))
    report.append(dict(id=a['id'],output_ids_exact=a['output_ids']==b['output_ids'],consumed_prefix_aligned=prefix,
                       reference_correct=strict(a['text'])==c['expected'],marlin_correct=strict(b['text'])==c['expected'],stages=stages))
resource=rows(new.parent/'resources.jsonl')
j=dict(cases=report,checks=checks,reference_backend='TRITON FP8 MoE W8A8',new_backend='MARLIN FP8 MoE W8A16',
       changed_expert_set_rows=sum(s['expert_sets_different'] for r in report for s in r['stages']),
       compared_token_layer_rows=sum(s['token_layer_rows'] for r in report for s in r['stages']),
       output_pairs_exact=sum(r['output_ids_exact'] for r in report),quality_correct=sum(r['marlin_correct'] for r in report),
       resources=dict(wall_s=supervisor['wall_s'],gpu_peak_mib=max(r['gpu_mib'] for r in resource),rss_sum_peak_bytes=max(r['rss_bytes'] for r in resource),available_min_bytes=min(r['mem_available_bytes'] for r in resource)),
       limitations=['Only four previously used tasks, no general quality or strict numerical clearance.',
                    'MoE activation precision changes with backend; not identical-format speed comparison.',
                    'Reused earlier baseline, no interleaving/warmup; not measured performance gain.',
                    'No expert weights, physical placement, dispatch/GEMM/combine timing or communication benefit.'])
(out/'analysis.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps({k:v for k,v in j.items() if k not in ['cases','limitations']}))
