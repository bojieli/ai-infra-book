"""Independent read-only candidate migration verification."""
from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
C = HERE.parent / 'omni-audio-preprocess/public'
checks=[]
def check(name, value):
    assert value, name
    checks.append(name)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
for row in json.loads((C/'bindings.json').read_text()):
    p=C/row['file']
    check('binding:'+row['file'],sha(p)==row['sha256'] and p.stat().st_size==row['bytes'])
original=C.parent/'omni_audio_preprocess.py'
module=C/'src/infra_calc/topics/omni_audio_preprocess.py'
def funcs(path):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
check('five complete function ASTs',funcs(original)==funcs(module) and len(funcs(module))==5)
for row in json.loads((C/'copy-manifest.json').read_text()):
    p=C/row['candidate_file']
    check('copy:'+row['candidate_file'],sha(p)==row['sha256'] and p.stat().st_size==row['bytes'])
lock=C/'sources/omni-audio-preprocess/sources.lock.json'
check('local source lock byte identical',lock.read_bytes()==(C.parent/'sources.lock.json').read_bytes())
for row in json.loads(lock.read_text())['sources']:
    check('original exact:'+row['file'],(lock.parent/row['file']).read_bytes()==(C.parent/row['file']).read_bytes())
sys.path.insert(0,str(PROJECT/'src'))
spec=importlib.util.spec_from_file_location('candidate',module)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.HERE=lock.parent
for scene in json.loads((C/'book.append.json').read_text()):
    r=m.calculate(**{k:v for k,v in scene.items() if k!='id'})
    for root in (C,C.parent):
        check('result:'+str(root)+scene['id'],r==json.loads((root/'results'/(scene['id']+'.json')).read_text()))
    check('replay:'+scene['id'],r==m.calculate(**r['scenario']))
    check('report:'+scene['id'],m.markdown(r)==(C/'results'/(scene['id']+'.md')).read_text())
p=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(C/'tests'),'-v'],capture_output=True,text=True)
(HERE/'tests.log').write_text(p.stdout+p.stderr)
check('six direct tests',p.returncode==0 and 'Ran 6 tests' in p.stderr and 'skipped=' not in p.stderr)
result={'checks':checks,'count':len(checks),'module_sha':sha(module),'original_sha':sha(original),'candidate_bindings_sha':sha(C/'bindings.json'),'public_present':(PROJECT/'src/infra_calc/topics/omni_audio_preprocess.py').is_file()}
(HERE/'migration-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
