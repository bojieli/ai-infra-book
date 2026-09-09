import asyncio, json, os, time
from pathlib import Path
from observer import install, emit
install()  # Executed by spawned scheduler imports as well as the parent.
ROOT=Path(__file__).resolve().parent

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--count',type=int,choices=[1,8],required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();out=a.output
    def save(name,data): (out/name).write_text(json.dumps(data,indent=2,default=str)+'\n')
    inputs=json.loads((ROOT/'inputs.json').read_text());ref=json.loads((ROOT/'reference.json').read_text());config=json.loads((ROOT/'config.json').read_text())
    import torch
    torch.set_num_threads(4);torch.set_num_interop_threads(4)
    import sglang
    rows=[];begin=time.monotonic();engine=sglang.Engine(**config,port=18190)
    ready=time.monotonic()
    try:
        save('server-info.json',engine.get_server_info())
        async def one(i):
            rid=f'native-{i}';sent=time.monotonic();emit('client_send',request_id=rid,index=i)
            response=await engine.async_generate(input_ids=inputs,sampling_params={'temperature':0,'max_new_tokens':16,'ignore_eos':True},return_logprob=False,logprob_start_len=-1,rid=rid)
            end=time.monotonic();ids=response.get('output_ids');passed=ids==ref['output_ids'] and response.get('text')==ref['text']
            emit('client_complete',request_id=rid,index=i,response_id=response.get('meta_info',{}).get('id'),cached_tokens=response.get('meta_info',{}).get('cached_tokens'))
            rows.append(dict(index=i,request_id=rid,sent_s=sent,end_s=end,response=response,output_ids=ids,passed=passed));save('requests.json',rows)
            assert passed,'Full output differs from fixed reference'
        async def batch(): await asyncio.wait_for(asyncio.gather(*(one(i) for i in range(a.count))),120)
        engine.loop.run_until_complete(batch())
    finally:
        engine.shutdown();save('lifecycle.json',dict(begin_s=begin,ready_s=ready,shutdown_return_s=time.monotonic(),requests=len(rows)))
    assert len(rows)==a.count
    save('execution.json',dict(status='completed',count=a.count))
if __name__=='__main__': main()
