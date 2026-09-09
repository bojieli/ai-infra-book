#!/usr/bin/env python3
"""Bounded real-expert run. Invoke through launch.py with the specified venv."""
import os, pathlib, json, hashlib, struct, subprocess, time, traceback, sys, shutil
BASE=pathlib.Path(__file__).resolve().parent
OUT=BASE/'results';OUT.mkdir(exist_ok=True)
SRC=OUT/'sources';SRC.mkdir(exist_ok=True)
def js(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False))
def sha(b):return hashlib.sha256(b).hexdigest()
PKG=pathlib.Path('/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/lib/python3.10/site-packages/sglang')
source_paths=['srt/layers/moe/fused_moe_triton/mxfp4_moe_sm120_triton.py','srt/layers/quantization/mxfp4_marlin_moe.py','srt/layers/moe/fused_moe_triton/layer.py','srt/models/deepseek_v4.py','srt/utils/offloader.py']
source_manifest=[]
for f in source_paths:
    b=(PKG/f).read_bytes(); (SRC/pathlib.Path(f).name).write_bytes(b)
    source_manifest.append(dict(path=str(PKG/f),sha256=sha(b)))
js('source_hashes.json',source_manifest)
free=subprocess.check_output(['nvidia-smi','--query-gpu=index,name,memory.free,memory.total','--format=csv,noheader'],text=True)
(OUT/'gpu_before.txt').write_text(free)
assert int(free.splitlines()[0].split(',')[-2].strip().split()[0])>=4096,free
import numpy as np
import torch, triton, importlib.metadata
from reference import E8,bf,reference,metrics
from sglang.srt.layers.moe.fused_moe_triton.mxfp4_moe_sm120_triton import mxfp4_moe_forward_triton as tested
import inspect
assert sha(pathlib.Path(inspect.getsourcefile(tested)).read_bytes())==source_manifest[0]['sha256']
torch.set_num_threads(4);torch.set_num_interop_threads(4)
torch.cuda.set_per_process_memory_fraction(2*1024**3/torch.cuda.get_device_properties(0).total_memory)
torch.cuda.reset_peak_memory_stats()
js('environment.json',dict(python=sys.version,executable=sys.executable,torch=torch.__version__,cuda=torch.version.cuda,triton=triton.__version__,sglang=importlib.metadata.version('sglang'),device=torch.cuda.get_device_name(),capability=torch.cuda.get_device_capability(),affinity=list(os.sched_getaffinity(0)),pid=os.getpid(),threads=torch.get_num_threads(),start=time.time(),protocol_sha256=sha((BASE/'PROTOCOL.md').read_bytes())))
CACHE=pathlib.Path('/home/ubuntu/.cache/huggingface/hub/models--deepseek-ai--DeepSeek-V4-Flash-0731/snapshots/7872f01b1d1fe23eabc4c98b48bffcef5a386062')
index_b=(CACHE/'model.safetensors.index.json').read_bytes(); index=json.loads(index_b)['weight_map']
(OUT/'checkpoint_config.json').write_bytes((CACHE/'config.json').read_bytes())
js('checkpoint_provenance.json',dict(cache=str(CACHE),index_sha256=sha(index_b),note='Only selected payload ranges hashed; no full-shard/full-checkpoint SHA verification.'))
raw={};manifest=[]; headers={}
for e,orig in enumerate([0,1,7,42,128,255]):
 for w in ['w1','w3','w2']:
  for kind in ['weight','scale']:
   key=f'layers.0.ffn.experts.{orig}.{w}.{kind}';file=index[key]
   with open(CACHE/file,'rb') as f:
    if file not in headers:
     n=struct.unpack('<Q',f.read(8))[0]; hb=f.read(n);headers[file]=(n,json.loads(hb),sha(hb))
    n,h,hh=headers[file];entry=h[key];start,end=entry['data_offsets']
    assert entry['dtype']==('I8' if kind=='weight' else 'F8_E8M0')
    f.seek(8+n+start);b=f.read(end-start);assert len(b)==end-start
   a=np.frombuffer(b,dtype=np.uint8).reshape(entry['shape']).copy();raw[f'{e}_{w}_{kind}']=a
   record=dict(local_expert=e,checkpoint_expert=orig,key=key,shard=file,header_sha256=hh,absolute_offset=8+n+start,**entry,raw_sha256=sha(b))
   if kind=='scale':
    assert not np.any(a==255),'NaN E8M0 byte'
    native=torch.from_numpy(a.copy()).view(torch.float8_e8m0fnu).float().numpy()
    assert np.array_equal(native,E8[a].astype(np.float32))
    record.update(byte_min=int(a.min()),byte_max=int(a.max()),scale_min=float(E8[a].min()),scale_max=float(E8[a].max()))
   manifest.append(record)
np.savez(OUT/'raw_checkpoint.npz',**raw);js('selected_tensors.json',manifest)
def assembly(H,I):
 p13=np.stack([np.concatenate([raw[f'{e}_w1_weight'][:I,:H//2],raw[f'{e}_w3_weight'][:I,:H//2]],axis=0) for e in range(6)])
 p2=np.stack([raw[f'{e}_w2_weight'][:H,:I//2] for e in range(6)])
 s13=np.stack([np.concatenate([raw[f'{e}_w1_scale'][:I,:H//32],raw[f'{e}_w3_scale'][:I,:H//32]],axis=0) for e in range(6)])
 s2=np.stack([raw[f'{e}_w2_scale'][:H,:I//32] for e in range(6)])
 # Match native checkpoint dtype conversion; do not numerically cast byte exponents.
 return [torch.from_numpy(a).view(torch.int8) for a in [p13,p2]]+[torch.from_numpy(a).view(torch.float8_e8m0fnu).float() for a in [s13,s2]]
rng=np.random.Generator(np.random.PCG64(20260909))
x=bf(rng.normal(0,.01,(8,4096)))
ids=np.array([[(s+m)%6 for s in range(6)] for m in range(8)],dtype=np.int32)
routes=np.array([[((s+m)%6+1)/21 for s in range(6)] for m in range(8)],dtype=np.float32)
results={};saved={};layout={}
def case(name,H,I,M,ii=None,rr=None,limit=10.,weights=None):
    print('CASE',name,flush=True)
    ci=ids[:M].copy() if ii is None else ii.copy();cr=routes[:M].copy() if rr is None else rr.copy();cx=x[:M,:H].copy()
    xx=torch.from_numpy(cx).to(device='cuda',dtype=torch.bfloat16);ti=torch.from_numpy(ci).cuda();tw=torch.from_numpy(cr).cuda()
    t=time.monotonic()
    with torch.inference_mode():
        y=tested(xx,*weights,ti,tw,H,I,routed_scaling_factor=1.5,clamp_limit=limit)
    torch.cuda.synchronize();y=y.float().cpu().numpy()
    ref=reference(cx,ci,cr,raw,H,I,limit,1.5)
    np.savez(OUT/f'{name}.npz',input=cx.astype(np.float32),ids=ci,routing=cr,output=y,**ref)
    # Only smoke is judged here; full analysis occurs after exit and transfer.
    results[name]=dict(H=H,I=I,M=M,clamp=limit,factor=1.5,observed_seconds_including_reference=time.monotonic()-t)
    saved[name]=y
    if name=='smoke':
        met=metrics(y,ref['reference']);js('smoke_gate.json',met)
        assert met['pass_criteria'],str(met)
    return (xx,ti,tw)
small=[v.cuda() for v in assembly(128,64)]
case('smoke',128,64,1,weights=small)
del small;torch.cuda.empty_cache()
full=assembly(4096,2048)
np.savez(OUT/'assembled.npz',**{k:v.view(torch.uint8).numpy() if v.dtype==torch.int8 else v.numpy() for k,v in zip(['w13_packed','w2_packed','w13_scale','w2_scale'],full)})
for k,v in zip(['w13_packed','w2_packed','w13_scale','w2_scale'],full):
 layout[k]=dict(shape=list(v.shape),stride=list(v.stride()),dtype=str(v.dtype),sha256=sha(v.numpy().tobytes()))
js('layout.json',layout)
full=[v.cuda() for v in full]
case('main_m1',4096,2048,1,weights=full)
main_args=case('main_m8',4096,2048,8,weights=full)
for e in range(6):
 case(f'only_expert_{e}',4096,2048,8,rr=(ids==e).astype(np.float32),weights=full)
case('zero_routes',4096,2048,8,rr=np.zeros_like(routes),weights=full)
ci=ids.copy();ci[:,2]=-1
case('padded_slot',4096,2048,8,ii=ci,weights=full)
cr=routes.copy();cr[:,2]=0
case('zero_slot',4096,2048,8,rr=cr,weights=full)
case('permuted_slots',4096,2048,8,ii=ids[:,::-1],rr=routes[:,::-1],weights=full)
case('unclamped',4096,2048,8,limit=None,weights=full)
case('active_clamp',4096,2048,8,limit=.005,weights=full)
js('cases.json',results)
xx,ti,tw=main_args
try:
 with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA],record_shapes=True) as prof:
  with torch.inference_mode():py=tested(xx,*full,ti,tw,4096,2048,routed_scaling_factor=1.5,clamp_limit=10.)
  torch.cuda.synchronize()
 prof.export_chrome_trace(str(OUT/'profile.json'))
 np.save(OUT/'profile_output.npy',py.float().cpu().numpy())
except Exception:
 (OUT/'profiler_error.txt').write_text(traceback.format_exc())
try:
 from sglang.srt.utils.offloader import OffloaderV1
 class Tiny(torch.nn.Module):
  def __init__(self,params):
   super().__init__()
   for key,val in zip(['w13','w2','s13','s2'],params):self.register_parameter(key,torch.nn.Parameter(val,requires_grad=False))
  def forward(self,a,i,w):
   return tested(a,self.w13,self.w2,self.s13,self.s2,i,w,4096,2048,routed_scaling_factor=1.5,clamp_limit=10.)
 mod=Tiny(full);del full
 off=OffloaderV1(cpu_offload_max_bytes=512*1024**2)
 mod=off.wrap_modules(iter([mod]))[0]
 before={k:dict(device=str(p.device),pinned=p.is_pinned(),shape=list(p.shape)) for k,p in mod.named_parameters()}
 assert all(p.device.type=='cpu' for p in mod.parameters())
 with torch.inference_mode():oy=mod(xx,ti,tw)
 torch.cuda.synchronize();np.save(OUT/'offloader_output.npy',oy.float().cpu().numpy())
 js('offloader.json',dict(cpu_offload_bytes=off._cpu_offload_bytes,parameters=before,after={k:str(p.device) for k,p in mod.named_parameters()}))
except Exception:
 (OUT/'offloader_error.txt').write_text(traceback.format_exc())
js('memory.json',dict(allocated_peak_bytes=torch.cuda.max_memory_allocated(),reserved_peak_bytes=torch.cuda.max_memory_reserved(),finish=time.time()))
print('RUN COMPLETE',flush=True)
