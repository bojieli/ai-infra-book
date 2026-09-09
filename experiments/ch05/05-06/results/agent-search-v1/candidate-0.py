import torch,triton
import triton.language as tl
@triton.jit
def kernel(X,Y,N:tl.constexpr,D:tl.constexpr,B:tl.constexpr):
 i=tl.program_id(0)*B+tl.arange(0,B);mask=i<N
 row=i//D;col=i%D
 g=tl.load(X+row*2*D+col,mask,0).to(tl.float32)
 u=tl.load(X+row*2*D+D+col,mask,0).to(tl.float32)
 y=(g/(1+tl.exp(-g)))*u
 tl.store(Y+i,y.to(tl.bfloat16),mask)

def run(x,block=256,warps=4):
 d=x.shape[-1]//2;y=torch.empty((x.shape[0],d),device=x.device,dtype=x.dtype)
 kernel[(triton.cdiv(y.numel(),block),)](x,y,y.numel(),d,block,num_warps=warps)
 return y