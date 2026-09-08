# OSDI 2025：摘要筛选与重点阅读

已按官方日程中的正式论文顺序阅读 53／53 篇完整摘要；2 篇补读所列正文。下载、首页核对、摘要筛选和正文阅读分别记录。

[逐项手工取舍](screening-osdi-2025.tsv)与[归档清单](../../references/proceedings/OSDI/2025/manifest.json)同步。

| 序号与论文 | 本轮取舍 | 原因与位置 |
| --- | --- | --- |
| 1. [Basilisk: Using Provenance Invariants to Automate Proofs of Undecidable Protocols](../../references/proceedings/OSDI/2025/volume.pdf#page=13) | 排除 | 分布式协议归纳不变量与证明自动化偏形式化方法，不补本书模型、资源和执行主线。 |
| 2. [Deriving Semantic Checkers from Tests to Detect Silent Failures in Production Distributed Systems](../../references/proceedings/OSDI/2025/volume.pdf#page=31) | 备选 | 生产静默错误的语义检查可作 11.6 旁证，但本卷 TrainCheck 更直接针对训练，先不重复采用。 |
| 3. [Picsou: Enabling Replicated State Machines to Communicate Efficiently](../../references/proceedings/OSDI/2025/volume.pdf#page=51) | 排除 | RSM 之间的一致广播不是 GPU 集合通信；不因跨集群字样归入第 7 章。 |
| 4. [FineMem: Breaking the Allocation Overhead vs. Memory Waste Dilemma in Fine-Grained Disaggregated Memory Management](../../references/proceedings/OSDI/2025/volume.pdf#page=69) | 候选待读 | 远程内存分配粒度、MR 注册与隔离可补 7／10 的内存池代价，须区别 KV 格式和一般 malloc。 |
| 5. [To PRI or Not To PRI, That's the question](../../references/proceedings/OSDI/2025/volume.pdf#page=87) | 备选 | VM 设备直通、固定页与超售取舍关联 12 的环境容量；并非每个 Agent 沙箱都需要设备直通。 |
| 6. [Enabling Efficient GPU Communication over Multiple NICs with FuseLink](../../references/proceedings/OSDI/2025/volume.pdf#page=103) | 补读采用 | 已读单篇物理页 2–14；采用多 NIC 与共享 PCIe／GPU 互联的带宽推算于 7.2.3、实验 7-3。保留倾斜流量、空闲借用、中继容量和控制开销边界。 |
| 7. [Tigon: A Distributed Database for a CXL Pod](../../references/proceedings/OSDI/2025/volume.pdf#page=121) | 备选 | CXL pod 的缓存一致性限制可作 4／6 的背景，数据库事务协议不进入正文。 |
| 8. [Mako: Speculative Distributed Transactions with Geo-Replication](../../references/proceedings/OSDI/2025/volume.pdf#page=141) | 排除 | 跨地域事务复制与推测提交偏数据库；不与模型推测解码或超节点通信混淆。 |
| 9. [Quake: Adaptive Indexing for Vector Search](../../references/proceedings/OSDI/2025/volume.pdf#page=165) | 候选待读 | 动态向量索引的召回、延迟与 NUMA 可补 12 的 Agent 检索工具，但限短案例，不扩检索数据库章。 |
| 10. [Achieving Low-Latency Graph-Based Vector Search via Aligning Best-First Search Algorithm with SSD](../../references/proceedings/OSDI/2025/volume.pdf#page=183) | 备选 | SSD ANN 的依赖重排适合检索工具关键路径，需与 Quake 同题比较；不把近似检索质量忽略。 |
| 11. [Skybridge: Bounded Staleness for Distributed Caches](../../references/proceedings/OSDI/2025/volume.pdf#page=199) | 备选 | 可变数据缓存的新鲜度边界可对照版本化状态；不可直接套到不可变模型前缀 KV。 |
| 12. [KPerfIR: Towards a Open and Compiler-centric Ecosystem for GPU Kernel Performance Tooling on Modern AI Workloads](../../references/proceedings/OSDI/2025/volume.pdf#page=217) | 候选待读 | 编译器内可编程 profiling 可补 5 的优化 Agent 反馈；需读探针开销和硬件覆盖，不能把计数器当无扰动真值。 |
| 13. [Mirage: A Multi-Level Superoptimizer for Tensor Programs](../../references/proceedings/OSDI/2025/volume.pdf#page=233) | 候选待读 | Mirage 的多层表示、搜索剪枝和等价验证可补 5；先与现有 MPK／Agent 优化比较，避免增加编译器名单。 |
| 14. [QiMeng-Xpiler: Transcompiling Tensor Programs for Deep Learning Systems with a Neural-Symbolic Approach](../../references/proceedings/OSDI/2025/volume.pdf#page=251) | 候选待读 | LLM 加符号修复的跨平台转换适合 5 的正确性与调优，摘要 95% 转换成功不等于全部正确或性能可移植。 |
| 15. [WaferLLM: Large Language Model Inference at Wafer Scale](../../references/proceedings/OSDI/2025/volume.pdf#page=269) | 候选待读 | WaferLLM 可补 4／13 的分布式片上存储与模型并行；需核实整片成本、容量、精度及 A100 集群基线。 |
| 16. [BlitzScale: Fast and Live Large Model Autoscaling with O(1) Host Caching](../../references/proceedings/OSDI/2025/volume.pdf#page=287) | 候选待读 | 按层开始服务与 GPU 网络扩容可补 10.6／12.2，须与 Breaking the Ice 的启动阶段及队列同算。 |
| 17. [Bayesian Code Diffusion for Efficient Automatic Deep Learning Program Optimization](../../references/proceedings/OSDI/2025/volume.pdf#page=307) | 候选待读 | Ansor 上的成本模型与搜索预算可对照 5 的 LLM Agent；编译搜索省时与生成程序省时分别计量。 |
| 18. [Training with Confidence: Catching Silent Errors in Deep Learning Training with Automated Proactive Checks](../../references/proceedings/OSDI/2025/volume.pdf#page=325) | 候选待读 | TrainCheck 直接针对训练静默错误，适合 11.6 的有效进展；读检查范围、漏报及运行开销后取舍。 |
| 19. [Neutrino: Fine-grained GPU Kernel Profiling via Programmable Probing](../../references/proceedings/OSDI/2025/volume.pdf#page=343) | 候选待读 | Neutrino 的指令探针可补 5 的自动 profile，先与 KPerfIR 比较粒度、侵入性与跨 GPU 支持。 |
| 20. [Principles and Methodologies for Serial Performance Optimization](../../references/proceedings/OSDI/2025/volume.pdf#page=369) | 备选 | 作为编辑方法参照保留；正文不另列八种优化分类，以免恢复抽象模板式讲法。 |
| 21. [Söze: One Network Telemetry Is All You Need for Per-flow Weighted Bandwidth Allocation at Scale](../../references/proceedings/OSDI/2025/volume.pdf#page=387) | 备选 | 加权带宽分配关联 7／12 的共享链路，但摘要实验为一般数据分析，须用 AI 流量再计算。 |
| 22. [Decouple and Decompose: Scaling Resource Allocation with DeDe](../../references/proceedings/OSDI/2025/volume.pdf#page=405) | 候选待读 | DeDe 的可分资源优化可补 12 的调度规模与求解开销，先明确约束结构和近似条件。 |
| 23. [Quantum Virtual Machines](../../references/proceedings/OSDI/2025/volume.pdf#page=423) | 排除 | 量子虚拟机超出 AI Infra 的 GPU／CPU 运行环境范围。 |
| 24. [QOS: Quantum Operating System](../../references/proceedings/OSDI/2025/volume.pdf#page=441) | 排除 | 量子操作系统的保真与资源管理超出本书范围。 |
| 25. [Scalio: Scaling up DPU-based JBOF Key-value Store with NVMe-oF Target Offload](../../references/proceedings/OSDI/2025/volume.pdf#page=461) | 备选 | DPU 存储目标端 CPU 瓶颈可补 10 的 KV 池路径，通用键值一致性细节不展开。 |
| 26. [Low End-to-End Latency atop a Speculative Shared Log with Fix-Ante Ordering](../../references/proceedings/OSDI/2025/volume.pdf#page=477) | 备选 | 推测共享日志可作 11 的持久化旁证，不能与 token WAL 或 router replay 视为同一机制。 |
| 27. [Understanding Stragglers in Large Model Training Using What-if Analysis](../../references/proceedings/OSDI/2025/volume.pdf#page=495) | 候选待读 | 训练慢节点的 what-if 分析直接补 11.6／13：通信等待与根因分开，避免把慢 rank 一律判硬件坏。 |
| 28. [Fork in the Road: Reflections and Optimizations for Cold Start Latency in Production Serverless Systems](../../references/proceedings/OSDI/2025/volume.pdf#page=511) | 候选待读 | AFaaS 的控制路径、并发争用与用户初始化适合 12 的 Serverless／E2B，不能用组件快照时间代表端到端。 |
| 29. [Kamino: Efficient VM Allocation at Scale with Latency-Driven Cache-Aware Scheduling](../../references/proceedings/OSDI/2025/volume.pdf#page=531) | 备选 | VM 分配控制面的缓存与延迟不同于 KV 路由；可补 12 的平台控制成本，不单开调度案例。 |
| 30. [ZEN: Empowering Distributed Training with Sparsity-driven Data Synchronization](../../references/proceedings/OSDI/2025/volume.pdf#page=549) | 候选待读 | 稀疏梯度同步适合 7／11，但要先核实模型真实梯度稀疏度，不能由 MoE 稀疏激活直接推出梯度通信稀疏。 |
| 31. [Extending Applications Safely and Efficiently](../../references/proceedings/OSDI/2025/volume.pdf#page=569) | 备选 | 用户态扩展的最小资源接口可对照 12 工具环境，底层 eBPF／二进制改写细节不扩写。 |
| 32. [Tintin: A Unified Hardware Performance Profiling Infrastructure to Uncover and Manage Uncertainty](../../references/proceedings/OSDI/2025/volume.pdf#page=587) | 候选待读 | 性能计数器复用和归因不确定性适合 5／13 的反馈质量，与 GPU 探针案例比较后择用。 |
| 33. [Building Bridges: Safe Interactions with Foreign Languages through Omniglot](../../references/proceedings/OSDI/2025/volume.pdf#page=607) | 排除 | Rust 外部库安全边界属于语言互操作，不新增到模型执行章节。 |
| 34. [KRR: Efficient and Scalable Kernel Record Replay](../../references/proceedings/OSDI/2025/volume.pdf#page=627) | 备选 | 内核 record replay 可作 12 的环境复现背景；并非 GPU graph replay、MoE router replay 或完整外部工具重现。 |
| 35. [Deterministic Client: Enforcing Determinism on Untrusted Machine Code](../../references/proceedings/OSDI/2025/volume.pdf#page=645) | 备选 | 确定性沙箱的计量与抢占可补 12 的环境保证，需说明外部输入和机器码边界，不借智能合约结果推 AI 性能。 |
| 36. [Disentangling the Dual Role of NIC Receive Rings](../../references/proceedings/OSDI/2025/volume.pdf#page=663) | 候选待读 | NIC 接收缓冲与 LLC／DRAM 压力可补 7／8 的 AI 传输主机路径；软件仿真与实际 NIC 分开。 |
| 37. [XSched: Preemptive Scheduling for Diverse XPUs](../../references/proceedings/OSDI/2025/volume.pdf#page=683) | 候选待读 | XSched 的不同抢占能力适合 12 资源调度，并与 5 的长 kernel／图执行衔接；跨平台保证逐项核实。 |
| 38. [OS Rendering Service Made Parallel with Out-of-Order Execution and In-Order Commit](../../references/proceedings/OSDI/2025/volume.pdf#page=705) | 排除 | 手机 OS 渲染优化与本书 Computer Use 截图传输不是同一瓶颈，不扩成 UI 渲染专题。 |
| 39. [EMT: An OS Framework for New Memory Translation Architectures](../../references/proceedings/OSDI/2025/volume.pdf#page=723) | 备选 | CPU 内存翻译的可扩展架构可作 10 的主存案例背景，不展开内核移植实现。 |
| 40. [Tiered Memory Management Beyond Hotness](../../references/proceedings/OSDI/2025/volume.pdf#page=743) | 候选待读 | 访存热度与关键路径收益不同，可补 10 的异构内存放置；AOL 的 CPU 模型不能直接套 GPU KV。 |
| 41. [NanoFlow: Towards Optimal Large Language Model Serving Throughput](../../references/proceedings/OSDI/2025/volume.pdf#page=761) | 补读采用 | 已读单篇物理页 2–15；采用独占／并发 profiling 和切分争用于 5.3.5／9.1.4／10.4.3。整体 compute-bound 限定大 batch 与历史模型，不外推到所有推理。 |
| 42. [PipeThreader: Software-Defined Pipelining for Efficient DNN Execution](../../references/proceedings/OSDI/2025/volume.pdf#page=779) | 候选待读 | PipeThreader 可补 5 的软件流水和真实 TileLang 实现，先比较现有 FA4／自动优化内容后决定替换。 |
| 43. [WLB-LLM: Workload-Balanced 4D Parallelism for Large Language Model Training](../../references/proceedings/OSDI/2025/volume.pdf#page=797) | 候选待读 | 按文档长度平衡 PP／CP 可补 6／11 的工作量推算；等 token 不等 attention 工作，与第 2／9 章关联。 |
| 44. [DecDEC: A Systems Approach to Advancing Low-Bit LLM Quantization](../../references/proceedings/OSDI/2025/volume.pdf#page=815) | 候选待读 | DecDEC 用 CPU 残差补偿量化质量可补 9.4／10.3；须计主存容量、按步访问及 RTX 4050 条件。 |
| 45. [Stripeless Data Placement for Erasure-Coded In-Memory Storage](../../references/proceedings/OSDI/2025/volume.pdf#page=833) | 备选 | 内存池冗余放置关联 10 的可用容量，纠删码构造不进入正文，先用恢复目标约束。 |
| 46. [PoWER Never Corrupts: Tool-Agnostic Verification of Crash Consistency and Corruption Detection](../../references/proceedings/OSDI/2025/volume.pdf#page=851) | 排除 | 持久内存存储形式化证明超出训练 checkpoint 与 KV 持久化所需层次。 |
| 47. [Fast and Synchronous Crash Consistency with Metadata Write-Once File System](../../references/proceedings/OSDI/2025/volume.pdf#page=871) | 排除 | PM 文件系统元数据组织较底层，已有持久化路径足以支撑本书恢复主线。 |
| 48. [Decentralized, Epoch-based F2FS Journaling with Fine-grained Crash Recovery](../../references/proceedings/OSDI/2025/volume.pdf#page=891) | 排除 | Android F2FS 日志不是训练 checkpoint 或模型状态恢复，避免因 checkpoint 关键词误收。 |
| 49. [Okapi: Decoupling Data Striping and Redundancy Grouping in Cluster File Systems](../../references/proceedings/OSDI/2025/volume.pdf#page=909) | 备选 | 条带与冗余解耦可作 11 的 checkpoint 存储比较，优先有 AI 负载的论文。 |
| 50. [Compass: Encrypted Semantic Search with High Accuracy](../../references/proceedings/OSDI/2025/volume.pdf#page=927) | 备选 | 加密语义检索可作 Agent 私有检索延迟边界，不扩 ORAM 专章。 |
| 51. [Weave: Efficient and Expressive Oblivious Analytics at Scale](../../references/proceedings/OSDI/2025/volume.pdf#page=951) | 排除 | 隐私分布式分析的访问模式保护与本书模型推理／训练主线距离较远。 |
| 52. [Paralegal: Practical Static Analysis for Privacy Bugs](../../references/proceedings/OSDI/2025/volume.pdf#page=969) | 排除 | Rust 隐私静态分析与 AI 系统资源推算关联不足。 |
| 53. [MettEagle: Costs and Benefits of Implementing Containers on Microkernels](../../references/proceedings/OSDI/2025/volume.pdf#page=991) | 候选待读 | 微内核容器可作 12 的隔离边界对照，保留 CVE 分析与实测范围，不由架构直接保证安全。 |

## 重点章节与采用边界

- **Enabling Efficient GPU Communication over Multiple NICs with FuseLink**：设计、实现、评估、限制及正文结尾；参考文献未逐项读。采用多 NIC 共享路径、借用资源与控制开销于 7.2.3、实验 7-3，并接 10.2。；原整卷物理页 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115。
- **NanoFlow: Towards Optimal Large Language Model Serving Throughput**：设计、计算、实现、评估与正文结尾；参考文献未逐项读。采用独占／并发 profiling、nano-batch 与吞吐前提于 5.3.5、9.1.4、10.4.3。；原整卷物理页 761, 762, 763, 764, 765, 766, 767, 768, 769, 770, 771, 772, 773, 774。

具体推算和采用决策另记案例笔记；新增候选不自动进入正文。历史实验的模型、软件、硬件和质量条件保持原样，本书贯穿模型继续使用 Qwen3／V4／K3。
