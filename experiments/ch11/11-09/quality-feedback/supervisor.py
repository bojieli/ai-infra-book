"""Watchdog signals only its newly-created model process group, never services."""
import hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent;RAW=R/'raw'
def gpu():
 return subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True)
def procs(group):
 rows=[]
 for d in Path('/proc').iterdir():
  if not d.name.isdigit():continue
  try:
   st=(d/'stat').read_text().rsplit(')',1)[1].split()
   if int(st[2])!=group:continue
   status={k:v.strip() for k,v in (line.split(':',1) for line in (d/'status').read_text().splitlines() if ':' in line)}
   rows.append(dict(pid=int(d.name),ppid=int(st[1]),pgrp=int(st[2]),rss_kib=int(status.get('VmRSS','0 kB').split()[0]),anon_kib=int(status.get('RssAnon','0 kB').split()[0]),file_kib=int(status.get('RssFile','0 kB').split()[0]),cpu_ticks=int(st[11])+int(st[12]),affinity=status['Cpus_allowed_list'],threads=int(status['Threads'])))
  except (OSError,KeyError,ValueError):pass
 return rows
if __name__=='__main__':
 RAW.mkdir(exist_ok=False)
 (RAW/'gpu-before.txt').write_text(subprocess.check_output(['nvidia-smi'],text=True));(RAW/'services-before.csv').write_text(gpu())
 free=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True).strip());assert free>=26*1024,free
 locked=json.loads((R/'run.lock.json').read_text())
 for name,h in locked.items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==h,name
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',VLLM_USE_FLASHINFER_SAMPLER='0',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',TOKENIZERS_PARALLELISM='false',CUDA_VISIBLE_DEVICES='0',VLLM_CACHE_ROOT=str(R/'cache'),XDG_CACHE_HOME=str(R/'cache'),TRITON_CACHE_DIR=str(R/'cache/triton'),TORCHINDUCTOR_CACHE_DIR=str(R/'cache/inductor'))
 start=time.monotonic();reason=None;lastgpu=0;gpuraw='';peak=0
 with (RAW/'model.log').open('w') as log,(RAW/'resources.jsonl').open('w',buffering=1) as samples:
  p=subprocess.Popen(['taskset','-c','8-11','/home/ubuntu/vllm023-venv/bin/python','-B',str(R/'run.py')],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  (RAW/'owned-group.json').write_text(json.dumps(dict(pid=p.pid,pgid=p.pid,start_epoch=time.time(),free_mib=free)))
  try:
   while p.poll() is None:
    rows=procs(p.pid);now=time.monotonic();ids={r['pid'] for r in rows}
    sampled_gpu=now-lastgpu>=1
    if sampled_gpu:gpuraw=gpu();lastgpu=now
    mem=sum(int(line.split(',')[1].strip()) for line in gpuraw.splitlines() if int(line.split(',')[0]) in ids)
    ready=(RAW/'engine-ready').exists();rss=sum(x['rss_kib'] for x in rows);anon=sum(x['anon_kib'] for x in rows)
    samples.write(json.dumps(dict(t_s=now-start,engine_ready=ready,processes=rows,rss_kib=rss,anon_kib=anon,gpu_mib=mem,gpu_fresh=sampled_gpu,gpu_raw=gpuraw))+'\n')
    if now-start>1200:reason='1200s watchdog'
    elif mem>24*1024:reason='GPU sampled >24GiB'
    elif (rss if ready else anon)>10*1024**2:reason='RSS boundary exceeded'
    elif sum(f.stat().st_size for f in RAW.rglob('*') if f.is_file())>95*1024**2:reason='raw budget'
    if reason:break
    time.sleep(.25)
  finally:
   # Only this owned group. Cleanup descendants even if controller exited.
   if procs(p.pid):
    try:os.killpg(p.pid,signal.SIGTERM)
    except ProcessLookupError:pass
    try:p.wait(timeout=10)
    except subprocess.TimeoutExpired:pass
    if procs(p.pid):
     try:os.killpg(p.pid,signal.SIGKILL)
     except ProcessLookupError:pass
   p.wait()
 (RAW/'exit.json').write_text(json.dumps(dict(returncode=p.returncode,watchdog_reason=reason,elapsed_s=time.monotonic()-start,remaining_owned=procs(p.pid)),indent=2)+'\n')
 (RAW/'gpu-after.txt').write_text(subprocess.check_output(['nvidia-smi'],text=True));(RAW/'services-after.csv').write_text(gpu())
