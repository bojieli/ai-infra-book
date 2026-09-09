"""Four frozen long retrieval requests with native routed-expert return."""
import argparse, asyncio, hashlib, json, os, time
from pathlib import Path
B=Path(__file__).absolute().parent
async def main(a):
    os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    import torch,vllm,numpy as np
    from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
    from transformers import AutoTokenizer
    out=a.out.absolute();out.mkdir(parents=True,exist_ok=False)
    tasks=json.loads((B/'tasks.json').read_text())
    if isinstance(tasks,dict):tasks=tasks['tasks']
    tok=AutoTokenizer.from_pretrained(a.model,local_files_only=True)
    cases=[]
    for t in tasks:
        ids=tok.apply_chat_template(t['messages'],tokenize=True,add_generation_prompt=True,return_dict=False)
        cases.append(dict(id=t['id'],messages=t['messages'],expected=t['expected'],input_ids=ids))
    (out/'cases.json').write_text(json.dumps(cases,ensure_ascii=False)+'\n')
    cfg=dict(model=a.model,dtype='auto',kv_cache_dtype='auto',attention_backend='TRITON_ATTN',
             max_model_len=16384,max_num_seqs=1,max_num_batched_tokens=2048,
             enable_chunked_prefill=True,enable_prefix_caching=False,enforce_eager=True,
             async_scheduling=False,kv_cache_memory_bytes=4*1024**3,gpu_memory_utilization=.65,
             limit_mm_per_prompt={'image':0,'video':0},enable_return_routed_experts=not a.disable_route_capture,seed=906)
    (out/'environment.json').write_text(json.dumps(dict(config=cfg,torch=torch.__version__,vllm=vllm.__version__,
        driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='native capture; no EP/EPLB/DBO; text-only VL model variant'),indent=2)+'\n')
    engine=None;start=time.monotonic()
    try:
        engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**cfg))
        (out/'ready.json').write_text(json.dumps(dict(initialization_s=time.monotonic()-start))+'\n')
        with (out/'requests.jsonl').open('w',buffering=1) as f:
            for c in cases:
                sent=time.monotonic();events=[];final=None
                async for r in engine.generate({'prompt_token_ids':c['input_ids']},SamplingParams(temperature=0,max_tokens=128),c['id']):
                    final=r;events.append([time.monotonic(),len(r.outputs[0].token_ids)])
                seq=final.outputs[0];routes=seq.routed_experts
                route_file=c['id']+'-routes.npy'
                if routes is not None:np.save(out/route_file,routes,allow_pickle=False)
                row=dict(id=c['id'],prompt_ids=final.prompt_token_ids,output_ids=list(seq.token_ids),text=seq.text,
                         finish_reason=seq.finish_reason,stop_reason=seq.stop_reason,events=events,wall_s=time.monotonic()-sent,
                         route_file=route_file if routes is not None else None,route_shape=list(routes.shape) if routes is not None else None,
                         route_dtype=str(routes.dtype) if routes is not None else None)
                f.write(json.dumps(row)+'\n');print(c['id'],row['finish_reason'],row['route_shape'],flush=True)
                assert final.prompt_token_ids==c['input_ids']
                assert tok.decode(seq.token_ids,skip_special_tokens=True)==seq.text
        (out/'completion.json').write_text(json.dumps(dict(requests=len(cases),status='returned_not_quality_claim'))+'\n')
    finally:
        if engine is not None:engine.shutdown()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--disable-route-capture',action='store_true')
    asyncio.run(main(p.parse_args()))
