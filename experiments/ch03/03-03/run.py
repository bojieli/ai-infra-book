import asyncio,argparse,hashlib,json,os,random,time
from dataclasses import asdict
from pathlib import Path
from tasks import TASKS,answer,dp,prompt
R=Path(__file__).resolve().parent
async def main(model):
 os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
 import torch,vllm
 from transformers import AutoTokenizer
 from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
 out=R/'results';out.mkdir(exist_ok=False)
 truth={t['id']:answer(t) for t in TASKS};assert all(truth[t['id']]==dp(t) for t in TASKS)
 (out/'tasks.json').write_text(json.dumps(dict(tasks=TASKS,answers=truth),indent=2))
 config=dict(model=model,dtype='bfloat16',max_model_len=8192,max_num_seqs=2,max_num_batched_tokens=512,enable_chunked_prefill=True,enable_prefix_caching=False,enforce_eager=True,gpu_memory_utilization=.30,kv_cache_memory_bytes=6*1024**3,seed=303,async_scheduling=False)
 (out/'environment.json').write_text(json.dumps(dict(config=config,torch=torch.__version__,vllm=vllm.__version__,source_hashes={f:hashlib.sha256((R/f).read_bytes()).hexdigest() for f in ['run.py','tasks.py']}),indent=2))
 order=[dict(trial=trial,task=t['id'],policy=p) for trial in range(2) for t in TASKS for p in ['serial','parallel','adaptive']];random.Random(303).shuffle(order)
 (out/'order.json').write_text(json.dumps(order,indent=2));tok=AutoTokenizer.from_pretrained(model,local_files_only=True);engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config))
 async def generate(task,trial,index,group):
  messages=[dict(role='user',content=prompt(task))];ids=tok.apply_chat_template(messages,tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=True)
  start=time.monotonic();events=[];final=None
  async for o in engine.generate({'prompt_token_ids':ids},SamplingParams(temperature=.6,top_p=.95,max_tokens=1024,seed=30300+trial*10+index),f'{group}-{index}'):
   final=o;events.append(dict(at=time.monotonic(),tokens=len(o.outputs[0].token_ids)))
  end=time.monotonic();o=final.outputs[0];vs=time.monotonic();value=None;error=None
  try:
   assert '</think>' in o.text,'no final-answer delimiter'
   parsed=json.loads(o.text.split('</think>',1)[1].strip());assert set(parsed)=={'count'} and type(parsed['count']) is int
   value=parsed['count']
  except Exception as e:error=repr(e)
  ve=time.monotonic()
  return dict(index=index,messages=messages,input_ids=ids,output_ids=list(o.token_ids),text=o.text,finish_reason=o.finish_reason,cached_tokens=final.num_cached_tokens,metrics=asdict(final.metrics) if final.metrics else None,start=start,end=end,validation_start=vs,validation_end=ve,events=events,value=value,error=error)
 try:
  for g,c in enumerate(order):
   task=next(t for t in TASKS if t['id']==c['task']);n=1 if c['policy']=='adaptive' and len(task['values'])<=8 else 2;start=time.monotonic()
   if c['policy']=='parallel':rows=await asyncio.gather(*(generate(task,c['trial'],i,g) for i in range(n)))
   else:rows=[await generate(task,c['trial'],i,g) for i in range(n)]
   ss=time.monotonic();valid=[r['value'] for r in rows if r['value'] is not None]
   selected=max(valid,key=lambda x:valid.count(x)) if valid else None
   selected_at=time.monotonic();correct=selected==truth[c['task']];scored=time.monotonic()
   record=dict(group=g,**c,candidates=rows,start=start,selection_start=ss,selected_at=selected_at,scored_at=scored,selected=selected,correct=correct,fee=None)
   with (out/'raw.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
   print(g,c,'tokens',[len(r['output_ids']) for r in rows],'values',[r['value'] for r in rows],'correct',correct,flush=True)
 finally:engine.shutdown()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);a=p.parse_args();asyncio.run(main(a.model))
