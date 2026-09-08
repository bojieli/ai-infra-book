# ASPLOS 2024：摘要筛选与取舍

按官方主日程顺序完成 **193／193** 篇完整摘要筛选，另选读 Korch 作者版本的 13 个物理页面。[逐项记录](screening-asplos-2024.tsv)与[归档清单](../../references/proceedings/ASPLOS/2024/manifest.json)逐项对应；下载、摘要筛选与正文选读分别计数；其余候选正文尚未核完。

优先比较下面几组能补充设计判断的材料。除下面明确声明的 Korch 正文范围外，不采用候选摘要中的速度、成本或可靠性数字。

| 候选 | 希望增加的判断 | 与已有内容的关系 |
| --- | --- | --- |
| 5. TCCL | 同一 PCIe 拓扑为什么有多种可行通信路径，单流最快的路径在并发时是否仍好 | 对照第 6→7→11 章的 rPCIeBench、AutoCCL；只有补出不同的路径选择约束才加入 |
| 6. Centauri；7. T3 | 通信原语、分组和分块如何改变重叠；何时需要硬件支持 | 与已有 TBO／DBO、NanoFlow 和通信调优区分，研究硬件不写成框架默认能力 |
| 11. A Journey of a 1,000 Kernels Begins with a Single Step | 从负载和执行层次解释三代 GPU 的瓶颈变化 | 服务第 4→5 章的架构演进；保留历史模型和框架条件 |
| 27. SMART；28. CC-NIC | 为什么链路带宽没有满，远端访问仍不再扩展；一致接口怎样改变通知和缓存成本 | 第 7／10 章已有内存池案例，补充 IOPS／延迟约束即可，不扩成 RDMA API 教程 |
| 30. ExeGPT；32. SpotServe | 输入输出分布、可抢占资源和状态迁移怎样改变配置收益 | 与 Sarathi、ServeGen、RLBoost 候选去重；不再用旧基线描述当前 vLLM／SGLang |
| 35. Loupe；39. LFI | sandbox 需要支持哪些工具，隔离密度和实际内存怎样计算 | 第 12 章以 Agent 工具执行为落点；兼容子集、地址空间和驻留内存分开 |
| 44. RAP；45. MAGIS；47. Cocco | 融合、拆分、重算、存储容量与并发干扰怎样共同决定执行方式 | 对照第 4／5／11 章已有图优化内容，只保留一个能算清楚的新增取舍 |

SpecInfer 只保留推测执行的历史线索；第 9 章已采用更新工作，不再为旧系统新增小节。安全攻击、二进制反汇编等论文有各自价值，但没有直接增加本书的模型资源推算能力，逐项记录排除理由。

第二批继续逐项阅读第 49–96 篇完整摘要。Explainable-DSE、BaCO、MiniMalloc 分别保留瓶颈指导设计、搜索预算和静态缓冲规划线索；FaaSMem／CodeCrunch／RainbowCake 比较 Serverless 内存和冷启动；POLCA／FOCAL 涉及功率与生命周期成本。AttAcc／NeuPIMs 留作异构注意力案例的候选，先核硬件与并发条件，再决定是否比现有 AF 案例多提供一个判断。尚未采用这些摘要中的性能数字。

TCCL 的正式 PDF 入口返回 403；已读作者说明、历史 AE 和固定源码的声明范围，另对照当前 NCCL SHM／cuMem 路径。采用的只是在原有实验 6-6 中加入主机中转和 NUMA 放置的[独立教学计算](../../case-studies/pcie-staging-and-numa.md)，第 7.3.3 节补路径判断；没有将该源码跟读计作论文正文阅读。

第三批完成第 97–193 篇完整摘要：编译方面重点比较 Korch／Souffle／SmartMem／MikPoly，内存方面保留 GMT／GMLake，环境方面保留 DataFlower／Fuyao／SEVeriFast，训练方面将 PrimePar／AdaPipe／Heet 与既有并行及调度案例去重。这里只形成候选池，不逐篇增加小节。

## 本届首篇正文选读：Korch

读取[作者 arXiv v1](../../references/proceedings/ASPLOS/2024/selected/korch-arxiv-v1.pdf)物理页 1–13，涵盖动机、设计、公式、实现、评估、局限及 artifact A.1–A.4；14–15 页的余下 artifact／参考文献未逐项读。[页码与版本记录](../../references/proceedings/ASPLOS/2024/selected/korch-reading.json)保留作者修正说明，未声称与正式卷 PDF 字节相同。已查看物理页 12 的图 11–13：Candy 子图的三个／四个 kernel 数与时间可核对；Segformer batch-16 的正文 2.24× 与图中 2.88× 不一致，不采用这组加速比。

采用的是“先拆算子再选择执行边界”与串行实测成本的适用范围，接入第 5.3 和既有实验 5-4／图 5-3。当前 vLLM 的激活量化融合以 Qwen3 同一矩阵补逻辑流量和张量生存期；[计算与取舍](../../case-studies/kernel-orchestration-and-quantization.md)区分旧论文测量和新教学假设。没有运行历史 artifact、模型或 GPU；公开 Korch 生成器不当作可直接运行 Qwen3 的完整服务框架。

本届摘要筛选完成。下一步优先比较少量候选正文及现有框架能力，再决定替换或补入；保持章节、实验和配图数量。
