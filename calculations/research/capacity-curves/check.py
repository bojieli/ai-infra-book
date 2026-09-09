from pathlib import Path
import importlib.util,json,sys,hashlib
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
sys.path.insert(0,str(PROJECT/'src'))
module_path=HERE/'public/src/infra_calc/capacity_plot.py'
spec=importlib.util.spec_from_file_location('capacity_plot',module_path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
data=m.calculate();checks=0
# Independent boundary rule: every rank must fit n; at least one must fail n at threshold-1.
for panel in data['panels']:
 source=json.loads(m.source_path(panel['model'],24).read_text());workspace=source['scenario']['workspace_bytes']
 for curve in panel['curves']:
  rows=[next(f for f in rank['formats'] if f['bits']==curve['bits']) for rank in source['ranks']]
  for point in curve['points'][1:-1]:
   n=point['maximum_requests'];c=point['capacity_bytes']
   assert all(r['weight_bytes']+workspace+n*r['kv_bytes_per_request']<=c for r in rows)
   assert any(r['weight_bytes']+workspace+n*r['kv_bytes_per_request']>c-1 for r in rows)
   assert any(r['weight_bytes']+workspace+(n+1)*r['kv_bytes_per_request']>c for r in rows)
   checks+=3
# Worst-rank ownership changes as cohort grows; do not assume fixed limiting rank.
ranks=[{'formats':[{'bits':16,'weight_bytes':100,'kv_bytes_per_request':1}]}, {'formats':[{'bits':16,'weight_bytes':20,'kv_bytes_per_request':10}]}]
assert m.threshold(ranks,16,0,1)==101
assert m.threshold(ranks,16,0,10)==120
checks+=2
files=[module_path,*sorted((HERE/'figures').glob('*'))]
report={'checks':checks,'passed':checks,'source_files':12,'panels':4,'series':12,'bindings':[{'file':str(f.relative_to(HERE)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]}
(HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(checks)
