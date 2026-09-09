import argparse,hashlib,json
from pathlib import Path
import torch,triton
import compare
p=argparse.ArgumentParser();p.add_argument('--t',type=int,required=True);p.add_argument('--path',required=True);a=p.parse_args()
root=Path(__file__).resolve().parent;data=torch.load(root/f'results/compare/t{a.t}-tensors.pt',weights_only=True)
g=data['g'].cuda();u=data['u'].cuda();q=torch.empty_like(g,dtype=torch.float8_e4m3fn);s=torch.empty((a.t,1),device='cuda',dtype=torch.float32)
if a.path=='opaque_custom':fn=lambda:compare.opaque(g,u)
elif a.path=='compiler_visible':
 compiled=torch.compile(compare.expression,fullgraph=True);fn=lambda:compiled(g,u)
else:
 def fn():
  compare.fused[(a.t,)](g,u,q,s,12288,16384,num_warps=8);return q,s
for _ in range(5):out=fn()
torch.cuda.synchronize();torch.cuda.profiler.start();out=fn();torch.cuda.synchronize();torch.cuda.profiler.stop()
aq,asc=[v.cpu() for v in out]
print(json.dumps(dict(t=a.t,path=a.path,input_sha256=hashlib.sha256(data['g'].view(torch.uint8).numpy().tobytes()+data['u'].view(torch.uint8).numpy().tobytes()).hexdigest(),different_fp8_elements=int((aq.view(torch.uint8)!=data['reference_q'].view(torch.uint8)).sum()),scale_difference=float((asc-data['reference_s']).abs().max()))))
