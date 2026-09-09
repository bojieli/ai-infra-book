import argparse,json,time,hashlib,os,platform
from pathlib import Path
os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
ROOT=Path(__file__).absolute().parent
def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    import torch,vllm,transformers
    from vllm import LLM,SamplingParams
    from transformers import AutoTokenizer
    cases=json.loads((ROOT/'cases.json').read_text())['cases'];t=AutoTokenizer.from_pretrained(args.model,local_files_only=True)
    prepared=[]
    for c in cases:
     ids=t.apply_chat_template(c['messages'],tokenize=True,add_generation_prompt=True,enable_thinking=False,return_dict=False)
     prepared.append(dict(case_id=c['id'],messages=c['messages'],input_ids=ids,expected=c['answer'],messages_sha256=hashlib.sha256(json.dumps(c['messages'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()))
    (args.out/'prepared.json').write_text(json.dumps(prepared,ensure_ascii=False,indent=2)+'\n')
    config=dict(model=args.model,dtype='bfloat16',kv_cache_dtype='auto',max_model_len=4096,max_num_seqs=1,max_num_batched_tokens=256,enable_chunked_prefill=True,enable_prefix_caching=False,enforce_eager=True,async_scheduling=False,kv_cache_memory_bytes=2*1024**3,gpu_memory_utilization=.3,attention_backend='TRITON_ATTN',seed=209)
    (args.out/'environment.json').write_text(json.dumps(dict(config=config,torch=torch.__version__,vllm=vllm.__version__,transformers=transformers.__version__,python=platform.python_version(),gpu=torch.cuda.get_device_name(),driver_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
    start=time.monotonic();llm=LLM(**config);init=time.monotonic()-start
    # No same-task warmup: this is a quality comparison, not warm-state performance.
    sampling=SamplingParams(temperature=0,top_p=1,top_k=1,max_tokens=32);rows=[]
    for c in prepared:
     start=time.monotonic();o=llm.generate([{'prompt_token_ids':c['input_ids']}],sampling,use_tqdm=False)[0];end=time.monotonic();s=o.outputs[0]
     assert o.prompt_token_ids==c['input_ids']
     assert t.decode(s.token_ids,skip_special_tokens=True)==s.text
     assert s.finish_reason!='stop' or s.token_ids[-1]==t.eos_token_id
     r=dict(case_id=c['case_id'],input_ids=o.prompt_token_ids,output_ids=list(s.token_ids),text=s.text,finish_reason=s.finish_reason,stop_reason=s.stop_reason,request_wall_s=end-start,messages_sha256=c['messages_sha256'],sampling=dict(temperature=0,top_p=1,top_k=1,max_tokens=32))
     rows.append(r);(args.out/'requests.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print(c['case_id'],len(c['input_ids']),repr(s.text),s.finish_reason,flush=True)
    (args.out/'completion.json').write_text(json.dumps(dict(requests=len(rows),init_s=init,decode_and_prompt_exact=len(rows)),indent=2)+'\n')

if __name__=='__main__':main()
