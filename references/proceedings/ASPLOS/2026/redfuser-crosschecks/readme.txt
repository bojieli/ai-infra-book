# RedFuser

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![ASPLOS 2026](https://img.shields.io/badge/ASPLOS-2026-orange.svg)](https://asplos-conference.org/)

This repository contains the artifact for our ASPLOS 2026 paper: **"RedFuser: An Automatic Operator Fusion Framework for Cascaded Reductions on AI Accelerators"**.

## Overview

RedFuser is a novel framework for optimizing cascaded reductions in deep learning compilers. Built on top of [Apache TVM](https://github.com/apache/tvm), RedFuser introduces a series of compiler transformation passes that enable efficient fusion of reduction operations with other computations, particularly targeting modern GPU architectures.

## Update

- \[2026-03\]: Support Flash Decoding, Moe Routing and Quant GEMM examples.
- \[2026-01\]: RedFuser is now avaliable with flash-attention example.
- \[2025-11\]: 🎉 RedFuser is accepted by ASPLOS 2026!

## Roadmap

- [x] flash-attention
- [x] flash-decoding
- [x] moe-routing
- [x] fp8 quant+gemm

## Getting Started

Please follow https://tvm.apache.org/docs/install/index.html to install.

## Example

For flash-attention example, see [`python/tvm/redfuser/example/flash_attention.py`](python/tvm/redfuser/example/flash_attention.py).

## Structure

```
redfuser/
├── python/tvm/redfuser/       # RedFuser Python implementation
│   ├── transform/             # Core transformation passes
│   └── example/               # Example workloads
│ ...
```

## Citation

If you use RedFuser in your research, please cite our paper:

```bibtex
@article{RedFuser,
  title={RedFuser: An Automatic Operator Fusion Framework for Cascaded Reductions on AI Accelerators},
  author={Xinsheng Tang and Yangchen Li and Nan Wang and Zhiyi Shu and Xingyu Ling and Junna Xing and Peng Zhou and Qiang Liu},
  journal={Proceedings of the 31st ACM International Conference on Architectural Support for Programming Languages and Operating Systems, Volume 2},
  year={2026},
  url={https://arxiv.org/abs/2603.10026}
}
```

## License

RedFuser is licensed under the [Apache License 2.0](LICENSE).

## Acknowledgments

This project builds upon [Apache TVM](https://github.com/apache/tvm). We thank the TVM community for their excellent infrastructure and support.
