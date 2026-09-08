# M2XFP: A Metadata-Augmented Microscaling Data Format for Efficient Low-bit Quantization

This repository contains the pseudo quantization workflow for M2XFP and provides a lightweight way to evaluate accuracy (e.g., perplexity) on LLaMA-3 and other LLMs.

## Setup

1. Create and activate conda environment:
```bash
conda create -n mxq python=3.10
conda activate mxq
```

2. Install the package in development mode:
```bash
pip install vllm==0.7.0 --extra-index-url https://download.pytorch.org/whl/cu128
pip install -e .
```

## Usage

Run the main quantization workflow:
```bash
# Perplexity evaluation on WikiText for LLaMA-3
bash llama3_run.sh wikitext

# Reasoning benchmarks
bash reasoning.sh
```

## Structure

- `entry.py` - Main entry point for quantization
- `llama3_run.sh` - An example script to run Llama3 quantization
- `quantize/` - Core quantization modules
  - `quant_func.py` - Quantization configuration and functions
  - `quantizer.py` - Main quantization logic
  - `linear.py` - Quantized linear layer implementation
  - `pre_quant.py` - Pre-quantization utilities
- `utils/` - Utility modules
  - `module.py` - Module manipulation utilities
  - `dataload_utils.py` - Data loading utilities
  - `parallel.py` - Parallel processing utilities
  - `calib_data.py` - Calibration data handling
  - `utils.py` - General utilities

## Citation

If you find this repository useful in your research or project, please kindly cite:

```text
@misc{hu2026m2xfpmetadataaugmentedmicroscalingdata,
  title={M2XFP: A Metadata-Augmented Microscaling Data Format for Efficient Low-bit Quantization}, 
  author={Weiming Hu and Zihan Zhang and Haoyan Zhang and Chen Zhang and Cong Guo and Yu Feng and Tianchi Hu and Guanglin Li and Guipeng Hu and Junsong Wang and Jingwen Leng},
  year={2026},
  eprint={2601.19213},
  archivePrefix={arXiv},
  primaryClass={cs.AR},
  url={https://arxiv.org/abs/2601.19213}, 
}
```

## Acknowledgements

We sincerely thank the authors and contributors of the following open-source projects. Our implementation builds upon their excellent codebases:

- [AWQ](https://github.com/mit-han-lab/llm-awq)
- [vLLM](https://github.com/vllm-project/vllm)
- [LM-Eval Harness](https://github.com/EleutherAI/lm-evaluation-harness)
- [LightEval](https://github.com/huggingface/lighteval/tree/main)
