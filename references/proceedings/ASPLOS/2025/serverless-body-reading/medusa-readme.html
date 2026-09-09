# Medusa: Accelerating Serverless LLM Inference with Materialization

This repository contains the source code and scripts for reproducing the experimental results of Medusa (ASPLOS'25). Medusa aims to reduce the cold-start latency of serverless LLM inference through state materialization.

This is the main repository providing the LLM inference service, built on top of [vLLM](https://github.com/vllm-project/vllm), a popular framework for LLM inference. It also depends on several other components, including PyTorch and SPDK. We also release these components as described in the Getting Started guide.

Most of our engineering efforts have focused on saving and recovering the CUDA Graph, which is crucial for improving the performance of LLM inference while also impacting cold-start latency. We have navigated significant challenges with closed-source CUDA APIs and GPU-accelerated libraries like cuBLAS. This part of codes can be found in our modified version of [PyTorch-Medusa](https://github.com/ShaoxunZeng/PyTorch-Medusa).

For more details, please refer to our paper: [ASPLOS'25] Medusa: Accelerating Serverless LLM Inference with Materialization.
We will release our paper after it is cemera-ready.

## System Requirements

1. CUDA Version: 12.4, Driver Version: 550.54.14 (!Important! Different versions could result in the different kernel implementation in cuBLAS.)
2. Conda and python environments would be created by given dependencies, see below.
3. 4 Optane P5800X SSDs to reproduce the results, and other disks with SPDK supporting could work.

## Getting Started

| Switch to root (required by SPDK).

<details>
<summary>Create Conda Environments (Skip, already done in AE server)</summary>

create conda envs
```jsx
# conda env create --name newenv --file myenv.yml
source /home/zsx/anaconda3/etc/profile.d/conda.sh ;  conda activate serverless
```
  <details>
  <summary>myenv.yml</summary>

      name: serverless
      channels:
        - conda-forge
        - defaults
      dependencies:
        - _libgcc_mutex=0.1=main
        - _openmp_mutex=5.1=1_gnu
        - bzip2=1.0.8=h5eee18b_6
        - c-ares=1.19.1=h5eee18b_0
        - ca-certificates=2024.3.11=h06a4308_0
        - cmake=3.26.4=h96355d8_0
        - expat=2.6.2=h6a678d5_0
        - intel-openmp=2023.1.0=hdb19cb5_46306
        - krb5=1.20.1=h143b758_1
        - ld_impl_linux-64=2.38=h1181459_1
        - libcurl=8.7.1=h251f7ec_0
        - libedit=3.1.20230828=h5eee18b_0
        - libev=4.33=h7f8727e_1
        - libffi=3.4.4=h6a678d5_1
        - libgcc-ng=11.2.0=h1234567_1
        - libgomp=11.2.0=h1234567_1
        - libnghttp2=1.57.0=h2d74bed_0
        - libssh2=1.11.0=h251f7ec_0
        - libstdcxx-ng=12.3.0=hc0a3c3a_7
        - libuv=1.44.2=h5eee18b_0
        - lz4-c=1.9.4=h6a678d5_1
        - mkl=2023.1.0=h213fc3f_46344
        - mkl-include=2023.1.0=h06a4308_46344
        - ncurses=6.4=h6a678d5_0
        - ninja-base=1.10.2=hd09550d_5
        - openssl=3.0.13=h7f8727e_2
        - pip=24.0=py39h06a4308_0
        - python=3.9.19=h955ad1f_1
        - readline=8.2=h5eee18b_0
        - rhash=1.4.3=hdbd6064_0
        - setuptools=69.5.1=py39h06a4308_0
        - sqlite=3.45.3=h5eee18b_0
        - tbb=2021.8.0=hdb19cb5_0
        - tk=8.6.14=h39e8969_0
        - wheel=0.43.0=py39h06a4308_0
        - xz=5.4.6=h5eee18b_1
        - zlib=1.2.13=h5eee18b_1
        - zstd=1.5.5=hc292b87_2
        - pip:
            - aioprometheus==23.12.0
            - aiosignal==1.3.1
            - annotated-types==0.7.0
            - anyio==3.7.1
            - astunparse==1.6.3
            - attrs==23.2.0
            - certifi==2024.2.2
            - charset-normalizer==3.3.2
            - clean==0.1.4
            - click==8.1.7
            - contourpy==1.3.0
            - cupy-cuda12x==12.1.0
            - cycler==0.12.1
            - dnspython==2.6.1
            - email-validator==2.1.1
            - exceptiongroup==1.2.1
            - expecttest==0.2.1
            - fastapi==0.111.0
            - fastapi-cli==0.0.4
            - fastrlock==0.8.2
            - filelock==3.14.0
            - fonttools==4.54.1
            - frozenlist==1.4.1
            - fsspec==2024.5.0
            - h11==0.12.0
            - httpcore==0.13.7
            - httptools==0.6.1
            - httpx==1.0.0b0
            - huggingface-hub==0.23.2
            - hypothesis==6.102.6
            - idna==3.7
            - importlib-resources==6.4.5
            - jinja2==3.1.4
            - jsonschema==4.22.0
            - jsonschema-specifications==2023.12.1
            - kiwisolver==1.4.7
            - markdown-it-py==3.0.0
            - markupsafe==2.1.5
            - matplotlib==3.9.2
            - mdurl==0.1.2
            - mpmath==1.3.0
            - msgpack==1.1.0rc1
            - networkx==3.2.1
            - ninja==1.11.1.1
            - numpy==1.26.4
            - optree==0.11.0
            - orjson==3.10.3
            - packaging==24.0
            - pandas==2.2.2
            - pillow==10.4.0
            - protobuf==5.27.0
            - psutil==5.9.8
            - pydantic==2.7.1
            - pydantic-core==2.18.2
            - pygments==2.18.0
            - pyinstrument==4.6.2
            - pynvml==11.5.0
            - pyparsing==3.1.4
            - python-dateutil==2.9.0.post0
            - python-dotenv==1.0.1
            - python-multipart==0.0.9
            - pytz==2024.1
            - pyyaml==6.0.1
            - ray==2.23.0
            - referencing==0.35.1
            - regex==2024.5.15
            - requests==2.32.2
            - rfc3986==1.5.0
            - rich==13.7.1
            - rpds-py==0.18.1
            - safetensors==0.4.3
            - sentencepiece==0.2.0
            - shellingham==1.5.4
            - six==1.16.0
            - sniffio==1.3.1
            - sortedcontainers==2.4.0
            - starlette==0.37.2
            - sympy==1.12
            - tokenizers==0.19.1
            - tqdm==4.66.4
            - transformers==4.41.1
            - triton==2.3.1
            - typer==0.12.3
            - types-dataclasses==0.6.6
            - typing-extensions==4.12.0
            - tzdata==2024.1
            - ujson==5.10.0
            - urllib3==2.2.1
            - uvicorn==0.29.0
            - uvloop==0.19.0
            - watchfiles==0.22.0
            - websockets==12.0
            - zipp==3.20.2
      prefix: /home/zsx/anaconda3/envs/serverless
      ```
  </details>  
</details>    

<details>
<summary>Compile (Skip, already done in AE server)</summary>

| Please clone all repositories under `/home/zsx/`

```jsx
export CUDA_HOME=/usr/local/cuda-12.4/
export LD_LIBRARY_PATH=/usr/local/cuda-12.4/lib64:/home/zsx/spdk/build/lib:$LD_LIBRARY_PATH
export PATH=/usr/local/cuda-12.4/bin/:$PATH
export C_INCLUDE_PATH=/home/zsx/spdk/build/include:/home/zsx/spdk/dpdk/build/include:$C_INCLUDE_PATH
export CPLUS_INCLUDE_PATH=/home/zsx/spdk/build/include:/home/zsx/spdk/dpdk/build/include:$CPLUS_INCLUDE_PATH
```

<details>
<summary>Compile PyTorch</summary>

```jsx
git clone git@github.com:ShaoxunZeng/PyTorch-Medusa.git PyTorch
git submodule update --init --recursive
```

```jsx
# cudnn is not tested, uninstall cudnn and then compile; or export envs to not compile with cudnn
conda install cmake ninja
pip install -r requirements.txt

conda install mkl mkl-include
conda install -c conda-forge libstdcxx-ng=12

pip uninstall torch
python setup.py clean

export _GLIBCXX_USE_CXX11_ABI=1
export CMAKE_PREFIX_PATH=${CONDA_PREFIX:-"/home/zsx/anaconda3/"}
CC=`which gcc-9` CXX=`which g++-9` CXXFLAGS='-Wno-maybe-uninitialized -Wno-uninitialized -Wno-free-nonheap-object -Wno-nonnull -I/usr/local/cuda-12.4/include -std=c++17' CFLAGS='-Wno-maybe-uninitialized -Wno-uninitialized -Wno-free-nonheap-object -Wno-nonnull -I/usr/local/cuda-12.4/include' USE_ROCM=0 TORCH_CUDA_ARCH_LIST="8.0;8.6" REL_WITH_DEB_INFO=1 USE_CUDA=1 MAX_JOBS=32 python setup.py develop
```

</details>

<details>
<summary>Compile SPDK</summary>

```jsx
git clone git@github.com:ShaoxunZeng/SPDK-Medusa.git spdk
git submodule update --init
```

```jsx
./configure --with-shared
make -j
make install
```
</details>

<details>
<summary>Compile xformers</summary>

```jsx
git clone https://github.com/facebookresearch/xformers.git
git checkout 042abc8aa47d1f5bcc2e82df041811de218924ba
git submodule update --init --recursive
pip install ninja
# Set TORCH_CUDA_ARCH_LIST if running and building on different GPU types
pip uninstall xformers
python setup.py clean
TORCH_CUDA_ARCH_LIST="8.0;8.6" MAX_JOBS=1 pip install -e .
```
</details>

<details>
<summary>Compile vLLM</summary>

```jsx
git clone git@github.com:thustorage/Medusa.git vllm
```

```jsx
pip install pyinstrument
```

```jsx
CC=`which gcc-9` CXX=`which g++-9` MAX_JOBS=32 python setup.py develop
```
</details>

<details>
<summary>Compile intercept lib</summary>

```jsx
/usr/bin/g++ -I/usr/local/cuda/include -fPIC -shared -o libmylib.so mylib.cpp -ldl -L/usr/local/cuda/lib64 -lcudart -lcuda 
```

</details>
</details>

<details>
<summary>Configure Environments (Skip, already done in AE server)</summary>

[Configure 1GB huge page](https://github.com/lagopus/lagopus/blob/master/docs/how-to-allocate-1gb-hugepages.md), which would affect the SPDK init time.

Add model names to `model_names` in `scripts/serverless_llm.py`.

Modify `model_offsets/xxx` to add the model offsets on the disks, which will be used as offsets for storing tensors in SPDK managed disks (`--save_tensor`).

Download model weights and move to `/home/zsx/raidfs-back/home/zsx/.cache/huggingface/hub/`, make sure the versions are correct.
Detailed versions and commit ids are described in `examples/llm_engine_example.py` (downloading from Huggingface).

</details>

<details>
<summary>Run Experiments</summary>

```jsx
cd /home/zsx/vllm # currently, this path is hard-coded in the script as the location of Medusa
```

Notice, we will kill python process multiple times during runing experiments.
GPU could be used by others, please run `pkill -9 python` and `pkill -9 python3` first.

All data and results could be found in backups, e.g., the expected results are in `results-backup`.

CUDA driver persistent mode to reduce latency.
```jsx
nvidia-smi -pm=1
```

```jsx
source /home/zsx/anaconda3/etc/profile.d/conda.sh ;  conda activate serverless
export CUDA_HOME=/usr/local/cuda-12.4/
export LD_LIBRARY_PATH=/usr/local/cuda-12.4/lib64:/home/zsx/spdk/build/lib:$LD_LIBRARY_PATH
export PATH=/usr/local/cuda-12.4/bin/:$PATH
export C_INCLUDE_PATH=/home/zsx/spdk/build/include:/home/zsx/spdk/dpdk/build/include:$C_INCLUDE_PATH
export CPLUS_INCLUDE_PATH=/home/zsx/spdk/build/include:/home/zsx/spdk/dpdk/build/include:$CPLUS_INCLUDE_PATH
```

SPDK setups huge pages.

```jsx
HUGENODE='nodes_hp[0]=48,nodes_hp[1]=48' /home/zsx/spdk/scripts/setup.sh 
```

Create directories for storing CUDA Graph and logs.

```jsx
./scripts/mktmpfs.sh 
```

Save tensors to SPDK managed disks.

```jsx
python scripts/serverless_llm.py --save_tensor 
```

Make sure PyTorch could print log information (needed when saving CUDA Graph): see `CUDACachingAllocator.h`, uncomment `#undef NDEBUG` and compile. (Skip, already done in AE server)


Save CUDA Graph.

```jsx
python scripts/serverless_llm.py --offline
```

Turn-off PyTorch's log in case it impacts performance. (Optional, just little slow down)


mkdir breakdowns

mkdir experiments

Figure2 & Figure7

```jsx
mkdir experiments/overall
python scripts/overall.py > results/Figure7
python scripts/breakdown.py > results/Figure2
```

Figure3

```jsx
mkdir experiments/cuda_graph
python scripts/cuda_graph.py > results/Figure3
```

Table1

```jsx
python scripts/calculations.py > results/Table1
```

Figure9 (Make sure PyTorch could print log information, see above)

```jsx
mkdir experiments/offline
python scripts/offline.py > results/Figure9
```

Figure10

```jsx
mkdir experiments/traces
mkdir experiments/traces/qps2
mkdir experiments/traces/qps10
python scripts/traces.py > results/Figure10
```

Figure11

```jsx
mkdir experiments/traces_throughput
python scripts/traces_throughput.py > results/Figure11
```

Figure8 and Figure1

```jsx
python scripts/breakdown_Qwen.py > results/Figure8_Figure1
```

</details>

## Citation

We will release our paper after it is cemera-ready.
