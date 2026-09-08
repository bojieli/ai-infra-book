# OSDI 2026：摘要筛选与重点阅读

已按官方日程中的正式论文顺序阅读 136／136 篇完整摘要；3 篇补读所列正文。下载、首页核对、摘要筛选和正文阅读分别记录。

[逐项手工取舍](screening-osdi-2026.tsv)与[归档清单](../../references/proceedings/OSDI/2026/manifest.json)同步。

| 序号与论文 | 本轮取舍 | 原因与位置 |
| --- | --- | --- |
| 1. [Strata: Hierarchical Context Caching for Long Context Language Model Serving](../../references/proceedings/OSDI/2026/volume.pdf#page=21) | 候选待读 | 分层 KV 的布局、加载等待与并发未命中可深化 10.5；与已有 HiCache 比较是否同一实现，性能倍数须核对正文条件。 |
| 2. [ECHO: Efficient KV Cache Offloading with Lossless Prefetching for Serving Native Sparse Attention LLMs](../../references/proceedings/OSDI/2026/volume.pdf#page=37) | 候选待读 | 原生稀疏注意力的访问与常驻容量分离、图内缓存管理及预取可补 2／5／10；须确认具体模型，不直接套到 V4／K3。 |
| 3. [No Buffer, No Bottleneck: Efficient Zero-Copy KV Cache Offloading for Long-Context LLMs](../../references/proceedings/OSDI/2026/volume.pdf#page=59) | 候选待读 | GH200／GB200 的 CPU 常驻 KV 直接访问可补 9.4／10.3；零拷贝仍有互联访问，不能外推到普通 PCIe 服务器。 |
| 4. [Simple Is Better: Multiplication May Be All You Need for LLM Request Scheduling](../../references/proceedings/OSDI/2026/volume.pdf#page=75) | 候选待读 | 未缓存 prefill token 与实例负载的简单乘积适合 10.5／12 的估算方法；需要正文的假设、失效条件和真实负载验证。 |
| 5. [Prism: Cost-Efficient Multi-LLM Serving via GPU Memory Ballooning](../../references/proceedings/OSDI/2026/volume.pdf#page=95) | 候选待读 | 多模型突发下的 KV 显存回收与空间／时间复用可补 12.2；先与已有容量调度案例比较，部署规模不代替效果证据。 |
| 6. [Break On Through to the Other Side: Pooling Memory Elastically with RamRyder](../../references/proceedings/OSDI/2026/volume.pdf#page=115) | 备选 | 按内存通道分别供给带宽与容量有助解释 10／12 的资源约束，但 VM 通用内存控制不是 KV 池，暂不展开。 |
| 7. [MAC: Metadata Acceleration for Sustainable Performance in Big-Data Systems with CXL DRAM](../../references/proceedings/OSDI/2026/volume.pdf#page=135) | 备选 | CXL 容量增加后的管理元数据瓶颈可作内存池旁证；NMP 原型与 AI 服务距离较远，不新增专节。 |
| 8. [Finding NEMO: Nimble and Expressive Memory Observability](../../references/proceedings/OSDI/2026/volume.pdf#page=153) | 备选 | 内存控制器遥测的粒度与开销可补性能反馈的边界，现有实验以 GPU 热点为主，先保留不直接采用。 |
| 9. [OBASE: Object-Based Address-Space Engineering to Improve Memory Tiering](../../references/proceedings/OSDI/2026/volume.pdf#page=171) | 备选 | 页内冷热对象混合导致回收失败可解释容量与热度粒度，但主要面向通用非托管程序，不替代模型状态分析。 |
| 10. [MDK: Rethinking the Data Center Memory Reclamation Problem](../../references/proceedings/OSDI/2026/volume.pdf#page=187) | 候选待读 | 从固定容量最小缺失率转向性能约束下可回收容量，适合与 12.2 模型共置比较；MPC 与 GPU KV 指标需明确映射。 |
| 11. [USEC: A User-Requirement-Driven Mandatory Access Control Framework for Operating Systems (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=211) | 排除 | 通用操作系统访问控制配置与兼容性不是本书 CPU 沙箱资源推算的重点，不因安全隔离术语扩大范围。 |
| 12. [Mohabi: Disaggregating and Sandboxing the Firefox JavaScript Engine](../../references/proceedings/OSDI/2026/volume.pdf#page=227) | 备选 | Firefox 引擎内 SFI 可作 12.4 隔离边界的旁证，但不是 Agent 微虚拟机实例，暂不替换 E2B／Firecracker 主例。 |
| 13. [Ichnaea: A Framework for Precise Tracking of Memory Objects](../../references/proceedings/OSDI/2026/volume.pdf#page=249) | 排除 | 内存保护键驱动的逐对象取证偏通用调试与安全，未提供直接 AI 执行案例，现有 profiling 主线足够。 |
| 14. [Extracting Database Access-Control Policies from Web Applications](../../references/proceedings/OSDI/2026/volume.pdf#page=269) | 排除 | Ruby 应用的数据库访问策略提取不属于模型计算、资源或运行环境主线。 |
| 15. [iLand: An Instruction-Level Dynamic Binary Instrumentation Framework for iOS](../../references/proceedings/OSDI/2026/volume.pdf#page=291) | 排除 | iOS 无 JIT 条件下的动态插桩与应用隐私分析偏移动安全，不补本书 AI 传输与端侧执行的关键推算。 |
| 16. [Tessera: A Holistic Pipeline Parallelism Framework for Trillion-Parameter Heterogeneous MoE Training (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=307) | 候选待读 | 异构 MoE 层按重叠后的成本切 PP、再填路由气泡，直接补 6／11 的具体模型切分；优先核对生产与公开基线。 |
| 17. [Hetu v2: A General and Scalable Deep Learning System with Hierarchical and Heterogeneous Single Program Multiple Data Annotations](../../references/proceedings/OSDI/2026/volume.pdf#page=325) | 候选待读 | 非对称分片、分层通信与动态图切换可连接 6 的约束和 11 的异构训练；先判断是否比现有并行案例新增解释能力。 |
| 18. [Syncopate: Efficient Multi-GPU AI Kernels via Automatic Chunk-Centric Compute-Communication Overlap](../../references/proceedings/OSDI/2026/volume.pdf#page=351) | 候选待读 | 将通信 chunk 与 kernel 结构分开、自动细粒度重叠可补 5.4／11.3；与已有 NanoFlow／DBO 区别及合法性待正文确认。 |
| 19. [Teaching the Old Dog New Tricks: Building Efficient Data Pipelines for Large-Scale LLM Pre-Training (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=369) | 候选待读 | 生产预训练的评测检查点分发、加载争用和多模态 CPU 转换可补 11.4；跨数据中心场景不混入第 7 章超节点网络。 |
| 20. [Cocoon: A System Architecture for Differentially Private Training with Correlated Noises](../../references/proceedings/OSDI/2026/volume.pdf#page=387) | 备选 | 相关噪声 DP 训练的多级内存与 NMP 有明确资源分析，但隐私训练不是本书主负载，先不引入整套算法。 |
| 21. [ValScope: Value-Semantics-Aware Metamorphic Testing for Detecting Logical Bugs in DBMSs](../../references/proceedings/OSDI/2026/volume.pdf#page=407) | 排除 | 数据库查询逻辑缺陷的变形测试偏 DBMS 验证，与模型数值一致性不是同一问题。 |
| 22. [The Abstention Protocol: RCA for Clos Fabrics (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=425) | 备选 | Clos 故障归因的证据不足处理可补 7.6 诊断边界，但生产网络 RCA 细节先不进入模型并行主线。 |
| 23. [When Sampling Lies: Trustworthy Performance Profiling for Flat Workloads with Blink (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=443) | 备选 | 短函数平坦负载下采样误差可提醒 5.3 的测量反馈不绝对可信；移动 CPU 编译器结论不直接当 GPU profiler 行为。 |
| 24. [Breaking the Reward Barrier: Accelerating Tree-of-Thought Reasoning via Speculative Exploration](../../references/proceedings/OSDI/2026/volume.pdf#page=457) | 候选待读 | 奖励依赖限制 ToT 并行，推测探索与 token 级推测解码可分开说明；适合 3／10 的 reasoning 任务，质量与额外工作待核对。 |
| 25. [Controlling Opaque-Component Effects with Semisolates and Try](../../references/proceedings/OSDI/2026/volume.pdf#page=473) | 备选 | 不透明组件的副作用控制与 Agent 工具执行相邻，可补 12.4 的恢复语义；不同于资源隔离或 VM 快照，暂不加机制细节。 |
| 26. [SBB: Eliminating Centralized Bottlenecks in Userspace Network Runtime](../../references/proceedings/OSDI/2026/volume.pdf#page=493) | 备选 | 用户态抢占、核分配与两级负载均衡可补 CPU 执行池，但通用网络 runtime 不是模型请求调度，不单设篇幅。 |
| 27. [Rakaia: Scalable In-Kernel Scheduling for TCP-Based RPCs](../../references/proceedings/OSDI/2026/volume.pdf#page=511) | 备选 | TCP RPC 消息化可解释 CPU 调度与队头阻塞；本书第 8／12 章优先 AI 交互实例，暂保留通用机制旁证。 |
| 28. [kSTEP: Characterization and Deterministic Testing of Linux CPU Scheduler Bugs](../../references/proceedings/OSDI/2026/volume.pdf#page=529) | 排除 | Linux 调度器确定性测试与缺陷触发偏内核验证，不能因确定性术语并入模型 batch invariance。 |
| 29. [What Are You (M)Waiting For: The Hidden Cost of Idle in the Hyperscale Cloud (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=549) | 候选待读 | 超售 VM 的空闲可见性与尾延迟直接影响 12.4 沙箱并发；需保留 mwait 与硬件条件，不把 CPU 空闲直接当可回收容量。 |
| 30. [Xkernel: Principled Performance Tunability of Operating System Kernels](../../references/proceedings/OSDI/2026/volume.pdf#page=567) | 排除 | 运行时修改内核性能常量及二进制安全性偏 OS 内部实现，不补本书少量关键资源约束的主线。 |
| 31. [Murakkab: Resource-Efficient Agentic Workflow Orchestration in Cloud Platforms](../../references/proceedings/OSDI/2026/volume.pdf#page=587) | 候选待读 | Agent 工作流把模型、硬件和质量约束一起配置，可补 12／13 的任务成本；需核对如何守住质量及配置转换开销。 |
| 32. [ECO: An AI-Driven Code Efficiency Optimizer for Warehouse Scale Computers (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=609) | 候选待读 | 生产 LLM 优化器先定位机会再验证、部署反馈，适合 5.3.5 的 Agent 优化讨论；CPU fleet 结果不能当 GPU kernel 加速。 |
| 33. [StriaTrace: Efficient Tracing and Diagnosis for Online LLM Inference (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=647) | 候选待读 | 在线推理按关键同步点与异常触发追踪，可补 9／13 的尾延迟定位及 5 的低扰动 profiling；模型拟合不替代理论下界。 |
| 34. [Diagnosing Performance Issues in Application-Defined Resources](../../references/proceedings/OSDI/2026/volume.pdf#page=667) | 备选 | 应用内缓冲与队列等资源语义补充系统计数器，可用于 KV 或沙箱等待的类比；当前评估为通用程序，不另设节。 |
| 35. [hS: Speculative Script Reordering at Subprocess Granularity](../../references/proceedings/OSDI/2026/volume.pdf#page=685) | 备选 | 子进程推测执行及副作用提交与 Agent 工具链相邻；不同于 token 级推测解码，暂不加入第 9 章机制清单。 |
| 36. [Incr: Faster Re-Execution via Bolt-On Incrementalization](../../references/proceedings/OSDI/2026/volume.pdf#page=703) | 备选 | 重执行中的依赖与中间结果复用可用于 12 的工具恢复旁证，但 shell 工作负载不是模型 KV 复用，暂不展开。 |
| 37. [A Compilation-Based Under-Constrained Execution Engine](../../references/proceedings/OSDI/2026/volume.pdf#page=721) | 排除 | 隔离函数的欠约束执行与内核缺陷检测偏软件验证，不直接增加 AI 资源分析能力。 |
| 38. [Aletheia: Automated Detection of Data Integrity Violations in Microservices](../../references/proceedings/OSDI/2026/volume.pdf#page=741) | 排除 | 微服务数据完整性静态检测与本书模型状态／训练概率一致性不同，不因数据流术语扩写。 |
| 39. [Arctic: A Practical Lock-Free Adaptive Radix Tree](../../references/proceedings/OSDI/2026/volume.pdf#page=759) | 排除 | 数据库无锁 ART 索引与 SGLang KV 前缀缓存不是同一层问题，不因 radix tree 名称引入。 |
| 40. [Efficient and Scalable Synchronization via Generalized Cache Coherence](../../references/proceedings/OSDI/2026/volume.pdf#page=775) | 备选 | 在一致性层实现同步可补 UB 内存语义的设计对照，但研究平台和通用锁性能不等于现有 UB 实现。 |
| 41. [Shaving the Peaks: Taming Tail Latency for Managed Workloads via Disaggregated Garbage Collection](../../references/proceedings/OSDI/2026/volume.pdf#page=793) | 备选 | 将 Java GC 标记阶段卸载可说明 CPU 服务争用，暂不替换 Agent 沙箱／工具执行的直接案例。 |
| 42. [DeLFS: A Decentralized Log-Structured File System for Manycores](../../references/proceedings/OSDI/2026/volume.pdf#page=813) | 排除 | 多核日志文件系统锁与元数据组织偏存储内核，现有训练 IO 案例更直接。 |
| 43. [Weave: Efficient Co-Scheduling for Disaggregated RL Post-Training](../../references/proceedings/OSDI/2026/volume.pdf#page=829) | 采用 | 用多个 on-policy RL 作业交错填补分离集群等待，且显式限制主机状态驻留；H20／H800 实验适合 11.5→12.2 的资源配比对照。 |
| 44. [RLinf: Flexible and Efficient Large-Scale Reinforcement Learning via Macro-to-Micro Flow Transformation](../../references/proceedings/OSDI/2026/volume.pdf#page=849) | 候选待读 | RL 工作流的时空切分、上下文切换与弹性流水可补 11.5；与 Weave、DynaRL 比较后选少量代表，避免框架罗列。 |
| 45. [DynaRL: Flexible and Dynamic Scheduling of Large-Scale Reinforcement Learning Training](../../references/proceedings/OSDI/2026/volume.pdf#page=867) | 候选待读 | 多轮工具长尾导致阶段瓶颈迁移，动态调资源及其迁移代价可补 12.2；先与静态配比和跨作业填闲区分。 |
| 46. [RollArt: Disaggregated Multi-Task Agentic RL Training at Scale](../../references/proceedings/OSDI/2026/volume.pdf#page=883) | 候选待读 | 按轨迹解耦 Agent 环境、奖励及 PD 异构执行，连接 11.5 与 12 的 CPU 工具池；需核对异步策略界限及失败环境处理。 |
| 47. [Seer: Online Context Learning for Fast Synchronous LLM Reinforcement Learning](../../references/proceedings/OSDI/2026/volume.pdf#page=903) | 候选待读 | 同 prompt 的组内长度关联用于同步 rollout 长尾调度和推测解码，可补 11.5；不把统计预测当确定长度。 |
| 48. [Harvesting Sub-Microsecond CXL Memory Stalls with LiteSwitch](../../references/proceedings/OSDI/2026/volume.pdf#page=923) | 备选 | CXL 停顿与快速线程切换说明容量扩展的延迟代价，但需要新增硬件且不是现有沙箱默认能力。 |
| 49. [Duhu: Shared Disaggregated Memory for Distributed Data Processing Frameworks](../../references/proceedings/OSDI/2026/volume.pdf#page=941) | 备选 | Ray 对象共享与弱一致性协调可旁证 12 的状态搬移；数据处理 shuffle 结果不等于 RL rollout 状态迁移。 |
| 50. [Blowfish: Elastic Virtual Machine Memory for Disaggregated Memory](../../references/proceedings/OSDI/2026/volume.pdf#page=959) | 候选待读 | 跨 VM 冷内存回收和恢复直接关系 12.4 沙箱密度，需区分空闲容量、可回收容量及恢复尾延迟。 |
| 51. [Espresso: Constructing Cost-Efficient CXL JBOF via Inter-SSD Computing Resource Sharing](../../references/proceedings/OSDI/2026/volume.pdf#page=977) | 排除 | SSD 内部控制器资源共享偏存储设备设计，暂不补 KV 层级缓存的数据搬移主线。 |
| 52. [FORGE: Mitigating Synchronization Amplification for Memory-Disaggregated Caching Systems](../../references/proceedings/OSDI/2026/volume.pdf#page=997) | 备选 | 分离缓存的热度跟踪和淘汰同步可旁证 10 的内存池元数据代价，但 YCSB 结果不是 LLM KV 命中性能。 |
| 53. [Accelerating Confidential Databases with Crypto-Free Mappings](../../references/proceedings/OSDI/2026/volume.pdf#page=1017) | 排除 | 机密数据库的映射与加密关键路径不是本书模型资源和执行环境的主要问题。 |
| 54. [JANUS: Cross-World, Cooperative Nested Virtualization for Secure Containers](../../references/proceedings/OSDI/2026/volume.pdf#page=1035) | 候选待读 | 云 VM 内轻量 VM 的嵌套虚拟化成本可补 12.4；需核对硬件及协作条件，不当成 E2B 已实现机制。 |
| 55. [Osprey: Transparent and Efficient Virtual Memory for Secure Computation](../../references/proceedings/OSDI/2026/volume.pdf#page=1053) | 排除 | 安全计算的加密数据分页与推测执行依赖 obliviousness，暂不扩入模型 KV 分层缓存。 |
| 56. [Nested SEV: Secure and Generic SEV Support for Nested Virtualization](../../references/proceedings/OSDI/2026/volume.pdf#page=1071) | 备选 | 嵌套 VM 的信任边界可补沙箱隔离限制，但不展开 SEV 内部实现和协议。 |
| 57. [μUSB: Practical and Safe USB Driver Reuse for Arm TrustZone](../../references/proceedings/OSDI/2026/volume.pdf#page=1087) | 排除 | TrustZone USB 驱动提取偏外设安全，未补 AI 工具执行资源推算。 |
| 58. [Achieving Cloud-Grade SLOs for Local Mixture-of-Experts Inference through CPU–GPU Hybrid Design](../../references/proceedings/OSDI/2026/volume.pdf#page=1109) | 候选待读 | CPU–GPU 混合、长 prefill 与并发 SLO 直接回应本地满血 MoE 的取舍；须逐项核对精度、模型、双路 CPU 和单／双卡配置。 |
| 59. [UEP: Portable Expert-Parallel Communication](../../references/proceedings/OSDI/2026/volume.pdf#page=1127) | 候选待读 | CPU 代理 EP 控制通道及异构 NIC 支持可补 7／10；保留 CPU 成本与数据路径，不能将代理误写成数据经 CPU 中转。 |
| 60. [BatchGen: An Architecture for Scalable and Efficient Batch Inference](../../references/proceedings/OSDI/2026/volume.pdf#page=1145) | 候选待读 | 离线批推理的事件驱动序列与专家批量可补 10 的任务完成时间目标；与在线 SLO、连续批处理明确区别。 |
| 61. [UCCL-Tran: An Extensible Software Transport Layer for GPU Networking](../../references/proceedings/OSDI/2026/volume.pdf#page=1163) | 候选待读 | CPU 控制面与多路径传输应对集合通信流碰撞，可补 7 的网络资源瓶颈；先比较 UEP 和既有 NIC 借用案例避免重复。 |
| 62. [Hardware Lifecycle-Aware Power Planning in Commercial Hyperscale Datacenters (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=1187) | 候选待读 | 按硬件生命周期和实际负载做机架功率预算，可补 13 的供电约束；生产遥测与预硅预测不能混成实测。 |
| 63. [Kareus: Joint Reduction of Dynamic and Static Energy in Large Model Training](../../references/proceedings/OSDI/2026/volume.pdf#page=1205) | 候选待读 | kernel 调度与频率联动影响动态／静态能耗，可补 5／13 的时间能耗取舍；不以瞬时功率代替每任务能耗。 |
| 64. [SPADE: Signal-Aware DAG Scheduling and Dynamic Provisioning for Data Processing Clusters](../../references/proceedings/OSDI/2026/volume.pdf#page=1225) | 备选 | 外部供给信号与 DAG 关键路径联合调度有方法价值，但 Spark 批任务暂不替换 AI 调度实例。 |
| 65. [Quota Marketplace: Dynamic Pricing for Efficient Allocation of ML Training Resources](../../references/proceedings/OSDI/2026/volume.pdf#page=1243) | 候选待读 | 组织任务价值异质性与动态配额定价可补 12.2 公平分配；需区分内部额度机制、任务效率与模型 API 市场价格。 |
| 66. [Bodega: Localized Linearizable Reads at Anywhere Anytime via Roster Leases](../../references/proceedings/OSDI/2026/volume.pdf#page=1263) | 排除 | 通用一致性协议的本地读优化偏分布式存储，不扩大本书 AI 模型通信范围。 |
| 67. [Equal Opportunity: A Correctness Condition for Ordered Consensus](../../references/proceedings/OSDI/2026/volume.pdf#page=1303) | 排除 | 区块链有序共识与金融公平性不属于 AI Infra 资源调度的公平性问题。 |
| 68. [Jetpack: Consensus Made Generally Fast](../../references/proceedings/OSDI/2026/volume.pdf#page=1319) | 排除 | 跨地域通用共识快路径不是跨超节点集合通信，避免因 RTT 术语引入旁支。 |
| 69. [Ambulance: Saving BFT through Racing](../../references/proceedings/OSDI/2026/volume.pdf#page=1345) | 排除 | 拜占庭状态机协议竞速与模型 serving 的请求推测和故障恢复不是同一问题。 |
| 70. [SDCs in the Wild: Characterizing and Diagnosing SDC-Defective GPUs in Production LLM Training (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=1369) | 候选待读 | 训练数据相关的 GPU 静默错误与精确重放可补 11.4 诊断；23 张故障卡样本不能当总体失效率。 |
| 71. [Safeguarding LLM Training at Scale: Online SDC Detection and Insights from 35 Million GPU Hours](../../references/proceedings/OSDI/2026/volume.pdf#page=1389) | 候选待读 | 轻量感知与精确验证分离可量化 11.4 检测成本；生产 GPU 小时、事件数与故障卡数要分开。 |
| 72. [OpGuard: Bitwise Alignment for Precise and General Debugging of Production LLM Training](../../references/proceedings/OSDI/2026/volume.pdf#page=1405) | 候选待读 | 控制良性非确定性后按算子定位首个分歧，补 5 的正确性反馈和 11.4 调试；不能将任意跨栈 bitwise 差异都判成 bug。 |
| 73. [RobustRL: Role-Based Fault Tolerance System for RL Post-Training](../../references/proceedings/OSDI/2026/volume.pdf#page=1427) | 采用 | RL 按角色恢复、保留 rollout 状态与重建通信可补 11.5／12.2；优先核对训练状态来源、旧权重轨迹约束及故障注入分母。 |
| 74. [Oxbow: A Coordinated Architecture for Multi-Component File Systems](../../references/proceedings/OSDI/2026/volume.pdf#page=1445) | 备选 | 分层文件系统的 CPU 与设备分工可旁证训练 IO，但暂不展开日志和文件语义，避免偏离模型执行主线。 |
| 75. [Scaling the IO Wall with Declarative IO](../../references/proceedings/OSDI/2026/volume.pdf#page=1463) | 备选 | 后台维护造成存储带宽竞争及按期限合并 IO 有方法价值；HDD 维护任务不是当前 KV／训练加载主案例。 |
| 76. [Umap: Revisiting Memory-Mapped I/O on Distributed File Systems for Efficient Matrix Access (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=1481) | 候选待读 | DFS 上 mmap 的页粒度网络利用和容器内存异常可补 11.4 数据准备，须核对矩阵负载与训练路径的对应。 |
| 77. [CoPilotIO: CPU as a Co-Pilot for GPU I/O to Free GPU Compute](../../references/proceedings/OSDI/2026/volume.pdf#page=1499) | 候选待读 | GPU 发起 IO、CPU 轮询完成可直接解释 5／9 的混合执行资源争用；SM 节省与端到端收益需分别核对。 |
| 78. [RoCE BALBOA: Service-Enhanced RDMA Offload Engine for Data Center SmartNICs](../../references/proceedings/OSDI/2026/volume.pdf#page=1515) | 备选 | 可编程 RDMA 与推荐预处理可作 1／7 的 SmartNIC 对照，但不扩成 FPGA 网络协议实现教程。 |
| 79. [DPA-Store: An Ordered Network Data Path Key-Value Store](../../references/proceedings/OSDI/2026/volume.pdf#page=1533) | 备选 | BlueField DPA 与主机分工说明片上容量和 DMA 往返，通用 KV 索引并非模型 KV cache，暂不替换主例。 |
| 80. [FARLock: Asymmetric RDMA Locking Made Fair](../../references/proceedings/OSDI/2026/volume.pdf#page=1551) | 排除 | 通用 RDMA 锁公平性与模型 EP／集合通信调度不同，不增加分布式锁细节。 |
| 81. [When DDIO Meets Page Coloring: Revisiting DDIO Performance with Sepia](../../references/proceedings/OSDI/2026/volume.pdf#page=1567) | 备选 | DDIO 冲突缺失说明网络 CPU 成本不只由容量决定；保留为第 8 章实际链路的旁证，不直接外推 GPU RDMA。 |
| 82. [Disentangling Graph Dependencies for Efficient Billion-Scale GPU Vector Search](../../references/proceedings/OSDI/2026/volume.pdf#page=1583) | 候选待读 | 向量搜索节点依赖放宽产生预取窗口，适合 5／12 的 AI 数据路径对照；须守住召回率和 IO 条件，避免另开图算法章。 |
| 83. [Efficient GPU-Centric Evolving Graph Processing at Scale](../../references/proceedings/OSDI/2026/volume.pdf#page=1605) | 备选 | 多快照图分析以额外计算换 IO 有方法价值，但不是模型计算图执行，暂不引入具体图算法。 |
| 84. [Pluto: High-Performance, Memory-Efficient Distributed Graph Analytics through Advanced Mirroring](../../references/proceedings/OSDI/2026/volume.pdf#page=1625) | 排除 | 分布式图分析复制与迁移已可由前章的数据搬移方法解释，不增加图处理框架分支。 |
| 85. [The Clustering Strikes Back: Building Cost-Effective and High-Performance ANNS at Scale with Helmsman (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=1643) | 候选待读 | 生产 ANNS 从 DRAM 到闪存的容量／IO／质量取舍可补 Agent 检索成本；集群成本口径与精度约束需正文核对。 |
| 86. [WiseCode: Breaking the Scalability Barriers of Wide-Stripe Vector Codes](../../references/proceedings/OSDI/2026/volume.pdf#page=1661) | 排除 | 宽条带纠删码细节偏存储可靠性，训练检查点主线不需要展开编码设计。 |
| 87. [The LogDrive: Composable Durability for Cloud-Based Shared Logs](../../references/proceedings/OSDI/2026/volume.pdf#page=1683) | 备选 | 对象存储上日志持久化与排序分离可旁证状态恢复，但通用元数据服务成本不当作模型 KV 保存成本。 |
| 88. [Timelock Drive: Isolated Time-Based Defense for Storage Systems](../../references/proceedings/OSDI/2026/volume.pdf#page=1703) | 排除 | 防勒索磁盘时间锁不是本书 RL 状态和沙箱恢复的主要问题。 |
| 89. [High Fidelity Models for Large Scale Stateful Services (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=1719) | 备选 | S3 抽象模型验证可用于讨论系统测试边界，但不是资源性能模型，不纳入 BOTE 的性能推算案例。 |
| 90. [M3U: Scalable Kernel Memory Management for Efficient Post-Copy Live Migration of High-End Virtual Machines](../../references/proceedings/OSDI/2026/volume.pdf#page=1735) | 备选 | 大型 VM 的迁移缺页与停机时间可补 12.4 状态转移边界；高端 VM 结果不能套到轻量沙箱。 |
| 91. [Compaction-Free Memory Defragmentation for Virtualization via Infinite Guest Physical Address Space](../../references/proceedings/OSDI/2026/volume.pdf#page=1751) | 备选 | 扩展虚拟地址避免物理搬移可对照 5／9 的分页方法，但 GPA 空间不等于真实内存容量，不单设篇幅。 |
| 92. [Inside Out: A Paradigm Shift in VM Introspection](../../references/proceedings/OSDI/2026/volume.pdf#page=1769) | 排除 | 云 VM 内省与安全观察偏监控实现，暂不扩写 Agent 沙箱的资源主线。 |
| 93. [vBOIDs: Taming Chaos via Coarse-Grained Scheduling Abstraction for Containers](../../references/proceedings/OSDI/2026/volume.pdf#page=1789) | 候选待读 | 高密度容器的调度抖动与线程成组可补 12.1／12.4 CPU 并发；需核对是否有 AI 工具执行实例。 |
| 94. [Efficient LLM Serving on Commodity GPU Clusters with Data-Reduced Cross-Instance Orchestration](../../references/proceedings/OSDI/2026/volume.pdf#page=1807) | 候选待读 | L20／Ethernet 上跨实例错开 PD 降低搬移可补 10.2 的分离临界点；需核对等待与 goodput 条件及当前框架对照。 |
| 95. [Revisiting Pipeline Parallelism for LLM Serving](../../references/proceedings/OSDI/2026/volume.pdf#page=1823) | 候选待读 | SGLang 上 PP 的动态 chunk 与 decode 延迟调度补 6／9；先与已有 Sarathi 和排队算例比较，A100 40GB 结论不泛化所有互联。 |
| 96. [OpenTela: Unifying Decentralized Computing Resources for Heterogeneous LLM Serving (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=1841) | 备选 | Slurm 资源上服务发现与路由可补 12 的服务控制面边界，但跨机构平台不改写第 7 章跨超节点网络。 |
| 97. [Kairox: Adaptive GPU-CPU Hybrid LLM Inference via Online Neuron Balancing](../../references/proceedings/OSDI/2026/volume.pdf#page=1859) | 候选待读 | CPU–GPU 动态神经元放置可补 9.4 极端本地推理的取舍；必须核对稀疏模型、激活预测与质量，不能套到任意 Dense。 |
| 98. [ADAngel: Accelerating Arbitrary-Precision Quantized LLMs with Adaptive Computing Mapping](../../references/proceedings/OSDI/2026/volume.pdf#page=1877) | 候选待读 | 混合位宽 GEMM 的形状自适应路径可补 4／5／9，先算解包和实际指令工作，不能仅按名义 bit 数推断速度。 |
| 99. [Optimal Software Pipelining and Warp Specialization for Tensor Core GPUs](../../references/proceedings/OSDI/2026/volume.pdf#page=1895) | 候选待读 | SWP 与 warp specialization 联合求解可补 5.3 手工／编译／Agent 优化比较；最优性限于模型，仍需真实 profiling。 |
| 100. [TileLoom: Automatic Dataflow Planning for Tile-Based Languages on Spatial Dataflow Accelerators](../../references/proceedings/OSDI/2026/volume.pdf#page=1911) | 候选待读 | MLIR 与空间数据流核间映射可补 4／5 跨架构设计，Tenstorrent vendor 比较需核对精度、形状和芯片代际。 |
| 101. [MPK: A Compiler and Runtime for Mega-Kernelizing Tensor Programs](../../references/proceedings/OSDI/2026/volume.pdf#page=1929) | 候选待读 | MPK 将多卡推理降为 SM 任务图和 persistent kernel，可补 5.4／10 的调度粒度；与 CUDA Graph 区分，先核对适用模型和负载。 |
| 102. [GraCE: Unlocking CUDA Graphs with Compiler Support for ML Workloads](../../references/proceedings/OSDI/2026/volume.pdf#page=1947) | 采用 | 图捕获的输入变换、参数复制与选择成本直接补 5.4 CUDA Graph；优先正文核对，再与 vLLM／SGLang 分段和整图实现比较。 |
| 103. [VTC: DNN Compilation with Virtual Tensors for Data Movement Elimination](../../references/proceedings/OSDI/2026/volume.pdf#page=1969) | 候选待读 | 虚拟张量通过索引映射消除物理搬移，可补 5.2 融合的边界；零额外拷贝不等于零访问，索引和布局成本需计入。 |
| 104. [Stop Pretending to Be Busy: A Case for Serverless Paradigms in Co-Located Batch Workloads (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=1987) | 备选 | 在线／批任务共置中的分配与实际工作差异可旁证 12／13，但 Spark 案例暂不替换已有 AI fleet 分析。 |
| 105. [Continuation-Centric Computing with Arca](../../references/proceedings/OSDI/2026/volume.pdf#page=2009) | 候选待读 | 将等待中的 continuation 保存／迁移与 Agent 环境驻留直接相邻，可补 12.4；需核对进程模型、外部状态和隔离。 |
| 106. [Rethinking Process Snapshots for Near-Warm Serverless Cold Starts](../../references/proceedings/OSDI/2026/volume.pdf#page=2027) | 候选待读 | 进程快照布局、预取和元数据批量恢复可补 12.4 冷启动；OS 原语改动及进程／VM 对照条件需保留。 |
| 107. [Distributed Speculative Execution for Resilient Cloud Applications](../../references/proceedings/OSDI/2026/volume.pdf#page=2047) | 备选 | 持久执行的推测与故障修复可补工具状态边界，但普通服务消息语义不能直接保证 Agent 外部操作可撤销。 |
| 108. [TrainMover: An Interruption-Resilient Runtime for ML Training](../../references/proceedings/OSDI/2026/volume.pdf#page=2067) | 候选待读 | 训练通信组增量重建与备用机器预热可补 11.4；1024 卡实验与 64K 卡投影应分开，并与 RobustRL 对比恢复粒度。 |
| 109. [MoonBright: A GPU Memory Allocator with Device-Side Page Table Materialization and Deferred TLB Coherence](../../references/proceedings/OSDI/2026/volume.pdf#page=2085) | 候选待读 | GPU 页表构造和新虚拟地址避免 TLB 同步可补 5／9 显存管理；需核对驱动修改和实际可复现范围。 |
| 110. [Nixie: Efficient, Transparent Temporal Multiplexing for Consumer GPUs](../../references/proceedings/OSDI/2026/volume.pdf#page=2105) | 候选待读 | 消费卡多模型时分复用的迁移、双向链路和 pinned 内存预算可补 9.4／12；先与 Ollama 容量放置区分。 |
| 111. [μShell: A Microkernel-based FPGA Shell Architecture](../../references/proceedings/OSDI/2026/volume.pdf#page=2123) | 备选 | FPGA 模块共享与隔离可作加速器执行对照，暂不引入硬件微内核的完整编程模型。 |
| 112. [Virtualizing eBPF with Late-Binding](../../references/proceedings/OSDI/2026/volume.pdf#page=2147) | 排除 | 多租户 eBPF 绑定与隔离不直接补 AI 工具执行或模型资源预算，暂不扩写。 |
| 113. [DVLA: Dynamic VM Lifetime Aware Scheduling for Drifting Lifetime Distributions and Long-Lived VM Placement Debt (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=2169) | 候选待读 | 长寿命 VM 分散阻碍回收、预测漂移与迁移成本可补 12.4 环境池；0.6 个百分点密度收益须保留总体口径。 |
| 114. [PIMS: Fleet-Wide Datacenter Maintenance with Minimal Capacity Buffer and Predictable Latency (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=2189) | 候选待读 | 维护预留容量与故障分组可补 13 的可用资源预算；上线维护时间目标不是单次模型请求 SLO。 |
| 115. [Heterogeneity at Hyperscale: Characterization and Scheduling of Large Production AI Clusters at Alibaba (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=2207) | 既有采用待核对 | ASI 已用于 12.2 的成组资源与碎片分析，本次完成整卷顺序摘要筛读；既有单篇归档另存，不重复计一篇新正文阅读或把分配率当 MFU。 |
| 116. [Mimesys: Generating Realistic Executable Testing Environments from Resource Usage Traces](../../references/proceedings/OSDI/2026/volume.pdf#page=2225) | 备选 | 资源轨迹合成可讨论实验保真度，但不能以合成压力替代真实框架记录；仅在无法取得负载时说明近似范围。 |
| 117. [Merlin: An Efficient Adaptive Cache Eviction Algorithm via Fine-Grained Characterization](../../references/proceedings/OSDI/2026/volume.pdf#page=2243) | 备选 | 逐对象特征和淘汰策略干扰可补缓存决策方法，通用 web trace 不能当 KV 前缀命中结果。 |
| 118. [Learning-Augmented Heuristics: Simple Yet Smart, Robust and Interpretable Cache Eviction](../../references/proceedings/OSDI/2026/volume.pdf#page=2261) | 候选待读 | 简单快速数据面与低频学习控制面适合 10／12 的缓存反馈讨论；解释性描述不代替优化目标或真实延迟验证。 |
| 119. [WriteGuards: Distributed Storage Support for Strongly Consistent Caches](../../references/proceedings/OSDI/2026/volume.pdf#page=2281) | 排除 | 分布式存储写入 fencing 与线性一致缓存偏通用数据库，不因 cache 名称引入模型 KV 章。 |
| 120. [MEGALON: Efficient Data Sharing for Partly Coherent CXL Memory](../../references/proceedings/OSDI/2026/volume.pdf#page=2301) | 备选 | 部分一致 CXL 的元数据容量可旁证 UB／内存池，需区分协议语义与本书已有硬件，不单列实现。 |
| 121. [Inference in the Shadows: Taming Memory Bandwidth Contention in Mobile LLM Inference with Sereno](../../references/proceedings/OSDI/2026/volume.pdf#page=2319) | 候选待读 | 移动 LLM 与前台共享带宽、推测解码提供让出点可补 8／9；既看 token 吞吐也看交互质量，不泛化 NPU 优先级。 |
| 122. [LifeLine: An Object-Page Lifetime Alignment GC Enabling Minimal Memory Copying for Mobile Devices](../../references/proceedings/OSDI/2026/volume.pdf#page=2339) | 排除 | Android GC 的对象页寿命优化偏移动运行时内部，不补当前模型状态主线。 |
| 123. [Unleash All Cores: Asymmetry-Aware Scalable DNN Inference on Mobile CPUs](../../references/proceedings/OSDI/2026/volume.pdf#page=2357) | 候选待读 | 大小核亲和与动态任务粒度直接解释 CPU 推理多核反而变慢，可补 5.5；算例须保持模型和功耗条件。 |
| 124. [Surviving the Impossible Trinity: Revisiting CPU Scheduling Problem on Modern COTS Mobile Devices (Operational Systems)](../../references/proceedings/OSDI/2026/volume.pdf#page=2373) | 备选 | 交互链路语义驱动 CPU 调度可旁证第 8 章任务延迟，通用 App 启动不替换 AI 交互实例。 |
| 125. [qTPU: Hybrid Tensor Networks for Quantum-Classical Acceleration](../../references/proceedings/OSDI/2026/volume.pdf#page=2387) | 排除 | 量子经典混合计算超出本书当前 GPU／CPU AI Infra 范围，不因张量和 TPU 名称增加章节。 |
| 126. [Acumen: A Platform for Encrypted and Accountable Collaborative Editing](../../references/proceedings/OSDI/2026/volume.pdf#page=2409) | 排除 | 加密协同编辑与 CRDT 快照一致性不属于模型执行或 Agent 沙箱资源分析。 |
| 127. [Drs.NAS: Ultra-Efficient Neural Architecture Search for Recommendation Systems](../../references/proceedings/OSDI/2026/volume.pdf#page=2427) | 候选待读 | 推荐模型硬件成本与架构搜索可旁证第 2 章设计尺寸；代理分数和离线 AUC 需核对，不能证明通用 LLM 甜点来源。 |
| 128. [SMARTTalk: Teaching SMART Logs to Talk to LLMs](../../references/proceedings/OSDI/2026/volume.pdf#page=2443) | 备选 | LLM 处理设备遥测的数值提取／解释分离有方法价值，但诊断分数和 LLM-as-judge 不等于实际故障率改善。 |
| 129. [Svalinn: Overload Control in Large-Scale Servers with Multiple Resource Bottlenecks](../../references/proceedings/OSDI/2026/volume.pdf#page=2463) | 候选待读 | 多资源过载控制和无显式队列的带宽限流可补 12 的 CPU 工具池；须找到 AI 路径映射并与现有供给预算比较。 |
| 130. [PeeR: First-Class Scheduling for Latency-Critical eBPF Applications](../../references/proceedings/OSDI/2026/volume.pdf#page=2485) | 排除 | eBPF 合作抢占与内核调度细节不直接补当前 AI 负载主例。 |
| 131. [TypeCraft: A Lightweight Data Type Profiler with High Resolution](../../references/proceedings/OSDI/2026/volume.pdf#page=2503) | 备选 | 按类型定位访存代价可作 5.3 profiling 反馈旁证，但 Linux 结构布局不扩为 GPU 算子优化教程。 |
| 132. [All Along the Watchtower: Achieving the Trinity of Observability in Cloud with DiTing](../../references/proceedings/OSDI/2026/volume.pdf#page=2521) | 备选 | 日志指标追踪的统一存储和闲置资源可旁证生产观测成本，暂不加整套云可观测平台。 |
| 133. [jwmalloc: A Verified Memory Allocator for Mobile Devices](../../references/proceedings/OSDI/2026/volume.pdf#page=2535) | 排除 | 移动分配器 slab 与弱内存验证不直接增加模型容量或访问量的判断能力。 |
| 134. [Neuro-Symbolic Proof Generation for Scaling Systems Software Verification](../../references/proceedings/OSDI/2026/volume.pdf#page=2553) | 备选 | LLM 候选加符号验证可对照 5.3 优化 Agent 的反馈闭环，但证明搜索不是 kernel 性能优化结果。 |
| 135. [Spain: Succinct Proofs for Numerical Computations](../../references/proceedings/OSDI/2026/volume.pdf#page=2571) | 排除 | 数值计算简洁证明与近似可满足性属于验证协议，不作为本书性能模型误差讨论的直接机制。 |
| 136. [RT: Regular Types for the Streaming Shell](../../references/proceedings/OSDI/2026/volume.pdf#page=2603) | 排除 | Shell 流式程序静态类型检查与 AI Infra 资源安排关系较远，不引入工具语言类型系统细节。 |

## 重点章节与采用边界

- **Weave: Efficient Co-Scheduling for Disaggregated RL Post-Training**：§2 后半、§3–5 与 §6.1–6.4；未读 §6.5 以后及附录证明。采用阶段互补、主机驻留、分层权重同步与 SLO／价格条件于 11.5→12.2。；原整卷物理页 831, 832, 833, 834, 835, 836, 837, 838, 839。
- **RobustRL: Role-Based Fault Tolerance System for RL Post-Training**：§1 后半、§2–7.4 与 §8 本页部分；后续讨论、结论、参考文献和附录未读。采用角色恢复、温备硬件条件、检查点与 ETTR／注入评估边界于 11.5→12.2。；原整卷物理页 1428, 1429, 1430, 1431, 1432, 1433, 1434, 1435, 1436, 1437, 1438, 1439。
- **GraCE: Unlocking CUDA Graphs with Compiler Support for ML Workloads**：§2–5 的动机、设计、实现、评估及额外准备成本，§6 相关工作与结论；参考文献、附录 artifact 未逐项读。采用图段选择、外部输入复制与版本边界于 5.4／9.1。；原整卷物理页 1949, 1950, 1951, 1952, 1953, 1954, 1955, 1956, 1957, 1958, 1959, 1960。

具体推算和采用决策另记案例笔记；新增候选不自动进入正文。历史实验的模型、软件、硬件和质量条件保持原样，本书贯穿模型继续使用 Qwen3／V4／K3。
