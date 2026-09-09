"""Paired complete-request replacement, same eager engine and exact prompt."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import time
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

async def main(a):
    if a.output.exists():raise RuntimeError('Fresh output directory required')
    a.output.mkdir(parents=True)
    os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
    from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
    config=json.loads((ROOT/'engine-config.json').read_text());task=json.loads((ROOT/'input.json').read_text())
    protocol=dict(trials=11,warmups_per_mode=2,max_tokens=32,ignore_eos=True,temperature=0,
        concurrency=1,seed=509,enforce_eager=True,enable_prefix_caching=False,
        measurement='Client monotonic TTFT and complete request latency, cumulative streaming token events. No RPC or audit callback inside measured requests.',
        quality='Exact token agreement on this one fixed prompt only; not general model quality.')
    (a.output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    result=dict(config=config,protocol=protocol,source_hashes={f:sha(ROOT/f) for f in ['run.py','replacement_worker.py','candidate.py','input.json','engine-config.json','selection-provenance.json']},requests=[],audits=[],switches=[],status='running')
    activity=(a.output/'gpu-activity.log').open('w');monitor=subprocess.Popen(['nvidia-smi','pmon','-s','um','-d','1'],stdout=activity,stderr=subprocess.STDOUT)
    engine=None;origin=time.perf_counter()
    async def request(mode,phase,trial,max_tokens=32):
        start=time.perf_counter();events=[];final=None
        async for output in engine.generate({'prompt_token_ids':task['prompt_token_ids']},SamplingParams(temperature=0,max_tokens=max_tokens,ignore_eos=True),f'{phase}-{trial}-{mode}'):
            final=output;events.append(dict(elapsed_s=time.perf_counter()-start,token_count=len(output.outputs[0].token_ids)))
        end=time.perf_counter();ids=list(final.outputs[0].token_ids)
        return dict(mode=mode,phase=phase,trial=trial,start_s=start-origin,latency_s=end-start,
            ttft_s=next(e['elapsed_s'] for e in events if e['token_count']>0),events=events,
            output_ids=ids,output_text=final.outputs[0].text,prompt_tokens=len(task['prompt_token_ids']),output_tokens=len(ids))
    try:
        startup=time.perf_counter();engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config));result['engine_startup_s']=time.perf_counter()-startup
        result['installed']=await engine.collective_rpc('install_replacement')
        # Verify actual calls outside all measured windows.
        for mode in ['native','schedule']:
            await engine.collective_rpc('set_replacement',args=(mode,True))
            row=await request(mode,'audit',0,max_tokens=2)
            row['records']=await engine.collective_rpc('replacement_snapshot');result['audits'].append(row)
            result['switches'].append(await engine.collective_rpc('set_replacement',args=(mode,False)))
            for trial in range(protocol['warmups_per_mode']):result['requests'].append(await request(mode,'warmup',trial))
        rng=random.Random(protocol['seed'])
        with (a.output/'requests.jsonl').open('w',buffering=1) as log:
            for trial in range(protocol['trials']):
                order=['native','schedule'];rng.shuffle(order)
                for mode in order:
                    result['switches'].append(await engine.collective_rpc('set_replacement',args=(mode,False)))
                    row=await request(mode,'measure',trial);row['order']=order.index(mode)
                    result['requests'].append(row);log.write(json.dumps(row)+'\n')
                    print(trial,mode,row['ttft_s'],row['latency_s'],flush=True)
        result['status']='passed'
    finally:
        if engine is not None:engine.shutdown()
        monitor.terminate();monitor.wait(timeout=10);activity.close()
        result['elapsed_s']=time.perf_counter()-origin
        (a.output/'raw.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);asyncio.run(main(p.parse_args()))
