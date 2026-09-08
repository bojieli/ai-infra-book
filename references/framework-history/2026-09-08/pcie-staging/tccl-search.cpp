#include <hwloc/bitmap.h>
#include <mpi.h>
#include <cstdio>
#include <cstdlib>
#include <cuda_runtime.h>
#include <map>
#include <set>
#include <hwloc.h>
#define FMT_HEADER_ONLY
#include <spdlog/fmt/ranges.h>
#include "conf_v2.hpp"
#include "benchmark_v2.hpp"
#include "util.hpp"
#include "check.hpp"

static void print_help(const char *prog_name) {
  printf("Usage: %s [-d]", prog_name);
  printf("Options:\n");
  printf("     -d : print debug. (default: off)\n");
  printf("     -t : BW threshold in GB/s. (default: 0)\n");
  printf("     -o : output xml directory.\n");
}

static char dir_name[1024] = "";
static void parse_opt(int argc, char **argv) {
  int c;
  while ((c = getopt(argc, argv, "dt:o:")) != -1) {
    switch (c) {
      case 'd': conf.debug = true; break;
      case 't': conf.bw_threshold = atof(optarg) * 1e9; break;
      case 'o': strcpy(dir_name, optarg); break;
      default: print_help(argv[0]); exit(0);
    }
  }
  if (strlen(dir_name) == 0) {
    print_help(argv[0]);
    exit(0);
  }
}

// Find numa index the object belongs to
int FindNumaNode(hwloc_obj_t obj) {
  while (obj && !obj->memory_arity) {
    obj = obj->parent;
  }
  obj = obj->memory_first_child;
  return obj->logical_index;
}

void DetectTopology() {
  /*
   * Example topo >
   * AMD-V100 and AMD-3090:
   *   conf.gpu_numa = {3, 1, 1, 0};
   *   conf.numa_gpu = {{3}, {1, 2}, {}, {0}};
   *   conf.nic_numa = {0};
   *   conf.numa_nic = {{0}, {}, {}, {}};
   *   conf.cpumem_numa = {0, 1, 2, 3};
   *   conf.numa_cpumem = {{0}, {1}, {2}, {3}};
   * Intel-V100:
   *   conf.gpu_numa = {0, 0, 2, 2};
   *   conf.numa_gpu = {{0, 1}, {}, {2, 3}, {}};
   *   conf.nic_numa = {1}; // Check with lstopo file.png
   *   conf.numa_nic = {{}, {0}, {}, {}};
   *   conf.cpumem_numa = {0, 1, 2, 3};
   *   conf.numa_cpumem = {{0}, {1}, {2}, {3}};
   */
  
  int num_objs = std::max(conf.num_gpus, conf.num_numa);
  conf.num_bits_idx = num_objs <= 1 ? 1 : 32 - __builtin_clz(num_objs - 1);
  conf.num_bits_inter_tf = 2 + 2 * conf.num_bits_idx;

  conf.numa_gpu.resize(conf.num_numa);
  conf.gpu_numa.resize(conf.num_gpus);
  conf.numa_nic.resize(conf.num_numa);
  conf.numa_cpumem.resize(conf.num_numa);
  for (int i = 0; i < conf.num_numa; ++i) {
    conf.cpumem_numa.push_back(i);
    conf.numa_cpumem[i].push_back(i);
  }

  hwloc_topology_t topo;
  CHECK_ERRNO(hwloc_topology_init(&topo));
  // osdev is disabled by default
  CHECK_ERRNO(hwloc_topology_set_io_types_filter(topo, HWLOC_TYPE_FILTER_KEEP_IMPORTANT));
  CHECK_ERRNO(hwloc_topology_load(topo));

  for (hwloc_obj_t it = NULL; (it = hwloc_get_next_osdev(topo, it)) != NULL; ) {
    // osdev itself does not have pci attribute
    // parent of osdev would be pcidev
    int pcibus = it->parent->attr->pcidev.bus;
    int pcidev = it->parent->attr->pcidev.dev;
    int pcifun = it->parent->attr->pcidev.func;
    if (it->attr->osdev.type == HWLOC_OBJ_OSDEV_OPENFABRICS) {
      int nic_idx = conf.nic_numa.size();
      int numa_idx = FindNumaNode(it);
      LOG_RANK_ANY("Found {} at PCI {:02x}:{:02x}.{:01x} / NUMA {}! Assuming it is IB NIC...\n",
        it->name, pcibus, pcidev, pcifun, numa_idx);
      if (nic_idx > 0) {
        LOG_RANK_ANY("ERROR: does not support NIC more than one");
        MPI_Abort(MPI_COMM_WORLD, 1);
      }
      conf.numa_nic[numa_idx].push_back(nic_idx);
      conf.nic_numa.push_back(numa_idx);
    } else if (it->attr->osdev.type == HWLOC_OBJ_OSDEV_COPROC) {
      int num_gpus, cuda_idx = -1;
      CHECK_CUDA(cudaGetDeviceCount(&num_gpus));
      for (int i = 0; i < num_gpus; ++i) {
        cudaDeviceProp prop;
        CHECK_CUDA(cudaGetDeviceProperties(&prop, i));
        if (pcibus == prop.pciBusID && pcidev == prop.pciDeviceID) {
          cuda_idx = i;
          int numa_idx = FindNumaNode(it);
          LOG_RANK_ANY("Found {} at PCI {:02x}:{:02x}.{:01x} / NUMA {}! Assuming it is NVIDIA GPU (CUDA idx={})...\n",
            it->name, pcibus, pcidev, pcifun, numa_idx, cuda_idx);
          conf.numa_gpu[numa_idx].push_back(cuda_idx);
          conf.gpu_numa[cuda_idx] = numa_idx;
          break;
        }
      }
    }
  }

  LOG_RANK_ANY("conf.num_bits_idx = {}", conf.num_bits_idx);
  LOG_RANK_ANY("conf.gpu_numa = {}", conf.gpu_numa);
  LOG_RANK_ANY("conf.numa_gpu = {}", conf.numa_gpu);
  LOG_RANK_ANY("conf.nic_numa = {}", conf.nic_numa);
  LOG_RANK_ANY("conf.numa_nic = {}", conf.numa_nic);
  LOG_RANK_ANY("conf.cpumem_numa = {}", conf.cpumem_numa);
  LOG_RANK_ANY("conf.numa_cpumem = {}", conf.numa_cpumem);
}

int main(int argc, char** argv) {
  MPI_Init(&argc, &argv);

  // conf defaults
  conf.start_time = get_time();
  conf.nbytes = 32 * 1024 * 1024;
  conf.bw_threshold = 0; 
  conf.niters = 10;
  conf.warmup_iters = conf.niters / 10;
  conf.disable_kernel = false;
  conf.disable_memcpy = true;
  conf.disable_memcpy_read = true;

  parse_opt(argc, argv);

  ValidateLaunchConf();
  ValidateCuda();
  ValidateNuma();
  DetectTopology();
  if (conf.debug) {
    spdlog::set_level(spdlog::level::debug);
  }
  MPI_Comm_rank(MPI_COMM_WORLD, &conf.rank);
  MPI_Comm_size(MPI_COMM_WORLD, &conf.size);

  LOG_RANK_ANY("Validation complete");

  int rank;
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Barrier(MPI_COMM_WORLD);
  if (rank == 0) {
    std::map<std::set<int>, double> cache;

    // Metadata
    {
      char xmlfn[2048];
      sprintf(xmlfn, "%s/metadata.xml", dir_name);
      FILE *fp = fopen(xmlfn, "w");
      tinyxml2::XMLPrinter printer(fp);
      printer.OpenElement("metadata");
      printer.PushAttribute("num_gpus", conf.num_gpus);
      printer.PushAttribute("num_numa", conf.num_numa);
      printer.PushAttribute("num_bits_idx", conf.num_bits_idx);
      printer.CloseElement();
      fclose(fp);
    }

    // Intra
    for (int gpu_mask = 0; gpu_mask < (1 << conf.num_gpus); ++gpu_mask) {
      if (__builtin_popcount(gpu_mask) < 2) continue;
      char xmlfn[2048];
      sprintf(xmlfn, "%s/intra_%d.xml", dir_name, gpu_mask);
      LOG_RANK_0("Progress: intra, gpu_mask = {:b}, xmlfn = {}", gpu_mask, xmlfn);
      Transfer dummy = Transfer::DecodeInter(0, 0, 0);
      RunDijkstra(cache, dummy, dummy, gpu_mask, xmlfn, true);
    }
    
    // Inter
    for (int head = 0; head < (1 << conf.num_bits_inter_tf); ++head) {
      for (int tail = 0; tail < (1 << conf.num_bits_inter_tf); ++tail) {
        for (int gpu_mask = 0; gpu_mask < (1 << conf.num_gpus); ++gpu_mask) {
          if (__builtin_popcount(gpu_mask) < 1) continue;
          Transfer head_transfer = Transfer::DecodeInter(head, 2, 0);
          Transfer tail_transfer = Transfer::DecodeInter(tail, 0, 1);
          char xmlfn[2048];
          sprintf(xmlfn, "%s/inter_%d_%d_%d.xml", dir_name, head, tail, gpu_mask);
          LOG_RANK_0("Progress: inter, head = {}, tail = {}, gpu_mask = {:b}, xmlfn = {}", head, tail, gpu_mask, xmlfn);
          RunDijkstra(cache, head_transfer, tail_transfer, gpu_mask, xmlfn, false);
        }
      }
    }

    CommandExit();
  } else {
    ProcessPoolLoop();
  }

  MPI_Finalize();

  return 0;
}