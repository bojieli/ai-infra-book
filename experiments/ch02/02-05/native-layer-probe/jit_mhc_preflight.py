"""Compile original mHC TileLang function using an include-only CCCL overlay."""
from pathlib import Path
import os,json,time,hashlib
B=Path(__file__).resolve().parent;out=B/'jit-mhc-preflight';out.mkdir(exist_ok=False)
cccl=Path('/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/lib/python3.10/site-packages/nvidia/cu13/include/cccl')
inc=B/'include-overlay';inc.mkdir(exist_ok=True);(inc/'cccl').symlink_to(cccl,target_is_directory=True)
os.environ.update(CUDA_HOME='/home/ubuntu/ai-infra-book-experiments/tools/flashinfer-cuda130/nvidia/cu13',CPATH=str(inc)+':'+str(cccl),TVM_FFI_CACHE_DIR=str(out/'tvm-cache'),TILELANG_CACHE_DIR=str(out/'tilelang-cache'),TILELANG_TMP_DIR=str(out/'tmp'),MAX_JOBS='4',OMP_NUM_THREADS='4')
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[4:8])
import torch
from sglang.srt.layers.mhc import hc_split_sinkhorn_kernel
start=time.time();k=hc_split_sinkhorn_kernel(4,20,1e-6)
result=dict(status='original_mhc_compiled_only_no_model_or_numerical_check',elapsed=time.time()-start,torch=torch.__version__,include_overlay=str(inc),cccl_target=str(cccl),cpath=os.environ['CPATH'],files=[])
for p in sorted(out.rglob('*')):
 if p.is_file():result['files'].append(dict(path=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
