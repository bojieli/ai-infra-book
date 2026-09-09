#include <tl_templates/cuda/gemm.h>
#include <tl_templates/cuda/copy.h>
#include <tl_templates/cuda/reduce.h>
#include <tl_templates/cuda/ldsm.h>
#include <tl_templates/cuda/threadblock_swizzle.h>
#include <tl_templates/cuda/debug.h>
#ifdef ENABLE_BF16
#include <tl_templates/cuda/cuda_bf16_fallbacks.cuh>
#endif

extern "C" __global__ void mhc_post_tilelang_kernel(const float* a, const bfloat16_t* b, const float* c, const bfloat16_t* d, bfloat16_t* x, int num_tokens);
extern "C" __global__ void __launch_bounds__(128, 1) mhc_post_tilelang_kernel(const float* a, const bfloat16_t* b, const float* c, const bfloat16_t* d, bfloat16_t* x, int num_tokens) {
  extern __shared__ __align__(1024) uchar buf_dyn_shmem[];
  float a_local[16];
  float c_local[4];
  float b_local[32];
  float d_local[8];
  float x_local[32];
  bfloat16_t b_shared_local_cast[4];
  bfloat16_t d_shared_local_cast_1[4];
  bfloat16_t x_shared_local_cast_2[4];
  bfloat16_t b_shared_local_cast_1[4];
  bfloat16_t d_shared_local_cast_1_1[4];
  bfloat16_t x_shared_local_cast_2_1[4];
  cudaGridDependencySynchronize();
  #pragma unroll
  for (int i = 0; i < 2; ++i) {
    *(ulonglong4*)(a_local + (i * 8)) = tl::load_global_256(&(*(ulonglong4*)(a + ((((int64_t)((int)blockIdx.x)) * (int64_t)16) + (((int64_t)i) * (int64_t)8)))));
  }
  *(float4*)(c_local + 0) = *(float4*)(c + (((int64_t)((int)blockIdx.x)) * (int64_t)4));
  #pragma unroll
  for (int i_1 = 0; i_1 < 4; ++i_1) {
    tl::cp_async_gs<16>((&(((bfloat16_t*)buf_dyn_shmem)[((i_1 * 1024) + (((int)threadIdx.x) * 8))])), (&(b[(((((int64_t)((int)blockIdx.x)) * (int64_t)16384) + (((int64_t)i_1) * (int64_t)4096)) + (((int64_t)((int)threadIdx.x)) * (int64_t)8))])));
  }
  tl::cp_async_commit();
  tl::cp_async_gs<16>((&(((bfloat16_t*)buf_dyn_shmem)[((((int)threadIdx.x) * 8) + 8192)])), (&(d[((((int64_t)((int)blockIdx.x)) * (int64_t)4096) + (((int64_t)((int)threadIdx.x)) * (int64_t)8))])));
  tl::cp_async_commit();
  #pragma unroll
  for (int i_2 = 0; i_2 < 4; ++i_2) {
    tl::cp_async_gs<16>((&(((bfloat16_t*)buf_dyn_shmem)[(((i_2 * 1024) + (((int)threadIdx.x) * 8)) + 4096)])), (&(b[((((((int64_t)((int)blockIdx.x)) * (int64_t)16384) + (((int64_t)i_2) * (int64_t)4096)) + (((int64_t)((int)threadIdx.x)) * (int64_t)8)) + (int64_t)1024)])));
  }
  tl::cp_async_commit();
  tl::cp_async_gs<16>((&(((bfloat16_t*)buf_dyn_shmem)[((((int)threadIdx.x) * 8) + 9216)])), (&(d[(((((int64_t)((int)blockIdx.x)) * (int64_t)4096) + (((int64_t)((int)threadIdx.x)) * (int64_t)8)) + (int64_t)1024)])));
  tl::cp_async_commit();
  for (int i0_h = 0; i0_h < 2; ++i0_h) {
    tl::cp_async_wait<1>();
    __syncthreads();
    #pragma unroll
    for (int i_3 = 0; i_3 < 8; ++i_3) {
      *(uint2*)(b_shared_local_cast + 0) = *(uint2*)(((bfloat16_t*)buf_dyn_shmem) + (((i0_h * 4096) + (i_3 * 512)) + (((int)threadIdx.x) * 4)));
      float4 __1;
      uint2 v_ = *(uint2*)(b_shared_local_cast + 0);
      ((float2*)(&__1))[0] = __bfloat1622float2((reinterpret_cast<__nv_bfloat162*>(&v_))[0]);
      ((float2*)(&__1))[1] = __bfloat1622float2((reinterpret_cast<__nv_bfloat162*>(&v_))[1]);
      *(float4*)(b_local + (i_3 * 4)) = __1;
    }
    __syncthreads();
    #pragma unroll
    for (int i_4 = 0; i_4 < 4; ++i_4) {
      tl::cp_async_gs<16>((&(((bfloat16_t*)buf_dyn_shmem)[(((i0_h * 4096) + (i_4 * 1024)) + (((int)threadIdx.x) * 8))])), (&(b[(((((((int64_t)((int)blockIdx.x)) * (int64_t)16384) + (((int64_t)i_4) * (int64_t)4096)) + (((int64_t)i0_h) * (int64_t)1024)) + (((int64_t)((int)threadIdx.x)) * (int64_t)8)) + (int64_t)2048)])));
    }
    tl::cp_async_commit();
    tl::cp_async_wait<1>();
    __syncthreads();
    #pragma unroll
    for (int i_5 = 0; i_5 < 2; ++i_5) {
      *(uint2*)(d_shared_local_cast_1 + 0) = *(uint2*)(((bfloat16_t*)buf_dyn_shmem) + ((((i0_h * 1024) + (i_5 * 512)) + (((int)threadIdx.x) * 4)) + 8192));
      float4 __2;
      uint2 v__1 = *(uint2*)(d_shared_local_cast_1 + 0);
      ((float2*)(&__2))[0] = __bfloat1622float2((reinterpret_cast<__nv_bfloat162*>(&v__1))[0]);
      ((float2*)(&__2))[1] = __bfloat1622float2((reinterpret_cast<__nv_bfloat162*>(&v__1))[1]);
      *(float4*)(d_local + (i_5 * 4)) = __2;
    }
    __syncthreads();
    tl::cp_async_gs<16>((&(((bfloat16_t*)buf_dyn_shmem)[(((i0_h * 1024) + (((int)threadIdx.x) * 8)) + 8192)])), (&(d[((((((int64_t)((int)blockIdx.x)) * (int64_t)4096) + (((int64_t)i0_h) * (int64_t)1024)) + (((int64_t)((int)threadIdx.x)) * (int64_t)8)) + (int64_t)2048)])));
    tl::cp_async_commit();
    #pragma unroll
    for (int i_6 = 0; i_6 < 32; ++i_6) {
      x_local[i_6] = (c_local[(i_6 >> 3)] * d_local[(i_6 & 7)]);
      for (int i_hci = 0; i_hci < 4; ++i_hci) {
        x_local[i_6] = (x_local[i_6] + (a_local[((i_hci * 4) + (i_6 >> 3))] * b_local[((i_hci * 8) + (i_6 & 7))]));
      }
    }
    #pragma unroll
    for (int i_7 = 0; i_7 < 8; ++i_7) {
      uint2 __3;
      float4 v__2 = *(float4*)(x_local + (i_7 * 4));
      (reinterpret_cast<__nv_bfloat162*>(&__3))[0] = __float22bfloat162_rn(((float2*)(&v__2))[0]);
      (reinterpret_cast<__nv_bfloat162*>(&__3))[1] = __float22bfloat162_rn(((float2*)(&v__2))[1]);
      *(uint2*)(x_shared_local_cast_2 + 0) = __3;
      *(uint2*)(((bfloat16_t*)buf_dyn_shmem) + (((i_7 * 512) + (((int)threadIdx.x) * 4)) + 10240)) = *(uint2*)(x_shared_local_cast_2 + 0);
    }
    __syncthreads();
    #pragma unroll
    for (int i_8 = 0; i_8 < 4; ++i_8) {
      *(uint4*)(x + ((((((int64_t)((int)blockIdx.x)) * (int64_t)16384) + (((int64_t)i_8) * (int64_t)4096)) + (((int64_t)i0_h) * (int64_t)1024)) + (((int64_t)((int)threadIdx.x)) * (int64_t)8))) = *(uint4*)(((bfloat16_t*)buf_dyn_shmem) + (((i_8 * 1024) + (((int)threadIdx.x) * 8)) + 10240));
    }
  }
  tl::cp_async_wait<1>();
  __syncthreads();
  #pragma unroll
  for (int i_9 = 0; i_9 < 8; ++i_9) {
    *(uint2*)(b_shared_local_cast_1 + 0) = *(uint2*)(((bfloat16_t*)buf_dyn_shmem) + ((i_9 * 512) + (((int)threadIdx.x) * 4)));
    float4 __4;
    uint2 v__3 = *(uint2*)(b_shared_local_cast_1 + 0);
    ((float2*)(&__4))[0] = __bfloat1622float2((reinterpret_cast<__nv_bfloat162*>(&v__3))[0]);
    ((float2*)(&__4))[1] = __bfloat1622float2((reinterpret_cast<__nv_bfloat162*>(&v__3))[1]);
    *(float4*)(b_local + (i_9 * 4)) = __4;
  }
  tl::cp_async_wait<1>();
  __syncthreads();
  #pragma unroll
  for (int i_10 = 0; i_10 < 2; ++i_10) {
    *(uint2*)(d_shared_local_cast_1_1 + 0) = *(uint2*)(((bfloat16_t*)buf_dyn_shmem) + (((i_10 * 512) + (((int)threadIdx.x) * 4)) + 8192));
    float4 __5;
    uint2 v__4 = *(uint2*)(d_shared_local_cast_1_1 + 0);
    ((float2*)(&__5))[0] = __bfloat1622float2((reinterpret_cast<__nv_bfloat162*>(&v__4))[0]);
    ((float2*)(&__5))[1] = __bfloat1622float2((reinterpret_cast<__nv_bfloat162*>(&v__4))[1]);
    *(float4*)(d_local + (i_10 * 4)) = __5;
  }
  #pragma unroll
  for (int i_11 = 0; i_11 < 32; ++i_11) {
    x_local[i_11] = (c_local[(i_11 >> 3)] * d_local[(i_11 & 7)]);
    for (int i_hci_1 = 0; i_hci_1 < 4; ++i_hci_1) {
      x_local[i_11] = (x_local[i_11] + (a_local[((i_hci_1 * 4) + (i_11 >> 3))] * b_local[((i_hci_1 * 8) + (i_11 & 7))]));
    }
  }
  #pragma unroll
  for (int i_12 = 0; i_12 < 8; ++i_12) {
    uint2 __6;
    float4 v__5 = *(float4*)(x_local + (i_12 * 4));
    (reinterpret_cast<__nv_bfloat162*>(&__6))[0] = __float22bfloat162_rn(((float2*)(&v__5))[0]);
    (reinterpret_cast<__nv_bfloat162*>(&__6))[1] = __float22bfloat162_rn(((float2*)(&v__5))[1]);
    *(uint2*)(x_shared_local_cast_2_1 + 0) = __6;
    *(uint2*)(((bfloat16_t*)buf_dyn_shmem) + (((i_12 * 512) + (((int)threadIdx.x) * 4)) + 10240)) = *(uint2*)(x_shared_local_cast_2_1 + 0);
  }
  __syncthreads();
  #pragma unroll
  for (int i_13 = 0; i_13 < 4; ++i_13) {
    *(uint4*)(x + ((((((int64_t)((int)blockIdx.x)) * (int64_t)16384) + (((int64_t)i_13) * (int64_t)4096)) + (((int64_t)((int)threadIdx.x)) * (int64_t)8)) + (int64_t)2048)) = *(uint4*)(((bfloat16_t*)buf_dyn_shmem) + (((i_13 * 1024) + (((int)threadIdx.x) * 8)) + 10240));
  }
  tl::cp_async_wait<0>();
  __syncthreads();
  #pragma unroll
  for (int i_14 = 0; i_14 < 8; ++i_14) {
    *(uint2*)(b_shared_local_cast_1 + 0) = *(uint2*)(((bfloat16_t*)buf_dyn_shmem) + (((i_14 * 512) + (((int)threadIdx.x) * 4)) + 4096));
    float4 __7;
    uint2 v__6 = *(uint2*)(b_shared_local_cast_1 + 0);
    ((float2*)(&__7))[0] = __bfloat1622float2((reinterpret_cast<__nv_bfloat162*>(&v__6))[0]);
    ((float2*)(&__7))[1] = __bfloat1622float2((reinterpret_cast<__nv_bfloat162*>(&v__6))[1]);
    *(float4*)(b_local + (i_14 * 4)) = __7;
  }
  tl::cp_async_wait<0>();
  __syncthreads();
  #pragma unroll
  for (int i_15 = 0; i_15 < 2; ++i_15) {
    *(uint2*)(d_shared_local_cast_1_1 + 0) = *(uint2*)(((bfloat16_t*)buf_dyn_shmem) + (((i_15 * 512) + (((int)threadIdx.x) * 4)) + 9216));
    float4 __8;
    uint2 v__7 = *(uint2*)(d_shared_local_cast_1_1 + 0);
    ((float2*)(&__8))[0] = __bfloat1622float2((reinterpret_cast<__nv_bfloat162*>(&v__7))[0]);
    ((float2*)(&__8))[1] = __bfloat1622float2((reinterpret_cast<__nv_bfloat162*>(&v__7))[1]);
    *(float4*)(d_local + (i_15 * 4)) = __8;
  }
  #pragma unroll
  for (int i_16 = 0; i_16 < 32; ++i_16) {
    x_local[i_16] = (c_local[(i_16 >> 3)] * d_local[(i_16 & 7)]);
    for (int i_hci_2 = 0; i_hci_2 < 4; ++i_hci_2) {
      x_local[i_16] = (x_local[i_16] + (a_local[((i_hci_2 * 4) + (i_16 >> 3))] * b_local[((i_hci_2 * 8) + (i_16 & 7))]));
    }
  }
  #pragma unroll
  for (int i_17 = 0; i_17 < 8; ++i_17) {
    uint2 __9;
    float4 v__8 = *(float4*)(x_local + (i_17 * 4));
    (reinterpret_cast<__nv_bfloat162*>(&__9))[0] = __float22bfloat162_rn(((float2*)(&v__8))[0]);
    (reinterpret_cast<__nv_bfloat162*>(&__9))[1] = __float22bfloat162_rn(((float2*)(&v__8))[1]);
    *(uint2*)(x_shared_local_cast_2_1 + 0) = __9;
    *(uint2*)(((bfloat16_t*)buf_dyn_shmem) + (((i_17 * 512) + (((int)threadIdx.x) * 4)) + 10240)) = *(uint2*)(x_shared_local_cast_2_1 + 0);
  }
  __syncthreads();
  #pragma unroll
  for (int i_18 = 0; i_18 < 4; ++i_18) {
    *(uint4*)(x + ((((((int64_t)((int)blockIdx.x)) * (int64_t)16384) + (((int64_t)i_18) * (int64_t)4096)) + (((int64_t)((int)threadIdx.x)) * (int64_t)8)) + (int64_t)3072)) = *(uint4*)(((bfloat16_t*)buf_dyn_shmem) + (((i_18 * 1024) + (((int)threadIdx.x) * 8)) + 10240));
  }
  cudaTriggerProgrammaticLaunchCompletion();
}

