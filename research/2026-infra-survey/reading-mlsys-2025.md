# MLSys 2025：逐篇摘要筛选与重点阅读

2026-09-07 已阅读官方目录全部 61 篇的标题和完整摘要；截至 2026-09-08，五篇补读下列设计与实验章节。候选条目尚不能作为全文结论；速度与质量条件需继续核对。取舍的机器可读输入见[筛选记录](screening-mlsys-2025.tsv)。

| 论文 | 本轮取舍 | 原因与位置 |
| --- | --- | --- |
| [Graph Learning at Scale: Characterizing and Optimizing Pre-Propagation GNNs](../../references/proceedings/MLSys/2025/papers/mlsys2025-0badcb4e95306df76a719409155e46e8.pdf) | 排除正文 | PP-GNN 的预传播与输入管线，主要是图学习专用问题，不扩展本书模型家族。 |
| [SwiftVI: Time-Efficient Planning and Learning with MDPs](../../references/proceedings/MLSys/2025/papers/mlsys2025-0f8426558905746fc38da5e335700aec.pdf) | 排除正文 | MDP 的值迭代更新策略；不是 LLM rollout 与参数更新的基础设施问题。 |
| [Balancing Pipeline Parallelism with Vocabulary Parallelism](../../references/proceedings/MLSys/2025/papers/mlsys2025-10e400a587ff6925e4e26333b419ff55.pdf) | 候选待读 | 词表与输出头造成流水阶段不均衡，可补 11.3；不能按相同层数直接认为各阶段等时。 |
| [Youmu: Efficient Columnar Data Pipeline for LLM Training](../../references/proceedings/MLSys/2025/papers/mlsys2025-136b9a13861308c8948cd308ccd02658.pdf) | 候选待读 | 列式训练数据的 shuffle、I/O 放大与副本成本，适合 11.4；须连同打乱质量阅读。 |
| [LeanAttention: Hardware-Aware Scalable Attention Mechanism for the Decode-Phase of Transformers](../../references/proceedings/MLSys/2025/papers/mlsys2025-16ec6494e9b5a4138de7238761d715b4.pdf) | 候选待读 | decode attention 的硬件切分与长 KV 负载，比较 FlashInfer 后再补 5、9，避免重复介绍内核。 |
| [Photon: Federated LLM Pre-Training](../../references/proceedings/MLSys/2025/papers/mlsys2025-185087ea328b4f03ea8fd0c8aa96f747.pdf) | 候选待读 | 低带宽联邦预训练可检验第 7、11 章网络可行性边界；不能把至 7B 的结论外推到 1T 同步训练。 |
| [MEADOW: Memory-efficient Dataflow and Data Packing for Low Power Edge LLMs](../../references/proceedings/MLSys/2025/papers/mlsys2025-259a5df46308d60f8454bd4adcc3b462.pdf) | 备选，不新增 | 低功耗 FPGA 数据流可作第 4 章端侧对照，当前不增加 FPGA 专题。 |
| [Rethinking Key-Value Cache Compression Techniques for Large Language Model Serving](../../references/proceedings/MLSys/2025/papers/mlsys2025-26289c647c6828e862e271ca3c490486.pdf) | 重点阅读并整合 | 容量与 token 吞吐之外，还要测生成长度和逐任务质量；补 9.4.4、实验 9-8。 |
| [Rubick: Exploiting Job Reconfigurability for Deep Learning Cluster Scheduling](../../references/proceedings/MLSys/2025/papers/mlsys2025-270339c997293ca2988c62f4308e389f.pdf) | 重点阅读并整合 | 资源分配和执行方案联合改变，接回 6、11 的推算，补 12.2.1、实验 12-2 的切换成本。 |
| [SampleAttention: Near-Lossless Acceleration of Long Context LLM Inference with Adaptive Structured Sparse Attention](../../references/proceedings/MLSys/2025/papers/mlsys2025-2d04d97593c8c33d415337f408ed0e1b.pdf) | 备选，不新增 | 近似稀疏 attention 的质量和块选择代价；已有 V4/K3 主线，不再新增一种稀疏方法小节。 |
| [SPA: SCALING GRAPH NEURAL NETWORK TRAINING ON LARGE GRAPHS VIA PROBABILISTIC SPLITTING](../../references/proceedings/MLSys/2025/papers/mlsys2025-3619b2fc65a5538a24b48efc089da709.pdf) | 排除正文 | 大图 GNN 训练的概率切分，偏图数据专用并行。 |
| [SparseTransX: Efficient Training of Translation-Based Knowledge Graph Embeddings Using Sparse Matrix Operations](../../references/proceedings/MLSys/2025/papers/mlsys2025-36e2967f87c3362e37cf988781a887ad.pdf) | 排除正文 | 知识图谱嵌入的稀疏矩阵化，与当前 LLM 贯穿案例距离较远。 |
| [ReaL: Efficient RLHF Training of Large Language Models with Parameter Reallocation](../../references/proceedings/MLSys/2025/papers/mlsys2025-3b3889d313ba9476c12c2d77ea66b24f.pdf) | 候选待读 | RLHF 动态资源与参数重分配，比较当前 verl、R1/V4 路径；保留为历史系统，不替代新 RL 案例。 |
| [Interference-aware Edge Runtime Prediction with Conformal Matrix Completion](../../references/proceedings/MLSys/2025/papers/mlsys2025-40b8fb4f90004405e14b1ede6ab42373.pdf) | 备选，不新增 | 干扰下的预测误差可补第 13 章方法；Wasm 边缘设备结果不能当作 GPU 吞吐预测精度。 |
| [DiffServe: Efficiently Serving Text-to-Image Diffusion Models with Query-Aware Model Scaling](../../references/proceedings/MLSys/2025/papers/mlsys2025-414fd191b3246a19a55741b938380136.pdf) | 备选，不新增 | 按请求选扩散模型与动态资源，作为 12.3 路由对照；不扩大图像生成背景。 |
| [ProtoRAIL: A Risk-cognizant Imitation Agent for Adaptive vCPU Oversubscription In the Cloud](../../references/proceedings/MLSys/2025/papers/mlsys2025-42e2b24104bc92d724ce45c0c2f91e1d.pdf) | 备选，不新增 | 生产 vCPU 超售与风险预测，和 Agent 环境有联系，但不是 GPU 调度或 MFU 的证据。 |
| [APOLLO: SGD-like Memory, AdamW-level Performance](../../references/proceedings/MLSys/2025/papers/mlsys2025-437bc4ccafd3fc6d4289bd10940be42b.pdf) | 候选待读 | 改变优化器算法来降低状态占用，需与 ZeRO 的等价状态切分分开；只作为 11.1 的取舍。 |
| [AI Metropolis: Scaling Large Language Model-based Multi-Agent Simulation with Out-of-order Execution](../../references/proceedings/MLSys/2025/papers/mlsys2025-4f31327e046913c7238d5b671f5d820e.pdf) | 候选待读 | 多 Agent 的真假依赖及乱序执行，可补 8、12；先区分独立 Agent 与同任务有因果依赖的轮次。 |
| [The Hidden Bloat in Machine Learning Systems](../../references/proceedings/MLSys/2025/papers/mlsys2025-5321b1dabcd2be188d796c21b733e8c7.pdf) | 候选待读 | 框架二进制依赖膨胀与冷启动，先与 2026 模型加载研究去重，再决定 5、12 落点。 |
| [PipeFill: Using GPUs During Bubbles in Pipeline-parallel LLM Training](../../references/proceedings/MLSys/2025/papers/mlsys2025-53d3f45797970d323bd8a0d379c525aa.pdf) | 候选待读 | 用另一作业填训练流水气泡，需算共用显存、干扰和中断；不是同一作业的零气泡调度。 |
| [HyC-LoRA: Memory Efficient LoRA Fine-tuning with Hybrid Activation Compression](../../references/proceedings/MLSys/2025/papers/mlsys2025-5431dca75a8d2abc1fb51e89e8324f10.pdf) | 备选，不新增 | LoRA 的激活状态仍可能很大，支持 11.1 的容量区分，不增加激活量化算法目录。 |
| [Radius: Range-based Gradient Sparsity for Large Foundation Model Pre-training](../../references/proceedings/MLSys/2025/papers/mlsys2025-54dd9e0cff6d9214e20d97eb2a3bae49.pdf) | 候选待读 | 结构化梯度稀疏与通信，实验规模是 355M/2B；核对收敛、编码和迭代成本再用于 7、11。 |
| [XGrammar: Flexible and Efficient Structured Generation Engine for Large Language Models](../../references/proceedings/MLSys/2025/papers/mlsys2025-5c20ca4b0b20b0bd2f1d839dc605e70f.pdf) | 重点阅读并整合 | 预处理与 CPU 掩码重叠补 9.1／实验 9-2，推测状态回滚接 9.3，格式与工具语义接 12.1；保留旧基线条件。 |
| [FlexAttention: A Programming Model for Generating Fused Attention Variants.](../../references/proceedings/MLSys/2025/papers/mlsys2025-61a9278dfef5f871b5e472389f8d6fa1.pdf) | 候选待读 | 可编程 attention 与融合变体的组合爆炸，切合 5.3 的编译器动机；和当前框架后端一起核对。 |
| [NEO: Saving GPU Memory Crisis with CPU Offloading for Online LLM Inference](../../references/proceedings/MLSys/2025/papers/mlsys2025-66a026c0d17040889b50f0dfa650e5e0.pdf) | 候选待读 | CPU 承接 attention 计算及 KV，和 KTransformers 的 CPU 专家路径不同；补 10.3 前先算 PCIe 与 CPU 带宽。 |
| [AdaParse: An Adaptive Parallel PDF Parsing and Resource Scaling Engine](../../references/proceedings/MLSys/2025/papers/mlsys2025-678773d96b5822e93348aeb5c80d4dc5.pdf) | 备选，不新增 | PDF 解析与资源扩缩可作 11.4 数据准备对照，不扩成解析框架教程。 |
| [FlexInfer: Flexible LLM Inference with CPU Computations](../../references/proceedings/MLSys/2025/papers/mlsys2025-698cfaf72a208aef2e78bcac55b74328.pdf) | 候选待读 | 按阶段安排 CPU/GPU 计算，比较 NEO 与现有 AF；FlexInfer 不是 FlashInfer。 |
| [Know Where You’re Uncertain When Planning with Multimodal Foundation Models: A Formal Framework](../../references/proceedings/MLSys/2025/papers/mlsys2025-703f727ec10190b2fddcf8e24f52df48.pdf) | 排除正文 | 多模态规划的不确定性与形式保证，重点是应用算法。 |
| [Supply-Chain Attacks in Machine Learning Frameworks](../../references/proceedings/MLSys/2025/papers/mlsys2025-75bb91b908e6924763c9f2bbe87e921e.pdf) | 排除正文 | 机器学习框架供应链攻击，不扩展本书当前性能与容量分析的范围。 |
| [Context Parallelism for Scalable Million-Token Inference](../../references/proceedings/MLSys/2025/papers/mlsys2025-78834433edc3291f4c6cbbd2759324db.pdf) | 候选待读 | 百万 token 推理的 pass-KV/pass-Q，可补 6、7 的跨超节点推理例外；长 prefill 的 TCP 结果不能推广到短 decode。 |
| [Marconi: Prefix Caching for the Era of Hybrid LLMs](../../references/proceedings/MLSys/2025/papers/mlsys2025-7c180af017258d239bac6248d1eb26ac.pdf) | 重点阅读并整合 | 混合模型检查点准入与每字节省下的 prefill 工作，补 9.2.5、实验 9-4；与 2026 Unified Radix Cache 分清年代和状态类型。 |
| [Venn: Resource Management For Collaborative Learning Jobs](../../references/proceedings/MLSys/2025/papers/mlsys2025-7fd522b89ac21009b7bbe7560a9a5add.pdf) | 排除正文 | 易失边缘设备上的联邦作业匹配，当前优先共享 GPU 集群与 Agent/RL 环境；摘要 Venn/Auxo 名称不一致待引用时核对。 |
| [On Distributed Larger-Than-Memory Subset Selection With Pairwise Submodular Functions](../../references/proceedings/MLSys/2025/papers/mlsys2025-8144a9d62e506af0fcdeac0e456b2710.pdf) | 备选，不新增 | 超内存数据子集选择可作训练数据成本旁证，主要贡献是子模优化算法。 |
| [Lightweight Software Kernels and Hardware Extensions for Efficient Sparse Deep Neural Networks on Microcontrollers](../../references/proceedings/MLSys/2025/papers/mlsys2025-8cb5b08f912600de3de07c6503599ba8.pdf) | 备选，不新增 | MCU 的 N:M 稀疏内核与 ISA 协同可作第 4 章对照，不增 MCU 专题。 |
| [MiLo: Efficient Quantized MoE Inference with Mixture of Low-Rank Compensators](../../references/proceedings/MLSys/2025/papers/mlsys2025-9032e5c9ec394ce768a2fa9bdc56af6c.pdf) | 候选待读 | 极低比特 MoE 的补偿参数与实际内核成本，可补 9.4 的极端量化说法核算。 |
| [FastTree: Optimizing Attention Kernel and Runtime for Tree-Structured LLM Inference](../../references/proceedings/MLSys/2025/papers/mlsys2025-96894468eb44631a32d7ebd56f9892c7.pdf) | 候选待读 | 共享前缀缓存之后，attention 仍可能重复读数据；SGLang 上的树分组内核适合 5、9 衔接，先与 FlashInfer 去重。 |
| [FedProphet: Memory-Efficient Federated Adversarial Training via Robust and Consistent Cascade Learning](../../references/proceedings/MLSys/2025/papers/mlsys2025-96f39c8de84678cb2a908cd52bfd7819.pdf) | 排除正文 | 联邦对抗训练的鲁棒性与一致性，超出本书 LLM 系统主线。 |
| [LAVA: Lifetime-Aware VM Allocation with Learned Distributions and Adaptation to Mispredictions](../../references/proceedings/MLSys/2025/papers/mlsys2025-9de62e421d58234dbf773abf43268630.pdf) | 候选待读 | 生产 VM 生存期分布、误判重估与资源整理，可深化 12.4 环境驻留；别把仿真收益当作生产增益。 |
| [Scaling Deep Learning Training with MPMD Pipeline Parallelism](../../references/proceedings/MLSys/2025/papers/mlsys2025-9f73d65a4186198152357be871345771.pdf) | 候选待读 | JaxPP 的 MPMD 执行与自定义流水调度，可作 11.3 对照，避免变成 JAX 教程。 |
| [ScaleFusion: Scalable Inference of Spatial-Temporal Diffusion Transformers for High-Resolution Long Video Generation](../../references/proceedings/MLSys/2025/papers/mlsys2025-a2fe4bb50fc6f3564cee1551d6309fea.pdf) | 备选，不新增 | 视频扩散的时空 attention 与跨机流水，主线保留简短多模态案例，不增加长视频专节。 |
| [Lumos: Efficient Performance Modeling and Estimation for Large-scale LLM Training](../../references/proceedings/MLSys/2025/papers/mlsys2025-a66caa1703fe34705a4368c3014c1966.pdf) | 候选待读 | Lumos 用真实轨迹校准训练性能，适合 13.5 解释何时简单估算不足；不能以仿真替代最初的瓶颈判断。 |
| [Self-Data Distillation for Recovering Quality in Pruned Large Language Models](../../references/proceedings/MLSys/2025/papers/mlsys2025-af2d9fb5bcee19ef2dfa70d843520c97.pdf) | 备选，不新增 | 剪枝后蒸馏恢复质量与草稿接受率，算法贡献为主；先与现有新推测解码案例去重。 |
| [Efficient LLM Inference using Dynamic Input Pruning and Cache-Aware Masking](../../references/proceedings/MLSys/2025/papers/mlsys2025-afd6374c7f2839cba22f537f15f4f760.pdf) | 候选待读 | 端侧动态稀疏、缓存命中与权重读取，补 9.4 的 Flash/DRAM 分层边界；摘要部分是模拟结果。 |
| [Efficient On-Device Machine Learning with a Biologically-Plausible Forward-Only Algorithm](../../references/proceedings/MLSys/2025/papers/mlsys2025-b0131b6ee02a00b03fc3320176fec8f5.pdf) | 排除正文 | 生物启发的前向学习算法，不是本书训练系统的核心执行路径。 |
| [Optimizing LLM Queries in Relational Data Analytics Workloads](../../references/proceedings/MLSys/2025/papers/mlsys2025-b5dc49f44db2fadc5c4d717c57f4a424.pdf) | 候选待读 | 按行列重排批量分析请求以提高前缀复用，补 9.2 的请求组织；须检查重排是否保持任务语义。 |
| [SOLA: Optimizing SLO Attainment for Large Language Model Serving with State-Aware Scheduling](../../references/proceedings/MLSys/2025/papers/mlsys2025-bc82dbfbfa43232be85b8d9838f49c3e.pdf) | 候选待读 | 按请求与系统状态同时调度 TTFT/TPOT，和现有 chunked prefill、SLO 主线合并比较。 |
| [ThunderServe: High-performance and Cost-efficient LLM Serving in Cloud Environments](../../references/proceedings/MLSys/2025/papers/mlsys2025-c2a0e26dd9ee7d57e92bb1c24b39659a.pdf) | 候选待读 | 异构 GPU 与网络条件下部署、在线重排，适合 10.2/10.6 的 A100/H20 分工；不照搬跨云价格倍数。 |
| [TileLink: Generating Efficient Compute-Communication Overlapping Kernels using Tile-Centric Primitives](../../references/proceedings/MLSys/2025/papers/mlsys2025-c6ee784cbe46d854843e4c883a3321ef.pdf) | 候选待读 | tile 级计算通信编译与重叠，联系 5→6→7；与 COMET、MPK 去重，不相乘各论文加速比。 |
| [Seesaw: High-throughput LLM Inference via Model Re-sharding](../../references/proceedings/MLSys/2025/papers/mlsys2025-cbc4ab80cd77aa0eb87da062fbcddb46.pdf) | 候选待读 | prefill/decode 阶段重切模型和分层 KV，区别于独立 PD 实例；适用于吞吐导向任务，需扣除切换成本。 |
| [LServe: Efficient Long-sequence LLM Serving with Unified Sparse Attention](../../references/proceedings/MLSys/2025/papers/mlsys2025-cc8c6b9d89f7a898a29f58869b238e46.pdf) | 备选，不新增 | 硬件友好稀疏 attention 的统一执行，已有 V4/K3 比较主线；固定 KV 页数的精度只在原实验范围成立。 |
| [AIOpsLab: A Holistic Framework to Evaluate AI Agents for Enabling Autonomous Clouds](../../references/proceedings/MLSys/2025/papers/mlsys2025-d1f9e4a9f109b6e8b75ed362736f22ec.pdf) | 备选，不新增 | 运维 Agent 的真实环境、故障和可验证结果，可作第 12 章实验依据，不扩成云运维教材。 |
| [MAS-ATTENTION: MEMORY-AWARE STREAM PROCESSING FOR ATTENTION ACCELERATION ON RESOURCE-CONSTRAINED EDGE DEVICES](../../references/proceedings/MLSys/2025/papers/mlsys2025-d3cf1559a8795eb1ed2b3ad52409ac7d.pdf) | 备选，不新增 | 端侧矩阵/向量单元并行与缓存调度，支持 4、5 设计取舍；仿真和实际 NPU 结果分别记录。 |
| [Training Ultra Long Context Language Model with Fully Pipelined Distributed Transformer](../../references/proceedings/MLSys/2025/papers/mlsys2025-d5a655b8b373737b4f2aea8f78e5e754.pdf) | 候选待读 | 超长上下文训练的 chunk 流水与卸载，适合 11.1/11.3；2M token 和 MFU 必须核对完整硬件、模型与计算口径。 |
| [FlashInfer: Efficient and Customizable Attention Engine for LLM Inference Serving](../../references/proceedings/MLSys/2025/papers/mlsys2025-dbf02b21d77409a2db30e56866a8ab3a.pdf) | 重点阅读并整合 | plan/run 分离使动态请求兼容图重放，补 5.4.4、实验 5-8；版本是论文的 FlashInfer v0.2 与 SGLang v0.3.4。 |
| [A Bring-Your-Own-Model Approach for ML-Driven Storage Placement in Warehouse-Scale Computers](../../references/proceedings/MLSys/2025/papers/mlsys2025-e01c431bbb83153632c0dcfaf8ccda0a.pdf) | 备选，不新增 | 应用提供小模型指导存储放置，和本书量化方法相合，但先保持 AI 工作负载的直接案例。 |
| [COMET: Fine-grained Computation-communication Overlapping for Mixture-of-Experts](../../references/proceedings/MLSys/2025/papers/mlsys2025-e27ea0cd50b798ff8942caf9203f0992.pdf) | 候选待读 | MoE 细粒度通信计算重叠和工作分配，比较 Lancet、DeepEP、TBO/DBO 后决定 10.4/11.3 的统一案例。 |
| [Enabling Unstructured Sparse Acceleration on Structured Sparse Accelerators](../../references/proceedings/MLSys/2025/papers/mlsys2025-e2ec2530db26b54d0b3b060c1e4a1bda.pdf) | 备选，不新增 | 将非结构稀疏近似为结构稀疏，支持第 4 章硬件利用条件；属于近似变换，需质量约束。 |
| [VoLUT: Efficient Volumetric streaming enhanced by LUT-based super-resolution](../../references/proceedings/MLSys/2025/papers/mlsys2025-f189e7580acad0fc7fd45405817ddee3.pdf) | 排除正文 | 体积视频流与超分辨率，用户已要求第 8 章收敛为少量 AI 交互例子。 |
| [FLStore: Efficient Federated Learning Storage for non-training workloads](../../references/proceedings/MLSys/2025/papers/mlsys2025-f37347375d8b54e3203e5d24aeb6c58c.pdf) | 备选，不新增 | 联邦非训练工作负载的 serverless 缓存，和 12 的环境主题有联系，当前优先代码 Agent/RL。 |
| [TurboAttention: Efficient attention approximation for high throughputs llm](../../references/proceedings/MLSys/2025/papers/mlsys2025-f4f55846501f3336f293fd8b6de10770.pdf) | 备选，不新增 | KV 量化与 attention 近似同时改动，已有 9.4 的质量/吞吐分析；不再添加量化算法小节。 |
| [QServe:W4A8KV4 Quantization and System Co-design for Efficient LLM Serving](../../references/proceedings/MLSys/2025/papers/mlsys2025-fbe2b2f74a2ece8070d8fb073717bda6.pdf) | 候选待读 | QServe 的 W4A8KV4 说明解量化会吃掉理论收益，适合 5、9；和 2024 Atom 及当前内核做同题比较。 |

## 重点阅读与采用范围

- **Rethinking Key-Value Cache Compression Techniques for Large Language Model Serving**：PDF 第 6、7、8、9、16、17 页；§4.1–4.4 开头、附录 A.7–A.8/B；吞吐基线、自然生成长度与单样本质量。
- **Rubick: Exploiting Job Reconfigurability for Deep Learning Cluster Scheduling**：PDF 第 5、6、7、8、9、10 页；§4–7.4 开头；性能拟合、资源选择、重启方式和实际/仿真条件。
- **Marconi: Prefix Caching for the Era of Hybrid LLMs**：PDF 第 4、5、6、7、8 页；§3 后半至 §5.2；状态复用、准入/淘汰与实验设置。
- **FlashInfer: Efficient and Customizable Attention Engine for LLM Inference Serving**：PDF 第 7、8 页；§3.3–4.2 开头；plan/run、图兼容和实验版本。

- **XGrammar: Flexible and Efficient Structured Generation Engine for Large Language Models**：PDF 物理页 1–11；动机、预处理／运行时划分、持久化栈、CPU／GPU 重叠和实验条件，另查看页 8 图 8。页 12–18 不在本次读取范围，历史语法正确率不代表工具任务成功。

推算、历史基线、原文疑点与采用边界见[缓存、图执行与资源重配笔记](../../case-studies/cache-and-reconfiguration.md)。只补 5.4.4、9.2.5、9.4.4、12.2.1 及相应实验变体，没有新增小节或实验编号。

XGrammar 与三个框架的版本、Qwen3 掩码计算及采用范围见[工具参数生成笔记](../../case-studies/structured-generation.md)。仅深化 9.1.3、9.3.1、12.1.1 及实验 9-2、图 9-1，未增加编号。

MLSys 2026 的摘要筛选已完成。后续从词表并行、数据输入、量化执行等候选中，选择能补充现有案例判断的论文比较正文；不因出现在优先队列就加入提纲。
