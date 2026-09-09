import hashlib,http.server,json,os,shutil,signal,socket,sqlite3,subprocess,threading,time,urllib.request,urllib.error
from pathlib import Path
R=Path(__file__).resolve().parent
BIN=R.parents[2]/'tools/otelcol-0133/otelcol-contrib'
OUT=R/'results'
state={};lock=threading.Lock()
def post(payload):
 req=urllib.request.Request('http://127.0.0.1:31331/v1/logs',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=5) as r:return dict(status=r.status,body=r.read().decode())
def payload(event):
 return {'resourceLogs':[{'scopeLogs':[{'logRecords':[{'timeUnixNano':str(time.time_ns()),'body':{'stringValue':json.dumps(event)}}]}]}]}
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_POST(self):
  raw=self.rfile.read(int(self.headers['Content-Length']));body=json.loads(raw)
  events=[json.loads(x['body']['stringValue']) for r in body['resourceLogs'] for s in r['scopeLogs'] for x in s['logRecords']]
  with lock:
   c=state['case'];mode=state['mode'];now=time.monotonic();commit=mode!='outage'
   with sqlite3.connect(c/'backend.sqlite') as db:
    for e in events:
     db.execute('insert into deliveries(event_id,time_s,committed,body) values(?,?,?,?)',(e['event_id'],now,int(commit),json.dumps(e)))
     if commit:db.execute('insert or ignore into events(event_id,body) values(?,?)',(e['event_id'],json.dumps(e)))
   if mode=='lose_ack':state['mode']='healthy';code=503
   elif mode=='outage':code=503
   else:code=200
   with (c/'backend.jsonl').open('a') as f:f.write(json.dumps(dict(time_s=now,mode=mode,status=code,events=events,committed=commit))+'\n')
  self.send_response(code);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b'{}')
def count(c,table):
 with sqlite3.connect(c/'backend.sqlite') as db:return db.execute(f'select count(*) from {table}').fetchone()[0]
def until(fn,seconds=12):
 deadline=time.monotonic()+seconds
 while time.monotonic()<deadline:
  if fn():return
  time.sleep(.02)
 raise TimeoutError('condition not reached')
def ready(p):
 if p.poll() is not None:raise RuntimeError(f'collector exited {p.returncode}')
 try:
  with urllib.request.urlopen('http://127.0.0.1:31333',timeout=.2) as r:return r.status==200
 except Exception:return False
def config(c,persistent):
 ext=f'  file_storage:\n    directory: {c / "storage"}\n    fsync: true\n' if persistent else ''
 storage='      storage: file_storage\n' if persistent else ''
 return f'''extensions:
  health_check:
    endpoint: 127.0.0.1:31333
{ext}receivers:
  otlp:
    protocols:
      http:
        endpoint: 127.0.0.1:31331
exporters:
  otlphttp:
    endpoint: http://127.0.0.1:31332
    encoding: json
    compression: none
    timeout: 1s
    retry_on_failure:
      enabled: true
      initial_interval: 200ms
      max_interval: 1s
      max_elapsed_time: 0s
    sending_queue:
      enabled: true
      num_consumers: 1
      queue_size: 100
{storage}service:
  extensions: [health_check{', file_storage' if persistent else ''}]
  telemetry:
    logs:
      level: debug
  pipelines:
    logs:
      receivers: [otlp]
      exporters: [otlphttp]
'''
def main():
 assert not OUT.exists();OUT.mkdir()
 for port in [31331,31332,31333]:
  with socket.socket() as s:s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',port))
 server=http.server.ThreadingHTTPServer(('127.0.0.1',31332),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 active=[];logs=[];summary=[]
 def launch(c,n):
  log=(c/f'collector-{n}.log').open('x');logs.append(log)
  p=subprocess.Popen([str(BIN),'--config',str(c/'config.yaml')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True);active.append(p);until(lambda:ready(p));return p
 try:
  for trial in range(2):
   for name in ['memory_crash','file_crash','file_ack_loss']:
    c=OUT/f'{trial}-{name}';c.mkdir();(c/'storage').mkdir();persistent=name!='memory_crash'
    with sqlite3.connect(c/'backend.sqlite') as db:
     db.execute('create table deliveries(event_id text,time_s real,committed integer,body text)');db.execute('create table events(event_id text primary key,body text)')
    with lock:state.update(case=c,mode='lose_ack' if name=='file_ack_loss' else 'outage')
    (c/'config.yaml').write_text(config(c,persistent));p=launch(c,0);accepted=[];work=[]
    for i in range(5):
     start=time.perf_counter();cpu=time.process_time();value=sum(j*j for j in range(10000));cpu=time.process_time()-cpu;elapsed=time.perf_counter()-start
     e=dict(event_id=f'{trial}-{name}-{i}',task_id=f'task-{i}',attempt_id=0,value=value,cpu_s=cpu,elapsed_s=elapsed);work.append(e);accepted.append(post(payload(e)))
    until(lambda:count(c,'deliveries')>=1)
    lifecycle=[]
    if name!='file_ack_loss':
     killed=time.monotonic();os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=5);lifecycle.append(dict(action='SIGKILL',time_s=killed,pid=p.pid,exit_code=p.returncode))
     shutil.copytree(c/'storage',c/'storage-after-kill')
     with lock:state['mode']='healthy'
     p=launch(c,1)
     if persistent:until(lambda:count(c,'events')>=5)
     else:time.sleep(2)
    else:until(lambda:count(c,'deliveries')>=6 and count(c,'events')>=5)
    before_probe=count(c,'events')
    # A separately executed attempt keeps its own identity and resource usage.
    start=time.perf_counter();cpu=time.process_time();value=sum(j*j for j in range(10000));cpu=time.process_time()-cpu
    e=dict(event_id=f'{trial}-{name}-rerun',task_id='task-0',attempt_id=1,value=value,cpu_s=cpu,elapsed_s=time.perf_counter()-start);work.append(e);accepted.append(post(payload(e)));until(lambda:count(c,'events')>=before_probe+1)
    time.sleep(.3);p.terminate();p.wait(timeout=10);lifecycle.append(dict(action='terminate',pid=p.pid,exit_code=p.returncode,time_s=time.monotonic()))
    with sqlite3.connect(c/'backend.sqlite') as db:
     deliveries=db.execute('select event_id,time_s,committed,body from deliveries').fetchall();unique=db.execute('select event_id,body from events order by event_id').fetchall()
    record=dict(trial=trial,name=name,accepted=accepted,work=work,before_probe=before_probe,deliveries=deliveries,unique_events=unique,lifecycle=lifecycle)
    (c/'record.json').write_text(json.dumps(record,indent=2)+'\n');summary.append(record);print('completed',trial,name,'unique',len(unique),'deliveries',len(deliveries),flush=True)
 finally:
  cleanup=[]
  for p in active:
   if p.poll() is None:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=5)
   cleanup.append(dict(pid=p.pid,exit_code=p.returncode))
  server.shutdown();server.server_close()
  for l in logs:l.close()
  (OUT/'execution.json').write_text(json.dumps(dict(cleanup=cleanup,binary_sha256=hashlib.sha256(BIN.read_bytes()).hexdigest(),run_sha256=hashlib.sha256((R/'run.py').read_bytes()).hexdigest()),indent=2)+'\n')
if __name__=='__main__':main()
