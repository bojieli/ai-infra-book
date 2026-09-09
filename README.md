# 《深入理解 AI Infra：量化分析与系统设计》

**数据搬移塑造了 AI Infra 的架构。** 这本书用作者的研究经历、具体模型和可复算的数字，解释芯片、网络、推理训练框架与模型算法怎样降低搬移代价，以及何时需要为容量、计算、正确性或质量付出更多搬移。

每次设计先问：搬什么、搬多少、搬几次、经过哪里、谁必须等它。读者沿同一任务逐章修正判断，最终能提出候选、找到遗漏约束，并用最小实验决定值得改什么。

目前完成草案 22 的结构与逐章写作大纲，尚未扩写正式书稿。

- [网页大纲](skeleton.html)与[逐章 Markdown](outlines/README.md)：十三章的主张、推导、练习和配图。
- [量化计算项目](calculations/README.md)：[全书计算计划](calculations/PLAN.md)、官方模型配置与硬件规格、统一 CLI 和[已复算结果](calculations/results/README.md)，持续实现中。
- [全书主线与章节依赖](outlines/structure.md)、[跨章设计决定](outlines/decision-record.md)：共同表示、固定输入和逐章修正。
- [阅读路径与配套](outlines/writing-support.md)、[完整扩写资料](outlines/extensions/README.md)：核心练习和详细技术材料。
- [本轮改动记录](research/outline-revision-2026-09-08/README.md)：主要建议的落地、章节映射及修改前快照。

论文和较大的计算输入、测量记录使用 Git LFS 保存。需要复算或读取原始记录时，克隆仓库后先运行 `git lfs install` 和 `git lfs pull`，再按对应项目的说明执行校验。

## 这本书怎样讲

首章从设备选择建立资源模型，随后用 TPU、SmartNIC 和 UB 解释判断怎样形成。模型与负载给出必须处理的数据；芯片、执行与互联改变复用、放置和等待；推理训练把这些机制组成有效服务；环境与端边云把服务放回完整任务。终章用 OpenTallas 的遗漏约束、Queqiao 的基线修正和未见配置，检验这套方法的解释力。

正文采用同一执行图：节点标计算与位置，边标字节、接口、频次和依赖，状态标生命周期。容量检查、资源下界和关键路径先排除明显不可行的方案，实测校准会改变选择的未知量。每章末保存当前决定、新增代价、下一个限制与翻转条件。

## 章节安排

<!-- CHAPTERS:START -->
1. [初识 AI Infra](outlines/01-%E5%88%9D%E8%AF%86%20AI%20Infra.md): 降低搬移代价需要同时比较复用、容量、计算、依赖和质量；最少字节与最快任务可以对应不同方案。
2. [模型架构](outlines/02-%E6%A8%A1%E5%9E%8B%E6%9E%B6%E6%9E%84.md): 驻留容量、逻辑访问与物理读写分别核算；状态更紧凑以后，索引、解压、更新或计算可能成为新的限制。
3. [推理与训练负载](outlines/03-%E6%8E%A8%E7%90%86%E4%B8%8E%E8%AE%AD%E7%BB%83%E8%B4%9F%E8%BD%BD.md): 到达率和平均长度不足以决定配置；复用间隔、阶段关联和尾部会同时改变搬移、驻留与排队。训练预算还需结合长期服务成本。
4. [加速器架构](outlines/04-%E5%8A%A0%E9%80%9F%E5%99%A8%E6%9E%B6%E6%9E%84.md): 增加计算单元的收益取决于供数和非矩阵工作；局部容量、带宽、面积与功率必须一起满足目标。
5. [算子与运行时](outlines/05-%E7%AE%97%E5%AD%90%E4%B8%8E%E8%BF%90%E8%A1%8C%E6%97%B6.md): 少一次写回、少一个 kernel 或更快的独占内核都要接受整条链的检验；复用、并发和缓冲寿命共同决定搬移代价。
6. [超节点](outlines/06-%E8%B6%85%E8%8A%82%E7%82%B9.md): 并行换来容量或处理能力，也增加交接与同步。总容量足够时仍要检查最忙设备；同一组卡应扩大协作还是增加副本，取决于负载和时限。
7. [数据中心网络](outlines/07-%E6%95%B0%E6%8D%AE%E4%B8%AD%E5%BF%83%E7%BD%91%E7%BB%9C.md): 网络设计降低的是完整协作的代价：载荷、启动、并发窗口、就绪偏差和语义约束共同决定进度；带宽与调用耗时各只能解释其中一部分。
8. [单实例推理](outlines/08-%E5%8D%95%E5%AE%9E%E4%BE%8B%E6%8E%A8%E7%90%86.md): 复用改变每个有效输出承担的搬移，但会占用容量、等待或额外计算；策略优劣要随到达率、历史长度和真实产出重算。
9. [分布式推理](outlines/09-%E5%88%86%E5%B8%83%E5%BC%8F%E6%8E%A8%E7%90%86.md): 分离和池化可以增加数据移动；成立条件是资源收益足以覆盖交接、双端缓冲、排队、失效和恢复。
10. [训练系统](outlines/10-%E8%AE%AD%E7%BB%83%E7%B3%BB%E7%BB%9F.md): 省容量可能增加通信或重算；提高生成吞吐也可能改变样本选择。执行优化要同时保持所声明的更新语义、质量和有效进展。
11. [资源调度与运行环境](outlines/11-%E8%B5%84%E6%BA%90%E8%B0%83%E5%BA%A6%E4%B8%8E%E8%BF%90%E8%A1%8C%E7%8E%AF%E5%A2%83.md): 计算空闲时状态仍可能驻留；降低搬移和重做需要检查状态身份与外部操作。资源分配最终以任务进展和完整成本评价。
12. [端边云协同](outlines/12-%E7%AB%AF%E8%BE%B9%E4%BA%91%E5%8D%8F%E5%90%8C.md): 距离、上下行、时限和恢复条件会改变放置。压缩或端侧编码是否省搬移由真实字节与质量决定；调优基线决定性能差距怎样归因。
13. [架构协同设计](outlines/13-%E6%9E%B6%E6%9E%84%E5%8D%8F%E5%90%8C%E8%AE%BE%E8%AE%A1.md): 降低搬移代价是候选设计的来源；物理可行、有效任务收益和投资回报必须分别建立证据。好的模型也应指出何时需要修改或放弃。
<!-- CHAPTERS:END -->

旧第 12 章（资源调度与运行环境）成为新第 11 章，旧第 8 章（端边云协同）成为新第 12 章。先有环境生命周期、状态及恢复预算，再比较任务的位置。多模态阶段和 EC／KV 已在第 3 章定义，后续推理章节可以独立展开。

## 实验与图

每章三项核心练习，共 39 项，其余就地标为延伸。练习先预测，再计算或测量，最后改变条件并修改选择；完整变体见扩写资料。公式、练习与图共用输入，机制图自绘 SVG，数据图由原始记录与脚本生成 SVG／PDF。

十三章共 70 节、240 个小节、117 项实验与计算、105 项配图计划。[统一计算项目](calculations/README.md)已开始交付配置、可复现代码与分析结果；[独立实验项目](experiments/README.md)已交付 CPU 分块、GPU 融合、attention 后端、编译代码及图重放五项实跑、原始数据与结果图，其余实验继续制作。本书拟测 M2 Max 38 核 GPU／96 GB 与 RTX PRO 6000 Blackwell Workstation Edition；H100／4090 保留为历史判断，昇腾使用已有公开证据，配置不同的结果分别使用。

## 材料入口


- [草案 14／15 新增内容的保留审计](research/draft14-15-outline-audit/report.md)：比较到草案 14 的增量，并用草案 15 同期审阅核对后续变化；补回 5 处占位，明确独立草案 15 原件未找到的证据限制。
- [草案 11 与当前大纲的完整对照](research/draft11-outline-audit/report.md)：[112 项取舍与原文定位](research/draft11-outline-audit/decision-matrix.md)，保留修改前快照；记录当时补回的章节与配套项目；[配套安排](outlines/writing-support.md)已在草案 22 具体化。
- [系统抽象边界上移调研](research/system-abstraction-boundary/report.md)：恢复旧版 skeleton 的可编程性主线，保存[历史原件与官方资料](references/outline-checks/2026-09-08/system-abstraction/README.md)，用于第 1 章的背景与第 11 章的环境边界。
- [2023—2026 年 token 成本下降调研](research/token-cost-2023-2026/report.md)：完整报告、[67 项原始资料](references/token-cost/2026-09-07/README.md)及[章节落点](research/token-cost-2023-2026/outline-placement.md)；草案 22 将相关问题融入推导，详细证据留在扩写材料。
- [2024–2026 长期调研](research/2026-infra-survey/README.md)：框架变迁、逐卷会议阅读、面试方向与精选题，当前进行中；[会议论文集](references/proceedings/README.md)保存全集，正文只采用经过筛选的案例。
- [业务与硬件的贯穿推算](case-studies/inference-training-scenarios.md)：请求、量化、异构服务与训练期限。
- [负载变化与芯片演进](case-studies/architecture-evolution.md)：代际机制在计算、存储和搬运各层的分析方法。

- [本地参考库](references/README.md)、[推理论文选读](references/INFERENCE-PAPER-GUIDE.md)、[芯片资料覆盖](references/HARDWARE-COVERAGE.md)、[UB 与昇腾 950 核对笔记](references/UB-ASCEND-NOTES.md)。
- 作者文章原件：[UB 背后的思考](references/files/documents/ub-reflection.html)，网络新黄金时代[（一）](references/files/documents/network-golden-1.html)、[（二）](references/files/documents/network-golden-2.html)、[（三）](references/files/documents/network-golden-3.html)，[A100/H100 太贵，何不用 4090？](references/files/documents/h100-vs-4090.html)。
- [可编程网卡案例](case-studies/programmable-nic.md)。
- [片上数据移动与能耗案例](case-studies/logicfolding-energy.md)。
- [训练计算量复算案例](case-studies/training-compute.md)、[Llama／Qwen 训练投入比较](case-studies/scaling-history.md)。
- [Qwen3／V4-Flash 模型与算子核对](case-studies/model-operator-examples.md)、[具体模型的并行推算](case-studies/model-parallelism.md)。
- [Queqiao 语音与广域实验案例](case-studies/queqiao.md)。
- [加速器架构比较案例](case-studies/accelerator-architecture.md)。
- [MacBook／RTX 配对案例](case-studies/macbook-rtx-pro6000.md)。
- [OpenTallas案例](case-studies/opentallas.md)。
- [异构 PD／AF案例](case-studies/pd-af-heterogeneous.md)。

近期模型、芯片和协议采用固定来源快照。规范说明行为，论文与公开实现支持相应机制，作者经历说明研究背景；根据数字作出的解释保留假设，未公开参数不填成确定结果。案例笔记中的旧细节节号按新版大纲重新定位。

## 历史文件与页面

[草案 15 审阅](reviews/draft15-review.md)、[草案 16 审阅](reviews/draft16-review.md)保留作为修订记录。[原在线 Artifact](https://claude.ai/code/artifact/f189e837-87cd-4db3-b58b-35db20856858)是此前的发布入口，本地修改尚未同步发布。

`skeleton.html` 保留 Artifact 使用的 HTML 片段形式，浏览器可以直接打开；独立分发时可由发布流程补充文档外壳。

本轮的模型计算与媒体案例：[容量、计算与访问](case-studies/model-resource-accounting.md)、[RAW 图片精修](case-studies/raw-retouching.md)；[全书写作要求](outlines/editorial-notes.md)。

本轮实用案例与取证：[执行优化与 Routing Replay](case-studies/execution-feedback.md)、[框架关键特性与章节对应](case-studies/framework-evolution.md)、[调度、模型路由与 E2B](case-studies/platform-routing.md)。
