"""APC-off nested-length sweep; lightweight client observations only."""
import argparse,asyncio,hashlib,json,os,random,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
async def main(a):
    if a.output.exists():raise RuntimeError('Fresh output directory required')
    a.output.mkdir(parents=True);os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
    from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
    config=json.loads((ROOT/'followup-config.json').read_text());inputs=json.loads((ROOT/'followup-inputs.json').read_text())
    protocol=dict(lengths=[2048,8192],batches=[1,16],trials=3,warmups_per_case=1,output_tokens=256,
        temperature=0,ignore_eos=True,seed=104,apc=False,
        observation='Client streaming events only; no per-step scheduler callbacks. nvidia-smi pmon external 1-second samples.',
        input_control='Short prompt is first2048 tokens of corresponding8192-token prompt. Short prompts may coincide; APC remains disabled.')
    result=dict(config=config,protocol=protocol,source_hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['run_followup.py','followup-inputs.json','followup-config.json']},batches=[],requests=[],status='running')
    (a.output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    monitor_log=(a.output/'gpu-activity.log').open('w');monitor=subprocess.Popen(['nvidia-smi','pmon','-s','um','-d','1'],stdout=monitor_log,stderr=subprocess.STDOUT)
    engine=None;origin=time.perf_counter()
    async def request(kind,batch,trial,i):
        ids=inputs[kind][i];rid=f'{trial}-{kind}-b{batch}-r{i}';start=time.perf_counter();events=[];final=None
        async for out in engine.generate({'prompt_token_ids':ids},SamplingParams(temperature=0,max_tokens=256,ignore_eos=True),rid):
            final=out;events.append([time.perf_counter()-origin,len(out.outputs[0].token_ids)])
        return dict(id=rid,kind=kind,batch=batch,trial=trial,index=i,start_s=start-origin,end_s=time.perf_counter()-origin,events=events,
            cached_tokens=final.num_cached_tokens,input_tokens=len(ids),input_sha256=hashlib.sha256(json.dumps(ids).encode()).hexdigest(),output_ids=list(final.outputs[0].token_ids))
    async def batch_run(kind,batch,trial):
        start=time.perf_counter();rows=await asyncio.gather(*(request(kind,batch,trial,i) for i in range(batch)));end=time.perf_counter()
        record=dict(kind=kind,batch=batch,trial=trial,start_s=start-origin,end_s=end-origin)
        result['requests'].extend(rows);result['batches'].append(record)
        with (a.output/'requests.jsonl').open('a') as f:
            for r in rows:f.write(json.dumps(r)+'\n')
        print(trial,kind,batch,end-start,flush=True)
    try:
        start=time.perf_counter();engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config));result['startup_s']=time.perf_counter()-start
        cases=[(kind,b) for kind in ['short','long'] for b in [1,16]]
        for kind,b in cases:await batch_run(kind,b,'warm')
        rng=random.Random(104)
        for trial in range(3):
            order=cases.copy();rng.shuffle(order)
            for kind,b in order:await batch_run(kind,b,trial)
        result['status']='passed'
    finally:
        if engine is not None:engine.shutdown()
        monitor.terminate();monitor.wait(timeout=10);monitor_log.close()
        result['elapsed_s']=time.perf_counter()-origin
        (a.output/'raw.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);asyncio.run(main(p.parse_args()))
