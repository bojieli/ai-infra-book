"""Check actual public CLI JSON/Markdown against the reviewed candidate."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import hashlib
HERE=Path(__file__).resolve().parent
P=HERE.parents[1]
C=HERE.parent/'v4-mtp-forward'
checks=[]
with tempfile.TemporaryDirectory() as tmp:
    for scene in json.loads((C/'scenarios.json').read_text()):
        inp=Path(tmp)/'inputs.json'
        inp.write_text(json.dumps({k:v for k,v in scene.items() if k!='id'}))
        for fmt in ('json','md'):
            proc=subprocess.run([sys.executable,str(P/'calc.py'),'v4-mtp-forward','--inputs',str(inp),'--format',fmt],capture_output=True,text=True,check=True)
            expected=(C/'results'/(scene['id']+'.'+fmt)).read_text()
            assert (json.loads(proc.stdout)==json.loads(expected)) if fmt=='json' else proc.stdout.rstrip()==expected.rstrip()
            checks.append(scene['id']+':'+fmt)
files=['src/infra_calc/topics/v4_mtp_forward.py','src/infra_calc/cli.py','src/infra_calc/reproduce.py','src/infra_calc/report.py','src/infra_calc/outline.py','scenarios/book.json']
(HERE/'cli-verification.json').write_text(json.dumps(dict(checks=checks,hashes={f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in files}),indent=2)+'\n')
print('8 actual CLI outputs equal reviewed candidates')
