# 大纲资料核对记录

## 草案 22：主线、依赖与阅读层次

2026-09-08。本轮依据已经核对的各章大纲、作者案例与原始材料，落实“降低数据搬移代价”的跨层设计方法：整章重写首尾、重排旧第 8–12 章、修改节内依赖、前置多模态阶段定义，并选择 39 项核心练习。参数、源码版本与完整实验变体保存在逐章扩写资料；来源状态沿用原有记录，本轮没有新增网络取证或设备测量。

当前结构、旧新映射及验证结果见[修订记录](../research/outline-revision-2026-09-08/README.md)。以下按草案保留历史工作记录；其中“本轮”、当时章数和实验体例指各自版本，当前阅读安排以[大纲索引](README.md)为准。

## 2026-09-08：草案 14／15 的新增内容是否再次遗失

在草案 11 审计后完整提取 11／14／16 原件文本并比较 11→14 的增量，核对当前章节、实验和案例材料。草案 15 没有找到独立文件或 Git 对象；同期审阅记录说它包含未提交修改，随后形成 16，因此不把 16 全部新增内容倒推归属 15。完整判断、原件、差异与快照见[增量审计](../research/draft14-15-outline-audit/report.md)及[清单](../research/draft14-15-outline-audit/source-manifest.json)。

补 D14-01—D14-05 五处短占位。另读 Megatron 官方 CP 文档、DualPipe 官方 README、DeepSeek-V3 提取文本的均衡／流水部分及 DFlash v1 的摘要与机制说明，原始资料均归档；未执行训练、故障注入或性能测试。其余保留、迁移、不恢复或版本归属不确定的项目分别记录。

## 2026-09-08：草案 11 全量内容对照

读取草案 11 的 19 个完整语义区域，逐章比较本轮修改前 13 份 Markdown 的主题、说明、实验与图计划，并核对相关配套笔记；形成[完整报告](../research/draft11-outline-audit/report.md)与[112 项判断](../research/draft11-outline-audit/decision-matrix.md)。[原件与修改前快照校验值](../research/draft11-outline-audit/source-snapshots.json)保存了审计基线。数字修正使用已有 H100 官方规格归档；跨租户前缀边界另读 vLLM 官方设计文档并保存源码快照，见[来源清单](../research/draft11-outline-audit/sources/manifest.json)。

补入 9 处章节占位及 4 项配套材料占位。恢复问题和教学联系，不把旧稿标为待核的拓扑、功耗、制程或尾延迟假说当成已核实事实；本轮没有执行硬件性能测量。保留原有 AB／TC 占位、十三章层级及实验图号。

## 2026-09-08：可编程性与系统抽象边界上移

按作者明确的 programmability 恢复第 1 章原有主线。草案 11（`12fc723`，第 482 行）与草案 14（`d9199ca`，第 483 行）均有“从 ISA/OS 上移至 token 层，可编程性与多租户迁移”的论述；草案 16（`e524afe`）重写后不再出现。已保存这三个版本的完整 skeleton，并核对 OSDI／SOSP、Stanford CRFM、NVIDIA MIG 与 Firecracker 五份官方网页的相关说明，原件与阅读范围见[专题索引](../references/outline-checks/2026-09-08/system-abstraction/README.md)。

[独立报告](../research/system-abstraction-boundary/report.md)展开云数据中心到 AI 数据中心的设计重心变化及其适用范围。大纲只在 1.1.1、1.5.1、11.2.2 放入 AB-01—03 三条简短占位；原有集群、芯片和软件全栈介绍合并到 1.1.2。章首、实验 1-1、图 1-1 和第 11 章增加叙述衔接，章节与实验、图号总数保持不变。该专题不改变长期调研的论文阅读计数。

## 2026-09-08：通信调优与卸载条件

选读 AutoCCL 物理页 2–14，与正式整卷逐页核对；另筛读 NSDI 2026 前 40 篇完整摘要。累计 710 篇摘要筛选、25 篇重点章节阅读。NCCL 2025 调优／2.28 公告与 2026 固定 2.31.2 接口补充通信资源的版本变化；[案例](../case-studies/communication-tuning.md)从 Qwen3 矩阵量级出发，用教学并发时间线比较局部与整体目标，计算调优回本次数，并区分 CE、设备 API 和 CPU proxy。

只深化 6.4.4／6.4.5、原实验 6-5／图 6-5 和 10.3.2 的衔接，I12 增加追问。没有新题号、面试来源或 GPU 实测。三份失败／空响应保留原件，已通过正确入口取得所需内容。NSDI 三届的分卷 README 现在随阅读清单同步，避免显示旧的筛读数量。

## 2026-09-08：检查点布局与加载

NSDI 2025 的 83 篇完整摘要已筛读，ByteCheckpoint 的 14 页选读与整卷比对完成；AutoCCL 只下载并读摘要，保留为下一步候选。累计 670 篇完整摘要筛选、24 篇重点章节阅读。对照 vLLM 三期 rank 权重文件与 PyTorch 2024／2025／2.14 的异步接口，深化 9.6.2／10.4.3 和原实验 9-10／10-6／10-7；[研究笔记](../case-studies/checkpoint-layout-and-loading.md)保留表示、后台争用、状态生成率和真正恢复点的区别。

九份官方响应含一个 stable 客户端重定向；已跟到 2.14 文档并读对应版本源码，不把重定向页面当作正文。实验、图号和精选题数量不变，没有新增公司面试样本；仍只完成提纲研究与算术验证，未运行模型。

## 2026-09-08：物理路径与作业错峰

NSDI 2024 的 112 篇完整摘要筛选完成。新增 CASSINI 的 13 页与 Swing 的 12 页选读，均与正式整卷逐页核对；累计 587 篇完整摘要筛选、23 篇重点章节阅读。第 6.4.3 数集合消息经过的有向链路，第 7.5.1 算周期通信峰值与超额量，第 11.3.1 检查多个局部错峰要求能否同时实现。修改现有实验 6-4／7-8／11-3 和对应配图；I12 加路径追问，没有新增题号或面试样本。

[案例与推算](../case-studies/network-planning-and-collectives.md)分别记录网络仿真、历史集群和教学输入，未将论文机制写成推理框架默认特性。其余 NSDI 届次、框架完整版本史和其他会议仍在进行中。以下保留各阶段记录，数量对应各自日期与范围。

## 2026-09-08：通信路径与等待诊断

NSDI 2024 前 42 篇完整摘要已筛读；rPCIeBench 物理页 3–13 与 MegaScale 物理页 4–14 的选读内容及整卷比对已登记。八份 vLLM 历史／当前、SGLang 当前来源核对实际通信分支、图缓冲与融合条件。第 6、7、10 章补消息尺度、在途窗口、rank 就绪偏差和固定 batch 扩展；实验 6-5、7-5、7-10 及既有配图加入对照，I12 加追问，未新增题号。

来源与采用范围见[通信笔记](../case-studies/collective-paths-and-diagnosis.md)和[长期调研](../research/2026-infra-survey/README.md)。本阶段仍为提纲与教学推算，没有 GPU／模型实测；余下会议及完整框架版本史继续进行。


## 固定能力下的 token 成本下降专题

2026-09-07 完成[独立报告](../research/token-cost-2023-2026/report.md)与[专题原件索引](../references/token-cost/2026-09-07/README.md)。核查 280 倍的起止日期与输入输出价格口径、Llama／Gemma 的模型对照、vLLM v0.6.0 及两条合入 PR、MTP 的训练与验证收益，以及 2026 年的模型、缓存和系统测量。报告保留无法证明统一千倍和独立归因的边界；没有进行本书 GPU 实测。

按作者本轮澄清，本专题在大纲仅插入 18 条简短占位，分布于 9 章并指向报告对应段落；[落点表](../research/token-cost-2023-2026/outline-placement.md)记录理由。保留 70 节、239 个小节、117 项实验和 105 项配图计划；7 章去掉占位后与捕获的修改前哈希一致。第 9、11 章在此期间还有其他工作区修改，已保留并单独记录，不将它们归入本专题，也不声称这两章原文哈希完全未变。

## 长期调研第一轮：MLSys 整卷与面试证据

2026-09-07 归档 MLSys 2024／2025／2026 官方目录的全部 233 篇 PDF 与文本，完成 2024 卷 37 篇完整摘要筛选，并读 Punica／S-LoRA 的共享计算、调度、内存管理和评估设置。两篇合为第 8.2 的多 adapter 案例，实验 8-3 增加变体；第 5.1 加归约形状对照，实验数量和章节层次保持不变。未把下载完成写成全卷全文读完。

首批面试资料区分官方考核、个人自述、二次整理与存在错误的答案，改编八个问题检查大纲回答路径。尚未完成 2026 年基础模型公司精选题的全面调研。具体阅读范围、来源、排除理由和下一步见[长期调研记录](../research/2026-infra-survey/README.md)。

第二轮完成 MLSys 2025 的 61 篇摘要筛选，重点读 FlashInfer、Marconi、KV 压缩评估和 Rubick，补 5.4.4、8.2.5、8.4.4、11.3.1 与原有实验变体，见[阅读记录](../research/2026-infra-survey/reading-mlsys-2025.md)。同时归档 OSDI／NSDI 2024–2026 六卷及勘误；这一部分只完成目录与正文首页核对，还未逐篇阅读。MLSys 2026 摘要、其他会议与完整框架历史仍在推进。

第三轮完成 MLSys 2026 前 45／135 篇完整摘要筛选，重点读 MoE Serving Tax、CRAFT 与 Breaking the Ice 的设计、实验和限制。用 Qwen3 复算批内专家复用、padding、副本挤占 KV 及启动成本，补回 6.3、9.4、9.6、11.3 和原有实验变体；[阅读记录](../research/2026-infra-survey/reading-mlsys-2026.md)当时尚有 90 篇待筛选，第四轮已完成。另固定历史 vLLM 打点工具与当前编译设计，补四份官方岗位说明和一篇 2026 年个人面经，精选改编题扩为 15 道；没有把岗位或论文追问称为公司原题。

## 草案 21：性能反馈、框架演进与任务平台

长期调研第七轮（2026-09-08）补核[第三批面试资料](../references/interviews/2026-09-08/third-pass/README.md)：官方性能岗位、署名 RL 问题与答卷、两份有归属的面试报告。保留作者整理、平台认证、实际岗位与日期的区别，题目扩到 18 道但不做频率统计。答案回到 Thinking Machines Lab、SGLang 2025／当前指南、vLLM v0.12.0／固定主线和 AReaL 状态流程；[概率与状态算例](../case-studies/rl-state-and-reproducibility.md)补入第 5→8→10 章的原有实验。实验、配图及成本占位数量保持；未运行 GPU 或训练实验，会议阅读数量未因此增加。

长期调研第六轮（2026-09-08）筛完 OSDI 2025 的 53 篇完整摘要，补读 NanoFlow、FuseLink 的设计、实现、评估与限制。用 Qwen3 的 FFN 切分、共享链路和并发 KV 预算深化 5.3.5、7.2.3、8.1.4／8.4.1、9.4.3；SGLang 的 H100→GB200 重叠变化与 Ollama 2024／2025／2026 固定路径随案例引入，见[资源共享笔记](../case-studies/resource-sharing-and-placement.md)。累计 339 篇摘要筛选、16 篇重点阅读；PipeThreader 只归档与读摘要，没有作为正文已读采用。现有 I08／I12 加计算追问，未新增公司面试样本。章节、实验、图号与 18 条成本占位保持，实际运行仍待扩写阶段提供。

长期调研第五轮（2026-09-08）筛完 OSDI 2024 全部 53 篇完整摘要，补读 Sarathi-Serve、DistServe、Llumnix 的相关设计、实现和评估页。以 Qwen3 同块长不同历史、TP／PP 排队、KV 速率与单次等待、迁移状态四个相连问题，深化 8.1、9.2、9.6 及原有实验和配图；[推算笔记](../case-studies/chunking-and-state-transfer.md)保留假设与历史条件。对照 vLLM v0.4.2、v0.8.0 和当前固定调度路径，区分早期分块与 V1 的统一进度；完整框架版本史仍未完成。累计 286 篇摘要筛选、14 篇重点阅读，16 道改编题保持不变；I05 增加有依据的计算追问，未增加公司面试样本。正文层次和实验数量不变，已有成本专题占位保留。

长期调研第四轮（2026-09-08）已筛完 MLSys 2026 全部 135 篇摘要，并补读 FA4 与 MPG 的设计、公式和实验条件；三届合计 233 篇摘要筛选、11 篇重点章节阅读。FA4 用单 SM 算例接通第 4→5→8 章及真实框架后端，MPG 用相容设备时间补 10.6／13.1；保留原有章节、实验和配图数量。逐篇范围见[阅读记录](../research/2026-infra-survey/reading-mlsys-2026.md)，当前代码见[固定后端](../references/framework-history/2026-09-08/attention/README.md)。另外归档 ASPLOS／ISCA／MICRO 官方入口及 ASPLOS 2024 摘要集，仍未宣称这些论文集已读完；精选改编题增加一项训练产出追问，不增加公司面试样本。

本轮补查并阅读 KernelAgent、FlashInfer-Bench、CUDA Agent 的优化／验证流程，MPK、NanoFlow、MegaScale-Infer 的执行设计，R3 的路由 mask 与多轮状态，以及 Megatron Core 2026 的内存、并行与 RL 部分。第 5 章补算子优化 Agent、合法性与成本预测的区别、CUDA Graph／persistent／流水；第 8、9 章在真实引擎中安排请求、图执行、专家分组、DBO／TBO、EPLB 和缓存实验；第 10 章补 Routing Replay、Sleep Mode 与训练后端分工。

完成这些落点后，再核对近两年的 vLLM、SGLang、Ollama 官方更新。阅读 V1、Wide EP、AFD、HiCache／HiSparse／Unified Radix Cache、BCG，以及 Ollama 多模态、内存调度、MLX 预览和 MTP。具体特性与章节、实验的关系记录在[框架演进笔记](../case-studies/framework-evolution.md)，正文不增设产品介绍章。保留发布、实验性和支持范围；没有将最新文档的选项拼成未经验证的通用部署命令。

第 11 章补读 ASI 的负载与调度、RLBoost 的部分响应迁移、DistRS 的批次约束，以及 SpecBox 的设计和实验条件；新增 E2B 架构固定提交、状态文档和 Claude／Google 官方计费快照。模型选择围绕同质量成功任务，把 reasoning、前缀缓存、排队、限流、重试与环境成本连起来。100／1,000 个思考 token、10 轮缓存、环境容量和 R3 记录容量均为有明确输入的算例。

原件分三组归档：[执行反馈](../references/outline-checks/2026-09-07/execution-feedback/sources.json)、[框架演进](../references/outline-checks/2026-09-07/framework-evolution/sources.json)、[调度与路由](../references/outline-checks/2026-09-07/platform-routing/sources.json)。CUDA Agent 的 arXiv HTML 返回空响应，改取成功下载的作者 PDF，没有把空文件记作原件。新价格采用查询日官方标准档位，区别 batch 折扣与产品订阅。

本轮没有重读全部参考库，没有安装 GPU 软件栈、下载权重、调用付费模型或实施训练。完成的是大纲、来源核对、代表算术与实验制作计划；扩写时再提供代码、原始运行记录和正式 SVG。所有实验与配图继续紧随相应内容，每章仍为 5–10 项实验。

## 草案 20：章节层次与模型资源推算

本轮通读十三章的目录层次并检查相邻内容：第 3 章归为推理与训练两块，第 4 章将低精度归入计算资源，第 5 章归并编程与编译、动态形状与运行时，第 6 章归并集合通信算法与执行、物理组织与架构，第 7 章归并访问路径，第 8 章归并批处理／调度及 KV／前缀，第 11 章归并环境隔离与复用恢复。第 9 章 KV 部分收为四个小节，保留 PD、AF 和共享池。其余章节保留有明确分工的一级节，不为数量统一而删内容。实验和图仍在相关段落旁。

第 1 章改为集群→超节点→主机与卡→芯片内部，再建立软件全栈，按 Jeff Dean 的历史 CPU 系统数字与本书 GPU 数字两步展开；容量、Roofline、链路与关键路径方法在本章直接给出。第 2 章以 Qwen3 跟算，主要比较 DeepSeek-V4 与 Kimi K3，分别核算常驻容量、prefill／decode 计算、权重读取、历史读取及状态更新。全局写作要求记录在[编辑笔记](editorial-notes.md)，借鉴定量原则与真实设计的连接，并参照本地 AI Agent book 的标题与说明方式。

重读 K3 报告 §2.1–2.3、表 1、§5.4.1，与 V4 参考代码中的 Compressor／Indexer／Attention 路径；新增固定 K3 配置及参考代码，读取 MLA、KDA 和缓存路径。发现 K3 NoPE 不代表当前代码删除 64 维额外分支；紧凑 BF16 教学表示在 8K 历史为 216 MiB MLA 状态，但该参考代码展开缓存约 11.25 GiB。KDA 的 414 MiB 是明确假设 FP32 的状态计算，不能由模型 dtype 推定实际部署。没有执行远程代码、下载权重或声称生产后端实测。

第 12 章使用图片精修、ASR／TTS 与 Computer Use 三类案例，图像信息背景简述，重点推算上传、处理、回传或逐轮截图的优化收益。图片精修经历来自作者本次补充，30 MB 原图等为教学值；语音沿 Queqiao 原记录，截图例子标明 0.8 MB／6.4 Mbit/s 等假设。查阅华为 RAW 使用说明、Adobe 图像处理与无损 DNG、HTTP/3 标准、Linear Transformers 作者说明，以及《计算机体系结构：量化研究方法》的出版说明；没有将后者称为全书重读。Adobe 旧版 DNG PDF 下载超时，改用成功归档的 Adobe 原文支持无损压缩。

另外回读 Llama 1 引言与 Qwen3 §2 的模型家族说明，第 2.6 节增加 7–8B／30–32B／70B／235B 的容量适配及层宽、专家颗粒度推算。没有将部署适配写成团队明确披露的选型动机。

新增来源见[媒体与方法](../references/outline-checks/2026-09-07/edge-media/sources.json)、[K3 固定配置与代码](../references/outline-checks/2026-09-07/model-accounting/sources.json)，代表算式见[算术记录](../references/outline-checks/2026-09-07/model-accounting/arithmetic.json)。全文仍为写作大纲，正式实验、完整代码和 SVG 随扩写制作。

## 草案 19：业务贯穿案例与芯片代际设计

本轮重点修改第 4、8、9、10、12 章，并同步 HTML、索引、实验图号与资料映射。第 8–10 章使用 Qwen3-8B 的具体请求和领域训练，再换 Qwen3-235B／V4-Flash；A100／A800、H20、H100／B200 分别检验互联、阶段适配与完成期限。第 12 章用语音、代码 Agent 和视觉助手替换一般网页、下载与投屏场景。第 4 章将代际机制穿插于计算、存储、搬运和低精度，不再单设年代回顾。

重读既有 Ampere／Hopper、Blackwell、Rubin、昇腾与 Apple 相关段落；补读 EAGLE 3.1、DFlash／DFlash 2、MiMo／TileRT、KTransformers V4／Kimi K2 和微调范围，核对 A800 原厂表及 NVIDIA HGX 稀疏脚注。新增 Apple M3／M5 与 CUTLASS 原件，后者另取固定提交的 TMEM 与双 SM 样例。没有逐页重读全部参考库，也没有运行项目性能实验。

直接读取 GGUF 仓库元数据并汇总分片：Qwen3-235B UD-Q2_K_XL 约 81.97 GiB，R1 UD-IQ1_S 约 130.60 GiB。它们是对应快照的文件大小，不是常驻内存或推理速度。Unsloth 历史博客经网页工具阅读，直接下载 403，未声称已存原始 HTML；本地另存作者模型卡与文件元数据。KTransformers 搜索结果与固定教程存在版本差异，采用固定提交的条件，单卡与八卡结果分开。

原件、版本及 SHA-256 见[本轮来源](../references/outline-checks/2026-09-07/systems-cases/sources.json)，教学数值见[算术记录](../references/outline-checks/2026-09-07/systems-cases/arithmetic.json)。[业务推算](../case-studies/inference-training-scenarios.md)与[芯片演进](../case-studies/architecture-evolution.md)记录落点、推断与未知量；50% MFU、1T／5T／10T 与流水时延均有明确假设，不作真实训练或芯片实测。


核对日期：2026-09-07。此记录说明逐章大纲的依据、实际阅读范围及尚需补证的内容；它与正式书稿的逐项事实审阅分别维护。

## 草案 18 的后续补正：模型切分与集合通信

再次对照初始提交 `12fc723` 的 skeleton，重点检查原“卡间：scale-up 域与超节点互联”“机间：网络与集合通信”以及并行策略的相关说明。前一版大纲虽然保留了集合通信名词，却将具体切分过多后移，削弱了模型与互联的联系；本次按最新反馈调整章节分工。

第 5 章切分芯片内计算，第 6 章用真实模型推算 TP／PP／DP／EP，第 7 章继续核算跨超节点训练集合通信与八卡服务器间的大模型推理。第 9 章移除基础并行介绍，集中讲 PD／AF、多级与持久化 KV，原有专家负载、共享池与服务恢复继续展开。原 skeleton 的内容范围作为参照，其中把某种瓶颈或部署结果概括为无条件结论的表述未沿用。

补存 Qwen3-235B-A22B 的固定配置，重读 Kimi K3 表 1 与潜空间专家、V4 的 on-disk KV 管理，以及 Mooncake／LMCache 的存储层次。新增[具体模型的并行推算](../case-studies/model-parallelism.md)，包括逐卡容量、权重／KV 读取、矩阵运算和通信的核算顺序；两个教学互联条件下的 TP 候选计算展示选择如何改变，不作为真实设备测量。

当前大纲共 86 节、242 个小节、105 项实验与计算、94 项配图计划，每章仍为 7–10 项实验。下文保存此前修订过程，其中数量是对应阶段的记录。

## 草案 18：体例、具体模型与章节衔接

本轮阅读了相邻 `ai-agent-book/book/` 的实际中文稿：第 1 章开篇、架构说明和嵌入式实验，第 4 章工具分类与描述段落，以及第 2、6、9 章相关小标题。借鉴“明确主题—解释关系—以具体实例推进”的体例，将实验改为相应小节中的块引用；所有章节小标题重新检查，去掉“公式没变，程序为什么慢”等过于随意的表达。

第 1 章恢复全栈架构在前、关键数字与推算实验居中、TPU／SmartNIC／UB 案例在后的顺序。补读 Jeff Dean 的 LADIS 2009 原始演讲，包括 “Numbers Everyone Should Know” 与缩略图页面的估算例子；历史数字不当成当代设备参数。

第 2 章以固定 Qwen3-8B 与 DeepSeek-V4-Flash 配置为贯穿算例；核对 QKV、FFN、缓存、压缩器、索引、专家和 mHC 的尺寸与路径。DeepSeek-V3 与 V4-Flash 分开，未采用不存在于本次官方资料中的“V3 Flash”名称。第 5 章的编译器动机改为手工优化与融合组合的成本，安排从小序列模型到大型 MoE 的算子／形状／融合机会表；表与完整运行 trace 尚待扩写。

本次已下载并阅读固定提交的 vLLM Qwen3、其复用的 Qwen2MLP，以及 V4-Flash 官方参考实现的 Attention、Compressor／Indexer、Gate／MoE、Block 与 MTP 路径。所固定的 vLLM 提交未发现对应 V4 模型文件，故以官方参考实现支持 V4 尺寸；没有宣称复现生产内核、所有后端或整套 vLLM。逻辑算子和实际 kernel launch 分开。

第 3 章改名为“推理与训练负载”，先讲 prefill／decode 和 Chat、Agentic、Real-time，再讲预训练／中期训练、SFT、RL。Scaling law 放在负载建立之后。补读 Llama 1 的模型与 GPU 小时表、Llama 2 的训练数据与设备表、Llama 3.1 官方卡，Qwen2.5 的预训练和超参数 scaling，Qwen3 的阶段与后训练表，以及 Qwen3.5 发布与模型卡。具体取值和比较限制见[训练投入笔记](../case-studies/scaling-history.md)。

RL 系统按最新反馈改用 DeepSeek-V4 §5.2，R1 用于解释训练路线。重读 V4 的 QAT、教师调度、token 级 WAL、长上下文数据组织与 DSec 沙箱，将它们分别接到第 3、9、10、11 章。Kimi k1.5 在此前核对时已归档，保留为历史备查，不再作为本书 RL 系统主例。

第 6 章加入内存借用与 KV 使用的具体计算，第 7 章从超节点边界、跨超节点流量与扩展效率引入；第 9 章分别展开 A100＋H20 的 PD、KTransformers 的 AF、共享 KV 内存池。1 GiB／25 GB/s、32 层激活交接、四节点容量等均标为明确假设下的教学算例，未标作设备实测。

新增资料的版本、URL、获取时间和 SHA-256 见[来源记录](../references/outline-checks/2026-09-07/scaling-history/sources.json)。13 章共 83 节、229 个小节，安排 100 项实验与计算、89 项配图，全部随小节出现。本次完成大纲与核对笔记，未完成书中实验、全库逐页精读或正式图片。

## 草案 17：叙述方式重写与补充阅读

本次在前一轮资料核对之后，回读初始十二章骨架（提交 `12fc723`）的整体思路，放弃沿用后续草案的逐节模板。十三章的当前分工保留，skeleton 与 Markdown 的节、小节和实验重新安排。

重点重读作者的五篇文章正文：**《Unified Bus 背后的思考》《计算机网络的新黄金时代（一）》《（二）》《（三）》和《A100/H100 太贵，何不用 4090？》**。前者与第一篇网络文章用于第 1、6、7 章；广域网和无线两篇进入第 3、12 章；H100／4090 的问题跨负载、硬件、推理和训练展开。采用从实际问题、初步估算到设计修正的叙述方式，历史价格、协议概括和性能判断另回原件核对。

同时对照可编程网卡案例与博士论文、UB 正式规范、950 白皮书和配套案例。UB 故事中早期研究与 GPT-3 后投入增加的时间关系明确区分；网络文章中的顺序、RDMA 状态与 QUIC 行为不直接作为规范。逐章取证限制移入[编辑笔记](editorial-notes.md)，让阅读目录集中于问题与设计。

Scaling law 的补充阅读包括 Kaplan、Chinchilla、Llama 3 的预测方法、[Beyond Chinchilla-Optimal 的 ICML 2024 发表页](https://proceedings.mlr.press/v235/sardana24a.html)和其 [arXiv v1 全文](https://arxiv.org/html/2401.00448v1)，以及已有的 test-time compute 研究。草案 17 曾据此将计算分配置于章首；草案 18 按最新意见改为先推理、后训练，再讨论 scaling law。进一步阅读并保存 [ICML 正式全文](../references/outline-checks/2026-09-07/beyond-chinchilla-icml24.pdf) 的 §2、§4–6：长训练仍有收益，但基于短训练拟合的关系会高估极端比例下的改善。§6 的费用模型区分训练、输入与输出效率，仍简化了延迟要求与效率的变化。两版实验规模不同，正式版与早期全文分别引用。

网络部分补存 [RFC 9001](https://www.rfc-editor.org/rfc/rfc9001.html) 和 [RFC 9221](https://www.rfc-editor.org/rfc/rfc9221.html)，用来区分 QUIC 的 TLS 集成、可靠流和不可靠数据报扩展。[本次新增来源记录](../references/outline-checks/2026-09-07/narrative-revision-sources.json)保留 URL、获取时间、大小和校验值。

这次新增的是叙述与推导安排，并未完成书中性能实验，也未把全库原件升级为逐页审阅状态。下面保留前一轮的归档及规格核对记录，便于继续扩写。

## 前一轮归档与规格核对范围

- 阅读现行 skeleton 的章节、教学、实验、配图、案例及证据安排，对照 README 和八份配套案例；旧审阅与协作记录仅用于理解历史变化，以现行十三章为准。
- 逐项核查参考库 230 项清单、获取状态及章号映射，查看可用文本的摘要、开篇或目录；长文档按大纲论点定位相关章节。现有提取文本约 2500 万字符，含完整规范、指南、源码和重复版本。本轮没有逐页通读全部 230 份原件，也没有逐条审核所有协议状态机或源码路径。
- 重点阅读近期模型架构与配置、950 核内通路、硬件覆盖和 UB 核对笔记、推理论文选读及相关机制段落；对平台文档进一步检查实际正文，发现并补正 OTel 的迁移入口。
- 对原清单中有文件路径的 229 项逐一校验文件存在与 SHA-256，均与原 manifest 一致。这只证明归档完整性，不证明内容准确或引用已足够。
- [全量资料对应表](source-map.md)记录每项资料在大纲中的主要引用或补充角色。未取得正文的入口、残缺网页和仅有厂商宣传的材料不承担超出其范围的技术论证。

大纲已经落实内容、实验与图的安排；正式扩写时仍需按实际采用的公式、数字、图和技术断言回到原文逐项核对。未公开参数与尚未完成的本书测量在编辑笔记中列出，不能填成确定结果。

## 近期模型与主实验设备复核

通过官方页面核对来源，并重新获取下列九项已知原始地址进行字节比较，保留旧快照。[网络复核 manifest](../references/outline-checks/2026-09-07/manifest.json)记录地址、时间、校验值和变化文件。

| 对象 | 核对结果 | 大纲采用方式 |
| --- | --- | --- |
| [Qwen3.5-397B-A17B 配置](https://huggingface.co/Qwen/Qwen3.5-397B-A17B/blob/main/config.json) | 重新获取与本地字节一致；60 层中 45 层线性注意力、15 层全注意力 | 第 2 章按 text_config 分层，视觉和 MTP 另计；第 3 章只做已知部分计算 |
| [DeepSeek-V4 报告](https://arxiv.org/abs/2606.19348v1) | 重新获取 PDF 与本地字节一致；核读 §2 的 CSA／HCA、mHC 和 MoE，以及训练配置相关记录 | 与 V3.2 DSA、V2／V3 MLA 分开；完整训练计算仍需阶段明细 |
| [Kimi K3 报告](https://github.com/MoonshotAI/Kimi-K3) | 重新获取报告与本地字节一致；核读 §2 和表 1 | KDA／Gated MLA、Attention Residuals 和 Stable LatentMoE 分项；69 KDA＋24 MLA 包含末尾额外 MLA |
| [RTX PRO 6000 Workstation Edition 数据表](https://www.nvidia.com/content/dam/en-zz/Solutions/data-center/rtx-pro-6000-blackwell-workstation-edition/workstation-blackwell-rtx-pro-6000-workstation-edition-nvidia-us-3519208-web.pdf) | 重新获取与本地字节一致 | 固定该形态的容量、带宽、板卡功率；不移用 B200 HBM／NVLink |
| [昇腾 950 官方白皮书](https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf) | 重新获取与本地字节一致；核读 CV、NDDMA、SIMD／SIMT、产品与互联条件 | 950PR／DT 及裁剪配置分开；结构、机制与实测分开 |
| [Trainium3 架构页](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/about-neuron/arch/neuron-hardware/trainium3.html) | 重新获取与本地字节一致；仍列 4.9 TB/s、16 CC-Core | 保留来源，不与 NKI 指南冲突参数合并 |
| [Trainium3 NKI 指南](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/nki/guides/architecture/trainium3_arch.html) | 重新获取与本地字节一致；仍列 4.7 TB/s、20 CC-Core | 作为编程架构参照；冲突未消除前不据此作精确产品比较 |
| [TPU 8t／8i 官方说明](https://cloud.google.com/blog/products/compute/tpu-8t-and-tpu-8i-technical-deep-dive) | HTML 字节变化；去除脚本、样式、导航后，文本差异为日期 4 月 23 日变为 4 月 22 日 | 保留[本轮快照](../references/outline-checks/2026-09-07/google-tpu8.html)；本次提取比较未发现主体参数变化，不等于像素或全站一致 |
| [Rubin 官方架构说明](https://developer.nvidia.com/blog/inside-nvidia-rubin-gpu-architecture-powering-the-era-of-agentic-ai/) | HTML 字节变化，所提取正文文本未见变化 | 保留[本轮快照](../references/outline-checks/2026-09-07/nvidia-rubin-arch.html)；只作带日期的架构专题，厂商收益声明不写成本书实测 |

另行搜索了近期模型和架构资料。只有能对应原始报告、配置或官方机制说明的内容进入大纲；搜索热度、新闻排行榜和缺少条件的代际倍数不作为采用依据。上述比较不能推出其他未复核资料都没有更新。

## 新发现与补充资料

原库 `otel-genai` 虽有已下载文件，正文实际是[迁移提示](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/)，不能继续作为完整指标规范引用。按官方跳转找到 [OpenTelemetry GenAI 仓库](https://github.com/open-telemetry/semantic-conventions-genai)，补存固定提交 `94f432d7126f5884d30a2cdde6f4e89908ebb6fd` 的 [metrics 正文](../references/outline-checks/2026-09-07/otel-genai-metrics.md)，获取与校验记录见[新增来源](../references/outline-checks/2026-09-07/otel-source.json)。

该文档仍标为 Development。它分别定义客户端 chunk 指标与服务端 token 指标，并覆盖 workflow、agent 和 tool；第 11 章采用其身份与观测思路，具体实验字段按固定版本核对。指标聚合不能替代可去重、可对账的原始计量事件。

## 关键取证位置

以下位置用于扩写时快速回到原件，不表示已审核所列资料的每一条断言。

| 内容 | 原件位置 | 需要保留的边界 |
| --- | --- | --- |
| 序列并行、注意力与 KV | Transformer；MQA／GQA 方法；DeepSeek-V2 的 MLA；FlashAttention §3 | 训练并行与自回归依赖、状态压缩与 IO 优化分开 |
| 近期混合模型 | Qwen3.5 text_config；V4 §2、§4.2；K3 §2、表 1 | 层数、位置表示、专家维度、辅助分支分别核算 |
| 训练计算量 | [训练复算案例](../case-studies/training-compute.md)及其原始报告 | 专家项、注意力项只是局部工作，缺失阶段不能闭合总量 |
| 早期 DaVinci | 原件 PDF 页序 108–111，论文 §3.1–3.4、图 9–15 | 期刊论文中的配置不能全部标成 910A 出货规格 |
| 910C | CloudMatrix384 v2 §3.3.1、§4.2.2，与 v3 对照 | 型号称谓和被删参数的版本分别注明 |
| 950 核内与互联 | 表 3-1；§4.1；§4.6，尤其图 4-6、4-7、4-14 | PR／DT、CV、NDDMA、CCU 与 UBoE 分别对应章节 |
| UB 与 OS | Base 2.0.1 §2、§5–10；OS 2.0 §3–7 | 规范、OS 机制、平台策略和 OpenURMA 实现不相互替代 |
| 编译与运行时 | AKG 的 tiling／fusion；TVM／TensorIR；Triton 矩阵乘教程；CUDA Graph 与 vLLM 设计 | 论文版本、现代代码、硬件支持与开发成本分别引用 |
| 端侧执行 | [配对案例](../case-studies/macbook-rtx-pro6000.md)和固定 Ollama Metal 代码 | 真实 runner、CPU 回退、统一内存和 ANE 路径需分别确认 |
| 投机采样 | Leviathan 等方法；Chen 等 Algorithm 2；Medusa acceptance；EAGLE 系列 | 分布保持、近似接受与浮点逐位一致不是同一保证 |
| PD／AF | DistServe、Splitwise；KTransformers §6.1；[异构案例](../case-studies/pd-af-heterogeneous.md) | 实例、卡数、KV 格式、逐层激活及公开配置不混用 |
| 语音与广域 | RFC 9293／9000／9002／3550／8831／8836；[Queqiao](../case-studies/queqiao.md) | 默认配置、公平基线、协议差异和路径变化分别归因 |
| 平台与环境 | DRF／Gavel／Tiresias／Pollux；Kueue 准入；Kubernetes 调度与镜像；Firecracker | 作业与请求调度、沙箱与虚拟化机制、启动与隔离保证分开 |
| 能耗与专用化 | LogicFolding 图 1–2、§IV–VII；OpenTallas 固定案例 | 单因素计算、作者报告、模拟、综合与完整系统实测分开 |

## 未闭合证据的处理

- 保留 [GAPS.md](../references/GAPS.md) 中的主要缺口：H20 完整规格、910 逐代指令与设计因果、跨平台同条件性能、训练阶段明细、作者任务与计量原始记录。
- 本轮没有运行本书性能实验。实验表中的预计输出不表示已获得相关日志或结果；数据包完成前不能制作实测曲线。
- 完整规范、芯片原图和厂商图的出版使用状态另行记录；原件已下载不能自动视为复制或改绘已获出版授权。
- 参考库的来源名称和版本保持原样；新增复核文件单独存放，没有覆盖旧 PDF、源码、规范或 manifest。
