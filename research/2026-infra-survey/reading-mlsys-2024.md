# MLSys 2024：逐篇摘要筛选与重点阅读

2026-09-07 已阅读官方目录全部 37 篇的标题与完整摘要。下面的“候选待读”仅是摘要判断，不能作为论文设计或性能结论的全文证据。正式正文不逐篇介绍论文。

| 论文 | 本轮取舍 | 原因与位置 |
| --- | --- | --- |
| [Punica: Multi-Tenant LoRA Serving](../../references/proceedings/MLSys/2024/papers/mlsys2024-054de805fcceb78a201f5e9d53c85908.pdf) | 重点阅读并整合 | 多 adapter 共享基座与异构批处理，补第 9 章缺失的多 LoRA 服务问题。 |
| [ACROBAT: Optimizing Auto-batching of Dynamic Deep Learning at Compile Time](../../references/proceedings/MLSys/2024/papers/mlsys2024-096b1019463f34eb241e87cfce8dfe16.pdf) | 备选，不新增 | 动态控制流自动批处理可补 5.4；已有图与形状主线，先不另立系统。 |
| [HeteroSwitch: Characterizing and Taming System-Induced Data Heterogeneity in Federated Learning](../../references/proceedings/MLSys/2024/papers/mlsys2024-0badcb4e95306df76a719409155e46e8.pdf) | 排除正文 | 重点是联邦数据异质性与泛化，不扩展本书的训练分片主线。 |
| [JIT-Q: Just-in-time Quantization with Processing-In-Memory for Efficient ML Training](../../references/proceedings/MLSys/2024/papers/mlsys2024-136b9a13861308c8948cd308ccd02658.pdf) | 候选待读 | 即时量化与高低精度权重副本可补 4、11；PIM 仿真与真实 GPU 收益须另读。 |
| [Schrodinger's FP Training Neural Networks with Dynamic Floating-Point Containers](../../references/proceedings/MLSys/2024/papers/mlsys2024-185087ea328b4f03ea8fd0c8aa96f747.pdf) | 备选，不新增 | 训练位宽动态选择，已由低精度与质量条件覆盖，避免量化算法目录。 |
| [Lancet: Accelerating Mixture-of-Experts Training via Whole Graph Computation-Communication Overlapping](../../references/proceedings/MLSys/2024/papers/mlsys2024-339caf45a6fa281cae8adc6465343464.pdf) | 候选待读 | 训练图级 all-to-all 重叠，比较 2025 COMET 与 2026 Megatron 再决定 11.3 落点。 |
| [AWQ: Activation-aware Weight Quantization for On-Device LLM Compression and Acceleration](../../references/proceedings/MLSys/2024/papers/mlsys2024-42a452cbafa9dd64e9ba4aa95cc1ef21.pdf) | 保留历史依据 | 权重量化与激活统计的历史基础；已有本地量化主线，不新增 AWQ 小节。 |
| [DiffusionPipe: Training Large Diffusion Models with Efficient Pipelines](../../references/proceedings/MLSys/2024/papers/mlsys2024-45c1f6a8cbf2da59ebf2c802b4f742cd.pdf) | 备选，不新增 | 扩散训练的冻结编码器填气泡可作 11.3 对照，先与 LLM 微批案例去重。 |
| [Keyformer: KV Cache reduction through key tokens selection for Efficient Generative Inference](../../references/proceedings/MLSys/2024/papers/mlsys2024-48fecef47b19fe501d27d338b6d52582.pdf) | 保留历史依据 | 历史 KV 选择案例；当前主比较仍是 V4/K3，旧模型速度不移植。 |
| [Accelerating ReLU for MPC-Based Private Inference with a Communication-Efficient Sign Estimation](../../references/proceedings/MLSys/2024/papers/mlsys2024-4e3157021c5f833bb2204081f1dda573.pdf) | 排除正文 | MPC 非线性协议开销，超出本书的模型服务与执行重点。 |
| [FlashDecoding++: Faster Large Language Model Inference with Asynchronization, Flat GEMM Optimization, and Heuristics](../../references/proceedings/MLSys/2024/papers/mlsys2024-5321b1dabcd2be188d796c21b733e8c7.pdf) | 候选待读 | 小 M GEMM 与同步开销可帮助 5、9 的形状推算；不直接使用摘要速度倍数。 |
| [HeteGen: Efficient Heterogeneous Parallel Inference for Large Language Models on Resource-Constrained Devices](../../references/proceedings/MLSys/2024/papers/mlsys2024-5431dca75a8d2abc1fb51e89e8324f10.pdf) | 候选待读 | CPU/GPU 并行与卸载的区别；先与既有 KTransformers 和新 NEO/FlexInfer 对照。 |
| [CloudEval-YAML: A Practical Benchmark for Cloud Configuration Generation](../../references/proceedings/MLSys/2024/papers/mlsys2024-554e056fe2b6d9fd27ffcd3367ae1267.pdf) | 排除正文 | 云配置代码生成评测不是本书的主要资源分析问题。 |
| [Atom: Low-Bit Quantization for Efficient and Accurate LLM Serving](../../references/proceedings/MLSys/2024/papers/mlsys2024-5edb57c05c81d04beb716ef1d542fe9e.pdf) | 保留历史依据 | 低比特算子吞吐与位宽配合；先由 2025 QServe 整合该演进。 |
| [ACCURATE LOW-DEGREE POLYNOMIAL APPROXIMATION OF NON-POLYNOMIAL OPERATORS FOR FAST PRIVATE INFERENCE IN HOMOMORPHIC ENCRYPTION](../../references/proceedings/MLSys/2024/papers/mlsys2024-621d0fd41c720ab252e178b77c200d90.pdf) | 排除正文 | FHE 多项式近似与隐私推理不展开。 |
| [SiDA: Sparsity-Inspired Data-Aware Serving for Efficient and Scalable  Large Mixture-of-Experts Models](../../references/proceedings/MLSys/2024/papers/mlsys2024-698cfaf72a208aef2e78bcac55b74328.pdf) | 候选待读 | 专家稀疏访问与 GPU/主存容量；检查路由预测与质量代价，再与 AF 区分。 |
| [Does Compressing Activations Help Model Parallel Training?](../../references/proceedings/MLSys/2024/papers/mlsys2024-71381211d0abef73ed1887b83c4547b1.pdf) | 候选待读 | 模型并行激活压缩的编解码/通信/质量条件，可能补 7、11 的成本推算。 |
| [Distributed Matrix-Based Sampling for Graph Neural Network Training](../../references/proceedings/MLSys/2024/papers/mlsys2024-75bb91b908e6924763c9f2bbe87e921e.pdf) | 排除正文 | GNN 图采样专用问题，不单独扩展模型家族。 |
| [Disaggregated Multi-Tower: Topology-aware Modeling Technique for Efficient Large Scale Recommendation](../../references/proceedings/MLSys/2024/papers/mlsys2024-78834433edc3291f4c6cbbd2759324db.pdf) | 备选，不新增 | 推荐系统拓扑建模是协同设计对照，当前先保持 LLM 贯穿案例。 |
| [VQPy: An Object-Oriented Approach to Modern Video Analytics](../../references/proceedings/MLSys/2024/papers/mlsys2024-87eaaa8605a1a472d9a9756e7500517b.pdf) | 排除正文 | 视频查询 DSL 与对象关系优化，偏应用编排。 |
| [SLoRA: Scalable Serving of Thousands of LoRA Adapters](../../references/proceedings/MLSys/2024/papers/mlsys2024-906419cd502575b617cc489a1a696a67.pdf) | 重点阅读并整合 | adapter 与 KV 的统一容量、异构 rank 与公平性，和 Punica 合并为一个案例。 |
| [L-GreCo: Layerwise-adaptive Gradient Compression For Efficient Data-parallel Deep Learning](../../references/proceedings/MLSys/2024/papers/mlsys2024-9069a8976ff06f6443e7f4172990a580.pdf) | 备选，不新增 | 分层梯度压缩与误差预算；等待更接近大模型训练的后续研究比较。 |
| [Prompt Cache: Modular Attention Reuse for Low-Latency Inference](../../references/proceedings/MLSys/2024/papers/mlsys2024-a66caa1703fe34705a4368c3014c1966.pdf) | 候选待读 | 模块化缓存需要位置与上下文语义；不能等同普通前缀缓存，先读边界。 |
| [Fine-Tuning Language Models Using Formal Methods Feedback: A Use Case in Autonomous Systems](../../references/proceedings/MLSys/2024/papers/mlsys2024-b0131b6ee02a00b03fc3320176fec8f5.pdf) | 排除正文 | 自动驾驶控制器的形式验证反馈，已有更贴近代码 RL 的验证案例。 |
| [VIDUR: A LARGE-SCALE SIMULATION FRAMEWORK FOR LLM INFERENCE](../../references/proceedings/MLSys/2024/papers/mlsys2024-b74a8de47d2b3c928360e0a011f48351.pdf) | 候选待读 | 微基准校准与推理仿真，拟补 13.5 何时值得增加模型细节，不能鼓励先造模拟器。 |
| [Torch2Chip: An End-to-end Customizable Deep Neural Network Compression and Deployment Toolkit for Prototype Hardware Accelerator Design](../../references/proceedings/MLSys/2024/papers/mlsys2024-b8bf2c0dd0b48511889b7d3b2c5fc8f5.pdf) | 备选，不新增 | 算法量化到硬件部署的表示缺口，可作 5.3 背景，不增加工具教程。 |
| [Q-Hitter: A Better Token Oracle for Efficient LLM Inference via Sparse-Quantized KV Cache](../../references/proceedings/MLSys/2024/papers/mlsys2024-bbb7506579431a85861a05fff048d3e1.pdf) | 候选待读 | 稀疏选择和量化互相影响，有助 9.4 避免直接相乘独立收益。 |
| [FedTrans: Efficient Federated Learning via Multi-Model Transformation](../../references/proceedings/MLSys/2024/papers/mlsys2024-bbd7d8bd780fcf7143add2317ba04638.pdf) | 排除正文 | 联邦模型个性化与聚合，不是本书当前主线。 |
| [LIFL: A Lightweight, Event-driven Serverless Platform for Federated Learning](../../references/proceedings/MLSys/2024/papers/mlsys2024-c2a0e26dd9ee7d57e92bb1c24b39659a.pdf) | 备选，不新增 | 联邦聚合 serverless；第 12 章优先 Agent/RL 实际环境。 |
| [Proteus: Preserving Model Confidentiality during Graph Optimizations](../../references/proceedings/MLSys/2024/papers/mlsys2024-c66a9db149261435664284a20b6f1d42.pdf) | 排除正文 | 图优化过程中的模型保密机制，超出当前容量与性能重点。 |
| [QMoE: Sub-1-Bit Compression of Trillion Parameter Models](../../references/proceedings/MLSys/2024/papers/mlsys2024-c74b624843218d9b6713fcf299d6d5e4.pdf) | 候选待读 | 亚 1 bit 大 MoE 的编码与执行代价，后续核对其模型、质量和理想未压缩基线。 |
| [vMCU: Coordinated Memory Management and Kernel Optimization for DNN Inference on MCUs](../../references/proceedings/MLSys/2024/papers/mlsys2024-d5a655b8b373737b4f2aea8f78e5e754.pdf) | 备选，不新增 | MCU 生存期与内核协同，可作简短旁证，避免扩展成 TinyML 教材。 |
| [UniDM: A Unified Framework for Data Manipulation with Large Language Models](../../references/proceedings/MLSys/2024/papers/mlsys2024-dcb38c6ad7911842ab31081be9540b89.pdf) | 排除正文 | 数据湖操作的 LLM 应用框架，不加入推理引擎主线。 |
| [Efficient Post-training Quantization with FP8 Formats](../../references/proceedings/MLSys/2024/papers/mlsys2024-dea9b4b6f55ae611c54065d6fc750755.pdf) | 保留历史依据 | FP8 E/M 位宽的跨任务比较，采用前须限制到原评估模型与硬件。 |
| [COMET: Neural Cost Model Explanation Framework](../../references/proceedings/MLSys/2024/papers/mlsys2024-eb261df4322a8bd0a73093c4d8a0d02d.pdf) | 排除正文 | 这是解释 CPU 神经成本模型的 COMET，并非 2025 MoE 通信重叠的同名系统。 |
| [On Latency Predictors for Neural Architecture Search](../../references/proceedings/MLSys/2024/papers/mlsys2024-f03cb785864596fa5901f1359d23fd81.pdf) | 备选，不新增 | 硬件外推与采样偏差支持第 13 章方法；不增加 NAS 专题。 |
| [FLASH: Fast Model Adaptation in ML-Centric Cloud Platforms](../../references/proceedings/MLSys/2024/papers/mlsys2024-f502981cbe221d857ad409450a7917c3.pdf) | 排除正文 | ML 控制器跨任务适应，当前优先与 LLM 资源调度直接相关论文。 |

## Punica 与 S-LoRA 的合并案例

重点读 Punica 的 PDF 第 3–6 页（§3–6 与 §7 开头），以及 S-LoRA 第 3–5、7 页（§3–5、§7.1 与 §7.2 开头）。共同问题是同一基座的不同 adapter 如何共享大矩阵乘，同时分别执行低秩修正。按 adapter 分组、非连续页与变长 rank 的支持是额外工作，不能从参数很少推导出没有执行开销。

Punica 的实验采用 Llama-2、rank 16、随机 LoRA 权重及特定请求分布；其迁移选择重做 prefill。S-LoRA 使用旧版 vLLM 多进程合并权重基线，且表 1 脚注明确其 70B 配置不采用官方 GQA。论文中的对比不能写成 2026 版 vLLM 仍不支持 LoRA，也不能直接移给 Qwen3-8B 的状态预算。

两篇论文合成第 9.2.2 的一个容量与批处理案例，实验 9-3 增加 adapter 变体，保留原实验总数。并发 adapter 数、活跃请求数、HBM 中热 adapter 数和主存中可提供的 adapter 数分别计量。具体推算见[多 LoRA 服务笔记](../../case-studies/multi-lora-serving.md)。

## 下一轮

2025 年全部摘要现已筛选，Marconi、FlashInfer 等四篇补读设计与实验条件，见[2025 阅读记录](reading-mlsys-2025.md)。继续读 2026 全部摘要，优先比较 MoE 通信重叠、冷启动与可靠性；然后按主题回到本卷候选的全文。当前 2026 已归档但尚未完成逐篇筛选。
