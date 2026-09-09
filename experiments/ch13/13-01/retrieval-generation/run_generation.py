"""Real sequential retrieval -> native Qwen generation, with observed KV blocks."""
import argparse
import asyncio
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import time

BASE = Path(__file__).resolve().parent

async def main(a):
    a.output.mkdir(parents=True, exist_ok=False)
    os.environ['VLLM_USE_FLASHINFER_SAMPLER'] = '0'
    os.environ['KV_OBSERVER_LOG'] = str((a.output / 'blocks.jsonl').resolve())
    import torch
    import vllm
    from vllm import AsyncEngineArgs, AsyncLLMEngine, SamplingParams
    prepared = json.loads(a.prepared.read_text())
    assert len(prepared['requests']) == 288
    assert a.model.name == prepared['generation_model_revision']
    config = dict(model=str(a.model), dtype='bfloat16', kv_cache_dtype='auto',
                  max_model_len=4096, max_num_seqs=1, max_num_batched_tokens=256,
                  enable_chunked_prefill=True, enable_prefix_caching=False,
                  enforce_eager=True, async_scheduling=False, gpu_memory_utilization=.40,
                  kv_cache_memory_bytes=2*1024**3, seed=130113,
                  attention_backend='TRITON_ATTN',
                  scheduler_cls='route_kv_observer.ObservedScheduler',
                  worker_extension_cls='generation_probe.KVProbe')
    for r in prepared['requests']:
        assert len(r['prompt_token_ids']) == r['input_tokens'] < 4064
        assert hashlib.sha256(json.dumps(r['prompt_token_ids'],separators=(',',':')).encode()).hexdigest() == r['prompt_sha256']
    environment = dict(config=config, torch=torch.__version__, vllm=vllm.__version__,
                       prepared_sha256=hashlib.sha256(a.prepared.read_bytes()).hexdigest(),
                       sampling=prepared['sampling'],
                       hashes={n:hashlib.sha256((BASE/n).read_bytes()).hexdigest() for n in
                               ['run_generation.py','route_kv_observer.py','generation_probe.py','run_guard.py']},
                       scope='Real serial CPU retrieval and CUDA generation; synchronous scheduler observation perturbs time. No pure-prefill claim.')
    (a.output/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
    cpu_spec=json.loads(a.retriever_command.read_text())
    cpu_env=dict(os.environ);cpu_env.update(cpu_spec.get('env',{}));cpu_env['CUDA_VISIBLE_DEVICES']=''
    cpu_log=(a.output/'retriever.log').open('wb')
    cpu_start=time.monotonic()
    cpu=await asyncio.create_subprocess_exec(*cpu_spec['argv'],stdin=asyncio.subprocess.PIPE,
          stdout=asyncio.subprocess.PIPE,stderr=cpu_log,env=cpu_env,cwd=str(BASE),limit=1024*1024)
    ready=json.loads(await asyncio.wait_for(cpu.stdout.readline(),300))
    (a.output/'retriever-ready.json').write_text(json.dumps(dict(start_s=cpu_start,end_s=time.monotonic(),record=ready),indent=2)+'\n')
    start=time.monotonic();engine=None;records=[];snapshots={}
    log=(a.output/'requests.jsonl').open('w',buffering=1)
    try:
        engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config))
        (a.output/'ready.json').write_text(json.dumps(dict(initialization_s=time.monotonic()-start))+'\n')
        snapshots['before']=await engine.collective_rpc('kv_snapshot')
        for i,r in enumerate(prepared['requests']):
            begin=time.monotonic()
            cpu.stdin.write((json.dumps({'id':r['id']})+'\n').encode());await cpu.stdin.drain()
            retrieval=json.loads(await asyncio.wait_for(cpu.stdout.readline(),120))
            assert retrieval['id']==r['id']
            assert retrieval['prompt_token_ids']==r['prompt_token_ids'], 'live retrieval must match frozen input exactly'
            generation_start=time.monotonic();events=[];final=None
            async for out in engine.generate({'prompt_token_ids':retrieval['prompt_token_ids']},
                    SamplingParams(**prepared['sampling']),r['id']):
                events.append([time.monotonic(),len(out.outputs[0].token_ids)]);final=out
            end=time.monotonic();assert final is not None
            seq=final.outputs[0]
            record=dict(id=r['id'],config_id=r['config_id'],query_id=r['query_id'],split=r['split'],
                        start_s=begin,generation_start_s=generation_start,end_s=end,
                        retrieval=retrieval,events=events,output_ids=list(seq.token_ids),text=seq.text,
                        finish_reason=seq.finish_reason,stop_reason=seq.stop_reason,metrics=asdict(final.metrics))
            log.write(json.dumps(record)+'\n');records.append(record)
            print(f'{i+1}/288 {r["id"]} {seq.finish_reason}',flush=True)
        snapshots['after']=await engine.collective_rpc('kv_snapshot')
        (a.output/'records.json').write_text(json.dumps(records,indent=2)+'\n')
        (a.output/'completion.json').write_text(json.dumps(dict(status='all_requests_returned',count=len(records)))+'\n')
    finally:
        (a.output/'kv-snapshots.json').write_text(json.dumps(snapshots,indent=2)+'\n')
        if engine is not None:engine.shutdown()
        cpu.stdin.close()
        try:await asyncio.wait_for(cpu.wait(),30)
        except asyncio.TimeoutError:
            cpu.terminate();await cpu.wait()
        (a.output/'retriever-exit.json').write_text(json.dumps({'exit_code':cpu.returncode})+'\n')
        cpu_log.close();log.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True)
    p.add_argument('--prepared',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--retriever-command',type=Path,required=True)
    asyncio.run(main(p.parse_args()))
