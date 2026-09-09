import argparse,asyncio,hashlib,json,os,time,importlib.metadata
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parent
async def main(a):
    if a.output.exists():raise RuntimeError('Fresh output required')
    a.output.mkdir(parents=True);os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
    from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
    config=json.loads((ROOT/'engine-config.json').read_text());base=json.loads((ROOT/'inputs.json').read_text());records=[];status='running'
    engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config))
    cases=[('a-cold','A',False),('a-warm','A',False),('b-cold','B',False),('b-warm','B',False),('a-return','A',False),('none-cold',None,False),('none-warm',None,False),('empty','',False),('mutated-a','A',True),('a-return2','A',False)]
    try:
        for trial in range(5):
            for case,salt,mutate in cases:
                ids=base.copy();ids[0]=(4200 if mutate else 4100)+trial
                prompt={'prompt_token_ids':ids}
                if salt is not None:prompt['cache_salt']=salt
                begin=time.monotonic();events=[];final=None
                async for out in engine.generate(prompt,SamplingParams(temperature=0,max_tokens=1,ignore_eos=True),f'trial-{trial}-{case}'):
                    final=out;events.append([time.monotonic()-begin,len(out.outputs[0].token_ids)])
                records.append(dict(trial=trial,case=case,salt=salt,mutated=mutate,input_first_token=ids[0],input_sha256=hashlib.sha256(json.dumps(ids).encode()).hexdigest(),input_tokens=len(ids),cached_tokens=final.num_cached_tokens,output_ids=list(final.outputs[0].token_ids),events=events,elapsed_s=time.monotonic()-begin,metrics=asdict(final.metrics) if final.metrics is not None else None))
            print('trial',trial,'completed',flush=True)
        status='passed'
    finally:
        engine.shutdown();(a.output/'raw.json').write_text(json.dumps(dict(status=status,records=records,config=config,versions={p:importlib.metadata.version(p) for p in ['vllm','torch','triton']},source_hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['run.py','inputs.json','engine-config.json','PROTOCOL.md','input-provenance.json']}),indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);asyncio.run(main(p.parse_args()))
