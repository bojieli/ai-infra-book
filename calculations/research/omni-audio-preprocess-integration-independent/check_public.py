"""Actual CLI replay plus isolated copy fault injection; no public mutations."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
P=HERE.parents[1]
C=HERE.parent/'omni-audio-preprocess/public'
module=P/'src/infra_calc/topics/omni_audio_preprocess.py'
assert module.read_bytes()==(C/'src/infra_calc/topics/omni_audio_preprocess.py').read_bytes()
for row in json.loads((C/'copy-manifest.json').read_text()):
    assert (P/row['project_target']).read_bytes()==(C/row['candidate_file']).read_bytes()
checks=[]
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    for scene in json.loads((C/'book.append.json').read_text()):
        inp=tmp/'input.json';inp.write_text(json.dumps({k:v for k,v in scene.items() if k!='id'}))
        for fmt in ('json','md'):
            p=subprocess.run([sys.executable,str(P/'calc.py'),'omni-audio-preprocess','--inputs',str(inp),'--format',fmt],capture_output=True,text=True)
            assert p.returncode==0,p.stderr
            if fmt=='json':assert json.loads(p.stdout)==json.loads((C/'results'/(scene['id']+'.json')).read_text())
            else:assert p.stdout.rstrip()==(C/'results'/(scene['id']+'.md')).read_text().rstrip()
            checks.append('actual CLI:'+scene['id']+':'+fmt)
    copied=tmp/'sources'
    shutil.copytree(P/'sources/omni-audio-preprocess',copied)
    # Run actual public CLI dispatch, replacing only source root with isolated clone.
    code="""import sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from infra_calc.topics import omni_audio_preprocess as m
from infra_calc.cli import main
m.HERE=Path(sys.argv[2])
sys.argv=['calc.py','omni-audio-preprocess']
main()
"""
    target=copied/'sources/preprocessor_config.json';original=target.read_bytes()
    for fault in ('missing','same_size_tamper'):
        if fault=='missing':target.unlink()
        else:target.write_bytes(original.replace(b'4800000',b'4800001'))
        p=subprocess.run([sys.executable,'-c',code,str(P/'src'),str(copied)],capture_output=True,text=True)
        assert p.returncode!=0
        assert ('Source mismatch' in p.stderr) if fault=='same_size_tamper' else ('No such file' in p.stderr)
        assert not p.stdout.strip()
        checks.append('public CLI rejection isolated source clone:'+fault)
        target.write_bytes(original)
    assert hashlib.sha256(target.read_bytes()).hexdigest()==hashlib.sha256((P/'sources/omni-audio-preprocess/sources/preprocessor_config.json').read_bytes()).hexdigest()
# Public source files never touched and still equal all staged originals.
for row in json.loads((C/'copy-manifest.json').read_text()):
    assert (P/row['project_target']).read_bytes()==(C/row['candidate_file']).read_bytes()
p=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(P/'tests'),'-p','test_omni_audio_preprocess.py','-v'],capture_output=True,text=True)
assert p.returncode==0 and 'Ran 6 tests' in p.stderr
(HERE/'public-tests.log').write_text(p.stdout+p.stderr)
(HERE/'public-results.json').write_text(json.dumps({'checks':checks,'public_tests':6,'public_module_sha':hashlib.sha256(module.read_bytes()).hexdigest(),'cli_sha':hashlib.sha256((P/'src/infra_calc/cli.py').read_bytes()).hexdigest(),'source_copy_count':10,'fault_scope':'Public CLI implementation with HERE redirected to isolated exact source clone; no shared sources modified'},indent=2)+'\n')
print('Public CLI 8 outputs, 2 rejection cases, 6 tests passed')
