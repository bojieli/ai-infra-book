import hashlib,json,os,signal,socket,subprocess,time,urllib.request,concurrent.futures,random
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
 model=json.loads((ROOT/'model.json').read_text());model_hash=hashlib.sha256((ROOT/'model.json').read_bytes()).hexdigest();assert model_hash==(ROOT/'model.sha256').read_text().strip()
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(MODEL)
 source=json.loads((ROOT/'agent-prompts.json').read_text());ids=source['requests'][-1]['prompt_token_ids'];text=tok.decode(ids,skip_special_tokens=False);assert tok.encode(text,add_special_tokens=False)==ids
 background='Background generation. Continue this unrelated sentence: '+ 'red green blue yellow '*64
 target=dict(text=text,sampling_params=dict(temperature=0,max_new_tokens=1,ignore_eos=True))
 (out/'inputs.json').write_text(json.dumps(dict(target=target,background=background,target_ids=ids),indent=2)+'\n')
 env=os.environ.copy();cuda=str(ENV/'lib/python3.10/site-packages/nvidia/cu13');env.update(CUDA_HOME=cuda,PATH=cuda+'/bin:'+env['PATH'],TVM_FFI_CACHE_DIR=str(ROOT.parents[1]/'09-08/jit-cache-cu13-v2'))
 ports=[31191,31192];procs=[];logs=[];commands=[];records=[]
 worker_common=json.loads((ROOT/'worker-command.json').read_text())
 def request(port,payload):
  start=time.monotonic();response=http(port,'/generate',payload);return dict(start_s=start,end_s=time.monotonic(),response=response)
 def load():return {str(port):http(port,'/get_load') for port in ports}
 try:
  for i,port in enumerate(ports):
   cmd=[str(port) if x=='PORT' else str(out/f'worker{i}-requests') if x=='REQUEST_LOG' else x for x in worker_common];commands.append(cmd)
   log=(out/f'worker{i}.log').open('x');logs.append(log);p=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);procs.append(p);wait_ready(p,port);print('ready',i,flush=True)
  order=[];rng=random.Random(910)
  for trial in range(2):
   budgets=[8,32,128];rng.shuffle(budgets)
   for budget in budgets:order.append(dict(trial=trial,policy='predicted_completion',output_budget=budget))
  (out/'order.json').write_text(json.dumps(order,indent=2)+'\n')
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
   for case in order:
    trial=case['trial'];policy=case['policy'];budget=case['output_budget'];label=f'book909p-{trial}-{budget}'
    for port in ports:http(port,'/flush_cache',{})
    warm=request(ports[0],{**target,'rid':label+'-warm'})
    busy_started=time.monotonic()
    busy=pool.submit(request,ports[0],dict(rid=label+'-busy',text=background,sampling_params=dict(temperature=0,max_new_tokens=budget,ignore_eos=True)))
    samples=[];deadline=time.monotonic()+15
    while True:
     state=load();samples.append(dict(time_s=time.monotonic(),loads=state))
     if state[str(ports[0])][0]['num_reqs']>=1:break
     if busy.done() or time.monotonic()>deadline:raise RuntimeError('failed to observe running background')
     time.sleep(.01)
    elapsed=time.monotonic()-busy_started
    predictions={str(ports[0]):max(0,model['busy128_s']*budget/128-elapsed)+model['warm_after_busy_s'],str(ports[1]):model['cold_concurrent_s']}
    selected=min(ports,key=lambda p:predictions[str(p)])
    decision=dict(time_s=time.monotonic(),elapsed_since_busy_submit_s=elapsed,predictions_s=predictions,selected_port=selected,model_sha256=model_hash)
    with (out/'decisions.jsonl').open('a') as f:f.write(json.dumps(dict(**case,**decision))+'\n')
    query=pool.submit(request,selected,{**target,'rid':label+'-target'})
    while not query.done():samples.append(dict(time_s=time.monotonic(),loads=load()));time.sleep(.01)
    result=query.result();background_result=busy.result()
    record=dict(**case,decision=decision,selected_port=selected,decision_load=state,warm=warm,target=result,background=background_result,samples=samples)
    records.append(record)
    with (out/'raw.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
    print('completed',trial,policy,flush=True)
 finally:
  cleanup=[dict(pid=p.pid,exit_code=stop(p)) for p in reversed(procs)]
  for log in logs:log.close()
  (out/'execution.json').write_text(json.dumps(dict(commands=commands,cleanup=cleanup,source_hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['run.py','worker-command.json','agent-prompts.json','model.json']}),indent=2)+'\n')
if __name__=='__main__':main()
