import hashlib,json,subprocess,sys
from pathlib import Path
from fixture import limits
R=Path(__file__).resolve().parent;out=R/'results';records=[]
for row in [json.loads(l) for l in (out/'raw.jsonl').read_text().splitlines()]:
 if 'write' not in row['result']:
  records.append(dict(case_index=row['case_index'],status='no_generated_code'));continue
 path=out/f"case{row['case_index']}"/'intervals.py'
 proc=subprocess.run([sys.executable,str(R/'check_code.py'),str(path),'--child'],capture_output=True,text=True,timeout=5,preexec_fn=limits)
 record=dict(case_index=row['case_index'],returncode=proc.returncode,stdout=proc.stdout,stderr=proc.stderr,code_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
 if proc.returncode==0:record['checks']=json.loads(proc.stdout)
 records.append(record)
(out/'independent-checks.json').write_text(json.dumps(dict(records=records,source_hashes={f:hashlib.sha256((R/f).read_bytes()).hexdigest() for f in ['check_all.py','check_code.py','fixture.py']}),indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k not in ['stdout','checks']} for r in records]))
