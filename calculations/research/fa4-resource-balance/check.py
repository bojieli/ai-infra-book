"""Independent enumeration of macro-tile operand reads and paper table checks."""
import json
from pathlib import Path
from fractions import Fraction
import hashlib
p=Path(__file__).resolve().parent
r=json.loads((p/'result.json').read_text())
checks=0

def equal(a,b):
    global checks
    assert a==b,(a,b)
    checks+=1

for row in r['scenarios']:
    m,n,d=(row['shape'][k] for k in ('M','N','d'))
    qk=0
    for mi in range(0,m,128):
        for ni in range(0,n,128):
            qk += sum(2 for _ in range(128*d)) # Q operand
            qk += sum(2 for _ in range(128*d)) # K operand
    pv=0
    for mi in range(0,m,128):
        for di in range(0,d,128):
            pv += sum(2 for _ in range(n*128))
    equal(row['interface_bytes']['qk_smem_read'],qk)
    equal(row['interface_bytes']['pv_smem_read'],pv)
    equal(row['work']['matrix_flops'],2*(m*n*d + m*d*n))
    equal(row['work']['exp_results'],m*n)
    rates=row['multipliers']
    costs={'matrix':Fraction(2*(m*n*d + m*d*n),8192*rates['matrix']),
           'smem':Fraction(qk+pv,128*rates['smem']),
           'exp':Fraction(m*n,16*rates['exp'])}
    for key,value in costs.items():equal(Fraction(**row['cycles'][key]),value)
    equal(Fraction(**row['accounted_steady_state_bound_cycles']),max(costs.values()))
    equal(row['tied_limiting_resources'],[k for k,v in costs.items() if v==max(costs.values())])
    equal(row['measured_kernel_cycles'],None)
    equal(row['complete_softmax_cycles'],None)
lookup={x['id']:x for x in r['scenarios']}
for shape,values in [('m128-n128',(1024,768,1024)),('m256-n128',(2048,1536,2048))]:
    row=lookup[shape+'-paper-baseline']
    equal(tuple(Fraction(**row['cycles'][k]) for k in ('matrix','smem','exp')),values)
for name,bound in [('paper-baseline',1024),('matrix-double',1024),('matrix-exp-double',768),('all-three-double',512)]:
    equal(Fraction(**lookup['m128-n128-'+name]['accounted_steady_state_bound_cycles']),bound)
# M256 causes reused K/V operands: SMEM bytes exceed unique QKV input.
row=lookup['m256-n128-paper-baseline']
equal(row['work']['smem_read_bytes']>row['interface_bytes']['unique_qkv_input_payload'],True)
result={'status':'passed','independent_checks':checks,'sha256':{name:hashlib.sha256((p/name).read_bytes()).hexdigest() for name in ('calculate.py','inputs.json','result.json')}}
(p/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(result)
