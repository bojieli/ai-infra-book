import argparse,asyncio,hashlib,json,os,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
async def main(a):
    if a.output.exists():raise RuntimeError('Fresh output required')
    a.output.mkdir(parents=True)
    os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
    from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
    config=json.loads((ROOT/'engine-config.json').read_text());config['worker_extension_cls']='trace_worker.TraceWorker'
    task=json.loads((ROOT/'input.json').read_text())
    result=dict(mode=a.mode,config=config,source_hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['profile_run.py','trace_worker.py','replacement_worker.py','candidate.py','input.json','engine-config.json']})
    engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config))
    async def request(rid):
        start=time.perf_counter();events=[];final=None
        async for output in engine.generate({'prompt_token_ids':task['prompt_token_ids']},SamplingParams(temperature=0,max_tokens=32,ignore_eos=True),rid):
            final=output;events.append(dict(elapsed_s=time.perf_counter()-start,tokens=len(output.outputs[0].token_ids)))
        return dict(output_ids=list(final.outputs[0].token_ids),events=events,elapsed_s=time.perf_counter()-start)
    try:
        result['installed']=await engine.collective_rpc('install_replacement')
        result['switch']=await engine.collective_rpc('set_replacement',args=(a.mode,False))
        for i in range(2):await request(f'warm-{i}')
        await engine.collective_rpc('begin_trace',args=(f'replacement-{a.mode}-7239-32',))
        try:result['request']=await request('trace')
        finally:result['steps']=await engine.collective_rpc('end_trace')
    finally:
        engine.shutdown();(a.output/'run.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['native','schedule'],required=True);p.add_argument('--output',type=Path,required=True);asyncio.run(main(p.parse_args()))
