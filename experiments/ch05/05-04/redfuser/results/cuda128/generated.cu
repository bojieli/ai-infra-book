#include <tl_templates/cuda/instruction/mma.h>
#include <tl_templates/cuda/cuda_fp8.h>
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

extern "C" __global__ void kernel_kernel(const half_t* __restrict__ A, __grid_constant__ const CUtensorMap W_fp8_desc, const float* __restrict__ W_scale, half_t* __restrict__ o);
extern "C" __global__ void __launch_bounds__(256, 1) kernel_kernel(const half_t* __restrict__ A, __grid_constant__ const CUtensorMap W_fp8_desc, const float* __restrict__ W_scale, half_t* __restrict__ o) {
  extern __shared__ __align__(1024) fp8_e4_t W_fp8_1[];
  float max_elem[4];
  float matmul_NT[128];
  half_t A_1[128];
  float prev_max_elem[4];
  float input_0_0[128];
  float rescale_factor_1[4];
  fp8_e4_t input_1_0[128];
  float W_scale_1[32];
  half_t o_1[128];
  float max_elem_clear[4];
  fp8_e4_t B_local[128];
  __shared__ __align__(16) uint64_t mbarrier_mem[2];
  auto mbarrier = reinterpret_cast<Barrier*>(mbarrier_mem);
  if (tl::tl_shuffle_elect<0>()) {
    tl::prefetch_tma_descriptor(W_fp8_desc);
    mbarrier[0].init(1);
    mbarrier[1].init(128);
  }
  tl::fence_barrier_init();
  __syncthreads();
  if (128 <= ((int)threadIdx.x)) {
    tl::warpgroup_reg_dealloc<24>();
    for (int v_k_o = 0; v_k_o < 32; ++v_k_o) {
      mbarrier[1].wait(((v_k_o & 1) ^ 1));
      if (tl::tl_shuffle_elect<128>()) {
        mbarrier[0].arrive_and_expect_tx(16384);
        tl::fence_proxy_async();
        tl::tma_load(W_fp8_desc, mbarrier[0], (&(W_fp8_1[0])), (v_k_o * 128), (((int)blockIdx.x) * 128));
      }
    }
  } else {
    tl::warpgroup_reg_alloc<240>();
    float broadcast_var = -0x1.e848p+19f/*-1.000000e+06*/;
    *(float4*)(max_elem + 0) = make_float4(broadcast_var, broadcast_var, broadcast_var, broadcast_var);
    #pragma unroll
    for (int i = 0; i < 32; ++i) {
      float broadcast_var_1 = 0x0p+0f/*0.000000e+00*/;
      *(float4*)(matmul_NT + (i * 4)) = make_float4(broadcast_var_1, broadcast_var_1, broadcast_var_1, broadcast_var_1);
    }
    for (int v_k_o_1 = 0; v_k_o_1 < 32; ++v_k_o_1) {
      #pragma unroll
      for (int i_1 = 0; i_1 < 32; ++i_1) {
        *(uint2*)(A_1 + (i_1 * 4)) = *(uint2*)(A + (((((((((((int)blockIdx.y) * 524288) + ((((int)threadIdx.x) >> 5) * 131072)) + (((i_1 & 7) >> 2) * 65536)) + ((i_1 & 1) * 32768)) + (((((int)threadIdx.x) & 31) >> 2) * 4096)) + (v_k_o_1 * 128)) + ((i_1 >> 3) * 32)) + (((i_1 & 3) >> 1) * 16)) + ((((int)threadIdx.x) & 3) * 4)));
      }
      *(float4*)(prev_max_elem + 0) = *(float4*)(max_elem + 0);
      #pragma unroll
      for (int i_2 = 0; i_2 < 32; ++i_2) {
        float4 __1;
        uint2 __2;
        uint2 v_ = *(uint2*)(A_1 + (i_2 * 4));
        ((half2*)(&(__2.x)))->x = __habs(((half2*)(&(v_.x)))->x);
        ((half2*)(&(__2.x)))->y = __habs(((half2*)(&(v_.x)))->y);
        ((half2*)(&(__2.y)))->x = __habs(((half2*)(&(v_.y)))->x);
        ((half2*)(&(__2.y)))->y = __habs(((half2*)(&(v_.y)))->y);
        ((float2*)(&__1))[0] = __half22float2(((half2*)(&__2))[0]);
        ((float2*)(&__1))[1] = __half22float2(((half2*)(&__2))[1]);
        *(float4*)(input_0_0 + (i_2 * 4)) = __1;
      }
      #pragma unroll
      for (int i_3 = 0; i_3 < 4; ++i_3) {
        max_elem_clear[i_3] = -CUDART_INF_F;
        #pragma unroll
        for (int rv = 0; rv < 32; ++rv) {
          max_elem_clear[i_3] = max(max_elem_clear[i_3], input_0_0[((((((rv & 3) * 32) + ((i_3 >> 1) * 16)) + (((rv & 7) >> 2) * 8)) + ((i_3 & 1) * 4)) + (rv >> 3))]);
        }
        max_elem_clear[i_3] = tl::AllReduce<tl::MaxOp, 4, 1, 0, tl::NamedBarrier<128>>::run(max_elem_clear[i_3]);
        max_elem[i_3] = max(max_elem[i_3], max_elem_clear[i_3]);
      }
      #pragma unroll
      for (int i_4 = 0; i_4 < 4; ++i_4) {
        rescale_factor_1[i_4] = (powf(max_elem[i_4], -0x1p+0f/*-1.000000e+00*/) * prev_max_elem[i_4]);
      }
      #pragma unroll
      for (int i_5 = 0; i_5 < 32; ++i_5) {
        fp8_e4_4_t __3;
        float4 __4;
          float4 __5;
          uint2 v__1 = *(uint2*)(A_1 + (i_5 * 4));
          ((float2*)(&__5))[0] = __half22float2(((half2*)(&v__1))[0]);
          ((float2*)(&__5))[1] = __half22float2(((half2*)(&v__1))[1]);
          float4 v__2 = make_float4((max_elem[((((i_5 & 7) >> 2) * 2) + (i_5 & 1))] / 0x1.cp+8f/*4.480000e+02*/), (max_elem[((((i_5 & 7) >> 2) * 2) + (i_5 & 1))] / 0x1.cp+8f/*4.480000e+02*/), (max_elem[((((i_5 & 7) >> 2) * 2) + (i_5 & 1))] / 0x1.cp+8f/*4.480000e+02*/), (max_elem[((((i_5 & 7) >> 2) * 2) + (i_5 & 1))] / 0x1.cp+8f/*4.480000e+02*/));
          __4.x = (__5.x/v__2.x);
          __4.y = (__5.y/v__2.y);
          __4.z = (__5.z/v__2.z);
          __4.w = (__5.w/v__2.w);
        (reinterpret_cast<__nv_fp8x2_storage_t*>(&__3))[0] = __nv_cvt_float2_to_fp8x2(((float2*)(&__4))[0], __NV_SATFINITE, __NV_E4M3);
        (reinterpret_cast<__nv_fp8x2_storage_t*>(&__3))[1] = __nv_cvt_float2_to_fp8x2(((float2*)(&__4))[1], __NV_SATFINITE, __NV_E4M3);
        *(fp8_e4_4_t*)(input_1_0 + (i_5 * 4)) = __3;
      }
      #pragma unroll
      for (int i_6 = 0; i_6 < 128; ++i_6) {
        matmul_NT[i_6] = (matmul_NT[i_6] * rescale_factor_1[(((i_6 >> 6) * 2) + ((i_6 & 3) >> 1))]);
      }
      mbarrier[0].wait((v_k_o_1 & 1));
      for (int ki = 0; ki < 4; ++ki) {
        for (int i_7 = 0; i_7 < 8; ++i_7) {
          tl::ptx_ldmatrix_x4((&(W_fp8_1[((((((i_7 * 2048) + (((((int)threadIdx.x) & 31) >> 4) * 1024)) + ((((int)threadIdx.x) & 7) * 128)) + (((((((int)threadIdx.x) & 7) >> 2) + (ki >> 1)) & 1) * 64)) + (((((((int)threadIdx.x) & 3) >> 1) + (ki & 1)) & 1) * 32)) + (((((((int)threadIdx.x) & 15) >> 3) + (((int)threadIdx.x) & 1)) & 1) * 16))])) + 0, B_local + (i_7 * 16));
        }
        for (int i_8 = 0; i_8 < 2; ++i_8) {
          for (int j = 0; j < 8; ++j) {
            tl::mma_sync<tl::DataType::kFloat8_e4m3, tl::DataType::kFloat8_e4m3, tl::DataType::kFloat32, 16, 8, 32, false, true>(reinterpret_cast<float*>(matmul_NT + ((i_8 * 64) + (j * 8))), reinterpret_cast<const unsigned*>(input_1_0 + ((ki * 32) + (i_8 * 16))), reinterpret_cast<const unsigned*>(B_local + (j * 16)));
            tl::mma_sync<tl::DataType::kFloat8_e4m3, tl::DataType::kFloat8_e4m3, tl::DataType::kFloat32, 16, 8, 32, false, true>(reinterpret_cast<float*>(matmul_NT + (((i_8 * 64) + (j * 8)) + 4)), reinterpret_cast<const unsigned*>(input_1_0 + ((ki * 32) + (i_8 * 16))), reinterpret_cast<const unsigned*>(B_local + ((j * 16) + 8)));
          }
        }
      }
      mbarrier[1].arrive();
    }
    #pragma unroll
    for (int i_9 = 0; i_9 < 16; ++i_9) {
      *(float2*)(W_scale_1 + (i_9 * 2)) = *(float2*)(W_scale + (((((int)blockIdx.x) * 128) + (i_9 * 8)) + ((((int)threadIdx.x) & 3) * 2)));
    }
    #pragma unroll
    for (int i_10 = 0; i_10 < 64; ++i_10) {
      uint1 __6;
      float2 v__3 = tl::fmul2(tl::fmul2(*(float2*)(matmul_NT + (i_10 * 2)), make_float2((max_elem[(((i_10 >> 5) * 2) + (i_10 & 1))] / 0x1.cp+8f/*4.480000e+02*/), (max_elem[(((i_10 >> 5) * 2) + (i_10 & 1))] / 0x1.cp+8f/*4.480000e+02*/))), *(float2*)(W_scale_1 + (((i_10 & 31) >> 1) * 2)));
      ((half2*)(&__6))[0] = __float22half2_rn(((float2*)(&v__3))[0]);
      *(uint1*)(o_1 + (i_10 * 2)) = __6;
    }
    #pragma unroll
    for (int i_11 = 0; i_11 < 64; ++i_11) {
      *(uint1*)(o + ((((((((((int)blockIdx.y) * 524288) + ((((int)threadIdx.x) >> 5) * 131072)) + ((i_11 >> 5) * 65536)) + ((i_11 & 1) * 32768)) + (((((int)threadIdx.x) & 31) >> 2) * 4096)) + (((int)blockIdx.x) * 128)) + (((i_11 & 31) >> 1) * 8)) + ((((int)threadIdx.x) & 3) * 2))) = *(uint1*)(o_1 + (i_11 * 2));
    }
  }
}

