"""Independent engine process controlled through a multiprocessing pipe."""
import asyncio
from dataclasses import asdict
import json
import os
from pathlib import Path
import time
import traceback


def run(connection, output, model, server_port):
    root = Path(output); root.mkdir(parents=True, exist_ok=False)
    # Libraries print during import; protocol uses a pipe, never stdout.
    with (root/'engine.log').open('w', buffering=1) as log:
        os.dup2(log.fileno(), 1); os.dup2(log.fileno(), 2)
        try:
            asyncio.run(serve(connection, root, model, server_port))
        except BaseException:
            traceback.print_exc()
            try: connection.send({'error': traceback.format_exc()})
            except (BrokenPipeError, EOFError): pass
            raise
        finally:
            connection.close()


async def serve(connection, root, model, server_port):
    os.environ.update(VLLM_USE_FLASHINFER_SAMPLER='0',
                      KV_OBSERVER_LOG=str(root/'blocks.jsonl'),
                      SHARED_KV_TRACE=str(root))
    import torch, vllm
    from vllm import AsyncEngineArgs, AsyncLLMEngine, SamplingParams
    config = dict(model=model, dtype='bfloat16', kv_cache_dtype='auto',
                  max_model_len=12288, max_num_seqs=1, max_num_batched_tokens=256,
                  enable_chunked_prefill=True, enable_prefix_caching=server_port is not None,
                  enforce_eager=True, async_scheduling=False, gpu_memory_utilization=.25,
                  kv_cache_memory_bytes=2*1024**3, seed=907,
                  attention_backend='TRITON_ATTN',
                  scheduler_cls='scheduler_observer.ObservedScheduler',
                  worker_extension_cls='generation_probe.KVProbe')
    if server_port is not None:
        from vllm.config import KVTransferConfig
        config['kv_transfer_config'] = KVTransferConfig(
            kv_connector='ObservedMPConnector', kv_connector_module_path='shared_connector',
            kv_role='kv_both', kv_connector_extra_config={
                'lmcache.mp.host':'tcp://127.0.0.1', 'lmcache.mp.port':server_port,
                'lmcache.mp.mq_timeout':30.0})
    (root/'environment.json').write_text(json.dumps(dict(
        config=config, torch=torch.__version__, vllm=vllm.__version__, pid=os.getpid()),
        default=asdict, indent=2)+'\n')
    engine = None
    try:
        start = time.monotonic()
        engine = AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config))
        snapshot = await engine.collective_rpc('kv_snapshot')
        (root/'initial-kv.json').write_text(json.dumps(snapshot, indent=2)+'\n')
        connection.send({'ready':True, 'pid':os.getpid(), 'init_s':time.monotonic()-start})
        while True:
            command = await asyncio.to_thread(connection.recv)
            if command['op'] == 'shutdown': break
            assert command['op'] == 'generate'
            req = command['request']; begin = time.monotonic(); events=[]; final=None
            async for item in engine.generate({'prompt_token_ids':req['prompt_token_ids']},
                    SamplingParams(temperature=0, max_tokens=16), req['id']):
                events.append([time.monotonic(),len(item.outputs[0].token_ids)]); final=item
            assert final is not None
            seq=final.outputs[0]
            result=dict(id=req['id'], start_s=begin, end_s=time.monotonic(),events=events,
                        output_ids=list(seq.token_ids),text=seq.text,
                        finish_reason=seq.finish_reason,stop_reason=seq.stop_reason,
                        metrics=asdict(final.metrics))
            with (root/'requests.jsonl').open('a') as f:f.write(json.dumps(result)+'\n')
            connection.send(result)
        (root/'final-kv.json').write_text(json.dumps(await engine.collective_rpc('kv_snapshot'),indent=2)+'\n')
    finally:
        if engine is not None: engine.shutdown()
