# ASPLOS 2025：公开稿、摘要筛选与专题正文

截至 2026-09-09，官方主日程 184 个 DOI 中已归档 34 份代表 PDF、完成 35 篇原始完整摘要筛选，六篇有声明范围的正文阅读；其余 149 篇摘要未读。本轮补读 DarwinGame 物理页 1–13，七页图表已查看，未新增摘要或 PDF。它只补现有自动调优实验的比较条件，不增赛制专题。

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
| 28. [PICACHU: Plug-In CGRA Handling Upcoming Nonlinear Operations in LLMs](../../references/proceedings/ASPLOS/2025/public/paper-028.pdf) | 候选待读 | PICACHU 以可重构单元加速非线性操作，候选对应第 4／13 章资源配比；需核模型、精度、仿真和实际接口，不从摘要采用加速比。 |
| 33. [Coach: Exploiting Temporal Patterns for All-Resource Oversubscription in Cloud Platforms](../../references/proceedings/ASPLOS/2025/public/paper-033.pdf) | 候选待读 | Azure 多资源超售与时间互补，可能补 11 的 CPU 环境容量；需与 CASSINI／Weave 的互补调度比较，避免泛化到 GPU。 |
| 34. [Cooperative Graceful Degradation in Containerized Clouds](../../references/proceedings/ASPLOS/2025/public/paper-034.pdf) | 备查 | Phoenix 按应用依赖和关键性关闭非关键容器，作为第 11 章故障降级备查；不把一般微服务的可用性直接当作 Agent 成功率。 |
| 35. [DarwinGame: Playing Tournaments for Tuning Applications in Noisy Cloud Environments](../../references/proceedings/ASPLOS/2025/public/paper-035.pdf) | 重点阅读并整合 | 物理页 1–13 已读；配对测量与候选之间的争用补 5.3.5／实验 5-6。公开工件与论文算法有差距，仅作方法对照，不采用 CPU 加速比或声称 GPU 可复现。 |
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

## 尚缺的材料

- 首个 session 中 Mosaic、DynaX、RASSM 的原始摘要／正文仍有缺口；DynaX 的作者 README 不能代替论文。TFHE 作者页面的 PDF 按钮仍指向 ACM。
- 184 条 OpenAlex 查询结果只用于定位公开稿，不能替代原始摘要；其中可用位置也不完整，已知 GUST／IKS 等须另行查找。公开副本归属再由标题、作者和正式 DOI 核对。
- 初次下载的一份机构副本返回 403，ACM 条目返回 403，探测的官方 abstracts 路径为 404。保留响应，继续寻找作者稿；其余工作正常推进。
- 本轮 NCSU 作者链接以 HTTP 200 重定向到 Purdue 实验室首页，Yale PULSE 链接为 404；均保存响应，不计论文。第 17／24 项仍缺公开稿，其余未筛条目按 manifest 保留。
- 其余 149 篇继续查摘要和全文。已读候选先与本书现有图执行、资源共享、调度和分层存储案例比较，只有新的约束或选择边界才进入提纲。

机器记录：[摘要与来源](../../references/proceedings/ASPLOS/2025/public-abstracts.json)、[筛选表](screening-asplos-2025.tsv)、[逐篇 manifest](../../references/proceedings/ASPLOS/2025/manifest.json)。

Earth+ 的 2024 作者 v1 有六位作者，含 Ranveer Chandra；已归档正式 DOI 的 Crossref 记录列五位，未列该名字。题名与其余五位作者一致，按较早作者版本归档；此处仅记录元数据差异，不推断正式 PDF 的作者名单已经变更。
