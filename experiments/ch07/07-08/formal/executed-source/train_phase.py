"""Real two-rank CPU DDP updates and native collective future observations."""
from datetime import timedelta
import json
import os
from pathlib import Path
import time
import traceback


def worker(index, job, rank, port, root, spec, ready, done, start_time, save_event):
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    with (root/'worker.log').open('w',buffering=1) as log:
        os.dup2(log.fileno(),1);os.dup2(log.fileno(),2)
        try:
            train(index,job,rank,port,root,spec,ready,done,start_time,save_event)
        except BaseException:
            traceback.print_exc();raise


def train(index,job,rank,port,root,spec,ready,done,start_time,save_event):
    import torch
    import torch.distributed as dist
    from torch.nn.parallel import DistributedDataParallel as DDP
    from torch.nn import functional as F
    from model import Model
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(7081+job)
    dist.init_process_group('gloo',init_method=f'tcp://127.0.0.1:{port}',rank=rank,world_size=2,
                            timeout=timedelta(seconds=60))
    model=Model(spec['width']);ddp=DDP(model,bucket_cap_mb=25)
    optimizer=torch.optim.AdamW(ddp.parameters(),lr=3e-4)
    data=torch.tensor(list((Path(__file__).parent/'data/input.txt').read_bytes()),dtype=torch.long)
    phases=[];communications=[];state={'step':None}
    def hook(state,bucket):
        begin=time.monotonic_ns();step=state['step'];buf=bucket.buffer()
        event=dict(step=step,bucket=bucket.index(),bytes=buf.numel()*buf.element_size(),
                   begin_ns=begin,last_bucket=bucket.is_last())
        work=dist.all_reduce(buf,async_op=True)
        def completed(future):
            event['future_done_ns']=time.monotonic_ns()
            result=future.value()[0].div_(2)
            event['averaged_ns']=time.monotonic_ns()
            if step is not None and step>=0:communications.append(event)
            return result
        return work.get_future().then(completed)
    ddp.register_comm_hook(state,hook)
    def update(step):
        state['step']=step
        begin=time.monotonic_ns()
        gen=torch.Generator().manual_seed(708000+job*10000+step+spec['warmup'])
        starts=torch.randint(0,len(data)-spec['sequence']-8192,(spec['global_batch'],),generator=gen)
        starts=starts[rank::2]
        xx=torch.stack([data[s:s+spec['sequence']] for s in starts])
        yy=torch.stack([data[s+1:s+spec['sequence']+1] for s in starts])
        optimizer.zero_grad(set_to_none=True)
        fw=time.monotonic_ns();logits=ddp(xx)
        loss=F.cross_entropy(logits.flatten(0,1),yy.flatten());bw=time.monotonic_ns()
        loss.backward();opt=time.monotonic_ns();optimizer.step();end=time.monotonic_ns()
        value=loss.item();assert torch.isfinite(loss).item()
        if step>=0:phases.append(dict(step=step,begin_ns=begin,forward_ns=fw,backward_ns=bw,
            optimizer_ns=opt,end_ns=end,loss=value,input_offsets=starts.tolist()))
    for step in range(-spec['warmup'],0):update(step)
    ready[index]=1
    while start_time.value==0:time.sleep(.001)
    target=start_time.value+(spec['offset_ns'] if job==1 else 0)
    while True:
        remaining=(target-time.monotonic_ns())/1e9
        if remaining<=0:break
        time.sleep(min(remaining,.005))
    begin=time.monotonic_ns()
    for step in range(spec['steps']):update(step)
    end=time.monotonic_ns();done[index]=1
    # Avoid checkpoint/log writes contending with a still-running peer job.
    if not save_event.wait(120):raise TimeoutError('save release')
    torch.save({'model':model.state_dict(),'optimizer':optimizer.state_dict()},root/'final.pt')
    (root/'steps.json').write_text(json.dumps(phases,indent=2)+'\n')
    (root/'collectives.json').write_text(json.dumps(communications,indent=2)+'\n')
    (root/'completion.json').write_text(json.dumps(dict(pid=os.getpid(),job=job,rank=rank,
        target_start_ns=target,start_ns=begin,end_ns=end,steps=len(phases),
        parameter_count=sum(p.numel() for p in model.parameters()),torch=torch.__version__,
        threads=torch.get_num_threads(),device='cpu'),indent=2)+'\n')
    dist.destroy_process_group()
