import argparse,asyncio,hashlib,json,os,random,time,subprocess,sys
from dataclasses import asdict
from pathlib import Path
from fixture import INITIAL,SPEC,CHECKER,execute,limits
R=Path(__file__).resolve().parent
async def main(model):
 os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
 import torch,vllm
 from transformers import AutoTokenizer
 from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
 out=R/'results';assert not out.exists();out.mkdir();tok=AutoTokenizer.from_pretrained(model,local_files_only=True)
 config=dict(model=model,dtype='bfloat16',max_model_len=8192,max_num_seqs=1,max_num_batched_tokens=512,enable_chunked_prefill=True,enable_prefix_caching=False,enforce_eager=True,gpu_memory_utilization=.30,kv_cache_memory_bytes=6*1024**3,seed=1108,async_scheduling=False)
 (out/'environment.json').write_text(json.dumps(dict(config=config,torch=torch.__version__,vllm=vllm.__version__,source_hashes={f:hashlib.sha256((R/f).read_bytes()).hexdigest() for f in ['run.py','fixture.py','check_code.py']}),indent=2)+'\n')
 base=[dict(role='system',content='Repair the function. Return exactly one JSON object with a single content field containing the complete Python code. No imports. No markdown.'),dict(role='user',content=SPEC+'\nCurrent implementation:\n'+INITIAL)]
 engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config));rng=random.Random(1109);rows=[]
 async def attempt(trial,stage,messages,initial_code):
  setup=time.monotonic();label=f'{trial}-{stage}';work=out/label;work.mkdir()
  for name,content in [('intervals.py',initial_code),('SPEC.txt',SPEC),('test_intervals.py',CHECKER)]: (work/name).write_text(content)
  setup_end=time.monotonic();ids=tok.apply_chat_template(messages,tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
  start=time.monotonic();events=[];final=None
  async for output in engine.generate({'prompt_token_ids':ids},SamplingParams(temperature=0,max_tokens=1000),label):
   events.append(dict(time_s=time.monotonic(),token_count=len(output.outputs[0].token_ids)));final=output
  end=time.monotonic();o=final.outputs[0]
  try:
   proposal=json.loads(o.text);write=execute(dict(tool='write_file',path='intervals.py',content=proposal['content']),work);check=execute(dict(tool='run_tests'),work)
   result=dict(write=write,validation=check,passed=check['returncode']==0 and json.loads(check['stdout'])['passed'])
  except Exception as e:result=dict(passed=False,error=type(e).__name__+': '+str(e))
  done=time.monotonic();row=dict(trial=trial,stage=stage,request_id=label,messages=messages,initial_code=initial_code,setup_start_s=setup,setup_end_s=setup_end,input_ids=ids,output_ids=list(o.token_ids),output_text=o.text,finish_reason=o.finish_reason,cached_tokens=final.num_cached_tokens,start_s=start,model_end_s=end,done_s=done,events=events,result=result,final_code=(work/'intervals.py').read_text())
  with (out/'raw.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  rows.append(row);print('completed',label,len(o.token_ids),result['passed'],flush=True);return row
 try:
  for trial in range(2):
   initial=await attempt(trial,'initial',base,INITIAL)
   if initial['result']['passed']:continue
   stages=['restart','continue'];rng.shuffle(stages)
   for stage in stages:
    if stage=='restart':await attempt(trial,stage,base,INITIAL)
    else:
     messages=base+[dict(role='assistant',content=initial['output_text']),dict(role='user',content='Tests failed. Repair using this feedback and return the same JSON schema. Tool result: '+json.dumps(initial['result']))]
     await attempt(trial,stage,messages,initial['final_code'])
 finally:engine.shutdown()
 checks=[]
 for row in rows:
  if 'write' not in row['result']:continue
  path=out/row['request_id']/'intervals.py';p=subprocess.run([sys.executable,str(R/'check_code.py'),str(path),'--child'],capture_output=True,text=True,timeout=5,preexec_fn=limits)
  checks.append(dict(request_id=row['request_id'],returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
 (out/'independent.json').write_text(json.dumps(checks,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);args=p.parse_args();asyncio.run(main(args.model))
