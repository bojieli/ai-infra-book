from pathlib import Path
import ast
import hashlib
import json
import sys
HERE=Path(__file__).resolve().parent;P=HERE.parents[1];C=HERE.parent/'capacity-curves'
sys.path.insert(0,str(P/'src'))
from infra_calc import capacity_plot as m
old=ast.parse((C/'public/src/infra_calc/capacity_plot.py').read_text());new=ast.parse((P/'src/infra_calc/capacity_plot.py').read_text())
def funcs(t):return {x.name:ast.dump(x,include_attributes=False) for x in t.body if isinstance(x,ast.FunctionDef)}
a,b=funcs(old),funcs(new)
for k in ('source_path','threshold','calculate'):assert a[k]==b[k]
r=m.calculate();assert r==json.loads((C/'figures/data.json').read_text())
(HERE/'static-results.json').write_text(json.dumps({'unchanged_functions':['source_path','threshold','calculate'],'data_equal':True,'module_sha':hashlib.sha256((P/'src/infra_calc/capacity_plot.py').read_bytes()).hexdigest()},indent=2)+'\n')
print('3 functions and full data equal')
