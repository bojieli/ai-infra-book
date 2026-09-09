import argparse,hashlib,json,os,platform,signal,subprocess,sys,time
from pathlib import Path
B=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--smoke',action='store_true');a=p.parse_args();out=B/a.name;out.mkdir(exist_ok=False)
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
write(out/'environment.json',dict(platform=platform.platform(),python=sys.version,executable=sys.executable,source_sha256={str(f.relative_to(B)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [B/'model.py',B/'run_worker.py',B/'launch.py',B/'PROTOCOL.md',B/'data/input.txt',B/'data/source.json']},time=time.monotonic(),seeds=[1061] if a.smoke else [1061,1062,1063],checkpoints=[17] if a.smoke else [17,41],steps=20 if a.smoke else 64))
records=[];resources=[];totalstart=time.monotonic()
def run(name,seed,stop=-1,checkpoint=None,control='correct'):
 dest=out/name;cmd=[sys.executable,'-B',str(B/'run_worker.py'),'--output',str(dest),'--seed',str(seed),'--steps',str(20 if a.smoke else 64),'--stop',str(stop),'--control',control]
 if checkpoint:cmd+=['--checkpoint',str(checkpoint)]
 env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',MKL_NUM_THREADS='1')
 with (out/f'{name}.log').open('w') as log:
  proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True);start=time.monotonic();termination=None
  while proc.poll() is None:
   rows=subprocess.check_output(['ps','-axo','pid=,ppid=,pgid=,rss='],text=True);own=[]
   for line in rows.splitlines():
    pid,ppid,pgid,rss=map(int,line.split())
    if pgid==proc.pid:own.append(dict(pid=pid,ppid=ppid,rss_bytes=rss*1024))
   resources.append(dict(run=name,time=time.monotonic(),rss_bytes=sum(v['rss_bytes'] for v in own),processes=own));assert resources[-1]['rss_bytes']<4*1024**3
   assert time.monotonic()-start<120 and time.monotonic()-totalstart<1200
   if stop>=0 and (dest/'ready.json').exists():
    ready=json.loads((dest/'ready.json').read_text());assert ready['pid']==proc.pid and ready['pgid']==proc.pid and os.getpgid(proc.pid)==proc.pid
    termination=time.monotonic();os.killpg(proc.pid,signal.SIGTERM);break
   time.sleep(.1)
  code=proc.wait(timeout=15);end=time.monotonic()
  assert code==(-signal.SIGTERM if stop>=0 else 0),(name,code)
  # A PGID allocated with start_new_session belongs only to this child tree.
  rows=subprocess.check_output(['ps','-axo','pid=,pgid=,stat='],text=True)
  leftover=[line for line in rows.splitlines() if int(line.split()[1])==proc.pid and not line.split()[2].startswith('Z')]
  assert not leftover,leftover
  records.append(dict(name=name,pid=proc.pid,start=start,end=end,exit_code=code,termination=termination,stop=stop,control=control,checkpoint=str(checkpoint) if checkpoint else None,leftover=[]));write(out/'execution.json',records);write(out/'resources.json',resources)
  print(name,code,round(end-start,3),flush=True)
 return dest
for seed in ([1061] if a.smoke else [1061,1062,1063]):
 run(f'seed{seed}-baseline',seed)
 for cut in ([17] if a.smoke else [17,41]):
  prefix=run(f'seed{seed}-cut{cut}-prefix',seed,stop=cut);run(f'seed{seed}-cut{cut}-resume',seed,checkpoint=prefix/'checkpoint.pt')
  if seed==1061 and cut==17:
   for control in ['omit_buffer','dispatch_cursor']:run(f'seed{seed}-cut{cut}-{control}',seed,checkpoint=prefix/'checkpoint.pt',control=control)
write(out/'completion.json',dict(done=True,runs=len(records),wall_s=time.monotonic()-totalstart,peak_rss_bytes=max(r['rss_bytes'] for r in resources)));print('complete',flush=True)
