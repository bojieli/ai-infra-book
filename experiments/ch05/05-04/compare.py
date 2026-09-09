"""Actual SwiGLU -> BF16 boundary -> per-row FP8 quantization implementations."""
import argparse,hashlib,json,platform,random,time
from pathlib import Path
import torch
import triton
import triton.language as tl

@triton.jit
def fused(G,U,Q,S,D:tl.constexpr,B:tl.constexpr):
 row=tl.program_id(0);i=tl.arange(0,B);mask=i<D
 g=tl.load(G+row*D+i,mask,other=0).to(tl.float32);u=tl.load(U+row*D+i,mask,other=0).to(tl.float32)
 y=(g/(1+tl.exp(-g))*u).to(tl.bfloat16).to(tl.float32)
 scale=tl.maximum(tl.max(tl.abs(y),0)/448.,1.e-8)
 v=tl.minimum(tl.maximum(y/scale,-448.),448.).to(tl.float8e4nv)
 tl.store(Q+row*D+i,v,mask);tl.store(S+row,scale)

def expression(g,u):
 raw=torch.nn.functional.silu(g.float())*u.float()
 # Explicit finite FP32 -> BF16 round-to-nearest-even, returned as FP32 bits.
 bits=raw.contiguous().view(torch.int32)
 y=((bits + 32767 + ((bits >> 16) & 1)) & -65536).view(torch.float32)
 s=y.abs().amax(-1,keepdim=True).div(448.).clamp_min(1.e-8)
 return (y/s).clamp(-448,448).to(torch.float8_e4m3fn),s

def native(g,u):
 y=(torch.nn.functional.silu(g.float())*u.float()).bfloat16().float()
 s=y.abs().amax(-1,keepdim=True).div(448.).clamp_min(1.e-8)
 return (y/s).clamp(-448,448).to(torch.float8_e4m3fn),s

@torch.library.custom_op('book504compare::opaque',mutates_args=())
def opaque(g:torch.Tensor,u:torch.Tensor)->tuple[torch.Tensor,torch.Tensor]:return native(g,u)
@opaque.register_fake
def _(g,u):return torch.empty_like(g,dtype=torch.float8_e4m3fn),torch.empty((g.shape[0],1),device=g.device,dtype=torch.float32)

def main(out):
 if out.exists():raise RuntimeError('Use fresh output directory')
 out.mkdir(parents=True);torch.manual_seed(504);rng=random.Random(504);rows=[]
 compiled=torch.compile(expression,fullgraph=True)
 custom=torch.compile(opaque,fullgraph=True)
 for t in [1,1024]:
  d=12288;g=torch.randn(t,d,device='cuda',dtype=torch.bfloat16);u=torch.randn_like(g)
  q=torch.empty_like(g,dtype=torch.float8_e4m3fn);s=torch.empty((t,1),device='cuda',dtype=torch.float32)
  def explicit():
   fused[(t,)](g,u,q,s,d,triton.next_power_of_2(d),num_warps=8);return q,s
  paths={'opaque_custom':lambda:custom(g,u),'compiler_visible':lambda:compiled(g,u),'explicit_fusion':explicit}
  refq,refs=native(g,u);ref=refq.float()*refs
  records={}
  for name,fn in paths.items():
   torch.cuda.synchronize();start=time.perf_counter();aq,asc=fn();torch.cuda.synchronize();prepare=time.perf_counter()-start
   actual=aq.float()*asc;assert torch.isfinite(actual).all()
   # Numerical variants near FP8 rounding boundaries are measured, not hidden by exactness claims.
   torch.testing.assert_close(actual,ref,atol=.04,rtol=.15)
   records[name]=dict(first_call_seconds=prepare,fp8_different_elements=int((aq.view(torch.uint8)!=refq.view(torch.uint8)).sum()),
    max_abs_dequant_difference=float((actual-ref).abs().max()),max_scale_difference=float((asc-refs).abs().max()),samples_us=[],graph_samples_us=[])
   for _ in range(5):fn()
  graphs={};graph_outputs={}
  for name,fn in paths.items():
   graph=torch.cuda.CUDAGraph()
   with torch.cuda.graph(graph):
    for _ in range(20):last=fn()
   graphs[name]=graph;graph_outputs[name]=last
   for _ in range(3):graph.replay()
  torch.cuda.synchronize()
  for name,(aq,asc) in graph_outputs.items():
   torch.testing.assert_close(aq.float()*asc,ref,atol=.04,rtol=.15)
   records[name]['graph_fp8_different_elements']=int((aq.view(torch.uint8)!=refq.view(torch.uint8)).sum())
   records[name]['graph_max_scale_difference']=float((asc-refs).abs().max())
  for trial in range(11):
   order=[(name,mode) for name in paths for mode in ['eager','graph']];rng.shuffle(order)
   for name,mode in order:
    a,b=torch.cuda.Event(enable_timing=True),torch.cuda.Event(enable_timing=True);a.record()
    if mode=='graph':graphs[name].replay()
    else:
     for _ in range(20):paths[name]()
    b.record();b.synchronize();records[name]['samples_us' if mode=='eager' else 'graph_samples_us'].append(a.elapsed_time(b)*1000/20)
  # Actual CUDA activity trace per path, separate from formal timing.
  for name,fn in paths.items():
   with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA]) as prof:
    fn();torch.cuda.synchronize()
   prof.export_chrome_trace(str(out/f't{t}-{name}-trace.json'))
  rows.append(dict(t=t,d=d,paths=records));print('completed',t,flush=True)
  torch.save(dict(g=g.cpu(),u=u.cpu(),reference_q=refq.cpu(),reference_s=refs.cpu(),outputs={name:tuple(x.cpu() for x in fn()) for name,fn in paths.items()}),out/f't{t}-tensors.pt')
 (out/'results.json').write_text(json.dumps(dict(rows=rows,environment=dict(torch=torch.__version__,triton=triton.__version__,python=platform.python_version(),gpu=torch.cuda.get_device_name(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
 contract='Finite FP32 SwiGLU -> explicit BF16 RNE bit boundary -> FP32 per-row absmax/448 clamped min1e-8 -> E4M3FN. No model weights. Approximate exp may alter rounding; report differences. Warm inputs; 11x20 interleaved CUDA-event eager and graph samples; native-cast opaque baseline. Eager includes submission gaps; graph construction excluded.'),indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
