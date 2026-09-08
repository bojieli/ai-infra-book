# NSDI 2025：摘要筛选与重点阅读

已按官方日程中的正式论文顺序阅读 83／83 篇完整摘要；2 篇补读所列正文。下载、首页核对、摘要筛选和正文阅读分别记录。

[逐项手工取舍](screening-nsdi-2025.tsv)与[归档清单](../../references/proceedings/NSDI/2025/manifest.json)同步。

| 序号与论文 | 本轮取舍 | 原因与位置 |
| --- | --- | --- |
| 1. [PRED: Performance-oriented Random Early Detection for Consistently Stable Performance in Datacenters](../../references/proceedings/NSDI/2025/volume.pdf#page=17) | 备查 | PRED 分离并发稳定与队列调节，针对静态 RED 和学习方案的尾部不稳；7 已有反馈主线，若采用需比较稳定性与调参代价。 |
| 2. [Rajomon: Decentralized and Coordinated Overload Control for Latency-Sensitive Microservices](../../references/proceedings/NSDI/2025/volume.pdf#page=37) | 备查 | Rajomon 沿微服务调用图传播价格和限流令牌；可映射 12 的工具链过载，但协议令牌不是模型 token，尚缺 AI 请求与重试的具体对应。 |
| 3. [Learnings from Deploying Network QoS Alignment to Application Priorities for Storage Services](../../references/proceedings/NSDI/2025/volume.pdf#page=53) | 备查 | 逐 RPC 的存储 QoS 部署发现降优先级有时反而降低延迟；可提醒 7 检查优先级拥挤，不展开存储全网迁移细节。 |
| 4. [DISC: Backpressure Mitigation In Multi-tier Applications With Distributed Shared Connection](../../references/proceedings/NSDI/2025/volume.pdf#page=71) | 备查 | DISC 让多个层共同作为 TCP 端点并绕过只转发数据的层；8 可比较真实 AI 返回路径，但不能默认 TLS／代理边界均可直接绕过。 |
| 5. [Enabling Silent Telemetry Data Transmission with InvisiFlow](../../references/proceedings/NSDI/2025/volume.pdf#page=87) | 备查 | InvisiFlow 利用空闲容量和拥塞梯度传遥测；可补 7 观测开销，当前先保留而不增加遥测算法清单。 |
| 6. [Unlocking ECMP Programmability for Precise Traffic Control](../../references/proceedings/NSDI/2025/volume.pdf#page=103) | 候选 | P-ECMP 利用 ECMP group 实现主机可选择的精确策略，减少反复改五元组试路；可补 7 故障绕行，需核对硬件配置与路径粒度。 |
| 7. [Enabling Portable and High-Performance SmartNIC Programs with Alkali](../../references/proceedings/NSDI/2025/volume.pdf#page=123) | 备查 | Alkali 用 IR 与迭代并行优化适配 NIC 的并行和内存差异；与 5 的硬件模型和实测校准相关，但不将 SmartNIC 编译结论套成 GPU 算子结果。 |
| 8. [Scaling IP Lookup to Large Databases using the CRAM Lens](../../references/proceedings/NSDI/2025/volume.pdf#page=143) | 排除 | CRAM 面向 IPv4／IPv6 路由表在 TCAM／SRAM 中的查找规模；不直接补充模型计算或 AI 集群的数据搬运推算。 |
| 9. [Quicksand: Harnessing Stranded Datacenter Resources with Granular Computing](../../references/proceedings/NSDI/2025/volume.pdf#page=163) | 备查 | Quicksand 将 CPU／内存消费拆为可迁移 proclet，缓解单资源耗尽造成的碎片；12 可对照环境资源，但应用移植与细粒度运行时条件不能省略。 |
| 10. [Beehive: A Scalable Disaggregated Memory Runtime Exploiting Asynchrony of Multithreaded Programs](../../references/proceedings/NSDI/2025/volume.pdf#page=183) | 备查 | Beehive 以编译转换暴露线程内异步，避免微秒远程内存访问的切线程开销和局部性损失；可补 12，需与已有远程 KV 路径区分。 |
| 11. [Making Serverless Pay-For-Use a Reality with Leopard](../../references/proceedings/NSDI/2025/volume.pdf#page=205) | 候选 | Leopard 将动态 CPU／内存与抢占纳入 serverless 计费和调度；可补 12.5 已分配、实际消耗与收费单位的差异，不将实验定价当现行服务价格。 |
| 12. [GRANNY: Granular Management of Compute-Intensive Applications in the Cloud](../../references/proceedings/NSDI/2025/volume.pdf#page=221) | 候选 | GRANNY 的 WebAssembly Granule 用快照做纵向扩核与横向迁移；可补 12 环境抽象，需核对可迁移状态、共享内存和原生工具兼容边界。 |
| 13. [On Temporal Verification of Stateful P4 Programs](../../references/proceedings/NSDI/2025/volume.pdf#page=235) | 排除 | P4LTL／Büchi transaction 的时序验证针对有状态数据平面程序；不为 AI 网络章节展开专门形式化验证工具链。 |
| 14. [NDD: A Decision Diagram for Network Verification](../../references/proceedings/NSDI/2025/volume.pdf#page=253) | 排除 | NDD 优化网络验证器的等价类表示与 BDD 开销；与本书主要资源约束和系统取舍距离较远。 |
| 15. [Smart Casual Verification of the Confidential Consortium Framework](../../references/proceedings/NSDI/2025/volume.pdf#page=275) | 排除 | CCF 的 TLA+ 与 C++ 一致性检查围绕联盟账本共识；CI 验证经验通用，不转写为训练或推理状态的一致性方案。 |
| 16. [VEP: A Two-stage Verification Toolchain for Full eBPF Programmability](../../references/proceedings/NSDI/2025/volume.pdf#page=293) | 排除 | VEP 为 eBPF 源码和字节码增加注解证明检查；不因 tracing 相关就扩展一节内核验证器设计。 |
| 17. [MeshTest: End-to-End Testing for Service Mesh Traffic Management](../../references/proceedings/NSDI/2025/volume.pdf#page=317) | 备查 | MeshTest 自动生成服务网格路径与请求验证行为；可检查 12 路由规则组合，但当前已有具体模型路由与缓存条件优先。 |
| 18. [Preventing Network Bottlenecks: Accelerating Datacenter Services with Hotspot-Aware Placement for Compute and Storage](../../references/proceedings/NSDI/2025/volume.pdf#page=333) | 候选 | Google 实测 ToR 热点可持续数小时，算存升级快于网络和带宽无关放置导致需求失衡；可与 CASSINI 的周期错峰比较平均持续超载和峰值碰撞。 |
| 19. [Enhancing Network Failure Mitigation with Performance-Aware Ranking](../../references/proceedings/NSDI/2025/volume.pdf#page=351) | 备查 | 按端到端流指标估算并排序故障缓解方案，避免局部代理指标；可补 7／13 诊断后的选择，先不重复已有最窄路径与完成时间分析。 |
| 20. [One-Size-Fits-None: Understanding and Enhancing Slow-Fault Tolerance in Modern Distributed Systems](../../references/proceedings/NSDI/2025/volume.pdf#page=375) | 候选 | 慢故障研究显示微小负载变化会改变系统反应，静态阈值不足，ADR 自适应处理；可补 11 恢复判据，需与 Minder／Holmes 的 AI 证据比较。 |
| 21. [Pyrrha: Congestion-Root-Based Flow Control to Eliminate Head-of-Line Blocking in Datacenter](../../references/proceedings/NSDI/2025/volume.pdf#page=395) | 备查 | Pyrrha 按拥塞根控制流以限制 HOL 与队列数；可补 7 队列资源约束，需保留交换实现和证明假设，不当作所有 RDMA 的现有保证。 |
| 22. [eTran: Extensible Kernel Transport with eBPF](../../references/proceedings/NSDI/2025/volume.pdf#page=423) | 备查 | eTran 将 eBPF 可扩展性与用户态路径优化结合；可补 8／12 执行开销，但 TCP／Homa 微基准不直接说明模型端到端收益。 |
| 23. [White-Boxing RDMA with Packet-Granular Software Control](../../references/proceedings/NSDI/2025/volume.pdf#page=443) | 候选 | SCR 用 BlueField-3 DPA 提供包粒度 RDMA 软件控制，应用到 GPU-Direct／NVMe-oF；可补 7 硬件卸载与可编程性的取舍，核对每包处理预算。 |
| 24. [SIRD: A Sender-Informed, Receiver-Driven Datacenter Transport Protocol](../../references/proceedings/NSDI/2025/volume.pdf#page=467) | 候选 | SIRD 区分单一所有者的接收链路与多人共享的发送／中间链路，调度配合反应式控制；可补 7 全局可行性，和 CASSINI 的作业错峰分层比较。 |
| 25. [Accelerating Design Space Exploration for LLM Training Systems with Multi-experiment Parallel Simulation](../../references/proceedings/NSDI/2025/volume.pdf#page=489) | 备查 | Multiverse 将多组训练设计实验放进 GPU 仿真以降搜索开销；13 只在粗算与测点仍不能决策时讨论模型精度，不引导读者先写复杂仿真器。 |
| 26. [Optimizing RLHF Training for Large Language Models with Stage Fusion](../../references/proceedings/NSDI/2025/volume.pdf#page=505) | 候选 | RLHFuse 按样本融合生成与推断、按微批融合训练流水，分别处理生成长尾和气泡；可补 11.5，需区分 PPO 各角色与当前 GRPO／Agent 依赖。 |
| 27. [Minder: Faulty Machine Detection for Large-scale Distributed Model Training](../../references/proceedings/NSDI/2025/volume.pdf#page=521) | 候选 | Minder 从故障前持续异常的指标模式识别机器，报告生产检测时间、precision 和 F1；11 应同时看误报、停机损失与恢复动作，不能只报检测秒数。 |
| 28. [Holmes: Localizing Irregularities in LLM Training with Mega-scale GPU Clusters](../../references/proceedings/NSDI/2025/volume.pdf#page=539) | 候选 | Holmes 用通信算子图和跨迭代分析定位慢迭代；可深化 7／11 的 rank 就绪偏差，需核对异常传播方向与仿真／生产证据。 |
| 29. [SimAI: Unifying Architecture Design and Performance Tuning for Large-Scale Large Language Model Training with Scalability and Precision](../../references/proceedings/NSDI/2025/volume.pdf#page=557) | 备查 | SimAI 跨框架、kernel 和通信库校准模拟粒度并并行执行；13 可比较粗模型何时失效，但平均拟合率不是任意新芯片预测保证。 |
| 30. [ByteCheckpoint: A Unified Checkpointing System for Large Foundation Model Development](../../references/proceedings/NSDI/2025/volume.pdf#page=575) | 候选 | ByteCheckpoint 用与并行布局解耦的表示在加载时重分片，并统一框架与存储路径；11 检查点与 12 重配可据此算持久化、加载和搬运，优先选读。 |
| 31. [Mowgli: Passively Learned Rate Control for Real-Time Video](../../references/proceedings/NSDI/2025/volume.pdf#page=595) | 备查 | Mowgli 用离线遥测学习实时视频码率，避免线上探索伤尾部体验；与 8 反馈有关，但这是网络控制 RL，不是模型 RL 训练系统。 |
| 32. [Dissecting and Streamlining the Interactive Loop of Mobile Cloud Gaming](../../references/proceedings/NSDI/2025/volume.pdf#page=611) | 备查 | LoopTailor 发现云游戏交互多个 VSync 的串行等待；8 可借其关键路径判断方法，用户已要求媒体背景简述，不扩成云游戏章节。 |
| 33. [Region-based Content Enhancement for Efﬁcient Video Analytics at the Edge](../../references/proceedings/NSDI/2025/volume.pdf#page=629) | 排除 | RegenHance 预测重要视频区域并拼接增强，围绕边缘视频分析质量；当前图片精修与 computer use 已覆盖必要媒体案例，不再展开增强算法。 |
| 34. [Tooth: Toward Optimal Balance of Video QoE and Redundancy Cost by Fine-Grained FEC in Cloud Gaming Streaming](../../references/proceedings/NSDI/2025/volume.pdf#page=651) | 备查 | Tooth 依帧长和网络状态调 FEC，兼顾编码开销与交互尾延迟；8 可用于重传／冗余的边界，但需要实际 AI 截图／音频数据验证。 |
| 35. [AsTree: An Audio Subscription Architecture Enabling Massive-Scale Multi-Party Conferencing](../../references/proceedings/NSDI/2025/volume.pdf#page=669) | 排除 | AsTree 解决海量会议音频订阅与转发的信令风暴；与选定的 ASR／TTS 和 Agent 交互主线不同，不增加会议系统架构细节。 |
| 36. [AutoCCL: Automated Collective Communication Tuning for Accelerating Distributed and Parallel DNN Training](../../references/proceedings/NSDI/2025/volume.pdf#page=683) | 候选 | AutoCCL 在 NCCL 上调实现参数并在线考虑通信计算干扰；6 的独立微基准最优可能不等于训练步时最优，优先读搜索成本与端到端验证。 |
| 37. [OptiReduce: Resilient and Tail-Optimal AllReduce for Distributed Deep Learning in the Cloud](../../references/proceedings/NSDI/2025/volume.pdf#page=701) | 候选 | OptiReduce 用有界不可靠传输、梯度变换平衡尾时延与精度；6／11 必须看等质量 TTA，不把可丢梯度推广到 KV、激活或权重同步。 |
| 38. [Efficient Direct-Connect Topologies for Collective Communications](../../references/proceedings/NSDI/2025/volume.pdf#page=721) | 候选 | 直接连接拓扑与集合日程共同构造，在端口度、延迟和带宽间选点；可深化 6.5／13，先比较已有 Swing 与割集例子是否足够。 |
| 39. [SuperServe: Fine-Grained Inference Serving for Unpredictable Workloads](../../references/proceedings/NSDI/2025/volume.pdf#page=755) | 候选 | SuperServe 依赖预训练共享权重超网络，以低开销切子网适配质量和时延；12 可补模型选择，不能当作任意独立 LLM 都可无加载切换。 |
| 40. [Pineapple: Unifying Multi-Paxos and Atomic Shared Registers](../../references/proceedings/NSDI/2025/volume.pdf#page=775) | 排除 | Pineapple 以共享寄存器和 Multi-Paxos 改善存储共识；不将通用线性一致性设计扩成 AI Infra 主线。 |
| 41. [Ladder: A Convergence-based Structured DAG Blockchain for High Throughput and Low Latency](../../references/proceedings/NSDI/2025/volume.pdf#page=795) | 排除 | Ladder 围绕双链 DAG 区块排序、确认和攻击抵抗；非模型计算图与训练通信问题。 |
| 42. [Vegeta: Enabling Parallel Smart Contract Execution in Leaderless Blockchains](../../references/proceedings/NSDI/2025/volume.pdf#page=811) | 排除 | Vegeta 是智能合约的推测执行、排序和确定性回放；不是推测解码或 MoE router replay，避免同词混用。 |
| 43. [Shoal++: High Throughput DAG BFT Can Be Fast and Robust!](../../references/proceedings/NSDI/2025/volume.pdf#page=829) | 排除 | Shoal++ 优化 DAG 拜占庭共识的提交轮数与吞吐；不是模型图执行或集体通信，不因 DAG 一词加入。 |
| 44. [Learning Production-Optimized Congestion Control Selection for Alibaba Cloud CDN](../../references/proceedings/NSDI/2025/volume.pdf#page=843) | 备查 | AliCCS 用实际区域网络选择已有拥塞算法，可供 8 比较固定协议与反馈选择；摘要中超过 100% 的重传率降低表述需核对分母，不直接采用数字。 |
| 45. [GPU-Disaggregated Serving for Deep Learning Recommendation Models at Scale](../../references/proceedings/NSDI/2025/volume.pdf#page=863) | 候选 | Prism 将推荐模型的 CPU／内存密集与 GPU 密集子图分池，减少 GPU 碎片；可补 10／12 的 AF 类资源匹配，必须保留 DLRM 与 LLM 专家计算的差别。 |
| 46. [Evolution of Aegis: Fault Diagnosis for AI Model Training Service in Production](../../references/proceedings/NSDI/2025/volume.pdf#page=881) | 候选 | Aegis 从通用诊断演进到通信库定制及交付前检查，生产上减少诊断闲置和重启；与 Minder／Holmes 比较后选择，避免 11 堆三套相近案例。 |
| 47. [PAPAYA Federated Analytics Stack: Engineering Privacy, Scalability and Practicality](../../references/proceedings/NSDI/2025/volume.pdf#page=899) | 排除 | PAPAYA 明确面向跨设备联邦统计与监控而非联邦学习；隐私分析栈不是本书集中式模型基础设施的必要扩展。 |
| 48. [HA/TCP: A Reliable and Scalable Framework for TCP Network Functions](../../references/proceedings/NSDI/2025/volume.pdf#page=915) | 备查 | HA/TCP 用复制 socket 支持连接迁移和故障切换；12 可说明恢复进程与恢复连接不同，但不能将 TCP 状态复制等同工具或模型状态恢复。 |
| 49. [High-level Programming for Application Networks](../../references/proceedings/NSDI/2025/volume.pdf#page=931) | 备查 | AppNet 联合放置 RPC 处理代码并检查状态语义等价；8／12 可借鉴链路中间层优化，当前先保留为模型路由实现的旁证。 |
| 50. [State-Compute Replication: Parallelizing High-Speed Stateful Packet Processing](../../references/proceedings/NSDI/2025/volume.pdf#page=953) | 备查 | state-compute replication 借包历史序列器跨核复制状态以处理大流；7／12 可比较分片与复制，但其确定性更新条件不是 MoE 专家复制的条件。 |
| 51. [MTP: Transport for In-Network Computing](../../references/proceedings/NSDI/2025/volume.pdf#page=975) | 候选 | 此 MTP 是 in-network computing 的消息传输协议，处理网络内修改、重排和延迟以及资源控制；可补 7 计算语义，不能混同 Multi-Token Prediction。 |
| 52. [ONCache: A Cache-Based Low-Overhead Container Overlay Network](../../references/proceedings/NSDI/2025/volume.pdf#page=995) | 备查 | ONCache 缓存 overlay 重复处理以降低每包 CPU 代价，作为 Antrea 插件；12 环境网络可引用测量方法，不声称任意容器都自动接近裸机。 |
| 53. [GREEN: Carbon-efficient Resource Scheduling for Machine Learning Clusters](../../references/proceedings/NSDI/2025/volume.pdf#page=1015) | 候选 | GREEN 利用训练任务的时间弹性兼顾碳排、峰值功率和 JCT；12／13 可计算等待预算下的移时选择，需明确碳强度数据与时间效率损失。 |
| 54. [The Benefits and Limitations of User Interrupts for Preemptive Userspace Scheduling](../../references/proceedings/NSDI/2025/volume.pdf#page=1031) | 候选 | 用户态中断降低抢占开销，但上层软件可能限制可用调度策略；12 可补 CPU 工具任务的尾延迟，需与 GPU kernel 抢占区分并核对硬件条件。 |
| 55. [Securing Public Cloud Networks with Efficient Role-based Micro-Segmentation](../../references/proceedings/NSDI/2025/volume.pdf#page=1049) | 排除 | 基于流量推断角色的微分段安全策略不直接补充模型资源与执行代价；保持环境隔离的必要内容，不扩写通用公有云安全系统。 |
| 56. [Mitigating Scalability Walls of RDMA-based Container Networks](../../references/proceedings/NSDI/2025/volume.pdf#page=1065) | 候选 | ScalaCN 用组合因果测试推断 RNIC 隐藏状态的扩展墙，再调整卸载安排；7／13 可补可观测性和模型校准，推断原因与厂商确认要分别记录。 |
| 57. [Eden: Developer-Friendly Application-Integrated Far Memory](../../references/proceedings/NSDI/2025/volume.pdf#page=1083) | 备查 | Eden 以少量访问位置提示配合硬件缺页保护优化远程内存；12 可对照透明分页和应用改造成本，不等同推理引擎的显式 KV 分层。 |
| 58. [Achieving Wire-Latency Storage Systems by Exploiting Hardware ACKs](../../references/proceedings/NSDI/2025/volume.pdf#page=1101) | 候选 | Juneberry 用有序队列使硬件 ACK 成为特定存储提交信号，CPU 后续异步执行；可深化 7 的到达、提交、执行区分，须保留顺序与持久化条件。 |
| 59. [ODRP: On-Demand Remote Paging with Programmable RDMA](../../references/proceedings/NSDI/2025/volume.pdf#page=1117) | 备查 | ODRP 用客户端辅助的 RNIC 原语链管理 OS 远程分页；10／12 可比较内存池管理开销，摘要无 CPU 使用不能泛化为整个系统不耗 CPU。 |
| 60. [Understanding and Profiling NVMe-over-TCP Using ntprof](../../references/proceedings/NSDI/2025/volume.pdf#page=1133) | 候选 | ntprof 将 NVMe/TCP 路径视为多级软件交换并分段 profiling；可补 10 KV／11 检查点 I/O 瓶颈，基于 Linux 5.15.143 的实现与现行栈分开。 |
| 61. [Building an Elastic Block Storage over EBOFs Using Shadow Views](../../references/proceedings/NSDI/2025/volume.pdf#page=1153) | 备查 | Flint 用 EBOF shadow view 显式暴露调度与带宽资源；10／11 可补共享存储，服务器间同步可忽略只在论文配置下成立。 |
| 62. [Pushing the Limits of In-Network Caching for Key-Value Stores](../../references/proceedings/NSDI/2025/volume.pdf#page=1171) | 排除 | OrbitCache 的包回流用于网络内键值数据库热项缓存；不是 Transformer KV 状态，不为同名 KV 加入。 |
| 63. [CellReplay: Towards accurate record-and-replay for cellular networks](../../references/proceedings/NSDI/2025/volume.pdf#page=1185) | 备查 | CellReplay 发现同一蜂窝链路轨迹随负载改变而失真，双负载采样校准回放；8／13 可提醒实验证据边界，不新增独立移动网络章。 |
| 64. [Large Network UWB Localization: Algorithms and Implementation](../../references/proceedings/NSDI/2025/volume.pdf#page=1203) | 排除 | Locate3D 融合距离和到达角做 UWB 定位；其拓扑刚性不是 AI 集群通信拓扑的设计约束。 |
| 65. [Towards Energy Efficient 5G vRAN Servers](../../references/proceedings/NSDI/2025/volume.pdf#page=1221) | 备查 | RENC 在亚毫秒期限下调 CPU 频率，并控制低负载区间与控制面尖峰；13 可借鉴余量测量，vRAN 的严格周期不能直接套 Agent 任务。 |
| 66. [Building Massive MIMO Baseband Processing on a Single-Node Supercomputer](../../references/proceedings/NSDI/2025/volume.pdf#page=1237) | 备查 | MegaStation 在 FabreX 上按实时硬件并行度重组 MIMO 流水；与 6 的共享路径相关，但用户要求聚焦 AI，暂不展开基带工作流。 |
| 67. [Efficient Multi-WAN Transport for 5G with OTTER](../../references/proceedings/NSDI/2025/volume.pdf#page=1259) | 排除 | OTTER 解决运营商与云之间多 WAN 的 5G NF 放置；不把跨 WAN 问题作为跨超节点网络的主线。 |
| 68. [Verifying maximum link loads in a changing world](../../references/proceedings/NSDI/2025/volume.pdf#page=1285) | 备查 | Velo 求故障与 BGP 变更下的最坏链路负载；7 已有 AI 流量和割集计算，保留鲁棒性方法，不扩成 ISP 路由验证。 |
| 69. [A Layered Formal Methods Approach to Answering Queue-related Queries](../../references/proceedings/NSDI/2025/volume.pdf#page=1305) | 备查 | QuASI 判断是否存在符合粗计数与队列查询的包轨迹；可补 13 观测不足的边界，其无误报漏报针对形式查询，不是恢复真实队列时间线。 |
| 70. [Runtime Protocol Refinement Checking for Distributed Protocol Implementations](../../references/proceedings/NSDI/2025/volume.pdf#page=1321) | 排除 | Ellsberg 的协议细化检查针对 Etcd／ZooKeeper／Redis Raft 安全行为；不等同训练重放或模型数值可复现性。 |
| 71. [CEGS: Configuration Example Generalizing Synthesizer](../../references/proceedings/NSDI/2025/volume.pdf#page=1343) | 备查 | CEGS 用 GNN 检索／泛化配置样例并由 LLM 合成设备配置；13 可比较生成与验证环节，但不是直接提供模型基础设施性能优化结果。 |
| 72. [Suppressing BGP Zombies with Route Status Transparency](../../references/proceedings/NSDI/2025/volume.pdf#page=1365) | 排除 | RoST 处理 BGP 撤销抑制和跨 AS 验证；与超节点及数据中心模型通信无直接关系。 |
| 73. [ValidaTor: Domain Validation over Tor](../../references/proceedings/NSDI/2025/volume.pdf#page=1383) | 排除 | ValidaTor 通过 Tor 出口做证书域名验证；不是 Agent 沙箱或 AI 请求调度问题。 |
| 74. [From Address Blocks to Authorized Prefixes: Redesigning RPKI ROV with a Hierarchical Hashing Scheme for Fast and Memory-Efficient Validation](../../references/proceedings/NSDI/2025/volume.pdf#page=1397) | 排除 | h2ROV 优化 RPKI 路由源验证的前缀与哈希结构；不补充本书所需模型计算和互联瓶颈方法。 |
| 75. [PreAcher: Secure and Practical Password Pre-Authentication by Content Delivery Networks](../../references/proceedings/NSDI/2025/volume.pdf#page=1415) | 排除 | PreAcher 把密码预认证卸载到 CDN 防应用层 DoS；认证密码学与模型服务路由成本不是同一问题。 |
| 76. [ClubHeap: A High-Speed and Scalable Priority Queue for Programmable Packet Scheduling](../../references/proceedings/NSDI/2025/volume.pdf#page=1437) | 备查 | ClubHeap 用硬件友好堆实现逐周期 PIFO，比较频率与资源；7 可作为队列电路预算旁证，不增加实现细节。 |
| 77. [Self-Clocked Round-Robin Packet Scheduling](../../references/proceedings/NSDI/2025/volume.pdf#page=1453) | 备查 | SCRR 修正 DRR 对包长和长突发的假设，降低短流延迟；7 的公平性可引用，但包调度参数不能直接当作 token 调度策略。 |
| 78. [Everything Matters in Programmable Packet Scheduling](../../references/proceedings/NSDI/2025/volume.pdf#page=1483) | 备查 | PACKS 同时近似 PIFO 的排序和接纳，说明有限队列不只看次序；7 可补丢弃策略边界，暂不并列展开多种队列算法。 |
| 79. [When P4 Meets Run-to-completion Architecture](../../references/proceedings/NSDI/2025/volume.pdf#page=1503) | 备查 | P4RTC 用 RTC 芯片的架构模型和 profiling 支持 P4，可与 5 的模型误差／实测反馈相连；1.2 Tbps 是原型条件，行业状态需另核对。 |
| 80. [Mutant: Learning Congestion Control from Existing Protocols via Online Reinforcement Learning](../../references/proceedings/NSDI/2025/volume.pdf#page=1523) | 备查 | Mutant 从已有拥塞协议在线学习切换并检查公平；与 8 反馈选择相关，但不是 RLHF/GRPO 训练调度工作。 |
| 81. [CATO: End-to-End Optimization of ML-Based Traffic Analysis Pipelines](../../references/proceedings/NSDI/2025/volume.pdf#page=1539) | 候选 | CATO 同时优化网络流量分类的质量与完整服务流水成本；13 可补为何只测模型推断会失真，需保留任务、特征抽取与零丢包吞吐的口径。 |
| 82. [Resolving Packets from Counters: Enabling Multi-scale Network Traffic Super Resolution via Composable Large Traffic Model](../../references/proceedings/NSDI/2025/volume.pdf#page=1557) | 备查 | ZOOMSYNTH 从粗计数合成多粒度包轨迹，是受规则约束的生成而非恢复唯一真实历史；13 可对照 QuASI 的观测不充分，不能拿合成流量作生产实测。 |
| 83. [BFTBrain: Adaptive BFT Consensus with Reinforcement Learning](../../references/proceedings/NSDI/2025/volume.pdf#page=1579) | 排除 | BFTBrain 用 RL 切换拜占庭共识协议；不因使用 RL 就归为模型强化学习基础设施。 |

## 重点章节与采用边界

- **ByteCheckpoint: A Unified Checkpointing System for Large Foundation Model Development**：读引言末段、§2–8（物理页 3–14）与附录 A–E、F 开头（19–20）：张量／dataloader 表示、加载重分片、异步流水、持久化与规模瓶颈，表 1–9 和图注文；未独立量化曲线，未审全部参考文献或附录 F 末页。比较限制于所列 DCP／MCP 提交和 HDFS 适配，GPU states 与 full states 区分；ETTR 为假设每周期故障的推算指标，布局改变后的曲线连续不证明逐位训练等价。；原整卷物理页 576, 577, 578, 579, 580, 581, 582, 583, 584, 585, 586, 587, 592, 593。
- **AutoCCL: Automated Collective Communication Tuning for Accelerating Distributed and Parallel DNN Training**：读物理页 2–14 的摘要、引言、§2–9：实现／资源参数拆分、定性模型和坐标搜索、训练内反馈与配置一致性、全部评估和失败限制；表 1–8、算法与图注文已读，曲线未独立量化。论文基于 NCCL 2.18.3，A40 的 NVLink 是四对连接而非八卡全互联；按通信耗时搜索并不保证整步全局最优，单峰经验也不是普遍证明。GPU／驱动版本和部分正文／图示数字疑点另记案例，不照搬为当前框架结果。；原整卷物理页 683, 684, 685, 686, 687, 688, 689, 690, 691, 692, 693, 694, 695。

具体推算和采用决策另记案例笔记；新增候选不自动进入正文。历史实验的模型、软件、硬件和质量条件保持原样，本书贯穿模型继续使用 Qwen3／V4／K3。
