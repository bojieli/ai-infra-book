import argparse,hashlib,http.server,json,os,random,signal,sqlite3,subprocess,sys,threading,time
from pathlib import Path
B=Path(__file__).resolve().parent

def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
class Manager:
 def __init__(self,root,job):
  self.root=root;self.job=job;self.lock=threading.Lock();self.cut=threading.Event();self.release=threading.Event();self.db=sqlite3.connect(root/'manager.sqlite',check_same_thread=False);self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA synchronous=FULL');self.db.executescript('CREATE TABLE tokens(seq INTEGER PRIMARY KEY, token INTEGER NOT NULL, eos INTEGER NOT NULL, attempt INTEGER NOT NULL, commit_before REAL NOT NULL); CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);');self.db.execute('INSERT INTO meta VALUES (?,?)',('request_id',job['request_id']));self.db.commit();self.finished=[]
 def event(self,**x):
  with (self.root/'manager-events.jsonl').open('a') as f:f.write(json.dumps(dict(time=time.monotonic(),**x))+'\n')
 def handle(self,path,x):
  with self.lock:
   if path=='/state':
    assert x['model_revision']==self.job['model_revision'];old=self.db.execute("SELECT value FROM meta WHERE key='prompt_sha'").fetchone()
    if old:assert old[0]==x['prompt_sha']
    else:
     for k in ['prompt_sha','prompt_ids','model_revision']:self.db.execute('INSERT INTO meta VALUES (?,?)',(k,x[k] if isinstance(x[k],str) else json.dumps(x[k])))
     self.db.commit()
    records=self.db.execute('SELECT seq,token,eos FROM tokens ORDER BY seq').fetchall();assert [r[0] for r in records]==list(range(len(records)));assert not any(r[2] for r in records),'Cannot resume terminal prefix';self.event(kind='state_read',count=len(records));return 200,{'tokens':[r[1] for r in records]},False
   if path=='/token':
    seq=x['seq'];old=self.db.execute('SELECT token,eos FROM tokens WHERE seq=?',(seq,)).fetchone();count=self.db.execute('SELECT count(*) FROM tokens').fetchone()[0]
    conflict=bool(old and tuple(old)!=(x['token'],int(x['eos']))) or (old is None and seq!=count)
    if conflict:self.event(kind='conflict',**x);return 409,{'conflict':True},False
    duplicate=old is not None;before=time.monotonic()
    if not duplicate:self.db.execute('INSERT INTO tokens VALUES (?,?,?,?,?)',(seq,x['token'],int(x['eos']),x['attempt'],before))
    self.db.commit();committed=time.monotonic();cut=self.job['strategy']!='baseline' and x['attempt']==0 and not x['eos'] and seq+1==self.job['cut']
    self.event(kind='committed',duplicate=duplicate,commit_start=before,commit_complete=committed,cut=cut,**x)
    if cut:self.cut.set()
    return 200,{'accepted':True,'duplicate':duplicate,'seq':seq},cut
   if path=='/finish':self.finished.append(x);self.event(kind='finish',**x);return 200,{'accepted':True},False
   raise ValueError(path)
 def close(self):
  with self.lock:
   dest=sqlite3.connect(self.root/'manager-snapshot.sqlite');self.db.backup(dest);dest.close();self.db.execute('PRAGMA wal_checkpoint(TRUNCATE)');self.db.close()

def run_case(root,job,totalstart):
 root.mkdir();dump(root/'job.json',job);manager=Manager(root,job)
 class Handler(http.server.BaseHTTPRequestHandler):
  def log_message(self,*a):pass
  def do_POST(self):
   try:
    x=json.loads(self.rfile.read(int(self.headers['Content-Length'])));code,value,cut=manager.handle(self.path,x)
    if cut:
     manager.release.wait(timeout=310)
     with manager.lock:manager.event(kind='ack_suppressed',seq=x['seq'],attempt=x['attempt'])
     self.close_connection=True;return
    raw=json.dumps(value).encode();self.send_response(code);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
   except (BrokenPipeError,ConnectionResetError):pass
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True;thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url=f'http://127.0.0.1:{server.server_port}';processes=[];resources=[]
 try:
  for attempt in [0,1]:
   name=f'attempt-{attempt}';cmd=[sys.executable,'-B',str(B/'worker.py'),'--job',str(root/'job.json'),'--output',str(root/name),'--url',url,'--attempt',str(attempt)]
   with (root/f'{name}.log').open('w') as log:
    proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);start=time.monotonic();killed=None
    try:
     while proc.poll() is None:
      own=[]
      for line in subprocess.check_output(['ps','-axo','pid=,ppid=,pgid=,rss='],text=True).splitlines():
       pid,ppid,pgid,rss=map(int,line.split())
       if pgid==proc.pid:own.append(dict(pid=pid,ppid=ppid,rss_bytes=rss*1024))
      resources.append(dict(time=time.monotonic(),attempt=attempt,members=own,rss_bytes=sum(x['rss_bytes'] for x in own)));assert resources[-1]['rss_bytes']<=16*1024**3;assert time.monotonic()-start<300 and time.monotonic()-totalstart<1800
      if attempt==0 and manager.cut.is_set():
       assert os.getpgid(proc.pid)==proc.pid;killed=time.monotonic();os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=20);manager.release.set();break
      time.sleep(.1)
     code=proc.wait(timeout=20);assert code==(-9 if killed else 0),(job['request_id'],attempt,code)
    finally:
     if proc.poll() is None:
      assert os.getpgid(proc.pid)==proc.pid;os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=20)
     manager.release.set()
    remaining=[s for s in subprocess.check_output(['ps','-axo','pid=,pgid=,stat='],text=True).splitlines() if int(s.split()[1])==proc.pid and not s.split()[2].startswith('Z')];assert not remaining
    processes.append(dict(attempt=attempt,pid=proc.pid,start=start,end=time.monotonic(),returncode=code,killed=killed,leftover=[]));dump(root/'execution.json',processes);dump(root/'resources.json',resources)
   if killed is None:break
 finally:manager.release.set();server.shutdown();server.server_close();thread.join();manager.close()
 dump(root/'completion.json',dict(done=True,preempted=bool(processes[0]['killed']),finishes=manager.finished,wall_s=processes[-1]['end']-processes[0]['start'],max_rss_bytes=max(r['rss_bytes'] for r in resources)))
 print(job['request_id'],'done',flush=True)

def main(a):
 root=B/a.name;root.mkdir(exist_ok=False);spec=json.loads((B/'tasks.json').read_text());meta=json.loads((B/'model-identity.json').read_text());jobs=[]
 for task in spec['smoke' if a.smoke else 'formal']:
  for cut in ([8] if a.smoke else [32,96]):
   for strategy in ['baseline','restart','preserve']:jobs.append(dict(request_id=f'{task["id"]}-k{cut}-{strategy}',task=task,cut=cut,strategy=strategy,max_tokens=128 if a.smoke else 768,model_revision=meta['revision']))
 if not a.smoke:random.Random(1104).shuffle(jobs)
 dump(root/'plan.json',jobs);dump(root/'source-sha.json',{n:hashlib.sha256((B/n).read_bytes()).hexdigest() for n in ['worker.py','launch.py','tasks.json','PROTOCOL.md','model-identity.json','installed-source-sha.json']});start=time.monotonic()
 for job in jobs:run_case(root/job['request_id'],job,start)
 dump(root/'completion.json',dict(done=True,paths=len(jobs),wall_s=time.monotonic()-start))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--smoke',action='store_true');main(p.parse_args())
