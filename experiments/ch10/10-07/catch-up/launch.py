"""Explicitly authorized sequential execution; no execution without --execute."""
import argparse,hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
B=Path(__file__).resolve().parent

def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def mem_available():
 return int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024

def group(pid):
 rows=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   raw=(p/'stat').read_text();v=raw[raw.rfind(')')+2:].split()
   if int(v[2])==pid and v[0]!='Z':rows.append(dict(pid=int(p.name),ppid=int(v[1]),birth=int(v[19]),rss_bytes=int(v[21])*os.sysconf('SC_PAGE_SIZE')))
  except (FileNotFoundError,ProcessLookupError,PermissionError):pass
 return rows

def main(a):
 if not a.execute:raise SystemExit('Prepared only. Actual CPU execution requires --execute after resource scheduling.')
 assert sys.platform=='linux';assert mem_available()>=28*1024**3,'Wait for root: MemAvailable below 28GiB';out=B/a.name;out.mkdir(exist_ok=False);records=[];resource=[]
 for mode in ['from_seed','from_fault3','from_normal23']:
  cmd=['taskset','-c','8,9',sys.executable,'-B',str(B/'run_worker.py'),'--mode',mode,'--output',str(out/mode),'--historical-root',a.historical_root]
  env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
  with (out/f'{mode}.log').open('w') as log:
   proc=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);start=time.monotonic();error=None
   try:
    while proc.poll() is None:
     own=group(proc.pid);available=mem_available();resource.append(dict(mode=mode,time=time.monotonic(),mem_available_bytes=available,rss_bytes=sum(v['rss_bytes'] for v in own),members=own));assert available>25*1024**3,'Global available memory reached 25GiB: stop only own tree';assert resource[-1]['rss_bytes']<=1024**3,'Own process group RSS exceeds 1GiB';assert time.monotonic()-start<120,'Own path deadline';time.sleep(.1)
    code=proc.wait();assert code==0,(mode,code)
   except BaseException as exc:
    error=repr(exc);raise
   finally:
    # This PGID was freshly allocated by start_new_session and includes only this path.
    if proc.poll() is None:
     assert os.getpgid(proc.pid)==proc.pid;os.killpg(proc.pid,signal.SIGTERM)
     try:proc.wait(timeout=10)
     except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=10)
    leftovers=group(proc.pid);records.append(dict(mode=mode,pid=proc.pid,start=start,end=time.monotonic(),returncode=proc.returncode,error=error,leftovers=leftovers));dump(out/'execution.json',records);dump(out/'resources.json',resource)
   assert not leftovers
 print(json.dumps(dict(complete=True,paths=3,peak_rss_bytes=max(x['rss_bytes'] for x in resource))))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--historical-root',default='/home/ubuntu/ai-infra-book-experiments/ch10/10-07');p.add_argument('--execute',action='store_true');main(p.parse_args())
