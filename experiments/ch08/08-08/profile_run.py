import argparse,asyncio,hashlib,json,os,time
from pathlib import Path

async def main(args):
    os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
    root=Path(__file__).parent
    if args.output.exists():raise RuntimeError('Choose a fresh profile output directory')
    args.output.mkdir(parents=True)
    base=root/'results'/args.format
    inp=json.loads((base/'inputs.json').read_text())
    config=json.loads((base/'environment.json').read_text())['config']
    config['worker_extension_cls']='trace_probe.TraceProbe'
    from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
    engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config))
    result=dict(config=config,input_sha256=hashlib.sha256((base/'inputs.json').read_bytes()).hexdigest(),
        sources={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ['profile_run.py','trace_probe.py','probe.py']})
    async def request(task,rid):
        start=time.monotonic();final=None
        async for out in engine.generate({'prompt_token_ids':task['prompt_token_ids']},SamplingParams(temperature=0,max_tokens=2,ignore_eos=True),rid):final=out
        assert len(final.outputs[0].token_ids)==2
        return dict(prompt_tokens=len(task['prompt_token_ids']),output_ids=list(final.outputs[0].token_ids),elapsed_s=time.monotonic()-start)
    try:
        if args.format=='fp8':await engine.collective_rpc('arm_kv_calibration')
        await request(inp['calibration'],'calibration')
        result['kv_before']=await engine.collective_rpc('kv_snapshot')
        target=next(t for t in inp['tasks'] if t['id']=='n512-r0')
        for w in range(2):await request(target,f'warm{w}')
        await engine.collective_rpc('begin_trace',args=(f'kv-{args.format}-7239-prefill-and-one-decode',))
        try:result['request']=await request(target,'profile')
        finally:await engine.collective_rpc('end_trace')
        result['kv_after']=await engine.collective_rpc('kv_snapshot')
    finally:
        engine.shutdown()
        (args.output/'run.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--format',choices=['bf16','fp8'],required=True);p.add_argument('--output',type=Path,required=True)
    asyncio.run(main(p.parse_args()))
