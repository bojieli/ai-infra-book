import hashlib,json,os,platform,random,subprocess,sys,threading,time
from pathlib import Path
P=Path(__file__).resolve().parent
clock=time.perf_counter_ns
fixture=json.loads((P/'fixture.json').read_text())
root=P/'results'; root.mkdir(exist_ok=False)
policies=['resident','demand','predict-50ms','predict-fullgap']
plan=[(t,p) for t in range(3) for p in policies];random.Random(1106).shuffle(plan)
(root/'environment.json').write_text(json.dumps(dict(platform=platform.platform(),python=platform.python_version(),plan=plan,seed=1106,buffer_bytes_per_worker=16*1024**2,source_hashes={n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ['run.py','worker.py','tools.py','fixture.json']}),indent=2)+'\n')
for trial,policy in plan:
 case=root/f'{trial}-{policy}';case.mkdir();work=case/'workspace';work.mkdir()
 for n,k in [('intervals.py','INITIAL'),('test_intervals.py','CHECKER'),('SPEC.txt','SPEC')]: (work/n).write_text(fixture['fixture'][k])
 live={};events=[];samples=[];done=threading.Event(); origin=clock()
 def sample():
  while not done.is_set():
   pids=list(live)
   start=clock()
   if pids:
    output=subprocess.run(['ps','-o','pid=,rss=','-p',','.join(map(str,pids))],capture_output=True,text=True)
    found=[dict(pid=int(line.split()[0]),rss_bytes=int(line.split()[1])*1024) for line in output.stdout.splitlines() if len(line.split())==2]
   else: found=[]
   samples.append(dict(start_ns=start,end_ns=clock(),workers=found));done.wait(.05)
 thread=threading.Thread(target=sample);thread.start()
 def launch(kind):
  start=clock(); p=subprocess.Popen([sys.executable,'-B',str(P/'worker.py'),kind,str(work)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
  live[p.pid]=p
  events.append(dict(event='launch',pid=p.pid,kind=kind,t_ns=start))
  return p
 def ready(p):
  r=json.loads(p.stdout.readline());assert r['event']=='ready';events.append(r);return r
 def stop(p):
  begin=clock();p.stdin.write(json.dumps({'stop':True})+'\n');p.stdin.flush();p.wait(timeout=5)
  stderr=p.stderr.read();live.pop(p.pid)
  events.append(dict(event='destroy',pid=p.pid,t_ns=begin,end_ns=clock(),returncode=p.returncode,stderr=stderr));assert p.returncode==0
 pool={}
 if policy=='resident':
  pool={k:launch(k) for k in ['file','test']}
  for p in pool.values():ready(p)
 transitions={};previous=None;rows=[]
 try:
  for source in fixture['rounds']:
   turn=source['turn'];gap=source['model_end_s']-source['model_start_s'];gap_start=clock()
   pred=transitions.get(previous,previous or 'file');prepared=None
   if policy.startswith('predict'):
    lead=min(.05,gap) if policy=='predict-50ms' else gap
    time.sleep(max(0,gap-lead));prepared=launch(pred)
   remaining=gap-(clock()-gap_start)/1e9
   if remaining>0:time.sleep(remaining)
   call=clock();action=source['action'];kind='test' if action['tool']=='run_tests' else 'file'
   if policy=='resident':p=pool[kind]
   elif prepared is not None:
    ready(prepared)
    if pred==kind:p=prepared
    else:stop(prepared);p=launch(kind);ready(p)
   else:p=launch(kind);ready(p)
   send=clock();p.stdin.write(json.dumps({'action':action})+'\n');p.stdin.flush();reply=json.loads(p.stdout.readline());received=clock()
   sha=hashlib.sha256((work/'intervals.py').read_bytes()).hexdigest()
   row=dict(turn=turn,kind=kind,predicted=pred if prepared else None,prediction_hit=pred==kind if prepared else None,gap_s=gap,gap_start_ns=gap_start,call_ns=call,send_ns=send,received_ns=received,worker_pid=p.pid,response=reply,file_sha256=sha)
   assert reply['reply']==source['tool_result'],(policy,turn,reply,source['tool_result'])
   assert sha==source['file_sha256']
   rows.append(row)
   if policy!='resident':stop(p)
   if previous is not None:transitions[previous]=kind
   previous=kind
  work_done=clock()
 finally:
  for p in list(live.values()):stop(p)
  end=clock();done.set();thread.join()
  (case/'raw.json').write_text(json.dumps(dict(trial=trial,policy=policy,origin_ns=origin,work_done_ns=work_done,end_ns=end,rows=rows,events=events,samples=samples),indent=2)+'\n')
 print(json.dumps(dict(trial=trial,policy=policy,completed_rounds=len(rows))),flush=True)
(root/'completion.json').write_text(json.dumps(dict(completed_cases=len(plan),completed=True))+'\n')
