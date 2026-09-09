"""Standalone real four-attempt Agent run; launch with supervisor.py."""
import asyncio, hashlib, json, os, resource, subprocess, sys, time
from pathlib import Path
from dataclasses import asdict
import fixture
R=Path(__file__).resolve().parent
RAW=R/'raw'
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def limits():
 fixture.limits();resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,1024**2))
def child(argv,work,timeout=4):
 start=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN)
 try:
  p=subprocess.run(argv,cwd=work,capture_output=True,text=True,timeout=timeout,preexec_fn=limits)
  result=dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
 except subprocess.TimeoutExpired as e:result=dict(returncode=None,stdout=(e.stdout or b'').decode() if isinstance(e.stdout,bytes) else e.stdout or '',stderr='TimeoutExpired',timeout=True)
 after=resource.getrusage(resource.RUSAGE_CHILDREN)
 return result,dict(wall_s=time.monotonic()-start,child_cpu_s=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime)
def execute(action,work,arm):
 if action.get('tool')!='run_tests':return fixture.execute(action,work),{}
 base,cost=child([sys.executable,'-B','test_intervals.py'],work)
 reply=dict(base);audit=dict(original_result=base,cost=cost)
 if arm=='feedback' and base['returncode']==0 and not json.loads(base['stdout'])['passed']:
  proc,diagcost=child([sys.executable,'-B',str(R/'diagnose.py')],work,5)
  reply['diagnostics_process']=proc
  reply['diagnostics']=json.loads(proc['stdout']) if proc['returncode']==0 else None
  audit['diagnostic_cost']=diagcost
 return reply,audit
async def main():
 from transformers import AutoTokenizer
 import transformers,torch,vllm
 from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
 torch.set_num_threads(1);torch.set_num_interop_threads(1)
 old=json.loads(Path('/home/ubuntu/ai-infra-book-experiments/ch11/11-01/results/environment.json').read_text())
 config=old['config'];assert config['model'].endswith('b968826d9c46dd6066d109eabc6255188de91218')
 config.update(kv_cache_memory_bytes=2*1024**3,gpu_memory_utilization=.24)
 tokenizer=AutoTokenizer.from_pretrained(config['model'],local_files_only=True)
 dump(RAW/'environment.json',dict(config=config,torch=torch.__version__,vllm=vllm.__version__,transformers=transformers.__version__,affinity=sorted(os.sched_getaffinity(0)),env={k:os.environ.get(k) for k in ['VLLM_USE_FLASHINFER_SAMPLER','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS']},protocol_sha256=sha((R/'PROTOCOL.md').read_bytes())))
 engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config))
 (RAW/'engine-ready').write_text(str(time.time()))
 try:
  for index,arm in enumerate(['baseline','feedback','feedback','baseline']):
   out=RAW/f'{index}-{arm}';work=out/'workspace';work.mkdir(parents=True)
   for name,content in [('intervals.py',fixture.INITIAL),('SPEC.txt',fixture.SPEC),('test_intervals.py',fixture.CHECKER)]: (work/name).write_text(content)
   reset=await engine.reset_prefix_cache();dump(out/'start.json',dict(index=index,arm=arm,reset_prefix_cache=reset,warmth='first engine request; page cache unknown' if index==0 else 'engine kernels warm; prefix cache reset',initial_hashes={p.name:sha(p.read_bytes()) for p in work.iterdir()}));assert reset is True
   messages=json.loads((R/'initial-messages.json').read_text());dump(out/'initial-messages.json',messages)
   base,audit=execute({'tool':'run_tests'},work,'baseline');dump(out/'baseline.json',dict(result=base,audit=audit))
   origin=time.monotonic();completed=False
   with (out/'rounds.jsonl').open('w',buffering=1) as log:
    for turn in range(12):
     tokens=tokenizer.apply_chat_template(messages,tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
     assert isinstance(tokens,list) and all(isinstance(t,int) for t in tokens)
     start=time.monotonic();events=[];final=None
     async for result in engine.generate({'prompt_token_ids':tokens},SamplingParams(temperature=0,max_tokens=1200),f'{index}-{turn}'):
      final=result;events.append(dict(t_s=time.monotonic()-origin,token_count=len(result.outputs[0].token_ids),text=result.outputs[0].text))
     end=time.monotonic();text=final.outputs[0].text;before=(work/'intervals.py').read_text();toolstart=time.monotonic()
     try:action=json.loads(text);reply,audit=execute(action,work,arm)
     except Exception as e:action={'tool':'invalid'};reply={'error':type(e).__name__+': '+str(e)};audit={}
     toolend=time.monotonic();code=(work/'intervals.py').read_text();(out/f'code-{turn:02}.py').write_text(code)
     row=dict(turn=turn,arm=arm,messages=messages,prompt_token_ids=tokens,output_token_ids=list(final.outputs[0].token_ids),output_text=text,finish_reason=final.outputs[0].finish_reason,cached_tokens=final.num_cached_tokens,engine_metrics=asdict(final.metrics) if final.metrics else None,output_events=events,model_start_s=start-origin,model_end_s=end-origin,tool_start_s=toolstart-origin,tool_end_s=toolend-origin,action=action,tool_result=reply,tool_audit=audit,code_before=before,file_sha256=sha(code.encode()),hashes={k:sha(json.dumps(v,sort_keys=True).encode()) for k,v in dict(messages=messages,prompt_token_ids=tokens,output_token_ids=list(final.outputs[0].token_ids),tool_result=reply).items()},output_sha256=sha(text.encode()))
     log.write(json.dumps(row)+'\n')
     messages=messages+[dict(role='assistant',content=text),dict(role='user',content='Tool result: '+json.dumps(reply))]
     if action.get('tool')=='finish':completed=True;break
   check,audit=execute({'tool':'run_tests'},work,'baseline')
   dump(out/'final.json',dict(agent_finished=completed,validation=check,audit=audit,elapsed_s=time.monotonic()-origin,final_code=(work/'intervals.py').read_text(),rounds=turn+1))
   print(json.dumps(dict(index=index,arm=arm,attempt_ended=True)),flush=True)
 finally:
  engine.shutdown();(RAW/'engine-shutdown').write_text(str(time.time()))
if __name__=='__main__':asyncio.run(main())
