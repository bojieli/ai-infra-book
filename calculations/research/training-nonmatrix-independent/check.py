"""Count declared scalar algorithms independently; verify real model scaling."""
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from infra_calc.topics import training_matrix
HERE=Path(__file__).resolve().parent
TARGET=ROOT/'research/training-nonmatrix-completion/src/infra_calc/topics/training_nonmatrix.py'
spec=importlib.util.spec_from_file_location('training_candidate',TARGET)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]

class Scalar:
    counts=Counter()
    def __add__(self,other):self.counts['add']+=1;return Scalar()
    def __sub__(self,other):self.counts['sub']+=1;return Scalar()
    def __mul__(self,other):self.counts['mul']+=1;return Scalar()
    def __truediv__(self,other):self.counts['div']+=1;return Scalar()
    def exp(self):self.counts['exp']+=1;return Scalar()
    def sqrt(self):self.counts['sqrt']+=1;return Scalar()
    def log(self):self.counts['log']+=1;return Scalar()
    def pow(self):self.counts['pow']+=1;return Scalar()

def reduce(xs):
    result=xs[0]
    for x in xs[1:]:result=result+x
    return result

def ordinary():return sum(Scalar.counts[x] for x in ['add','sub','mul','div'])

for rows,width in [(1,1),(2,3),(6,4)]:
    Scalar.counts.clear();z=[[Scalar() for _ in range(width)] for _ in range(rows)]
    dy=[[Scalar() for _ in range(width)] for _ in range(rows)];gamma=[Scalar() for _ in range(width)]
    for i in range(rows):
        g=[dy[i][j]*gamma[j] for j in range(width)]
        a=reduce([g[j]*z[i][j] for j in range(width)])/width
        dx=[Scalar()*(g[j]-z[i][j]*a) for j in range(width)]
    dgamma=[reduce([dy[i][j]*z[i][j] for i in range(rows)]) for j in range(width)]
    assert ordinary()==6*rows*width+(2*rows-1)*width
    checks.append(f'operation-instrumented RMS VJP R{rows} D{width}')
for width in (1,2,5):
    Scalar.counts.clear();p=[Scalar() for _ in range(width)];dy=[Scalar() for _ in range(width)]
    dot=reduce([a*b for a,b in zip(p,dy)])
    ds=[(a*(b-dot))*Scalar() for a,b in zip(p,dy)]
    assert ordinary()==5*width-1
    checks.append(f'operation-instrumented scaled softmax VJP K{width}')
Scalar.counts.clear();dy,a,u,s=Scalar(),Scalar(),Scalar(),Scalar()
du=dy*a;da=dy*u;dg=da*(s+a*(Scalar()-s));assert ordinary()==6
checks.append('operation-instrumented SwiGLU backward6')
for count in (1,3):
    Scalar.counts.clear();b1,b2,lr,wd=Scalar(),Scalar(),Scalar(),Scalar()
    c1,c2=Scalar()-b1.pow(),Scalar()-b2.pow();one1,one2=Scalar()-b1,Scalar()-b2;decay=Scalar()-lr*wd
    for _ in range(count):
        theta,g,first,second=Scalar(),Scalar(),Scalar(),Scalar()
        first=b1*first+one1*g;second=b2*second+one2*(g*g)
        mh,vh=first/c1,second/c2
        theta=theta*decay-(lr*mh)/(vh.sqrt()+Scalar())
    assert ordinary()==14*count+6 and Scalar.counts['pow']==2 and Scalar.counts['sqrt']==count
    checks.append(f'operation-instrumented dense AdamW P{count}')

# Fixed config dimensions, separate integer formulas; no candidate op rows
# are used in computing expected totals.
H,F,D,Q,K,L,V=4096,12288,128,32,8,36,151936
for batch,tokens,supervised in [(1,1,1),(2,3,1),(2,3,5)]:
    R=batch*tokens
    norm_specs=[(R,H,L),(R,H,L),(R*Q,D,L),(R*K,D,L),(R,H,1)]
    norm_f=sum(c*r*(4*d+1) for r,d,c in norm_specs)
    norm_b=sum(c*(6*r*d+(2*r-1)*d) for r,d,c in norm_specs)
    E=L*R*F;cells=L*batch*Q*tokens*(tokens+1)//2;arows=L*batch*Q*tokens;rope=L*R*(Q+K)*D
    for head in ('dense','compact'):
        for policy in ('save_nonlinear','recompute_silu'):
            r=m.calculate(batch=batch,tokens=tokens,supervised_tokens=supervised,head_strategy=head,activation_policy=policy)
            base=training_matrix.calculate('qwen3-8b',batch=batch,tokens=tokens,supervised_tokens=supervised,head_strategy=head,gradient_bytes=4,master_weight_bytes=4)
            assert r['training_matrix_original']==base
            forward=norm_f+2*E+(4*cells-arows)+3*rope+tokens*D//2+2*L*R*H+supervised*(3*V+2)
            backward=norm_b+(6+(policy=='recompute_silu'))*E+(5*cells-arows)+3*rope+5*L*R*H+2*L*R*K*D*(Q//K-1)+R*H+supervised*(V+1)
            assert r['summary']['forward_scalar_flops']==forward
            assert r['summary']['backward_scalar_flops']==backward
            assert r['optimizer']['interfaces']==dict(fp32_gradient_master_m_v_read_bytes=16*base['summary']['parameters'],fp32_master_m_v_write_bytes=12*base['summary']['parameters'],bf16_parameter_write_bytes=2*base['summary']['parameters'])
            objects=r['saved_objects'];events=r['lifetime_events'];live={};peak=0
            for event in events:
                if event['delta_bytes']>0:
                    assert event['object'] not in live;live[event['object']]=event['delta_bytes']
                else:
                    assert live.pop(event['object'])==-event['delta_bytes']
                peak=max(peak,sum(live.values()));assert event['declared_subset_live_bytes']==sum(live.values())
            assert not live and peak==r['summary']['declared_saved_and_recomputed_subset_peak_bytes']
            assert sum(x['bytes'] for x in objects)==r['summary']['nonlinear_saved_at_forward_end_bytes']
            assert r['summary']['accounted_matrix_plus_scalar_flops']==base['summary']['training_matrix_flops']+forward+backward+14*base['summary']['parameters']+6
            assert r['summary']['complete_training_step_flops'] is None and r['summary']['complete_activation_peak_bytes'] is None
            checks.append(f'B{batch}T{tokens}S{supervised} {head}/{policy}: totals, unchanged matrices, typed AdamW, object intervals')
(HERE/'results.json').write_text(json.dumps(dict(module_sha256=hashlib.sha256(TARGET.read_bytes()).hexdigest(),checks=checks,count=len(checks)),indent=2)+'\n')
print('PASS',len(checks),'independent counted-algorithm/model/lifetime cases')
