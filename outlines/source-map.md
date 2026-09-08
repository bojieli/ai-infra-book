# 参考资料与大纲对应

固定能力成本下降的专题来源另见[67 项原件及逐项阅读范围](../references/token-cost/2026-09-07/README.md)，与[18 条大纲占位](../research/token-cost-2023-2026/outline-placement.md)对应；其中复用来源保持下表原件不变。

本表逐项对应原参考库的 230 项清单，另列补充的 OTel 正文、Beyond Chinchilla 两版入口、两份 RFC，以及历史训练报告、模型配置、近期推测解码、量化文件元数据、硬件演进与源码快照。它记录资料状态和本轮重写后的大纲引用位置，不代表已逐页审阅全部原文；阅读范围见[核对记录](research-notes.md)。未进入章内主要引用的资料仍作为版本、规格或专题参照保留。

原清单章号保留草案 22 修订前的登记；当前落点按新目录重新计算，正文、章末选读与扩写引用分别标明。

| 资料 ID | 资料与本地原件 | 历史清单章号 | 当前正文／章末／扩写引用 | 原件状态 |
| --- | --- | --- | --- | --- |
| `transformer` | [Attention Is All You Need](../references/files/papers/transformer.pdf) | 2 | 章末 2 | 已归档 |
| `mqa` | [Fast Transformer Decoding: One Write-Head is All You Need](../references/files/papers/mqa.pdf) | 2,9 | 章末 2 | 已归档 |
| `gqa` | [GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints](../references/files/papers/gqa.pdf) | 2,9 | 章末 2 | 已归档 |
| `deepseek-moe` | [DeepSeekMoE: Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models](../references/files/papers/deepseek-moe.pdf) | 2,10 | 章末 2 | 已归档 |
| `deepseek-v2` | [DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model](../references/files/papers/deepseek-v2.pdf) | 2,9 | 章末 8 | 已归档 |
| `deepseek-v3` | [DeepSeek-V3 Technical Report](../references/files/papers/deepseek-v3.pdf) | 2,3,10,11,13 | 章末 3,6,9,10 | 已归档 |
| `deepseek-v32` | [DeepSeek-V3.2: Pushing the Frontier of Open Large Language Models](../references/files/papers/deepseek-v32.pdf) | 2,3,11 | 补充／版本参照 | 已归档 |
| `deepseek-v4` | [DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence](../references/files/papers/deepseek-v4.pdf) | 2,3,10,11,13 | 章末 2,3,6,7,8,9,10,11 | 已归档 |
| `kimi-k3` | [Kimi K3: Open Frontier Intelligence](../references/files/papers/kimi-k3.pdf) | 2,3,10,11,12 | 章末 2,3,6,7,10 | 已归档 |
| `kimi-linear` | [Kimi Linear: An Expressive, Efficient Attention Architecture](../references/files/papers/kimi-linear.pdf) | 2,4,9 | 章末 2 | 已归档 |
| `gated-delta` | [Gated Delta Networks: Improving Mamba2 with Delta Rule](../references/files/papers/gated-delta.pdf) | 2,4 | 章末 2 | 已归档 |
| `mamba` | [Mamba: Linear-Time Sequence Modeling with Selective State Spaces](../references/files/papers/mamba.pdf) | 2 | 章末 2 | 已归档 |
| `switch-transformer` | [Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity](../references/files/papers/switch-transformer.pdf) | 2,10,11 | 章末 2 | 已归档 |
| `scaling-laws` | [Scaling Laws for Neural Language Models](../references/files/papers/scaling-laws.pdf) | 3,13 | 章末 3 | 已归档 |
| `chinchilla` | [Training Compute-Optimal Large Language Models](../references/files/papers/chinchilla.pdf) | 3,13 | 章末 3 | 已归档 |
| `qwen35-config` | [Qwen3.5-397B-A17B official configuration](../references/files/models/qwen35-config.json) | 2,3 | 章末 2 | 已归档 |
| `qwen35-card` | [Qwen3.5-397B-A17B official model card](../references/files/models/qwen35-card.md) | 2,3 | 章末 3 | 已归档 |
| `flashattention` | [FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](../references/files/papers/flashattention.pdf) | 2,4,5 | 章末 5 | 已归档 |
| `flashattention2` | [FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning](../references/files/papers/flashattention2.pdf) | 4,5 | 章末 5 | 已归档 |
| `flashattention3` | [FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-precision](../references/files/papers/flashattention3.pdf) | 4,5 | 章末 5 | 已归档 |
| `akg-pldi21` | [AKG: Automatic Kernel Generation for Neural Processing Units using Polyhedral Transformations](../references/files/papers/akg-pldi21.pdf) | 5 | 章末 5 | 已归档 |
| `tvm` | [TVM: An Automated End-to-End Optimizing Compiler for Deep Learning](../references/files/papers/tvm.pdf) | 5 | 章末 5 | 已归档 |
| `tensorir` | [TensorIR: An Abstraction for Automatic Tensorized Program Optimization](../references/files/papers/tensorir.pdf) | 5 | 章末 5 | 已归档 |
| `isl-tutorial` | [Presburger Formulas and Polyhedral Compilation](../references/files/documents/isl-tutorial.pdf) | 5 | 章末 5 | 已归档 |
| `isl-manual` | [Integer Set Library Manual](../references/files/documents/isl-manual.html) | 5 | 补充／版本参照 | 已归档 |
| `tvm-architecture` | [Apache TVM Design and Architecture](../references/files/documents/tvm-architecture.html) | 5 | 补充／版本参照 | 已归档 |
| `roofline` | [Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures](../references/files/papers/roofline.pdf) | 1,4,13 | 章末 1,4,13 | 已归档 |
| `hardware-lottery` | [The Hardware Lottery](../references/files/papers/hardware-lottery.pdf) | 1,13 | 章末 2,13 | 已归档 |
| `tpu-v1` | [In-Datacenter Performance Analysis of a Tensor Processing Unit](../references/files/papers/tpu-v1.pdf) | 1,3,4,13 | 章末 1,4,13 | 已归档 |
| `tpu-v4` | [TPU v4: An Optically Reconfigurable Supercomputer for Machine Learning with Hardware Support for Embeddings](../references/files/papers/tpu-v4.pdf) | 4,6,13 | 章末 6 | 已归档 |
| `nvidia-v100` | [NVIDIA Tesla V100 GPU Architecture](../references/files/specs/nvidia-v100.pdf) | 4 | 章末 4 | 已归档 |
| `nvidia-a100` | [NVIDIA A100 Tensor Core GPU Architecture](../references/files/specs/nvidia-a100.pdf) | 4 | 章末 4 | 已归档 |
| `nvidia-h100` | [NVIDIA H100 Tensor Core GPU Architecture](../references/files/specs/nvidia-h100.pdf) | 4,6 | 章末 4 | 已归档 |
| `nvidia-h100-spec` | [NVIDIA H100 Product Specifications](../references/files/specs/nvidia-h100-spec.html) | 4 | 章末 1 | 已归档 |
| `nvidia-blackwell-guide` | [NVIDIA Blackwell Tuning Guide](../references/files/specs/nvidia-blackwell-guide.html) | 4,5 | 补充／版本参照 | 已归档 |
| `nvidia-dgx-b200` | [NVIDIA DGX B200 Specifications](../references/files/specs/nvidia-dgx-b200.html) | 4,6 | 补充／版本参照 | 已归档 |
| `nvidia-gb200` | [NVIDIA GB200 NVL72](../references/files/specs/nvidia-gb200.html) | 6,13 | 章末 6 | 已归档 |
| `nvidia-rtx4090` | [NVIDIA GeForce RTX 4090 Specifications](../references/files/specs/nvidia-rtx4090.html) | 4,10,11 | 补充／版本参照 | 已归档 |
| `ascend-davinci` | [Communications of HUAWEI RESEARCH：昇腾架构论文所在期](../references/files/specs/ascend-davinci.pdf) | 4 | 章末 4 | 已归档 |
| `ascend-c-guide` | [CANN 8.1.RC1.alpha002 Ascend C 算子开发指南](../references/files/specs/ascend-c-guide.pdf) | 4,5 | 章末 4,5 | 已归档 |
| `ascend-c-architecture` | [CANN 9.0.0 Ascend C 硬件架构](../references/files/specs/ascend-c-architecture.html) | 4,5 | 补充／版本参照 | 正文不完整 |
| `ascend-910-launch` | [Huawei Atlas 900 and ResNet-50 announcement, 2019](../references/files/documents/ascend-910-launch.html) | 4,6 | 补充／版本参照 | 已归档 |
| `ascend-950-roadmap` | [昇腾 950 与 Unified Bus 公开路线图](../references/files/specs/ascend-950-roadmap.html) | 4,6,7,13 | 补充／版本参照 | 已归档 |
| `ascend-950-mwc` | [Huawei SuperPoD Portfolio at MWC Barcelona 2026](../references/files/documents/ascend-950-mwc.html) | 4,6,13 | 补充／版本参照 | 已归档 |
| `apple-ane` | [Deploying Transformers on the Apple Neural Engine](../references/files/documents/apple-ane.html) | 4,8 | 补充／版本参照 | 已归档 |
| `mlx` | [MLX official README](../references/files/documents/mlx.md) | 5,8 | 章末 5 | 已归档 |
| `llama-cpp` | [llama.cpp official README](../references/files/documents/llama-cpp.md) | 5,9 | 补充／版本参照 | 已归档 |
| `unsloth` | [Unsloth official README](../references/files/documents/unsloth.md) | 5,8,11 | 补充／版本参照 | 已归档 |
| `ollama` | [Ollama Development and Compute Backends](../references/files/documents/ollama.html) | 5,9 | 补充／版本参照 | 已归档 |
| `nccl-guide` | [NCCL User Guide](../references/files/documents/nccl-guide.html) | 6,7 | 章末 6,7 | 已归档 |
| `nccl-collectives` | [NCCL Collective Operations](../references/files/documents/nccl-collectives.html) | 6,7 | 章末 6,7 | 已归档 |
| `ub-reflection` | [Unified Bus 背后的思考](../references/files/documents/ub-reflection.html) | 6,7,13 | 章末 1,6,7,13 | 已归档 |
| `ub-spec-entry` | [Unified Bus Base Specification 2.0 Preview 官方入口](../references/files/specs/ub-spec-entry.html) | 6,7 | 补充／版本参照 | 仅入口 |
| `openurma` | [OpenURMA: A Clean-Room Open Implementation of the Unified Bus Protocol](../references/files/papers/openurma.pdf) | 6,7 | 章末 7 | 已归档 |
| `openurma-readme` | [OpenURMA official README](../references/files/documents/openurma-readme.md) | 6,7 | 补充／版本参照 | 已归档 |
| `ualink-whitepaper` | [Introducing UALink 200G 1.0 Specification](../references/files/specs/ualink-whitepaper.pdf) | 6 | 补充／版本参照 | 已归档 |
| `ualink-spec-entry` | [UALink Common 2.0 Specification 官方入口](../references/files/specs/ualink-spec-entry.html) | 6 | 补充／版本参照 | 仅入口 |
| `rdma-guide` | [NVIDIA DOCA RDMA-Aware Networks Programming Guide](../references/files/documents/rdma-guide.html) | 7 | 章末 7 | 已归档 |
| `dcqcn` | [Congestion Control for Large-Scale RDMA Deployments](../references/files/papers/dcqcn.pdf) | 7 | 章末 7 | 已归档 |
| `timely` | [TIMELY: RTT-based Congestion Control for the Datacenter](../references/files/papers/timely.pdf) | 7 | 章末 7 | 已归档 |
| `rfc9293` | [RFC 9293: Transmission Control Protocol](../references/files/standards/rfc9293.txt) | 7,8 | 章末 12 | 已归档 |
| `rfc9000` | [RFC 9000: QUIC Transport](../references/files/standards/rfc9000.txt) | 8 | 章末 12 | 已归档 |
| `rfc9002` | [RFC 9002: QUIC Loss Detection and Congestion Control](../references/files/standards/rfc9002.txt) | 8 | 章末 12 | 已归档 |
| `rfc3550` | [RFC 3550: RTP](../references/files/standards/rfc3550.txt) | 8 | 章末 12 | 已归档 |
| `rfc8831` | [RFC 8831: WebRTC Data Channels](../references/files/standards/rfc8831.txt) | 8,12 | 章末 12 | 已归档 |
| `rfc8836` | [RFC 8836: Congestion Control Requirements for Interactive Real-Time Media](../references/files/standards/rfc8836.txt) | 8 | 章末 12 | 已归档 |
| `whisper` | [Robust Speech Recognition via Large-Scale Weak Supervision](../references/files/papers/whisper.pdf) | 3,8 | 章末 12 | 已归档 |
| `vits` | [Conditional Variational Autoencoder with Adversarial Learning for End-to-End Text-to-Speech](../references/files/papers/vits.pdf) | 3,8 | 章末 12 | 已归档 |
| `network-golden-1` | [计算机网络的新黄金时代（一）](../references/files/documents/network-golden-1.html) | 1,6,7 | 章末 1,6,7,11 | 已归档 |
| `network-golden-2` | [计算机网络的新黄金时代（二）](../references/files/documents/network-golden-2.html) | 8 | 章末 3,12 | 已归档 |
| `network-golden-3` | [计算机网络的新黄金时代（三）](../references/files/documents/network-golden-3.html) | 4,8 | 章末 12 | 已归档 |
| `vllm` | [Efficient Memory Management for Large Language Model Serving with PagedAttention](../references/files/papers/vllm.pdf) | 9,10 | 章末 8 | 已归档 |
| `orca` | [Orca: A Distributed Serving System for Transformer-Based Generative Models](../references/files/papers/orca.pdf) | 9 | 章末 8 | 已归档 |
| `sarathi-serve` | [Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve](../references/files/papers/sarathi-serve.pdf) | 9 | 章末 8 | 已归档 |
| `sglang` | [SGLang: Efficient Execution of Structured Language Model Programs](../references/files/papers/sglang.pdf) | 9,10 | 章末 8,9 | 已归档 |
| `speculative-decoding` | [Fast Inference from Transformers via Speculative Decoding](../references/files/papers/speculative-decoding.pdf) | 9 | 章末 8 | 已归档 |
| `flexgen` | [FlexGen: High-Throughput Generative Inference of Large Language Models with a Single GPU](../references/files/papers/flexgen.pdf) | 4,8,9 | 章末 8 | 已归档 |
| `distserve` | [DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving](../references/files/papers/distserve.pdf) | 10 | 章末 9 | 已归档 |
| `splitwise` | [Splitwise: Efficient Generative LLM Inference Using Phase Splitting](../references/files/papers/splitwise.pdf) | 10,13 | 章末 9 | 已归档 |
| `mooncake` | [Mooncake: A KVCache-centric Disaggregated Architecture for LLM Serving](../references/files/papers/mooncake.pdf) | 3,10 | 章末 9 | 已归档 |
| `megatron` | [Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism](../references/files/papers/megatron.pdf) | 11 | 章末 6,7,10 | 已归档 |
| `megatron-scale` | [Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM](../references/files/papers/megatron-scale.pdf) | 11 | 章末 10 | 已归档 |
| `zero` | [ZeRO: Memory Optimizations Toward Training Trillion Parameter Models](../references/files/papers/zero.pdf) | 11 | 章末 10 | 已归档 |
| `gpipe` | [GPipe: Easy Scaling with Micro-Batch Pipeline Parallelism](../references/files/papers/gpipe.pdf) | 11 | 章末 10 | 已归档 |
| `activation-recompute` | [Reducing Activation Recomputation in Large Transformer Models](../references/files/papers/activation-recompute.pdf) | 4,11 | 章末 10 | 已归档 |
| `checkfreq` | [CheckFreq: Frequent, Fine-Grained DNN Checkpointing](../references/files/papers/checkfreq.pdf) | 11 | 章末 10 | 已归档 |
| `verl` | [HybridFlow: A Flexible and Efficient RLHF Framework](../references/files/papers/verl.pdf) | 11,12 | 章末 10 | 已归档 |
| `areal` | [AReaL: A Large-Scale Asynchronous Reinforcement Learning System for Language Reasoning](../references/files/papers/areal.pdf) | 11,12 | 章末 10 | 已归档 |
| `gavel` | [Heterogeneity-Aware Cluster Scheduling Policies for Deep Learning Workloads](../references/files/papers/gavel.pdf) | 12 | 章末 11 | 已归档 |
| `pollux` | [Pollux: Co-adaptive Cluster Scheduling for Goodput-Optimized Deep Learning](../references/files/papers/pollux.pdf) | 12 | 章末 11 | 已归档 |
| `tiresias` | [Tiresias: A GPU Cluster Manager for Distributed Deep Learning](../references/files/papers/tiresias.pdf) | 12 | 补充／版本参照 | 已归档 |
| `drf` | [Dominant Resource Fairness: Fair Allocation of Multiple Resource Types](../references/files/papers/drf.pdf) | 12 | 章末 11 | 已归档 |
| `routellm` | [RouteLLM: Learning to Route LLMs from Preference Data](../references/files/papers/routellm.pdf) | 12 | 章末 11 | 已归档 |
| `frugalgpt` | [FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance](../references/files/papers/frugalgpt.pdf) | 12 | 章末 11 | 已归档 |
| `firecracker` | [Firecracker: Lightweight Virtualization for Serverless Applications](../references/files/papers/firecracker.pdf) | 12 | 章末 11 | 已归档 |
| `kueue` | [Kueue Concepts](../references/files/documents/kueue.html) | 12 | 补充／版本参照 | 已归档 |
| `k8s-scheduling` | [Kubernetes Scheduling Framework](../references/files/documents/k8s-scheduling.html) | 12 | 补充／版本参照 | 已归档 |
| `k8s-images` | [Kubernetes Images](../references/files/documents/k8s-images.html) | 12 | 补充／版本参照 | 已归档 |
| `opencost` | [OpenCost Specification](../references/files/documents/opencost.html) | 12 | 章末 11 | 已归档 |
| `otel-genai` | [OpenTelemetry Semantic Conventions for Generative AI Metrics](../references/files/documents/otel-genai.html) | 12 | 补充／版本参照 | 已归档迁移提示；正文见新增条目 |
| `nvidia-blackwell-brief` | [NVIDIA Blackwell Architecture Technical Brief](../references/files/specs/nvidia-blackwell-brief.pdf) | 4,6 | 章末 4 | 已归档 |
| `ub-base-preview` | [Unified Bus Base Specification 2.0 Preview](../references/files/specs/ub-base-preview.pdf) | 6,7 | 补充／版本参照 | 已归档 |
| `ub-os-reference` | [Unified Bus Software Reference Design for Operating Systems 2.0](../references/files/specs/ub-os-reference.pdf) | 6,7,12 | 补充／版本参照 | 已归档 |
| `ub-root-table` | [Unified Bus Root Table Specification 1.0](../references/files/specs/ub-root-table.pdf) | 6,7 | 补充／版本参照 | 已归档 |
| `h100-vs-4090` | [A100/H100 太贵，何不用 4090？](../references/files/documents/h100-vs-4090.html) | 3,4,11 | 章末 1,4,6,8,9,10,12,13 | 已归档 |
| `opentallas-readme` | [OpenTallas architecture and analysis](../references/files/documents/opentallas-readme.md) | 2,4,5,6,7,9,13 | 章末 4,13 | 本地固定快照 |
| `kueue-clusterqueue` | [Kueue ClusterQueue](../references/files/documents/kueue-clusterqueue.html) | 12 | 章末 11 | 已归档 |
| `kueue-preemption` | [Kueue Preemption](../references/files/documents/kueue-preemption.html) | 12 | 章末 11 | 已归档 |
| `fat-tree` | [A Scalable, Commodity Data Center Network Architecture](../references/files/papers/fat-tree.pdf) | 7 | 章末 7 | 已归档 |
| `collective-algorithms` | [Optimization of Collective Communication Operations in MPICH](../references/files/papers/collective-algorithms.pdf) | 6,7 | 章末 6,7 | 已归档 |
| `ualink-common` | [UALink Common Specification 2.0, Evaluation Copy](../references/files/specs/ualink-common.pdf) | 6 | 补充／版本参照 | 已归档 |
| `ualink-link` | [UALink 200G Data Link and Physical Layers 2.0, Evaluation Copy](../references/files/specs/ualink-link.pdf) | 6 | 补充／版本参照 | 已归档 |
| `ub-base-201` | [Unified Bus Base Specification 2.0.1（英文获取入口）](https://www.unifiedbus.com/en/docs/UB-Base-Specification-2.0.1-en-clean) | 6,7 | 补充／版本参照 | 入口需协议确认 |
| `gptq` | [GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers](../references/files/papers/gptq.pdf) | 4,5,9 | 补充／版本参照 | 已归档 |
| `awq` | [AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration](../references/files/papers/awq.pdf) | 4,5,9 | 补充／版本参照 | 已归档 |
| `smoothquant` | [SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models](../references/files/papers/smoothquant.pdf) | 4,5,9 | 补充／版本参照 | 已归档 |
| `lora` | [LoRA: Low-Rank Adaptation of Large Language Models](../references/files/papers/lora.pdf) | 3,4,11 | 章末 10 | 已归档 |
| `qlora` | [QLoRA: Efficient Finetuning of Quantized LLMs](../references/files/papers/qlora.pdf) | 3,4,11 | 章末 10 | 已归档 |
| `llama2` | [Llama 2: Open Foundation and Fine-Tuned Chat Models](../references/files/papers/llama2.pdf) | 2,3,9 | 章末 3,10 | 已归档 |
| `llama3` | [The Llama 3 Herd of Models](../references/files/papers/llama3.pdf) | 2,3,5,10,11,13 | 章末 3,10 | 已归档 |
| `cerebras-wse3` | [The Cerebras Wafer-Scale Architecture for Deep Learning](../references/files/specs/cerebras-wse3.pdf) | 4,6,13 | 补充／版本参照 | 已归档 |
| `sambanova-sn40l` | [SambaNova SN40L Reconfigurable Dataflow Unit](../references/files/specs/sambanova-sn40l.pdf) | 4,13 | 补充／版本参照 | 已归档 |
| `sambanova-sambarack` | [SambaNova SambaRack SN40L-16 Datasheet](../references/files/specs/sambanova-sambarack.pdf) | 4,6,13 | 补充／版本参照 | 已归档 |
| `groq-tsp` | [Think Fast: A Tensor Streaming Processor (TSP) for Accelerating Deep Learning Workloads](../references/files/papers/groq-tsp.pdf) | 4,13 | 章末 4 | 已归档 |
| `groq-scale` | [A Software-defined Tensor Streaming Multiprocessor for Large-scale Machine Learning](../references/files/papers/groq-scale.pdf) | 4,6,13 | 补充／版本参照 | 已归档 |
| `groq-chip` | [GroqChip Processor Product Brief v1.5](../references/files/specs/groq-chip.pdf) | 4,13 | 补充／版本参照 | 已归档 |
| `taalas-hc1` | [Taalas HC1 Technology Demonstrator](../references/files/specs/taalas-hc1.html) | 4,9,13 | 补充／版本参照 | 已归档 |
| `etched-sohu` | [Etched 官方产品页面](../references/files/documents/etched-sohu.html) | 4,13 | 补充／版本参照 | 已归档 |
| `cerebras-wse3-spec` | [Cerebras Wafer-Scale Engine 3 Datasheet](../references/files/specs/cerebras-wse3-spec.pdf) | 4,6,13 | 章末 4 | 已归档 |
| `cerebras-cs4-spec` | [Cerebras CS-4 Datasheet](../references/files/specs/cerebras-cs4-spec.pdf) | 4,6,13 | 补充／版本参照 | 已归档 |
| `ub-base-201-zh` | [灵衢基础规范 2.0.1（中文版）](../references/files/specs/UB-Base-Specification-2.0.1-zh-clean.pdf) | 6,7,12 | 章末 6,7 | 作者提供 |
| `ub-os-zh` | [灵衢使能操作系统参考设计 2.0（中文版）](../references/files/specs/UB-Software-Reference-Design-for-OS-2.0-zh.pdf) | 6,7,12 | 章末 6,7,11 | 作者提供 |
| `ascend-950-whitepaper` | [昇腾 950 NPU 架构白皮书](../references/files/specs/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf) | 4,5,6,7,10,13 | 补充／版本参照 | 作者提供 |
| `google-v4` | [Google Cloud TPU v4 官方规格](../references/files/specs/google-v4.html) | 4,6,13 | 补充／版本参照 | 已归档 |
| `google-v5e` | [Google Cloud TPU v5e 官方规格](../references/files/specs/google-v5e.html) | 4,6,13 | 补充／版本参照 | 已归档 |
| `google-v5p` | [Google Cloud TPU v5p 官方规格](../references/files/specs/google-v5p.html) | 4,6,13 | 补充／版本参照 | 已归档 |
| `google-v6e` | [Google Cloud TPU v6e 官方规格](../references/files/specs/google-v6e.html) | 4,6,13 | 补充／版本参照 | 已归档 |
| `google-tpu7x` | [Google Cloud TPU tpu7x 官方规格](../references/files/specs/google-tpu7x.html) | 4,6,13 | 补充／版本参照 | 已归档 |
| `google-tpu-architecture` | [Google Cloud TPU System Architecture](../references/files/documents/google-tpu-architecture.html) | 4,6 | 补充／版本参照 | 已归档 |
| `google-tpu-machines` | [Google Cloud TPU Machine Specifications](../references/files/specs/google-tpu-machines.html) | 4,6,12 | 补充／版本参照 | 已归档 |
| `google-tpu8` | [Inside the Eighth-Generation TPU: An Architecture Deep Dive](../references/files/specs/google-tpu8.html) | 4,6,7,13 | 章末 4 | 已归档 |
| `google-tpu-generations` | [Google's Training Supercomputers from TPU v2 to Ironwood: Architectural Stability, Scale, Resilience, Power Efficiency, and Sustainability Across Five Generations](../references/files/papers/google-tpu-generations.pdf) | 4,6,11,13 | 章末 4,6 | 已归档 |
| `graphcore-mk2` | [The Data Center Architecture for Graphcore Computing](../references/files/specs/graphcore-mk2.pdf) | 4,6,13 | 补充／版本参照 | 已归档 |
| `graphcore-m2000-pdf` | [IPU-Machine M2000 Datasheet 1.0.0](../references/files/specs/graphcore-m2000-pdf.pdf) | 4,6,13 | 补充／版本参照 | 已归档 |
| `graphcore-m2000` | [IPU-M2000 Product Description and Technical Specifications](../references/files/specs/graphcore-m2000.html) | 4,6,13 | 补充／版本参照 | 已归档 |
| `graphcore-bow2000` | [Bow-2000 Product Description and Technical Specifications](../references/files/specs/graphcore-bow2000.html) | 4,6,13 | 补充／版本参照 | 已归档 |
| `graphcore-hardware` | [IPU Hardware Overview](../references/files/documents/graphcore-hardware.html) | 4,6 | 补充／版本参照 | 已归档 |
| `graphcore-programming` | [IPU Programming Model](../references/files/documents/graphcore-programming.html) | 4,6 | 章末 4 | 已归档 |
| `graphcore-isa` | [Graphcore Tile Vertex ISA 1.2.3 (GC200 and Bow)](../references/files/specs/graphcore-isa.pdf) | 4 | 补充／版本参照 | 已归档 |
| `graphcore-isa-fp8` | [Graphcore Tile Vertex ISA IPU21 1.3.1](../references/files/specs/graphcore-isa-fp8.pdf) | 4 | 补充／版本参照 | 已归档 |
| `graphcore-bowpod16` | [Graphcore Bow Pod16 Product Brief](../references/files/specs/graphcore-bowpod16.pdf) | 6,13 | 补充／版本参照 | 已归档 |
| `graphcore-microbench` | [Dissecting the Graphcore IPU Architecture via Microbenchmarking](../references/files/papers/graphcore-microbench.pdf) | 4,6,13 | 补充／版本参照 | 已归档 |
| `sambanova-sn40l-paper` | [SambaNova SN40L: Scaling the AI Memory Wall with Dataflow and Composition of Experts](../references/files/papers/sambanova-sn40l-paper.pdf) | 4,6,9,12,13 | 章末 4 | 已归档 |
| `amd-cdna3` | [Introducing AMD CDNA 3 Architecture](../references/files/specs/amd-cdna3.pdf) | 4,6,13 | 补充／版本参照 | 已归档 |
| `amd-cdna4` | [Introducing AMD CDNA 4 Architecture](../references/files/specs/amd-cdna4.pdf) | 4,6,13 | 补充／版本参照 | 已归档 |
| `amd-mi300x` | [AMD Instinct MI300X Product Specifications](../references/files/specs/amd-mi300x.html) | 4,13 | 补充／版本参照 | 已归档 |
| `amd-mi300x-platform` | [AMD Instinct MI300X Platform Datasheet](../references/files/specs/amd-mi300x-platform.pdf) | 4,6,13 | 补充／版本参照 | 已归档 |
| `amd-mi350x` | [AMD Instinct MI350X GPU Datasheet](../references/files/specs/amd-mi350x.pdf) | 4,13 | 补充／版本参照 | 已归档 |
| `amd-mi350x-platform` | [AMD Instinct MI350X Platform Datasheet](../references/files/specs/amd-mi350x-platform.pdf) | 4,6,13 | 补充／版本参照 | 已归档 |
| `intel-gaudi3` | [Intel Gaudi 3 AI Accelerator White Paper](../references/files/specs/intel-gaudi3.pdf) | 4,6,7,13 | 补充／版本参照 | 已归档 |
| `cambricon-mlu370` | [寒武纪思元 370 系列官方产品规格](../references/files/specs/cambricon-mlu370.html) | 4,6,13 | 补充／版本参照 | 已归档 |
| `aws-trainium2` | [AWS Trainium2 Architecture](../references/files/specs/aws-trainium2.html) | 4,6,13 | 补充／版本参照 | 已归档 |
| `aws-trainium3` | [AWS Trainium3 Architecture](../references/files/specs/aws-trainium3.html) | 4,6,13 | 补充／版本参照 | 已归档 |
| `aws-neuroncore-v3` | [AWS NeuronCore-v3 Architecture](../references/files/documents/aws-neuroncore-v3.html) | 4 | 补充／版本参照 | 已归档 |
| `aws-trainium3-nki` | [Trainium3 Architecture Guide for NKI](../references/files/documents/aws-trainium3-nki.html) | 4 | 补充／版本参照 | 已归档 |
| `aws-trn2-system` | [Amazon EC2 Trn2 Architecture](../references/files/specs/aws-trn2-system.html) | 6,11,13 | 补充／版本参照 | 已归档 |
| `aws-trn3-system` | [Amazon EC2 Trn3 UltraServers](../references/files/specs/aws-trn3-system.html) | 6,11,13 | 补充／版本参照 | 已归档 |
| `sambanova-sn50` | [Hot Chips 2026: SN50 RDU Dataflow at Scale](../references/files/documents/sambanova-sn50.html) | 4,6,7,13 | 补充／版本参照 | 已归档 |
| `sambanova-sn50-system` | [SambaRack SN50 Official Product Description](../references/files/specs/sambanova-sn50-system.html) | 6,10,13 | 补充／版本参照 | 已归档 |
| `nvidia-rubin-arch` | [Inside NVIDIA Rubin GPU Architecture](../references/files/documents/nvidia-rubin-arch.html) | 4,6,13 | 补充／版本参照 | 已归档 |
| `nvidia-rubin-system` | [NVIDIA Vera Rubin NVL72 Specifications](../references/files/specs/nvidia-rubin-system.html) | 4,6,13 | 章末 4 | 已归档 |
| `nvidia-nvlink-spec` | [NVIDIA NVLink and NVLink Switch Specifications](../references/files/specs/nvidia-nvlink-spec.html) | 6 | 章末 6,7 | 已归档 |
| `qualcomm-xelite` | [Snapdragon X Elite Product Brief](../references/files/specs/qualcomm-xelite.pdf) | 4,8 | 补充／版本参照 | 已归档 |
| `groq-rack` | [GroqRack Compute Cluster Product Brief v1.0](../references/files/specs/groq-rack.pdf) | 6,13 | 补充／版本参照 | 已归档 |
| `apple-m5-macbook` | [MacBook Pro (14-inch, M5) Technical Specifications](../references/files/specs/apple-m5-macbook.html) | 4,8 | 补充／版本参照 | 已归档 |
| `cloudmatrix384-v2` | [Serving Large Language Models on Huawei CloudMatrix384, v2](../references/files/papers/cloudmatrix384-v2.pdf) | 4,5,6,9,10,11,13 | 章末 4,5,6 | 已归档 |
| `cloudmatrix384-v3` | [Serving Large Language Models on Huawei CloudMatrix384, v3](../references/files/papers/cloudmatrix384-v3.pdf) | 4,5,6,9,10,11,13 | 补充／版本参照 | 已归档 |
| `nvidia-hopper-tuning` | [NVIDIA Hopper Tuning Guide](../references/files/documents/nvidia-hopper-tuning.html) | 4,5 | 章末 4,5 | 已归档 |
| `nvidia-async-copies` | [CUDA Programming Guide 13.2.1: Asynchronous Data Copies](../references/files/documents/nvidia-async-copies.html) | 4,5 | 补充／版本参照 | 已归档 |
| `cuda-graphs` | [CUDA Graph Best Practice for PyTorch: CUDA Graph](../references/files/documents/cuda-graphs.html) | 5,9,11 | 章末 5 | 已归档 |
| `vllm-cuda-graphs` | [vLLM CUDA Graphs Design](../references/files/documents/vllm-cuda-graphs.html) | 5,9 | 章末 5,8 | 已归档 |
| `triton-introduction` | [Triton Programming Guide: Introduction](../references/files/documents/triton-introduction.html) | 5 | 补充／版本参照 | 已归档 |
| `triton-matmul` | [Triton Tutorial: Matrix Multiplication](../references/files/documents/triton-matmul.html) | 5 | 章末 5 | 已归档 |
| `ascend-950-official` | [昇腾 950 NPU 架构白皮书（官方下载原件）](../references/files/specs/ascend-950-official.pdf) | 4,5,6,7,10,13 | 章末 4,6,7 | 已归档 |
| `apple-m2-pro-max` | [Apple M2 Pro and M2 Max launch specifications](../references/files/specs/apple-m2-pro-max.html) | 4,8,9 | 章末 4,8,12 | 已归档 |
| `apple-metal-memory` | [Choosing a resource storage mode for Apple GPUs — DocC JSON](../references/files/documents/apple-metal-memory.json) | 4,5 | 章末 4 | 已归档 |
| `apple-gpu-architecture` | [Explore the architecture of Apple GPUs — WWDC20](../references/files/documents/apple-gpu-architecture.html) | 4,5 | 章末 4 | 已归档 |
| `nvidia-rtx-pro6000-spec` | [RTX PRO 6000 Blackwell Workstation Edition Datasheet](../references/files/specs/nvidia-rtx-pro6000-spec.pdf) | 4,9 | 章末 4,8,12 | 已归档 |
| `nvidia-rtx-blackwell-pro` | [NVIDIA RTX Blackwell PRO GPU Architecture v1.0](../references/files/specs/nvidia-rtx-blackwell-pro.pdf) | 4,5 | 章末 4 | 已归档 |
| `ollama-hardware` | [Ollama Hardware support](../references/files/documents/ollama-hardware.html) | 5,9 | 补充／版本参照 | 已归档 |
| `ollama-api-generate` | [Ollama Generate API](../references/files/documents/ollama-api-generate.md) | 5,9 | 章末 8 | 已归档 |
| `ollama-metal-device` | [Ollama v0.20.7 Apple device and working-set discovery](../references/files/documents/ollama-metal-device.txt) | 5,9 | 章末 5 | 已归档 |
| `kt-kernel-guide` | [KT-Kernel inference README — fixed revision](../references/files/documents/kt-kernel-guide.md) | 5,9,10 | 章末 9 | 已归档 |
| `kt-amx` | [KTransformers 0.3 AMX design notes](../references/files/documents/kt-amx.md) | 4,5,10 | 章末 5,9 | 已归档 |
| `ktransformers-paper` | [KTransformers: Unleashing the Full Potential of CPU/GPU Hybrid Inference for MoE Models](../references/files/papers/ktransformers-paper.pdf) | 5,9,10 | 章末 9 | 已归档 |
| `nvidia-a100-80-spec` | [NVIDIA A100 80GB datasheet — December 2020](../references/files/specs/nvidia-a100-80-spec.pdf) | 4,10 | 章末 9 | 已归档 |
| `nvidia-h20-vgpu` | [NVIDIA AI Enterprise 6.2 supported H20 SXM5 configurations](../references/files/specs/nvidia-h20-vgpu.html) | 4,10 | 章末 9 | 已归档 |
| `bullet` | [Bullet: Boosting GPU Utilization for LLM Serving via Dynamic Spatial-Temporal Orchestration](../references/files/papers/bullet.pdf) | 4,9,10 | 补充／版本参照 | 已归档 |
| `heterogeneous-pd` | [Demystifying the Design Space and Best Practices for Heterogeneous LLM Inference and Serving](../references/files/papers/heterogeneous-pd.pdf) | 10 | 章末 9 | 已归档 |
| `ollama-ggml-metal-memory` | [Ollama v0.20.7 bundled ggml Metal device and buffers](../references/files/documents/ollama-ggml-metal-memory.txt) | 5,9 | 章末 5 | 已归档 |
| `ollama-ggml-metal-kernels` | [Ollama v0.20.7 bundled ggml Metal kernels](../references/files/documents/ollama-ggml-metal-kernels.txt) | 4,5,9 | 章末 4,5 | 已归档 |
| `kt-kml-build` | [KT-Kernel CMake ARM KML build path](../references/files/documents/kt-kml-build.txt) | 5,10 | 补充／版本参照 | 已归档 |
| `kt-kml-example` | [KT-Kernel KML MoE correctness example](../references/files/documents/kt-kml-example.txt) | 5,10 | 补充／版本参照 | 已归档 |
| `scaling-inference` | [Efficiently Scaling Transformer Inference](../references/files/papers/scaling-inference.pdf) | 3,4,10,13 | 章末 9 | 已归档 |
| `deepspeed-inference` | [DeepSpeed Inference: Enabling Efficient Inference of Transformer Models at Unprecedented Scale](../references/files/papers/deepspeed-inference.pdf) | 5,9,10 | 章末 9 | 已归档 |
| `deepspeed-fastgen` | [DeepSpeed-FastGen: High-throughput Text Generation for LLMs via MII and DeepSpeed-Inference](../references/files/papers/deepspeed-fastgen.pdf) | 9 | 补充／版本参照 | 已归档 |
| `flashinfer` | [FlashInfer: Efficient and Customizable Attention Engine for LLM Inference Serving](../references/files/papers/flashinfer.pdf) | 5,9 | 补充／版本参照 | 已归档 |
| `kivi` | [KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache](../references/files/papers/kivi.pdf) | 5,9 | 章末 8 | 已归档 |
| `h2o` | [H$_2$O: Heavy-Hitter Oracle for Efficient Generative Inference of Large Language Models](../references/files/papers/h2o.pdf) | 9 | 章末 8 | 已归档 |
| `streamingllm` | [Efficient Streaming Language Models with Attention Sinks](../references/files/papers/streamingllm.pdf) | 2,9 | 章末 8 | 已归档 |
| `speculative-sampling` | [Accelerating Large Language Model Decoding with Speculative Sampling](../references/files/papers/speculative-sampling.pdf) | 9 | 章末 8 | 已归档 |
| `medusa` | [Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads](../references/files/papers/medusa.pdf) | 9 | 补充／版本参照 | 已归档 |
| `eagle` | [EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty](../references/files/papers/eagle.pdf) | 9 | 补充／版本参照 | 已归档 |
| `eagle3` | [EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test](../references/files/papers/eagle3.pdf) | 9 | 章末 8 | 已归档 |
| `preble` | [Preble: Efficient Distributed Prompt Scheduling for LLM Serving](../references/files/papers/preble.pdf) | 10 | 章末 9 | 已归档 |
| `lmcache` | [LMCache: An Efficient KV Cache Layer for Enterprise-Scale LLM Inference](../references/files/papers/lmcache.pdf) | 9,10 | 章末 8,9 | 已归档 |
| `s-lora` | [S-LoRA: Serving Thousands of Concurrent LoRA Adapters](../references/files/papers/s-lora.pdf) | 9,12 | 章末 11 | 已归档 |
| `alpaserve` | [AlpaServe: Statistical Multiplexing with Model Parallelism for Deep Learning Serving](../references/files/papers/alpaserve.pdf) | 10,12 | 章末 11 | 已归档 |
| `fastserve` | [Fast Distributed Inference Serving for Large Language Models](../references/files/papers/fastserve.pdf) | 9,12 | 补充／版本参照 | 已归档 |
| `llm-int8` | [LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale](../references/files/papers/llm-int8.pdf) | 5,9 | 补充／版本参照 | 已归档 |
| `qwen3` | [Qwen3 Technical Report](../references/files/papers/qwen3.pdf) | 2,3,13 | 章末 2,3 | 已归档 |
| `mixtral` | [Mixtral of Experts](../references/files/papers/mixtral.pdf) | 2,10 | 补充／版本参照 | 已归档 |
| `deepseek-r1` | [DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](../references/files/papers/deepseek-r1.pdf) | 3,11,13 | 章末 3,10 | 已归档 |
| `test-time-compute` | [Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters](../references/files/papers/test-time-compute.pdf) | 3,13 | 章末 3,13 | 已归档 |
| `deepseek-infra` | [Insights into DeepSeek-V3: Scaling Challenges and Reflections on Hardware for AI Architectures](../references/files/papers/deepseek-infra.pdf) | 6,10,13 | 章末 7,9 | 已归档 |
| `deepseek-serving-report` | [Day 6: DeepSeek-V3/R1 Inference System Overview](../references/files/documents/deepseek-serving-report.md) | 6,10,13 | 补充／版本参照 | 已归档 |
| `dynamo-production` | [How NVIDIA Dynamo 1.0 Powers Multi-Node Inference at Production Scale](../references/files/documents/dynamo-production.html) | 10,12 | 补充／版本参照 | 已归档 |
| `tensorrt-llm-architecture` | [TensorRT LLM Architecture Overview](../references/files/documents/tensorrt-llm-architecture.html) | 5,9,10 | 补充／版本参照 | 已归档 |
| `bojieli-phd-thesis` | [基于可编程网卡的高性能数据中心系统](../references/files/papers/bojieli-phd-thesis.pdf) | 1,4,5,7,13 | 章末 1,7 | 作者提供 |
| `logicfolding-energy` | [Huawei’s τ Chip Was Supposed to Melt?](../references/files/papers/202609.00031v1.pdf) | 1,4,13 | 扩写 13 | 作者提供 |
| `otel-genai-current` | [OpenTelemetry GenAI metrics — fixed commit](../references/outline-checks/2026-09-07/otel-genai-metrics.md) | 12 | 补充／版本参照 | 已归档 |
| `beyond-chinchilla-v1` | [Beyond Chinchilla-Optimal，arXiv v1](../references/outline-checks/2026-09-07/beyond-chinchilla-v1.html) | 新增 | 章末 3 | 已归档 |
| `beyond-chinchilla-pmlr` | [Beyond Chinchilla-Optimal，ICML 2024 发表页](../references/outline-checks/2026-09-07/beyond-chinchilla-pmlr.html) | 新增 | 补充／版本参照 | 已归档 |
| `rfc9001` | [RFC 9001](../references/outline-checks/2026-09-07/rfc9001.txt) | 新增 | 章末 12 | 已归档 |
| `rfc9221` | [RFC 9221](../references/outline-checks/2026-09-07/rfc9221.txt) | 新增 | 章末 12 | 已归档 |
| `beyond-chinchilla-icml24` | [Beyond Chinchilla-Optimal，ICML 2024 正式全文](../references/outline-checks/2026-09-07/beyond-chinchilla-icml24.pdf) | 新增 | 章末 3,13 | 已归档 |
| `llama1-v1` | [LLaMA 原始技术报告 v1](../references/outline-checks/2026-09-07/scaling-history/llama1-v1.pdf) | 补充 | 章末 2,3 | 已归档；固定快照 |
| `qwen25-v2` | [Qwen2.5 技术报告 v2](../references/outline-checks/2026-09-07/scaling-history/qwen25-v2.pdf) | 补充 | 章末 3 | 已归档；固定快照 |
| `llama31-card` | [Llama 3.1 官方模型卡](../references/outline-checks/2026-09-07/scaling-history/llama31-card.md) | 补充 | 章末 3 | 已归档；固定快照 |
| `qwen35-blog` | [Qwen3.5 官方发布与训练说明](../references/outline-checks/2026-09-07/scaling-history/qwen35-blog.html) | 补充 | 章末 3 | 已归档；固定快照 |
| `kimi-k15-v4` | [Kimi k1.5 report v4](../references/outline-checks/2026-09-07/scaling-history/kimi-k15-v4.pdf) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `jeff-dean-ladis2009` | [Jeff Dean LADIS 2009 original slides (Columbia mirror)](../references/outline-checks/2026-09-07/scaling-history/jeff-dean-ladis2009.pdf) | 补充 | 章末 1 | 已归档；固定快照 |
| `qwen3-8b-config` | [qwen3-8b official configuration at b968826d9c46dd6066d109eabc6255188de91218](../references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json) | 补充 | 章末 2,6 | 已归档；固定快照 |
| `deepseek-v4-flash-config` | [deepseek-v4-flash official configuration at 60d8d70770c6776ff598c94bb586a859a38244f1](../references/outline-checks/2026-09-07/scaling-history/deepseek-v4-flash-config.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `deepseek-v4-flash-config.json` | [deepseek-v4-flash reference inference/config.json](../references/outline-checks/2026-09-07/scaling-history/deepseek-v4-flash-inference-config.json) | 补充 | 章末 2 | 已归档；固定快照 |
| `deepseek-v4-flash-model.py` | [deepseek-v4-flash reference inference/model.py](../references/outline-checks/2026-09-07/scaling-history/deepseek-v4-flash-inference-model.py) | 补充 | 章末 2,5 | 已归档；固定快照 |
| `vllm-qwen3` | [vLLM qwen3 model implementation at 58ad1f3b8973b23943107b51230d594050b42ec3](../references/outline-checks/2026-09-07/scaling-history/vllm-qwen3.py) | 补充 | 章末 2,5 | 已归档；固定快照 |
| `vllm-deepseek_v2` | [vLLM deepseek_v2 model implementation at 58ad1f3b8973b23943107b51230d594050b42ec3](../references/outline-checks/2026-09-07/scaling-history/vllm-deepseek_v2.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-qwen2` | [vLLM Qwen2 MLP implementation reused by Qwen3](../references/outline-checks/2026-09-07/scaling-history/vllm-qwen2.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `qwen3-235b-config` | [Qwen3-235B-A22B official configuration](../references/outline-checks/2026-09-07/scaling-history/qwen3-235b-config.json) | 补充 | 章末 2,6 | 已归档；固定快照 |
| `a800-lenovo` | [ThinkSystem A800 PCIe product guide](../references/outline-checks/2026-09-07/systems-cases/a800-lenovo.pdf) | 补充 | 章末 10 | 已归档；固定快照 |
| `nvidia-hgx` | [NVIDIA HGX platform specifications](../references/outline-checks/2026-09-07/systems-cases/nvidia-hgx.html) | 补充 | 章末 10 | 已归档；固定快照 |
| `eagle31` | [EAGLE 3.1 — EAGLE, vLLM, TorchSpec teams](../references/outline-checks/2026-09-07/systems-cases/eagle31.html) | 补充 | 章末 8 | 已归档；固定快照 |
| `dflash-paper` | [DFlash paper v1](../references/outline-checks/2026-09-07/systems-cases/dflash-paper.pdf) | 补充 | 章末 8 | 已归档；固定快照 |
| `dflash2` | [DFlash 2 — Inco AI](../references/outline-checks/2026-09-07/systems-cases/dflash2.html) | 补充 | 章末 8 | 已归档；固定快照 |
| `mimo-tilert` | [Xiaomi MiMo V2.5 Pro — FP4 and DFlash](../references/outline-checks/2026-09-07/systems-cases/mimo-tilert.html) | 补充 | 章末 8 | 已归档；固定快照 |
| `kt-v4` | [KTransformers V4 Flash tutorial — fixed revision](../references/outline-checks/2026-09-07/systems-cases/kt-v4.md) | 补充 | 章末 9 | 已归档；固定快照 |
| `kt-kimi2` | [KTransformers Kimi K2 tutorial — fixed revision](../references/outline-checks/2026-09-07/systems-cases/kt-kimi2.md) | 补充 | 章末 9 | 已归档；固定快照 |
| `kt-sft` | [KTransformers fine tuning cookbook — fixed revision](../references/outline-checks/2026-09-07/systems-cases/kt-sft.md) | 补充 | 章末 10 | 已归档；固定快照 |
| `qwen235-gguf-metadata` | [Unsloth Qwen3-235B GGUF file metadata](../references/outline-checks/2026-09-07/systems-cases/qwen235-gguf-metadata.json) | 补充 | 章末 8 | 已归档；固定快照 |
| `unsloth-r1-metadata` | [Unsloth DeepSeek R1 GGUF file metadata](../references/outline-checks/2026-09-07/systems-cases/unsloth-r1-metadata.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `dflash-revision` | [DFlash repository revision](../references/outline-checks/2026-09-07/systems-cases/dflash-revision.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `dflash-readme` | [DFlash repository README — fixed revision](../references/outline-checks/2026-09-07/systems-cases/dflash-readme.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `qwen235-gguf-readme` | [unsloth/Qwen3-235B-A22B-GGUF model card at 09e11417ffdc30c1c63d0296a40fd8fde0abb180](../references/outline-checks/2026-09-07/systems-cases/qwen235-gguf-readme.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `r1-gguf-readme` | [unsloth/DeepSeek-R1-GGUF model card at 4dab99fdb3fea560e5a402b49c6ef11e025321a8](../references/outline-checks/2026-09-07/systems-cases/r1-gguf-readme.md) | 补充 | 章末 8 | 已归档；固定快照 |
| `apple-m3-evolution` | [Apple M3 GPU local-memory allocation](../references/outline-checks/2026-09-07/systems-cases/apple-m3-evolution.html) | 补充 | 章末 4 | 已归档；固定快照 |
| `apple-m5-evolution` | [Apple M5 GPU Neural Accelerators](../references/outline-checks/2026-09-07/systems-cases/apple-m5-evolution.html) | 补充 | 章末 4 | 已归档；固定快照 |
| `nvidia-h200-systems` | [NVIDIA H200 official specifications](../references/outline-checks/2026-09-07/systems-cases/nvidia-h200-systems.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `cutlass-blackwell` | [CUTLASS SM100 and SM120 distinctions](../references/outline-checks/2026-09-07/systems-cases/cutlass-blackwell.html) | 补充 | 章末 4 | 已归档；固定快照 |
| `rubin-rechecked` | [Rubin architecture official article — rechecked](../references/outline-checks/2026-09-07/systems-cases/rubin-rechecked.html) | 补充 | 章末 4 | 已归档；固定快照 |
| `cutlass-revision` | [CUTLASS repository revision](../references/outline-checks/2026-09-07/systems-cases/cutlass-revision.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `cutlass-01_mma_sm100` | [CUTLASS 01_mma_sm100 fixed example](../references/outline-checks/2026-09-07/systems-cases/cutlass-01_mma_sm100.cu) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `cutlass-04_mma_tma_2sm_sm100` | [CUTLASS 04_mma_tma_2sm_sm100 fixed example](../references/outline-checks/2026-09-07/systems-cases/cutlass-04_mma_tma_2sm_sm100.cu) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `raw-huawei-pro` | [华为：使用专业模式拍摄](../references/outline-checks/2026-09-07/edge-media/huawei-pro-raw.html) | 补充 | 章末 12 | 已归档；固定快照 |
| `raw-adobe-indigo` | [Adobe Research：Project Indigo 图像处理路径](../references/outline-checks/2026-09-07/edge-media/adobe-indigo.html) | 补充 | 章末 12 | 已归档；固定快照 |
| `raw-adobe-dng-compression` | [Adobe：DNG Pros, Cons and Myths](../references/outline-checks/2026-09-07/edge-media/adobe-dng-compression.html) | 补充 | 章末 12 | 已归档；固定快照 |
| `edge-http3-rfc9114` | [RFC 9114：HTTP/3](../references/outline-checks/2026-09-07/edge-media/rfc9114.txt) | 补充 | 章末 12 | 已归档；固定快照 |
| `model-linear-transformer` | [Linear Transformers：作者项目说明](../references/outline-checks/2026-09-07/edge-media/linear-transformers.html) | 补充 | 章末 2 | 已归档；固定快照 |
| `quantitative-architecture-publisher` | [Computer Architecture: A Quantitative Approach，第六版出版说明](../references/outline-checks/2026-09-07/edge-media/quantitative-architecture.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `accounting-kimi-k3-revision-json` | [kimi-k3-revision.json](../references/outline-checks/2026-09-07/model-accounting/kimi-k3-revision.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `accounting-kimi-k3-config-json` | [kimi-k3-config.json](../references/outline-checks/2026-09-07/model-accounting/kimi-k3-config.json) | 补充 | 章末 2 | 已归档；固定快照 |
| `accounting-kimi-k3-modeling_kimi_linear-py` | [Kimi K3 modeling_kimi_linear.py](../references/outline-checks/2026-09-07/model-accounting/kimi-k3-modeling_kimi_linear.py) | 补充 | 章末 2 | 已归档；固定快照 |
| `accounting-kimi-k3-configuration_kimi_k3-py` | [Kimi K3 configuration_kimi_k3.py](../references/outline-checks/2026-09-07/model-accounting/kimi-k3-configuration_kimi_k3.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `claude-api-pricing-20260907` | [Claude API 计价，2026-09-07 快照](../references/outline-checks/2026-09-07/platform-routing/claude-api-pricing.html) | 补充 | 章末 11 | 已归档；固定快照 |
| `claude-plans-20260907` | [Claude 订阅方案，2026-09-07 快照](../references/outline-checks/2026-09-07/platform-routing/claude-plans.html) | 补充 | 章末 11 | 已归档；固定快照 |
| `claude-prompt-cache` | [Claude：Prompt caching](../references/outline-checks/2026-09-07/platform-routing/claude-prompt-cache.html) | 补充 | 章末 11 | 已归档；固定快照 |
| `claude-subscription-api` | [Claude：订阅与 API 分开计费](../references/outline-checks/2026-09-07/platform-routing/claude-subscription-api.html) | 补充 | 章末 11 | 已归档；固定快照 |
| `e2b-infra-architecture` | [E2B infra 架构，固定提交 1f34e5d6c822](../references/outline-checks/2026-09-07/platform-routing/e2b-architecture.md) | 补充 | 章末 11 | 已归档；固定快照 |
| `e2b-infra-revision` | [E2B infra 固定版本信息](../references/outline-checks/2026-09-07/platform-routing/e2b-infra-revision.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `e2b-persistence` | [E2B：Sandbox persistence](../references/outline-checks/2026-09-07/platform-routing/e2b-persistence.html) | 补充 | 章末 11 | 已归档；固定快照 |
| `e2b-sandbox` | [E2B：Sandbox](../references/outline-checks/2026-09-07/platform-routing/e2b-sandbox.html) | 补充 | 章末 11 | 已归档；固定快照 |
| `e2b-snapshots` | [E2B：Snapshots](../references/outline-checks/2026-09-07/platform-routing/e2b-snapshots.html) | 补充 | 章末 11 | 已归档；固定快照 |
| `gemini-api-pricing-20260907` | [Gemini API 计价，2026-09-07 快照](../references/outline-checks/2026-09-07/platform-routing/gemini-api-pricing.html) | 补充 | 章末 11 | 已归档；固定快照 |
| `gemini-cache` | [Gemini：Context caching](../references/outline-checks/2026-09-07/platform-routing/gemini-cache.html) | 补充 | 章末 11 | 已归档；固定快照 |
| `google-ai-plans-20260907` | [Google AI 订阅方案，2026-09-07 快照](../references/outline-checks/2026-09-07/platform-routing/google-ai-plans.html) | 补充 | 章末 11 | 已归档；固定快照 |
| `scheduling-asi26` | [ASI：异构生产 AI 集群与 SpotGPU，OSDI 2026](../references/outline-checks/2026-09-07/platform-routing/asi-osdi26.pdf) | 补充 | 章末 11 | 已归档；固定快照 |
| `scheduling-distrs26` | [DistRS，NSDI 2026](../references/outline-checks/2026-09-07/platform-routing/distrs-nsdi26.pdf) | 补充 | 章末 11 | 已归档；固定快照 |
| `scheduling-rlboost26` | [RLBoost，NSDI 2026](../references/outline-checks/2026-09-07/platform-routing/rlboost-nsdi26.pdf) | 补充 | 章末 11 | 已归档；固定快照 |
| `scheduling-specbox-v2` | [SpecBox，arXiv v2，2026-08-05](../references/outline-checks/2026-09-07/platform-routing/specbox-v2.html) | 补充 | 章末 11 | 已归档；固定快照 |
| `ansor-osdi20` | [Ansor，OSDI 2020](../references/outline-checks/2026-09-07/execution-feedback/ansor.pdf) | 补充 | 章末 5 | 已归档；固定快照 |
| `cuda-agent26` | [CUDA Agent，2026 v1](../references/outline-checks/2026-09-07/execution-feedback/cuda-agent.pdf) | 补充 | 章末 5 | 已归档；固定快照 |
| `flashinfer-bench26` | [FlashInfer-Bench，2026 v1](../references/outline-checks/2026-09-07/execution-feedback/flashinfer-bench.html) | 补充 | 章末 5 | 已归档；固定快照 |
| `kernelagent26` | [KernelAgent：基于硬件反馈的自动优化，2026-03](../references/outline-checks/2026-09-07/execution-feedback/kernelagent.html) | 补充 | 章末 5 | 已归档；固定快照 |
| `megascale-infer25` | [MegaScale-Infer，2025 v1](../references/outline-checks/2026-09-07/execution-feedback/megascale-infer.pdf) | 补充 | 章末 9 | 已归档；固定快照 |
| `megatron-moe26` | [Scalable Training of MoE with Megatron Core，2026 v1](../references/outline-checks/2026-09-07/execution-feedback/megatron-moe26.html) | 补充 | 章末 10 | 已归档；固定快照 |
| `mpk26-v2` | [MPK，2026-06 v2](../references/outline-checks/2026-09-07/execution-feedback/mpk-v2.html) | 补充 | 章末 5 | 已归档；固定快照 |
| `nanoflow-osdi25` | [NanoFlow，OSDI 2025](../references/outline-checks/2026-09-07/execution-feedback/nanoflow.pdf) | 补充 | 章末 8 | 已归档；固定快照 |
| `nemo-automodel-r3` | [NeMo AutoModel：离散路由重放与梯度](../references/outline-checks/2026-09-07/execution-feedback/nemo-automodel-replay.html) | 补充 | 章末 10 | 已归档；固定快照 |
| `nemo-r3-guide26` | [NeMo RL Router Replay 官方实现文档快照](../references/outline-checks/2026-09-07/execution-feedback/nemo-router-replay.html) | 补充 | 章末 10 | 已归档；固定快照 |
| `r3-router25-v2` | [Stabilizing MoE RL by Aligning Training and Inference Routers，v2](../references/outline-checks/2026-09-07/execution-feedback/routing-replay.html) | 补充 | 章末 10 | 已归档；固定快照 |
| `sglang-ep26` | [SGLang EP、重叠与 EPLB](../references/outline-checks/2026-09-07/execution-feedback/sglang-ep.html) | 补充 | 章末 9 | 已归档；固定快照 |
| `sglang-hicache26` | [SGLang HiCache 官方实现](../references/outline-checks/2026-09-07/execution-feedback/sglang-hicache.html) | 补充 | 章末 9 | 已归档；固定快照 |
| `tensorrt-quickstart26` | [TensorRT Quick Start Guide](../references/outline-checks/2026-09-07/execution-feedback/tensorrt-quickstart.html) | 补充 | 章末 8 | 已归档；固定快照 |
| `trtllm-overview26` | [TensorRT-LLM Overview](../references/outline-checks/2026-09-07/execution-feedback/trtllm-overview.html) | 补充 | 章末 8 | 已归档；固定快照 |
| `tvm-meta-schedule26` | [TVM MetaSchedule 官方调优文档](../references/outline-checks/2026-09-07/execution-feedback/tvm-meta-schedule.html) | 补充 | 章末 5 | 已归档；固定快照 |
| `verl-overview26` | [verl 官方文档与后端入口](../references/outline-checks/2026-09-07/execution-feedback/verl-overview.html) | 补充 | 章末 10 | 已归档；固定快照 |
| `vllm-dbo26` | [vLLM Dual Batch Overlap](../references/outline-checks/2026-09-07/execution-feedback/vllm-dbo.html) | 补充 | 章末 9 | 已归档；固定快照 |
| `vllm-ep26` | [vLLM Expert Parallel Deployment](../references/outline-checks/2026-09-07/execution-feedback/vllm-ep.html) | 补充 | 章末 9 | 已归档；固定快照 |
| `vllm-graphs26` | [vLLM CUDA Graphs design](../references/outline-checks/2026-09-07/execution-feedback/vllm-graphs.html) | 补充 | 章末 5,8 | 已归档；固定快照 |
| `ollama-mlx-2026` | [Ollama MLX 预览，2026-03](../references/outline-checks/2026-09-07/framework-evolution/ollama-mlx.html) | 补充 | 章末 5,8 | 已归档；固定快照 |
| `ollama-mtp-2026` | [Ollama MLX 多 token 预测，2026-06](../references/outline-checks/2026-09-07/framework-evolution/ollama-mtp.html) | 补充 | 章末 5,8 | 已归档；固定快照 |
| `ollama-multimodal-2025` | [Ollama 多模态执行引擎，2025-05](../references/outline-checks/2026-09-07/framework-evolution/ollama-multimodal.html) | 补充 | 章末 12 | 已归档；固定快照 |
| `ollama-schedule-2025` | [Ollama 新内存调度，2025-09](../references/outline-checks/2026-09-07/framework-evolution/ollama-scheduling.html) | 补充 | 章末 8 | 已归档；固定快照 |
| `ollama-stream-tool-2025` | [Ollama 流式工具调用，2025-05](../references/outline-checks/2026-09-07/framework-evolution/ollama-stream-tool.html) | 补充 | 章末 11,12 | 已归档；固定快照 |
| `sglang-graph-2026` | [SGLang Advanced CUDA Graph，2026-08](../references/outline-checks/2026-09-07/framework-evolution/sglang-graphs.html) | 补充 | 章末 5,8 | 已归档；固定快照 |
| `sglang-hicache-2025` | [SGLang HiCache，2025-09](../references/outline-checks/2026-09-07/framework-evolution/sglang-hicache.html) | 补充 | 章末 9 | 已归档；固定快照 |
| `sglang-hisparse-2026` | [SGLang HiSparse，2026-04](../references/outline-checks/2026-09-07/framework-evolution/sglang-hisparse.html) | 补充 | 章末 9 | 已归档；固定快照 |
| `sglang-unified-cache-2026` | [SGLang Unified Radix Cache，2026-08](../references/outline-checks/2026-09-07/framework-evolution/sglang-unified-cache.html) | 补充 | 章末 8,9 | 已归档；固定快照 |
| `sglang-v04-2024` | [SGLang v0.4，2024-12](../references/outline-checks/2026-09-07/framework-evolution/sglang-v04.html) | 补充 | 章末 8 | 已归档；固定快照 |
| `vllm-afd-2026` | [vLLM AFD Plugin，2026-07](../references/outline-checks/2026-09-07/framework-evolution/vllm-afd.html) | 补充 | 章末 9 | 已归档；固定快照 |
| `vllm-sleep-2026` | [vLLM Sleep Mode 官方文档快照](../references/outline-checks/2026-09-07/framework-evolution/vllm-sleep.html) | 补充 | 章末 10 | 已归档；固定快照 |
| `vllm-v1-2025` | [vLLM V1 架构与当前指南](../references/outline-checks/2026-09-07/framework-evolution/vllm-v1.html) | 补充 | 章末 8,10 | 已归档；固定快照 |
| `vllm-wide-ep-2025` | [vLLM 大规模服务，2025-12](../references/outline-checks/2026-09-07/framework-evolution/vllm-wide-ep.html) | 补充 | 章末 9 | 已归档；固定快照 |
| `mlsys2024-054de805fcceb78a201f5e9d53c85908` | [Punica: Multi-Tenant LoRA Serving](../references/proceedings/MLSys/2024/papers/mlsys2024-054de805fcceb78a201f5e9d53c85908.pdf) | 补充 | 章末 8 | 已归档；固定快照 |
| `mlsys2024-906419cd502575b617cc489a1a696a67` | [SLoRA: Scalable Serving of Thousands of LoRA Adapters](../references/proceedings/MLSys/2024/papers/mlsys2024-906419cd502575b617cc489a1a696a67.pdf) | 补充 | 章末 8 | 已归档；固定快照 |
| `sglang-lora` | [SGLang LoRA Serving](../references/framework-history/2026-09-07/lora/sglang-lora.html) | 补充 | 章末 8 | 已归档；固定快照 |
| `ollama-modelfile` | [Ollama Modelfile](../references/framework-history/2026-09-07/lora/ollama-modelfile.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-lora-revision` | [vLLM LoRA document revision](../references/framework-history/2026-09-07/lora/vllm-lora-revision.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-lora` | [vLLM LoRA document at fixed revision](../references/framework-history/2026-09-07/lora/vllm-lora.md) | 补充 | 章末 8 | 已归档；固定快照 |
| `mlsys2025-26289c647c6828e862e271ca3c490486` | [Rethinking Key-Value Cache Compression Techniques for Large Language Model Serving](../references/proceedings/MLSys/2025/papers/mlsys2025-26289c647c6828e862e271ca3c490486.pdf) | 补充 | 章末 8 | 已归档；固定快照 |
| `mlsys2025-270339c997293ca2988c62f4308e389f` | [Rubick: Exploiting Job Reconfigurability for Deep Learning Cluster Scheduling](../references/proceedings/MLSys/2025/papers/mlsys2025-270339c997293ca2988c62f4308e389f.pdf) | 补充 | 章末 11 | 已归档；固定快照 |
| `mlsys2025-7c180af017258d239bac6248d1eb26ac` | [Marconi: Prefix Caching for the Era of Hybrid LLMs](../references/proceedings/MLSys/2025/papers/mlsys2025-7c180af017258d239bac6248d1eb26ac.pdf) | 补充 | 章末 8 | 已归档；固定快照 |
| `mlsys2025-dbf02b21d77409a2db30e56866a8ab3a` | [FlashInfer: Efficient and Customizable Attention Engine for LLM Inference Serving](../references/proceedings/MLSys/2025/papers/mlsys2025-dbf02b21d77409a2db30e56866a8ab3a.pdf) | 补充 | 章末 5 | 已归档；固定快照 |
| `flashinfer-attention-api-20260907` | [FlashInfer Attention API — retrieved 2026-09-07](../references/framework-history/2026-09-07/flashinfer/attention.html) | 补充 | 章末 5 | 已归档；固定快照 |
| `mlsys2026-29416b66c2149872b9d1415a3fd2c5e0` | [Breaking the Ice: Analyzing Cold Start Latency in vLLM](../references/proceedings/MLSys/2026/papers/mlsys2026-29416b66c2149872b9d1415a3fd2c5e0.pdf) | 补充 | 章末 9 | 已归档；固定快照 |
| `mlsys2026-3a7f9e485845dac27423375c934cb4db` | [CRAFT: Fine-Grained Cost-Aware Expert Replication For Efficient Mixture-of-Experts Serving](../references/proceedings/MLSys/2026/papers/mlsys2026-3a7f9e485845dac27423375c934cb4db.pdf) | 补充 | 章末 9 | 已归档；固定快照 |
| `mlsys2026-42a452cbafa9dd64e9ba4aa95cc1ef21` | [Demystifying the Mixture of Experts Serving Tax](../references/proceedings/MLSys/2026/papers/mlsys2026-42a452cbafa9dd64e9ba4aa95cc1ef21.pdf) | 补充 | 章末 6,9 | 已归档；固定快照 |
| `startup-profiler-revision-json` | [profiler-revision.json](../references/framework-history/2026-09-07/startup/profiler-revision.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `startup-profiler-readme-md` | [profiler-readme.md](../references/framework-history/2026-09-07/startup/profiler-readme.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `startup-profiler-log-py` | [profiler-log.py](../references/framework-history/2026-09-07/startup/profiler-log.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `startup-profiler-apply-py` | [profiler-apply.py](../references/framework-history/2026-09-07/startup/profiler-apply.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `startup-vllm-revision-json` | [vllm-revision.json](../references/framework-history/2026-09-07/startup/vllm-revision.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `startup-vllm-compile-md` | [vllm-compile.md](../references/framework-history/2026-09-07/startup/vllm-compile.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `mlsys2026-ae8b0b5838ba510daff1198474e7b984` | [FlashAttention-4: Algorithm and Kernel Pipelining Co-Design for Asymmetric Hardware Scaling](../references/proceedings/MLSys/2026/papers/mlsys2026-ae8b0b5838ba510daff1198474e7b984.pdf) | 补充 | 章末 4,5 | 已归档；固定快照 |
| `mlsys2026-fbe2b2f74a2ece8070d8fb073717bda6` | [Machine Learning Fleet Efficiency: Improving TPU Systems at Scale with ML Productivity Goodput](../references/proceedings/MLSys/2026/papers/mlsys2026-fbe2b2f74a2ece8070d8fb073717bda6.pdf) | 补充 | 章末 10 | 已归档；固定快照 |
| `fa4-commit` | [Dao-AILab/flash-attention current commit](../references/framework-history/2026-09-08/attention/fa4-commit.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `fa4-readme` | [Dao-AILab/flash-attention flash_attn/cute/README.md](../references/framework-history/2026-09-08/attention/fa4-readme.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `fa4-forward` | [Dao-AILab/flash-attention flash_attn/cute/flash_fwd_sm100.py](../references/framework-history/2026-09-08/attention/fa4-forward.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `fa4-softmax` | [Dao-AILab/flash-attention flash_attn/cute/softmax.py](../references/framework-history/2026-09-08/attention/fa4-softmax.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-commit` | [sgl-project/sglang current commit](../references/framework-history/2026-09-08/attention/sglang-commit.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-hybrid` | [sgl-project/sglang python/sglang/srt/layers/attention/hybrid_attn_backend.py](../references/framework-history/2026-09-08/attention/sglang-hybrid.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-fa` | [sgl-project/sglang python/sglang/srt/layers/attention/flashattention_backend.py](../references/framework-history/2026-09-08/attention/sglang-fa.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-commit` | [vllm-project/vllm current commit](../references/framework-history/2026-09-08/attention/vllm-commit.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-fa` | [vllm-project/vllm vllm/v1/attention/backends/flash_attn.py](../references/framework-history/2026-09-08/attention/vllm-fa.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-fa-utils` | [vllm-project/vllm vllm/v1/attention/backends/fa_utils.py](../references/framework-history/2026-09-08/attention/vllm-fa-utils.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-attention-doc` | [vllm-attention-doc](../references/framework-history/2026-09-08/attention/vllm-attention-doc.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-attention-doc` | [sglang-attention-doc](../references/framework-history/2026-09-08/attention/sglang-attention-doc.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `osdi24-agrawal` | [Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve](../references/proceedings/OSDI/2024/selected/osdi24-agrawal.pdf) | 补充 | 章末 8 | 已归档；固定快照 |
| `osdi24-sun-biao` | [Llumnix: Dynamic Scheduling for Large Language Model Serving](../references/proceedings/OSDI/2024/selected/osdi24-sun-biao.pdf) | 补充 | 章末 9 | 已归档；固定快照 |
| `osdi24-zhong-yinmin` | [DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving](../references/proceedings/OSDI/2024/selected/osdi24-zhong-yinmin.pdf) | 补充 | 章末 9 | 已归档；固定快照 |
| `vllm-v042-commit` | [vLLM v0.4.2 source commit](../references/framework-history/2026-09-08/chunk-scheduling/vllm-v042-commit.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-v042-scheduler` | [vLLM v0.4.2 scheduling implementation](../references/framework-history/2026-09-08/chunk-scheduling/vllm-v042-scheduler.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-v080-commit` | [vLLM v0.8.0 source commit](../references/framework-history/2026-09-08/chunk-scheduling/vllm-v080-commit.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-v080-scheduler` | [vLLM v0.8.0 scheduling implementation](../references/framework-history/2026-09-08/chunk-scheduling/vllm-v080-scheduler.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-v042-tuning` | [vllm-v042-tuning](../references/framework-history/2026-09-08/chunk-scheduling/vllm-v042-tuning.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-current-tuning` | [vllm-current-tuning](../references/framework-history/2026-09-08/chunk-scheduling/vllm-current-tuning.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-current-scheduler` | [vLLM V1 scheduling implementation at current fixed commit](../references/framework-history/2026-09-08/chunk-scheduling/vllm-current-scheduler.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `osdi25-ren` | [Enabling Efficient GPU Communication over Multiple NICs with FuseLink](../references/proceedings/OSDI/2025/selected/osdi25-ren.pdf) | 补充 | 章末 7 | 已归档；固定快照 |
| `osdi25-zhu-kan` | [NanoFlow: Towards Optimal Large Language Model Serving Throughput](../references/proceedings/OSDI/2025/selected/osdi25-zhu-kan.pdf) | 补充 | 章末 5,8 | 已归档；固定快照 |
| `sglang-ep-2025` | [SGLang H100 PD and expert parallelism](../references/framework-history/2026-09-08/overlap-placement/sglang-ep-2025.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-gb200-2025-june` | [SGLang GB200 deployment, part I](../references/framework-history/2026-09-08/overlap-placement/sglang-gb200-2025-june.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-gb200-2025-sept` | [SGLang GB200 deployment, part II](../references/framework-history/2026-09-08/overlap-placement/sglang-gb200-2025-sept.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ollama-memory-2025` | [Ollama new model scheduling announcement](../references/framework-history/2026-09-08/overlap-placement/ollama-memory-2025.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ollama-2024-scheduler-history` | [Ollama scheduler commit query before 2024-10-01T00:00:00Z](../references/framework-history/2026-09-08/overlap-placement/ollama-2024-scheduler-history.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ollama-2024-scheduler` | [Ollama scheduler at fixed historical commit](../references/framework-history/2026-09-08/overlap-placement/ollama-2024-scheduler.go) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ollama-2025-scheduler-history` | [Ollama scheduler commit query before 2025-10-01T00:00:00Z](../references/framework-history/2026-09-08/overlap-placement/ollama-2025-scheduler-history.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ollama-2025-scheduler` | [Ollama scheduler at fixed historical commit](../references/framework-history/2026-09-08/overlap-placement/ollama-2025-scheduler.go) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ollama-current-commit` | [Ollama current commit metadata](../references/framework-history/2026-09-08/overlap-placement/ollama-current-commit.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ollama-current-scheduler` | [Ollama scheduler at fixed current commit](../references/framework-history/2026-09-08/overlap-placement/ollama-current-scheduler.go) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-current-tree` | [SGLang source tree at fixed current commit](../references/framework-history/2026-09-08/overlap-placement/sglang-current-tree.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-two-batch` | [SGLang fixed python/sglang/srt/batch_overlap/two_batch_overlap.py](../references/framework-history/2026-09-08/overlap-placement/sglang-two-batch.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-single-batch` | [SGLang fixed python/sglang/srt/batch_overlap/single_batch_overlap.py](../references/framework-history/2026-09-08/overlap-placement/sglang-single-batch.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-operations-strategy` | [SGLang fixed python/sglang/srt/batch_overlap/operations_strategy.py](../references/framework-history/2026-09-08/overlap-placement/sglang-operations-strategy.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ollama-2024-llm-server` | [Ollama fixed model loading server](../references/framework-history/2026-09-08/overlap-placement/ollama-2024-llm-server.go) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ollama-2025-llm-server` | [Ollama fixed model loading server](../references/framework-history/2026-09-08/overlap-placement/ollama-2025-llm-server.go) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ollama-current-llm-server` | [Ollama fixed model loading server](../references/framework-history/2026-09-08/overlap-placement/ollama-current-llm-server.go) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rl-consistency-thinking-machines-determinism` | [Defeating Nondeterminism in LLM Inference - Thinking Machines Lab](../references/framework-history/2026-09-08/rl-consistency/thinking-machines-determinism.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rl-consistency-sglang-determinism-2025` | [Towards Deterministic Inference in SGLang and Reproducible RL Training - LMSYS Org](../references/framework-history/2026-09-08/rl-consistency/sglang-determinism-2025.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rl-consistency-vllm-batch-invariance-012` | [Batch Invariance — vLLM v0.12.0](../references/framework-history/2026-09-08/rl-consistency/vllm-batch-invariance-012.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rl-consistency-vllm-batch-invariance-current` | [Batch Invariance — vLLM fixed main](../references/framework-history/2026-09-08/rl-consistency/vllm-batch-invariance-current.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rl-consistency-vllm-reproducibility-current` | [Reproducibility — vLLM fixed main](../references/framework-history/2026-09-08/rl-consistency/vllm-reproducibility-current.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rl-consistency-areal-async-current` | [Asynchronous RL — AReaL Documentation](../references/framework-history/2026-09-08/rl-consistency/areal-async-current.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rl-consistency-areal-grpo-current` | [Running GRPO on GSM8K Dataset — AReaL Documentation](../references/framework-history/2026-09-08/rl-consistency/areal-grpo-current.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rl-consistency-sglang-determinism-current` | [Deterministic Inference - SGLang Documentation](../references/framework-history/2026-09-08/rl-consistency/sglang-determinism-current.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rl-consistency-vllm-v012-release` | [vLLM v0.12.0 release metadata](../references/framework-history/2026-09-08/rl-consistency/vllm-v012-release.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `osdi26-wu-tianyuan` | [Weave: Efficient Co-Scheduling for Disaggregated RL Post-Training](../references/proceedings/OSDI/2026/selected/osdi26-wu-tianyuan.pdf) | 补充 | 章末 10 | 已归档；固定快照 |
| `osdi26-chen-zhenqian` | [RobustRL: Role-Based Fault Tolerance System for RL Post-Training](../references/proceedings/OSDI/2026/selected/osdi26-chen-zhenqian.pdf) | 补充 | 章末 10 | 已归档；固定快照 |
| `osdi26-ghosh` | [GraCE: Unlocking CUDA Graphs with Compiler Support for ML Workloads](../references/proceedings/OSDI/2026/selected/osdi26-ghosh.pdf) | 补充 | 章末 5 | 已归档；固定快照 |
| `nsdi24-hou` | [Understanding Routable PCIe Performance for Composable Infrastructures](../references/proceedings/NSDI/2024/selected/nsdi24-hou.pdf) | 补充 | 章末 7 | 已归档；固定快照 |
| `nsdi24-jiang-ziheng` | [MegaScale: Scaling Large Language Model Training to More Than 10,000 GPUs](../references/proceedings/NSDI/2024/selected/nsdi24-jiang-ziheng.pdf) | 补充 | 章末 7,10 | 已归档；固定快照 |
| `collective-vllm-060-custom-ar` | [vllm-project/vllm vllm/distributed/device_communicators/custom_all_reduce.py at v0.6.0](../references/framework-history/2026-09-08/collective-paths/vllm-060-custom-ar.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `collective-vllm-092-custom-ar` | [vllm-project/vllm vllm/distributed/device_communicators/custom_all_reduce.py at v0.9.2](../references/framework-history/2026-09-08/collective-paths/vllm-092-custom-ar.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `collective-vllm-current-custom-ar` | [vllm-project/vllm vllm/distributed/device_communicators/custom_all_reduce.py at 51da0ca66c8065619c79e35dff97aa99aeaf5644](../references/framework-history/2026-09-08/collective-paths/vllm-current-custom-ar.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `collective-vllm-current-cuda-communicator` | [vllm-project/vllm vllm/distributed/device_communicators/cuda_communicator.py at 51da0ca66c8065619c79e35dff97aa99aeaf5644](../references/framework-history/2026-09-08/collective-paths/vllm-current-cuda-communicator.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `collective-vllm-current-all-reduce-utils` | [vllm-project/vllm vllm/distributed/device_communicators/all_reduce_utils.py at 51da0ca66c8065619c79e35dff97aa99aeaf5644](../references/framework-history/2026-09-08/collective-paths/vllm-current-all-reduce-utils.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `collective-vllm-current-fusions` | [vllm-project/vllm docs/design/fusions.md at 51da0ca66c8065619c79e35dff97aa99aeaf5644](../references/framework-history/2026-09-08/collective-paths/vllm-current-fusions.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `collective-sglang-current-layer-communicator` | [SGLang python/sglang/srt/layers/communicator.py at c99d906effa8bd05573995127f0d4a0984c5a96a](../references/framework-history/2026-09-08/collective-paths/sglang-current-layer-communicator.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `collective-sglang-current-fused-collective-readme` | [SGLang benchmark/kernels/flashinfer_allreduce_fusion/README.md at c99d906effa8bd05573995127f0d4a0984c5a96a](../references/framework-history/2026-09-08/collective-paths/sglang-current-fused-collective-readme.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `nsdi24-rajasekaran` | [CASSINI: Network-Aware Job Scheduling in Machine Learning Clusters](../references/proceedings/NSDI/2024/selected/nsdi24-rajasekaran.pdf) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `nsdi24-de-sensi` | [Swing: Short-cutting Rings for Higher Bandwidth Allreduce](../references/proceedings/NSDI/2024/selected/nsdi24-de-sensi.pdf) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `nsdi25-wan-borui` | [ByteCheckpoint: A Unified Checkpointing System for Large Foundation Model Development](../references/proceedings/NSDI/2025/selected/nsdi25-wan-borui.pdf) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `checkpoint-vllm-060-loader` | [checkpoint-vllm-060-loader](../references/framework-history/2026-09-08/checkpoint-loading/vllm-060-loader.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `checkpoint-vllm-092-loader` | [checkpoint-vllm-092-loader](../references/framework-history/2026-09-08/checkpoint-loading/vllm-092-loader.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `checkpoint-vllm-current-loader` | [checkpoint-vllm-current-loader](../references/framework-history/2026-09-08/checkpoint-loading/vllm-current-loader.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `checkpoint-vllm-current-memory` | [checkpoint-vllm-current-memory](../references/framework-history/2026-09-08/checkpoint-loading/vllm-current-memory.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `checkpoint-pytorch-2024-blog` | [checkpoint-pytorch-2024-blog](../references/framework-history/2026-09-08/checkpoint-loading/pytorch-2024-blog.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `checkpoint-pytorch-2025-blog` | [checkpoint-pytorch-2025-blog](../references/framework-history/2026-09-08/checkpoint-loading/pytorch-2025-blog.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `checkpoint-pytorch-current-doc` | [checkpoint-pytorch-current-doc](../references/framework-history/2026-09-08/checkpoint-loading/pytorch-current-doc.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `checkpoint-pytorch-214-doc` | [PyTorch 2.14 Distributed Checkpoint documentation](../references/framework-history/2026-09-08/checkpoint-loading/pytorch-214-doc.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `checkpoint-pytorch-214-saver` | [PyTorch DCP state_dict_saver source linked from 2.14 documentation](../references/framework-history/2026-09-08/checkpoint-loading/pytorch-214-saver.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `nsdi25-xu-guanbin` | [AutoCCL: Automated Collective Communication Tuning for Accelerating Distributed and Parallel DNN Training](../references/proceedings/NSDI/2025/selected/nsdi25-xu-guanbin.pdf) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `nccl-2025-tuning-blog` | [NVIDIA tuning article — initial HTTP 200 empty response](../references/framework-history/2026-09-08/communication-tuning/nccl-2025-tuning-blog.html) | 补充 | 补充／版本参照 | 失败／空响应；不作正文证据 |
| `nccl-2025-device-blog` | [NCCL 2.28: device API, copy engines and profiling — official 2025 article](../references/framework-history/2026-09-08/communication-tuning/nccl-2025-device-blog.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `autoccl-current-commit` | [AutoCCL incorrect main-branch lookup — HTTP 422](../references/framework-history/2026-09-08/communication-tuning/autoccl-current-commit.json) | 补充 | 补充／版本参照 | 失败／空响应；不作正文证据 |
| `nccl-2312-tag` | [NCCL v2.31.2-1 tag target — official metadata](../references/framework-history/2026-09-08/communication-tuning/nccl-2312-tag.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `nccl-current-ce-guide` | [Guessed CE guide location — HTTP 404, not documentation](../references/framework-history/2026-09-08/communication-tuning/nccl-current-ce-guide.html) | 补充 | 补充／版本参照 | 失败／空响应；不作正文证据 |
| `nccl-2025-tuning-blog-retry` | [Understanding NCCL Tuning — official 2025-07-22 article](../references/framework-history/2026-09-08/communication-tuning/nccl-2025-tuning-blog-retry.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `autoccl-head-commit` | [AutoCCL HEAD fixed at 63acb15 — official metadata](../references/framework-history/2026-09-08/communication-tuning/autoccl-head-commit.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `nccl-2312-bufferreg` | [NCCL v2.31.2-1 user-buffer registration and zero-CTA requirements](../references/framework-history/2026-09-08/communication-tuning/nccl-2312-bufferreg.rst) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `nccl-2312-tuner` | [NCCL v2.31.2-1 tuner include and symbol definitions](../references/framework-history/2026-09-08/communication-tuning/nccl-2312-tuner.h) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `autoccl-fixed-readme` | [AutoCCL author README at fixed 63acb15](../references/framework-history/2026-09-08/communication-tuning/autoccl-fixed-readme.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `nccl-2312-tuner-v6` | [NCCL v2.31.2-1 tuner v6 API: getCollInfo and getChunkSize](../references/framework-history/2026-09-08/communication-tuning/nccl-2312-tuner-v6.h) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `nccl-2312-release` | [NCCL v2.31.2-1 — official 2026-08-11 release and known issues](../references/framework-history/2026-09-08/communication-tuning/nccl-2312-release.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `nsdi26-xiang-servegen` | [ServeGen: Workload Characterization and Generation of Large Language Model Serving in Production](../references/proceedings/NSDI/2026/selected/nsdi26-xiang-servegen.pdf) | 补充 | 章末 3,9 | 已归档；固定快照 |
| `servegen-head` | [ServeGen current HEAD identity](../references/framework-history/2026-09-08/workload-generation/head.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `servegen-tree` | [ServeGen fixed repository tree](../references/framework-history/2026-09-08/workload-generation/tree.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `servegen-README` | [ServeGen fixed README](../references/framework-history/2026-09-08/workload-generation/servegen-readme.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `servegen-construct` | [ServeGen fixed workload construction source](../references/framework-history/2026-09-08/workload-generation/construct.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-vllm-2024` | [vLLM speculative decoding — October 2024](../references/framework-history/2026-09-08/speculative-execution/vllm-2024.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-vllm-speculators-2025` | [vLLM Speculators v0.3 — December 2025](../references/framework-history/2026-09-08/speculative-execution/vllm-speculators-2025.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-vllm-peagle-2026` | [vLLM parallel P-EAGLE — March 2026](../references/framework-history/2026-09-08/speculative-execution/vllm-peagle-2026.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-sglang-mtp-2025` | [SGLang MTP — July 2025](../references/framework-history/2026-09-08/speculative-execution/sglang-mtp-2025.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-sglang-specv2-2026` | [SGLang DFlash and Spec V2 — June 2026](../references/framework-history/2026-09-08/speculative-execution/sglang-specv2-2026.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-sglang-dspark-2026` | [SGLang DSpark variable verification — July 2026](../references/framework-history/2026-09-08/speculative-execution/sglang-dspark-2026.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-ollama-mlx-performance-2026` | [Ollama MLX execution and snapshots — June 2026](../references/framework-history/2026-09-08/speculative-execution/ollama-mlx-performance-2026.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-vllm-head` | [vLLM current revision identity](../references/framework-history/2026-09-08/speculative-execution/vllm-head.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-sglang-dspark-pr` | [SGLang DSpark integration PR identity](../references/framework-history/2026-09-08/speculative-execution/sglang-dspark-pr.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-vllm-tree` | [vLLM fixed file tree](../references/framework-history/2026-09-08/speculative-execution/vllm-tree.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-sglang-spec-guide` | [SGLang fixed docs/docs/advanced_features/speculative_decoding.mdx](../references/framework-history/2026-09-08/speculative-execution/sglang-spec-guide.mdx) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-sglang-adaptive-guide` | [SGLang fixed docs/docs/advanced_features/adaptive_speculative_decoding.mdx](../references/framework-history/2026-09-08/speculative-execution/sglang-adaptive-guide.mdx) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-sglang-dspark-sps` | [SGLang fixed python/sglang/srt/speculative/dspark_components/dspark_sps.py](../references/framework-history/2026-09-08/speculative-execution/sglang-dspark-sps.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-vllm-spec-config` | [vLLM fixed vllm/config/speculative.py](../references/framework-history/2026-09-08/speculative-execution/vllm-spec-config.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-vllm-spec-metrics` | [vLLM fixed vllm/v1/spec_decode/metrics.py](../references/framework-history/2026-09-08/speculative-execution/vllm-spec-metrics.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-vllm-dynamic_speculative_decoding` | [vLLM fixed dynamic_speculative_decoding guide](../references/framework-history/2026-09-08/speculative-execution/vllm-dynamic_speculative_decoding.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-vllm-adaptive_verification` | [vLLM fixed adaptive_verification guide](../references/framework-history/2026-09-08/speculative-execution/vllm-adaptive_verification.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-vllm-acceptance_metrics` | [vLLM fixed acceptance_metrics guide](../references/framework-history/2026-09-08/speculative-execution/vllm-acceptance_metrics.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-vllm-peagle-pr` | [vLLM P-EAGLE integration PR identity](../references/framework-history/2026-09-08/speculative-execution/vllm-peagle-pr.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `spec-vllm-v016-release` | [vLLM v0.16.0 release metadata](../references/framework-history/2026-09-08/speculative-execution/vllm-v016-release.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `nsdi26-gao-wei` | [RollPacker: Taming Long-Tail Rollouts for RL Post-Training with Tail Batching](../references/proceedings/NSDI/2026/selected/nsdi26-gao-wei.pdf) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rollout-tail-rollpacker-head` | [RollPacker current revision identity](../references/framework-history/2026-09-08/rollout-tail/rollpacker-head.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rollout-tail-rollpacker-tree` | [RollPacker fixed source paths](../references/framework-history/2026-09-08/rollout-tail/rollpacker-tree.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rollout-tail-rollpacker-readme` | [RollPacker fixed README.md](../references/framework-history/2026-09-08/rollout-tail/rollpacker-readme.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rollout-tail-rollpacker-requirements` | [RollPacker fixed requirements_torch260_vllm.txt](../references/framework-history/2026-09-08/rollout-tail/rollpacker-requirements.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rollout-tail-rollpacker-pipeline` | [RollPacker fixed roll/pipeline/rlvr/rlvr_pipeline_megatron_async.py](../references/framework-history/2026-09-08/rollout-tail/rollpacker-pipeline.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rollout-tail-rollpacker-batcher` | [RollPacker fixed roll/distributed/scheduler/generate_scheduler_batcher_reward.py](../references/framework-history/2026-09-08/rollout-tail/rollpacker-batcher.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rollout-tail-rollpacker-megatron` | [RollPacker fixed roll/distributed/strategy/megatron_strategy.py](../references/framework-history/2026-09-08/rollout-tail/rollpacker-megatron.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rollout-tail-rollpacker-example` | [RollPacker fixed examples/e2e_performance/rlvr_config_rollpacker_full_7B.yaml](../references/framework-history/2026-09-08/rollout-tail/rollpacker-example.yaml) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rollout-tail-rollpacker-multi-scheduler` | [RollPacker fixed roll/distributed/scheduler/multi_async_generate_scheduler.py](../references/framework-history/2026-09-08/rollout-tail/rollpacker-multi-scheduler.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `rollout-tail-rollpacker-stream-run` | [RollPacker fixed examples/stream_trainer_table3/run_stream_trainer.sh](../references/framework-history/2026-09-08/rollout-tail/rollpacker-stream-run.sh) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `offload-vllm-2024-utils` | [vLLM v0.6.0 CPU offload helper](../references/framework-history/2026-09-08/offload-execution/vllm-2024-utils.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `offload-vllm-2025-utils` | [vLLM v0.9.2 CPU offload helper](../references/framework-history/2026-09-08/offload-execution/vllm-2025-utils.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `offload-vllm-current-config` | [vLLM fixed weight-offload configuration](../references/framework-history/2026-09-08/offload-execution/vllm-current-config.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `offload-vllm-current-uva` | [vLLM fixed UVA weight offloader](../references/framework-history/2026-09-08/offload-execution/vllm-current-uva.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `offload-vllm-current-prefetch` | [vLLM fixed prefetch weight offloader](../references/framework-history/2026-09-08/offload-execution/vllm-current-prefetch.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `offload-vllm-prefetch-pr` | [vLLM weight prefetch PR identity](../references/framework-history/2026-09-08/offload-execution/vllm-prefetch-pr.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `offload-vllm-selective-pr` | [vLLM selective CPU offload PR identity](../references/framework-history/2026-09-08/offload-execution/vllm-selective-pr.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `offload-vllm-v017-release` | [vLLM 0.17.0 official release](../references/framework-history/2026-09-08/offload-execution/vllm-v017-release.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `offload-sglang-kt-2025` | [SGLang and KTransformers CPU kernels, October 2025](../references/framework-history/2026-09-08/offload-execution/sglang-kt-2025.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `offload-sglang-current-offloader` | [SGLang fixed generic offloader](../references/framework-history/2026-09-08/offload-execution/sglang-current-offloader.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `offload-sglang-current-kt` | [SGLang fixed KTransformers MoE wrapper](../references/framework-history/2026-09-08/offload-execution/sglang-current-kt.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `offload-ollama-gguf-2026` | [Ollama 0.30 GGUF and hardware announcement](../references/framework-history/2026-09-08/offload-execution/ollama-gguf-2026.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `offload-ollama-llm-directory` | [Ollama fixed runner file paths](../references/framework-history/2026-09-08/offload-execution/ollama-llm-directory.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `offload-vllm-omni-dlo-2026` | [vLLM-Omni distributed layerwise offload](../references/framework-history/2026-09-08/offload-execution/vllm-omni-dlo-2026.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `offload-ollama-current-llama-server` | [Ollama fixed llama-server client and launch arguments](../references/framework-history/2026-09-08/offload-execution/ollama-current-llama-server.go) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `offload-ollama-v030-release` | [Ollama 0.30.0 official release](../references/framework-history/2026-09-08/offload-execution/ollama-v030-release.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `offload-vllm-omni-pr5864` | [vLLM-Omni DLO multi-request admission PR](../references/framework-history/2026-09-08/offload-execution/vllm-omni-pr5864.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `mlsys2026-f068c65585985c25c17f221390774ec7` | [TriInfer: Hybrid EPD Disaggregation for Efficient Multimodal Large Language Model Inference](../references/proceedings/MLSys/2026/papers/mlsys2026-f068c65585985c25c17f221390774ec7.pdf) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `multimodal-vllm-epd-2025` | [vLLM encoder disaggregation December 2025](../references/framework-history/2026-09-08/multimodal-execution/vllm-epd-2025.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `multimodal-sglang-epd-2026` | [SGLang encoder disaggregation January 2026](../references/framework-history/2026-09-08/multimodal-execution/sglang-epd-2026.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `multimodal-vllm-epd-current` | [vLLM fixed encoder disaggregation guide](../references/framework-history/2026-09-08/multimodal-execution/vllm-epd-current.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `multimodal-vllm-epd-pr25233` | [vLLM initial EC transfer PR identity](../references/framework-history/2026-09-08/multimodal-execution/vllm-epd-pr25233.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `multimodal-vllm-v0111-release` | [vLLM v0.11.1 release](../references/framework-history/2026-09-08/multimodal-execution/vllm-v0111-release.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `multimodal-sglang-tree` | [SGLang fixed multimodal path discovery](../references/framework-history/2026-09-08/multimodal-execution/sglang-tree.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `multimodal-vllm-qwen3-vl` | [vLLM fixed Qwen3 VL encoder output layout](../references/framework-history/2026-09-08/multimodal-execution/vllm-qwen3-vl.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `multimodal-qwen3-vl4-identity` | [Qwen3 VL 4B official repository identity](../references/framework-history/2026-09-08/multimodal-execution/qwen3-vl4-identity.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `multimodal-omni-tree` | [vLLM-Omni fixed DLO merge tree](../references/framework-history/2026-09-08/multimodal-execution/omni-tree.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `multimodal-qwen3-vl4-config` | [Qwen3 VL 4B fixed configuration](../references/framework-history/2026-09-08/multimodal-execution/qwen3-vl4-config.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `multimodal-qwen3-vl4-preprocessor` | [Qwen3 VL 4B fixed image preprocessing](../references/framework-history/2026-09-08/multimodal-execution/qwen3-vl4-preprocessor.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `multimodal-sglang-epd-current` | [SGLang fixed EPD guide](../references/framework-history/2026-09-08/multimodal-execution/sglang-epd-current.mdx) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `multimodal-omni-dlo-backend` | [vLLM-Omni DLO backend at request-correctness merge](../references/framework-history/2026-09-08/multimodal-execution/omni-dlo-backend.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `multimodal-vllm-mm-2024` | [vLLM v0.6.0 multimodal guide](../references/framework-history/2026-09-08/multimodal-execution/vllm-mm-2024.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `multimodal-vllm-ec-example` | [vLLM fixed example encoder-cache connector](../references/framework-history/2026-09-08/multimodal-execution/vllm-ec-example.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `multimodal-sglang-mm-identity` | [SGLang fixed multimodal cache identity](../references/framework-history/2026-09-08/multimodal-execution/sglang-mm-identity.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `multimodal-sglang-encoder-runtime` | [SGLang fixed encoder runtime cache integration](../references/framework-history/2026-09-08/multimodal-execution/sglang-encoder-runtime.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `interview-fourth-takehome-identity` | [Anthropic original takehome fixed identity](../references/interviews/2026-09-08/fourth-pass/takehome-identity.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `interview-fourth-minimax-first` | [8.17 minimax 平台研发工程师秋招一面_牛客网](../references/interviews/2026-09-08/fourth-pass/minimax-first.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `interview-fourth-minimax-second` | [8.19 minimax 平台研发工程师秋招二面_牛客网](../references/interviews/2026-09-08/fourth-pass/minimax-second.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `interview-fourth-anthropic-em` | [Anthropic Engineering Manager, Data Infrastructure Interview Experience (2026) - Aced (formerly Exponent)](../references/interviews/2026-09-08/fourth-pass/anthropic-em.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `interview-fourth-anthropic-em-index` | [Anthropic Engineering Manager Interview Experiences (2026) - Aced (formerly Exponent)](../references/interviews/2026-09-08/fourth-pass/anthropic-em-index.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `interview-fourth-anthropic-prachub` | [Anthropic Software Engineer Interview Experience — Perfect OA, Rejected at the ML Inference System Design Phone Screen | PracHub](../references/interviews/2026-09-08/fourth-pass/anthropic-prachub.html) | 补充／版本参照 | 补充／版本参照 | 已归档；固定快照 |
| `interview-fourth-minimax-guide` | [MiniMax AI Infra 实习 一面 (2) - 面试宝典](../references/interviews/2026-09-08/fourth-pass/minimax-guide.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `interview-fourth-otel-resiliency` | [Resiliency | OpenTelemetry](../references/interviews/2026-09-08/fourth-pass/otel-resiliency.html) | 补充／版本参照 | 补充／版本参照 | 已归档；固定快照 |
| `interview-fourth-otel-sampling` | [Sampling | OpenTelemetry](../references/interviews/2026-09-08/fourth-pass/otel-sampling.html) | 补充／版本参照 | 补充／版本参照 | 已归档；固定快照 |
| `interview-fourth-kafka-delivery` | [Design | Apache Kafka](../references/interviews/2026-09-08/fourth-pass/kafka-delivery.html) | 补充／版本参照 | 补充／版本参照 | 已归档；固定快照 |
| `interview-fourth-takehome-readme` | [Anthropic takehome Readme.md](../references/interviews/2026-09-08/fourth-pass/takehome-readme.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `interview-fourth-takehome-problem` | [Anthropic takehome problem.py](../references/interviews/2026-09-08/fourth-pass/takehome-problem.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `interview-fourth-takehome-kernel` | [Anthropic takehome perf_takehome.py](../references/interviews/2026-09-08/fourth-pass/takehome-kernel.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `interview-fourth-takehome-tests` | [Anthropic takehome tests/submission_tests.py](../references/interviews/2026-09-08/fourth-pass/takehome-tests.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `interview-fourth-takehome-frozen` | [Anthropic takehome tests/frozen_problem.py](../references/interviews/2026-09-08/fourth-pass/takehome-frozen.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `pcie-staging-tccl-commit` | [tccl-commit](../references/framework-history/2026-09-08/pcie-staging/tccl-commit.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `pcie-staging-tccl-tree` | [tccl-tree](../references/framework-history/2026-09-08/pcie-staging/tccl-tree.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `pcie-staging-tccl-README` | [TCCL fixed README](../references/framework-history/2026-09-08/pcie-staging/tccl-README.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `pcie-staging-tccl-AE` | [TCCL historical artifact conditions](../references/framework-history/2026-09-08/pcie-staging/tccl-AE.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `pcie-staging-tccl-author` | [TCCL author explanation (2024)](../references/framework-history/2026-09-08/pcie-staging/tccl-author.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `pcie-staging-tccl-shm` | [tccl-shm](../references/framework-history/2026-09-08/pcie-staging/tccl-shm.cc) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `pcie-staging-tccl-search` | [tccl-search](../references/framework-history/2026-09-08/pcie-staging/tccl-search.cpp) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `pcie-staging-tccl-benchmark` | [tccl-benchmark](../references/framework-history/2026-09-08/pcie-staging/tccl-benchmark.cpp) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `pcie-staging-nccl-2.18.3-shm` | [nccl-2.18.3-shm](../references/framework-history/2026-09-08/pcie-staging/nccl-2.18.3-shm.cc) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `pcie-staging-nccl-2.31.2-shm` | [nccl-2.31.2-shm](../references/framework-history/2026-09-08/pcie-staging/nccl-2.31.2-shm.cc) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `pcie-staging-nccl-2.31.2-shmutils` | [nccl-2.31.2-shmutils](../references/framework-history/2026-09-08/pcie-staging/nccl-2.31.2-shmutils.cc) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `pcie-staging-nccl-2.31.2-runtime` | [NCCL 2.31.2 shared-memory runtime conditions](../references/framework-history/2026-09-08/pcie-staging/nccl-2.31.2-runtime.rst) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `pcie-staging-nccl-releases` | [nccl-releases](../references/framework-history/2026-09-08/pcie-staging/nccl-releases.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `pcie-staging-nccl-2.31.2-alloc` | [nccl-2.31.2-alloc](../references/framework-history/2026-09-08/pcie-staging/nccl-2.31.2-alloc.h) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `pcie-staging-tccl-shmutils` | [tccl-shmutils](../references/framework-history/2026-09-08/pcie-staging/tccl-shmutils.cc) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `pcie-staging-tccl-kernels` | [tccl-kernels](../references/framework-history/2026-09-08/pcie-staging/tccl-kernels.cu) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `korch-author` | [korch-author](../references/framework-history/2026-09-08/kernel-orchestration/korch-author.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `korch-arxiv-landing` | [korch-arxiv-landing](../references/framework-history/2026-09-08/kernel-orchestration/korch-arxiv-landing.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `korch-commit` | [korch-commit](../references/framework-history/2026-09-08/kernel-orchestration/korch-commit.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `korch-tree` | [korch-tree](../references/framework-history/2026-09-08/kernel-orchestration/korch-tree.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `korch-readme` | [korch-readme](../references/framework-history/2026-09-08/kernel-orchestration/korch-README.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `korch-calc-py` | [Korch framework/calc.py](../references/framework-history/2026-09-08/kernel-orchestration/korch-calc.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `korch-profiler-py` | [Korch framework/profiler.py](../references/framework-history/2026-09-08/kernel-orchestration/korch-profiler.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `korch-kernel_profiler-py` | [Korch framework/kernel_profiler.py](../references/framework-history/2026-09-08/kernel-orchestration/korch-kernel_profiler.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `korch-operator_fission-py` | [Korch framework/operator_fission.py](../references/framework-history/2026-09-08/kernel-orchestration/korch-operator_fission.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `korch-segformer-toml` | [Korch cases/segformer.toml](../references/framework-history/2026-09-08/kernel-orchestration/korch-segformer.toml) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `kernel-orchestration-vllm-2024-activation` | [vllm-2024-activation](../references/framework-history/2026-09-08/kernel-orchestration/vllm-2024-activation.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `kernel-orchestration-vllm-current-act-quant` | [vllm-current-act-quant](../references/framework-history/2026-09-08/kernel-orchestration/vllm-current-act-quant.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `kernel-orchestration-vllm-current-compile-config` | [vllm-current-compile-config](../references/framework-history/2026-09-08/kernel-orchestration/vllm-current-compile-config.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `kernel-orchestration-vllm-current-fusions` | [vllm-current-fusions](../references/framework-history/2026-09-08/kernel-orchestration/vllm-current-fusions.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `asplos2024-tccl-acm` | [TCCL official PDF request](../references/proceedings/ASPLOS/2024/selected/tccl-acm-response.html) | 补充 | 补充／版本参照 | 失败／空响应；不作正文证据 |
| `korch-paper` | [Korch, ASPLOS 2024 author arXiv v1 (corrections noted by author)](../references/proceedings/ASPLOS/2024/selected/korch-arxiv-v1.pdf) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-kv-offload-2026` | [vllm-kv-offload-2026.html](../references/framework-history/2026-09-08/cache-routing/vllm-kv-offload-2026.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-current-kv-guide` | [vllm-current-kv-guide.md](../references/framework-history/2026-09-08/cache-routing/vllm-current-kv-guide.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-current-hicache` | [sglang-current-hicache.mdx](../references/framework-history/2026-09-08/cache-routing/sglang-current-hicache.mdx) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-current-hicache-design` | [sglang-current-hicache-design.mdx](../references/framework-history/2026-09-08/cache-routing/sglang-current-hicache-design.mdx) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-current-hicache-practices` | [sglang-current-hicache-practices.mdx](../references/framework-history/2026-09-08/cache-routing/sglang-current-hicache-practices.mdx) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-current-gateway` | [sglang-current-gateway.mdx](../references/framework-history/2026-09-08/cache-routing/sglang-current-gateway.mdx) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-current-cache-aware` | [sglang-current-cache-aware.rs](../references/framework-history/2026-09-08/cache-routing/sglang-current-cache-aware.rs) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ollama-current-faq` | [ollama-current-faq.html](../references/framework-history/2026-09-08/cache-routing/ollama-current-faq.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `structured-vllm-structured-2025` | [vLLM：Structured Decoding，2025 年接入与 V1 计划](../references/framework-history/2026-09-08/structured-generation/vllm-structured-2025.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `structured-ollama-structured-2024` | [Ollama：Structured Outputs，2024 年公告](../references/framework-history/2026-09-08/structured-generation/ollama-structured-2024.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `structured-vllm-current-guide` | [vLLM 固定版本结构化输出指南](../references/framework-history/2026-09-08/structured-generation/vllm-current-guide.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `structured-vllm-current-manager` | [vLLM 固定版本语法管理与批量掩码](../references/framework-history/2026-09-08/structured-generation/vllm-current-manager.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `structured-vllm-current-xgrammar` | [vLLM 固定版本 XGrammar 后端](../references/framework-history/2026-09-08/structured-generation/vllm-current-xgrammar.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `structured-sglang-current-guide` | [SGLang 固定版本结构化输出指南](../references/framework-history/2026-09-08/structured-generation/sglang-current-guide.mdx) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `structured-sglang-current-reasoning` | [SGLang 固定版本 Reasoning 与约束边界](../references/framework-history/2026-09-08/structured-generation/sglang-current-reasoning.mdx) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `structured-sglang-current-xgrammar` | [SGLang 固定版本 XGrammar 后端](../references/framework-history/2026-09-08/structured-generation/sglang-current-xgrammar.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `structured-ollama-current-guide` | [Ollama 获取日结构化输出指南](../references/framework-history/2026-09-08/structured-generation/ollama-current-guide.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `asplos25-iks-pdf` | [Accelerating Retrieval-Augmented Generation author preprint v1](../references/proceedings/ASPLOS/2025/public/iks-v1.pdf) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `asplos25-faiss-faiss-indexes` | [Faiss official wiki: Faiss-indexes](../references/proceedings/ASPLOS/2025/public/faiss-faiss-indexes.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `asplos25-faiss-guidelines-to-choose-an-index` | [Faiss official wiki: Guidelines-to-choose-an-index](../references/proceedings/ASPLOS/2025/public/faiss-guidelines-to-choose-an-index.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-elastic-2026` | [vllm-elastic-2026](../references/framework-history/2026-09-08/ep-reconfiguration/vllm-elastic-2026.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-waterfill-lplb-2026` | [sglang-waterfill-lplb-2026](../references/framework-history/2026-09-08/ep-reconfiguration/sglang-waterfill-lplb-2026.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-current-ep-guide` | [vllm-current-ep-guide](../references/framework-history/2026-09-08/ep-reconfiguration/vllm-current-ep-guide.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-current-ep-guide` | [sglang-current-ep-guide](../references/framework-history/2026-09-08/ep-reconfiguration/sglang-current-ep-guide.mdx) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-expert-location-dispatch` | [sglang-expert-location-dispatch](../references/framework-history/2026-09-08/ep-reconfiguration/sglang-expert-location-dispatch.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-eplb-manager` | [sglang-eplb-manager](../references/framework-history/2026-09-08/ep-reconfiguration/sglang-eplb-manager.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-elastic-execute` | [vllm-elastic-execute](../references/framework-history/2026-09-08/ep-reconfiguration/vllm-elastic-execute.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-waterfill` | [sglang-waterfill](../references/framework-history/2026-09-08/ep-reconfiguration/sglang-waterfill.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-lplb-solver` | [sglang-lplb-solver](../references/framework-history/2026-09-08/ep-reconfiguration/sglang-lplb-solver.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-parallel-config` | [vllm-parallel-config](../references/framework-history/2026-09-08/ep-reconfiguration/vllm-parallel-config.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-elastic-api` | [vllm-elastic-api](../references/framework-history/2026-09-08/ep-reconfiguration/vllm-elastic-api.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `asplos25-public-pdf-94` | [FSMoE: A Flexible and Scalable Training System for Sparse Mixture-of-Experts Models — public copy, identity pending](../references/proceedings/ASPLOS/2025/public/paper-094.pdf) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ab-osdi` | [OSDI：Operating Systems Design and Implementation](../references/outline-checks/2026-09-08/system-abstraction/osdi26.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ab-sosp` | [SOSP：Symposium on Operating Systems Principles](../references/outline-checks/2026-09-08/system-abstraction/sosp26.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ab-foundation-models` | [Stanford CRFM：On the Opportunities and Risks of Foundation Models](../references/outline-checks/2026-09-08/system-abstraction/foundation-models.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ab-firecracker` | [Firecracker：microVM 与多租户服务](../references/outline-checks/2026-09-08/system-abstraction/firecracker.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ab-mig` | [NVIDIA MIG User Guide：Introduction](../references/outline-checks/2026-09-08/system-abstraction/mig-introduction.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ab-skeleton-11` | [初始提交：《深入理解 AI Infra》结构蓝图（草案 11）](../references/outline-checks/2026-09-08/system-abstraction/skeleton-draft11-12fc723.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ab-skeleton-14` | [草案 14：推理两章重划为「单实例／跨实例」，补齐五处缺口](../references/outline-checks/2026-09-08/system-abstraction/skeleton-draft14-d9199ca.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `ab-skeleton-16` | [修订三部分章节蓝图，归档论文规格并核对 UB 与昇腾 950](../references/outline-checks/2026-09-08/system-abstraction/skeleton-draft16-e524afe.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-current-kv-publisher` | [vllm-current-kv-publisher](../references/framework-history/2026-09-08/cache-events/vllm-current-kv-publisher.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `dynamo-native-offload-fixed` | [dynamo-native-offload-fixed](../references/framework-history/2026-09-08/cache-events/dynamo-native-offload-fixed.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `dynamo-event-recovery-fixed` | [dynamo-event-recovery-fixed](../references/framework-history/2026-09-08/cache-events/dynamo-event-recovery-fixed.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `dynamo-router-design` | [dynamo-router-design](../references/framework-history/2026-09-08/cache-events/dynamo-router-design.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `dynamo-local-indexer` | [dynamo-local-indexer](../references/framework-history/2026-09-08/cache-events/dynamo-local-indexer.rs) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `dynamo-recovery-state` | [dynamo-recovery-state](../references/framework-history/2026-09-08/cache-events/dynamo-recovery-state.rs) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `dynamo-sglang-hicache` | [dynamo-sglang-hicache](../references/framework-history/2026-09-08/cache-events/dynamo-sglang-hicache.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `dynamo-config-tuning` | [dynamo-config-tuning](../references/framework-history/2026-09-08/cache-events/dynamo-config-tuning.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-sleep-current` | [vllm-sleep-current](../references/framework-history/2026-09-08/weight-handoff/vllm-sleep-current.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-transfer-current` | [vllm-transfer-current](../references/framework-history/2026-09-08/weight-handoff/vllm-transfer-current.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-transfer-rdt` | [vllm-transfer-rdt](../references/framework-history/2026-09-08/weight-handoff/vllm-transfer-rdt.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-worker-current` | [vllm-worker-current](../references/framework-history/2026-09-08/weight-handoff/vllm-worker-current.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-sleep-2025` | [vllm-sleep-2025](../references/framework-history/2026-09-08/weight-handoff/vllm-sleep-2025.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-rdt-2026` | [vllm-rdt-2026](../references/framework-history/2026-09-08/weight-handoff/vllm-rdt-2026.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-rl-guide-fixed` | [sglang-rl-guide-fixed](../references/framework-history/2026-09-08/weight-handoff/sglang-rl-guide-fixed.mdx) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `verl-v1-async-fixed` | [verl-v1-async-fixed](../references/framework-history/2026-09-08/weight-handoff/verl-v1-async-fixed.md) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `verl-vllm-server` | [verl-vllm-server](../references/framework-history/2026-09-08/weight-handoff/verl-vllm-server.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `verl-sglang-server` | [verl-sglang-server](../references/framework-history/2026-09-08/weight-handoff/verl-sglang-server.py) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `sglang-memory-2025` | [sglang-memory-2025](../references/framework-history/2026-09-08/weight-handoff/sglang-memory-2025.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `vllm-native-rl-2026-fixed-url` | [Native RL APIs in vLLM (May 28, 2026)](../references/framework-history/2026-09-08/weight-handoff/vllm-native-rl-2026-fixed.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `isca24-public-011-author` | [Mind the Gap: author-hosted public PDF](../references/proceedings/ISCA/2024/public/paper-011-author.pdf) | 补充 | 章末 5 | 已归档；固定快照 |
| `interview-fifth-pytorch-pinmem` | [A guide on good usage of non_blocking and pin_memory() in PyTorch — PyTorch Tutorials 2.14.0+cu130 documentation](../references/interviews/2026-09-08/fifth-pass/pytorch-pinmem.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `interview-fifth-cuda-sync` | [CUDA Runtime API :: CUDA Toolkit Documentation](../references/interviews/2026-09-08/fifth-pass/cuda-sync.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `interview-fifth-cuda-memory` | [2.6. Unified and System Memory — CUDA Programming Guide](../references/interviews/2026-09-08/fifth-pass/cuda-memory.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `isca24-public-014` | [ISCA 2024 program paper 14 public copy](../references/proceedings/ISCA/2024/public/paper-014.pdf) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `kvquant-vllm-2026-blog` | [vllm-2026-blog](../references/framework-history/2026-09-08/kv-quantization/vllm-2026-blog.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `kvquant-ollama-faq` | [ollama-faq](../references/framework-history/2026-09-08/kv-quantization/ollama-faq.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `kvquant-vllm-current-kv` | [vllm-current-kv](../references/framework-history/2026-09-08/kv-quantization/vllm-current-kv.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `kvquant-vllm-018-kv-raw` | [vllm-018-kv-raw](../references/framework-history/2026-09-08/kv-quantization/vllm-018-kv-raw.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `kvquant-vllm-055-e4m3` | [vllm-055-e4m3](../references/framework-history/2026-09-08/kv-quantization/vllm-055-e4m3.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `kvquant-vllm-055-e5m2` | [vllm-055-e5m2](../references/framework-history/2026-09-08/kv-quantization/vllm-055-e5m2.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `kvquant-ollama-llama-server` | [ollama-llama-server](../references/framework-history/2026-09-08/kv-quantization/ollama-llama-server.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `kvquant-sglang-current-kv` | [sglang-current-kv](../references/framework-history/2026-09-08/kv-quantization/sglang-current-kv.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `kvquant-ollama-050-faq` | [ollama-050-faq](../references/framework-history/2026-09-08/kv-quantization/ollama-050-faq.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `kvquant-ollama-096-blocks` | [ollama-096-blocks](../references/framework-history/2026-09-08/kv-quantization/ollama-096-blocks.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `kvquant-sglang-memory-pool` | [sglang-memory-pool](../references/framework-history/2026-09-08/kv-quantization/sglang-memory-pool.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `kvquant-sglang-fp4-mla-pr` | [sglang-fp4-mla-pr](../references/framework-history/2026-09-08/kv-quantization/sglang-fp4-mla-pr.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `kvquant-sglang-fp4-mha-pr` | [sglang-fp4-mha-pr](../references/framework-history/2026-09-08/kv-quantization/sglang-fp4-mha-pr.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `kvquant-sglang-fp4-recipe` | [sglang-fp4-recipe](../references/framework-history/2026-09-08/kv-quantization/sglang-fp4-recipe.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `isca25-paper-033` | [ISCA 2025 source: paper-033](../references/proceedings/ISCA/2025/paper-033.pdf) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `isca25-paper-055` | [MeshSlice: Efficient 2D Tensor Parallelism for Distributed DNN Training](../references/proceedings/ISCA/2025/paper-055.pdf) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `hybrid-vllm-k3-preview` | [Kimi K3 preview: KDA prefix caching](../references/framework-history/2026-09-08/hybrid-state/vllm-k3-preview.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `hybrid-vllm-k3-release` | [Kimi K3 day-0 article: retention and partial reuse](../references/framework-history/2026-09-08/hybrid-state/vllm-k3-release.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `hybrid-vllm-hybrid-disagg` | [Disaggregated serving for hybrid SSM models](../references/framework-history/2026-09-08/hybrid-state/vllm-hybrid-disagg.html) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `hybrid-vllm-hybrid-design` | [Hybrid KV cache manager design (declared early scope)](../references/framework-history/2026-09-08/hybrid-state/vllm-hybrid-design.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `hybrid-vllm-coordinator` | [vLLM common cache-hit coordinator](../references/framework-history/2026-09-08/hybrid-state/vllm-coordinator.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `hybrid-vllm-single-manager` | [vLLM recurrent state CoW lifetime](../references/framework-history/2026-09-08/hybrid-state/vllm-single-manager.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `hybrid-vllm-block-pool` | [vLLM partial prefix metadata](../references/framework-history/2026-09-08/hybrid-state/vllm-block-pool.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `hybrid-vllm-055-apc` | [vLLM v0.5.5 automatic prefix caching](../references/framework-history/2026-09-08/hybrid-state/vllm-055-apc.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `hybrid-sglang-k3-ratio` | [SGLang Kimi K3 state-pool calculator](../references/framework-history/2026-09-08/hybrid-state/sglang-k3-ratio.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `hybrid-sglang-unified` | [SGLang Unified Radix Cache match dispatch](../references/framework-history/2026-09-08/hybrid-state/sglang-unified.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `hybrid-sglang-checkpoint-pool` | [SGLang optional recurrent checkpoint pool](../references/framework-history/2026-09-08/hybrid-state/sglang-checkpoint-pool.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `hybrid-ollama-recurrent` | [Ollama MLX recurrent cache](../references/framework-history/2026-09-08/hybrid-state/ollama-recurrent.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `hybrid-ollama-cache-trie` | [Ollama MLX cache trie](../references/framework-history/2026-09-08/hybrid-state/ollama-cache-trie.txt) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `hybrid-vllm-pr-37898` | [[Hybrid] Marconi-style admission policy for hybrid cache](../references/framework-history/2026-09-08/hybrid-state/vllm-pr-37898.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `hybrid-vllm-pr-45845` | [[v1][kvcache] Honor prefix-cache retention interval for Mamba/linear attention](../references/framework-history/2026-09-08/hybrid-state/vllm-pr-45845.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `hybrid-vllm-pr-45939` | [[1/N][Core] add partial prefix cache primitives](../references/framework-history/2026-09-08/hybrid-state/vllm-pr-45939.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `hybrid-vllm-pr-47782` | [[Core] Preserve Marconi caching with selective hybrid cache retention](../references/framework-history/2026-09-08/hybrid-state/vllm-pr-47782.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `hybrid-vllm-pr-49502` | [[3/N][Core][KV Connector] Support reliable partial-tail KV offload for sub-block prompts](../references/framework-history/2026-09-08/hybrid-state/vllm-pr-49502.json) | 补充 | 补充／版本参照 | 已归档；固定快照 |
| `micro24-paper-011` | [A Mess of Memory System Benchmarking, Simulation and Application Profiling](../references/proceedings/MICRO/2024/paper-011.pdf) | 补充 | 章末 1,4 | 已归档；固定快照 |
| `micro25-paper-014` | [StreamTensor](../references/proceedings/MICRO/2025/paper-014.pdf) | 补充 | 章末 5 | 已选读物理页 3–14；FPGA 条件独立登记 |
| `micro25-paper-030` | [LLM.265](../references/proceedings/MICRO/2025/paper-030.pdf) | 补充 | 章末 8 | 已选读物理页 4–13；现有引擎、硬件设计与模型估计分开 |
| `micro25-nvidia-codec-matrix` | [NVIDIA 编解码支持表](../references/proceedings/MICRO/2025/nvidia-codec-matrix.html) | 补充 | 补充／版本参照 | 固定网页；只核相应设备的编码／解码表行 |
| `micro25-dynamo-codec-requirements` | [Dynamo 视频解码条件](../references/proceedings/MICRO/2025/dynamo-codec-requirements.html) | 补充 | 补充／版本参照 | 固定网页；核设备表行，不作为张量压缩实现证据 |
| `asplos26-paper-004` | [Shift Parallelism: Low-Latency, High-Throughput LLM Inference for Dynamic Workloads](../references/proceedings/ASPLOS/2026/paper-004.pdf) | 补充 | 章末 6 | 物理页 1–12 已选读；arXiv v2 与会议年份分别记录 |
| `shift-v007-runner` | [ArcticInference v0.0.7 runner](../references/framework-history/2026-09-08/shift-parallelism/v007-runner.py) | 补充 | 章末 9 | 选读加载、KV 绑定、调度与捕获范围；未运行 |
| `shift-runner` | [ArcticInference 当前固定 runner](../references/framework-history/2026-09-08/shift-parallelism/runner.py) | 补充 | 章末 9 | 固定 aca5d9a；选读模式、状态绑定与图分派，未审计全文件 |
| `shift-shift-guide` | [Arctic Shift Parallelism 指南](../references/framework-history/2026-09-08/shift-parallelism/shift-guide.rst) | 补充 | 补充／版本参照 | 完整指南已读；阈值表述与配置差异另记 |
| `asplos26-paper-023` | [SuperOffload：arXiv v1，选读 3–12、16 页](../references/proceedings/ASPLOS/2026/paper-023.pdf) | 论文／官方实现 | 章末 10 | 梯度转换与更新放置；教学计算另列 |
| `superoffload-pytorch-2025` | [PyTorch SuperOffload，2025-10-09](../references/framework-history/2026-09-08/training-superchip/pytorch-superoffload.html) | 论文／官方实现 | 章末 10 | 发布版本与机制文字；未新增图像性能读数 |
| `superoffload-example-readme` | [DeepSpeed SuperOffload 固定示例](../references/framework-history/2026-09-08/training-superchip/examples-readme.md) | 论文／官方实现 | 章末 10 | 完整 README 及另存启动脚本；未运行 |
| `asplos26-paper-041` | [AttenIO：选读物理页 2–13](../references/proceedings/ASPLOS/2026/paper-041.pdf) | 论文／作者稿 | 补充／版本参照 | 分块、驻留与流量；仿真和扩大资源的 GPU 对比分开 |
| `attenio-fa259-launch` | [FA2 v2.5.9 固定分块实现](../references/proceedings/ASPLOS/2026/attenio-crosschecks/flash_fwd_launch_template.h) | 官方实现 | 补充／版本参照 | 只读 head_dim=64 分支，类型定义另核；未执行 |
| `attenio-fa259-softmax` | [FA2 v2.5.9 固定 Softmax 实现](../references/proceedings/ASPLOS/2026/attenio-crosschecks/softmax.h) | 官方实现 | 补充／版本参照 | 选读缩放与归一化，独立小例子检查递推 |
| `attenio-saha24-abstract` | [Saha／Ye，ICML 2024](../references/proceedings/ASPLOS/2026/attenio-crosschecks/saha24a.html) | 原始完整摘要 | 补充／版本参照 | 大小缓存区域的下界线索；未读完整证明 |
| `asplos26-paper-068` | [RedFuser：归约融合的设计与数值条件](../references/proceedings/ASPLOS/2026/paper-068.pdf) | 论文／作者稿 | 补充／版本参照 | 5.3.3；选读页 2–12、15–18 内声明范围，含第 12 页左栏结论 |
| `redfuser-decompose` | [RedFuser 固定符号分解实现](../references/proceedings/ASPLOS/2026/redfuser-crosschecks/decompose.txt) | 官方实现 | 补充／版本参照 | 5.3.3 扩写；完整静态阅读，未执行或审计全部依赖 |
| `redfuser-online-expr` | [RedFuser 在线表达式生成入口](../references/proceedings/ASPLOS/2026/redfuser-crosschecks/online-expr.txt) | 官方实现 | 补充／版本参照 | 5.3.3 扩写；完整静态阅读，顺序与分段路径分别记录 |
| `redfuser-quant-generated` | [RedFuser FP8 生成示例](../references/proceedings/ASPLOS/2026/redfuser-crosschecks/quant-generated.txt) | 官方实现 | 补充／版本参照 | 实验 5-4 扩写；前缀尺度与 cast 核对，未运行内核 |
| `redfuser-quant-test` | [RedFuser FP8 参考与误差测试](../references/proceedings/ASPLOS/2026/redfuser-crosschecks/quant-test.txt) | 官方实现 | 补充／版本参照 | 实验 5-4 扩写；完整静态阅读，随机输入容差不代表普遍等价 |
| `redfuser-onnx-float8` | [ONNX Float8 类型与转换](../references/proceedings/ASPLOS/2026/redfuser-crosschecks/onnx-float8.html) | 官方文档 | 补充／版本参照 | 实验 5-4 扩写；只读 E4M3FN/E5M2 定义与 Cast 两节 |
| `asplos26-paper-101` | [RhymeRL：历史草稿与 RL 供给](../references/proceedings/ASPLOS/2026/paper-101.pdf) | 补充 | 补充／版本参照 | 8.3.1／10.5.3；选读公开 v1 页 2–12 内声明范围，正式版另核 |
| `rhymerl-vllm-suffix-guide` | [vLLM 固定 Suffix 指南](../references/proceedings/ASPLOS/2026/rhymerl-crosschecks/vllm-suffix-guide.txt) | 补充 | 补充／版本参照 | 8.3.1 扩写；完整指南，未执行示例 |
| `rhymerl-vllm-rejection` | [vLLM 固定 rejection sampler](../references/proceedings/ASPLOS/2026/rhymerl-crosschecks/vllm-rejection.txt) | 补充 | 补充／版本参照 | 草稿与目标概率；仅读取登记行段，不代表全部采样路径审计 |
| `rhymerl-arctic-cache` | [Arctic 固定历史缓存](../references/proceedings/ASPLOS/2026/rhymerl-crosschecks/arctic-cache.txt) | 补充 | 补充／版本参照 | 实验 8-5／10-8；完整静态阅读，容量上限与请求数分别计量 |
| `asplos26-paper-127` | [LOOPRAG：候选反馈与评测范围](../references/proceedings/ASPLOS/2026/paper-127.pdf) | 补充 | 补充／版本参照 | 5.3.5 扩写；选读公开 v1 页 4–13、18–22，采用方法与条件，不移用 CPU 加速倍数 |
| `optval-fib-evaluation` | [FlashInfer 比赛：B200、基线与评分](../references/framework-history/2026-09-08/optimization-validation/starter-evaluation.md) | 补充 | 补充／版本参照 | 实验 5-6；固定比赛提交，不作为所有 GPU／模型的默认评测条件 |
| `optval-fib-default` | [FlashInfer-Bench 默认评估器](../references/framework-history/2026-09-08/optimization-validation/fib-default.py) | 补充 | 补充／版本参照 | 5.3.5；完整静态阅读，专用 evaluator 与时间后端另核 |
| `optval-fib-runtime` | [FlashInfer-Bench apply 运行时](../references/framework-history/2026-09-08/optimization-validation/fib-runtime.py) | 补充 | 补充／版本参照 | 实验 5-9；完整静态阅读，匹配表与完整引擎集成待核 |
| `remote-ordering-paper` | [Efficient Remote Memory Ordering（作者公开稿）](../references/proceedings/ASPLOS/2026/paper-116.pdf) | 7 | 补充／版本参照 | 正文页 2–13 选读；新硬件方案与无写冲突性能参照分别记录 |
| `remote-ordering-nvshmem-using` | [远端排序对照：nvshmem-using](../references/framework-history/2026-09-09/remote-ordering/nvshmem-using.html) | 7 | 补充／版本参照 | 声明范围见 remote-ordering/reading.json；文档快照与固定提交分别核对 |
| `remote-ordering-nvshmem-ordering` | [远端排序对照：nvshmem-ordering](../references/framework-history/2026-09-09/remote-ordering/nvshmem-ordering.html) | 7 | 补充／版本参照 | 声明范围见 remote-ordering/reading.json；文档快照与固定提交分别核对 |
| `remote-ordering-nvshmem-sync` | [远端排序对照：nvshmem-sync](../references/framework-history/2026-09-09/remote-ordering/nvshmem-sync.html) | 7 | 补充／版本参照 | 声明范围见 remote-ordering/reading.json；文档快照与固定提交分别核对 |
| `remote-ordering-author-readme` | [远端排序对照：author-readme](../references/framework-history/2026-09-09/remote-ordering/author-readme.md) | 7 | 补充／版本参照 | 声明范围见 remote-ordering/reading.json；文档快照与固定提交分别核对 |
| `remote-ordering-nvshmem-ib-common` | [远端排序对照：nvshmem-ib-common](../references/framework-history/2026-09-09/remote-ordering/nvshmem-ib-common.cpp) | 7 | 补充／版本参照 | 声明范围见 remote-ordering/reading.json；文档快照与固定提交分别核对 |
| `reward-resources-polyrl-readme` | [验证资源对照：polyrl-readme](../references/framework-history/2026-09-09/rollout-resources/polyrl-readme.md) | 11 | 补充／版本参照 | 11.3.3；固定版本与声明范围见 rollout-resources/reading.json，非完整框架实现审计 |
| `reward-resources-polyrl-usage` | [验证资源对照：polyrl-usage](../references/framework-history/2026-09-09/rollout-resources/polyrl-usage.md) | 11 | 补充／版本参照 | 11.3.3；固定版本与声明范围见 rollout-resources/reading.json，非完整框架实现审计 |
| `reward-resources-polyrl-roadmap` | [验证资源对照：polyrl-roadmap](../references/framework-history/2026-09-09/rollout-resources/polyrl-roadmap.md) | 11 | 补充／版本参照 | 11.3.3；固定版本与声明范围见 rollout-resources/reading.json，非完整框架实现审计 |
| `reward-resources-verl-reward-loop` | [验证资源对照：verl-reward-loop](../references/framework-history/2026-09-09/rollout-resources/verl-reward-loop.py) | 11 | 补充／版本参照 | 11.3.3；固定版本与声明范围见 rollout-resources/reading.json，非完整框架实现审计 |
| `reward-resources-verl-reward-remote` | [验证资源对照：verl-reward-remote](../references/framework-history/2026-09-09/rollout-resources/verl-reward-remote.py) | 11 | 补充／版本参照 | 11.3.3；固定版本与声明范围见 rollout-resources/reading.json，非完整框架实现审计 |
| `reward-resources-verl-reward-limited` | [验证资源对照：verl-reward-limited](../references/framework-history/2026-09-09/rollout-resources/verl-reward-limited.py) | 11 | 补充／版本参照 | 11.3.3；固定版本与声明范围见 rollout-resources/reading.json，非完整框架实现审计 |
| `reward-resources-verl-agent-loop` | [验证资源对照：verl-agent-loop](../references/framework-history/2026-09-09/rollout-resources/verl-agent-loop.py) | 11 | 补充／版本参照 | 11.3.3；固定版本与声明范围见 rollout-resources/reading.json，非完整框架实现审计 |
| `reward-resources-verl-v041-trainer` | [验证资源对照：verl-v041-trainer](../references/framework-history/2026-09-09/rollout-resources/verl-v041-trainer.py) | 11 | 补充／版本参照 | 11.3.3；固定版本与声明范围见 rollout-resources/reading.json，非完整框架实现审计 |
| `reward-resources-python-futures` | [验证资源对照：python-futures](../references/framework-history/2026-09-09/rollout-resources/python-futures.html) | 11 | 补充／版本参照 | 11.3.3；固定版本与声明范围见 rollout-resources/reading.json，非完整框架实现审计 |
| `rlboost-recovery-rlboost-polyrl-install` | [可抢占资源对照：rlboost-polyrl-install](../references/framework-history/2026-09-09/rlboost-recovery/polyrl-install.md) | 11 | 补充／版本参照 | 11.3.2；固定实现或官方配置，声明范围见 rlboost-recovery/reading.json |
| `rlboost-recovery-rlboost-polyrl-gitmodules` | [可抢占资源对照：rlboost-polyrl-gitmodules](../references/framework-history/2026-09-09/rlboost-recovery/polyrl-gitmodules.txt) | 11 | 补充／版本参照 | 11.3.2；固定实现或官方配置，声明范围见 rlboost-recovery/reading.json |
| `rlboost-recovery-rlboost-polyrl-launch-sglang` | [可抢占资源对照：rlboost-polyrl-launch-sglang](../references/framework-history/2026-09-09/rlboost-recovery/polyrl-launch-sglang.sh) | 11 | 补充／版本参照 | 11.3.2；固定实现或官方配置，声明范围见 rlboost-recovery/reading.json |
| `rlboost-recovery-rlboost-polyrl-config` | [可抢占资源对照：rlboost-polyrl-config](../references/framework-history/2026-09-09/rlboost-recovery/polyrl-config.toml) | 11 | 补充／版本参照 | 11.3.2；固定实现或官方配置，声明范围见 rlboost-recovery/reading.json |
| `rlboost-recovery-rlboost-qwen3-14b-config` | [可抢占资源对照：rlboost-qwen3-14b-config](../references/framework-history/2026-09-09/rlboost-recovery/qwen3-14b-config.json) | 11 | 补充／版本参照 | 11.3.2；固定实现或官方配置，声明范围见 rlboost-recovery/reading.json |
| `rlboost-recovery-rlboost-polyrl-sglang-launch` | [可抢占资源对照：rlboost-polyrl-sglang-launch](../references/framework-history/2026-09-09/rlboost-recovery/polyrl-sglang-launch.py) | 11 | 补充／版本参照 | 11.3.2；固定实现或官方配置，声明范围见 rlboost-recovery/reading.json |
| `rlboost-recovery-rlboost-polyrl-sglang-autopatch` | [可抢占资源对照：rlboost-polyrl-sglang-autopatch](../references/framework-history/2026-09-09/rlboost-recovery/polyrl-sglang-autopatch.py) | 11 | 补充／版本参照 | 11.3.2；固定实现或官方配置，声明范围见 rlboost-recovery/reading.json |
| `rlboost-recovery-rlboost-polyrl-handlers` | [可抢占资源对照：rlboost-polyrl-handlers](../references/framework-history/2026-09-09/rlboost-recovery/polyrl-handlers.rs) | 11 | 补充／版本参照 | 11.3.2；固定实现或官方配置，声明范围见 rlboost-recovery/reading.json |
| `rlboost-recovery-rlboost-polyrl-state` | [可抢占资源对照：rlboost-polyrl-state](../references/framework-history/2026-09-09/rlboost-recovery/polyrl-state.rs) | 11 | 补充／版本参照 | 11.3.2；固定实现或官方配置，声明范围见 rlboost-recovery/reading.json |
| `rlboost-recovery-rlboost-polyrl-utils` | [可抢占资源对照：rlboost-polyrl-utils](../references/framework-history/2026-09-09/rlboost-recovery/polyrl-utils.rs) | 11 | 补充／版本参照 | 11.3.2；固定实现或官方配置，声明范围见 rlboost-recovery/reading.json |
| `rlboost-recovery-rlboost-polyrl-fsdp-interface` | [可抢占资源对照：rlboost-polyrl-fsdp-interface](../references/framework-history/2026-09-09/rlboost-recovery/polyrl-fsdp-interface.py) | 11 | 补充／版本参照 | 11.3.2；固定实现或官方配置，声明范围见 rlboost-recovery/reading.json |
| `rlboost-recovery-rlboost-polyrl-sender` | [可抢占资源对照：rlboost-polyrl-sender](../references/framework-history/2026-09-09/rlboost-recovery/polyrl-sender.py) | 11 | 补充／版本参照 | 11.3.2；固定实现或官方配置，声明范围见 rlboost-recovery/reading.json |
| `rlboost-recovery-rlboost-polyrl-receiver` | [可抢占资源对照：rlboost-polyrl-receiver](../references/framework-history/2026-09-09/rlboost-recovery/polyrl-receiver.py) | 11 | 补充／版本参照 | 11.3.2；固定实现或官方配置，声明范围见 rlboost-recovery/reading.json |
| `rlboost-recovery-rlboost-polyrl-sglang-patches` | [可抢占资源对照：rlboost-polyrl-sglang-patches](../references/framework-history/2026-09-09/rlboost-recovery/polyrl-sglang-patches.py) | 11 | 补充／版本参照 | 11.3.2；固定实现或官方配置，声明范围见 rlboost-recovery/reading.json |
| `rlboost-recovery-rlboost-polyrl-tcp-engine` | [可抢占资源对照：rlboost-polyrl-tcp-engine](../references/framework-history/2026-09-09/rlboost-recovery/polyrl-tcp-engine.py) | 11 | 补充／版本参照 | 11.3.2；固定实现或官方配置，声明范围见 rlboost-recovery/reading.json |
| `asplos26-pact-body` | [PACT 正文范围](../references/proceedings/ASPLOS/2026/pact-reading.json) | 6、9 | 补充／版本参照 | 6.6→9.3／9.5；窗口停顿、迁移与 NUMA 模拟条件 |
| `asplos26-camp-body` | [Camp 正文范围](../references/proceedings/ASPLOS/2026/camp-reading.json) | 6、9 | 补充／版本参照 | 6.6→9.3／9.5；未饱和预测、加权交错及平台条件 |
| `memory-tiering-fixed-implementations` | [分层内存固定实现对照](../references/framework-history/2026-09-09/memory-tiering/README.md) | 6、9 | 补充／版本参照 | 6.6→9.3／9.5；PACT 工件演进、Camp 补丁、Linux 与 vLLM 对象边界 |
| `memory-tiering-qwen3-case` | [Qwen3 权重放置推算](../case-studies/memory-criticality-and-tiering.md) | 6、9 | 补充／版本参照 | 6.6→9.3／9.5；现有实验 6-9／9-7 的扩写依据；不新增编号 |
| `asplos26-morphlux-body` | [Morphlux 正文范围](../references/proceedings/ASPLOS/2026/morphlux-reading.json) | 6、7、11 | 补充／版本参照 | 6.4→7.5／7.6→11.3；公开 v3 与正式版本、三种验证层次分开 |
| `torus-allocation-fixed-artifact` | [资源分配与固定工件](../references/framework-history/2026-09-09/torus-allocation/README.md) | 6、7、11 | 补充／版本参照 | 形状、端口、容量与恢复；NCCL 接口不等于端口收益保证 |
| `torus-allocation-arithmetic` | [Qwen3 消息与位置枚举](../research/2026-infra-survey/torus-allocation-arithmetic.json) | 6、7、11 | 补充／版本参照 | 现有实验 6-4、7-8、11-3；计算示例不替代物理系统实测 |
| `asplos26-m2xfp-body` | [M²XFP 正文范围](../references/proceedings/ASPLOS/2026/m2xfp-reading.json) | 4、5、8 | 补充／版本参照 | 4.2.5→5.3→8.4；静态与动态编码、元数据及专用架构条件 |
| `metadata-quantization-implementations` | [格式与实际实现](../references/framework-history/2026-09-09/metadata-quantization/README.md) | 4、5、8 | 补充／版本参照 | 伪量化、vLLM v0.12.0 与固定当前路径；质量与执行分别核对 |
| `metadata-quantization-qwen3-case` | [同一 Qwen3 权重的表示](../case-studies/kernel-orchestration-and-quantization.md) | 4、5、8 | 补充／版本参照 | 现有实验 4-2／5-4 与图 4-3；容量、搜索与缓冲推算，不新增编号 |
| `asplos26-wave-body` | [Wave 正文范围](../references/proceedings/ASPLOS/2026/wave-reading.json) | 1、11 | 补充／版本参照 | 2025 出版卷、2026 日程；十三页正文范围与五张实际查看图页 |
| `smartnic-policy-interfaces` | [Wave 与公开 ghOSt 接口](../references/framework-history/2026-09-09/smartnic-policy/README.md) | 1、5、8、11 | 补充／版本参照 | 固定接口、硬件与主机请求路径分别核对；无引擎集成结论 |
| `smartnic-policy-agent-budget` | [主机调度与 Agent 平台预算](../case-studies/host-policy-and-dispatch.md) | 1、11 | 扩写 1,11 | 实验 1-6／11-1 的延伸；核数翻转点、环境容量与任务吞吐 |
| `asplos25-ascend-components-body` | [昇腾单元分析正文范围](../references/proceedings/ASPLOS/2025/ascend-components-reading.json) | 4、5 | 补充／版本参照 | 历史 MindSpore 与芯片条件、十三页正文和五张实际查看图页 |
| `ascend-components-framework` | [激活分支与性能采集](../references/framework-history/2026-09-09/ascend-components/README.md) | 5、8、9 | 补充／版本参照 | 固定普通／310P 入口、三段发行说明及 PD 采集；不把接口当作论文工件 |
| `ascend-components-qwen3-case` | [同一 Qwen3 的单元与流水推算](../case-studies/component-utilization-and-overlap.md) | 4、5 | 扩写 5 | 5.2.3／5.3.5、实验 5-6、图 5-5；R×E、缓冲和资源共享 |
| `asplos25-diffuse-body` | [Diffuse 正文范围](../references/proceedings/ASPLOS/2025/diffuse-reading.json) | 5、6 | 补充／版本参照 | 十二页正文与四张图页；任务、内核和临时存储的不同边界 |
| `asplos25-cxlfork-body` | [CXLfork 正文范围](../references/proceedings/ASPLOS/2025/cxlfork-reading.json) | 6、11 | 补充／版本参照 | 十三页正文与四张图页；进程原型、共享页和分层限制 |
| `snapshot-residency-e2b` | [E2B 模板读取与内存安装](../references/framework-history/2026-09-09/snapshot-residency/README.md) | 11 | 补充／版本参照 | 固定提交、六份响应／十个范围；不将原型当作云服务实现 |
| `snapshot-residency-case` | [快照恢复与首次访问预算](../case-studies/snapshot-residency-and-first-use.md) | 11 | 扩写 11 | 实验 11-2／图 11-3 的容量、共享带宽与粒度变体 |
| `asplos25-darwingame-body` | [DarwinGame 正文范围](../references/proceedings/ASPLOS/2025/darwingame-reading.json) | 5 | 补充／版本参照 | 十三页正文与七张图页；CPU 配置比赛的噪声与争用条件 |
| `tuning-measurement-framework` | [公开工件与框架计时](../references/framework-history/2026-09-09/tuning-measurement/README.md) | 5、8 | 补充／版本参照 | vLLM 三个年份、FlashInfer-Bench 固定入口；十四份响应和二十一个范围 |
| `tuning-measurement-case` | [比较顺序与实际形状](../case-studies/optimization-evaluation-and-deployment.md) | 2、5 | 扩写 5 | 实验 5-6／5-9：配对、争用和 Qwen3 SwiGLU 局部宽度 |
