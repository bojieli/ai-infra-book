# NSDI 2024：摘要筛选与重点阅读

已按官方日程中的正式论文顺序阅读 112／112 篇完整摘要；4 篇补读所列正文。下载、首页核对、摘要筛选和正文阅读分别记录。

[逐项手工取舍](screening-nsdi-2024.tsv)与[归档清单](../../references/proceedings/NSDI/2024/manifest.json)同步。

| 序号与论文 | 本轮取舍 | 原因与位置 |
| --- | --- | --- |
| 1. [Horus: Granular In-Network Task Scheduler for Cloud Datacenters](../../references/proceedings/NSDI/2024/volume.pdf#page=18) | 候选 | Horus 用交换机维护短任务调度状态；可补 12 的 CPU 短工具任务，但微秒任务假设不等于 token 调度。 |
| 2. [Fast Vector Query Processing for Large Datasets Beyond GPU Memory with Reordered Pipelining](../../references/proceedings/NSDI/2024/volume.pdf#page=40) | 候选 | RUMMY 对超过 GPU 容量的向量检索重排与流水；可补 5／12 检索工具的访存预算，须保留检索质量和数据条件。 |
| 3. [LoLKV: The Logless, Linearizable, RDMA-based Key-Value Storage System](../../references/proceedings/NSDI/2024/volume.pdf#page=58) | 排除 | LoLKV 是 RDMA 键值数据库的复制与线性一致性；与模型 KV cache 的身份和用途不同，不为同名扩写。 |
| 4. [Making Kernel Bypass Practical for the Cloud with Junction](../../references/proceedings/NSDI/2024/volume.pdf#page=72) | 候选 | Junction 从 NIC 队列与固定内存限制解释内核旁路实例密度；可补 12 运行环境，但不能归成轻量 VM 的隔离保证。 |
| 5. [Sifter: An Inversion-Free and Large-Capacity Programmable Packet Scheduler](../../references/proceedings/NSDI/2024/volume.pdf#page=92) | 备查 | Sifter 用桶与 PIFO 的资源速度比实现排序；7 已有队列与反馈主线，待有具体 AI 流量需求再补硬件调度细节。 |
| 6. [Flow Scheduling with Imprecise Knowledge](../../references/proceedings/NSDI/2024/volume.pdf#page=112) | 备查 | QCLIMB 用流长上下界代替精确预知；可检验 7 的调度假设，暂不再加入一个拥塞／优先级算法。 |
| 7. [Pudica: Toward Near-Zero Queuing Delay in Congestion Control for Cloud Gaming](../../references/proceedings/NSDI/2024/volume.pdf#page=130) | 备查 | Pudica 对云游戏帧选择 paced sending 和 BUR 反馈；8 仅保留实时 AI 场景，不能照搬游戏收益。 |
| 8. [Revisiting Congestion Control for Lossless Ethernet](../../references/proceedings/NSDI/2024/volume.pdf#page=148) | 候选 | ACC 以包守恒区分真实拥塞与队头阻塞受害流；可补 7.5 无损以太网的反馈条件，需读正文检验适用拓扑。 |
| 9. [Autothrottle: A Practical Bi-Level Approach to Resource Management for SLO-Targeted Microservices](../../references/proceedings/NSDI/2024/volume.pdf#page=166) | 备查 | Autothrottle 将应用 SLO 与服务 CPU 节流反馈连接；12 需结合实际 AI 多阶段依赖，暂不增加通用微服务背景。 |
| 10. [Jolteon: Unleashing the Promise of Serverless for Serverless Workflows](../../references/proceedings/NSDI/2024/volume.pdf#page=184) | 候选 | Jolteon 用随机延迟与机会约束配置 Serverless 工作流；可补 12 环境资源与期限，但须重新映射 Agent 任务。 |
| 11. [Can't Be Late: Optimizing Spot Instance Savings under Deadlines](../../references/proceedings/NSDI/2024/volume.pdf#page=202) | 候选 | Can’t Be Late 的 Spot 加按需备份考虑截止时间和未知可用性；可补 12 调度，不把历史云价当当前报价。 |
| 12. [Towards Intelligent Automobile Cockpit via A New Container Architecture](../../references/proceedings/NSDI/2024/volume.pdf#page=222) | 排除 | AutoVP 聚焦汽车座舱异构虚拟化和媒体子系统；与本书 Agent 工具／RL 环境范围相距较远。 |
| 13. [MuCache: A General Framework for Caching in Microservice Graphs](../../references/proceedings/NSDI/2024/volume.pdf#page=238) | 备查 | MuCache 缓存跨微服务调用并保持观察等价；可参照 12 工具结果复用，不能当模型前缀缓存。 |
| 14. [A large-scale deployment of DCTCP](../../references/proceedings/NSDI/2024/volume.pdf#page=256) | 候选 | 生产 DCTCP 部署经验补 7.5 新旧流量共存、公平和实现问题；先查与现有 ECN 内容重叠。 |
| 15. [TECC: Towards Efficient QUIC Tunneling via Collaborative Transmission Control](../../references/proceedings/NSDI/2024/volume.pdf#page=270) | 备查 | TECC 处理 QUIC 隧道内外拥塞反馈失配；8 若补实际 AI 上传代理路径可引用，不另开隧道协议史。 |
| 16. [iStack: A General and Stateful Name-based Protocol Stack for Named Data Networking](../../references/proceedings/NSDI/2024/volume.pdf#page=284) | 排除 | iStack 是 NDN 的 OS 内核网络栈；不是本书当前 AI 数据路径主线。 |
| 17. [Cloudcast: High-Throughput, Cost-Aware Overlay Multicast in the Cloud](../../references/proceedings/NSDI/2024/volume.pdf#page=298) | 备查 | Cloudcast 的跨地域复制考虑吞吐与出口费用；10／12 权重分发可参照，明确是 WAN 而非 7 的跨超节点网络。 |
| 18. [Understanding Routable PCIe Performance for Composable Infrastructures](../../references/proceedings/NSDI/2024/volume.pdf#page=314) | 采用 | 已读正文 §2–8；补 7.3.2 在途窗口与竞争反馈，区分同路径流量和不同入口公平。Gen3 平台测值不外推全部 PCIe／CXL／UB。 |
| 19. [Alea-BFT: Practical Asynchronous Byzantine Fault Tolerance](../../references/proceedings/NSDI/2024/volume.pdf#page=330) | 排除 | Alea-BFT 聚焦异步拜占庭共识；不扩展为本书通用分布式系统内容。 |
| 20. [Harmony: A Congestion-free Datacenter Architecture](../../references/proceedings/NSDI/2024/volume.pdf#page=346) | 备查 | Harmony 在无故障条件下承诺消息延迟与队列界；可检验 7 反馈与保证边界，不能省略故障假设。 |
| 21. [SwiftPaxos: Fast Geo-Replicated State Machines](../../references/proceedings/NSDI/2024/volume.pdf#page=362) | 排除 | SwiftPaxos 的跨地域状态机复制与争用投票优化不直接补模型切分或推理状态主线。 |
| 22. [The Bedrock of Byzantine Fault Tolerance: A Unified Platform for BFT Protocols Analysis, Implementation, and Experimentation](../../references/proceedings/NSDI/2024/volume.pdf#page=388) | 排除 | Bedrock 是 BFT 协议分析与实现平台；不增加共识协议谱系。 |
| 23. [DINT: Fast In-Kernel Distributed Transactions with eBPF](../../references/proceedings/NSDI/2024/volume.pdf#page=418) | 备查 | DINT 以 eBPF 加速内核内事务，提示旁路并非唯一选择；与 7 主机路径重复，暂不引入数据库细节。 |
| 24. [Brain-on-Switch: Towards Advanced Intelligent Network Data Plane via NN-Driven Traffic Analysis at Line-Speed](../../references/proceedings/NSDI/2024/volume.pdf#page=436) | 备查 | Brain-on-Switch 将受限 RNN 数据平面与主机 Transformer 组合；13 可参照约束驱动分工，非通用 LLM 上交换机方案。 |
| 25. [The Eternal Tussle: Exploring the Role of Centralization in IPFS](../../references/proceedings/NSDI/2024/volume.pdf#page=458) | 排除 | IPFS 的索引、DHT 与 HTTP 网关集中化经验不直接解决既定 AI Infra 算例。 |
| 26. [BBQ: A Fast and Scalable Integer Priority Queue for Hardware Packet Scheduling](../../references/proceedings/NSDI/2024/volume.pdf#page=472) | 备查 | BBQ 用流水化整数优先队列兼顾流数和包速；与 5／7 已有资源约束相通，暂不细讲交换机队列实现。 |
| 27. [Sirius: Composing Network Function Chains into P4-Capable Edge Gateways](../../references/proceedings/NSDI/2024/volume.pdf#page=494) | 备查 | Sirius 组合 P4 网络函数链并在 ASIC／CPU 间切分；13 可作编译与硬件容量类比，非模型算子融合本身。 |
| 28. [Empower Programmable Pipeline for Advanced Stateful Packet Processing](../../references/proceedings/NSDI/2024/volume.pdf#page=508) | 备查 | RAPID 用侧环与推测执行处理流水状态依赖；需要专门数据平面背景，暂不进入核心章节。 |
| 29. [GRACE: Loss-Resilient Real-Time Video through Neural Codecs](../../references/proceedings/NSDI/2024/volume.pdf#page=526) | 备查 | GRACE 是有损实时视频的联合训练编解码器；与 OSDI 2026 图执行 GraCE 区分，8 不展开视频压缩专题。 |
| 30. [LiFteR: Unleash Learned Codecs in Video Streaming with Loose Frame Referencing](../../references/proceedings/NSDI/2024/volume.pdf#page=550) | 备查 | LiFteR 通过改变帧依赖提升神经编解码并行；13 可说明依赖与流水，但本书 8 的 AI 交互例子已足够。 |
| 31. [MadEye: Boosting Live Video Analytics Accuracy with Adaptive Camera Configurations](../../references/proceedings/NSDI/2024/volume.pdf#page=566) | 备查 | MadEye 改变摄像机方向以提高分析质量／资源效率；属于输入采集控制，避免扩展到摄像机专题。 |
| 32. [Gemino: Practical and Robust Neural Compression for Video Conferencing](../../references/proceedings/NSDI/2024/volume.pdf#page=586) | 备查 | Gemino 的低码率人像恢复依赖参考图与个性化；不能套到保留 RAW 信息的精修或 Computer Use 截图。 |
| 33. [ARTEMIS: Adaptive Bitrate Ladder Optimization for Live Video Streaming](../../references/proceedings/NSDI/2024/volume.pdf#page=608) | 排除 | ARTEMIS 的直播码率阶梯优化不是本书既定 AI 服务的关键限制，不增加传统直播背景。 |
| 34. [Credence: Augmenting Datacenter Switch Buffer Sharing with ML Predictions](../../references/proceedings/NSDI/2024/volume.pdf#page=630) | 备查 | Credence 的学习预测受硬件丢弃能力限制并有误差退化界；7 已有反馈推算，暂不加独立 ML 缓冲算法。 |
| 35. [Seer: Enabling Future-Aware Online Caching in Networked Systems](../../references/proceedings/NSDI/2024/volume.pdf#page=652) | 备查 | Seer 提前通知在途包以改善状态缓存；与 OSDI 2026 同名 RL 系统不同，不等于预知未来 LLM 请求。 |
| 36. [Reverie: Low Pass Filter-Based Switch Buffer Sharing for Datacenters with RDMA and TCP Traffic](../../references/proceedings/NSDI/2024/volume.pdf#page=668) | 候选 | Reverie 协调入口／出口缓冲视图与 RDMA／TCP 混合突发；可补 7.5 共享缓冲隔离，先读具体队列条件。 |
| 37. [Precise Data Center Traffic Engineering with Constrained Hardware Resources](../../references/proceedings/NSDI/2024/volume.pdf#page=686) | 备查 | TE 权重分布受交换机表资源与精度限制；可补 7.5 理想选路与实际映射，暂不细分多种路由算法。 |
| 38. [Multitenant In-Network Acceleration with SwitchVM](../../references/proceedings/NSDI/2024/volume.pdf#page=708) | 排除 | SwitchVM 是 P4 数据平面的多租户程序沙箱；与第 12 章 Agent 的云沙箱不是同一种运行环境。 |
| 39. [Characterization of Large Language Model Development in the Datacenter](../../references/proceedings/NSDI/2024/volume.pdf#page=726) | 候选 | 六个月 LLM 集群开发记录涵盖利用率、故障与评估调度；可补 11／12，需辨明观测范围和生产工作负载年代。 |
| 40. [QuickUpdate: a Real-Time Personalization System for Large-Scale Recommendation Models](../../references/proceedings/NSDI/2024/volume.pdf#page=748) | 备查 | QuickUpdate 用稀疏更新、优先级与弱一致性降低推荐模型分发；不能直接移为 RL 的无损权重同步。 |
| 41. [MegaScale: Scaling Large Language Model Training to More Than 10,000 GPUs](../../references/proceedings/NSDI/2024/volume.pdf#page=762) | 采用 | 已读 §3–8；补 7.6.3 的就绪偏差、11.3 的固定 batch 扩展和 11.4 初始化。保留 2023 集群及旧基线，不将全部 MFU 收益归给网络。 |
| 42. [Resiliency at Scale: Managing Google’s TPUv4 Machine Learning Supercomputer](../../references/proceedings/NSDI/2024/volume.pdf#page=778) | 候选 | TPUv4 以 OCS 重构绕过硬件故障并协调维修；可补 6／7／11 可用性与进度，区别 TPU 架构论文及可用率口径。 |
| 43. [NN-Defined Modulator: Reconfigurable and Portable Software Modulator on IoT Gateways](../../references/proceedings/NSDI/2024/volume.pdf#page=792) | 备查 | NN-defined modulator 将物理层调制映射到神经网络以跨设备执行；13 可作结构适配类比，暂不增加 IoT 调制专题。 |
| 44. [Democratizing Direct-to-Cell Low Earth Orbit Satellite Networks](../../references/proceedings/NSDI/2024/volume.pdf#page=808) | 排除 | MOSAIC 聚焦移动运营商和卫星多租户接入；与本书模型执行及数据中心资源约束相距较远。 |
| 45. [Known Knowns and Unknowns: Near-realtime Earth Observation Via Query Bifurcation in Serval](../../references/proceedings/NSDI/2024/volume.pdf#page=826) | 备查 | Serval 在星地带宽、能量约束下分割图像分析；可参照 8／13 计算位置，但不以轨道与灾害检测替换既定交互案例。 |
| 46. [Spectrumize: Spectrum-efficient Satellite Networks for the Internet of Things](../../references/proceedings/NSDI/2024/volume.pdf#page=842) | 排除 | Spectrumize 利用多普勒效应改善卫星 IoT 检测与解码；不进入模型 Infra 主线。 |
| 47. [Application-Level Service Assurance with 5G RAN Slicing](../../references/proceedings/NSDI/2024/volume.pdf#page=858) | 备查 | Zipper 用模型预测控制提供应用级 RAN 保障；8 可比较端到端时限，但不扩展完整 5G 切片控制。 |
| 48. [CHISEL: An optical slice of the wide-area network](../../references/proceedings/NSDI/2024/volume.pdf#page=876) | 备查 | CHISEL 是长途光网络切片，需频谱、光程和配置信息；不能归为第 7 章超节点间数据中心交换。 |
| 49. [LuoShen: A Hyper-Converged Programmable Gateway for Multi-Tenant Multi-Service Edge Clouds](../../references/proceedings/NSDI/2024/volume.pdf#page=894) | 备查 | LuoShen 把多服务网络功能折叠到 P4 网关以节约预算；13 的专用硬件取舍可参照，暂不重复网络函数编译案例。 |
| 50. [Sprinter: Speeding Up High-Fidelity Crawling of the Modern Web](../../references/proceedings/NSDI/2024/volume.pdf#page=910) | 备查 | Sprinter 复用浏览器计算加速同站点批量爬取；与逐轮状态变化的 Computer Use 不同，12 若涉及检索采集工具再核。 |
| 51. [Hairpin: Rethinking Packet Loss Recovery in Edge-based Interactive Video Streaming](../../references/proceedings/NSDI/2024/volume.pdf#page=924) | 候选 | Hairpin 在边缘实时流中分开配置首传和重传冗余；8 的截图／语音时限可参照，但须验证往返时延和错误恢复条件。 |
| 52. [Finding Adversarial Inputs for Heuristics using Multi-level Optimization](../../references/proceedings/NSDI/2024/volume.pdf#page=944) | 候选 | MetaOpt 寻找启发式的反例和性能差距；13 可补模型化后的反证方法，先与已有调优反馈内容比较，不堆求解器细节。 |
| 53. [Towards provably performant congestion control](../../references/proceedings/NSDI/2024/volume.pdf#page=968) | 备查 | CCA 形式化分析给出必要动作、信息条件及不可能性；7 可参照反馈边界，暂不引入完整合成框架。 |
| 54. [EPVerifier: Accelerating Update Storms Verification with Edge-Predicate](../../references/proceedings/NSDI/2024/volume.pdf#page=996) | 排除 | EPVerifier 中 EP 指 edge predicate；是网络规则更新验证，不是专家并行，避免因缩写相同误收录。 |
| 55. [Netcastle: Network Infrastructure Testing At Scale](../../references/proceedings/NSDI/2024/volume.pdf#page=1010) | 备查 | Netcastle 用大规模持续网络测试提高变更可靠性；7／13 可留工程背景，当前诊断和故障主线不需再开 CI 平台小节。 |
| 56. [MESSI: Behavioral Testing of BGP Implementations](../../references/proceedings/NSDI/2024/volume.pdf#page=1026) | 排除 | MESSI 生成 BGP 黑盒行为测试；不扩展至通用路由协议验证章节。 |
| 57. [A High-Performance Design, Implementation, Deployment, and Evaluation of The Slim Fly Network](../../references/proceedings/NSDI/2024/volume.pdf#page=1042) | 候选 | Slim Fly 有 200 服务器的实际低直径网络部署与 DNN 评估；6／7 比较拓扑成本时应读布线、路由和负载条件。 |
| 58. [Crescent: Emulating Heterogeneous Production Network at Scale](../../references/proceedings/NSDI/2024/volume.pdf#page=1062) | 备查 | Crescent 以真实交换机镜像和对称子网控制仿真范围；符合先判边界再模拟的方法，暂不展开通用网络仿真平台。 |
| 59. [Reasoning about Network Traffic Load Property at Production Scale](../../references/proceedings/NSDI/2024/volume.pdf#page=1080) | 备查 | Jingubang 推算生产 WAN 变更后的流量负载；可参照约束检查，但不将 WAN BGP 逻辑混入跨超节点网络。 |
| 60. [POSEIDON: A Consolidated Virtual Network Controller that Manages Millions of Tenants via Config Tree](../../references/proceedings/NSDI/2024/volume.pdf#page=1100) | 排除 | POSEIDON 是虚拟网络配置控制器；其树形依赖优化不直接补现有模型调度算例。 |
| 61. [OPPerTune: Post-Deployment Configuration Tuning of Services Made Easy](../../references/proceedings/NSDI/2024/volume.pdf#page=1118) | 候选 | OPPerTune 处理上线后配置搜索的扰动和离散／连续参数；13 可补离线最优与动态负载变化，需与 Agent 调优区分。 |
| 62. [Parcae: Proactive, Liveput-Optimized DNN Training on Preemptible Instances](../../references/proceedings/NSDI/2024/volume.pdf#page=1138) | 候选 | Parcae 把抢占后的预期训练吞吐与迁移成本纳入并行选择；11／12 可补 Spot，须检验可用性预测误差及 liveput 口径。 |
| 63. [Accelerating Neural Recommendation Training with Embedding Scheduling](../../references/proceedings/NSDI/2024/volume.pdf#page=1158) | 候选 | Herald 用可预见 embedding 访问调整训练位置和同步；11／13 可对比数据与状态移动，不能直接等同于 MoE 专家路由。 |
| 64. [DISTMM: Accelerating Distributed Multimodal Model Training](../../references/proceedings/NSDI/2024/volume.pdf#page=1174) | 候选 | DISTMM 日程题名与摘要系统名 DISTIMM 均保留；多模态子模块采用不同并行且受对比损失跨样本依赖约束，可补 3／11。 |
| 65. [Approximate Caching for Efficiently Serving Text-to-Image Diffusion Models](../../references/proceedings/NSDI/2024/volume.pdf#page=1190) | 候选 | NIRVANA 复用相近提示的扩散噪声中间状态；9／13 可比较近似复用与精确缓存，须保留质量／随机性条件。 |
| 66. [THC: Accelerating Distributed Deep Learning Using Tensor Homomorphic Compression](../../references/proceedings/NSDI/2024/volume.pdf#page=1208) | 候选 | THC 在压缩域直接聚合以省 PS 解压重压，可与 6／11 通信压缩对照；目标精度和到达该精度的时间必须一起比较。 |
| 67. [Accelerating Skewed Workloads With Performance Multipliers in the TurboDB Distributed Database](../../references/proceedings/NSDI/2024/volume.pdf#page=1230) | 排除 | TurboDB 通过单机／分布式数据库混合结构处理事务偏斜；不因“热点”类比就扩写数据库机制。 |
| 68. [SIEVE is Simpler than LRU: an Efficient Turn-Key Eviction Algorithm for Web Caches](../../references/proceedings/NSDI/2024/volume.pdf#page=1246) | 备查 | SIEVE 的命中开销、淘汰与并发性可补缓存比较；Web cache 的对象价值与模型 KV 重算成本不同，暂不直接移用命中率。 |
| 69. [Harvesting Idle Memory for Application-managed Soft State with Midas](../../references/proceedings/NSDI/2024/volume.pdf#page=1264) | 候选 | Midas 以可撤销和重建的 soft memory 回收空闲主存；10／12 缓存与环境共享可参照，检查重建成本和接口侵入性。 |
| 70. [Efficient Exposure of Partial Failure Bugs in Distributed Systems with Inferred Abstract States](../../references/proceedings/NSDI/2024/volume.pdf#page=1284) | 备查 | Legolas 用程序抽象状态指导细粒度故障注入；11／12 可留测试方法，但当前未读正文，不能作为已复现故障保证。 |
| 71. [Load is not what you should balance: Introducing Prequal](../../references/proceedings/NSDI/2024/volume.pdf#page=1302) | 候选 | Prequal 以预估延迟和在途请求选后端而非均衡 CPU；10／12 路由可参照，但要重新纳入 KV 复用和 token 成本。 |
| 72. [Orthcatter: High-throughput In-band OFDM Backscatter with Over-the-Air Code Division](../../references/proceedings/NSDI/2024/volume.pdf#page=1318) | 排除 | Orthcatter 的 OFDM 反射通信与空中码分不属于本书模型资源主线。 |
| 73. [EdgeRIC: Empowering Real-time Intelligent Optimization and Control in NextG Cellular Networks](../../references/proceedings/NSDI/2024/volume.pdf#page=1332) | 备查 | EdgeRIC 将 AI 控制放在 RAN 本地以满足亚毫秒周期；8 可参照计算位置，暂不新增无线控制流程。 |
| 74. [ADR-X: ANN-Assisted Wireless Link Rate Adaptation for Compute-Constrained Embedded Gaming Devices](../../references/proceedings/NSDI/2024/volume.pdf#page=1348) | 备查 | ADR-X 用领域先验设计轻量 ANN 满足控制时限；13 有同类取舍，避免加入游戏外设专章。 |
| 75. [RFID+: Spatially Controllable Identification of UHF RFIDs via Controlled Magnetic Fields](../../references/proceedings/NSDI/2024/volume.pdf#page=1368) | 排除 | RFID+ 关注磁场与标签空间选择性；不进入 AI Infra 大纲。 |
| 76. [SMUFF: Towards Line Rate Wi-Fi Direct Transport with Orchestrated On-device Buffer Management](../../references/proceedings/NSDI/2024/volume.pdf#page=1386) | 候选 | SMUFF 利用 Wi-Fi Direct 可见缓冲调节发送率；8 的近端传输可参照，必须区别直连链路与远程云 HTTP 服务。 |
| 77. [Vulcan: Automatic Query Planning for Live ML Analytics](../../references/proceedings/NSDI/2024/volume.pdf#page=1402) | 候选 | Vulcan 为实时 ML 查询联合选流水、配置和放置；8／13 可补 profiling 成本，先比较现有端到端案例再决定。 |
| 78. [CASSINI: Network-Aware Job Scheduling in Machine Learning Clusters](../../references/proceedings/NSDI/2024/volume.pdf#page=1420) | 候选 | CASSINI 在作业放置时利用周期通信的相位互补；7／12 可补拥塞前的时间安排，需读跨链路一致性、漂移和重新对齐开销。 |
| 79. [Towards Domain-Specific Network Transport for Distributed DNN Training](../../references/proceedings/NSDI/2024/volume.pdf#page=1438) | 候选 | MLT 的包级多路径、梯度优先级和有限丢失依赖训练算法容错；7／11 须保留收敛边界，不当成对推理 KV 或激活的无损优化。 |
| 80. [Swing: Short-cutting Rings for Higher Bandwidth Allreduce](../../references/proceedings/NSDI/2024/volume.pdf#page=1462) | 候选 | Swing 通过环面方向交替减少归约物理跳数；6.4／6.5 可连接逻辑轮次与链路拥塞，须核非 2 的幂规模及实际平台。 |
| 81. [LitePred: Transferable and Scalable Latency Prediction for Hardware-Aware Neural Architecture Search](../../references/proceedings/NSDI/2024/volume.pdf#page=1480) | 备查 | LitePred 迁移延迟预测器，面对 NAS 模型分布和硬件差异；13 已有实测校准方法，暂不增加独立 NAS 搜索小节。 |
| 82. [Harmonic: Hardware-assisted RDMA Performance Isolation for Public Clouds](../../references/proceedings/NSDI/2024/volume.pdf#page=1496) | 候选 | Harmonic 关注隐藏的 RDMA NIC 微架构资源与隔离；7／12 可补线速以下仍有争用，须区别 FPGA 原型与已部署产品。 |
| 83. [LDB: An Efficient Latency Profiling Tool for Multithreaded Applications](../../references/proceedings/NSDI/2024/volume.pdf#page=1514) | 候选 | LDB 以栈采样和事件标签定位多线程尾延迟；12 工具进程可用作诊断参照，不能把 CPU 采样时长当作 GPU kernel 时间。 |
| 84. [UFO: The Ultimate QoS-Aware Core Management for Virtualized and Oversubscribed Public Clouds](../../references/proceedings/NSDI/2024/volume.pdf#page=1528) | 候选 | UFO 针对虚拟机超售、双重调度及 VM 内争用管理核心；12 的轻量 VM 服务可参照，需核业务和隔离假设。 |
| 85. [Automatic Parallelization of Software Network Functions](../../references/proceedings/NSDI/2024/volume.pdf#page=1548) | 备查 | Maestro 自动并行网络函数并保持状态语义，最终受 PCIe 或线速约束；13 可比较合法性与性能，非 LLM 自动算子优化实现。 |
| 86. [AutoSketch: Automatic Sketch-Oriented Compiler for Query-driven Network Telemetry](../../references/proceedings/NSDI/2024/volume.pdf#page=1568) | 备查 | AutoSketch 用精度意图约束网络遥测编译和资源配置；13 可留编译预算类比，不展开 sketch 算法目录。 |
| 87. [Leo: Online ML-based Traffic Classification at Multi-Terabit Line Rate](../../references/proceedings/NSDI/2024/volume.pdf#page=1590) | 备查 | Leo 在交换机运行可更新决策树并控制表资源；13 已有加速器对照，暂不加新的线速 ML 分类器。 |
| 88. [Sequence Abstractions for Flexible, Line-Rate Network Monitoring](../../references/proceedings/NSDI/2024/volume.pdf#page=1610) | 排除 | FLM 将包序列识别编译成 P4；不是模型序列并行或注意力执行。 |
| 89. [OctoSketch: Enabling Real-Time, Continuous Network Monitoring over Multiple Cores](../../references/proceedings/NSDI/2024/volume.pdf#page=1638) | 备查 | OctoSketch 的多核增量聚合折中查询误差与性能；与模型训练归约目标不同，暂不直接引入。 |
| 90. [NR-Surface: NextG-ready µW-reconfigurable mmWave Metasurface](../../references/proceedings/NSDI/2024/volume.pdf#page=1658) | 排除 | NR-Surface 重点是毫米波超表面功耗、同步和无线控制，不属于既定 AI 系统算例。 |
| 91. [Cyclops: A Nanomaterial-based, Battery-Free Intraocular Pressure (IOP) Monitoring System inside Contact Lens](../../references/proceedings/NSDI/2024/volume.pdf#page=1676) | 排除 | Cyclops 是隐形眼镜内眼压传感器和无源读取；不扩展医学感知器件专题。 |
| 92. [Habitus: Boosting Mobile Immersive Content Delivery through Full-body Pose Tracking and Multipath Networking](../../references/proceedings/NSDI/2024/volume.pdf#page=1694) | 备查 | Habitus 结合姿态预测和多路径改善沉浸媒体；8 只保留与现有 AI 交互时限直接相关的部分，当前不采用。 |
| 93. [BFMSense: WiFi Sensing Using Beamforming Feedback Matrix](../../references/proceedings/NSDI/2024/volume.pdf#page=1714) | 排除 | BFMSense 用 Wi-Fi 波束反馈作感知；不补模型计算、访存或系统调度主线。 |
| 94. [mmComb: High-speed mmWave Commodity WiFi Backscatter](../../references/proceedings/NSDI/2024/volume.pdf#page=1730) | 排除 | mmComb 聚焦商用毫米波反射通信物理层，与本书 AI Infra 范围不符。 |
| 95. [Where The Wild Things Are: Brute-Force SSH Attacks In The Wild And How To Stop Them](../../references/proceedings/NSDI/2024/volume.pdf#page=1748) | 排除 | 生产 SSH 暴力猜密防护是通用安全运维；不因第 12 章有云环境就新增安全专题。 |
| 96. [A System to Detect Forged-Origin BGP Hijacks](../../references/proceedings/NSDI/2024/volume.pdf#page=1768) | 排除 | DFOH 检测公网伪造起源 BGP 劫持，不是数据中心模型并行问题。 |
| 97. [NetVigil: Robust and Low-Cost Anomaly Detection for East-West Data Center Security](../../references/proceedings/NSDI/2024/volume.pdf#page=1788) | 备查 | NetVigil 用图学习检测东西向流量异常；这是 AI 用于网络安全，不等于网络用于 AI，暂不采用。 |
| 98. [TANGO: Secure Collaborative Route Control across the Public Internet](../../references/proceedings/NSDI/2024/volume.pdf#page=1808) | 备查 | TANGO 用边缘协作控制公网跨域路由；8 可留跨地域服务线索，不能写成第 7 章跨超节点协作。 |
| 99. [Sidekick: In-Network Assistance for Secure End-to-End Transport Protocols](../../references/proceedings/NSDI/2024/volume.pdf#page=1830) | 候选 | Sidekick 用旁路反馈帮助加密传输而不读取明文序号；8 可对照中间节点辅助，但需核端点改动与具体链路。 |
| 100. [VILAM: Infrastructure-assisted 3D Visual Localization and Mapping for Autonomous Driving](../../references/proceedings/NSDI/2024/volume.pdf#page=1848) | 排除 | VILAM 是车路协同视觉定位与点云校准；避免引入本书未计划的自动驾驶建图背景。 |
| 101. [Catch Me If You Can: Laser Tethering with Highly Mobile Targets](../../references/proceedings/NSDI/2024/volume.pdf#page=1864) | 排除 | Lasertag 是高速移动目标的激光跟踪与连接；不增加光学机械控制专题。 |
| 102. [MobileConfig: Remote Configuration Management for Mobile Apps at Hyperscale](../../references/proceedings/NSDI/2024/volume.pdf#page=1884) | 备查 | MobileConfig 权衡启动、配置新鲜度与灰度风险；12 可留环境配置类比，暂不替换实际 Agent 运行案例。 |
| 103. [Passengers' Safety Matters: Experiences of Deploying a Large-Scale Indoor Delivery Monitoring System](../../references/proceedings/NSDI/2024/volume.pdf#page=1900) | 排除 | DeMo 聚焦室内配送安全与 BLE／IMU 定位；不纳入模型 Infra。 |
| 104. [AUGUR: Practical Mobile Multipath Transport Service for Low Tail Latency in Real-Time Streaming](../../references/proceedings/NSDI/2024/volume.pdf#page=1918) | 候选 | AUGUR 在实时流中权衡蜂窝字节与 Wi-Fi 尾延迟；8 可补双路径重传，但不要把云游戏倍数移作 AI 实测。 |
| 105. [Zombie: Middleboxes that Don’t Snoop](../../references/proceedings/NSDI/2024/volume.pdf#page=1934) | 备查 | Zombie 将零知识证明预处理、批处理与异步执行分开；虽有相同摊销思想，但不展开密码证明机制。 |
| 106. [Solving Max-Min Fair Resource Allocations Quickly on Large Graphs](../../references/proceedings/NSDI/2024/volume.pdf#page=1954) | 候选 | 多路径 max-min 分配的近似与求解时间可检验 7／12 公平预算；先读理论与误差，不能仅凭单链路 waterfilling 外推。 |
| 107. [Cloud-LoRa: Enabling Cloud Radio Access LoRa Networks Using Reinforcement Learning Based Bandwidth-Adaptive Compression](../../references/proceedings/NSDI/2024/volume.pdf#page=1976) | 排除 | Cloud-LoRa 中 LoRa 是无线调制，不是低秩适配 LoRA；强化学习只是压缩控制方法，不构成 RL 训练系统案例。 |
| 108. [Cloudy with a Chance of Cyberattacks: Dangling Resources Abuse on Cloud Platforms](../../references/proceedings/NSDI/2024/volume.pdf#page=1994) | 备查 | 云资源悬挂与重用涉及环境生命周期；12 当前聚焦容量和执行，只留命名／回收语义线索，不展开攻击测量。 |
| 109. [CAPA: An Architecture For Operating Cluster Networks With High Availability](../../references/proceedings/NSDI/2024/volume.pdf#page=2012) | 备查 | CAPA 用变更调节层降低网络运维故障；7／13 可留可用性工程参照，不增加通用变更治理章节。 |
| 110. [NetAssistant: Dialogue Based Network Diagnosis in Data Center Networks](../../references/proceedings/NSDI/2024/volume.pdf#page=2028) | 候选 | NetAssistant 是实际网络诊断对话工作流；12 可补 Agent 工具路径和证据，但需核历史模型与能力，不能当现代推理模型实现。 |
| 111. [Klonet: an Easy-to-Use and Scalable Platform for Computer Networks Education](../../references/proceedings/NSDI/2024/volume.pdf#page=2042) | 备查 | Klonet 可参考实验平台可用性与共享资源；不以部署上万仿真路由器取代本书先手算的教学方法。 |
| 112. [ExChain: Exception Dependency Analysis for Root Cause Diagnosis](../../references/proceedings/NSDI/2024/volume.pdf#page=2064) | 备查 | ExChain 追踪跨异常状态传播以诊断根因；12 可留执行失败研究，与当前 RL 角色恢复互补但暂未读正文。 |

## 重点章节与采用边界

- **Understanding Routable PCIe Performance for Composable Infrastructures**：读 §2–8 的正文及表 2（单篇物理页 3–13），包括平台、端点事务、共享路径、算法和验证；图中文字与正文已读，未独立提取曲线，未读附录或核验全部参考文献。测量限于论文 FabreX／Gen3／FPGA 条件，不把公平性和方向隔离当成全部 PCIe／CXL／UB 的保证。；原整卷物理页 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325。
- **MegaScale: Scaling Large Language Model Training to More Than 10,000 GPUs**：读背景末段及 §3–8（单篇物理页 4–14）：3D 重叠、初始化、网络、诊断与评估；表 1–3 及图注文读，曲线未独立量化，未审全部参考文献。固定 batch 扩展与改变模型／优化器／batch 的消融分开，2023 年集群和旧 Megatron 基线不代表当前框架。；原整卷物理页 764, 765, 766, 767, 768, 769, 770, 771, 772, 773, 774。
- **CASSINI: Network-Aware Job Scheduling in Machine Learning Clusters**：读 §2–8（单篇物理页 3–14）及附录 B／C（页 19）：流量周期、兼容度、放置与唯一时间偏移、评估和局限，表 1–3 与图注文；未独立量化曲线，未读附录 A 证明或审完参考文献。24 台单 A100 40 GB／50 Gbps 的主实验与 6 台双 GPU 扩展分开；周期、无 GPU 共享、独立训练网络及无环候选条件明确保留。；原整卷物理页 1421, 1422, 1423, 1424, 1425, 1426, 1427, 1428, 1429, 1430, 1431, 1432, 1437。
- **Swing: Short-cutting Rings for Higher Bandwidth Allreduce**：读引言末段及 §2–7（单篇物理页 3–14）：轮次、字节与物理链路拥塞，Swing 单维／多维／非二次幂设计、SST 评估及拓扑局限；表 1–2 与图注文已读，曲线未独立量化，附录证明与全部参考文献未审。性能为论文网络仿真，不称为 TPU／NCCL 实测；采用逐轮路由枚举教学例，不照搬正文中有不一致的简式。；原整卷物理页 1463, 1464, 1465, 1466, 1467, 1468, 1469, 1470, 1471, 1472, 1473, 1474。

具体推算和采用决策另记案例笔记；新增候选不自动进入正文。历史实验的模型、软件、硬件和质量条件保持原样，本书贯穿模型继续使用 Qwen3／V4／K3。
