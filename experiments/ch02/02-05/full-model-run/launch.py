"""Per-candidate watchdog; token AND birth verified, pidfds prevent PID reuse kills."""
import argparse,os,signal,socket,subprocess,sys,time,uuid,tempfile,shutil
from pathlib import Path
from common import *
TOKEN_KEY='V4_FULL_RUN_TOKEN'
def token_matches(pid,token):
 try:return (TOKEN_KEY+'='+token).encode() in (Path('/proc')/str(pid)/'environ').read_bytes().split(b'\0')
 except (FileNotFoundError,ProcessLookupError,PermissionError):return False

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--execute-after-rl',action='store_true',required=True);a=p.parse_args();out=a.out.resolve()
 assert (out/'candidate.json').is_file() and not (out/'launch.json').exists()
 assert hasattr(os,'pidfd_open') and hasattr(signal,'pidfd_send_signal'),'Linux pidfd support required'
 try:
  before=snapshot();save(out/'resource-before.json',before)
  assert before['available_bytes']>=LIMITS['start_available_gib']*1024**3,'Insufficient MemAvailable; root must reschedule'
  assert before['gpu_free_mib']>=LIMITS['start_gpu_free_mib'],'Insufficient GPU headroom; root must reschedule'
  with socket.socket() as probe_socket:probe_socket.bind(('127.0.0.1',CONFIG['port']))
  assert not any(r['is_verl'] for r in before['processes']),'verl still present; root must wait'
 except Exception as exc:
  save(out/'launch-refused.json',dict(status='refused_before_model_process',reason=repr(exc),time=time.time(),limits=LIMITS))
  from score import score
  score(out)
  raise SystemExit(1)
 coordinator_pid=os.getppid();coordinator=next((r for r in before['processes'] if r['pid']==coordinator_pid),None)
 token=uuid.uuid4().hex;start=time.monotonic();start_ticks=int(float(Path('/proc/uptime').read_text().split()[0])*os.sysconf('SC_CLK_TCK'))
 ipc_tmp=Path(tempfile.mkdtemp(prefix='v4-',dir='/tmp'))
 save(out/'ipc-directory.json',dict(path=str(ipc_tmp),purpose='private short Unix socket path',mode=oct(ipc_tmp.stat().st_mode & 0o777)))
 env=os.environ.copy()
 for k in list(env):
  if k.startswith('SGLANG_') or k in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD']:env.pop(k)
 env.update({k:'4' for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS']})
 cccl=TOOLS/'sglang0513-venv/lib/python3.10/site-packages/nvidia/cu13/include/cccl'
 env.update({TOKEN_KEY:token,'V4_FULL_COMPAT_LOG_DIR':str(out/'compatibility-records'),'CPATH':str(out/'include-overlay')+':'+str(cccl),'TVM_FFI_CACHE_DIR':str(out/'cache/tvm'),'TILELANG_CACHE_DIR':str(out/'cache/tilelang'),'TILELANG_TMP_DIR':str(out/'tmp/tilelang'),'MAX_JOBS':'4','PYTHONDONTWRITEBYTECODE':'1','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','TRITON_CACHE_DIR':str(out/'cache/triton'),'TORCHINDUCTOR_CACHE_DIR':str(out/'cache/inductor'),'CUDA_CACHE_PATH':str(out/'cache/cuda'),'XDG_CACHE_HOME':str(out/'cache/xdg'),'TMPDIR':str(ipc_tmp),'CUDA_VISIBLE_DEVICES':'0','CUDA_HOME':str(TOOLS/'flashinfer-cuda130/nvidia/cu13'),'TOKENIZERS_PARALLELISM':'false','FLASHINFER_WORKSPACE_BASE':str(out/'cache/flashinfer-home'),'TORCH_EXTENSIONS_DIR':str(out/'cache/torch-extensions'),'NUMBA_CACHE_DIR':str(out/'cache/numba'),'HF_HOME':str(out/'cache/huggingface'),'HF_MODULES_CACHE':str(out/'cache/huggingface/modules')})
 cores=sorted(os.sched_getaffinity(0))[4:8];assert len(cores)==4
 def setup():os.setsid();os.sched_setaffinity(0,cores)
 known={};reason=None;child=None;exit_code=None;signalled=[]
 def discover():
  for r in processes():
   if r['birth']>=start_ticks and token_matches(r['pid'],token):
    key=(r['pid'],r['birth'])
    if key not in known:
     try:
      fd=os.pidfd_open(r['pid']);now=next((v for v in processes() if v['pid']==r['pid']),None)
      if now and now['birth']==r['birth'] and token_matches(r['pid'],token):known[key]=fd
      else:os.close(fd)
     except ProcessLookupError:pass
  return {r['pid']:r for r in processes() if (r['pid'],r['birth']) in known}
 def terminate(sig):
  live=discover()
  for pid,r in live.items():
   # Enrollment confirmed the unique environment token and birth together.
   # Keep the pinned identity even if this same process later clears its env.
   try:signal.pidfd_send_signal(known[(pid,r['birth'])],sig);signalled.append(dict(pid=pid,birth=r['birth'],signal=int(sig),time=time.time(),token_confirmed_at_enrollment=True))
   except ProcessLookupError:pass
 def interrupted(signum,frame):raise RuntimeError('watchdog received signal '+str(signum))
 for sig in (signal.SIGTERM,signal.SIGHUP):signal.signal(sig,interrupted)
 try:
  with (out/'run.log').open('x') as log,(out/'watchdog.jsonl').open('x') as samples:
   child=subprocess.Popen([sys.executable,'-B',str(out/'run.py'),'--out',str(out)],env=env,cwd=out,stdout=log,stderr=subprocess.STDOUT,preexec_fn=setup)
   live=discover();assert child.pid in live,'Child token/birth not confirmed'
   save(out/'launch.json',dict(pid=child.pid,birth=live[child.pid]['birth'],sid=live[child.pid]['sid'],token=token,start_ticks=start_ticks,time=time.time(),limits=LIMITS,affinity=cores,scope='new_process_tree_only_including_reparented_token_holders'))
   save(out/'start-gate.json',dict(confirmed=True))
   while True:
    live=discover();snap=snapshot();own_gpu=0
    for line in snap['gpu_apps_raw'].splitlines():
     parts=[v.strip() for v in line.split(',')]
     if len(parts)==3 and int(parts[0]) in live:own_gpu+=int(parts[2])
    accounting=[r for r in snap['processes'] if r['pid']==os.getpid() or (coordinator is not None and r['pid']==coordinator_pid and r['birth']==coordinator['birth'])]
    rss=sum(r['rss_kib']*1024 for r in list(live.values())+accounting);anon=sum(r['anon_kib']*1024 for r in list(live.values())+accounting)
    phase=json.loads((out/'phase.json').read_text()) if (out/'phase.json').exists() else dict(phase='initializing',monotonic=start)
    row=dict(time=time.time(),elapsed_s=time.monotonic()-start,phase=phase,own=list(live.values()),supervisor_and_coordinator=accounting,own_rss_bytes=rss,own_anon_bytes=anon,own_gpu_mib=own_gpu,available_bytes=snap['available_bytes'],gpu_free_mib=snap['gpu_free_mib'],gpu_raw=snap['gpu_raw'],gpu_apps_raw=snap['gpu_apps_raw'],shared_key_processes=[r for r in snap['processes'] if r['pid'] not in live and r['rss_kib']>=512*1024])
    samples.write(json.dumps(row)+'\n');samples.flush()
    age=time.monotonic()-phase['monotonic'];elapsed=time.monotonic()-start
    if rss>LIMITS['max_rss_gib']*1024**3:reason='own RSS threshold'
    elif own_gpu>LIMITS['max_gpu_mib']:reason='own GPU threshold'
    elif snap['available_bytes']<LIMITS['min_available_gib']*1024**3:reason='global MemAvailable threshold'
    elif snap['gpu_free_mib']<LIMITS['min_gpu_free_mib']:reason='global GPU free threshold'
    elif elapsed>LIMITS['total_timeout_s']:reason='total timeout'
    elif phase['phase']=='initializing' and age>LIMITS['init_timeout_s']:reason='initialization timeout'
    elif phase['phase']=='request' and age>LIMITS['request_timeout_s']:reason='request timeout'
    elif phase['phase']=='shutdown' and age>60:reason='shutdown timeout'
    if reason or child.poll() is not None:break
    time.sleep(LIMITS['poll_s'])
 except BaseException as exc:
  reason='watchdog/launch exception: '+repr(exc)
 finally:
  for sig in (signal.SIGTERM,signal.SIGHUP):signal.signal(sig,signal.SIG_IGN)
  # Always reap descendants, including ones reparented out of the original session.
  for sig,duration in [(signal.SIGTERM,10),(signal.SIGKILL,5)]:
   deadline=time.monotonic()+duration
   while time.monotonic()<deadline:
    terminate(sig)
    if child is not None:child.poll()
    if not discover():break
    time.sleep(.25)
  if child is not None:
   try:exit_code=child.wait(timeout=2)
   except subprocess.TimeoutExpired:reason=(reason or '')+'; child did not exit'
  leftovers=list(discover().values())
  save(out/'supervisor.json',dict(time=time.time(),reason=reason,exit_code=exit_code,signalled=signalled,leftovers=leftovers,known_births=[dict(pid=k[0],birth=k[1]) for k in known],poll_is_not_a_hard_memory_limit=True))
  for fd in known.values():os.close(fd)
  if not leftovers:shutil.rmtree(ipc_tmp)
  try:save(out/'resource-after.json',snapshot())
  except Exception as exc:save(out/'resource-after-error.json',dict(error=repr(exc)))
  from score import score
  score(out)
 if reason or leftovers or exit_code!=0:raise SystemExit(1)
if __name__=='__main__':main()
