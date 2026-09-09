#include <tvm/ffi/container/tensor.h>
#include <tvm/ffi/dtype.h>
#include <tvm/ffi/error.h>
#include <tvm/ffi/extra/c_env_api.h>
#include <tvm/ffi/function.h>

#include "/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/lib/python3.10/site-packages/sglang/jit_kernel/csrc/deepseek_v4/c4_v2.cuh"
TVM_FFI_DLL_EXPORT_TYPED_FUNC(decode, (FlashCompress4Kernel<512, fp32_t, fp32_t, true>::run_decode));
TVM_FFI_DLL_EXPORT_TYPED_FUNC(prefill, (FlashCompress4Kernel<512, fp32_t, fp32_t, true>::run_prefill));
