"""Independent closed-form operands and conditional selection audit."""
from pathlib import Path
from fractions import Fraction as F
import sys,json,hashlib,tempfile,shutil
H=Path(__file__).resolve().parent
C=H.parent/'granularity-selection'
sys.path.insert(0,str(C))
import calculate as m
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)
for scene in json.loads((C/'scenarios.json').read_text()):
    r=m.calculate(**{k:v for k,v in scene.items() if k!='id'})
    costs=[]
    for row,E,FF in zip(r['variants'],(64,256),(3072,768)):
        # Balanced frozen routes visit each expert once; TP halves F.
        L,HID,TP,EP=94,4096,2,4
        visited=L*(E//EP)
        weight=visited*3*HID*(FF//TP)*2
        interfaces=weight+visited*3*(HID+FF//TP)*2
        check('operand:'+scene['id']+str(E),interfaces==row['max_rank_operand_bytes'])
        check('flops:'+scene['id']+str(E),weight==row['max_rank_expert_flops'])
        check('capacity:'+scene['id']+str(E),row['peak_necessary_capacity_bytes']==7948753920+weight+2*L*E*HID+788529152+2147483648)
        rate=r['scenario']['coarse_flops_per_second' if E==64 else 'fine_flops_per_second']
        router=2*L*16*HID*E
        router_io=2*L*(16*HID+HID*E+16*E)
        cost=F(weight,rate)+F(interfaces+router_io,r['scenario']['operand_bytes_per_second'])+F(router,r['scenario']['router_flops_per_second'])+F(108017280,r['scenario']['wire_bytes_per_second'])
        check('serialcost:'+scene['id']+str(E),cost==F(row['conditional_subaccount_seconds_exact']))
        costs.append(cost)
    check('slack:'+scene['id'],F(r['fine_remaining_minus_coarse_must_be_less_than_seconds_exact'])==costs[0]-costs[1])
    rest=[r['scenario'][key] for key in ('coarse_remaining_ns','fine_remaining_ns')]
    if None in rest:
        check('unknown:'+scene['id'],r['conditional_capacity_eligible_fastest_variants'] is None)
    else:
        extended=[cost+F(ns,10**9) for cost,ns in zip(costs,rest)]
        check('choice:'+scene['id'],r['conditional_capacity_eligible_fastest_variants']==[row['variant'] for row,t in zip(r['variants'],extended) if t==min(extended)])
# Corrupt a private copy; never mutate shared source/results.
original=m.P
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    for name in m.EXPECTED_INPUTS:
        target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original/name,target)
    m.P=root
    for name in m.EXPECTED_INPUTS:
        target=root/name;raw=target.read_bytes();target.write_bytes(raw+b' ')
        rejected=False
        try:m.calculate()
        except ValueError as exc:rejected='Frozen input changed' in str(exc)
        finally:target.write_bytes(raw)
        check('reject:'+name,rejected)
    m.P=original
(H/'verification.json').write_text(json.dumps(dict(checks=len(checks),names=checks,module_sha256=hashlib.sha256((C/'calculate.py').read_bytes()).hexdigest()),indent=2)+'\n')
print(len(checks),'checks passed')
