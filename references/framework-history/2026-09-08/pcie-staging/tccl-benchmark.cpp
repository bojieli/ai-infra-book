#include "benchmark_v2.hpp"

#include <cstdio>
#include <vector>
#include <string>
#include <set>
#include <map>
#include <queue>
#include <mpi.h>
#include <cuda_runtime.h>
#include <numa.h>
#include <numaif.h>
#include <tinyxml2.h>
#include "conf_v2.hpp"
#include "kernels_v2.hpp"
#include "util.hpp"
#include "check.hpp"
#include "ibv_helper.hpp"

enum struct NodeType : int {
  NODE_MAIN,
  NODE_SUB0,
  NODE_SUB1,
  NUM_NODE_TYPE
};

enum struct CommandType : int {
  COMMAND_BENCHMARK,
  COMMAND_EXIT
};

Transfer::DeviceType GetType(Transfer& t, bool src) {
  if (src) {
    switch (t.type) {
      case Transfer::TransferType::GPU_READ_CPUMEM_KERNEL:
      case Transfer::TransferType::GPU_READ_CPUMEM_MEMCPY:
      case Transfer::TransferType::CPU_GPU_INTER:
      case Transfer::TransferType::CPU_CPU_INTER:
        return Transfer::DeviceType::CPUMEM;
      case Transfer::TransferType::GPU_WRITE_CPUMEM_KERNEL:
      case Transfer::TransferType::GPU_READ_GPUMEM_KERNEL:
      case Transfer::TransferType::GPU_WRITE_GPUMEM_KERNEL:
      case Transfer::TransferType::GPU_WRITE_CPUMEM_MEMCPY:
      case Transfer::TransferType::GPU_READ_GPUMEM_MEMCPY:
      case Transfer::TransferType::GPU_WRITE_GPUMEM_MEMCPY:
      case Transfer::TransferType::GPU_GPU_INTER:
      case Transfer::TransferType::GPU_CPU_INTER:
        return Transfer::DeviceType::GPU;
      default:
        assert(false);
    }
  } else { // dst
    switch (t.type) {
      case Transfer::TransferType::GPU_WRITE_CPUMEM_KERNEL:
      case Transfer::TransferType::GPU_WRITE_CPUMEM_MEMCPY:
      case Transfer::TransferType::CPU_CPU_INTER:
      case Transfer::TransferType::GPU_CPU_INTER:
        return Transfer::DeviceType::CPUMEM;
      case Transfer::TransferType::GPU_READ_CPUMEM_KERNEL:
      case Transfer::TransferType::GPU_READ_CPUMEM_MEMCPY:
      case Transfer::TransferType::GPU_READ_GPUMEM_KERNEL:
      case Transfer::TransferType::GPU_WRITE_GPUMEM_KERNEL:
      case Transfer::TransferType::GPU_READ_GPUMEM_MEMCPY:
      case Transfer::TransferType::GPU_WRITE_GPUMEM_MEMCPY:
      case Transfer::TransferType::GPU_GPU_INTER:
      case Transfer::TransferType::CPU_GPU_INTER:
        return Transfer::DeviceType::GPU;
      default:
        assert(false);
    }
  }
}


std::string Transfer::ToString() {
  std::string ans;
  ans = TransferTypeToString(type);
  ans += fmt::format(" src_node={} dst_node={} src_idx={} dst_idx={} nbytes={}", src_node, dst_node, src_idx, dst_idx, nbytes);
  return ans;
}

int Transfer::GetGPUIdxKernelLaunchedOn() const {
  if (type == TransferType::GPU_READ_CPUMEM_KERNEL ||
      type == TransferType::GPU_READ_GPUMEM_KERNEL ||
      type == TransferType::GPU_READ_CPUMEM_MEMCPY ||
      type == TransferType::GPU_READ_GPUMEM_MEMCPY) {
    return dst_idx;
  }
  if (type == TransferType::GPU_WRITE_CPUMEM_KERNEL ||
      type == TransferType::GPU_WRITE_GPUMEM_KERNEL ||
      type == TransferType::GPU_WRITE_CPUMEM_MEMCPY ||
      type == TransferType::GPU_WRITE_GPUMEM_MEMCPY) {
    return src_idx;
  }
  return -1;
}

bool Transfer::IsRead() const {
  if (type == TransferType::GPU_READ_CPUMEM_KERNEL ||
      type == TransferType::GPU_READ_GPUMEM_KERNEL ||
      type == TransferType::GPU_READ_CPUMEM_MEMCPY ||
      type == TransferType::GPU_READ_GPUMEM_MEMCPY) {
    return true;
  }
  if (type == TransferType::GPU_WRITE_CPUMEM_KERNEL ||
      type == TransferType::GPU_WRITE_GPUMEM_KERNEL ||
      type == TransferType::GPU_WRITE_CPUMEM_MEMCPY ||
      type == TransferType::GPU_WRITE_GPUMEM_MEMCPY) {
    return false;
  }
  assert(false);
}

bool Transfer::IsWrite() const {
  if (type == TransferType::GPU_READ_CPUMEM_KERNEL ||
      type == TransferType::GPU_READ_GPUMEM_KERNEL ||
      type == TransferType::GPU_READ_CPUMEM_MEMCPY ||
      type == TransferType::GPU_READ_GPUMEM_MEMCPY) {
    return false;
  }
  if (type == TransferType::GPU_WRITE_CPUMEM_KERNEL ||
      type == TransferType::GPU_WRITE_GPUMEM_KERNEL ||
      type == TransferType::GPU_WRITE_CPUMEM_MEMCPY ||
      type == TransferType::GPU_WRITE_GPUMEM_MEMCPY) {
    return true;
  }
  assert(false);
}

bool Transfer::IsMemcpy() const {
  if (type == TransferType::GPU_READ_CPUMEM_KERNEL ||
      type == TransferType::GPU_READ_GPUMEM_KERNEL ||
      type == TransferType::GPU_WRITE_CPUMEM_KERNEL ||
      type == TransferType::GPU_WRITE_GPUMEM_KERNEL) {
    return false;
  }
  if (type == TransferType::GPU_READ_CPUMEM_MEMCPY ||
      type == TransferType::GPU_READ_GPUMEM_MEMCPY ||
      type == TransferType::GPU_WRITE_CPUMEM_MEMCPY ||
      type == TransferType::GPU_WRITE_GPUMEM_MEMCPY) {
    return true;
  }
  assert(false);
}

bool Transfer::IsInter() const {
  if (type == TransferType::GPU_GPU_INTER ||
      type == TransferType::GPU_CPU_INTER ||
      type == TransferType::CPU_GPU_INTER ||
      type == TransferType::CPU_CPU_INTER) {
    return true;
  }
  return false;
}

bool Transfer::operator<(const Transfer &that) const {
  if (type != that.type) return type < that.type;
  if (src_node != that.src_node) return src_node < that.src_node;
  if (dst_node != that.dst_node) return dst_node < that.dst_node;
  if (src_idx != that.src_idx) return src_idx < that.src_idx;
  if (dst_idx != that.dst_idx) return dst_idx < that.dst_idx;
  if (nbytes != that.nbytes) return nbytes < that.nbytes;
  return false;
}

std::string Transfer::TransferTypeToString(Transfer::TransferType type) {
  std::string ans;
  switch (type) {
    case TransferType::GPU_READ_CPUMEM_KERNEL:
      ans = "GPU_READ_CPUMEM_KERNEL";
      break;
    case TransferType::GPU_WRITE_CPUMEM_KERNEL:
      ans = "GPU_WRITE_CPUMEM_KERNEL";
      break;
    case TransferType::GPU_READ_GPUMEM_KERNEL:
      ans = "GPU_READ_GPUMEM_KERNEL";
      break;
    case TransferType::GPU_WRITE_GPUMEM_KERNEL:
      ans = "GPU_WRITE_GPUMEM_KERNEL";
      break;
    case TransferType::GPU_READ_CPUMEM_MEMCPY:
      ans = "GPU_READ_CPUMEM_MEMCPY";
      break;
    case TransferType::GPU_WRITE_CPUMEM_MEMCPY:
      ans = "GPU_WRITE_CPUMEM_MEMCPY";
      break;
    case TransferType::GPU_READ_GPUMEM_MEMCPY:
      ans = "GPU_READ_GPUMEM_MEMCPY";
      break;
    case TransferType::GPU_WRITE_GPUMEM_MEMCPY:
      ans = "GPU_WRITE_GPUMEM_MEMCPY";
      break;
    case TransferType::GPU_GPU_INTER:
      ans = "GPU_GPU_INTER";
      break;
    case TransferType::GPU_CPU_INTER:
      ans = "GPU_CPU_INTER";
      break;
    case TransferType::CPU_GPU_INTER:
      ans = "CPU_GPU_INTER";
      break;
    case TransferType::CPU_CPU_INTER:
      ans = "CPU_CPU_INTER";
      break;
    default:
      assert(false);
  }
  return ans;
}

Transfer::TransferType Transfer::TransferTypeFromString(std::string str) {
  if (str == "GPU_READ_CPUMEM_KERNEL") return TransferType::GPU_READ_CPUMEM_KERNEL;
  if (str == "GPU_WRITE_CPUMEM_KERNEL") return TransferType::GPU_WRITE_CPUMEM_KERNEL;
  if (str == "GPU_READ_GPUMEM_KERNEL") return TransferType::GPU_READ_GPUMEM_KERNEL;
  if (str == "GPU_WRITE_GPUMEM_KERNEL") return TransferType::GPU_WRITE_GPUMEM_KERNEL;
  if (str == "GPU_READ_CPUMEM_MEMCPY") return TransferType::GPU_READ_CPUMEM_MEMCPY;
  if (str == "GPU_WRITE_CPUMEM_MEMCPY") return TransferType::GPU_WRITE_CPUMEM_MEMCPY;
  if (str == "GPU_READ_GPUMEM_MEMCPY") return TransferType::GPU_READ_GPUMEM_MEMCPY;
  if (str == "GPU_WRITE_GPUMEM_MEMCPY") return TransferType::GPU_WRITE_GPUMEM_MEMCPY;
  if (str == "GPU_GPU_INTER") return TransferType::GPU_GPU_INTER;
  if (str == "GPU_CPU_INTER") return TransferType::GPU_CPU_INTER;
  if (str == "CPU_GPU_INTER") return TransferType::CPU_GPU_INTER;
  if (str == "CPU_CPU_INTER") return TransferType::CPU_CPU_INTER;
  assert(false);
  return TransferType::DUMMY;
}

std::string Transfer::SerToString() const {
  tinyxml2::XMLPrinter printer;
  printer.OpenElement("transfer");
  printer.PushAttribute("type", TransferTypeToString(type).c_str());
  printer.PushAttribute("src_node", src_node);
  printer.PushAttribute("dst_node", dst_node);
  printer.PushAttribute("src_idx", src_idx);
  printer.PushAttribute("dst_idx", dst_idx);
  printer.PushAttribute("nbytes", nbytes);
  return printer.CStr();
}

Transfer Transfer::DesFromString(std::string str) {
  tinyxml2::XMLDocument doc;
  doc.Parse(str.c_str());
  auto elem = doc.FirstChildElement("transfer");
  return Transfer::DesFromXmlElem(elem);
}

Transfer Transfer::DesFromXmlElem(tinyxml2::XMLElement *elem) {
  if (!elem) {
    LOG_RANK_0("ERROR: Failed to parse xml");
    assert(false);
  }
  Transfer transfer = {
    .type = TransferTypeFromString(elem->Attribute("type")),
    .src_node = elem->IntAttribute("src_node"),
    .dst_node = elem->IntAttribute("dst_node"),
    .src_idx = elem->IntAttribute("src_idx"),
    .dst_idx = elem->IntAttribute("dst_idx"),
    .nbytes = (size_t)elem->IntAttribute("nbytes")
  };
  return transfer;
}

int Transfer::Encode() const {
  // 4 bit for Transfer Type (less than 16 types)
  // 2 bit for src_node
  // 2 bit for dst_node
  // conf.num_bits_idx bit for src_idx
  // conf.num_bits_idx bit for dst_idx
  int encoded = 0, ofs = 0;
  encoded |= ((int)type << ofs);
  ofs += 4;
  encoded |= (src_node << ofs);
  ofs += 2;
  encoded |= (dst_node << ofs);
  ofs += 2;
  encoded |= (src_idx << ofs);
  ofs += conf.num_bits_idx;
  encoded |= (dst_idx << ofs);
  ofs += conf.num_bits_idx;
  return encoded;
}

Transfer Transfer::Decode(int encoded) {
  int ofs = 0;
  ofs = 4;
  int type = encoded & ((1 << ofs) - 1);
  encoded >>= ofs;
  ofs = 2;
  int src_node = encoded & ((1 << ofs) - 1);
  encoded >>= ofs;
  ofs = 2;
  int dst_node = encoded & ((1 << ofs) - 1);
  encoded >>= ofs;
  ofs = conf.num_bits_idx;
  int src_idx = encoded & ((1 << ofs) - 1);
  encoded >>= ofs;
  ofs = conf.num_bits_idx;
  int dst_idx = encoded & ((1 << ofs) - 1);
  encoded >>= ofs;
  return Transfer {
    .type = (Transfer::TransferType)type,
    .src_node = src_node,
    .dst_node = dst_node,
    .src_idx = src_idx,
    .dst_idx = dst_idx,
    .nbytes = conf.nbytes
  };
}

Transfer Transfer::DecodeInter(int encoded, int src_node, int dst_node) {
  Transfer::TransferType type;
  switch (encoded & 0x3) {
    case 0:
      type = Transfer::TransferType::GPU_GPU_INTER;
      break;
    case 1:
      type = Transfer::TransferType::GPU_CPU_INTER;
      break;
    case 2:
      type = Transfer::TransferType::CPU_GPU_INTER;
      break;
    case 3:
      type = Transfer::TransferType::CPU_CPU_INTER;
      break;
    default:
      assert(false);
  }
  encoded >>= 2;
  int src_idx = encoded & ((1 << conf.num_bits_idx) - 1);
  encoded >>= conf.num_bits_idx;
  int dst_idx = encoded & ((1 << conf.num_bits_idx) - 1);
  encoded >>= conf.num_bits_idx;
  return Transfer{
    .type = type,
    .src_node = src_node,
    .dst_node = dst_node,
    .src_idx = src_idx,
    .dst_idx = dst_idx,
    .nbytes = conf.nbytes
  };
}

std::vector<Transfer> DeserializeTransfers(std::string str) {
  tinyxml2::XMLDocument doc;
  doc.Parse(str.c_str());
  auto elem = doc.FirstChildElement("transfer");
  std::vector<Transfer> transfers;
  while (elem) {
    transfers.push_back(Transfer::DesFromXmlElem(elem));
    elem = elem->NextSiblingElement("transfer");
  }
  return transfers;
}

struct SearchState {
  std::vector<Transfer> transfers;
  double bw;

  bool operator<(const SearchState &that) const {
    return bw < that.bw;
  }

  bool operator>(const SearchState &that) const {
    return bw > that.bw;
  }
};

void BenchmarkResult::FillStat() {
  std::vector<size_t> real_db(us_db.begin() + conf.warmup_iters, us_db.end());
  std::sort(real_db.begin(), real_db.end());
  us_med = real_db[real_db.size() / 2];

  size_t us_sum = 0;
  for (int i = 0; i < (int)real_db.size(); ++i) {
    us_sum += real_db[i];
  }
  us_avg = us_sum / (double)real_db.size();
}

void ValidateLaunchConf() {
  // Needs 3 nodes to cover all patterns
  // Node 1 needs NUM_GPU * 2 + 2 ranks
  // worst case: NIC -> CPU -> GPU -> ... -> GPU -> CPU -> NIC (every transfer hits cpumem)
  // Node 2 needs 2 ranks for 2-node ring exception
  // Node 3 needs 1 rank
  char hostname[MPI_MAX_PROCESSOR_NAME];
  int len;
  MPI_Get_processor_name(hostname, &len);

  int rank, size;
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &size);

  char hostnamebuf[size][MPI_MAX_PROCESSOR_NAME];
  MPI_Allgather(hostname, MPI_MAX_PROCESSOR_NAME, MPI_CHAR, hostnamebuf, MPI_MAX_PROCESSOR_NAME, MPI_CHAR, MPI_COMM_WORLD);

  std::vector<std::string> hostnames;
  for (int i = 0; i < size; ++i) {
    hostnames.push_back(hostnamebuf[i]);
  }

  std::map<std::string, int> hostname_to_node;
  int node_to_assign = 0;
  for (int i = 0; i < size; ++i) {
    if (hostname_to_node.find(hostnames[i]) == hostname_to_node.end()) {
      hostname_to_node[hostnames[i]] = node_to_assign;
      ++node_to_assign;
    }
  }
  
  for (int i = 0; i < size; ++i) {
    conf.node_idx.push_back(hostname_to_node[hostnames[i]]);
    LOG_RANK_0("Rank {} is on node {} (node idx {})", i, hostnames[i], conf.node_idx[i]);
  }

  //std::set<std::string> unique_hostnames;
  //for (int i = 0; i < size; ++i) {
  //  unique_hostnames.insert(hostnames[i]);
  //}

  //if (unique_hostnames.size() != static_cast<int>(NodeType::NUM_NODE_TYPE)) {
  //  LOG_RANK_0("ERROR: Need {} nodes, but only {} nodes are available", static_cast<int>(NodeType::NUM_NODE_TYPE), unique_hostnames.size());
  //  MPI_Abort(MPI_COMM_WORLD, 1);
  //}

  //for (const auto& hostname : unique_hostnames) {
  //  LOG_RANK_0("{}", hostname);
  //}
}

void ValidateCuda() {
  int num_gpus, min_num_gpus;
  CHECK_CUDA(cudaGetDeviceCount(&num_gpus));
  conf.num_gpus = num_gpus;
  MPI_Allreduce(&num_gpus, &min_num_gpus, 1, MPI_INT, MPI_MIN, MPI_COMM_WORLD);
  if (num_gpus != min_num_gpus) {
    LOG_RANK_ANY("ERROR: All nodes must have the same number of GPUs ({} != {})", num_gpus, min_num_gpus);
    MPI_Abort(MPI_COMM_WORLD, 1);
  }

  int p2p_available = 1;
  for (int i = 0; i < num_gpus; ++i) {
    for (int j = 0; j < num_gpus; ++j) {
      if (i != j) {
        int can_access;
        CHECK_CUDA(cudaDeviceCanAccessPeer(&can_access, i, j));
        if (can_access == 0) p2p_available = 0;
      }
    }
  }

  MPI_Allreduce(MPI_IN_PLACE, &p2p_available, 1, MPI_INT, MPI_MIN, MPI_COMM_WORLD);
  if (p2p_available == 1) {
    conf.p2p_available = 1;
    for (int i = 0; i < num_gpus; ++i) {
      for (int j = 0; j < num_gpus; ++j) {
        if (i != j) {
          CHECK_CUDA(cudaSetDevice(i));
          CHECK_CUDA(cudaDeviceEnablePeerAccess(j, 0));
        }
      }
    }
  } else {
    conf.p2p_available = 0;
  }
  LOG_RANK_0("P2P available: {}", conf.p2p_available);
}

void ValidateNuma() {
  int num_numa = numa_max_node() + 1, min_num_numa;
  MPI_Allreduce(&num_numa, &min_num_numa, 1, MPI_INT, MPI_MIN, MPI_COMM_WORLD);
  if (num_numa != min_num_numa) {
    LOG_RANK_ANY("ERROR: All nodes must have the same number of NUMA nodes ({} != {})", num_numa, min_num_numa);
    MPI_Abort(MPI_COMM_WORLD, 1);
  }
  conf.num_numa = num_numa;

  LOG_RANK_0("NUMA node available: {}", num_numa);
  for (int i = 0; i < num_numa; ++i) {
    long long mem_size = numa_node_size64(i, nullptr);
    //long long min_mem_size;
    //MPI_Allreduce(&mem_size, &min_mem_size, 1, MPI_LONG_LONG, MPI_MIN, MPI_COMM_WORLD);
    //if (mem_size != min_mem_size) {
    //  LOG_RANK_ANY("ERROR: All NUMA nodes must have the same amount of memory ({} != {})", mem_size, min_mem_size);
    //  MPI_Abort(MPI_COMM_WORLD, 1);
    //}

    conf.numa_available.push_back(i);
    LOG_RANK_ANY("NUMA node {} available: {} bytes", i, mem_size);
  }
}

std::vector<int> RemoveElem(const std::vector<int>& vec, int elem) {
  std::vector<int> ans;
  for (int i : vec) {
    if (i != elem) {
      ans.push_back(i);
    }
  }
  return ans;
}

static void collect_stat(BenchmarkResult& res, int iter, size_t us, size_t us_local, double expected, double actual) {
  int rank, size;
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &size);
  size_t us_locals[size];
  MPI_Gather(&us_local, 1, MPI_UNSIGNED_LONG, us_locals, 1, MPI_UNSIGNED_LONG, 0, MPI_COMM_WORLD);

  if (rank == 0) {
    res.us_db.push_back(us);
    if (iter == 0) {
      res.us_local_db.resize(size);
    }
    for (int i = 0; i < size; ++i) {
      DEBUG_RANK_0("rank {} us_local {}", i, us_locals[i]);
      res.us_local_db[i].push_back(us_locals[i]);
    }
  }
}

void AllocGPUMem(void** ptr, size_t nbytes, int gpu_idx) {
  int org_idx;
  CHECK_CUDA(cudaGetDevice(&org_idx));
  CHECK_CUDA(cudaSetDevice(gpu_idx));
  CHECK_CUDA(cudaMalloc(ptr, nbytes));
  CHECK_CUDA(cudaSetDevice(org_idx));
}

void FreeGPUMem(void* ptr) {
  CHECK_CUDA(cudaFree(ptr));
}

void AllocCPUMem(void** ptr, size_t nbytes, int numa_idx) {
  // allocate with interleaved policy on NUMA node 0 and 1
  *ptr = numa_alloc_onnode(nbytes, numa_idx);
  CHECK_CUDA(cudaHostRegister(*ptr, nbytes, cudaHostRegisterMapped));
}

void FreeCPUMem(void* ptr, size_t nbytes) {
  CHECK_CUDA(cudaHostUnregister(ptr));
  numa_free(ptr, nbytes);
}

void AllocCPUMemAccessibleFromGPU(void** dptr, void** hptr, size_t nbytes, int numa_idx) {
  *hptr = (float*)numa_alloc_onnode(nbytes, numa_idx);
  CHECK_CUDA(cudaHostRegister(*hptr, nbytes, cudaHostRegisterMapped));
  CHECK_CUDA(cudaHostGetDevicePointer(dptr, *hptr, 0));
}

void FreeCPUMemAccessibleFromGPU(void* hptr, size_t nbytes) {
  CHECK_CUDA(cudaHostUnregister(hptr));
  numa_free(hptr, nbytes);
}

BenchmarkResult RunInterJob(const std::vector<Transfer>& transfers, int peer_rank) {
  if (transfers.size() != 1) {
    LOG_RANK_ANY("ERROR: Inter-node transfer job must have only one transfer");
    MPI_Abort(MPI_COMM_WORLD, 1);
  }

  auto& transfer = transfers[0];

  if (transfer.src_node == conf.node_idx[conf.rank]) {
    // Sending process
    float* sbuf;
    if (transfer.type == Transfer::TransferType::CPU_CPU_INTER ||
        transfer.type == Transfer::TransferType::CPU_GPU_INTER) {
      AllocCPUMem((void**)&sbuf, transfer.nbytes, transfer.src_idx);
      //fill_random_float(sbuf, transfer.nbytes / sizeof(float));
    } else if (transfer.type == Transfer::TransferType::GPU_CPU_INTER ||
               transfer.type == Transfer::TransferType::GPU_GPU_INTER) {
      AllocGPUMem((void**)&sbuf, transfer.nbytes, transfer.src_idx);
      //fill_random_float_gpu(sbuf, transfer.nbytes / sizeof(float));
    } else {
      LOG_RANK_ANY("ERROR: Unknown transfer type");
      MPI_Abort(MPI_COMM_WORLD, 1);
    }

    ib_connection* conn = create_ib_connection(0, peer_rank);
    ib_memory* mem = create_ib_memory(conn, sbuf, transfer.nbytes);
    exchange_peer_memory_info(conn, mem, peer_rank);

    BenchmarkResult res;
    for (int it = 0; it < conf.niters; ++it) {
      CHECK_MPI(MPI_Barrier(MPI_COMM_WORLD));
      auto st = get_time();

      //ib_post_send(conn, mem, 0, transfer.nbytes);
      ib_post_rdma_write(conn, mem, 0, transfer.nbytes);
      ib_poll_cq(conn);

      auto et_local = get_time();
      CHECK_MPI(MPI_Barrier(MPI_COMM_WORLD));
      auto et = get_time();

      auto us = get_duration_us(st, et);
      auto us_local = get_duration_us(st, et_local);
      //LOG_RANK_ANY("us={} us_local={}", us, us_local);

      collect_stat(res, it, us, us_local, 0, 0);
      //std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    destroy_ib_memory(mem);
    destroy_ib_connection(conn);

    if (transfer.type == Transfer::TransferType::CPU_CPU_INTER ||
        transfer.type == Transfer::TransferType::CPU_GPU_INTER) {
      FreeCPUMem(sbuf, transfer.nbytes);
    } else if (transfer.type == Transfer::TransferType::GPU_CPU_INTER ||
               transfer.type == Transfer::TransferType::GPU_GPU_INTER) {
      FreeGPUMem(sbuf);
    }

    return res;
  } else {
    // Receiving process
    float* rbuf;
    if (transfer.type == Transfer::TransferType::CPU_CPU_INTER ||
        transfer.type == Transfer::TransferType::GPU_CPU_INTER) {
      AllocCPUMem((void**)&rbuf, transfer.nbytes, transfer.dst_idx);
      //fill_random_float(rbuf, transfer.nbytes / sizeof(float));
    } else if (transfer.type == Transfer::TransferType::CPU_GPU_INTER ||
               transfer.type == Transfer::TransferType::GPU_GPU_INTER) {
      AllocGPUMem((void**)&rbuf, transfer.nbytes, transfer.dst_idx);
      //fill_random_float_gpu(rbuf, transfer.nbytes / sizeof(float));
    } else {
      LOG_RANK_ANY("ERROR: Unknown transfer type");
      MPI_Abort(MPI_COMM_WORLD, 1);
    }

    ib_connection* conn = create_ib_connection(0, peer_rank);
    ib_memory* mem = create_ib_memory(conn, rbuf, transfer.nbytes);
    exchange_peer_memory_info(conn, mem, peer_rank);

    BenchmarkResult res;
    for (int it = 0; it < conf.niters; ++it) {
      // Recv should be posted before send
      //ib_post_recv(conn, mem, 0, transfer.nbytes);
      ib_post_recv_to_rdma_write(conn, mem, 0, transfer.nbytes);

      CHECK_MPI(MPI_Barrier(MPI_COMM_WORLD));
      auto st = get_time();

      ib_poll_cq(conn);

      auto et_local = get_time();
      CHECK_MPI(MPI_Barrier(MPI_COMM_WORLD));
      auto et = get_time();

      auto us = get_duration_us(st, et);
      auto us_local = get_duration_us(st, et_local);
      //LOG_RANK_ANY("us={} us_local={}", us, us_local);

      collect_stat(res, it, us, us_local, 0, 0);
      //std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    destroy_ib_memory(mem);
    destroy_ib_connection(conn);

    if (transfer.type == Transfer::TransferType::CPU_CPU_INTER ||
        transfer.type == Transfer::TransferType::GPU_CPU_INTER) {
      FreeCPUMem(rbuf, transfer.nbytes);
    } else if (transfer.type == Transfer::TransferType::CPU_GPU_INTER ||
               transfer.type == Transfer::TransferType::GPU_GPU_INTER) {
      FreeGPUMem(rbuf);
    }

    return res;
  }

}

BenchmarkResult RunGPUKernelJob(const std::vector<Transfer>& transfers) {
  // According to experiments, running write-only or read-only workloads on different thread blocks causes severe congestion
  // So we only consider:
  // 1. single transfer job
  // 2. two transfer jobs; one is read, the other is write
  assert(transfers.size() == 1 || transfers.size() == 2);

  Transfer read_transfer = transfers[0];
  Transfer write_transfer = transfers[0];
  bool read_transfer_exists = false;
  bool write_transfer_exists = false;

  if (transfers.size() > 0) {
    if (transfers[0].IsRead()) {
      read_transfer = transfers[0];
      read_transfer_exists = true;
    } else if (transfers[0].IsWrite()) {
      write_transfer = transfers[0];
      write_transfer_exists = true;
    } else {
      assert(false);
    }
  }

  if (transfers.size() > 1) {
    if (transfers[1].IsRead()) {
      assert(!read_transfer_exists);
      read_transfer = transfers[1];
      read_transfer_exists = true;
    } else if (transfers[1].IsWrite()) {
      assert(!write_transfer_exists);
      write_transfer = transfers[1];
      write_transfer_exists = true;
    } else {
      assert(false);
    }
  }
  
  int gpu_idx = read_transfer_exists ? read_transfer.GetGPUIdxKernelLaunchedOn() : write_transfer.GetGPUIdxKernelLaunchedOn();
  size_t nbytes = read_transfer_exists ? read_transfer.nbytes : write_transfer.nbytes;

  float *src;
  float *src_cpuptr;
  if (read_transfer_exists) {
    if (read_transfer.type == Transfer::TransferType::GPU_READ_CPUMEM_KERNEL) {
      DEBUG_RANK_ANY("read transfer is GPU_READ_CPUMEM_KERNEL src_idx={}", read_transfer.src_idx);
      AllocCPUMemAccessibleFromGPU((void**)&src, (void**)&src_cpuptr, read_transfer.nbytes, read_transfer.src_idx);
      //fill_random_float(src_cpuptr, read_transfer.nbytes / sizeof(float));
    } else if (read_transfer.type == Transfer::TransferType::GPU_READ_GPUMEM_KERNEL) {
      DEBUG_RANK_ANY("read transfer is GPU_READ_GPUMEM_KERNEL src_idx={}", read_transfer.src_idx);
      AllocGPUMem((void**)&src, read_transfer.nbytes, read_transfer.src_idx);
      //fill_random_float_gpu(src, read_transfer.nbytes / sizeof(float));
    } else {
      LOG_RANK_ANY("ERROR: Unknown transfer type");
      MPI_Abort(MPI_COMM_WORLD, 1);
    }
  } else {
    DEBUG_RANK_ANY("read transfer DNE gpu_idx={}", gpu_idx);
    AllocGPUMem((void**)&src, write_transfer.nbytes, gpu_idx);
    //fill_random_float_gpu(src, read_transfer.nbytes / sizeof(float));
  }

  float *dst;
  float *dst_cpuptr;
  if (write_transfer_exists) {
    if (write_transfer.type == Transfer::TransferType::GPU_WRITE_CPUMEM_KERNEL) {
      DEBUG_RANK_ANY("write transfer is GPU_WRITE_CPUMEM_KERNEL dst_idx={}", write_transfer.dst_idx);
      AllocCPUMemAccessibleFromGPU((void**)&dst, (void**)&dst_cpuptr, write_transfer.nbytes, write_transfer.dst_idx);
      //fill_random_float(dst_cpuptr, write_transfer.nbytes / sizeof(float));
    } else if (write_transfer.type == Transfer::TransferType::GPU_WRITE_GPUMEM_KERNEL) {
      DEBUG_RANK_ANY("write transfer is GPU_WRITE_GPUMEM_KERNEL dst_idx={}", write_transfer.dst_idx);
      AllocGPUMem((void**)&dst, write_transfer.nbytes, write_transfer.dst_idx);
      //fill_random_float_gpu(dst, write_transfer.nbytes / sizeof(float));
    } else {
      LOG_RANK_ANY("ERROR: Unknown transfer type");
      MPI_Abort(MPI_COMM_WORLD, 1);
    }
  } else {
    DEBUG_RANK_ANY("write transfer DNE gpu_idx={}", gpu_idx);
    AllocGPUMem((void**)&dst, read_transfer.nbytes, gpu_idx);
    //fill_random_float_gpu(dst, write_transfer.nbytes / sizeof(float));
  }

  BenchmarkResult res;
  for (int it = 0; it < conf.niters; ++it) {
    CHECK_MPI(MPI_Barrier(MPI_COMM_WORLD));
    auto st = get_time();

    gpu_copy_wrapper_single_channel(dst, src, nbytes, gpu_idx);

    auto et_local = get_time();
    CHECK_MPI(MPI_Barrier(MPI_COMM_WORLD));
    auto et = get_time();

    auto us = get_duration_us(st, et);
    auto us_local = get_duration_us(st, et_local);

    collect_stat(res, it, us, us_local, 0, 0);
  }

  if (read_transfer_exists) {
    if (read_transfer.type == Transfer::TransferType::GPU_READ_CPUMEM_KERNEL) {
      FreeCPUMemAccessibleFromGPU(src_cpuptr, read_transfer.nbytes);
    } else if (read_transfer.type == Transfer::TransferType::GPU_READ_GPUMEM_KERNEL) {
      FreeGPUMem(src);
    } else {
      LOG_RANK_ANY("ERROR: Unknown transfer type");
      MPI_Abort(MPI_COMM_WORLD, 1);
    }
  } else {
    FreeGPUMem(src);
  }

  if (write_transfer_exists) {
    if (write_transfer.type == Transfer::TransferType::GPU_WRITE_CPUMEM_KERNEL) {
      FreeCPUMemAccessibleFromGPU(dst_cpuptr, write_transfer.nbytes);
    } else if (write_transfer.type == Transfer::TransferType::GPU_WRITE_GPUMEM_KERNEL) {
      FreeGPUMem(dst);
    } else {
      LOG_RANK_ANY("ERROR: Unknown transfer type");
      MPI_Abort(MPI_COMM_WORLD, 1);
    }
  } else {
    FreeGPUMem(dst);
  }

  return res;
}

BenchmarkResult RunGPUMemcpyJob(const std::vector<Transfer>& transfers) {
  if (transfers.size() != 1) {
    LOG_RANK_ANY("ERROR: Memcpy job must have only one transfer");
    MPI_Abort(MPI_COMM_WORLD, 1);
  }

  auto& transfer = transfers[0];
  float *src;
  float *dst;
  if (transfer.type == Transfer::TransferType::GPU_READ_CPUMEM_MEMCPY) {
    AllocCPUMem((void**)&src, transfer.nbytes, transfer.src_idx);
    AllocGPUMem((void**)&dst, transfer.nbytes, transfer.dst_idx);
  } else if (transfer.type == Transfer::TransferType::GPU_WRITE_CPUMEM_MEMCPY) {
    AllocGPUMem((void**)&src, transfer.nbytes, transfer.src_idx);
    AllocCPUMem((void**)&dst, transfer.nbytes, transfer.dst_idx);
  } else if (transfer.type == Transfer::TransferType::GPU_READ_GPUMEM_MEMCPY) {
    AllocGPUMem((void**)&src, transfer.nbytes, transfer.src_idx);
    AllocGPUMem((void**)&dst, transfer.nbytes, transfer.dst_idx);
  } else if (transfer.type == Transfer::TransferType::GPU_WRITE_GPUMEM_MEMCPY) {
    AllocGPUMem((void**)&src, transfer.nbytes, transfer.src_idx);
    AllocGPUMem((void**)&dst, transfer.nbytes, transfer.dst_idx);
  } else {
    LOG_RANK_ANY("ERROR: Unknown transfer type");
    MPI_Abort(MPI_COMM_WORLD, 1);
  }
  
  int gpu_idx = transfer.IsRead() ? transfer.dst_idx : transfer.src_idx;
  size_t nbytes = transfer.nbytes;

  BenchmarkResult res;
  for (int it = 0; it < conf.niters; ++it) {
    CHECK_MPI(MPI_Barrier(MPI_COMM_WORLD));
    auto st = get_time();

    gpu_copy_wrapper_memcpy(dst, src, nbytes, gpu_idx);

    auto et_local = get_time();
    CHECK_MPI(MPI_Barrier(MPI_COMM_WORLD));
    auto et = get_time();

    auto us = get_duration_us(st, et);
    auto us_local = get_duration_us(st, et_local);

    collect_stat(res, it, us, us_local, 0, 0);
  }

  if (transfer.type == Transfer::TransferType::GPU_READ_CPUMEM_MEMCPY) {
    FreeCPUMem(src, transfer.nbytes);
    FreeGPUMem(dst);
  } else if (transfer.type == Transfer::TransferType::GPU_WRITE_CPUMEM_MEMCPY) {
    FreeGPUMem(src);
    FreeCPUMem(dst, transfer.nbytes);
  } else if (transfer.type == Transfer::TransferType::GPU_READ_GPUMEM_MEMCPY) {
    FreeGPUMem(src);
    FreeGPUMem(dst);
  } else if (transfer.type == Transfer::TransferType::GPU_WRITE_GPUMEM_MEMCPY) {
    FreeGPUMem(src);
    FreeGPUMem(dst);
  } else {
    LOG_RANK_ANY("ERROR: Unknown transfer type");
    MPI_Abort(MPI_COMM_WORLD, 1);
  }

  return res;
}

BenchmarkResult RunDummyJob() {
  BenchmarkResult res;
  for (int it = 0; it < conf.niters; ++it) {
    CHECK_MPI(MPI_Barrier(MPI_COMM_WORLD));
    auto st = get_time();

    // do nothing

    auto et_local = get_time();
    CHECK_MPI(MPI_Barrier(MPI_COMM_WORLD));
    auto et = get_time();

    auto us = get_duration_us(st, et);
    auto us_local = get_duration_us(st, et_local);

    collect_stat(res, it, us, us_local, 0, 0);
  }
  return res;
}

void ReceiveBenchmark() {
  // Share assignment with SendBenchmark
  int transfers_size;
  CHECK_MPI(MPI_Bcast(&transfers_size, 1, MPI_INT, 0, MPI_COMM_WORLD));

  std::vector<Transfer> transfers(transfers_size);
  CHECK_MPI(MPI_Bcast(transfers.data(), transfers_size * sizeof(Transfer), MPI_BYTE, 0, MPI_COMM_WORLD));

  int transfer_to_rank[transfers_size];
  int transfer_to_rank_sub[transfers_size];
  CHECK_MPI(MPI_Bcast(transfer_to_rank, transfers_size, MPI_INT, 0, MPI_COMM_WORLD));
  CHECK_MPI(MPI_Bcast(transfer_to_rank_sub, transfers_size, MPI_INT, 0, MPI_COMM_WORLD));

  // Transform transfer into actual jobs to run
  // 1. multiple transfers that launch on the same GPU will be merged into one job
  // 2. inter-node transfers will be split into multiple jobs
  int my_rank;
  CHECK_MPI(MPI_Comm_rank(MPI_COMM_WORLD, &my_rank));
  std::vector<int> transfer_idx_assigned;
  for (int i = 0; i < transfers_size; ++i) {
    if (transfer_to_rank[i] == my_rank || transfer_to_rank_sub[i] == my_rank) {
      transfer_idx_assigned.push_back(i);
    }
  }

  if (transfer_idx_assigned.size() == 0) {
    // No job assigned
    //DEBUG_RANK_ANY("ReceiveBenchmark: No job assigned; RunDummyJob");
    RunDummyJob();
  } else {
    std::vector<Transfer> transfers_assigned;
    for (int idx : transfer_idx_assigned) {
      transfers_assigned.push_back(transfers[idx]);
    }
    switch (transfers_assigned[0].type) {
      case Transfer::TransferType::GPU_READ_CPUMEM_KERNEL:
      case Transfer::TransferType::GPU_WRITE_CPUMEM_KERNEL:
      case Transfer::TransferType::GPU_READ_GPUMEM_KERNEL:
      case Transfer::TransferType::GPU_WRITE_GPUMEM_KERNEL:
        //DEBUG_RANK_ANY("ReceiveBenchmark: RunGPUKernelJob");
        RunGPUKernelJob(transfers_assigned);
        break;
      case Transfer::TransferType::GPU_READ_CPUMEM_MEMCPY:
      case Transfer::TransferType::GPU_WRITE_CPUMEM_MEMCPY:
      case Transfer::TransferType::GPU_READ_GPUMEM_MEMCPY:
      case Transfer::TransferType::GPU_WRITE_GPUMEM_MEMCPY:
        RunGPUMemcpyJob(transfers_assigned);
        break;
      case Transfer::TransferType::GPU_GPU_INTER:
      case Transfer::TransferType::GPU_CPU_INTER:
      case Transfer::TransferType::CPU_GPU_INTER:
      case Transfer::TransferType::CPU_CPU_INTER:
        {
          //DEBUG_RANK_ANY("ReceiveBenchmark: RunInterJob");
          int idx = transfer_idx_assigned[0];
          int peer_rank = transfer_to_rank[idx] == my_rank ? transfer_to_rank_sub[idx] : transfer_to_rank[idx];
          RunInterJob(transfers_assigned, peer_rank);
          break;
        }
      default:
        LOG_RANK_ANY("ERROR: Unsupported transfer type");
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
  }
}

BenchmarkResult SendBenchmark(std::vector<Transfer> transfers) {
  int command_idx = static_cast<int>(CommandType::COMMAND_BENCHMARK);
  CHECK_MPI(MPI_Bcast(&command_idx, 1, MPI_INT, 0, MPI_COMM_WORLD)); // match with ProcessPoolLoop

  int transfer_to_rank[transfers.size()];
  int transfer_to_rank_sub[transfers.size()]; // receiving ranks for inter-node transfer
  bool rank_is_assigned[conf.size];
  for (int i = 0; i < conf.size; ++i) {
    rank_is_assigned[i] = false;
  }
  // Prevent rank 0 from being assigned
  rank_is_assigned[0] = true;

  for (size_t i = 0; i < transfers.size(); ++i) {
    int idx_cur = transfers[i].GetGPUIdxKernelLaunchedOn();
    if (idx_cur != -1 && transfers[i].IsMemcpy()) { // Intra-node GPU memcpy job
      bool assigned = false;
      for (int rank = 0; rank < conf.size; ++rank) {
        if (rank_is_assigned[rank] == false && conf.node_idx[rank] == transfers[i].src_node) {
          transfer_to_rank[i] = rank;
          transfer_to_rank_sub[i] = -1;
          rank_is_assigned[transfer_to_rank[i]] = true;
          assigned = true;
          break;
        }
      }
      if (!assigned) {
        LOG_RANK_ANY("ERROR: No rank available for job {}", transfers[i].ToString());
        MPI_Abort(MPI_COMM_WORLD, 1);
      }
    } else if (idx_cur != -1) { // Intra-node GPU kernel job
      bool assigned = false;
      for (size_t j = 0; j < i; ++j) {
        int idx_prev = transfers[j].GetGPUIdxKernelLaunchedOn();
        if (transfers[i].src_node == transfers[j].src_node // as its intra, src_node == dst_node
            && idx_prev == idx_cur && !transfers[j].IsMemcpy()) {
          // TODO assign transfer i to the same rank as j
          transfer_to_rank[i] = transfer_to_rank[j];
          transfer_to_rank_sub[i] = -1;
          rank_is_assigned[transfer_to_rank[i]] = true;
          assigned = true;
          break;
        }
      }
      if (!assigned) {
        for (int rank = 0; rank < conf.size; ++rank) {
          if (rank_is_assigned[rank] == false && conf.node_idx[rank] == transfers[i].src_node) {
            transfer_to_rank[i] = rank;
            transfer_to_rank_sub[i] = -1;
            rank_is_assigned[transfer_to_rank[i]] = true;
            assigned = true;
            break;
          }
        }
        if (!assigned) {
          LOG_RANK_ANY("ERROR: No rank available for job {}", transfers[i].ToString());
          MPI_Abort(MPI_COMM_WORLD, 1);
        }
      }
    } else { // Inter-node transfer job
      // Assign sending(src) side
      {
        bool assigned = false;
        for (int rank = 0; rank < conf.size; ++rank) {
          if (rank_is_assigned[rank] == false && conf.node_idx[rank] == transfers[i].src_node) {
            transfer_to_rank[i] = rank;
            rank_is_assigned[rank] = true;
            assigned = true;
            break;
          }
        }
        if (!assigned) {
          LOG_RANK_ANY("ERROR: No rank available for sending job {}", transfers[i].ToString());
          MPI_Abort(MPI_COMM_WORLD, 1);
        }
      }
      // Assign recving(dst) side
      {
        bool assigned = false;
        for (int rank = 0; rank < conf.size; ++rank) {
          if (rank_is_assigned[rank] == false && conf.node_idx[rank] == transfers[i].dst_node) {
            transfer_to_rank_sub[i] = rank;
            rank_is_assigned[rank] = true;
            assigned = true;
            break;
          }
        }
        if (!assigned) {
          LOG_RANK_ANY("ERROR: No rank available for recving job {}", transfers[i].ToString());
          MPI_Abort(MPI_COMM_WORLD, 1);
        }
      }
    }
  }

  // Log the assignment
  DEBUG_RANK_0("SendBenchmark assignment result:");
  for (size_t i = 0; i < transfers.size(); ++i) {
    DEBUG_RANK_0("Transfer {}: to_rank {}, to_rank_sub {}, {}", i, transfer_to_rank[i], transfer_to_rank_sub[i], transfers[i].ToString());
  }

  // Share assignment with ReceiveBenchmark
  int transfers_size = transfers.size();
  CHECK_MPI(MPI_Bcast(&transfers_size, 1, MPI_INT, 0, MPI_COMM_WORLD));
  CHECK_MPI(MPI_Bcast(transfers.data(), transfers_size * sizeof(Transfer), MPI_BYTE, 0, MPI_COMM_WORLD));
  CHECK_MPI(MPI_Bcast(transfer_to_rank, transfers_size, MPI_INT, 0, MPI_COMM_WORLD));
  CHECK_MPI(MPI_Bcast(transfer_to_rank_sub, transfers_size, MPI_INT, 0, MPI_COMM_WORLD));

  // Rank 0 executes dummy job
  auto res = RunDummyJob();
  res.FillStat();
  double bw = conf.nbytes / (res.us_avg / 1e6); // bytes per second
  DEBUG_RANK_0("BW = {} GB/s", bw / 1e9);

  return res;
}

BenchmarkResult Benchmark(Transfer transfer1, Transfer transfer2) {
  static std::map<std::pair<Transfer, Transfer>, BenchmarkResult> cache;
  if (transfer2 < transfer1) {
    std::swap(transfer1, transfer2);
  }
  std::pair<Transfer, Transfer> p = std::make_pair(transfer1, transfer2);
  if (cache.find(p) != cache.end()) {
    return cache[p];
  }
  std::vector<Transfer> transfers;
  transfers.push_back(transfer1);
  transfers.push_back(transfer2);
  DEBUG_RANK_0("Benchmarking {} and {}", transfer1.ToString(), transfer2.ToString());
  auto res = SendBenchmark(transfers);
  double bw = conf.nbytes / (res.us_avg / 1e6); // bytes per second
  DEBUG_RANK_0("BW = {} GB/s", bw / 1e9);
  cache[p] = res;

  // Congestion analysis
  if (bw < conf.bw_threshold && conf.debug) {
    auto res1 = SendBenchmark({transfer1});
    auto res2 = SendBenchmark({transfer2});
    double bw1 = conf.nbytes / (res1.us_avg / 1e6);
    double bw2 = conf.nbytes / (res2.us_avg / 1e6);
    double rel_cong = bw / std::min(bw1, bw2);
    DEBUG_RANK_0("Relative congestion = {:.3f}, (bw1={}, bw2={})", rel_cong, bw1, bw2);
  }

  return res;
}

BenchmarkResult Benchmark(std::vector<Transfer> transfers) {
  auto res = SendBenchmark(transfers);
  return res;
}

std::vector<Transfer> AddTransfer(std::vector<Transfer> transfers, std::vector<Transfer> transfers_new) {
  for (Transfer transfer_new : transfers_new) {
    for (Transfer transfer : transfers) {
      auto res = Benchmark(transfer, transfer_new);
      double bw = conf.nbytes / (res.us_avg / 1e6); // bytes per second
      if (bw < conf.bw_threshold) {
        // return empty
        return std::vector<Transfer>();
      }
    }
    transfers.push_back(transfer_new);
  }
  return transfers;
}

std::vector<Transfer> AddTransferAtFront(std::vector<Transfer> transfers, std::vector<Transfer> transfers_new) {
  int idx = 0;
  for (Transfer transfer_new : transfers_new) {
    for (Transfer transfer : transfers) {
      auto res = Benchmark(transfer, transfer_new);
      double bw = conf.nbytes / (res.us_avg / 1e6); // bytes per second
      if (bw < conf.bw_threshold) {
        // return empty
        return std::vector<Transfer>();
      }
    }
    transfers.insert(transfers.begin() + idx, transfer_new);
    idx++;
  }
  return transfers;
}

void VisitGPUIntra(std::vector<Transfer> transfers, int g_root, int g_cur, std::vector<int> gpu_unvisited,
              std::vector<std::pair<std::vector<Transfer>, BenchmarkResult>>& result_db
              ) {
  if (transfers.size() != 0 && g_root == g_cur) {
    auto res = Benchmark(transfers);
    double bw = conf.nbytes / (res.us_avg / 1e6); // bytes per second
    DEBUG_RANK_0("Final transfer of size {}:", transfers.size());
    for (size_t i = 0; i < transfers.size(); ++i) {
      DEBUG_RANK_0("{}", transfers[i].ToString());
    }
    DEBUG_RANK_0("BW = {} GB/s", bw / 1e9);
    result_db.push_back(std::make_pair(transfers, res));
    return;
  }
  if (gpu_unvisited.size() == 0) {
    gpu_unvisited.push_back(g_root);
  }
  for (int g_new : gpu_unvisited) {
    std::vector<int> gpu_unvisited_new = RemoveElem(gpu_unvisited, g_new);
    // Try write direct transfer
    if (conf.p2p_available) {
      Transfer new_transfer = {
        .type = Transfer::TransferType::GPU_WRITE_GPUMEM_KERNEL,
        .src_node = 0,
        .dst_node = 0,
        .src_idx = g_cur,
        .dst_idx = g_new,
        .nbytes = conf.nbytes,
      };
      std::vector<Transfer> transfers_new;
      transfers_new.push_back(new_transfer);
      transfers_new = AddTransfer(transfers, transfers_new);
      if (transfers_new.size() != 0) {
        VisitGPUIntra(transfers_new, g_root, g_new, gpu_unvisited_new, result_db);
      }
    }
    // Try read direct transfer
    if (conf.p2p_available) {
      Transfer new_transfer = {
        .type = Transfer::TransferType::GPU_READ_GPUMEM_KERNEL,
        .src_node = 0,
        .dst_node = 0,
        .src_idx = g_cur,
        .dst_idx = g_new,
        .nbytes = conf.nbytes,
      };
      std::vector<Transfer> transfers_new;
      transfers_new.push_back(new_transfer);
      transfers_new = AddTransfer(transfers, transfers_new);
      if (transfers_new.size() != 0) {
        VisitGPUIntra(transfers_new, g_root, g_new, gpu_unvisited_new, result_db);
      }
    }
    for (int numa_idx : conf.numa_available) {
      Transfer write_transfer = {
        .type = Transfer::TransferType::GPU_WRITE_CPUMEM_KERNEL,
        .src_node = 0,
        .dst_node = 0,
        .src_idx = g_cur,
        .dst_idx = numa_idx,
        .nbytes = conf.nbytes,
      };
      Transfer read_transfer = {
        .type = Transfer::TransferType::GPU_READ_CPUMEM_KERNEL,
        .src_node = 0,
        .dst_node = 0,
        .src_idx = numa_idx,
        .dst_idx = g_new,
        .nbytes = conf.nbytes,
      };
      std::vector<Transfer> transfers_new;
      transfers_new.push_back(write_transfer);
      transfers_new.push_back(read_transfer);
      transfers_new = AddTransfer(transfers, transfers_new);
      if (transfers_new.size() != 0) {
        VisitGPUIntra(transfers_new, g_root, g_new, gpu_unvisited_new, result_db);
      }
    }
  }
}

void VisitGPUInterAddPrefix(std::vector<Transfer> transfers, int g_root,
              std::vector<std::pair<std::vector<Transfer>, BenchmarkResult>>& result_db
) {
  // Cases:
  // #0: CPU-NIC-CPU-GPU
  // #1: GPU-NIC-GPU (p2p)
  // #2: CPU-NIC-GPU (p2p)
  // #3: GPU-NIC-CPU-GPU (p2p)

  // case 0: CPU(i)-NIC(Node2)-NIC(Node0)-CPU(j)-GPU(g_root)
  LOG_RANK_0("VisitGPUInterAddPrefix Case 0");
  for (int i : conf.numa_available) {
    for (int j : conf.numa_available) {
      std::vector<Transfer> prefix;
      prefix.push_back(Transfer{
        .type = Transfer::TransferType::CPU_CPU_INTER,
        .src_node = 2,
        .dst_node = 0,
        .src_idx = i,
        .dst_idx = j,
        .nbytes = conf.nbytes,
      });
      prefix.push_back(Transfer{
        .type = Transfer::TransferType::GPU_READ_CPUMEM_KERNEL,
        .src_node = 0,
        .dst_node = 0,
        .src_idx = j,
        .dst_idx = g_root,
        .nbytes = conf.nbytes,
      });
      auto transfers_new = AddTransferAtFront(transfers, prefix);
      if (transfers_new.size() != 0) {
        auto res = Benchmark(transfers_new);
        result_db.push_back(std::make_pair(transfers_new, res));
      }
    }
  }

  if (conf.p2p_available == false) return;

  // case 1: GPU(i)-NIC(Node2)-NIC(Node0)-GPU(g_root)
  LOG_RANK_0("VisitGPUInterAddPrefix Case 1");
  for (int i = 0; i < conf.num_gpus; ++i) {
    std::vector<Transfer> prefix;
    prefix.push_back(Transfer{
      .type = Transfer::TransferType::GPU_GPU_INTER,
      .src_node = 2,
      .dst_node = 0,
      .src_idx = i,
      .dst_idx = g_root,
      .nbytes = conf.nbytes,
    });
    auto transfers_new = AddTransferAtFront(transfers, prefix);
    if (transfers_new.size() != 0) {
      auto res = Benchmark(transfers_new);
      result_db.push_back(std::make_pair(transfers_new, res));
    }
  }

  // case 2: CPU(i)-NIC(Node2)-NIC(Node0)-GPU(g_root)
  LOG_RANK_0("VisitGPUInterAddPrefix Case 2");
  for (int i : conf.numa_available) {
    std::vector<Transfer> prefix;
    prefix.push_back(Transfer{
      .type = Transfer::TransferType::CPU_GPU_INTER,
      .src_node = 2,
      .dst_node = 0,
      .src_idx = i,
      .dst_idx = g_root,
      .nbytes = conf.nbytes,
    });
    auto transfers_new = AddTransferAtFront(transfers, prefix);
    if (transfers_new.size() != 0) {
      auto res = Benchmark(transfers_new);
      result_db.push_back(std::make_pair(transfers_new, res));
    }
  }

  // case 3: GPU(i)-NIC(Node2)-NIC(Node0)-CPU(j)-GPU(g_root)
  LOG_RANK_0("VisitGPUInterAddPrefix Case 3");
  for (int i : conf.numa_available) {
    for (int j : conf.numa_available) {
      std::vector<Transfer> prefix;
      prefix.push_back(Transfer{
        .type = Transfer::TransferType::GPU_CPU_INTER,
        .src_node = 2,
        .dst_node = 0,
        .src_idx = i,
        .dst_idx = j,
        .nbytes = conf.nbytes,
      });
      prefix.push_back(Transfer{
        .type = Transfer::TransferType::GPU_READ_CPUMEM_KERNEL,
        .src_node = 0,
        .dst_node = 0,
        .src_idx = j,
        .dst_idx = g_root,
        .nbytes = conf.nbytes,
      });
      auto transfers_new = AddTransferAtFront(transfers, prefix);
      if (transfers_new.size() != 0) {
        auto res = Benchmark(transfers_new);
        result_db.push_back(std::make_pair(transfers_new, res));
      }
    }
  }
}

void VisitGPUInterAddSuffix(std::vector<Transfer> transfers, int g_root, int g_cur,
              std::vector<std::pair<std::vector<Transfer>, BenchmarkResult>>& result_db
) {
  // Cases:
  // #0: GPU-CPU-NIC-CPU
  // #1: GPU-NIC-GPU (p2p necessary)
  // #2: GPU-NIC-CPU (p2p necessary)
  // #3: GPU-CPU-NIC-GPU (p2p necessary)

  // case 0: GPU(g_cur)-CPU(i)-NIC(Node0)-NIC(Node1)-CPU(j):
  LOG_RANK_0("VisitGPUInterAddSuffix Case 0");
  for (int i : conf.numa_available) {
    for (int j : conf.numa_available) {
      std::vector<Transfer> suffix;
      suffix.push_back(Transfer{
        .type = Transfer::TransferType::GPU_WRITE_CPUMEM_KERNEL,
        .src_node = 0,
        .dst_node = 0,
        .src_idx = g_cur,
        .dst_idx = i,
        .nbytes = conf.nbytes,
      });
      suffix.push_back(Transfer{
        .type = Transfer::TransferType::CPU_CPU_INTER,
        .src_node = 0,
        .dst_node = 1,
        .src_idx = i,
        .dst_idx = j,
        .nbytes = conf.nbytes,
      });
      auto transfers_new = AddTransfer(transfers, suffix);
      if (transfers_new.size() != 0) {
        VisitGPUInterAddPrefix(transfers_new, g_root, result_db);
      }
    }
  }

  if (conf.p2p_available == false) return;

  // case 1: GPU(g_cur)-NIC(Node0)-NIC(Node1)-GPU(i):
  LOG_RANK_0("VisitGPUInterAddSuffix Case 1");
  for (int i = 0; i < conf.num_gpus; ++i) {
    std::vector<Transfer> suffix;
    suffix.push_back(Transfer{
      .type = Transfer::TransferType::GPU_GPU_INTER,
      .src_node = 0,
      .dst_node = 1,
      .src_idx = g_cur,
      .dst_idx = i,
      .nbytes = conf.nbytes,
    });
    auto transfers_new = AddTransfer(transfers, suffix);
    if (transfers_new.size() != 0) {
      VisitGPUInterAddPrefix(transfers_new, g_root, result_db);
    }
  }

  // case 2: GPU(g_cur)-NIC(Node0)-NIC(Node1)-CPU(i):
  LOG_RANK_0("VisitGPUInterAddSuffix Case 2");
  for (int i : conf.numa_available) {
    std::vector<Transfer> suffix;
    suffix.push_back(Transfer{
      .type = Transfer::TransferType::GPU_CPU_INTER,
      .src_node = 0,
      .dst_node = 1,
      .src_idx = g_cur,
      .dst_idx = i,
      .nbytes = conf.nbytes,
    });
    auto transfers_new = AddTransfer(transfers, suffix);
    if (transfers_new.size() != 0) {
      VisitGPUInterAddPrefix(transfers_new, g_root, result_db);
    }
  }

  // case 3: GPU(g_cur)-CPU(i)-NIC(Node0)-NIC(Node1)-GPU(j):
  LOG_RANK_0("VisitGPUInterAddSuffix Case 3");
  for (int i : conf.numa_available) {
    for (int j = 0; j < conf.num_gpus; ++j) {
      std::vector<Transfer> suffix;
      suffix.push_back(Transfer{
        .type = Transfer::TransferType::GPU_WRITE_CPUMEM_KERNEL,
        .src_node = 0,
        .dst_node = 0,
        .src_idx = g_cur,
        .dst_idx = i,
        .nbytes = conf.nbytes,
      });
      suffix.push_back(Transfer{
        .type = Transfer::TransferType::CPU_GPU_INTER,
        .src_node = 0,
        .dst_node = 1,
        .src_idx = i,
        .dst_idx = j,
        .nbytes = conf.nbytes,
      });
      auto transfers_new = AddTransfer(transfers, suffix);
      if (transfers_new.size() != 0) {
        VisitGPUInterAddPrefix(transfers_new, g_root, result_db);
      }
    }
  }
}

void VisitGPUInter(std::vector<Transfer> transfers, int g_root, int g_cur, std::vector<int> gpu_unvisited,
              std::vector<std::pair<std::vector<Transfer>, BenchmarkResult>>& result_db
              ) {
  if (gpu_unvisited.size() == 0) {
    // transfers is now a linear chain that visits all GPUs, starts at GPU, ends at GPU
    LOG_RANK_0("VisitGPUInter end condition prolog");
    VisitGPUInterAddSuffix(transfers, g_root, g_cur, result_db);
    LOG_RANK_0("VisitGPUInter end condition epilog");
    return;
  }
  for (int g_new : gpu_unvisited) {
    std::vector<int> gpu_unvisited_new = RemoveElem(gpu_unvisited, g_new);
    // Try write direct transfer
    if (conf.p2p_available) {
      Transfer new_transfer = {
        .type = Transfer::TransferType::GPU_WRITE_GPUMEM_KERNEL,
        .src_node = 0,
        .dst_node = 0,
        .src_idx = g_cur,
        .dst_idx = g_new,
        .nbytes = conf.nbytes,
      };
      std::vector<Transfer> transfers_new;
      transfers_new.push_back(new_transfer);
      transfers_new = AddTransfer(transfers, transfers_new);
      if (transfers_new.size() != 0) {
        VisitGPUInter(transfers_new, g_root, g_new, gpu_unvisited_new, result_db);
      }
    }
    // Try read direct transfer
    if (conf.p2p_available) {
      Transfer new_transfer = {
        .type = Transfer::TransferType::GPU_READ_GPUMEM_KERNEL,
        .src_node = 0,
        .dst_node = 0,
        .src_idx = g_cur,
        .dst_idx = g_new,
        .nbytes = conf.nbytes,
      };
      std::vector<Transfer> transfers_new;
      transfers_new.push_back(new_transfer);
      transfers_new = AddTransfer(transfers, transfers_new);
      if (transfers_new.size() != 0) {
        VisitGPUInter(transfers_new, g_root, g_new, gpu_unvisited_new, result_db);
      }
    }
    for (int numa_idx : conf.numa_available) {
      Transfer write_transfer = {
        .type = Transfer::TransferType::GPU_WRITE_CPUMEM_KERNEL,
        .src_node = 0,
        .dst_node = 0,
        .src_idx = g_cur,
        .dst_idx = numa_idx,
        .nbytes = conf.nbytes,
      };
      Transfer read_transfer = {
        .type = Transfer::TransferType::GPU_READ_CPUMEM_KERNEL,
        .src_node = 0,
        .dst_node = 0,
        .src_idx = numa_idx,
        .dst_idx = g_new,
        .nbytes = conf.nbytes,
      };
      std::vector<Transfer> transfers_new;
      transfers_new.push_back(write_transfer);
      transfers_new.push_back(read_transfer);
      transfers_new = AddTransfer(transfers, transfers_new);
      if (transfers_new.size() != 0) {
        VisitGPUInter(transfers_new, g_root, g_new, gpu_unvisited_new, result_db);
      }
    }
  }
}

std::vector<std::vector<Transfer>> GetNewTransferCandidatesIntra(SearchState& s, int gpu_mask, bool& done) {
  // ring formed
  if (s.transfers.size() > 0 && s.transfers.front().src_idx == s.transfers.back().dst_idx) {
    done = true;
    return {};
  }

  std::vector<bool> visited(conf.num_gpus, false);
  int g_cur = -1;

  if (s.transfers.size() == 0) {
    // Visit first available GPU
    for (int i = 0; i < conf.num_gpus; ++i) {
      if (gpu_mask & (1 << i)) {
        visited[i] = true;
        g_cur = i;
        break;
      }
    }
  } else {
    // Check which GPUs are visited
    for (auto transfer : s.transfers) {
      if (GetType(transfer, false) == Transfer::DeviceType::GPU) {
        visited[transfer.dst_idx] = true;
        g_cur = transfer.dst_idx;
      }
      if (GetType(transfer, true) == Transfer::DeviceType::GPU) {
        visited[transfer.src_idx] = true;
      }
    }
  }
  assert(g_cur != -1);

  std::vector<int> gpu_unvisited;
  for (int i = 0; i < conf.num_gpus; ++i) {
    if (visited[i] == false && (gpu_mask & (1 << i))) {
      gpu_unvisited.push_back(i);
    }
  }

  if (gpu_unvisited.size() == 0) {
    // route back to the first GPU to form a ring
    gpu_unvisited.push_back(s.transfers.front().src_idx);
  }

  if (gpu_unvisited.size() > 0) {
    // Intra-node transfer
    std::vector<std::vector<Transfer>> cands;
    for (int g_new : gpu_unvisited) {
      if (conf.p2p_available) {
        // Try write direct transfer
        if (!conf.disable_kernel) {
          Transfer new_transfer = {
            .type = Transfer::TransferType::GPU_WRITE_GPUMEM_KERNEL,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = g_cur,
            .dst_idx = g_new,
            .nbytes = conf.nbytes,
          };
          std::vector<Transfer> transfers_new;
          transfers_new.push_back(new_transfer);
          cands.push_back(transfers_new);
        }
        if (!conf.disable_memcpy) {
          Transfer new_transfer = {
            .type = Transfer::TransferType::GPU_WRITE_GPUMEM_MEMCPY,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = g_cur,
            .dst_idx = g_new,
            .nbytes = conf.nbytes,
          };
          std::vector<Transfer> transfers_new;
          transfers_new.push_back(new_transfer);
          cands.push_back(transfers_new);
        }
        // Try read direct transfer
        if (!conf.disable_kernel) {
          Transfer new_transfer = {
            .type = Transfer::TransferType::GPU_READ_GPUMEM_KERNEL,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = g_cur,
            .dst_idx = g_new,
            .nbytes = conf.nbytes,
          };
          std::vector<Transfer> transfers_new;
          transfers_new.push_back(new_transfer);
          cands.push_back(transfers_new);
        }
        if (!conf.disable_memcpy && !conf.disable_memcpy_read) {
          Transfer new_transfer = {
            .type = Transfer::TransferType::GPU_READ_GPUMEM_MEMCPY,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = g_cur,
            .dst_idx = g_new,
            .nbytes = conf.nbytes,
          };
          std::vector<Transfer> transfers_new;
          transfers_new.push_back(new_transfer);
          cands.push_back(transfers_new);
        }
      }
      for (int numa_idx : conf.numa_available) {
        if (!conf.disable_kernel) {
          Transfer write_transfer = {
            .type = Transfer::TransferType::GPU_WRITE_CPUMEM_KERNEL,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = g_cur,
            .dst_idx = numa_idx,
            .nbytes = conf.nbytes,
          };
          Transfer read_transfer = {
            .type = Transfer::TransferType::GPU_READ_CPUMEM_KERNEL,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = numa_idx,
            .dst_idx = g_new,
            .nbytes = conf.nbytes,
          };
          std::vector<Transfer> transfers_new;
          transfers_new.push_back(write_transfer);
          transfers_new.push_back(read_transfer);
          cands.push_back(transfers_new);
        }
        if (!conf.disable_kernel && !conf.disable_memcpy) {
          Transfer write_transfer = {
            .type = Transfer::TransferType::GPU_WRITE_CPUMEM_MEMCPY,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = g_cur,
            .dst_idx = numa_idx,
            .nbytes = conf.nbytes,
          };
          Transfer read_transfer = {
            .type = Transfer::TransferType::GPU_READ_CPUMEM_KERNEL,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = numa_idx,
            .dst_idx = g_new,
            .nbytes = conf.nbytes,
          };
          std::vector<Transfer> transfers_new;
          transfers_new.push_back(write_transfer);
          transfers_new.push_back(read_transfer);
          cands.push_back(transfers_new);
        }
        if (!conf.disable_kernel && !conf.disable_memcpy && !conf.disable_memcpy_read) {
          Transfer write_transfer = {
            .type = Transfer::TransferType::GPU_WRITE_CPUMEM_KERNEL,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = g_cur,
            .dst_idx = numa_idx,
            .nbytes = conf.nbytes,
          };
          Transfer read_transfer = {
            .type = Transfer::TransferType::GPU_READ_CPUMEM_MEMCPY,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = numa_idx,
            .dst_idx = g_new,
            .nbytes = conf.nbytes,
          };
          std::vector<Transfer> transfers_new;
          transfers_new.push_back(write_transfer);
          transfers_new.push_back(read_transfer);
          cands.push_back(transfers_new);
        }
        if (!conf.disable_memcpy && !conf.disable_memcpy_read) {
          Transfer write_transfer = {
            .type = Transfer::TransferType::GPU_WRITE_CPUMEM_MEMCPY,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = g_cur,
            .dst_idx = numa_idx,
            .nbytes = conf.nbytes,
          };
          Transfer read_transfer = {
            .type = Transfer::TransferType::GPU_READ_CPUMEM_MEMCPY,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = numa_idx,
            .dst_idx = g_new,
            .nbytes = conf.nbytes,
          };
          std::vector<Transfer> transfers_new;
          transfers_new.push_back(write_transfer);
          transfers_new.push_back(read_transfer);
          cands.push_back(transfers_new);
        }
      }
    }
    return cands;
  }

  assert(false);
  return {};
}

std::vector<std::vector<Transfer>> GetNewTransferCandidatesInter(SearchState& s, Transfer head, Transfer tail, int gpu_mask, bool& done, bool& prefix) {
  // linear chain formed; done
  if (s.transfers.size() > 0 && s.transfers.front().src_node != 0 && s.transfers.back().dst_node != 0) {
    done = 1;
    return {};
  }

  // Add tail transfer
  if (s.transfers.size() > 0 && s.transfers.front().src_node != 0) {
    // Last transfer should be inter-node transfer with next node
    std::vector<std::vector<Transfer>> cands;
    // Cases:
    // #0: GPU-CPU-NIC-CPU
    // #1: GPU-NIC-GPU (p2p necessary)
    // #2: GPU-NIC-CPU (p2p necessary)
    // #3: GPU-CPU-NIC-GPU (p2p necessary)

    int g_cur = s.transfers.back().dst_idx;
    // case 0: GPU(g_cur)-CPU(i)-NIC(Node0)-NIC(Node1)-CPU(j):
    if (GetType(tail, true) == Transfer::DeviceType::CPUMEM && GetType(tail, false) == Transfer::DeviceType::CPUMEM) {
      if (!conf.disable_kernel) {
        std::vector<Transfer> suffix;
        suffix.push_back(Transfer{
          .type = Transfer::TransferType::GPU_WRITE_CPUMEM_KERNEL,
          .src_node = 0,
          .dst_node = 0,
          .src_idx = g_cur,
          .dst_idx = tail.src_idx,
          .nbytes = conf.nbytes,
        });
        suffix.push_back(tail);
        cands.push_back(suffix);
      }
      if (!conf.disable_memcpy) {
        std::vector<Transfer> suffix;
        suffix.push_back(Transfer{
          .type = Transfer::TransferType::GPU_WRITE_CPUMEM_MEMCPY,
          .src_node = 0,
          .dst_node = 0,
          .src_idx = g_cur,
          .dst_idx = tail.src_idx,
          .nbytes = conf.nbytes,
        });
        suffix.push_back(tail);
        cands.push_back(suffix);
      }
    }

    if (conf.p2p_available == false) return cands;

    // case 1: GPU(g_cur)-NIC(Node0)-NIC(Node1)-GPU(i):
    if (GetType(tail, true) == Transfer::DeviceType::GPU && GetType(tail, false) == Transfer::DeviceType::GPU
        && s.transfers.back().dst_idx == tail.src_idx) {
      std::vector<Transfer> suffix;
      suffix.push_back(tail);
      cands.push_back(suffix);
    }

    // case 2: GPU(g_cur)-NIC(Node0)-NIC(Node1)-CPU(i):
    if (GetType(tail, true) == Transfer::DeviceType::GPU && GetType(tail, false) == Transfer::DeviceType::CPUMEM
        && s.transfers.back().dst_idx == tail.src_idx) {
      std::vector<Transfer> suffix;
      suffix.push_back(tail);
      cands.push_back(suffix);
    }

    // case 3: GPU(g_cur)-CPU(i)-NIC(Node0)-NIC(Node1)-GPU(j):
    if (GetType(tail, true) == Transfer::DeviceType::CPUMEM && GetType(tail, false) == Transfer::DeviceType::GPU) {
      if (!conf.disable_kernel) {
        std::vector<Transfer> suffix;
        suffix.push_back(Transfer{
          .type = Transfer::TransferType::GPU_WRITE_CPUMEM_KERNEL,
          .src_node = 0,
          .dst_node = 0,
          .src_idx = g_cur,
          .dst_idx = tail.src_idx,
          .nbytes = conf.nbytes,
        });
        suffix.push_back(tail);
        cands.push_back(suffix);
      }
      if (!conf.disable_memcpy) {
        std::vector<Transfer> suffix;
        suffix.push_back(Transfer{
          .type = Transfer::TransferType::GPU_WRITE_CPUMEM_MEMCPY,
          .src_node = 0,
          .dst_node = 0,
          .src_idx = g_cur,
          .dst_idx = tail.src_idx,
          .nbytes = conf.nbytes,
        });
        suffix.push_back(tail);
        cands.push_back(suffix);
      }
    }
    return cands;
  }

  // Pick unvisited GPUs
  std::vector<bool> visited(conf.num_gpus, false);
  int g_cur = -1;

  // Check which GPUs are visited
  for (auto transfer : s.transfers) {
    if (GetType(transfer, false) == Transfer::DeviceType::GPU && transfer.dst_node == 0) {
      if (!(gpu_mask & (1 << transfer.dst_idx))) {
        // head transfer is visiting wrong gpu
        return {};
      }
      visited[transfer.dst_idx] = true;
      g_cur = transfer.dst_idx;
    }
  }

  std::vector<int> gpu_unvisited;
  for (int i = 0; i < conf.num_gpus; ++i) {
    if (visited[i] == false && (gpu_mask & (1 << i))) {
      gpu_unvisited.push_back(i);
    }
  }

  // Add head transfer
  if (gpu_unvisited.size() == 1) {
    prefix = true;
    // we visited all; (1 because of first transfer's src_idx) add head transfer
    std::vector<std::vector<Transfer>> cands;
    // Cases:
    // #0: CPU-NIC-CPU-GPU
    // #1: GPU-NIC-GPU (p2p necessary)
    // #2: CPU-NIC-GPU (p2p necessary)
    // #3: GPU-NIC-CPU-GPU (p2p)

    // case 0: CPU(i)-NIC(Node2)-NIC(Node0)-CPU(j)-GPU(g_root)
    int g_root = gpu_unvisited[0];
    if (GetType(head, true) == Transfer::DeviceType::CPUMEM && GetType(head, false) == Transfer::DeviceType::CPUMEM) {
      if (!conf.disable_kernel) {
        std::vector<Transfer> prefix;
        prefix.push_back(head);
        prefix.push_back(Transfer{
          .type = Transfer::TransferType::GPU_READ_CPUMEM_KERNEL,
          .src_node = 0,
          .dst_node = 0,
          .src_idx = head.dst_idx,
          .dst_idx = g_root,
          .nbytes = conf.nbytes,
        });
        cands.push_back(prefix);
      }
      if (!conf.disable_memcpy && !conf.disable_memcpy_read) {
        std::vector<Transfer> prefix;
        prefix.push_back(head);
        prefix.push_back(Transfer{
          .type = Transfer::TransferType::GPU_READ_CPUMEM_MEMCPY,
          .src_node = 0,
          .dst_node = 0,
          .src_idx = head.dst_idx,
          .dst_idx = g_root,
          .nbytes = conf.nbytes,
        });
        cands.push_back(prefix);
      }
    }

    if (conf.p2p_available == false) return cands;

    // case 1: GPU(i)-NIC(Node2)-NIC(Node0)-GPU(g_root)
    if (GetType(head, true) == Transfer::DeviceType::GPU && GetType(head, false) == Transfer::DeviceType::GPU) {
      std::vector<Transfer> prefix;
      prefix.push_back(head);
      cands.push_back(prefix);
    }

    // case 2: CPU(i)-NIC(Node2)-NIC(Node0)-GPU(g_root)
    if (GetType(head, true) == Transfer::DeviceType::CPUMEM && GetType(head, false) == Transfer::DeviceType::GPU) {
      std::vector<Transfer> prefix;
      prefix.push_back(head);
      cands.push_back(prefix);
    }

    // case 3: GPU(i)-NIC(Node2)-NIC(Node0)-CPU(j)-GPU(g_root)
    if (GetType(head, true) == Transfer::DeviceType::GPU && GetType(head, false) == Transfer::DeviceType::CPUMEM) {
      if (!conf.disable_kernel) {
        std::vector<Transfer> prefix;
        prefix.push_back(head);
        prefix.push_back(Transfer{
          .type = Transfer::TransferType::GPU_READ_CPUMEM_KERNEL,
          .src_node = 0,
          .dst_node = 0,
          .src_idx = head.dst_idx,
          .dst_idx = g_root,
          .nbytes = conf.nbytes,
        });
        cands.push_back(prefix);
      }
      if (!conf.disable_memcpy && !conf.disable_memcpy_read) {
        std::vector<Transfer> prefix;
        prefix.push_back(head);
        prefix.push_back(Transfer{
          .type = Transfer::TransferType::GPU_READ_CPUMEM_MEMCPY,
          .src_node = 0,
          .dst_node = 0,
          .src_idx = head.dst_idx,
          .dst_idx = g_root,
          .nbytes = conf.nbytes,
        });
        cands.push_back(prefix);
      }
    }

    return cands; 
  }

  // Intra-node transfer
  std::vector<int> gpu_src;
  if (g_cur == -1) {
    // First GPU can be any GPU
    assert(s.transfers.size() == 0);
    for (int i = 0; i < conf.num_gpus; ++i) {
      if (gpu_mask & (1 << i)) {
        gpu_src.push_back(i);
      }
    }
  } else {
    gpu_src.push_back(g_cur);
  }

  std::vector<std::vector<Transfer>> cands;
  for (int g_src : gpu_src) {
    for (int g_dst : gpu_unvisited) {
      if (g_src == g_dst) continue;
      if (s.transfers.size() > 0 && s.transfers.front().src_idx == g_dst) continue;
      if (conf.p2p_available) {
        // Try write direct transfer
        if (!conf.disable_kernel) {
          Transfer new_transfer = {
            .type = Transfer::TransferType::GPU_WRITE_GPUMEM_KERNEL,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = g_src,
            .dst_idx = g_dst,
            .nbytes = conf.nbytes,
          };
          std::vector<Transfer> transfers_new;
          transfers_new.push_back(new_transfer);
          cands.push_back(transfers_new);
        }
        if (!conf.disable_memcpy) {
          Transfer new_transfer = {
            .type = Transfer::TransferType::GPU_WRITE_GPUMEM_MEMCPY,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = g_src,
            .dst_idx = g_dst,
            .nbytes = conf.nbytes,
          };
          std::vector<Transfer> transfers_new;
          transfers_new.push_back(new_transfer);
          cands.push_back(transfers_new);
        }
        // Try read direct transfer
        if (!conf.disable_kernel) {
          Transfer new_transfer = {
            .type = Transfer::TransferType::GPU_READ_GPUMEM_KERNEL,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = g_src,
            .dst_idx = g_dst,
            .nbytes = conf.nbytes,
          };
          std::vector<Transfer> transfers_new;
          transfers_new.push_back(new_transfer);
          cands.push_back(transfers_new);
        }
        if (!conf.disable_memcpy && !conf.disable_memcpy_read){
          Transfer new_transfer = {
            .type = Transfer::TransferType::GPU_READ_GPUMEM_MEMCPY,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = g_src,
            .dst_idx = g_dst,
            .nbytes = conf.nbytes,
          };
          std::vector<Transfer> transfers_new;
          transfers_new.push_back(new_transfer);
          cands.push_back(transfers_new);
        }
      }
      for (int numa_idx : conf.numa_available) {
        if (!conf.disable_kernel) {
          Transfer write_transfer = {
            .type = Transfer::TransferType::GPU_WRITE_CPUMEM_KERNEL,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = g_src,
            .dst_idx = numa_idx,
            .nbytes = conf.nbytes,
          };
          Transfer read_transfer = {
            .type = Transfer::TransferType::GPU_READ_CPUMEM_KERNEL,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = numa_idx,
            .dst_idx = g_dst,
            .nbytes = conf.nbytes,
          };
          std::vector<Transfer> transfers_new;
          transfers_new.push_back(write_transfer);
          transfers_new.push_back(read_transfer);
          cands.push_back(transfers_new);
        }
        if (!conf.disable_kernel && !conf.disable_memcpy) {
          Transfer write_transfer = {
            .type = Transfer::TransferType::GPU_WRITE_CPUMEM_MEMCPY,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = g_src,
            .dst_idx = numa_idx,
            .nbytes = conf.nbytes,
          };
          Transfer read_transfer = {
            .type = Transfer::TransferType::GPU_READ_CPUMEM_KERNEL,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = numa_idx,
            .dst_idx = g_dst,
            .nbytes = conf.nbytes,
          };
          std::vector<Transfer> transfers_new;
          transfers_new.push_back(write_transfer);
          transfers_new.push_back(read_transfer);
          cands.push_back(transfers_new);
        }
        if (!conf.disable_kernel && !conf.disable_memcpy && !conf.disable_memcpy_read) {
          Transfer write_transfer = {
            .type = Transfer::TransferType::GPU_WRITE_CPUMEM_KERNEL,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = g_src,
            .dst_idx = numa_idx,
            .nbytes = conf.nbytes,
          };
          Transfer read_transfer = {
            .type = Transfer::TransferType::GPU_READ_CPUMEM_MEMCPY,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = numa_idx,
            .dst_idx = g_dst,
            .nbytes = conf.nbytes,
          };
          std::vector<Transfer> transfers_new;
          transfers_new.push_back(write_transfer);
          transfers_new.push_back(read_transfer);
          cands.push_back(transfers_new);
        }
        if (!conf.disable_memcpy && !conf.disable_memcpy_read) {
          Transfer write_transfer = {
            .type = Transfer::TransferType::GPU_WRITE_CPUMEM_MEMCPY,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = g_src,
            .dst_idx = numa_idx,
            .nbytes = conf.nbytes,
          };
          Transfer read_transfer = {
            .type = Transfer::TransferType::GPU_READ_CPUMEM_MEMCPY,
            .src_node = 0,
            .dst_node = 0,
            .src_idx = numa_idx,
            .dst_idx = g_dst,
            .nbytes = conf.nbytes,
          };
          std::vector<Transfer> transfers_new;
          transfers_new.push_back(write_transfer);
          transfers_new.push_back(read_transfer);
          cands.push_back(transfers_new);
        }
      }
    }
  }
  return cands;
}

void PopulateCache(cache_t& cache, std::vector<Transfer>& transfers, double bw) {
  //LOG_RANK_0("PopulateCache: bw={}", bw);
  //for (size_t i = 0; i < transfers.size(); ++i) {
  //  LOG_RANK_0("{}", transfers[i].ToString());
  //}

  DEBUG_RANK_0("Populate Cache Encoded:");
  std::set<int> transfers_enc;
  for (auto& transfer : transfers) {
    transfers_enc.insert(transfer.Encode());
    DEBUG_RANK_0("enc={} {}", transfer.Encode(), transfer.ToString());
  }
  cache.emplace(transfers_enc, bw);
}

int GetNuma(Transfer& t, bool src) {
  if (src) {
    switch (t.type) {
      case Transfer::TransferType::GPU_READ_CPUMEM_KERNEL:
      case Transfer::TransferType::GPU_READ_CPUMEM_MEMCPY:
      case Transfer::TransferType::CPU_CPU_INTER:
      case Transfer::TransferType::CPU_GPU_INTER:
        return t.src_idx;
      case Transfer::TransferType::GPU_WRITE_CPUMEM_KERNEL:
      case Transfer::TransferType::GPU_READ_GPUMEM_KERNEL:
      case Transfer::TransferType::GPU_WRITE_GPUMEM_KERNEL:
      case Transfer::TransferType::GPU_WRITE_CPUMEM_MEMCPY:
      case Transfer::TransferType::GPU_READ_GPUMEM_MEMCPY:
      case Transfer::TransferType::GPU_WRITE_GPUMEM_MEMCPY:
      case Transfer::TransferType::GPU_GPU_INTER:
      case Transfer::TransferType::GPU_CPU_INTER:
        return conf.gpu_numa[t.src_idx];
      default:
        assert(false);
    }
  } else { // dst
    switch (t.type) {
      case Transfer::TransferType::GPU_WRITE_CPUMEM_KERNEL:
      case Transfer::TransferType::GPU_WRITE_CPUMEM_MEMCPY:
      case Transfer::TransferType::CPU_CPU_INTER:
      case Transfer::TransferType::GPU_CPU_INTER:
        return t.dst_idx;
      case Transfer::TransferType::GPU_READ_CPUMEM_KERNEL:
      case Transfer::TransferType::GPU_READ_CPUMEM_MEMCPY:
      case Transfer::TransferType::GPU_READ_GPUMEM_KERNEL:
      case Transfer::TransferType::GPU_WRITE_GPUMEM_KERNEL:
      case Transfer::TransferType::GPU_READ_GPUMEM_MEMCPY:
      case Transfer::TransferType::GPU_WRITE_GPUMEM_MEMCPY:
      case Transfer::TransferType::GPU_GPU_INTER:
      case Transfer::TransferType::CPU_GPU_INTER:
        return conf.gpu_numa[t.dst_idx];
      default:
        assert(false);
    }
  }
}

bool IsInNuma(Transfer& t, int node, int numa, bool src) {
  if (src) {
    if (t.src_node == node && GetNuma(t, true) == numa) {
      return true;
    }
    return false;
  } else {
    if (t.dst_node == node && GetNuma(t, false) == numa) {
      return true;
    }
    return false;
  }
}

// n C k
// https://gist.github.com/shaunlebron/2843980
bool next_combination(std::vector<int>& values, int k, int n) {
  if (k == 0) return false;

    // identify the rightmost index that can be shifted to the right
    // e.g. 11000111
    //       ^
    int i = k-1;
    if (values[i] == n - 1) {
        i--;
        while (i >= 0 && values[i] == values[i+1]-1)
            i--;
    }

    // exit if no more combinations can be made
    // e.g. 00011111
    if (i==-1)
        return false;

    // shift chosen index to the right
    // e.g.
    // (before: 11000111)
    //           ^
    // (after:  10100111)
    //            ^
    values[i]++;

    // left-collapse any following indexes
    // (before: 10100111)
    //            ^  ***
    // (after:  10111100)
    //            ^***
    i++;
    while (i < k) {
        values[i] = values[i-1]+1;
        i++;
    }
    return true;
}

// f: X -> Y, |X| = n, |Y| = m, n <= m
// len(comb) == n, initially filled with 0 ~ n - 1
// len(perm) == n, initially filled with 0 ~ n - 1 
bool init_injection(int n, int m, std::vector<int>& comb, std::vector<int>& perm, std::vector<int>& out) {
  if (n > m) {
    return false;
  }
  comb.clear(); perm.clear(); out.clear();
  for (int i = 0; i < n; ++i) {
    comb.push_back(i);
    perm.push_back(i);
    out.push_back(i);
  }
  return true;
}

bool next_injection(int n, int m, std::vector<int>& comb, std::vector<int>& perm, std::vector<int>& out) {
  if (n > m) {
    return false;
  }
  if (comb.size() == 0 || perm.size() == 0) {
    comb.clear(); perm.clear();
    for (int i = 0; i < n; ++i) {
      comb.push_back(i);
      perm.push_back(i);
    }
  }

  if (std::next_permutation(perm.begin(), perm.end())) {
    out.clear();
    for (int i = 0; i < n; ++i) {
      out.push_back(comb[perm[i]]);
    }
    return true;
  } else {
    if (next_combination(comb, n, m)) {
      perm.clear();
      for (int i = 0; i < n; ++i) {
        perm.push_back(i);
      }
      out.clear();
      for (int i = 0; i < n; ++i) {
        out.push_back(comb[perm[i]]);
      }
      return true;
    } else {
      return false;
    }
  }
}

static void LogVector(std::vector<int> v) {
  for (size_t i = 0; i < v.size(); ++i) {
    DEBUG_RANK_0("[{}] : {}", i, v[i]);
  }
}

  // Lets solve it recursively
  // copy transfers, mark all idxs as -1
  // if you find -1 idx, check original (node, numa) of that slot
  // Find all devices in that (node, numa)
  // Pick (node, new numa) to map (including the case (old numa) == (new numa))
  // Check that devices are compatible
  // * for NIC, NIC exists in only one node (currently) so cannot move to other numa
  // * for CPU, always movable
  // * for GPUs, we should try all mappings if multiple GPUs exist in the NUMA (N->M bijections, m!/(m-n)! = mCn * n!)
double CheckCacheRecurse(cache_t& cache, std::vector<Transfer> transfers, std::vector<Transfer> new_transfers) {
  DEBUG_RANK_0("CheckCacheRecurse enter");
  int node = -1, numa;
  for (int i = 0; i < (int)new_transfers.size(); ++i){
    if (new_transfers[i].src_idx == -1) {
      node = new_transfers[i].src_node;
      numa = GetNuma(transfers[i], true);
      break;
    }
    if (new_transfers[i].dst_idx == -1) {
      node = new_transfers[i].dst_node;
      numa = GetNuma(transfers[i], false);
      break;
    }
  }
  if (node == -1) { // not found; all transfers are mapped properly
    std::set<int> transfers_enc;
    DEBUG_RANK_0("CheckCacheRecurse Encoded:");
    for (auto& transfer : new_transfers) {
      transfers_enc.insert(transfer.Encode());
      DEBUG_RANK_0("{}", transfer.Encode());
    }
    auto it = cache.find(transfers_enc);
    if (it != cache.end()) { // cache hit
      double bw = it->second;
      if (conf.debug_cache) {
        LOG_RANK_0("Cache hit! bw={}GB/s", bw / 1e9);
        LOG_RANK_0("Original transfer:");
        for (size_t i = 0; i < transfers.size(); ++i) {
          LOG_RANK_0("{}", transfers[i].ToString());
        }
        LOG_RANK_0("Isomorphic transfer:");
        for (size_t i = 0; i < new_transfers.size(); ++i) {
          LOG_RANK_0("{}", new_transfers[i].ToString());
        }
        LOG_RANK_0("Cache transfer:");
        for (int x: it->first) {
          LOG_RANK_0("{}", Transfer::Decode(x).ToString());
        }
      }
      return bw;
    } else {
      DEBUG_RANK_0("Cache miss!");
      DEBUG_RANK_0("Original transfer:");
      for (size_t i = 0; i < transfers.size(); ++i) {
        DEBUG_RANK_0("{}", transfers[i].ToString());
      }
      DEBUG_RANK_0("Isomorphic transfer:");
      for (size_t i = 0; i < new_transfers.size(); ++i) {
        DEBUG_RANK_0("{}", new_transfers[i].ToString());
      }
      return -1;
    }
  }
  std::vector<int> cpumems, gpus, nics;
  for (int i = 0; i < (int)new_transfers.size(); ++i) {
    if (IsInNuma(transfers[i], node, numa, true)) {
      switch (GetType(transfers[i], true)) {
        case Transfer::DeviceType::CPUMEM:
          cpumems.push_back(transfers[i].src_idx);
          break;
        case Transfer::DeviceType::GPU:
          gpus.push_back(transfers[i].src_idx);
          break;
        default:
          assert(false);
      }
    }
    if (IsInNuma(transfers[i], node, numa, false)) {
      switch (GetType(transfers[i], false)) {
        case Transfer::DeviceType::CPUMEM:
          cpumems.push_back(transfers[i].dst_idx);
          break;
        case Transfer::DeviceType::GPU:
          gpus.push_back(transfers[i].dst_idx);
          break;
        default:
          assert(false);
      }
    }
    if (transfers[i].IsInter() && (transfers[i].src_node == node || transfers[i].dst_node == node)
        && conf.nic_numa[0] == numa) { // TODO assume one NIC currently
      nics.push_back(0);
    }
  }
  // unique cpumems
  std::sort(cpumems.begin(), cpumems.end());
  cpumems.erase(std::unique(cpumems.begin(), cpumems.end()), cpumems.end());
  // unique gpus
  std::sort(gpus.begin(), gpus.end());
  gpus.erase(std::unique(gpus.begin(), gpus.end()), gpus.end());
  // unique nics
  std::sort(nics.begin(), nics.end());
  nics.erase(std::unique(nics.begin(), nics.end()), nics.end());

  // Find unused numa
  std::vector<bool> numa_used(conf.num_numa, false);
  for (int i = 0; i < (int)new_transfers.size(); ++i) {
    if (new_transfers[i].src_node == node && new_transfers[i].src_idx != -1) {
      numa_used[GetNuma(new_transfers[i], true)] = true;
    }
    if (new_transfers[i].dst_node == node && new_transfers[i].dst_idx != -1) {
      numa_used[GetNuma(new_transfers[i], false)] = true;
    }
  }

  for (int new_numa: conf.numa_available) {
    DEBUG_RANK_0("node={} old_numa={} new_numa={}", node, numa, new_numa);
    if (numa_used[new_numa]) continue;
    // numa -> new_numa mapping
    // * Check NIC
    // f: nics -> conf.numa_nic[new_numa]
    std::vector<int> nic_comb, nic_perm, nic_map;
    if (!init_injection(nics.size(), conf.numa_nic[new_numa].size(), nic_comb, nic_perm, nic_map)) continue;
    do {
      DEBUG_RANK_0("nic_map:"); LogVector(nic_map);
      // * check GPU
      std::vector<int> gpu_comb, gpu_perm, gpu_map;
      if (!init_injection(gpus.size(), conf.numa_gpu[new_numa].size(), gpu_comb, gpu_perm, gpu_map)) continue;
      do {
        DEBUG_RANK_0("gpu_map:"); LogVector(gpu_map);
        // * check cpumem
        std::vector<int> cpumem_comb, cpumem_perm, cpumem_map;
        if (!init_injection(cpumems.size(), conf.numa_cpumem[new_numa].size(), cpumem_comb, cpumem_perm, cpumem_map)) continue;
        do {
          DEBUG_RANK_0("cpumem_map:"); LogVector(cpumem_map);
          DEBUG_RANK_0("Original transfer:");
          for (size_t i = 0; i < transfers.size(); ++i) {
            DEBUG_RANK_0("{}", transfers[i].ToString());
          }
          DEBUG_RANK_0("New transfer (before fill):");
          for (size_t i = 0; i < new_transfers.size(); ++i) {
            DEBUG_RANK_0("{}", new_transfers[i].ToString());
          }
          // mapping is fine! Apply mapping to new_transfers
          for (int i = 0; i < (int)new_transfers.size(); ++i) {
            if (IsInNuma(transfers[i], node, numa, true)) {
              switch (GetType(transfers[i], true)) {
                case Transfer::DeviceType::CPUMEM:
                  new_transfers[i].src_idx = conf.numa_cpumem[new_numa][cpumem_map[std::find(cpumems.begin(), cpumems.end(), transfers[i].src_idx) - cpumems.begin()]];
                  break;
                case Transfer::DeviceType::GPU:
                  new_transfers[i].src_idx = conf.numa_gpu[new_numa][gpu_map[std::find(gpus.begin(), gpus.end(), transfers[i].src_idx) - gpus.begin()]];
                  break;
                default:
                  assert(false);
              }
            }
            if (IsInNuma(transfers[i], node, numa, false)) {
              switch (GetType(transfers[i], false)) {
                case Transfer::DeviceType::CPUMEM:
                  new_transfers[i].dst_idx = conf.numa_cpumem[new_numa][cpumem_map[std::find(cpumems.begin(), cpumems.end(), transfers[i].dst_idx) - cpumems.begin()]];
                  break;
                case Transfer::DeviceType::GPU:
                  new_transfers[i].dst_idx = conf.numa_gpu[new_numa][gpu_map[std::find(gpus.begin(), gpus.end(), transfers[i].dst_idx) - gpus.begin()]];
                  break;
                default:
                  assert(false);
              }
            }
          }
          DEBUG_RANK_0("New transfer (after fill):");
          for (size_t i = 0; i < new_transfers.size(); ++i) {
            DEBUG_RANK_0("{}", new_transfers[i].ToString());
          }
          // Recursive call
          double bw = CheckCacheRecurse(cache, transfers, new_transfers);
          if (bw < 0) {
            // keep searching
          } else {
            return bw;
          }
        } while (next_injection(cpumems.size(), conf.numa_cpumem[new_numa].size(), cpumem_comb, cpumem_perm, cpumem_map));
      } while (next_injection(gpus.size(), conf.numa_gpu[new_numa].size(), gpu_comb, gpu_perm, gpu_map));
    } while (next_injection(nics.size(), conf.numa_nic[new_numa].size(), nic_comb, nic_perm, nic_map));
  }
  return -1;
}

double CheckCache(cache_t& cache, std::vector<Transfer> transfers) {
  std::vector<Transfer> new_transfers;
  for (auto transfer : transfers) {
    transfer.src_idx = -1;
    transfer.dst_idx = -1;
    new_transfers.push_back(transfer);
  }
  return CheckCacheRecurse(cache, transfers, new_transfers);
}

void RunDijkstra(cache_t& cache, Transfer head, Transfer tail, int gpu_mask, const char* fn, bool intra) {
  // sanity check
  if (intra) {
    if (__builtin_popcount(gpu_mask) < 2) {
      return;
    }
  } else {
    if (__builtin_popcount(gpu_mask) < 1) {
      return;
    }
    if (GetType(head, false) == Transfer::DeviceType::GPU && (gpu_mask & (1 << head.dst_idx)) == 0) {
      return;
    }
    if (GetType(tail, true) == Transfer::DeviceType::GPU && (gpu_mask & (1 << tail.src_idx)) == 0) {
      return;
    }
    if (GetType(head, false) == Transfer::DeviceType::GPU && GetType(tail, true) == Transfer::DeviceType::GPU) {
      if (head.dst_idx == tail.src_idx && __builtin_popcount(gpu_mask) > 1) {
        return;
      }
    }
  }

  std::priority_queue<SearchState> pq;
  if (intra) {
    SearchState s = {
      .transfers = {},
      .bw = std::numeric_limits<double>::max()
    };
    pq.push(s);
  } else {
    SearchState s = {
      .transfers = {},
      .bw = std::numeric_limits<double>::max()
    };
    pq.push(s);
  }

  int log_interval = 20, log_count = 0;
  while (!pq.empty()) {
    auto s = pq.top();
    pq.pop();
    log_count++;
    if (log_count % log_interval == 0) {
      DEBUG_RANK_0("Dijkstra current(BW = {} GB/s):", s.bw / 1e9);
      for (size_t i = 0; i < s.transfers.size(); ++i) {
        DEBUG_RANK_0("{}", s.transfers[i].ToString());
      }
    }
    {
      DEBUG_RANK_0("Searching transfer of size {} from dijkstra:", s.transfers.size());
      for (size_t i = 0; i < s.transfers.size(); ++i) {
        DEBUG_RANK_0("{}", s.transfers[i].ToString());
      }
      DEBUG_RANK_0("BW = {} GB/s", s.bw / 1e9);
    }
    bool done = false, prefix = false;
    std::vector<std::vector<Transfer>> new_transfer_candidates;
    if (intra) {
      new_transfer_candidates = GetNewTransferCandidatesIntra(s, gpu_mask, done);
    } else {
      new_transfer_candidates = GetNewTransferCandidatesInter(s, head, tail, gpu_mask, done, prefix);
    }
    if (done) {
      LOG_RANK_0("Best transfer of size {} from dijkstra:", s.transfers.size());
      for (size_t i = 0; i < s.transfers.size(); ++i) {
        LOG_RANK_0("{}", s.transfers[i].ToString());
      }
      LOG_RANK_0("BW = {} GB/s", s.bw / 1e9);
      FILE *fp = fopen(fn, "w");
      tinyxml2::XMLPrinter printer(fp);
      printer.OpenElement("transfers");
      printer.PushAttribute("gbps", s.bw / 1e9);
      for (size_t i = 0; i < s.transfers.size(); ++i) {
        printer.OpenElement("transfer");
        printer.PushAttribute("type", Transfer::TransferTypeToString(s.transfers[i].type).c_str());
        printer.PushAttribute("src_idx", s.transfers[i].src_idx);
        printer.PushAttribute("dst_idx", s.transfers[i].dst_idx);
        printer.CloseElement();
      }
      printer.CloseElement();
      fclose(fp);
      return;
    }
    for (auto& cand : new_transfer_candidates) {
      auto new_transfers = s.transfers;
      if (prefix) {
        new_transfers.insert(new_transfers.begin(), cand.begin(), cand.end());
      } else {
        new_transfers.insert(new_transfers.end(), cand.begin(), cand.end());
      }
      double bw = CheckCache(cache, new_transfers);
      if (bw < 0) {
        auto res = Benchmark(new_transfers);
        bw = conf.nbytes / (res.us_avg / 1e6); // bytes per second
        PopulateCache(cache, new_transfers, bw);
        if (conf.debug_cache) {
          LOG_RANK_0("Cache miss bw = {}GB/s", bw / 1e9);
          for (size_t i = 0; i < new_transfers.size(); ++i) {
            LOG_RANK_0("{}", new_transfers[i].ToString());
          }
        }
        conf.cache_miss++;
      } else {
        conf.cache_hit++;
      }
      if ((conf.cache_miss + conf.cache_hit) % 20 == 0) {
        size_t bench_us = get_duration_us(conf.start_time, get_time());
        double bench_per_sec = (double)conf.cache_miss / (bench_us == 0 ? 1 : bench_us) * 1e6;
        DEBUG_RANK_0("total_bench = {}, cache_miss = {}, cache_hit = {}, {} bench/s", conf.cache_miss + conf.cache_hit, conf.cache_miss, conf.cache_hit, bench_per_sec);
        //LOG_RANK_0("Bench example(BW = {} GB/s):", bw / 1e9);
        //for (size_t i = 0; i < new_transfers.size(); ++i) {
        //  LOG_RANK_0("{}", new_transfers[i].ToString());
        //}
      }
      SearchState new_s = {
        .transfers = new_transfers,
        .bw = bw,
      };
      pq.push(new_s);
    }
  }
}

void ProcessPoolLoop() {
  while (true) {
    int command_idx;
    CHECK_MPI(MPI_Bcast(&command_idx, 1, MPI_INT, 0, MPI_COMM_WORLD));
    CommandType command = static_cast<CommandType>(command_idx);
    switch (command) {
      case CommandType::COMMAND_BENCHMARK:
        ReceiveBenchmark();
        break;
      case CommandType::COMMAND_EXIT:
        return;
        break;
      default:
        LOG_RANK_0("Unknown command {}", command_idx);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
  }
}

void CommandExit() {
  int command_idx = static_cast<int>(CommandType::COMMAND_EXIT);
  CHECK_MPI(MPI_Bcast(&command_idx, 1, MPI_INT, 0, MPI_COMM_WORLD)); // match with ProcessPoolLoop
}

void PrintResultDBByRank(std::vector<std::pair<std::vector<Transfer>, BenchmarkResult>>& result_db, int top = 0) {
  // Sort by BW
  std::vector<std::pair<size_t, size_t>> rank_sorter;
  for (size_t i = 0; i < result_db.size(); ++i) {
    rank_sorter.push_back(std::make_pair(result_db[i].second.us_avg, i));
  }
  std::sort(rank_sorter.begin(), rank_sorter.end());
  size_t end = top == 0 ? rank_sorter.size() : std::min(top, static_cast<int>(rank_sorter.size()));
  for (size_t i = 0; i < end; ++i) {
    auto& transfers = result_db[rank_sorter[i].second].first;
    auto& res = result_db[rank_sorter[i].second].second;
    double bw = conf.nbytes / (res.us_avg / 1e6); // bytes per second
    LOG_RANK_0("Rank {} transfer of size {}:", i, transfers.size());
    for (size_t i = 0; i < transfers.size(); ++i) {
      LOG_RANK_0("{}", transfers[i].ToString());
    }
    LOG_RANK_0("BW = {} GB/s", bw / 1e9);
  }
}
