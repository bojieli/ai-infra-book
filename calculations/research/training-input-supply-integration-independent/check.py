"""Read-only verification against the independently reviewed pre-migration freeze."""
from pathlib import Path
import ast
import hashlib
import json
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
ORIGINAL=HERE.parent/'training-input-supply'
C=ORIGINAL/'public'
PUBLIC=PROJECT/'src/infra_calc/topics/training_input_supply.py'
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def funcs(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
for row in json.loads((ORIGINAL/'bindings.json').read_text())['files']:
    check('original freeze:'+row['file'],sha(ORIGINAL/row['file'])==row['sha256'])
for row in json.loads((C/'bindings.json').read_text())['files']:
    check('migration freeze:'+row['file'],sha(C/row['file'])==row['sha256'])
for row in json.loads((HERE.parent/'training-input-supply-independent/bindings.json').read_text()):
    check('prior independent review binding:'+row['file'],sha(PROJECT/row['file'])==row['sha256'])
old=funcs(ORIGINAL/'calculate.py')
new=funcs(PUBLIC)
for name in ('calculate','schedule'):check('complete function AST:'+name,old[name]==new[name])
check('public module byte equality',PUBLIC.read_bytes()==(C/'src/infra_calc/topics/training_input_supply.py').read_bytes())
sys.path.insert(0,str(PROJECT/'src'))
from infra_calc.topics import training_input_supply as m
scenes=json.loads((C/'scenarios.json').read_text())
with tempfile.TemporaryDirectory() as tmp:
    for scene in scenes:
        inputs={k:v for k,v in scene.items() if k!='id'}
        result=m.calculate(**inputs)
        expected=json.loads((ORIGINAL/'results'/(scene['id']+'.json')).read_text())
        check('all fields:'+scene['id'],result==expected)
        check('replay:'+scene['id'],result==m.calculate(**result['scenario']))
        md=m.markdown(result)
        check('full report JSON:'+scene['id'],json.loads(md.split('```json\n')[1].split('\n```')[0])==result)
        inp=Path(tmp)/'input.json';inp.write_text(json.dumps(inputs))
        for fmt in ('json','md'):
            run=subprocess.run([sys.executable,str(PROJECT/'calc.py'),'training-input-supply','--inputs',str(inp),'--format',fmt],capture_output=True,text=True)
            check('CLI status:'+scene['id']+fmt,run.returncode==0)
            check('CLI all fields:'+scene['id']+fmt,json.loads(run.stdout)==expected if fmt=='json' else run.stdout.rstrip()==md.rstrip())
r=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(PROJECT/'tests'),'-p','test_training_input_supply.py','-v'],capture_output=True,text=True)
(HERE/'tests.log').write_text(r.stdout+r.stderr)
check('five public tests no skip',r.returncode==0 and 'Ran 5 tests' in r.stderr and 'skipped=' not in r.stderr)
(HERE/'results.json').write_text(json.dumps(dict(checks=checks,count=len(checks),module_sha=sha(PUBLIC),cli_sha=sha(PROJECT/'src/infra_calc/cli.py'),original_bindings_sha=sha(ORIGINAL/'bindings.json'),migration_bindings_sha=sha(C/'bindings.json')),indent=2)+'\n')
print(len(checks),'checks passed')
