"""Replay pinned ServeGen arrivals with intact-pair temporal permutation."""
import argparse,asyncio,hashlib,json,os,subprocess,time
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parent
async def main(a):
    if a.output.exists():raise RuntimeError('Fresh output required')
    a.output.mkdir(parents=True);os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
    from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
    from vllm.v1.metrics.loggers import StatLoggerBase
    config=json.loads((ROOT/'engine-config.json').read_text());inputs=json.loads((ROOT/'inputs.json').read_text());workloads=json.loads((ROOT/'workloads.json').read_text())
    state={'case':'warmup','origin':time.monotonic(),'last_sample':0.,'preemptions':0}
    stat_file=(a.output/'scheduler.jsonl').open('w',buffering=1)
    class Logger(StatLoggerBase):
        def __init__(self,*args,**kwargs):pass
        def log_engine_initialized(self):pass
        def record(self,scheduler_stats,iteration_stats,mm_cache_stats=None,engine_idx=0):
            now=time.monotonic();pre=getattr(iteration_stats,'num_preempted_reqs',0) if iteration_stats is not None else 0
            state['preemptions']+=pre
            if now-state['last_sample']<.1 and not pre:return
            state['last_sample']=now
            stat_file.write(json.dumps(dict(case=state['case'],t_s=now-state['origin'],
                running=scheduler_stats.num_running_reqs,waiting=scheduler_stats.num_waiting_reqs,
                kv_usage=scheduler_stats.kv_cache_usage,preemptions_total=state['preemptions'],
                generated_tokens=getattr(iteration_stats,'num_generation_tokens',None)))+'\n')
    environment=dict(config=config,source_hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['run.py','inputs.json','workloads.json','engine-config.json','input-provenance.json']},
        protocol='Two sequential120s cases: original ServeGen window337800 seed302 and permutation seed303 of intact input/output-length pairs over the exact same timestamps.480 each. Synthetic valid token adapter, unique leading token per task; no production content or prefix identity. Greedy forced output, APC off; open loop then drain. Fixed order is a limitation, not replicated performance evidence.',
        status='running',cases=[])
    (a.output/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
    monitor_file=(a.output/'gpu-activity.log').open('w');monitor=subprocess.Popen(['nvidia-smi','pmon','-s','um','-d','1'],stdout=monitor_file,stderr=subprocess.STDOUT)
    engine=None
    try:
        engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config),stat_loggers=[lambda cfg,idx:Logger(cfg,idx)])
        for mode,arrivals in workloads.items():
            state.update(case=mode+'-warmup',origin=time.monotonic(),last_sample=0.,preemptions=0)
            for kind in ['0','1']:
                async for _ in engine.generate({'prompt_token_ids':inputs[kind][0]},SamplingParams(temperature=0,max_tokens=8,ignore_eos=True),mode+'-warm-'+kind):pass
            state.update(case=mode,origin=time.monotonic(),last_sample=0.,preemptions=0)
            origin=state['origin'];pending=[];finished=0
            request_file=(a.output/f'{mode}-requests.jsonl').open('w',buffering=1)
            dispatch_file=(a.output/f'{mode}-dispatch.jsonl').open('w',buffering=1)
            async def one(row):
                nonlocal finished
                rid=f"{mode}-{row['index']}";ids=inputs[row['kind']][row['task_index']];start=time.monotonic();events=[];final=None
                dispatch_file.write(json.dumps(dict(**row,actual_dispatch_s=start-origin,lag_s=start-origin-row['arrival_s']))+'\n')
                async for output in engine.generate({'prompt_token_ids':ids},SamplingParams(temperature=0,max_tokens=row['output_tokens'],ignore_eos=True),rid):
                    final=output;events.append([time.monotonic()-origin,len(output.outputs[0].token_ids)])
                end=time.monotonic();record=dict(**row,actual_dispatch_s=start-origin,end_s=end-origin,
                    events=events,output_ids=list(final.outputs[0].token_ids),cached_tokens=final.num_cached_tokens,
                    metrics=asdict(final.metrics),input_sha256=hashlib.sha256(json.dumps(ids).encode()).hexdigest())
                request_file.write(json.dumps(record)+'\n');finished+=1
                if finished%40==0:print(mode,'finished',finished,'elapsed',end-origin,flush=True)
            try:
                for row in arrivals:
                    await asyncio.sleep(max(0,origin+row['arrival_s']-time.monotonic()))
                    pending.append(asyncio.create_task(one(row)))
                await asyncio.sleep(max(0,origin+120-time.monotonic()))
                print(mode,'arrivals ended; completed',finished,flush=True)
                await asyncio.gather(*pending)
                environment['cases'].append(dict(mode=mode,origin_monotonic=origin,elapsed_s=time.monotonic()-origin,completed=finished,preemptions=state['preemptions']))
            finally:request_file.close();dispatch_file.close()
            (a.output/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
        environment['status']='passed'
    finally:
        if engine is not None:engine.shutdown()
        monitor.terminate();monitor.wait(timeout=10);monitor_file.close();stat_file.close()
        (a.output/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);asyncio.run(main(p.parse_args()))
