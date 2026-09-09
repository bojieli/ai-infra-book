/*************************************************************************
 * Copyright (c) 2016-2022, NVIDIA CORPORATION. All rights reserved.
 *
 * See LICENSE.txt for license information
 ************************************************************************/

#include "common.h"
#include <algorithm>
#include <cstdio>
#include <type_traits>
#include <limits>
#include <string.h>
#include <ctype.h>
#include <mutex>
#include <condition_variable>
#include <thread>
#include <vector>
#include "cuda.h"

#include "util.h"
#include "../verifiable/verifiable.h"

#if defined(NCCL_OS_LINUX)
#pragma weak ncclCommWindowRegister
#pragma weak ncclCommWindowDeregister
#pragma weak ncclDevCommCreate
#pragma weak ncclDevCommDestroy
#endif

#define DIVUP(x, y) \
    (((x)+(y)-1)/(y))

int test_ncclVersion = 0; // init'd with ncclGetVersion()

#if NCCL_MAJOR >= 2
  ncclDataType_t test_types[ncclNumTypes] = {
    ncclInt8, ncclUint8, ncclInt32, ncclUint32, ncclInt64, ncclUint64, ncclHalf, ncclFloat, ncclDouble
  #if HAVE_BF16
    , ncclBfloat16
  #endif
  #if HAVE_FP8
    , ncclFloat8e4m3, ncclFloat8e5m2
  #endif
  };
  const char *test_typenames[ncclNumTypes] = {
    "int8", "uint8", "int32", "uint32", "int64", "uint64", "half", "float", "double"
  #if HAVE_BF16
    , "bfloat16"
  #endif
  #if HAVE_FP8
    , "f8e4m3", "f8e5m2"
  #endif
  };
  int test_typenum = -1;

  const char *test_opnames[] = {"sum", "prod", "max", "min", "avg", "mulsum"};
  ncclRedOp_t test_ops[] = {ncclSum, ncclProd, ncclMax, ncclMin
  #if NCCL_VERSION_CODE >= NCCL_VERSION(2,10,0)
    , ncclAvg
  #endif
  #if NCCL_VERSION_CODE >= NCCL_VERSION(2,11,0)
    , ncclNumOps // stand in for ncclRedOpCreatePreMulSum() created on-demand
  #endif
  };
  int test_opnum = -1;
#else
  ncclDataType_t test_types[ncclNumTypes] = {ncclChar, ncclInt, ncclHalf, ncclFloat, ncclDouble, ncclInt64, ncclUint64};
  const char *test_typenames[ncclNumTypes] = {"char", "int", "half", "float", "double", "int64", "uint64"};
  int test_typenum = 7;
  const char *test_opnames[] = {"sum", "prod", "max", "min"};
  ncclRedOp_t test_ops[] = {ncclSum, ncclProd, ncclMax, ncclMin};
  int test_opnum = 4;
#endif

// For libnccl's < 2.13
#if defined(NCCL_OS_LINUX)
extern "C" __attribute__((weak)) char const* ncclGetLastError(ncclComm_t comm) {
  return "";
}
#elif defined(NCCL_OS_WINDOWS)
extern "C" char const* ncclGetLastError(ncclComm_t comm);
#endif

int is_main_proc = 0;
thread_local int is_main_thread = 0;
static const char* programName = nullptr;

// Command line parameter defaults
int nThreads = 1;
int nGpus = 1;
size_t minBytes = 32*1024*1024;
size_t maxBytes = 32*1024*1024;
size_t stepBytes = 1*1024*1024;
size_t stepFactor = 1;
int datacheck = 1;
int warmup_iters = 1;
int iters = 20;
int agg_iters = 1;
static int run_cycles = 1;
static int ncclop = ncclSum;
static int nccltype = ncclFloat;
static int ncclroot = 0;
int parallel_init = 0;
int blocking_coll = 0;
int per_iter_timing = 0;
int per_iter_skip = 0;
static int streamnull = 0;
static int timeout = 0;
int cudaGraphLaunches = 0;
static int report_cputime = 0;
static int report_timestamps = 0;
static int deviceImpl = 0;
static int hostRmaImpl = 0;
int unalign = 0;
int memory_report = 0;
int tuning = 0;

int deviceCtaCount = 16; // Default number of CTAs for device implementation
int rmaCtxCount = 1;     // Number of RMA contexts to provision for host RMA (-H)

// Report average iteration time: (0=RANK0,1=AVG,2=MIN,3=MAX)
static int average = 1;
#define LOCAL_REGISTER 1
#define SYMMETRIC_REGISTER 2
static int local_register = 0;
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,27,0)
static int ctaPolicy = -1;
#endif
static int minCudaArch = 1<<30;

enum output_file_type_t {
  JSON_FILE_OUTPUT,
  UNSPECIFIED_FILE_OUTPUT
};

// Return pointer to extension in `path` if one is found. An extension
// is the last `.` in the `path`, if there is no `/` following the `.`
// and there are characters after `.`.
//
// Therefore: returns 0 if no meaningful extension was found, or returns offset
// into string where extension begins
static const char *getExtension(const char *path) {
  if (path == nullptr) return nullptr;
  int last_dot = -1;
  int last_slash = -1;

  int pos;
  for (pos = 0; path[pos] != '\0'; ++pos) {
    switch (path[pos]) {
    case '.':
      last_dot = pos;
      break;
    case '/':
      last_slash = pos;
      break;
    default:
      break;
    }
  }

  if (last_dot > last_slash && last_dot + 1 != pos) {
    return path + last_dot + 1;
  }

  return nullptr;
}

static output_file_type_t classifyOutputFile(const char *filename) {
  const char *extension = getExtension(filename);
  if (extension != nullptr && ncclTestStrcasecmp(extension, "json") == 0) {
    return JSON_FILE_OUTPUT;
  }

  return UNSPECIFIED_FILE_OUTPUT;
}

static void outputFileInit(output_file_type_t output_file_type,
                           const char *output_file, char argc, char **argv, char **envp) {
  switch (output_file_type) {
  case JSON_FILE_OUTPUT:
    jsonOutputInit(output_file, argc, argv, envp);
    break;
  case UNSPECIFIED_FILE_OUTPUT:
  default:
    break;
  }
}

static void outputFileFinalize(output_file_type_t output_file_type) {
  switch (output_file_type) {
  case JSON_FILE_OUTPUT:
    jsonOutputFinalize();
    break;
  case UNSPECIFIED_FILE_OUTPUT:
  default:
    break;
  }
}

testResult_t initComms(ncclComm_t* comms, int nComms, int firstRank, int nRanks, int* cudaDevs, ncclUniqueId& ncclId) {
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,14,0)
  ncclConfig_t config = NCCL_CONFIG_INITIALIZER;
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,27,0)
  if (ctaPolicy >= 0)
    config.CTAPolicy = ctaPolicy;
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,28,0)
  config.nvlinkCentricSched = 1;
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,29,0)
  if (cudaGraphLaunches >= 1)
    config.graphUsageMode = 1;
  else
    config.graphUsageMode = 0;
#endif
#endif
#endif
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,31,0)
  if (hostRmaImpl) {
    config.numRmaCtx = rmaCtxCount;
    config.numRmaSig = NUM_RMA_SIG;
  }
#endif
  if (ncclTestEngine.initCommConfig)
    ncclTestEngine.initCommConfig(&config);
#endif

  NCCLCHECK(ncclGroupStart());
  for (int i=0; i<nComms; i++) {
    int rank = firstRank + i;
    CUDACHECK(cudaSetDevice(cudaDevs[i]));
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,14,0)
    NCCLCHECK(ncclCommInitRankConfig(comms+i, nRanks, ncclId, rank, &config));
#else
    NCCLCHECK(ncclCommInitRank(comms+i, nRanks, ncclId, rank));
#endif
  }
  NCCLCHECK(ncclGroupEnd());
  return testSuccess;
}

// NOTE: We use the binary system, so M=Mebibytes and G=Gibibytes
static double parsesize(const char *value) {
    long long int units;
    double size;
    char size_lit;

    int count = sscanf(value, "%lf %1s", &size, &size_lit);

    switch (count) {
    case 2:
      switch (size_lit) {
      case 'G':
      case 'g':
        units = 1024*1024*1024;
        break;
      case 'M':
      case 'm':
        units = 1024*1024;
        break;
      case 'K':
      case 'k':
        units = 1024;
        break;
      default:
        return -1.0;
      };
      break;
    case 1:
      units = 1;
      break;
    default:
      return -1.0;
    }

    return size * units;
}

testResult_t CheckDelta(void* results, void* expected, size_t count, size_t offset, ncclDataType_t type, ncclRedOp_t op, uint64_t seed, int nranks, int64_t *wrongEltN) {
  CUDACHECK(ncclVerifiableVerify(results, expected, count, (int)type, (int)op, nranks, seed, offset, wrongEltN, cudaStreamDefault));
  CUDACHECK(cudaDeviceSynchronize());
  return testSuccess;
}

testResult_t InitDataReduce(void* data, const size_t count, const size_t offset, ncclDataType_t type, ncclRedOp_t op, uint64_t seed, int nranks) {
  CUDACHECK(ncclVerifiablePrepareExpected(data, count, (int)type, (int)op, nranks, seed, offset, cudaStreamDefault));
  return testSuccess;
}

testResult_t InitData(void* data, const size_t count, size_t offset, ncclDataType_t type, ncclRedOp_t op, uint64_t seed, int nranks, int rank) {
  CUDACHECK(ncclVerifiablePrepareInput(data, count, (int)type, (int)op, nranks, rank, seed, offset, cudaStreamDefault));
  return testSuccess;
}

void Barrier(struct threadArgs *args) {
  thread_local int epoch = 0;
  static std::mutex lock[2];
  static std::condition_variable cond[2];
  static int counter[2] = {0, 0};

  std::unique_lock<std::mutex> ul(lock[epoch]);
  if(++counter[epoch] == args->nThreads)
    cond[epoch].notify_all();

  if(args->thread+1 == args->nThreads) {
    while(counter[epoch] != args->nThreads)
      cond[epoch].wait(ul);
    #ifdef MPI_SUPPORT
      MPI_Barrier(MPI_COMM_WORLD);
    #endif
    counter[epoch] = 0;
    cond[epoch].notify_all();
  }
  else {
    while(counter[epoch] != 0)
      cond[epoch].wait(ul);
  }
  ul.unlock();
  epoch ^= 1;
}

// Inter-thread/process barrier+allreduce. The quality of the return value
// for average=0 (which means broadcast from rank=0) is dubious. The returned
// value will actually be the result of process-local broadcast from the local thread=0.
template<typename T>
void Allreduce(struct threadArgs* args, T* value, int average) {
  thread_local int epoch = 0;
  static std::mutex lock[2];
  static std::condition_variable cond[2];
  static T accumulator[2];
  static int counter[2] = {0, 0};

  std::unique_lock<std::mutex> ul(lock[epoch]);
  if(counter[epoch] == 0) {
    if(average != 0 || args->thread == 0) accumulator[epoch] = *value;
  } else {
    switch(average) {
    case /*r0*/ 0: if(args->thread == 0) accumulator[epoch] = *value; break;
    case /*avg*/1: accumulator[epoch] += *value; break;
    case /*min*/2: accumulator[epoch] = std::min<T>(accumulator[epoch], *value); break;
    case /*max*/3: accumulator[epoch] = std::max<T>(accumulator[epoch], *value); break;
    case /*sum*/4: accumulator[epoch] += *value; break;
    }
  }

  if(++counter[epoch] == args->nThreads)
    cond[epoch].notify_all();

  if(args->thread+1 == args->nThreads) {
    while(counter[epoch] != args->nThreads)
      cond[epoch].wait(ul);

    #ifdef MPI_SUPPORT
    if(average != 0) {
      static_assert(std::is_same<T, long long>::value || std::is_same<T, double>::value, "Allreduce<T> only for T in {long long, double}");
      MPI_Datatype ty = std::is_same<T, long long>::value ? MPI_LONG_LONG :
                        std::is_same<T, double>::value ? MPI_DOUBLE :
                        MPI_Datatype();
      MPI_Op op = average == 1 ? MPI_SUM :
                  average == 2 ? MPI_MIN :
                  average == 3 ? MPI_MAX :
                  average == 4 ? MPI_SUM : MPI_Op();
      MPI_Allreduce(MPI_IN_PLACE, (void*)&accumulator[epoch], 1, ty, op, MPI_COMM_WORLD);
    }
    #endif

    if(average == 1) accumulator[epoch] /= args->totalProcs*args->nThreads;
    counter[epoch] = 0;
    cond[epoch].notify_all();
  }
  else {
    while(counter[epoch] != 0)
      cond[epoch].wait(ul);
  }
  ul.unlock();

  *value = accumulator[epoch];
  epoch ^= 1;
}

// Reduce per-thread iteration times to a process-local max, then gather one row
// per MPI process.
void GatherProcessMaxIterTimes(struct threadArgs* args, double* localTimes, int nIters, double* recvBuf) {
  thread_local int epoch = 0;
  static std::mutex lock[2];
  static std::condition_variable cond[2];
  static double* sendBuf[2] = {NULL, NULL};
  static int sendBufIters[2] = {0, 0};
  static double* recvPtr[2];
  static int counter[2] = {0, 0};

  std::unique_lock<std::mutex> ul(lock[epoch]);

  if (sendBufIters[epoch] < nIters) {
    sendBuf[epoch] = (double*)realloc(sendBuf[epoch], nIters * sizeof(double));
    sendBufIters[epoch] = nIters;
  }

  if (counter[epoch] == 0) {
    memcpy(sendBuf[epoch], localTimes, nIters * sizeof(double));
  } else {
    for (int i = 0; i < nIters; i++)
      sendBuf[epoch][i] = std::max(sendBuf[epoch][i], localTimes[i]);
  }

  if (args->thread == 0) {
    recvPtr[epoch] = recvBuf;
  }

  if(++counter[epoch] == args->nThreads)
    cond[epoch].notify_all();

  if(args->thread+1 == args->nThreads) {
    while(counter[epoch] != args->nThreads)
      cond[epoch].wait(ul);

    #ifdef MPI_SUPPORT
    if (args->totalProcs > 1) {
      MPI_Gather(sendBuf[epoch], nIters, MPI_DOUBLE,
                 recvPtr[epoch], nIters, MPI_DOUBLE,
                 0, MPI_COMM_WORLD);
    }
    #else
    if (recvPtr[epoch])
      memcpy(recvPtr[epoch], sendBuf[epoch], nIters * sizeof(double));
    #endif

    memcpy(localTimes, sendBuf[epoch], nIters * sizeof(double));
    counter[epoch] = 0;
    cond[epoch].notify_all();
  }
  else {
    while(counter[epoch] != 0)
      cond[epoch].wait(ul);
    memcpy(localTimes, sendBuf[epoch], nIters * sizeof(double));
  }
  ul.unlock();
  epoch ^= 1;
}

void ReduceProcessMaxIterTimes(double* iterTimes, const double* allProcessTimes,
                               int nProcs, int nIters) {
  for (int i = 0; i < nIters; i++) {
    double maxSec = allProcessTimes[i];
    for (int p = 1; p < nProcs; p++)
      maxSec = std::max(maxSec, allProcessTimes[p * nIters + i]);
    iterTimes[i] = maxSec;
  }
}

testResult_t CheckData(struct threadArgs* args, ncclDataType_t type, ncclRedOp_t op, int root, int in_place, int64_t *wrongElts) {
  int nranks = args->nProcs*args->nGpus*args->nThreads;
  size_t count = args->expectedBytes/wordSize(type);

  int64_t *wrongPerGpu = nullptr;
  CUDACHECK(cudaHostAlloc((void**)&wrongPerGpu, args->nGpus*sizeof(int64_t), cudaHostAllocMapped));

  for (int i=0; i<args->nGpus; i++) {
    int rank = ((args->proc*args->nThreads + args->thread)*args->nGpus + i);
    CUDACHECK(cudaSetDevice(args->gpus[i]));
    void *data = in_place ? ((void *)((uintptr_t)args->recvbuffs[i] + args->recvInplaceOffset*rank)) : args->recvbuffs[i];

    TESTCHECK(CheckDelta(data, args->expected[i], count, 0, type, op, 0, nranks, wrongPerGpu+i));

#if 1 && DEBUG_PRINT
    if (args->reportErrors && wrongPerGpu[i] != 0) {
      printf("rank=%d #wrong=%d\n", rank, (int)wrongPerGpu[i]);
      char *expectedHost = (char*)malloc(args->expectedBytes);
      char *dataHost = (char*)malloc(args->expectedBytes);
      int eltsz = wordSize(type);
      cudaMemcpy(expectedHost, args->expected[i], args->expectedBytes, cudaMemcpyDeviceToHost);
      cudaMemcpy(dataHost, data, args->expectedBytes, cudaMemcpyDeviceToHost);

      for(int j=0; j<args->expectedBytes/eltsz; j++) {
        unsigned long long want, got;
        want = 0;
        memcpy(&want, expectedHost + j*eltsz, eltsz);
        got = 0;
        memcpy(&got, dataHost + j*eltsz, eltsz);
        if(want != got) {
          printf(" rank=%d elt[%d]: want=0x%llx got=0x%llx\n", rank, j, want, got);
        }
      }
      free(expectedHost);
      free(dataHost);
    }
#endif
  }

  *wrongElts = 0;
  for (int i=0; i < args->nGpus; i++) *wrongElts += wrongPerGpu[i];
  cudaFreeHost(wrongPerGpu);

  if (args->reportErrors && *wrongElts) args->errors[0]++;
  return testSuccess;
}

testResult_t testStreamSynchronize(int ngpus, cudaStream_t* streams, ncclComm_t* comms) {
  cudaError_t cudaErr;
  int remaining = ngpus;
  int* done = (int*)malloc(sizeof(int)*ngpus);
  memset(done, 0, sizeof(int)*ngpus);
  timer tim;

  while (remaining) {
   int idle = 1;
   for (int i=0; i<ngpus; i++) {
     if (done[i]) continue;

     cudaErr = cudaStreamQuery(streams[i]);
     if (cudaErr == cudaSuccess) {
       done[i] = 1;
       remaining--;
       idle = 0;
       continue;
     }

     if (cudaErr != cudaErrorNotReady) CUDACHECK(cudaErr);

#if NCCL_VERSION_CODE >= NCCL_VERSION(2,4,0)
     if (test_ncclVersion >= NCCL_VERSION(2,4,0) && comms) {
       ncclResult_t ncclAsyncErr;
       NCCLCHECK(ncclCommGetAsyncError(comms[i], &ncclAsyncErr));
       if (ncclAsyncErr != ncclSuccess) {
         // An asynchronous error happened. Stop the operation and destroy
         // the communicator
         for (int i=0; i<ngpus; i++)
           NCCLCHECK(ncclCommAbort(comms[i]));
         // Abort the perf test
         NCCLCHECK(ncclAsyncErr);
       }
     }
     double delta = tim.elapsed();
     if (delta > timeout && timeout > 0) {
       for (int i=0; i<ngpus; i++)
         NCCLCHECK(ncclCommAbort(comms[i]));
       char hostname[1024];
       getHostName(hostname, 1024);
       printf("%s: Test timeout (%ds) %s:%d\n",
           hostname,
           timeout,
           __FILE__,__LINE__);
       free(done);
       return testTimeout;
     }
#endif
   }

   // We might want to let other threads (including NCCL threads) use the CPU.
   if (idle) std::this_thread::yield();
  }
  free(done);
  return testSuccess;
}

testResult_t startColl(struct threadArgs* args, ncclDataType_t type, ncclRedOp_t opIndex, int root, int in_place, int iter) {
  size_t count = args->nbytes / wordSize(type);

  // Try to change offset for each iteration so that we avoid cache effects and catch race conditions in ptrExchange
  size_t totalnbytes = max(args->sendBytes, args->expectedBytes);
  size_t steps = totalnbytes ? args->maxbytes / totalnbytes : 1;
  size_t shift = totalnbytes * (iter % steps);
  size_t unalignBytes = (size_t)unalign * wordSize(type);

  if (args->nGpus > 1) NCCLCHECK(ncclGroupStart());
  for (int i = 0; i < args->nGpus; i++) {
#ifndef NCCL_MAJOR
    CUDACHECK(cudaSetDevice(args->gpus[i]));
#endif
    int rank = ((args->proc*args->nThreads + args->thread)*args->nGpus + i);
    char* recvBuff = ((char*)args->recvbuffs[i]) + shift;
    char* sendBuff = ((char*)args->sendbuffs[i]) + shift;
    ncclRedOp_t op;

    if(opIndex < ncclNumOps) {
      op = opIndex;
    }
    #if NCCL_VERSION_CODE >= NCCL_VERSION(2,11,0)
    else {
      union {
        int8_t i8; uint8_t u8; int32_t i32; uint32_t u32; int64_t i64; uint64_t u64;
        half f16; float f32; double f64;
        #if HAVE_BF16
        __nv_bfloat16 bf16;
        #endif
        #if HAVE_FP8
        __nv_fp8_e4m3 f8e4m3; __nv_fp8_e5m2 f8e5m2;
        #endif
      };
      switch(type) {
      case ncclInt8: i8 = ncclVerifiablePremulScalar<int8_t>(rank); break;
      case ncclUint8: u8 = ncclVerifiablePremulScalar<uint8_t>(rank); break;
      case ncclInt32: i32 = ncclVerifiablePremulScalar<int32_t>(rank); break;
      case ncclUint32: u32 = ncclVerifiablePremulScalar<uint32_t>(rank); break;
      case ncclInt64: i64 = ncclVerifiablePremulScalar<int64_t>(rank); break;
      case ncclUint64: u64 = ncclVerifiablePremulScalar<uint64_t>(rank); break;
      case ncclFloat16: f16 = ncclVerifiablePremulScalar<half>(rank); break;
      case ncclFloat32: f32 = ncclVerifiablePremulScalar<float>(rank); break;
      case ncclFloat64: f64 = ncclVerifiablePremulScalar<double>(rank); break;
      #if HAVE_BF16
      case ncclBfloat16: bf16 = ncclVerifiablePremulScalar<__nv_bfloat16>(rank); break;
      #endif
      #if HAVE_FP8
      case ncclFloat8e4m3: f8e4m3 = ncclVerifiablePremulScalar<__nv_fp8_e4m3>(rank); break;
      case ncclFloat8e5m2: f8e5m2 = ncclVerifiablePremulScalar<__nv_fp8_e5m2>(rank); break;
      #endif
      default: break; // Just to silence clang
      }
      NCCLCHECK(ncclRedOpCreatePreMulSum(&op, &u64, type, ncclScalarHostImmediate, args->comms[i]));
    }
    #endif

#if NCCL_VERSION_CODE >= NCCL_VERSION(2,29,0)
    if (hostRmaImpl) {
      void* sendwin = args->sendRegHandles[i];
      void* recvwin = args->recvRegHandles[i];
      CUDACHECK(cudaSetDevice(args->gpus[i]));
      TESTCHECK(args->collTest->runColl(
            (void*)(in_place ? recvwin : sendwin), shift + (in_place ? args->sendInplaceOffset*rank : 0) + unalignBytes,
            (void*)recvwin, shift + (in_place ? args->recvInplaceOffset*rank : 0) + unalignBytes,
            count, type, op, root, args->comms[i], args->streams[i], HOST_RMA_IMPL));
    } else
#endif
    if (deviceImpl == 0) {
      TESTCHECK(args->collTest->runColl(
            (void*)(in_place ? recvBuff : sendBuff), in_place ? args->sendInplaceOffset*rank : 0,
            (void*)recvBuff, in_place ? args->recvInplaceOffset*rank : 0,
            count, type, op, root, args->comms[i], args->streams[i], 0));
    } else {
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,28,0)
      void* sendwin = args->sendRegHandles[i];
      void* recvwin = args->recvRegHandles[i];
      CUDACHECK(cudaSetDevice(args->gpus[i]));
      TESTCHECK(args->collTest->runColl(
            (void*)(in_place ? recvwin : sendwin), shift + (in_place ? args->sendInplaceOffset*rank : 0) + unalignBytes,
            (void*)recvwin, shift + (in_place ? args->recvInplaceOffset*rank : 0) + unalignBytes,
            count, type, op, root, (ncclComm_t)(args->devComms+i), args->streams[i], deviceImpl));
#endif
    }

    #if NCCL_VERSION_CODE >= NCCL_VERSION(2,11,0)
    if(opIndex >= ncclNumOps) {
      NCCLCHECK(ncclRedOpDestroy(op, args->comms[i]));
    }
    #endif
  }
  if (args->nGpus > 1) NCCLCHECK(ncclGroupEnd());

  if (blocking_coll && blocking_coll != 3) {
    // Complete op before returning
    TESTCHECK(testStreamSynchronize(args->nGpus, args->streams, args->comms));
  }
  if (blocking_coll == 1) Barrier(args);
  return testSuccess;
}

testResult_t completeColl(struct threadArgs* args) {
  if (blocking_coll && blocking_coll != 3 && agg_iters <= 1) return testSuccess;

  TESTCHECK(testStreamSynchronize(args->nGpus, args->streams, args->comms));
  return testSuccess;
}

static int getEventCount(int eventIters) {
  return blocking_coll == 3 ? eventIters*2 : eventIters + 1;
}

testResult_t getElapsedTimes(struct threadArgs* args, int eventIters, int aggIters) {
  args->ms = (float*) malloc(sizeof(float)*args->nGpus*eventIters);
  int pairedEvents = blocking_coll == 3;
  int eventCount = getEventCount(eventIters);
  // Get timings
  for (int i = 0; i < args->nGpus; i++) {
    CUDACHECK(cudaSetDevice(args->gpus[i]));
    for (int j = 0; j < eventIters; j++) {
      int startEvent = pairedEvents ? 2*j : j;
      int stopEvent = pairedEvents ? 2*j + 1 : j + 1;
      CUDACHECK(cudaEventElapsedTime(&args->ms[i*(eventIters) + j], args->events[i*eventCount + startEvent], args->events[i*eventCount + stopEvent]));

      // This elapsed time is for iterations equal to agg_iters.
      // We need to divide by aggIters
      args->ms[i*(eventIters)+j] /= aggIters;
    }
  }
  return testSuccess;
}

testResult_t recordEvents(struct threadArgs* args, int iterations, int iteration, int stopEvent = 0) {
  int pairedEvents = blocking_coll == 3;
  int eventCount = getEventCount(iterations);
  int eventIndex = pairedEvents ? 2*iteration + stopEvent : iteration;
  for(int i = 0; i < args->nGpus; i++) {
    CUDACHECK(cudaSetDevice(args->gpus[i]));
    CUDACHECK(cudaEventRecord(args->events[i*eventCount + eventIndex], args->streams[i]));
  }
  return testSuccess;
}

testResult_t initEvents(struct threadArgs* args, int eventIters) {
  int eventCount = getEventCount(eventIters);
  // Normal timing shares boundary events; z3 uses start/stop pairs to exclude barriers.
  args->events = (cudaEvent_t*) malloc(sizeof(cudaEvent_t)*args->nGpus*eventCount);
  for (int i = 0; i < args->nGpus; i++) {
    CUDACHECK(cudaSetDevice(args->gpus[i]));
    for (int j = 0; j < eventCount; j++) {
      CUDACHECK(cudaEventCreate(&args->events[(i*eventCount + j)]));
    }
  }
  return testSuccess;
}

testResult_t destroyEvents(struct threadArgs* args, int eventIters) {
  int eventCount = getEventCount(eventIters);
  for (int i = 0; i < args->nGpus; i++) {
    for (int j = 0; j < eventCount; j++)
      CUDACHECK(cudaEventDestroy(args->events[i*eventCount+j]));
  }
  free(args->events);
  return testSuccess;
}

testResult_t BenchTime(struct threadArgs* args, ncclDataType_t type, ncclRedOp_t op, int root, int in_place) {
  size_t count = args->nbytes / wordSize(type);
  if (datacheck) {
    // Initialize sendbuffs, recvbuffs and expected
    TESTCHECK(args->collTest->initData(args, type, op, root, 99, in_place));
  }

  // Warm-up immediately after data initialization
  for (int iter = 0; iter < warmup_iters; iter++) {
    TESTCHECK(startColl(args, type, op, root, in_place, iter));
  }
  TESTCHECK(completeColl(args));

  Barrier(args);

#if CUDART_VERSION >= 11030
  std::vector<cudaGraph_t> graphs(args->nGpus);
  std::vector<cudaGraphExec_t> graphExec(args->nGpus);
  if (cudaGraphLaunches >= 1) {
    // Begin cuda graph capture
    for (int i=0; i<args->nGpus; i++) {
      // Thread local mdoe is needed for:
      // - Multi-thread mode: where graph capture and instantiation can happen concurrently across threads
      // - P2P pre-connect: when there is no warm-up, P2P pre-connect is done during graph capture.
      //   Since pre-connect calls cudaMalloc, we cannot use global capture mode
      CUDACHECK(cudaStreamBeginCapture(args->streams[i], cudaStreamCaptureModeThreadLocal));
    }
  }
#endif

  int record = per_iter_timing;
  if (record) TESTCHECK(initEvents(args, iters));

  // Performance Benchmark
  double collOnlySec = 0;
  int pairedEvents = record && blocking_coll == 3;
  timer tim;
  for (int iter = 0; iter < iters; iter++) {
    double t0 = tim.elapsed();
    if (agg_iters>1) NCCLCHECK(ncclGroupStart());
    if (record) TESTCHECK(recordEvents(args, iters, iter));
    for (int aiter = 0; aiter < agg_iters; aiter++) {
      TESTCHECK(startColl(args, type, op, root, in_place, iter*agg_iters+aiter));
    }
    if (agg_iters>1) NCCLCHECK(ncclGroupEnd());
    if (blocking_coll == 3) {
      TESTCHECK(testStreamSynchronize(args->nGpus, args->streams, args->comms));
      if (pairedEvents) TESTCHECK(recordEvents(args, iters, iter, 1));
      collOnlySec += tim.elapsed() - t0;
      Barrier(args);
    }
  }
  if (record && !pairedEvents) TESTCHECK(recordEvents(args, iters, iters));

#if CUDART_VERSION >= 11030
  if (cudaGraphLaunches >= 1) {
    // End cuda graph capture
    for (int i=0; i<args->nGpus; i++) {
      CUDACHECK(cudaStreamEndCapture(args->streams[i], graphs.data()+i));
    }
    // Instantiate cuda graph
    for (int i=0; i<args->nGpus; i++) {
      CUDACHECK(cudaGraphInstantiate(graphExec.data()+i, graphs[i], NULL, NULL, 0));
    }
    // Resync CPU, restart timing, launch cuda graph
    Barrier(args);
    tim.reset();
    for (int l=0; l<cudaGraphLaunches; l++) {
      for (int i=0; i<args->nGpus; i++) {
        CUDACHECK(cudaGraphLaunch(graphExec[i], args->streams[i]));
      }
    }
  }
#endif

  double cputimeSec = blocking_coll == 3 ? collOnlySec : tim.elapsed();
  cputimeSec /= iters*agg_iters;
  TESTCHECK(completeColl(args));

  // Exclude per-iteration result processing from the reported time.
  double deltaSec = (blocking_coll == 3 ? collOnlySec : tim.elapsed())/(iters*agg_iters);
  if (cudaGraphLaunches >= 1) deltaSec = deltaSec/cudaGraphLaunches;

  if (record) {
    // completeColl skips the stream sync for blocking modes 1 and 2 with a single aggregated iteration.
    if (blocking_coll && blocking_coll != 3 && agg_iters <= 1)
      TESTCHECK(testStreamSynchronize(args->nGpus, args->streams, args->comms));
    TESTCHECK(getElapsedTimes(args, iters, agg_iters));
    TESTCHECK(destroyEvents(args, iters));
  }

  Allreduce(args, &deltaSec, average);

#if CUDART_VERSION >= 11030
  if (cudaGraphLaunches >= 1) {
    //destroy cuda graph
    for (int i=0; i<args->nGpus; i++) {
      CUDACHECK(cudaGraphExecDestroy(graphExec[i]));
      CUDACHECK(cudaGraphDestroy(graphs[i]));
    }
  }
#endif

  double algBw, busBw;
  args->collTest->getBw(count, wordSize(type), deltaSec, &algBw, &busBw, args->nProcs*args->nThreads*args->nGpus);

  Barrier(args);

  int64_t wrongElts = 0;
  static thread_local int rep = 0;
  rep++;
  for (int c = 0; c < datacheck; c++) {
      // Initialize sendbuffs, recvbuffs and expected
      TESTCHECK(args->collTest->initData(args, type, op, root, rep, in_place));

#if CUDART_VERSION >= 11030
      if (cudaGraphLaunches >= 1) {
        // Begin cuda graph capture for data check
        for (int i=0; i<args->nGpus; i++) {
          CUDACHECK(cudaStreamBeginCapture(args->streams[i], args->nThreads > 1 ? cudaStreamCaptureModeThreadLocal : cudaStreamCaptureModeGlobal));
        }
      }
#endif

      //test validation in single itertion, should ideally be included into the multi-iteration run
      TESTCHECK(startColl(args, type, op, root, in_place, 0));

#if CUDART_VERSION >= 11030
      if (cudaGraphLaunches >= 1) {
        // End cuda graph capture
        for (int i=0; i<args->nGpus; i++) {
          CUDACHECK(cudaStreamEndCapture(args->streams[i], graphs.data()+i));
        }
        // Instantiate cuda graph
        for (int i=0; i<args->nGpus; i++) {
          CUDACHECK(cudaGraphInstantiate(graphExec.data()+i, graphs[i], NULL, NULL, 0));
        }
        // Launch cuda graph
        for (int i=0; i<args->nGpus; i++) {
          CUDACHECK(cudaGraphLaunch(graphExec[i], args->streams[i]));
        }
      }
#endif

      TESTCHECK(completeColl(args));

#if CUDART_VERSION >= 11030
      if (cudaGraphLaunches >= 1) {
        //destroy cuda graph
        for (int i=0; i<args->nGpus; i++) {
          CUDACHECK(cudaGraphExecDestroy(graphExec[i]));
          CUDACHECK(cudaGraphDestroy(graphs[i]));
        }
      }
#endif

      TESTCHECK(CheckData(args, type, op, root, in_place, &wrongElts));

      //aggregate delta from all threads and procs
      long long wrongElts1 = wrongElts;
      //if (wrongElts) fprintf(stderr, "\nERROR: Data corruption : rank %d size %ld wrongElts %ld\n", args->proc, args->expectedBytes, wrongElts);
      Allreduce(args, &wrongElts1, /*sum*/4);
      wrongElts = wrongElts1;
      if (wrongElts) break;
  }

  double timeUsec = (report_cputime ? cputimeSec : deltaSec)*1.0E6;
  writeBenchmarkLineBody(timeUsec, algBw, busBw, args->reportErrors, wrongElts, report_cputime, report_timestamps, in_place==0);

  if (record && args->ms) {
    // Extract max-across-GPUs per iteration (convert ms to seconds)
    double* iterTimes = (double*)calloc(iters, sizeof(double));
    for (int iter = 0; iter < iters; iter++) {
      double maxSec = 0;
      for (int i = 0; i < args->nGpus; i++) {
        double sec = (double)args->ms[i * iters + iter] * 1e-3;
        if (sec > maxSec) maxSec = sec;
      }
      iterTimes[iter] = maxSec;
    }

    double* allProcessTimes = NULL;
    int nProcessRows = args->totalProcs;
    if (nProcessRows > 1) {
      if (is_main_thread)
        allProcessTimes = (double*)malloc(nProcessRows * iters * sizeof(double));
    }
    GatherProcessMaxIterTimes(args, iterTimes, iters, allProcessTimes);
    if (allProcessTimes && nProcessRows > 1)
      ReduceProcessMaxIterTimes(iterTimes, allProcessTimes, nProcessRows, iters);

    int summaryIters = iters - per_iter_skip;
    struct IterStats stats;
    computeIterStats(iterTimes + per_iter_skip, summaryIters, &stats);
    writePerIterReport(&stats, iterTimes, iters, per_iter_skip, in_place==0, allProcessTimes, nProcessRows);

    if (in_place && report_timestamps) writeTimestamp();

    free(allProcessTimes);
    free(iterTimes);
    free(args->ms);
  }

  args->bw[0] += busBw;
  args->bw_count[0]++;
  return testSuccess;
}

void setupArgs(size_t size, ncclDataType_t type, struct threadArgs* args) {
  int nranks = args->nProcs*args->nGpus*args->nThreads;
  size_t count, sendCount, recvCount, paramCount, sendInplaceOffset, recvInplaceOffset;

  count = size / wordSize(type);
  args->collTest->getCollByteCount(&sendCount, &recvCount, &paramCount, &sendInplaceOffset, &recvInplaceOffset, (size_t)count, wordSize(type), (size_t)nranks);

  args->nbytes = paramCount * wordSize(type);
  args->sendBytes = sendCount * wordSize(type);
  args->expectedBytes = recvCount * wordSize(type);
  args->sendInplaceOffset = sendInplaceOffset * wordSize(type);
  args->recvInplaceOffset = recvInplaceOffset * wordSize(type);
}

testResult_t TimeTest(struct threadArgs* args, ncclDataType_t type, const char* typeName, ncclRedOp_t op, const char* opName, int root) {
  // Sync to avoid first-call timeout
  Barrier(args);

  // Add forced misalignment
  for (int i = 0; i < args->nGpus; i++) {
    args->sendbuffs[i] = (char*)args->sendbuffs[i] + unalign * wordSize(type);
    args->recvbuffs[i] = (char*)args->recvbuffs[i] + unalign * wordSize(type);
  }

  // Benchmark
  long repeat = run_cycles;
  do {
    for (size_t size = args->minbytes; size<=args->maxbytes; size = ((args->stepfactor > 1) ? size*args->stepfactor : size+args->stepbytes)) {
      setupArgs(size, type, args);
      writeBenchmarkLinePreamble(max(args->sendBytes, args->expectedBytes), args->nbytes / wordSize(type), typeName, opName, root);
      TESTCHECK(BenchTime(args, type, op, root, 0));
      TESTCHECK(BenchTime(args, type, op, root, 1));
      writeBenchmarkLineTerminator(iters, "");
    }
  } while (--repeat);

  // Revert forced misalignment
  for (int i = 0; i < args->nGpus; i++) {
    args->sendbuffs[i] = (char*)args->sendbuffs[i] - unalign * wordSize(type);
    args->recvbuffs[i] = (char*)args->recvbuffs[i] - unalign * wordSize(type);
  }
  return testSuccess;
}

static void getGPUMemoryInfo(int64_t* ptotalGpuMem, int64_t* pfreeGpuMem) {
  size_t freeGpuMem, totalGpuMem = 0;
  cudaMemGetInfo(&freeGpuMem, &totalGpuMem);
  if (ptotalGpuMem != nullptr) *ptotalGpuMem = totalGpuMem;
  if (pfreeGpuMem != nullptr) *pfreeGpuMem = freeGpuMem;
}

testResult_t threadRunTests(struct threadArgs* args) {
  //  capture the free memory before
  int64_t* totalGpuFreeMem = (int64_t*)calloc(args->nGpus*2, sizeof(int64_t));
  for (int g = 0; g < args->nGpus; ++g) {
    CUDACHECK(cudaSetDevice(args->gpus[g]));
    getGPUMemoryInfo(nullptr, &totalGpuFreeMem[g]);
  }

  // Set device to the first of our GPUs. If we don't do that, some operations
  // will be done on the current GPU (by default : 0) and if the GPUs are in
  // exclusive mode those operations will fail.
  CUDACHECK(cudaSetDevice(args->gpus[0]));
  TESTCHECK(ncclTestEngine.runTest(args, ncclroot, (ncclDataType_t)nccltype, test_typenames[nccltype], (ncclRedOp_t)ncclop, test_opnames[ncclop]));

  // Capture the memory used by the GPUs
  for (int g = 0; g < args->nGpus; ++g) {
    CUDACHECK(cudaSetDevice(args->gpus[g]));
    getGPUMemoryInfo(nullptr, &totalGpuFreeMem[g + args->nGpus]);
    *args->devMemUsed = std::max(*args->devMemUsed, totalGpuFreeMem[g] - totalGpuFreeMem[g + args->nGpus]);
  }
  free(totalGpuFreeMem);
  return testSuccess;
}

testResult_t threadInit(struct threadArgs* args) {
  int nranks =  args->nProcs*args->nThreads*args->nGpus;

  //set main thread again
  is_main_thread = (is_main_proc && args->thread == 0) ? 1 : 0;

  jsonIdentifyWriter(is_main_thread);

  // Capture GPU memory before initializing the NCCL communicators
  int64_t* initFreeGpuMem = (int64_t*)calloc(args->nGpus*3, sizeof(int64_t));
  for (int g = 0; g < args->nGpus; ++g) {
    CUDACHECK(cudaSetDevice(args->gpus[g]));
    getGPUMemoryInfo(nullptr, &initFreeGpuMem[g]);
  }

  int firstRank = args->proc*args->nThreads*args->nGpus + args->thread*args->nGpus;
  TESTCHECK(initComms(args->comms, args->nGpus, firstRank, nranks, args->gpus, args->ncclId));

  /* Allocate buffers for each GPU (parallel_init: each thread allocates its own) */
  size_t sendBytes, recvBytes;
  size_t allocBytes;
  ncclTestEngine.getBuffSize(&sendBytes, &recvBytes, (size_t)args->maxbytes, (size_t)nranks);
  NCCLCHECK(ncclGroupStart());
  for (int i = 0; i < args->nGpus; i++) {
    CUDACHECK(cudaSetDevice(args->gpus[i]));
    TESTCHECK(AllocateBuffs(args->sendbuffs + i, sendBytes, args->recvbuffs + i, recvBytes, args->expected + i, (size_t)args->maxbytes, &allocBytes));
  }
  NCCLCHECK(ncclGroupEnd());

  // Capture the memory used by the GPUs after initializing the NCCL communicators
  for (int g = 0; g < args->nGpus; ++g) {
    CUDACHECK(cudaSetDevice(args->gpus[g]));
    getGPUMemoryInfo(nullptr, &initFreeGpuMem[g + args->nGpus]);
    *args->initGpuMem = std::max(*args->initGpuMem, initFreeGpuMem[g] - initFreeGpuMem[g + args->nGpus]);
  }

#if NCCL_VERSION_CODE >= NCCL_VERSION(2,19,0)
  NCCLCHECK(ncclGroupStart());
  for (int i=0; i<args->nGpus; i++) {
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,27,0)
    if (test_ncclVersion >= NCCL_VERSION(2,27,0) && (local_register == SYMMETRIC_REGISTER)) {
      NCCLCHECK(ncclCommWindowRegister(args->comms[i], args->sendbuffs[i], allocBytes, (ncclWindow_t*)&args->sendRegHandles[i], NCCL_WIN_COLL_SYMMETRIC));
      NCCLCHECK(ncclCommWindowRegister(args->comms[i], args->recvbuffs[i], allocBytes, (ncclWindow_t*)&args->recvRegHandles[i], NCCL_WIN_COLL_SYMMETRIC));
    } else
#endif
    {
      if (local_register) NCCLCHECK(ncclCommRegister(args->comms[i], args->sendbuffs[i], allocBytes, &args->sendRegHandles[i]));
      if (local_register) NCCLCHECK(ncclCommRegister(args->comms[i], args->recvbuffs[i], allocBytes, &args->recvRegHandles[i]));
    }
  }
  NCCLCHECK(ncclGroupEnd());
#endif
#if NCCL_TESTS_HAS_HOST_RMA_SUPPORT_PROPERTY
  if (hostRmaImpl) {
    ncclCommProperties_t commProperties = NCCL_COMM_PROPERTIES_INITIALIZER;
    NCCLCHECK(ncclCommQueryProperties(args->comms[0], &commProperties));
    if (!commProperties.hostRmaSupport) {
      fprintf(stderr, "Host RMA is not supported on this system\n");
      return testInvalidUsage;
    }
  }
#endif
  // Capture memory used by test buffers
  for (int g = 0; g < args->nGpus; ++g) {
    CUDACHECK(cudaSetDevice(args->gpus[g]));
    getGPUMemoryInfo(nullptr, &initFreeGpuMem[g + args->nGpus*2]);
    *args->bufferMemory = std::max(*args->bufferMemory, initFreeGpuMem[g + args->nGpus] - initFreeGpuMem[g + args->nGpus*2]);
  }
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,28,0)
  /* Create device communicators based on test-specific requirements */
  if (deviceImpl) {
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,29,0)
    if (test_ncclVersion < NCCL_VERSION(2,29,0)) {
      fprintf(stderr,
        "Incompatible NCCL versions. nccl-tests was compiled with NCCL %d, but is running with NCCL %d. "
        "The %d Device API is not compatible with versions before 2.29.\n",
        NCCL_VERSION_CODE, test_ncclVersion, NCCL_VERSION_CODE);
      return testInvalidUsage;
    }
    ncclDevCommRequirements reqs = NCCL_DEV_COMM_REQUIREMENTS_INITIALIZER;
    if (!ncclTestEngine.getDevCommRequirements) {
      fprintf(stderr, "Device implementation %d is not supported by this test\n", deviceImpl);
      return testNotImplemented;
    }
    TESTCHECK(ncclTestEngine.getDevCommRequirements(deviceImpl, &reqs, args->comms[0]));
#else
    if (test_ncclVersion >= NCCL_VERSION(2,29,0)) {
      fprintf(stderr, "Incompatible NCCL versions. nccl-tests was compiled with NCCL 2.28, but is running with NCCL %d. "
        "The 2.28 Device API is not compatible with later.\n",
        test_ncclVersion);
      return testInvalidUsage;
    }
    ncclDevCommRequirements reqs = {};
    if (!ncclTestEngine.getDevCommRequirements ||
        !ncclTestEngine.getDevCommRequirements(deviceImpl, &reqs)) {
      fprintf(stderr, "Device implementation %d is not supported by this test\n", deviceImpl);
      return testNotImplemented;
    }
#endif

    NCCLCHECK(ncclGroupStart());
    for (int i = 0; i < args->nGpus; i++) {
      NCCLCHECK(ncclDevCommCreate(args->comms[i], &reqs, args->devComms+i));
    }
    NCCLCHECK(ncclGroupEnd());
  }
  // Capture memory used by test buffers
  int64_t deviceCommMaxMem = 0;
  for (int g = 0; g < args->nGpus; ++g) {
    CUDACHECK(cudaSetDevice(args->gpus[g]));
    int64_t freeGpuMem;
    getGPUMemoryInfo(nullptr, &freeGpuMem);
    deviceCommMaxMem = std::max(deviceCommMaxMem, initFreeGpuMem[g + args->nGpus*2] - freeGpuMem);
  }
  *args->initGpuMem += deviceCommMaxMem;
#endif
  free(initFreeGpuMem);

  TESTCHECK(threadRunTests(args));

  return testSuccess;
}

static void threadLauncher(struct testThread* thread) {
  thread->ret = thread->func(&thread->args);
}
testResult_t threadLaunch(struct testThread* thread) {
  thread->thread = std::thread(threadLauncher, thread);
  return testSuccess;
}

testResult_t AllocateBuffs(void **sendbuff, size_t sendBytes, void **recvbuff, size_t recvBytes, void **expected, size_t nbytes, size_t *allocBytes) {
    nbytes += 8*unalign; // pad with size of max datatype in case all datatypes selected
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,19,0)
    NCCLCHECK(ncclMemAlloc(sendbuff, nbytes));
    NCCLCHECK(ncclMemAlloc(recvbuff, nbytes));
    if (datacheck) NCCLCHECK(ncclMemAlloc(expected, recvBytes));
#else
    CUDACHECK(cudaMalloc(sendbuff, nbytes));
    CUDACHECK(cudaMalloc(recvbuff, nbytes));
    if (datacheck) CUDACHECK(cudaMalloc(expected, recvBytes));
#endif
    *allocBytes = nbytes;
    return testSuccess;
}

testResult_t run(); // Main function

int main(int argc, char* argv[], char **envp) {
  // Make sure everyline is flushed so that we see the progress of the test
  ncclTestSetlinebuf(stdout);
  const char* slash = strrchr(argv[0], '/');
  const char* backslash = strrchr(argv[0], '\\');
  const char* sep = nullptr;
  if (slash && backslash) {
    sep = slash > backslash ? slash : backslash;
  } else if (slash) {
    sep = slash;
  } else {
    sep = backslash;
  }
  programName = sep ? sep + 1 : argv[0];

  #if NCCL_VERSION_CODE >= NCCL_VERSION(2,4,0)
    ncclGetVersion(&test_ncclVersion);
  #else
    test_ncclVersion = NCCL_VERSION_CODE;
  #endif
  //printf("# nccl-tests version %s NCCL_VERSION_CODE=%d ncclGetVersion=%d\n", NCCL_TESTS_VERSION, NCCL_VERSION_CODE, test_ncclVersion);
  #if NCCL_VERSION_CODE >= NCCL_VERSION(2,0,0)
    test_opnum = 4;
    test_typenum = 9;
    if (NCCL_VERSION_CODE >= NCCL_VERSION(2,10,0) && test_ncclVersion >= NCCL_VERSION(2,10,0)) {
      test_opnum++; // ncclAvg
    }
    if (NCCL_VERSION_CODE >= NCCL_VERSION(2,11,0) && test_ncclVersion >= NCCL_VERSION(2,11,0)) {
      test_opnum++; // PreMulSum
    }
    #if defined(__CUDA_BF16_TYPES_EXIST__)
    if (NCCL_VERSION_CODE >= NCCL_VERSION(2,10,0) && test_ncclVersion >= NCCL_VERSION(2,10,0)) {
      test_typenum++; // bfloat16
    }
    #endif
    #if defined(__CUDA_FP8_TYPES_EXIST__)
    if (NCCL_VERSION_CODE >= NCCL_VERSION(2,24,0) && test_ncclVersion >= NCCL_VERSION(2,24,0)) {
      test_typenum += 2; // fp8 e4m3,e5m2
    }
    #endif
  #endif

  // Parse args
  double parsed;
  int longindex;
  char *output_file = nullptr;

  static struct option longopts[] = {
    {"nthreads", required_argument, 0, 't'},
    {"ngpus", required_argument, 0, 'g'},
    {"minbytes", required_argument, 0, 'b'},
    {"maxbytes", required_argument, 0, 'e'},
    {"stepbytes", required_argument, 0, 'i'},
    {"stepfactor", required_argument, 0, 'f'},
    {"iters", required_argument, 0, 'n'},
    {"agg_iters", required_argument, 0, 'm'},
    {"warmup_iters", required_argument, 0, 'w'},
    {"run_cycles", required_argument, 0, 'N'},
    {"parallel_init", required_argument, 0, 'p'},
    {"check", required_argument, 0, 'c'},
    {"op", required_argument, 0, 'o'},
    {"datatype", required_argument, 0, 'd'},
    {"root", required_argument, 0, 'r'},
    {"blocking", required_argument, 0, 'z'},
    {"stream_null", required_argument, 0, 'y'},
    {"timeout", required_argument, 0, 'T'},
    {"cudagraph", required_argument, 0, 'G'},
    {"report_cputime", required_argument, 0, 'C'},
    {"report_timestamps", required_argument, 0, 'S'},
    {"output_file", required_argument, 0, 'J'},
    {"average", required_argument, 0, 'a'},
    {"local_register", required_argument, 0, 'R'},
    {"cta_policy", required_argument, 0, 'x'},
    {"device_implementation", required_argument, 0, 'D'},
    {"device_cta_count", required_argument, 0, 'V'},
    {"memory", required_argument, 0, 'M'},
    {"unalign", required_argument, 0, 'u'},
    {"per_iter_timing", required_argument, 0, 'I'},
    {"per_iter_skip", required_argument, 0, 'K'},
    {"host_rma_implementation", required_argument, 0, 'H'},
    {"tuning", required_argument, 0, 'U'},
    {"help", no_argument, 0, 'h'},
    {}
  };

  while(1) {
    int c;
    c = getopt_long(argc, argv, "t:g:b:e:i:f:n:m:w:N:p:I:K:c:o:d:r:z:y:T:hG:C:a:R:x:D:V:J:S:M:u:H:U:", longopts, &longindex);

    if (c == -1)
      break;

    switch(c) {
      case 't':
        nThreads = strtol(optarg, NULL, 0);
        break;
      case 'g':
        nGpus = strtol(optarg, NULL, 0);
        break;
      case 'b':
        parsed = parsesize(optarg);
        if (parsed < 0) {
          fprintf(stderr, "invalid size specified for 'minbytes'\n");
          return -1;
        }
        minBytes = (size_t)parsed;
        break;
      case 'e':
        parsed = parsesize(optarg);
        if (parsed < 0) {
          fprintf(stderr, "invalid size specified for 'maxbytes'\n");
          return -1;
        }
        maxBytes = (size_t)parsed;
        break;
      case 'i':
        parsed = parsesize(optarg);
        if (parsed < 0) {
          fprintf(stderr, "invalid size specified for 'stepBytes'\n");
          return -1;
        }
        stepBytes = (size_t)parsed;
        break;
      case 'f':
        stepFactor = strtol(optarg, NULL, 0);
        break;
      case 'n':
        iters = (int)strtol(optarg, NULL, 0);
        break;
      case 'm':
#if NCCL_MAJOR > 2 || (NCCL_MAJOR >= 2 && NCCL_MINOR >= 2)
        agg_iters = (int)strtol(optarg, NULL, 0);
#else
        fprintf(stderr, "Option -m not supported before NCCL 2.2. Ignoring\n");
#endif
        break;
      case 'w':
        warmup_iters = (int)strtol(optarg, NULL, 0);
        break;
      case 'N':
        run_cycles = (int)strtol(optarg, NULL, 0);
        break;
      case 'c':
        datacheck = (int)strtol(optarg, NULL, 0);
        break;
      case 'p':
        parallel_init = (int)strtol(optarg, NULL, 0);
        break;
      case 'o':
        ncclop = ncclstringtoop(optarg);
        break;
      case 'd':
        nccltype = ncclstringtotype(optarg);
        break;
      case 'r':
        ncclroot = strtol(optarg, NULL, 0);
        break;
      case 'z':
        blocking_coll = strtol(optarg, NULL, 0);
        break;
      case 'y':
        streamnull = strtol(optarg, NULL, 0);
        break;
      case 'T':
        timeout = strtol(optarg, NULL, 0);
        break;
      case 'G':
#if (NCCL_MAJOR > 2 || (NCCL_MAJOR >= 2 && NCCL_MINOR >= 9)) && CUDART_VERSION >= 11030
        cudaGraphLaunches = strtol(optarg, NULL, 0);
#else
        printf("Option -G (CUDA graph) not supported before NCCL 2.9 + CUDA 11.3. Ignoring\n");
#endif
        break;
      case 'C':
        report_cputime = strtol(optarg, NULL, 0);
        break;
      case 'J':
        output_file = strdup(optarg);
        break;
      case 'S':
        report_timestamps = strtol(optarg, NULL, 0);
        break;
      case 'a':
        average = (int)strtol(optarg, NULL, 0);
        break;
      case 'R':
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,19,0)
        local_register = (int)strtol(optarg, NULL, 0);
        if (local_register == SYMMETRIC_REGISTER && test_ncclVersion < NCCL_VERSION(2,27,0)) {
          printf("Option -R 2 (symmetric) is not supported before NCCL 2.27. Defaulting to local registration\n");
          local_register = LOCAL_REGISTER;
        }
#else
        printf("Option -R (register) is not supported before NCCL 2.19. Ignoring\n");
#endif
        break;
      case 'M':
        memory_report = (int)strtol(optarg, NULL, 0);
        break;
      case 'I':
        per_iter_timing = (int)strtol(optarg, NULL, 0);
        break;
      case 'K':
        per_iter_skip = (int)strtol(optarg, NULL, 0);
        break;
      case 'U':
        tuning = (int)strtol(optarg, NULL, 0);
        if (tuning && test_ncclVersion < NCCL_VERSION(2,28,0)) {
          printf("Option -U (tuning) is not supported before NCCL 2.28. Ignoring\n");
          tuning = 0;
        }
        break;
      case 'x':
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,27,0)
        ctaPolicy = (int)strtol(optarg, NULL, 0);
        if (ctaPolicy > 1 && test_ncclVersion < NCCL_VERSION(2,28,0)) {
          printf("Option -x (cta_policy) %d is not supported before NCCL 2.28. Ignoring\n", ctaPolicy);
          ctaPolicy = -1;
        }
#else
        printf("Option -x (cta_policy) is not supported before NCCL 2.27. Ignoring\n");
#endif
        break;
      case 'D':
	if (test_ncclVersion >= NCCL_VERSION(2,28,0)) {
          deviceImpl = (int)strtol(optarg, NULL, 0);
        } else {
          fprintf(stderr, "Option -D (device implementation) requires NCCL >= 2.28.0\n");
          return -1;
        }
        break;
      case 'V':
	if (test_ncclVersion >= NCCL_VERSION(2,28,0)) {
          deviceCtaCount = (int)strtol(optarg, NULL, 0);
          if (deviceCtaCount <= 0 || deviceCtaCount > 128) {
            fprintf(stderr, "device_cta_count (-V) must be positive and less than 128, got %d. "
                    "Using default value 16.\n", deviceCtaCount);
            deviceCtaCount = 16;
          }
        } else {
          fprintf(stderr, "Option -V (device CTA count) requires NCCL >= 2.28.0\n");
          return -1;
	}
        break;
      case 'u':
        unalign = (int)strtol(optarg, NULL, 0);
        break;
      case 'H':
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,29,0)
        if (test_ncclVersion >= NCCL_VERSION(2,29,0)) {
          char* endptr = NULL;
          hostRmaImpl = 1;
          rmaCtxCount = (int)strtol(optarg, &endptr, 0);
          if (*endptr != '\0' || rmaCtxCount < 1) {
            fprintf(stderr, "Option -H (host RMA implementation) takes a positive number of RMA contexts, got '%s'\n", optarg);
            return -1;
          }
        } else {
          fprintf(stderr, "Option -H (host RMA implementation) requires NCCL >= 2.29.0\n");
          return -1;
        }
#else
        fprintf(stderr, "Option -H (host RMA implementation) requires nccl-tests to be compiled with NCCL >= 2.29.0\n");
        return -1;
#endif
        break;
      case 'h':
      default:
        if (c != 'h') printf("invalid option '%c'\n", c == '?' && optopt ? optopt : c);
        printf("USAGE: %s \n\t"
            "[-t,--nthreads <num threads>] \n\t"
            "[-g,--ngpus <gpus per thread>] \n\t"
            "[-b,--minbytes <min size in bytes>] \n\t"
            "[-e,--maxbytes <max size in bytes>] \n\t"
            "[-i,--stepbytes <increment size>] \n\t"
            "[-f,--stepfactor <increment factor>] \n\t"
            "[-n,--iters <iteration count>] \n\t"
            "[-m,--agg_iters <aggregated iteration count>] \n\t"
            "[-w,--warmup_iters <warmup iteration count>] \n\t"
            "[-N,--run_cycles <cycle count> run & print each cycle (default: 1; 0=infinite)] \n\t"
            "[-p,--parallel_init <0/1>] \n\t"
            "[-c,--check <check iteration count>] \n\t"
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,11,0)
            "[-o,--op <sum/prod/min/max/avg/mulsum/all>] \n\t"
#elif NCCL_VERSION_CODE >= NCCL_VERSION(2,10,0)
            "[-o,--op <sum/prod/min/max/avg/all>] \n\t"
#else
            "[-o,--op <sum/prod/min/max/all>] \n\t"
#endif
            "[-d,--datatype <nccltype/all>] \n\t"
            "[-r,--root <root>] \n\t"
            "[-z,--blocking <0/1/2/3> 1=barrier after each inner iter (-m), 2=no barrier, 3=wait and barrier after each outer iter (-n)] \n\t"
            "[-y,--stream_null <0/1>] \n\t"
            "[-T,--timeout <time in seconds>] \n\t"
            "[-G,--cudagraph <num graph launches>] \n\t"
            "[-C,--report_cputime <0/1>] \n\t"
            "[-S,--report_timestamps <0/1> report timestamps (default 0)] \n\t"
            "[-J,--output_file <file> write output to filepath, if accessible. Infer type from suffix (only json supported presently.)] \n\t"
            "[-a,--average <0/1/2/3> report average iteration time <0=RANK0/1=AVG/2=MIN/3=MAX>] \n\t"
            "[-R,--local_register <0/1/2> enable local (1) or symmetric (2) buffer registration on send/recv buffers (default: disable (0))] \n\t"
            "[-x,--cta_policy <0/1/2> set CTA policy (NCCL_CTA_POLICY_DEFAULT (0), NCCL_CTA_POLICY_EFFICIENCY (1), NCCL_CTA_POLICY_ZERO (2)) (default: do not set)] \n\t"
            "[-D,--device_implementation <implementation number> enable device implementation (default: 0, use NCCL implementation; requires -R 2 if > 0)] \n\t"
            "[-V,--device_cta_count <number> set number of CTAs for device implementation (default: 16)] \n\t"
            "[-H,--host_rma_implementation <num RMA contexts> enable Host RMA API implementations using <num> RMA contexts\n\t"
            "    (1 = single context; >1 distributes RMA ops across contexts and requires NCCL >= 2.31.0; requires -R 2)] \n\t"
            "[-M,--memory <0/1> enable memory usage report (default: 0)] \n\t"
            "[-u,--unalign <index of first element> Misalign source and destination buffers (default: 0)] \n\t"
            "[-I,--per_iter_timing <0/1> per-iteration CUDA event timing\n\t"
            "    (best with -z 0, -z 2, or -z 3; with -z 1 includes barrier wait;\n\t"
            "    i_p99 uses nearest-rank percentile and may equal i_max\n\t"
            "    with <100 samples) (default: 0)] \n\t"
            "[-K,--per_iter_skip <count> exclude leading samples from -I summary stats (default: 0)] \n\t"
            "[-U,--tuning <0/1> report NCCL tuning info (NCCL >= 2.28; full detail >= 2.31) (default: 0)] \n\t"
            "[-h,--help]\n",
          programName);
        return 0;
    }
  }
  if (minBytes > maxBytes) {
    fprintf(stderr, "invalid sizes for 'minbytes' and 'maxbytes': %llu > %llu\n",
           (unsigned long long)minBytes,
           (unsigned long long)maxBytes);
    return -1;
  }
  if (deviceImpl > 0 && (local_register != SYMMETRIC_REGISTER)) {
    fprintf(stderr, "device implementation (-D > 0) requires enabling symmetric memory registration (-R 2)\n");
    return -1;
  }
  if (hostRmaImpl && deviceImpl > 0) {
    fprintf(stderr, "Cannot use both -H (host RMA implementation) and -D (device implementation) at the same time\n");
    return -1;
  }
  if (hostRmaImpl && (local_register != SYMMETRIC_REGISTER)) {
    fprintf(stderr, "host RMA implementation (-H) requires enabling symmetric memory registration (-R 2)\n");
    return -1;
  }
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,31,0)
  if (rmaCtxCount > 1 && test_ncclVersion < NCCL_VERSION(2,31,0))
#else
  if (rmaCtxCount > 1)
#endif
  {
    fprintf(stderr, "more than one RMA context (-H %d) requires NCCL >= 2.31.0\n", rmaCtxCount);
    return -1;
  }
  if (per_iter_timing != 0 && per_iter_timing != 1) {
    fprintf(stderr, "per-iteration timing (-I) only supports 0=off or 1=on. Disabling.\n");
    per_iter_timing = 0;
  }
  if (per_iter_timing && cudaGraphLaunches >= 1) {
    fprintf(stderr, "per-iteration timing (-I) is incompatible with CUDA graph mode (-G). Disabling.\n");
    per_iter_timing = 0;
  }
  if (blocking_coll == 3 && cudaGraphLaunches >= 1) {
    fprintf(stderr, "blocking mode (-z 3) is incompatible with CUDA graph mode (-G). Disabling.\n");
    blocking_coll = 0;
  }
  if (per_iter_skip < 0 || per_iter_skip >= iters) {
    fprintf(stderr, "per-iteration skip (-K) must be between 0 and %d. Disabling.\n", iters - 1);
    per_iter_skip = 0;
  }
  if (per_iter_skip && !per_iter_timing) {
    fprintf(stderr, "per-iteration skip (-K) requires per-iteration timing (-I 1). Disabling.\n");
    per_iter_skip = 0;
  }

  if (tuning) {
    const char* profilerPlugin = getenv("NCCL_PROFILER_PLUGIN");
    if (profilerPlugin && strcmp(profilerPlugin, "STATIC_PLUGIN") != 0) {
      fprintf(stderr, "Option -U overrides NCCL_PROFILER_PLUGIN=%s with STATIC_PLUGIN\n", profilerPlugin);
    }
#if defined(NCCL_OS_WINDOWS)
    _putenv_s("NCCL_PROFILER_PLUGIN", "STATIC_PLUGIN");
#else
    setenv("NCCL_PROFILER_PLUGIN", "STATIC_PLUGIN", 1);
#endif
  }

#ifdef MPI_SUPPORT
  MPI_Init(&argc, &argv);
#endif

  const output_file_type_t output_file_type = classifyOutputFile(output_file);
  outputFileInit(output_file_type, output_file, argc, argv, envp);

  if(output_file) {
    free(output_file);
    output_file = nullptr;
  }

  testResult_t result = run();

  outputFileFinalize(output_file_type);

  TESTCHECK(result);

  return 0;
}

#ifdef MPI_SUPPORT
// parse int for base 2/10/16, will ignore first whitespaces
static bool parseInt(char *s, int *num) {
  char *p = NULL;
  if (!s || !num)
    return false;
  while (*s && isspace(*s)) ++s;
  if (!*s) return false;

  if (ncclTestStrncasecmp(s, "0b", 2) == 0)
    *num = (int)strtoul(s + 2, &p, 2);
  else
    *num = (int)strtoul(s, &p, 0);

  if (p == s)
    return false;
  return true;
}
#endif

testResult_t run() {
  int totalProcs = 1, proc = 0, ncclProcs = 1, ncclProc = 0, color = 0;
  int localRank = 0;
  char hostname[1024];
  getHostName(hostname, 1024);

#ifdef MPI_SUPPORT
  MPI_Comm_size(MPI_COMM_WORLD, &totalProcs);
  MPI_Comm_rank(MPI_COMM_WORLD, &proc);
  std::vector<uint64_t> hostHashs(totalProcs);
  hostHashs[proc] = getHostHash(hostname);
  MPI_Allgather(MPI_IN_PLACE, 0, MPI_DATATYPE_NULL, hostHashs.data(), sizeof(uint64_t), MPI_BYTE, MPI_COMM_WORLD);
  for (int p=0; p<totalProcs; p++) {
    if (p == proc) break;
    if (hostHashs[p] == hostHashs[proc]) localRank++;
  }

  char *splitMaskEnv = NULL;
  if (splitMaskEnv = getenv("NCCL_TESTS_SPLIT_MASK")) {
    color = proc & strtoul(splitMaskEnv, NULL, 16);
  } else if (splitMaskEnv = getenv("NCCL_TESTS_SPLIT")) {
    if (
      (ncclTestStrncasecmp(splitMaskEnv, "AND", strlen("AND")) == 0 && parseInt(splitMaskEnv + strlen("AND"), &color)) ||
      (ncclTestStrncasecmp(splitMaskEnv, "&", strlen("&")) == 0 && parseInt(splitMaskEnv + strlen("&"), &color))
    )
        color = proc & color;
    if (
      (ncclTestStrncasecmp(splitMaskEnv, "OR", strlen("OR")) == 0 && parseInt(splitMaskEnv + strlen("OR"), &color)) ||
      (ncclTestStrncasecmp(splitMaskEnv, "|", strlen("|")) == 0 && parseInt(splitMaskEnv + strlen("|"), &color))
    )
        color = proc | color;
    if (
      (ncclTestStrncasecmp(splitMaskEnv, "MOD", strlen("MOD")) == 0 && parseInt(splitMaskEnv + strlen("MOD"), &color)) ||
      (ncclTestStrncasecmp(splitMaskEnv, "%", strlen("%")) == 0 && parseInt(splitMaskEnv + strlen("%"), &color))
    )
        color = proc % color;
    if (
      (ncclTestStrncasecmp(splitMaskEnv, "DIV", strlen("DIV")) == 0 && parseInt(splitMaskEnv + strlen("DIV"), &color)) ||
      (ncclTestStrncasecmp(splitMaskEnv, "/", strlen("/")) == 0 && parseInt(splitMaskEnv + strlen("/"), &color))
    )
        color = proc / color;
  }

  MPI_Comm mpi_comm;
  MPI_Comm_split(MPI_COMM_WORLD, color, proc, &mpi_comm);
  MPI_Comm_size(mpi_comm, &ncclProcs);
  MPI_Comm_rank(mpi_comm, &ncclProc);
#endif
  is_main_thread = is_main_proc = (proc == 0) ? 1 : 0;

  jsonIdentifyWriter(is_main_thread);

  size_t maxMem = ~0;
  testResult_t report_result = writeDeviceReport(&maxMem, localRank, proc, totalProcs, color, hostname, programName);
  if(report_result != testSuccess) {
    return report_result;
  }

  // Reserve 1GiB of memory for each 16GiB installed, but limit to a max of 4GiB
  const size_t GB = (1ULL << 30);
  size_t reserveMem =  std::min(DIVUP(maxMem, 16*GB) * 1*GB, 4*GB);
  // We need sendbuff, recvbuff, expected (when datacheck enabled), plus 1G for the rest.
  size_t memMaxBytes = (maxMem - reserveMem - 1*GB) / (datacheck ? 3 : 2);
  if (maxBytes > memMaxBytes) {
    maxBytes = memMaxBytes;
    if (minBytes > maxBytes) minBytes = maxBytes;
    if (proc == 0) printf("#\n# Reducing maxBytes to %ld due to memory limitation\n", maxBytes);
  }

  ncclUniqueId ncclId;
  if (ncclProc == 0) {
    NCCLCHECK(ncclGetUniqueId(&ncclId));
  }
#ifdef MPI_SUPPORT
  MPI_Bcast(&ncclId, sizeof(ncclId), MPI_BYTE, 0, mpi_comm);
  MPI_Barrier(MPI_COMM_WORLD); // Ensure Bcast is complete for HCOLL
#endif
  std::vector<int> gpus(nGpus*nThreads);
  std::vector<cudaStream_t> streams(nGpus*nThreads);
  std::vector<void*> sendbuffs(nGpus*nThreads);
  std::vector<void*> recvbuffs(nGpus*nThreads);
  std::vector<void*> expected(nGpus*nThreads);
  size_t sendBytes, recvBytes;
  size_t allocBytes;

  ncclTestEngine.getBuffSize(&sendBytes, &recvBytes, (size_t)maxBytes, (size_t)ncclProcs*nGpus*nThreads);

  char* envstr = getenv("NCCL_TESTS_DEVICE");
  int gpu0 = envstr ? atoi(envstr) : -1;
  for (int i=0; i<nGpus*nThreads; i++) {
    gpus[i] = (gpu0 != -1 ? gpu0 : localRank*nThreads*nGpus) + i;
    CUDACHECK(cudaSetDevice(gpus[i]));
    if (streamnull) {
      streams[i] = NULL;
    }
    else {
      CUDACHECK(cudaStreamCreateWithFlags(streams.data()+i, cudaStreamNonBlocking));
    }
    int archMajor, archMinor;
    CUDACHECK(cudaDeviceGetAttribute(&archMajor, cudaDevAttrComputeCapabilityMajor, gpus[i]));
    CUDACHECK(cudaDeviceGetAttribute(&archMinor, cudaDevAttrComputeCapabilityMinor, gpus[i]));
    minCudaArch = std::min(minCudaArch, 100*archMajor + 10*archMinor);
  }

#ifdef MPI_SUPPORT
  MPI_Allreduce(MPI_IN_PLACE, &minCudaArch, 1, MPI_INT, MPI_MIN, MPI_COMM_WORLD);
#endif
#if defined(__CUDA_FP8_TYPES_EXIST__)
  if (NCCL_VERSION_CODE >= NCCL_VERSION(2,24,0) && test_ncclVersion >= NCCL_VERSION(2,24,0)) {
    if (minCudaArch < 900) { // Filter out fp8 on pre-Hopper hardware
      int n = 0;
      for (int i=0; i < test_typenum; i++) {
        if (!(test_types[i] == ncclFloat8e4m3 || test_types[i] == ncclFloat8e5m2)) {
          test_types[n] = test_types[i];
          test_typenames[n] = test_typenames[i];
          n += 1;
        }
      }
      test_typenum = n;
    }
  }
#endif

  //if parallel init is not selected, use main thread to initialize NCCL
  ncclComm_t* comms = (ncclComm_t*)malloc(sizeof(ncclComm_t)*nThreads*nGpus);
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,19,0)
  std::vector<void*> sendRegHandles(nThreads*nGpus);
  std::vector<void*> recvRegHandles(nThreads*nGpus);
#endif
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,28,0)
  std::vector<ncclDevComm> devComms(nThreads*nGpus);
#endif
  std::vector<int64_t> initGpuMem(nThreads);
  std::vector<int64_t> bufferMemory(nThreads);
  if (!parallel_init) {
    // Capture the memory used by the GPUs before initializing the NCCL communicators
    int64_t* initFreeGpuMem = (int64_t*)calloc(nGpus*3, sizeof(int64_t));
    for (int g = 0; g < nGpus; ++g) {
      CUDACHECK(cudaSetDevice(gpus[g]));
      getGPUMemoryInfo(nullptr, &initFreeGpuMem[g]);
    }
    //if parallel init is not selected, use main thread to initialize NCCL
    TESTCHECK(initComms(comms, nGpus*nThreads, ncclProc*nThreads*nGpus, ncclProcs*nThreads*nGpus, gpus.data(), ncclId));

     // Capture the memory used by the GPUs after initializing the NCCL communicators
     for (int g = 0; g < nGpus; ++g) {
       CUDACHECK(cudaSetDevice(gpus[g]));
       getGPUMemoryInfo(nullptr, &initFreeGpuMem[g + nGpus]);
     }
     for ( size_t t = 0; t < nThreads; ++t) {
       for (int g = 0; g < nGpus; ++g) {
         initGpuMem[t] = std::max(initGpuMem[t], initFreeGpuMem[g] - initFreeGpuMem[g + nGpus]);
       }
     }
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,19,0)
     NCCLCHECK(ncclGroupStart());
     for (int i=0; i<nGpus*nThreads; i++) {
       CUDACHECK(cudaSetDevice(gpus[i]));
       TESTCHECK(AllocateBuffs(sendbuffs.data()+i, sendBytes, recvbuffs.data()+i, recvBytes, expected.data()+i, (size_t)maxBytes, &allocBytes));
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,27,0)
       if (test_ncclVersion >= NCCL_VERSION(2,27,0) && (local_register == SYMMETRIC_REGISTER)) {
         NCCLCHECK(ncclCommWindowRegister(comms[i], sendbuffs[i], allocBytes, (ncclWindow_t*)&sendRegHandles[i], NCCL_WIN_COLL_SYMMETRIC));
         NCCLCHECK(ncclCommWindowRegister(comms[i], recvbuffs[i], allocBytes, (ncclWindow_t*)&recvRegHandles[i], NCCL_WIN_COLL_SYMMETRIC));
       } else
#endif
       {
         if (local_register) NCCLCHECK(ncclCommRegister(comms[i], sendbuffs[i], allocBytes, &sendRegHandles[i]));
         if (local_register) NCCLCHECK(ncclCommRegister(comms[i], recvbuffs[i], allocBytes, &recvRegHandles[i]));
       }
     }
     NCCLCHECK(ncclGroupEnd());
#endif
#if NCCL_TESTS_HAS_HOST_RMA_SUPPORT_PROPERTY
     if (hostRmaImpl) {
       ncclCommProperties_t commProperties = NCCL_COMM_PROPERTIES_INITIALIZER;
       NCCLCHECK(ncclCommQueryProperties(comms[0], &commProperties));
       if (!commProperties.hostRmaSupport) {
         fprintf(stderr, "Host RMA is not supported on this system\n");
         return testInvalidUsage;
       }
     }
#endif
     // Capture memory used by after allocating buffers
     for (int g = 0; g < nGpus; ++g) {
       CUDACHECK(cudaSetDevice(gpus[g]));
       getGPUMemoryInfo(nullptr, &initFreeGpuMem[g + nGpus*2]);
     }
     for ( size_t t = 0; t < nThreads; ++t) {
      for (int g = 0; g < nGpus; ++g) {
        bufferMemory[t] = std::max(bufferMemory[t], initFreeGpuMem[g + nGpus] - initFreeGpuMem[g + nGpus*2]);
      }
     }
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,28,0)
     /* Create device communicators based on test-specific requirements */
     if (deviceImpl) {
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,29,0)
      if (test_ncclVersion < NCCL_VERSION(2,29,0)) {
        fprintf(stderr,
          "Incompatible NCCL versions. nccl-tests was compiled with NCCL %d, but is running with NCCL %d. "
          "The %d Device API is not compatible with versions before 2.29.\n",
          NCCL_VERSION_CODE, test_ncclVersion, NCCL_VERSION_CODE);
        return testInvalidUsage;
      }
      ncclDevCommRequirements reqs = NCCL_DEV_COMM_REQUIREMENTS_INITIALIZER;
      if (!ncclTestEngine.getDevCommRequirements) {
        fprintf(stderr, "Device implementation %d is not supported by this test\n", deviceImpl);
        return testNotImplemented;
      }
      TESTCHECK(ncclTestEngine.getDevCommRequirements(deviceImpl, &reqs, comms[0]));
#else
      if (test_ncclVersion >= NCCL_VERSION(2,29,0)) {
        fprintf(stderr, "Incompatible NCCL versions. nccl-tests was compiled with NCCL 2.28, but is running with NCCL %d. "
          "The 2.28 Device API is not compatible with later versions.\n", test_ncclVersion);
        return testInvalidUsage;
      }
      ncclDevCommRequirements reqs = {};
      if (!ncclTestEngine.getDevCommRequirements ||
          !ncclTestEngine.getDevCommRequirements(deviceImpl, &reqs)) {
        fprintf(stderr, "Device implementation %d is not supported by this test\n", deviceImpl);
        return testNotImplemented;
      }
#endif

       NCCLCHECK(ncclGroupStart());
       for (int i = 0; i < nGpus * nThreads; i++) {
         NCCLCHECK(ncclDevCommCreate(comms[i], &reqs, devComms.data()+i));
       }
       NCCLCHECK(ncclGroupEnd());
     }
     int64_t deviceCommMaxMem = 0;
     for (int g = 0; g < nGpus; ++g) {
       CUDACHECK(cudaSetDevice(gpus[g]));
       int64_t freeGpuMem;
       getGPUMemoryInfo(nullptr, &freeGpuMem);
       deviceCommMaxMem = std::max(deviceCommMaxMem, initFreeGpuMem[g + nGpus*2] - freeGpuMem);
     }
     for ( size_t t = 0; t < nThreads; ++t) {
       initGpuMem[t] += deviceCommMaxMem;
     }
#endif
    free(initFreeGpuMem);
  }

  std::vector<int> errors(nThreads);
  std::vector<double> bw(nThreads);
  std::vector<int64_t> devMemUsed(nThreads);
  std::vector<int> bw_count(nThreads);
  for (int t=0; t<nThreads; t++) {
    bw[t] = 0.0;
    errors[t] = bw_count[t] = 0;
    devMemUsed[t] = std::numeric_limits<int64_t>::min();
  }

  fflush(stdout);

  writeResultHeader(report_cputime, report_timestamps);

  std::vector<struct testThread> threads(nThreads);

  for (int t=nThreads-1; t>=0; t--) {
    threads[t].args.minbytes=minBytes;
    threads[t].args.maxbytes=maxBytes;
    threads[t].args.stepbytes=stepBytes;
    threads[t].args.stepfactor=stepFactor;
    threads[t].args.localRank = localRank;

    threads[t].args.totalProcs=totalProcs;
    threads[t].args.nProcs=ncclProcs;
    threads[t].args.proc=ncclProc;
    threads[t].args.nThreads=nThreads;
    threads[t].args.thread=t;
    threads[t].args.nGpus=nGpus;
    threads[t].args.gpus=gpus.data()+t*nGpus;
    threads[t].args.sendbuffs = sendbuffs.data()+t*nGpus;
    threads[t].args.recvbuffs = recvbuffs.data()+t*nGpus;
    threads[t].args.expected = expected.data()+t*nGpus;
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,28,0)
    threads[t].args.devComms = devComms.data()+t*nGpus;
#endif
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,19,0)
    threads[t].args.sendRegHandles = sendRegHandles.data()+t*nGpus;
    threads[t].args.recvRegHandles = recvRegHandles.data()+t*nGpus;
#endif
    threads[t].args.ncclId = ncclId;
    threads[t].args.comms=comms+t*nGpus;
    threads[t].args.streams=streams.data()+t*nGpus;

    threads[t].args.errors=errors.data()+t;
    threads[t].args.bw=bw.data()+t;
    threads[t].args.bw_count=bw_count.data()+t;
    threads[t].args.initGpuMem = initGpuMem.data() + t;
    threads[t].args.bufferMemory = bufferMemory.data() + t;
    threads[t].args.devMemUsed = devMemUsed.data() + t;

    threads[t].args.reportErrors = datacheck;

    threads[t].func = parallel_init ? threadInit : threadRunTests;
    if (t)
      TESTCHECK(threadLaunch(threads.data()+t));
    else
      TESTCHECK(threads[t].func(&threads[t].args));
  }

  // Wait for other threads and accumulate stats and errors
  for (int t=nThreads-1; t>=0; t--) {
    if (t) threads[t].thread.join();
    TESTCHECK(threads[t].ret);
    if (t) {
      errors[0] += errors[t];
      bw[0] += bw[t];
      bw_count[0] += bw_count[t];
      devMemUsed[0] = std::max(devMemUsed[0], devMemUsed[t]);
      initGpuMem[0] = std::max(initGpuMem[0], initGpuMem[t]);
      bufferMemory[0] = std::max(bufferMemory[0], bufferMemory[t]);
    }
  }

#ifdef MPI_SUPPORT
  MPI_Allreduce(MPI_IN_PLACE, &errors[0], 1, MPI_INT, MPI_SUM, MPI_COMM_WORLD);
  MPI_Allreduce(MPI_IN_PLACE, &devMemUsed[0], 1, MPI_INT64_T, MPI_MAX, MPI_COMM_WORLD);
  MPI_Allreduce(MPI_IN_PLACE, &initGpuMem[0], 1, MPI_INT64_T, MPI_MAX, MPI_COMM_WORLD);
  MPI_Allreduce(MPI_IN_PLACE, &bufferMemory[0], 1, MPI_INT64_T, MPI_MAX, MPI_COMM_WORLD);
#endif

  if (!parallel_init) {
    for(int i=0; i<nGpus*nThreads; ++i) {
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,19,0)
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,27,0)
      if (test_ncclVersion >= NCCL_VERSION(2,27,0) && (local_register == SYMMETRIC_REGISTER)) {
        NCCLCHECK(ncclCommWindowDeregister(comms[i], (ncclWindow_t)sendRegHandles[i]));
        NCCLCHECK(ncclCommWindowDeregister(comms[i], (ncclWindow_t)recvRegHandles[i]));
      } else
#endif
      {
        if (local_register) NCCLCHECK(ncclCommDeregister(comms[i], sendRegHandles[i]));
        if (local_register) NCCLCHECK(ncclCommDeregister(comms[i], recvRegHandles[i]));
      }
#endif
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,28,0)
      if (deviceImpl) {
        NCCLCHECK(ncclDevCommDestroy(comms[i], devComms.data()+i));
      }
#endif
      NCCLCHECK(ncclCommDestroy(comms[i]));
    }
    free(comms);
  }

  // Free off CUDA allocated memory
  for (int i=0; i<nGpus*nThreads; i++) {
#if NCCL_VERSION_CODE >= NCCL_VERSION(2,19,0)
    if (sendbuffs[i]) NCCLCHECK(ncclMemFree((char*)sendbuffs[i]));
    if (recvbuffs[i]) NCCLCHECK(ncclMemFree((char*)recvbuffs[i]));
    if (datacheck) NCCLCHECK(ncclMemFree(expected[i]));
#else
    if (sendbuffs[i]) CUDACHECK(cudaFree((char*)sendbuffs[i]));
    if (recvbuffs[i]) CUDACHECK(cudaFree((char*)recvbuffs[i]));
    if (datacheck) CUDACHECK(cudaFree(expected[i]));
#endif
  }

  envstr = getenv("NCCL_TESTS_MIN_BW");
  const double check_avg_bw = envstr ? atof(envstr) : -1;
  bw[0] /= bw_count[0];

  writeResultFooter(errors.data(), bw.data(), check_avg_bw, programName);
  if (memory_report) {
    memInfo_t memInfos[3];
    memInfos[0] = { initGpuMem[0], "Initialization" };
    memInfos[1] = { bufferMemory[0], "User-Allocated" };
    memInfos[2] = { devMemUsed[0], "Collective" };
    writeMemInfo(memInfos, 3);
  }
  finalizeFooter();

#ifdef MPI_SUPPORT
  MPI_Comm_free(&mpi_comm);
  MPI_Finalize();
#endif

  writeErrors();

  // 'cuda-memcheck --leak-check full' requires this
  cudaDeviceReset();

  if (errors[0] || bw[0] < check_avg_bw*(0.9))
    return testNumResults;
  else
    return testSuccess;
}
