"""Run only after public C33 integration is stable; do not modify public files."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
HERE=Path(__file__).resolve().parent;CALC=HERE.parents[1];CAND=CALC/'research/qwen235-execution/public';sys.path.insert(0,str(CALC/'src'))
from infra_calc.topics import qwen235_execution as public
from infra_calc import report
checks=[]
def ck(label,value):
 checks.append(dict(check=label,passed=bool(value)))
 assert value,label
candidate=CAND/'src/infra_calc/topics/qwen235_execution.py';publicpath=Path(public.__file__)
ck('Public module byte identical to frozen candidate',candidate.read_bytes()==publicpath.read_bytes())
ck('Frozen reviewed SHA',hashlib.sha256(candidate.read_bytes()).hexdigest()=='a4ee2e24fa01ea4854f974a26b8266c2d3c4bb37571ad9d418de58d33a7b48e2')
scenes=json.loads((CAND/'book.append.json').read_text());book=json.loads((CALC/'scenarios/book.json').read_text())['qwen235_execution']
ck('Seven public scenes exact',scenes==book and len(scenes)==7)
for scene in scenes:
 args={k:v for k,v in scene.items() if k!='id'};r=public.calculate(**args);frozen=json.loads((CAND/'results'/(scene['id']+'.json')).read_text())
 ck(scene['id']+' frozen JSON equality',r==frozen)
 ck(scene['id']+' custom report dispatch',report.markdown(r)==public.markdown(r))
 ck(scene['id']+' finite subaccount runtime unknown',r['summary']['full_request_runtime_seconds'] is None and r['summary']['actual_peak_bytes'] is None and any('Expert subaccount only' in line for line in r['scope']))
 inputs=HERE/(scene['id']+'.inputs.json');inputs.write_text(json.dumps(args)+'\n')
 run=subprocess.run([sys.executable,str(CALC/'calc.py'),'qwen235-execution','--inputs',str(inputs)],capture_output=True,text=True,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 ck(scene['id']+' real CLI JSON equal',json.loads(run.stdout)==r)
run=subprocess.run([sys.executable,str(CALC/'calc.py'),'qwen235-execution','--format','md'],capture_output=True,text=True,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
ck('Default CLI md uses custom renderer',run.stdout.strip()==public.markdown(public.calculate()).strip())
test=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(CALC/'tests'),'-p','test_qwen235_execution.py','-v'],capture_output=True,text=True,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
(HERE/'tests.log').write_text(test.stdout+test.stderr);ck('Five public tests run','Ran 5 tests' in test.stderr and 'OK' in test.stderr)
files=[candidate,publicpath,CALC/'src/infra_calc/cli.py',CALC/'src/infra_calc/report.py',CALC/'src/infra_calc/reproduce.py',CALC/'tests/test_qwen235_execution.py',CALC/'scenarios/book.json']
output=dict(checks=len(checks),passed=sum(c['passed'] for c in checks),failed=[c for c in checks if not c['passed']],bindings=[dict(file=str(p.relative_to(CALC)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files])
(HERE/'verification.json').write_text(json.dumps(output,indent=2)+'\n');(HERE/'checks.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(output,indent=2))
