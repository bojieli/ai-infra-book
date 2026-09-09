import hashlib,json,os,resource,subprocess,sys,time,urllib.request,urllib.error,signal
from pathlib import Path
import fixture
R=Path(__file__).resolve().parent
RAW=R/'raw'
ARMS=['baseline','proper-exit','proper-exit','baseline']
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def limits():
 fixture.limits();resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576))
def child(argv,work):
 start=time.time()
 try:
  p=subprocess.run(argv,cwd=work,capture_output=True,text=True,timeout=5,preexec_fn=limits)
  result=dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
 except subprocess.TimeoutExpired as e:
  result=dict(returncode=None,stdout=(e.stdout or b'').decode(),stderr=(e.stderr or b'').decode(),timeout=True)
 return result,dict(argv=argv,cwd=str(work),start_unix=start,end_unix=time.time(),limits=dict(cpu_s=2,as_bytes=536870912,wall_s=5,file_bytes=1048576))
def check(work,arm):return child([sys.executable,'-B',str(R/'wrapper.py'),arm],work)
def environment():
 with urllib.request.urlopen('http://127.0.0.1:8000/v1/models',timeout=10) as p:models=p.read().decode()
 cmd=Path('/proc/3613078/cmdline').read_bytes().replace(b'\0',b' ').decode()
 root='/home/ubuntu/.cache/huggingface/hub/models--Qwen--Qwen3-VL-30B-A3B-Instruct-FP8/snapshots/d9748a51ae66354c4dad665aab2c71f26cf2c8cd'
 assert root in cmd and any(m['id']=='qwen-fast' and m['root']==root for m in json.loads(models)['data'])
 return dict(time_unix=time.time(),models_raw=models,server_cmdline=cmd,engine_stat=Path('/proc/3614304/stat').read_text(),gpu_background=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader'],text=True),affinity=sorted(os.sched_getaffinity(0)),threads={k:os.environ[k] for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS']},model_config=json.loads(Path(root,'config.json').read_text()),cost=None,kernel_time=None,scheduling_time=None)
def worker():
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
 lock=json.loads((R/'run.lock.json').read_text())
 for name,h in lock.items():assert sha((R/name).read_bytes())==h
 dump(RAW/'service-before.json',environment())
 # Before any model request, demonstrate real process-code-only intervention on INITIAL.
 w=RAW/'preflight';w.mkdir()
 for n,c in [('intervals.py',fixture.INITIAL),('test_intervals.py',fixture.CHECKER)]: (w/n).write_text(c)
 a,aa=check(w,'baseline');b,ba=check(w,'proper-exit')
 assert a['returncode']==0 and b['returncode']==1 and a['stdout']==b['stdout'] and a['stderr']==b['stderr'] and not json.loads(a['stdout'])['passed']
 dump(RAW/'wrapper-proof.json',dict(baseline=a,proper_exit=b,audit=[aa,ba]))
 origin=time.time();deadline=origin+1200
 for i,arm in enumerate(ARMS):
  out=RAW/f'{i}-{arm}';work=out/'workspace';work.mkdir(parents=True)
  for n,c in [('intervals.py',fixture.INITIAL),('SPEC.txt',fixture.SPEC),('test_intervals.py',fixture.CHECKER)]: (work/n).write_text(c)
  messages=json.loads((R/'initial-messages.json').read_text());finished=False
  with (out/'rounds.jsonl').open('w',buffering=1) as log:
   for turn in range(12):
    before=(work/'intervals.py').read_text()
    request=dict(model='qwen-fast',messages=messages,temperature=0,top_p=1,seed=304,max_tokens=1200,stream=False,chat_template_kwargs=dict(enable_thinking=False))
    body=json.dumps(request).encode();(out/f'request-{turn:02}.json').write_bytes(body)
    start=time.time();assert start<deadline
    try:
     with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000/v1/chat/completions',data=body,headers={'Content-Type':'application/json'}),timeout=min(120,deadline-start)) as p:raw=p.read();status=p.status;headers=dict(p.headers)
    except urllib.error.HTTPError as e:raw=e.read();status=e.code;headers=dict(e.headers)
    end=time.time();(out/f'response-{turn:02}.json').write_bytes(raw)
    response=json.loads(raw);assert status==200,response
    choice=response['choices'][0];text=choice['message']['content'];finish=choice['finish_reason'];audit={}
    try:
     if finish=='length':raise ValueError('Model output finish_reason=length')
     action=json.loads(text)
     if action.get('tool')=='run_tests':reply,audit=check(work,arm)
     else:reply=fixture.execute(action,work)
    except Exception as e:action={'tool':'invalid'};reply={'error':type(e).__name__+': '+str(e)}
    code=(work/'intervals.py').read_text();(out/f'code-{turn:02}.py').write_text(code)
    row=dict(turn=turn,arm=arm,request=request,response=response,http_status=status,http_headers=headers,client_start_unix=start,client_end_unix=end,messages=messages,output_text=text,finish_reason=finish,usage=response.get('usage'),prompt_token_ids=None,output_token_ids=None,kernel_time=None,scheduling_time=None,cost=None,action=action,tool_result=reply,tool_audit=audit,code_before=before,code_after=code,file_sha256=sha(code.encode()),request_sha256=sha(body),response_sha256=sha(raw))
    log.write(json.dumps(row)+'\n');messages=messages+[dict(role='assistant',content=text),dict(role='user',content='Tool result: '+json.dumps(reply))]
    if action.get('tool')=='finish':finished=True;break
  result,audit=check(work,'baseline')
  dump(out/'final.json',dict(agent_finished=finished,validation=result,audit=audit,rounds=turn+1,final_code=code,final_sha256=sha(code.encode())))
  print(json.dumps(dict(attempt=i,arm=arm,rounds=turn+1,finished=finished,validation=result)),flush=True)
 dump(RAW/'model-ended.json',dict(start_unix=origin,end_unix=time.time(),elapsed_s=time.time()-origin))
 for i,arm in enumerate(ARMS):
  out=RAW/f'{i}-{arm}';p,a=child([sys.executable,'-B',str(R/'check_code.py'),str(out/'workspace/intervals.py'),'--child'],out)
  dump(out/'independent-checks.json',dict(result=p,audit=a,checker_sha256=sha((R/'check_code.py').read_bytes())))
 dump(RAW/'service-after.json',environment())
def tree(pid):
 found=[pid]
 try:
  for c in Path(f'/proc/{pid}/task/{pid}/children').read_text().split():found+=tree(int(c))
 except FileNotFoundError:pass
 return found
def supervise():
 RAW.mkdir()
 p=subprocess.Popen([sys.executable,'-B',str(R/'run.py'),'--worker'],start_new_session=True)
 start=time.time();reason=None
 with (RAW/'resources.jsonl').open('w',buffering=1) as f:
  while p.poll() is None:
   rows=[]
   for pid in [os.getpid()]+tree(p.pid):
    try:
     status=Path(f'/proc/{pid}/status').read_text();rss=int(next((x.split()[1] for x in status.splitlines() if x.startswith('VmRSS:')),'0'))*1024
     rows.append(dict(pid=pid,rss_bytes=rss,stat=Path(f'/proc/{pid}/stat').read_text(),affinity=sorted(os.sched_getaffinity(pid))))
    except (FileNotFoundError,ProcessLookupError):pass
   total=sum(x['rss_bytes'] for x in rows);f.write(json.dumps(dict(time_unix=time.time(),processes=rows,rss_bytes=total))+'\n')
   if total>2*1024**3 or time.time()-start>1250:
    reason='rss_or_wall_limit';os.killpg(p.pid,signal.SIGKILL);break
   time.sleep(.25)
 rc=p.wait();dump(RAW/'exit.json',dict(returncode=rc,reason=reason,elapsed_s=time.time()-start,remaining_owned=[x for x in tree(p.pid) if Path(f'/proc/{x}').exists()]))
 sys.exit(rc)
if __name__=='__main__':
 os.sched_setaffinity(0,{8,9,10,11})
 for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
 if '--worker' in sys.argv:worker()
 else:supervise()
