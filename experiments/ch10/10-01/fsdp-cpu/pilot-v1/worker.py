import os,json,argparse,time,traceback,hashlib,resource
from pathlib import Path
import torch
import torch.distributed as dist
from torch.distributed.fsdp import fully_shard
from torch.distributed.device_mesh import init_device_mesh
from model import FFN,data
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--reshard',type=int,required=True);a=p.parse_args()
rank=int(os.environ['RANK']);world=int(os.environ['WORLD_SIZE']);out=a.output/f'rank{rank}';out.mkdir(exist_ok=False)
torch.set_num_threads(1);dist.init_process_group('gloo');records=[]
def local(t):return t.to_local() if hasattr(t,'to_local') else t
try:
 with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU],profile_memory=True) as prof:
  torch.manual_seed(1001);model=FFN();fully_shard(model,mesh=init_device_mesh('cpu',(world,)),reshard_after_forward=bool(a.reshard));opt=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.01,foreach=False)
  def snapshot(stage,step):
   states=[];stores={}
   def add(name,t):
    v=local(t);st=v.untyped_storage();sid=str(st._cdata);stores[sid]=st.nbytes()
    states.append(dict(name=name,type=type(t).__name__,global_shape=list(t.shape),local_shape=list(v.shape),placements=str(getattr(t,'placements',None)),logical_bytes=v.numel()*v.element_size(),storage_id=sid,storage_bytes=st.nbytes()))
   for name,param in model.named_parameters():
    add('param/'+name,param)
    if param.grad is not None:add('grad/'+name,param.grad)
   for idx,(param,state) in enumerate(opt.state.items()):
    for key,v in state.items():
     if torch.is_tensor(v):add(f'optimizer/{idx}/{key}',v)
   records.append(dict(stage=stage,step=step,monotonic_ns=time.perf_counter_ns(),states=states,unique_visible_storage_bytes=sum(stores.values()),process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
  snapshot('initialized',-1)
  for step in range(3):
   opt.zero_grad(set_to_none=True);x,y=data(step);x=x.chunk(world)[rank];y=y.chunk(world)[rank]
   model.observer=lambda: snapshot('inside_forward',step)
   snapshot('before_forward',step)
   with torch.profiler.record_function(f'training_step_{step}'):
    pred=model(x);snapshot('after_forward',step);loss=(pred-y).square().mean();loss.backward();snapshot('after_backward',step);opt.step();snapshot('after_step',step)
   tensors={}
   for name,param in model.named_parameters():
    tensors['param/'+name]=local(param).detach();tensors['grad/'+name]=local(param.grad).detach()
    for key,v in opt.state[param].items():
     tensors['optimizer/'+name+'/'+key]=local(v).detach() if torch.is_tensor(v) else v
   with torch.profiler.record_function(f'save_evidence_{step}'):torch.save(tensors,out/f'step{step}.pt')
   (out/'snapshots.json').write_text(json.dumps(records,indent=2)+'\n')
  dist.barrier()
 prof.export_chrome_trace(str(out/'trace.json'))
 (out/'completion.json').write_text(json.dumps(dict(status='complete',rank=rank,world=world,reshard=bool(a.reshard),torch=torch.__version__,steps=3,source_sha256={f:hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest() for f in ['worker.py','model.py']}),indent=2)+'\n')
except BaseException:
 (out/'failure.txt').write_text(traceback.format_exc());raise
finally:dist.destroy_process_group()
