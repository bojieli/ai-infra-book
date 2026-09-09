"""Closed-form independent audit of full-rectangle, causal and tile arithmetic."""
import hashlib
import importlib.util
import json
import math
from fractions import Fraction
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
AUTHOR = PROJECT/'research/architecture-tile-work/public'
sys.path.insert(0,str(PROJECT/'src'))
path=AUTHOR/'src/infra_calc/topics/architecture_tile_work.py'
spec=importlib.util.spec_from_file_location('reviewed_tile_work',path)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
checks=0


def equal(a,b):
    global checks
    assert a==b,(a,b)
    checks+=1


def verify(r):
    s=r['scenario']
    B,T,S=s['batch'],s['tokens'],s['history']
    tm,tn,tk=s['tile_m'],s['tile_n'],s['tile_k']
    for v in r['variants']:
        a=v['architecture']
        H,L,F,A,D=[a[k] for k in ('hidden','layers','ffn','heads','head_dim')]
        dims={'q_proj':(B*T,A*D,H,L),'k_proj':(B*T,8*D,H,L),'v_proj':(B*T,8*D,H,L),'o_proj':(B*T,H,A*D,L),'gate_proj':(B*T,F,H,L),'up_proj':(B*T,F,H,L),'down_proj':(B*T,H,F,L),'lm_head':(B,151936,H,1),'qk':(T,S+T,D,L*B*A),'pv':(T,D,S+T,L*B*A)}
        equal(set(x['name'] for x in v['matrices']),set(dims))
        totals=[0,0,0]
        pairs=T*S+T*(T+1)//2
        for x in v['matrices']:
            M,N,K,copies=dims[x['name']]
            equal(x['mnk'],[M,N,K]);equal(x['multiplicity'],copies)
            valid=2*D*pairs if x['name'] in ('qk','pv') else 2*M*N*K
            rect=2*M*N*K
            padded=2*((M+tm-1)//tm*tm)*((N+tn-1)//tn*tn)*((K+tk-1)//tk*tk)
            for i,(key,value) in enumerate(zip(('valid','rectangular','padded'),(valid,rect,padded))):
                equal(x[key+'_per_instance_flops'],value)
                equal(x[key+'_flops'],value*copies)
                totals[i]+=value*copies
            equal(x['causal_rectangle_extra_flops'],(rect-valid)*copies)
            equal(x['tile_padding_extra_flops'],(padded-rect)*copies)
            equal(Fraction(x['valid_fraction_of_padded_exact']),Fraction(valid,padded))
            equal(x['tile_blocks']['valid_matrix_flops'],rect)
        equal([v[k+'_flops'] for k in ('valid','rectangular','padded')],totals)
        equal(v['padded_flops'],v['valid_flops']+v['causal_rectangle_extra_flops']+v['tile_padding_extra_flops'])
        equal(v['conditional_matrix_service_seconds'],totals[2]/v['declared_padded_matrix_flops_per_second'])
        equal(v['full_forward_runtime_seconds'],None)
        equal(v['actual_tensor_core_utilization'],None)
    deep,wide=r['variants']
    equal(Fraction(r['comparison']['shallow_to_deep_padded_flop_ratio_exact']),Fraction(wide['padded_flops'],deep['padded_flops']))


def main():
    data=path.read_bytes()
    (HERE/'reviewed.snapshot.py').write_bytes(data)
    summaries=[]
    for scene in json.loads((AUTHOR/'book.append.json').read_text()):
        args={k:v for k,v in scene.items() if k!='id'}
        r=m.calculate(**args)
        equal(r,json.loads((AUTHOR/'results'/f"{scene['id']}.json").read_text()))
        verify(r)
        summaries.append(dict(id=scene['id'],comparison=r['comparison'],variants=[{k:v[k] for k in ('name','valid_flops','rectangular_flops','padded_flops')} for v in r['variants']]))
    for B,T,S in ((3,1,0),(2,3,2),(3,7,11),(1,65,0)):
        r=m.calculate(batch=B,tokens=T,history=S,tile_m=3,tile_n=5,tile_k=7)
        verify(r)
        pairs=sum(j<=S+i for i in range(T) for j in range(S+T))
        equal(pairs,T*S+T*(T+1)//2)
        deep,wide=r['variants']
        # Rates exactly proportional to integer padded work give a 1-second tie.
        for factor,expected in ((Fraction(999,1000),False),(Fraction(1),False),(Fraction(1001,1000),True)):
            q=m.calculate(batch=B,tokens=T,history=S,tile_m=3,tile_n=5,tile_k=7,variant_rates={'deeper_same_width':deep['padded_flops'],'shallower_wider':float(wide['padded_flops']*factor)})
            equal(q['comparison']['shallow_has_lower_conditional_matrix_service'],expected)
    (HERE/'verification.json').write_text(json.dumps(dict(status='pass',sha256=hashlib.sha256(data).hexdigest(),python=sys.version,checks=checks,scenarios=summaries),indent=2)+'\n')
    print(json.dumps(dict(status='pass',checks=checks)))


if __name__=='__main__':
    main()
