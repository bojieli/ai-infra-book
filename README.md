# 《深入理解 AI Infra：量化分析与系统设计》

**数据搬移塑造了 AI Infra 的架构。** 这本书用作者的研究经历、具体模型和可复算的数字，解释芯片、网络、推理训练框架与模型算法怎样降低搬移代价，以及何时需要为容量、计算、正确性或质量付出更多搬移。

每次设计先问：搬什么、搬多少、搬几次、经过哪里、谁必须等它。读者沿同一任务逐章修正判断，最终能提出候选、找到遗漏约束，并用最小实验决定值得改什么。

全书已完成草案 22 的结构与逐章写作大纲。第一章已扩写为正文初稿并制作六幅配图，第二章已完成六节正文初稿与八幅配图，其余章节继续按大纲展开。

- [第一章正文阅读版](manuscripts/01-%E5%88%9D%E8%AF%86%20AI%20Infra.html)、[Markdown 与图片](manuscripts/README.md)。
- [第二章正文阅读版](manuscripts/02-%E6%A8%A1%E5%9E%8B%E6%9E%B6%E6%9E%84.html)、[图片与复现](manuscripts/ch02/README.md)。
- [第十一章正文阅读版](manuscripts/11-资源调度与运行环境.html)、[Markdown、插图与复现](manuscripts/ch11/README.md)：五节全文、八幅无内嵌图号插图、量化算例与十项练习。
- [网页大纲](skeleton.html)与[逐章 Markdown](outlines/README.md)：十二章的主张、推导、练习和配图。
- [量化计算项目](calculations/README.md)：[全书计算计划](calculations/PLAN.md)、官方模型配置与硬件规格、统一 CLI 和[已复算结果](calculations/results/README.md)，持续实现中。
- [全书主线与章节依赖](outlines/structure.md)、[跨章设计决定](outlines/decision-record.md)：共同表示、固定输入和逐章修正。
- [阅读路径与配套](outlines/writing-support.md)、[完整扩写资料](outlines/extensions/README.md)：核心练习和详细技术材料。
- [本轮改动记录](research/outline-revision-2026-09-08/README.md)：主要建议的落地、章节映射及修改前快照。

论文和较大的计算输入、测量记录使用 Git LFS 保存。需要复算或读取原始记录时，克隆仓库后先运行 `git lfs install` 和 `git lfs pull`，再按对应项目的说明执行校验。

## 这本书怎样讲

首章从六层全景与关键数字开始，估算一次模型生成，再用 TPU、SmartNIC 和 UB 的短例解释架构选择。模型与负载给出必须处理的数据；芯片、执行与互联改变复用、放置和等待；推理训练把这些机制组成有效服务；环境与端边云把服务放回完整任务。OpenTallas 的供数与通信修正融入芯片和超节点，Queqiao 的基线修正留在端边云；各章用具体证据修正选择。

正文采用同一执行图：节点标计算与位置，边标字节、接口、频次和依赖，状态标生命周期。容量检查、资源下界和关键路径先排除明显不可行的方案，实测校准会改变选择的未知量。每章末保存当前决定、新增代价、下一个限制与翻转条件。

## 章节安排

<!-- CHAPTERS:START -->
1. [初识 AI Infra](outlines/01-%E5%88%9D%E8%AF%86%20AI%20Infra.md): 从六层全景和关键数字出发，估算生成一个 token 的容量、计算与读取下界，再用三个短例理解资源约束怎样推动架构选择。
2. [模型架构](outlines/02-%E6%A8%A1%E5%9E%8B%E6%9E%B6%E6%9E%84.md): 从前向执行与完整生成建立资源基线，分别比较历史状态、专家权重和网络组织；参数量或激活计算相近的模型仍可提出不同的系统需求。
3. [推理与训练负载](outlines/03-%E6%8E%A8%E7%90%86%E4%B8%8E%E8%AE%AD%E7%BB%83%E8%B4%9F%E8%BD%BD.md): 模型结构给出单次执行的需求；任务的阶段组成、到达与依赖关系，以及状态寿命，决定这些需求如何在时间上叠加。比较系统方案时，还必须保持任务质量和完成目标一致。
4. [加速器架构](outlines/04-%E5%8A%A0%E9%80%9F%E5%99%A8%E6%9E%B6%E6%9E%84.md): 从加速器组成出发，理解计算、存储、数据搬运、封装互联与专用化，再结合性能、功耗和成本选择适合负载的架构。
5. [算子与运行时](outlines/05-%E7%AE%97%E5%AD%90%E4%B8%8E%E8%BF%90%E8%A1%8C%E6%97%B6.md): 少一次写回、少一个 kernel 或更快的独占内核都要接受整条链的检验；复用、并发和缓冲寿命共同决定搬移代价。
6. [超节点](outlines/06-%E8%B6%85%E8%8A%82%E7%82%B9.md): 并行换来容量或处理能力，也增加交接与同步。总容量足够时仍要检查最忙设备；同一组卡应扩大协作还是增加推理实例数量，取决于负载和时限。
7. [数据中心网络](outlines/07-%E6%95%B0%E6%8D%AE%E4%B8%AD%E5%BF%83%E7%BD%91%E7%BB%9C.md): 网络设计既要利用并行与共享降低搬移代价，也要界定必要的顺序、资源寿命和故障范围；最终收益取决于这些选择能否减少任务关键路径上的等待。
8. [单实例推理](outlines/08-%E5%8D%95%E5%AE%9E%E4%BE%8B%E6%8E%A8%E7%90%86.md): 固定实例的并行配置，依次组织批处理、KV 复用、压缩与卸载及推测解码，再用相同质量和 SLO 验证有效服务。
9. [分布式推理](outlines/09-%E5%88%86%E5%B8%83%E5%BC%8F%E6%8E%A8%E7%90%86.md): 从完整副本基线出发，比较计算分工、专家负载均衡与共享状态，再将启动、重配置和恢复纳入完整部署；资源收益必须覆盖新增交接、驻留与等待。
10. [训练系统](outlines/10-%E8%AE%AD%E7%BB%83%E7%B3%BB%E7%BB%9F.md): 省容量可能增加通信或重算；提高生成吞吐也可能改变样本选择。执行优化要同时保持所声明的更新语义、质量和有效进展。
11. [资源调度与运行环境](outlines/11-%E8%B5%84%E6%BA%90%E8%B0%83%E5%BA%A6%E4%B8%8E%E8%BF%90%E8%A1%8C%E7%8E%AF%E5%A2%83.md): 计算空闲时状态仍可能驻留；释放、复用和迁移状态都要支付准备或恢复代价。资源与模型服务的选择，以满足质量和期限的完整任务及其全部成本评价。
12. [端边云协同](outlines/12-%E7%AB%AF%E8%BE%B9%E4%BA%91%E5%8D%8F%E5%90%8C.md): 执行位置要按相同质量下的完整交互选择；用分工、实际传输与恢复条件修正预算，再以调优基线验证收益，形成部署方案和选择翻转条件。
<!-- CHAPTERS:END -->

旧第 12 章（资源调度与运行环境）成为新第 11 章，旧第 8 章（端边云协同）成为新第 12 章。先有环境生命周期、状态及恢复预算，再比较任务的位置。多模态阶段和 EC／KV 已在第 3 章定义，后续推理章节可以独立展开。

## 实验与图

每章三项核心练习，共 36 项，其余就地标为延伸。练习先预测，再计算或测量，最后改变条件并修改选择；完整变体见扩写资料。公式、练习与图共用输入，机制图自绘 SVG，数据图由原始记录与脚本生成 SVG／PDF。

十二章共 72 节、250 个小节、106 项实验与计算、98 项配图计划。[统一计算项目](calculations/README.md)交付官方配置、可复现代码与分析结果；[独立实验项目](experiments/README.md)为这 106 项各建一个可独立运行的目录（程序、README 与结果），正文在每个实验块之后回填一段简洁结果并链接到对应目录。计算类实验复用统一计算项目的结果，不重复实现公式；实跑类保留完整原始记录、哈希与失败尝试，仍未覆盖的部分逐项写在 `experiments/inventory.json` 的 `remaining` 字段。本书实测 M2 Max 38 核 GPU／96 GB 与 RTX PRO 6000 Blackwell Workstation Edition；H100／4090 保留为历史判断，昇腾使用已有公开证据，配置不同的结果分别使用。

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
