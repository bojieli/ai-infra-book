"""Public integration equality and nonmutating report-evidence failure injection."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,subprocess,sys
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;CALC=HERE.parents[1];CAND=CALC/'research/v4-optimizer/public';sys.path.insert(0,str(CALC/'src'))
from infra_calc.topics import v4_optimizer as public
from infra_calc import report
candidate_path=CAND/'src/infra_calc/topics/v4_optimizer.py'
spec=importlib.util.spec_from_file_location('optimizer_candidate',candidate_path);candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
checks=[]
def ck(label,ok):
 checks.append(dict(check=label,passed=bool(ok)))
 assert ok,label
old_ast=ast.parse(candidate_path.read_text());new_ast=ast.parse(Path(public.__file__).read_text())
# Remove only the known additional imports and report verification loop.
new_ast.body=[n for n in new_ast.body if not(isinstance(n,ast.Import) and any(a.name=='hashlib' for a in n.names)) and not(isinstance(n,ast.ImportFrom) and n.module=='infra_calc.paths')]
for node in new_ast.body:
 if isinstance(node,ast.FunctionDef) and node.name=='calculate':
  ck('New guard is first calculate statement',isinstance(node.body[0],ast.For) and 'v4-optimizer-report.lock.json' in ast.unparse(node.body[0]));node.body=node.body[1:]
ck('All remaining AST mathematics/output equal',ast.dump(old_ast,include_attributes=False)==ast.dump(new_ast,include_attributes=False))
scenes=json.loads((CAND/'scenarios.json').read_text());book=json.loads((CALC/'scenarios/book.json').read_text())['v4_optimizer'];ck('Four public scene inputs exact',[x['scenario'] for x in book]==[x['scenario'] for x in scenes] and len(book)==4)
for row in scenes:
 expected=candidate.calculate(**row['scenario']);actual=public.calculate(**row['scenario'])
 ck(row['id']+' candidate/public full JSON equality',expected==actual)
 ck(row['id']+' frozen JSON equality',json.loads(json.dumps(actual))==json.loads((CAND/'results'/(row['id']+'.json')).read_text()))
 ck(row['id']+' report dispatch equality',report.markdown(actual)==public.markdown(actual))
 inputs=HERE/(row['id']+'.inputs.json');inputs.write_text(json.dumps(row['scenario'])+'\n')
 cli=subprocess.run([sys.executable,str(CALC/'calc.py'),'v4-optimizer','--inputs',str(inputs)],check=True,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 ck(row['id']+' CLI full JSON equality',json.loads(cli.stdout)==json.loads(json.dumps(actual)))
cli=subprocess.run([sys.executable,str(CALC/'calc.py'),'v4-optimizer','--format','md'],check=True,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
ck('CLI markdown invokes custom report',cli.stdout.strip()==public.markdown(public.calculate()).strip())
locks=json.loads((CALC/'configs/v4-optimizer-report.lock.json').read_text());original_read=Path.read_bytes
for row in locks:
 target=CALC/row['file'];raw=target.read_bytes()
 ck(row['file']+' local SHA',hashlib.sha256(raw).hexdigest()==row['sha256'])
 ck(row['file']+' original archive exact',raw==(CALC.parent/row['original_file']).read_bytes())
 for failure in ['missing','changed']:
  def injected(path):
   if path==target:
    if failure=='missing':raise FileNotFoundError(str(target))
    return raw+b'changed'
   return original_read(path)
  with patch.object(Path,'read_bytes',injected):
   try:public.calculate()
   except (ValueError,FileNotFoundError) as error:ck(row['file']+' '+failure+' rejected',True)
   else:ck(row['file']+' '+failure+' rejected',False)
# Reproduction uses current local paths, records the lock in configs/*.json and dispatches calculate+save.
repro=(CALC/'src/infra_calc/reproduce.py').read_text()
ck('Reproduce binds local report inputs','PROJECT / row["file"] for row in json.loads((PROJECT / "configs/v4-optimizer-report.lock.json").read_text())' in repro)
ck('Reproduce four-scene loop','for row in scenarios.get("v4_optimizer", []):' in repro and 'result = v4_optimizer.calculate(**row["scenario"])' in repro)
files=[candidate_path,Path(public.__file__),CALC/'configs/v4-optimizer-report.lock.json',CALC/'src/infra_calc/report.py',CALC/'src/infra_calc/cli.py',CALC/'src/infra_calc/reproduce.py']+[CALC/r['file'] for r in locks]
bindings=[dict(file=str(p.relative_to(CALC)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
output=dict(checks=len(checks),passed=sum(c['passed'] for c in checks),failed=[c for c in checks if not c['passed']],bindings=bindings)
(HERE/'verification.json').write_text(json.dumps(output,indent=2)+'\n');(HERE/'checks.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(output,indent=2))
