#include <math_constants.h>
#include <tl_templates/cuda/gemm.h>
#include <tl_templates/cuda/copy.h>
#include <tl_templates/cuda/reduce.h>
#include <tl_templates/cuda/ldsm.h>
#include <tl_templates/cuda/threadblock_swizzle.h>
#include <tl_templates/cuda/debug.h>
#ifdef ENABLE_BF16
#include <tl_templates/cuda/cuda_bf16_fallbacks.cuh>
#endif

extern "C" __global__ void hc_split_sinkhorn_kernel__kernel(float* comb, const float* hc_base, const float* hc_scale, const float* mixes, float* post, float* pre, int n);
extern "C" __global__ void __launch_bounds__(64, 1) hc_split_sinkhorn_kernel__kernel(float* comb, const float* hc_base, const float* hc_scale, const float* mixes, float* post, float* pre, int n) {
  extern __shared__ __align__(1024) float mixes_shared[];
  float comb_frag[1];
  float row_max[1];
  float row_sum[1];
  float col_sum[1];
  cudaGridDependencySynchronize();
  if (((int)threadIdx.x) < 24) {
    mixes_shared[((int)threadIdx.x)] = mixes[((((int64_t)((int)blockIdx.x)) * (int64_t)24) + ((int64_t)((int)threadIdx.x)))];
  }
  __syncthreads();
  if (((int)threadIdx.x) < 4) {
    pre[((((int64_t)((int)blockIdx.x)) * (int64_t)4) + ((int64_t)((int)threadIdx.x)))] = ((0x1p+0f/*1.000000e+00*/ / (0x1p+0f/*1.000000e+00*/ + expf((0x0p+0f/*0.000000e+00*/ - ((mixes_shared[((int)threadIdx.x)] * hc_scale[0]) + hc_base[((int)threadIdx.x)]))))) + 0x1.0c6f7a0b5ed8dp-20f/*1.000000e-06*/);
    post[((((int64_t)((int)blockIdx.x)) * (int64_t)4) + ((int64_t)((int)threadIdx.x)))] = (0x1p+1f/*2.000000e+00*/ * (0x1p+0f/*1.000000e+00*/ / (0x1p+0f/*1.000000e+00*/ + expf((0x0p+0f/*0.000000e+00*/ - ((mixes_shared[(((int)threadIdx.x) + 4)] * hc_scale[1]) + hc_base[(((int)threadIdx.x) + 4)]))))));
  }
  comb_frag[0] = ((mixes_shared[((((int)threadIdx.x) & 15) + 8)] * hc_scale[2]) + hc_base[((((int)threadIdx.x) & 15) + 8)]);
  row_max[0] = -CUDART_INF_F;
  row_max[0] = max(row_max[0], comb_frag[0]);
  row_max[0] = tl::AllReduce<tl::MaxOp, 4, 1, 0, tl::NamedBarrier<64>>::run(row_max[0]);
  comb_frag[0] = expf((comb_frag[0] - row_max[0]));
  row_sum[0] = 0x0p+0f/*0.000000e+00*/;
  row_sum[0] = (row_sum[0] + comb_frag[0]);
  row_sum[0] = tl::AllReduce<tl::SumOp, 4, 1, 0, tl::NamedBarrier<64>>::run(row_sum[0]);
  comb_frag[0] = ((comb_frag[0] / row_sum[0]) + 0x1.0c6f7a0b5ed8dp-20f/*1.000000e-06*/);
  col_sum[0] = 0x0p+0f/*0.000000e+00*/;
  col_sum[0] = (col_sum[0] + comb_frag[0]);
  col_sum[0] = tl::AllReduce<tl::SumOp, 16, 4, 0, tl::NamedBarrier<64>>::run(col_sum[0]);
  comb_frag[0] = (comb_frag[0] / (col_sum[0] + 0x1.0c6f7a0b5ed8dp-20f/*1.000000e-06*/));
  for (int __1 = 0; __1 < 19; ++__1) {
    row_sum[0] = 0x0p+0f/*0.000000e+00*/;
    row_sum[0] = (row_sum[0] + comb_frag[0]);
    row_sum[0] = tl::AllReduce<tl::SumOp, 4, 1, 0, tl::NamedBarrier<64>>::run(row_sum[0]);
    comb_frag[0] = (comb_frag[0] / (row_sum[0] + 0x1.0c6f7a0b5ed8dp-20f/*1.000000e-06*/));
    col_sum[0] = 0x0p+0f/*0.000000e+00*/;
    col_sum[0] = (col_sum[0] + comb_frag[0]);
    col_sum[0] = tl::AllReduce<tl::SumOp, 16, 4, 0, tl::NamedBarrier<64>>::run(col_sum[0]);
    comb_frag[0] = (comb_frag[0] / (col_sum[0] + 0x1.0c6f7a0b5ed8dp-20f/*1.000000e-06*/));
  }
  if ((((int)threadIdx.x) >> 4) == 0) {
    comb[((((int64_t)((int)blockIdx.x)) * (int64_t)16) + (((int64_t)((int)threadIdx.x)) & (int64_t)15))] = comb_frag[0];
  }
  cudaTriggerProgrammaticLaunchCompletion();
}

