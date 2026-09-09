#!/usr/bin/env python3
"""One saved M8, unmodified installed function, observational trace/dispatch."""
import os,sys,pathlib,json,hashlib,time,subprocess,inspect
B=pathlib.Path(__file__).resolve().parent; O=B/'results';O.mkdir(exist_ok=True)
P=B.parent/'expert-preflight'; R=P/'results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(n,x):(O/n).write_text(json.dumps(x,indent=2))
free=subprocess.check_output(['nvidia-smi','--query-gpu=index,name,memory.free,memory.total','--format=csv,noheader'],text=True)
(O/'gpu_before.txt').write_text(free);assert int(free.splitlines()[0].split(',')[-2].strip().split()[0])>=4096
import numpy as np
import torch,triton,importlib.metadata
from torch.utils._python_dispatch import TorchDispatchMode
from sglang.srt.layers.moe.fused_moe_triton import mxfp4_moe_sm120_triton as mod
f=mod.mxfp4_moe_forward_triton
src=pathlib.Path(inspect.getsourcefile(f));assert sha(src)==sha(R/'sources'/src.name)
(O/src.name).write_bytes(src.read_bytes())
paths=[R/'main_m8.npz',R/'assembled.npz',R/'raw_checkpoint.npz',R/'selected_tensors.json',P/'PROTOCOL.md',P/'reference.py',src]
js('input_sources.json',[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in paths])
torch.set_num_threads(4);torch.set_num_interop_threads(4)
assert torch.__version__=='2.11.0+cu130';assert importlib.metadata.version('sglang')=='0.5.13.post1'
torch.cuda.set_per_process_memory_fraction(2*1024**3/torch.cuda.get_device_properties(0).total_memory)
torch.cuda.reset_peak_memory_stats()
js('environment.json',dict(executable=sys.executable,python=sys.version,torch=torch.__version__,sglang=importlib.metadata.version('sglang'),triton=triton.__version__,cuda=torch.version.cuda,device=torch.cuda.get_device_name(),capability=torch.cuda.get_device_capability(),pid=os.getpid(),affinity=list(os.sched_getaffinity(0)),threads=torch.get_num_threads(),start=time.time()))
a=np.load(R/'assembled.npz'); c=np.load(R/'main_m8.npz')
w=[torch.from_numpy(a[k]).to('cuda') for k in ['w13_packed','w2_packed','w13_scale','w2_scale']]
x=torch.from_numpy(c['input']).to('cuda',dtype=torch.bfloat16); ids=torch.from_numpy(c['ids']).cuda();routes=torch.from_numpy(c['routing']).cuda()
saved={};events=[];configs={}
def snap(k,t):
 torch.cuda.synchronize();saved[k]=t.detach().float().cpu().numpy().copy()
def config(k):
 obj=mod._mxfp4_slot_gemv_kernel
 configs[k]=dict(best_config=str(obj.best_config),cache={str(a):str(b) for a,b in obj.cache.items()})
lines,start=inspect.getsourcelines(f)
gate_line=start+next(i for i,s in enumerate(lines) if s.strip()=='gate = intermediate[:, :I].float()')
mask_line=start+next(i for i,s in enumerate(lines) if s.strip().startswith('valid_mask ='))
def trace(frame,event,arg):
 if frame.f_code is not f.__code__:return None
 if event=='line' and frame.f_lineno==gate_line:config('gemv1')
 if event=='line' and frame.f_lineno==mask_line:snap('down',frame.f_locals['down']);config('gemv2')
 if event=='return':
  for k,n in [('first','intermediate'),('activated','activated'),('masked','down'),('flat_weights','flat_weights')]:snap(k,frame.f_locals[n])
  snap('output',arg)
 return trace
class Observe(TorchDispatchMode):
 def __torch_dispatch__(self,func,types,args=(),kwargs=None):
  out=func(*args,**(kwargs or {}))
  if str(func)=='aten.mul.Tensor' and isinstance(out,torch.Tensor) and tuple(out.shape)==(48,4096):
   k='masked_dispatch' if 'masked_dispatch' not in saved else 'product';snap(k,out);events.append(dict(op=str(func),stage=k))
  if str(func)=='aten.sum.dim_IntList' and isinstance(out,torch.Tensor) and tuple(out.shape)==(8,4096):snap('reduce',out);events.append(dict(op=str(func),stage='reduce'))
  return out
with torch.inference_mode(),Observe():
 sys.settrace(trace)
 try:y=f(x,*w,ids,routes,4096,2048,routed_scaling_factor=1.5,clamp_limit=10.)
 finally:sys.settrace(None)
torch.cuda.synchronize()
assert set(['first','activated','down','masked','product','reduce','output','flat_weights'])<=saved.keys()
np.savez(O/'stages.npz',**saved,input=c['input'],ids=c['ids'],routing=c['routing'])
# One same-input unobserved control, same process/autotune cache.
with torch.inference_mode():plain=f(x,*w,ids,routes,4096,2048,routed_scaling_factor=1.5,clamp_limit=10.)
snap('plain_output',plain);np.save(O/'plain_output.npy',saved['plain_output'])
js('observation.json',dict(events=events,gate_line=gate_line,pre_mask_line=mask_line,source_sha256=sha(src),note='Synchronous CPU copies; no source, algorithm or autotune config changes. Unobserved same-input control follows.'))
js('autotune.json',configs)
js('memory.json',dict(allocated_peak_bytes=torch.cuda.max_memory_allocated(),reserved_peak_bytes=torch.cuda.max_memory_reserved(),finish=time.time()))
js('raw_manifest.json',[dict(path=str(p.relative_to(B)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(O.iterdir()) if p.is_file()])
print('RAW COMPLETE',flush=True)
