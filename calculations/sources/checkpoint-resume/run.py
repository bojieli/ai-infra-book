"""Real PyTorch DCP resharding, CPU/Gloo; not a distributed LLM trainer.

torchrun --standalone --nproc-per-node=2 run.py save --root results
torchrun --standalone --nproc-per-node=3 run.py load --root results --axis 1
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import torch
import torch.distributed as dist
import torch.distributed.checkpoint as dcp
from torch.distributed.device_mesh import init_device_mesh
from torch.distributed.tensor import DTensor, Shard, Replicate, distribute_tensor


def build():
    torch.manual_seed(1006)
    model=torch.nn.Sequential(torch.nn.Linear(129,257),torch.nn.Tanh(),
                              torch.nn.Dropout(.2),torch.nn.Linear(257,17))
    optimizer=torch.optim.AdamW(model.parameters(),lr=.001)
    generator=torch.Generator().manual_seed(106)
    return model,optimizer,generator


def step(model,optimizer,generator):
    x=torch.randn(11,129,generator=generator)
    target=torch.randn(11,17,generator=generator)
    optimizer.zero_grad(set_to_none=True)
    loss=(model(x)-target).square().mean()
    loss.backward();optimizer.step()
    return loss.item()


def state(model,optimizer,generator,cursor):
    values={f'model.{k}':v.detach().clone() for k,v in model.state_dict().items()}
    for i,p in enumerate(model.parameters()):
        for k,v in optimizer.state[p].items():values[f'optim.{i}.{k}']=v.clone()
    values.update(rng=torch.get_rng_state(),data_rng=generator.get_state(),cursor=torch.tensor(cursor))
    return values


def restore(values,model,optimizer,generator):
    model.load_state_dict({k:values[f'model.{k}'] for k in model.state_dict()})
    for i,p in enumerate(model.parameters()):
        for k in optimizer.state[p]:optimizer.state[p][k]=values[f'optim.{i}.{k}'].clone()
    torch.set_rng_state(values['rng']);generator.set_state(values['data_rng'])


def fingerprint(values):
    return {k:hashlib.sha256(v.contiguous().numpy().tobytes()).hexdigest() for k,v in values.items()}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['save','load'])
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--axis',type=int,default=0,choices=[0,1])
    args=parser.parse_args()
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    dist.init_process_group('gloo')
    rank,world=dist.get_rank(),dist.get_world_size()
    mesh=init_device_mesh('cpu',(world,))
    args.root.mkdir(parents=True,exist_ok=True)
    model,optimizer,generator=build()
    for _ in range(4):step(model,optimizer,generator)
    initial=state(model,optimizer,generator,4)
    if args.mode=='save' and rank==0:
        before=fingerprint(initial)
        loss=step(model,optimizer,generator)
        after=fingerprint(state(model,optimizer,generator,5))
        (args.root/'reference.json').write_text(json.dumps(dict(before=before,after=after,next_loss=loss),indent=2)+'\n')
    # On load every tensor starts from zeros, preventing a matching initial
    # training run from concealing a missing checkpoint field.
    distributed={}
    for key,value in initial.items():
        placement=Shard(min(args.axis,value.ndim-1)) if value.ndim and not key.endswith('rng') else Replicate()
        source=value if args.mode=='save' else torch.zeros_like(value)
        distributed[key]=distribute_tensor(source,mesh,[placement])
    dist.barrier();start=time.perf_counter()
    if args.mode=='save':
        metadata=dcp.save(distributed,checkpoint_id=args.root/'checkpoint')
    else:
        dcp.load(distributed,checkpoint_id=args.root/'checkpoint')
    seconds=time.perf_counter()-start
    record=dict(rank=rank,world_size=world,axis=args.axis,mode=args.mode,api_seconds=seconds,
                torch=torch.__version__,backend='gloo',device='cpu',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                local_shapes={k:list(v.to_local().shape) for k,v in distributed.items()})
    if args.mode=='load':
        restored={k:v.full_tensor() for k,v in distributed.items()}
        reference=json.loads((args.root/'reference.json').read_text())
        assert fingerprint(restored)==reference['before']
        restore(restored,model,optimizer,generator)
        loss=step(model,optimizer,generator)
        assert loss==reference['next_loss']
        after=state(model,optimizer,generator,int(restored['cursor'])+1)
        assert fingerprint(after)==reference['after']
        # Negative control: same restored weights/RNG with lost Adam moments
        # must fail the next-state equality check.
        restore(restored,model,optimizer,generator)
        for values in optimizer.state.values():
            for k in ['exp_avg','exp_avg_sq']:values[k].zero_()
        step(model,optimizer,generator)
        bad=fingerprint(state(model,optimizer,generator,5))
        assert bad!=reference['after']
        record.update(restored_hashes=fingerprint(restored),next_state_hashes=fingerprint(after),
                      next_loss=loss,optimizer_loss_negative_control_detected=True)
    (args.root/f'{args.mode}-w{world}-axis{args.axis}-rank{rank}.json').write_text(json.dumps(record,indent=2)+'\n')
    dist.barrier()
    if rank==0:print(json.dumps(dict(mode=args.mode,world=world,axis=args.axis,passed=True)),flush=True)
    dist.destroy_process_group()


if __name__=='__main__':main()
