"""Check the finite-only RNE bit boundary against independent native BF16 conversion."""
import argparse,hashlib,json
from pathlib import Path
import torch
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise RuntimeError('Use fresh output directory')
a.output.mkdir(parents=True)
torch.manual_seed(504777)
# Every BF16 upper word at its FP32 midpoint, and both adjacent representable FP32 values.
upper=torch.arange(65536,dtype=torch.int64)<<16
bits=torch.cat([upper+32767,upper+32768,upper+32769,torch.randint(0,2**32,(200000,),dtype=torch.int64)]).to(torch.int32)
x=bits.view(torch.float32);x=x[torch.isfinite(x)].contiguous()
expected=x.bfloat16().float().view(torch.int32)
def rne(v):
 b=v.view(torch.int32)
 return ((b+32767+((b>>16)&1))&-65536).view(torch.float32)
compiled=torch.compile(rne,fullgraph=True)
actual=compiled(x.cuda()).cpu().view(torch.int32)
assert torch.equal(actual,expected)
(a.output/'check.json').write_text(json.dumps(dict(elements=x.numel(),bitwise_match=True,scope='Finite FP32: all BF16 upper words midpoint +/- one FP32 ULP, plus 200000 random bit patterns; nonfinite inputs excluded. Overflow to BF16 infinity and signed zero compared by bits.',input_sha256=hashlib.sha256(x.numpy().tobytes()).hexdigest(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),torch=torch.__version__),indent=2)+'\n')
torch.save(dict(input=x,expected_bits=expected,actual_bits=actual),a.output/'tensors.pt')
print('PASS',x.numel(),'finite rounding cases')
