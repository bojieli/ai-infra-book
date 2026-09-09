"""Read-only public trace bridge integration, with isolated source faults."""
from pathlib import Path
import ast
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
HERE=Path(__file__).resolve().parent;P=HERE.parents[1];C=HERE.parent/'trace-resource-bridge/public'
checks=[]
def check(name,ok):
    assert ok,name
    checks.append(name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for row in json.loads((C.parent/'bindings.json').read_text())['files']:
    check('freeze:'+row['file'],sha(P/row['file'])==row['sha256'])
module=P/'src/infra_calc/topics/trace_resource_bridge.py';candidate=C/'src/infra_calc/topics/trace_resource_bridge.py'
check('public exact module',module.read_bytes()==candidate.read_bytes())
for row in json.loads((C/'copy-manifest.json').read_text()):
    check('copy:'+row['project_target'],(P/row['project_target']).read_bytes()==(C/row['candidate_file']).read_bytes())
sys.path.insert(0,str(P/'src'))
from infra_calc.topics import trace_resource_bridge as m
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    for scene in json.loads((C/'book.append.json').read_text()):
        inputs={k:v for k,v in scene.items() if k!='id'}
        result=m.calculate(**inputs);expected=json.loads((C/'results'/(scene['id']+'.json')).read_text())
        check('allfields:'+scene['id'],json.loads(json.dumps(result))==expected)
        check('replay:'+scene['id'],m.calculate(**result['scenario'])==result)
        check('observed calls remain unknown:'+scene['id'],result['summary']['observed_model_forward_calls'] is None)
        for call in result['calls']:
            check('observed percall unknown:'+scene['id']+str(call['request']),call['mapping']['observed_model_forward_calls'] is None)
            check('observed lengths mapped:'+scene['id']+str(call['request']),call['mapping']['prefix_tokens']+call['mapping']['new_tokens']==call['recorded']['input_tokens'])
            if result['scenario']['generation_policy']=='unknown_steps':
                check('unknown default preserved:'+str(call['request']),call['mapping']['sampled_steps'] is None and call['mapping']['decode_forward_calls'] is None and call['resources']['decode'] is None and call['resources']['complete_logical_totals'] is None and call['resources']['final_state_bytes'] is None)
            else:
                check('serial declared G-1:'+str(call['request']),call['mapping']['decode_forward_calls']==call['recorded']['returned_id_tokens']-1)

        inp=tmp/'input.json';inp.write_text(json.dumps(inputs))
        for fmt in ('json','md'):
            proc=subprocess.run([sys.executable,str(P/'calc.py'),'trace-resource-bridge','--inputs',str(inp),'--format',fmt],capture_output=True,text=True)
            check('CLI status:'+scene['id']+fmt,proc.returncode==0)
            check('CLI equality:'+scene['id']+fmt,json.loads(proc.stdout)==expected if fmt=='json' else proc.stdout.rstrip()==(C/'results'/(scene['id']+'.md')).read_text().rstrip())
    dest=tmp/'sources';shutil.copytree(P/'sources/trace-resource-bridge',dest)
    rows=json.loads((dest/'sources.lock.json').read_text());target=dest/rows[0]['file'];raw=target.read_bytes()
    code="""from pathlib import Path
import sys
sys.path.insert(0,sys.argv[1])
from infra_calc.topics import trace_resource_bridge as m
from infra_calc.cli import main
m.SOURCE_ROOT=Path(sys.argv[2])
sys.argv=['calc.py','trace-resource-bridge']
main()
"""
    for fault in ('missing','same_length_tamper'):
        if fault=='missing':target.unlink()
        else:target.write_bytes(bytes([raw[0]^1])+raw[1:])
        proc=subprocess.run([sys.executable,'-c',code,str(P/'src'),str(dest)],capture_output=True,text=True)
        check('reject:'+fault,proc.returncode!=0 and not proc.stdout.strip())
        if fault=='same_length_tamper':check('checksum diagnostic','Sealed trace source mismatch' in proc.stderr)
        target.write_bytes(raw)
proc=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(P/'tests'),'-p','test_trace_resource_bridge.py','-v'],capture_output=True,text=True)
(HERE/'tests.log').write_text(proc.stdout+proc.stderr)
check('4tests zero skips',proc.returncode==0 and 'Ran 4 tests' in proc.stderr and 'skipped=' not in proc.stderr)
(HERE/'results.json').write_text(json.dumps({'count':len(checks),'checks':checks,'module_sha':sha(module),'cli_sha':sha(P/'src/infra_calc/cli.py')},indent=2)+'\n')
print(len(checks),'checks passed')
