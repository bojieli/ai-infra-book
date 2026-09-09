"""Fixed-work batch sweep; synthetic token lengths, real engine execution."""
import argparse,asyncio,hashlib,json,os,random,subprocess,time
from dataclasses import asdict,is_dataclass
from pathlib import Path

async def main(args):
    os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
    import torch,vllm
    from transformers import AutoTokenizer
    from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
    from vllm.v1.metrics.loggers import StatLoggerBase
    if args.output.exists():raise RuntimeError('Choose a fresh output directory')
    args.output.mkdir(parents=True)
    tok=AutoTokenizer.from_pretrained(args.model,local_files_only=True)
    base=tok.encode('Review the queue worker and explain correctness, ordering, and bounded memory. '*3000,add_special_tokens=False)
    shared=base[:6144]
    inputs={kind:[([1000+i]+base[:2047] if kind=='short' else shared+[2000+i]+base[:2047]) for i in range(64)] for kind in ['short','prefix']}
    (args.output/'inputs.json').write_text(json.dumps(dict(requests=inputs,shared_prefix=shared))+'\n')
    config=dict(model=args.model,dtype='bfloat16',max_model_len=8448,max_num_seqs=64,
        max_num_batched_tokens=4096,enable_chunked_prefill=True,enable_prefix_caching=True,
        enforce_eager=True,async_scheduling=False,gpu_memory_utilization=.60,
        kv_cache_memory_bytes=24*1024**3,seed=801,disable_log_stats=False,stream_interval=1)
    env=dict(config=config,torch=torch.__version__,vllm=vllm.__version__,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        input_sha256=hashlib.sha256((args.output/'inputs.json').read_bytes()).hexdigest(),
        gpu_before=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.used,memory.free','--format=csv'],text=True),
        scope='Synthetic fixed input/output lengths; 256 forced output tokens; APC on, unique first token for short, exactly 6144 common tokens for prefix; no task quality claim.')
    (args.output/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
    stats=(args.output/'engine-stats.jsonl').open('w',buffering=1)
    state={'run_id':'init'}
    def serialize(x):return asdict(x) if is_dataclass(x) else vars(x) if hasattr(x,'__dict__') else str(x)
    class RawStats(StatLoggerBase):
        def __init__(self,*a,**kw):pass
        def log_engine_initialized(self):pass
        def record(self,scheduler_stats,iteration_stats,mm_cache_stats=None,engine_idx=0):
            stats.write(json.dumps(dict(run_id=state['run_id'],observed_s=time.monotonic(),scheduler=scheduler_stats,iteration=iteration_stats),default=serialize)+'\n')
    engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config),stat_loggers=[lambda cfg,idx:RawStats(cfg,idx)])
    logs=(args.output/'requests.jsonl').open('w',buffering=1)
    batches=(args.output/'batches.jsonl').open('w',buffering=1)
    async def one(ids,rid,n=256):
        start=time.monotonic();events=[];final=None
        async for o in engine.generate({'prompt_token_ids':ids},SamplingParams(temperature=0,max_tokens=n,ignore_eos=True),rid):
            events.append([time.monotonic(),len(o.outputs[0].token_ids)])
            final=o
        end=time.monotonic()
        assert len(final.outputs[0].token_ids)==n
        r=dict(run_id=state['run_id'],id=rid,start_s=start,end_s=end,events=events,
            input_tokens=len(ids),input_sha256=hashlib.sha256(json.dumps(ids).encode()).hexdigest(),
            cached_tokens=final.num_cached_tokens,output_ids=list(final.outputs[0].token_ids),
            metrics=asdict(final.metrics),finish_reason=final.outputs[0].finish_reason)
        logs.write(json.dumps(r)+'\n');return r
    async def batch(kind,b,trial):
        state['run_id']=f'{trial}-{kind}-b{b}-reset'
        assert await engine.reset_prefix_cache()
        if kind=='prefix':
            state['run_id']=f'{trial}-{kind}-b{b}-seed'
            await one(shared,state['run_id'],1)
        state['run_id']=f'{trial}-{kind}-b{b}'
        start=time.monotonic()
        await asyncio.gather(*(one(inputs[kind][i],f'{state["run_id"]}-r{i}') for i in range(b)))
        end=time.monotonic()
        batches.write(json.dumps(dict(run_id=state['run_id'],kind=kind,batch=b,trial=trial,start_s=start,end_s=end))+'\n')
        print(state['run_id'],'done',flush=True)
    pairs=[(k,b) for k in inputs for b in [1,4,16,64]]
    rng=random.Random(801)
    try:
        for kind,b in pairs:await batch(kind,b,'warm')
        for trial in range(3):
            order=pairs.copy();rng.shuffle(order)
            for kind,b in order:await batch(kind,b,trial)
    finally:
        engine.shutdown();stats.close();logs.close();batches.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--output',type=Path,required=True)
    asyncio.run(main(p.parse_args()))
