# ASPLOS 2025：公开稿与首批摘要筛选

2026-09-08 已按官方主日程 184 个 DOI 查找公开副本：归档 23 份 PDF，另取得一篇作者摘要，完成这 24 篇的完整摘要筛选。其余 160 篇尚未完成摘要阅读。下表按日程编号排列，编号不连续；不能称“前 24 篇已读”。出版元数据、作者稿和后续上传版本分开记录，见[归档说明](../../references/proceedings/ASPLOS/2025/README.md)。

| 日程编号与论文                                                                                                                                                                                                   | 取舍      | 判断与位置                                                                       |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | --------------------------------------------------------------------------- |
| 3. [Accelerating Retrieval-Augmented Generation](../../references/proceedings/ASPLOS/2025/public/iks-v1.pdf)                                                                                              | 重点阅读并整合 | 检索精度会改变生成输入，适合 13.1／13.4 的协同设计；将历史 NQ／Llama 基线、模拟硬件和 Qwen3 教学预算分开。          |
| 4. [GUST: Graph Edge-Coloring Utilization for Accelerating Sparse Matrix Vector Multiplication](../../references/proceedings/ASPLOS/2025/public/gust-v1.pdf)                                              | 备查      | SpMV 的乘加资源共享与边着色可说明稀疏映射，但已有注意力／MoE 贯穿案例；暂不增添通用稀疏加速器。                        |
| 6. [Orion: A Fully Homomorphic Encryption Framework for Deep Learning](../../references/proceedings/ASPLOS/2025/public/orion-v3.pdf)                                                                      | 排除      | FHE 私密神经推理的密文打包与 bootstrap 编译，超出本书明文模型执行与 Agent 沙箱主线。                       |
| 7. [CIPHERMATCH: Accelerating Homomorphic Encryption-Based String Matching via Memory-Efficient Data Packing and In-Flash Processing](../../references/proceedings/ASPLOS/2025/public/ciphermatch-v1.pdf) | 排除      | 加密字符串匹配与闪存内计算面向 DNA／数据库；不因包含数据搬移就扩展为 AI Infra 正文。                           |
| 8. [ReSBM: Region-based Scale and Minimal-Level Bootstrapping Management for FHE via Min-Cut](../../references/proceedings/ASPLOS/2025/public/resbm.pdf)                                                  | 排除      | 密文 scale 与 bootstrap 的联合管理属于 FHE 专用编译；不替代第 5 章张量切分和融合。                      |
| 9. [HALO: Loop-aware Bootstrapping Management for Fully Homomorphic Encryption](../../references/proceedings/ASPLOS/2025/public/halo-author.html)                                                         | 排除      | FHE 循环中 ciphertext level 与 bootstrap 放置，和本书推理循环／CUDA Graph 不是同一问题。          |
| 15. [Fat-Tree QRAM: A High-Bandwidth Shared Quantum Random Access Memory for Parallel Queries](../../references/proceedings/ASPLOS/2025/public/paper-015.pdf)                                             | 排除      | 量子 QRAM 的叠加态查询与量子比特资源，不能用名称相似替代第 7 章的数据中心 Fat-tree。                         |
| 26. [Enhancing CGRA Efficiency Through Aligned Compute and Communication Provisioning](../../references/proceedings/ASPLOS/2025/public/paper-026.pdf)                                                     | 备查      | CGRA 的计算与互联按子图 motif 配比，可作 4／13 的结构取舍备选；先与已有 GPU／昇腾代际案例比较。                  |
| 33. [Coach: Exploiting Temporal Patterns for All-Resource Oversubscription in Cloud Platforms](../../references/proceedings/ASPLOS/2025/public/paper-033.pdf)                                             | 候选待读    | Azure 多资源超售与时间互补，可能补 12 的 CPU 环境容量；需与 CASSINI／Weave 的互补调度比较，避免泛化到 GPU。      |
| 79. [MVQ: Towards Efficient DNN Compression and Acceleration with Masked Vector Quantization](../../references/proceedings/ASPLOS/2025/public/paper-079.pdf)                                              | 备查      | N:M 剪枝、向量码本和阵列协同，实验主要是视觉 CNN；已有模型量化主线，暂不增算法小节。                              |
| 87. [Bounding Speculative Execution of Atomic Regions to a Single Retry](../../references/proceedings/ASPLOS/2025/public/paper-087.pdf)                                                                   | 排除      | 共享内存原子区域的事务重试与 cacheline 锁，区别于 LLM 的推测解码和 rollout 重试。                       |
| 94. [FSMoE: A Flexible and Scalable Training System for Sparse Mixture-of-Experts Models](../../references/proceedings/ASPLOS/2025/public/paper-094.pdf)                                                  | 重点阅读并整合 | 已读正文 1–13 页；将梯度就绪、链路空隙和分桶接到 11.3 与实验 11-5，保留历史改型模型。                         |
| 95. [CoServe: Efficient Collaboration-of-Experts (CoE) Model Inference with Limited Memory](../../references/proceedings/ASPLOS/2025/public/paper-095.pdf)                                                | 候选待读    | CoE 的专家是多个模型，依赖感知切换与分层驻留可补 12 路由；不能直接等同 MoE FFN 专家，先核服务质量与模型边界。             |
| 115. [Past-Future Scheduler for LLM Serving under SLA Guarantees](../../references/proceedings/ASPLOS/2025/public/paper-115.pdf)                                                                          | 候选待读    | 按输出历史分布预测未来 batch 内存峰值，补 9 的准入与 12 的 goodput 判断；需核论文和 LightLLM 固定实现及分布漂移条件。 |
| 119. [ClosureX: Compiler Support for Correct Persistent Fuzzing](../../references/proceedings/ASPLOS/2025/public/paper-119.pdf)                                                                           | 备查      | 持久 fuzzing 重用进程但恢复测试相关状态，可对照 12 的环境复用；它不直接证明多租户 Agent 的隔离或完整快照语义。           |
| 124. [Protecting Cryptographic Code Against Spectre-RSB: (and, in Fact, All Known Spectre Variants)](../../references/proceedings/ASPLOS/2025/public/paper-124.pdf)                                       | 排除      | Jasmin／Coq 的投机常数时间保护聚焦密码实现；不扩成本书 CPU 微架构攻击专题。                               |
| 126. [SMaCk: Efficient Instruction Cache Attacks via Self-Modifying Code Conflicts](../../references/proceedings/ASPLOS/2025/public/paper-126.pdf)                                                        | 排除      | 自修改代码的指令缓存侧信道与检测，和本书 GPU 推理优化主线距离较远。                                        |
| 131. [Micro Blossom: Accelerated Minimum-Weight Perfect Matching Decoding for Quantum Error Correction](../../references/proceedings/ASPLOS/2025/public/paper-131.pdf)                                    | 排除      | 量子纠错 MWPM 的异构加速，decode 是纠错译码，不能归入 LLM decode 案例。                            |
| 136. [FastGL: A GPU-Efficient Framework for Accelerating Sampling-Based GNN Training at Large Scale](../../references/proceedings/ASPLOS/2025/public/paper-136.pdf)                                       | 备查      | GNN 采样、IO 与计算协同有方法价值，但不新增模型家族；现有 Transformer 案例优先。                          |
| 155. [PIM Is All You Need: A CXL-Enabled GPU-Free System for Large Language Model Inference](../../references/proceedings/ASPLOS/2025/public/paper-155.pdf)                                               | 候选待读    | CENT 把模型放到 CXL 近存设备并实现并行通信，可能补 4／6／13 的容量带宽选择；需核实际模型、批量、功耗和 TCO 假设。         |
| 164. [TensorTEE: Unifying Heterogeneous TEE Granularity for Efficient Secure Collaborative Tensor Computing](../../references/proceedings/ASPLOS/2025/public/paper-164.pdf)                               | 候选待读    | TensorTEE 的 CPU／NPU 数据粒度与重加密成本可补 6／12 的协同边界；需核模拟与安全假设，不当作现有 GPU 默认功能。       |
| 169. [Litmus: Fair Pricing for Serverless Computing](../../references/proceedings/ASPLOS/2025/public/paper-169.pdf)                                                                                       | 候选待读    | Serverless 拥塞造成时长和费用变化，可补 12 成本；先核测试如何区分负载与干扰，不冒充服务商现行计费规则。                 |
| 180. [A Software Caching Runtime for Embedded NVRAM Systems](../../references/proceedings/ASPLOS/2025/public/paper-180.pdf)                                                                               | 排除      | 嵌入式 NVRAM 指令缓存的编译与运行时，和模型权重／KV 分层不是同一流量，不扩展 MCU 专题。                         |
| 181. [Velosiraptor: Code Synthesis for Memory Translation](../../references/proceedings/ASPLOS/2025/public/paper-181.pdf)                                                                                 | 备查      | 从内存映射规格生成低层 OS 代码，可能作 12 隔离机制背景；不当作大模型优化 kernel，作者预印本上传晚于出版年。               |

## 重点阅读与采用范围

**Accelerating Retrieval-Augmented Generation／IKS**：作者 arXiv v1，物理页 1–13 已读，包含设计、评估、讨论及 artifact 简介；图 2、图 5 已查看。14–18 页为未读参考文献。页级记录见 [iks-reading.json](../../references/proceedings/ASPLOS/2025/iks-reading.json)。

采用的是检索和生成共同决定质量与时间的分析，以及将向量扫描放到数据附近的设计选择。第 13.1／13.4 与既有实验 13-1、图 13-1 使用[Qwen3 与向量库教学计算](../../case-studies/retrieval-and-generation.md)。论文 NQ、T5／Llama 和历史 H100 条件不移植到 Qwen3；近存硬件是 RTL 参数与周期近似模拟评估。原稿的加速范围、ANNS 标注和算力口径存在不一致，未采用这些数字。

Faiss 官方索引表与选择指南补充真实实验入口；普通 Flat 的 FP32 容量与教学 FP16 存储分别核算。尚未运行 Faiss、模型、作者代码或模拟器。

**FSMoE**：作者 arXiv 2501.10714v1（2025-01-18），物理页 1–13 已读；14–15 页参考文献未读，图 3／4 已查看。采用前反向分别选择切块、梯度分桶与跨机 All-to-All 共同调度的判断，用[同一 Qwen3 专家的 72 MiB 梯度](../../case-studies/expert-dispatch-and-resizing.md)接到 11.3／实验 11-5；不是当前推理引擎特性。页级证明见 [fsmoe-reading.json](../../references/proceedings/ASPLOS/2025/fsmoe-reading.json)。

实验为 RTX A6000／RTX 2080 Ti 集群，PyTorch 1.12、CUDA 11.3、NCCL 2.12；GPT-2／Mixtral 的专家数、部分层数按机器修改，不能称完整原始模型。正文说 Testbed-A 六节点、每节点四卡，却称 48 卡，表 3 与后文并行组为每节点八卡；保留冲突，不修成作者已确认的配置。第 7 页八张 200 Gb/s 与聚合 800 Gb/s、NVLink 口径混用；第 9 页把反向的 α、β、n 都翻倍，与 α+nβ 的解释不一致；图 5 的子图／参数标签也需复核。正文关于单个 Mixtral／Qwen 专家必须跨卡的论断不能替代实际矩阵和状态容量计算。本书只采用资源与依赖分析，不采用这些硬件数字、解析公式或加速比。未下载运行作者代码。

## 尚缺的材料

- 首个 session 中 Mosaic、DynaX、RASSM 的原始摘要／正文仍有缺口；DynaX 的作者 README 不能代替论文。TFHE 作者页面的 PDF 按钮仍指向 ACM。
- 184 条 OpenAlex 查询结果只用于定位公开稿，不能替代原始摘要；其中可用位置也不完整，已知 GUST／IKS 等须另行查找。公开副本归属再由标题、作者和正式 DOI 核对。
- 初次下载的一份机构副本返回 403，ACM 条目返回 403，探测的官方 abstracts 路径为 404。保留响应，继续寻找作者稿；其余工作正常推进。
- 其余 160 篇继续查摘要和全文。已读候选先与本书现有图执行、资源共享、调度和分层存储案例比较，只有新的约束或选择边界才进入提纲。

机器记录：[摘要与来源](../../references/proceedings/ASPLOS/2025/public-abstracts.json)、[筛选表](screening-asplos-2025.tsv)、[逐篇 manifest](../../references/proceedings/ASPLOS/2025/manifest.json)。
