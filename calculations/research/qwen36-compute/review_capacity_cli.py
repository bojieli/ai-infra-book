import subprocess,json,sys,os
from pathlib import Path
base=Path(__file__).resolve().parents[2]
env=dict(os.environ,PYTHONPATH=str(base/'src'))
def cli(data=None):
    args=[sys.executable,'-m','infra_calc','qwen36-capacity']
    if data is not None:
        path=base/'research/qwen36-compute/capacity-review-input.json';path.write_text(json.dumps(data));args+=['--inputs',str(path)]
    p=subprocess.run(args,env=env,text=True,capture_output=True)
    return p,json.loads(p.stdout) if p.returncode==0 else None
p,r=cli();assert p.returncode==0,p.stderr
expected=69321221376+8192*20480+30*32*128*128*4+30*8192*4*2+2*1024**3
assert r['summary']['necessary_budget_bytes']==expected
assert r['summary']['entire_checkpoint_bytes']==71903645408
print('default',r['summary']['necessary_budget_bytes'],[(d['device'],d['necessary_budget_fits']) for d in r['devices']])
for data in [{'batch':3,'length':1,'reserve_bytes':0},{'batch':2,'length':262144,'include_auxiliary_weights':True},{'include_auxiliary_weights':True}]:
    p,r=cli(data);assert p.returncode==0,p.stderr
    B=data.get('batch',1);L=data.get('length',8192);W=71903645408 if data.get('include_auxiliary_weights') else 69321221376
    assert r['summary']['necessary_budget_bytes']==W+B*(L*20480+30*32*128*128*4+30*8192*4*2)+data.get('reserve_bytes',2*1024**3)
print('independent formulas pass3 custom cases')
# Reserve on either side of exact nominal H100 boundary.
base_required=69321221376+20480+30*32*128*128*4+30*8192*4*2
for extra in [0,1]:
    p,r=cli({'length':1,'reserve_bytes':80000000000-base_required+extra});assert p.returncode==0,p.stderr
    d=next(d for d in r['devices'] if d['device']=='h100-sxm')
    assert d['necessary_budget_fits']==(extra==0)
    assert d['headroom_after_declared_budget_bytes']==-extra
print('exact boundary and boundary+1 pass')
for data in [{'batch':True},{'length':0},{'length':262145},{'reserve_bytes':-1},{'include_auxiliary_weights':'false'}]:
    p,r=cli(data);assert p.returncode!=0,data
print('invalid inputs reject5 cases')
