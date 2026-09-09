import argparse,hashlib,json,os,platform,random,resource,subprocess,sys,time
from pathlib import Path

def worker(mode):
 start=time.monotonic();mem=bytearray(64*1024**2)
 for i in range(0,len(mem),4096):mem[i]=1
 ready=time.monotonic();cpu=time.process_time();digest=None
 if mode=='wait':time.sleep(.4)
 else:
  h=hashlib.sha256()
  for _ in range(250000):h.update(b'x'*256)
  digest=h.hexdigest()
 end=time.monotonic()
 print(json.dumps(dict(pid=os.getpid(),start=start,ready=ready,end=end,cpu_work=time.process_time()-cpu,cpu_total=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,digest=digest,memory_check=sum(mem[::4096]))),flush=True)

def main(out):
 out.mkdir(exist_ok=False);root=Path(__file__).resolve().parent
 (out/'environment.json').write_text(json.dumps(dict(platform=platform.platform(),python=sys.version,clock_tick=os.sysconf('SC_CLK_TCK'),source_sha256=hashlib.sha256((root/'run.py').read_bytes()).hexdigest(),rss_definition='Sum of individual VmRSS, shared pages double counted; not PSS or cgroup memory',sampling_target_s=.01),indent=2))
 order=[dict(trial=t,mode=m,arrival=a) for t in range(3) for m,a in [('wait','burst'),('cpu','burst'),('cpu','stagger')]];random.Random(1101).shuffle(order)
 (out/'order.json').write_text(json.dumps(order,indent=2))
 for index,case in enumerate(order):
  start=time.monotonic();procs=[];samples=[];done={};launch=[]
  while len(done)<4:
   now=time.monotonic();n=len(procs)
   if n<4 and now-start >= (n*.15 if case['arrival']=='stagger' else 0):
    p=subprocess.Popen([sys.executable,str(root/'run.py'),'--worker',case['mode']],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);procs.append(p);launch.append(dict(pid=p.pid,at=time.monotonic(),scheduled=start+(n*.15 if case['arrival']=='stagger' else 0)))
    continue
   rows=[]
   for p in procs:
    if p.pid in done:continue
    try:
     status=Path(f'/proc/{p.pid}/status').read_text();rss=next((int(x.split()[1])*1024 for x in status.splitlines() if x.startswith('VmRSS:')),0)
     stat=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split();rows.append(dict(pid=p.pid,rss=rss,cpu_ticks=int(stat[11])+int(stat[12])))
    except FileNotFoundError:pass
    if p.poll() is not None:
     stdout,stderr=p.communicate();done[p.pid]=dict(returncode=p.returncode,stdout=stdout,stderr=stderr,reaped=time.monotonic())
   samples.append(dict(at=time.monotonic(),processes=rows));time.sleep(.01)
  record=dict(index=index,**case,start=start,end=time.monotonic(),launch=launch,samples=samples,completed=done)
  (out/f'case{index}.json').write_text(json.dumps(record,indent=2));print(index,case,'done',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--worker',choices=['wait','cpu']);p.add_argument('--output',type=Path,default=Path('results'));a=p.parse_args()
 if a.worker:worker(a.worker)
 else:main(a.output)
