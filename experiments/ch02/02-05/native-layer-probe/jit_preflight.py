"""Compile original native compression-plan module, no model or inference."""
from pathlib import Path
import os,json,hashlib,time
B=Path(__file__).resolve().parent
out=B/'jit-preflight';out.mkdir(exist_ok=False)
cccl='/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/lib/python3.10/site-packages/nvidia/cu13/include/cccl'
os.environ.update(CUDA_HOME='/home/ubuntu/ai-infra-book-experiments/tools/flashinfer-cuda130/nvidia/cu13',CPATH=cccl,TVM_FFI_CACHE_DIR=str(out/'tvm-cache'),MAX_JOBS='4',OMP_NUM_THREADS='4')
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[4:8])
import torch
from sglang.jit_kernel.dsv4.compress import _jit_compress_plan_module
start=time.time();module=_jit_compress_plan_module()
result=dict(status='original_compress_plan_compiled_only_no_inference',elapsed=time.time()-start,torch=torch.__version__,cuda_home=os.environ['CUDA_HOME'],cpath=cccl,cache=os.environ['TVM_FFI_CACHE_DIR'],files=[])
for p in sorted((out/'tvm-cache').rglob('*')):
 if p.is_file():result['files'].append(dict(path=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
for name in ['nv/target','nv/detail/__target_macros']:
 p=Path(cccl)/name
 if p.exists():result.setdefault('headers',[]).append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
