# 从业务要求推算推理与训练系统

本笔记用于第 8–11 章的贯穿案例。模型形状沿用[模型与算子核对](model-operator-examples.md)及[并行推算](model-parallelism.md)，不另造一套抽象模型。这里固定推算输入、公开证据和实验问题；完整实验与实测数据随正文扩写制作。

## 三类请求与两类训练任务

第 9、10 章使用同一套请求，并在第 11 章把生成部分接入 rollout。以下数字是便于第一遍手算的教学起点，不是生产分布的统计结论。随后必须换成长短混合、到达突发和工具等待记录。

| 业务 | 初始输入 | 要回答的问题 |
| --- | --- | --- |
| 交互问答 | Qwen3-8B；2,048 输入、256 输出 token；并发从 1 扫到 4、16、64 | 权重读取怎样被摊薄，KV 和等待何时限制 batch；首 token 与逐 token 期限能否同时满足 |
| 文档与代码 Agent | 同一 Qwen3-8B 作可运行起点，再替换 Qwen3-235B-A22B／V4-Flash；8,192-token 输入中先设 6,144-token 可复用前缀，每轮生成先设 1,024 token | 复用前缀、reasoning 长度和工具等待怎样改变 PD 配比、缓存位置与整项任务耗时 |
| 实时语音 | 端侧采集／检测、ASR、Qwen3-8B 对话、TTS；模型版本取 Queqiao 配套记录，另固定可复现实验配置 | 每块音频的积累、上传、识别、生成和播放能否按时衔接；中断后有哪些无效计算 |
| 领域继续训练 | Qwen3-8B，先给 100B 有效 token 与 30 天期限，再改 token 预算和全参数／LoRA 范围 | 容量、总工作、供数、互联及故障分别需要多少资源；小数据微调与从头训练差在哪里 |
| 大规模预训练与 RL | Qwen3-235B／V4-Flash 逐层计数；V4-Pro／Kimi K3 分别计总状态与实际计算；V4 RL 接生成、验证、教师与更新 | 总参数、激活路径、训练 token 与有效样本不能相互替代；未披露阶段采用显式情景，不虚构产品总成本 |

每轮比较都交付：逐卡与主机容量、阶段工作和字节、关键路径、可承载负载、质量与完成时间。再改变一个业务或硬件条件，重新选择。服务的并发请求数、引擎某一步的活跃 batch、每个专家收到的 token 数是三个不同输入。

## 硬件替换改变了哪项约束

H100／4090 保留作者历史文章的问题。A100／A800 用于隔离互联差异，H20 用于检验“推理卡”称呼与实际任务是否一致，H100／H200／B200 用于分开理解算力、容量、带宽和互联的代际变化。

- **A100／A800：** [Lenovo 原厂指南](../references/outline-checks/2026-09-07/systems-cases/a800-lenovo.pdf)首页明确比较 NVLink 600／400 GB/s。其表列 A800 80 GB PCIe／SXM 的 HBM 带宽分别为 1,935／2,039 GB/s，BF16 dense 为 312 TFLOP/s。与[对应 A100 数据表](../references/files/specs/nvidia-a100-80-spec.pdf)同形态对齐，不能把 NVLink 削减写成 HBM 削减。只引用本例需要的项目；端口双向聚合规格还需换算为实际路径有效单向带宽。
- **H20：** [NVIDIA 的固定产品支持表](../references/files/specs/nvidia-h20-vgpu.html)可确认本例 H20 SXM5 96 GB；本轮仍未获得可完整核对的官方算力／带宽表。H20 训练是否合算采用具体 GEMM、训练步和 P／D 服务率记录推算，未测项目保留区间。[Bullet](../references/files/papers/bullet.pdf)含 A100／H20 的 SM 与访存实验、Qwen3 服务案例，可作为原条件证据，不能拼成 A100＋H20 异构 PD 的实测。
- **H100／B200：** [H100 规格](../references/files/specs/nvidia-h100-spec.html)的 80 GB SXM 与[HGX B200 表](../references/outline-checks/2026-09-07/systems-cases/nvidia-hgx.html)分开核对。HGX B200 的 8 卡 BF16 表值 36 PFLOP/s 含结构稀疏，dense 为一半，即每卡 2.25 PFLOP/s。[DGX B200](../references/files/specs/nvidia-dgx-b200.html)的 1,440 GB／8 卡对应本例每卡 180 GB；不混入 GB200 的形态与容量。[H200](../references/outline-checks/2026-09-07/systems-cases/nvidia-h200-systems.html)的容量和带宽增长另由其官方规格解释。

若用稳态总步时得到的 MFU 估计训练时间，其中已经包含该计时区间的通信、重计算和气泡影响，不再重复叠加。若从计算、访存、通信分别建模，则先组合执行时间，再反算 MFU。跨卡比较先统一算法 FLOPs、精度与 dense／structured-sparse 峰值口径；MoE 路由稀疏不等于 Tensor Core 的 2:4 结构稀疏。

缺少 H20 同条件测量时，也能先算业务门槛：将约 8B Dense、100B token 的矩阵代理值暂取 `6×8B×100B`，若要求 16 卡在 30 天内完成，平均每卡需要约 115.7 TFLOP/s 的有效算法进度。随后用具体训练步判断 H20 是否达到、差多少、加卡是否受互联或 batch 限制；这个门槛不是 H20 规格或性能声明。

## “最大能训练多大”怎样计算

先确定模型族、数据量、训练目标、卡数、可用时长与并行拓扑。容量给出能否容纳状态的约束，计算与通信给出能否按期完成的约束。对混合精度 Adam 的教学初算，持久状态可暂取 16 byte／参数；真实优化器、分片与复制再改写该数。

以 Dense 的矩阵计算代理值 `C ≈ 6ND` 作第一遍期限估算：`T ≈ C / (G × F_dense × MFU)`。它承接第 3 章的粗估范围，之后补注意力、辅助分支等；MoE 则从每层实际执行矩阵求 C，用总参数求存储。目标模型不是越大越好，扩大参数后需要怎样的数据预算由 scaling law 与质量目标决定。

为了回答 1T、5T、10T 的说法，设 **16,384 卡、20T 训练 token、BF16 dense、50% MFU**，保持这些条件不变。以下是计算情景，1T／5T／10T 为假设 Dense 规模，不冒充已有模型配置或真实训练计划。

| Dense 参数规模 | A100 SXM，312 TFLOP/s | H100 SXM，989 TFLOP/s | B200 SXM，2,250 TFLOP/s |
| --- | ---: | ---: | ---: |
| 1T | 543.4 天 | 171.4 天 | 75.4 天 |
| 5T | 2,717.0 天 | 857.1 天 | 376.8 天 |
| 10T | 5,434.0 天 | 1,714.3 天 | 753.5 天 |

这组估算尚不构成容量与通信可行性的证明，也不是供应商训练速度。它说明：在相同规模与精度下，代际峰值的倍数不会自动变成任意倍数的可训练模型规模。再分别改变卡数、90／180 天期限、MFU 30%／40%／50%，以及固定 D 或让 D 随 N 增长，得到不同的边界曲线。50% 是本题的较乐观起点，不是所有模型、精度、集群都应达到的常数。

容量也先算一笔：16 byte／参数时，1T／5T／10T 的持久状态为 16／80／160 TB。逐组检查这些状态在 TP、PP、DP／ZeRO、EP 下放到哪里；直接除以全部卡数会掩盖副本、激活峰值和通信工作。换 FP8／FP4 训练还要证明方法支持与质量，不把推理量化权重大小套到优化器状态。

## MacBook 上的数百 B 模型

用作者的 M2 Max 96 GB 与 Qwen3-235B-A22B 作待验证案例。先看真实文件，再算内存：已固定[Unsloth 文件元数据](../references/outline-checks/2026-09-07/systems-cases/qwen235-gguf-metadata.json)，`UD-Q2_K_XL` 全部 GGUF 分片合计 **88,014,818,560 bytes，约 81.97 GiB**，而不是直接按“2 bit × 235B”得到 58.75 GB。

由元数据逐文件相加，解释分组 scale、较高位宽矩阵、格式和填充对实际平均位宽的影响；精确参数数量与文件头可进一步分解，不能只从文件名反推。随后为系统、工作区、KV 和并发留空间。每条 8,192-token 序列的 BF16 GQA KV 约 1.47 GiB，沿用第 6 章结果；实际后端若压缩 KV 则重算。96 GB 是整机统一内存，CPU 与 GPU 不各有一份。

对照[Unsloth R1 原始案例](https://unsloth.ai/blog/deepseekr1-dynamic)和[本轮文件元数据](../references/outline-checks/2026-09-07/systems-cases/unsloth-r1-metadata.json)：固定版本 `DeepSeek-R1-UD-IQ1_S` 分片合计 **140,231,438,464 bytes，约 130.60 GiB**。原文“131GB”的展示口径与精确字节须分开；不能据此承诺完整权重驻留 128 GiB MacBook。若项目采用 mmap、分页或 SSD，需计算每步未命中字节、有效随机读取与冷启动。也不能反过来把所有本地大模型部署都认定为极端量化。

“保留全部层和专家”“保留原始权重精度”“达到相近任务质量”分别验证。低比特 PTQ、量化感知训练、蒸馏和专家裁剪各自对应不同的结果，不能笼统称“满血”。长推理、代码测试和长上下文任务的质量、退化与重复都进入比较；能输出一个示例只是运行证据。

## 少量 GPU 与大型主机内存

以固定提交的 KTransformers 文档逐一还原实例，不把一篇文档内不同机器的成绩合并：

- [V4-Flash 教程](../references/outline-checks/2026-09-07/systems-cases/kt-v4.md)给出单 RTX 5090 32 GB、至少 200 GB 主存的配置；路由专家由 CPU／GPU 分担，较长 prefill 可按层搬到 GPU。分别核算专家 DRAM 读取、CPU 算力、激活交接和新增 GPU 缓冲。
- [Kimi K2 教程](../references/outline-checks/2026-09-07/systems-cases/kt-kimi2.md)给出 Q4_K_M、约 600 GB 主存、14 GB 显存的资源量级，示例最大 batch 为 4。这个明确版本不能替代 Kimi K3 的证据，也不能概括为只能 batch＝1。
- 原有 RTX 4090＋双 Xeon Gold 6454S 的 KT-Kernel 案例继续用于 AMX、NUMA 和专家调度；SOSP 论文的机器单独引用。V4 教程中的 MTP 对比属于 8×5090，不能作为单卡速度。

从低到高扫描到达率与并发，统计批内专家集合及每专家 token 数。同一专家被多 token 使用会增加复用，但活跃专家集合也可能扩大，读取不能简单固定为一个 token 的激活参数。比较 CPU 执行专家、按需搬权重、热点专家留 GPU 与全 GPU 驻留；最终用满足质量和延迟的 requests/s、每项成功任务成本和整机能耗评价。

batch＝1 的低矩阵利用率可能由交互期限决定，并不自动等于浪费；数据中心 GPU 也需要足够负载和合适批处理才可摊薄费用。反过来，少量 GPU 的演示成本不能省略主机、DRAM、SSD、功耗和长 prefill。对同一业务，找到本地、异构服务器和全 GPU 服务之间随到达率变化的选择条件。

## 推测解码的近期案例

基础只用一幅草稿—验证时序说明；主案例采用 [EAGLE 3.1](../references/outline-checks/2026-09-07/systems-cases/eagle31.html)、[DFlash 论文](../references/outline-checks/2026-09-07/systems-cases/dflash-paper.pdf)及[固定仓库](../references/outline-checks/2026-09-07/systems-cases/dflash-readme.md)、[DFlash 2](../references/outline-checks/2026-09-07/systems-cases/dflash2.html)、[MiMo／TileRT 官方说明](../references/outline-checks/2026-09-07/systems-cases/mimo-tilert.html)和 DeepSeek-V4 的 MTP。EAGLE 团队与小米 MiMo 分别归属；引擎里的 EAGLE 选项也可能执行模型自带的 MTP，需检查实际草稿来源。

Qwen3-8B 的 DFlash 提供与前文相连的小规模实验。EAGLE 3.1 的 Kimi K2.6、DFlash 2 的近期模型、MiMo-V2.5-Pro 与 V4 则各自保留目标、草稿、精度和机器条件，不能把跨论文加速比当同条件排名。

按记录计算 `总耗时 / 最终产出 token 数`，或在平稳循环下估计 `E[草稿＋验证＋提交/回退时间] / E[产出 token 数]`。产出包含实际提交的草稿及目标补偿 token，记录中避免重复计数。接受率、接受长度和速度不是同一量。

EAGLE 3.1 用输入归一化与反馈状态变化解释长上下文草稿稳定性；DFlash 用并行草稿减少串行等待，DFlash 2 进一步分析候选路径选择和局部卷积的成本。MiMo 展示 FP4、SWA 草稿与执行系统的共同影响；V4 按报告保留 MTP 设计，其运行收益用具体后端记录补足。严格验证保持的是所选目标模型的采样分布，不意味着低比特目标与原精度目标相同，也不保证浮点逐位一致。

用推理阶段占 Agent 总时长的比例检验宣传数字：即使 decode 提速 4 倍，若它原先只占任务一半，总任务理想加速也只有 `1/(0.5+0.5/4)=1.6` 倍。再加入草稿显存挤占 batch、CPU 专家验证流量和多用户排队，解释开关策略为什么需要随负载调整。

## 本轮证据状态

原件、文件元数据和固定提交的 SHA-256 见[本轮来源清单](../references/outline-checks/2026-09-07/systems-cases/sources.json)。只下载报告、文档、代码与元数据，没有下载大模型权重或启动昂贵训练。Unsloth 历史博客经网页工具阅读，直接归档返回 403；本地另存其模型卡和精确文件元数据，保留获取失败记录。硬件效果与项目速度均按作者原条件使用，本书尚未完成性能复测。
