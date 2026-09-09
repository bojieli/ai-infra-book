<p align="center">
  <picture>
    <img alt="POD-Attention" src="https://github.com/user-attachments/assets/61c10fd0-66fe-4cd7-8790-97f50fe5f2ad" width=15%>
  </picture>
</p>

<h1 align="center">
POD-Attention: <br> Unlocking Full Prefill-Decode Overlap 
	For Faster LLM Inference
</h1>
This repository contains the source code and profiling scripts for POD-Attention. POD-Attention fuses prefill and decode attention kernels into a single optimized kernel that aims to saturate both GPU compute and memory simultaneously &mdash; critical for hybrid-batching-based LLM inference.
Two alternative versions are available of POD-Attention, built on top of either (1) FlashAttention v2.6.1 [this repo] or (2) default FlashInfer
(https://github.com/flashinfer-ai/flashinfer). POD-Attention has been integrated with Sarathi-Serve &mdash; a state-of-the-art hybrid-batching-based LLM inference scheduler. This repo contains the source code of POD-Attention, benchmarks for evaluation, and all scripts needed to replicate results reported in the paper.

Full details of our implementation can be found in our [paper](https://dl.acm.org/doi/10.1145/3676641.3715996):
<pre>
<b>POD-Attention: Unlocking Full Prefill-Decode Overlap for Faster LLM Inference</b>
Aditya K Kamath, Ramya Prabhu, Jayashree Mohan, Simon Peter, Ramachandran Ramjee, Ashish Panwar
<i>ACM 30th International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS), 2025</i>
DOI: https://doi.org/10.1145/3676641.3715996
</pre>

## Performance
![POD_attention_sweep](https://github.com/user-attachments/assets/f5d90c6f-4b73-435c-8be5-23dc3fbed7f1)
To examine POD-Attention's broad applicability in LLM inference, we evaluated over a thousand different hybrid-batch configurations, sweeping different context lengths, decode batch sizes, and LLM model configurations.
We also compared against existing GPU methodologies of combining complementary kernels (e.g., [CUDA streams](https://developer.nvidia.com/blog/gpu-pro-tip-cuda-7-streams-simplify-concurrency/)).
The above graph shows POD-Attention's speedup over the current approach of serially executing FlashAttention-2's prefill and decode kernels. 

POD-Attention outperforms this approach by up to <b>61% (average 33%)</b>.

<u>Legend</u>
* FA_Stream: Executes [FlashAttention-2](https://github.com/Dao-AILab/flash-attention) with prefill and decode in separate streams.   
* FI_Serial: Executes [FlashInfer](https://github.com/flashinfer-ai/flashinfer) prefill and decode in serial.   
* FI_Batched: Combines prefill and decode inputs and executes using a single FlashInfer kernel.   
* FA_HFuse: Employs [HFuse](https://github.com/aoli-al/HFuse) to create a merged kernel for prefill and decode.   
* POD (FI): Our POD-Attention implementation fusing FlashInfer's prefill and decode kernels ([available here](https://github.com/AKKamath/flashinfer/)).   
* POD (FA): Our POD-Attention implementation fusing FlashAttention-2's prefill and decode kernels (this repository).   

# Installation and dependencies
Minimum NVIDIA Ampere GPU is needed to run this code. We tested using an A100 GPU on an x86 machine running Ubuntu 22.04.

## Docker installation 
We provide a docker image for POD-Attention with all its dependencies pre-installed. To access the docker image, you need to have [Docker](https://docs.docker.com/engine/installation/) and [NVIDIA Docker](https://github.com/NVIDIA/nvidia-docker/) installed on your system. You can then launch the docker container and navigate to the folder containing the POD-Attention artifact, as follows:
```sh
$ docker run --gpus all -it \
  -p 8181:8181 --rm --ipc=host --cap-add=SYS_ADMIN \
  rnp1910/pod_attention:asplos_25_pytorch_run
$ cd /workspace/vattention/pod_attn  
```

## Manual installation
For manual installation, we can download POD-Attention to the home directory to install it. 
We use Anaconda to obtain the appropriate versions of CUDA, Python, and PyTorch. 
This can take up to 2 hours.
```sh
$ git clone \
  https://github.com/microsoft/vattention.git
$ cd vattention/pod_attn/
# Install miniconda; skip if already installed
$ make install_miniconda
$ bash # Refresh shell and activate
$ conda create --name pod_attn python=3.12
$ conda activate pod_attn
# Install CUDA Toolkit
(pod_attn)$ conda install -y -c \
  conda-forge cuda-toolkit=12.4.0
# Install dependencies
(pod_attn)$ pip install -r requirements.txt
# Install FlashInfer
(pod_attn)$ git clone https://github.com/AKKamath/flashinfer.git --recursive
(pod_attn)$ pushd flashinfer; pip install -e . -v; popd
# Install POD-Attention and vAttention
(pod_attn)$ make install_all
```

## Test configuration
The code has been tested with CUDA 12.4 and Python 3.9 on an A100 GPU.

# Running POD-Attention
We shall now look at how you can use POD-Attention in your framework, as well as how to replicate our paper results.

## API Usage
We expose a Python function that can be called to use POD with the function parameters shown below.
```python
import pod_attn
# POD function call
out_p, out_d = pod_attn.true_fused_attn_with_kvcache(
    q_p, k_cache_p, v_cache_p, q_d, k_cache_d, v_cache_d, k=None, v=None,
    rotary_cos=None, rotary_sin=None, cache_seqlens_p: Optional[Union[(int, torch.Tensor)]] = None,
    cache_seqlens_d: Optional[Union[(int, torch.Tensor)]] = None, cache_batch_idx: Optional[torch.Tensor] = None,
    softmax_scale=None, causal=False, window_size=(-1, -1), rotary_interleaved=True, fused_params=15)
"""
Arguments:
    q_p: (batch_size_p, seqlen_p, nheads, headdim). Prefill query tensor.
    k_cache_p: (batch_size_p, seqlen_kv_p, nheads_k, headdim). Prefill key tensor.
    v_cache_p: (batch_size_p, seqlen_kv_p, nheads_k, headdim). Prefill value tensor.
    q_d: (batch_size_d, 1, nheads, headdim). Decode query tensor.
    k_cache_d: (batch_size_d, seqlen_kv_d, nheads_k, headdim). Decode key tensor.
    v_cache_d: (batch_size_d, seqlen_kv_d, nheads_k, headdim). Decode value tensor.
    k [optional]: (batch_size_d, seqlen_new, nheads_k, headdim). If not None, we concatenate
            k with k_cache_d, starting at the indices specified by cache_seqlens_d.
    v [optional]: (batch_size_d, seqlen_new, nheads_k, headdim). Similar to k.
    rotary_cos [optional]: (seqlen_ro, rotary_dim / 2). If not None, we apply rotary embedding
            to k and q. Only applicable if k and v are passed in. rotary_dim must be divisible by 16.
    rotary_sin [optional]: (seqlen_ro, rotary_dim / 2). Similar to rotary_cos.
    cache_seqlens_p: int, or (batch_size,), dtype torch.int32. The sequence lengths of the
            prefill KV cache.
    cache_seqlens_d: int, or (batch_size,), dtype torch.int32. The sequence lengths of the
            decode KV cache.
    cache_batch_idx: (batch_size,), dtype torch.int32. The indices used to index into the decode KV cache.
            If None, we assume that the batch indices are [0, 1, 2, ..., batch_size - 1].
            If the indices are not distinct, and k and v are provided, the values updated in the cache
                 might come from any of the duplicate indices.
    softmax_scale: float. The scaling of QK^T before applying softmax.
            Default to 1 / sqrt(headdim).
    causal: bool. Whether to apply causal attention mask for prefill (decode cannot apply causal mask)
            (e.g., for auto-regressive modeling).
    window_size: (left, right). If not (-1, -1), implements sliding window local attention.
    rotary_interleaved: bool. Only applicable if rotary_cos and rotary_sin are passed in.
            If True, rotary embedding will combine dimensions 0 & 1, 2 & 3, etc. If False,
            rotary embedding will combine dimensions 0 & rotary_dim / 2, 1 & rotary_dim / 2 + 1
            (i.e. GPT-NeoX style).
    fused_params: int. Used to control POD-Attention configs. 9 = 2 CTAs per SM, 11 = 4 CTAs per SM, 
            15 = automatically choose best option based on input parameters.
Return:
    out_p: Prefill output (batch_size, seqlen, nheads, headdim)
    out_d: Decode output (batch_size, seqlen, nheads, headdim)
"""
```

## Replicating paper results

POD-Attention's API has been integrated into vAttention's fork of Sarathi-serve. You can run the associated backend by running sarathi-serve's benchmark runner with the attention backend `'FA_POD'` or `'FA_POD_MEGACACHE'`.

Our evaluation primarily contains two kinds of experiments, attention performance (Figures 1, 6, 10, 11, 13, 14) and end-to-end LLM performance (Figure 12 and Table 5). 
Figure 7 evaluates various kernel fusion strategies with a micro-benchmark. Most of these require only one GPU except for Table 5 and Figure 12 that require two GPUs. Use the Makefile present in the vattention/pod_attn/ folder to run experiments as follows:

```sh
make figure1  # 2 minutes; sudo used by script
make figure6  # 2 minutes
make figure7  # 2 minutes
make figure10 # 1 minute; sudo used by script
make figure11 # 2 hours
make figure12 # 9 hours
make figure13 # 1 minute
make figure14 # 1 minute
make table6 # 4 hours
```

## Expected results
The artifact scripts redirect the raw output numbers and logs to the output/ folder, while the plotted graphs can be found in the graphs/ folder. Tables are saved as CSVs in the same folder. Results may have minor runtime variations from those reported in in the paper, but general trends should hold.

# Folder contents
The various folders are as follows:
* csrc/cutlass/ contains required CUTLASS files.
* pod_attn/ contains the source code. The important files are:
	* pod_attn/fused_fwd_kernel.h --- Contains the GPU code. Specifically, "compute_fused_tb_attn" contains POD-Attention's SM-aware CTA scheduling code.
	* pod_attn/fused_fwd_launch_template.h --- Contains the code which launches the POD-Attention kernel. In this file, "run_true_fused_fwd" contains the actual kernel launch, while "run_true_fused_mha_fwd_hdim128" performs various parameter selection (prefill/decode tile size) for the launch.
	* pod_attn/fused_api.cpp --- Contains some preprocessing and parameter selection. Here, "mha_true_fused_fwd_kvcache" contains the code for limiting prefill splitting.
* tests/ contains tests used during evaluation of POD-Attention.

# Citation
If you use our work, please consider citing our paper:
```
@inproceedings {POD:ASPLOS:2025, 
	author = {Kamath, Aditya K and Prabhu, Ramya and Mohan, Jayashree and Peter, Simon and Ramjee, Ramachandran and Panwar, Ashish}, 
	title = {POD-Attention: Unlocking Full Prefill-Decode Overlap for Faster LLM Inference}, 
	year = {2025},
	publisher = {Association for Computing Machinery}, 
	address = {New York, NY, USA}, 
	url = {https://doi.org/10.1145/3676641.3715996}, 
	doi = {10.1145/3676641.3715996}, 
	booktitle = {Proceedings of the 30th ACM International Conference on Architectural Support for Programming Languages and Operating Systems, Volume 2}, 
	location = {Rotterdam, The Netherlands}, 
	series = {ASPLOS 2025}
} 
```
