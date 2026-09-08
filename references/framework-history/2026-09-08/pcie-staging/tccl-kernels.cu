#include "kernels_v2.hpp"
#include "check.hpp"

typedef ulong2 Pack128;

inline __device__ void Fetch128(Pack128& v, const Pack128* p) {
  asm volatile("ld.volatile.global.v2.u64 {%0,%1}, [%2];" : "=l"(v.x), "=l"(v.y) : "l"(p) : "memory");
}

inline __device__ void Store128(Pack128* p, Pack128& v) {
  asm volatile("st.volatile.global.v2.u64 [%0], {%1,%2};" :: "l"(p), "l"(v.x), "l"(v.y) : "memory");
}

__global__ void gpu_copy_multi_channel(float** dsts, float** srcs, size_t* nbytess) {
  int channel = blockIdx.x;
  size_t idx = threadIdx.x;
  size_t stride = blockDim.x;
  float* dst = dsts[channel];
  float* src = srcs[channel];
  size_t nelem = nbytess[channel] / sizeof(Pack128);
  for (size_t i = idx; i < nelem; i += stride) {
    Pack128 v;
    Fetch128(v, ((Pack128*)src) + i);
    Store128(((Pack128*)dst) + i, v);
  }
}

void gpu_copy_wrapper_multi_channel(float** dsts, float** srcs, size_t* nbytess, int nchannels, int gpu_idx) {
  CHECK_CUDA(cudaSetDevice(gpu_idx));
  gpu_copy_multi_channel<<<nchannels, 1024>>>(dsts, srcs, nbytess);
  CHECK_CUDA(cudaDeviceSynchronize());
  CHECK_CUDA(cudaGetLastError());
}

__global__ void gpu_copy_single_channel(float* dst, float* src, size_t nbytes) {
  size_t idx = threadIdx.x;
  size_t stride = blockDim.x;
  size_t nelem = nbytes / sizeof(Pack128);
  for (size_t i = idx; i < nelem; i += stride) {
    Pack128 v;
    Fetch128(v, ((Pack128*)src) + i);
    Store128(((Pack128*)dst) + i, v);
  }
}

__global__ void gpu_copy_full_v2(float* dst, float* src, size_t nbytes) {
  size_t idx = threadIdx.x + blockIdx.x * blockDim.x;
  size_t stride = blockDim.x * gridDim.x;
  size_t nelem = nbytes / sizeof(Pack128);
  #define UNROLL 2
  for (size_t i = idx; i < nelem; i += stride * UNROLL) {
    Pack128 v[UNROLL];
    for (int j = 0; j < UNROLL; ++j) {
      if (i + stride * j < nelem)
        v[j] = ((Pack128*)src)[i + stride * j];
    }
    for (int j = 0; j < UNROLL; ++j) {
      if (i + stride * j < nelem)
        ((Pack128*)dst)[i + stride * j] = v[j];
    }
  }
  #undef UNROLL
}

void gpu_copy_wrapper_single_channel(float* dst, float* src, size_t nbytes, int gpu_idx) {
  CHECK_CUDA(cudaSetDevice(gpu_idx));
  //gpu_copy_full_v2<<<1, 256>>>(dst, src, nbytes);
  //gpu_copy_full_v2<<<1, 1024>>>(dst, src, nbytes);
  gpu_copy_full_v2<<<10, 1024>>>(dst, src, nbytes);
  CHECK_CUDA(cudaDeviceSynchronize());
  CHECK_CUDA(cudaGetLastError());
}

void gpu_copy_wrapper_memcpy(float* dst, float* src, size_t nbytes, int gpu_idx) {
  CHECK_CUDA(cudaSetDevice(gpu_idx));
  CHECK_CUDA(cudaMemcpy(dst, src, nbytes, cudaMemcpyDefault));
  CHECK_CUDA(cudaDeviceSynchronize());
  CHECK_CUDA(cudaGetLastError());
}