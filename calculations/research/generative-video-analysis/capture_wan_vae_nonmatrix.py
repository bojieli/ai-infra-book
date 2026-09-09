"""Execute pinned official decoder on meta; archive scalar/copy dispatcher boundaries.
No checkpoint weights, pixel tensor storage, CUDA timing or HBM measurements.
"""
import hashlib, importlib.util, inspect, json
from collections import defaultdict
from pathlib import Path
import torch
from torch.utils._python_dispatch import TorchDispatchMode
from torch.utils._pytree import tree_leaves
root=Path(__file__).resolve().parent
source=root/'Wan-Video--Wan2.2/wan/modules/vae2_2.py'
spec=importlib.util.spec_from_file_location('wan_vae_fixed',source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with torch.device('meta'):
    model=m.WanVAE_(dim=160,z_dim=48,dim_mult=[1,2,4,4],temperal_downsample=[False,True,True]).eval()

def capture(t,h,w):
    rows=defaultdict(lambda:dict(calls=0,input_elements=0,output_elements=0,reduction_input_elements=0))
    class Trace(TorchDispatchMode):
        def __torch_dispatch__(self,func,types,args=(),kwargs=None):
            kwargs=kwargs or {};out=func(*args,**kwargs)
            line=next((f.lineno for f in inspect.stack() if f.filename==str(source)),0)
            key=f'{func}|{line}'
            r=rows[key];r['calls']+=1
            r['input_elements']+=sum(x.numel() for x in tree_leaves((args,kwargs)) if isinstance(x,torch.Tensor))
            r['output_elements']+=sum(x.numel() for x in tree_leaves(out) if isinstance(x,torch.Tensor))
            if str(func)=='aten.linalg_vector_norm.default':r['reduction_input_elements']+=args[0].numel()
            return out
    with torch.no_grad(),Trace():
        z=torch.empty(1,48,t,h,w,device='meta')
        scale=[torch.empty(48,device='meta'),torch.empty(48,device='meta')]
        out=model.decode(z,scale).float().clamp_(-1,1).squeeze(0)
    return dict(shape=[t,h,w],output_shape=list(out.shape),rows=dict(sorted(rows.items())))
# Each known primitive element count is degree <=2 in temporal length and each
# spatial axis: conv padding affine; full attention quadratic; growing cat sum quadratic.
samples=[capture(t,h,w) for t in (1,2,3,4) for h in (2,3,4) for w in (2,3,4)]
validation=[capture(5,5,6),capture(1,5,6),capture(7,2,5)]
result=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),torch_version=torch.__version__,samples=samples,validation=validation)
(root/'wan-vae-nonmatrix-meta.json').write_text(json.dumps(result,indent=2)+'\n')
print('captured',len(samples),'validation',len(validation),'ops',sorted(set(k.split('|')[0] for s in samples for k in s['rows'])))
