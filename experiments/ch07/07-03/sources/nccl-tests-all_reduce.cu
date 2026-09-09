/*************************************************************************
 * Copyright (c) 2016-2022, NVIDIA CORPORATION. All rights reserved.
 *
 * See LICENSE.txt for license information
 ************************************************************************/

/*
 * AllReduce Performance Test Implementation
 *
 * This file implements multiple AllReduce kernel variants optimized for different
 * use cases within CUDA P2P connectivity.
 * These kernels are designed to highlight the device API functionality. As well as how to optimize for best performance.
 *
 * IMPORTANT: All custom kernels require CUDA P2P connectivity since they require Load-Store Accessible (LSA) memory.
 *
 * Kernel Selection Strategy:
 * - deviceImpl = 0: NCCL's built-in AllReduce implementation (fallback)
 * - deviceImpl = 1: allReduceLsaKernel - Basic LSA implementation for demonstration and small message sizes.
 * - deviceImpl = 2: allReduceLsaVectorizedKernel - Vectorized LSA for demonstration to achieve performance for large message sizes.
 * - deviceImpl = 3: allReduceMultimemKernel - Multi-memory for hardware acceleration. Requires Multimem capable hardware but can offer better performance.
 * - deviceImpl = 4: allReduceMultimemVectorizedKernel - Vectorized multi-memory for best performance. Requires Multimem capable hardware but can offer better performance.
 */

#include "cuda_runtime.h"
#include "common.h"
#include <algorithm>
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,28,0)
#include "nccl_device.h"
#include "vector_types.h"
#include "multimem_ops.h"
constexpr int WARP_SIZE = 32;
#endif

void AllReduceGetCollByteCount(size_t *sendcount, size_t *recvcount, size_t *paramcount, size_t *sendInplaceOffset, size_t *recvInplaceOffset, size_t count, size_t eltSize, int nranks) {
  *sendcount = count;
  *recvcount = count;
  *sendInplaceOffset = 0;
  *recvInplaceOffset = 0;
  *paramcount = *sendcount;
}

testResult_t AllReduceInitData(struct threadArgs* args, ncclDataType_t type, ncclRedOp_t op, int root, int rep, int in_place) {
  size_t sendcount = args->sendBytes / wordSize(type);
  size_t recvcount = args->expectedBytes / wordSize(type);
  int nranks = args->nProcs*args->nThreads*args->nGpus;

  for (int i=0; i<args->nGpus; i++) {
    CUDACHECK(cudaSetDevice(args->gpus[i]));
    int rank = ((args->proc*args->nThreads + args->thread)*args->nGpus + i);
    CUDACHECK(cudaMemset(args->recvbuffs[i], 0, args->expectedBytes));
    void* data = in_place ? args->recvbuffs[i] : args->sendbuffs[i];
    TESTCHECK(InitData(data, sendcount, 0, type, op, rep, nranks, rank));
    TESTCHECK(InitDataReduce(args->expected[i], recvcount, 0, type, op, rep, nranks));
    CUDACHECK(cudaDeviceSynchronize());
  }
  return testSuccess;
}

void AllReduceGetBw(size_t count, size_t typesize, double sec, double* algBw, double* busBw, int nranks) {
  double baseBw = (double)(count * typesize) / 1.0E9 / sec;

  *algBw = baseBw;
  double factor = ((double)(2*(nranks - 1)))/((double)nranks);
  *busBw = baseBw * factor;
}

#if NCCL_VERSION_CODE >= NCCL_VERSION(2,29,0)
 // set devComm reqs for allreduce device kernels
testResult_t AllReduceGetDevCommRequirements(int deviceImpl, ncclDevCommRequirements* reqs, ncclComm_t comm) {
  if (!reqs || !comm) return testInternalError;

  ncclCommProperties_t commProperties = NCCL_COMM_PROPERTIES_INITIALIZER;
  if (ncclCommQueryProperties(comm, &commProperties) != ncclSuccess) {
    return testNcclError;
  }

  if (deviceImpl > 0 && commProperties.nRanks != ncclTeamLsa(comm).nRanks) {
    fprintf(
        stderr,
        "DeviceImplementation > 1 requires CUDA P2P connectivity across all "
        "ranks. Not all ranks of this communicator have P2P connectivity.\n");
    return testInvalidUsage;
  }

  switch(deviceImpl) {
    case 1: // allReduceLsaKernel
    case 2: // allReduceLsaVectorizedKernel
      reqs->lsaBarrierCount = deviceCtaCount;
      return testSuccess;
    case 3: // allReduceMultimemKernel
    case 4: // allReduceMultimemVectorizedKernel
      if (!commProperties.multimemSupport) {
        fprintf(stderr, "This test requires multimem support, but multimem support is not enabled for this communicator.\n");
        return testInvalidUsage;
      }
      reqs->lsaMultimem = true;
      reqs->lsaBarrierCount = deviceCtaCount;
      return testSuccess;
    default:
      return testNotImplemented;
  }
}
#elif NCCL_VERSION_CODE >= NCCL_VERSION(2,28,0)
 bool AllReduceGetDevCommRequirements(int deviceImpl, ncclDevCommRequirements* reqs) {
   if (!reqs) return false;
   memset(reqs, 0, sizeof(*reqs));
   switch(deviceImpl) {
    case 1: // allReduceLsaKernel
    case 2: // allReduceLsaVectorizedKernel
      reqs->lsaBarrierCount = deviceCtaCount;
      return true;
    case 3: // allReduceMultimemKernel
    case 4: // allReduceMultimemVectorizedKernelMultimem = true;
    reqs->lsaMultimem = true;
    reqs->lsaBarrierCount = deviceCtaCount;
      return true;
    default:
      return false;
  }
 }
#endif

#if NCCL_VERSION_CODE >= NCCL_VERSION(2,28,0)
/*
 * Kernel 1: allReduceLsaKernel - Basic LSA-based AllReduce
 *
 * Purpose: Provides a simple, deterministic AllReduce implementation for small to
 * medium message sizes within CUDA P2P connectivity.
 *
 * Solution: Implements AllReduce using direct peer-to-peer memory access through
 * LSA windows. Each rank reads from all other ranks, performs reduction, and
 * writes the result back to all ranks using cooperative thread arrays.
 *
 * Key Optimizations:
 * - LSA barriers for faster synchronization than global barriers
 * - Global grid stride loop to distribute work across all ranks
 * - Direct peer access within CUDA P2P connectivity for optimal bandwidth
 *
 * CUDA P2P Connectivity Requirement: CRITICAL - This kernel requires all participating
 * ranks to be within the same CUDA P2P connectivity.
 *
 * Use Case: Small to medium messages (< 1MB) where simplicity and determinism
 * are more important than maximum bandwidth.
 */
template <typename T>
__global__ void allReduceLsaKernel(ncclWindow_t sendwin, size_t sendoffset, ncclWindow_t recvwin, size_t recvoffset, size_t count, int root, struct ncclDevComm devComm) {
  ncclLsaBarrierSession<ncclCoopCta> bar { ncclCoopCta(), devComm, ncclTeamLsa(devComm), devComm.lsaBarrier, blockIdx.x };
  bar.sync(ncclCoopCta(), cuda::memory_order_acquire);

  const int rank = devComm.rank, nRanks = devComm.nRanks;

  const int globalTid = threadIdx.x + blockDim.x * (rank + blockIdx.x * nRanks);
  const int globalNthreads = blockDim.x * gridDim.x * nRanks;

  for (size_t offset = globalTid; offset < count; offset += globalNthreads) {
    T v = T{0};
    for (int peer=0; peer<nRanks; peer++) {
      T* sendPtr = (T*)ncclGetLsaPointer(sendwin, sendoffset, peer);
      v += sendPtr[offset];
    }
    for (int peer=0; peer<nRanks; peer++) {
      T* recvPtr = (T*)ncclGetLsaPointer(recvwin, recvoffset, peer);
      recvPtr[offset] = v;
    }
  }
  bar.sync(ncclCoopCta(), cuda::memory_order_release);
}

/*
 * Kernel 2: allReduceLsaVectorizedKernel - Vectorized LSA-based AllReduce
 *
 * Purpose: Enhanced AllReduce implementation using vectorized memory operations
 * and loop unrolling to maximize memory bandwidth utilization for large messages
 * within CUDA P2P connectivity.
 *
 * Solution: Builds upon the basic LSA approach but adds vectorized loads/stores
 * and aggressive loop unrolling to achieve higher memory bandwidth. Handles
 * misaligned data gracefully while maximizing vectorized throughput. Not necessarily optimal for small message sizes.
 *
 * Key Optimizations:
 * - Vectorized loads/stores for improved memory bandwidth (128-bit operations)
 * - Loop unrolling to reduce loop overhead and improve instruction-level parallelism
 * - Warp-coalesced memory access patterns for optimal memory controller utilization
 * - Graceful handling of misaligned data with scalar fallback, comes at the cost of higher latency if not required.
 *
 * CUDA P2P Connectivity Requirement: CRITICAL - Same as basic LSA kernel. Requires
 * CUDA P2P connectivity due to LSA memory access patterns.
 *
 * Use Case: Large messages where maximum memory bandwidth is
 * critical and data alignment can be optimized.
 */
template <typename T>
__global__ void allReduceLsaVectorizedKernel(ncclWindow_t sendwin, size_t sendoffset, ncclWindow_t recvwin, size_t recvoffset, size_t count, int root, struct ncclDevComm devComm) {
  ncclLsaBarrierSession<ncclCoopCta> bar { ncclCoopCta(), devComm, ncclTeamLsa(devComm), devComm.lsaBarrier, blockIdx.x };
  bar.sync(ncclCoopCta(), cuda::memory_order_acquire);

  // Compile time vector type and vector size mapping
  using TN = typename VectorTypeMapping<T>::Type;
  constexpr int VECTOR_FACTOR = sizeof(TN)/sizeof(T);

  constexpr int UNROLL_FACTOR = 128/sizeof(TN); // Same as before 128 Bytes per thread

  const int rank = devComm.rank, nRanks = devComm.nRanks;

  const int globalTid = threadIdx.x + blockDim.x * (rank + blockIdx.x * nRanks);
  const int globalNthreads = blockDim.x * gridDim.x * nRanks;

  // Since we use vector types, the non-vector allocated memory is not necessarily aligned.
  const size_t alignment_offset = (sendoffset % sizeof(TN)) / sizeof(T);
  const size_t aligned_count = count - alignment_offset;
  const size_t vector_count = aligned_count / VECTOR_FACTOR;
  const size_t remainder = aligned_count % VECTOR_FACTOR;

  // As before
  const int elements_per_block = globalNthreads * UNROLL_FACTOR;
  const int num_blocks = vector_count / elements_per_block;

  const int warp_id = globalTid / WARP_SIZE;
  const int lane_id = globalTid % WARP_SIZE;

  const int warp_offset = warp_id * WARP_SIZE * UNROLL_FACTOR;
  const int lane_offset = lane_id;
  const int warp_lane_offset = warp_offset + lane_offset;

  // Handle misaligned elements first using scalar operations. Grid stride loop with scalar handling
  if (alignment_offset > 0) {
    for (size_t offset = globalTid; offset < alignment_offset; offset += globalNthreads) {
      T v_scalar = T{0};

      for (int peer=0; peer<nRanks; peer++) {
        T* remotePtr = (T*)ncclGetLsaPointer(sendwin, sendoffset, peer);
        v_scalar += remotePtr[offset];
      }

      for (int peer=0; peer<nRanks; peer++) {
        T* remotePtr = (T*)ncclGetLsaPointer(recvwin, recvoffset, peer);
        remotePtr[offset] = v_scalar;
      }
    }
  }

  // Handle vectorized memory that can be handled in whole chunks (no if)
  for (int block = 0; block < num_blocks; block += 1) {
    TN v[UNROLL_FACTOR] = {TN{0}};
    const size_t block_offset = block * globalNthreads * UNROLL_FACTOR;
    for (int peer=0; peer<nRanks; peer++) {
#pragma unroll
      for (int i=0; i < UNROLL_FACTOR; i++) {
        const int stride_offset = i * WARP_SIZE;
        const size_t offset = warp_lane_offset + block_offset + stride_offset;
        // Uses TN* as pointer type for vectorized pointer arithmatic
        // The pointer is also adjusted for misalignment
        TN* remotePtr = (TN*)ncclGetLsaPointer(sendwin, sendoffset + alignment_offset * sizeof(T), peer);
        v[i] = vectorAdd(v[i], remotePtr[offset]);
      }
    }
    for (int peer=0; peer<nRanks; ++peer) {
#pragma unroll
      for (int i=0; i < UNROLL_FACTOR; i++) {
        const int stride_offset = i * WARP_SIZE;
        const size_t offset = warp_lane_offset + block_offset + stride_offset;
        TN* remotePtr = (TN*)ncclGetLsaPointer(recvwin, recvoffset + alignment_offset * sizeof(T), peer);
        remotePtr[offset] = v[i];
      }
    }
  }

    // Handle the last partial vectorized block, but with if conditions
  const int block = num_blocks;
  TN v[UNROLL_FACTOR] = {TN{0}};
  const size_t block_offset = block * globalNthreads * UNROLL_FACTOR;
  for (int peer=0; peer<nRanks; peer++) {
#pragma unroll
      for (int i=0; i < UNROLL_FACTOR; i++) {
        const int stride_offset = i * WARP_SIZE;
        const size_t offset = warp_lane_offset + block_offset + stride_offset;
        if (offset < vector_count) {
          TN* remotePtr = (TN*)ncclGetLsaPointer(sendwin, sendoffset + alignment_offset * sizeof(T), peer);
          v[i] = vectorAdd(v[i], remotePtr[offset]);
        }
      }
  }
  for (int peer=0; peer<nRanks; ++peer) {
#pragma unroll
      for(int i=0; i < UNROLL_FACTOR; i++){
        const int stride_offset = i * WARP_SIZE;
        const size_t offset = warp_lane_offset + block_offset + stride_offset;
        if (offset < vector_count) {
          TN* remotePtr = (TN*)ncclGetLsaPointer(recvwin, recvoffset + alignment_offset * sizeof(T), peer);
          remotePtr[offset] = v[i];
        }
      }
  }

  // Since the data doesn't have to be perfectly aligned with the vector size, we need to handle remaining elements.
  if (remainder > 0) {
    const size_t remainder_start = alignment_offset + vector_count * VECTOR_FACTOR;
    const int globalTid_remainder = globalTid;
    const int globalNthreads_remainder = globalNthreads;

    for (size_t offset = globalTid_remainder; offset < remainder; offset += globalNthreads_remainder) {
      T v_scalar = 0;
      const size_t actual_offset = remainder_start + offset;

      for (int peer=0; peer<nRanks; peer++) {
        T* remotePtr = (T*)ncclGetLsaPointer(sendwin, sendoffset, peer);
        v_scalar += remotePtr[actual_offset];
      }

      for (int peer=0; peer<nRanks; peer++) {
        T* remotePtr = (T*)ncclGetLsaPointer(recvwin, recvoffset, peer);
        remotePtr[actual_offset] = v_scalar;
      }
    }
  }

  // Sync
  bar.sync(ncclCoopCta(), cuda::memory_order_release);
}

/*
 * Kernel 3: allReduceMultimemKernel - Multi-memory Hardware-Accelerated AllReduce
 *
 * Purpose: High-performance AllReduce implementation using multi-memory primitives
 * that leverage hardware acceleration for memory operations, significantly reducing
 * SM utilization while maintaining high bandwidth within CUDA P2P connectivity.
 *
 * Solution: Replaces the O(Nrank) peer loop approach with hardware-accelerated
 * multi-memory operations. The kernel initiates CUDA P2P reductions directly through
 * hardware, eliminating the need for explicit peer-to-peer communication loops.
 *
 * Key Optimizations:
 * - Multi-memory primitives for hardware-accelerated operations
 * - Eliminates O(Nrank) scaling by using hardware reduction capabilities
 * - Hardware-assisted memory synchronization and reduction
 *
 * CUDA P2P Connectivity Requirement: CRITICAL - Requires CUDA P2P connectivity and
 * multi-memory support. Hardware acceleration is only available within the
 * same CUDA P2P connectivity where multi-memory operations can be performed.
 *
 * Use Case: Large CUDA P2P connectivity where scaling to more ranks is desired.
 *
 * Hardware Requirements: Hopper+ architecture with multi-memory support enabled.
 */
template <typename T>
__global__ void allReduceMultimemKernel(ncclWindow_t sendwin, size_t sendoffset, ncclWindow_t recvwin, size_t recvoffset, size_t count, int root, struct ncclDevComm devComm) {
  ncclLsaBarrierSession<ncclCoopCta> bar { ncclCoopCta(), devComm, ncclTeamTagLsa(), blockIdx.x, true };
  bar.sync(ncclCoopCta(), cuda::memory_order_acquire);

  const int rank = devComm.rank, nRanks = devComm.nRanks;

  const int globalTid = threadIdx.x + blockDim.x * (rank + blockIdx.x * nRanks);
  const int globalNthreads = blockDim.x * gridDim.x * nRanks;

  T* send_ptr = reinterpret_cast<T*>(ncclGetLsaMultimemPointer(sendwin, sendoffset, devComm));
  T* recv_ptr = reinterpret_cast<T*>(ncclGetLsaMultimemPointer(recvwin, recvoffset, devComm));
  for (size_t offset=globalTid; offset < count; offset += globalNthreads) {
    if (offset < count) {
      T v = multimemLoadSum<T,T>(send_ptr + offset);
      multimemStore<T,T>(recv_ptr + offset, v);
    }
  }
  bar.sync(ncclCoopCta(), cuda::memory_order_release);
}

/*
 * Kernel 4: allReduceMultimemVectorizedKernel - Vectorized Multi-memory AllReduce
 *
 * Purpose: Ultimate performance AllReduce implementation combining multi-memory
 * hardware acceleration with vectorized operations and loop unrolling for maximum
 * bandwidth utilization within CUDA P2P connectivity.
 *
 * Solution: Combines the hardware acceleration benefits of multi-memory operations
 * with the bandwidth optimization techniques from vectorized kernels. This kernel
 * represents the highest performance option for large, aligned data sets.
 *
 * Key Optimizations:
 * - Multi-memory primitives for hardware-accelerated operations
 * - Vectorized loads/stores for maximum memory bandwidth (128-bit operations)
 * - Aggressive loop unrolling for improved instruction-level parallelism
 * - Warp-coalesced memory access patterns for optimal memory controller utilization
 * - Hardware-assisted memory synchronization and reduction
 * - Graceful handling of misaligned data with scalar fallback
 *
 * CUDA P2P Connectivity Requirement: CRITICAL - Requires CUDA P2P connectivity and
 * multi-memory support. This kernel leverages both P2P locality and hardware
 * acceleration for optimal performance.
 *
 * Hardware Requirements: Hopper+ architecture with multi-memory support enabled.
 *
 * Performance Note: This kernel provides the best performance for large, aligned
 * data sets but requires careful data alignment for optimal vectorization benefits.
 */
template <typename T>
__global__ void allReduceMultimemVectorizedKernel(ncclWindow_t sendwin, size_t sendoffset, ncclWindow_t recvwin, size_t recvoffset, size_t count, int root, struct ncclDevComm devComm) {
  ncclLsaBarrierSession<ncclCoopCta> bar { ncclCoopCta(), devComm, ncclTeamTagLsa(), blockIdx.x, true };

  bar.sync(ncclCoopCta(), cuda::memory_order_acquire);

  using TN = typename VectorTypeMapping<T>::Type;
  constexpr int VECTOR_FACTOR = sizeof(TN)/sizeof(T);

  constexpr int UNROLL_FACTOR = 128/sizeof(TN);

  const int rank = devComm.rank, nRanks = devComm.nRanks;

  const int globalTid = threadIdx.x + blockDim.x * (rank + blockIdx.x * nRanks);
  const int globalNthreads = blockDim.x * gridDim.x * nRanks;

  // Calculate alignment offset to handle misaligned elements first
  const size_t alignment_offset = (sendoffset % sizeof(TN)) / sizeof(T);
  const size_t aligned_count = count - alignment_offset;
  const size_t vector_count = aligned_count / VECTOR_FACTOR;
  const size_t remainder = aligned_count % VECTOR_FACTOR;

  const int elements_per_block = globalNthreads * UNROLL_FACTOR;
  const int num_blocks = vector_count / elements_per_block;

  const int warp_id = globalTid / WARP_SIZE;
  const int lane_id = globalTid % WARP_SIZE;

  const int warp_offset = warp_id * WARP_SIZE * UNROLL_FACTOR;
  const int lane_offset = lane_id;
  const int warp_lane_offset = warp_offset + lane_offset;

  // Multimem pointers that handle scalar access for misaligned and remainder elements
  T* send_ptr = reinterpret_cast<T*>(ncclGetLsaMultimemPointer(sendwin, sendoffset, devComm));
  T* recv_ptr = reinterpret_cast<T*>(ncclGetLsaMultimemPointer(recvwin, recvoffset, devComm));

  // Handle misaligned elements first using scalar operations
  if (alignment_offset > 0) {
    for (size_t offset = globalTid; offset < max(alignment_offset,count); offset += globalNthreads) {
      T v_scalar = multimemLoadSum<T,T>(send_ptr + offset);
      multimemStore<T,T>(recv_ptr+offset, v_scalar);
    }
  }

  // separate TN* for 2 reasons. a) alignment offset, b) pointer arithmetic with the vectorized type
  TN* send_ptrN = reinterpret_cast<TN*>(ncclGetLsaMultimemPointer(sendwin, sendoffset+alignment_offset*sizeof(T), devComm));
  TN* recv_ptrN = reinterpret_cast<TN*>(ncclGetLsaMultimemPointer(recvwin, recvoffset+alignment_offset*sizeof(T), devComm));

  // Handle vectorized memory that can be handled in whole chunks (no if)
  for (int block = 0; block < num_blocks; block += 1) {
    TN v[UNROLL_FACTOR] = {TN{0}};
    const size_t block_offset = block * globalNthreads * UNROLL_FACTOR;
#pragma unroll
    for (int i=0; i < UNROLL_FACTOR; i++) {
      const int stride_offset = i * WARP_SIZE;
      const size_t offset = warp_lane_offset + block_offset + stride_offset;
      v[i] = multimemLoadSum<T,TN>(reinterpret_cast<T*>(send_ptrN + offset));
    }

#pragma unroll
    for (int i=0; i < UNROLL_FACTOR; i++) {
      const int stride_offset = i * WARP_SIZE;
      const size_t offset = warp_lane_offset + block_offset + stride_offset;
      multimemStore<T,TN>(reinterpret_cast<T*>(recv_ptrN+offset), v[i]);
    }
  }

  // Handle the last partial vectorized block, but with if conditions
  const int block = num_blocks;
  TN v[UNROLL_FACTOR] = {TN{0}};
  const size_t block_offset = block * globalNthreads * UNROLL_FACTOR;
#pragma unroll
  for (int i=0; i < UNROLL_FACTOR; i++) {
    const int stride_offset = i * WARP_SIZE;
    const size_t offset = warp_lane_offset + block_offset + stride_offset;
    if (offset < vector_count) {
      v[i] = multimemLoadSum<T,TN>(reinterpret_cast<T*>(send_ptrN+offset));
    }
  }
#pragma unroll
  for (int i=0; i < UNROLL_FACTOR; i++) {
    const int stride_offset = i * WARP_SIZE;
    const size_t offset = warp_lane_offset + block_offset + stride_offset;
    if (offset < vector_count) {
      multimemStore<T,TN>(reinterpret_cast<T*>(recv_ptrN+offset), v[i]);
    }
  }

  // Handle remainder elements using scalar operations
  if (remainder > 0) {
    const size_t remainder_start = alignment_offset + vector_count * VECTOR_FACTOR;
    const int globalTid_remainder = globalTid;
    const int globalNthreads_remainder = globalNthreads;

    for (size_t offset = globalTid_remainder; offset < remainder; offset += globalNthreads_remainder) {
      const size_t actual_offset = remainder_start + offset;
      T v_scalar = multimemLoadSum<T,T>(send_ptr+actual_offset);
      multimemStore<T,T>(recv_ptr+actual_offset, v_scalar);
    }
  }

  // Sync
  bar.sync(ncclCoopCta(), cuda::memory_order_release);
}
#endif

testResult_t AllReduceRunColl(void* sendbuff, size_t sendoffset, void* recvbuff, size_t recvoffset, size_t count, ncclDataType_t type, ncclRedOp_t op, int root, ncclComm_t comm, cudaStream_t stream, int deviceImpl) {

  char* sptr = (char*)sendbuff + sendoffset;
  char* rptr = (char*)recvbuff + recvoffset;

  switch (deviceImpl) {
  case 0:
    NCCLCHECK(ncclAllReduce(sptr, rptr, count, type, op, comm, stream));
    return testSuccess;
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,28,0)
  case 1:
    TESTCHECK(testLaunchDeviceKernel(SPECIALIZE_KERNEL(allReduceLsaKernel, type, op),
               sendbuff, sendoffset, recvbuff, recvoffset, count, type, op, root, comm, stream));
    return testSuccess;
  case 2:
    TESTCHECK(testLaunchDeviceKernel(SPECIALIZE_KERNEL(allReduceLsaVectorizedKernel, type, op),
               sendbuff, sendoffset, recvbuff, recvoffset, count, type, op, root, comm, stream));
    return testSuccess;
  case 3:
    TESTCHECK(testLaunchDeviceKernel(SPECIALIZE_KERNEL(allReduceMultimemKernel, type, op),
               sendbuff, sendoffset, recvbuff, recvoffset, count, type, op, root, comm, stream));
    return testSuccess;
  case 4:
    TESTCHECK(testLaunchDeviceKernel(SPECIALIZE_KERNEL(allReduceMultimemVectorizedKernel, type, op),
               sendbuff, sendoffset, recvbuff, recvoffset, count, type, op, root, comm, stream));
    return testSuccess;
#endif
  }

  return testNotImplemented;
}

struct testColl allReduceTest = {
  "AllReduce",
  AllReduceGetCollByteCount,
  AllReduceInitData,
  AllReduceGetBw,
  AllReduceRunColl
};

void AllReduceGetBuffSize(size_t *sendcount, size_t *recvcount, size_t count, int nranks) {
  size_t paramcount, sendInplaceOffset, recvInplaceOffset;
  AllReduceGetCollByteCount(sendcount, recvcount, &paramcount, &sendInplaceOffset, &recvInplaceOffset, count, /*eltSize=*/1, nranks);
}

testResult_t AllReduceRunTest(struct threadArgs* args, int root, ncclDataType_t type, const char* typeName, ncclRedOp_t op, const char* opName) {
  args->collTest = &allReduceTest;
  ncclDataType_t *run_types;
  ncclRedOp_t *run_ops;
  const char **run_typenames, **run_opnames;
  int type_count, op_count;

  if ((int)type != -1) {
    type_count = 1;
    run_types = &type;
    run_typenames = &typeName;
  } else {
    type_count = test_typenum;
    run_types = test_types;
    run_typenames = test_typenames;
  }

  if ((int)op != -1) {
    op_count = 1;
    run_ops = &op;
    run_opnames = &opName;
  } else {
    op_count = test_opnum;
    run_ops = test_ops;
    run_opnames = test_opnames;
  }

  for (int i=0; i<type_count; i++) {
    for (int j=0; j<op_count; j++) {
      TESTCHECK(TimeTest(args, run_types[i], run_typenames[i], run_ops[j], run_opnames[j], -1));
    }
  }
  return testSuccess;
}

NCCL_WEAK struct testEngine ncclTestEngine = {
  /* .getBuffSize = */ AllReduceGetBuffSize,
  /* .runTest = */ AllReduceRunTest,
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,14,0)
  /* .initCommConfig = */ nullptr,
#endif
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,28,0)
  /* .getDevCommRequirements = */ AllReduceGetDevCommRequirements
#endif
};
