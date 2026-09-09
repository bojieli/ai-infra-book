import hashlib,json,os,signal,socket,subprocess,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ENV=Path('/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv')
ROUTER='/home/ubuntu/ai-infra-book-experiments/tools/router032-venv/bin/python'
MODEL='/home/ubuntu/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218'
def http(port,path,payload=None):
 data=json.dumps(payload).encode() if payload is not None else None
 req=urllib.request.Request(f'http://127.0.0.1:{port}{path}',data=data,headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=120) as r:
  b=r.read();return json.loads(b) if b and r.headers.get_content_type()=='application/json' else b.decode()
def wait_ready(p,port):
 deadline=time.monotonic()+180
 while time.monotonic()<deadline:
  if p.poll() is not None:raise RuntimeError(f'process {p.pid} exited {p.returncode}')
  try:http(port,'/health');return
  except Exception:time.sleep(.2)
 raise TimeoutError(f'not ready {port}')
def stop(p):
 if p.poll() is None:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=10)
 return p.returncode
def main():
 out=ROOT/'results';assert not out.exists();out.mkdir()
 for port in [31091,31092,31090,31099]:
  with socket.socket() as s:
   s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',port))
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(MODEL)
 source=json.loads((ROOT/'agent-prompts.json').read_text());prompts=[]
 for r in source['requests']:
  text=tok.decode(r['prompt_token_ids'],skip_special_tokens=False)
  assert tok.encode(text,add_special_tokens=False)==r['prompt_token_ids']
  prompts.append(dict(id=r['id'],text=text,input_ids=r['prompt_token_ids']))
 (out/'prompts.json').write_text(json.dumps(prompts,indent=2)+'\n')
 env=os.environ.copy();cuda=str(ENV/'lib/python3.10/site-packages/nvidia/cu13');env.update(CUDA_HOME=cuda,PATH=cuda+'/bin:'+env['PATH'],TVM_FFI_CACHE_DIR=str(ROOT.parents[1]/'09-08/jit-cache-cu13-v2'))
 procs=[];logs=[];commands=[];records=[];cleanup=[]
 try:
  for i,port in enumerate([31091,31092]):
   cmd=[str(ENV/'bin/python'),'-m','sglang.launch_server','--model-path',MODEL,'--host','127.0.0.1','--port',str(port),'--dtype','bfloat16','--context-length','8192','--mem-fraction-static','0.25','--max-total-tokens','8192','--max-running-requests','8','--chunked-prefill-size','2048','--disable-cuda-graph','--attention-backend','triton','--sampling-backend','pytorch','--random-seed','909','--log-requests','--log-requests-level','0','--log-requests-format','json','--log-requests-target',str(out/f'worker{i}-requests')]
   log=(out/f'worker{i}.log').open('x');logs.append(log);p=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);procs.append(p);commands.append(cmd);wait_ready(p,port);print('ready worker',i,flush=True)
  for trial in range(3):
   policy='cache_aware';label=f'trial{trial}'
   for port in [31091,31092]:http(port,'/flush_cache',{})
   cmd=[ROUTER,'-m','sglang_router.launch_router','--host','127.0.0.1','--port','31090','--worker-urls','http://127.0.0.1:31091','http://127.0.0.1:31092','--policy',policy,'--prometheus-port','31099','--disable-retries','--log-level','debug']
   log=(out/f'router-{label}.log').open('x');logs.append(log);p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);procs.append(p);commands.append(cmd);wait_ready(p,31090)
   deadline=time.monotonic()+180
   while True:
    status=http(31090,'/workers')
    with (out/f'registration-{label}.jsonl').open('a') as f:f.write(json.dumps(status)+'\n')
    workers=status.get('workers',status.get('data',[])) if isinstance(status,dict) else status
    if len(workers)==2 and all(w.get('is_healthy') for w in workers):break
    if time.monotonic()>deadline:raise TimeoutError('worker registration')
    time.sleep(.2)
   r=prompts[-1]
   for stage in ['cold','warm','after_flush','rewarm']:
    if stage=='after_flush':
     event=dict(trial=trial,start_s=time.monotonic(),responses={str(port):http(port,'/flush_cache',{}) for port in [31091,31092]},end_s=time.monotonic())
     with (out/'flush-events.jsonl').open('a') as f:f.write(json.dumps(event)+'\n')
    rid=f'book909i-{trial}-{stage}';start=time.monotonic();response=http(31090,'/generate',dict(rid=rid,text=r['text'],sampling_params=dict(temperature=0,max_new_tokens=1,ignore_eos=True)));end=time.monotonic()
    record=dict(trial=trial,stage=stage,policy=policy,prompt_id=r['id'],rid=rid,start_s=start,end_s=end,response=response)
    with (out/'requests.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
   (out/f'metrics-{label}.txt').write_text(str(http(31099,'/metrics')))
   cleanup.append(dict(role='router',policy=policy,pid=p.pid,exit_code=stop(p)));print('completed',policy,flush=True)
 finally:
  for p in reversed(procs):cleanup.append(dict(pid=p.pid,exit_code=stop(p)))
  for log in logs:log.close()
  (out/'execution.json').write_text(json.dumps(dict(commands=commands,cleanup=cleanup,source_hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['run.py','agent-prompts.json']}),indent=2)+'\n')
if __name__=='__main__':main()
