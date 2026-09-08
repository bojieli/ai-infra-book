<div align="center" id="top">

<picture>
  <source media="(prefers-color-scheme: light)" srcset="docs/logo/fib-white-bg.png">
  <source media="(prefers-color-scheme: dark)" srcset="docs/logo/fib-black-bg.png">
  <img src="docs/logo/fib-white-bg.png" alt="FlashInfer-Bench logo" width="400">
</picture>


[![Documentation](https://img.shields.io/badge/docs-latest-green)](https://bench.flashinfer.ai/docs/)
[![License](https://img.shields.io/badge/license-apache_2-blue)](https://github.com/flashinfer-ai/flashinfer-bench/blob/main/LICENCE)
[![PyPI](https://img.shields.io/pypi/v/flashinfer-bench)](https://pypi.org/project/flashinfer-bench/)

**Building the Virtuous Cycle for AI-driven LLM Systems**

[Get Started](#get-started) | [Documentation](https://bench.flashinfer.ai/docs/) | [Blogpost](https://flashinfer.ai/2025/10/21/flashinfer-bench.html)
| [Slack (#flashinfer-bench)](https://join.slack.com/t/flashinfer/shared_invite/zt-379wct3hc-D5jR~1ZKQcU00WHsXhgvtA) </div>

**FlashInfer-Bench** is a benchmark suite and production workflow designed to build a virtuous cycle of self-improving AI systems.

It is part of a broader initiative to build the *virtuous cycle of AI improving AI systems* — enabling AI agents and engineers to collaboratively optimize the very kernels that power large language models.

## Installation

Install FlashInfer-Bench with pip:

```bash
pip install flashinfer-bench
```

Import FlashInfer-Bench:

```python
import flashinfer_bench as fib

print(fib.__version__)
```

## Get Started

This [guide](https://bench.flashinfer.ai/docs/start/quickstart) shows you how to use FlashInfer-Bench python module with the FlashInfer-Trace dataset.

## FlashInfer Trace Dataset

We provide an official dataset called **FlashInfer-Trace** with kernels and workloads in real-world AI system deployment environments. FlashInfer-Bench can use this dataset to measure and compare the performance of kernels. It follows the [FlashInfer Trace Schema](https://bench.flashinfer.ai/docs/flashinfer-trace).

The official dataset is on HuggingFace: https://huggingface.co/datasets/flashinfer-ai/flashinfer-trace

Clone it with Git LFS pointer files only (large tensor files are downloaded on demand during benchmarking):

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/datasets/flashinfer-ai/flashinfer-trace
flashinfer-bench run --local flashinfer-trace
```

## Collaborators

Our collaborators include:

<div align="center">

[<img src="https://raw.githubusercontent.com/mlc-ai/XGrammar-web-assets/refs/heads/main/repo/nvidia.svg" height=50/>](https://github.com/NVIDIA/TensorRT-LLM)
&emsp;
[<img src="https://raw.githubusercontent.com/mlc-ai/XGrammar-web-assets/refs/heads/main/repo/gpu_mode.png" height=50/>](https://github.com/gpu-mode)
&emsp;
[<img src="https://raw.githubusercontent.com/mlc-ai/XGrammar-web-assets/refs/heads/main/repo/sglang.png" height=50/>](https://github.com/sgl-project/sglang)
&emsp;
[<img src="https://raw.githubusercontent.com/mlc-ai/XGrammar-web-assets/refs/heads/main/repo/vllm.png" height=50/>](https://github.com/vllm-project/vllm)
&emsp;
[<img src="https://raw.githubusercontent.com/mlc-ai/XGrammar-web-assets/refs/heads/main/repo/bosch.svg" height=50/>](https://www.bosch.com/)

</div>
