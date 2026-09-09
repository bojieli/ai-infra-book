"""Verify frozen mathematical AST and every scenario leaf across public migration."""
from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
for parent in HERE.parents:
    if (parent / 'src/infra_calc/sources.py').is_file():
        sys.path.insert(0, str(parent / 'src'))
        break
module_path = HERE / 'src/infra_calc/topics/training_input_supply.py'
spec = importlib.util.spec_from_file_location('candidate_supply', module_path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
def functions(path):
    return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef)}
old = functions(HERE.parent/'calculate.py')
new = functions(module_path)
assert all(new[k] == v for k,v in old.items())
scenes = json.loads((HERE/'scenarios.json').read_text())
for scene in scenes:
    r = m.calculate(**{k:v for k,v in scene.items() if k != 'id'})
    assert r == json.loads((HERE/'results'/(scene['id']+'.json')).read_text())
    assert r == m.calculate(**r['scenario'])
    assert json.loads(m.markdown(r).split('```json\n')[1].split('\n```')[0]) == r
out = {'unchanged_function_asts':list(old), 'scenario_replays':len(scenes), 'report_full_json_replay':len(scenes), 'module_sha':hashlib.sha256(module_path.read_bytes()).hexdigest()}
(HERE/'migration-verification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
