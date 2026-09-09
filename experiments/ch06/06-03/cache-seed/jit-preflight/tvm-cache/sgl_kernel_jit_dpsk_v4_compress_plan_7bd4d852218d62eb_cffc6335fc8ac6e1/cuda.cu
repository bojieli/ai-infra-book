#include <tvm/ffi/container/tensor.h>
#include <tvm/ffi/dtype.h>
#include <tvm/ffi/error.h>
#include <tvm/ffi/extra/c_env_api.h>
#include <tvm/ffi/function.h>

#include "/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/lib/python3.10/site-packages/sglang/jit_kernel/csrc/deepseek_v4/c_plan.cuh"
TVM_FFI_DLL_EXPORT_TYPED_FUNC(plan_prefill, (plan_compress_prefill));
TVM_FFI_DLL_EXPORT_TYPED_FUNC(plan_decode, (plan_compress_decode));
TVM_FFI_DLL_EXPORT_TYPED_FUNC(plan_prefill_legacy, (plan_compress_prefill_legacy));
TVM_FFI_DLL_EXPORT_TYPED_FUNC(plan_decode_legacy, (plan_compress_decode_legacy));
