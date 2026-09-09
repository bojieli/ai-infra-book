"""Meta-only execution of pinned Wan VAE decode; no weights/pixels allocated."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import torch

root=Path(__file__).resolve().parent
path=root/'Wan-Video--Wan2.2/wan/modules/vae2_2.py'
spec=importlib.util.spec_from_file_location('official_wan_vae',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
parser=argparse.ArgumentParser()
parser.add_argument('--latent-frames',type=int,default=3)
parser.add_argument('--latent-height',type=int,default=2)
parser.add_argument('--latent-width',type=int,default=3)
parser.add_argument('--output',default='wan-vae-decode-meta.json')
args=parser.parse_args()
shape=[1,48,args.latent_frames,args.latent_height,args.latent_width]
events=[];current={'chunk':-1}
with torch.device('meta'):
    model=module.WanVAE_(dim=160,z_dim=48,dim_mult=[1,2,4,4],temperal_downsample=[False,True,True]).eval()

def enter(module,args,kwargs):
    current['chunk']+=1
model.decoder.register_forward_pre_hook(enter,with_kwargs=True)
def hook(name):
    def record(mod,args,out):
        x=args[0]
        row=dict(name=name,kind=type(mod).__name__,chunk=current['chunk'],input_shape=list(x.shape),output_shape=list(out.shape))
        if isinstance(mod,(torch.nn.Conv2d,torch.nn.Conv3d)):
            row.update(weight_shape=list(mod.weight.shape),kernel=list(mod.kernel_size),stride=list(mod.stride),
                padding=list(mod.padding),dilation=list(mod.dilation),groups=mod.groups,
                causal_padding=list(mod._padding) if hasattr(mod,'_padding') else None,
                cache_shape=list(args[1].shape) if len(args)>1 and isinstance(args[1],torch.Tensor) else None,
                bias=mod.bias is not None)
        events.append(row)
    return record
for name,layer in model.named_modules():
    if isinstance(layer,(torch.nn.Conv2d,torch.nn.Conv3d)):
        layer.register_forward_hook(hook(name))
original=torch.nn.functional.scaled_dot_product_attention
def attention(q,k,v,*args,**kwargs):
    events.append(dict(name='decoder.spatial_attention',kind='attention',chunk=current['chunk'],
        q_shape=list(q.shape),k_shape=list(k.shape),v_shape=list(v.shape),causal=kwargs.get('is_causal',False)))
    return original(q,k,v,*args,**kwargs)
torch.nn.functional.scaled_dot_product_attention=attention
with torch.no_grad():
    output=model.decode(torch.empty(*shape,device='meta'),[0.,1.])
result=dict(torch_version=torch.__version__,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    input_shape=shape,output_shape=list(output.shape),events=events,
    learned_parameters=sum(p.numel() for p in model.parameters()),
    decoder_parameters=sum(p.numel() for p in model.decoder.parameters())+sum(p.numel() for p in model.conv2.parameters()))
(root/args.output).write_text(json.dumps(result,indent=2)+'\n')
print('events',len(events),'output',list(output.shape))
