#include <tvm/ffi/container/tensor.h>
#include <tvm/ffi/dtype.h>
#include <tvm/ffi/error.h>
#include <tvm/ffi/extra/c_env_api.h>
#include <tvm/ffi/function.h>

#include "/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/lib/python3.10/site-packages/sglang/jit_kernel/csrc/deepseek_v4/rope.cuh"
TVM_FFI_DLL_EXPORT_TYPED_FUNC(forward, (FusedQKRopeKernel<true>::forward));
