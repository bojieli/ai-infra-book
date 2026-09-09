from pathlib import Path
import json,subprocess,sys,tempfile,hashlib
H=Path(__file__).resolve().parent
P=H.parents[1]
C=H.parent/'granularity-selection'
checks=[]
with tempfile.TemporaryDirectory() as tmp:
    for scene in json.loads((C/'scenarios.json').read_text()):
        inp=Path(tmp)/'input.json';inp.write_text(json.dumps({k:v for k,v in scene.items() if k!='id'}))
        for fmt in ('json','md'):
            actual=subprocess.run([sys.executable,str(P/'calc.py'),'granularity-selection','--inputs',str(inp),'--format',fmt],capture_output=True,text=True,check=True).stdout
            expected=(C/(scene['id']+'.'+fmt)).read_text()
            assert (json.loads(actual)==json.loads(expected)) if fmt=='json' else actual.rstrip()==expected.rstrip()
            checks.append(scene['id']+':'+fmt)
files=['src/infra_calc/topics/granularity_selection.py','src/infra_calc/cli.py','src/infra_calc/reproduce.py','src/infra_calc/report.py','src/infra_calc/outline.py','scenarios/book.json']
(H/'cli-verification.json').write_text(json.dumps(dict(checks=checks,hashes={f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in files}),indent=2)+'\n')
print('8 CLI outputs equal reviewed candidates')
