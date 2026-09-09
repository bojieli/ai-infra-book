
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.13150677.svg)](https://doi.org/10.5281/zenodo.13150677)

The source code for the simulator presented in our paper at the "MICRO 2024" conference.

## Paper Details

- Title: HyFiSS: A Hybrid Fidelity Stall-Aware Simulator for GPGPUs
- Conference: MICRO 2024

## Prerequisites

- C++ Compiler (g++), the version we use is `g++ (GCC) 7.3.1 20180303 (Red Hat 7.3.1-5)`.
  All compilers that support the C++11 standard will do well. You can install by this way:
  ```shell
  yum install g++
  ```
- Make, the version we use is `GNU Make 4.2.1`. You can install by this way:
  ```shell
  yum install make
  ```
- Python, the version we use is `Python 3.7.0`. We recommend you to use Anaconda to manage
  Python packages, and the guide to install Anaconda is available
  [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html#installing-conda).
- MPICH, the version of MPICH we use is `v3.3.2` and it is available
  [here](https://www.mpich.org/static/downloads/3.3.2/mpich-3.3.2.tar.gz).
  Download the source code, uncompress the folder, and change into the MPICH directory.
  ```shell
  wget https://www.mpich.org/static/downloads/3.3.2/mpich-3.3.2.tar.gz
  tar -xzf mpich-3.3.2.tar.gz
  cd mpich-3.3.2
  ```
  After doing this, you should be able to configure your installation by performing `./configure`.
  ```shell
  ./configure
  ```
  If you need to install MPICH to a local directory (for example, if you don't have root access
  to your machine), type `./configure --prefix=/path/to/your/path`. 
  When the configuration is done, build and install MPICH with `make && sudo make install`.
  After installing MPICH, you also need to set the environment variable:
  ```shell
  export MPI_HOME=/path/to/mpich-3.3.2
  export PATH=$PATH:$MPI_HOME/bin
  export MANPATH=$MANPATH:$MPI_HOME/man
  export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MPI_HOME/lib
  ```
  After this, you should be able to type `mpiexec --version` or `mpirun --version` and see the
  version information of MPICH.
- Boost Library, the version we use is `v1.83.0`, and it is available
  [here](https://boostorg.jfrog.io/artifactory/main/release/1.83.0/source/boost_1_83_0.tar.gz).
  Download the source code, uncompress the folder, and change into the Boost directory.
  ```shell
  wget https://boostorg.jfrog.io/artifactory/main/release/1.83.0/source/boost_1_83_0.tar.gz
  tar -xzf boost_1_83_0.tar.gz
  cd boost_1_83_0
  ```
  After doing this, you should be able to compile the Boost library.
  ```shell
  ./bootstrap.sh -prefix=/path/to/boost
  ```
  Where `/path/to/boost` is the path you want to install Boost in.
  As explained in the boost installation instructions, running the `./bootstrap.sh` from the boost root directory will produce a `project-config.jam` file. You need to edit that file and add the following line:
  ```shell
  using mpi ;
  ```
  When the above is done, install Boost with `sudo ./b2 install`， and this will allow you
  to install the Boost library in the `/path/to/boost` directory.
  After installing, you also need to set the environment variable:
  ```shell
  export BOOST_HOME=/path/to/boost
  export CPLUS_INCLUDE_PATH=$BOOST_HOME/include:$CPLUS_INCLUDE_PATH
  export C_INCLUDE_PATH=$BOOST_HOME/include:$C_INCLUDE_PATH
  export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$BOOST_HOME/lib
  ```

## Building the Simulator

1. Clone the repository:
   ```shell
   git clone https://github.com/RepositoryAnonymous/gpu-simulator.git gpu-simulator
   ```

2. Change to the project directory:
   ```shell
   cd gpu-simulator
   ```

3. Build the simulator:
   ```shell
   make all -j
   ```

The compiled simulator executable is called `gpu-simulator.x`, and is just in the current directory.

## Clone the Benchmark Suit 

The benchmark application suit we used for validation consisted of 43 applications with a total 
of 1784 kernels. We evaluate them on a real NVIDIA QUADRO GV100. These applications are from the 
cuBLAS library, the heterogeneous computing benchmark suite PolyBench and Rodinia, the fluid 
dynamics benchmark LULESH, the deep learning basic operator benchmark suite DeepBench, the DNN 
benchmark suite Tango, the unstructured mesh mini-app benchmark PENNANT. For all selected 
applications, we select their first 100 kernels for evaluation. All workloads are compiled using 
CUDA 11.8 with the compute capability `sm70` for the Volta architecture. You can clone this 
benchmark suit we used from [here](https://github.com/RepositoryAnonymous/simulator-apps).

1. Change to the simulator project directory:
   ```shell
   cd gpu-simulator
   ```

2. Clone the benchmark suit repository:
   ```shell
   git clone https://github.com/RepositoryAnonymous/simulator-apps.git apps
   ```

For guidance on compiling these applications and getting their traces on real hardware, please 
refer to [here](https://github.com/RepositoryAnonymous/simulator-apps/blob/main/README.md). And this repo 
also provides the guide to obtain experimental results and reproduction images of our paper. 
All compilation scripts are being sorted out and will be released in a few days (current time: August 1, 2024).
We have evaluated more than 50 applications from many different benchmark suites, so writing a compile 
script for them all will take some time.

## Preprocessing the Traces

Please refer to our reply [here](https://github.com/RepositoryAnonymous/gpu-simulator/issues/1).

## Running the Simulator

To run the GPU simulator, use the following command:
```shell
mpirun -np [num of processes] ./gpu-simulator.x 
  --configs [/path/to/application/configs] 
  --kernel_id [kernel id you want to evaluate] 
  --config_file ./DEV-Def/QV100.config
```

The options:
- `-np <num>`: Number of processes.
- `--configs <path>`: Specify the configuration file of the application
- `--kernel_id <num>`: Specify the kernel ID for simulation

Example:
```shell
mpirun -np 10 ./gpu_simulator --configs ./apps/Rodinia/hotspot/configs --kernel_id 0 --config_file ./DEV-Def/QV100.config
```

Here, the `./apps/Rodinia/hotspot/configs` are generated by `tracing_tool`. For detailed instructions, please refer to 
[here](https://github.com/RepositoryAnonymous/gpu-simulator/blob/main/tracing-tool/README.md).

After this, the simulator will generate output files (like `kernel-0-rank-x.temp.txt`, where `x` represents the process number) 
of many processes to the `./apps/Rodinia/hotspot/outputs` directory. 

Next, we need to merge the results of these processes using the script in the root directory of our simulator:

```shell
python merge_report.py --dir ./apps/Rodinia/hotspot/outputs --kernel_id 0 --np 10
```

The merged output file is named `kernel-0-summary.txt` and will be located in the `./apps/Rodinia/hotspot/outputs` directory, 
and the content is roughly as follows:

```c

 - Config: ./apps/Rodinia/hotspot/outputs

 - Theoretical Performance: 
       * Thread_block_limit_SM: 32
       * Thread_block_limit_registers: 6
       * Thread_block_limit_shared_memory: 32
       * Thread_block_limit_warps: 8
       * Theoretical_max_active_warps_per_SM: 48
       * Theoretical_occupancy: 0.75

 - L1 Cache Performance: 
       * Unified_L1_cache_hit_rate: 0.0349
       * Unified_L1_cache_requests: 216240

 - L2 Cache Performance: 
       * L2_cache_hit_rate: 0.6657
       * L2_cache_requests: 1186944
       * L2_read_transactions: 166020
       * L2_write_transactions: 42680
       * L2_total_transactions: 208700

 - DRAM Performance: 
       * DRAM_total_transactions: 49152

 - Global Memory Performance: 
       * GMEM_read_requests: 29240
       * GMEM_write_requests: 11008
       * GMEM_total_requests: 40248
       * GMEM_read_transactions: 172720
       * GMEM_write_transactions: 43520
       * GMEM_total_transactions: 216240
       * Number_of_read_transactions_per_read_requests: 5.91
       * Number_of_write_transactions_per_write_requests: 3.95
       * Total_number_of_global_atomic_requests: 0
       * Total_number_of_global_reduction_requests: 0
       * Global_memory_atomic_and_reduction_transactions: 0

 - SMs Performance: 
       * Achieved_active_warps_per_SM: 37.93
       * Achieved_occupancy: 0.75

       * GPU_active_cycles: 26087
       * SM_active_cycles: 26087

       * Warp_instructions_executed: 3073296
       * Instructions_executed_per_clock_cycle_IPC: 1.47
       * Total_instructions_executed_per_seconds (MIPS): 2182.06

       * Kernel_execution_time (ns): 18028

 - Simulator Performance: 
       * Simulation_time_memory_model (s): 0.37
       * Simulation_time_compute_model (s): 1.30

 - Stall Cycles: 
       * Compute_Structural_Stall: 6153
       * Compute_Data_Stall: 899
       * Memory_Structural_Stall: 3023
       * Memory_Data_Stall: 3501
       * Synchronization_Stall: 749
       * Control_Stall: 0
       * Idle_Stall: 90
       * Other_Stall: 0
       * No_Stall: 5489

 - Stall Cycles Distribution: 
       * Compute_Structural_Stall_ratio: 0.309134
       * Compute_Data_Stall_ratio: 0.045167
       * Memory_Structural_Stall_ratio: 0.151879
       * Memory_Data_Stall_ratio: 0.175894
       * Synchronization_Stall_ratio: 0.037631
       * Control_Stall_ratio: 0.000000
       * Idle_Stall_ratio: 0.004522
       * Other_Stall_ratio: 0.000000
       * No_Stall_ratio: 0.275774

 - Memory Structural Stall Cycles Breakdown: 
       * Issue_out_has_no_free_slot: 3023.0
       * Issue_previous_issued_inst_exec_type_is_memory: 0.0
       * Execute_result_bus_has_no_slot_for_latency: 0.0
       * Execute_m_dispatch_reg_of_fu_is_not_empty: 2010.0
       * Writeback_bank_of_reg_is_not_idle: 35.0
       * ReadOperands_bank_reg_belonged_to_was_allocated: 9.0
       * ReadOperands_port_num_m_in_ports_m_in_fails_as_not_found_free_cu: 2783.0
       * Execute_icnt_injection_buffer_is_full: 0.0

 - Memory Structural Stall Cycles Breakdown Distribution: 
       * Issue_out_has_no_free_slot: 0.384606
       * Issue_previous_issued_inst_exec_type_is_memory: 0.000000
       * Execute_result_bus_has_no_slot_for_latency: 0.000000
       * Execute_m_dispatch_reg_of_fu_is_not_empty: 0.255725
       * Writeback_bank_of_reg_is_not_idle: 0.004453
       * ReadOperands_bank_reg_belonged_to_was_allocated: 0.001145
       * ReadOperands_port_num_m_in_ports_m_in_fails_as_not_found_free_cu: 0.354071
       * Execute_icnt_injection_buffer_is_full: 0.000000

 - Compute Structural Stall Cycles Breakdown: 
       * Issue_out_has_no_free_slot: 6153.0
       * Issue_previous_issued_inst_exec_type_is_compute: 0.0
       * Execute_result_bus_has_no_slot_for_latency: 4.0
       * Execute_m_dispatch_reg_of_fu_is_not_empty: 5623.0
       * Writeback_bank_of_reg_is_not_idle: 518.0
       * ReadOperands_bank_reg_belonged_to_was_allocated: 927.0
       * ReadOperands_port_num_m_in_ports_m_in_fails_as_not_found_free_cu: 5240.0

 - Compute Structural Stall Cycles Breakdown Distribution: 
       * Issue_out_has_no_free_slot: 0.333225
       * Issue_previous_issued_inst_exec_type_is_compute: 0.000000
       * Execute_result_bus_has_no_slot_for_latency: 0.000217
       * Execute_m_dispatch_reg_of_fu_is_not_empty: 0.304522
       * Writeback_bank_of_reg_is_not_idle: 0.028053
       * ReadOperands_bank_reg_belonged_to_was_allocated: 0.050203
       * ReadOperands_port_num_m_in_ports_m_in_fails_as_not_found_free_cu: 0.283780

 - Memory Data Stall Cycles Breakdown: 
       * Issue_scoreboard: 3501.0
       * Execute_L1: 1337.0
       * Execute_L2: 95308.0
       * Execute_Main_Memory: 45181.0

 - Memory Data Stall Cycles Breakdown Distribution: 
       * Issue_scoreboard: 0.024090
       * Execute_L1: 0.009200
       * Execute_L2: 0.655818
       * Execute_Main_Memory: 0.310892

 - Compute Data Stall Cycles Breakdown: 
       * Issue_scoreboard: 899.0

 - Compute Data Stall Cycles Breakdown Distribution: 
       * Issue_scoreboard: 1.000000

 - Function Unit Execution Cycles Breakdown: 
       * SP_UNIT_execute_clks: 86027.0
       * SFU_UNIT_execute_clks: 50285.0
       * INT_UNIT_execute_clks: 765709.0
       * DP_UNIT_execute_clks: 82461.0
       * TENSOR_CORE_UNIT_execute_clks: 0.0
       * LDST_UNIT_execute_clks: 318340.0
       * SPEC_UNIT_1_execute_clks: 263957.0
       * SPEC_UNIT_2_execute_clks: 0.0
       * SPEC_UNIT_3_execute_clks: 0.0
       * Other_UNIT_execute_clks: 0.0

 - Function Unit Execution Cycles Breakdown Distribution: 
       * SP_UNIT_execute_clks: 0.054907
       * SFU_UNIT_execute_clks: 0.032095
       * INT_UNIT_execute_clks: 0.488715
       * DP_UNIT_execute_clks: 0.052631
       * TENSOR_CORE_UNIT_execute_clks: 0.000000
       * LDST_UNIT_execute_clks: 0.203181
       * SPEC_UNIT_1_execute_clks: 0.168471
       * SPEC_UNIT_2_execute_clks: 0.000000
       * SPEC_UNIT_3_execute_clks: 0.000000
       * Other_UNIT_execute_clks: 0.000000

 - Function Unit Execution Instns Number: 
       * SP_UNIT_Instns_num: 4004.0
       * SFU_UNIT_Instns_num: 736.0
       * INT_UNIT_Instns_num: 24267.0
       * DP_UNIT_Instns_num: 2177.0
       * TENSOR_CORE_UNIT_Instns_num: 0.0
       * LDST_UNIT_Instns_num: 3525.0
       * SPEC_UNIT_1_Instns_num: 3255.0
       * SPEC_UNIT_2_Instns_num: 0.0
       * SPEC_UNIT_3_Instns_num: 0.0
       * Other_UNIT_Instns_num: 0.0

 - Function Unit Execution Instns Number Distribution: 
       * SP_UNIT_Instns_num: 0.105468
       * SFU_UNIT_Instns_num: 0.019387
       * INT_UNIT_Instns_num: 0.639211
       * DP_UNIT_Instns_num: 0.057344
       * TENSOR_CORE_UNIT_Instns_num: 0.000000
       * LDST_UNIT_Instns_num: 0.092851
       * SPEC_UNIT_1_Instns_num: 0.085739
       * SPEC_UNIT_2_Instns_num: 0.000000
       * SPEC_UNIT_3_Instns_num: 0.000000
       * Other_UNIT_Instns_num: 0.000000

 - Function Unit Execution Average Cycles Per Instn : 
       * SP_UNIT_average_cycles_per_instn: 21.485265
       * SFU_UNIT_average_cycles_per_instn: 68.322011
       * INT_UNIT_average_cycles_per_instn: 31.553509
       * DP_UNIT_average_cycles_per_instn: 37.878273
       * TENSOR_CORE_UNIT_average_cycles_per_instn: 0.000000
       * LDST_UNIT_average_cycles_per_instn: 90.309220
       * SPEC_UNIT_1_average_cycles_per_instn: 81.092780
       * SPEC_UNIT_2_average_cycles_per_instn: 0.000000
       * SPEC_UNIT_3_average_cycles_per_instn: 0.000000
       * Other_UNIT_average_cycles_per_instn: 0.000000

 - Report Time: 2024-04-13 18:12:11

```


## Docker

We are creating a docker image that will be released once AE is complete. 
You can preview it from [Zenodo](https://zenodo.org/records/13150677) 
and the docker image is called `micro57.tar.gz`.
