# Introduction

vAttention is a memory manager for KV-cache in LLM serving systems. It decouples the allocation of virtual memory and physical memory using the [CUDA virtual memory APIs](https://docs.nvidia.com/cuda/cuda-driver-api/group__CUDA__VA.html). This approach enables allocating physical memory on demand while retaining the contiguity of KV-cache in virtual memory. This way, vAttention provides support for dynamic memory allocation to unmodified attention kernels. This way of memory management is different from the popular [PagedAttention](https://blog.vllm.ai/2023/06/20/vllm.html) approach; PagedAttention implements demand paging in user space and requires rewriting custom kernels to support dynamic memory allocation. vAttention also improves performance over PagedAttention in many cases, especially for prefill-bound workloads. Please checkout our [paper](https://arxiv.org/abs/2405.04437) for more details.


# Content

This repository contains an implementation of vAttention, intergrated with an LLM serving system Sarathi-Serve that was published in OSDI'24 ([paper](https://www.usenix.org/conference/osdi24/presentation/agrawal), [code](https://github.com/microsoft/sarathi-serve)). The content is organized as follows:

 * `vattention` contains the source code of vattention memory allocator
 * `sarathi-lean` modified version of Sarathi-Serve with support for both PagedAttention and vAttention style of memory management
 * `scripts` contains scripts to run the experiments
 * `nvidia-vattn-uvm-driver` contains our modified version of the NVIDIA UVM drivers
 * `microbenchmarks` contains scripts to run some useful microbenchmarks


# Installation and Dependencies

Using this repo requires **PyTorch 2.3.0** and **CUDA 12.1** (or later but other CUDA versions may or may not work). We have tested vAttention with the Linux kernel, **A100 GPUs** and **python 3.10** but expect it to work on other Linux-based systems as long as they are running the specified CUDA and PyTorch versions.

To install vAttention and Sarathi-Serve, create a conda environment as follows:

```sh
conda create -n vattn python=3.10
conda activate vattn
```

Now, download and extract libtorch first (this is required to build the vattention memory allocator), and then build sarathi-serve and vattention as follows:

```sh
# the libtorch version has to match with the torch version, and we have tested only v2.3.0
wget https://download.pytorch.org/libtorch/cu121/libtorch-shared-with-deps-2.3.0%2Bcu121.zip
unzip libtorch-shared-with-deps-2.3.0+cu121.zip

# build sarathi-serve
cd sarathi-lean/
pip install -e . --extra-index-url https://flashinfer.ai/whl/cu121/torch2.3/
cd ../

# build vattention
cd vattention/
LIBTORCH_PATH=<path to libtorch dir> python setup.py install
cd ../
```
# Running Benchmarks

The repo provides a benchmark-runner which can be used to run different workloads (dynamic/static, datasets/synthetic) with various attention-backends and schedulers. The benchmark-runner provides a comprehensive list of configuration knobs listed in [default.yml](sarathi-lean/sarathi/benchmark/config/default.yml). Please check [Sarathi-Serve](sarathi-lean/sarathi/benchmark/README.md) for a detailed explanation of the knobs.

This repository includes two customizable benchmark scripts:

* [benchmark_e2e_dynamic_trace.py](scripts/benchmark_e2e_dynamic_trace.py): This script runs expriments on a dynamic trace. It runs 256 requests from the **_arxive dataset_** for qps of 0.4, 0.8, 1, 2, 4 and 6 where requests arrive as per the poisson distribution.
* [benchmark_e2e_static_trace.py](scripts/benchmark_e2e_static_trace.py): This script runs experiments on a static trace and can be used to reproduce the makespan results of our paper. It runs 50 requests for context length 32k, 64k and 128k and prefill to decode ratios of 500, 100 and 50.

```sh
# testing the setup:
python scripts/benchmark_e2e_static_trace.py --test
or 
python scripts/benchmark_e2e_dynamic_trace.py --test

# run benchmarks for performance evaluation:
python scripts/benchmark_e2e_static_trace.py
or
python scripts/benchmark_e2e_dynamic_trace.py
```

Benchmark results are redirected to `experiments/e2e_static_eval` or `experiments/e2e_dynamic_eval`. Model configurations can be found in `scripts/utils.py` (all Yi and Llama family of models are expected to work). Parse benchmark results as follows:

```sh
python scripts/process_e2e_static.py
or
python scripts/process_e2e_dynamic.py
```


### Configuring attention backends

We have modified Sarathi-Serve to support [FlashAttention]((https://github.com/Dao-AILab/flash-attention)) and [FlashInfer](https://github.com/flashinfer-ai/flashinfer) backends for attention computation.

* [vattention_flashattention_wrapper.py](sarathi-lean/sarathi/model_executor/attention/vattention_flashattention_wrapper.py) This backend uses FlashAttention's `flash_attn_with_kvcache` API for both prefill and decode attention computation.
* [vattention_flashinfer_wrapper.py](sarathi-lean/sarathi/model_executor/attention/vattention_flashinfer_wrapper.py) This experimental backend demonstrates the portability of vAttention approach. It uses FlashInfer's `flashinfer.prefill.single_prefill_with_kv_cache` API for (non-paged) prefill and FlashAttention's `flash_attn_with_kvcache` API for (non-paged) decode.


The backends can be configured by updating the `attention_backends` list in our scripts. We currently support `fa_paged_[block_size]`, `fi_paged_[block_size]`, `fa_vattn_[page_size]`, `fi_vattn_[page_size]`, `fa_vattn_[page_size]_sync`, `fi_vattn_[page_size]_sync` where `fa` denotes FlashAttention (we tested v2.5.9) and `fi` denotes FlashInfer (we tested v0.0.6). We recommend using block size 256 for FlashAttention and 16 for FlashInfer because we have observed them performing best with these block sizes. vAttention supports 64KB, 128KB, 256KB and 2MB page sizes (example knobs: `fa_vattn_256kb`, `fi_vattn_2mb_sync`). Using suffix `_sync` in vAttention knob disables our optimization of overlapping memory allocation with compute which may be useful for benchmarking. We recommend using vAttention with asynchronous memory allocation i.e., without the `_sync` suffix.


### Using smaller page sizes

NVIDIA CUDA drivers allocate memory only at the granularity of large pages (2MB or above). If you want to use vAttention with smaller page sizes of 64KB, 128KB or 256KB, please follow the [README.md](./nvidia-vattn-uvm-driver/README.md) to replace the default CUDA UVM driver with our custom driver (check `nvidia-vattn-uvm-driver`).

**NOTE:** Replacing CUDA drivers is not required if you want to use vAttention with only 2MB pages.

# OpenAI Compatible API

We also provide an OpenAI compatible API to facilitate benchmarking. An endpoint such as this one can be used with LLM benchmarking tools like [metron](https://github.com/project-metron/metron/tree/main?tab=readme-ov-file).
Start the server as follows:

```sh
cd sarathi-lean/
python -m sarathi.entrypoints.openai_server.api_server [COMMAND LINE ARGUMENTS]

# for example, run Yi-6B on a single GPU with fa_paged attention backend
python -m sarathi.entrypoints.openai_server.api_server --model_name 01-ai/Yi-6B-200k --model_tensor_parallel_degree 1 --model_attention_backend fa_paged --model_block_size 256
# or, run Llama-3-8B on two GPUs with fa_vattn attention backend using 2MB pages
python -m sarathi.entrypoints.openai_server.api_server --model_name meta-llama/Meta-Llama-3-8B --model_tensor_parallel_degree 2  --model_attention_backend fa_vattn --model_block_size 2097152
```
Just like the benchmark runner, you can configure many other knobs listed here: [default.yml](sarathi-lean/sarathi/benchmark/config/default.yml). Once the serve is up and running, you can use metron to benchmark performance as follows:

```sh
# Export API Key and URL
export OPENAI_API_KEY=secret_abcdefg
export OPENAI_API_BASE=http://localhost:8000/v1

# running a static trace
 python -m metron.run_benchmark \
--model "01-ai/Yi-6B-200k" \
--max-num-completed-requests 150 \
--timeout 600 \
--num-ray-clients 2 \
--num-concurrent-requests-per-client 5 \
--output-dir "experiments" \
--request-interval-generator-provider "static" \
--request-length-generator-provider "fixed" \
--fixed-request-generator-prefill-tokens 65536 \ 
--fixed-request-generator-decode-tokens 128 \
--request-generator-max-tokens 65536 \

# running a dynamic trace
python -m metron.run_benchmark \
--model "01-ai/Yi-6B-200k" \
--max-num-completed-requests 150 \
--timeout 600 \
--num-ray-clients 2 \
--num-concurrent-requests-per-client 5 \
--output-dir "experiments" \
--request-interval-generator-provider "poisson" \
--poisson-request-interval-generator-qps 0.5 \
--request-length-generator-provider "trace" \
--trace-request-length-generator-trace-file "sarathi-lean/data/processed_traces/arxiv_summarization_filtered_stats_llama2_tokenizer.csv" \
--request-generator-max-tokens 8192 \
```

The results would be redirected to `experiments` directory. You can learn more about customising the benchmarks you run here: [project metron](https://project-metron.readthedocs.io/en/latest/).


# Using vAttention APIs for memory management in LLM serving

vAttention exports a set of simple APIs that a serving system can use for KV-cache related memory management. We choose Sarathi-Serve to exemplify this because Sarathi-Serve is a state-of-the-art LLM inference scheduler, has an elaborate metric store and a versatile benchmark_runner that makes running traces and performing experiments easy. Furthermore, its modular setup makes it easy to add more attention backends. Our core APIs are used as follows in Sarathi-Serve:

- [vATTN_cache_engine.py](sarathi-lean/sarathi/worker/cache_engine/vATTN_cache_engine.py): The `vATTNCacheEngine` class initializes and manages some aspects of KV-cache in python land e.g., mapping the sequence id of a request to its batch index in the KV-cache, and the current context length of the each request (like `vLLMCacheEngine`). vAttention memory allocator is initialized as follows:

    ```sh
    vattention.init_kvcache(
        self.num_layers,
        self.num_heads,
        self.head_size,
        self.max_batch_size,
        self.max_model_seq_len,
        self.device_idx,
        self.dtype,
        self.page_size
        )
    ```

    which returns **virtual** PyTorch tensors without any physical memory mapped underneath. The serving system can also reserve physical memory for KV-cache ahead-of-time as follows:

    ```sh
    vattention.reserve_physical_pages(cache_config.memory_for_gpu)
    ```

    which pre-allocates physical memory pages on the GPU. These pages are then attached to the virtual tensors at runtime.
    
    When a request is scheduled for the first time, `vATTNCacheEngine` calls the vattention memory allocator's `alloc_new_batch_idx` to get its batch index which determines the request's KV-cache offset within the virtual tensors.

- [base_worker.py](sarathi-lean/sarathi/worker/base_worker.py): Before the model forward pass, the worker calls

    ```sh
        # asynchronous memory allocation
        vattention.step_async(self.curr_seq_lens)
        or
        # synchronous memory allocation
        vattention.step(self.curr_seq_lens)
    ```

    which allocates physical memory pages for the active requests, based on their requirement. After the forward pass, the worker calls

    ```sh
        vattention.free_batch_idx(batch_idx)
    ```

    on request ids which have been completed. vAttention can reclaim these pages as and when required.


And that is most of it.

## Citation

If you use our work, please consider citing our paper:

```
@misc{prabhu2024vattention,
      title={vAttention: Dynamic Memory Management for Serving LLMs without PagedAttention},
      author={Ramya Prabhu and Ajay Nayak and Jayashree Mohan and Ramachandran Ramjee and Ashish Panwar},
      year={2024},
      url={https://arxiv.org/abs/2405.04437},
}
```

## Acknowledgment

This repository originally started as a fork of [Sarathi-Serve](https://github.com/microsoft/sarathi-serve) which in turn is a fork of the [vLLM project](https://vllm-project.github.io/). vAttention and Sarathi-Serve are research prototypes and do not have complete feature parity with open-source vLLM. We have only retained the most critical features and adopted the codebase for faster research iterations.
