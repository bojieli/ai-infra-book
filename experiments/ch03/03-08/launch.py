"""Own-session local CPU training watchdog."""
import argparse,json,os,signal,subprocess,sys,time
from pathlib import Path
B=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--smoke',action='store_true');a=p.parse_args()
assert Path(a.name).name==a.name and a.name not in ('.','..')
root=B/a.name;assert not root.exists()
env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',VECLIB_MAXIMUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1')
cmd=[sys.executable,'-B',str(B/'run.py'),'--output',str(root)]+(['--smoke'] if a.smoke else [])
start=time.time();samples=[];reason=None
with (B/(a.name+'.log')).open('x') as log:
 child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 while child.poll() is None:
  try:
   rows=[list(map(int,l.split())) for l in subprocess.check_output(['ps','-axo','pid,ppid,rss'],text=True).splitlines()[1:] if len(l.split())==3]
   own={child.pid};previous=set()
   while own!=previous:
    previous=own.copy();own.update(r[0] for r in rows if r[1] in own)
   rss=sum(r[2]*1024 for r in rows if r[0] in own);samples.append(dict(time=time.time(),pids=sorted(own),rss_bytes=rss))
   if rss>8*1024**3 or time.time()-start>1200:reason='own process-tree resource/deadline guard';break
  except Exception as e:reason=repr(e);break
  time.sleep(.5)
 if reason:
  os.killpg(child.pid,signal.SIGTERM)
  try:child.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL)
 code=child.wait()
(B/(a.name+'-supervisor.json')).write_text(json.dumps(dict(pid=child.pid,start=start,end=time.time(),exit_code=code,reason=reason,peak_rss_bytes=max([s['rss_bytes'] for s in samples],default=0),samples=samples),indent=2)+'\n')
print('EXIT',code,'reason',reason);sys.exit(code if code>=0 else 128-code)
