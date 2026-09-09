"""Separate instrumented step audit; not mixed with client timing benchmark."""
import argparse,asyncio,hashlib,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
async def main(a):
    if a.output.exists():raise RuntimeError('Fresh output required')
    a.output.mkdir(parents=True);os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
    from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
    config=json.loads((ROOT/'followup-config.json').read_text());config['worker_extension_cls']='step_worker.StepWorker'
    inputs=json.loads((ROOT/'followup-inputs.json').read_text());records=[]
    engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config))
    async def request(kind,b,i,phase,max_tokens):
        final=None
        async for out in engine.generate({'prompt_token_ids':inputs[kind][i]},SamplingParams(temperature=0,max_tokens=max_tokens,ignore_eos=True),f'{phase}-{kind}-{b}-{i}'):final=out
        return dict(index=i,output_ids=list(final.outputs[0].token_ids),cached_tokens=final.num_cached_tokens)
    try:
        for kind in ['short','long']:
            for b in [1,16]:
                await asyncio.gather(*(request(kind,b,i,'warm',2) for i in range(b)))
                await engine.collective_rpc('arm_steps')
                outputs=await asyncio.gather(*(request(kind,b,i,'audit',256) for i in range(b)))
                steps=await engine.collective_rpc('finish_steps')
                records.append(dict(kind=kind,batch=b,outputs=outputs,steps=steps))
                print(kind,b,len(steps[0]),flush=True)
    finally:
        engine.shutdown();(a.output/'raw.json').write_text(json.dumps(dict(records=records,config=config,
            source_hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['run_steps.py','step_worker.py','followup-config.json','followup-inputs.json']},
            scope='CUDA events bracket model_runner.execute_model, excluding sampling/logits outside method; host launch gaps can be inside event interval. Metadata from scheduler; separate from uninstrumented formal sweep.'),indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);asyncio.run(main(p.parse_args()))
