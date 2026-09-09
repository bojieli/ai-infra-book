"""Supervise only this probe's session; refuse overwrite and preserve raw failures."""
import os,sys,json,time,signal,subprocess,hashlib
from pathlib import Path
B=Path(__file__).resolve().parent
R=B/'results';R.mkdir(exist_ok=False)
for n in ['cache','tmp']:(B/n).mkdir(exist_ok=True)
def command(args):return subprocess.check_output(args,text=True)
gpu_before=command(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'])
(R/'gpu-before.txt').write_text(command(['nvidia-smi']))
assert int(gpu_before.strip())>=28*1024,'Requires 28 GiB free before native probe'
env=os.environ.copy();env.update({k:'4' for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS']})
env.update(CPATH=str(B.parent/'include-overlay')+':/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/lib/python3.10/site-packages/nvidia/cu13/include/cccl',TVM_FFI_CACHE_DIR=str(B/'cache/tvm'),TILELANG_CACHE_DIR=str(B/'cache/tilelang'),TILELANG_TMP_DIR=str(B/'tmp/tilelang'),MAX_JOBS='4',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TRITON_CACHE_DIR=str(B/'cache/triton'),TORCHINDUCTOR_CACHE_DIR=str(B/'cache/inductor'),CUDA_CACHE_PATH=str(B/'cache/cuda'),XDG_CACHE_HOME=str(B/'cache/xdg'),TMPDIR=str(B/'tmp'),CUDA_VISIBLE_DEVICES='0',CUDA_HOME='/home/ubuntu/ai-infra-book-experiments/tools/flashinfer-cuda130/nvidia/cu13')
cores=sorted(os.sched_getaffinity(0))[4:8]
def setup():os.setsid();os.sched_setaffinity(0,cores)
start=time.time();samples=[];reason=None
with (B/'run.log').open('w') as log:
 p=subprocess.Popen([sys.executable,'-B',str(B/'run.py')],stdout=log,stderr=subprocess.STDOUT,env=env,preexec_fn=setup)
 (R/'pid.json').write_text(json.dumps(dict(pid=p.pid,started=start,affinity=cores)))
 while p.poll() is None:
  try:
   proc=[line.split() for line in command(['ps','-eo','pid,sid,rss']).splitlines()[1:]]
   own={int(v[0]) for v in proc if len(v)==3 and int(v[1])==p.pid}
   rss=sum(int(v[2])*1024 for v in proc if len(v)==3 and int(v[0]) in own)
   gpu=command(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'])
   gm=sum(int(v[1]) for line in gpu.splitlines() if len(v:=line.split(','))==2 and int(v[0]) in own)
   avail=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024
   samples.append(dict(time=time.time(),pids=sorted(own),rss_bytes=rss,gpu_mib=gm,available_bytes=avail))
   if rss>50*1024**3 or gm>24*1024 or avail<24*1024**3 or time.time()-start>720:
    reason=f'guard RSS={rss}, GPU={gm}, available={avail}, elapsed={time.time()-start}';break
  except Exception as exc:reason='monitor error '+repr(exc);break
  time.sleep(1)
 if reason:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL)
 code=p.wait()
 # Terminate residual members of OUR created session even if the main process died.
 leftovers=[int(v[0]) for line in command(['ps','-eo','pid,sid']).splitlines()[1:] if len(v:=line.split())==2 and int(v[1])==p.pid]
 if leftovers:
  try:os.killpg(p.pid,signal.SIGTERM)
  except ProcessLookupError:pass
  time.sleep(2)
  try:os.killpg(p.pid,signal.SIGKILL)
  except ProcessLookupError:pass
 (R/'supervisor.json').write_text(json.dumps(dict(pid=p.pid,start=start,end=time.time(),exit_code=code,reason=reason,residual_pids_signalled=leftovers,peak_gpu_mib=max([x['gpu_mib'] for x in samples],default=0),peak_rss_bytes=max([x['rss_bytes'] for x in samples],default=0),samples=samples),indent=2))
 (R/'gpu-after.txt').write_text(command(['nvidia-smi']))
print('EXIT',code,'reason',reason,flush=True)
sys.exit(code if code>=0 else 128-code)
