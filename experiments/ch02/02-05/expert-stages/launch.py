#!/usr/bin/env python3
"""Own-child watchdog; never stops or signals unrelated processes."""
import os,sys,pathlib,subprocess,time,json,signal
B=pathlib.Path(__file__).resolve().parent
for sub in ['results','cache','tmp']:(B/sub).mkdir(exist_ok=True)
e=os.environ.copy()
e.update({k:'4' for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS']})
e.update(PYTHONDONTWRITEBYTECODE='1',TRITON_CACHE_DIR=str(B/'cache/triton'),TORCHINDUCTOR_CACHE_DIR=str(B/'cache/inductor'),CUDA_CACHE_PATH=str(B/'cache/cuda'),XDG_CACHE_HOME=str(B/'cache/xdg'),TMPDIR=str(B/'tmp'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CUDA_VISIBLE_DEVICES='0')
cores=sorted(os.sched_getaffinity(0))[:4]
def setup():os.setsid();os.sched_setaffinity(0,cores)
start=time.time();log=open(B/'run.log','w');p=subprocess.Popen([sys.executable,'-B',str(B/'run.py')],stdout=log,stderr=subprocess.STDOUT,env=e,preexec_fn=setup)
samples=[];reason=None
while p.poll() is None:
 try:
  # Descendants stay in this session; includes compiler children.
  lines=subprocess.check_output(['ps','-eo','pid,sid,rss'],text=True).splitlines()[1:]
  rss=sum(int(v[2])*1024 for line in lines if len(v:=line.split())==3 and int(v[1])==p.pid)
  gpu=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True)
  gm=sum(int(v[1].strip()) for line in gpu.splitlines() if len(v:=line.split(','))==2 and int(v[0])==p.pid)
  samples.append(dict(t=time.time(),rss_tree_bytes=rss,gpu_mib=gm))
  if rss>8*1024**3 or gm>3072 or time.time()-start>900:
   reason=f'resource limit: RSS {rss}, GPU {gm} MiB';os.killpg(p.pid,signal.SIGTERM);break
 except Exception as ex:
  reason='monitor failure: '+repr(ex);os.killpg(p.pid,signal.SIGTERM);break
 time.sleep(.5)
code=p.wait();log.close()
(B/'results/supervisor.json').write_text(json.dumps(dict(pid=p.pid,start=start,end=time.time(),exit_code=code,reason=reason,affinity=cores,peak_rss_tree_bytes=max([s['rss_tree_bytes'] for s in samples],default=0),peak_gpu_mib=max([s['gpu_mib'] for s in samples],default=0),samples=samples),indent=2))
print('EXIT',code,'reason',reason,flush=True)
sys.exit(code if code>=0 else 128-code)
