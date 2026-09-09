import argparse,asyncio,hashlib,json,os,time
from dataclasses import asdict
from pathlib import Path

async def main(args):
    os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
    if args.output.exists():raise RuntimeError('Use a fresh output directory')
    args.output.mkdir(parents=True)
    os.environ['KV_OBSERVER_LOG']=str((args.output/'blocks.jsonl').resolve())
    import torch,vllm
    from transformers import AutoTokenizer
    from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
    tok=AutoTokenizer.from_pretrained(args.model,local_files_only=True)
    base=tok.encode('Explain the queue worker, its bounded memory, and completion ordering. '*1000,add_special_tokens=False)
    inputs=[[1000+i]+base[:1535] for i in range(4)]
    (args.output/'inputs.json').write_text(json.dumps(inputs)+'\n')
    config=dict(model=args.model,dtype='bfloat16',max_model_len=2048,max_num_seqs=4,
        max_num_batched_tokens=512,enable_chunked_prefill=True,enable_prefix_caching=False,
        enforce_eager=True,async_scheduling=False,gpu_memory_utilization=.30,
        kv_cache_memory_bytes=args.kv_gib*1024**3,seed=803,scheduler_cls='observer.ObservedScheduler')
    env=dict(config=config,cancel=args.cancel,torch=torch.__version__,vllm=vllm.__version__,
        hashes={n:hashlib.sha256((Path(__file__).parent/n).read_bytes()).hexdigest() for n in ['run.py','observer.py']},
        input_sha256=hashlib.sha256((args.output/'inputs.json').read_bytes()).hexdigest(),
        scope='Synthetic four 1536-token inputs, forced 512 outputs. Instrumented scheduler timings include synchronous trace cost. Native scheduling/state changes retained.')
    (args.output/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
    engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config))
    f=(args.output/'requests.jsonl').open('w',buffering=1)
    actions=(args.output/'actions.jsonl').open('w',buffering=1)
    async def one(i):
        start=time.monotonic();events=[];cancelled=False;final=None
        async for result in engine.generate({'prompt_token_ids':inputs[i]},SamplingParams(temperature=0,max_tokens=512,ignore_eos=True),f'r{i}'):
            events.append([time.monotonic(),len(result.outputs[0].token_ids)])
            final=result
            if args.cancel and i==3 and not cancelled and len(result.outputs[0].token_ids)>=128:
                t=time.monotonic()
                await engine.abort('r3')
                actions.write(json.dumps(dict(action='abort',id='r3',start_s=t,returned_s=time.monotonic(),observed_tokens=len(result.outputs[0].token_ids)))+'\n')
                cancelled=True
        f.write(json.dumps(dict(id=f'r{i}',start_s=start,end_s=time.monotonic(),events=events,
            cancelled=cancelled,output_ids=list(final.outputs[0].token_ids),
            finish_reason=final.outputs[0].finish_reason,metrics=asdict(final.metrics)))+'\n')
    try:
        await asyncio.gather(*(one(i) for i in range(4)))
    finally:engine.shutdown();f.close();actions.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--kv-gib',type=int,default=1);p.add_argument('--cancel',action='store_true')
    asyncio.run(main(p.parse_args()))
