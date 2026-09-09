import argparse,asyncio,hashlib,json,os,random,time
from dataclasses import asdict
from pathlib import Path

def fixture(tok,rows,seed,index):
    rng=random.Random(seed)
    values=[str(rng.randrange(100000,1000000)) for _ in range(rows)]
    document='\n'.join(f'k{i:04d} = {v}' for i,v in enumerate(values))
    targets=[rows//8,rows//2,rows-rows//8-1]
    expected={f'k{i:04d}':values[i] for i in targets}
    messages=[dict(role='system',content='Read the supplied records. Return only a JSON object mapping each requested key to its exact six-digit value as a string. Do not add explanation.'),
        dict(role='user',content=f'Records:\n{document}\n\nReturn values for these keys: '+', '.join(expected))]
    ids=tok.apply_chat_template(messages,tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
    return dict(id=index,rows=rows,seed=seed,messages=messages,prompt_token_ids=ids,expected=expected)

async def main(args):
    os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
    if args.output.exists():raise RuntimeError('Use a fresh output directory')
    args.output.mkdir(parents=True)
    import torch,vllm
    from transformers import AutoTokenizer
    from vllm import AsyncEngineArgs,AsyncLLMEngine,SamplingParams
    tok=AutoTokenizer.from_pretrained(args.model,local_files_only=True)
    tasks=[fixture(tok,n,808000+n+i,f'n{n}-r{i}') for n in [128,512] for i in range(4)]
    calibration=fixture(tok,512,999808,'calibration')
    (args.output/'inputs.json').write_text(json.dumps(dict(tasks=tasks,calibration=calibration))+'\n')
    config=dict(model=args.model,dtype='bfloat16',kv_cache_dtype=args.kv_dtype,
        calculate_kv_scales=False,max_model_len=16384,max_num_seqs=4,max_num_batched_tokens=16384,
        enable_chunked_prefill=True,enable_prefix_caching=False,enforce_eager=True,async_scheduling=False,
        gpu_memory_utilization=.45,kv_cache_memory_bytes=12*1024**3,seed=808,
        attention_backend='TRITON_ATTN',worker_extension_cls='probe.KVProbe')
    env=dict(config=config,torch=torch.__version__,vllm=vllm.__version__,
        hashes={n:hashlib.sha256((Path(__file__).parent/n).read_bytes()).hexdigest() for n in ['run.py','probe.py']},
        input_sha256=hashlib.sha256((args.output/'inputs.json').read_bytes()).hexdigest(),
        scope='BF16 weights held fixed. Explicit independent calibration before warmups; first attention call computes scales once. Synthetic exact retrieval quality, not general task quality.')
    (args.output/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
    engine=AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**config))
    requests=(args.output/'requests.jsonl').open('w',buffering=1)
    batches=(args.output/'batches.jsonl').open('w',buffering=1)
    snapshots={}
    async def one(task,rid,mode):
        start=time.monotonic();events=[];final=None
        async for out in engine.generate({'prompt_token_ids':task['prompt_token_ids']},
                SamplingParams(temperature=0,max_tokens=64 if mode=='fixed' else 128,ignore_eos=mode=='fixed'),rid):
            events.append([time.monotonic(),len(out.outputs[0].token_ids)]);final=out
        seq=final.outputs[0]
        row=dict(id=rid,task_id=task['id'],mode=mode,start_s=start,end_s=time.monotonic(),events=events,
            output_ids=list(seq.token_ids),text=seq.text,finish_reason=seq.finish_reason,stop_reason=seq.stop_reason,metrics=asdict(final.metrics))
        requests.write(json.dumps(row)+'\n');return row
    async def batch(n,concurrency,mode,trial):
        selected=[t for t in tasks if t['rows']==n]
        rid=f'{trial}-n{n}-b{concurrency}-{mode}';start=time.monotonic()
        if concurrency==1:
            for t in selected:await one(t,f'{rid}-{t["id"]}',mode)
        else:await asyncio.gather(*(one(t,f'{rid}-{t["id"]}',mode) for t in selected))
        batches.write(json.dumps(dict(id=rid,rows=n,concurrency=concurrency,mode=mode,trial=trial,start_s=start,end_s=time.monotonic()))+'\n')
        print(rid,'done',flush=True)
    try:
        snapshots['before']=await engine.collective_rpc('kv_snapshot')
        if args.kv_dtype!='auto':snapshots['armed_layers']=await engine.collective_rpc('arm_kv_calibration')
        await one(calibration,'calibration','natural')
        snapshots['after_calibration']=await engine.collective_rpc('kv_snapshot')
        conditions=[(n,b,m) for n in [128,512] for b in [1,4] for m in ['natural','fixed']]
        for n,b,m in conditions:await batch(n,b,m,'warm')
        rng=random.Random(808)
        for trial in range(2):
            order=conditions.copy();rng.shuffle(order)
            for n,b,m in order:await batch(n,b,m,trial)
        snapshots['after']=await engine.collective_rpc('kv_snapshot')
    finally:
        (args.output/'kv-snapshots.json').write_text(json.dumps(snapshots,indent=2)+'\n')
        engine.shutdown();requests.close();batches.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--kv-dtype',choices=['auto','fp8_e4m3'],default='auto')
    asyncio.run(main(p.parse_args()))
