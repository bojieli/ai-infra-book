/******************************************************************************
 * Copyright (c) 2023, Tri Dao.
 ******************************************************************************/

#pragma once

#include <ATen/cuda/CUDAContext.h>

#include "static_switch.h"
#include "flash.h"
#include "fused_fwd_kernel.h"
#define HFUSE
#ifdef HFUSE
// HFuse headers
#include "hfuse_regular.cuh"
#include "hfuse_split.cuh"
#include "hfuse_splitonly.cuh"
#endif

// Determine if the architecture supports FLASH and define a macro to handle parameter modifiers
#if defined(__CUDA_ARCH__) && __CUDA_ARCH__ >= 800
#define ARCH_SUPPORTS_FLASH
#define KERNEL_PARAM_MODIFIER __grid_constant__
#else
#define KERNEL_PARAM_MODIFIER
#endif

// Define a macro for unsupported architecture handling to centralize the error message
#define FLASH_UNSUPPORTED_ARCH printf("FATAL: FlashAttention requires building with sm version sm80-sm90, but was built for < 8.0!");

// Use a macro to clean up kernel definitions
#define DEFINE_FLASH_FORWARD_KERNEL(kernelName, ...) \
template<typename Kernel_traits, __VA_ARGS__> \
__global__ void kernelName(KERNEL_PARAM_MODIFIER const Flash_fwd_params params)
/*
template<typename Kernel_traits_prefill, typename Kernel_traits_decode, bool Is_dropout, bool Is_causal_p, bool Is_causal_d, bool Is_local_p, bool Is_local_d, 
    bool Has_alibi, bool Is_even_MN_p, bool Is_even_K_p, bool Is_even_MN_d, bool Is_even_K_d, 
    bool Is_softcap, bool Return_softmax, bool DecodeIsSplit>
__global__ void true_fused_fwd_kernel(KERNEL_PARAM_MODIFIER const Flash_fwd_params prefill_params, 
    KERNEL_PARAM_MODIFIER const Flash_fwd_params decode_params) {
    #if defined(ARCH_SUPPORTS_FLASH)
        static_assert(!(Is_causal_p && Is_local_p)); // Enforce constraints
        static_assert(!(Is_causal_d && Is_local_d)); // Enforce constraints
        fused::compute_fused_attn<Kernel_traits_prefill, Kernel_traits_decode, Is_dropout, Is_causal_p, Is_causal_d, Is_local_p, Is_local_d, Has_alibi, 
            Is_even_MN_p, Is_even_K_p, Is_even_MN_d, Is_even_K_d, Is_softcap, Return_softmax, DecodeIsSplit>(prefill_params, decode_params);
    #else
        FLASH_UNSUPPORTED_ARCH
    #endif
}
*/
template<typename Kernel_traits_prefill, typename Kernel_traits_decode, 
    bool Is_dropout, bool Is_causal_p, bool Is_causal_d, bool Is_local_p, bool Is_local_d, 
    bool Has_alibi, bool Is_even_MN_p, bool Is_even_K_p, bool Is_even_MN_d, bool Is_even_K_d, 
    bool Is_softcap, bool Return_softmax, bool PrefillIsSplit, bool DecodeIsSplit, 
    bool DecodeAppend_KV, int FusedOp, bool UseSplitPrefill, bool UseSplitDecode>
__global__ void true_fused_tb_fwd_kernel(KERNEL_PARAM_MODIFIER const Flash_fwd_params prefill_params, 
    KERNEL_PARAM_MODIFIER const Flash_fwd_params decode_params, int *tbAssign) {
    #if defined(ARCH_SUPPORTS_FLASH)
        static_assert(!(Is_causal_p && Is_local_p)); // Enforce constraints
        static_assert(!(Is_causal_d && Is_local_d)); // Enforce constraints
        fused::compute_fused_tb_attn<Kernel_traits_prefill, Kernel_traits_decode, 
            Is_dropout, Is_causal_p, Is_causal_d, Is_local_p, Is_local_d, Has_alibi, 
            Is_even_MN_p, Is_even_K_p, Is_even_MN_d, Is_even_K_d, Is_softcap, 
            Return_softmax, PrefillIsSplit, DecodeIsSplit, DecodeAppend_KV, FusedOp,
            UseSplitPrefill, UseSplitDecode>
            (prefill_params, decode_params, tbAssign);
    #else
        FLASH_UNSUPPORTED_ARCH
    #endif
}

template<typename Kernel_traits_prefill, typename Kernel_traits_decode, 
    bool Is_dropout, bool Is_causal_p, bool Is_causal_d, bool Is_local_p, bool Is_local_d, 
    bool Has_alibi, bool Is_even_MN_p, bool Is_even_K_p, bool Is_even_MN_d, bool Is_even_K_d, 
    bool Is_softcap, bool Return_softmax, bool PrefillIsSplit, bool DecodeIsSplit, 
    bool DecodeAppend_KV, int FusedOp, bool UseSplitPrefill, bool UseSplitDecode>
__global__ void true_fused_pt_tb_fwd_kernel(KERNEL_PARAM_MODIFIER const Flash_fwd_params prefill_params, 
    KERNEL_PARAM_MODIFIER const Flash_fwd_params decode_params, int *tbAssign) {
    #if defined(ARCH_SUPPORTS_FLASH)
        static_assert(!(Is_causal_p && Is_local_p)); // Enforce constraints
        static_assert(!(Is_causal_d && Is_local_d)); // Enforce constraints
        fused::compute_fused_pt_tb_attn<Kernel_traits_prefill, Kernel_traits_decode, 
            Is_dropout, Is_causal_p, Is_causal_d, Is_local_p, Is_local_d, Has_alibi, 
            Is_even_MN_p, Is_even_K_p, Is_even_MN_d, Is_even_K_d, Is_softcap, 
            Return_softmax, PrefillIsSplit, DecodeIsSplit, DecodeAppend_KV, FusedOp,
            UseSplitPrefill, UseSplitDecode>
            (prefill_params, decode_params, tbAssign);
    #else
        FLASH_UNSUPPORTED_ARCH
    #endif
}

DEFINE_FLASH_FORWARD_KERNEL(fused_fwd_kernel, bool Is_dropout, bool Is_causal, bool Is_local, bool Has_alibi, bool Is_even_MN, bool Is_even_K, bool Is_softcap, bool Return_softmax) {
    #if defined(ARCH_SUPPORTS_FLASH)
        static_assert(!(Is_causal && Is_local)); // Enforce constraints
        fused::compute_attn<Kernel_traits, Is_dropout, Is_causal, Is_local, Has_alibi, Is_even_MN, Is_even_K, Is_softcap, Return_softmax>(params);
    #else
        FLASH_UNSUPPORTED_ARCH
    #endif
}

DEFINE_FLASH_FORWARD_KERNEL(fused_fwd_splitkv_kernel, bool Is_causal, bool Is_local, bool Has_alibi, bool Is_even_MN, bool Is_even_K, bool Is_softcap, bool Split, bool Append_KV) {
    #if defined(ARCH_SUPPORTS_FLASH)
        fused::compute_attn_splitkv<Kernel_traits, Is_causal, Is_local, Has_alibi, Is_even_MN, Is_even_K, Is_softcap, Split, Append_KV>(params);
    #else
        FLASH_UNSUPPORTED_ARCH
    #endif
}

DEFINE_FLASH_FORWARD_KERNEL(fused_fwd_splitkv_combine_kernel, int kBlockM, int Log_max_splits, bool Is_even_K) {
    static_assert(Log_max_splits >= 1);
    fused::combine_attn_seqk_parallel<Kernel_traits, kBlockM, Log_max_splits, Is_even_K>(params);
}

template<typename Kernel_traits, bool Is_dropout, bool Is_causal>
void run_fused_fwd(Flash_fwd_params &params, cudaStream_t stream) {
    constexpr size_t smem_size = Kernel_traits::kSmemSize;
    // printf("smem_size = %d\n", smem_size);

    // Work-around for gcc 7. It doesn't like nested BOOL_SWITCH.
    // https://github.com/kokkos/kokkos-kernels/issues/349
    // https://github.com/HazyResearch/flash-attention/issues/21

    const int num_m_block = (params.seqlen_q + Kernel_traits::kBlockM - 1) / Kernel_traits::kBlockM;
    dim3 grid(num_m_block, params.b, params.h);
    const bool is_even_MN = params.cu_seqlens_q == nullptr && params.cu_seqlens_k == nullptr && params.seqlen_k % Kernel_traits::kBlockN == 0 && params.seqlen_q % Kernel_traits::kBlockM == 0;
    //const bool is_even_K = params.d == Kernel_traits::kHeadDim;
    //const bool return_softmax = params.p_ptr != nullptr;
    BOOL_SWITCH(is_even_MN, IsEvenMNConst, [&] {
        const bool IsEvenKConst = true;
        //EVENK_SWITCH(true, IsEvenKConst, [&] {
            LOCAL_SWITCH((params.window_size_left >= 0 || params.window_size_right >= 0) && !Is_causal, Is_local, [&] {
                //BOOL_SWITCH(false, ReturnSoftmaxConst, [&] {
                const bool ReturnSoftmaxConst = false;
                    //ALIBI_SWITCH(params.alibi_slopes_ptr != nullptr, Has_alibi, [&] {
                    const bool Has_alibi = false;
                        SOFTCAP_SWITCH(params.softcap > 0.0, Is_softcap, [&] {
                            // Will only return softmax if dropout, to reduce compilation time.
                            // If not IsEvenKConst, we also set IsEvenMNConst to false to reduce number of templates.
                            // If return_softmax, set IsEvenMNConst to false to reduce number of templates
                            // If head dim > 128, set IsEvenMNConst to false to reduce number of templates
                            // If Is_local, set Is_causal to false
                            auto kernel = &fused_fwd_kernel<Kernel_traits, Is_dropout && !Is_softcap, Is_causal, Is_local && !Is_causal, Has_alibi, IsEvenMNConst && IsEvenKConst && !Is_local && !ReturnSoftmaxConst && Kernel_traits::kHeadDim <= 128, IsEvenKConst, Is_softcap, ReturnSoftmaxConst && Is_dropout && !Is_softcap>;
                            // auto kernel = &flash_fwd_kernel<Kernel_traits, false, Is_causal, false, false, true, true, false>;
                            // printf("IsEvenMNConst = %d, IsEvenKConst = %d, Is_local = %d, Is_causal = %d, ReturnSoftmaxConst = %d, Is_dropout = %d\n", int(IsEvenMNConst), int(IsEvenKConst), int(Is_local), int(Is_causal), int(ReturnSoftmaxConst), int(Is_dropout));
                            // auto kernel = &flash_fwd_kernel<Kernel_traits, false, Is_causal, false, true, true, false>;
                            if (smem_size >= 48 * 1024) {
                                C10_CUDA_CHECK(cudaFuncSetAttribute(
                                    kernel, cudaFuncAttributeMaxDynamicSharedMemorySize, smem_size));
                            }
                            // int ctas_per_sm;
                            // cudaError status_ = cudaOccupancyMaxActiveBlocksPerMultiprocessor(
                            //     &ctas_per_sm, kernel, Kernel_traits::kNThreads, smem_size);
                            // printf("smem_size = %d, CTAs per SM = %d\n", int(smem_size), ctas_per_sm);
                            int num_threads = Kernel_traits::kNThreads;
                            kernel<<<grid, num_threads, smem_size, stream>>>(params);
                            C10_CUDA_KERNEL_LAUNCH_CHECK();
                        });
                    //});
                //});
            });
        //});
    });
}

#ifdef HFUSE
template<typename Kernel_traits_prefill, typename Kernel_traits_decode, bool Is_dropout, bool Is_causal_p, int fused_op, bool DecodeIsSplit, bool PrefillIsSplit=false>
void run_hfused_fwd(Flash_fwd_params &prefill_params, Flash_fwd_params &decode_params, cudaStream_t stream) {
    static_assert(!Kernel_traits_decode::Is_Q_in_regs, "SplitKV implementation does not support Is_Q_in_regs");
    static_assert(!Kernel_traits_decode::Share_Q_K_smem, "SplitKV implementation does not support Share_Q_K_smem");

    // Work-around for gcc 7. It doesn't like nested BOOL_SWITCH.
    // https://github.com/kokkos/kokkos-kernels/issues/349
    // https://github.com/HazyResearch/flash-attention/issues/21
    //assert(prefill_params.b >= decode_params.b);
    assert(prefill_params.h == decode_params.h);
    assert(prefill_params.d == decode_params.d);
    assert(prefill_params.seqlen_k == decode_params.seqlen_k);

    //fprintf(stderr, "p.b = %d, p.seqlen_q = %d, ", prefill_params.b, prefill_params.seqlen_q);
    //fprintf(stderr, "d.b = %d, d.seqlen_q = %d\n", decode_params.b, decode_params.seqlen_q);
    
    const int num_m_block_prefill = (prefill_params.seqlen_q + Kernel_traits_prefill::kBlockM - 1) / Kernel_traits_prefill::kBlockM;
    const int num_m_block_decode = (decode_params.seqlen_q + Kernel_traits_decode::kBlockM - 1) / Kernel_traits_decode::kBlockM;

    size_t num_blocks_prefill = (num_m_block_prefill * prefill_params.b * prefill_params.h * prefill_params.num_splits);
    size_t num_blocks_decode;
    if constexpr(DecodeIsSplit) {
        num_blocks_decode = num_m_block_decode * decode_params.num_splits * decode_params.b * decode_params.h;
    } else {
        num_blocks_decode = num_m_block_decode * decode_params.b * decode_params.h;
    }
    //fprintf(stderr, "nblks_p = %d, nblks_d = %d\n", int(num_blocks_prefill), int(num_blocks_decode));
    //dim3 grid(num_m_block_prefill, prefill_params.b, prefill_params.h);
    //const bool is_even_K = prefill_params.d == Kernel_traits_prefill::kHeadDim;
    const bool is_even_MN_prefill = prefill_params.cu_seqlens_q == nullptr && prefill_params.cu_seqlens_k == nullptr && prefill_params.seqlen_k % Kernel_traits_prefill::kBlockN == 0 && prefill_params.seqlen_q % Kernel_traits_prefill::kBlockM == 0;
    const bool is_even_MN_decode = decode_params.cu_seqlens_q == nullptr && decode_params.cu_seqlens_k == nullptr && decode_params.seqlen_k % Kernel_traits_decode::kBlockN == 0 && decode_params.seqlen_q % Kernel_traits_decode::kBlockM == 0;
    // We do not support these currently
    assert(prefill_params.alibi_slopes_ptr == nullptr);
    assert(decode_params.alibi_slopes_ptr == nullptr);
    assert(prefill_params.softcap == 0.0);
    assert(decode_params.softcap == 0.0);
    //const bool return_softmax = params.p_ptr != nullptr;
    //EVENK_SWITCH(is_even_K, IsEvenKConst, [&] {
    constexpr static bool IsEvenKConst = true;
        BOOL_SWITCH(is_even_MN_prefill, IsEvenMNConst_p, [&] {
            BOOL_SWITCH(is_even_MN_decode, IsEvenMNConst_d, [&] {
                BOOL_SWITCH(decode_params.knew_ptr != nullptr, DecodeAppend_KV, [&] {
                    //EVENK_SWITCH(is_even_K_decode, IsEvenKConst_d, [&] {
                    //BOOL_SWITCH(decode_params.is_causal, Is_causal_d, [&] {
                    static constexpr bool Is_causal_d = false;
                        LOCAL_SWITCH((prefill_params.window_size_left >= 0 || prefill_params.window_size_right >= 0) && !Is_causal_p, Is_local_p, [&] {
                            LOCAL_SWITCH((decode_params.window_size_left >= 0 || decode_params.window_size_right >= 0) && !Is_causal_d, Is_local_d, [&] {
                                //BOOL_SWITCH(false, ReturnSoftmaxConst, [&] {
                                constexpr static bool ReturnSoftmaxConst = false;
                                // Will only return softmax if dropout, to reduce compilation time.
                                // If not IsEvenKConst, we also set IsEvenMNConst to false to reduce number of templates.
                                // If return_softmax, set IsEvenMNConst to false to reduce number of templates
                                // If head dim > 128, set IsEvenMNConst to false to reduce number of templates
                                // If Is_local, set Is_causal to false
                                //bool UsePrefillSplit = PrefillIsSplit || prefill_params.block_table != nullptr;
                                bool UseDecodeSplit = DecodeIsSplit || DecodeAppend_KV || decode_params.cache_batch_idx != nullptr || decode_params.block_table != nullptr;
                                // -----------------------> Code for HFuse <-----------------------
                                dim3 grid = dim3(max(num_blocks_prefill, num_blocks_decode), 1, 1);
                                size_t smem_size = Kernel_traits_prefill::kSmemSize + Kernel_traits_decode::kSmemSize;
                                int num_threads = Kernel_traits_prefill::kNThreads + Kernel_traits_decode::kNThreads;
                                if constexpr(PrefillIsSplit) {
                                    if (!UseDecodeSplit) {
                                        auto kernel = flash_fwd_kernel_flash_fwd_splitkv_kernel_fused_kernel_hfuse_idx_0<
                                            Kernel_traits_decode, Is_dropout && !false, Is_causal_d, Is_local_d && !Is_causal_d, false, 
                                            IsEvenMNConst_d && IsEvenKConst && !Is_local_d && Kernel_traits_decode::kHeadDim <= 128, 
                                            IsEvenKConst, false, ReturnSoftmaxConst && Is_dropout && !false,
                                            Kernel_traits_prefill, Is_causal_p, Is_local_p && !Is_causal_p, false, 
                                            IsEvenMNConst_p && IsEvenKConst && !Is_local_p && Kernel_traits_prefill::kHeadDim <= 128,
                                            IsEvenKConst, false, PrefillIsSplit, false>;
                                        if (smem_size >= 48 * 1024) {
                                            C10_CUDA_CHECK(cudaFuncSetAttribute(
                                                kernel, cudaFuncAttributeMaxDynamicSharedMemorySize, smem_size));
                                        }
                                        kernel<<<grid, num_threads, smem_size, stream>>>(decode_params, prefill_params);
                                    } else if (UseDecodeSplit) {
                                        auto kernel = flash_fwd_splitkv_kernel_flash_fwd_splitkv_kernel_fused_kernel_hfuse_idx_0<
                                            Kernel_traits_prefill, Is_causal_p, Is_local_p && !Is_causal_p, false, 
                                            IsEvenMNConst_p && IsEvenKConst && !Is_local_p && Kernel_traits_prefill::kHeadDim <= 128,
                                            IsEvenKConst, false, PrefillIsSplit, false,
                                            Kernel_traits_decode, Is_causal_d, Is_local_d && !Is_causal_d, false, 
                                            IsEvenMNConst_d && !DecodeAppend_KV && IsEvenKConst && !Is_local_d && Kernel_traits_decode::kHeadDim <= 128, 
                                            IsEvenKConst, false, DecodeIsSplit, DecodeAppend_KV>;
                                        if (smem_size >= 48 * 1024) {
                                            C10_CUDA_CHECK(cudaFuncSetAttribute(
                                                kernel, cudaFuncAttributeMaxDynamicSharedMemorySize, smem_size));
                                        }
                                        kernel<<<grid, num_threads, smem_size, stream>>>(prefill_params, decode_params);
                                    }
                                } else {
                                    if (UseDecodeSplit) {
                                        auto kernel = flash_fwd_kernel_flash_fwd_splitkv_kernel_fused_kernel_hfuse_idx_0<
                                            Kernel_traits_prefill, Is_dropout && !false, Is_causal_p, Is_local_p && !Is_causal_p, false, 
                                            IsEvenMNConst_p && IsEvenKConst && !Is_local_p && !ReturnSoftmaxConst && Kernel_traits_prefill::kHeadDim <= 128,
                                            IsEvenKConst, false, ReturnSoftmaxConst && Is_dropout && !false, 
                                            Kernel_traits_decode, Is_causal_d, Is_local_d && !Is_causal_d, false, 
                                            IsEvenMNConst_d && !DecodeAppend_KV && IsEvenKConst && !Is_local_d && Kernel_traits_decode::kHeadDim <= 128, 
                                            IsEvenKConst, false, DecodeIsSplit, DecodeAppend_KV>;
                                        if (smem_size >= 48 * 1024) {
                                            C10_CUDA_CHECK(cudaFuncSetAttribute(
                                                kernel, cudaFuncAttributeMaxDynamicSharedMemorySize, smem_size));
                                        }
                                        kernel<<<grid, num_threads, smem_size, stream>>>(prefill_params, decode_params);
                                    } else if (!UseDecodeSplit) {
                                        auto kernel = flash_fwd_kernel_flash_fwd_kernel_fused_kernel_hfuse_idx_0<
                                            Kernel_traits_prefill, Is_dropout && !false, Is_causal_p, Is_local_p && !Is_causal_p, false, 
                                            IsEvenMNConst_p && IsEvenKConst && !Is_local_p && !ReturnSoftmaxConst && Kernel_traits_prefill::kHeadDim <= 128,
                                            IsEvenKConst, false, ReturnSoftmaxConst && Is_dropout && !false, 
                                            Kernel_traits_decode, Is_dropout && !false, Is_causal_d, Is_local_d && !Is_causal_d, false,
                                            IsEvenMNConst_d && IsEvenKConst && !Is_local_d && Kernel_traits_decode::kHeadDim <= 128, 
                                            IsEvenKConst, false, ReturnSoftmaxConst && Is_dropout && !false>;
                                        if (smem_size >= 48 * 1024) {
                                            C10_CUDA_CHECK(cudaFuncSetAttribute(
                                                kernel, cudaFuncAttributeMaxDynamicSharedMemorySize, smem_size));
                                        }
                                        kernel<<<grid, num_threads, smem_size, stream>>>(prefill_params, decode_params);
                                    }
                                }
                                //});
                            });
                        });
                    });
                //});
            });
        });
        if constexpr(PrefillIsSplit) {
            // We want kBlockM to be as small as possible for more parallelism.
            // With 128 threads we can load 512 elements at a time, so if headdim is divisible by 128, kBlockM = 4.
            // If headdim is divisible by 64, then we set kBlockM = 8, etc.
            constexpr static int kBlockM = Kernel_traits_prefill::kHeadDim % 128 == 0 ? 4 : (Kernel_traits_prefill::kHeadDim % 64 == 0 ? 8 : 16);
            dim3 grid_combine((prefill_params.b * prefill_params.h * prefill_params.seqlen_q + kBlockM - 1) / kBlockM);
            // Below kernels REQUIRE 128 threads.
            //EVENK_SWITCH(is_even_K, IsEvenKConst, [&] {
                const int num_threads = 128;
                if (prefill_params.num_splits <= 2) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_prefill, kBlockM, 1, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(prefill_params);
                } else if (prefill_params.num_splits <= 4) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_prefill, kBlockM, 2, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(prefill_params);
                } else if (prefill_params.num_splits <= 8) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_prefill, kBlockM, 3, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(prefill_params);
                } else if (prefill_params.num_splits <= 16) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_prefill, kBlockM, 4, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(prefill_params);
                } else if (prefill_params.num_splits <= 32) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_prefill, kBlockM, 5, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(prefill_params);
                } else if (prefill_params.num_splits <= 64) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_prefill, kBlockM, 6, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(prefill_params);
                } else if (prefill_params.num_splits <= 128) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_prefill, kBlockM, 7, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(prefill_params);
                }
                C10_CUDA_KERNEL_LAUNCH_CHECK();
            //});
        }
        //printf("smem used: p = %d, d = %d\n", Kernel_traits_prefill::kSmemSize, Kernel_traits_decode::kSmemSize);
        if constexpr(DecodeIsSplit) {
            // We want kBlockM to be as small as possible for more parallelism.
            // With 128 threads we can load 512 elements at a time, so if headdim is divisible by 128, kBlockM = 4.
            // If headdim is divisible by 64, then we set kBlockM = 8, etc.
            constexpr static int kBlockM = Kernel_traits_decode::kHeadDim % 128 == 0 ? 4 : (Kernel_traits_decode::kHeadDim % 64 == 0 ? 8 : 16);
            dim3 grid_combine((decode_params.b * decode_params.h * decode_params.seqlen_q + kBlockM - 1) / kBlockM);
            // Below kernels REQUIRE 128 threads.
            //EVENK_SWITCH(is_even_K, IsEvenKConst, [&] {
                const int num_threads = 128;
                if (decode_params.num_splits <= 2) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_decode, kBlockM, 1, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(decode_params);
                } else if (decode_params.num_splits <= 4) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_decode, kBlockM, 2, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(decode_params);
                } else if (decode_params.num_splits <= 8) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_decode, kBlockM, 3, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(decode_params);
                } else if (decode_params.num_splits <= 16) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_decode, kBlockM, 4, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(decode_params);
                } else if (decode_params.num_splits <= 32) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_decode, kBlockM, 5, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(decode_params);
                } else if (decode_params.num_splits <= 64) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_decode, kBlockM, 6, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(decode_params);
                } else if (decode_params.num_splits <= 128) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_decode, kBlockM, 7, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(decode_params);
                }
                C10_CUDA_KERNEL_LAUNCH_CHECK();
            //});
        }
    //});
}
#endif

template<typename Kernel_traits_prefill, typename Kernel_traits_decode, bool Is_dropout, bool Is_causal_p, int fused_op, bool DecodeIsSplit, bool PrefillIsSplit=false>
void run_true_fused_fwd(Flash_fwd_params &prefill_params, Flash_fwd_params &decode_params, cudaStream_t stream) {
    static_assert(!Kernel_traits_decode::Is_Q_in_regs, "SplitKV implementation does not support Is_Q_in_regs");
    static_assert(!Kernel_traits_decode::Share_Q_K_smem, "SplitKV implementation does not support Share_Q_K_smem");

    // Work-around for gcc 7. It doesn't like nested BOOL_SWITCH.
    // https://github.com/kokkos/kokkos-kernels/issues/349
    // https://github.com/HazyResearch/flash-attention/issues/21
    //assert(prefill_params.b >= decode_params.b);
    assert(prefill_params.h == decode_params.h);
    assert(prefill_params.d == decode_params.d);
    assert(prefill_params.seqlen_k == decode_params.seqlen_k);

    //fprintf(stderr, "p.b = %d, p.seqlen_q = %d, ", prefill_params.b, prefill_params.seqlen_q);
    //fprintf(stderr, "d.b = %d, d.seqlen_q = %d\n", decode_params.b, decode_params.seqlen_q);
    
    const int num_m_block_prefill = (prefill_params.seqlen_q + Kernel_traits_prefill::kBlockM - 1) / Kernel_traits_prefill::kBlockM;
    const int num_m_block_decode = (decode_params.seqlen_q + Kernel_traits_decode::kBlockM - 1) / Kernel_traits_decode::kBlockM;

    size_t num_blocks_prefill = (num_m_block_prefill * prefill_params.b * prefill_params.h * prefill_params.num_splits);
    size_t num_blocks_decode;
    if constexpr(DecodeIsSplit) {
        num_blocks_decode = num_m_block_decode * decode_params.num_splits * decode_params.b * decode_params.h;
    } else {
        num_blocks_decode = num_m_block_decode * decode_params.b * decode_params.h;
    }
    //fprintf(stderr, "nblks_p = %d, nblks_d = %d\n", int(num_blocks_prefill), int(num_blocks_decode));
    //dim3 grid(num_m_block_prefill, prefill_params.b, prefill_params.h);
    //const bool is_even_K = prefill_params.d == Kernel_traits_prefill::kHeadDim;
    const bool is_even_MN_prefill = prefill_params.cu_seqlens_q == nullptr && prefill_params.cu_seqlens_k == nullptr && prefill_params.seqlen_k % Kernel_traits_prefill::kBlockN == 0 && prefill_params.seqlen_q % Kernel_traits_prefill::kBlockM == 0;
    const bool is_even_MN_decode = decode_params.cu_seqlens_q == nullptr && decode_params.cu_seqlens_k == nullptr && decode_params.seqlen_k % Kernel_traits_decode::kBlockN == 0 && decode_params.seqlen_q % Kernel_traits_decode::kBlockM == 0;
    // We do not support these currently
    assert(prefill_params.alibi_slopes_ptr == nullptr);
    assert(decode_params.alibi_slopes_ptr == nullptr);
    assert(prefill_params.softcap == 0.0);
    assert(decode_params.softcap == 0.0);
    //const bool return_softmax = params.p_ptr != nullptr;
    //EVENK_SWITCH(is_even_K, IsEvenKConst, [&] {
    constexpr static bool IsEvenKConst = true;
        BOOL_SWITCH(is_even_MN_prefill, IsEvenMNConst_p, [&] {
            BOOL_SWITCH(is_even_MN_decode, IsEvenMNConst_d, [&] {
                //BOOL_SWITCH(decode_params.num_splits > 1, DecodeIsSplit, [&] {
                    BOOL_SWITCH(decode_params.knew_ptr != nullptr, DecodeAppend_KV, [&] {
                    //EVENK_SWITCH(is_even_K_decode, IsEvenKConst_d, [&] {
                    BOOL_SWITCH(decode_params.is_causal, Is_causal_d, [&] {
                        LOCAL_SWITCH((prefill_params.window_size_left >= 0 || prefill_params.window_size_right >= 0) && !Is_causal_p, Is_local_p, [&] {
                            LOCAL_SWITCH((decode_params.window_size_left >= 0 || decode_params.window_size_right >= 0) && !Is_causal_d, Is_local_d, [&] {
                                BOOL_SWITCH(PrefillIsSplit || prefill_params.block_table != nullptr, UseSplitPrefill, [&] {
                                BOOL_SWITCH(DecodeIsSplit || DecodeAppend_KV || decode_params.cache_batch_idx != nullptr || decode_params.block_table != nullptr, UseSplitDecode, [&] {
                                //BOOL_SWITCH(false, ReturnSoftmaxConst, [&] {
                                constexpr static bool ReturnSoftmaxConst = false;
                                // Will only return softmax if dropout, to reduce compilation time.
                                // If not IsEvenKConst, we also set IsEvenMNConst to false to reduce number of templates.
                                // If return_softmax, set IsEvenMNConst to false to reduce number of templates
                                // If head dim > 128, set IsEvenMNConst to false to reduce number of templates
                                // If Is_local, set Is_causal to false
                                    // Can we preallocate this somewhere? Seems kinda clunky doing it here.
                                    auto numSMs = at::cuda::getCurrentDeviceProperties()->multiProcessorCount;
                                    int *tbAssign = nullptr;
                                    cudaMalloc(&tbAssign, sizeof(int) * (numSMs + 2));
                                    cudaMemset(tbAssign, 0, sizeof(int) * (numSMs + 2));
                                    
                                    static constexpr int num_threads = Kernel_traits_prefill::kNThreads > Kernel_traits_decode::kNThreads ? 
                                       Kernel_traits_prefill::kNThreads : Kernel_traits_decode::kNThreads;
                                    // Find the logical threadblocks per real threadblock
                                    static constexpr int blk_factor_p = num_threads / Kernel_traits_prefill::kNThreads;
                                    static constexpr int blk_factor_d = num_threads / Kernel_traits_decode::kNThreads;
                                    // Persistent threads
                                    if constexpr(fused_op & 128) {
                                        // 2 TB per SM
                                        int grid = numSMs * (256 / num_threads);
                                        size_t smem_size = max(Kernel_traits_prefill::kSmemSize * blk_factor_p, Kernel_traits_decode::kSmemSize * blk_factor_d);
                                        auto kernel = &true_fused_pt_tb_fwd_kernel<Kernel_traits_prefill, Kernel_traits_decode, 
                                            Is_dropout && !false, Is_causal_p, Is_causal_d, Is_local_p && !Is_causal_p, Is_local_d && !Is_causal_d, false, 
                                            IsEvenMNConst_p && IsEvenKConst && !Is_local_p && !ReturnSoftmaxConst && Kernel_traits_prefill::kHeadDim <= 128, IsEvenKConst, 
                                            IsEvenMNConst_d && !DecodeAppend_KV && IsEvenKConst && !Is_local_d && Kernel_traits_decode::kHeadDim <= 128, IsEvenKConst, 
                                            false, ReturnSoftmaxConst && Is_dropout && !false, PrefillIsSplit, DecodeIsSplit, DecodeAppend_KV, fused_op, 
                                            UseSplitPrefill, UseSplitDecode>;
                                        if (smem_size >= 48 * 1024) {
                                            C10_CUDA_CHECK(cudaFuncSetAttribute(
                                                kernel, cudaFuncAttributeMaxDynamicSharedMemorySize, smem_size));
                                        }
                                        kernel<<<grid, num_threads, smem_size, stream>>>(prefill_params, decode_params, tbAssign);
                                    } else {
                                        dim3 grid = dim3((num_blocks_prefill + blk_factor_p - 1) / blk_factor_p + (num_blocks_decode + blk_factor_d - 1) / blk_factor_d, 1, 1);
                                        size_t smem_size = max(Kernel_traits_prefill::kSmemSize * blk_factor_p, Kernel_traits_decode::kSmemSize * blk_factor_d);
                                        auto kernel = &true_fused_tb_fwd_kernel<Kernel_traits_prefill, Kernel_traits_decode, 
                                            Is_dropout && !false, Is_causal_p, Is_causal_d, Is_local_p && !Is_causal_p, Is_local_d && !Is_causal_d, false, 
                                            IsEvenMNConst_p && IsEvenKConst && !Is_local_p && !ReturnSoftmaxConst && Kernel_traits_prefill::kHeadDim <= 128, IsEvenKConst, 
                                            IsEvenMNConst_d && !DecodeAppend_KV && IsEvenKConst && !Is_local_d && Kernel_traits_decode::kHeadDim <= 128, IsEvenKConst, 
                                            false, ReturnSoftmaxConst && Is_dropout && !false, PrefillIsSplit, DecodeIsSplit, DecodeAppend_KV, fused_op, 
                                            UseSplitPrefill, UseSplitDecode>;
                                        if (smem_size >= 48 * 1024) {
                                            C10_CUDA_CHECK(cudaFuncSetAttribute(
                                                kernel, cudaFuncAttributeMaxDynamicSharedMemorySize, smem_size));
                                        }
                                        kernel<<<grid, num_threads, smem_size, stream>>>(prefill_params, decode_params, tbAssign);
                                    }
                                    C10_CUDA_KERNEL_LAUNCH_CHECK();
                                //});
                                    });
                                    });
                                });
                            });
                        });
                    });
                //});
            });
        });
        if constexpr(PrefillIsSplit) {
            // We want kBlockM to be as small as possible for more parallelism.
            // With 128 threads we can load 512 elements at a time, so if headdim is divisible by 128, kBlockM = 4.
            // If headdim is divisible by 64, then we set kBlockM = 8, etc.
            constexpr static int kBlockM = Kernel_traits_prefill::kHeadDim % 128 == 0 ? 4 : (Kernel_traits_prefill::kHeadDim % 64 == 0 ? 8 : 16);
            dim3 grid_combine((prefill_params.b * prefill_params.h * prefill_params.seqlen_q + kBlockM - 1) / kBlockM);
            // Below kernels REQUIRE 128 threads.
            //EVENK_SWITCH(is_even_K, IsEvenKConst, [&] {
                const int num_threads = 128;
                if (prefill_params.num_splits <= 2) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_prefill, kBlockM, 1, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(prefill_params);
                } else if (prefill_params.num_splits <= 4) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_prefill, kBlockM, 2, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(prefill_params);
                } else if (prefill_params.num_splits <= 8) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_prefill, kBlockM, 3, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(prefill_params);
                } else if (prefill_params.num_splits <= 16) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_prefill, kBlockM, 4, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(prefill_params);
                } else if (prefill_params.num_splits <= 32) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_prefill, kBlockM, 5, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(prefill_params);
                } else if (prefill_params.num_splits <= 64) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_prefill, kBlockM, 6, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(prefill_params);
                } else if (prefill_params.num_splits <= 128) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_prefill, kBlockM, 7, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(prefill_params);
                }
                C10_CUDA_KERNEL_LAUNCH_CHECK();
            //});
        }
        //printf("smem used: p = %d, d = %d\n", Kernel_traits_prefill::kSmemSize, Kernel_traits_decode::kSmemSize);
        if constexpr(DecodeIsSplit) {
            // We want kBlockM to be as small as possible for more parallelism.
            // With 128 threads we can load 512 elements at a time, so if headdim is divisible by 128, kBlockM = 4.
            // If headdim is divisible by 64, then we set kBlockM = 8, etc.
            constexpr static int kBlockM = Kernel_traits_decode::kHeadDim % 128 == 0 ? 4 : (Kernel_traits_decode::kHeadDim % 64 == 0 ? 8 : 16);
            dim3 grid_combine((decode_params.b * decode_params.h * decode_params.seqlen_q + kBlockM - 1) / kBlockM);
            // Below kernels REQUIRE 128 threads.
            //EVENK_SWITCH(is_even_K, IsEvenKConst, [&] {
                const int num_threads = 128;
                if (decode_params.num_splits <= 2) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_decode, kBlockM, 1, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(decode_params);
                } else if (decode_params.num_splits <= 4) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_decode, kBlockM, 2, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(decode_params);
                } else if (decode_params.num_splits <= 8) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_decode, kBlockM, 3, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(decode_params);
                } else if (decode_params.num_splits <= 16) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_decode, kBlockM, 4, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(decode_params);
                } else if (decode_params.num_splits <= 32) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_decode, kBlockM, 5, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(decode_params);
                } else if (decode_params.num_splits <= 64) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_decode, kBlockM, 6, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(decode_params);
                } else if (decode_params.num_splits <= 128) {
                    fused_fwd_splitkv_combine_kernel<Kernel_traits_decode, kBlockM, 7, IsEvenKConst><<<grid_combine, num_threads, 0, stream>>>(decode_params);
                }
                C10_CUDA_KERNEL_LAUNCH_CHECK();
            //});
        }
    //});
}

template<typename T, bool Is_causal, int fusedOp, bool DecodeSplit>
void run_true_fused_mha_fwd_hdim128(Flash_fwd_params &params_prefill, Flash_fwd_params &params_decode, cudaStream_t stream) {
    constexpr static int Headdim = 128;
    auto dprops = at::cuda::getCurrentDeviceProperties();
    //bool is_sm8x = dprops->major == 8 && dprops->minor > 0;
    //DROPOUT_SWITCH(params_prefill.p_dropout < 1.f, Is_dropout, [&] {
    // We do not support dropout
    assert(params_prefill.p_dropout < 1.f);
    constexpr static bool Is_dropout = false;
        if constexpr(!Is_dropout) {
            // For sm86 or sm89, 64 x 64 is the fastest for causal (because it's square),
            // and 128 x 32 (48 KB smem) is the fastest for non-causal since we get 2 CTAs per SM.
            /*if (is_sm8x) {
                if constexpr(!Is_causal) {
                    using traits_p = Flash_fwd_kernel_traits<Headdim, 128, 32, 4, false, false, T>;
                    using traits_d = Flash_fwd_kernel_traits<Headdim, 32, 32, 1, false, false, T>;
                    run_true_fused_fwd<traits_p, traits_d, Is_dropout, Is_causal>(params_prefill, params_decode, stream);
                } else {
                    using traits_p = Flash_fwd_kernel_traits<Headdim, 64, 64, 4, false, false, T>;
                    using traits_d = Flash_fwd_kernel_traits<Headdim, 32, 32, 1, false, false, T>;
                    run_true_fused_fwd<traits_p, traits_d, Is_dropout, Is_causal>(params_prefill, params_decode, stream);
                }
            } else {*/
#ifdef HFUSE
                if constexpr(fusedOp == 64) {
                    // --------------------------> HFUSED CODE <--------------------------
                    const bool prefill_split = params_prefill.num_splits > 1;
                    if(!prefill_split) {
                        using traits_p = Flash_fwd_kernel_traits<Headdim, 128, 64, 4, false, false, T>;
                        using traits_d = Flash_fwd_kernel_traits<Headdim, 64, 128, 4, false, false, T>;
                        run_hfused_fwd<traits_p, traits_d, Is_dropout, Is_causal, fusedOp, DecodeSplit>(params_prefill, params_decode, stream);
                    } else {
                        // Just for clarity.
                        constexpr int PrefillSplit = true;
                        using traits_p = Flash_fwd_kernel_traits<Headdim, 64, 128, 4, false, false, T>;
                        using traits_d = Flash_fwd_kernel_traits<Headdim, 64, 128, 4, false, false, T>;
                        run_hfused_fwd<traits_p, traits_p, Is_dropout, Is_causal, fusedOp, DecodeSplit, PrefillSplit>(params_prefill, params_decode, stream);
                    }
                    return;
                }
#endif
                if constexpr(fusedOp & 8) {
                    // Split kernel requires tile lengths (64, 128). Non-split we can play around with.
                    const bool prefill_split = params_prefill.num_splits > 1;
                    // (64, 128) -> for split decodes; (16, 32) -> for non-split decodes
                    constexpr int QDim_d = DecodeSplit ? 64 : 16;
                    constexpr int KVDim_d = DecodeSplit ? 128 : 32;
                    constexpr int Warps_d = DecodeSplit ? 4 : 1;
                    // Restrict decode tile size to 16 x HeadDim, for minimal compute utilization
                    using traits_d = Flash_fwd_kernel_traits<Headdim, QDim_d, KVDim_d, Warps_d, false, false, T>;
                    if(!prefill_split) {
                        if constexpr(fusedOp & 2) {
                            using traits_p = Flash_fwd_kernel_traits<Headdim, 64, 32, 2, false, false, T>;
                            run_true_fused_fwd<traits_p, traits_d, Is_dropout, Is_causal, fusedOp, DecodeSplit>(params_prefill, params_decode, stream);
                        } else if constexpr(fusedOp & 4) {
                            using traits_p = Flash_fwd_kernel_traits<Headdim, 16, 32, 1, false, false, T>;
                            run_true_fused_fwd<traits_p, traits_d, Is_dropout, Is_causal, fusedOp, DecodeSplit>(params_prefill, params_decode, stream);
                        } else {
                            using traits_p = Flash_fwd_kernel_traits<Headdim, 128, 64, 4, false, false, T>;
                            run_true_fused_fwd<traits_p, traits_d, Is_dropout, Is_causal, fusedOp, DecodeSplit>(params_prefill, params_decode, stream);
                        }
                    } else {
                        // Just for clarity.
                        constexpr int PrefillSplit = true;
                        using traits_p = Flash_fwd_kernel_traits<Headdim, 64, 128, 4, false, false, T>;
                        run_true_fused_fwd<traits_p, traits_d, Is_dropout, Is_causal, fusedOp, DecodeSplit, PrefillSplit>(params_prefill, params_decode, stream);
                    }
                } else {
                    if constexpr(fusedOp & 2) {
                        using traits_p = Flash_fwd_kernel_traits<Headdim, 64, 32, 2, false, false, T>;
                        using traits_d = Flash_fwd_kernel_traits<Headdim, 32, 64, 2, false, false, T>;
                        run_true_fused_fwd<traits_p, traits_d, Is_dropout, Is_causal, fusedOp, DecodeSplit>(params_prefill, params_decode, stream);
                    } else if constexpr(fusedOp & 4) {
                        using traits_p = Flash_fwd_kernel_traits<Headdim, 16, 32, 1, false, false, T>;
                        using traits_d = Flash_fwd_kernel_traits<Headdim, 16, 32, 1, false, false, T>;
                        run_true_fused_fwd<traits_p, traits_d, Is_dropout, Is_causal, fusedOp, DecodeSplit>(params_prefill, params_decode, stream);
                    } else {
                        using traits_p = Flash_fwd_kernel_traits<Headdim, 128, 64, 4, false, false, T>;
                        using traits_d = Flash_fwd_kernel_traits<Headdim, 64, 128, 4, false, false, T>;
                        run_true_fused_fwd<traits_p, traits_d, Is_dropout, Is_causal, fusedOp, DecodeSplit>(params_prefill, params_decode, stream);
                    }
                }
            //}
            // run_flash_fwd<Flash_fwd_kernel_traits<Headdim, 128, 64, 4, true, false, T>, Is_dropout, Is_causal>(params, stream);
            // run_flash_fwd<Flash_fwd_kernel_traits<Headdim, 128, 64, 4, true, true, T>, Is_dropout, Is_causal>(params, stream);
            // run_flash_fwd<Flash_fwd_kernel_traits<Headdim, 64, 128, 4, false, false, T>, Is_dropout, Is_causal>(params, stream);
            // Using 8 warps (128 x 128 and 256 x 64) is 28% slower for seqlen=2k
            // run_flash_fwd<Flash_fwd_kernel_traits<Headdim, 128, 128, 8, false, false, T>, Is_dropout, Is_causal>(params, stream);
            // run_flash_fwd<Flash_fwd_kernel_traits<Headdim, 128, 64, 8, false, false, T>, Is_dropout, Is_causal>(params, stream);
            // 1st ones are good for H100, A100
            // 2nd one is good for A6000 bc we get slightly better occupancy
        } else {
            using traits = Flash_fwd_kernel_traits<Headdim, 128, 32, 4, false, false, T>;
            run_true_fused_fwd<traits, traits, Is_dropout, Is_causal, fusedOp, DecodeSplit>(params_prefill, params_decode, stream);
            // run_flash_fwd<Flash_fwd_kernel_traits<Headdim, 64, 64, 4, false, false, T>, Is_dropout, Is_causal>(params, stream);
            // run_flash_fwd<Flash_fwd_kernel_traits<Headdim, 128, 32, 4, true, false, T>, Is_dropout, Is_causal>(params, stream);
            // run_flash_fwd<Flash_fwd_kernel_traits<Headdim, 128, 32, 4, true, true, T>, Is_dropout, Is_causal>(params, stream);
        }
    //});
}