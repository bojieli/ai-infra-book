#!/usr/bin/env python3
"""Bound entire process group to four CPU cores; abort if aggregate RSS >= 11 GiB."""
import os,pathlib,subprocess,sys,time,json
root=pathlib.Path(__file__).resolve().parent;os.chdir(root)
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS']:os.environ[k]='4'
os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1')
r=root/'results';r.mkdir(exist_ok=True)
procs=[];peak=0
f=(r/'supervisor.jsonl').open('w')
def record(**kw):f.write(json.dumps(dict(time_ns=time.time_ns(),**kw))+'\n');f.flush()
def start(mode):
 out=(r/(mode+'.jsonl')).open('w');err=(r/(mode+'.stderr')).open('w')
 p=subprocess.Popen([sys.executable,'run.py',mode],stdout=out,stderr=err);procs.append(p);record(event='start',mode=mode,pid=p.pid);return p
def check():
 global peak
 rss=0
 for p in procs:
  try:
   text=pathlib.Path(f'/proc/{p.pid}/status').read_text()
   rss+=int(next(x for x in text.splitlines() if x.startswith('VmRSS:')).split()[1])*1024
  except (FileNotFoundError,StopIteration):pass
 peak=max(peak,rss)
 if rss>=11*1024**3:
  for p in procs:
   if p.poll() is None:p.kill()
  raise RuntimeError('aggregate RSS limit exceeded')
 time.sleep(.1)
def wait(p):
 while p.poll() is None:check()
 record(event='exit',pid=p.pid,code=p.returncode,aggregate_peak_rss_bytes=peak)
 assert p.returncode==0
try:
 wait(start('prepare'))
 ready=r/'ready.json';ready.unlink(missing_ok=True)
 receiver=start('receiver');deadline=time.time()+180
 while not ready.exists():
  check();assert receiver.poll() is None and time.time()<deadline
 sender=start('sender');wait(sender);wait(receiver)
 record(event='complete',aggregate_peak_rss_bytes=peak)
finally:
 for p in procs:
  if p.poll() is None:p.terminate()
