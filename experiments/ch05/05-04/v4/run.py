import argparse,ast,hashlib,json,random,time,types
from pathlib import Path
from typing import Optional
import torch
import torch.nn.functional as F
import triton
import triton.language as tl
ROOT=Path(__file__).resolve().parent
@triton.jit
def clip(G,U,GC,UC,N:tl.constexpr,B:tl.constexpr):
 i=tl.program_id(0)*B+tl.arange(0,B);m=i<N
 g=tl.load(G+i,m,0).to(tl.float32);u=tl.load(U+i,m,0).to(tl.float32)
 tl.store(GC+i,tl.minimum(g,10.),m);tl.store(UC+i,tl.minimum(tl.maximum(u,-10.),10.),m)
@triton.jit
def finish(G,U,W,Y,N:tl.constexpr,D:tl.constexpr,CLIP:tl.constexpr,B:tl.constexpr):
 i=tl.program_id(0)*B+tl.arange(0,B);m=i<N
 g=tl.load(G+i,m,0).to(tl.float32);u=tl.load(U+i,m,0).to(tl.float32)
 if CLIP:g=tl.minimum(g,10.);u=tl.minimum(tl.maximum(u,-10.),10.)
 w=tl.load(W+i//D,m,0);y=(g/(1+tl.exp(-g))*u)*w
 tl.store(Y+i,y.to(tl.bfloat16),m)
def original():
 tree=ast.parse((ROOT/'model.py.snapshot').read_text());expert=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Expert')
 fn=next(n for n in expert.body if isinstance(n,ast.FunctionDef) and n.name=='forward');mod=ast.Module(body=[fn],type_ignores=[])
 env={'torch':torch,'F':F,'Optional':Optional};exec(compile(ast.fix_missing_locations(mod),'frozen-Expert.forward','exec'),env)
 return env['forward']
def main(out):
 if out.exists():raise RuntimeError('Use fresh output directory')
 out.mkdir(parents=True);cfg=json.loads((ROOT/'config.json').read_text());assert cfg['moe_inter_dim']==2048 and cfg['swiglu_limit']==10
 torch.manual_seed(5042048);rng=random.Random(5042048);forward=original();rows=[]
 for t in [1,1024]:
  d=2048;n=t*d;g=(torch.randn(t,d,device='cuda')*12).bfloat16();u=(torch.randn(t,d,device='cuda')*12).bfloat16();w=torch.rand(t,1,device='cuda')*1.5
  g[0,:5]=torch.tensor([-20.,-10.,0.,10.,20.],device='cuda');u[0,:5]=torch.tensor([-20.,20.,-10.,10.,20.],device='cuda')
  gc=torch.empty_like(g,dtype=torch.float32);uc=torch.empty_like(gc);y=torch.empty_like(g)
  obj=types.SimpleNamespace(w1=lambda x:g,w3=lambda x:u,w2=lambda x:x,swiglu_limit=10.)
  x=torch.empty(0,device='cuda',dtype=torch.bfloat16)
  def baseline():return forward(obj,x,w)
  def partial():
   clip[(triton.cdiv(n,256),)](g,u,gc,uc,n,256)
   finish[(triton.cdiv(n,256),)](gc,uc,w,y,n,d,False,256);return y
  def full():
   finish[(triton.cdiv(n,256),)](g,u,w,y,n,d,True,256);return y
  paths={'source_chain':baseline,'two_kernel':partial,'one_kernel':full};ref=baseline();records={};outputs={}
  for name,fn in paths.items():
   start=time.perf_counter();actual=fn();torch.cuda.synchronize();prepare=time.perf_counter()-start
   torch.testing.assert_close(actual.float(),ref.float(),atol=.125,rtol=.02)
   outputs[name]=actual.cpu();records[name]=dict(first_call_s=prepare,different_elements=int((actual!=ref).sum()),max_abs_difference=float((actual.float()-ref.float()).abs().max()),eager_us=[],graph_us=[])
   for _ in range(5):fn()
  graphs={};retained={}
  for name,fn in paths.items():
   graph=torch.cuda.CUDAGraph()
   with torch.cuda.graph(graph):
    for _ in range(20):value=fn()
   graphs[name]=graph;retained[name]=value
   for _ in range(3):graph.replay()
  torch.cuda.synchronize()
  for name,value in retained.items():torch.testing.assert_close(value.float(),ref.float(),atol=.125,rtol=.02)
  for _ in range(11):
   order=[(name,mode) for name in paths for mode in ['eager','graph']];rng.shuffle(order)
   for name,mode in order:
    a,b=torch.cuda.Event(enable_timing=True),torch.cuda.Event(enable_timing=True);a.record()
    if mode=='graph':graphs[name].replay()
    else:
     for _ in range(20):paths[name]()
    b.record();b.synchronize();records[name][mode+'_us'].append(a.elapsed_time(b)*1000/20)
  for name,fn in paths.items():
   with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA]) as prof:fn();torch.cuda.synchronize()
   prof.export_chrome_trace(str(out/f't{t}-{name}-trace.json'))
  torch.save(dict(g=g.cpu(),u=u.cpu(),w=w.cpu(),reference=ref.cpu(),outputs=outputs),out/f't{t}-tensors.pt')
  rows.append(dict(t=t,d=d,paths=records));print('completed',t,flush=True)
 (out/'results.json').write_text(json.dumps(dict(rows=rows,source_hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['run.py','model.py.snapshot','config.json']},torch=torch.__version__,triton=triton.__version__,scope='Frozen Expert.forward activation subchain with w1/w3 supplied outputs and identity w2. FP32 asymmetric clipping, SiLU, up multiply, route weight multiply, final BF16. Not projections, FP4/FP8 GEMM or whole MoE. 11x20 shuffled eager/graph batches.'),indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
