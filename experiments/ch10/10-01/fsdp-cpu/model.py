import torch
class FFN(torch.nn.Module):
 def __init__(self):
  super().__init__();self.gate=torch.nn.Linear(512,1536,bias=False);self.up=torch.nn.Linear(512,1536,bias=False);self.down=torch.nn.Linear(1536,512,bias=False);self.observer=None
 def forward(self,x):
  if self.observer:self.observer()
  return self.down(torch.nn.functional.silu(self.gate(x))*self.up(x))
def data(step):
 g=torch.Generator().manual_seed(1002+step)
 return torch.randn(32,512,generator=g),torch.randn(32,512,generator=g)
