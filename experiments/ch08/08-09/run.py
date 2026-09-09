import argparse,asyncio,json,time,os,hashlib,subprocess,sys
from pathlib import Path
from dataclasses import asdict,is_dataclass
ROOT=Path(__file__).absolute().parent
async def main(a):
 os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
 import torch,vllm
 from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
 from vllm.v1.metrics.loggers import StatLoggerBase
 from transformers import AutoTokenizer
 root=a.out.absolute();root.mkdir(parents=True,exist_ok=False)
 protocol=json.loads((ROOT/'protocol.json').read_text());inputs=json.loads((ROOT/'inputs.json').read_text());tasks={t['id']:t for t in inputs['tasks']};tok=AutoTokenizer.from_pretrained(a.model,local_files_only=True)
 for t in tasks.values():assert tok.apply_chat_template(t['messages'],tokenize=True,add_generation_prompt=True,enable_thinking=False,return_dict=False)==t['prompt_token_ids']
 (root/'protocol.json').write_bytes((ROOT/'protocol.json').read_bytes());(root/'inputs.json').write_bytes((ROOT/'inputs.json').read_bytes())
 config=dict(model=a.model,dtype='bfloat16',kv_cache_dtype='auto',attention_backend='TRITON_ATTN',max_model_len=16384,max_num_seqs=4,max_num_batched_tokens=16384,enable_chunked_prefill=True,enable_prefix_caching=False,enforce_eager=True,async_scheduling=False,kv_cache_memory_bytes=12*1024**3,gpu_memory_utilization=.5,seed=809,disable_log_stats=False)
 (root/'environment.json').write_text(json.dumps(dict(config=config,torch=torch.__version__,vllm=vllm.__version__,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
 statlog=(root/'stats.jsonl').open('w',buffering=1);requests=(root/'requests.jsonl').open('w',buffering=1);groups=(root/'groups.jsonl').open('w',buffering=1);state={'group':'init'}
 def serial(x):return asdict(x) if is_dataclass(x) else vars(x) if hasattr(x,'__dict__') else str(x)
 class Stats(StatLoggerBase):
  def __init__(self,*args,**kw):pass
  def log_engine_initialized(self):pass
  def record(self,scheduler_stats,iteration_stats,mm_cache_stats=None,engine_idx=0):statlog.write(json.dumps(dict(group=state['group'],observed_s=time.monotonic(),scheduler=scheduler_stats,iteration=iteration_stats),default=serial)+'\n')
 engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config),stat_loggers=[lambda cfg,idx:Stats(cfg,idx)])
 async def energy():
  result=await asyncio.to_thread(subprocess.run,['sudo','-n',str(Path(sys.executable).absolute()),'-B',str(ROOT/'energy.py')],capture_output=True,text=True,timeout=10,check=True)
  return json.loads(result.stdout)
 async def one(tid,rid,intended,sem):
  await asyncio.sleep(max(0,intended-time.monotonic()));arrived=time.monotonic()
  if sem:await sem.acquire()
  try:
   start=time.monotonic();events=[];final=None
   async for out in engine.generate({'prompt_token_ids':tasks[tid]['prompt_token_ids']},SamplingParams(temperature=0,max_tokens=128),rid):events.append([time.monotonic(),len(out.outputs[0].token_ids)]);final=out
   end=time.monotonic();seq=final.outputs[0]
   assert final.prompt_token_ids==tasks[tid]['prompt_token_ids'] and tok.decode(seq.token_ids,skip_special_tokens=True)==seq.text
   assert seq.finish_reason!='stop' or seq.token_ids[-1]==tok.eos_token_id
   r=dict(group=state['group'],id=rid,task_id=tid,intended_arrival_s=intended,actual_arrival_s=arrived,submitted_s=start,end_s=end,events=events,output_ids=list(seq.token_ids),text=seq.text,finish_reason=seq.finish_reason,metrics=asdict(final.metrics),cached_tokens=final.num_cached_tokens)
   requests.write(json.dumps(r)+'\n');return r
  finally:
   if sem:sem.release()
 try:
  state['group']='warm';begin=time.monotonic();await asyncio.gather(*(one(tid,'warm-'+tid,begin,None) for tid in tasks))
  for g in protocol['groups']:
   state['group']=g['id'];before=await energy();begin=time.monotonic();sem=asyncio.Semaphore(1) if g['service']=='serial' else None
   await asyncio.gather(*(one(tid,g['id']+f'-{i}',begin+(i/g['rate'] if g['rate'] is not None else 0),sem) for i,tid in enumerate(g['tasks'])))
   end=time.monotonic();after=await energy();groups.write(json.dumps(dict(**g,start_s=begin,end_s=end,energy_before=before,energy_after=after))+'\n');print(g['id'],'complete',round(end-begin,3),flush=True)
  (root/'completion.json').write_text(json.dumps(dict(groups=len(protocol['groups']),formal_requests=sum(len(g['tasks']) for g in protocol['groups']),warmup_requests=len(tasks)),indent=2)+'\n')
 finally:engine.shutdown();statlog.close();requests.close();groups.close()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--out',type=Path,required=True);asyncio.run(main(p.parse_args()))
