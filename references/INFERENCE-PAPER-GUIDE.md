# LLM 推理资料选读与写作落点

整理日期：2026-09-06；对应十三章、91 节蓝图。这是作者写作时的查阅索引，围绕书中要解释的问题选择证据。正文仍按资源约束、执行过程和系统取舍推进，论文在具体机制、数据或历史归属需要依据时出现。

本轮对照已有 203 项资料，新增 **22 篇论文 PDF 和 3 份官方工程资料**，全部取得正文。总库现在为 **228 项、224 项取得正文、134 份 PDF**。本页按写作问题精选 **49 项资料**，包含 24 项已有核心资料与本轮 25 项新增资料。首次提交集中于 2017–2025 年，另纳入 2026 年的报告修订与工程文章；这不是截至今日所有论文的穷尽清单，也不是按引用次数或 GitHub stars 排出的榜单。

[机器可读的章节与论点映射](inference-reading-map.tsv) · [本轮新增论文 BibTeX](inference-additions.bib) · [全库索引](README.md) · [版本、下载和校验记录](manifest.json)

## 选择与阅读顺序

选择依据是：是否建立可复用的资源／执行模型，是否解释已经进入主流实现的机制，是否提供公司系统的具体设计与测量，是否能补齐现有蓝图的证据。核心来源包括原始算法、系统论文和作者技术报告；综述及二手文章仅作检索线索，不作为这里的论证依据。

- **核心**：写对应小节前优先阅读方法和实验条件，通常只在正文保留一项关键机制或一张重绘示意图。
- **专题**：出现相应问题再查；用于比较条件、解释反例或编写习题，不要求正文逐篇介绍。
- **工程**：用于核对具体系统职责与部署行为，按官方文档或工程文章引用，不改称学术论文。

优先阅读可按五组问题推进：Pope 的推理模型与 MQA／GQA；FlashAttention 与 FlashInfer；Orca、PagedAttention、Sarathi-Serve 与 SGLang；投机解码两篇基础工作与 KIVI；DistServe、Splitwise、Mooncake、Preble 及 DeepSeek 基础设施报告。模型报告在相应配置和部署问题出现时穿插阅读。

**阅读深度**：本轮核对了新增 PDF 的标题、版本与可提取正文，定向查看了下表的机制、图表或实验入口；已有论文按相关小节回查。不是逐页精读或复现实验。所有 PDF 页码指本地文件从第一页起的物理页序；节号优先于页码。已视觉抽查投机采样 Algorithm 2（p.3）、StreamingLLM 滚动缓存 Figure 4（p.5）和 Pope 资源模型（p.3）；其他公式与图表在正式引述时仍须回看原页。

## 先确定写法，再选择引文

| 蓝图位置 | 从什么问题切入 | 资料怎样融入 | 合适的写作产物 |
| --- | --- | --- | --- |
| 第 2 章；3.1–3.2；第 4 章 | 一个 token 需要什么计算、状态与数据移动？ | Transformer、MQA／GQA／MLA 给出结构依据；Pope 帮助组织算存通信模型；模型报告提供配置 | 同一模型的 prefill／decode 资源账表，按层类型核算 |
| 3.4；13.2 | 多想一会儿增加了什么资源需求？ | test-time compute 与 R1 的证据用于说明候选、验证和长输出；Qwen3 用于预算控制例子 | 质量—执行量—墙钟时间三者分开的案例 |
| 5.1–5.2、5.5、5.7 | 相同计算为什么因实现不同而快慢不同？ | FlashAttention 支撑 IO 推导；FlashInfer 支撑布局、动态调度与图复用；量化论文支撑误差处理 | 一张执行时间线、一个流量复算；实测继续使用 Apple／NVIDIA 主线 |
| 9.1–9.4、9.7 | 并发请求怎样共享容量并减少相互阻塞？ | Orca、vLLM、Sarathi、SGLang 各负责一个机制；FastServe 补抢占的代价 | 用同一组长短请求逐步比较分配、批处理、复用与尾延迟 |
| 9.5 | 多做草稿为什么可能减少延迟？ | 基础论文给出采样正确性和成本条件；Medusa、EAGLE 作为扩展 | 接受长度与验证成本的条件式算例，不列加速比排行榜 |
| 9.6 | 长上下文中哪些状态能压缩或淘汰？ | KIVI、H2O、StreamingLLM 分别解释量化与两种淘汰思路 | 状态字节、额外执行和质量测量的并列表 |
| 10.1–10.4 | 何时切模型，何时拆阶段？ | DistServe／Splitwise 支撑 PD；DeepSeek／CloudMatrix／KTransformers 支撑不同粒度的专家分工 | 延续 A100＋H20 与 4090＋双路 Xeon 既有案例，明确收益被通信抵消的条件 |
| 10.5–10.7 | 请求和 KV 应去哪里，丢失后如何恢复？ | Mooncake、Preble、LMCache 解释缓存与路由；Dynamo 提供工程例子 | 请求与状态的生命周期图；恢复保证另查固定实现 |
| 12.3；13.3 | 多个服务如何共享机器？ | AlpaServe 与 S-LoRA 分别解释多模型和多 adapter 复用；Dynamo 补冷启动 | 模型放置、容量预留及冷启动成本的算例 |

上述是编辑建议，不是论文作者对本书案例的实验结论。现有章节顺序和两组硬件案例继续沿用，无需新增“相关工作”章。

## 需求与资源模型

| 资料与优先级 | 章内位置／查阅入口 | 可支撑的内容 | 引用边界 |
| --- | --- | --- | --- |
| **核心** · [Efficiently Scaling Transformer Inference](https://arxiv.org/abs/2211.05102v1) · [原件](files/papers/scaling-inference.pdf) · [文本](text/scaling-inference.txt) · 新增 | 3.1,4,10.1,13.3；§2–3；PDF pp.2–7 | 从权重、KV、计算与集合通信分别记账，解释增加芯片后延迟与单位成本为何不同时改善 | PaLM／TPU v4 历史条件；忽略注意力 FLOPs 的近似不适用于所有长上下文算例 |
| **核心** · [Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures](https://digicoll.lib.berkeley.edu/record/136692) · [原件](files/papers/roofline.pdf) · [文本](text/roofline.txt) | 4,13.1；Roofline 模型及 operational intensity 定义 | 先估算运算强度与供给，再用实测有效带宽校准 | 单算子上界不能直接代替排队与端到端延迟 |
| **专题** · [Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters](https://arxiv.org/abs/2408.03314v1) · [原件](files/papers/test-time-compute.pdf) · [文本](text/test-time-compute.txt) · 新增 | 3.4,13.2；Figure 1；§5–7 | 将多候选、修订、验证器等执行量计入推理预算，比较不同问题难度下的分配 | 特定模型与数学任务；FLOPs 最优不等于交互延迟最优 |

## 模型结构与公司报告

| 资料与优先级 | 章内位置／查阅入口 | 可支撑的内容 | 引用边界 |
| --- | --- | --- | --- |
| **核心** · [Attention Is All You Need](https://arxiv.org/abs/1706.03762) · [原件](files/papers/transformer.pdf) · [文本](text/transformer.txt) | 2；§3；Figure 1 | 从依赖关系推导训练与 prefill 的并行空间，再说明自回归 decode 的串行性 | 避免把数学注意力矩阵等同于必须物化的中间张量 |
| **核心** · [Fast Transformer Decoding: One Write-Head is All You Need](https://arxiv.org/abs/1911.02150) · [原件](files/papers/mqa.pdf) · [文本](text/mqa.txt) | 2,9.1；Incremental Inference 及性能实验 | 用 KV head 数变化复算状态字节和读取量 | 原实验质量结论不外推到所有任务和架构 |
| **核心** · [GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints](https://arxiv.org/abs/2305.13245) · [原件](files/papers/gqa.pdf) · [文本](text/gqa.txt) | 2,9.1；§2；Figure 2 | 在 MHA 与 MQA 之间引入 KV 分组，连到容量和并行切分 | 质量、uptraining 条件与推理实现分别引用 |
| **核心** · [DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model](https://arxiv.org/abs/2405.04434) · [原件](files/papers/deepseek-v2.pdf) · [文本](text/deepseek-v2.txt) | 2,9.1；Multi-Head Latent Attention 小节 | 按实际缓存的潜变量与位置相关分量核算 MLA 状态 | 不能只用压缩维度代替全部状态，也不能假设每种后端均执行相同吸收路径 |
| **核心** · [DeepSeek-V3 Technical Report](https://arxiv.org/abs/2412.19437) · [原件](files/papers/deepseek-v3.pdf) · [文本](text/deepseek-v3.txt) | 2,3,10.1,11,13；§2.2；§3.4–3.5，PDF pp.18–20 | MTP、推理部署及硬件建议分别接到草稿验证、EP 和协同设计 | 训练 FP8、推理精度、费用估算是不同口径；MTP 不自动等于无代价多 token 输出 |
| **核心** · [The Llama 3 Herd of Models](https://arxiv.org/abs/2407.21783) · [原件](files/papers/llama3.pdf) · [文本](text/llama3.txt) | 2,5,10.1,13；§3.2；§6.1–6.2，PDF pp.51–53 | 把 GQA 模型配置、流水并行和 FP8 推理连成公司部署案例 | 该报告的推理方案不代表所有 Llama 服务；记录 405B、设备和精度条件 |
| **专题** · [Qwen3 Technical Report](https://arxiv.org/abs/2505.09388v1) · [原件](files/papers/qwen3.pdf) · [文本](text/qwen3.txt) · 新增 | 2,3.4,13.2；§2；§4.3、§4.7 | 用稠密／MoE 型号和 thinking budget 解释模型结构、输出长度与资源需求 | 仅支持 Qwen3；Qwen3.5 使用自己的配置与报告 |
| **专题** · [Mixtral of Experts](https://arxiv.org/abs/2401.04088v1) · [原件](files/papers/mixtral.pdf) · [文本](text/mixtral.txt) · 新增 | 2,10.4；§2；§5，PDF pp.2、7–8 | 分开总参数、每 token 激活参数与实际专家负载；利用路由分析组织算例 | 激活参数节省不能按同倍率折算驻留容量或通信 |
| **专题** · [DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/abs/2501.12948v2) · [原件](files/papers/deepseek-r1.pdf) · [文本](text/deepseek-r1.txt) · 新增 | 3.4,11,13.2；PDF p.4 的训练中回答长度与准确率曲线；Methods | 解释推理型模型的长输出、RL 采样与预算变化 | 本地是 2026-01-04 v2；首次提交为 2025；训练曲线不是在线用户长度分布 |
| **核心** · [Insights into DeepSeek-V3: Scaling Challenges and Reflections on Hardware for AI Architectures](https://arxiv.org/abs/2505.09343v2) · [原件](files/papers/deepseek-infra.pdf) · [文本](text/deepseek-infra.txt) · 新增 | 6,10.3,10.4,13；§2.1–2.3、§4–5 | 将 MLA／MoE 的算存需求与多平面网络、硬件设计建议放在同一案例中核算 | 公司经验与设计建议分别表述，不能当作所有系统的必要架构 |

## 算子与低精度

| 资料与优先级 | 章内位置／查阅入口 | 可支撑的内容 | 引用边界 |
| --- | --- | --- | --- |
| **核心** · [FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](https://arxiv.org/abs/2205.14135) · [原件](files/papers/flashattention.pdf) · [文本](text/flashattention.txt) | 2,5.1,5.2；§3.1–3.2，PDF pp.4–6 | 在注意力推导后计算分块、融合与重计算减少的 HBM 访问 | 精确注意力算法；不声称消除全注意力的二次计算量 |
| **专题** · [FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning](https://arxiv.org/abs/2307.08691) · [原件](files/papers/flashattention2.pdf) · [文本](text/flashattention2.txt) | 5.1,5.2；§3 的 work partitioning | 同一个数学算子，用线程块和 warp 分工解释有效算力变化 | 架构与形状相关，不能累乘不同论文的加速比 |
| **专题** · [FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-precision](https://arxiv.org/abs/2407.08608) · [原件](files/papers/flashattention3.pdf) · [文本](text/flashattention3.txt) | 5.2；Asynchrony、Warp Specialization、Low-precision 相关小节 | 把异步搬运、矩阵计算与 softmax 放到执行时间线上 | Hopper 实现结论不直接移植到 Apple 或昇腾 |
| **核心** · [FlashInfer: Efficient and Customizable Attention Engine for LLM Inference Serving](https://arxiv.org/abs/2501.01005v2) · [原件](files/papers/flashinfer.pdf) · [文本](text/flashinfer.txt) · 新增 | 5.5,5.7,9.4；§3.1–3.3，PDF pp.4–7 | 解释 KV 物理格式、可组合注意力、动态调度和图执行之间的接口 | 引擎论文固定快照，不替代当前支持列表和内核代码 |
| **专题** · [LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale](https://arxiv.org/abs/2208.07339v2) · [原件](files/papers/llm-int8.pdf) · [文本](text/llm-int8.txt) · 新增 | 5,9；§3.1–3.2、§4 | 通过激活异常值说明混合精度分解的必要性，再核算存储与额外运算 | INT8 权重容量节省不等于矩阵乘或服务的同比加速 |
| **核心** · [GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers](https://arxiv.org/abs/2210.17323) · [原件](files/papers/gptq.pdf) · [文本](text/gptq.txt) | 5,9；量化算法与实验部分 | 解释离线权重量化误差补偿，连到本地部署的模型质量检查 | 量化算法论文不能证明任意 GGUF／CUDA 内核的实际吞吐 |
| **核心** · [AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration](https://arxiv.org/abs/2306.00978) · [原件](files/papers/awq.pdf) · [文本](text/awq.txt) | 5,9；Activation-aware Weight Quantization 与 TinyChat 部分 | 区分权重量化选择和真正执行低比特算子的系统支持 | 必须同时记录量化格式、group size 和硬件后端 |
| **核心** · [SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models](https://arxiv.org/abs/2211.10438) · [原件](files/papers/smoothquant.pdf) · [文本](text/smoothquant.txt) | 5,9；§3 的 smoothing 变换与 W8A8 实验 | 说明将激活量化难度转移到权重的等价变换和校准 | 校准集、量化后误差与硬件支持仍需验证 |

## 单实例状态与调度

| 资料与优先级 | 章内位置／查阅入口 | 可支撑的内容 | 引用边界 |
| --- | --- | --- | --- |
| **核心** · [Orca: A Distributed Serving System for Transformer-Based Generative Models](https://www.usenix.org/conference/osdi22/presentation/yu) · [原件](files/papers/orca.pdf) · [文本](text/orca.txt) | 9.3；Iteration-level Scheduling、Selective Batching | 用一张请求时间线解释按迭代补入和移出请求 | 历史系统中的 selective batching 不等于今天所有引擎的具体实现 |
| **核心** · [Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180) · [原件](files/papers/vllm.pdf) · [文本](text/vllm.txt) | 9.1,9.2；§4.1，PDF p.5 起；memory sharing 部分 | 用逻辑块到物理块映射推导碎片、共享与 copy-on-write | PagedAttention 不改变模型数学所需的逻辑 KV 数量；论文不代表当前 vLLM 全部架构 |
| **核心** · [Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve](https://arxiv.org/abs/2403.02310) · [原件](files/papers/sarathi-serve.pdf) · [文本](text/sarathi-serve.txt) | 9.3,9.7；§4.2–4.3，PDF pp.8–9 | 沿 prefill 与 decode 时间线分析 chunk 大小和 token budget | 分块会增加调度／执行开销，吞吐与 TTFT／TPOT 要联合测量 |
| **专题** · [DeepSpeed-FastGen: High-throughput Text Generation for LLMs via MII and DeepSpeed-Inference](https://arxiv.org/abs/2401.08671v1) · [原件](files/papers/deepspeed-fastgen.pdf) · [文本](text/deepspeed-fastgen.txt) · 新增 | 9.3,9.7；§3.2、§4.1，PDF pp.5–6 | 以 Dynamic SplitFuse 为另一种分块组合实现，并借用 effective throughput 的测量问题 | 2024 年对照版本和请求分布必须保留，不引用为今天的引擎排名 |
| **核心** · [SGLang: Efficient Execution of Structured Language Model Programs](https://arxiv.org/abs/2312.07104) · [原件](files/papers/sglang.pdf) · [文本](text/sglang.txt) | 9.2,10.5；§3，PDF pp.4–5；§6.3 | 用 RadixAttention 的前缀组织连接请求程序、KV 复用与调度 | 论文初版功能范围与现在的 SGLang 运行时分开；相同文本不必然满足 KV 复用条件 |
| **专题** · [FlexGen: High-Throughput Generative Inference of Large Language Models with a Single GPU](https://arxiv.org/abs/2303.06865) · [原件](files/papers/flexgen.pdf) · [文本](text/flexgen.txt) | 8,9.2；Offloading Strategy、Block Schedule 与实验 | 在权重／KV／激活之间选择卸载对象，计算搬移、驻留与批量的取舍 | 面向吞吐的离线条件不能当成低延迟交互结论 |
| **专题** · [DeepSpeed Inference: Enabling Efficient Inference of Transformer Models at Unprecedented Scale](https://arxiv.org/abs/2207.00032v1) · [原件](files/papers/deepspeed-inference.pdf) · [文本](text/deepspeed-inference.txt) · 新增 | 5,9.2,10.1；§III–VI：内核、多 GPU 与 ZeRO-Inference | 比较 GPU 驻留、模型并行和 CPU／NVMe 卸载三种执行路径 | 历史模型、硬件与延迟目标分别保留 |
| **专题** · [Fast Distributed Inference Serving for Large Language Models](https://arxiv.org/abs/2305.05920v3) · [原件](files/papers/fastserve.pdf) · [文本](text/fastserve.txt) · 新增 | 9.7,12.3；§4.1 Skip-Join MLFQ Scheduler；KV 管理 | 说明输出长度未知时，抢占策略如何平衡短请求和状态交换 | 平台作业抢占与单服务内部请求抢占不能混为一谈 |

## 长上下文与KV压缩

| 资料与优先级 | 章内位置／查阅入口 | 可支撑的内容 | 引用边界 |
| --- | --- | --- | --- |
| **核心** · [KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache](https://arxiv.org/abs/2402.02750v2) · [原件](files/papers/kivi.pdf) · [文本](text/kivi.txt) · 新增 | 9.6；§3.1–3.3；量化误差与 residual cache | 按 K per-channel、V per-token 展开低比特存储，并补 scale、zero point 和残余段 | 2 bit 是量化数据位宽，不是整个 KV 分配的平均精确位宽；质量需按任务验证 |
| **专题** · [H₂O: Heavy-Hitter Oracle for Efficient Generative Inference of Large Language Models](https://arxiv.org/abs/2306.14048v3) · [原件](files/papers/h2o.pdf) · [文本](text/h2o.txt) · 新增 | 9.6；§3–4，PDF pp.4–6 | 用近期 token 与 heavy hitter 的保留策略解释 KV 淘汰 | 近似改变可访问历史；理论保证附带假设，不等于所有模型无质量损失 |
| **专题** · [Efficient Streaming Language Models with Attention Sinks](https://arxiv.org/abs/2309.17453v4) · [原件](files/papers/streamingllm.pdf) · [文本](text/streamingllm.txt) · 新增 | 2,9.6；§3.2，PDF p.5，Figure 4；§4.3 | 用 attention sinks 与滚动窗口说明固定容量的流式状态 | 旧 token 已淘汰；稳定生成不等于完整长历史理解或检索 |

## 投机解码

| 资料与优先级 | 章内位置／查阅入口 | 可支撑的内容 | 引用边界 |
| --- | --- | --- | --- |
| **核心** · [Fast Inference from Transformers via Speculative Decoding](https://arxiv.org/abs/2211.17192) · [原件](files/papers/speculative-decoding.pdf) · [文本](text/speculative-decoding.txt) | 9.5；§2.3、§3.1–3.4；Theorem 3.8 | 从草稿成本、接受长度和目标模型验证成本推导何时加速 | 期望加速公式依赖接受率及成本假设；高并发服务需重新测量 |
| **核心** · [Accelerating Large Language Model Decoding with Speculative Sampling](https://arxiv.org/abs/2302.01318v1) · [原件](files/papers/speculative-sampling.pdf) · [文本](text/speculative-sampling.txt) · 新增 | 9.5；PDF p.3 Algorithm 2；后续拒绝校正证明 | 与 Leviathan 等并列说明独立提出的分布保持采样机制 | 目标分布一致不等于浮点逐位一致或同随机种子输出一致 |
| **专题** · [Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads](https://arxiv.org/abs/2401.10774v3) · [原件](files/papers/medusa.pdf) · [文本](text/medusa.txt) · 新增 | 9.5；§2.1–2.3，尤其 §2.3.1 Typical Acceptance | 多头候选与树形验证作为扩展，比较 backbone 冻结与联合训练 | typical acceptance 与严格拒绝采样的保证不同，不能统称精确采样 |
| **专题** · [EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty](https://arxiv.org/abs/2401.15077v3) · [原件](files/papers/eagle.pdf) · [文本](text/eagle.txt) · 新增 | 9.5；特征预测方法、草稿结构及消融 | 解释特征层草稿为何需要处理下一 token 的不确定性 | 训练代价、草稿长度和服务负载一并记录 |
| **专题** · [EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test](https://arxiv.org/abs/2503.01840v3) · [原件](files/papers/eagle3.pdf) · [文本](text/eagle3.txt) · 新增 | 9.5；§3.2；§4.3，PDF pp.5、8 | 在基础推导后补多层特征、training-time test 和 SGLang 集成案例 | 采用论文中的 batch 与模型条件；不把单请求收益当成整机吞吐收益 |

## 分布式推理与生产系统

| 资料与优先级 | 章内位置／查阅入口 | 可支撑的内容 | 引用边界 |
| --- | --- | --- | --- |
| **核心** · [DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving](https://arxiv.org/abs/2401.09670) · [原件](files/papers/distserve.pdf) · [文本](text/distserve.txt) | 10.2；§3–4：disaggregation 与 placement | 从 TTFT／TPOT 的干扰提出 PD 分离，并把 KV 交接与池配比加回成本 | 分离收益取决于链路、放置、请求分布和 SLO |
| **核心** · [Splitwise: Efficient Generative LLM Inference Using Phase Splitting](https://arxiv.org/abs/2311.18677) · [原件](files/papers/splitwise.pdf) · [文本](text/splitwise.txt) | 10.2,13.3；Phase Splitting、Cluster Design 与评估 | 在 A100／H20 案例前借用按阶段匹配资源的分析方法 | 论文机器组合与本书异构组合不同，不能照搬性能数值 |
| **核心** · [Mooncake: A KVCache-centric Disaggregated Architecture for LLM Serving](https://arxiv.org/abs/2407.00079) · [原件](files/papers/mooncake.pdf) · [文本](text/mooncake.txt) | 3.2,10.2,10.5,10.6；§4、§6–7；PDF pp.6–7、10–14 | 将真实请求分布、缓存局部性、传输与过载拒绝连成系统案例 | 公司负载的统计特征不能代替本书服务的 trace |
| **核心** · [Preble: Efficient Distributed Prompt Scheduling for LLM Serving](https://arxiv.org/abs/2407.00023v2) · [原件](files/papers/preble.pdf) · [文本](text/preble.txt) · 新增 | 10.5；§3.2–3.3，PDF pp.4–7 | 在跨副本前缀共享场景比较缓存命中与排队成本 | 缓存命中最大化不是全局延迟最小化；必须考虑状态更新成本 |
| **核心** · [LMCache: An Efficient KV Cache Layer for Enterprise-Scale LLM Inference](https://arxiv.org/abs/2510.09665v2) · [原件](files/papers/lmcache.pdf) · [文本](text/lmcache.txt) · 新增 | 9.2,10.6；§3–5；§8.5；§9 | 把 KV 作为独立存储层讨论，连接格式转换、批量 I/O、分层缓存和 PD | 跨实例复用要求模型、位置、前缀和格式等条件相容；一致性与恢复不能由下载论文自动补齐 |
| **核心** · [Day 6: DeepSeek-V3/R1 Inference System Overview](https://github.com/deepseek-ai/open-infra-index/blob/56d86855fcf6e08fdfd45ce6280bd24322c93351/202502OpenSourceWeek/day_6_one_more_thing_deepseekV3R1_inference_system_overview.md) · [原件](files/documents/deepseek-serving-report.md) · [文本](text/deepseek-serving-report.txt) · 新增 | 6,10.2,10.4,13.3；System Design Principles；Large-scale Cross-node EP；统计与费用段落 | 以生产工程报告检查 EP 扩大批量、通信重叠和负载均衡的共同条件 | 固定 Git 提交；理论租用成本估算不等于公司利润或完整 TCO |
| **专题** · [Serving Large Language Models on Huawei CloudMatrix384, v3](https://arxiv.org/abs/2506.12708v3) · [原件](files/papers/cloudmatrix384-v3.pdf) · [文本](text/cloudmatrix384-v3.txt) | 4,6,10.3,10.4；系统架构、Attention／FFN 分离与评估；型号差异回看 v2 | 用另一硬件体系检验 MoE 放置与通信分析；复用已有架构笔记 | 硬件型号措辞在 v2／v3 有变化，参数必须注明版本 |
| **核心** · [KTransformers: Unleashing the Full Potential of CPU/GPU Hybrid Inference for MoE Models](https://madsys.cs.tsinghua.edu.cn/publication/ktransformers-unleashing-the-full-potential-of-cpu/gpu-hybrid-inference-for-moe-models/SOSP25-chen.pdf) · [原件](files/papers/ktransformers-paper.pdf) · [文本](text/ktransformers-paper.txt) | 5.8,10.3；系统设计、CPU 专家执行与 Evaluation 设置 | 为既有 4090＋双路 Xeon 案例解释专家就地计算与 CPU／GPU 交接 | 论文实验配置与当前官方示例不同；同机协作不自动证明跨机 AF 收益 |
| **工程** · [How NVIDIA Dynamo 1.0 Powers Multi-Node Inference at Production Scale](https://developer.nvidia.com/blog/?p=113961) · [原件](files/documents/dynamo-production.html) · [文本](text/dynamo-production.txt) · 新增 | 10.5,10.7,12.3；ModelExpress、KV-aware router、resilient inference 相关段落 | 用于写部署、状态复用、扩缩容及恢复的具体工程例子 | 2026-03-16 官方文章；性能数值是厂商报告，完整恢复语义仍需代码与实验 |
| **工程** · [TensorRT LLM Architecture Overview](https://nvidia.github.io/TensorRT-LLM/developer-guide/overview.html) · [原件](files/documents/tensorrt-llm-architecture.html) · [文本](text/tensorrt-llm-architecture.txt) · 新增 | 5,9.4,10.1；Architecture Overview 正文 | 解释 API、执行器与后端的职责，和 vLLM／SGLang 的实现边界比较 | 动态官方文档按 SHA-256 保存；不把它标作项目论文 |

## 多模型服务与平台

| 资料与优先级 | 章内位置／查阅入口 | 可支撑的内容 | 引用边界 |
| --- | --- | --- | --- |
| **专题** · [S-LoRA: Serving Thousands of Concurrent LoRA Adapters](https://arxiv.org/abs/2311.03285v3) · [原件](files/papers/s-lora.pdf) · [文本](text/s-lora.txt) · 新增 | 9,12.3；§4–6；Unified Paging | 从多个 adapter 共享基座引出异构批处理、状态分页和适配器放置 | 不是多个独立基座的通用复用；租户隔离、公平性需额外验证 |
| **专题** · [AlpaServe: Statistical Multiplexing with Model Parallelism for Deep Learning Serving](https://arxiv.org/abs/2302.11665v2) · [原件](files/papers/alpaserve.pdf) · [文本](text/alpaserve.txt) · 新增 | 10.1,12.3；§3.4；§4；PDF p.6 的排队分析 | 解释模型并行带来的统计复用机会，联合选择模型放置和副本 | 论文的服务对象与负载模型不等于完整现代 LLM 连续批处理服务 |

## 开源项目与论文的对应关系

| 项目 | 本地证据 | 写作时的定位 |
| --- | --- | --- |
| vLLM | PagedAttention 论文；既有 CUDA Graph 设计文档 | 状态管理的基础机制与当前图执行实现分开引用 |
| SGLang | SGLang 论文；EAGLE-3 的集成实验 | 原论文侧重结构化程序与 RadixAttention；后来的 PD／EP／内核能力另查固定版本 |
| FlashAttention／FlashInfer | 三代 FlashAttention；FlashInfer 论文 | 算法、硬件执行和推理注意力引擎分别说明 |
| DeepSpeed／MII | DeepSpeed Inference；DeepSpeed-FastGen | 分别支撑并行／卸载与 Dynamic SplitFuse |
| Mooncake／LMCache | 同名系统论文／报告 | 分布式服务架构与独立 KV 存储层各有职责，不视为同一层替代品 |
| KTransformers | SOSP 论文与既有固定提交文档 | 论文配置、当前示例配置和本书实测各自登记 |
| EAGLE／Medusa | 同名论文和 EAGLE-3 | 草稿训练、验证组织与采样规则分别引用 |
| S-LoRA／AlpaServe | 同名系统论文 | 分别用于多 adapter 与多模型复用的专题 |
| TensorRT-LLM／Dynamo | 本轮官方架构页／生产技术文章 | 本轮使用工程原件，不虚构一篇覆盖整个项目的“对应论文” |
| llama.cpp／MLX／Ollama | 已有官方 README、API 和固定代码快照 | 继续用于本地执行路径；不强行为每个项目寻找论文替身 |

## 引述内容的实际用法

**资源模型。** 正文可以先写“同一步执行既要读取权重，也要访问随上下文增长的 KV；小批量和长上下文下，占主导的读取对象可能不同”，在该判断之后引用 Pope 的 §2。随后用本书模型、精度和设备参数复算。论文中的 TPU 时间不直接填入 RTX 案例。

**分页。** 在解释“逻辑 KV 数量没有减少，但未使用预留与分配碎片可以减少”之后引用 PagedAttention，再画一个请求跨多个物理块的示意图。这里需要的是内存管理机制，不需要回顾所有 KV 管理论文。

**投机解码。** 先定义一次迭代产出的已提交 token 数 K，以及草稿、验证、校正与提交开销。对长时间运行，在可应用更新奖励比值的条件下，用 `平均每 token 时间 ≈ E[迭代耗时] / E[K]` 组织测量；采用独立同分布接受率等简化时，再引用 Leviathan 等的推导。Chen 等的 Algorithm 2 支撑拒绝校正的分布保证。Medusa 的 typical acceptance 单列规则，不能承接同一个精确性结论。

**PD／缓存。** 从既有 A100＋H20 案例提出“分离缓解阶段干扰，但引入 KV 交接与两阶段排队”，引用 DistServe／Splitwise。只有当案例出现跨副本前缀共享时，才引入 Preble／Mooncake；出现外置缓存层再查 LMCache。

这些示例均为拟议的中文转述，不是从论文摘录的原句；正式正文选定版本、模型和参数后再补最终引文。

## 仍需补证的内容

- 系统性能比较必须固定模型、量化格式、输入输出分布、到达过程、缓存冷热、设备、引擎提交和 TTFT／TPOT 目标。旧论文的“最快”及倍数仅属于原实验。
- 本轮补齐机制来源，没有替代本书的 Apple／NVIDIA 实测，也没有补出昇腾实机数据。跨平台与异构案例的缺项继续见 [GAPS.md](GAPS.md)。
- KV 复用和恢复须补模型／adapter 版本、位置编码、精度、块格式、隔离与失效规则；论文原理不能证明某个版本的接口或故障保证。
- 既有 2025–2026 模型报告继续通过 [训练计算量案例](../case-studies/training-compute.md)查阅。没有因报告更新就替换已固定算例；本轮 R1 明确保存 v2，其他已有快照未重新下载。
- 新增 BibTeX 只覆盖这次 22 篇 arXiv 论文，作者来自 arXiv 元数据，版本由 URL 和 note 固定。全库统一书目、正式出版会议信息与最终页码在正文引用确定后整理，避免凭记忆补写。

## 归档核验

新增 25 项全部取得正文：22 个 PDF，1 个固定提交 Markdown，2 个官方 HTML 快照。原件署名和版权说明保留；可搜索文本另存。新增 PDF 检查了签名、页数、非空文本和 arXiv 版本；全部新增原件按 manifest 中的 SHA-256 校验。网页不是整站镜像，外链图片与脚本不保证离线可用。此前 4 个非完整正文条目保持原状态，本轮没有新增获取缺口。
