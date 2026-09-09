# ASPLOS 2025：公开稿、摘要筛选与专题正文

截至 2026-09-09，官方主日程 184 个 DOI 中已归档 55 份代表 PDF／941 页、完成 58 篇原始完整摘要筛选，十一篇有声明范围的正文阅读；其余 126 篇摘要未读。另存 PipeLLM 十五页正式格式作者稿，物理页 1–13 已读、六页图像已查看；代表 PDF 与原始摘要数量保持，新增副本不重复计算论文。

出版卷、演讲年份、作者版本与实际读取范围分开。QRCC 作者稿写 Volume 1，但正式 DOI 的出版元数据为 Volume 4；DarwinGame 2025-09 上传稿晚于正式出版，且留有 Conference17／占位 DOI，身份由完整题名和作者核对。见[归档说明](../../references/proceedings/ASPLOS/2025/README.md)。

| 日程编号与论文 | 取舍 | 判断与位置 |
| --- | --- | --- |
| 3. [Accelerating Retrieval-Augmented Generation](../../references/proceedings/ASPLOS/2025/public/iks-v1.pdf) | 重点阅读并整合 | 检索精度会改变生成输入，适合 13.1／13.4 的协同设计；将历史 NQ／Llama 基线、模拟硬件和 Qwen3 教学预算分开。 |
| 4. [GUST: Graph Edge-Coloring Utilization for Accelerating Sparse Matrix Vector Multiplication](../../references/proceedings/ASPLOS/2025/public/gust-v1.pdf) | 备查 | SpMV 的乘加资源共享与边着色可说明稀疏映射，但已有注意力／MoE 贯穿案例；暂不增添通用稀疏加速器。 |
| 6. [Orion: A Fully Homomorphic Encryption Framework for Deep Learning](../../references/proceedings/ASPLOS/2025/public/orion-v3.pdf) | 排除 | FHE 私密神经推理的密文打包与 bootstrap 编译，超出本书明文模型执行与 Agent 沙箱主线。 |
| 7. [CIPHERMATCH: Accelerating Homomorphic Encryption-Based String Matching via Memory-Efficient Data Packing and In-Flash Processing](../../references/proceedings/ASPLOS/2025/public/ciphermatch-v1.pdf) | 排除 | 加密字符串匹配与闪存内计算面向 DNA／数据库；不因包含数据搬移就扩展为 AI Infra 正文。 |
| 8. [ReSBM: Region-based Scale and Minimal-Level Bootstrapping Management for FHE via Min-Cut](../../references/proceedings/ASPLOS/2025/public/resbm.pdf) | 排除 | 密文 scale 与 bootstrap 的联合管理属于 FHE 专用编译；不替代第 5 章张量切分和融合。 |
| 9. [HALO: Loop-aware Bootstrapping Management for Fully Homomorphic Encryption](../../references/proceedings/ASPLOS/2025/public/halo-author.html) | 排除 | FHE 循环中 ciphertext level 与 bootstrap 放置，和本书推理循环／CUDA Graph 不是同一问题。 |
| 11. [FMCC: Flexible Measurement-based Quantum Computation over Cluster State](../../references/proceedings/ASPLOS/2025/public/paper-011.pdf) | 排除 | 光子量子计算的测量深度与纠错代价，和本书张量分块／模型并行不同；不扩展量子编译专题。 |
| 12. [QRCC: Evaluating Large Quantum Circuits on Small Quantum Computers through Integrated Qubit Reuse and Circuit Cutting](../../references/proceedings/ASPLOS/2025/public/paper-012.pdf) | 排除 | 量子比特复用与电路切割的经典后处理成本，不能直接类比 TP／PP 的张量通信。 |
| 13. [Optimizing Quantum Circuits, Fast and Slow](../../references/proceedings/ASPLOS/2025/public/paper-013.pdf) | 排除 | 量子电路重写与酉矩阵合成，主要约束是门数与近似误差；不替代 AI 算子融合案例。 |
| 15. [Fat-Tree QRAM: A High-Bandwidth Shared Quantum Random Access Memory for Parallel Queries](../../references/proceedings/ASPLOS/2025/public/paper-015.pdf) | 排除 | 量子 QRAM 的叠加态查询与量子比特资源，不能用名称相似替代第 7 章的数据中心 Fat-tree。 |
| 18. [Earth+: On-Board Satellite Imagery Compression Leveraging Historical Earth Observations](../../references/proceedings/ASPLOS/2025/public/paper-018.pdf) | 备查 | 跨卫星共享历史影像、以有限上行改善差分压缩；第 12 章已有截图／图像案例，暂不增加卫星系统。 |
| 20. [Nazar: Monitoring and Adapting ML Models on Mobile Devices](../../references/proceedings/ASPLOS/2025/public/paper-020.pdf) | 备查 | 端侧视觉模型的漂移监测与适应，作为第 12／13 章质量反馈备查，不从摘要移植准确率或系统性能。 |
| 21. [Composing Distributed Computations Through Task and Kernel Fusion](../../references/proceedings/ASPLOS/2025/public/paper-021.pdf) | 重点阅读并整合 | 物理页 2–13 已读；任务合并、临时存储与跨分片依赖接回 5.3.1／6.4.4。科学计算和固定推理框架分别取证。 |
| 22. [CXLfork: Fast Remote Fork over CXL Fabrics](../../references/proceedings/ASPLOS/2025/public/paper-022.pdf) | 重点阅读并整合 | 物理页 2–14 已读；共享只读页、写时复制和分层读取接回 11.2／实验 11-2。CPU 进程原型、E2B microVM 和教学预算分开。 |
| 26. [Enhancing CGRA Efficiency Through Aligned Compute and Communication Provisioning](../../references/proceedings/ASPLOS/2025/public/paper-026.pdf) | 备查 | CGRA 的计算与互联按子图 motif 配比，可作 4／13 的结构取舍备选；先与已有 GPU／昇腾代际案例比较。 |
| 27. [Squeezing Operator Performance Potential for the Ascend Architecture](../../references/proceedings/ASPLOS/2025/public/paper-027.pdf) | 重点阅读并整合 | 正文物理页 2–14 已读；用单元活动时间和忙时效率补 5.2.3／5.3.5。历史 MindSpore 工作负载、论文算子库声明与当前 vLLM Ascend 分派分开。 |
| 28. [PICACHU: Plug-In CGRA Handling Upcoming Nonlinear Operations in LLMs](../../references/proceedings/ASPLOS/2025/public/paper-028.pdf) | 重点阅读并整合 | 物理页 2–12 已读；资源配比、共享缓冲与实际函数求值接 4.2.4／13.4.2。RTL／建模比较与固定 vLLM 缓存路径分开，不移植总加速比。 |
| 33. [Coach: Exploiting Temporal Patterns for All-Resource Oversubscription in Cloud Platforms](../../references/proceedings/ASPLOS/2025/public/paper-033.pdf) | 候选待读 | Azure 多资源超售与时间互补，可能补 11 的 CPU 环境容量；需与 CASSINI／Weave 的互补调度比较，避免泛化到 GPU。 |
| 34. [Cooperative Graceful Degradation in Containerized Clouds](../../references/proceedings/ASPLOS/2025/public/paper-034.pdf) | 备查 | Phoenix 按应用依赖和关键性关闭非关键容器，作为第 11 章故障降级备查；不把一般微服务的可用性直接当作 Agent 成功率。 |
| 35. [DarwinGame: Playing Tournaments for Tuning Applications in Noisy Cloud Environments](../../references/proceedings/ASPLOS/2025/public/paper-035.pdf) | 重点阅读并整合 | 物理页 1–13 已读；配对测量与候选之间的争用补 5.3.5／实验 5-6。公开工件与论文算法有差距，仅作方法对照，不采用 CPU 加速比或声称 GPU 可复现。 |
| 36. [Copper and Wire: Bridging Expressiveness and Performance for Service Mesh Policies](../../references/proceedings/ASPLOS/2025/public/paper-036.pdf) | 备查 | L7 策略表达与 sidecar 放置，供 11 的控制路径备查；不是 TP／EP 集合通信或模型路由的直接实现。 |
| 37. [MetaSapiens: Real-Time Neural Rendering with Efficiency-Aware Pruning and Accelerated Foveated Rendering](../../references/proceedings/ASPLOS/2025/public/paper-037.pdf) | 备查 | 点式神经渲染按计算成本剪枝及注视点质量取舍；可补 12／13 的质量约束，暂不展开新的渲染主线。 |
| 38. [D-VSync: Decoupled Rendering and Displaying for Smartphone Graphics](../../references/proceedings/ASPLOS/2025/public/paper-038.pdf) | 备查 | 显示前预执行缓解长帧，保留真实交互边界；图形合成机制不直接迁移为实时 AI 请求的吞吐保证。 |
| 39. [StreamGrid: Streaming Point Cloud Analytics via Compulsory Splitting and Deterministic Termination](../../references/proceedings/ASPLOS/2025/public/paper-039.pdf) | 备查 | 物理页 2–12 已读；点云切分与提前终止改变算法工作及质量，缓冲模型需要给定数据流；作为 5／13 方法参照，不增加渲染专题。 |
| 40. [ARC: Warp-level Adaptive Atomic Reduction in GPUs to Accelerate Differentiable Rendering](../../references/proceedings/ASPLOS/2025/public/paper-040.pdf) | 备查 | 物理页 2–13 已读；高 L2 命中仍可能受原子队列限制，warp 内归约另有指令和寄存器代价；软件实测与新增硬件模拟分开，暂不扩展正文。 |
| 41. [Treelet Accelerated Ray Tracing on GPUs](../../references/proceedings/ASPLOS/2025/public/paper-041.pdf) | 备查 | RT 遍历用队列和 warp 重组改善局部性；不是当前 LLM 注意力路径，暂不增加光追案例。 |
| 43. [Mint: Cost-Efficient Tracing with All Requests Collection via Commonality and Variability Analysis](../../references/proceedings/ASPLOS/2025/public/paper-043.pdf) | 备查 | trace 模式聚合与参数过滤降低采集成本；全请求覆盖不等于保留全部信息，供实验记录取舍备查。 |
| 44. [Automatic Tracing in Task-Based Runtime Systems](../../references/proceedings/ASPLOS/2025/public/paper-044.pdf) | 重点阅读并整合 | 物理页 2–12、16–17 已读；身份、匹配等待与准备成本接 5.4.4／实验 5-8。Legion 工件与固定 vLLM 图封装分开；历史 DP 训练结果不外推当前模型。 |
| 46. [Rethinking Java Performance Analysis](../../references/proceedings/ASPLOS/2025/public/paper-046.pdf) | 备查 | DaCapo 负载更新和用户延迟方法支持测量取舍；已有 AI 调优案例，保留方法参照而不添加 Java 专节。 |
| 48. [Cinnamon: A Framework for Scale-Out Encrypted AI](../../references/proceedings/ASPLOS/2025/public/paper-048.pdf) | 备查 | FHE 的多层并行与芯片资源配比，任务语义与普通推理不同；不能将加密 CPU 基线倍数并入常规 GPU 比较。 |
| 49. [PipeLLM: Fast and Confidential Large Language Model Services with Speculative Pipelined Encryption](../../references/proceedings/ASPLOS/2025/pipellm/author-final.pdf) | 重点阅读并整合 | 正式格式作者稿物理页 1–13 已读；提前准备、额外复制与有用工作接 5.2.3。历史换出、工件限制与 V1 抢占／connector 分开。 |
| 50. [Practical Federated Recommendation Model Learning Using ORAM with Controlled Privacy](../../references/proceedings/ASPLOS/2025/public/paper-050.pdf) | 备查 | FEDORA 为联邦推荐的嵌入子集访问引入 ORAM、隐私预算和 SSD 布局；可作约束参照，不扩展本书的 LLM 训练主线。 |
| 51. [Tackling ML-based Dynamic Mispredictions using Statically Computed Invariants for Attack Surface Reduction](../../references/proceedings/ASPLOS/2025/public/paper-051-landing.html) | 排除 | ML 预测程序调用集后用静态关系区分失配与攻击，属于 CPU 程序去膨胀和安全分析；不是模型服务的推测解码。 |
| 52. [Control Logic Synthesis: Drawing the Rest of the OWL](../../references/proceedings/ASPLOS/2025/public/paper-052.pdf) | 排除 | 根据 ISA／架构规格合成 SoC 控制逻辑，主要验证 RISC-V 与密码加速器；不同于第 5 章以 profiling 反馈优化张量内核。 |
| 53. [CRUSH: A Credit-Based Approach for Functional Unit Sharing in Dynamically Scheduled HLS](../../references/proceedings/ASPLOS/2025/public/paper-053.pdf) | 备查 | CRUSH 以 credit 和依赖约束共享 HLS 功能单元；保留资源共享方法参照，不将 Dynamatic 集成声明写成推理框架特性。 |
| 54. [AMuLeT: Automated Design-Time Testing of Secure Speculation Countermeasures](../../references/proceedings/ASPLOS/2025/public/paper-054.pdf) | 排除 | AMuLeT 在微架构模拟器内测试安全投机防护；这里的 speculation 不是 LLM 推测解码，不增加 CPU 攻击专题。 |
| 55. [Don't Repeat Yourself! Coarse-Grained Circuit Deduplication to Accelerate RTL Simulation](../../references/proceedings/ASPLOS/2025/public/paper-055-author.pdf) | 排除 | RTL 仿真的共享指令代码与 LLC 瓶颈；本书已有 AI 复用和争用例子，不展开 EDA 仿真系统。 |
| 56. [Parendi: Thousand-Way Parallel RTL Simulation](../../references/proceedings/ASPLOS/2025/public/paper-056.pdf) | 备查 | Parendi 为 Graphcore IPU 上的 RTL 仿真平衡同步、通信和计算；有切分方法价值，已有 AI 贯穿案例，不另开 EDA 仿真内容。 |
| 58. [Embracing Imbalance: Dynamic Load Shifting among Microservice Containers in Shared Clusters](../../references/proceedings/ASPLOS/2025/public/paper-058.pdf) | 备查 | Imbres 联合调整微服务容器的负载、连接和资源；可作 11 的争用背景，不能直接等同 MoE 专家调度或模型 goodput。 |
| 60. [FleetIO: Managing Multi-Tenant Cloud Storage with Multi-Agent Reinforcement Learning](../../references/proceedings/ASPLOS/2025/public/paper-060.pdf) | 备查 | 虚拟 SSD 的隔离、利用率与 RL 奖励取舍；不是模型 RL 训练调度，暂不扩展存储控制器专题。 |
| 61. [ZRAID: Leveraging Zone Random Write Area (ZRWA) for Alleviating Partial Parity Tax in ZNS RAID](../../references/proceedings/ASPLOS/2025/public/paper-061-landing.html) | 备查 | ZRAID 借 ZRWA 改变 ZNS RAID 部分校验的写入与回收；仅作存储写放大背景，不直接移植为 KV 缓存性能。 |
| 63. [MOAT: Securely Mitigating Rowhammer with Per-Row Activation Counters](../../references/proceedings/ASPLOS/2025/public/paper-063.pdf) | 排除 | MOAT 研究 DRAM 行激活计数与 Rowhammer 防护，超出 AI 资源配置和模型运行环境主线。 |
| 64. [HyperHammer: Breaking Free from KVM-Enforced Isolation](../../references/proceedings/ASPLOS/2025/public/paper-064.pdf) | 排除 | HyperHammer 是特定配置下的虚拟化隔离概念验证；摘要明确限定系统条件，不用它替代 Agent 沙箱设计或泛化现行服务风险。 |
| 79. [MVQ: Towards Efficient DNN Compression and Acceleration with Masked Vector Quantization](../../references/proceedings/ASPLOS/2025/public/paper-079.pdf) | 备查 | N:M 剪枝、向量码本和阵列协同，实验主要是视觉 CNN；已有模型量化主线，暂不增算法小节。 |
| 87. [Bounding Speculative Execution of Atomic Regions to a Single Retry](../../references/proceedings/ASPLOS/2025/public/paper-087.pdf) | 排除 | 共享内存原子区域的事务重试与 cacheline 锁，区别于 LLM 的推测解码和 rollout 重试。 |
| 94. [FSMoE: A Flexible and Scalable Training System for Sparse Mixture-of-Experts Models](../../references/proceedings/ASPLOS/2025/public/paper-094.pdf) | 重点阅读并整合 | 已读物理页 1–13；采用梯度就绪、共享跨机链路与分桶空隙的判断，接 10.3 和实验 10-5；历史改型模型与当前预算分开。 |
| 95. [CoServe: Efficient Collaboration-of-Experts (CoE) Model Inference with Limited Memory](../../references/proceedings/ASPLOS/2025/public/paper-095.pdf) | 候选待读 | CoE 的专家是多个模型，依赖感知切换与分层驻留可补 11 路由；不能直接等同 MoE FFN 专家，先核服务质量与模型边界。 |
| 115. [Past-Future Scheduler for LLM Serving under SLA Guarantees](../../references/proceedings/ASPLOS/2025/public/paper-115.pdf) | 候选待读 | 按输出历史分布预测未来 batch 内存峰值，补 8 的准入与 11 的 goodput 判断；需核论文和 LightLLM 固定实现及分布漂移条件。 |
| 119. [ClosureX: Compiler Support for Correct Persistent Fuzzing](../../references/proceedings/ASPLOS/2025/public/paper-119.pdf) | 备查 | 持久 fuzzing 重用进程但恢复测试相关状态，可对照 11 的环境复用；它不直接证明多租户 Agent 的隔离或完整快照语义。 |
| 124. [Protecting Cryptographic Code Against Spectre-RSB: (and, in Fact, All Known Spectre Variants)](../../references/proceedings/ASPLOS/2025/public/paper-124.pdf) | 排除 | Jasmin／Coq 的投机常数时间保护聚焦密码实现；不扩成本书 CPU 微架构攻击专题。 |
| 126. [SMaCk: Efficient Instruction Cache Attacks via Self-Modifying Code Conflicts](../../references/proceedings/ASPLOS/2025/public/paper-126.pdf) | 排除 | 自修改代码的指令缓存侧信道与检测，和本书 GPU 推理优化主线距离较远。 |
| 131. [Micro Blossom: Accelerated Minimum-Weight Perfect Matching Decoding for Quantum Error Correction](../../references/proceedings/ASPLOS/2025/public/paper-131.pdf) | 排除 | 量子纠错 MWPM 的异构加速，decode 是纠错译码，不能归入 LLM decode 案例。 |
| 136. [FastGL: A GPU-Efficient Framework for Accelerating Sampling-Based GNN Training at Large Scale](../../references/proceedings/ASPLOS/2025/public/paper-136.pdf) | 备查 | GNN 采样、IO 与计算协同有方法价值，但不新增模型家族；现有 Transformer 案例优先。 |
| 155. [PIM Is All You Need: A CXL-Enabled GPU-Free System for Large Language Model Inference](../../references/proceedings/ASPLOS/2025/public/paper-155.pdf) | 候选待读 | CENT 把模型放到 CXL 近存设备并实现并行通信，可能补 4／6／13 的容量带宽选择；需核实际模型、批量、功耗和 TCO 假设。 |
| 164. [TensorTEE: Unifying Heterogeneous TEE Granularity for Efficient Secure Collaborative Tensor Computing](../../references/proceedings/ASPLOS/2025/public/paper-164.pdf) | 候选待读 | TensorTEE 的 CPU／NPU 数据粒度与重加密成本可补 6／11 的协同边界；需核模拟与安全假设，不当作现有 GPU 默认功能。 |
| 169. [Litmus: Fair Pricing for Serverless Computing](../../references/proceedings/ASPLOS/2025/public/paper-169.pdf) | 候选待读 | Serverless 拥塞造成时长和费用变化，可补 11 成本；先核测试如何区分负载与干扰，不冒充服务商现行计费规则。 |
| 180. [A Software Caching Runtime for Embedded NVRAM Systems](../../references/proceedings/ASPLOS/2025/public/paper-180.pdf) | 排除 | 嵌入式 NVRAM 指令缓存的编译与运行时，和模型权重／KV 分层不是同一流量，不扩展 MCU 专题。 |
| 181. [Velosiraptor: Code Synthesis for Memory Translation](../../references/proceedings/ASPLOS/2025/public/paper-181.pdf) | 备查 | 从内存映射规格生成低层 OS 代码，可能作 11 隔离机制背景；不当作大模型优化 kernel，作者预印本上传晚于出版年。 |

## 重点阅读与采用范围

**Accelerating Retrieval-Augmented Generation／IKS**：作者 arXiv v1，物理页 1–13 已读，包含设计、评估、讨论及 artifact 简介；图 2、图 5 已查看。14–18 页为未读参考文献。页级记录见 [iks-reading.json](../../references/proceedings/ASPLOS/2025/iks-reading.json)。

采用的是检索和生成共同决定质量与时间的分析，以及将向量扫描放到数据附近的设计选择。第 13.1／13.4 与既有实验 13-1、图 13-1 使用[Qwen3 与向量库教学计算](../../case-studies/retrieval-and-generation.md)。论文 NQ、T5／Llama 和历史 H100 条件不移植到 Qwen3；近存硬件是 RTL 参数与周期近似模拟评估。原稿的加速范围、ANNS 标注和算力口径存在不一致，未采用这些数字。

Faiss 官方索引表与选择指南补充真实实验入口；普通 Flat 的 FP32 容量与教学 FP16 存储分别核算。尚未运行 Faiss、模型、作者代码或模拟器。

**FSMoE**：作者 arXiv 2501.10714v1（2025-01-18），物理页 1–13 已读；14–15 页参考文献未读，图 3／4 已查看。采用前反向分别选择切块、梯度分桶与跨机 All-to-All 共同调度的判断，用[同一 Qwen3 专家的 72 MiB 梯度](../../case-studies/expert-dispatch-and-resizing.md)接到 10.3／实验 10-5；不是当前推理引擎特性。页级证明见 [fsmoe-reading.json](../../references/proceedings/ASPLOS/2025/fsmoe-reading.json)。

实验为 RTX A6000／RTX 2080 Ti 集群，PyTorch 1.12、CUDA 11.3、NCCL 2.12；GPT-2／Mixtral 的专家数、部分层数按机器修改，不能称完整原始模型。正文说 Testbed-A 六节点、每节点四卡，却称 48 卡，表 3 与后文并行组为每节点八卡；保留冲突，不修成作者已确认的配置。第 7 页八张 200 Gb/s 与聚合 800 Gb/s、NVLink 口径混用；第 9 页把反向的 α、β、n 都翻倍，与 α+nβ 的解释不一致；图 5 的子图／参数标签也需复核。正文关于单个 Mixtral／Qwen 专家必须跨卡的论断不能替代实际矩阵和状态容量计算。本书只采用资源与依赖分析，不采用这些硬件数字、解析公式或加速比。未下载运行作者代码。

**昇腾 component-based Roofline**：作者托管 PDF，物理页 2–14 的正文、评估和讨论已读，首页完整摘要另计；15–16 页参考文献未读。图 1、公式、图 6–12 和表 1／2 所在五页已查看，见[页级记录](../../references/proceedings/ASPLOS/2025/ascend-components-reading.json)。采用同一单元服务时间合并、活动时间与忙时效率的分解，接 5.2.3／5.3.5、实验 5-6 和图 5-5 的既有内容。[Qwen3 激活推算](../../case-studies/component-utilization-and-overlap.md)独立核算流量、缓冲与流水，不采用论文测量作为 Qwen3 成绩。

实验以 MindSpore 的 MobileNetV3、100B PanGu-α／128 NPU、7B Llama2／8 NPU 等为对象；正文仅用训练／推理芯片区分，不能替代完整芯片型号、软件版本与输入形状锁定。第 8 页阈值不等式的分子分母与 U=E×R 不一致；第 9／11 页的搬运方向与所归因的 MTE 名称有疑点；第 13 页 59.59 s／83.57% 与后述 72.31 s 分母不同。原稿保留，案例用独立算式；不由排版或文字问题推断作者执行代码一定错误。论文对 GPU 缓存、手工管理和相邻层搬运的概括也不适用于全部现代 GPU。

论文的“41 个算子进入 Ascend 库”保留为作者声明。[固定 vLLM Ascend](../../references/framework-history/2026-09-09/ascend-components/README.md)的六份响应、八个范围覆盖激活入口、310P 条件、profiler 迁移及三段发行说明；尚未验证这些入口与论文优化的一一对应。发行说明中的模型限定、Triton 硬件范围与撤回旧融合提醒实验必须固定组合，不将当前源码存在写成全模型支持。

**Diffuse**：物理页 2–13 共十二页已读，包含设计、评估、相关工作和参考文献起始；14–16 页参考文献未读。图 4、8、9、12／13 所在四页已查看，见[阅读记录](../../references/proceedings/ASPLOS/2025/diffuse-reading.json)。采用的是先检查分片和依赖，再检查内部循环与临时数据生命周期的顺序。它针对已经并行化的 cuPyNumeric／Legate 任务，并不自动为任意程序选择 TP／PP；库开发者需提供 MLIR 生成接口。任务融合单独未在所测负载上加速，临时数据消除和缓存分析缺少独立消融，不能据任务数下降分配各项收益。

论文使用 A100 DGX 节点、科学计算负载与最多 128 GPU 的弱扩展；稳态吞吐排除预热，部分应用需要 25–119 轮摊销编译。CFD 在多卡下因分片别名依赖失去部分融合机会，适合连接第五章与第六章。图 8(d) 算得最终 `%4` 却写回 `%2`，保留原图而不复制为可执行样例；不由排版问题推断作者运行代码错误。以[现有 Qwen3 归约案例](../../case-studies/collective-paths-and-diagnosis.md)的两维归一化反例说明为什么不能越过全局归约；带通信的专用融合仍可合法，不能把该保守分析的拒绝条件扩大成一般不可能性。没有验证 Diffuse 工件与 vLLM／SGLang 的直接实现继承。

**CXLfork**：物理页 2–14 共十三页已读，包含设计、评估、讨论和参考文献起始；15–17 页未读。图 4／5、方法页与图 8／9 所在四页已查看，见[阅读记录](../../references/proceedings/ASPLOS/2025/cxlfork-reading.json)。检查点制作会把数据复制到 CXL，恢复时只读映射与写时复制改变的是后续成本；全局 OS 状态仍需重建。所谓 ghost container 在正文中仍占约 512 KB；只报本地内存减少会漏掉共享池容量。

作者原型为 Linux 6.6、一台双路主机上的两个 VM 和 FPGA CXL 装置，Mitosis-CXL 比较在单 VM 内替代 RDMA。独立函数恢复不含容器和检查点制作；服务突发结果又包含 ghost container 条件差异。正文明确未验证大规模节点和共享带宽，延迟敏感性由校准模拟获得。这些条件不等于生产 E2B microVM 的部署或 GPU 状态恢复。[固定 E2B 缺页调用链](../../references/framework-history/2026-09-09/snapshot-residency/README.md)提供六份响应、十个选读范围：模板读取后安装虚拟机内存，与直接映射共享只读页分开。[同一模板推算](../../case-studies/snapshot-residency-and-first-use.md)独立算并发驻留、共享读取、首次访问粒度，接入 11.2、实验 11-2 与原图 11-3，不采用论文加速比作为当前结果。

**DarwinGame**：物理页 1–13 通读，参考文献页 14–16 未读，七张图页已查看，见[正文记录](../../references/proceedings/ASPLOS/2025/darwingame-reading.json)。论文在 CPU 云端运行不同配置的应用副本，用相对比赛应对噪声；外界噪声接近不代表候选造成的争用相同。采用这一限制来连接独占内核、并发片段和实际请求，而不将整个赛制写进大纲。

[作者工件与真实框架](../../references/framework-history/2026-09-09/tuning-measurement/README.md)补出了具体差距：随机等待的应用入口、没有进度提前停止的所读比赛、时间减一致性的分数、顺序执行的决赛，都不能冒充论文对应机制的复现。配置还需单独验证质量与应用语义；论文的 CPU 测试不证明当前 GPU 引擎收益。对应的 vLLM 2024／2025／2026 RMSNorm 仍测主机循环，激活 benchmark 与 FlashInfer-Bench 又使用不同计时入口。用[现有案例](../../case-studies/optimization-evaluation-and-deployment.md)的测量顺序、条件混合与 Qwen3 拼接宽度推算补实验 5-6，不新增正文事实清单。

**PICACHU**：物理页 2–12 共十一页已读，表 1、共享缓冲图、质量／面积表及图 7–9 所在五页已查看，见[页级记录](../../references/proceedings/ASPLOS/2025/picachu-reading.json)。采用资源配比、归约依赖和缓冲条件的判断；DFG 节点比不是 FLOPs/byte。4×8 的非线性扩展收益及 40 KB 的阈值都带有具体映射和模型条件，不能只增加单元或缓存容量便推定线性收益。

其 45 nm RTL 综合、Timeloop 建模、FP16 线性层保留与 U280 DMA 测量分别说明。对 A100 的端到端比较同时改变矩阵和非矩阵路径，不作为已流片产品或当前引擎实测。表 1 的 tanh 分式写反，图 7c 的有限缓冲与 unlimited 仍有差距；原件保留，正文不复制公式或据此断言普适最优容量。与[固定 vLLM RoPE 基类](../../references/framework-history/2026-09-09/nonlinear-resources/README.md)对照后，现有 Qwen3 案例区分系数准备、稳态旋转、主张量接口流量和真实 HBM 读取，接实验 4-1／图 4-2 与 13.4.2，不新增架构专题。

**Apophenia**：声明物理页 2–12 与完整工件附录 16–17，共十三页，六页图像已查看，见[页级记录](../../references/proceedings/ASPLOS/2025/apophenia-reading.json)。重复片段需要保持影响依赖的身份；异步寻找候选、收齐匹配、记录与稳态重放各自计量。FlexFlow 强扩展仅采用当时的 CANDLE／DP 配置，短 trace 在部分规模更好；任务发起的 7／12 μs、另一阶段的 100 μs 与 30–300 次预热不能改写成通用 GPU 开销。

[公开工件与 vLLM 对照](../../references/framework-history/2026-09-09/trace-identification/README.md)保存三份原始响应、精确 ZIP 成员和九个读取范围。附录的未公开依赖、所读 hash 的省略字段、固定图封装对外部缓冲的要求分别保留。现有 Qwen3 案例只补地址绑定和收齐片段后的流水推算；不展开字符串算法、不移植论文总加速比，也不声称当前引擎采用该自动识别系统。

**PipeLLM**：新增十五页正式格式作者稿，物理页 1–13 与六页图像已读，原十四页 v1 及摘要保留，见[页级记录](../../references/proceedings/ASPLOS/2025/pipellm-reading.json)。采用的是多一次复制允许更早准备，以及错误准备仍耗资源的判断；同一 64 MiB 张量分别核算等待、服务量与三类缓冲。正文的零顺序预测成功率仍能复用已准备密文，不解释成零有用工作也没有代价。

其单 H100-SXM 评估并未启用 CPU TDX，旧 vLLM 测的是 OPT 模型的并行采样。公开工件需要修改 CUDA／OpenSSL 集成，所读失配分支进入断言；源码与论文的保护、回退设计尚未逐项对应，不能宣称完整复现。[三期 vLLM 对照](../../references/framework-history/2026-09-09/pipellm-swap/README.md)区分旧单／多序列抢占、V1 重计算与 connector 缓存，未发现直接集成该研究的证据。图注与 52.8% 指标歧义留在记录，正文不移植性能倍数；只补 5.2.3／实验 5-2／图 5-2 的选做变体，接回第 8→9 章已有缓存计算。

**StreamGrid**：作者 v1 物理页 2–12 的十一页正文范围已读，五页图像已查看，见[页级记录](../../references/proceedings/ASPLOS/2025/streamgrid-reading.json)。强制切分和搜索提前终止会改变算法工作量与任务质量，需要配合训练；不能当作保持原计算不变的 GPU 融合。固定吞吐下的缓冲模型还需要给定数据流、时序和复用信息，给快阶段留空隙有时可以节省缓冲。

硬件部分采用 RTL 综合／布局与周期、带宽模型；PointNet++、分割与 3DGS 所用机制不同，训练适应的成本也单独存在。图 20(b) 的图注与任务指标有差异，原稿保留。本书已有质量、资源与生命周期的分析，故由候选改为备查：不增加点云专题、不迁移总加速比，也没有验证当前推理框架直接采用该设计。

**ARC**：物理页 2–13 的十二页正文范围已读，四页图像已查看，见[页级记录](../../references/proceedings/ASPLOS/2025/arc-reading.json)。高 L2 命中不消除原子请求排队；先在 warp 内归约可以减少请求，也会增加指令、寄存器和控制流开销。收益受地址局部性、活跃 lane 数与调优阈值影响，不能只用 HBM 字节数判断。

ARC-HW 的新增指令与单元依靠模拟评估，ARC-SW 是 GPU 上的软件实现；梯度内核、完整训练与模拟硬件参数分别看待。适用条件涉及归约顺序、原子操作语义和返回值；论文比较中的历史库限制不代表当前 CCCL。所引软件工件本批未读，不能声称已核实框架接入。现有第五章的分单元分析已经覆盖这一判断，暂留备查，不新增章节或实验。

## 尚缺的材料

- 首个 session 中 Mosaic、DynaX、RASSM 的原始摘要／正文仍有缺口；DynaX 的作者 README 不能代替论文。TFHE 作者页面的 PDF 按钮仍指向 ACM。
- 184 条 OpenAlex 查询结果只用于定位公开稿，不能替代原始摘要；其中可用位置也不完整，已知 GUST／IKS 等须另行查找。公开副本归属再由标题、作者和正式 DOI 核对。
- 初次下载的一份机构副本返回 403，ACM 条目返回 403，探测的官方 abstracts 路径为 404。保留响应，继续寻找作者稿；其余工作正常推进。
- 本轮 NCSU 作者链接以 HTTP 200 重定向到 Purdue 实验室首页，Yale PULSE 链接为 404；均保存响应，不计论文。第 17／24 项仍缺公开稿，其余未筛条目按 manifest 保留。
- 其余 126 篇继续查摘要和全文。已读候选先与本书现有图执行、资源共享、调度和分层存储案例比较，只有新的约束或选择边界才进入提纲。

机器记录：[摘要与来源](../../references/proceedings/ASPLOS/2025/public-abstracts.json)、[筛选表](screening-asplos-2025.tsv)、[逐篇 manifest](../../references/proceedings/ASPLOS/2025/manifest.json)。

Earth+ 的 2024 作者 v1 有六位作者，含 Ranveer Chandra；已归档正式 DOI 的 Crossref 记录列五位，未列该名字。题名与其余五位作者一致，按较早作者版本归档；此处仅记录元数据差异，不推断正式 PDF 的作者名单已经变更。

前一批十三篇新摘要的逐项判断和版本备注见[筛选记录](../../references/proceedings/ASPLOS/2025/middle-screening-notes.json)。首轮将 StreamGrid、ARC、Apophenia、PipeLLM 留为正文候选，四篇随后均完成声明范围的正文阅读；StreamGrid／ARC 留作备查；该批其他论文备查或排除，不根据摘要加速比向主大纲追加内容。Mint 作者稿仍有占位 DOI；Java 方法论文的 72 页包含附录；第 55 项按正式 2024 卷与 2025 演讲分别记录。MPI 路径返回非 PDF 页面、EXIST 作者链接返回 404、eScholarship 返回空 202，原响应保留；ARC 与 RTL 去重论文随后取得另一作者路径的有效 PDF。旧第 55 项失败响应仍保留原件，不覆盖它。

本批[存储与系统摘要记录](../../references/proceedings/ASPLOS/2025/storage-screening-notes.json)新增十篇完整摘要、八份代表 PDF／130 页，以及六份其他原始响应。OWL 属于正式 2024 卷；CRUSH 采用实验室链接的十五页 ASPLOS 版，保留先前错误路径的 404，不混用同名 IWLS 版。IBM／SNU 两条采用机构完整摘要元素，明确没有 PDF 正文阅读。AMuLeT／HyperHammer 的跨栏摘要经首页图像复核，作者脚注与版权文字不进入提取范围。Necro-reaper、Tela、Marionette 仍未取得本地可核的完整摘要，保留作者页、403 和传输失败，不用搜索片段补足阅读计数。
