"""Small numerical check before loading model; no model/cache claims."""
import json
import torch
import tilelang
from sglang.jit_kernel.norm import fused_inplace_qknorm
torch.manual_seed(908)
q=torch.randn(16,32,128,device='cuda',dtype=torch.bfloat16)
k=torch.randn(16,8,128,device='cuda',dtype=torch.bfloat16)
w=torch.ones(128,device='cuda',dtype=torch.bfloat16)
refs=[(x.float()*torch.rsqrt(x.float().square().mean(-1,keepdim=True)+1e-6)).to(x.dtype) for x in [q,k]]
fused_inplace_qknorm(q,k,w,w,head_dim=128,eps=1e-6)
torch.cuda.synchronize()
errors=[(x.float()-r.float()).abs().max().item() for x,r in zip([q,k],refs)]
for x,r in zip([q,k],refs):torch.testing.assert_close(x,r,atol=.03125,rtol=.01)
print(json.dumps(dict(torch=torch.__version__,tilelang=tilelang.__version__,max_abs_errors=errors,status='passed')))
