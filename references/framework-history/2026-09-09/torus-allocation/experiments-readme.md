# iPronics Port mapping

## Server port to iPronics port binding

```
Server 0:
    TX: 12, RX: 18
    TX: 20, RX: 36
Server 1:
    TX: 5, RX: 9
    TX: 37, RX: 6
Server 2:
    TX: 2, RX: 17
    TX: 1, RX: 0
Server 3:
    TX: 7, RX: 13
    TX: 35, RX: 34
```

## Installation and Environment Setup
- Init communication environment on servers
    ```
    conda create --name nccl python=3.9
    conda activate nccl
    conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
    conda install -c conda-forge openmpi mpi4py
    conda install -c nvidia nccl
    conda install nvidia/label/cuda-12.1.0::cuda-nvcc
    ```
<!-- [optional] conda install gcc libstdcxx-ng -->
- Set environment variables
    ```
    export PATH=$CONDA_PREFIX/bin:$PATH
    export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
    export OMPI_MCA_opal_cuda_support=true # enable MPI cuda awareness
    export UCX_MEMTYPE_CACHE=n
    ```
- Test environment
    ```
    python ml/env.py
    nvcc --version
    ```

- Run net_config
    - Set up IP address for iPronics interface
    - Share ssh key to enable keyless ssh

- Build `nccl-tests` and test

    ```
    cd nccl-tests # Assume already installed
    make MPI=1 NCCL_HOME=~/miniconda3/envs/nccl_env/nccl  CUDA_HOME=~/miniconda3/envs/nccl MPI_HOME=~/miniconda3/envs/nccl
    mpirun --host localhost --np 1 -N 1 --mca plm_base_verbose 10 ./build/all_reduce_perf -b 8 -e 8G -f 2 -g 1
    cd ..
    ```

## Configure Circuits and Perform Collectives on Multiple Machines
- Login iPronics server, start server process   
    `python ipronics_server.py`
- From manager server, start client process
    `python ipronics_client.py`
- Login to one GPU server which serve as master, create hostfile
- Run NCCL allreduce

    `mpirun --hostfile ./hostfile --np 2 ./nccl-tests/build/all_reduce_perf -b 8 -e 128M -f 2 -g 1
    `

## Training

- Training Resnet

    ```
    # MPI
    echo "source /home/$USER/miniconda3/bin/activate nccl
    python ./ml/train_resnet.py" > ./ml/run
    
    mpirun -np 2 --mca plm_base_verbose 10  --hostfile ./hostfile -x NCCL_DEBUG=INFO -x MASTER_ADDR=<master_ip> -x MASTER_PORT=12345 bash ./ml/run
    ```

- Training LLM
    
    ```
    echo "source /home/$USER/miniconda3/bin/activate nccl
    python ./ml/train_llama3.py" > ./ml/run

    mpirun -np 2 --mca plm_base_verbose 10 --hostfile ./hostfile -x NCCL_DEBUG=INFO -x MASTER_ADDR=<master_ip> -x MASTER_PORT=12345   bash ./ml/run
    ```

# Cleanup
- Stop server process on iPronics
- Clean up GPU server ports 
    `net_config -d <eth> <ip>`

