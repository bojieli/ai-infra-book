# Efficient Remote Memory Ordering

Code for the paper "[Efficient Remote Memory Ordering for Non-Coherent Interconnects](https://dl.acm.org/doi/abs/10.1145/3779212.3790156)" presented in ASPLOS 2026.

## gem5 Simulation

The files for gem5 simulation can be found in the gem5 directory. 
The files are obtained from version 24.1 of gem5.

Requirements for gem5:

* gcc version >= 10
* Clang 7 to 16
* SCons 3.0 or greater
* Python 3.6+
* protobuf 2.1+

Python requirements for plotting results:

* NumPy
* Matplotlib

Scripts for running the gem5 simulations can be found in the directory `gem5-scripts`.

Instructions for reproducing the figures from gem5 simulation:

1. Enter the gem5 script directory: `cd gem5-scripts`
2. Run the script to set up and build gem5 (some interaction needed): `./setup-gem5.bash`
3. Run the script to generate input files: `./setup-benchmarks.bash`
4. Run the script to run all simulations: `./run-gem5.bash`
5. Set the python command in line 3 of `plot-gem5.bash` (default is `python3`)
6. Run the script to plot all simulation results: `./plot-gem5.bash`

Plots can be found in the directory `gem5-scripts/plots`. 

Running simulations for individual figures can be done by entering the directory `gem5/experiment-scripts` and executing the required bash scripts. 
This should be done at step 4. 

## CACTI

Scripts for building and running CACTI can be found in the directory `cacti-scripts`. 

Instructions for obtaining the CACTI results:

1. `git submodule init`
2. `git submodule update`
3. Enter the CACTI script directory: `cd cacti-scripts`
4. Build CACTI: `./build_cacti.bash`
5. Run CACTI: `./run_cacti.bash`

Results can be found in the directory `cacti-scripts/results`.

## Using Docker (for gem5 simulation and CACTI)

We tested this repository in the Docker container created from the Dockerfile. 
Instructions for setting up the Docker container 
(depending on how Docker is set up on your system, sudo permissions might be required):

1. Build the Docker image: `docker build -t test-image .`
2. Create the Docker container and run in interactive mode: `docker run -it --name test-container test-image /bin/bash`
3. Clone this repository into the Docker container: `git clone https://github.com/icsa-caps/efficient-remote-memory-ordering.git efficient-remote-memory-ordering`
4. Enter the directory of the repository: `cd efficient-remote-memory-ordering`

Refer to the sections on [gem5 Simulation](#gem5-simulation) and [CACTI](#cacti) for instructions on running the gem5 simulation and CACTI respectively. 

Copying the results and plots out of the Docker container:

1. Detach from the running container: Use the keys `Ctrl` + `p` then `Ctrl` + `q`
2. Copy the plots out of the running container: `docker container cp test-container:/top/efficient-remote-memory-ordering/gem5-scripts/plots .`

If the CACTI results need to be copied out of the container instead of the gem5 simulation plots, run 
`docker container cp test-container:/top/efficient-remote-memory-ordering/cacti-scripts/results .` instead of the command in step 2. 

Instructions for deleting the Docker container and image:

1. Kill the running container: `docker container kill test-container`
2. Remove the container: `docker container rm test-container`
3. Remove the image: `docker rmi test-image`

## Benchmarks and Emulation ##

These experiments require two Cloudlab machines of type `sm110p` with Ubuntu 22.04 — one acting as a client and the other as a server.

Set up both machines by running the following commands to install necessary packages and the OFED library:
```bash
bash benchmarks/scripts/setup.sh ofed
reboot
bash benchmarks/scripts/setup.sh setup
```

On both the client and server machines, build the RDMA benchmarks:
```bash
cd benchmarks/rdma
make
```

> **Note:** Replace `SERVER_IP` and `CLIENT_IP` in the commands below with the actual IP addresses of your machines. The examples use `10.10.1.2` for the server and `10.10.1.1` for the client.

### Cost of DMA Ordering (Figure-2) ###

This benchmark measures the cost of DMA ordering.

On the **server** machine, start the server:
```bash
./benchmarks/rdma/rdma_server 128 1
```

On the **client** machine, collect results and generate the plot:
```bash
SERVER_IP=10.10.1.2 PORT=20079 CPU=0 bash benchmarks/scripts/run_write_lat_bench.sh
```

Generated plot: `benchmarks/rdma/results/write_lat_cdf.pdf`

### RDMA READ/WRITE Throughput (Figure-3) ###

This benchmark measures throughput for RDMA READ and WRITE operations across varying queue pair counts.

On the **server** machine, start the server:
```bash
./benchmarks/rdma/rdma_server 128 1
```

On the **client** machine, collect results and generate the plot:
```bash
SERVER_IP=10.10.1.2 PORT=20079 bash benchmarks/scripts/run_rdma_bench.sh
```

Generated plot: `benchmarks/rdma/results/rdma_read_write_qp.pdf`

### MMIO Write Bandwidth (Figure-4) ###

This benchmark measures the bandwidth of write-combining MMIO writes with or without sfence instructions.

This experiment can be run on a single machine. The paper uses a Cloudlab machine of type `r6525` with Ubuntu 22.04.

Run the experiment:
```bash
bash benchmarks/scripts/run_mmio_bench.sh
```

Generated plot: `benchmarks/mmio/results/mmio_bench.pdf`

### RDMA Key-Value Store Emulation (Figure-7) ###

The experiment script assumes that the client and server machines share a common network-attached directory (as available on Cloudlab).
For this experiment, the paper uses two Cloudlab machines of type `sm110p` with Ubuntu 22.04.

Build the benchmark (run once on either machine):
```bash
git submodule update --init --recursive
bash benchmarks/RDMA_synchronization/scripts/install.sh build
```

Set up hugepages on **both** the client and server machines:
```bash
bash benchmarks/RDMA_synchronization/scripts/install.sh hugepages
```

Ensure the server machine can SSH into the client machine. Then run the experiment script on the **server** machine:
```bash
SERVER_IP=10.10.1.2 CLIENT_IP=10.10.1.1 bash benchmarks/RDMA_synchronization/scripts/run_exp.sh
```

Generated plot: `benchmarks/RDMA_synchronization/scripts/results/rdma_kvs.pdf`
