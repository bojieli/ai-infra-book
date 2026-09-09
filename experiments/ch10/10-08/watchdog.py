#!/usr/bin/env python3
"""Linux-only own-job supervisor. No global Ray/service operations."""
import argparse,json,os,pathlib,signal,subprocess,time,uuid
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--private',required=True);p.add_argument('--gpu',action='store_true');p.add_argument('--seconds',type=int,default=1200);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
if (out/'stdout.log').exists():raise SystemExit('Refusing to overwrite existing run')
def mem():
 return int(next(x.split()[1] for x in pathlib.Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
def smi(args):
 r=subprocess.run(['nvidia-smi',*args,'--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5);r.check_returncode();return r.stdout
(out/'limits.json').write_text(json.dumps(dict(gpu_gib=16,rss_gib=24,rss_includes_supervisor=True,min_mem_available_gib=16,min_gpu_free_gib=10,cpu_affinity=[12,13,14,15],library_threads=4,timeout_s=a.seconds,private_disk_limit_gib=25,private_disk_guard_gib=24),indent=2)+'\n')
if mem()<16*2**30: raise SystemExit('MemAvailable below 16GiB; not launched')
if a.gpu and min(float(x) for x in smi(['--query-gpu=memory.free']).splitlines())<10240: raise SystemExit('GPU free below 10GiB; not launched')
if len(os.sched_getaffinity(0)&set(range(12,16)))!=4: raise SystemExit('CPU12-15 unavailable')
os.sched_setaffinity(0,set(range(12,16)))
token=uuid.uuid4().hex; env=os.environ.copy();env.update(VERLRL_JOB_TOKEN=token,OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',MKL_NUM_THREADS='4',NUMEXPR_NUM_THREADS='4',RAYON_NUM_THREADS='4',TOKENIZERS_PARALLELISM='false')
if not a.gpu: env['CUDA_VISIBLE_DEVICES']=''
cmd=a.command[1:] if a.command[:1]==['--'] else a.command
log=open(out/'stdout.log','w');start=time.monotonic(); known={};reason='command_exit';samples=open(out/'resources.jsonl','w')
child=subprocess.Popen(['taskset','-c','12-15',*cmd],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
def owned():
 found={}
 for d in pathlib.Path('/proc').iterdir():
  if not d.name.isdigit(): continue
  try:
   raw=(d/'stat').read_text(); fields=raw[raw.rindex(')')+2:].split(); birth=fields[19]; pid=int(d.name)
   if known.get(pid)==birth or ('VERLRL_JOB_TOKEN='+token).encode() in (d/'environ').read_bytes().split(b'\0'):
    found[pid]=birth
  except (OSError,ValueError,ProcessLookupError): pass
 known.update(found);return found
def interrupted(signum,frame):
 raise RuntimeError('supervisor_signal_'+str(signum))
signal.signal(signal.SIGTERM,interrupted)
signal.signal(signal.SIGINT,interrupted)
try:
 while True:
  procs=owned(); rss=0
  for pid in procs:
   try:rss+=int(pathlib.Path(f'/proc/{pid}/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
   except OSError:pass
  gpu=0; rows=[]
  if a.gpu:
   for l in smi(['--query-compute-apps=pid,used_gpu_memory']).splitlines():
    cols=l.split(',');pid=int(cols[0]);v=float(cols[1]);rows.append([pid,v])
    if pid in procs:gpu+=v
  supervisor_rss=int(pathlib.Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE');rss+=supervisor_rss
  affinities={}
  for pid in procs:
   try:affinities[pid]=sorted(os.sched_getaffinity(pid))
   except ProcessLookupError:pass
  available=mem();elapsed=time.monotonic()-start
  # Physical private allocation; hard links counted once by du.
  size=None
  if int(elapsed)%10==0:
   size=int(subprocess.check_output(['du','-s','-B1',a.private],text=True).split()[0])
  record=dict(elapsed_s=elapsed,pids=sorted(procs),rss_bytes=rss,gpu_mib=gpu,mem_available_bytes=available,private_bytes=size,gpu_processes=rows,supervisor_rss_bytes=supervisor_rss,affinity_by_pid=affinities)
  samples.write(json.dumps(record)+'\n');samples.flush()
  if any(not set(cpus)<=set(range(12,16)) for cpus in affinities.values()):reason='cpu_affinity_violation';break
  if rss>24*2**30:reason='rss_limit_24GiB';break
  if gpu>16384:reason='gpu_limit_16GiB';break
  if available<16*2**30:reason='mem_available_limit';break
  if size is not None and size>24*2**30:reason='private_disk_limit_reserve_1GiB';break
  if elapsed>a.seconds:reason='timeout';break
  if child.poll() is not None:break
  time.sleep(1)
except BaseException as e:
 reason='supervisor_exception:'+repr(e)
finally:
 # Kill every process bearing this job token, even Ray children reparented to init.
 for sig,delay in [(signal.SIGTERM,3),(signal.SIGKILL,1)]:
  for pid in owned():
   try:os.kill(pid,sig)
   except ProcessLookupError:pass
  time.sleep(delay)
 rc=child.wait();left=owned();samples.close();log.close()
 result=dict(command=cmd,root_pid=child.pid,job_token=token,reason=reason,returncode=rc,elapsed_s=time.monotonic()-start,remaining_pids=sorted(left),gpu_run=a.gpu)
 (out/'exit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
raise SystemExit(rc if reason=='command_exit' and not left else 125)
