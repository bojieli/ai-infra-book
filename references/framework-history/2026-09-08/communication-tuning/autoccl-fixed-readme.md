## Prepare the docker
```
docker pull nvcr.io/nvidia/pytorch:23.08-py3
```

## Download source code
```
git clone --recursive https://github.com/gbxu/autoccl.git
```

## To build the library :

```shell
cd autoccl
make -j src.build
```

If CUDA is not installed in the default /usr/local/cuda path, you can define the CUDA path with :

```shell
make src.build CUDA_HOME=<path to cuda install>
```

AutoCCL will be compiled and installed in `build/` unless `BUILDDIR` is set.

By default, AutoCCL is compiled for all supported architectures. To accelerate the compilation and reduce the binary size, consider redefining `NVCC_GENCODE` (defined in `makefiles/common.mk`) to only include the architecture of the target platform :
```shell
$ make -j src.build NVCC_GENCODE="-gencode=arch=compute_70,code=sm_70"
```

## Build AutoCCL Tuner
```shell
$ cd ext-tuner/example && make clean && make
```

## Use AutoCCL
We assume that in a distributed scenario, each CPU process is responsible for managing a GPU.

* Preload runtime and tuner to bypass Tccl on the system
```sh
# Setting environment variables on each process
export LD_PRELOAD=path/to/autoccl/build/lib/libnccl.so
export LD_LIBRARY_PATH=path/to/autoccl/build/lib:path/to/autoccl/ext-tuner/example/build/:$LD_LIBRARY_PATH
export NCCL_TUNER_PLUGIN=path/to/autoccl/ext-tuner/example/build/libnccl-plugin.so
```

* Specify the ip and port of the monitoring process
```sh
# Setting environment variables on each process
export TUNER_COORDINATOR="coordinator_node_ip:port"
export TUNER_WORLDSIZE="YOUR_COMM_GROUP_SIZE"
```

* Specify a process on the coordinator node to create an additional thread to act as a coordinator responsible for listening to the coordinator_node_ip:port.
```sh
# Setting environment variables only on a certain process
export TUNER_ROLE="COORDINATOR"
```

## Example
see  `autoccl/ext-tuner/example/example/cuda/pytorch/run.sh`


## Citation
If you use autoccl in a scientific publication, we encourage you to add the following reference to the related papers:
```
@inproceedings {xu2025autoccl,
    author = {Guanbin Xu and Zhihao Le and Yinhe Chen and Zhiqi Lin and Zewen Jin and Youshan Miao and Cheng Li},
    title = {{AutoCCL}: Automated Collective Communication Tuning for Accelerating Distributed and Parallel {DNN} Training},
    booktitle = {22nd USENIX Symposium on Networked Systems Design and Implementation (NSDI 25)},
    year = {2025},
    isbn = {978-1-939133-46-5},
    address = {Philadelphia, PA},
    pages = {667--683},
    url = {https://www.usenix.org/conference/nsdi25/presentation/xu-guanbin},
    publisher = {USENIX Association},
    month = apr
}
```
