import json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent
start=time.monotonic_ns()
with (R/'run.log').open('x') as f:
    p=subprocess.Popen([sys.executable,str(R/'run.py'),'--release',str(R/'GPU-RELEASE.json'),'--released-pids','2490395','2531457'],stdout=f,stderr=subprocess.STDOUT)
    (R/'controller-launch.json').write_text(json.dumps(dict(pid=p.pid,launcher_pid=os.getpid(),start_ns=start),indent=2)+'\n')
    code=p.wait()
(R/'controller-exit.json').write_text(json.dumps(dict(pid=p.pid,exit_code=code,start_ns=start,end_ns=time.monotonic_ns()),indent=2)+'\n')
sys.exit(code)
