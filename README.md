# 《深入理解 AI Infra：量化分析与系统设计》

这本书从真实的研究和设计选择讲 AI Infra：当时为什么这样设计，负载变化后哪里先不够用，又怎样用几笔计算找到下一步值得做的事。读者应能建立一个足够简单、又能帮助作判断的系统模型。

目前完成结构与逐章写作大纲，尚未扩写正式书稿。

- [书的 skeleton](skeleton.html)：草案 21，整体叙述方式、十三章安排、实验与图的制作策略。
- [逐章 Markdown 大纲](outlines/README.md)：每章一个文件，包含节、小节、拟讲内容、实验与配图；后续在此扩写。
- [编辑笔记](outlines/editorial-notes.md)：原文版本、规格差异与需要补充的材料。
- [资料核对记录](outlines/research-notes.md)与[全库对应表](outlines/source-map.md)：说明实际阅读、线上复核和资料落点。

## 这本书怎样讲

第一章先讲从云数据中心到 AI 数据中心的变化：可编程性的主要表达层与系统抽象边界上移到大模型，底层设计围绕模型执行重新组织。随后从集群、超节点、主机与加速卡逐层进入芯片内部，再联系软件全栈。由 Jeff Dean 在 CPU 时代的关键数字进入 GPU 的算力、容量、带宽与互联，用纸笔估算建立分析方法，再回看 Google TPU、作者的可编程网卡研究和 GPT-3 对 UB 项目的影响。第 12 章接回通用工具执行中的多租户、虚拟化与运行环境。

量化研究从简单估算开始。先数状态、字节、计算和依赖，用容量、Roofline、最窄链路或关键路径排除明显不合要求的方案，再用小实验检查剩下的选择。只有更细的信息可能改变判断时，才增加模型细节或仿真。数字首次出现时解释单位，每步换算后说明设计意义。

H100／4090 保留历史选择问题，A100／A800、H20、H100／B200 在具体模型、请求和训练期限下反复推算；NVIDIA、昇腾和 Apple 沿计算、存储和搬运逐层比较。数据中心网络承接超节点的边界与扩展，借鉴作者网络与 UB 文章解释设计的方式。模型计算、推算实验和历史案例都能回到第一章的[全景图](skeleton.html#infra-panorama)上定位。

## 章节安排

1. [初识 AI Infra](outlines/01-%E5%88%9D%E8%AF%86%20AI%20Infra.md)：从可编程性与系统抽象边界上移解释云到 AI 数据中心的变化，再建立全景与量化方法。
2. [模型架构](outlines/02-%E6%A8%A1%E5%9E%8B%E6%9E%B6%E6%9E%84.md)：用 Qwen3 跟算，比较 DeepSeek-V4 与 Kimi K3 的 prefill／decode 计算、常驻容量和访问。
3. [推理与训练负载](outlines/03-%E6%8E%A8%E7%90%86%E4%B8%8E%E8%AE%AD%E7%BB%83%E8%B4%9F%E8%BD%BD.md)：分推理与训练两块组织请求、阶段与计算预算，结合公开投入理解规模选择。
4. [加速器架构](outlines/04-%E5%8A%A0%E9%80%9F%E5%99%A8%E6%9E%B6%E6%9E%84.md)：从负载和瓶颈解释计算、存储、搬运的架构取舍，将各家代际演进穿插其中。
5. [算子与运行时](outlines/05-%E7%AE%97%E5%AD%90%E4%B8%8E%E8%BF%90%E8%A1%8C%E6%97%B6.md)：沿真实算子推算复用、融合、编译调优与 Agent 性能反馈，再比较图执行和细粒度流水。
6. [超节点](outlines/06-%E8%B6%85%E8%8A%82%E7%82%B9.md)：用具体模型推算 TP、PP、DP、EP，比较容量、计算、访存与卡间通信。
7. [数据中心网络](outlines/07-%E6%95%B0%E6%8D%AE%E4%B8%AD%E5%BF%83%E7%BD%91%E7%BB%9C.md)：沿既定切分计算跨超节点训练、集合通信和八卡服务器间的大模型推理。
8. [端边云协同](outlines/08-%E7%AB%AF%E8%BE%B9%E4%BA%91%E5%8D%8F%E5%90%8C.md)：用图片精修、ASR／TTS 和 Computer Use，推算传输、执行位置与逐轮交互的优化。
9. [单实例推理](outlines/09-%E5%8D%95%E5%AE%9E%E4%BE%8B%E6%8E%A8%E7%90%86.md)：用 Qwen 贯穿请求调度、近期推测解码和本地量化，计算业务要求下的设备选择。
10. [分布式推理](outlines/10-%E5%88%86%E5%B8%83%E5%BC%8F%E6%8E%A8%E7%90%86.md)：沿相同模型和请求推算 PD／AF、少量 GPU 的异构服务、持久化 KV 与共享池。
11. [训练系统](outlines/11-%E8%AE%AD%E7%BB%83%E7%B3%BB%E7%BB%9F.md)：用具体训练任务推算资源与期限，以真实后端讨论通信重叠、RL 阶段配比和 Routing Replay。
12. [资源调度与运行环境](outlines/12-%E8%B5%84%E6%BA%90%E8%B0%83%E5%BA%A6%E4%B8%8E%E8%BF%90%E8%A1%8C%E7%8E%AF%E5%A2%83.md)：承接抽象边界上移，讨论调度、模型路由与通用工具环境中的多租户、虚拟化和任务成本。
13. [架构协同设计](outlines/13-%E6%9E%B6%E6%9E%84%E5%8D%8F%E5%90%8C%E8%AE%BE%E8%AE%A1.md)：综合模型、硬件、互联与平台，用下界和最小实验判断新设计。

第 1–4 章建立全景、方法、模型、负载与硬件认识；第 5–8 章沿执行、超节点、数据中心网络与端边云推进；第 9–13 章组织推理、训练、CPU 环境与协同设计。

## 实验与图

每章 5–10 项实验与计算，本轮为 7–10 项，实验与配图均放在对应小节中。基础活动以手算、小脚本和已有记录分析为主，编程与设备测量用于检验已经形成的预测；少量进阶活动使用特定设备或模拟。固定案例尽量跨章复用，让读者看见同一判断怎样逐步修正。

机制图、结构图和时序图主要自绘 SVG；数据图和理论曲线由公式、数据与脚本生成 SVG／PDF。少量芯片原图采用论文或官方来源，保留图号、版本及使用状态。每张图说明它帮助回答什么问题，重要结果图与实验共用输入。详细约定见[大纲索引](outlines/README.md)。实验代码、配套数据和正式图片尚待扩写时制作。

本书拟实测以 M2 Max 38 核 GPU／96 GB 和 RTX PRO 6000 Blackwell Workstation Edition 为主。H100／4090 是另外的历史案例；昇腾依据公开文档和论文，目前没有本书实机测量。不同模型、后端、精度与年代的结果分别使用。

## 材料入口

- [草案 14／15 新增内容的保留审计](research/draft14-15-outline-audit/report.md)：比较到草案 14 的增量，并用草案 15 同期审阅核对后续变化；补回 5 处占位，明确独立草案 15 原件未找到的证据限制。
- [草案 11 与当前大纲的完整对照](research/draft11-outline-audit/report.md)：[112 项取舍与原文定位](research/draft11-outline-audit/decision-matrix.md)，保留修改前快照；补入 9 处章节占位和 [4 项配套材料占位](outlines/writing-support.md)。
- [系统抽象边界上移调研](research/system-abstraction-boundary/report.md)：恢复旧版 skeleton 的可编程性主线，保存[历史原件与官方资料](references/outline-checks/2026-09-08/system-abstraction/README.md)，以简短占位衔接第一章与第 12 章。
- [2023—2026 年 token 成本下降调研](research/token-cost-2023-2026/report.md)：完整报告、[67 项原始资料](references/token-cost/2026-09-07/README.md)及[章节落点](research/token-cost-2023-2026/outline-placement.md)；大纲只加入指向报告的简短占位。
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
