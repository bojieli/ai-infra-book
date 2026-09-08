# 框架演进的章节覆盖复核

核对日期：2026-09-08。以下落点已按[草案 22 的当前章节](../../outlines/chapters.json)和小节内容重新核对：单实例／分布式推理为第 8／9 章，训练为第 10 章，运行环境为第 11 章，端边云为第 12 章。逐项时间、提交与读取范围保留在[框架对应记录](../../case-studies/framework-evolution.md)；这里检查主线是否连通，不将取样版本视为完整发布史，也不将计划中的实验记为已运行。

| 读者需要作出的判断 | 已有框架对照与计算 | 章节与实验落点 |
| --- | --- | --- |
| 减少主机提交，是否值得增加准备和显存占用？ | vLLM 图模式演进、SGLang BCG；[图形状、padding 和捕获预算](../../case-studies/graph-execution-tradeoffs.md) | 5.4 执行准备→8.1.5 动态批次与图重放→9.6.2 部署寿命；实验 5-8、8-2、9-10 |
| 同样的 token 预算，为何仍会干扰交互请求？ | vLLM 分块到统一进度，SGLang 重叠；[前后 chunk 的不同历史工作](../../case-studies/chunking-and-state-transfer.md) | 3.1 推理负载→8.1.4 分块执行→9.2 PD；实验 8-2、9-2 |
| 减少生成步骤，实际节省了多少执行？ | vLLM 并行起草／动态验证、SGLang Spec V2／DSpark、Ollama 状态快照；[接受计数、实际图行数与回滚](../../case-studies/speculative-execution.md) | 5.4 执行准备→8.3 推测执行，RL 的概率要求接 10.5；实验 8-5、8-6、10-9 |
| KV 位宽降低以后，容量和执行各改善多少？ | vLLM FP8 Attention、SGLang 分阶段配方、Ollama block 格式；[数值、scale、工作区和转换交点](../../case-studies/kv-quantization-and-execution.md) | 8.4.4 KV 压缩与模型状态；实验 8-8／图 8-7 |
| 标为四位的模型，是否真的按四位保存和执行？ | M²XFP 伪量化与专用架构分开；vLLM v0.12.0 的 MoE 路径到固定当前 Linear 在线量化；[权重、激活与实际表示](../../case-studies/kernel-orchestration-and-quantization.md) | 4.2.5 格式与计算→5.3 融合／生存期→8.4 容量与质量；实验 4-2／5-4，图 4-3 |
| 前缀匹配之后，能够从哪里恢复？ | vLLM 混合状态准入与部分块、SGLang 统一树、Ollama 选择性快照；[K3 逐卡检查点、保留间隔与尾段重算](../../case-studies/hybrid-prefix-state.md) | 2.4 模型状态→8.2 前缀复用→9.5 跨层身份与复用；实验 8-4／图 8-3 |
| adapter 已注册，为何请求仍进不了批次？ | vLLM 三期接口、SGLang 分组／前缀／异步加载／排空，以及 Ollama 三期重载条件；[容量、分组和等待](../../case-studies/multi-lora-serving.md) | 5 小矩阵分块→8.2.2 共享与准入；实验 8-3／图 8-2。专用 Inkling B200 路径和通用接口分开 |
| 能放下模型以后，能服务多少请求？ | vLLM 权重预取、SGLang CPU 专家协同、Ollama 加载反馈；[权重、KV、缓冲和链路分别计量](../../case-studies/weight-offload-execution.md) | 8.4 压缩与卸载→9.3 AF；实验 8-7、9-3、9-5 |
| 哪些状态值得保存，应该把请求送到哪里？ | vLLM 原生 offload、SGLang HiCache／Model Gateway、Ollama 模型保留与状态寿命；[取回、排队与重算](../../case-studies/cache-tiers-and-routing.md)，以及[事件、位置与尾延迟](../../case-studies/cache-events-and-routing.md) | 5.2 缓冲寿命→8.2 状态复用→9.5 KV 层次与路由；实验 8-4、9-7、9-8、9-9 |
| 模型并行估算怎样变成实际执行？ | vLLM／SGLang 通信分派、MoE 重叠、专家副本及[分派／动态重配](../../case-studies/expert-dispatch-and-resizing.md)；[共享资源](../../case-studies/resource-sharing-and-placement.md)、[专家实际工作](../../case-studies/moe-and-startup.md)与 ArcticInference 的[并行切换状态条件](../../case-studies/parallel-switching-and-state.md) | 6 超节点→7 数据中心网络→9.4 专家放置／9.6 部署，训练接 10.3；实验 6-2、6-5、9-6、9-10 |
| 图片或工具参数加入后，关键路径改变在哪里？ | vLLM／SGLang 编码交接、Ollama 本地入口；[截图的阶段与字节](../../case-studies/multimodal-stage-placement.md)、[语法准备与采样汇合](../../case-studies/structured-generation.md) | 第 3 章先定义 E→P→D；8.1／9.1 处理执行条件，11.1 处理工具任务，12.1／12.2 再改变网络和位置；实验 8-2、9-10、11-1、12-2、12-3 |
| 推理引擎接进 RL，还缺哪些状态与一致性条件？ | vLLM／SGLang 确定性、休眠和权重交接；[概率、路由与 KV 版本](../../case-studies/rl-state-and-reproducibility.md)，以及[阶段峰值与分片权重交接](../../case-studies/weight-handoff.md)；研究系统负责跨角色协调 | 5.1／5.4 执行语义→8.1 服务条件→10.5 RL 闭环→11.2／11.3 环境及调度；实验 10-8、10-9、11-4、11-5 |
| 历史匹配能否换成有效产出？ | vLLM 2024 prompt lookup、2025 Arctic 插件提议及 2026 suffix 入口，SGLang NGRAM；[确定性草稿、索引成本与 RL 供给](../../case-studies/history-drafts-and-rollout.md) | 8.3.1 每轮收支→10.5.3 阶段配比；实验 8-5、10-8 |
| 相同利用率意味着相同瓶颈吗？ | 昇腾单元分析与固定 vLLM Ascend 激活／310P 分支；[Qwen3 字节、缓冲及活动时间分解](../../case-studies/component-utilization-and-overlap.md) | 4 单元组织→5.2.3 重叠→5.3.5 反馈；实验 5-6／图 5-5。论文算子库声明、框架入口和依赖内核尚未一一对应 |
| 恢复之后还缺哪些数据？ | 固定 E2B memfile→缺页复制，与 CXLfork 只读共享／写时复制对照；[环境驻留和首次访问](../../case-studies/snapshot-residency-and-first-use.md) | 11.1 容量→11.2 恢复；实验 11-2／图 11-3。CPU 进程与 microVM、论文原型与云端版本分别说明 |
| 自动优化的分数能否换成部署收益？ | LOOPRAG／DarwinGame 的 CPU 方法边界、vLLM 2024–2026 计时样本与固定 FlashInfer-Bench 评估、评分和分派；[参考／基线与调用频数](../../case-studies/optimization-evaluation-and-deployment.md) | 5.3.5 候选验证→5.5.2 实际请求；实验 5-6、5-9。完整引擎集成、硬件匹配与真实替换仍待实验验证 |
| 少配验证资源，会不会拖住更大的训练组？ | DistRS 条件剩余时间与批次目标，对照 verl v0.4.1／2026 Agent Loop 的评分入口；[执行超时、反馈与释放](../../case-studies/reward-deadlines-and-feedback.md)；PolyRL 文档中的定制 SGLang 路径另列 | 3 长尾分布→5 优化反馈→10 批次依赖→11.3.3 验证资源；实验 11-5。逐条评分接口不等于跨作业阶段调度 |
| 新增 rollout 实例，能否在可用窗口内降低训练成本？ | RLBoost 评估与固定 PolyRL／SGLang 0.5.5 补丁；[共享出口、完整权重与实际恢复进度](../../case-studies/preemptible-rollout-and-weight-readiness.md)。配置的 Mooncake 名称与实际 TCP 路径分别核对 | 7 出口预算→8 前缀重建→10 同步阶段→11.3.2 可抢占资源；实验 11-4。模型配置、历史成本与当前实现分别保留 |

此前补查的结构化生成连接了冷 schema 准备、CPU 掩码、GPU 前向的重叠条件和推测回滚。当前 8.1.3 先讲请求调度，把语法、视觉、数值一致性作为执行条件留在实验变体和延伸材料；沿用实验 8-2 和图 8-1，不恢复成一个新的主小节。各框架的定位不同，只在同模型、精度、任务与执行条件可以对齐时做性能比较。

版本核对已覆盖暂停／恢复和权重交接的代表路径；缓存事件与动态 EP 的已读边界见下文。只有现有案例不能解释相应选择时才补充；模型支持名单、单个错误修复和接口改名保留在版本记录。更广的发布史与候选论文比较仍未完成。

扩写时，正文保留问题、主要预算、设计选择和结果解释；提交、命令、完整 profile、兼容限制放入实验材料。现有实验的多个变体按基础与选做分配，不能要求读者为学习一个判断同时安装全部框架。

2026-09-09 沿“提前准备→状态就绪→有效产出”复核图执行、权重交接和[主机调度](../../case-studies/host-policy-and-dispatch.md)：CUDA Graph 保留地址不等于恢复数据；vLLM 请求准入不等于 OS 线程调度；公开 ghOSt 接口也不等于 Wave 的 SmartNIC 实现。1.5.2→11.1.2 的扩写算例用相同 Agent CPU／内存预算检验省核收益。修正框架演进笔记中 Rubick 残留的旧章号，当前为第 6、10→11 章。此项是局部贯穿复核，没有完成全书逐例一致性验收。

动态 EP 已补查到“已有副本分派→权重重排→改变组规模”的执行边界及回本预算；Dynamo 消费 vLLM／SGLang 事件的分层与恢复条件，当前接在 9.5.3 和实验 9-9，区分平均收益与尾延迟。训练交接保留 vLLM／SGLang／verl 的固定路径与 Qwen3 峰值、分发计算；这不等于完整训练控制器或所有传输后端均已审计。LPLB、Waterfill 与 Elastic EP 各自的模型和执行条件分别保留，未作为可以任意组合的一组开关。

2026-09-09 单元分析复核沿同一 Qwen3 BF16 激活的 72 MiB 进入缓冲和流水；与第 5.3 节后接 FP8 量化的不同输出口径分开。当前框架源码、历史发行说明与论文采用条件分别留档。复核 ASPLOS 2025 候选落点时修正旧第 12／9／11 章号；另按 FSMoE 原件修正案例误写的 CUDA 10.3 为 11.3。此项未完成全书逐例验收。

2026-09-09 融合／快照复核：第五章任务合并不自动消除 HBM 中间读写，第六章 TP 归约不能把 RMSNorm 错移到各 rank 局部。第十一章模板缓存、安装到虚拟机的页和直接共享只读页分别计费，沿 11.1 的环境数重算容量；共享池与私有驻留不重复或遗漏。Diffuse 与 E2B 的新证据仅深化已有判断，仍未完成全书逐例验收。

2026-09-09 测量条件复核：所读 RMSNorm 脚本跨三个年份仍采用主机循环与设备同步，不能把另一个 activation 的图计时或 FlashInfer-Bench 的 CUPTI 调用描述成统一迁移。模型中间维度、拼接输入和 TP 局部宽度分别核对；同机比赛还会引入候选自身争用。现有实验 5-6 增加比较顺序变体，5-9 继续检验完整请求，不新增主节或图号。

2026-09-09 非矩阵资源复核：PICACHU 的建模比较与固定 vLLM RoPE 缓存路径分别取证。第 4 章的资源清单先区分准备和稳态，再接第 5 章同一 Qwen3 缓冲例子；第 13 章回顾专用化所依赖的执行条件。DFG 节点比、逻辑接口字节和物理 HBM 访问分别计量。

2026-09-09 重复片段复核：Apophenia 的自动匹配与 vLLM 外部批次分派分别取证。第 5 章沿现有 Qwen3 算子链核对输入绑定、收齐片段和设备进度；第 8 章继续区分请求内部就绪与合批等待。更少分析工作并不自动缩短整条链，声明来源与教学时间线见既有图执行案例。
