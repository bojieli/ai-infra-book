import argparse,asyncio,hashlib,json,os,random,time
from dataclasses import asdict
from pathlib import Path
from fixture import INITIAL,SPEC,CHECKER,execute
R=Path(__file__).resolve().parent
async def main(model):
 os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
 import torch,vllm
 from transformers import AutoTokenizer
 from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
 out=R/'results';assert not out.exists();out.mkdir();tok=AutoTokenizer.from_pretrained(model,local_files_only=True)
 config=dict(model=model,dtype='bfloat16',max_model_len=8192,max_num_seqs=1,max_num_batched_tokens=512,enable_chunked_prefill=True,enable_prefix_caching=False,enforce_eager=True,gpu_memory_utilization=.60,limit_mm_per_prompt=dict(image=0,video=0),kv_cache_memory_bytes=6*1024**3,seed=1108,async_scheduling=False)
 (out/'environment.json').write_text(json.dumps(dict(config=config,torch=torch.__version__,vllm=vllm.__version__,source_hashes={f:hashlib.sha256((R/f).read_bytes()).hexdigest() for f in ['run.py','fixture.py']}),indent=2)+'\n')
 order=[];rng=random.Random(1108)
 for trial in range(2):
  cases=[dict(thinking=False,budget=1000)];rng.shuffle(cases)
  order.extend(dict(trial=trial,**c) for c in cases)
 (out/'order.json').write_text(json.dumps(order,indent=2)+'\n')
 engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config))
 try:
  for i,case in enumerate(order):
   work=out/f'case{i}';work.mkdir()
   for name,content in [('intervals.py',INITIAL),('SPEC.txt',SPEC),('test_intervals.py',CHECKER)]: (work/name).write_text(content)
   messages=[dict(role='system',content='Repair the function. Return exactly one JSON object with a single content field containing the complete Python code. No imports. No markdown.'),dict(role='user',content=SPEC+'\nCurrent implementation:\n'+INITIAL)]
   ids=tok.apply_chat_template(messages,tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=case['thinking'])
   start=time.monotonic();events=[];final=None;answer_first=None
   async for output in engine.generate({'prompt_token_ids':ids},SamplingParams(temperature=0,max_tokens=case['budget']),f'budget-{i}'):
    now=time.monotonic();o=output.outputs[0];events.append(dict(time_s=now,token_count=len(o.token_ids)))
    answer=o.text.split('</think>',1)[1] if case['thinking'] and '</think>' in o.text else '' if case['thinking'] else o.text
    if answer.strip() and answer_first is None:answer_first=now
    final=output
   end=time.monotonic();o=final.outputs[0];answer=o.text.split('</think>',1)[1] if case['thinking'] and '</think>' in o.text else '' if case['thinking'] else o.text
   parse_start=time.monotonic()
   try:
    proposal=json.loads(answer.strip());write=execute(dict(tool='write_file',path='intervals.py',content=proposal['content']),work);check=execute(dict(tool='run_tests'),work)
    result=dict(write=write,validation=check,passed=check['returncode']==0 and json.loads(check['stdout'])['passed'])
   except Exception as e:result=dict(passed=False,error=type(e).__name__+': '+str(e))
   done=time.monotonic()
   row=dict(case_index=i,**case,messages=messages,input_ids=ids,output_ids=list(o.token_ids),output_text=o.text,finish_reason=o.finish_reason,cached_tokens=final.num_cached_tokens,engine_metrics=asdict(final.metrics) if final.metrics else None,start_s=start,model_end_s=end,answer_first_s=answer_first,validation_start_s=parse_start,done_s=done,events=events,result=result)
   with (out/'raw.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
   print('completed',case,'tokens',len(o.token_ids),'passed',result['passed'],flush=True)
 finally:engine.shutdown()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);a=p.parse_args();asyncio.run(main(a.model))
