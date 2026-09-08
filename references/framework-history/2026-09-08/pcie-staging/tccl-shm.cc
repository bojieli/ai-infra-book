/*************************************************************************
 * Copyright (c) 2016-2022, NVIDIA CORPORATION. All rights reserved.
 * Modifications Copyright (c) 2024 Seoul National University. All rights reserved.
 *
 * See LICENSE.txt for license information
 ************************************************************************/

#include "comm.h"
#include "shm.h"
#include <numa.h>
#include <numaif.h>

struct shmConnectInfo {
  char shmName[7];
  int shmSize;
  char numaShmName[7];
  int numaShmSize;
};
static_assert(sizeof(shmConnectInfo) <= CONNECT_SIZE, "SHM Connect info is too large");

struct shmSendResources {
  int remShmSize;
  struct ncclRecvMem* remHostMem;
  struct ncclRecvMem* devRemHostMem;
  ncclShmHandle_t remHandle;
  int shmSize;
  struct ncclSendMem* hostMem;
  struct ncclSendMem* devHostMem;
  ncclShmHandle_t hostHandle;
  int useMemcpySend;
  int useMemcpyRecv;
  int numaIdx;
  int numaSize;
  void* numaMem;
  void* devNumaMem;
  ncclShmHandle_t numaHandle;
};

struct shmRecvResources {
  int remShmSize;
  struct ncclSendMem* remHostMem;
  struct ncclSendMem* devRemHostMem;
  ncclShmHandle_t remHandle;
  int shmSize;
  struct ncclRecvMem* hostMem;
  struct ncclRecvMem* devHostMem;
  ncclShmHandle_t hostHandle;
  int useMemcpySend;
  int useMemcpyRecv;
  int numaIdx;
  int numaSize;
  void* numaMem;
  void* devNumaMem;
  ncclShmHandle_t numaHandle;
};

const int tcclShmTransportSendResourceMemcpyOffset = offsetof(shmSendResources, useMemcpySend);
const int tcclShmTransportRecvResourceMemcpyOffset = offsetof(shmRecvResources, useMemcpyRecv);

/* Determine two peers can communicate with SHM */
static ncclResult_t tcclShmCanConnect(int* ret, struct ncclTopoSystem* topo, struct ncclTopoGraph* graph, struct ncclPeerInfo* info1, struct ncclPeerInfo* info2) {
  *ret = 0;

  int useNet = 0;
  NCCLCHECK(ncclTopoCheckNet(topo, info1->busId, info2->busId, &useNet));
  if (useNet) return ncclSuccess;

  // Same host?
  TRACE(NCCL_INIT|NCCL_SHM, "peer1 hostHash %lx peer2 hostHash %lx", info1->hostHash, info2->hostHash);
  if (info1->hostHash != info2->hostHash) return ncclSuccess;

  // Common /dev/shm (between containers) ?
  TRACE(NCCL_INIT|NCCL_SHM, "peer1 shmDev %lx peer2 shmDev %lx", info1->shmDev, info2->shmDev);
  if (info1->shmDev != info2->shmDev) return ncclSuccess;

  *ret = 1;

  return ncclSuccess;
}

#define MAX_SHM_NAME_LEN 1024

/* Create and return connect structures for this peer to connect to me */
static ncclResult_t tcclShmSendSetup(struct ncclComm* comm, struct ncclTopoGraph* graph, struct ncclPeerInfo* myInfo, struct ncclPeerInfo* peerInfo, struct ncclConnect* connectInfo, struct ncclConnector* send, int channelId, int connIndex) {
  if (comm->proxyState->cudaCtx != NULL) {
    CUPFN(cuCtxSetCurrent(comm->proxyState->cudaCtx));
  }

  struct shmSendResources* resources;
  NCCLCHECK(ncclCalloc(&resources, 1));
  send->transportResources = resources;
  resources->useMemcpySend = comm->tcclComm.sendOpt.shm_send_use_memcpy;
  resources->useMemcpyRecv = comm->tcclComm.sendOpt.shm_recv_use_memcpy;
  resources->numaIdx = comm->tcclComm.sendOpt.shm_numa_idx;

  static_assert(sizeof(struct shmConnectInfo) <= sizeof(struct ncclConnect), "shm Connect Info is too big");
  struct shmConnectInfo* info = (struct shmConnectInfo*)connectInfo;

  char shmPath[PATH_MAX];
  shmPath[0] = '\0';
  int shmSize = sizeof(struct ncclSendMem);
  info->shmSize = resources->shmSize = shmSize;
  NCCLCHECK(ncclShmOpen(shmPath, resources->shmSize, (void**)&resources->hostMem, (void**)&resources->devHostMem, 1, &resources->hostHandle));
  TRACE(NCCL_SHM,"Opened shmName %s shmSize %d", shmPath, info->shmSize);
  memcpy(info->shmName, shmPath+sizeof("/dev/shm/nccl-")-1, sizeof(info->shmName));

  // NUMA is always allocated from the send side
  char numaShmPath[PATH_MAX];
  numaShmPath[0] = '\0';
  int numaShmSize = 0;
  for (int p=0; p<NCCL_NUM_PROTOCOLS; p++) numaShmSize += comm->buffSizes[p];
  info->numaShmSize = resources->numaSize = numaShmSize;
  NCCLCHECK(ncclShmOpen(numaShmPath, resources->numaSize, (void**)&resources->numaMem, (void**)&resources->devNumaMem, 1, &resources->numaHandle, resources->numaIdx));
  memcpy(info->numaShmName, numaShmPath+sizeof("/dev/shm/nccl-")-1, sizeof(info->numaShmName));

  INFO(NCCL_INIT|NCCL_SHM|NCCL_TCCL,"Channel %02d : %d[%d] -> %d[%d] via SHM/%s/%s", channelId, myInfo->rank, myInfo->nvmlDev, peerInfo->rank, peerInfo->nvmlDev,\
      resources->useMemcpySend?"CE":"direct", resources->useMemcpyRecv?"CE":"direct");
  return ncclSuccess;
}

static ncclResult_t tcclShmRecvSetup(struct ncclComm* comm, struct ncclTopoGraph* graph, struct ncclPeerInfo* myInfo, struct ncclPeerInfo* peerInfo, struct ncclConnect* connectInfo, struct ncclConnector* recv, int channelId, int connIndex) {
  if (comm->proxyState->cudaCtx != NULL) {
    CUPFN(cuCtxSetCurrent(comm->proxyState->cudaCtx));
  }

  struct shmRecvResources* resources;
  NCCLCHECK(ncclCalloc(&resources, 1));
  recv->transportResources = resources;
  resources->useMemcpySend = comm->tcclComm.recvOpt.shm_send_use_memcpy;
  resources->useMemcpyRecv = comm->tcclComm.recvOpt.shm_recv_use_memcpy;
  resources->numaIdx = comm->tcclComm.recvOpt.shm_numa_idx;

  static_assert(sizeof(struct shmConnectInfo) <= sizeof(struct ncclConnect), "shm Connect Info is too big");
  struct shmConnectInfo* info = (struct shmConnectInfo*)connectInfo;

  char shmPath[PATH_MAX];
  shmPath[0] = '\0';
  int shmSize = sizeof(struct ncclRecvMem);
  // NUMA is always allocated from the send side; no need to modify shmSize
  info->shmSize = resources->shmSize = shmSize;
  NCCLCHECK(ncclShmOpen(shmPath, resources->shmSize, (void**)&resources->hostMem, (void**)&resources->devHostMem, 1, &resources->hostHandle));
  TRACE(NCCL_SHM,"Opened shmName %s shmSize %d", shmPath, info->shmSize);
  memcpy(info->shmName, shmPath+sizeof("/dev/shm/nccl-")-1, sizeof(info->shmName));

  return ncclSuccess;
}

struct shmProxyInfo {
  struct ncclRecvMem* ceRecvMem;
  char* devFifo;
  char* shmFifo;
  struct ncclSendMem* sendMem;
  struct ncclRecvMem* recvMem;

  // used by progress only
  uint64_t step;
  cudaStream_t stream;
  cudaEvent_t events[NCCL_STEPS];
};

/* Connect to this peer */
static ncclResult_t tcclShmSendConnect(struct ncclComm* comm, struct ncclConnect* connectInfo, int nranks, int rank, struct ncclConnector* send) {
  // Setup device pointers
  struct shmConnectInfo* info = (struct shmConnectInfo*)connectInfo;
  struct shmSendResources* resources = (struct shmSendResources*)send->transportResources;

  char shmPath[PATH_MAX];
  sprintf(shmPath, "/dev/shm/nccl-%s", info->shmName);
  resources->remShmSize = info->shmSize;
  TRACE(NCCL_SHM,"Open shmName %s shmSize %d", shmPath, info->shmSize);
  NCCLCHECK(ncclShmOpen(shmPath, resources->remShmSize, (void**)&resources->remHostMem, (void**)&resources->devRemHostMem, -1, &resources->remHandle));

  // NUMA is opened from the send side; no need to ncclShmOpen separately
  char* buff = (char*)resources->devNumaMem;
  for (int p=0; p<NCCL_NUM_PROTOCOLS; p++) {
    send->conn.buffs[p] = buff;
    buff += comm->buffSizes[p];
  }
  send->conn.tail = &resources->devRemHostMem->tail;
  send->conn.head = &resources->devHostMem->head;

  if (resources->useMemcpyRecv) {
    send->conn.sizesFifo = resources->devRemHostMem->sizesFifo;
  }
  if (resources->useMemcpySend) {
    int tpProxyRank;
    tpProxyRank = comm->topParentRanks[comm->rank];
    NCCLCHECK(ncclProxyConnect(comm, TRANSPORT_TCCL_SHM, 1, tpProxyRank, &send->proxyConn));
    struct shmProxyInfo proxyInfo = { NULL, NULL, send->conn.buffs[NCCL_PROTO_SIMPLE], resources->hostMem, resources->remHostMem };
    NCCLCHECK(ncclProxyCallBlocking(comm, &send->proxyConn, ncclProxyMsgConnect, &proxyInfo, sizeof(struct shmProxyInfo), &proxyInfo, sizeof(struct shmProxyInfo)));
    send->conn.buffs[NCCL_PROTO_SIMPLE] = proxyInfo.devFifo;
    send->conn.tail = &proxyInfo.ceRecvMem->tail;
    send->conn.sizesFifo = proxyInfo.ceRecvMem->sizesFifo;
  }
  return ncclSuccess;
}

static ncclResult_t tcclShmRecvConnect(struct ncclComm* comm, struct ncclConnect* connectInfo, int nranks, int rank, struct ncclConnector* recv) {
  // Setup device pointers
  struct shmRecvResources* resources = (struct shmRecvResources*)recv->transportResources;
  struct shmConnectInfo* info = (struct shmConnectInfo*)connectInfo;
  TRACE(NCCL_TCCL, "tcclShmRecvConnect shmName %s shmSize %d numaShmName %s numaShmSize %d", info->shmName, info->shmSize, info->numaShmName, info->numaShmSize);

  char shmPath[PATH_MAX];
  sprintf(shmPath, "/dev/shm/nccl-%s", info->shmName);
  resources->remShmSize = info->shmSize;
  TRACE(NCCL_SHM,"Open shmName %s shmSize %d", shmPath, info->shmSize);
  NCCLCHECK(ncclShmOpen(shmPath, resources->remShmSize, (void**)&resources->remHostMem, (void**)&resources->devRemHostMem, -1, &resources->remHandle));

  // NUMA is opened from the send side; need to ncclShmOpen separately
  char numaShmPath[PATH_MAX];
  sprintf(numaShmPath, "/dev/shm/nccl-%s", info->numaShmName);
  resources->numaSize = info->numaShmSize;
  NCCLCHECK(ncclShmOpen(numaShmPath, resources->numaSize, (void**)&resources->numaMem, (void**)&resources->devNumaMem, -1, &resources->numaHandle));

  char* buff = (char*)(resources->devNumaMem);
  for (int p=0; p<NCCL_NUM_PROTOCOLS; p++) {
    recv->conn.buffs[p] = buff;
    buff += comm->buffSizes[p];
  }
  recv->conn.head = &resources->devRemHostMem->head;
  recv->conn.tail = &resources->devHostMem->tail;

  if (resources->useMemcpyRecv) {
    NCCLCHECK(ncclProxyConnect(comm, TRANSPORT_TCCL_SHM, 0, comm->rank, &recv->proxyConn));
    struct shmProxyInfo proxyInfo = { NULL, NULL, recv->conn.buffs[NCCL_PROTO_SIMPLE], resources->remHostMem, resources->hostMem };
    NCCLCHECK(ncclProxyCallBlocking(comm, &recv->proxyConn, ncclProxyMsgConnect, &proxyInfo, sizeof(struct shmProxyInfo), &proxyInfo, sizeof(struct shmProxyInfo)));
    recv->conn.buffs[NCCL_PROTO_SIMPLE] = proxyInfo.devFifo;
    recv->conn.tail = &proxyInfo.ceRecvMem->tail;
  }
  return ncclSuccess;
}

static ncclResult_t tcclShmSendFree(struct ncclConnector* send) {
  struct shmRecvResources* resources = (struct shmRecvResources*)send->transportResources;
  if (resources) {
    NCCLCHECK(ncclShmClose(resources->hostHandle));
    NCCLCHECK(ncclShmClose(resources->remHandle));
    NCCLCHECK(ncclShmClose(resources->numaHandle));
    free(resources);
  }
  return ncclSuccess;
}

static ncclResult_t tcclShmRecvFree(struct ncclConnector* recv) {
  struct shmRecvResources* resources = (struct shmRecvResources*)recv->transportResources;
  if (resources) {
    NCCLCHECK(ncclShmClose(resources->hostHandle));
    NCCLCHECK(ncclShmClose(resources->remHandle));
    NCCLCHECK(ncclShmClose(resources->numaHandle));
    free(resources);
  }
  return ncclSuccess;
}

static ncclResult_t tcclShmSendProxyConnect(struct ncclProxyConnection* connection, struct ncclProxyState* proxyState, void* reqBuff, int reqSize, void* respBuff, int respSize, int* done) {
  if (proxyState->cudaCtx != NULL) {
    CUPFN(cuCtxSetCurrent(proxyState->cudaCtx));
  }

  struct shmProxyInfo* proxyInfo;
  NCCLCHECK(ncclCalloc(&proxyInfo, 1));
  if (reqSize != sizeof(struct shmProxyInfo)) return ncclInternalError;
  memcpy(proxyInfo, reqBuff, reqSize);
  NCCLCHECK(ncclCudaCalloc(&proxyInfo->devFifo, proxyState->buffSizes[NCCL_PROTO_SIMPLE]));
  NCCLCHECK(ncclCudaHostCalloc(&proxyInfo->ceRecvMem, 1));
  CUDACHECK(cudaStreamCreateWithFlags(&proxyInfo->stream, cudaStreamNonBlocking));
  for (int i=0; i<NCCL_STEPS; i++) {
    CUDACHECK(cudaEventCreate(proxyInfo->events+i));
  }
  connection->proxyAppendPtr = &connection->proxyAppend;
  connection->transportResources = proxyInfo;
  if (respSize != sizeof(struct shmProxyInfo)) return ncclInternalError;
  memcpy(respBuff, proxyInfo, respSize);
  return ncclSuccess;
}

static ncclResult_t tcclShmRecvProxyConnect(struct ncclProxyConnection* connection, struct ncclProxyState* proxyState, void* reqBuff, int reqSize, void* respBuff, int respSize, int* done) {
  if (proxyState->cudaCtx != NULL) {
    CUPFN(cuCtxSetCurrent(proxyState->cudaCtx));
  }

  struct shmProxyInfo* proxyInfo;
  NCCLCHECK(ncclCalloc(&proxyInfo, 1));
  if (reqSize != sizeof(struct shmProxyInfo)) return ncclInternalError;
  memcpy(proxyInfo, reqBuff, reqSize);
  NCCLCHECK(ncclCudaCalloc(&proxyInfo->devFifo, proxyState->buffSizes[NCCL_PROTO_SIMPLE]));
  NCCLCHECK(ncclCudaHostCalloc(&proxyInfo->ceRecvMem, 1));
  CUDACHECK(cudaStreamCreateWithFlags(&proxyInfo->stream, cudaStreamNonBlocking));
  for (int i=0; i<NCCL_STEPS; i++) {
    CUDACHECK(cudaEventCreate(proxyInfo->events+i));
  }
  connection->proxyAppendPtr = &connection->proxyAppend;
  connection->transportResources = proxyInfo;
  if (respSize != sizeof(struct shmProxyInfo)) return ncclInternalError;
  memcpy(respBuff, proxyInfo, respSize);
  return ncclSuccess;
}

static ncclResult_t tcclShmSendProxyFree(struct ncclProxyConnection* connection, struct ncclProxyState* proxyState) {
  struct shmProxyInfo* resources = (struct shmProxyInfo*)connection->transportResources;

  if (resources) {
    CUDACHECK(cudaStreamDestroy(resources->stream));
    NCCLCHECK(ncclCudaFree(resources->devFifo));
    NCCLCHECK(ncclCudaHostFree(resources->ceRecvMem));
    for (int i=0; i<NCCL_STEPS; i++) {
      CUDACHECK(cudaEventDestroy(resources->events[i]));
    }
    free(connection->transportResources);
  }
  return ncclSuccess;
}

static ncclResult_t tcclShmRecvProxyFree(struct ncclProxyConnection* connection, struct ncclProxyState* proxyState) {
  struct shmProxyInfo* resources = (struct shmProxyInfo*)connection->transportResources;

  if (resources) {
    CUDACHECK(cudaStreamDestroy(resources->stream));
    NCCLCHECK(ncclCudaFree(resources->devFifo));
    NCCLCHECK(ncclCudaHostFree(resources->ceRecvMem));
    for (int i=0; i<NCCL_STEPS; i++) {
      CUDACHECK(cudaEventDestroy(resources->events[i]));
    }
    free(connection->transportResources);
  }
  return ncclSuccess;
}

static ncclResult_t tcclShmSendProxyProgress(struct ncclProxyState* proxyState, struct ncclProxyArgs* args) {
  //static int warn_once = 0;
  //if (proxyState->tpRank == 1) {
  //  INFO(NCCL_TCCL, "SendProxyProgress called");
  //}
  if (args->state == ncclProxyOpReady) {
    for (int s=0; s<args->nsubs; s++) {
      struct ncclProxySubArgs* sub = args->subs+s;
      struct shmProxyInfo* resources = (struct shmProxyInfo*) (sub->connection->transportResources);
      // Round to next multiple of sliceSteps
      sub->base = ROUNDUP(resources->step, args->chunkSteps);
      sub->posted = sub->transmitted = sub->done = 0;
    }
    args->state = ncclProxyOpProgress;
  }
  args->idle = 1;
  if (args->state == ncclProxyOpProgress) {
    int p = args->protocol;
    int stepSize = proxyState->buffSizes[p] / NCCL_STEPS;
    for (int s=0; s<args->nsubs; s++) {
      struct ncclProxySubArgs* sub = args->subs+s;
      if (proxyState->tpRank == 1) {
        //INFO(NCCL_TCCL, "SendProxyProgress: sub %d trans %d done %d diff %d", s, sub->transmitted, sub->done, sub->transmitted-sub->done);
      }
      struct shmProxyInfo* resources = (struct shmProxyInfo*) (sub->connection->transportResources);
      if (p != NCCL_PROTO_SIMPLE) { // Only Simple uses cudaMemcpy
          resources->step = sub->base + sub->nsteps;
          args->done++;
          continue;
      }
      if (sub->transmitted < sub->done + NCCL_STEPS && sub->transmitted < sub->nsteps) {
        int buffSlot = (sub->base+sub->transmitted)%NCCL_STEPS;
        volatile int* sizesFifo = resources->ceRecvMem->sizesFifo;
        volatile uint64_t* recvTail = &resources->ceRecvMem->tail;
        //if (*recvTail >= sub->base + sub->transmitted + NCCL_STEPS && !warn_once) {
        //  INFO(NCCL_TCCL, "TCCL_SHM send GPU buffer full!!!");
        //  warn_once = 1;
        //}
        // Check GPU has sent everything
        if ((*recvTail > sub->base+sub->transmitted)) {
          int size = sizesFifo[buffSlot];
          //INFO(NCCL_TCCL, "SendProxyProgress: cudaMemcpyAsync size %d", size);
          CUDACHECK(cudaMemcpyAsync(resources->shmFifo+buffSlot*stepSize, resources->devFifo+buffSlot*stepSize, size, cudaMemcpyDeviceToHost, resources->stream));
          CUDACHECK(cudaEventRecord(resources->events[buffSlot], resources->stream));
          resources->recvMem->sizesFifo[buffSlot] = size;
          __sync_synchronize(); // make sure sizesFifo is visible
          sub->transmitted += args->sliceSteps;
        }
      }
      if (sub->done < sub->transmitted){
        //if (sub->transmitted >= sub->done + NCCL_STEPS && !warn_once) {
        //  INFO(NCCL_TCCL, "TCCL_SHM recv CPU buffer full!!!");
        //  warn_once = 1;
        //}
        int buffSlot = (sub->base+sub->done)%NCCL_STEPS;
        cudaError_t res = cudaEventQuery(resources->events[buffSlot]);
        if (res != cudaErrorNotReady) CUDACHECK(res);
        if (res == cudaSuccess) {
          sub->done += args->sliceSteps;
          // Notify SHM, GPU at the same time (send->conn.tail == resources->devRemHostMem->tail == recvMem->tail)
          resources->recvMem->tail = sub->base + sub->done;
          __sync_synchronize(); // make sure sizesFifo is visible
        }
        if (sub->done == sub->nsteps) {
          resources->step = sub->base + sub->nsteps;
          args->done++;
        }
      }
    }
    if (args->done == args->nsubs) {
      args->state = ncclProxyOpNone;
    }
  }
  return ncclSuccess;
}

static ncclResult_t tcclShmRecvProxyProgress(struct ncclProxyState* proxyState, struct ncclProxyArgs* args) {
  //static int warn_once = 0;
  //if (proxyState->tpRank == 1) {
  //  INFO(NCCL_TCCL, "RecvProxyProgress called");
  //}
  if (args->state == ncclProxyOpReady) {
    for (int s=0; s<args->nsubs; s++) {
      struct ncclProxySubArgs* sub = args->subs+s;
      struct shmProxyInfo* resources = (struct shmProxyInfo*) (sub->connection->transportResources);
      // Round to next multiple of sliceSteps
      sub->base = ROUNDUP(resources->step, args->chunkSteps);
      sub->posted = sub->transmitted = sub->done = 0;
    }
    args->state = ncclProxyOpProgress;
  }
  args->idle = 1;
  if (args->state == ncclProxyOpProgress) {
    int p = args->protocol;
    int stepSize = proxyState->buffSizes[p] / NCCL_STEPS;
    for (int s=0; s<args->nsubs; s++) {
      struct ncclProxySubArgs* sub = args->subs+s;
      struct shmProxyInfo* resources = (struct shmProxyInfo*) (sub->connection->transportResources);
      if (p != NCCL_PROTO_SIMPLE) { // Only Simple uses cudaMemcpy
          resources->step = sub->base + sub->nsteps;
          args->done++;
          continue;
      }
      if (sub->transmitted < sub->done + NCCL_STEPS && sub->transmitted < sub->nsteps) {
        int buffSlot = (sub->base+sub->transmitted)%NCCL_STEPS;
        volatile int* sizesFifo = resources->recvMem->sizesFifo;
        volatile uint64_t* recvTail = &resources->recvMem->tail;
        //if (*recvTail >= sub->base + sub->transmitted + NCCL_STEPS && !warn_once) {
        //  INFO(NCCL_TCCL, "TCCL_SHM recv CPU buffer full!!!");
        //  warn_once = 1;
        //}
        // Check data is ready in SHM
        if ((*recvTail > sub->base+sub->transmitted)) {
          int size = sizesFifo[buffSlot];
          CUDACHECK(cudaMemcpyAsync(resources->devFifo+buffSlot*stepSize, resources->shmFifo+buffSlot*stepSize, size, cudaMemcpyHostToDevice, resources->stream));
          CUDACHECK(cudaEventRecord(resources->events[buffSlot], resources->stream));
          sub->transmitted += args->sliceSteps;
        }
      }
      if (sub->done < sub->transmitted) {
        //if (sub->transmitted >= sub->done + NCCL_STEPS && !warn_once) {
        //  INFO(NCCL_TCCL, "TCCL_SHM recv GPU buffer full!!!");
        //  warn_once = 1;
        //}
        int buffSlot = (sub->base+sub->done)%NCCL_STEPS;
        cudaError_t res = cudaEventQuery(resources->events[buffSlot]);
        if (res != cudaErrorNotReady) CUDACHECK(res);
        if (res == cudaSuccess) {
          sub->done += args->sliceSteps;
          // Notify GPU
          resources->ceRecvMem->tail = sub->base + sub->done;
          __sync_synchronize(); // make sure sizesFifo is visible
        }
        if (sub->done == sub->nsteps) {
          resources->step = sub->base + sub->nsteps;
          args->done++;
        }
      }
    }
    if (args->done == args->nsubs) {
      args->state = ncclProxyOpNone;
    }
  }
  return ncclSuccess;
}

struct ncclTransport tcclShmTransport = {
  "TCCL_SHM",
  tcclShmCanConnect,
  { tcclShmSendSetup, tcclShmSendConnect, tcclShmSendFree, NULL, NULL, tcclShmSendProxyConnect, tcclShmSendProxyFree, tcclShmSendProxyProgress },
  { tcclShmRecvSetup, tcclShmRecvConnect, tcclShmRecvFree, NULL, NULL, tcclShmRecvProxyConnect, tcclShmRecvProxyFree, tcclShmRecvProxyProgress }
};