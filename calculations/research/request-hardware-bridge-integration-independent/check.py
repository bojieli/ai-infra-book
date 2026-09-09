"""Mechanical public integration audit against the frozen candidate."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
HERE=Path(__file__).resolve().parent;P=HERE.parents[1];C=HERE.parent/'request-hardware-bridge/public'
sys.path.insert(0,str(P/'src'))
from infra_calc.topics import request_hardware_bridge as m
from infra_calc.topics import request_model_comparison
checks=[]
def check(name,ok):
    assert ok,name
    checks.append(name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
module=P/'src/infra_calc/topics/request_hardware_bridge.py'
check('module byte equality',module.read_bytes()==(C/'src/infra_calc/topics/request_hardware_bridge.py').read_bytes())
for row in json.loads((C.parent/'bindings.json').read_text())['files']:
    check('freeze:'+row['file'],sha(P/row['file'])==row['sha256'])
hardware_before=(P/'configs/hardware.json').read_bytes()
with tempfile.TemporaryDirectory() as tmp:
    for scene in json.loads((C/'book.append.json').read_text()):
        kwargs={k:v for k,v in scene.items() if k!='id'}
        result=m.calculate(**kwargs);expected=json.loads((C/'results'/(scene['id']+'.json')).read_text())
        check('full frozen:'+scene['id'],json.loads(json.dumps(result))==expected)
        check('replay:'+scene['id'],result==m.calculate(**result['scenario']))
        old=result['original_request']
        check('original request preserved:'+scene['id'],old==request_model_comparison.calculate(**old['scenario']))
        for model in result['models']:
            check('runtime unknown:'+scene['id']+model['model'],model['complete_runtime_seconds'] is None and model['quality_equivalence'] is None)
            check('official versus scenario capacity:'+scene['id']+model['model'],model['capacity']['official_nominal_bytes']==result['device']['memory']['nominal_capacity']*10**9)
            for call in model['calls']:
                check('physical HBM unknown:'+scene['id']+model['model']+str(len(checks)),call['work']['physical_hbm_bytes'] is None)
        check('positive unresolved PV:'+scene['id'],result['models'][0]['matrix_buckets']['matrix_pv_mixed_or_unresolved']>0 and result['rates']['matrix_pv_mixed_or_unresolved'] is None)
        inp=Path(tmp)/'input.json';inp.write_text(json.dumps(kwargs))
        for fmt in ('json','md'):
            proc=subprocess.run([sys.executable,str(P/'calc.py'),'request-hardware-bridge','--inputs',str(inp),'--format',fmt],capture_output=True,text=True)
            check('CLI:'+scene['id']+fmt,proc.returncode==0)
            check('CLI exact:'+scene['id']+fmt,json.loads(proc.stdout)==expected if fmt=='json' else proc.stdout.rstrip()==(C/'results'/(scene['id']+'.md')).read_text().rstrip())
check('hardware config unchanged',hardware_before==(P/'configs/hardware.json').read_bytes())
proc=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(P/'tests'),'-p','test_request_hardware_bridge.py','-v'],capture_output=True,text=True)
(HERE/'tests.log').write_text(proc.stdout+proc.stderr)
check('4 public tests zero skips',proc.returncode==0 and 'Ran 4 tests' in proc.stderr and 'skipped=' not in proc.stderr)
(HERE/'results.json').write_text(json.dumps({'count':len(checks),'checks':checks,'module_sha':sha(module),'hardware_sha':sha(P/'configs/hardware.json'),'cli_sha':sha(P/'src/infra_calc/cli.py')},indent=2)+'\n')
print(len(checks),'checks passed')
