"""Actual AsyncLLM arrival replay; no simulated execution times.

Run each configuration in a fresh process. Generated fixtures represent Chat
and code-review request shapes, not production traffic or an autonomous agent.
"""
import argparse
import asyncio
from dataclasses import asdict, is_dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time


def gpu():
    return subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.used,memory.free,utilization.gpu', '--format=csv'], text=True)


async def replay(args):
    # Greedy experiment uses native sampling, avoiding optional FlashInfer JIT.
    os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
    import torch
    import vllm
    from transformers import AutoTokenizer
    from vllm import AsyncEngineArgs, AsyncLLMEngine, SamplingParams
    from vllm.v1.metrics.loggers import StatLoggerBase
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True)
    requests = []
    specs = [(0,128,96,'chat'),(.08,2048,128,'agent'),(.16,256,96,'chat'),
             (.24,4096,128,'agent'),(.32,512,96,'chat'),(.40,1024,128,'agent')]
    for i,(arrival,length,tokens,kind) in enumerate(specs):
        content = ('Explain why bounded queues need backpressure. ' if kind == 'chat' else
                   'Review this Python queue worker for correctness: def worker(q):\n    while True:\n        item=q.get()\n        process(item)\n        q.task_done()\n')
        # Fixed token inputs avoid per-run chat-template and tokenization variation.
        ids = tokenizer.encode(content * (length + 1), add_special_tokens=False)[:length]
        requests.append(dict(id=f'r{i}',arrival_s=arrival,kind=kind,
                             prompt_token_ids=ids,decoded_prompt=tokenizer.decode(ids),max_tokens=tokens))
    (out/'requests.json').write_text(json.dumps(requests, indent=2)+'\n')
    config = dict(model=args.model,dtype='bfloat16',max_model_len=8192,
                  max_num_seqs=6,max_num_batched_tokens=args.budget,
                  enable_chunked_prefill=not args.no_chunk,
                  enable_prefix_caching=False,enforce_eager=not args.graph,
                  gpu_memory_utilization=.30,kv_cache_memory_bytes=6*1024**3,
                  seed=802,async_scheduling=False,disable_log_stats=False,
                  max_cudagraph_capture_size=8,stream_interval=1)
    # Hold torch.compile disabled in both paths; only decode graph changes.
    config['compilation_config']={'mode':0,'cudagraph_mode':'FULL_DECODE_ONLY' if args.graph else 'NONE'}
    metadata = dict(config=config,torch=torch.__version__,vllm=vllm.__version__,
                    VLLM_USE_FLASHINFER_SAMPLER='0',
                    python=platform.python_version(),gpu_before=gpu(),
                    run_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    requests_sha256=hashlib.sha256((out/'requests.json').read_bytes()).hexdigest(),
                    timing_scope='AsyncLLM output delivery, excludes HTTP; events may contain multiple tokens',
                    fixture_origin='synthetic fixed Chat/code-review text; not production or autonomous agent trace')
    (out/'environment.json').write_text(json.dumps(metadata,indent=2)+'\n')
    started=time.perf_counter()
    stats_file=(out/'engine-stats.jsonl').open('w',buffering=1)
    def serialize(value):
        if is_dataclass(value):
            return asdict(value)
        if hasattr(value,'__dict__'):
            return vars(value)
        return str(value)
    class RawStats(StatLoggerBase):
        def __init__(self,vllm_config,engine_index=0):
            pass
        def log_engine_initialized(self):
            pass
        def record(self,scheduler_stats,iteration_stats,mm_cache_stats=None,engine_idx=0):
            stats_file.write(json.dumps(dict(observed_monotonic_s=time.monotonic(),
                scheduler=scheduler_stats,iteration=iteration_stats),default=serialize)+'\n')
    engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config),
        stat_loggers=[lambda cfg,idx:RawStats(cfg,idx)])
    metadata['engine_init_s']=time.perf_counter()-started
    try:
        for w in range(2):
            async for _ in engine.generate({'prompt_token_ids':requests[0]['prompt_token_ids']},
                    SamplingParams(temperature=0,max_tokens=16,ignore_eos=True),f'warm{w}'):
                pass
        metadata['gpu_after_warmup']=gpu()
        with (out/'events.jsonl').open('w',buffering=1) as f:
            for trial in range(args.trials):
                epoch=time.perf_counter()+.1
                async def one(r):
                    await asyncio.sleep(max(0,epoch+r['arrival_s']-time.perf_counter()))
                    submitted=time.perf_counter()-epoch
                    previous=0
                    async for result in engine.generate({'prompt_token_ids':r['prompt_token_ids']},
                            SamplingParams(temperature=0,max_tokens=r['max_tokens'],ignore_eos=True),
                            f't{trial}-{r["id"]}'):
                        now=time.perf_counter()-epoch
                        seq=result.outputs[0]
                        ids=list(seq.token_ids)
                        assert len(ids)>=previous
                        record=dict(trial=trial,id=r['id'],scheduled_s=r['arrival_s'],
                                    submitted_s=submitted,delivered_s=now,new_token_ids=ids[previous:],
                                    cumulative_tokens=len(ids),finished=result.finished,
                                    finish_reason=seq.finish_reason,
                                    engine_request_metrics=asdict(result.metrics) if result.metrics is not None else None)
                        f.write(json.dumps(record)+'\n')
                        previous=len(ids)
                    assert previous==r['max_tokens'],(r['id'],previous)
                await asyncio.gather(*(one(r) for r in requests))
        metadata['gpu_after_replay']=gpu()
        metadata['completed_trials']=args.trials
    finally:
        engine.shutdown()
        stats_file.close()
        (out/'environment.json').write_text(json.dumps(metadata,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--model',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--budget',type=int,default=512)
    p.add_argument('--no-chunk',action='store_true')
    p.add_argument('--graph',action='store_true')
    p.add_argument('--trials',type=int,default=3)
    asyncio.run(replay(p.parse_args()))
