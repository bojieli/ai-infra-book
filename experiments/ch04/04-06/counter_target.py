"""Profile one projection after controlled predecessor accesses, preserving normal caches."""
import argparse,hashlib,json
from pathlib import Path
import torch
from projection import fixture
p=argparse.ArgumentParser();p.add_argument('--m',type=int,choices=[1,256],required=True);p.add_argument('--mode',choices=['reused','rotating'],required=True);args=p.parse_args()
torch.set_num_threads(1);torch.backends.cuda.matmul.allow_tf32=False
torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction=False
bcpu=fixture(4096**2,10000).reshape(4096,4096)
acpu=fixture(args.m*4096,20000).reshape(args.m,4096)
ref=acpu.double()@bcpu.double()
a=acpu.cuda();weights=[bcpu.cuda().clone() for _ in range(16)]
c=torch.empty((args.m,4096),device='cuda',dtype=torch.bfloat16)
for _ in range(10):torch.mm(a,weights[0],out=c)
# Target is buffer 0 in both arms. Rotation accesses 480 MiB of other weights first.
for i in range(1,16):torch.mm(a,weights[0 if args.mode=='reused' else i],out=c)
torch.cuda.synchronize()
torch.cuda.profiler.start()
torch.mm(a,weights[0],out=c)
torch.cuda.synchronize();torch.cuda.profiler.stop()
actual=c.float().cpu().double();torch.testing.assert_close(actual,ref,atol=.01,rtol=.01)
print(json.dumps(dict(m=args.m,mode=args.mode,max_abs_error=float((actual-ref).abs().max()),
 input_sha256=hashlib.sha256(acpu.float().numpy().tobytes()).hexdigest(),
 weight_sha256=hashlib.sha256(bcpu.float().numpy().tobytes()).hexdigest(),torch=torch.__version__)))
