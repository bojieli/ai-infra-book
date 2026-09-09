"""Read-only migration verification; no result regeneration in author folders."""
import ast
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
CALC=HERE.parents[1]
PUBLIC=HERE.parent/'v4-hc-training-completion/public'
sys.path.insert(0,str(CALC/'src'))
from infra_calc import topics
topics.__path__.insert(0,str(PUBLIC/'src/infra_calc/topics'))
from infra_calc.topics import v4_training_primitives as p, v4_hc_training as h
checks=[]
def check(name, value):
    assert value,name
    checks.append(name)

def functions(path):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}

old_p=HERE.parent/'v4-training-reference/src/infra_calc/topics/v4_training_primitives.py'
old_h=HERE.parent/'v4-hc-training-completion/src/v4_hc_training.py'
for old,new in [(old_p,Path(p.__file__)),(old_h,Path(h.__file__))]:
    a,b=functions(old),functions(new)
    for name,tree in a.items():check(old.name+' AST '+name,tree==b[name])
    check(new.name+' no research loader','importlib' not in new.read_text() and 'Path(__file__)' not in new.read_text())
check('normal primitive import identity',h.primitive is p)
scenes=json.loads((PUBLIC/'book.append.json').read_text())
for topic,module,folder,names in [
    ('v4-training-primitives',p,HERE.parent/'v4-training-reference/results',['one-row','128-tokens','batch2']),
    ('v4-hc-training',h,HERE.parent/'v4-hc-training-completion/results',['one-row','default','batch2'])]:
    for scene,name in zip(scenes[topic],names):
        actual=module.calculate(**{k:v for k,v in scene.items() if k!='id'})
        check(scene['id']+' old result',actual==json.loads((folder/(name+'.json')).read_text()))
        check(scene['id']+' public JSON',actual==json.loads((PUBLIC/'results'/(scene['id']+'.json')).read_text()))
        check(scene['id']+' replay',actual==module.calculate(**actual['scenario']))
        report=module.markdown(actual)
        check(scene['id']+' MD replay',report==(PUBLIC/'results'/(scene['id']+'.md')).read_text())
        # Independently traverse the object and check exact table cell values.
        stack=[('',actual)]
        while stack:
            path,value=stack.pop()
            if isinstance(value,dict) and value:
                stack.extend(((path+'.' if path else '')+k,v)for k,v in value.items())
            elif isinstance(value,list) and value:
                stack.extend((f'{path}[{i}]',v)for i,v in enumerate(value))
            else:
                rendered='unknown (null)' if value is None else str(value)
                rendered=rendered.replace('\n','<br>').replace('|','&#124;')
                check(scene['id']+' leaf '+path,f'| {path} | {rendered} |' in report)
subset=json.loads((PUBLIC/'sources.lock.subset.json').read_text())['sources']
public=json.loads((CALC/'configs/sources.lock.json').read_text())['sources']
check('54 sources',len(subset)==54)
for entry in subset:
    check('source already public '+entry['file'],entry in public)
    raw=(CALC/entry['file']).read_bytes()
    check('source bytes '+entry['file'],len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256'])
binding=json.loads((PUBLIC/'bindings.json').read_text())
for entry in binding['artifacts']+binding['dependencies']:
    check('binding '+entry['file'],hashlib.sha256((CALC.parent/entry['file']).read_bytes()).hexdigest()==entry['sha256'])
(HERE/'public-results.json').write_text(json.dumps(dict(check_count=len(checks),checks=checks,module_sha256={Path(module.__file__).name:hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest() for module in [p,h]}),indent=2)+'\n')
print(len(checks),'checks passed')
