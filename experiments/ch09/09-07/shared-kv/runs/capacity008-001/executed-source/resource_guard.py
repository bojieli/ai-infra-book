"""Linux guard for this run's uniquely tagged processes; never signals other work."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import uuid

KNOWN = {}
SESSION_ID = None

def processes(token):
    found={};all_processes={};tagged=set()
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            stat=(p/'stat').read_text().rsplit(')',1)[1].split()
            status=(p/'status').read_text().splitlines()
            rss=next((int(x.split()[1])*1024 for x in status if x.startswith('VmRSS:')),0)
            pid=int(p.name)
            all_processes[pid]={'birth':int(stat[19]),'rss':rss,'state':stat[0],
                                'parent':int(stat[1]),'session':int(stat[3])}
            if ('BOOK_SHARED_KV_TOKEN='+token).encode() in (p/'environ').read_bytes().split(b'\0'):tagged.add(pid)
        except (FileNotFoundError,ProcessLookupError,PermissionError):pass
    for pid,info in all_processes.items():
        if pid in tagged or info['session']==SESSION_ID or KNOWN.get(pid)==info['birth']:
            found[pid]=info
    while True:
        added={pid:info for pid,info in all_processes.items() if pid not in found and info['parent'] in found}
        if not added:break
        found.update(added)
    KNOWN.update({pid:info['birth'] for pid,info in found.items()})
    return found

def send(token, sig):
    for pid,info in processes(token).items():
        try:
            fd=os.pidfd_open(pid)
            try:
                if processes(token).get(pid,{}).get('birth')==info['birth']:
                    signal.pidfd_send_signal(fd,sig)
            finally:os.close(fd)
        except ProcessLookupError:pass

p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
assert a.command and a.command[0]=='--';a.command=a.command[1:]
a.out.mkdir(parents=True,exist_ok=False)
token=uuid.uuid4().hex;env=dict(os.environ,BOOK_SHARED_KV_TOKEN=token,OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4')
start=time.monotonic();reason=None
log=(a.out/'process.log').open('wb');records=(a.out/'resources.jsonl').open('w',buffering=1)
proc=subprocess.Popen(a.command,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
SESSION_ID=proc.pid
(a.out/'launch.json').write_text(json.dumps(dict(command=a.command,pid=proc.pid,token=token,start_s=start,
    timeout_s=3600,own_rss_limit_bytes=40*1024**3,own_gpu_limit_mib=64*1024,global_available_min_bytes=24*1024**3),indent=2)+'\n')
try:
    while proc.poll() is None:
        current=processes(token)
        available=int(next(x for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')).split()[1])*1024
        gpu=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10)
        gpu_rows=[tuple(int(x.strip()) for x in row.split(',')) for row in gpu.splitlines() if row.strip()]
        own_gpu=sum(m for pid,m in gpu_rows if pid in current)
        rss=sum(x['rss'] for x in current.values());elapsed=time.monotonic()-start
        records.write(json.dumps(dict(elapsed_s=elapsed,processes=current,rss_bytes=rss,gpu_mib=own_gpu,mem_available_bytes=available))+'\n')
        if elapsed>3600:reason='timeout'
        elif rss>40*1024**3:reason='own_rss_limit'
        elif own_gpu>64*1024:reason='own_gpu_limit'
        elif available<24*1024**3:reason='global_available_limit'
        if reason:break
        time.sleep(.5)
finally:
    if proc.poll() is None or processes(token):
        send(token,signal.SIGTERM)
        deadline=time.monotonic()+15
        while time.monotonic()<deadline and any(x['state']!='Z' for x in processes(token).values()):time.sleep(.2)
        send(token,signal.SIGKILL)
    code=proc.wait();log.close();records.close()
    remaining={pid:r for pid,r in processes(token).items() if r['state']!='Z'}
    result=dict(exit_code=code,reason=reason,leftovers=remaining,wall_s=time.monotonic()-start)
    (a.out/'supervisor.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
raise SystemExit(0 if code==0 and reason is None and not remaining else 1)
