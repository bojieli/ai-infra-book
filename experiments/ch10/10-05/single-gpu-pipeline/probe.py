import os,json,datetime
from pathlib import Path
import torch
rank=int(os.environ['RANK']);torch.cuda.set_device(0)
torch.distributed.init_process_group('gloo',timeout=datetime.timedelta(seconds=60))
x=torch.arange(128,device='cuda',dtype=torch.float32) if rank==0 else torch.zeros(128,device='cuda')
if rank==0:torch.distributed.send(x,1)
else:torch.distributed.recv(x,0)
assert torch.equal(x,torch.arange(128,device='cuda',dtype=torch.float32))
torch.distributed.all_reduce(x);assert torch.equal(x,2*torch.arange(128,device='cuda',dtype=torch.float32))
torch.cuda.synchronize()
Path(f'probe-rank{rank}.json').write_text(json.dumps(dict(rank=rank,torch=torch.__version__,cuda=torch.version.cuda,device=torch.cuda.get_device_name(),backend='gloo',send_recv_elements=128,allreduce_elements=128,passed=True),indent=2)+'\n')
torch.distributed.destroy_process_group()
