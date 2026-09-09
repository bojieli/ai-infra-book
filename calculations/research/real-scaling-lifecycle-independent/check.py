import hashlib
import json
import math
from decimal import Decimal, localcontext
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
CALC=HERE.parents[1]
PUBLIC=HERE.parent/'real-scaling-lifecycle/public'
sys.path.insert(0,str(CALC/'src'))
from infra_calc import topics
topics.__path__.insert(0,str(PUBLIC/'src/infra_calc/topics'))
from infra_calc.topics import real_scaling_lifecycle as m
result=m.calculate()
original=json.loads((PUBLIC.parent/'result.json').read_text())
checks=[]
def check(name,value):
    assert value,name
    checks.append(name)
check('five original variants byte-value equal',result['variants']==original['variants'])
check('scenario equal',result['scenario']==original['scenario'])
check('scenario replay',result==m.calculate(**result['scenario']))
for variant in result['variants']:
    law=variant['law'];bounds=variant['fit_bounds']; rows=variant['lifecycle']['rows']
    for row in rows:
        with localcontext() as ctx:
            ctx.prec=60
            d=lambda x:Decimal(str(x))
            gap=d(2.9)-d(law['E'])-d(law['A'])*(d(row['N'])/d(law['N0']))**(-d(law['alpha']))
            budget=d(law['D0'])*(d(law['B'])/gap)**(1/d(law['beta']))
        tag=variant['variant']+' '+str(row['N'])
        check(tag+' independent Decimal D',math.isclose(float(budget),row['D'],rel_tol=2e-12))
        check(tag+' exact additional decode',row['decode_proxy_flops_per_call']==2*row['N']*127)
        check(tag+' upfront proxy',math.isclose(row['upfront_cost'],6*row['N']*float(budget)*1e-18,rel_tol=2e-12))
        check(tag+' fitbox',row['outside_fit_box']==(row['N']<bounds['N'][0] or row['N']>bounds['N'][1] or row['D']<bounds['D'][0] or row['D']>bounds['D'][1]))
    index={row['N']:row for row in rows}
    for crossing in variant['lifecycle']['crossovers']:
        a,b=(index[crossing[k]] for k in ['left_N','right_N'])
        intercept=a['upfront_cost']-b['upfront_cost'];slope=a['cost_per_call']-b['cost_per_call']
        if crossing['calls'] is not None:
            c=crossing['calls']
            check(variant['variant']+' root '+str(c),math.isclose(c,-intercept/slope,rel_tol=1e-12))
            if c>0:check(variant['variant']+' root sign '+str(c),(intercept+slope*.9*c)*(intercept+slope*1.1*c)<0)
    for curve in variant['curves']:
        independent={row['N']:row['training_proxy_flops']*1e-18+curve['calls']*2*row['N']*639*1e-18 for row in rows}
        check(variant['variant']+' minimum '+str(curve['calls']),curve['minimizing_candidate_N']==min(independent,key=independent.get))
one=m.calculate(returned_tokens=1)
check('G1 zero additional decode',all(r['decode_proxy_flops_per_call']==0 for v in one['variants'] for r in v['lifecycle']['rows']))
zero=m.calculate(input_tokens=0,returned_tokens=1)
check('zero-work parallel lines',all(c['calls'] is None and c['status'] in ('parallel','coincident') for v in zero['variants'] for c in v['lifecycle']['crossovers']))
impossible=m.calculate(target_loss=.1)
check('infeasible retained',all(v['lifecycle']['status']=='no_feasible_candidate' for v in impossible['variants']))
check('infeasible curve has no optimum',all(c['minimizing_candidate_N'] is None for v in impossible['variants'] for c in v['curves']))
check('no price or currency claim',any('not currency, official hardware price' in s for s in result['scope']))
check('attention and KV excluded',any('Attention, KV' in s for s in result['scope']))
for item in json.loads((PUBLIC/'bindings.json').read_text())['files']:
    path=PUBLIC/item['file'];raw=path.read_bytes()
    check('binding '+item['file'],hashlib.sha256(raw).hexdigest()==item['sha256'])
(HERE/'results.json').write_text(json.dumps(dict(check_count=len(checks),checks=checks,module_sha256=hashlib.sha256((PUBLIC/'src/infra_calc/topics/real_scaling_lifecycle.py').read_bytes()).hexdigest()),indent=2)+'\n')
print(len(checks),'checks passed')
