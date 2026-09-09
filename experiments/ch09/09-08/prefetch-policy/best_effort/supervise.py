import hashlib,json,os,shutil,signal,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def members(pgid):
 lines=subprocess.check_output(['ps','-eo','pid,pgid,args'],text=True).splitlines()[1:]
 return [line.strip() for line in lines if len(line.split())>=2 and line.split()[1]==str(pgid)]
def main():
 results=ROOT/'results';assert not results.exists();results.mkdir();storage=ROOT/'storage';assert not storage.exists()
 source=ROOT.parents[1]/'storage-v3';shutil.copytree(source,storage)
 trace=[json.loads(l) for l in (ROOT.parents[1]/'results/consumer-v6/storage.jsonl').read_text().splitlines()]
 filename=Path(next(x['file'] for x in trace if x['method']=='get')).name
 target=storage/filename;before=target.read_bytes();target.write_bytes(before[:-2])
 record=dict(truncated_file=filename,original_bytes=len(before),truncated_bytes=target.stat().st_size,original_sha256=sha(before),truncated_sha256=sha(target.read_bytes()),request_observation_s=60,initialization_limit_s=180,source_hashes={f:sha((ROOT/f).read_bytes()) for f in ['run.py','storage_trace.py','supervise.py','config.json','inputs.json','launch.sh']})
 start=time.monotonic();ready=None;reason=None
 with (results/'engine.log').open('x') as log:
  p=subprocess.Popen(['sh','launch.sh'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);record['pid']=p.pid
  while p.poll() is None:
   lifecycle=results/'lifecycle.jsonl'
   if lifecycle.exists():
    events=[json.loads(l) for l in lifecycle.read_text().splitlines() if l.endswith('}')]
    ready=next((x['time_s'] for x in events if x['event']=='request_start'),None)
   now=time.monotonic()
   if ready is not None and now-ready>=60:reason='request_observation_expired';break
   if ready is None and now-start>=180:reason='initialization_observation_expired';break
   time.sleep(.1)
  record.update(reason=reason or 'process_exited',observed_s=time.monotonic()-start,request_observed_s=time.monotonic()-ready if ready else None,exit_before_cleanup=p.poll(),members_before_cleanup=members(p.pid))
  if record['members_before_cleanup']:
   os.killpg(p.pid,signal.SIGTERM)
   deadline=time.monotonic()+5
   while members(p.pid) and time.monotonic()<deadline:time.sleep(.1)
   if members(p.pid):os.killpg(p.pid,signal.SIGKILL)
  record['exit_code']=p.wait(timeout=10);time.sleep(.2);record['members_after_cleanup']=members(p.pid)
 record['final_truncated_file_sha256']=sha(target.read_bytes());(results/'supervisor.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if __name__=='__main__':main()
