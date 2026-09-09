"""Read-only environment preflight; never initializes CUDA or MPS."""
import os, sys, json, platform, resource, importlib.util
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
 os.environ[key]='1'
import torch
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
data=dict(platform=platform.platform(),machine=platform.machine(),python=sys.version,
 executable=sys.executable,torch=torch.__version__,torch_cuda_build=torch.version.cuda,
 cuda_available=torch.cuda.is_available(),nccl_available=torch.distributed.is_nccl_available(),
 gloo_available=torch.distributed.is_gloo_available(),numpy_installed=importlib.util.find_spec('numpy') is not None,
 megatron_installed=importlib.util.find_spec('megatron') is not None,
 intraop_threads=torch.get_num_threads(),interop_threads=torch.get_num_interop_threads(),
 environment={k:os.environ[k] for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS')},
 max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
 coexistence='Shared Mac with other sessions; no exclusive CPU reservation; no performance ranking.',
 status='BLOCKED_CPU_ONLY',reason='Pinned Megatron Core schedules allocate device=cuda unconditionally; no device execution attempted.')
print(json.dumps(data,indent=2))
sys.exit(2)
