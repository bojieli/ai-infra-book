import os,json,traceback
from pathlib import Path
import torch
import torch.distributed as dist
from torch.distributed.fsdp import fully_shard
from torch.distributed.device_mesh import init_device_mesh
P=Path(__file__).resolve().parent
rank=int(os.environ['RANK']); torch.set_num_threads(1)
dist.init_process_group('gloo')
try:
 torch.manual_seed(1001)
 model=torch.nn.Linear(16,8)
 mesh=init_device_mesh('cpu',(dist.get_world_size(),))
 fully_shard(model,mesh=mesh,reshard_after_forward=True)
 opt=torch.optim.AdamW(model.parameters(),lr=.001)
 before={k:list(p.to_local().shape) for k,p in model.named_parameters()}
 loss=model(torch.randn(4,16)).square().mean();loss.backward();opt.step()
 after={k:dict(type=type(p).__name__,shape=list(p.to_local().shape),grad=list(p.grad.to_local().shape)) for k,p in model.named_parameters()}
 (P/f'probe-rank{rank}.json').write_text(json.dumps(dict(status='passed',rank=rank,torch=torch.__version__,before=before,after=after,loss=loss.item()),indent=2)+'\n')
except Exception:
 (P/f'probe-rank{rank}-failure.txt').write_text(traceback.format_exc());raise
finally:dist.destroy_process_group()
