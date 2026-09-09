"""Independently score unique generated code with the original six-case fixture."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parent
root=ROOT/'runs/history-001';codes={}
for path in sorted(root.glob('r*/requests.jsonl')):
    for line in path.read_text().splitlines():
        row=json.loads(line)
        try:action=json.loads(row['text'])
        except json.JSONDecodeError:continue
        if action.get('tool')!='write_file':continue
        code=action['content'];digest=hashlib.sha256(code.encode()).hexdigest()
        if digest not in codes:codes[digest]={'code':code,'requests':[]}
        codes[digest]['requests'].append(row['id'])
out=ROOT/'code-quality';out.mkdir(exist_ok=True);results=[]
for digest,entry in sorted(codes.items()):
    tree=ast.parse(entry['code'])
    assert len(tree.body)==1 and isinstance(tree.body[0],ast.FunctionDef)
    assert tree.body[0].name=='merge_intervals'
    assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) for n in ast.walk(tree))
    (out/(digest+'.py')).write_text(entry['code'])
    with tempfile.TemporaryDirectory() as d:
        tmp=Path(d);(tmp/'intervals.py').write_text(entry['code'])
        (tmp/'test_intervals.py').write_bytes((ROOT/'test_intervals.py').read_bytes())
        process=subprocess.run([sys.executable,'test_intervals.py'],cwd=tmp,
                               timeout=5,capture_output=True,text=True)
        record=dict(code_sha256=digest,requests=entry['requests'],exit_code=process.returncode,
                    stdout=process.stdout,stderr=process.stderr)
        assert process.returncode==0
        parsed=json.loads(process.stdout);record['passed_cases']=sum(x['passed'] for x in parsed['cases'])
        record['cases']=len(parsed['cases']);record['all_passed']=parsed['passed']
        results.append(record)
result=dict(fixture_sha256=hashlib.sha256((ROOT/'test_intervals.py').read_bytes()).hexdigest(),
            unique_codes=results,scope='Independent generated-code checks only; no replayed tool timeline or new Agent success claim')
(ROOT/'code-quality.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps([{'code':x['code_sha256'],'requests':len(x['requests']),'passed':x['passed_cases'],'cases':x['cases']} for x in results]))
