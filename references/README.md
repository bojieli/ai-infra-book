# 本地参考资料库

对应草案 22 的十三章顺序：方法与需求、硬件与协作、推理训练、任务环境与端边云、综合设计。收录原始论文、作者报告、芯片与系统规格、协议及官方软件文档，按具体论证选用。原件快照保留历史版本；本索引章号采用当前目录。

当前清单 230 项：已保存正文 226 项，其中 PDF 136 份。其余项目的获取状态见文末。

[浏览本地索引](index.html) · [来源清单](sources.tsv) · [下载与校验记录](manifest.json) · [证据缺口](GAPS.md)

[LLM 推理论文选读与写作落点](INFERENCE-PAPER-GUIDE.md)按问题整理 49 项核心与专题资料，标注查阅小节、可支撑的论点及引用边界；另有 [章节映射](inference-reading-map.tsv)和[本轮新增论文 BibTeX](inference-additions.bib)。

[芯片与系统资料覆盖](HARDWARE-COVERAGE.md)按架构列出论文、编程文档和产品规格，并说明尚缺的证据；关键网页配图另见[配图索引](figures/README.md)。

作者补充的 UB 正式规范、操作系统参考设计和昇腾 950 白皮书，见 [三份文档的核对笔记](UB-ASCEND-NOTES.md)。

昇腾与 NVIDIA 的数据通路、动态 shape、编程责任和代际证据，见 [架构与执行比较](../case-studies/accelerator-architecture.md)。第 4 章分析硬件供给，第 5 章用实现与执行轨迹验证。

PDF 原件位于 `files/`，可搜索文本位于 `text/`；官方网页同时保存原始 HTML 与离线文本，外部图片、脚本和站内链接不保证离线可用。不得把网页入口记作规范全文。

`manifest.json` 记录实际获取时间、下载与来源地址、内容校验值、字节数、PDF 页数及能从正文识别出的 arXiv／ChinaXiv 版本。网页和可变分支按本地文件的 SHA-256 固定快照；下载完成不代表已经逐页审阅。

`local_snapshot` 表示从作者本地仓库的指定提交归档，记录仓库路径与提交号，不计作网络下载。`landing_only` 是索引入口，`incomplete_text` 表示未取得完整正文，`access_required` 表示来源要求额外的访问条件。

`user_provided` 表示作者提供的原件，保留原文件名并记录校验值。清单中的 `local:` 地址只用于读取本资料库内的文件，不发起网络请求；其中的登记时间不是原始下载时间。

本书使用的 PDF 均须归档到仓库并登记 sources.tsv 与 manifest.json，生成可搜索文本和章节索引；案例使用仓库内相对链接，不能仅引用 Downloads 等个人目录。

片上数据移动与能耗的写作落点见 [LogicFolding 笔记](../case-studies/logicfolding-energy.md)；网络处理与 PCIe 并发预算见 [可编程网卡案例](../case-studies/programmable-nic.md)。两篇作者提供的 PDF 均已归档。

写作时先查本地资料，引用具体页码、节号、版本及适用条件。规格、实现和测量分别取证；新证据改变参数时新增或明确更新快照，保留变更原因。

## 第 1 章 初识 AI Infra

| 资料 | 本地文件 | 用途 |
| --- | --- | --- |
| [Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures](https://digicoll.lib.berkeley.edu/record/136692) | [原件](files/papers/roofline.pdf) · [文本](text/roofline.txt) | 作者机构技术报告；Berkeley 图书馆归档 |
| [The Hardware Lottery](https://arxiv.org/abs/2009.06489) | [原件](files/papers/hardware-lottery.pdf) · [文本](text/hardware-lottery.txt) | 硬件、软件与研究选择 |
| [In-Datacenter Performance Analysis of a Tensor Processing Unit](https://arxiv.org/abs/1704.04760) | [原件](files/papers/tpu-v1.pdf) · [文本](text/tpu-v1.txt) | TPU 起源与设计比较 |
| [计算机网络的新黄金时代（一）](https://01.me/2023/05/new-golden-age-for-network-1/) | [原件](files/documents/network-golden-1.html) · [文本](text/network-golden-1.txt) | 作者素材；数据中心 |
| [基于可编程网卡的高性能数据中心系统](https://01.me/files/pubs/bojieli-phd-thesis.pdf) | [原件](files/papers/bojieli-phd-thesis.pdf) · [文本](text/bojieli-phd-thesis.txt)（user_provided） | 李博杰博士论文，2019-05-26；ClickNP 核数预算、KV-Direct PCIe 并发与数据通路；论文测量按原配置引用 |
| [Huawei’s τ Chip Was Supposed to Melt?](files/papers/202609.00031v1.pdf) | [原件](files/papers/202609.00031v1.pdf) · [文本](text/logicfolding-energy.txt)（user_provided） | 何庭波，ChinaXiv:202609.00031v1，2026-09-04；片上连线、降压与功率密度；作者报告，AI 集群 80% 能耗说法待独立取证 |

## 第 2 章 模型架构

| 资料 | 本地文件 | 用途 |
| --- | --- | --- |
| [Attention Is All You Need](https://arxiv.org/abs/1706.03762) | [原件](files/papers/transformer.pdf) · [文本](text/transformer.txt) | 原始架构与并行度 |
| [Fast Transformer Decoding: One Write-Head is All You Need](https://arxiv.org/abs/1911.02150) | [原件](files/papers/mqa.pdf) · [文本](text/mqa.txt) | MQA 与 KV 访问 |
| [GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints](https://arxiv.org/abs/2305.13245) | [原件](files/papers/gqa.pdf) · [文本](text/gqa.txt) | GQA |
| [DeepSeekMoE: Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models](https://arxiv.org/abs/2401.06066) | [原件](files/papers/deepseek-moe.pdf) · [文本](text/deepseek-moe.txt) | 专家粒度与共享专家 |
| [DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model](https://arxiv.org/abs/2405.04434) | [原件](files/papers/deepseek-v2.pdf) · [文本](text/deepseek-v2.txt) | MLA |
| [DeepSeek-V3 Technical Report](https://arxiv.org/abs/2412.19437) | [原件](files/papers/deepseek-v3.pdf) · [文本](text/deepseek-v3.txt) | FP8、MTP、负载均衡与训练系统 |
| [DeepSeek-V3.2: Pushing the Frontier of Open Large Language Models](https://arxiv.org/abs/2512.02556) | [原件](files/papers/deepseek-v32.pdf) · [文本](text/deepseek-v32.txt) | DSA 与后训练 |
| [DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence](https://arxiv.org/abs/2606.19348) | [原件](files/papers/deepseek-v4.pdf) · [文本](text/deepseek-v4.txt) | 混合压缩注意力与分阶段训练 |
| [Kimi K3: Open Frontier Intelligence](https://github.com/MoonshotAI/Kimi-K3) | [原件](files/papers/kimi-k3.pdf) · [文本](text/kimi-k3.txt) | 官方报告；以内容校验值固定版本 |
| [Kimi Linear: An Expressive, Efficient Attention Architecture](https://arxiv.org/abs/2510.26692) | [原件](files/papers/kimi-linear.pdf) · [文本](text/kimi-linear.txt) | KDA 与分块实现 |
| [Gated Delta Networks: Improving Mamba2 with Delta Rule](https://arxiv.org/abs/2412.06464) | [原件](files/papers/gated-delta.pdf) · [文本](text/gated-delta.txt) | 线性注意力与并行训练 |
| [Mamba: Linear-Time Sequence Modeling with Selective State Spaces](https://arxiv.org/abs/2312.00752) | [原件](files/papers/mamba.pdf) · [文本](text/mamba.txt) | 状态空间与硬件执行 |
| [Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity](https://arxiv.org/abs/2101.03961) | [原件](files/papers/switch-transformer.pdf) · [文本](text/switch-transformer.txt) | 条件计算与路由 |
| [Qwen3.5-397B-A17B official configuration](https://huggingface.co/Qwen/Qwen3.5-397B-A17B/blob/main/config.json) | [原件](files/models/qwen35-config.json) · [文本](text/qwen35-config.txt) | 本次注意力复算输入 |
| [Qwen3.5-397B-A17B official model card](https://huggingface.co/Qwen/Qwen3.5-397B-A17B) | [原件](files/models/qwen35-card.md) · [文本](text/qwen35-card.txt) | 模型卡与训练报告不是同一种来源 |
| [FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](https://arxiv.org/abs/2205.14135) | [原件](files/papers/flashattention.pdf) · [文本](text/flashattention.txt) | 分块、融合与 HBM 访问 |
| [OpenTallas architecture and analysis](https://github.com/bojieli/OpenTallas/tree/39b96158d35b24bd2bcd49061a689aea6893d2ed) | [原件](files/documents/opentallas-readme.md) · [文本](text/opentallas-readme.txt)（local_snapshot） | 与本书已有案例使用相同提交 |
| [Llama 2: Open Foundation and Fine-Tuned Chat Models](https://arxiv.org/abs/2307.09288) | [原件](files/papers/llama2.pdf) · [文本](text/llama2.txt) | 历史 70B 案例的配置来源 |
| [The Llama 3 Herd of Models](https://arxiv.org/abs/2407.21783) | [原件](files/papers/llama3.pdf) · [文本](text/llama3.txt) | 架构与训练报告 |
| [Efficient Streaming Language Models with Attention Sinks](https://arxiv.org/abs/2309.17453v4) | [原件](files/papers/streamingllm.pdf) · [文本](text/streamingllm.txt) | Attention sinks 与滑动窗口；流式稳定性不等于保留完整历史检索能力 |
| [Qwen3 Technical Report](https://arxiv.org/abs/2505.09388v1) | [原件](files/papers/qwen3.pdf) · [文本](text/qwen3.txt) | Alibaba 公司技术报告；稠密／MoE 配置与 thinking budget，不代填 Qwen3.5 参数 |
| [Mixtral of Experts](https://arxiv.org/abs/2401.04088v1) | [原件](files/papers/mixtral.pdf) · [文本](text/mixtral.txt) | Mistral 公司模型报告；稀疏激活、专家路由与驻留参数的区别 |

## 第 3 章 推理与训练负载

| 资料 | 本地文件 | 用途 |
| --- | --- | --- |
| [DeepSeek-V3 Technical Report](https://arxiv.org/abs/2412.19437) | [原件](files/papers/deepseek-v3.pdf) · [文本](text/deepseek-v3.txt) | FP8、MTP、负载均衡与训练系统 |
| [DeepSeek-V3.2: Pushing the Frontier of Open Large Language Models](https://arxiv.org/abs/2512.02556) | [原件](files/papers/deepseek-v32.pdf) · [文本](text/deepseek-v32.txt) | DSA 与后训练 |
| [DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence](https://arxiv.org/abs/2606.19348) | [原件](files/papers/deepseek-v4.pdf) · [文本](text/deepseek-v4.txt) | 混合压缩注意力与分阶段训练 |
| [Kimi K3: Open Frontier Intelligence](https://github.com/MoonshotAI/Kimi-K3) | [原件](files/papers/kimi-k3.pdf) · [文本](text/kimi-k3.txt) | 官方报告；以内容校验值固定版本 |
| [Scaling Laws for Neural Language Models](https://arxiv.org/abs/2001.08361) | [原件](files/papers/scaling-laws.pdf) · [文本](text/scaling-laws.txt) | 历史 scaling law；计算口径须重核 |
| [Training Compute-Optimal Large Language Models](https://arxiv.org/abs/2203.15556) | [原件](files/papers/chinchilla.pdf) · [文本](text/chinchilla.txt) | 参数、数据与预算 |
| [Qwen3.5-397B-A17B official configuration](https://huggingface.co/Qwen/Qwen3.5-397B-A17B/blob/main/config.json) | [原件](files/models/qwen35-config.json) · [文本](text/qwen35-config.txt) | 本次注意力复算输入 |
| [Qwen3.5-397B-A17B official model card](https://huggingface.co/Qwen/Qwen3.5-397B-A17B) | [原件](files/models/qwen35-card.md) · [文本](text/qwen35-card.txt) | 模型卡与训练报告不是同一种来源 |
| [In-Datacenter Performance Analysis of a Tensor Processing Unit](https://arxiv.org/abs/1704.04760) | [原件](files/papers/tpu-v1.pdf) · [文本](text/tpu-v1.txt) | TPU 起源与设计比较 |
| [Robust Speech Recognition via Large-Scale Weak Supervision](https://arxiv.org/abs/2212.04356) | [原件](files/papers/whisper.pdf) · [文本](text/whisper.txt) | ASR 计算与数据流 |
| [Conditional Variational Autoencoder with Adversarial Learning for End-to-End Text-to-Speech](https://arxiv.org/abs/2106.06103) | [原件](files/papers/vits.pdf) · [文本](text/vits.txt) | TTS 结构；不预设为流式系统 |
| [Mooncake: A KVCache-centric Disaggregated Architecture for LLM Serving](https://arxiv.org/abs/2407.00079) | [原件](files/papers/mooncake.pdf) · [文本](text/mooncake.txt) | KV 池化与路由 |
| [A100/H100 太贵，何不用 4090？](https://01.me/2023/09/h100-vs-4090/) | [原件](files/documents/h100-vs-4090.html) · [文本](text/h100-vs-4090.txt) | 历史价格与计算需按正文案例重新核算 |
| [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685) | [原件](files/papers/lora.pdf) · [文本](text/lora.txt) | 冻结参数与训练计算量 |
| [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314) | [原件](files/papers/qlora.pdf) · [文本](text/qlora.txt) | 量化微调 |
| [Llama 2: Open Foundation and Fine-Tuned Chat Models](https://arxiv.org/abs/2307.09288) | [原件](files/papers/llama2.pdf) · [文本](text/llama2.txt) | 历史 70B 案例的配置来源 |
| [The Llama 3 Herd of Models](https://arxiv.org/abs/2407.21783) | [原件](files/papers/llama3.pdf) · [文本](text/llama3.txt) | 架构与训练报告 |
| [Efficiently Scaling Transformer Inference](https://arxiv.org/abs/2211.05102v1) | [原件](files/papers/scaling-inference.pdf) · [文本](text/scaling-inference.txt) | Google；推理计算／通信模型、TPU 分片与延迟—吞吐取舍；历史配置不直接套用 GPU |
| [Qwen3 Technical Report](https://arxiv.org/abs/2505.09388v1) | [原件](files/papers/qwen3.pdf) · [文本](text/qwen3.txt) | Alibaba 公司技术报告；稠密／MoE 配置与 thinking budget，不代填 Qwen3.5 参数 |
| [DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/abs/2501.12948v2) | [原件](files/papers/deepseek-r1.pdf) · [文本](text/deepseek-r1.txt) | 公司技术报告；RL 推理模型、长输出与采样负载；不视为 serving 性能报告 |
| [Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters](https://arxiv.org/abs/2408.03314v1) | [原件](files/papers/test-time-compute.pdf) · [文本](text/test-time-compute.txt) | DeepMind／Berkeley；按难度分配推理预算；计算量、质量与墙钟时间分开 |

## 第 4 章 加速器架构

| 资料 | 本地文件 | 用途 |
| --- | --- | --- |
| [Kimi Linear: An Expressive, Efficient Attention Architecture](https://arxiv.org/abs/2510.26692) | [原件](files/papers/kimi-linear.pdf) · [文本](text/kimi-linear.txt) | KDA 与分块实现 |
| [Gated Delta Networks: Improving Mamba2 with Delta Rule](https://arxiv.org/abs/2412.06464) | [原件](files/papers/gated-delta.pdf) · [文本](text/gated-delta.txt) | 线性注意力与并行训练 |
| [FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](https://arxiv.org/abs/2205.14135) | [原件](files/papers/flashattention.pdf) · [文本](text/flashattention.txt) | 分块、融合与 HBM 访问 |
| [FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning](https://arxiv.org/abs/2307.08691) | [原件](files/papers/flashattention2.pdf) · [文本](text/flashattention2.txt) | 工作划分 |
| [FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-precision](https://arxiv.org/abs/2407.08608) | [原件](files/papers/flashattention3.pdf) · [文本](text/flashattention3.txt) | 异步执行与精度 |
| [Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures](https://digicoll.lib.berkeley.edu/record/136692) | [原件](files/papers/roofline.pdf) · [文本](text/roofline.txt) | 作者机构技术报告；Berkeley 图书馆归档 |
| [In-Datacenter Performance Analysis of a Tensor Processing Unit](https://arxiv.org/abs/1704.04760) | [原件](files/papers/tpu-v1.pdf) · [文本](text/tpu-v1.txt) | TPU 起源与设计比较 |
| [TPU v4: An Optically Reconfigurable Supercomputer for Machine Learning with Hardware Support for Embeddings](https://arxiv.org/abs/2304.01433) | [原件](files/papers/tpu-v4.pdf) · [文本](text/tpu-v4.txt) | 芯片与互联协同 |
| [NVIDIA Tesla V100 GPU Architecture](https://www.nvidia.com/en-gb/data-center/tesla-product-literature/) | [原件](files/specs/nvidia-v100.pdf) · [文本](text/nvidia-v100.txt) | 2017 年架构白皮书 |
| [NVIDIA A100 Tensor Core GPU Architecture](https://www.nvidia.com/en-us/data-center/a100/) | [原件](files/specs/nvidia-a100.pdf) · [文本](text/nvidia-a100.txt) | 架构白皮书；40GB 与 80GB 规格需区分 |
| [NVIDIA H100 Tensor Core GPU Architecture](https://resources.nvidia.com/en-us-hopper-architecture/nvidia-h100-tensor-c) | [原件](files/specs/nvidia-h100.pdf) · [文本](text/nvidia-h100.txt) | 下载地址由 NVIDIA 官方阅读页直接提供 |
| [NVIDIA H100 Product Specifications](https://www.nvidia.com/en-us/data-center/h100/) | [原件](files/specs/nvidia-h100-spec.html) · [文本](text/nvidia-h100-spec.txt) | 产品形态与规格表快照 |
| [NVIDIA Blackwell Tuning Guide](https://docs.nvidia.com/cuda/blackwell-tuning-guide/) | [原件](files/specs/nvidia-blackwell-guide.html) · [文本](text/nvidia-blackwell-guide.txt) | 官方微架构与编程依据 |
| [NVIDIA DGX B200 Specifications](https://www.nvidia.com/en-us/data-center/dgx-b200/) | [原件](files/specs/nvidia-dgx-b200.html) · [文本](text/nvidia-dgx-b200.txt) | 系统规格不能替代单芯片规格 |
| [NVIDIA GeForce RTX 4090 Specifications](https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/) | [原件](files/specs/nvidia-rtx4090.html) · [文本](text/nvidia-rtx4090.txt) | 历史硬件比较；KTransformers RTX 4090＋Xeon AF 案例 |
| [Communications of HUAWEI RESEARCH：昇腾架构论文所在期](https://www-file.huawei.com/admin/asset/v1/pro/view/6ca306adab0a4852bacffce25f5573ec.pdf) | [原件](files/specs/ascend-davinci.pdf) · [文本](text/ascend-davinci.txt) | 官方整期刊物；含 A Scalable and Unified AI Architecture；部分提取文字编码不完整，应查 PDF 原件 |
| [CANN 8.1.RC1.alpha002 Ascend C 算子开发指南](https://www.hiascend.com/) | [原件](files/specs/ascend-c-guide.pdf) · [文本](text/ascend-c-guide.txt) | 公开编程与硬件架构文档 |
| [CANN 9.0.0 Ascend C 硬件架构](https://www.hiascend.com/) | [原件](files/specs/ascend-c-architecture.html) · [文本](text/ascend-c-architecture.txt)（incomplete_text） | 若为动态页面，仅在获取到正文时记为全文 |
| [Huawei Atlas 900 and ResNet-50 announcement, 2019](https://www.huawei.com/kr/news/2019/9/huawei-computing-strategy-atlas-900-ai-training-cluster) | [原件](files/documents/ascend-910-launch.html) · [文本](text/ascend-910-launch.txt) | 历史负载；非 910C 微架构规格 |
| [昇腾 950 与 Unified Bus 公开路线图](https://www.huawei.com/cn/news/2025/9/hc-xu-keynote-speech) | [原件](files/specs/ascend-950-roadmap.html) · [文本](text/ascend-950-roadmap.txt) | 按型号区分计划与交付状态 |
| [Huawei SuperPoD Portfolio at MWC Barcelona 2026](https://www.huawei.com/en/news/2026/3/mwc-superpod-computing) | [原件](files/documents/ascend-950-mwc.html) · [文本](text/ascend-950-mwc.txt) | Atlas 950 至多 8192 NPU 的官方公告 |
| [Deploying Transformers on the Apple Neural Engine](https://machinelearning.apple.com/research/neural-engine-transformers) | [原件](files/documents/apple-ane.html) · [文本](text/apple-ane.txt) | 保留文章年代与实验设备 |
| [计算机网络的新黄金时代（三）](https://01.me/2023/06/new-golden-age-for-network-3/) | [原件](files/documents/network-golden-3.html) · [文本](text/network-golden-3.txt) | 作者素材；无线与端侧 |
| [FlexGen: High-Throughput Generative Inference of Large Language Models with a Single GPU](https://arxiv.org/abs/2303.06865) | [原件](files/papers/flexgen.pdf) · [文本](text/flexgen.txt) | 卸载与数据移动 |
| [Reducing Activation Recomputation in Large Transformer Models](https://arxiv.org/abs/2205.05198) | [原件](files/papers/activation-recompute.pdf) · [文本](text/activation-recompute.txt) | 选择性重计算 |
| [NVIDIA Blackwell Architecture Technical Brief](https://resources.nvidia.com/en-us-blackwell-architecture) | [原件](files/specs/nvidia-blackwell-brief.pdf) · [文本](text/nvidia-blackwell-brief.txt) | 官方入口直接提供的 PDF |
| [A100/H100 太贵，何不用 4090？](https://01.me/2023/09/h100-vs-4090/) | [原件](files/documents/h100-vs-4090.html) · [文本](text/h100-vs-4090.txt) | 历史价格与计算需按正文案例重新核算 |
| [OpenTallas architecture and analysis](https://github.com/bojieli/OpenTallas/tree/39b96158d35b24bd2bcd49061a689aea6893d2ed) | [原件](files/documents/opentallas-readme.md) · [文本](text/opentallas-readme.txt)（local_snapshot） | 与本书已有案例使用相同提交 |
| [GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers](https://arxiv.org/abs/2210.17323) | [原件](files/papers/gptq.pdf) · [文本](text/gptq.txt) | 权重量化 |
| [AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration](https://arxiv.org/abs/2306.00978) | [原件](files/papers/awq.pdf) · [文本](text/awq.txt) | 量化与设备效率 |
| [SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models](https://arxiv.org/abs/2211.10438) | [原件](files/papers/smoothquant.pdf) · [文本](text/smoothquant.txt) | 激活量化 |
| [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685) | [原件](files/papers/lora.pdf) · [文本](text/lora.txt) | 冻结参数与训练计算量 |
| [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314) | [原件](files/papers/qlora.pdf) · [文本](text/qlora.txt) | 量化微调 |
| [The Cerebras Wafer-Scale Architecture for Deep Learning](https://www.cerebras.ai/chip) | [原件](files/specs/cerebras-wse3.pdf) · [文本](text/cerebras-wse3.txt) | 13 页架构白皮书，正文介绍 WSE-3；官网 Datasheet 链接名称与正文标题不同，以正文为准 |
| [SambaNova SN40L Reconfigurable Dataflow Unit](https://sambanova.ai/) | [原件](files/specs/sambanova-sn40l.pdf) · [文本](text/sambanova-sn40l.txt) | 两页官方产品技术介绍；非完整微架构论文 |
| [SambaNova SambaRack SN40L-16 Datasheet](https://sambanova.ai/) | [原件](files/specs/sambanova-sambarack.pdf) · [文本](text/sambanova-sambarack.txt) | 按 PDF 正文核对产品代际，不从下载文件名推断日期 |
| [Think Fast: A Tensor Streaming Processor (TSP) for Accelerating Deep Learning Workloads](https://groq.com/papers/) | [原件](files/papers/groq-tsp.pdf) · [文本](text/groq-tsp.txt) | ISCA 2020；编译调度与确定性执行 |
| [A Software-defined Tensor Streaming Multiprocessor for Large-scale Machine Learning](https://groq.com/papers/) | [原件](files/papers/groq-scale.pdf) · [文本](text/groq-scale.txt) | ISCA 2022；多芯片协同 |
| [GroqChip Processor Product Brief v1.5](https://groq.com/papers/) | [原件](files/specs/groq-chip.pdf) · [文本](text/groq-chip.txt) | 官方规格；历史代际参数 |
| [Taalas HC1 Technology Demonstrator](https://taalas.com/products/) | [原件](files/specs/taalas-hc1.html) · [文本](text/taalas-hc1.txt) | 厂商模型固化产品介绍；吞吐为厂商声明，须保留负载条件 |
| [Etched 官方产品页面](https://www.etched.com/) | [原件](files/documents/etched-sohu.html) · [文本](text/etched-sohu.txt) | 当前公开介绍；不能代替 Sohu 完整微架构规格 |
| [Cerebras Wafer-Scale Engine 3 Datasheet](https://training-docs.cerebras.ai/rel-2.4.0/concepts/cerebras-wafer-scale-cluster) | [原件](files/specs/cerebras-wse3-spec.pdf) · [文本](text/cerebras-wse3-spec.txt) | 由官方开发文档直接链接；与 WSE-3T 区分 |
| [Cerebras CS-4 Datasheet](https://investors.cerebras.ai/news-releases/news-release-details/cerebras-unveils-cs-4-30-times-faster-gpu-based-solutions) | [原件](files/specs/cerebras-cs4-spec.pdf) · [文本](text/cerebras-cs4-spec.txt) | 2026 年公开新代际；保留产品声明和交付时间边界 |
| [昇腾 950 NPU 架构白皮书](files/specs/昇腾950%20NPU架构白皮书.pdf) | [原件](files/specs/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf) · [文本](text/ascend-950-whitepaper.txt)（user_provided） | 作者提供，40 页；保留原文件；另存官方 OBS 文件 ascend-950-official，两份文件差异核对见 UB-ASCEND-NOTES.md |
| [Google Cloud TPU v4 官方规格](https://docs.cloud.google.com/tpu/docs/v4) | [原件](files/specs/google-v4.html) · [文本](text/google-v4.txt) | 芯片、HBM、ICI 与 Pod 配置；云资源参数与硬件能力分别引用 |
| [Google Cloud TPU v5e 官方规格](https://docs.cloud.google.com/tpu/docs/v5e) | [原件](files/specs/google-v5e.html) · [文本](text/google-v5e.txt) | 芯片、HBM、ICI 与 Pod 配置；云资源参数与硬件能力分别引用 |
| [Google Cloud TPU v5p 官方规格](https://docs.cloud.google.com/tpu/docs/v5p) | [原件](files/specs/google-v5p.html) · [文本](text/google-v5p.txt) | 芯片、HBM、ICI 与 Pod 配置；云资源参数与硬件能力分别引用 |
| [Google Cloud TPU v6e 官方规格](https://docs.cloud.google.com/tpu/docs/v6e) | [原件](files/specs/google-v6e.html) · [文本](text/google-v6e.txt) | 芯片、HBM、ICI 与 Pod 配置；云资源参数与硬件能力分别引用 |
| [Google Cloud TPU tpu7x 官方规格](https://docs.cloud.google.com/tpu/docs/tpu7x) | [原件](files/specs/google-tpu7x.html) · [文本](text/google-tpu7x.txt) | 芯片、HBM、ICI 与 Pod 配置；云资源参数与硬件能力分别引用 |
| [Google Cloud TPU System Architecture](https://docs.cloud.google.com/tpu/docs/system-architecture-tpu-vm) | [原件](files/documents/google-tpu-architecture.html) · [文本](text/google-tpu-architecture.txt) | TensorCore、MXU、向量与存储组织 |
| [Google Cloud TPU Machine Specifications](https://docs.cloud.google.com/compute/docs/tpus/tpu-machines) | [原件](files/specs/google-tpu-machines.html) · [文本](text/google-tpu-machines.txt) | 主机 VM、芯片、ICI 和 DCN 的口径区别 |
| [Inside the Eighth-Generation TPU: An Architecture Deep Dive](https://cloud.google.com/blog/products/compute/tpu-8t-and-tpu-8i-technical-deep-dive) | [原件](files/specs/google-tpu8.html) · [文本](text/google-tpu8.txt) | 2026-04-22 官方技术说明及规格表；不等同于完整 ISA 或正式云实例规格 |
| [Google's Training Supercomputers from TPU v2 to Ironwood: Architectural Stability, Scale, Resilience, Power Efficiency, and Sustainability Across Five Generations](https://arxiv.org/abs/2606.15870) | [原件](files/papers/google-tpu-generations.pdf) · [文本](text/google-tpu-generations.txt) | Google 作者跨代架构论文；与云文档日期分别登记 |
| [The Data Center Architecture for Graphcore Computing](https://www.graphcore.ai/hubfs/Graphcore-Mk2-IPU-System-Architecture-GC.pdf) | [原件](files/specs/graphcore-mk2.pdf) · [文本](text/graphcore-mk2.txt) | 官方系统白皮书；芯片、Streaming Memory 与主机解耦 |
| [IPU-Machine M2000 Datasheet 1.0.0](https://docs.graphcore.ai/projects/graphcore-ipu-m2000-datasheet/en/1.0.0/) | [原件](files/specs/graphcore-m2000-pdf.pdf) · [文本](text/graphcore-m2000-pdf.txt) | 历史版本的整机规格，4 个 IPU 的参数不当作单芯片 |
| [IPU-M2000 Product Description and Technical Specifications](https://docs.graphcore.ai/projects/graphcore-ipu-m2000-datasheet/en/latest/product-description.html) | [原件](files/specs/graphcore-m2000.html) · [文本](text/graphcore-m2000.txt) | 官方完整产品规格章节快照；latest URL 不代表当前仍在销售 |
| [Bow-2000 Product Description and Technical Specifications](https://docs.graphcore.ai/projects/bow-2000-datasheet/en/latest/product-description.html) | [原件](files/specs/graphcore-bow2000.html) · [文本](text/graphcore-bow2000.txt) | 官方完整产品规格章节快照；latest URL 不代表当前仍在销售 |
| [IPU Hardware Overview](https://docs.graphcore.ai/projects/ipu-programmers-guide/en/latest/about_ipu.html) | [原件](files/documents/graphcore-hardware.html) · [文本](text/graphcore-hardware.txt) | 官方程序员指南的指定完整章节；非整套指南全文 |
| [IPU Programming Model](https://docs.graphcore.ai/projects/ipu-programmers-guide/en/latest/programming_model.html) | [原件](files/documents/graphcore-programming.html) · [文本](text/graphcore-programming.txt) | 官方程序员指南的指定完整章节；非整套指南全文 |
| [Graphcore Tile Vertex ISA 1.2.3 (GC200 and Bow)](https://docs.graphcore.ai/projects/isa/en/latest/) | [原件](files/specs/graphcore-isa.pdf) · [文本](text/graphcore-isa.txt) | 官方 worker-thread ISA；不夸大为芯片全部内部指令 |
| [Graphcore Tile Vertex ISA IPU21 1.3.1](https://docs.graphcore.ai/projects/isa/en/latest/) | [原件](files/specs/graphcore-isa-fp8.pdf) · [文本](text/graphcore-isa-fp8.txt) | C600 对应的 FP8 扩展；与 GC200、Bow 区分 |
| [Dissecting the Graphcore IPU Architecture via Microbenchmarking](https://arxiv.org/abs/1912.03413) | [原件](files/papers/graphcore-microbench.pdf) · [文本](text/graphcore-microbench.txt) | 原始测量论文；第一代 IPU 的结果不移植为 GC200 或 Bow 实测 |
| [SambaNova SN40L: Scaling the AI Memory Wall with Dataflow and Composition of Experts](https://arxiv.org/abs/2405.07518) | [原件](files/papers/sambanova-sn40l-paper.pdf) · [文本](text/sambanova-sn40l-paper.txt) | 厂商原始架构论文；三级存储、融合与多模型切换，非两页宣传材料 |
| [Introducing AMD CDNA 3 Architecture](https://www.amd.com/en/technologies/cdna.html) | [原件](files/specs/amd-cdna3.pdf) · [文本](text/amd-cdna3.txt) | 架构白皮书；MI300A 与 MI300X 的芯粒和内存组织分开 |
| [Introducing AMD CDNA 4 Architecture](https://www.amd.com/en/technologies/cdna.html) | [原件](files/specs/amd-cdna4.pdf) · [文本](text/amd-cdna4.txt) | 架构白皮书；精度、分块、存储与通信 |
| [AMD Instinct MI300X Product Specifications](https://www.amd.com/en/products/accelerators/instinct/mi300/mi300x.html) | [原件](files/specs/amd-mi300x.html) · [文本](text/amd-mi300x.txt) | 单加速器规格与功率边界 |
| [AMD Instinct MI300X Platform Datasheet](https://www.amd.com/en/products/accelerators/instinct/mi300/mi300x.html) | [原件](files/specs/amd-mi300x-platform.pdf) · [文本](text/amd-mi300x-platform.txt) | 8 GPU 平台；与单 OAM 规格区分 |
| [AMD Instinct MI350X GPU Datasheet](https://www.amd.com/en/products/accelerators/instinct/mi350/mi350x.html) | [原件](files/specs/amd-mi350x.pdf) · [文本](text/amd-mi350x.txt) | 单 OAM 规格，按精度与稀疏条件引用 |
| [AMD Instinct MI350X Platform Datasheet](https://www.amd.com/en/products/accelerators/instinct/mi350/mi350x.html) | [原件](files/specs/amd-mi350x-platform.pdf) · [文本](text/amd-mi350x-platform.txt) | 8 GPU 平台、互联、容量与系统功率 |
| [Intel Gaudi 3 AI Accelerator White Paper](https://www.intel.com/content/www/us/en/content-details/817486/intel-gaudi-3-ai-accelerator-white-paper.html) | [原件](files/specs/intel-gaudi3.pdf) · [文本](text/intel-gaudi3.txt) | July 2025 V1 Rev.3；矩阵、可编程核、HBM 与以太互联 |
| [寒武纪思元 370 系列官方产品规格](https://cambricon.com/index.php?a=lists&c=index&catid=360&m=content) | [原件](files/specs/cambricon-mlu370.html) · [文本](text/cambricon-mlu370.txt) | 官方产品页；不能代替完整 ISA、微架构或后续代际规格 |
| [AWS Trainium2 Architecture](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/about-neuron/arch/neuron-hardware/trainium2.html) | [原件](files/specs/aws-trainium2.html) · [文本](text/aws-trainium2.txt) | 芯片规格；与 NKI 指南中 CC-Core 计数的口径差异单列 |
| [AWS Trainium3 Architecture](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/about-neuron/arch/neuron-hardware/trainium3.html) | [原件](files/specs/aws-trainium3.html) · [文本](text/aws-trainium3.txt) | 单芯片 NeuronCore、内存、DMA 与 NeuronLink 规格 |
| [AWS NeuronCore-v3 Architecture](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/about-neuron/arch/neuron-hardware/neuron-core-v3.html) | [原件](files/documents/aws-neuroncore-v3.html) · [文本](text/aws-neuroncore-v3.txt) | Tensor、Vector、Scalar、GPSIMD 与片上存储 |
| [Trainium3 Architecture Guide for NKI](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/nki/guides/architecture/trainium3_arch.html) | [原件](files/documents/aws-trainium3-nki.html) · [文本](text/aws-trainium3-nki.txt) | 算子编程视角；内存带宽和 CC-Core 数与产品架构表有差异，保留版本 |
| [Hot Chips 2026: SN50 RDU Dataflow at Scale](https://sambanova.ai/blog/hot-chips-2026-dataflow-at-scale) | [原件](files/documents/sambanova-sn50.html) · [文本](text/sambanova-sn50.txt) | 2026-09-02 厂商技术说明；模型推演与测量结果分别标注 |
| [Inside NVIDIA Rubin GPU Architecture](https://developer.nvidia.com/blog/inside-nvidia-rubin-gpu-architecture-powering-the-era-of-agentic-ai/) | [原件](files/documents/nvidia-rubin-arch.html) · [文本](text/nvidia-rubin-arch.txt) | 2026-07-21 官方技术说明；与早期发布规格分开记录 |
| [NVIDIA Vera Rubin NVL72 Specifications](https://www.nvidia.com/en-us/data-center/vera-rubin-nvl72/) | [原件](files/specs/nvidia-rubin-system.html) · [文本](text/nvidia-rubin-system.txt) | 当前官方产品规格；部署形态、精度和供货状态分开 |
| [Snapdragon X Elite Product Brief](https://www.qualcomm.com/content/dam/qcomm-martech/dm-assets/images/company/news-media/media-center/press-kits/snapdragon-summit-2023/documents/SnapdragonXEliteProductBrief.pdf) | [原件](files/specs/qualcomm-xelite.pdf) · [文本](text/qualcomm-xelite.txt) | 端侧 CPU、GPU、Hexagon 与共享内存；2023 年产品代际 |
| [MacBook Pro (14-inch, M5) Technical Specifications](https://support.apple.com/en-mide/125405) | [原件](files/specs/apple-m5-macbook.html) · [文本](text/apple-m5-macbook.txt) | 2025 年具体端侧产品；CPU、GPU、Neural Engine 与统一内存，非完整微架构手册 |
| [Serving Large Language Models on Huawei CloudMatrix384, v2](https://arxiv.org/abs/2506.12708v2) | [原件](files/papers/cloudmatrix384-v2.pdf) · [文本](text/cloudmatrix384-v2.txt) | 2025-06-18；§3.3.1 的 910C、§4.2.2 MLA 与动态 tiling；与 v3 分开保存 |
| [Serving Large Language Models on Huawei CloudMatrix384, v3](https://arxiv.org/abs/2506.12708v3) | [原件](files/papers/cloudmatrix384-v3.pdf) · [文本](text/cloudmatrix384-v3.txt) | 2025-06-19 修订；核对型号称谓与 v2 差异 |
| [NVIDIA Hopper Tuning Guide](https://docs.nvidia.com/cuda/hopper-tuning-guide/index.html) | [原件](files/documents/nvidia-hopper-tuning.html) · [文本](text/nvidia-hopper-tuning.txt) | SM、Tensor Core、TMA 与 shared memory；固定网页快照 |
| [CUDA Programming Guide 13.2.1: Asynchronous Data Copies](https://docs.nvidia.com/cuda/archive/13.2.1/cuda-programming-guide/04-special-topics/async-copies.html) | [原件](files/documents/nvidia-async-copies.html) · [文本](text/nvidia-async-copies.txt) | 显式异步搬运、tensor map、stride、对齐与同步；与 NDDMA 比较 |
| [昇腾 950 NPU 架构白皮书（官方下载原件）](https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf) | [原件](files/specs/ascend-950-official.pdf) · [文本](text/ascend-950-official.txt) | 作者提供官方 OBS 下载地址；与先前作者提供版本分别保留，差异核对见 UB-ASCEND-NOTES.md |
| [Apple M2 Pro and M2 Max launch specifications](https://www.apple.com/newsroom/2023/01/apple-unveils-m2-pro-and-m2-max-next-generation-chips-for-next-level-workflows/) | [原件](files/specs/apple-m2-pro-max.html) · [文本](text/apple-m2-pro-max.txt) | 2023-01-17；M2 Pro 200 GB/s，M2 Max 400 GB/s；本书实机为 M2 Max 38 核 GPU、96 GB |
| [Choosing a resource storage mode for Apple GPUs — DocC JSON](https://developer.apple.com/tutorials/data/documentation/metal/choosing-a-resource-storage-mode-for-apple-gpus.json) | [原件](files/documents/apple-metal-memory.json) · [文本](text/apple-metal-memory.txt) | 官方文档数据原件；shared／private、访问和同步；非芯片完整微架构 |
| [Explore the architecture of Apple GPUs — WWDC20](https://developer.apple.com/videos/play/wwdc2020/10602/) | [原件](files/documents/apple-gpu-architecture.html) · [文本](text/apple-gpu-architecture.txt) | Apple GPU 执行与存储模型；2020 年架构说明不证明 M2 未公开单元参数 |
| [RTX PRO 6000 Blackwell Workstation Edition Datasheet](https://www.nvidia.com/content/dam/en-zz/Solutions/data-center/rtx-pro-6000-blackwell-workstation-edition/workstation-blackwell-rtx-pro-6000-workstation-edition-nvidia-us-3519208-web.pdf) | [原件](files/specs/nvidia-rtx-pro6000-spec.pdf) · [文本](text/nvidia-rtx-pro6000-spec.txt) | 用户确认 Workstation Edition；96 GB GDDR7、1792 GB/s、600 W；不能套用 Max-Q／Server 参数 |
| [NVIDIA RTX Blackwell PRO GPU Architecture v1.0](https://www.nvidia.com/content/dam/en-zz/Solutions/design-visualization/quadro-product-literature/NVIDIA-RTX-Blackwell-PRO-GPU-Architecture-v1.0.pdf) | [原件](files/specs/nvidia-rtx-blackwell-pro.pdf) · [文本](text/nvidia-rtx-blackwell-pro.txt) | RTX Blackwell 的 SM、Tensor Core 与 GDDR7；与 B200 数据中心 Blackwell 分开分析 |
| [KTransformers 0.3 AMX design notes](https://raw.githubusercontent.com/kvcache-ai/ktransformers/31985f40bcc40da08107efdb1f81bf88cb38c6b2/doc/en/AMX.md) | [原件](files/documents/kt-amx.md) · [文本](text/kt-amx.txt) | 2025 年 v0.3 历史设计；Intel AMX、AVX-512、权重重排与调度；性能按原配置引用 |
| [NVIDIA A100 80GB datasheet — December 2020](https://www.nvidia.cn/content/dam/en-zz/zh_cn/Solutions/Data-Center/a100/pdf/a100-80gb-datasheet-update-a4-nvidia-1485612-r13-web_zhCN.pdf) | [原件](files/specs/nvidia-a100-80-spec.pdf) · [文本](text/nvidia-a100-80-spec.txt) | A100 80 GB；SXM 与 PCIe、稠密与稀疏峰值分别引用 |
| [NVIDIA AI Enterprise 6.2 supported H20 SXM5 configurations](https://docs.nvidia.com/ai-enterprise/release-6/6.2/appendix/vgpu.html) | [原件](files/specs/nvidia-h20-vgpu.html) · [文本](text/nvidia-h20-vgpu.txt) | 官方确认 H20 SXM5 96GB 型号；不是完整 H20 带宽／算力数据表 |
| [Bullet: Boosting GPU Utilization for LLM Serving via Dynamic Spatial-Temporal Orchestration](https://xianweiz.github.io/doc/papers/26asplos_bullet.pdf) | [原件](files/papers/bullet.pdf) · [文本](text/bullet.txt) | ASPLOS 2026 作者原件；A100/H20 内存与 SM 微基准；作为同卡 P/D 协作对照，不是 A100＋H20 PD 部署实测 |
| [Ollama v0.20.7 bundled ggml Metal kernels](https://raw.githubusercontent.com/ollama/ollama/8d0dcf4b6daf8d7833c8b55108e5b45063795e57/ml/backend/ggml/ggml/src/ggml-metal/ggml-metal.metal) | [原件](files/documents/ollama-ggml-metal-kernels.txt) · [文本](text/ollama-ggml-metal-kernels.txt) | 固定提交；量化解码、矩阵／向量计算、simdgroup；实际分派仍需运行日志确认 |
| [Efficiently Scaling Transformer Inference](https://arxiv.org/abs/2211.05102v1) | [原件](files/papers/scaling-inference.pdf) · [文本](text/scaling-inference.txt) | Google；推理计算／通信模型、TPU 分片与延迟—吞吐取舍；历史配置不直接套用 GPU |
| [基于可编程网卡的高性能数据中心系统](https://01.me/files/pubs/bojieli-phd-thesis.pdf) | [原件](files/papers/bojieli-phd-thesis.pdf) · [文本](text/bojieli-phd-thesis.txt)（user_provided） | 李博杰博士论文，2019-05-26；ClickNP 核数预算、KV-Direct PCIe 并发与数据通路；论文测量按原配置引用 |
| [Huawei’s τ Chip Was Supposed to Melt?](files/papers/202609.00031v1.pdf) | [原件](files/papers/202609.00031v1.pdf) · [文本](text/logicfolding-energy.txt)（user_provided） | 何庭波，ChinaXiv:202609.00031v1，2026-09-04；片上连线、降压与功率密度；作者报告，AI 集群 80% 能耗说法待独立取证 |

## 第 5 章 算子与运行时

| 资料 | 本地文件 | 用途 |
| --- | --- | --- |
| [FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](https://arxiv.org/abs/2205.14135) | [原件](files/papers/flashattention.pdf) · [文本](text/flashattention.txt) | 分块、融合与 HBM 访问 |
| [FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning](https://arxiv.org/abs/2307.08691) | [原件](files/papers/flashattention2.pdf) · [文本](text/flashattention2.txt) | 工作划分 |
| [FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-precision](https://arxiv.org/abs/2407.08608) | [原件](files/papers/flashattention3.pdf) · [文本](text/flashattention3.txt) | 异步执行与精度 |
| [AKG: Automatic Kernel Generation for Neural Processing Units using Polyhedral Transformations](https://01.me/projects/AKG/) | [原件](files/papers/akg-pldi21.pdf) · [文本](text/akg-pldi21.txt) | 作者托管；PLDI 2021 |
| [TVM: An Automated End-to-End Optimizing Compiler for Deep Learning](https://arxiv.org/abs/1802.04799) | [原件](files/papers/tvm.pdf) · [文本](text/tvm.txt) | 编译与调度 |
| [TensorIR: An Abstraction for Automatic Tensorized Program Optimization](https://arxiv.org/abs/2207.04296) | [原件](files/papers/tensorir.pdf) · [文本](text/tensorir.txt) | 张量程序表示 |
| [Presburger Formulas and Polyhedral Compilation](https://libisl.sourceforge.io/) | [原件](files/documents/isl-tutorial.pdf) · [文本](text/isl-tutorial.txt) | 整数集合、访问与依赖 |
| [Integer Set Library Manual](https://libisl.sourceforge.io/) | [原件](files/documents/isl-manual.html) · [文本](text/isl-manual.txt) | 以网页快照记录版本 |
| [Apache TVM Design and Architecture](https://tvm.apache.org/docs/arch/index.html) | [原件](files/documents/tvm-architecture.html) · [文本](text/tvm-architecture.txt) | 现代 TVM 分层；与 2018 年论文区分 |
| [NVIDIA Blackwell Tuning Guide](https://docs.nvidia.com/cuda/blackwell-tuning-guide/) | [原件](files/specs/nvidia-blackwell-guide.html) · [文本](text/nvidia-blackwell-guide.txt) | 官方微架构与编程依据 |
| [CANN 8.1.RC1.alpha002 Ascend C 算子开发指南](https://www.hiascend.com/) | [原件](files/specs/ascend-c-guide.pdf) · [文本](text/ascend-c-guide.txt) | 公开编程与硬件架构文档 |
| [CANN 9.0.0 Ascend C 硬件架构](https://www.hiascend.com/) | [原件](files/specs/ascend-c-architecture.html) · [文本](text/ascend-c-architecture.txt)（incomplete_text） | 若为动态页面，仅在获取到正文时记为全文 |
| [MLX official README](https://github.com/ml-explore/mlx) | [原件](files/documents/mlx.md) · [文本](text/mlx.txt) | Apple Silicon 软件栈 |
| [llama.cpp official README](https://github.com/ggml-org/llama.cpp) | [原件](files/documents/llama-cpp.md) · [文本](text/llama-cpp.txt) | 本地运行时与后端 |
| [Unsloth official README](https://github.com/unslothai/unsloth) | [原件](files/documents/unsloth.md) · [文本](text/unsloth.txt) | 本地训练、运行、量化与导出 |
| [Ollama Development and Compute Backends](https://docs.ollama.com/development) | [原件](files/documents/ollama.html) · [文本](text/ollama.txt) | Metal 与当前后端能力 |
| [OpenTallas architecture and analysis](https://github.com/bojieli/OpenTallas/tree/39b96158d35b24bd2bcd49061a689aea6893d2ed) | [原件](files/documents/opentallas-readme.md) · [文本](text/opentallas-readme.txt)（local_snapshot） | 与本书已有案例使用相同提交 |
| [GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers](https://arxiv.org/abs/2210.17323) | [原件](files/papers/gptq.pdf) · [文本](text/gptq.txt) | 权重量化 |
| [AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration](https://arxiv.org/abs/2306.00978) | [原件](files/papers/awq.pdf) · [文本](text/awq.txt) | 量化与设备效率 |
| [SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models](https://arxiv.org/abs/2211.10438) | [原件](files/papers/smoothquant.pdf) · [文本](text/smoothquant.txt) | 激活量化 |
| [The Llama 3 Herd of Models](https://arxiv.org/abs/2407.21783) | [原件](files/papers/llama3.pdf) · [文本](text/llama3.txt) | 架构与训练报告 |
| [昇腾 950 NPU 架构白皮书](files/specs/昇腾950%20NPU架构白皮书.pdf) | [原件](files/specs/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf) · [文本](text/ascend-950-whitepaper.txt)（user_provided） | 作者提供，40 页；保留原文件；另存官方 OBS 文件 ascend-950-official，两份文件差异核对见 UB-ASCEND-NOTES.md |
| [Serving Large Language Models on Huawei CloudMatrix384, v2](https://arxiv.org/abs/2506.12708v2) | [原件](files/papers/cloudmatrix384-v2.pdf) · [文本](text/cloudmatrix384-v2.txt) | 2025-06-18；§3.3.1 的 910C、§4.2.2 MLA 与动态 tiling；与 v3 分开保存 |
| [Serving Large Language Models on Huawei CloudMatrix384, v3](https://arxiv.org/abs/2506.12708v3) | [原件](files/papers/cloudmatrix384-v3.pdf) · [文本](text/cloudmatrix384-v3.txt) | 2025-06-19 修订；核对型号称谓与 v2 差异 |
| [NVIDIA Hopper Tuning Guide](https://docs.nvidia.com/cuda/hopper-tuning-guide/index.html) | [原件](files/documents/nvidia-hopper-tuning.html) · [文本](text/nvidia-hopper-tuning.txt) | SM、Tensor Core、TMA 与 shared memory；固定网页快照 |
| [CUDA Programming Guide 13.2.1: Asynchronous Data Copies](https://docs.nvidia.com/cuda/archive/13.2.1/cuda-programming-guide/04-special-topics/async-copies.html) | [原件](files/documents/nvidia-async-copies.html) · [文本](text/nvidia-async-copies.txt) | 显式异步搬运、tensor map、stride、对齐与同步；与 NDDMA 比较 |
| [CUDA Graph Best Practice for PyTorch: CUDA Graph](https://docs.nvidia.com/dl-cuda-graph/cuda-graph-basics/cuda-graph.html) | [原件](files/documents/cuda-graphs.html) · [文本](text/cuda-graphs.txt) | 定义、实例化与执行；区分主机提交和设备启动成本 |
| [vLLM CUDA Graphs Design](https://docs.vllm.ai/en/latest/design/cuda_graphs/) | [原件](files/documents/vllm-cuda-graphs.html) · [文本](text/vllm-cuda-graphs.txt) | 整图与分段图、批次调度、捕获时间与内存成本；固定网页快照 |
| [Triton Programming Guide: Introduction](https://triton-lang.org/main/programming-guide/chapter-1/introduction.html) | [原件](files/documents/triton-introduction.html) · [文本](text/triton-introduction.txt) | 块级编程与编译器管理布局、共享存储和异步搬运；软件与硬件分层 |
| [Triton Tutorial: Matrix Multiplication](https://triton-lang.org/main/getting-started/tutorials/03-matrix-multiplication.html) | [原件](files/documents/triton-matmul.html) · [文本](text/triton-matmul.txt) | 运行时尺寸、stride、边界 mask、分块与调优；动态 shape 案例 |
| [昇腾 950 NPU 架构白皮书（官方下载原件）](https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf) | [原件](files/specs/ascend-950-official.pdf) · [文本](text/ascend-950-official.txt) | 作者提供官方 OBS 下载地址；与先前作者提供版本分别保留，差异核对见 UB-ASCEND-NOTES.md |
| [Choosing a resource storage mode for Apple GPUs — DocC JSON](https://developer.apple.com/tutorials/data/documentation/metal/choosing-a-resource-storage-mode-for-apple-gpus.json) | [原件](files/documents/apple-metal-memory.json) · [文本](text/apple-metal-memory.txt) | 官方文档数据原件；shared／private、访问和同步；非芯片完整微架构 |
| [Explore the architecture of Apple GPUs — WWDC20](https://developer.apple.com/videos/play/wwdc2020/10602/) | [原件](files/documents/apple-gpu-architecture.html) · [文本](text/apple-gpu-architecture.txt) | Apple GPU 执行与存储模型；2020 年架构说明不证明 M2 未公开单元参数 |
| [NVIDIA RTX Blackwell PRO GPU Architecture v1.0](https://www.nvidia.com/content/dam/en-zz/Solutions/design-visualization/quadro-product-literature/NVIDIA-RTX-Blackwell-PRO-GPU-Architecture-v1.0.pdf) | [原件](files/specs/nvidia-rtx-blackwell-pro.pdf) · [文本](text/nvidia-rtx-blackwell-pro.txt) | RTX Blackwell 的 SM、Tensor Core 与 GDDR7；与 B200 数据中心 Blackwell 分开分析 |
| [Ollama Hardware support](https://docs.ollama.com/gpu) | [原件](files/documents/ollama-hardware.html) · [文本](text/ollama-hardware.txt) | Apple GPU 经 Metal；RTX PRO 6000 Blackwell compute capability 12.0；网页按获取日固定 |
| [Ollama Generate API](https://docs.ollama.com/api/generate.md) | [原件](files/documents/ollama-api-generate.md) · [文本](text/ollama-api-generate.txt) | API 耗时为纳秒；prefill／decode 统计不能直接替代客户端流式 TTFT／ITL |
| [Ollama v0.20.7 Apple device and working-set discovery](https://raw.githubusercontent.com/ollama/ollama/8d0dcf4b6daf8d7833c8b55108e5b45063795e57/discover/gpu_info_darwin.m) | [原件](files/documents/ollama-metal-device.txt) · [文本](text/ollama-metal-device.txt) | 固定提交 8d0dcf4b6daf8d7833c8b55108e5b45063795e57；仅为设备识别，内核来源另计 |
| [KT-Kernel inference README — fixed revision](https://raw.githubusercontent.com/kvcache-ai/ktransformers/31985f40bcc40da08107efdb1f81bf88cb38c6b2/kt-kernel/README.md) | [原件](files/documents/kt-kernel-guide.md) · [文本](text/kt-kernel-guide.txt) | 固定提交 31985f40bcc40da08107efdb1f81bf88cb38c6b2；AF 主案例采用 RTX 4090＋双路 Xeon Gold 6454S 示例 |
| [KTransformers 0.3 AMX design notes](https://raw.githubusercontent.com/kvcache-ai/ktransformers/31985f40bcc40da08107efdb1f81bf88cb38c6b2/doc/en/AMX.md) | [原件](files/documents/kt-amx.md) · [文本](text/kt-amx.txt) | 2025 年 v0.3 历史设计；Intel AMX、AVX-512、权重重排与调度；性能按原配置引用 |
| [KTransformers: Unleashing the Full Potential of CPU/GPU Hybrid Inference for MoE Models](https://madsys.cs.tsinghua.edu.cn/publication/ktransformers-unleashing-the-full-potential-of-cpu/gpu-hybrid-inference-for-moe-models/SOSP25-chen.pdf) | [原件](files/papers/ktransformers-paper.pdf) · [文本](text/ktransformers-paper.txt) | SOSP 2025 作者原件；双 Xeon Platinum 8452Y＋A100 40GB／RTX 4080 16GB；与主案例配置分别引用 |
| [Ollama v0.20.7 bundled ggml Metal device and buffers](https://raw.githubusercontent.com/ollama/ollama/8d0dcf4b6daf8d7833c8b55108e5b45063795e57/ml/backend/ggml/ggml/src/ggml-metal/ggml-metal-device.m) | [原件](files/documents/ollama-ggml-metal-memory.txt) · [文本](text/ollama-ggml-metal-memory.txt) | 固定提交；hasUnifiedMemory、shared／bytesNoCopy、工作集；保留 upstream 署名 |
| [Ollama v0.20.7 bundled ggml Metal kernels](https://raw.githubusercontent.com/ollama/ollama/8d0dcf4b6daf8d7833c8b55108e5b45063795e57/ml/backend/ggml/ggml/src/ggml-metal/ggml-metal.metal) | [原件](files/documents/ollama-ggml-metal-kernels.txt) · [文本](text/ollama-ggml-metal-kernels.txt) | 固定提交；量化解码、矩阵／向量计算、simdgroup；实际分派仍需运行日志确认 |
| [KT-Kernel CMake ARM KML build path](https://raw.githubusercontent.com/kvcache-ai/ktransformers/31985f40bcc40da08107efdb1f81bf88cb38c6b2/kt-kernel/CMakeLists.txt) | [原件](files/documents/kt-kml-build.txt) · [文本](text/kt-kml-build.txt) | 固定提交；KML 构建分支的背景归档，不作为当前 Xeon AF 案例的实现依据 |
| [KT-Kernel KML MoE correctness example](https://raw.githubusercontent.com/kvcache-ai/ktransformers/31985f40bcc40da08107efdb1f81bf88cb38c6b2/kt-kernel/examples/test_moe_kml.py) | [原件](files/documents/kt-kml-example.txt) · [文本](text/kt-kml-example.txt) | 固定提交；KML MoE 样例的背景归档，不作为当前 Xeon AF 案例的实现依据 |
| [DeepSpeed Inference: Enabling Efficient Inference of Transformer Models at Unprecedented Scale](https://arxiv.org/abs/2207.00032v1) | [原件](files/papers/deepspeed-inference.pdf) · [文本](text/deepspeed-inference.txt) | Microsoft／DeepSpeed；内核、模型并行及 CPU／NVMe 异构推理的联合设计 |
| [FlashInfer: Efficient and Customizable Attention Engine for LLM Inference Serving](https://arxiv.org/abs/2501.01005v2) | [原件](files/papers/flashinfer.pdf) · [文本](text/flashinfer.txt) | 开源注意力引擎；KV 布局、负载均衡调度、JIT 与 CUDA Graph 兼容 |
| [KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache](https://arxiv.org/abs/2402.02750v2) | [原件](files/papers/kivi.pdf) · [文本](text/kivi.txt) | KV 的 K/V 非对称量化；计入 scale、zero point、残余缓存与反量化成本 |
| [LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale](https://arxiv.org/abs/2208.07339v2) | [原件](files/papers/llm-int8.pdf) · [文本](text/llm-int8.txt) | 大模型激活异常值与混合精度分解；低比特存储不等于端到端加速 |
| [TensorRT LLM Architecture Overview](https://nvidia.github.io/TensorRT-LLM/developer-guide/overview.html) | [原件](files/documents/tensorrt-llm-architecture.html) · [文本](text/tensorrt-llm-architecture.txt) | 官方架构文档快照；作为开源项目实现资料，不标为学术论文 |
| [基于可编程网卡的高性能数据中心系统](https://01.me/files/pubs/bojieli-phd-thesis.pdf) | [原件](files/papers/bojieli-phd-thesis.pdf) · [文本](text/bojieli-phd-thesis.txt)（user_provided） | 李博杰博士论文，2019-05-26；ClickNP 核数预算、KV-Direct PCIe 并发与数据通路；论文测量按原配置引用 |

## 第 6 章 超节点

| 资料 | 本地文件 | 用途 |
| --- | --- | --- |
| [TPU v4: An Optically Reconfigurable Supercomputer for Machine Learning with Hardware Support for Embeddings](https://arxiv.org/abs/2304.01433) | [原件](files/papers/tpu-v4.pdf) · [文本](text/tpu-v4.txt) | 芯片与互联协同 |
| [NVIDIA H100 Tensor Core GPU Architecture](https://resources.nvidia.com/en-us-hopper-architecture/nvidia-h100-tensor-c) | [原件](files/specs/nvidia-h100.pdf) · [文本](text/nvidia-h100.txt) | 下载地址由 NVIDIA 官方阅读页直接提供 |
| [NVIDIA DGX B200 Specifications](https://www.nvidia.com/en-us/data-center/dgx-b200/) | [原件](files/specs/nvidia-dgx-b200.html) · [文本](text/nvidia-dgx-b200.txt) | 系统规格不能替代单芯片规格 |
| [NVIDIA GB200 NVL72](https://www.nvidia.com/en-us/data-center/gb200-nvl72/) | [原件](files/specs/nvidia-gb200.html) · [文本](text/nvidia-gb200.txt) | 整柜与 NVLink 域 |
| [Huawei Atlas 900 and ResNet-50 announcement, 2019](https://www.huawei.com/kr/news/2019/9/huawei-computing-strategy-atlas-900-ai-training-cluster) | [原件](files/documents/ascend-910-launch.html) · [文本](text/ascend-910-launch.txt) | 历史负载；非 910C 微架构规格 |
| [昇腾 950 与 Unified Bus 公开路线图](https://www.huawei.com/cn/news/2025/9/hc-xu-keynote-speech) | [原件](files/specs/ascend-950-roadmap.html) · [文本](text/ascend-950-roadmap.txt) | 按型号区分计划与交付状态 |
| [Huawei SuperPoD Portfolio at MWC Barcelona 2026](https://www.huawei.com/en/news/2026/3/mwc-superpod-computing) | [原件](files/documents/ascend-950-mwc.html) · [文本](text/ascend-950-mwc.txt) | Atlas 950 至多 8192 NPU 的官方公告 |
| [NCCL User Guide](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/overview.html) | [原件](files/documents/nccl-guide.html) · [文本](text/nccl-guide.txt) | 域内与域间通信 |
| [NCCL Collective Operations](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/usage/collectives.html) | [原件](files/documents/nccl-collectives.html) · [文本](text/nccl-collectives.txt) | 集合通信语义 |
| [Unified Bus 背后的思考](https://01.me/2025/09/a-story-of-unified-bus/) | [原件](files/documents/ub-reflection.html) · [文本](text/ub-reflection.txt) | 作者综述；非协议规范 |
| [Unified Bus Base Specification 2.0 Preview 官方入口](https://www.unifiedbus.com/en/docs/UB-Base-Specification-2.0-preview-en) | [原件](files/specs/ub-spec-entry.html) · [文本](text/ub-spec-entry.txt)（landing_only） | 入口不等于规范全文；2.0.1 另核 |
| [OpenURMA: A Clean-Room Open Implementation of the Unified Bus Protocol](https://arxiv.org/abs/2605.28717) | [原件](files/papers/openurma.pdf) · [文本](text/openurma.txt) | 实现范围、模拟与综合证据 |
| [OpenURMA official README](https://github.com/bojieli/OpenURMA) | [原件](files/documents/openurma-readme.md) · [文本](text/openurma-readme.txt) | 与本地项目版本分别固定 |
| [Introducing UALink 200G 1.0 Specification](https://ualinkconsortium.org/specification/) | [原件](files/specs/ualink-whitepaper.pdf) · [文本](text/ualink-whitepaper.txt) | 官方技术介绍；非完整规范 |
| [UALink Common 2.0 Specification 官方入口](https://ualinkconsortium.org/specification/) | [原件](files/specs/ualink-spec-entry.html) · [文本](text/ualink-spec-entry.txt)（landing_only） | 完整规范的获取状态单列 |
| [计算机网络的新黄金时代（一）](https://01.me/2023/05/new-golden-age-for-network-1/) | [原件](files/documents/network-golden-1.html) · [文本](text/network-golden-1.txt) | 作者素材；数据中心 |
| [NVIDIA Blackwell Architecture Technical Brief](https://resources.nvidia.com/en-us-blackwell-architecture) | [原件](files/specs/nvidia-blackwell-brief.pdf) · [文本](text/nvidia-blackwell-brief.txt) | 官方入口直接提供的 PDF |
| [Unified Bus Base Specification 2.0 Preview](https://www.unifiedbus.com/en/docs/UB-Base-Specification-2.0-preview-en) | [原件](files/specs/ub-base-preview.pdf) · [文本](text/ub-base-preview.txt) | 官网公开预览版；与 2.0.1 正式版区分 |
| [Unified Bus Software Reference Design for Operating Systems 2.0](https://www.unifiedbus.com/en/software) | [原件](files/specs/ub-os-reference.pdf) · [文本](text/ub-os-reference.txt) | 官网公开操作系统参考设计 |
| [Unified Bus Root Table Specification 1.0](https://www.unifiedbus.com/) | [原件](files/specs/ub-root-table.pdf) · [文本](text/ub-root-table.txt) | 独立规范；不替代 Base Specification |
| [OpenTallas architecture and analysis](https://github.com/bojieli/OpenTallas/tree/39b96158d35b24bd2bcd49061a689aea6893d2ed) | [原件](files/documents/opentallas-readme.md) · [文本](text/opentallas-readme.txt)（local_snapshot） | 与本书已有案例使用相同提交 |
| [Optimization of Collective Communication Operations in MPICH](https://web.cels.anl.gov/~thakur/papers/papers.html) | [原件](files/papers/collective-algorithms.pdf) · [文本](text/collective-algorithms.txt) | 环、树与消息规模 |
| [UALink Common Specification 2.0, Evaluation Copy](https://ualinkconsortium.org/specification/ualink-common-2-0-specification/) | [原件](files/specs/ualink-common.pdf) · [文本](text/ualink-common.txt) | 官方公开文件目录提供的评估版；保留原版使用条款 |
| [UALink 200G Data Link and Physical Layers 2.0, Evaluation Copy](https://ualinkconsortium.org/specification/ualink-data-link-and-physical-layers-2-0-specification/) | [原件](files/specs/ualink-link.pdf) · [文本](text/ualink-link.txt) | 链路与物理层；评估版 |
| [Unified Bus Base Specification 2.0.1（英文获取入口）](https://www.unifiedbus.com/en/docs/UB-Base-Specification-2.0.1-en-clean) | 未获取（access_required） | 英文版未取得；作者已提供 545 页中文 2.0.1 正式版，见 ub-base-201-zh |
| [The Cerebras Wafer-Scale Architecture for Deep Learning](https://www.cerebras.ai/chip) | [原件](files/specs/cerebras-wse3.pdf) · [文本](text/cerebras-wse3.txt) | 13 页架构白皮书，正文介绍 WSE-3；官网 Datasheet 链接名称与正文标题不同，以正文为准 |
| [SambaNova SambaRack SN40L-16 Datasheet](https://sambanova.ai/) | [原件](files/specs/sambanova-sambarack.pdf) · [文本](text/sambanova-sambarack.txt) | 按 PDF 正文核对产品代际，不从下载文件名推断日期 |
| [A Software-defined Tensor Streaming Multiprocessor for Large-scale Machine Learning](https://groq.com/papers/) | [原件](files/papers/groq-scale.pdf) · [文本](text/groq-scale.txt) | ISCA 2022；多芯片协同 |
| [Cerebras Wafer-Scale Engine 3 Datasheet](https://training-docs.cerebras.ai/rel-2.4.0/concepts/cerebras-wafer-scale-cluster) | [原件](files/specs/cerebras-wse3-spec.pdf) · [文本](text/cerebras-wse3-spec.txt) | 由官方开发文档直接链接；与 WSE-3T 区分 |
| [Cerebras CS-4 Datasheet](https://investors.cerebras.ai/news-releases/news-release-details/cerebras-unveils-cs-4-30-times-faster-gpu-based-solutions) | [原件](files/specs/cerebras-cs4-spec.pdf) · [文本](text/cerebras-cs4-spec.txt) | 2026 年公开新代际；保留产品声明和交付时间边界 |
| [灵衢基础规范 2.0.1（中文版）](https://www.unifiedbus.com/zh/docs/UB-Base-Specification-2.0.1-zh-clean) | [原件](files/specs/UB-Base-Specification-2.0.1-zh-clean.pdf) · [文本](text/ub-base-201-zh.txt)（user_provided） | 作者提供；2026 年 4 月，545 页；协议语义、顺序、完成、地址和管理 |
| [灵衢使能操作系统参考设计 2.0（中文版）](https://www.unifiedbus.com/zh/docs/UB-Software-Reference-Design-for-OS-2.0-zh) | [原件](files/specs/UB-Software-Reference-Design-for-OS-2.0-zh.pdf) · [文本](text/ub-os-zh.txt)（user_provided） | 作者提供；2025 年 9 月，57 页；设备、内存、通信、虚拟化与 RAS；引用 Base 2.0 |
| [昇腾 950 NPU 架构白皮书](files/specs/昇腾950%20NPU架构白皮书.pdf) | [原件](files/specs/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf) · [文本](text/ascend-950-whitepaper.txt)（user_provided） | 作者提供，40 页；保留原文件；另存官方 OBS 文件 ascend-950-official，两份文件差异核对见 UB-ASCEND-NOTES.md |
| [Google Cloud TPU v4 官方规格](https://docs.cloud.google.com/tpu/docs/v4) | [原件](files/specs/google-v4.html) · [文本](text/google-v4.txt) | 芯片、HBM、ICI 与 Pod 配置；云资源参数与硬件能力分别引用 |
| [Google Cloud TPU v5e 官方规格](https://docs.cloud.google.com/tpu/docs/v5e) | [原件](files/specs/google-v5e.html) · [文本](text/google-v5e.txt) | 芯片、HBM、ICI 与 Pod 配置；云资源参数与硬件能力分别引用 |
| [Google Cloud TPU v5p 官方规格](https://docs.cloud.google.com/tpu/docs/v5p) | [原件](files/specs/google-v5p.html) · [文本](text/google-v5p.txt) | 芯片、HBM、ICI 与 Pod 配置；云资源参数与硬件能力分别引用 |
| [Google Cloud TPU v6e 官方规格](https://docs.cloud.google.com/tpu/docs/v6e) | [原件](files/specs/google-v6e.html) · [文本](text/google-v6e.txt) | 芯片、HBM、ICI 与 Pod 配置；云资源参数与硬件能力分别引用 |
| [Google Cloud TPU tpu7x 官方规格](https://docs.cloud.google.com/tpu/docs/tpu7x) | [原件](files/specs/google-tpu7x.html) · [文本](text/google-tpu7x.txt) | 芯片、HBM、ICI 与 Pod 配置；云资源参数与硬件能力分别引用 |
| [Google Cloud TPU System Architecture](https://docs.cloud.google.com/tpu/docs/system-architecture-tpu-vm) | [原件](files/documents/google-tpu-architecture.html) · [文本](text/google-tpu-architecture.txt) | TensorCore、MXU、向量与存储组织 |
| [Google Cloud TPU Machine Specifications](https://docs.cloud.google.com/compute/docs/tpus/tpu-machines) | [原件](files/specs/google-tpu-machines.html) · [文本](text/google-tpu-machines.txt) | 主机 VM、芯片、ICI 和 DCN 的口径区别 |
| [Inside the Eighth-Generation TPU: An Architecture Deep Dive](https://cloud.google.com/blog/products/compute/tpu-8t-and-tpu-8i-technical-deep-dive) | [原件](files/specs/google-tpu8.html) · [文本](text/google-tpu8.txt) | 2026-04-22 官方技术说明及规格表；不等同于完整 ISA 或正式云实例规格 |
| [Google's Training Supercomputers from TPU v2 to Ironwood: Architectural Stability, Scale, Resilience, Power Efficiency, and Sustainability Across Five Generations](https://arxiv.org/abs/2606.15870) | [原件](files/papers/google-tpu-generations.pdf) · [文本](text/google-tpu-generations.txt) | Google 作者跨代架构论文；与云文档日期分别登记 |
| [The Data Center Architecture for Graphcore Computing](https://www.graphcore.ai/hubfs/Graphcore-Mk2-IPU-System-Architecture-GC.pdf) | [原件](files/specs/graphcore-mk2.pdf) · [文本](text/graphcore-mk2.txt) | 官方系统白皮书；芯片、Streaming Memory 与主机解耦 |
| [IPU-Machine M2000 Datasheet 1.0.0](https://docs.graphcore.ai/projects/graphcore-ipu-m2000-datasheet/en/1.0.0/) | [原件](files/specs/graphcore-m2000-pdf.pdf) · [文本](text/graphcore-m2000-pdf.txt) | 历史版本的整机规格，4 个 IPU 的参数不当作单芯片 |
| [IPU-M2000 Product Description and Technical Specifications](https://docs.graphcore.ai/projects/graphcore-ipu-m2000-datasheet/en/latest/product-description.html) | [原件](files/specs/graphcore-m2000.html) · [文本](text/graphcore-m2000.txt) | 官方完整产品规格章节快照；latest URL 不代表当前仍在销售 |
| [Bow-2000 Product Description and Technical Specifications](https://docs.graphcore.ai/projects/bow-2000-datasheet/en/latest/product-description.html) | [原件](files/specs/graphcore-bow2000.html) · [文本](text/graphcore-bow2000.txt) | 官方完整产品规格章节快照；latest URL 不代表当前仍在销售 |
| [IPU Hardware Overview](https://docs.graphcore.ai/projects/ipu-programmers-guide/en/latest/about_ipu.html) | [原件](files/documents/graphcore-hardware.html) · [文本](text/graphcore-hardware.txt) | 官方程序员指南的指定完整章节；非整套指南全文 |
| [IPU Programming Model](https://docs.graphcore.ai/projects/ipu-programmers-guide/en/latest/programming_model.html) | [原件](files/documents/graphcore-programming.html) · [文本](text/graphcore-programming.txt) | 官方程序员指南的指定完整章节；非整套指南全文 |
| [Graphcore Bow Pod16 Product Brief](https://www.graphcore.ai/hubfs/assets/pdf/Product%20Brief%20Bow%20Pod16%20020322.pdf) | [原件](files/specs/graphcore-bowpod16.pdf) · [文本](text/graphcore-bowpod16.txt) | Pod 系统规格；保留主机与交换机是否计入的边界 |
| [Dissecting the Graphcore IPU Architecture via Microbenchmarking](https://arxiv.org/abs/1912.03413) | [原件](files/papers/graphcore-microbench.pdf) · [文本](text/graphcore-microbench.txt) | 原始测量论文；第一代 IPU 的结果不移植为 GC200 或 Bow 实测 |
| [SambaNova SN40L: Scaling the AI Memory Wall with Dataflow and Composition of Experts](https://arxiv.org/abs/2405.07518) | [原件](files/papers/sambanova-sn40l-paper.pdf) · [文本](text/sambanova-sn40l-paper.txt) | 厂商原始架构论文；三级存储、融合与多模型切换，非两页宣传材料 |
| [Introducing AMD CDNA 3 Architecture](https://www.amd.com/en/technologies/cdna.html) | [原件](files/specs/amd-cdna3.pdf) · [文本](text/amd-cdna3.txt) | 架构白皮书；MI300A 与 MI300X 的芯粒和内存组织分开 |
| [Introducing AMD CDNA 4 Architecture](https://www.amd.com/en/technologies/cdna.html) | [原件](files/specs/amd-cdna4.pdf) · [文本](text/amd-cdna4.txt) | 架构白皮书；精度、分块、存储与通信 |
| [AMD Instinct MI300X Platform Datasheet](https://www.amd.com/en/products/accelerators/instinct/mi300/mi300x.html) | [原件](files/specs/amd-mi300x-platform.pdf) · [文本](text/amd-mi300x-platform.txt) | 8 GPU 平台；与单 OAM 规格区分 |
| [AMD Instinct MI350X Platform Datasheet](https://www.amd.com/en/products/accelerators/instinct/mi350/mi350x.html) | [原件](files/specs/amd-mi350x-platform.pdf) · [文本](text/amd-mi350x-platform.txt) | 8 GPU 平台、互联、容量与系统功率 |
| [Intel Gaudi 3 AI Accelerator White Paper](https://www.intel.com/content/www/us/en/content-details/817486/intel-gaudi-3-ai-accelerator-white-paper.html) | [原件](files/specs/intel-gaudi3.pdf) · [文本](text/intel-gaudi3.txt) | July 2025 V1 Rev.3；矩阵、可编程核、HBM 与以太互联 |
| [寒武纪思元 370 系列官方产品规格](https://cambricon.com/index.php?a=lists&c=index&catid=360&m=content) | [原件](files/specs/cambricon-mlu370.html) · [文本](text/cambricon-mlu370.txt) | 官方产品页；不能代替完整 ISA、微架构或后续代际规格 |
| [AWS Trainium2 Architecture](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/about-neuron/arch/neuron-hardware/trainium2.html) | [原件](files/specs/aws-trainium2.html) · [文本](text/aws-trainium2.txt) | 芯片规格；与 NKI 指南中 CC-Core 计数的口径差异单列 |
| [AWS Trainium3 Architecture](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/about-neuron/arch/neuron-hardware/trainium3.html) | [原件](files/specs/aws-trainium3.html) · [文本](text/aws-trainium3.txt) | 单芯片 NeuronCore、内存、DMA 与 NeuronLink 规格 |
| [Amazon EC2 Trn2 Architecture](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/about-neuron/arch/neuron-hardware/trn2-arch.html) | [原件](files/specs/aws-trn2-system.html) · [文本](text/aws-trn2-system.txt) | 实例、UltraServer、NeuronLink 拓扑和 EFA |
| [Amazon EC2 Trn3 UltraServers](https://aws.amazon.com/ec2/instance-types/trn3/) | [原件](files/specs/aws-trn3-system.html) · [文本](text/aws-trn3-system.txt) | 系统规格；整机 HBM、芯片数与单设备参数分开 |
| [Hot Chips 2026: SN50 RDU Dataflow at Scale](https://sambanova.ai/blog/hot-chips-2026-dataflow-at-scale) | [原件](files/documents/sambanova-sn50.html) · [文本](text/sambanova-sn50.txt) | 2026-09-02 厂商技术说明；模型推演与测量结果分别标注 |
| [SambaRack SN50 Official Product Description](https://sambanova.ai/products/sambarack) | [原件](files/specs/sambanova-sn50-system.html) · [文本](text/sambanova-sn50-system.txt) | 系统产品介绍，非完整 ISA 或全部产品参数手册 |
| [Inside NVIDIA Rubin GPU Architecture](https://developer.nvidia.com/blog/inside-nvidia-rubin-gpu-architecture-powering-the-era-of-agentic-ai/) | [原件](files/documents/nvidia-rubin-arch.html) · [文本](text/nvidia-rubin-arch.txt) | 2026-07-21 官方技术说明；与早期发布规格分开记录 |
| [NVIDIA Vera Rubin NVL72 Specifications](https://www.nvidia.com/en-us/data-center/vera-rubin-nvl72/) | [原件](files/specs/nvidia-rubin-system.html) · [文本](text/nvidia-rubin-system.txt) | 当前官方产品规格；部署形态、精度和供货状态分开 |
| [NVIDIA NVLink and NVLink Switch Specifications](https://www.nvidia.com/en-us/data-center/nvlink/) | [原件](files/specs/nvidia-nvlink-spec.html) · [文本](text/nvidia-nvlink-spec.txt) | 公开接口规格与代际比较；不是完整私有协议或 ISA |
| [GroqRack Compute Cluster Product Brief v1.0](https://groq.com/papers/) | [原件](files/specs/groq-rack.pdf) · [文本](text/groq-rack.txt) | 官方整柜规格；历史 Groq 代际，与 NVIDIA Groq 3 LPX 分开 |
| [Serving Large Language Models on Huawei CloudMatrix384, v2](https://arxiv.org/abs/2506.12708v2) | [原件](files/papers/cloudmatrix384-v2.pdf) · [文本](text/cloudmatrix384-v2.txt) | 2025-06-18；§3.3.1 的 910C、§4.2.2 MLA 与动态 tiling；与 v3 分开保存 |
| [Serving Large Language Models on Huawei CloudMatrix384, v3](https://arxiv.org/abs/2506.12708v3) | [原件](files/papers/cloudmatrix384-v3.pdf) · [文本](text/cloudmatrix384-v3.txt) | 2025-06-19 修订；核对型号称谓与 v2 差异 |
| [昇腾 950 NPU 架构白皮书（官方下载原件）](https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf) | [原件](files/specs/ascend-950-official.pdf) · [文本](text/ascend-950-official.txt) | 作者提供官方 OBS 下载地址；与先前作者提供版本分别保留，差异核对见 UB-ASCEND-NOTES.md |
| [Insights into DeepSeek-V3: Scaling Challenges and Reflections on Hardware for AI Architectures](https://arxiv.org/abs/2505.09343v2) | [原件](files/papers/deepseek-infra.pdf) · [文本](text/deepseek-infra.txt) | DeepSeek ISCA 2025 报告；MLA／MoE、跨节点通信及硬件协同设计建议 |
| [Day 6: DeepSeek-V3/R1 Inference System Overview](https://github.com/deepseek-ai/open-infra-index/blob/56d86855fcf6e08fdfd45ce6280bd24322c93351/202502OpenSourceWeek/day_6_one_more_thing_deepseekV3R1_inference_system_overview.md) | [原件](files/documents/deepseek-serving-report.md) · [文本](text/deepseek-serving-report.txt) | 2025 公司工程报告；固定提交；PD、EP、通信与费用口径 |

## 第 7 章 数据中心网络

| 资料 | 本地文件 | 用途 |
| --- | --- | --- |
| [昇腾 950 与 Unified Bus 公开路线图](https://www.huawei.com/cn/news/2025/9/hc-xu-keynote-speech) | [原件](files/specs/ascend-950-roadmap.html) · [文本](text/ascend-950-roadmap.txt) | 按型号区分计划与交付状态 |
| [NCCL User Guide](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/overview.html) | [原件](files/documents/nccl-guide.html) · [文本](text/nccl-guide.txt) | 域内与域间通信 |
| [NCCL Collective Operations](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/usage/collectives.html) | [原件](files/documents/nccl-collectives.html) · [文本](text/nccl-collectives.txt) | 集合通信语义 |
| [Unified Bus 背后的思考](https://01.me/2025/09/a-story-of-unified-bus/) | [原件](files/documents/ub-reflection.html) · [文本](text/ub-reflection.txt) | 作者综述；非协议规范 |
| [Unified Bus Base Specification 2.0 Preview 官方入口](https://www.unifiedbus.com/en/docs/UB-Base-Specification-2.0-preview-en) | [原件](files/specs/ub-spec-entry.html) · [文本](text/ub-spec-entry.txt)（landing_only） | 入口不等于规范全文；2.0.1 另核 |
| [OpenURMA: A Clean-Room Open Implementation of the Unified Bus Protocol](https://arxiv.org/abs/2605.28717) | [原件](files/papers/openurma.pdf) · [文本](text/openurma.txt) | 实现范围、模拟与综合证据 |
| [OpenURMA official README](https://github.com/bojieli/OpenURMA) | [原件](files/documents/openurma-readme.md) · [文本](text/openurma-readme.txt) | 与本地项目版本分别固定 |
| [NVIDIA DOCA RDMA-Aware Networks Programming Guide](https://networking-docs.nvidia.com/doca/sdk/rdma-aware-networks-programming-guide) | [原件](files/documents/rdma-guide.html) · [文本](text/rdma-guide.txt) | 替代已弃用旧手册；非 IB 规范全文 |
| [Congestion Control for Large-Scale RDMA Deployments](https://conferences.sigcomm.org/sigcomm/2015/program.php) | [原件](files/papers/dcqcn.pdf) · [文本](text/dcqcn.txt) | SIGCOMM 2015；DCQCN |
| [TIMELY: RTT-based Congestion Control for the Datacenter](https://conferences.sigcomm.org/sigcomm/2015/program.php) | [原件](files/papers/timely.pdf) · [文本](text/timely.txt) | SIGCOMM 2015 |
| [RFC 9293: Transmission Control Protocol](https://www.rfc-editor.org/rfc/rfc9293) | [原件](files/standards/rfc9293.txt) · [文本](text/rfc9293.txt) | TCP |
| [计算机网络的新黄金时代（一）](https://01.me/2023/05/new-golden-age-for-network-1/) | [原件](files/documents/network-golden-1.html) · [文本](text/network-golden-1.txt) | 作者素材；数据中心 |
| [Unified Bus Base Specification 2.0 Preview](https://www.unifiedbus.com/en/docs/UB-Base-Specification-2.0-preview-en) | [原件](files/specs/ub-base-preview.pdf) · [文本](text/ub-base-preview.txt) | 官网公开预览版；与 2.0.1 正式版区分 |
| [Unified Bus Software Reference Design for Operating Systems 2.0](https://www.unifiedbus.com/en/software) | [原件](files/specs/ub-os-reference.pdf) · [文本](text/ub-os-reference.txt) | 官网公开操作系统参考设计 |
| [Unified Bus Root Table Specification 1.0](https://www.unifiedbus.com/) | [原件](files/specs/ub-root-table.pdf) · [文本](text/ub-root-table.txt) | 独立规范；不替代 Base Specification |
| [OpenTallas architecture and analysis](https://github.com/bojieli/OpenTallas/tree/39b96158d35b24bd2bcd49061a689aea6893d2ed) | [原件](files/documents/opentallas-readme.md) · [文本](text/opentallas-readme.txt)（local_snapshot） | 与本书已有案例使用相同提交 |
| [A Scalable, Commodity Data Center Network Architecture](https://cseweb.ucsd.edu/~vahdat/papers/sigcomm08.pdf) | [原件](files/papers/fat-tree.pdf) · [文本](text/fat-tree.txt) | 作者机构副本；SIGCOMM 2008 |
| [Optimization of Collective Communication Operations in MPICH](https://web.cels.anl.gov/~thakur/papers/papers.html) | [原件](files/papers/collective-algorithms.pdf) · [文本](text/collective-algorithms.txt) | 环、树与消息规模 |
| [Unified Bus Base Specification 2.0.1（英文获取入口）](https://www.unifiedbus.com/en/docs/UB-Base-Specification-2.0.1-en-clean) | 未获取（access_required） | 英文版未取得；作者已提供 545 页中文 2.0.1 正式版，见 ub-base-201-zh |
| [灵衢基础规范 2.0.1（中文版）](https://www.unifiedbus.com/zh/docs/UB-Base-Specification-2.0.1-zh-clean) | [原件](files/specs/UB-Base-Specification-2.0.1-zh-clean.pdf) · [文本](text/ub-base-201-zh.txt)（user_provided） | 作者提供；2026 年 4 月，545 页；协议语义、顺序、完成、地址和管理 |
| [灵衢使能操作系统参考设计 2.0（中文版）](https://www.unifiedbus.com/zh/docs/UB-Software-Reference-Design-for-OS-2.0-zh) | [原件](files/specs/UB-Software-Reference-Design-for-OS-2.0-zh.pdf) · [文本](text/ub-os-zh.txt)（user_provided） | 作者提供；2025 年 9 月，57 页；设备、内存、通信、虚拟化与 RAS；引用 Base 2.0 |
| [昇腾 950 NPU 架构白皮书](files/specs/昇腾950%20NPU架构白皮书.pdf) | [原件](files/specs/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf) · [文本](text/ascend-950-whitepaper.txt)（user_provided） | 作者提供，40 页；保留原文件；另存官方 OBS 文件 ascend-950-official，两份文件差异核对见 UB-ASCEND-NOTES.md |
| [Inside the Eighth-Generation TPU: An Architecture Deep Dive](https://cloud.google.com/blog/products/compute/tpu-8t-and-tpu-8i-technical-deep-dive) | [原件](files/specs/google-tpu8.html) · [文本](text/google-tpu8.txt) | 2026-04-22 官方技术说明及规格表；不等同于完整 ISA 或正式云实例规格 |
| [Intel Gaudi 3 AI Accelerator White Paper](https://www.intel.com/content/www/us/en/content-details/817486/intel-gaudi-3-ai-accelerator-white-paper.html) | [原件](files/specs/intel-gaudi3.pdf) · [文本](text/intel-gaudi3.txt) | July 2025 V1 Rev.3；矩阵、可编程核、HBM 与以太互联 |
| [Hot Chips 2026: SN50 RDU Dataflow at Scale](https://sambanova.ai/blog/hot-chips-2026-dataflow-at-scale) | [原件](files/documents/sambanova-sn50.html) · [文本](text/sambanova-sn50.txt) | 2026-09-02 厂商技术说明；模型推演与测量结果分别标注 |
| [昇腾 950 NPU 架构白皮书（官方下载原件）](https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf) | [原件](files/specs/ascend-950-official.pdf) · [文本](text/ascend-950-official.txt) | 作者提供官方 OBS 下载地址；与先前作者提供版本分别保留，差异核对见 UB-ASCEND-NOTES.md |
| [基于可编程网卡的高性能数据中心系统](https://01.me/files/pubs/bojieli-phd-thesis.pdf) | [原件](files/papers/bojieli-phd-thesis.pdf) · [文本](text/bojieli-phd-thesis.txt)（user_provided） | 李博杰博士论文，2019-05-26；ClickNP 核数预算、KV-Direct PCIe 并发与数据通路；论文测量按原配置引用 |

## 第 8 章 单实例推理

| 资料 | 本地文件 | 用途 |
| --- | --- | --- |
| [Fast Transformer Decoding: One Write-Head is All You Need](https://arxiv.org/abs/1911.02150) | [原件](files/papers/mqa.pdf) · [文本](text/mqa.txt) | MQA 与 KV 访问 |
| [GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints](https://arxiv.org/abs/2305.13245) | [原件](files/papers/gqa.pdf) · [文本](text/gqa.txt) | GQA |
| [DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model](https://arxiv.org/abs/2405.04434) | [原件](files/papers/deepseek-v2.pdf) · [文本](text/deepseek-v2.txt) | MLA |
| [Kimi Linear: An Expressive, Efficient Attention Architecture](https://arxiv.org/abs/2510.26692) | [原件](files/papers/kimi-linear.pdf) · [文本](text/kimi-linear.txt) | KDA 与分块实现 |
| [llama.cpp official README](https://github.com/ggml-org/llama.cpp) | [原件](files/documents/llama-cpp.md) · [文本](text/llama-cpp.txt) | 本地运行时与后端 |
| [Ollama Development and Compute Backends](https://docs.ollama.com/development) | [原件](files/documents/ollama.html) · [文本](text/ollama.txt) | Metal 与当前后端能力 |
| [Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180) | [原件](files/papers/vllm.pdf) · [文本](text/vllm.txt) | KV 与分页 |
| [Orca: A Distributed Serving System for Transformer-Based Generative Models](https://www.usenix.org/conference/osdi22/presentation/yu) | [原件](files/papers/orca.pdf) · [文本](text/orca.txt) | 迭代级调度 |
| [Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve](https://arxiv.org/abs/2403.02310) | [原件](files/papers/sarathi-serve.pdf) · [文本](text/sarathi-serve.txt) | 分块 prefill 与调度 |
| [SGLang: Efficient Execution of Structured Language Model Programs](https://arxiv.org/abs/2312.07104) | [原件](files/papers/sglang.pdf) · [文本](text/sglang.txt) | 前缀缓存与执行 |
| [Fast Inference from Transformers via Speculative Decoding](https://arxiv.org/abs/2211.17192) | [原件](files/papers/speculative-decoding.pdf) · [文本](text/speculative-decoding.txt) | 草稿与验证 |
| [FlexGen: High-Throughput Generative Inference of Large Language Models with a Single GPU](https://arxiv.org/abs/2303.06865) | [原件](files/papers/flexgen.pdf) · [文本](text/flexgen.txt) | 卸载与数据移动 |
| [OpenTallas architecture and analysis](https://github.com/bojieli/OpenTallas/tree/39b96158d35b24bd2bcd49061a689aea6893d2ed) | [原件](files/documents/opentallas-readme.md) · [文本](text/opentallas-readme.txt)（local_snapshot） | 与本书已有案例使用相同提交 |
| [GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers](https://arxiv.org/abs/2210.17323) | [原件](files/papers/gptq.pdf) · [文本](text/gptq.txt) | 权重量化 |
| [AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration](https://arxiv.org/abs/2306.00978) | [原件](files/papers/awq.pdf) · [文本](text/awq.txt) | 量化与设备效率 |
| [SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models](https://arxiv.org/abs/2211.10438) | [原件](files/papers/smoothquant.pdf) · [文本](text/smoothquant.txt) | 激活量化 |
| [Llama 2: Open Foundation and Fine-Tuned Chat Models](https://arxiv.org/abs/2307.09288) | [原件](files/papers/llama2.pdf) · [文本](text/llama2.txt) | 历史 70B 案例的配置来源 |
| [Taalas HC1 Technology Demonstrator](https://taalas.com/products/) | [原件](files/specs/taalas-hc1.html) · [文本](text/taalas-hc1.txt) | 厂商模型固化产品介绍；吞吐为厂商声明，须保留负载条件 |
| [SambaNova SN40L: Scaling the AI Memory Wall with Dataflow and Composition of Experts](https://arxiv.org/abs/2405.07518) | [原件](files/papers/sambanova-sn40l-paper.pdf) · [文本](text/sambanova-sn40l-paper.txt) | 厂商原始架构论文；三级存储、融合与多模型切换，非两页宣传材料 |
| [Serving Large Language Models on Huawei CloudMatrix384, v2](https://arxiv.org/abs/2506.12708v2) | [原件](files/papers/cloudmatrix384-v2.pdf) · [文本](text/cloudmatrix384-v2.txt) | 2025-06-18；§3.3.1 的 910C、§4.2.2 MLA 与动态 tiling；与 v3 分开保存 |
| [Serving Large Language Models on Huawei CloudMatrix384, v3](https://arxiv.org/abs/2506.12708v3) | [原件](files/papers/cloudmatrix384-v3.pdf) · [文本](text/cloudmatrix384-v3.txt) | 2025-06-19 修订；核对型号称谓与 v2 差异 |
| [CUDA Graph Best Practice for PyTorch: CUDA Graph](https://docs.nvidia.com/dl-cuda-graph/cuda-graph-basics/cuda-graph.html) | [原件](files/documents/cuda-graphs.html) · [文本](text/cuda-graphs.txt) | 定义、实例化与执行；区分主机提交和设备启动成本 |
| [vLLM CUDA Graphs Design](https://docs.vllm.ai/en/latest/design/cuda_graphs/) | [原件](files/documents/vllm-cuda-graphs.html) · [文本](text/vllm-cuda-graphs.txt) | 整图与分段图、批次调度、捕获时间与内存成本；固定网页快照 |
| [Apple M2 Pro and M2 Max launch specifications](https://www.apple.com/newsroom/2023/01/apple-unveils-m2-pro-and-m2-max-next-generation-chips-for-next-level-workflows/) | [原件](files/specs/apple-m2-pro-max.html) · [文本](text/apple-m2-pro-max.txt) | 2023-01-17；M2 Pro 200 GB/s，M2 Max 400 GB/s；本书实机为 M2 Max 38 核 GPU、96 GB |
| [RTX PRO 6000 Blackwell Workstation Edition Datasheet](https://www.nvidia.com/content/dam/en-zz/Solutions/data-center/rtx-pro-6000-blackwell-workstation-edition/workstation-blackwell-rtx-pro-6000-workstation-edition-nvidia-us-3519208-web.pdf) | [原件](files/specs/nvidia-rtx-pro6000-spec.pdf) · [文本](text/nvidia-rtx-pro6000-spec.txt) | 用户确认 Workstation Edition；96 GB GDDR7、1792 GB/s、600 W；不能套用 Max-Q／Server 参数 |
| [Ollama Hardware support](https://docs.ollama.com/gpu) | [原件](files/documents/ollama-hardware.html) · [文本](text/ollama-hardware.txt) | Apple GPU 经 Metal；RTX PRO 6000 Blackwell compute capability 12.0；网页按获取日固定 |
| [Ollama Generate API](https://docs.ollama.com/api/generate.md) | [原件](files/documents/ollama-api-generate.md) · [文本](text/ollama-api-generate.txt) | API 耗时为纳秒；prefill／decode 统计不能直接替代客户端流式 TTFT／ITL |
| [Ollama v0.20.7 Apple device and working-set discovery](https://raw.githubusercontent.com/ollama/ollama/8d0dcf4b6daf8d7833c8b55108e5b45063795e57/discover/gpu_info_darwin.m) | [原件](files/documents/ollama-metal-device.txt) · [文本](text/ollama-metal-device.txt) | 固定提交 8d0dcf4b6daf8d7833c8b55108e5b45063795e57；仅为设备识别，内核来源另计 |
| [KT-Kernel inference README — fixed revision](https://raw.githubusercontent.com/kvcache-ai/ktransformers/31985f40bcc40da08107efdb1f81bf88cb38c6b2/kt-kernel/README.md) | [原件](files/documents/kt-kernel-guide.md) · [文本](text/kt-kernel-guide.txt) | 固定提交 31985f40bcc40da08107efdb1f81bf88cb38c6b2；AF 主案例采用 RTX 4090＋双路 Xeon Gold 6454S 示例 |
| [KTransformers: Unleashing the Full Potential of CPU/GPU Hybrid Inference for MoE Models](https://madsys.cs.tsinghua.edu.cn/publication/ktransformers-unleashing-the-full-potential-of-cpu/gpu-hybrid-inference-for-moe-models/SOSP25-chen.pdf) | [原件](files/papers/ktransformers-paper.pdf) · [文本](text/ktransformers-paper.txt) | SOSP 2025 作者原件；双 Xeon Platinum 8452Y＋A100 40GB／RTX 4080 16GB；与主案例配置分别引用 |
| [Bullet: Boosting GPU Utilization for LLM Serving via Dynamic Spatial-Temporal Orchestration](https://xianweiz.github.io/doc/papers/26asplos_bullet.pdf) | [原件](files/papers/bullet.pdf) · [文本](text/bullet.txt) | ASPLOS 2026 作者原件；A100/H20 内存与 SM 微基准；作为同卡 P/D 协作对照，不是 A100＋H20 PD 部署实测 |
| [Ollama v0.20.7 bundled ggml Metal device and buffers](https://raw.githubusercontent.com/ollama/ollama/8d0dcf4b6daf8d7833c8b55108e5b45063795e57/ml/backend/ggml/ggml/src/ggml-metal/ggml-metal-device.m) | [原件](files/documents/ollama-ggml-metal-memory.txt) · [文本](text/ollama-ggml-metal-memory.txt) | 固定提交；hasUnifiedMemory、shared／bytesNoCopy、工作集；保留 upstream 署名 |
| [Ollama v0.20.7 bundled ggml Metal kernels](https://raw.githubusercontent.com/ollama/ollama/8d0dcf4b6daf8d7833c8b55108e5b45063795e57/ml/backend/ggml/ggml/src/ggml-metal/ggml-metal.metal) | [原件](files/documents/ollama-ggml-metal-kernels.txt) · [文本](text/ollama-ggml-metal-kernels.txt) | 固定提交；量化解码、矩阵／向量计算、simdgroup；实际分派仍需运行日志确认 |
| [DeepSpeed Inference: Enabling Efficient Inference of Transformer Models at Unprecedented Scale](https://arxiv.org/abs/2207.00032v1) | [原件](files/papers/deepspeed-inference.pdf) · [文本](text/deepspeed-inference.txt) | Microsoft／DeepSpeed；内核、模型并行及 CPU／NVMe 异构推理的联合设计 |
| [DeepSpeed-FastGen: High-throughput Text Generation for LLMs via MII and DeepSpeed-Inference](https://arxiv.org/abs/2401.08671v1) | [原件](files/papers/deepspeed-fastgen.pdf) · [文本](text/deepspeed-fastgen.txt) | Microsoft／DeepSpeed-MII；Dynamic SplitFuse 与 token 级尾延迟；与 Sarathi 对照 |
| [FlashInfer: Efficient and Customizable Attention Engine for LLM Inference Serving](https://arxiv.org/abs/2501.01005v2) | [原件](files/papers/flashinfer.pdf) · [文本](text/flashinfer.txt) | 开源注意力引擎；KV 布局、负载均衡调度、JIT 与 CUDA Graph 兼容 |
| [KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache](https://arxiv.org/abs/2402.02750v2) | [原件](files/papers/kivi.pdf) · [文本](text/kivi.txt) | KV 的 K/V 非对称量化；计入 scale、zero point、残余缓存与反量化成本 |
| [H$_2$O: Heavy-Hitter Oracle for Efficient Generative Inference of Large Language Models](https://arxiv.org/abs/2306.14048v3) | [原件](files/papers/h2o.pdf) · [文本](text/h2o.txt) | 基于 heavy hitter 的 KV 淘汰；近似注意力须单独测量质量 |
| [Efficient Streaming Language Models with Attention Sinks](https://arxiv.org/abs/2309.17453v4) | [原件](files/papers/streamingllm.pdf) · [文本](text/streamingllm.txt) | Attention sinks 与滑动窗口；流式稳定性不等于保留完整历史检索能力 |
| [Accelerating Large Language Model Decoding with Speculative Sampling](https://arxiv.org/abs/2302.01318v1) | [原件](files/papers/speculative-sampling.pdf) · [文本](text/speculative-sampling.txt) | DeepMind；投机采样的拒绝校正与目标分布；和 Leviathan 等独立工作并列 |
| [Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads](https://arxiv.org/abs/2401.10774v3) | [原件](files/papers/medusa.pdf) · [文本](text/medusa.txt) | 多头草稿与树形验证；区分不同训练方式、接受规则及分布保证 |
| [EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty](https://arxiv.org/abs/2401.15077v3) | [原件](files/papers/eagle.pdf) · [文本](text/eagle.txt) | 特征层草稿与不确定性；额外模型训练、接受率和验证代价 |
| [EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test](https://arxiv.org/abs/2503.01840v3) | [原件](files/papers/eagle3.pdf) · [文本](text/eagle3.txt) | 2025 投机解码进展；多层特征融合、training-time test 与负载适用范围 |
| [LMCache: An Efficient KV Cache Layer for Enterprise-Scale LLM Inference](https://arxiv.org/abs/2510.09665v2) | [原件](files/papers/lmcache.pdf) · [文本](text/lmcache.txt) | 2025 开源系统报告；KV 分层存储、复用与传输；论文不代替当前接口文档 |
| [S-LoRA: Serving Thousands of Concurrent LoRA Adapters](https://arxiv.org/abs/2311.03285v3) | [原件](files/papers/s-lora.pdf) · [文本](text/s-lora.txt) | 多适配器服务；Unified Paging、异构批处理与张量并行 |
| [Fast Distributed Inference Serving for Large Language Models](https://arxiv.org/abs/2305.05920v3) | [原件](files/papers/fastserve.pdf) · [文本](text/fastserve.txt) | FastServe；输出长度未知下的抢占式调度与 KV 交换 |
| [LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale](https://arxiv.org/abs/2208.07339v2) | [原件](files/papers/llm-int8.pdf) · [文本](text/llm-int8.txt) | 大模型激活异常值与混合精度分解；低比特存储不等于端到端加速 |
| [TensorRT LLM Architecture Overview](https://nvidia.github.io/TensorRT-LLM/developer-guide/overview.html) | [原件](files/documents/tensorrt-llm-architecture.html) · [文本](text/tensorrt-llm-architecture.txt) | 官方架构文档快照；作为开源项目实现资料，不标为学术论文 |

## 第 9 章 分布式推理

| 资料 | 本地文件 | 用途 |
| --- | --- | --- |
| [DeepSeekMoE: Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models](https://arxiv.org/abs/2401.06066) | [原件](files/papers/deepseek-moe.pdf) · [文本](text/deepseek-moe.txt) | 专家粒度与共享专家 |
| [DeepSeek-V3 Technical Report](https://arxiv.org/abs/2412.19437) | [原件](files/papers/deepseek-v3.pdf) · [文本](text/deepseek-v3.txt) | FP8、MTP、负载均衡与训练系统 |
| [DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence](https://arxiv.org/abs/2606.19348) | [原件](files/papers/deepseek-v4.pdf) · [文本](text/deepseek-v4.txt) | 混合压缩注意力与分阶段训练 |
| [Kimi K3: Open Frontier Intelligence](https://github.com/MoonshotAI/Kimi-K3) | [原件](files/papers/kimi-k3.pdf) · [文本](text/kimi-k3.txt) | 官方报告；以内容校验值固定版本 |
| [Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity](https://arxiv.org/abs/2101.03961) | [原件](files/papers/switch-transformer.pdf) · [文本](text/switch-transformer.txt) | 条件计算与路由 |
| [NVIDIA GeForce RTX 4090 Specifications](https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/) | [原件](files/specs/nvidia-rtx4090.html) · [文本](text/nvidia-rtx4090.txt) | 历史硬件比较；KTransformers RTX 4090＋Xeon AF 案例 |
| [Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180) | [原件](files/papers/vllm.pdf) · [文本](text/vllm.txt) | KV 与分页 |
| [SGLang: Efficient Execution of Structured Language Model Programs](https://arxiv.org/abs/2312.07104) | [原件](files/papers/sglang.pdf) · [文本](text/sglang.txt) | 前缀缓存与执行 |
| [DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving](https://arxiv.org/abs/2401.09670) | [原件](files/papers/distserve.pdf) · [文本](text/distserve.txt) | PD 分离 |
| [Splitwise: Efficient Generative LLM Inference Using Phase Splitting](https://arxiv.org/abs/2311.18677) | [原件](files/papers/splitwise.pdf) · [文本](text/splitwise.txt) | 阶段资源池 |
| [Mooncake: A KVCache-centric Disaggregated Architecture for LLM Serving](https://arxiv.org/abs/2407.00079) | [原件](files/papers/mooncake.pdf) · [文本](text/mooncake.txt) | KV 池化与路由 |
| [The Llama 3 Herd of Models](https://arxiv.org/abs/2407.21783) | [原件](files/papers/llama3.pdf) · [文本](text/llama3.txt) | 架构与训练报告 |
| [昇腾 950 NPU 架构白皮书](files/specs/昇腾950%20NPU架构白皮书.pdf) | [原件](files/specs/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf) · [文本](text/ascend-950-whitepaper.txt)（user_provided） | 作者提供，40 页；保留原文件；另存官方 OBS 文件 ascend-950-official，两份文件差异核对见 UB-ASCEND-NOTES.md |
| [SambaRack SN50 Official Product Description](https://sambanova.ai/products/sambarack) | [原件](files/specs/sambanova-sn50-system.html) · [文本](text/sambanova-sn50-system.txt) | 系统产品介绍，非完整 ISA 或全部产品参数手册 |
| [Serving Large Language Models on Huawei CloudMatrix384, v2](https://arxiv.org/abs/2506.12708v2) | [原件](files/papers/cloudmatrix384-v2.pdf) · [文本](text/cloudmatrix384-v2.txt) | 2025-06-18；§3.3.1 的 910C、§4.2.2 MLA 与动态 tiling；与 v3 分开保存 |
| [Serving Large Language Models on Huawei CloudMatrix384, v3](https://arxiv.org/abs/2506.12708v3) | [原件](files/papers/cloudmatrix384-v3.pdf) · [文本](text/cloudmatrix384-v3.txt) | 2025-06-19 修订；核对型号称谓与 v2 差异 |
| [昇腾 950 NPU 架构白皮书（官方下载原件）](https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf) | [原件](files/specs/ascend-950-official.pdf) · [文本](text/ascend-950-official.txt) | 作者提供官方 OBS 下载地址；与先前作者提供版本分别保留，差异核对见 UB-ASCEND-NOTES.md |
| [KT-Kernel inference README — fixed revision](https://raw.githubusercontent.com/kvcache-ai/ktransformers/31985f40bcc40da08107efdb1f81bf88cb38c6b2/kt-kernel/README.md) | [原件](files/documents/kt-kernel-guide.md) · [文本](text/kt-kernel-guide.txt) | 固定提交 31985f40bcc40da08107efdb1f81bf88cb38c6b2；AF 主案例采用 RTX 4090＋双路 Xeon Gold 6454S 示例 |
| [KTransformers 0.3 AMX design notes](https://raw.githubusercontent.com/kvcache-ai/ktransformers/31985f40bcc40da08107efdb1f81bf88cb38c6b2/doc/en/AMX.md) | [原件](files/documents/kt-amx.md) · [文本](text/kt-amx.txt) | 2025 年 v0.3 历史设计；Intel AMX、AVX-512、权重重排与调度；性能按原配置引用 |
| [KTransformers: Unleashing the Full Potential of CPU/GPU Hybrid Inference for MoE Models](https://madsys.cs.tsinghua.edu.cn/publication/ktransformers-unleashing-the-full-potential-of-cpu/gpu-hybrid-inference-for-moe-models/SOSP25-chen.pdf) | [原件](files/papers/ktransformers-paper.pdf) · [文本](text/ktransformers-paper.txt) | SOSP 2025 作者原件；双 Xeon Platinum 8452Y＋A100 40GB／RTX 4080 16GB；与主案例配置分别引用 |
| [NVIDIA A100 80GB datasheet — December 2020](https://www.nvidia.cn/content/dam/en-zz/zh_cn/Solutions/Data-Center/a100/pdf/a100-80gb-datasheet-update-a4-nvidia-1485612-r13-web_zhCN.pdf) | [原件](files/specs/nvidia-a100-80-spec.pdf) · [文本](text/nvidia-a100-80-spec.txt) | A100 80 GB；SXM 与 PCIe、稠密与稀疏峰值分别引用 |
| [NVIDIA AI Enterprise 6.2 supported H20 SXM5 configurations](https://docs.nvidia.com/ai-enterprise/release-6/6.2/appendix/vgpu.html) | [原件](files/specs/nvidia-h20-vgpu.html) · [文本](text/nvidia-h20-vgpu.txt) | 官方确认 H20 SXM5 96GB 型号；不是完整 H20 带宽／算力数据表 |
| [Bullet: Boosting GPU Utilization for LLM Serving via Dynamic Spatial-Temporal Orchestration](https://xianweiz.github.io/doc/papers/26asplos_bullet.pdf) | [原件](files/papers/bullet.pdf) · [文本](text/bullet.txt) | ASPLOS 2026 作者原件；A100/H20 内存与 SM 微基准；作为同卡 P/D 协作对照，不是 A100＋H20 PD 部署实测 |
| [Demystifying the Design Space and Best Practices for Heterogeneous LLM Inference and Serving](https://arxiv.org/pdf/2606.29708v1) | [原件](files/papers/heterogeneous-pd.pdf) · [文本](text/heterogeneous-pd.txt) | 固定 v1；放置、KV 表示和生命周期；其生产例为 C600＋Hopper，不能写成 A100＋H20 |
| [KT-Kernel CMake ARM KML build path](https://raw.githubusercontent.com/kvcache-ai/ktransformers/31985f40bcc40da08107efdb1f81bf88cb38c6b2/kt-kernel/CMakeLists.txt) | [原件](files/documents/kt-kml-build.txt) · [文本](text/kt-kml-build.txt) | 固定提交；KML 构建分支的背景归档，不作为当前 Xeon AF 案例的实现依据 |
| [KT-Kernel KML MoE correctness example](https://raw.githubusercontent.com/kvcache-ai/ktransformers/31985f40bcc40da08107efdb1f81bf88cb38c6b2/kt-kernel/examples/test_moe_kml.py) | [原件](files/documents/kt-kml-example.txt) · [文本](text/kt-kml-example.txt) | 固定提交；KML MoE 样例的背景归档，不作为当前 Xeon AF 案例的实现依据 |
| [Efficiently Scaling Transformer Inference](https://arxiv.org/abs/2211.05102v1) | [原件](files/papers/scaling-inference.pdf) · [文本](text/scaling-inference.txt) | Google；推理计算／通信模型、TPU 分片与延迟—吞吐取舍；历史配置不直接套用 GPU |
| [DeepSpeed Inference: Enabling Efficient Inference of Transformer Models at Unprecedented Scale](https://arxiv.org/abs/2207.00032v1) | [原件](files/papers/deepspeed-inference.pdf) · [文本](text/deepspeed-inference.txt) | Microsoft／DeepSpeed；内核、模型并行及 CPU／NVMe 异构推理的联合设计 |
| [Preble: Efficient Distributed Prompt Scheduling for LLM Serving](https://arxiv.org/abs/2407.00023v2) | [原件](files/papers/preble.pdf) · [文本](text/preble.txt) | 分布式前缀感知调度；缓存局部性与队列均衡的联合取舍 |
| [LMCache: An Efficient KV Cache Layer for Enterprise-Scale LLM Inference](https://arxiv.org/abs/2510.09665v2) | [原件](files/papers/lmcache.pdf) · [文本](text/lmcache.txt) | 2025 开源系统报告；KV 分层存储、复用与传输；论文不代替当前接口文档 |
| [AlpaServe: Statistical Multiplexing with Model Parallelism for Deep Learning Serving](https://arxiv.org/abs/2302.11665v2) | [原件](files/papers/alpaserve.pdf) · [文本](text/alpaserve.txt) | 多模型服务的统计复用；模型并行、放置与 SLO 联合优化 |
| [Mixtral of Experts](https://arxiv.org/abs/2401.04088v1) | [原件](files/papers/mixtral.pdf) · [文本](text/mixtral.txt) | Mistral 公司模型报告；稀疏激活、专家路由与驻留参数的区别 |
| [Insights into DeepSeek-V3: Scaling Challenges and Reflections on Hardware for AI Architectures](https://arxiv.org/abs/2505.09343v2) | [原件](files/papers/deepseek-infra.pdf) · [文本](text/deepseek-infra.txt) | DeepSeek ISCA 2025 报告；MLA／MoE、跨节点通信及硬件协同设计建议 |
| [Day 6: DeepSeek-V3/R1 Inference System Overview](https://github.com/deepseek-ai/open-infra-index/blob/56d86855fcf6e08fdfd45ce6280bd24322c93351/202502OpenSourceWeek/day_6_one_more_thing_deepseekV3R1_inference_system_overview.md) | [原件](files/documents/deepseek-serving-report.md) · [文本](text/deepseek-serving-report.txt) | 2025 公司工程报告；固定提交；PD、EP、通信与费用口径 |
| [How NVIDIA Dynamo 1.0 Powers Multi-Node Inference at Production Scale](https://developer.nvidia.com/blog/?p=113961) | [原件](files/documents/dynamo-production.html) · [文本](text/dynamo-production.txt) | 2026 官方技术文章；编排、KV 路由与恢复；厂商比较须保留原条件 |
| [TensorRT LLM Architecture Overview](https://nvidia.github.io/TensorRT-LLM/developer-guide/overview.html) | [原件](files/documents/tensorrt-llm-architecture.html) · [文本](text/tensorrt-llm-architecture.txt) | 官方架构文档快照；作为开源项目实现资料，不标为学术论文 |

## 第 10 章 训练系统

| 资料 | 本地文件 | 用途 |
| --- | --- | --- |
| [DeepSeek-V3 Technical Report](https://arxiv.org/abs/2412.19437) | [原件](files/papers/deepseek-v3.pdf) · [文本](text/deepseek-v3.txt) | FP8、MTP、负载均衡与训练系统 |
| [DeepSeek-V3.2: Pushing the Frontier of Open Large Language Models](https://arxiv.org/abs/2512.02556) | [原件](files/papers/deepseek-v32.pdf) · [文本](text/deepseek-v32.txt) | DSA 与后训练 |
| [DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence](https://arxiv.org/abs/2606.19348) | [原件](files/papers/deepseek-v4.pdf) · [文本](text/deepseek-v4.txt) | 混合压缩注意力与分阶段训练 |
| [Kimi K3: Open Frontier Intelligence](https://github.com/MoonshotAI/Kimi-K3) | [原件](files/papers/kimi-k3.pdf) · [文本](text/kimi-k3.txt) | 官方报告；以内容校验值固定版本 |
| [Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity](https://arxiv.org/abs/2101.03961) | [原件](files/papers/switch-transformer.pdf) · [文本](text/switch-transformer.txt) | 条件计算与路由 |
| [NVIDIA GeForce RTX 4090 Specifications](https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/) | [原件](files/specs/nvidia-rtx4090.html) · [文本](text/nvidia-rtx4090.txt) | 历史硬件比较；KTransformers RTX 4090＋Xeon AF 案例 |
| [Unsloth official README](https://github.com/unslothai/unsloth) | [原件](files/documents/unsloth.md) · [文本](text/unsloth.txt) | 本地训练、运行、量化与导出 |
| [Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism](https://arxiv.org/abs/1909.08053) | [原件](files/papers/megatron.pdf) · [文本](text/megatron.txt) | 模型并行 |
| [Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM](https://arxiv.org/abs/2104.04473) | [原件](files/papers/megatron-scale.pdf) · [文本](text/megatron-scale.txt) | 并行组合 |
| [ZeRO: Memory Optimizations Toward Training Trillion Parameter Models](https://arxiv.org/abs/1910.02054) | [原件](files/papers/zero.pdf) · [文本](text/zero.txt) | 状态分片 |
| [GPipe: Easy Scaling with Micro-Batch Pipeline Parallelism](https://arxiv.org/abs/1811.06965) | [原件](files/papers/gpipe.pdf) · [文本](text/gpipe.txt) | 当前下载的 arXiv 版本标题；流水并行 |
| [Reducing Activation Recomputation in Large Transformer Models](https://arxiv.org/abs/2205.05198) | [原件](files/papers/activation-recompute.pdf) · [文本](text/activation-recompute.txt) | 选择性重计算 |
| [CheckFreq: Frequent, Fine-Grained DNN Checkpointing](https://www.usenix.org/conference/fast21/presentation/mohan) | [原件](files/papers/checkfreq.pdf) · [文本](text/checkfreq.txt) | 检查点频率与数据读取状态 |
| [HybridFlow: A Flexible and Efficient RLHF Framework](https://arxiv.org/abs/2409.19256) | [原件](files/papers/verl.pdf) · [文本](text/verl.txt) | RL 执行闭环 |
| [AReaL: A Large-Scale Asynchronous Reinforcement Learning System for Language Reasoning](https://arxiv.org/abs/2505.24298) | [原件](files/papers/areal.pdf) · [文本](text/areal.txt) | 异步训练与策略版本 |
| [A100/H100 太贵，何不用 4090？](https://01.me/2023/09/h100-vs-4090/) | [原件](files/documents/h100-vs-4090.html) · [文本](text/h100-vs-4090.txt) | 历史价格与计算需按正文案例重新核算 |
| [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685) | [原件](files/papers/lora.pdf) · [文本](text/lora.txt) | 冻结参数与训练计算量 |
| [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314) | [原件](files/papers/qlora.pdf) · [文本](text/qlora.txt) | 量化微调 |
| [The Llama 3 Herd of Models](https://arxiv.org/abs/2407.21783) | [原件](files/papers/llama3.pdf) · [文本](text/llama3.txt) | 架构与训练报告 |
| [Google's Training Supercomputers from TPU v2 to Ironwood: Architectural Stability, Scale, Resilience, Power Efficiency, and Sustainability Across Five Generations](https://arxiv.org/abs/2606.15870) | [原件](files/papers/google-tpu-generations.pdf) · [文本](text/google-tpu-generations.txt) | Google 作者跨代架构论文；与云文档日期分别登记 |
| [Amazon EC2 Trn2 Architecture](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/about-neuron/arch/neuron-hardware/trn2-arch.html) | [原件](files/specs/aws-trn2-system.html) · [文本](text/aws-trn2-system.txt) | 实例、UltraServer、NeuronLink 拓扑和 EFA |
| [Amazon EC2 Trn3 UltraServers](https://aws.amazon.com/ec2/instance-types/trn3/) | [原件](files/specs/aws-trn3-system.html) · [文本](text/aws-trn3-system.txt) | 系统规格；整机 HBM、芯片数与单设备参数分开 |
| [Serving Large Language Models on Huawei CloudMatrix384, v2](https://arxiv.org/abs/2506.12708v2) | [原件](files/papers/cloudmatrix384-v2.pdf) · [文本](text/cloudmatrix384-v2.txt) | 2025-06-18；§3.3.1 的 910C、§4.2.2 MLA 与动态 tiling；与 v3 分开保存 |
| [Serving Large Language Models on Huawei CloudMatrix384, v3](https://arxiv.org/abs/2506.12708v3) | [原件](files/papers/cloudmatrix384-v3.pdf) · [文本](text/cloudmatrix384-v3.txt) | 2025-06-19 修订；核对型号称谓与 v2 差异 |
| [CUDA Graph Best Practice for PyTorch: CUDA Graph](https://docs.nvidia.com/dl-cuda-graph/cuda-graph-basics/cuda-graph.html) | [原件](files/documents/cuda-graphs.html) · [文本](text/cuda-graphs.txt) | 定义、实例化与执行；区分主机提交和设备启动成本 |
| [DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/abs/2501.12948v2) | [原件](files/papers/deepseek-r1.pdf) · [文本](text/deepseek-r1.txt) | 公司技术报告；RL 推理模型、长输出与采样负载；不视为 serving 性能报告 |

## 第 11 章 资源调度与运行环境

| 资料 | 本地文件 | 用途 |
| --- | --- | --- |
| [Kimi K3: Open Frontier Intelligence](https://github.com/MoonshotAI/Kimi-K3) | [原件](files/papers/kimi-k3.pdf) · [文本](text/kimi-k3.txt) | 官方报告；以内容校验值固定版本 |
| [RFC 8831: WebRTC Data Channels](https://www.rfc-editor.org/rfc/rfc8831) | [原件](files/standards/rfc8831.txt) · [文本](text/rfc8831.txt) | DataChannel 与 SCTP |
| [HybridFlow: A Flexible and Efficient RLHF Framework](https://arxiv.org/abs/2409.19256) | [原件](files/papers/verl.pdf) · [文本](text/verl.txt) | RL 执行闭环 |
| [AReaL: A Large-Scale Asynchronous Reinforcement Learning System for Language Reasoning](https://arxiv.org/abs/2505.24298) | [原件](files/papers/areal.pdf) · [文本](text/areal.txt) | 异步训练与策略版本 |
| [Heterogeneity-Aware Cluster Scheduling Policies for Deep Learning Workloads](https://www.usenix.org/conference/osdi20/presentation/narayanan-deepak) | [原件](files/papers/gavel.pdf) · [文本](text/gavel.txt) | Gavel |
| [Pollux: Co-adaptive Cluster Scheduling for Goodput-Optimized Deep Learning](https://www.usenix.org/conference/osdi21/presentation/qiao) | [原件](files/papers/pollux.pdf) · [文本](text/pollux.txt) | 作业弹性与训练适配；指标不强加给环境平台 |
| [Tiresias: A GPU Cluster Manager for Distributed Deep Learning](https://www.usenix.org/conference/nsdi19/presentation/gu) | [原件](files/papers/tiresias.pdf) · [文本](text/tiresias.txt) | 排队、公平与放置 |
| [Dominant Resource Fairness: Fair Allocation of Multiple Resource Types](https://www.usenix.org/conference/nsdi11/dominant-resource-fairness-fair-allocation-multiple-resource-types) | [原件](files/papers/drf.pdf) · [文本](text/drf.txt) | 多资源公平分配 |
| [RouteLLM: Learning to Route LLMs from Preference Data](https://arxiv.org/abs/2406.18665) | [原件](files/papers/routellm.pdf) · [文本](text/routellm.txt) | 跨模型路由 |
| [FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance](https://arxiv.org/abs/2305.05176) | [原件](files/papers/frugalgpt.pdf) · [文本](text/frugalgpt.txt) | 模型级联与选择 |
| [Firecracker: Lightweight Virtualization for Serverless Applications](https://www.usenix.org/conference/nsdi20/presentation/agache) | [原件](files/papers/firecracker.pdf) · [文本](text/firecracker.txt) | 微型虚拟机 |
| [Kueue Concepts](https://kueue.sigs.k8s.io/docs/concepts/) | [原件](files/documents/kueue.html) · [文本](text/kueue.txt) | 作业、队列与配额 |
| [Kubernetes Scheduling Framework](https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/) | [原件](files/documents/k8s-scheduling.html) · [文本](text/k8s-scheduling.txt) | 调度阶段与插件 |
| [Kubernetes Images](https://kubernetes.io/docs/concepts/containers/images/) | [原件](files/documents/k8s-images.html) · [文本](text/k8s-images.txt) | 镜像与拉取行为 |
| [OpenCost Specification](https://opencost.io/docs/specification/) | [原件](files/documents/opencost.html) · [文本](text/opencost.txt) | 资源成本归集；与对外计价规则区分 |
| [OpenTelemetry Semantic Conventions for Generative AI Metrics](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/) | [原件](files/documents/otel-genai.html) · [文本](text/otel-genai.txt) | 用量事件与 token 计量；记录规范稳定性 |
| [Unified Bus Software Reference Design for Operating Systems 2.0](https://www.unifiedbus.com/en/software) | [原件](files/specs/ub-os-reference.pdf) · [文本](text/ub-os-reference.txt) | 官网公开操作系统参考设计 |
| [Kueue ClusterQueue](https://kueue.sigs.k8s.io/docs/concepts/cluster_queue/) | [原件](files/documents/kueue-clusterqueue.html) · [文本](text/kueue-clusterqueue.txt) | 配额、借用与队列 |
| [Kueue Preemption](https://kueue.sigs.k8s.io/docs/concepts/preemption/) | [原件](files/documents/kueue-preemption.html) · [文本](text/kueue-preemption.txt) | 作业抢占 |
| [灵衢基础规范 2.0.1（中文版）](https://www.unifiedbus.com/zh/docs/UB-Base-Specification-2.0.1-zh-clean) | [原件](files/specs/UB-Base-Specification-2.0.1-zh-clean.pdf) · [文本](text/ub-base-201-zh.txt)（user_provided） | 作者提供；2026 年 4 月，545 页；协议语义、顺序、完成、地址和管理 |
| [灵衢使能操作系统参考设计 2.0（中文版）](https://www.unifiedbus.com/zh/docs/UB-Software-Reference-Design-for-OS-2.0-zh) | [原件](files/specs/UB-Software-Reference-Design-for-OS-2.0-zh.pdf) · [文本](text/ub-os-zh.txt)（user_provided） | 作者提供；2025 年 9 月，57 页；设备、内存、通信、虚拟化与 RAS；引用 Base 2.0 |
| [Google Cloud TPU Machine Specifications](https://docs.cloud.google.com/compute/docs/tpus/tpu-machines) | [原件](files/specs/google-tpu-machines.html) · [文本](text/google-tpu-machines.txt) | 主机 VM、芯片、ICI 和 DCN 的口径区别 |
| [SambaNova SN40L: Scaling the AI Memory Wall with Dataflow and Composition of Experts](https://arxiv.org/abs/2405.07518) | [原件](files/papers/sambanova-sn40l-paper.pdf) · [文本](text/sambanova-sn40l-paper.txt) | 厂商原始架构论文；三级存储、融合与多模型切换，非两页宣传材料 |
| [S-LoRA: Serving Thousands of Concurrent LoRA Adapters](https://arxiv.org/abs/2311.03285v3) | [原件](files/papers/s-lora.pdf) · [文本](text/s-lora.txt) | 多适配器服务；Unified Paging、异构批处理与张量并行 |
| [AlpaServe: Statistical Multiplexing with Model Parallelism for Deep Learning Serving](https://arxiv.org/abs/2302.11665v2) | [原件](files/papers/alpaserve.pdf) · [文本](text/alpaserve.txt) | 多模型服务的统计复用；模型并行、放置与 SLO 联合优化 |
| [Fast Distributed Inference Serving for Large Language Models](https://arxiv.org/abs/2305.05920v3) | [原件](files/papers/fastserve.pdf) · [文本](text/fastserve.txt) | FastServe；输出长度未知下的抢占式调度与 KV 交换 |
| [How NVIDIA Dynamo 1.0 Powers Multi-Node Inference at Production Scale](https://developer.nvidia.com/blog/?p=113961) | [原件](files/documents/dynamo-production.html) · [文本](text/dynamo-production.txt) | 2026 官方技术文章；编排、KV 路由与恢复；厂商比较须保留原条件 |

## 第 12 章 端边云协同

| 资料 | 本地文件 | 用途 |
| --- | --- | --- |
| [Deploying Transformers on the Apple Neural Engine](https://machinelearning.apple.com/research/neural-engine-transformers) | [原件](files/documents/apple-ane.html) · [文本](text/apple-ane.txt) | 保留文章年代与实验设备 |
| [MLX official README](https://github.com/ml-explore/mlx) | [原件](files/documents/mlx.md) · [文本](text/mlx.txt) | Apple Silicon 软件栈 |
| [Unsloth official README](https://github.com/unslothai/unsloth) | [原件](files/documents/unsloth.md) · [文本](text/unsloth.txt) | 本地训练、运行、量化与导出 |
| [RFC 9293: Transmission Control Protocol](https://www.rfc-editor.org/rfc/rfc9293) | [原件](files/standards/rfc9293.txt) · [文本](text/rfc9293.txt) | TCP |
| [RFC 9000: QUIC Transport](https://www.rfc-editor.org/rfc/rfc9000) | [原件](files/standards/rfc9000.txt) · [文本](text/rfc9000.txt) | QUIC 传输 |
| [RFC 9002: QUIC Loss Detection and Congestion Control](https://www.rfc-editor.org/rfc/rfc9002) | [原件](files/standards/rfc9002.txt) · [文本](text/rfc9002.txt) | 丢包与拥塞 |
| [RFC 3550: RTP](https://www.rfc-editor.org/rfc/rfc3550) | [原件](files/standards/rfc3550.txt) · [文本](text/rfc3550.txt) | 实时媒体 |
| [RFC 8831: WebRTC Data Channels](https://www.rfc-editor.org/rfc/rfc8831) | [原件](files/standards/rfc8831.txt) · [文本](text/rfc8831.txt) | DataChannel 与 SCTP |
| [RFC 8836: Congestion Control Requirements for Interactive Real-Time Media](https://www.rfc-editor.org/rfc/rfc8836) | [原件](files/standards/rfc8836.txt) · [文本](text/rfc8836.txt) | 交互媒体目标 |
| [Robust Speech Recognition via Large-Scale Weak Supervision](https://arxiv.org/abs/2212.04356) | [原件](files/papers/whisper.pdf) · [文本](text/whisper.txt) | ASR 计算与数据流 |
| [Conditional Variational Autoencoder with Adversarial Learning for End-to-End Text-to-Speech](https://arxiv.org/abs/2106.06103) | [原件](files/papers/vits.pdf) · [文本](text/vits.txt) | TTS 结构；不预设为流式系统 |
| [计算机网络的新黄金时代（二）](https://01.me/2023/05/new-golden-age-for-network-2/) | [原件](files/documents/network-golden-2.html) · [文本](text/network-golden-2.txt) | 作者素材；广域 |
| [计算机网络的新黄金时代（三）](https://01.me/2023/06/new-golden-age-for-network-3/) | [原件](files/documents/network-golden-3.html) · [文本](text/network-golden-3.txt) | 作者素材；无线与端侧 |
| [FlexGen: High-Throughput Generative Inference of Large Language Models with a Single GPU](https://arxiv.org/abs/2303.06865) | [原件](files/papers/flexgen.pdf) · [文本](text/flexgen.txt) | 卸载与数据移动 |
| [Snapdragon X Elite Product Brief](https://www.qualcomm.com/content/dam/qcomm-martech/dm-assets/images/company/news-media/media-center/press-kits/snapdragon-summit-2023/documents/SnapdragonXEliteProductBrief.pdf) | [原件](files/specs/qualcomm-xelite.pdf) · [文本](text/qualcomm-xelite.txt) | 端侧 CPU、GPU、Hexagon 与共享内存；2023 年产品代际 |
| [MacBook Pro (14-inch, M5) Technical Specifications](https://support.apple.com/en-mide/125405) | [原件](files/specs/apple-m5-macbook.html) · [文本](text/apple-m5-macbook.txt) | 2025 年具体端侧产品；CPU、GPU、Neural Engine 与统一内存，非完整微架构手册 |
| [Apple M2 Pro and M2 Max launch specifications](https://www.apple.com/newsroom/2023/01/apple-unveils-m2-pro-and-m2-max-next-generation-chips-for-next-level-workflows/) | [原件](files/specs/apple-m2-pro-max.html) · [文本](text/apple-m2-pro-max.txt) | 2023-01-17；M2 Pro 200 GB/s，M2 Max 400 GB/s；本书实机为 M2 Max 38 核 GPU、96 GB |

## 第 13 章 架构协同设计

| 资料 | 本地文件 | 用途 |
| --- | --- | --- |
| [DeepSeek-V3 Technical Report](https://arxiv.org/abs/2412.19437) | [原件](files/papers/deepseek-v3.pdf) · [文本](text/deepseek-v3.txt) | FP8、MTP、负载均衡与训练系统 |
| [DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence](https://arxiv.org/abs/2606.19348) | [原件](files/papers/deepseek-v4.pdf) · [文本](text/deepseek-v4.txt) | 混合压缩注意力与分阶段训练 |
| [Scaling Laws for Neural Language Models](https://arxiv.org/abs/2001.08361) | [原件](files/papers/scaling-laws.pdf) · [文本](text/scaling-laws.txt) | 历史 scaling law；计算口径须重核 |
| [Training Compute-Optimal Large Language Models](https://arxiv.org/abs/2203.15556) | [原件](files/papers/chinchilla.pdf) · [文本](text/chinchilla.txt) | 参数、数据与预算 |
| [Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures](https://digicoll.lib.berkeley.edu/record/136692) | [原件](files/papers/roofline.pdf) · [文本](text/roofline.txt) | 作者机构技术报告；Berkeley 图书馆归档 |
| [The Hardware Lottery](https://arxiv.org/abs/2009.06489) | [原件](files/papers/hardware-lottery.pdf) · [文本](text/hardware-lottery.txt) | 硬件、软件与研究选择 |
| [In-Datacenter Performance Analysis of a Tensor Processing Unit](https://arxiv.org/abs/1704.04760) | [原件](files/papers/tpu-v1.pdf) · [文本](text/tpu-v1.txt) | TPU 起源与设计比较 |
| [TPU v4: An Optically Reconfigurable Supercomputer for Machine Learning with Hardware Support for Embeddings](https://arxiv.org/abs/2304.01433) | [原件](files/papers/tpu-v4.pdf) · [文本](text/tpu-v4.txt) | 芯片与互联协同 |
| [NVIDIA GB200 NVL72](https://www.nvidia.com/en-us/data-center/gb200-nvl72/) | [原件](files/specs/nvidia-gb200.html) · [文本](text/nvidia-gb200.txt) | 整柜与 NVLink 域 |
| [昇腾 950 与 Unified Bus 公开路线图](https://www.huawei.com/cn/news/2025/9/hc-xu-keynote-speech) | [原件](files/specs/ascend-950-roadmap.html) · [文本](text/ascend-950-roadmap.txt) | 按型号区分计划与交付状态 |
| [Huawei SuperPoD Portfolio at MWC Barcelona 2026](https://www.huawei.com/en/news/2026/3/mwc-superpod-computing) | [原件](files/documents/ascend-950-mwc.html) · [文本](text/ascend-950-mwc.txt) | Atlas 950 至多 8192 NPU 的官方公告 |
| [Unified Bus 背后的思考](https://01.me/2025/09/a-story-of-unified-bus/) | [原件](files/documents/ub-reflection.html) · [文本](text/ub-reflection.txt) | 作者综述；非协议规范 |
| [Splitwise: Efficient Generative LLM Inference Using Phase Splitting](https://arxiv.org/abs/2311.18677) | [原件](files/papers/splitwise.pdf) · [文本](text/splitwise.txt) | 阶段资源池 |
| [OpenTallas architecture and analysis](https://github.com/bojieli/OpenTallas/tree/39b96158d35b24bd2bcd49061a689aea6893d2ed) | [原件](files/documents/opentallas-readme.md) · [文本](text/opentallas-readme.txt)（local_snapshot） | 与本书已有案例使用相同提交 |
| [The Llama 3 Herd of Models](https://arxiv.org/abs/2407.21783) | [原件](files/papers/llama3.pdf) · [文本](text/llama3.txt) | 架构与训练报告 |
| [The Cerebras Wafer-Scale Architecture for Deep Learning](https://www.cerebras.ai/chip) | [原件](files/specs/cerebras-wse3.pdf) · [文本](text/cerebras-wse3.txt) | 13 页架构白皮书，正文介绍 WSE-3；官网 Datasheet 链接名称与正文标题不同，以正文为准 |
| [SambaNova SN40L Reconfigurable Dataflow Unit](https://sambanova.ai/) | [原件](files/specs/sambanova-sn40l.pdf) · [文本](text/sambanova-sn40l.txt) | 两页官方产品技术介绍；非完整微架构论文 |
| [SambaNova SambaRack SN40L-16 Datasheet](https://sambanova.ai/) | [原件](files/specs/sambanova-sambarack.pdf) · [文本](text/sambanova-sambarack.txt) | 按 PDF 正文核对产品代际，不从下载文件名推断日期 |
| [Think Fast: A Tensor Streaming Processor (TSP) for Accelerating Deep Learning Workloads](https://groq.com/papers/) | [原件](files/papers/groq-tsp.pdf) · [文本](text/groq-tsp.txt) | ISCA 2020；编译调度与确定性执行 |
| [A Software-defined Tensor Streaming Multiprocessor for Large-scale Machine Learning](https://groq.com/papers/) | [原件](files/papers/groq-scale.pdf) · [文本](text/groq-scale.txt) | ISCA 2022；多芯片协同 |
| [GroqChip Processor Product Brief v1.5](https://groq.com/papers/) | [原件](files/specs/groq-chip.pdf) · [文本](text/groq-chip.txt) | 官方规格；历史代际参数 |
| [Taalas HC1 Technology Demonstrator](https://taalas.com/products/) | [原件](files/specs/taalas-hc1.html) · [文本](text/taalas-hc1.txt) | 厂商模型固化产品介绍；吞吐为厂商声明，须保留负载条件 |
| [Etched 官方产品页面](https://www.etched.com/) | [原件](files/documents/etched-sohu.html) · [文本](text/etched-sohu.txt) | 当前公开介绍；不能代替 Sohu 完整微架构规格 |
| [Cerebras Wafer-Scale Engine 3 Datasheet](https://training-docs.cerebras.ai/rel-2.4.0/concepts/cerebras-wafer-scale-cluster) | [原件](files/specs/cerebras-wse3-spec.pdf) · [文本](text/cerebras-wse3-spec.txt) | 由官方开发文档直接链接；与 WSE-3T 区分 |
| [Cerebras CS-4 Datasheet](https://investors.cerebras.ai/news-releases/news-release-details/cerebras-unveils-cs-4-30-times-faster-gpu-based-solutions) | [原件](files/specs/cerebras-cs4-spec.pdf) · [文本](text/cerebras-cs4-spec.txt) | 2026 年公开新代际；保留产品声明和交付时间边界 |
| [昇腾 950 NPU 架构白皮书](files/specs/昇腾950%20NPU架构白皮书.pdf) | [原件](files/specs/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf) · [文本](text/ascend-950-whitepaper.txt)（user_provided） | 作者提供，40 页；保留原文件；另存官方 OBS 文件 ascend-950-official，两份文件差异核对见 UB-ASCEND-NOTES.md |
| [Google Cloud TPU v4 官方规格](https://docs.cloud.google.com/tpu/docs/v4) | [原件](files/specs/google-v4.html) · [文本](text/google-v4.txt) | 芯片、HBM、ICI 与 Pod 配置；云资源参数与硬件能力分别引用 |
| [Google Cloud TPU v5e 官方规格](https://docs.cloud.google.com/tpu/docs/v5e) | [原件](files/specs/google-v5e.html) · [文本](text/google-v5e.txt) | 芯片、HBM、ICI 与 Pod 配置；云资源参数与硬件能力分别引用 |
| [Google Cloud TPU v5p 官方规格](https://docs.cloud.google.com/tpu/docs/v5p) | [原件](files/specs/google-v5p.html) · [文本](text/google-v5p.txt) | 芯片、HBM、ICI 与 Pod 配置；云资源参数与硬件能力分别引用 |
| [Google Cloud TPU v6e 官方规格](https://docs.cloud.google.com/tpu/docs/v6e) | [原件](files/specs/google-v6e.html) · [文本](text/google-v6e.txt) | 芯片、HBM、ICI 与 Pod 配置；云资源参数与硬件能力分别引用 |
| [Google Cloud TPU tpu7x 官方规格](https://docs.cloud.google.com/tpu/docs/tpu7x) | [原件](files/specs/google-tpu7x.html) · [文本](text/google-tpu7x.txt) | 芯片、HBM、ICI 与 Pod 配置；云资源参数与硬件能力分别引用 |
| [Inside the Eighth-Generation TPU: An Architecture Deep Dive](https://cloud.google.com/blog/products/compute/tpu-8t-and-tpu-8i-technical-deep-dive) | [原件](files/specs/google-tpu8.html) · [文本](text/google-tpu8.txt) | 2026-04-22 官方技术说明及规格表；不等同于完整 ISA 或正式云实例规格 |
| [Google's Training Supercomputers from TPU v2 to Ironwood: Architectural Stability, Scale, Resilience, Power Efficiency, and Sustainability Across Five Generations](https://arxiv.org/abs/2606.15870) | [原件](files/papers/google-tpu-generations.pdf) · [文本](text/google-tpu-generations.txt) | Google 作者跨代架构论文；与云文档日期分别登记 |
| [The Data Center Architecture for Graphcore Computing](https://www.graphcore.ai/hubfs/Graphcore-Mk2-IPU-System-Architecture-GC.pdf) | [原件](files/specs/graphcore-mk2.pdf) · [文本](text/graphcore-mk2.txt) | 官方系统白皮书；芯片、Streaming Memory 与主机解耦 |
| [IPU-Machine M2000 Datasheet 1.0.0](https://docs.graphcore.ai/projects/graphcore-ipu-m2000-datasheet/en/1.0.0/) | [原件](files/specs/graphcore-m2000-pdf.pdf) · [文本](text/graphcore-m2000-pdf.txt) | 历史版本的整机规格，4 个 IPU 的参数不当作单芯片 |
| [IPU-M2000 Product Description and Technical Specifications](https://docs.graphcore.ai/projects/graphcore-ipu-m2000-datasheet/en/latest/product-description.html) | [原件](files/specs/graphcore-m2000.html) · [文本](text/graphcore-m2000.txt) | 官方完整产品规格章节快照；latest URL 不代表当前仍在销售 |
| [Bow-2000 Product Description and Technical Specifications](https://docs.graphcore.ai/projects/bow-2000-datasheet/en/latest/product-description.html) | [原件](files/specs/graphcore-bow2000.html) · [文本](text/graphcore-bow2000.txt) | 官方完整产品规格章节快照；latest URL 不代表当前仍在销售 |
| [Graphcore Bow Pod16 Product Brief](https://www.graphcore.ai/hubfs/assets/pdf/Product%20Brief%20Bow%20Pod16%20020322.pdf) | [原件](files/specs/graphcore-bowpod16.pdf) · [文本](text/graphcore-bowpod16.txt) | Pod 系统规格；保留主机与交换机是否计入的边界 |
| [Dissecting the Graphcore IPU Architecture via Microbenchmarking](https://arxiv.org/abs/1912.03413) | [原件](files/papers/graphcore-microbench.pdf) · [文本](text/graphcore-microbench.txt) | 原始测量论文；第一代 IPU 的结果不移植为 GC200 或 Bow 实测 |
| [SambaNova SN40L: Scaling the AI Memory Wall with Dataflow and Composition of Experts](https://arxiv.org/abs/2405.07518) | [原件](files/papers/sambanova-sn40l-paper.pdf) · [文本](text/sambanova-sn40l-paper.txt) | 厂商原始架构论文；三级存储、融合与多模型切换，非两页宣传材料 |
| [Introducing AMD CDNA 3 Architecture](https://www.amd.com/en/technologies/cdna.html) | [原件](files/specs/amd-cdna3.pdf) · [文本](text/amd-cdna3.txt) | 架构白皮书；MI300A 与 MI300X 的芯粒和内存组织分开 |
| [Introducing AMD CDNA 4 Architecture](https://www.amd.com/en/technologies/cdna.html) | [原件](files/specs/amd-cdna4.pdf) · [文本](text/amd-cdna4.txt) | 架构白皮书；精度、分块、存储与通信 |
| [AMD Instinct MI300X Product Specifications](https://www.amd.com/en/products/accelerators/instinct/mi300/mi300x.html) | [原件](files/specs/amd-mi300x.html) · [文本](text/amd-mi300x.txt) | 单加速器规格与功率边界 |
| [AMD Instinct MI300X Platform Datasheet](https://www.amd.com/en/products/accelerators/instinct/mi300/mi300x.html) | [原件](files/specs/amd-mi300x-platform.pdf) · [文本](text/amd-mi300x-platform.txt) | 8 GPU 平台；与单 OAM 规格区分 |
| [AMD Instinct MI350X GPU Datasheet](https://www.amd.com/en/products/accelerators/instinct/mi350/mi350x.html) | [原件](files/specs/amd-mi350x.pdf) · [文本](text/amd-mi350x.txt) | 单 OAM 规格，按精度与稀疏条件引用 |
| [AMD Instinct MI350X Platform Datasheet](https://www.amd.com/en/products/accelerators/instinct/mi350/mi350x.html) | [原件](files/specs/amd-mi350x-platform.pdf) · [文本](text/amd-mi350x-platform.txt) | 8 GPU 平台、互联、容量与系统功率 |
| [Intel Gaudi 3 AI Accelerator White Paper](https://www.intel.com/content/www/us/en/content-details/817486/intel-gaudi-3-ai-accelerator-white-paper.html) | [原件](files/specs/intel-gaudi3.pdf) · [文本](text/intel-gaudi3.txt) | July 2025 V1 Rev.3；矩阵、可编程核、HBM 与以太互联 |
| [寒武纪思元 370 系列官方产品规格](https://cambricon.com/index.php?a=lists&c=index&catid=360&m=content) | [原件](files/specs/cambricon-mlu370.html) · [文本](text/cambricon-mlu370.txt) | 官方产品页；不能代替完整 ISA、微架构或后续代际规格 |
| [AWS Trainium2 Architecture](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/about-neuron/arch/neuron-hardware/trainium2.html) | [原件](files/specs/aws-trainium2.html) · [文本](text/aws-trainium2.txt) | 芯片规格；与 NKI 指南中 CC-Core 计数的口径差异单列 |
| [AWS Trainium3 Architecture](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/about-neuron/arch/neuron-hardware/trainium3.html) | [原件](files/specs/aws-trainium3.html) · [文本](text/aws-trainium3.txt) | 单芯片 NeuronCore、内存、DMA 与 NeuronLink 规格 |
| [Amazon EC2 Trn2 Architecture](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/about-neuron/arch/neuron-hardware/trn2-arch.html) | [原件](files/specs/aws-trn2-system.html) · [文本](text/aws-trn2-system.txt) | 实例、UltraServer、NeuronLink 拓扑和 EFA |
| [Amazon EC2 Trn3 UltraServers](https://aws.amazon.com/ec2/instance-types/trn3/) | [原件](files/specs/aws-trn3-system.html) · [文本](text/aws-trn3-system.txt) | 系统规格；整机 HBM、芯片数与单设备参数分开 |
| [Hot Chips 2026: SN50 RDU Dataflow at Scale](https://sambanova.ai/blog/hot-chips-2026-dataflow-at-scale) | [原件](files/documents/sambanova-sn50.html) · [文本](text/sambanova-sn50.txt) | 2026-09-02 厂商技术说明；模型推演与测量结果分别标注 |
| [SambaRack SN50 Official Product Description](https://sambanova.ai/products/sambarack) | [原件](files/specs/sambanova-sn50-system.html) · [文本](text/sambanova-sn50-system.txt) | 系统产品介绍，非完整 ISA 或全部产品参数手册 |
| [Inside NVIDIA Rubin GPU Architecture](https://developer.nvidia.com/blog/inside-nvidia-rubin-gpu-architecture-powering-the-era-of-agentic-ai/) | [原件](files/documents/nvidia-rubin-arch.html) · [文本](text/nvidia-rubin-arch.txt) | 2026-07-21 官方技术说明；与早期发布规格分开记录 |
| [NVIDIA Vera Rubin NVL72 Specifications](https://www.nvidia.com/en-us/data-center/vera-rubin-nvl72/) | [原件](files/specs/nvidia-rubin-system.html) · [文本](text/nvidia-rubin-system.txt) | 当前官方产品规格；部署形态、精度和供货状态分开 |
| [GroqRack Compute Cluster Product Brief v1.0](https://groq.com/papers/) | [原件](files/specs/groq-rack.pdf) · [文本](text/groq-rack.txt) | 官方整柜规格；历史 Groq 代际，与 NVIDIA Groq 3 LPX 分开 |
| [Serving Large Language Models on Huawei CloudMatrix384, v2](https://arxiv.org/abs/2506.12708v2) | [原件](files/papers/cloudmatrix384-v2.pdf) · [文本](text/cloudmatrix384-v2.txt) | 2025-06-18；§3.3.1 的 910C、§4.2.2 MLA 与动态 tiling；与 v3 分开保存 |
| [Serving Large Language Models on Huawei CloudMatrix384, v3](https://arxiv.org/abs/2506.12708v3) | [原件](files/papers/cloudmatrix384-v3.pdf) · [文本](text/cloudmatrix384-v3.txt) | 2025-06-19 修订；核对型号称谓与 v2 差异 |
| [昇腾 950 NPU 架构白皮书（官方下载原件）](https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf) | [原件](files/specs/ascend-950-official.pdf) · [文本](text/ascend-950-official.txt) | 作者提供官方 OBS 下载地址；与先前作者提供版本分别保留，差异核对见 UB-ASCEND-NOTES.md |
| [Efficiently Scaling Transformer Inference](https://arxiv.org/abs/2211.05102v1) | [原件](files/papers/scaling-inference.pdf) · [文本](text/scaling-inference.txt) | Google；推理计算／通信模型、TPU 分片与延迟—吞吐取舍；历史配置不直接套用 GPU |
| [Qwen3 Technical Report](https://arxiv.org/abs/2505.09388v1) | [原件](files/papers/qwen3.pdf) · [文本](text/qwen3.txt) | Alibaba 公司技术报告；稠密／MoE 配置与 thinking budget，不代填 Qwen3.5 参数 |
| [DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/abs/2501.12948v2) | [原件](files/papers/deepseek-r1.pdf) · [文本](text/deepseek-r1.txt) | 公司技术报告；RL 推理模型、长输出与采样负载；不视为 serving 性能报告 |
| [Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters](https://arxiv.org/abs/2408.03314v1) | [原件](files/papers/test-time-compute.pdf) · [文本](text/test-time-compute.txt) | DeepMind／Berkeley；按难度分配推理预算；计算量、质量与墙钟时间分开 |
| [Insights into DeepSeek-V3: Scaling Challenges and Reflections on Hardware for AI Architectures](https://arxiv.org/abs/2505.09343v2) | [原件](files/papers/deepseek-infra.pdf) · [文本](text/deepseek-infra.txt) | DeepSeek ISCA 2025 报告；MLA／MoE、跨节点通信及硬件协同设计建议 |
| [Day 6: DeepSeek-V3/R1 Inference System Overview](https://github.com/deepseek-ai/open-infra-index/blob/56d86855fcf6e08fdfd45ce6280bd24322c93351/202502OpenSourceWeek/day_6_one_more_thing_deepseekV3R1_inference_system_overview.md) | [原件](files/documents/deepseek-serving-report.md) · [文本](text/deepseek-serving-report.txt) | 2025 公司工程报告；固定提交；PD、EP、通信与费用口径 |
| [基于可编程网卡的高性能数据中心系统](https://01.me/files/pubs/bojieli-phd-thesis.pdf) | [原件](files/papers/bojieli-phd-thesis.pdf) · [文本](text/bojieli-phd-thesis.txt)（user_provided） | 李博杰博士论文，2019-05-26；ClickNP 核数预算、KV-Direct PCIe 并发与数据通路；论文测量按原配置引用 |
| [Huawei’s τ Chip Was Supposed to Melt?](files/papers/202609.00031v1.pdf) | [原件](files/papers/202609.00031v1.pdf) · [文本](text/logicfolding-energy.txt)（user_provided） | 何庭波，ChinaXiv:202609.00031v1，2026-09-04；片上连线、降压与功率密度；作者报告，AI 集群 80% 能耗说法待独立取证 |

## 获取记录

以下条目不能作为已经取得的完整资料：

- **ascend-c-architecture**：incomplete_text；动态文档页未包含硬件架构正文；另有完整 Ascend C PDF。
- **ub-spec-entry**：landing_only；入口不等于规范全文；2.0.1 另核。
- **ualink-spec-entry**：landing_only；完整规范的获取状态单列。
- **ub-base-201**：access_required；官网返回 HTTP 400，code=has_not_agreed，msg=has not agreed；正式版要求协议确认，未取得文件。

维护命令：`python3 references/fetch.py --only 资料ID` 下载指定条目；`--reindex` 只更新索引。直接运行会补齐失败或未获取的项目，保留已经下载的快照。需要 Python 3 和 Poppler 的 `pdftotext`、`pdfinfo`。
