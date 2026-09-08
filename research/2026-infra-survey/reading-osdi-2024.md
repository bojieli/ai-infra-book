# OSDI 2024：摘要筛选与重点阅读

已按官方日程中的正式论文顺序阅读 53／53 篇完整摘要；3 篇补读所列正文。下载、首页核对、摘要筛选和正文阅读分别记录。

[逐项手工取舍](screening-osdi-2024.tsv)与[归档清单](../../references/proceedings/OSDI/2024/manifest.json)同步。

| 序号与论文 | 本轮取舍 | 原因与位置 |
| --- | --- | --- |
| 1. [Sabre: Hardware-Accelerated Snapshot Compression for Serverless MicroVMs](../../references/proceedings/OSDI/2024/volume.pdf#page=13) | 候选待读 | Sabre 的 Firecracker 快照压缩与预取可补 12.3 的环境就绪时间；依赖特定 CPU 加速器，不能当作 E2B 默认机制。 |
| 2. [Nomad: Non-Exclusive Memory Tiering via Transactional Page Migration](../../references/proceedings/OSDI/2024/volume.pdf#page=31) | 备选，不新增 | Nomad 的非独占 CPU 页迁移可对照 6／10 的多级存储；页影子与 GPU KV 块管理的语义不同。 |
| 3. [Managing Memory Tiers with CXL in Virtualized Environments](../../references/proceedings/OSDI/2024/volume.pdf#page=49) | 备选，不新增 | Memstrata 的 CXL 硬件分层与租户隔离可补 6／12；原型性能与特定 CPU VM 条件不可直接外推 GPU 内存池。 |
| 4. [Harvesting Memory-bound CPU Stall Cycles in Software with MSH](../../references/proceedings/OSDI/2024/volume.pdf#page=69) | 备选，不新增 | MSH 用软件并发利用 CPU 内存停顿，方法可对照 5／12，当前不增加通用 CPU 调度专题。 |
| 5. [A Tale of Two Paths: Toward a Hybrid Data Plane for Efficient Far-Memory Applications](../../references/proceedings/OSDI/2024/volume.pdf#page=89) | 备选，不新增 | Atlas 比较远程内存页级与对象级访问的局部性和 CPU 代价，供 6／10 访问粒度取舍参考。 |
| 6. [DRust: Language-Guided Distributed Shared Memory with Fine Granularity, Full Transparency, and Ultra Efficiency](../../references/proceedings/OSDI/2024/volume.pdf#page=109) | 排除正文 | Rust 所有权辅助 DSM 一致性实现，当前不扩展语言运行时与共享内存专题。 |
| 7. [Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve](../../references/proceedings/OSDI/2024/volume.pdf#page=129) | 补读采用 | 已读单篇物理页 3–12，采用 token 预算及历史长度反例于 9.1、实验 9-2；保留旧模型、TBT 指标和当前实现区别。 |
| 8. [ServerlessLLM: Low-Latency Serverless Inference for Large Language Models](../../references/proceedings/OSDI/2024/volume.pdf#page=147) | 候选待读 | ServerlessLLM 的权重存储层次、迁移和就近启动，补 10.6／12.2；与已读 vLLM 进程启动及后续 FaaScale 比较。 |
| 9. [InfiniGen: Efficient Generative Inference of Large Language Models with Dynamic KV Cache Management](../../references/proceedings/OSDI/2024/volume.pdf#page=167) | 候选待读 | InfiniGen 的 KV 重要性预测与按需预取可和 HiSparse 对照 9／10；选择性读取需保留模型质量和预测开销条件。 |
| 10. [Llumnix: Dynamic Scheduling for Large Language Model Serving](../../references/proceedings/OSDI/2024/volume.pdf#page=185) | 补读采用 | 已读单篇物理页 4–11，采用迁移状态与暂停／复制时间区别于 10.6.1、实验 10-10；不把计划迁移等同于故障恢复。 |
| 11. [DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving](../../references/proceedings/OSDI/2024/volume.pdf#page=205) | 补读采用 | 已读单篇物理页 4–11，采用排队、阶段放置与 KV 速率／延迟推算于 10.2、实验 10-2；保留历史 OPT、链路及实验指标边界。 |
| 12. [ACCL+: an FPGA-Based Collective Engine for Distributed Applications](../../references/proceedings/OSDI/2024/volume.pdf#page=223) | 备选，不新增 | ACCL+ 的 FPGA 集合通信卸载可作 7 的硬件执行位置对照，当前不增加 FPGA MPI 实现细节。 |
| 13. [Beaver: Practical Partial Snapshots for Distributed Cloud Services](../../references/proceedings/OSDI/2024/volume.pdf#page=245) | 备选，不新增 | Beaver 面向有外部流量的分布式部分快照，因果一致性可供 11／12 对照；不能直接等同训练 checkpoint。 |
| 14. [Fast and Scalable In-network Lock Management Using Lock Fission](../../references/proceedings/OSDI/2024/volume.pdf#page=263) | 排除正文 | 可编程交换机的分布式锁服务，主要围绕事务系统，不扩大当前 AI 集合通信主线。 |
| 15. [Chop Chop: Byzantine Atomic Broadcast to the Network Limit](../../references/proceedings/OSDI/2024/volume.pdf#page=281) | 排除正文 | 拜占庭原子广播与认证批处理，超出当前训练和模型服务的故障模型。 |
| 16. [Enabling Tensor Language Model to Assist in Generating High-Performance Tensor Programs for Deep Learning](../../references/proceedings/OSDI/2024/volume.pdf#page=301) | 候选待读 | TLM 用语言模型探索 tensor schedule，可与 2025／2026 Agent 实测反馈对照 5.3，核对调优预算和支持硬件。 |
| 17. [Ladder: Enabling Efficient Low-Precision Deep Learning Computing through Hardware-aware Tensor Transformation](../../references/proceedings/OSDI/2024/volume.pdf#page=319) | 候选待读 | Ladder 把低精度格式、布局和转换纳入编译，可强化 4.2.5／5.3；权重压缩不等于同倍执行加速。 |
| 18. [Caravan: Practical Online Learning of In-Network ML Models with Labeling Agents](../../references/proceedings/OSDI/2024/volume.pdf#page=337) | 排除正文 | 网络流量分类器的在线学习与标注代理，不是本书 Agent 推理或数据中心 AI 通信主线。 |
| 19. [nnScaler: Constraint-Guided Parallelization Plan Generation for Deep Learning Training](../../references/proceedings/OSDI/2024/volume.pdf#page=359) | 候选待读 | nnScaler 用变换、放置和顺序约束并行搜索，接 6／11／13 的先推算后搜索；不把历史模型收益当当前 MoE 保证。 |
| 20. [ChameleonAPI: Automatic and Efficient Customization of Neural Networks for ML Applications](../../references/proceedings/OSDI/2024/volume.pdf#page=377) | 备选，不新增 | ChameleonAPI 按应用决策损失定制模型，可对照 12／13 的任务成功率，当前不增加通用 API 模型训练专题。 |
| 21. [SquirrelFS: using the Rust compiler to check file-system crash consistency](../../references/proceedings/OSDI/2024/volume.pdf#page=399) | 排除正文 | Rust typestate 验证持久内存文件系统崩溃一致性，超出当前训练 checkpoint 与环境恢复主线。 |
| 22. [High-throughput and Flexible Host Networking for Accelerated Computing](../../references/proceedings/OSDI/2024/volume.pdf#page=417) | 候选待读 | ZeroNIC 将 GPU 数据通路与传输控制拆开，适合 7 的主机网络与 SmartNIC 取舍；需核对 FPGA 原型和协议处理位置。 |
| 23. [IntOS: Persistent Embedded Operating System and Language Support for Multi-threaded Intermittent Computing](../../references/proceedings/OSDI/2024/volume.pdf#page=437) | 排除正文 | 无电池间歇嵌入式 OS 的事务恢复，不扩充为本书的边缘 LLM 运行环境。 |
| 24. [Data-flow Availability: Achieving Timing Assurance in Autonomous Systems](../../references/proceedings/OSDI/2024/volume.pdf#page=457) | 备选，不新增 | Kairos 的数据新鲜度与实时约束可对照 8 的逐轮交互，CPS 时序保证与云推理 SLO 不同。 |
| 25. [Microkernel Goes General: Performance and Compatibility in the HongMeng Production Microkernel](../../references/proceedings/OSDI/2024/volume.pdf#page=477) | 备选，不新增 | 鸿蒙微内核的 IPC 频次、重复状态与隔离取舍可供 12 的运行环境参考，不增加通用 OS 架构专题。 |
| 26. [When will my ML Job finish? Toward providing Completion Time Estimates through Predictability-Centric Scheduling](../../references/proceedings/OSDI/2024/volume.pdf#page=499) | 候选待读 | PCS 将训练完成时间可预测性与公平、平均性能做取舍，适合 12.2／11.6；先读误差与调度条件。 |
| 27. [Optimizing Resource Allocation in Hyperscale Datacenters: Scalability, Usability, and Experiences](../../references/proceedings/OSDI/2024/volume.pdf#page=519) | 候选待读 | Meta Rebalancer 的资源约束表达与大规模搜索，适合 12／13 的方案生成，不把形式优化复杂度当第一步。 |
| 28. [μSlope: High Compression and Fast Search on Semi-Structured Logs](../../references/proceedings/OSDI/2024/volume.pdf#page=541) | 排除正文 | 半结构化日志压缩与查询系统，当前不扩展日志存储专题。 |
| 29. [ServiceLab: Preventing Tiny Performance Regressions at Hyperscale through Pre-Production Testing](../../references/proceedings/OSDI/2024/volume.pdf#page=557) | 候选待读 | ServiceLab 用实验设计与统计识别微小回退，可补 5.3／13 的真实反馈和测量噪声；不能把最小可检出值外推所有 GPU 实验。 |
| 30. [MAST: Global Scheduling of ML Training across Geo-Distributed Datacenters at Hyperscale](../../references/proceedings/OSDI/2024/volume.pdf#page=575) | 候选待读 | MAST 协同数据与训练作业的跨地域放置，可补 12.2 的资源供需和迁移条件；明确区别于第 7 章跨超节点通信。 |
| 31. [Automatically Reasoning About How Systems Code Uses the CPU Cache](../../references/proceedings/OSDI/2024/volume.pdf#page=593) | 备选，不新增 | CFAR 的程序分析与 cache 行为估计可对照 5／13 的预测与实测，当前不增加 CPU 二进制分析教程。 |
| 32. [VeriSMo: A Verified Security Module for Confidential VMs](../../references/proceedings/OSDI/2024/volume.pdf#page=611) | 备选，不新增 | VeriSMo 研究机密 VM 安全模块验证，可供 12 区分隔离与机密计算，当前不扩展安全证明专题。 |
| 33. [Validating the eBPF Verifier via State Embedding](../../references/proceedings/OSDI/2024/volume.pdf#page=627) | 排除正文 | eBPF verifier 的正确性测试，超出本书性能观测工具的使用范围。 |
| 34. [Using Dynamically Layered Definite Releases for Verifying the RefFS File System](../../references/proceedings/OSDI/2024/volume.pdf#page=641) | 排除正文 | 并发文件系统的活性与安全证明，不扩展为训练存储系统专题。 |
| 35. [Anvil: Verifying Liveness of Cluster Management Controllers](../../references/proceedings/OSDI/2024/volume.pdf#page=661) | 备选，不新增 | Anvil 的控制器最终收敛可对照 12 的环境生命周期，当前不增加形式验证与 Kubernetes 控制器教程。 |
| 36. [DSig: Breaking the Barrier of Signatures in Data Centers](../../references/proceedings/OSDI/2024/volume.pdf#page=679) | 排除正文 | 微秒数字签名与 BFT/KV 应用，当前不扩大 AI 通信的认证协议范围。 |
| 37. [Ransom Access Memories: Achieving Practical Ransomware Protection in Cloud with DeftPunk](../../references/proceedings/OSDI/2024/volume.pdf#page=699) | 排除正文 | 云块存储的勒索软件检测恢复，与本书模型执行和训练容错的主要问题不同。 |
| 38. [Secret Key Recovery in a Global-Scale End-to-End Encryption System](../../references/proceedings/OSDI/2024/volume.pdf#page=715) | 排除正文 | 通信应用的密钥恢复与异构 enclave 信任，不进入模型服务资源取舍。 |
| 39. [Flock: A Framework for Deploying On-Demand Distributed Trust](../../references/proceedings/OSDI/2024/volume.pdf#page=733) | 排除正文 | 按需分布式信任部署，非当前 AI 计算资源与隔离环境主线。 |
| 40. [FairyWREN: A Sustainable Cache for Emerging Write-Read-Erase Flash Interfaces](../../references/proceedings/OSDI/2024/volume.pdf#page=757) | 备选，不新增 | FairyWREN 用缓存策略与闪存 GC 降低写放大，可供 10.5 持久化 KV 的 SSD 写入成本参考；需另验 KV 访问负载。 |
| 41. [Massively Parallel Multi-Versioned Transaction Processing](../../references/proceedings/OSDI/2024/volume.pdf#page=777) | 排除正文 | GPU 多版本事务处理的数据库并发控制，当前不扩展 OLTP 应用。 |
| 42. [Burstable Cloud Block Storage with Data Processing Units](../../references/proceedings/OSDI/2024/volume.pdf#page=795) | 备选，不新增 | BurstCBS 的 DPU IO 资源计量和突发隔离可对照 7／12；生产块存储并非模型 KV 池的直接实测。 |
| 43. [Motor: Enabling Multi-Versioning for Distributed Transactions on Disaggregated Memory](../../references/proceedings/OSDI/2024/volume.pdf#page=813) | 排除正文 | 分离内存中的 MVCC 事务协议，不扩大本书 KV 状态共享的语义范围。 |
| 44. [Detecting Logic Bugs in Database Engines via Equivalent Expression Transformation](../../references/proceedings/OSDI/2024/volume.pdf#page=833) | 排除正文 | 数据库等价表达式变换测试，当前保留算子正确性方法而不展开 SQL 检错。 |
| 45. [Inductive Invariants That Spark Joy: Using Invariant Taxonomies to Streamline Distributed Protocol Proofs](../../references/proceedings/OSDI/2024/volume.pdf#page=849) | 排除正文 | 分布式协议不变量的自动证明框架，超出量化系统设计主线。 |
| 46. [Performance Interfaces for Hardware Accelerators](../../references/proceedings/OSDI/2024/volume.pdf#page=867) | 候选待读 | 加速器 performance interface 的输入依赖与可执行性能表示，适合 4／5／13 的分析模型边界；先有简单资源预算再讨论更精细表达。 |
| 47. [IronSpec: Increasing the Reliability of Formal Specifications](../../references/proceedings/OSDI/2024/volume.pdf#page=887) | 备选，不新增 | IronSpec 提醒形式规格仍可能写错，可作 13 模型可证伪性的旁证，不增加证明工具章节。 |
| 48. [Identifying On-/Off-CPU Bottlenecks Together with Blocked Samples](../../references/proceedings/OSDI/2024/volume.pdf#page=905) | 候选待读 | bperf／BCOZ 区分在核执行和等待并分析优化因果，可补 5／12／13 的 CPU 准备与关键路径，避免仅看 CPU 利用率。 |
| 49. [dLoRA: Dynamically Orchestrating Requests and Adapters for LoRA LLM Serving](../../references/proceedings/OSDI/2024/volume.pdf#page=923) | 候选待读 | dLoRA 的合并／解合并与请求、adapter 共同迁移，可补已读 Punica／SLoRA 的热度倾斜对照，避免旧版 vLLM 倍数。 |
| 50. [Parrot: Efficient Serving of LLM-based Applications with Semantic Variable](../../references/proceedings/OSDI/2024/volume.pdf#page=941) | 候选待读 | Parrot 暴露跨模型请求的数据依赖，适合 3／12 的 Agent 工作流调度；单请求速度与整个任务完成不同。 |
| 51. [USHER: Holistic Interference Avoidance for Resource Optimized ML Inference](../../references/proceedings/OSDI/2024/volume.pdf#page=959) | 候选待读 | USHER 把算子资源、模型复制和缓存干扰共同估计，适合 9／12／13，多模型共置须保留原负载及 SLO 条件。 |
| 52. [Fairness in Serving Large Language Models](../../references/proceedings/OSDI/2024/volume.pdf#page=977) | 候选待读 | VTC 以输入和输出工作量定义 LLM 服务公平，适合 9.1／12.2；token 成本权重与连续批处理假设需核对。 |
| 53. [MonoNN: Enabling a New Monolithic Optimization Space for Neural Network Inference Tasks on Modern GPU-Centric Architectures](../../references/proceedings/OSDI/2024/volume.pdf#page=1001) | 候选待读 | MonoNN 的整图 kernel 与资源不兼容问题可接 5.4，和 2026 动态 megakernel 比较；静态图前提不能套到全部服务请求。 |

## 重点章节与采用边界

- **Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve**：分块设计、预算、实现、实验设置及部分结果；采用于 9.1.3–9.1.4、实验 9-2，未读剩余页或估读图线；原整卷物理页 130, 131, 132, 133, 134, 135, 136, 137, 138, 139。
  单篇物理页 6 与整卷 133 的抽取文本有图轴刻度差异（200/400/600/800 与 0K/0K/1K/1K）；已查看文本差异，其余本次所读页去空白后相同。不据此取图中数值，也不声称两版字节或图形完全一致。
- **Llumnix: Dynamic Scheduling for Large Language Model Serving**：动态调度、迁移、实现、故障处理、实验设置及部分结果；采用于 10.6.1、实验 10-10，未读剩余页或估读图线；原整卷物理页 187, 188, 189, 190, 191, 192, 193, 194。
- **DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving**：排队分析、放置、实现、实验设置及部分结果；采用于 10.2、实验 10-2，未读剩余页或估读图线；原整卷物理页 207, 208, 209, 210, 211, 212, 213, 214。

具体推算和采用决策另记案例笔记；新增候选不自动进入正文。历史实验的模型、软件、硬件和质量条件保持原样，本书贯穿模型继续使用 Qwen3／V4／K3。
