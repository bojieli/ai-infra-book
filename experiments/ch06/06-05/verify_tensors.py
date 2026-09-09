"""Regenerate dyadic inputs and independently recompute saved FP64 reference on CPU."""
from pathlib import Path
import torch,json,hashlib,ctypes
B=Path(__file__).resolve().parent
torch.set_num_threads(2);torch.set_num_interop_threads(2)
def sha(x):
 x=x.contiguous();return hashlib.sha256((ctypes.c_char*(x.numel()*x.element_size())).from_address(x.data_ptr())).hexdigest()
checks=[]
for dataset in ['smoke','formal']:
 for rank in range(4):
  p=B/dataset/f'rank{rank}-tensors.pt';d=torch.load(p,map_location='cpu',weights_only=True);identity=json.loads((p.parent/f'rank{rank}-identity.json').read_text())
  torch.manual_seed(605+rank);a=torch.randint(-4,5,(16,4096),dtype=torch.int8).float()/16;w=torch.randint(-4,5,(4096,4096),dtype=torch.int8).float()/16;ref=a.double()@w.double()
  assert sha(a)==identity['hashes']['a'] and sha(w)==identity['hashes']['w']
  assert torch.equal(a,d['a']) and torch.equal(ref,d['reference']) and torch.equal(d['actual'].double(),ref)
  assert sha(ref)==identity['hashes']['reference']
  checks.append(dict(dataset=dataset,rank=rank,passed=True,actual_sha256=sha(d['actual']),reference_sha256=sha(ref)))
(B/'tensor-checks.json').write_text(json.dumps(dict(passed=True,checks=checks,torch=torch.__version__),indent=2)+'\n');print('8 full saved matrices and regenerated inputs passed exactly')
