# 推理框架近两年关键特性与章节对应

核对日期：2026-09-08。完成算子优化、推理和训练修改后，补查约 2024 年 9 月至 2026 年 9 月的官方公告与当前文档，并为分块调度补溯至 2024 年 5 月的 vLLM v0.4.2。本表是编辑和实验制作的对应记录；正文随负载、瓶颈与设计选择引入系统，没有新增框架介绍章。原件、日期与 SHA-256 见[框架演进来源](../references/outline-checks/2026-09-07/framework-evolution/sources.json)，DBO／EP／训练等实现另见[执行资料](../references/outline-checks/2026-09-07/execution-feedback/sources.json)。

## vLLM

| 变化与公开时间 | 本书要解释的设计问题 | 落点与实验 |
|---|---|---|
| v0.4.2（2024）实验性分块到 V1（2025 起）的统一请求进度；当前预算另受 KV／图等条件约束 | 相同 token 数为何不是相同工作量；prefill、decode、验证怎样共用预算 | 8.1，实验 8-1、8-2；[三个版本的源码与调优文档](../references/framework-history/2026-09-08/chunk-scheduling/README.md) |
| APC 与 V1 的缓存、logprob 语义 | 重复前缀减少多少工作；索取 prompt logprob 可能需要重算 | 8.2、10.5，实验 8-3、8-4、10-9 |
| 图执行：v0.6.0（2024）decode、v0.9.2（2025）分段、2025-08 双模式合入与 2026 固定分派 | 捕获范围、输入复制、batch 形状和后端约束怎样改变收益；异步提交另看关键路径 | 5.4、8.1，实验 5-8、8-2；[版本与源码](../references/framework-history/2026-09-08/graph-selection/README.md) |
| 通信路径：2024／2025 custom AR 与 2026 多后端及 AG／RS 扩展 | 小消息、注册缓冲、对称内存与拓扑怎样改变分派；操作支持、类名单和整套模型支持分别核实 | 6.4，实验 6-5；[固定版本与选读范围](../references/framework-history/2026-09-08/collective-paths/README.md) |
| 注意力后端及 FA 版本选择：2026 年 9 月实现核对，非首次发布日期 | 硬件代际、形状、KV 格式与确定性条件为何会改变内核及回退 | 4.2、5.2、8.1，实验 4-1、5-3、8-2 的同题对照 |
| 权重卸载：2024 按需搬入、2025 V1 UVA、2026 v0.17 选择性卸载与预取 | 权重放置、GPU 计算与 CPU 计算分别计量；扣除静态缓冲，再算每步链路流量和批量摊销 | 8.4→9.3，实验 8-7／9-3；[版本和算例](weight-offload-execution.md) |
| 预分片权重：v0.6.0（2024）、v0.9.2（2025）与 2026 固定加载器 | 用与部署匹配的 rank 文件减少重复逻辑读取；改 TP 的重分片、完整训练状态与推理加载各有条件 | 9.6→10.4，实验 9-10／10-6；[版本与源码](../references/framework-history/2026-09-08/checkpoint-loading/README.md) |
| 编译缓存、启动准备与图规格 | 稳态优化增加多少启动时间，短寿命副本何时合算 | 9.6、11.3，实验 9-10 的启动变体 |
| Wide EP、DBO、EPLB：2025–2026 | 每专家工作量、跨卡通信重叠与物理副本放置 | 9.4，实验 9-6 |
| 视觉执行：2024 单图实验接口、2025 v0.11.1 EC transfer、2026 固定 connector | 远程编码怎样从张量入口变成完整交接；多层视觉特征、EC 与 KV 分开计字节 | 3.1.4→8.1→9.2／9.5→12.2，实验 12-3／8-2／9-10；[算例与比较](multimodal-stage-placement.md) |
| 分离式 prefill 与 KV connector | 阶段资源分工和 KV 交接如何形成完整服务 | 9.2、9.5，实验 9-2、9-7 |
| 原生 KV offload：2026 年 1 月回顾 v0.9／0.11／0.12，固定当前多级后端 | 连续块、CPU 中转、共享范围与选择性写入怎样影响取回和下一轮前缀；不是权重卸载 | 5.2→8.2→9.5，实验 9-7／9-9；[版本与算例](cache-tiers-and-routing.md) |
| 推测执行：2024 多 token 槽位、2025 草稿训练接入、2026 并行起草与动态验证 | 接受计数、草稿布局、图成本与按负载选预算；静态区间表和置信度调度各有条件 | 8.3，实验 8-5／8-6；[版本与量化对照](speculative-execution.md) |
| AFD Plugin：2026 年 7 月实验性发布 | attention 与 FFN 独立部署、逐层交接、图与微批约束 | 9.3、9.6，实验 9-4、9-10 |
| Sleep Mode | RL 两阶段怎样释放显存，哪些权重和 KV 必须恢复或重建 | 10.5，实验 10-8 |
| Batch invariance：v0.12.0（2025）与 2026 固定主线 | 同一请求改变 batch 后的数值，如何关联归约、采样与训练概率 | 5.1→8.1→10.5，实验 5-1／10-9；[版本对照](../references/framework-history/2026-09-08/rl-consistency/README.md) |
| 结构化生成：2025 V0 接入 XGrammar，2026 固定 manager／backend | 预处理、编译缓存和 CPU 掩码怎样进入采样关键路径；reasoning／推测回滚需同步状态 | 8.1／8.3→11.1，实验 8-2；[版本与计算](structured-generation.md) |

依据：[V1 官方指南](https://docs.vllm.ai/en/stable/usage/v1_guide/)、[大规模服务公告](https://vllm.ai/blog/2025-12-17-large-scale-serving)、[AFD](https://vllm-project.github.io/2026/07/23/vllm-afd-plugin.html)、[Sleep Mode](https://docs.vllm.ai/en/latest/features/sleep_mode/)。这不是说所有特性都在 V1 发布当日具备。

AFD 的当前公告展示 DeepSeek V2／V3 家族等 wrappers，GPU／NPU connector 的阶段与图模式不同。部分结果使用强制均衡、缩层或逻辑规模模拟，改变模型输出；只用来研究机制，不能视为完整 V4／K3 的等质量线上收益。其他 current／nightly 文档也是获取日快照，实验必须固定实际提交。

## SGLang

| 变化与公开时间 | 本书要解释的设计问题 | 落点与实验 |
|---|---|---|
| v0.4：2024 年 12 月，CPU／GPU 重叠、缓存感知路由与结构化输出 | 减少主机等待，兼顾前缀复用与队列；语法约束也有执行成本 | 8.1、9.5，实验 8-2、9-9 |
| 推测执行：2025 MTP 到 2026 Spec V2／DSpark | 主机与 GPU 重叠、目标特征投影、按请求截短验证、图档位与 DP 约束 | 5→8.3，实验 8-5／8-6；[固定来源](../references/framework-history/2026-09-08/speculative-execution/README.md) |
| 2025 GB200 权重预取与 KT 集成预览，2026 固定通用 offloader／KT wrapper | 搬权重和 CPU 就地算专家各自受什么限制；同层并行与 Expert Deferral 的质量条件分开 | 8.4、9.3，实验 9-3／9-5；[实际实现](../references/framework-history/2026-09-08/offload-execution/README.md) |
| EPD：2026 年 1 月公告与固定当前指南 | 独立编码的卡数、延迟与图像配比；传输后端和全局 EC 缓存各自解决什么问题 | 3.1.4→9.2／9.5→12.2，实验 12-3／9-10；[版本证据](../references/framework-history/2026-09-08/multimodal-execution/README.md) |
| HiCache：2025 年 9 月与 2026 固定设计／PD 配置 | 实例私有 host 与条件式共享存储、预取终止、decode 状态写入；取回和重算怎样选择 | 9.5，实验 9-7／9-9／9-8；[层次与路由](cache-tiers-and-routing.md) |
| TBO／SBO、DeepEP 和 EPLB；补 2025 H100→GB200 与 2026 固定操作路径 | 互联改变后重新权衡切分效率、通信等待与并发争用；热点放置另算 | 9.4，实验 9-6；[历史与当前实现](../references/framework-history/2026-09-08/overlap-placement/README.md) |
| HiSparse：2026 年 4 月 | 稀疏访问不等于完整历史容量已消失；按需搬入的 IO 代价 | 2.4 与 9.5 衔接，实验 9-8 的条件扩展 |
| Unified Radix Cache：2026 年 8 月 | V4 滑窗／压缩、K3 循环状态与全注意力共用前缀身份，但复用边界不同 | 8.2、9.5，实验 8-4、9-8 |
| Breakable CUDA Graph：2026-02 PR、04 月合入及 prefill 扩展；08 月全图说明 | 显式 eager 边界及输入复制、token／request padding、捕获上限与峰值内存 | 5.4、8.1，实验 5-8、8-2；[日期与采用范围](../references/framework-history/2026-09-08/graph-selection/README.md) |
| 分阶段 attention backend：2026 年 9 月实现核对，非首次发布日期 | prefill、decode、推测验证为什么可能选择不同内核；图与元数据怎样跟随 | 5.2→8.1，实验 8-2 的可选后端对照 |
| AllReduce＋残差＋RMSNorm：2026 年 9 月实现核对，非首次发布日期 | 减少启动和中间搬运，同时保持归约组、残差与布局；混合 EP×TP 为什么限制跨层融合 | 5→6.4，实验 6-5；[实际接口与 benchmark 说明](../references/framework-history/2026-09-08/collective-paths/README.md) |
| 确定性推理：2025 年 9 月公告与 2026 当前指南 | chunk 边界、归约切分、前缀缓存和请求种子怎样共同影响复验；与 Routing Replay 各解决什么问题 | 5.1→8.1→10.5，实验 10-9；[状态与数值案例](rl-state-and-reproducibility.md) |

依据：[v0.4](https://www.lmsys.org/blog/2024-12-04-sglang-v0-4/)、[HiCache](https://www.lmsys.org/blog/2025-09-10-sglang-hicache/)、[EP 文档](https://docs.sglang.io/docs/advanced_features/expert_parallelism)、[HiSparse](https://www.lmsys.org/blog/2026-04-10-sglang-hisparse/)、[Unified Radix Cache](https://www.lmsys.org/blog/2026-08-11-unified-radix-cache/)、[CUDA Graph](https://www.lmsys.org/blog/2026-08-17-advanced-cuda-graph/)。

HiSparse 公布的支持路径是 DSA（含 V3.2 与 GLM-5.1），不能直接推广到 V4／K3。Unified Radix Cache 则明确讨论 V4 和 K3 的不同组合；其 MAMBA 组件名称描述复用机制，不代表 K3 模型变成 Mamba。BCG 原始代码发布、合并、prefill 扩展与文章日期分开，正文只用版本化机制，不强调“首创”排名。相关吞吐与 TTFT 倍数都保留原负载条件，未写成本书实测。

## Ollama

| 变化与公开时间 | 本书要解释的设计问题 | 落点与实验 |
|---|---|---|
| 多模态新引擎：2025 年 5 月 | 图片编码、投影、缓存与语言模型前向分工 | 5.5、12.1，实验 12-2 |
| JSON schema：2024 年 12 月与 2026 获取日指南 | 普通 JSON、结构约束与消费端验证各做什么；本地入口与 Cloud 支持分开 | 8.1→11.1，实验 8-2 的本地对照；[采用范围](structured-generation.md) |
| 流式工具调用：2025 年 5 月 | 首段文字、完整参数与工具真正可执行的时刻不同 | 11.1，实验 11-1 |
| 容量规划：2024 预测、2025 分阶段分配反馈、2026 主线 runner 分工 | 上下文、并发和图缓冲怎样改变装入层数；实际路径与容量预测分别核实 | 5.5、8.4，实验 8-7；[三期源码](../references/framework-history/2026-09-08/overlap-placement/README.md) |
| v0.30 GGUF：2026-05 release／06 月公告，当前层放置与内存报告 | llama-server 自动 GPU 层、projector 单独放置、mmap 计量；驻留比例不能代替阶段耗时 | 8.4，实验 8-7；[发布与源码](../references/framework-history/2026-09-08/offload-execution/README.md) |
| MLX 预览：2026 年 3 月 | Apple 后端与量化格式改变了访存和执行路径 | 5.5、8.4，实验 8-7 的后端对照 |
| MLX 选择性状态快照：2026 年 6 月 | Agent 分支、删除旧 reasoning 后的续接与滑窗／循环状态恢复边界 | 8.2.4，实验 8-4；[公告原件](../references/framework-history/2026-09-08/speculative-execution/ollama-mlx-performance-2026.html) |
| Ollama 0.31 的 Gemma 4／MLX MTP：2026 年 6 月 | 动态草稿长度、状态回滚、2–8 token 验证时的权重复用 | 8.3，实验 8-5、8-6 的本地对照 |

依据：[多模态引擎](https://ollama.com/blog/multimodal-models)、[流式工具](https://ollama.com/blog/streaming-tool)、[内存调度](https://ollama.com/blog/new-model-scheduling)、[MLX 预览](https://ollama.com/blog/mlx)、[本地 MTP](https://ollama.com/blog/faster-gemma-4-mlx-mtp)。

MLX 预览的比较同时改变了 NVFP4 与 Q4_K_M，不能把整个加速归因于后端；该发布的机器与模型限制也不代表所有 Ollama 安装。MTP 的收益来自具体支持模型、草稿与内核，不能推广成所有量化文件均支持。旧版固定 Metal 源码仍作历史路径证据，新路径另行固定版本。图像编码缓存只在图片与处理条件相同时复用，Computer Use 每轮变化的截图要重新判断。

## 实验的制作约束

长期调研补读 MLSys 2024 的 Punica／S-LoRA，将共享基座、多 adapter 批处理和状态容量接到 8.2；用当前 vLLM／SGLang 支持与 Ollama 的 ADAPTER 入口对照，避免沿用旧论文对早期引擎的限制。[阅读与推算](multi-lora-serving.md)保留论文条件；完整逐版本历史仍在[持续调研](../research/2026-infra-survey/README.md)。

MLSys 2025 的四篇重点阅读补上了变化之间的联系：FlashInfer v0.2 的 plan/run 为 5.4 的动态图执行提供具体实现；Marconi 的混合状态准入与淘汰接到 8.2 的 Unified Radix Cache；KV 压缩评估补 8.4 的自然输出长度与任务质量；Rubick 把第 6、10 章的执行方案选择接到第 11 章的资源调度。版本和算例见[状态与执行取舍](cache-and-reconfiguration.md)。这些是同题比较，不声称当前框架直接继承所有论文实现。

MLSys 2026 首批阅读进一步把 MoE 实际执行接回第 6 章的切分估算：独立活跃专家、后端 padding 和逐层副本预算共同决定第 9 章的放置。另用 vLLM v0.10.1.1 的启动分解，对照当前固定提交的编译缓存设计，解释“多做准备换稳态效率”的适用寿命。历史实验、当前实现边界与 Qwen3 算例见[专家与启动取舍](moe-and-startup.md)，没有将 CRAFT 当作已合入当前框架的特性。

每个实验先做资源预算，再选一套真实系统作为基线，改变一个机制；第二套系统仅在模型、精度和任务能对齐时比较。命令、提交、形状、质量门槛、原始记录及图表脚本随实验提供。本轮完成特性调研和大纲落点，没有安装这些 GPU 栈、下载模型权重或运行性能实验。未具备设备的读者分析同一份真实记录，而不是另一套假装复现系统的小模拟器。

MLSys 2026 余卷补读 FA4 后，将代际演进落实到一个可算的 attention tile，再检查 vLLM 两级选择和 SGLang 的分阶段 wrapper。上游 FA4、框架 wrapper 和当前服务默认分开记录；同名算法不能保证相同执行、支持范围或确定性行为。来源见[固定实现](../references/framework-history/2026-09-08/attention/README.md)，第 4→5→8 章的计算和实验衔接见[内核与训练效率](kernel-and-fleet-efficiency.md)。Google TPU 的 MPG 研究只补第 10、13 章的完成时间口径，不归成三个推理框架的新特性。

本文筛选影响资源、数据流、调度、状态和交互时间的变化。模型名单更新、产品集成入口和单个 bug 修复不逐条铺进正文；随着扩写继续按这些问题核对新版本，避免让章节变成 release notes。

OSDI 2025 的 NanoFlow 与 FuseLink 补上两个反例：切小 batch 或增加 NIC 都不自动提高完整服务速度，必须计入重复读取、并发争用和共享链路。SGLang 的 H100／GB200 选择与 Ollama 的三期加载路径用来检验这一方法，见[资源共享与放置](resource-sharing-and-placement.md)。研究插件、当前主线和正式安装版本分别记录，没有将 FuseLink 写成框架默认功能。

RL 问题调研又把确定性路径接回同一主线：第 5 章说明切分改变数值，第 8 章说明连续批处理怎样触发，第 10 章才讨论概率、路由与样本版本。vLLM 的同硬件／同版本边界、SGLang 历史 Dense 到当前 MoE 示例的变化，以及 AReaL 更新权重后的 KV 重建，见[原始资料](../references/framework-history/2026-09-08/rl-consistency/README.md)。不把同一引擎可重复误写成所有引擎、硬件与训练过程逐位一致。

OSDI 2026 的 Weave／RobustRL 继续检验这些接口如何组成 RL 系统：前者在 ROLL 上交错安排多个作业，后者在 verl＋vLLM 路径上按角色恢复。10.5→11.3 用[阶段与恢复计算](rl-scheduling-and-recovery.md)连接 sleep／唤醒、状态保存和权重交接；只将论文实际实现归给研究系统，不将跨作业调度、动态恢复能力直接归为引擎默认功能。 NSDI 2026 的 RollPacker 再用 ROLL＋vLLM 0.8.4＋Megatron 区分取消请求、迁移后 KV 重建与整批最终更新。[长尾算例](rollout-tail-and-sampling.md)同时检查额外执行量和样本选择；固定作者源码的完成组包含奖励与过滤，不能把“先完成”只理解为生成速度。研究系统机制与当前引擎默认支持分开。

OSDI 2026 全卷摘要筛完后，GraCE 补充逐图段的性能选择。5.4 的地址与边界复制接到 8.1 的动态 bucket 和图池，再用 9.6 的副本寿命判断准备成本。vLLM 当前分派、SGLang BCG 与 GraCE 实测选择并非相同机制，见[计算与实验变体](graph-execution-tradeoffs.md)；没有把旧 PyTorch 2.4 基线的不足写成所有当前框架的问题。

NSDI 2024 首批筛读用 rPCIeBench 和 MegaScale 深化路径与等待，再回到 vLLM 的历史 custom AR、当前分派和 SGLang 层间融合。第 6 章的消息大小接到第 7 章的窗口与 rank 就绪，最后由第 10 章的固定 batch 扩展与恢复收回，见[采用与计算](collective-paths-and-diagnosis.md)。论文的 Gen3／Ampere 条件和旧 Megatron 基线保留；不将研究系统归成推理框架的新功能。

NSDI 2025 的 ByteCheckpoint 选读与 PyTorch 2024／2025／2.14 对照补入 10.4，说明快照、后台保存、全局分片坐标与恢复语义；vLLM 的预分片加载在 9.6 作对照。PyTorch DCP 是训练基础组件，这段不归为 vLLM／SGLang／Ollama 自带的完整检查点能力。见[布局与时间线](checkpoint-layout-and-loading.md)。

NSDI 2025 的 AutoCCL 则把第 6 章的通信配置接回实际并发片段。对照 NCCL 2025 调优／2.28 公告与 2026 的 2.31.2 接口和注册条件，说明局部覆盖、逐操作配置、chunk 回调以及 CE／CPU proxy 怎样改变资源占用。它们是底层库与研究 fork 的能力，vLLM／SGLang 的真实分派仍按已核框架条件判断；不把安装新版库等同启用所有优化。见[通信取舍与实算](communication-tuning.md)。

NSDI 2026 的 ServeGen 为这些框架实验补充负载依据：全局相同的 QPS 和长度分布，不能替代客户组成、多轮间隔与时段需求。第 3 章先算，第 9 章用 vLLM／SGLang 检验实例和 PD 配比，第 11 章计入准备时间；[案例与生成入口核对](workload-and-provisioning.md)区分论文方法、当前开源入口和教学假设。ServeGen 不属于推理引擎的新特性，也不能直接生成完整的 Agent 工具轨迹或真实前缀缓存行为。

推测执行的版本比较进一步将第 5 章的形状与图执行接到 8.3：P-EAGLE 的并行草稿仍有额外元数据和行数，Spec V2 减少主机间隙，DSpark 的动态验证只有落到更小执行图才真正节省矩阵工作。[四请求算例](speculative-execution.md)保留接受率定义、截短后的未观察尾部、DP 共享档位和成本表的上下文范围。Ollama 的分支快照与 MTP 回滚作为本地例子，支持范围按实际模型／runner 记录。

权重卸载用[同一组矩阵](weight-offload-execution.md)把版本变化接回容量与服务能力：预取缓冲会占回一部分显存，更多请求摊薄权重流量却不自动缩短步间隔；KT 的 CPU 专家随批量增大可能转为计算受限。PR 的 dummy 权重、单输出 prefill 测试、混合精度和每卡归一化均单独说明。后续多模态阶段已读完 vLLM-Omni DLO 文章与声明范围的 backend；评估条件留在研究笔记，没有为此新增生成模型小节。

多模态的后续阅读由一张截图串起三个框架与 TriInfer：2024 的 embedding 输入不是分离服务，2025 的 EC 生命周期接到 2026 的独立编码与全局缓存。Qwen3-VL-4B 的 400 个视觉位置产生含 DeepStack 的 7.8125 MiB EC，语言 KV 另算；[四卡算例](multimodal-stage-placement.md)解释缓存命中后为什么链路或 PD 会先成为瓶颈。Ollama 的本地投影／位置处理按模型执行，不强加同一分布式功能。

第 6→7 章的底层通信对照再补主机中转：TCCL 作者资料与固定实现说明 NUMA 放置也属于路径选择，NCCL 2.31.2 文档和分配函数提供当前机制的核对。先辨认 vLLM／SGLang 实际分派，再读 transport；`SHM/direct` 不能判为 GPU 间 P2P。四卡 Qwen3 矩阵的[流量推算](pcie-staging-and-numa.md)沿用实验 6-6；正式 TCCL PDF 未取得，未采用论文性能数字，也没有把底层库的演进列为三个框架共同新增的功能。

第 5.3 的后续阅读用 Korch 说明拆分算子后再组合 kernel 的选择，随后回到 vLLM v0.6.0 的 SiluAndMul 和当前 activation-quant pass。Qwen3 同一 FP8 变体的[逻辑流量与生存期计算](kernel-orchestration-and-quantization.md)分别给出读写减少和活动张量峰值变化。实验以实际图与 trace 判断融合，避免将关闭 custom pass 误判为没有 Inductor 融合；Korch 的旧视觉模型测量只作历史反例，不描述当前推理引擎的性能。

动态 EP 补查将三个时间尺度接在一起：已有副本的 token 分派、专家权重重排、运行中改变组规模。SGLang 2026 Waterfill／LPLB 和 vLLM Elastic EP 的文章、合入日期及固定源码见[专家分派与重配](expert-dispatch-and-resizing.md)；只在 9.4、9.6、11.3 增补原有实验变体。Qwen3 离线算例不冒充当前 LPLB 的可运行模型，单输出 token 的历史测试不当作长 decode 结论。

KV 量化的版本比较接回 8.4.4：vLLM 从 2024 scalar-scale 文档到 2026 Attention 融合／分层选择，SGLang 从 2025 FP4 存储到当前分阶段访问，Ollama 从早期 KV 选项到当前后端入口。用同一 Qwen3 请求计算格式、scale、工作区，再判断转换成本，见[算例](kv-quantization-and-execution.md)与[固定资料范围](../references/framework-history/2026-09-08/kv-quantization/README.md)。沿用实验 8-8，不增加框架功能节。

2026-09-09 多 LoRA 复核补上代表版本的准入语义：vLLM 2024 逐请求到 2025 动态加载和固定 2026 文档入口，SGLang 2025 前缀身份／CSGMV 到 2026 加载重叠与排空；Ollama 三期 adapter 变更重载作为不同服务方式的对照。[读取范围与合入日期](../references/framework-history/2026-09-09/lora-admission/README.md)分别记录；Inkling 的 B200 W4A16 TP8 专用双流实现不能推广给全部模型。四请求算例比较平均与最晚完成时间，接现有实验 8-3，不新增工具介绍节。
