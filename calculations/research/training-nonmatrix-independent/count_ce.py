"""Additional operation instrumentation for forward norm and mean CE."""
import importlib.util
from pathlib import Path
# Local counting class only; do not execute the full check.py test suite here.
import ast
p=Path(__file__).resolve().parent
source=ast.parse((p/'check.py').read_text())
selected=[n for n in source.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and getattr(n,'name',None) in ('Scalar','reduce','ordinary')]
from collections import Counter
namespace={'Counter':Counter};exec(compile(ast.Module(body=selected,type_ignores=[]),'<counter>','exec'),namespace)
Scalar,reduce,ordinary=(namespace[k] for k in ('Scalar','reduce','ordinary'))
checks=[]
for rows,width in [(1,1),(2,3),(3,7)]:
    Scalar.counts.clear()
    for _ in range(rows):
        x=[Scalar() for j in range(width)]
        variance=reduce([v*v for v in x])/width+Scalar()
        Scalar.counts['rsqrt']+=1;r=Scalar()
        output=[(v*r)*Scalar() for v in x]
    assert ordinary()==rows*(4*width+1)
    assert Scalar.counts['rsqrt']==rows
    checks.append(f'RMS forward R{rows}D{width}')
for rows,width in [(1,1),(2,3),(3,7)]:
    Scalar.counts.clear();losses=[];prob=[]
    for _ in range(rows):
        peak=Scalar();logits=[Scalar() for j in range(width)]
        e=[(v-peak).exp() for v in logits];den=reduce(e)
        losses.append(den.log()+peak-logits[0]);prob.append([v/den for v in e])
    loss=reduce(losses)/rows
    assert ordinary()==rows*(3*width+2)
    assert Scalar.counts['exp']==rows*width and Scalar.counts['log']==rows
    Scalar.counts.clear()
    for row in prob:
        row[0]=row[0]-1
        gradients=[value/rows for value in row]
    assert ordinary()==rows*(width+1)
    checks.append(f'meanCE forward/back R{rows}V{width}')
import json
(p/'ce-count-results.json').write_text(json.dumps(checks,indent=2)+'\n');print('PASS',len(checks),'additional count cases')
