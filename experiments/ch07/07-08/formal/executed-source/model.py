"""Standalone byte-level causal decoder, deliberately small and entirely real Torch ops."""
import torch
from torch import nn
from torch.nn import functional as F
class Block(nn.Module):
 def __init__(self,d):
  super().__init__();self.d=d;self.ln1=nn.LayerNorm(d);self.qkv=nn.Linear(d,3*d);self.proj=nn.Linear(d,d);self.ln2=nn.LayerNorm(d);self.ff1=nn.Linear(d,4*d);self.ff2=nn.Linear(4*d,d)
 def forward(self,x):
  b,t,d=x.shape;q,k,v=self.qkv(self.ln1(x)).reshape(b,t,3,4,d//4).permute(2,0,3,1,4).unbind(0)
  z=F.scaled_dot_product_attention(q,k,v,is_causal=True,dropout_p=0).transpose(1,2).reshape(b,t,d)
  x=x+self.proj(z);return x+self.ff2(F.gelu(self.ff1(self.ln2(x))))
class Model(nn.Module):
 def __init__(self,width):
  super().__init__();self.width=width;self.emb=nn.Embedding(256,width);self.pos=nn.Embedding(128,width);self.blocks=nn.ModuleList([Block(width) for _ in range(2)]);self.norm=nn.LayerNorm(width)
  for m in self.modules():
   if isinstance(m,(nn.Linear,nn.Embedding)):nn.init.normal_(m.weight,mean=0,std=.02)
   if isinstance(m,nn.Linear) and m.bias is not None:nn.init.zeros_(m.bias)
 def forward(self,x):
  z=self.emb(x)+self.pos(torch.arange(x.shape[1],device=x.device))
  for block in self.blocks:z=block(z)
  return F.linear(self.norm(z),self.emb.weight)
