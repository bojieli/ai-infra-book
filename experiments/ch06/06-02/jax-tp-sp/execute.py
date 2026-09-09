"""Wait for the identified Mac experiment, then run the registered sequence."""
import argparse,json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--wait-pid',type=int,required=True);args=p.parse_args()
log=R/'execution.jsonl'
if log.exists():raise SystemExit('Refusing to overwrite prior execution')
def record(**kw):
 row=dict(time=time.time(),**kw)
 with log.open('a') as f:f.write(json.dumps(row)+'\n')
 print(json.dumps(row),flush=True)
def identity():
 r=subprocess.run(['ps','-p',str(args.wait_pid),'-o','lstart=,command='],capture_output=True,text=True)
 return r.stdout.strip() if r.returncode==0 else None
original=identity();record(event='wait_start',pid=args.wait_pid,identity=original)
deadline=time.monotonic()+1800
while original is not None and identity()==original:
 if time.monotonic()>deadline:
  record(event='wait_timeout');raise SystemExit(2)
 time.sleep(1)
record(event='wait_terminal_or_identity_changed',current_identity=identity())
steps=[('smoke',[sys.executable,'run.py','--smoke','--output','smoke']),('analyze-smoke',[sys.executable,'analyze.py','smoke']),('formal',[sys.executable,'run.py','--output','results']),('analyze-formal',[sys.executable,'analyze.py','results']),('plot',[sys.executable,'plot.py','results'])]
for name,command in steps:
 record(event='step_start',step=name,command=command)
 with (R/f'{name}.log').open('x') as f:
  result=subprocess.run(command,cwd=R,stdout=f,stderr=subprocess.STDOUT)
 record(event='step_exit',step=name,exit_code=result.returncode)
 if result.returncode:raise SystemExit(result.returncode)
record(event='sequence_complete')
