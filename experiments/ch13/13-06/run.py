import argparse,asyncio,hashlib,json,os,time,importlib.metadata
from pathlib import Path
ROOT=Path(__file__).resolve().parent
async def main(a):
    if a.output.exists():raise RuntimeError('Fresh output required')
    a.output.mkdir(parents=True);os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
    from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
    config=json.loads((ROOT/'engine-config.json').read_text());config['worker_extension_cls']='step_worker.StepWorker';config['max_num_batched_tokens']=a.budget
    ids=json.loads((ROOT/'inputs.json').read_text());records=[];status='running'
    engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config))
    async def request(rid):
        start=time.monotonic();final=None
        async for out in engine.generate({'prompt_token_ids':ids},SamplingParams(temperature=0,max_tokens=1,ignore_eos=True),rid):final=out
        return dict(output_ids=list(final.outputs[0].token_ids),cached_tokens=final.num_cached_tokens,client_elapsed_s=time.monotonic()-start)
    try:
        warm=await request('warm')
        for trial in range(5):
            await engine.collective_rpc('arm_steps');output=await request(f'trial-{trial}');steps=await engine.collective_rpc('finish_steps')
            records.append(dict(trial=trial,output=output,steps=steps));print(trial,len(steps[0]),flush=True)
        status='passed'
    finally:
        engine.shutdown();(a.output/'raw.json').write_text(json.dumps(dict(status=status,records=records,config=config,versions={p:importlib.metadata.version(p) for p in ['vllm','torch','triton']},source_hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['run.py','step_worker.py','inputs.json','engine-config.json','PROTOCOL.md','prediction.json','prediction.sha256']}),indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--budget',type=int,choices=[256,512],required=True);asyncio.run(main(p.parse_args()))
