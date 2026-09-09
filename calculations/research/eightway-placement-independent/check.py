"""Independent closed-form two-layout ownership and grouped-storage oracle."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent
P=HERE.parents[1]
sys.path.insert(0,str(P/'src'))
from infra_calc.topics.qwen235_placement import calculate
cfg=json.loads((P/'configs/models/qwen3-235b-a22b/config.json').read_text())
h,f,L,E,Q,K,d,V=[cfg[k] for k in ('hidden_size','moe_intermediate_size','num_hidden_layers','num_experts','num_attention_heads','num_key_value_heads','head_dim','vocab_size')]
checks=[];records=[]
def check(name,ok):
    assert ok,name
    checks.append(name)
for tp,ep,name,wanted in [(8,1,'qwen235-placement-tp8-kv-replica',[47,120,158]),(1,8,'qwen235-placement-ep8-expert-partition',[3,25,36])]:
    r=calculate(tp=tp,ep=ep,pp=1)
    localK=max(1,K//tp)
    kv=4*L*localK*d*8192
    # Independent actual projection shapes. All layers on every PP=1 rank.
    matrices=[(Q*d//tp,h),(localK*d,h),(localK*d,h),(h,Q*d//tp)]
    matrices += [(f//tp,h),(f//tp,h),(h,f//tp)]*(E//ep)
    high=2*(2*V*h//tp + h + L*(E*h+2*h+2*d))
    expected=[]
    for bits in (16,8,4):
        low=L*sum(rows*((cols*bits+7)//8) for rows,cols in matrices)
        meta=0 if bits==16 else L*sum(rows*((cols+127)//128)*2 for rows,cols in matrices)
        weights=high+low+meta
        n=(80_000_000_000-2*2**30-weights)//kv
        expected.append(n)
        for rank in r['ranks']:
            form=next(z for z in rank['formats'] if z['bits']==bits)
            check(f'{name}:rank{rank["rank"]}:weights{bits}',form['weight_bytes']==weights)
            check(f'{name}:rank{rank["rank"]}:metadata{bits}',form['scale_bytes']==meta)
            check(f'{name}:rank{rank["rank"]}:KV{bits}',form['kv_bytes_per_request']==kv)
            check(f'{name}:rank{rank["rank"]}:boundary{bits}',form['maximum_requests']==n and weights+2*2**30+n*kv<=80_000_000_000<weights+2*2**30+(n+1)*kv)
    check(name+':expected cohort',expected==wanted==[x['maximum_requests'] for x in r['cohort']])
    for rank in r['ranks']:
        a,b=rank['kv_head_range'];check(name+':wholeKV'+str(rank['rank']),b-a==localK and 0<=a<b<=K)
        a,b=rank['expert_range'];check(name+':expert range'+str(rank['rank']),b-a==E//ep)
    if tp==8:
        check(name+':KV replicated twice',[x['kv_head_range'] for x in r['ranks']]==[[j//2,j//2+1] for j in range(8)])
        check(name+':all expert shards',[x['expert_range'] for x in r['ranks']]==[[0,E]]*8)
    else:
        check(name+':EP allKV',[x['kv_head_range'] for x in r['ranks']]==[[0,K]]*8)
        check(name+':EP unique cover',[i for x in r['ranks'] for i in range(*x['expert_range'])]==list(range(E)))
    stored=json.loads((P/'results'/(name+'.json')).read_text())
    check(name+':frozen equal',r==stored)
    check(name+':input replay',r==calculate(**r['scenario']))
    inp=HERE/(name+'-inputs.json');inp.write_text(json.dumps(r['scenario']))
    for fmt in ('json','md'):
        proc=subprocess.run([sys.executable,str(P/'calc.py'),'qwen235-placement','--inputs',str(inp),'--format',fmt],capture_output=True,text=True)
        check(name+':CLI status'+fmt,proc.returncode==0)
        check(name+':CLI equal'+fmt,json.loads(proc.stdout)==r if fmt=='json' else proc.stdout.rstrip()==(P/'results'/(name+'.md')).read_text().rstrip())
    records.append(dict(id=name,tp=tp,ep=ep,per_rank_kv_bytes=kv,concurrency=expected,physical_kv_bytes=8*kv,formats=r['ranks'][0]['formats']))
(HERE/'results.json').write_text(json.dumps(dict(count=len(checks),checks=checks,cases=records),indent=2)+'\n')
print(len(checks),'checks passed')
