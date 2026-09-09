import hashlib,http.server,json,os,signal,socket,sqlite3,subprocess,threading,time,urllib.request,random
from pathlib import Path
from config import config
R=Path(__file__).resolve().parent;OUT=R/'results';BIN=R.parents[2]/'tools/otelcol-0133/otelcol-contrib'
state={};lock=threading.Lock()
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_POST(self):
  start=time.monotonic();raw=self.rfile.read(int(self.headers['Content-Length']));body=json.loads(raw)
  events=[json.loads(x['body']['stringValue']) for r in body['resourceLogs'] for s in r['scopeLogs'] for x in s['logRecords']]
  with lock:c=state['case'];restore=state['restore'];delay=state['delay']
  success=start>=restore
  if success:time.sleep(delay)
  commit=time.monotonic()
  with sqlite3.connect(c/'backend.sqlite') as db:
   if success:
    for e in events:db.execute('insert or ignore into events(id,commit_s,body) values(?,?,?)',(e['event_id'],commit,json.dumps(e,sort_keys=True)))
  commit_end=time.monotonic()
  record=dict(start_s=start,commit_start_s=commit,end_s=commit_end,success=success,events=events,wire_bytes=len(raw))
  with (c/'backend.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
  self.send_response(200 if success else 503);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b'{}')
def ready(p):
 if p.poll() is not None:raise RuntimeError(f'collector exited {p.returncode}')
 try:
  with urllib.request.urlopen('http://127.0.0.1:31333',timeout=.2) as r:return r.status==200
 except Exception:return False
def until(fn,timeout=25):
 deadline=time.monotonic()+timeout
 while time.monotonic()<deadline:
  if fn():return
  time.sleep(.02)
 raise TimeoutError('observation window exhausted')
def count(c):
 with sqlite3.connect(c/'backend.sqlite') as db:return db.execute('select count(*) from events').fetchone()[0]
def main():
 assert not OUT.exists();OUT.mkdir()
 for port in [31331,31332,31333]:
  with socket.socket() as s:s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',port))
 server=http.server.ThreadingHTTPServer(('127.0.0.1',31332),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
 rng=random.Random(1109);order=[]
 for trial in range(2):
  delays=[.01,.08];rng.shuffle(delays);order.extend(dict(trial=trial,delay_s=d) for d in delays)
 (OUT/'order.json').write_text(json.dumps(order,indent=2)+'\n');processes=[];logs=[]
 try:
  for case in order:
   c=OUT/f"{case['trial']}-{int(case['delay_s']*1000)}ms";c.mkdir();(c/'storage').mkdir();(c/'config.yaml').write_text(config(c,True))
   with sqlite3.connect(c/'backend.sqlite') as db:db.execute('create table events(id integer primary key,commit_s real,body text)')
   with lock:state.update(case=c,restore=float('inf'),delay=case['delay_s'])
   log=(c/'collector.log').open('x');logs.append(log);p=subprocess.Popen([str(BIN),'--config',str(c/'config.yaml')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True);processes.append(p);until(lambda:ready(p))
   start=time.monotonic();restore=start+2
   with lock:state['restore']=restore
   for i in range(120):
    deadline=start+i*.05;remaining=deadline-time.monotonic()
    if remaining>0:time.sleep(remaining)
    event=dict(event_id=i,padding='x'*2048)
    payload={'resourceLogs':[{'scopeLogs':[{'logRecords':[{'timeUnixNano':str(time.time_ns()),'body':{'stringValue':json.dumps(event,sort_keys=True)}}]}]}]}
    data=json.dumps(payload).encode();dispatch=time.monotonic();req=urllib.request.Request('http://127.0.0.1:31331/v1/logs',data=data,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=5) as response:ack=dict(status=response.status,body=response.read().decode())
    with (c/'source.jsonl').open('a') as f:f.write(json.dumps(dict(id=i,planned_s=deadline,dispatch_s=dispatch,ack_s=time.monotonic(),ack=ack,event=event,wire_bytes=len(data)))+'\n')
   production_end=time.monotonic();until(lambda:count(c)==120)
   observation_end=time.monotonic();p.terminate();p.wait(timeout=10)
   (c/'execution.json').write_text(json.dumps(dict(**case,start_s=start,restore_s=restore,production_end_s=production_end,observation_end_s=observation_end,pid=p.pid,exit_code=p.returncode),indent=2)+'\n');print('completed',case,flush=True)
 finally:
  for p in processes:
   if p.poll() is None:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=5)
  server.shutdown();server.server_close()
  for log in logs:log.close()
  (OUT/'execution.json').write_text(json.dumps(dict(processes=[dict(pid=p.pid,exit_code=p.returncode) for p in processes],source_hashes={f:hashlib.sha256((R/f).read_bytes()).hexdigest() for f in ['run.py','config.py']},binary_sha256=hashlib.sha256(BIN.read_bytes()).hexdigest()),indent=2)+'\n')
if __name__=='__main__':main()
