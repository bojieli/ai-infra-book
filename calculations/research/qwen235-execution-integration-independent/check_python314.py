"""Explicit cross-interpreter tolerance for only the final phase-sum scalar."""
from pathlib import Path
import copy,json,math,os,subprocess
HERE=Path(__file__).resolve().parent;CALC=HERE.parents[1];CAND=CALC/'research/qwen235-execution/public'
exe='/opt/homebrew/bin/python3.14';rows=[]
for scene in json.loads((CAND/'book.append.json').read_text()):
 inputs=HERE/(scene['id']+'.inputs.json');inputs.write_text(json.dumps({k:v for k,v in scene.items() if k!='id'})+'\n')
 run=subprocess.run([exe,str(CALC/'calc.py'),'qwen235-execution','--inputs',str(inputs)],check=True,text=True,capture_output=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 current=json.loads(run.stdout);frozen=json.loads((CAND/'results'/(scene['id']+'.json')).read_text())
 a=current['summary'].pop('conditional_phase_barrier_bound_seconds');b=frozen['summary'].pop('conditional_phase_barrier_bound_seconds')
 assert current==frozen,'Unexpected cross-version field change: '+scene['id']
 assert math.isclose(a,b,rel_tol=1e-13,abs_tol=1e-16)
 rows.append(dict(id=scene['id'],python314=a,frozen_python311=b,absolute_difference=abs(a-b),all_other_fields_exact=True,accepted=True))
result=dict(interpreter=subprocess.check_output([exe,'--version'],text=True).strip(),scope='Only summary.conditional_phase_barrier_bound_seconds gets rel1e-13/abs1e-16; every other field exact',scenarios=rows)
(HERE/'python314-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
