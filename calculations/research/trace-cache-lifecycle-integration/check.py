"""Actual CLI outputs must preserve all reviewed candidate fields."""
from pathlib import Path
import json,subprocess,sys,tempfile,hashlib
H=Path(__file__).resolve().parent
P=H.parents[1]
C=H.parent/'trace-cache-lifecycle'
checks=[]
with tempfile.TemporaryDirectory() as tmp:
    for name,kwargs in [('default',{}),('host50gb',{'host_bytes_per_second':50_000_000_000}),('lookup2ms',{'lookup_ns':2_000_000})]:
        inp=Path(tmp)/'input.json';inp.write_text(json.dumps(kwargs))
        for fmt in ('json','md'):
            actual=subprocess.run([sys.executable,str(P/'calc.py'),'trace-cache-lifecycle','--inputs',str(inp),'--format',fmt],capture_output=True,text=True,check=True).stdout
            expected=(C/(name+'.'+fmt)).read_text()
            assert (json.loads(actual)==json.loads(expected)) if fmt=='json' else actual.rstrip()==expected.rstrip()
            checks.append(name+':'+fmt)
files=['src/infra_calc/topics/trace_cache_lifecycle.py','src/infra_calc/cli.py','src/infra_calc/reproduce.py','src/infra_calc/report.py','src/infra_calc/outline.py','scenarios/book.json']
(H/'cli-verification.json').write_text(json.dumps(dict(checks=checks,hashes={f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in files}),indent=2)+'\n')
print('6 CLI outputs equal reviewed candidates')
