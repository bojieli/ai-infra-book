"""Independent normal-domain NNLS, split, bindings and extreme probes."""
import copy
import hashlib
import importlib.util
import json
import math
import random
import sys
from pathlib import Path
import numpy as np
from scipy.optimize import nnls
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
spec=importlib.util.spec_from_file_location("boundary_audit", BASE/"scaling-boundary-fit/boundary_fit.py")
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
checks=[]
def ok(name, condition):
    assert condition,name
    checks.append(name)
rng=random.Random(914)
for i in range(80):
    x=np.array([[1.,rng.uniform(.1,4),rng.uniform(.1,4)] for _ in range(9)])
    if i%4==0:x[:,2]=2*x[:,1]
    if i%4==1:x[:,2]=3
    y=np.array([rng.uniform(.1,4) for _ in x])
    got=b.nonnegative_fit(x.tolist(),y.tolist())
    _,norm=nnls(x,y,maxiter=100)
    ok(f"scipy objective {i}",math.isclose(got['sse'],norm**2,rel_tol=1e-9,abs_tol=1e-10))
    ok(f"nonnegative finite {i}",all(math.isfinite(v) and v>=0 for v in got['coefficients']))
p=BASE/'scaling-real-points'
sys.path.insert(0,str(p))
import adapt_statistical as adapter
actual=adapter.calculate()
saved=json.loads((p/'statistical-fit.json').read_text())
ok('primary and sensitivities frozen replay', {k:v for k,v in actual.items() if k!='boundary_diagnostic'}=={k:v for k,v in saved.items() if k!='boundary_diagnostic'})
for key in ['E','A','B','alpha','beta']:
    ok('boundary corrected law '+key,math.isclose(actual['boundary_diagnostic']['law'][key],saved['boundary_diagnostic']['law'][key],rel_tol=1e-10,abs_tol=1e-10))
for r in actual['records']:
    ok('prespecified split '+r['id'],r['split']==('holdout' if r['N']>=2e9 else 'fit'))
    e=r['evaluation']; raw=(p/e['file']).read_bytes()
    ok('actual evaluation binding '+r['id'],hashlib.sha256(raw).hexdigest()==e['sha256'])
ok('six fit two held',sum(r['split']=='fit' for r in actual['records'])==6 and len(actual['records'])==8)
changed=copy.deepcopy(actual['records'])
for r in changed:
    if r['split']=='holdout':r['loss']=100+r['loss']
first=actual['boundary_diagnostic']; second=b.fit(changed,adapter.GRID)
ok('holdout cannot select boundary law',first['law']==second['law'] and first['fit_sse']==second['fit_sse'])
pfirst=actual['primary']['result'];psecond=adapter.run_fit(changed,adapter.GRID)['result']
ok('holdout cannot select primary law',pfirst['law']==psecond['law'] and pfirst['fit_sse']==psecond['fit_sse'])
for item in json.loads((p/'delivery-bindings.json').read_text())['files']:
    if item['file']=='../scaling-boundary-fit/boundary_fit.py':continue  # Parent intentionally replaced this dependency; final report binds current SHA.
    raw=(p/item['file']).read_bytes()
    ok('delivery '+item['file'],len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'])
for kind in ('shape_N','declared_D','both'):
    preds=actual['sensitivity'][kind]['result']['predictions']
    for row in preds:
        source=next(r for r in actual['records'] if r['id']==row['id'])
        ok(kind+' split '+row['id'],row['split']==source['split'])
        ok(kind+' N '+row['id'],row['N']==(source['N_shape_estimate'] if kind in ('shape_N','both') else source['N']))
        expected=source['D_declared_budget'] if kind in ('declared_D','both') and source['D_declared_budget'] is not None else source['D']
        ok(kind+' D '+row['id'],row['D']==expected)
def records(nscale=1e9,loss=3.):
    return [dict(id=str(i),N=(i+1)*nscale,D=(i+1)*1e10,loss=loss,split='fit' if i<4 else 'holdout',control_id='test') for i in range(5)]
probes=[]
for name,fn in [
 ('large finite loss',lambda:b.fit(records(loss=1e308),[(.2,.3)])),
 ('bad grid candidate precedes representable',lambda:b.fit(records(1e-300),[(2.,.3),(.2,.3)])),
 ('representable candidate alone',lambda:b.fit(records(1e-300),[(.2,.3)])),
 ('large representable column QR',lambda:b.least_squares([[1e200,2e200,3e200,4e200]],[1.,2.,3.,4.])),
 ('representable multi-heldout RMSE',lambda:b.fit([dict(id=str(i),N=(i+1)*1e9,D=(i+1)*1e10,loss=3. if i<4 else 1e308,split='fit' if i<4 else 'holdout',control_id='x') for i in range(8)],[(.2,.3)])),
 ('infinite public NNLS',lambda:b.nonnegative_fit([[1.,1.,1.]]*4,[float('inf')]*4)),
]:
    try:
        value=fn();probes.append(dict(name=name,outcome='returned',value=value))
    except Exception as e:probes.append(dict(name=name,outcome=type(e).__name__,message=str(e)))
out=dict(check_count=len(checks),checks=checks,probes=probes,boundary_sha256=hashlib.sha256((BASE/'scaling-boundary-fit/boundary_fit.py').read_bytes()).hexdigest(),adapter_sha256=hashlib.sha256((p/'adapt_statistical.py').read_bytes()).hexdigest())
(HERE/'results.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(check_count=len(checks),probes=probes),indent=2))
