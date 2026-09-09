import hashlib
import json
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
P=HERE.parent/'scaling-real-points/public'
sys.path.insert(0,str(ROOT/'src'))
from infra_calc import topics
topics.__path__.insert(0,str(P/'src/infra_calc/topics'))
from infra_calc.topics import real_scaling_fit as m
m.PROJECT=P
actual=m.calculate()
original=json.loads((P.parent/'statistical-fit.json').read_text())
checks=[]
def ok(name,x):
 assert x,name
 checks.append(name)
for label in ['primary',*actual['sensitivity']]:
 a=actual['primary'] if label=='primary' else actual['sensitivity'][label]
 b=original['primary'] if label=='primary' else original['sensitivity'][label]
 for key in ['law','fit_sse','holdout_rmse','candidates','rejected_candidates','fit_bounds']:
  ok(label+' '+key,a['result'][key]==b['result'][key])
 for x,y in zip(a['result']['predictions'],b['result']['predictions']):
  for key in ['id','N','D','loss','split','predicted_loss','residual','outside_fit_box']:
   ok(label+' '+x['id']+' '+key,x[key]==y[key])
for f in json.loads((P/'bindings.json').read_text())['files']:
 raw=(P/f['file']).read_bytes()
 ok('binding '+f['file'],len(raw)==f['bytes'] and hashlib.sha256(raw).hexdigest()==f['sha256'])
lock=json.loads((P/'configs/scaling-real-points.lock.json').read_text())
locked={x['file'] for x in lock}
for r in actual['records']:
 ok('evaluation in direct lock '+r['id'],r['evaluation']['file'] in locked)
 if r['budget_source']:ok('budget in direct lock '+r['id'],r['budget_source'] in locked)
ok('config itself locked','configs/scaling-real-points/data.json' in locked)
ok('original notebook locked','sources/scaling-real-points/utils/parametric_fit.ipynb' in locked)
(HERE/'public-results.json').write_text(json.dumps(dict(check_count=len(checks),checks=checks,module_sha256=hashlib.sha256((P/'src/infra_calc/topics/real_scaling_fit.py').read_bytes()).hexdigest()),indent=2)+'\n')
print(len(checks),'public checks passed')
