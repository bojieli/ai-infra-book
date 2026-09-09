#include <tl_templates/cuda/instruction/mma.h>
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

extern "C" __global__ void kernel_kernel(half_t* __restrict__ Cast, __grid_constant__ const CUtensorMap k_desc, __grid_constant__ const CUtensorMap q_desc, __grid_constant__ const CUtensorMap v_desc);
extern "C" __global__ void __launch_bounds__(256, 1) kernel_kernel(half_t* __restrict__ Cast, __grid_constant__ const CUtensorMap k_desc, __grid_constant__ const CUtensorMap q_desc, __grid_constant__ const CUtensorMap v_desc) {
  extern __shared__ __align__(1024) uchar buf_dyn_shmem[];
  float softmax_maxelem[2];
  float matmul_NN[32];
  float softmax_expsum[2];
  float matmul_NT[32];
  float prev_softmax_maxelem[2];
  float input_0_0[32];
  float rescale_factor_1[2];
  half_t input_1_0[32];
  float rescale_factor_2[2];
  float input_2_0[32];
  half_t Cast_1[32];
  half_t A_local[8];
  half_t B_local[32];
  float softmax_maxelem_clear[2];
  half_t B_local_1[32];
  float softmax_expsum_clear[2];
  __shared__ __align__(16) uint64_t mbarrier_mem[5];
  auto mbarrier = reinterpret_cast<Barrier*>(mbarrier_mem);
  if (tl::tl_shuffle_elect<0>()) {
    tl::prefetch_tma_descriptor(q_desc);
    tl::prefetch_tma_descriptor(k_desc);
    tl::prefetch_tma_descriptor(v_desc);
    mbarrier[0].init(1);
    mbarrier[1].init(1);
    mbarrier[2].init(128);
    mbarrier[3].init(128);
    mbarrier[4].init(1);
  }
  tl::fence_barrier_init();
  __syncthreads();
  if (128 <= ((int)threadIdx.x)) {
    tl::warpgroup_reg_dealloc<24>();
    if (tl::tl_shuffle_elect<128>()) {
      mbarrier[4].arrive_and_expect_tx(8192);
      tl::fence_proxy_async();
      tl::tma_load(q_desc, mbarrier[4], (&(((half_t*)buf_dyn_shmem)[0])), 0, (((int)blockIdx.x) * 64), ((int)blockIdx.y), ((int)blockIdx.z));
    }
    for (int v_kv_len_o = 0; v_kv_len_o < 8; ++v_kv_len_o) {
      mbarrier[2].wait(((v_kv_len_o & 1) ^ 1));
      if (tl::tl_shuffle_elect<128>()) {
        mbarrier[0].arrive_and_expect_tx(8192);
        tl::fence_proxy_async();
        tl::tma_load(k_desc, mbarrier[0], (&(((half_t*)buf_dyn_shmem)[4096])), 0, (v_kv_len_o * 64), ((int)blockIdx.y), ((int)blockIdx.z));
      }
      mbarrier[3].wait(((v_kv_len_o & 1) ^ 1));
      if (tl::tl_shuffle_elect<128>()) {
        mbarrier[1].arrive_and_expect_tx(8192);
        tl::fence_proxy_async();
        tl::tma_load(v_desc, mbarrier[1], (&(((half_t*)buf_dyn_shmem)[8192])), 0, (v_kv_len_o * 64), ((int)blockIdx.y), ((int)blockIdx.z));
      }
    }
  } else {
    tl::warpgroup_reg_alloc<240>();
    float broadcast_var = -0x1.e848p+19f/*-1.000000e+06*/;
    *(float2*)(softmax_maxelem + 0) = make_float2(broadcast_var, broadcast_var);
    #pragma unroll
    for (int i = 0; i < 8; ++i) {
      float broadcast_var_1 = 0x0p+0f/*0.000000e+00*/;
      *(float4*)(matmul_NN + (i * 4)) = make_float4(broadcast_var_1, broadcast_var_1, broadcast_var_1, broadcast_var_1);
    }
    float broadcast_var_2 = 0x0p+0f/*0.000000e+00*/;
    *(float2*)(softmax_expsum + 0) = make_float2(broadcast_var_2, broadcast_var_2);
    mbarrier[4].wait(0);
    for (int v_kv_len_o_1 = 0; v_kv_len_o_1 < 8; ++v_kv_len_o_1) {
      #pragma unroll
      for (int i_1 = 0; i_1 < 8; ++i_1) {
        float broadcast_var_3 = 0x0p+0f/*0.000000e+00*/;
        *(float4*)(matmul_NT + (i_1 * 4)) = make_float4(broadcast_var_3, broadcast_var_3, broadcast_var_3, broadcast_var_3);
      }
      mbarrier[0].wait((v_kv_len_o_1 & 1));
      for (int ki = 0; ki < 4; ++ki) {
        tl::ptx_ldmatrix_x4((&(((half_t*)buf_dyn_shmem)[((((((int)threadIdx.x) >> 5) * 1024) + (((((int)threadIdx.x) & 15) >> 3) * 512)) + ((((((((int)threadIdx.x) & 15) * 64) + (((((((int)threadIdx.x) & 7) >> 2) + (ki >> 1)) & 1) * 32)) + (((((((int)threadIdx.x) & 3) >> 1) + (ki & 1)) & 1) * 16)) + (((((((int)threadIdx.x) & 31) >> 4) + (((int)threadIdx.x) & 1)) & 1) * 8)) & 511))])) + 0, A_local + 0);
        for (int i_2 = 0; i_2 < 4; ++i_2) {
          tl::ptx_ldmatrix_x4((&(((half_t*)buf_dyn_shmem)[(((((((i_2 * 1024) + (((((int)threadIdx.x) & 31) >> 4) * 512)) + ((((int)threadIdx.x) & 7) * 64)) + (((((((int)threadIdx.x) & 7) >> 2) + (ki >> 1)) & 1) * 32)) + (((((((int)threadIdx.x) & 3) >> 1) + (ki & 1)) & 1) * 16)) + (((((((int)threadIdx.x) & 15) >> 3) + (((int)threadIdx.x) & 1)) & 1) * 8)) + 4096)])) + 0, B_local + (i_2 * 8));
        }
        for (int j = 0; j < 4; ++j) {
          tl::mma_sync<tl::DataType::kFloat16, tl::DataType::kFloat16, tl::DataType::kFloat32, 16, 8, 16, false, true>(reinterpret_cast<float*>(matmul_NT + (j * 8)), reinterpret_cast<const unsigned*>(A_local + 0), reinterpret_cast<const unsigned*>(B_local + (j * 8)));
          tl::mma_sync<tl::DataType::kFloat16, tl::DataType::kFloat16, tl::DataType::kFloat32, 16, 8, 16, false, true>(reinterpret_cast<float*>(matmul_NT + ((j * 8) + 4)), reinterpret_cast<const unsigned*>(A_local + 0), reinterpret_cast<const unsigned*>(B_local + ((j * 8) + 4)));
        }
      }
      mbarrier[2].arrive();
      *(float2*)(prev_softmax_maxelem + 0) = *(float2*)(softmax_maxelem + 0);
      #pragma unroll
      for (int i_3 = 0; i_3 < 32; ++i_3) {
        input_0_0[i_3] = (matmul_NT[i_3] * (0x1p+0f/*1.000000e+00*/ / sqrtf(0x1p+6f/*6.400000e+01*/)));
      }
      #pragma unroll
      for (int i_4 = 0; i_4 < 2; ++i_4) {
        softmax_maxelem_clear[i_4] = -CUDART_INF_F;
        #pragma unroll
        for (int rv = 0; rv < 16; ++rv) {
          softmax_maxelem_clear[i_4] = max(softmax_maxelem_clear[i_4], input_0_0[((((rv & 7) * 4) + (i_4 * 2)) + (rv >> 3))]);
        }
        softmax_maxelem_clear[i_4] = tl::AllReduce<tl::MaxOp, 4, 1, 0, tl::NamedBarrier<128>>::run(softmax_maxelem_clear[i_4]);
        softmax_maxelem[i_4] = max(softmax_maxelem[i_4], softmax_maxelem_clear[i_4]);
      }
      #pragma unroll
      for (int i_5 = 0; i_5 < 2; ++i_5) {
        rescale_factor_1[i_5] = expf(((-0x1p+0f/*-1.000000e+00*/ * softmax_maxelem[i_5]) + prev_softmax_maxelem[i_5]));
      }
      #pragma unroll
      for (int i_6 = 0; i_6 < 16; ++i_6) {
        uint1 __1;
        float2 __2;
        float2 __3;
          float2 v_ = tl::fmul2(*(float2*)(matmul_NT + (i_6 * 2)), make_float2((0x1p+0f/*1.000000e+00*/ / sqrtf(0x1p+6f/*6.400000e+01*/)), (0x1p+0f/*1.000000e+00*/ / sqrtf(0x1p+6f/*6.400000e+01*/))));
          float2 v__1 = make_float2(softmax_maxelem[(i_6 & 1)], softmax_maxelem[(i_6 & 1)]);
          __3.x = (v_.x-v__1.x);
          __3.y = (v_.y-v__1.y);
        __2.x = expf(__3.x);
        __2.y = expf(__3.y);
        ((half2*)(&__1))[0] = __float22half2_rn(((float2*)(&__2))[0]);
        *(uint1*)(input_1_0 + (i_6 * 2)) = __1;
      }
      #pragma unroll
      for (int i_7 = 0; i_7 < 32; ++i_7) {
        matmul_NN[i_7] = (matmul_NN[i_7] * rescale_factor_1[((i_7 & 3) >> 1)]);
      }
      mbarrier[1].wait((v_kv_len_o_1 & 1));
      for (int ki_1 = 0; ki_1 < 4; ++ki_1) {
        for (int i_8 = 0; i_8 < 4; ++i_8) {
          tl::ptx_ldmatrix_x4_trans((&(((half_t*)buf_dyn_shmem)[((((ki_1 * 1024) + (((((int)threadIdx.x) & 15) >> 3) * 512)) + ((((((((int)threadIdx.x) & 15) * 64) + (((((((int)threadIdx.x) & 7) >> 2) + (i_8 >> 1)) & 1) * 32)) + (((((((int)threadIdx.x) & 3) >> 1) + (i_8 & 1)) & 1) * 16)) + (((((((int)threadIdx.x) & 31) >> 4) + (((int)threadIdx.x) & 1)) & 1) * 8)) & 511)) + 8192)])) + 0, B_local_1 + (i_8 * 8));
        }
        for (int j_1 = 0; j_1 < 4; ++j_1) {
          tl::mma_sync<tl::DataType::kFloat16, tl::DataType::kFloat16, tl::DataType::kFloat32, 16, 8, 16, false, true>(reinterpret_cast<float*>(matmul_NN + (j_1 * 8)), reinterpret_cast<const unsigned*>(input_1_0 + (ki_1 * 8)), reinterpret_cast<const unsigned*>(B_local_1 + (j_1 * 8)));
          tl::mma_sync<tl::DataType::kFloat16, tl::DataType::kFloat16, tl::DataType::kFloat32, 16, 8, 16, false, true>(reinterpret_cast<float*>(matmul_NN + ((j_1 * 8) + 4)), reinterpret_cast<const unsigned*>(input_1_0 + (ki_1 * 8)), reinterpret_cast<const unsigned*>(B_local_1 + ((j_1 * 8) + 4)));
        }
      }
      mbarrier[3].arrive();
      #pragma unroll
      for (int i_9 = 0; i_9 < 2; ++i_9) {
        rescale_factor_2[i_9] = expf(((-0x1p+0f/*-1.000000e+00*/ * softmax_maxelem[i_9]) + prev_softmax_maxelem[i_9]));
      }
      #pragma unroll
      for (int i_10 = 0; i_10 < 32; ++i_10) {
        input_2_0[i_10] = expf(((matmul_NT[i_10] * (0x1p+0f/*1.000000e+00*/ / sqrtf(0x1p+6f/*6.400000e+01*/))) - softmax_maxelem[((i_10 & 3) >> 1)]));
      }
      #pragma unroll
      for (int i_11 = 0; i_11 < 2; ++i_11) {
        softmax_expsum[i_11] = (softmax_expsum[i_11] * rescale_factor_2[i_11]);
      }
      #pragma unroll
      for (int i_12 = 0; i_12 < 2; ++i_12) {
        softmax_expsum_clear[i_12] = 0x0p+0f/*0.000000e+00*/;
        #pragma unroll
        for (int rv_1 = 0; rv_1 < 16; ++rv_1) {
          softmax_expsum_clear[i_12] = (softmax_expsum_clear[i_12] + input_2_0[((((rv_1 & 7) * 4) + (i_12 * 2)) + (rv_1 >> 3))]);
        }
        softmax_expsum_clear[i_12] = tl::AllReduce<tl::SumOp, 4, 1, 0, tl::NamedBarrier<128>>::run(softmax_expsum_clear[i_12]);
        softmax_expsum[i_12] = (softmax_expsum[i_12] + softmax_expsum_clear[i_12]);
      }
    }
    #pragma unroll
    for (int i_13 = 0; i_13 < 16; ++i_13) {
      uint1 __4;
      float2 __5;
        float2 v__2 = *(float2*)(matmul_NN + (i_13 * 2));
        float2 v__3 = make_float2(softmax_expsum[(i_13 & 1)], softmax_expsum[(i_13 & 1)]);
        __5.x = (v__2.x/v__3.x);
        __5.y = (v__2.y/v__3.y);
      ((half2*)(&__4))[0] = __float22half2_rn(((float2*)(&__5))[0]);
      *(uint1*)(Cast_1 + (i_13 * 2)) = __4;
    }
    #pragma unroll
    for (int i_14 = 0; i_14 < 16; ++i_14) {
      *(uint1*)(Cast + ((((((((((int)blockIdx.z) * 524288) + (((int)blockIdx.y) * 32768)) + (((int)blockIdx.x) * 4096)) + ((((int)threadIdx.x) >> 5) * 1024)) + ((i_14 & 1) * 512)) + (((((int)threadIdx.x) & 31) >> 2) * 64)) + ((i_14 >> 1) * 8)) + ((((int)threadIdx.x) & 3) * 2))) = *(uint1*)(Cast_1 + (i_14 * 2));
    }
  }
}

