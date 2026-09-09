"""Replay frozen real Agent inputs with measured APC hits and cache pressure."""
import argparse
import asyncio
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import random
import time


async def main(args):
    os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
    import torch,vllm
    from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
    if args.output.exists():raise RuntimeError('Use a fresh result directory')
    args.output.mkdir(parents=True)
    inp=Path(__file__).parent/'inputs/agent-prompts.json'
    requests=json.loads(inp.read_text())['requests']
    config=dict(model=args.model,dtype='bfloat16',max_model_len=4096,max_num_seqs=1,
        max_num_batched_tokens=512,enable_prefix_caching=not args.no_cache,
        enable_chunked_prefill=True,enforce_eager=True,async_scheduling=False,
        gpu_memory_utilization=.30,kv_cache_memory_bytes=args.kv_gib*1024**3,seed=804)
    (args.output/'environment.json').write_text(json.dumps(dict(config=config,torch=torch.__version__,vllm=vllm.__version__,
        gap_s=args.gap,pressure_requests=args.pressure,input_sha256=hashlib.sha256(inp.read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        boundary='Frozen actual Agent prompts; one generated token per request, no tool rerun. Pressure is synthetic.'),indent=2)+'\n')
    engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config))
    rng=random.Random(804)
    with (args.output/'requests.jsonl').open('w',buffering=1) as log:
        async def one(ids,rid,kind):
            start=time.monotonic();first=None;final=None
            async for out in engine.generate({'prompt_token_ids':ids},SamplingParams(temperature=0,max_tokens=1,ignore_eos=True),rid):
                if first is None:first=time.monotonic()
                final=out
            end=time.monotonic()
            log.write(json.dumps(dict(id=rid,kind=kind,prompt_tokens=len(ids),
                prompt_sha256=hashlib.sha256(json.dumps(ids).encode()).hexdigest(),
                start_s=start,end_s=end,delivery_ttft_s=first-start,cached_tokens=final.num_cached_tokens,
                output_ids=list(final.outputs[0].token_ids),metrics=asdict(final.metrics) if final.metrics else None))+'\n')
        try:
            for i,r in enumerate(requests):
                if i:
                    await asyncio.sleep(args.gap)
                    for j in range(args.pressure):
                        ids=[rng.randrange(100,50000) for _ in range(4000)]
                        await one(ids,f'pressure-{i}-{j}','pressure')
                await one(r['prompt_token_ids'],f'agent-{r["id"]}','agent')
        finally:engine.shutdown()
    print(json.dumps(dict(output=str(args.output),agent_requests=len(requests))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--kv-gib',type=int,default=6);p.add_argument('--gap',type=float,default=0)
    p.add_argument('--pressure',type=int,default=0);p.add_argument('--no-cache',action='store_true')
    asyncio.run(main(p.parse_args()))
