# ISCA 2024 阅读与取舍

2026-09-08：87 个日程条目已匹配出版 DOI，当前归档覆盖 70 份公开稿、1,081 个物理页面，筛读 77 篇完整原始摘要（其中 7 篇依据机构 HTML／JSON）。其中 Splitwise 复用已有 PDF；Orojenesis 物理页 1–14 已选读，图 18–22 已查看；MAD-Max 物理页 5–8 已选读，图 7–9 和表 I–III 已查看；FEATHER 物理页 2–13 已选读，图 4–6、12–13 及表 III–IV 已查看。其余 10 篇摘要和更多公开稿仍待获取。没有将目录、OpenAlex 元数据或下载计作正文读完。依据见[目录](../../references/proceedings/ISCA/2024/manifest.json)、[GhOST 摘要](../../references/proceedings/ISCA/2024/ghost-abstract-reading.json)、[机构摘要证明](../../references/proceedings/ISCA/2024/institutional-abstracts.json)与[其他 69 篇的抽取范围](../../references/proceedings/ISCA/2024/public-manifest.json)。

| 日程序号与论文 | 取舍 | 对本书的意义 |
| --- | --- | --- |
| 1 GhOST | 备查 | GPU 停顿与评价中间表示值得注意；未读正文评估，不采用摘要加速比 |
| 3 The Maya Cache | 不纳入 | 通用 CPU 共享末级缓存的冲突侧信道与标签／数据容量取舍；本书的 AI 缓存、隔离主线暂不需要扩展至此类微架构。 |
| 4 DS-GL | 不纳入 | 通过改写动力学求解与稀疏互连处理图学习；并非在 GPU 上保持同一模型语义的算子优化。现有 AI 模型主线已足够，不扩展 Ising 图学习案例或采用摘要倍率。 |
| 5 ReAIM | 不纳入 | ReRAM Ising 求解器同时调整算法参数与器件误差条件；不是 LLM 或 RL 资源调度。保留摘要筛选记录，不扩展组合优化硬件专题。 |
| 6 Mirage | 备查 | 光子训练以多次低精度模运算实现高精度，转换精度值得备查；未读误差与评估，不采用摘要性能数字或视为现有 GPU 路径。 |
| 7 Constable | 不纳入 | 通用 CPU 在跟踪寄存器、内存和 snoop 修改后消除稳定 load；不是 GPU kernel 消除、KV 缓存或 Agent 运行环境的新案例。 |
| 8 QuTracer | 不纳入 | 追踪量子比特子集以缓解门及测量错误；超出当前 AI Infra 负载与分析主线。 |
| 9 Splitwise | 备查 | 已有 PD 分离来源；补会议与早稿身份，复用现有案例，不新增技术小节 |
| 10 HiFi-DRAM | 备查 | 通过实际 DRAM 成像核查感应放大器模型，支持模型假设需验证的写作判断；未读评估，不把摘要误差倍数泛化到 HBM 或所有模拟器。 |
| 11 Mind the Gap／Orojenesis | 纳入既有小节 | 片上容量限制可实现的复用，融合会改变分块选择；以独立 Qwen3 计数补 5.1–5.2 |
| 12 A Tale of Two Domains／CHRYSALIS | 不纳入 | 能量采集、间歇执行与小型自主设备的架构协同；这里的 autonomy 并非大模型 Agent，不扩展边缘设备专题。 |
| 13 Determining the Minimum Number of Virtual Networks | 备查 | 一致性协议的消息依赖与 VN 数量，不等于网络路由 VC 死锁问题；暂不扩充 AI 集合通信章节 |
| 14 FEATHER | 纳入既有小节 | 物理页 2–13 已选读；将总字节计数进一步落到 bank 端口及布局交接，补 4.4→5.1→5.2 的同一 Qwen3 算例，不采用研究硬件性能倍率。 |
| 15 Waferscale Network Switches | 待比较正文 | 面积以外还受内部带宽、外部带宽与功率密度限制；待读正文核查 radix、非阻塞条件与拓扑规模，比较现有超节点边界案例后再决定是否采用。 |
| 16 The Case For Data Centre Hyperloops | 备查 | 将 SSD 实体搬运作为数据移动量级的思想实验；不能据此替换低延迟 AI 协作链路 |
| 17 PID-Comm | 备查 | 存内计算的通信仍需经过主机；UPMEM 路径不等于 GPU 集合通信，不采用摘要速度 |
| 18 Bosehedral | 不纳入 | Boson sampling 的量子门分解、映射与近似丢门；不因名称类似 polyhedral 而归入 AI 编译优化。 |
| 19 Tetris | 不纳入 | VQA 指 variational quantum algorithms，优化双量子位门及量子电路映射；不是本书的视觉问答负载。 |
| 20 Atomique | 不纳入 | 中性原子阵列的量子比特映射、原子移动和门调度；不引入本书的大模型资源调度。 |
| 21 Suppressing Correlated Noise in Quantum Computers | 不纳入 | 超导量子比特噪声与量子编译，超出本书负载主线 |
| 22 A SAT Scalpel for Lattice Surgery | 不纳入 | 容错量子计算子程序的 SAT 综合，暂无需要补入的 AI 系统判断 |
| 23 PreSto | 备查 | 推荐系统预处理会限制训练供给；现有供给链已经有对应判断，不增加存储处理器专题 |
| 24 pSyncPIM | 备查 | 全 bank 同步 PIM 与不规则稀疏执行存在控制冲突；SpMV／SpTRSV 稀疏不等于 MoE 专家路由，未采用与 RTX 3080 的摘要比较。 |
| 25 NDSEARCH | 待比较正文 | 图索引的存储访问与近存计算值得对照 IKS／Faiss；先核 recall、随机 IO 和数据集条件 |
| 28 ElasticRec | 待比较正文 | 推荐模型的细粒度资源分配有助于对照分离部署；待读稀疏 embedding／dense 的分工、复制流量与 SLO 条件，不把推荐 serving 等同于 LLM PD／AF。 |
| 29 Derm | 备查 | 按动态调用图分配资源，并对时延作分布假设；可备查，但 TrainTicket 类微服务不直接代表 Agent／RL 的重尾与分支负载。 |
| 30 SmartOClock | 备查 | 生产负载下按功耗需求分配超频预算，涉及尾延迟与寿命；不是 GPU 功耗管理的直接证据，未读实验不新增超频实践。 |
| 31 Designing Cloud Servers for Lower Carbon／GreenSKU | 备查 | GreenSKU 将组件复用、运行能耗与性能要求合并评估；可备查成本之外的口径，但通用云的减排数字不能移用于 AI 集群。 |
| 32 EcoFaaS | 待比较正文 | 端到端 SLO 分配到函数期限，再按调用选择频率与 core pool；待读等待、输入和平台假设，比较 Agent 工具执行后再考虑采用。 |
| 33 AIO | 待比较正文 | 算法级数据并行工作与启动、计算、内存及重叠的分解，可能补充简单 Roofline 的适用边界。须读正文核对校准输入、评估负载及启动定义后再决定是否采用；不移用摘要误差或调度倍率。 |
| 34 FireAxe | 备查 | RTL 超过单 FPGA 时通过分区扩展仿真，并区分精确／快速模式；属于需要详细硬件验证时的工具，不作为本书初步估算的起点。 |
| 35 Harpocrates | 备查 | 静默数据损坏与崩溃不同；硬件模型辅助生成测试用于故障覆盖，不等于用 Agent 优化算子性能。保留可靠性背景，暂不扩充已有故障分析。 |
| 36 The Dataflow Abstract Machine Simulator Framework | 待比较正文 | 数据流组件、队列与同步的建模，并含注意力局部存储案例；待读算法与假设，只有能补充现有缓冲、融合分析时才采用。 |
| 37 Tartan | 备查 | 机器人专用向量化、语义预取及近似计算体现负载与架构的关系；当前只核摘要，保留背景，不增加完整机器人处理器案例。 |
| 38 Collision Prediction for Robotics Accelerators | 不纳入 | 预测碰撞后优先做详细安全检查，以提前淘汰无效路径；不替代安全检查。本书已有 AI 数据搬移案例，暂不扩展机器人规划专题。 |
| 39 BLESS | 不纳入 | DNA SMEM seeding 的 learned index、布局和缓存有特定搜索语义；不能作为 LLM 检索或 KV 访问的直接例子。沿用已有 AI 数据搬移案例。 |
| 40 QUETZAL | 不纳入 | 基因组向量加速、scatter／gather 缓冲；现有 AI 数据搬移案例已覆盖所需分析方法 |
| 41 HAL | 待比较正文 | SmartNIC 卸载是否有利取决于包速率、主机加速器及尾延迟；待读网络函数与能耗口径，不把摘要结果扩展到 LLM 推理。 |
| 42 NDPBridge | 备查 | 近 DRAM bank 的通信与负载均衡仍有数据迁移代价；作为近存设计备查，不等同于现有 GPU 专家迁移机制。 |
| 44 MegIS | 不纳入 | 存储内元基因组分析的任务切分与数据访问；本书已有 AI 数据搬移案例，无需扩展生物信息学专章。 |
| 45 On Error Correction for Nonvolatile Processing-In-Memory | 不纳入 | 非易失存内计算同时面对存储错误与计算中产生的错误；普通内存 ECC 不能直接覆盖后者。暂不扩展新型存储纠错专题。 |
| 46 MetaLeak | 不纳入 | 安全处理器的元数据维护形成侧信道；与当前 AI 负载、资源约束和运行环境主线较远，暂不增加微架构攻击专题。 |
| 47 sNPU | 备查 | 集成 NPU 的访问控制、scratchpad 和 NoC 隔离需要硬件支持；本文为 FPGA 原型，不能当作 E2B 轻量虚拟机或现有 GPU 默认能力。 |
| 48 Counter-light Memory Encryption | 不纳入 | 通用内存加密在计数器流量与解密依赖之间取舍；与当前 AI 运行环境主线相距较远，不采用摘要性能比例。 |
| 49 Perspective | 不纳入 | 操作系统对瞬态执行攻击的软硬件防御；此处 speculative execution 并非大模型推测解码，不混入对应章节。 |
| 50 HEAP | 不纳入 | CKKS／TFHE 切换使同态加密 bootstrapping 并行化，另需专用数据通路；与常规大模型低精度运算不同，不新增密码加速器案例。 |
| 51 HammerBlade | 备查 | RISC-V 多核的扩展性、可编程性和计算密度；保留实际芯片设计背景，不增加第四套完整架构讲解。 |
| 52 HADES | 备查 | 快速网络使分布式事务的软件开销突出，SmartNIC 与协议协同减少开销；数据库事务不能直接替代 AI 集合通信或 RL 状态交接分析。 |
| 53 BlitzCoin | 备查 | 分散式片上功耗管理缓解响应时间与规模限制；保留芯片资源取舍背景，不将其等同于云端 GPU 作业调度。 |
| 54 MAD-Max Beyond Single-Node | 备查（已选读） | 已选读物理页 5–8 的建模与验证：分层估时后按计算／通信依赖拼接，且假定模型驻留设备；现有推算主线已覆盖该方法，保留适用边界，不新增小节或移用预测加速比。 |
| 55 Barre Chord | 备查 | MCM GPU 地址翻译与 IOMMU 并发约束；可备查，但硬件页表合并与软件 KV 分页不是同一机制。 |
| 58 AMD Exascale Heterogeneous Processor | 备查 | 从分立 exascale 节点到 MI300A 的设计演变可作写作背景；当前仅读摘要与身份，不采用内部架构或产品性能结论。出版作者元数据合并两名作者，另存核对记录。 |
| 59 Tensor Contraction Processor／TCP | 待比较正文 | 张量收缩的形状、循环次序与片上复用有具体硬件实例；待读软件映射及 LLaMA-2 历史实验口径，不将其能效倍率当作现款通用排名。 |
| 61 Flagger | 备查 | 同态加密造成密文膨胀与聚合开销，再以 DPU、计算存储和 P2P 分工；跨机构联邦聚合不等于超节点间普通梯度 AllReduce。保留备查，不引入摘要性能比例。 |
| 62 Trapezoid | 备查 | 以不同数据流适配不同矩阵稀疏度；可对照索引、归约与存储代价，不把非结构化稀疏直接等同于 MoE 路由或 2:4。 |
| 63 NeuraChip | 备查 | GNN 稀疏乘加解耦、部分和驻留与负载均衡；现有 AI 缓冲和搬移案例先行，不移用 GNN 加速比。 |
| 64 Compiler-Directed Whole-System Persistence／cWSP | 备查 | 编译器以可恢复 epoch 协同硬件实现非易失内存上的全系统持久化；与分布式训练检查点及模型版本协议的故障边界不同。 |
| 65 Memento | 备查 | GPU 寄存器文件缓存及 profile 辅助调度可作背景；未读评估条件，不当作当前芯片已有机制 |
| 67 ALISA | 备查 | 稀疏注意力改变计算语义，并结合缓存与重算；不把它等同于无损 KV 分层或当前 vLLM 性能 |
| 68 Pre-gated MoE | 待比较正文 | 修改模型以提前确定专家，需与透明预取、CPU 专家执行分开；现阶段不新增性能结论 |
| 70 Tender | 待比较正文 | 以尺度相差二的幂的分解矩阵处理低精度累加与重缩放；待读量化语义、硬件改动和质量条件，不视为现有 GPU 的免费整数性能。 |
| 71 Hotline | 待比较正文 | 按 embedding 热度重组 micro-batch，在 GPU 计算时准备冷 embedding；待读训练语义、数据分布和额外硬件，再与 CPU／GPU 协同案例比较。 |
| 72 LLMCompass | 待比较正文 | 何时从简单估算升级到映射与成本模型；归档的是不同题名的 2023 年早稿，未采用其误差或性价比数字 |
| 73 DRAMScope | 备查 | 用多种测试交叉验证 DRAM 内部映射与结构，说明模型假设仍需核查；不将商品 DRAM 结论当作 HBM 规格或通用可靠性保证。 |
| 74 (MC)²: Lazy MemCopy at the Memory Controller | 备查 | 延迟实际复制可省去未访问的数据搬移，但需要内存控制器和 ISA 扩展，评估基于 gem5；不当作现有 CUDA 异步复制的完成语义。 |
| 75 DyLeCT | 备查 | 硬件压缩内存仍要平衡地址翻译覆盖范围与页面搬移带宽；不是权重量化或 PagedAttention，暂不增加一套压缩内存机制。 |
| 76 Native DRAM Cache | 备查 | 在 DRAM 内完成 tag 匹配与 way 选择的 CPU 末级缓存设计；CIM 在此指 Caching-In-Memory，不是 KV 内存池或通用存内计算。暂不新增本书机制。 |
| 77 PrIDE | 不纳入 | 低成本 DRAM 内跟踪器以随机插入推导 Rowhammer 防护边界；每 bank 的失效时间不能当作整台 AI 服务器或集群的可靠性保证。 |
| 78 A New Formulation of Neural Data Prefetching | 备查 | 神经预取器自身的延迟、存储与泛化能力会抵消收益；保留优化开销也需计数的背景，不把 CPU 预取算法直接套成 LLM 缓存预取。 |
| 79 UDP | 不纳入 | CPU 前端取指预取兼顾及时性与有效性；这里 UDP 不是网络传输协议，也不等同于 KV 预取，暂不扩展前端微架构。 |
| 80 Triangel | 不纳入 | 通用 CPU 时间相关预取；摘要未提供本书尚缺的 AI 系统案例 |
| 81 Alternate Path Fetch | 不纳入 | 乱序 CPU 在分支另一条路径上做取指和部分重命名，以减少预测错误后的恢复延迟；不混入大模型推测解码。 |
| 82 Alternate Path μ-op Cache Prefetching | 不纳入 | 通用数据中心 CPU 前端优化；不替代 Agent／RL 运行环境的应用分析 |
| 83 DACAPO | 备查 | 端侧视频持续学习同时分配推理、标注和重训资源；是教师／学生系统，不能直接替代大模型 RL 的 rollout／更新分析。 |
| 84 BlissCam | 备查 | 传感器内稀疏采样同时减少传输与后端计算，可备查端到端协同方法；依照本书范围，不扩展图像采集背景或采用摘要性能数字。 |
| 86 Cicero | 备查 | NeRF 的工作量减少、访存规则化和 SRAM 布局一起优化；质量变化需单独计入，不能直接比较为当前 LLM 框架性能。 |
| 87 GameStreamSR | 备查 | 用游戏渲染的深度数据选择局部超分区域，以网络、端侧计算和交互时限作取舍；Computer Use 截图通常不具备这项输入。已有图像精修与截图案例保持简洁，不移用摘要速度、质量或能耗数字。 |

首批完成摘要和首页身份核对；13、82 的机构封面保留，摘要位于物理第 2 页，其他条目的摘要位于第 1 页。双栏文本可能把引言穿插到摘要附近，记录保存实际起止字符。修订号、题名与作者差异见清单；PDF 页数与已读页数分别统计。

Orojenesis 选读后只补一个分析步骤：先根据可用容量计复用，再为对应存储层次构造 Roofline。它的融合分析限定模板、分块和重计算范围，不作为所有 GPU 映射的最优性保证；原文面积／单位问题及历史模型简化单列在[读取记录](../../references/proceedings/ISCA/2024/orojenesis-reading.json)，不移用其性能阈值。具体采用[Qwen3 独立算例](../../case-studies/buffer-capacity-and-data-movement.md)，深化实验 5-1、5-2 和图 5-1、5-2，没有增加章节、实验编号或面试题。

新增 16 篇中，7 篇不纳入、5 篇备查、4 篇保留为正文候选；均已读完整原始摘要并核对首页题名与作者。四张首页只用于确认双栏摘要边界，没有据此增加重点正文阅读计数。来源版本、连接失败与成功重试见[批次记录](../../references/proceedings/ISCA/2024/screening-batch-2026-09-08.json)。

后续读正文时，围绕已有章节核对四个问题：

- Waferscale Network Switches：内部搬移、外部端口与功率分别怎样限制 radix；与现有超节点扩展案例相比，是否增加了必要的推算步骤。
- ElasticRec：拆开不同资源需求的层以后，节省了哪些副本，又增加多少传输；推荐模型的 embedding 访问条件与 LLM 的 PD／AF 分离有什么不同。
- EcoFaaS：怎样从端到端时限推到函数的 CPU 时间、等待时间和频率选择；输入变化与预测失误怎样影响尾延迟，能否用于 Agent 工具链的已有实验。
- Tender：低位宽节省的容量与流量，是否被重缩放、部分和以及硬件支持条件抵消；在采用前先核模型质量和计算语义。

该批次尚未改变 skeleton、小节、实验或图的安排，也不新增面试题。

新增的架构与建模批次又补 17 份公开稿／259 页、17 篇完整摘要，其中 3 篇排除、10 篇备查、4 篇保留为正文候选。DAM、HAL、TCP、Hotline 的后续问题分别是流式注意力的局部存储、主机／SmartNIC 的分工、张量收缩的复用，以及冷 embedding 准备能否与 GPU 工作重叠。版本和首页核对见[该批次记录](../../references/proceedings/ISCA/2024/screening-batch-models-2026-09-08.json)。

MAD-Max 已读[物理页 5–8 的建模与验证](../../references/proceedings/ISCA/2024/madmax-reading.json)。它用层的 FLOPs 或 lookup bytes 估时，再根据并行方式、依赖和集合通信组织时序；这与本书现有第 6、7、11 章的方法相符，暂不增加一套模拟器教程。它也给出值得保留的适用边界：

- 模型分片后必须驻留设备，尚不支持 CPU／GPU 之间反复搬运权重；host-device 数据加载也被假设为大部分隐藏。不能用该模型直接支持 offload、AF 或 KTransformers 的结论。
- 利用率与有效集合通信带宽需要校准。分别核对串行执行和重叠执行，才能分清工作量误差与调度误差；图 9 的预取时序不能代表任何框架版本都达到同样的重叠率。
- 误差要对应具体指标、形状和规模。图 8 的部分预测明显偏离测量，原文平均 modeling accuracy 不构成每个点的误差保证；图中数值未做数字化提取。表 III 的系统合计带宽不可用来除单 rank 字节，且 TB/s 与 Tbps 分开。

原文的 compute utilization／SM utilization／occupancy 并列表述、表 I 与正文的 DLRM-B 小数差异，以及 LLaMA 型号标签差异都保留在阅读记录。假想 1.8T MoE 不当作当前公开模型。AMD 论文的公开首页显示 13 位作者，出版元数据把 Mark Fowler 与 Nathan Kalyanasundharam 合成一条；[合著者出版页](../../references/proceedings/ISCA/2024/isca24-amd-author-publication.html)也明确列出 13 位作者。原始元数据保留，另存编辑核对说明。该批次未改动书的提纲结构或引入新的性能结论。

本次补齐其余公开稿中的 19 篇／299 页，逐篇筛读完整原始摘要：12 篇备查、7 篇不纳入，没有新增正文候选。CPU 前端、存内纠错、同态加密与机器人规划等方向暂不扩展书的范围；sNPU、懒复制、神经预取等保留可供核对的适用边界。现有第 4、5、8、11、12、13 章已经有相应的负载、数据搬移或恢复分析方法，仅读摘要不足以采用新的实现或性能结论。见[本批记录](../../references/proceedings/ISCA/2024/screening-batch-remainder-2026-09-08.json)。

六张页面图只用于核对身份和摘要边界。Tartan 的物理第 1 页为 ACM 附加封面，显示 Published: 23 July 2025、PDF Download: 19 March 2026，同时注明 ISCA ’24；论文从物理第 2 页开始，其会议页眉为 2024。保留这些不同含义的日期，会议归属仍为 ISCA 2024。sNPU 页脚的下载日期也不作为发表日期；(MC)² 的出版标题 HTML 上标仅作格式规范化，原值保留。此次没有增加正文选读计数或提纲内容。

此前该批结束时尚缺 17 篇完整原始摘要，日程序号为 2、4、5、26、27、33、39、43、56、57、60、61、66、69、76、85、87。AIO、Soter、MECLA、UM-PIM 等仍优先寻找作者公开稿；作者出版列表、代码仓库和检索摘要不能代替已归档的完整原始摘要。此前 LLMCompass、NDSEARCH 等正文候选继续保留，未因这一批完成而视为已读。

FEATHER 随后完成[物理页 2–13 的选读](../../references/proceedings/ISCA/2024/feather-reading.json)，四张页面图核对了布局例子、归一化指标与评估配置。第 4→5 章采用独立的 32×32 暂存块计数：128 B padding 改变 bank 请求分布，完整物化 24 MiB 投影输出的重排另增 48 MiB 逻辑访问；均不作为实测加速比。原文 `max(N_P/N_L,1)` 的 slowdown 写法与其端口限制解释不一致，Edge TPU 的图文数字也不一致，保留未采用。专用网络、离线配置、INT8 数据通路和修改后的模拟配置不移作当前 GPU 结论。此项增加一个重点阅读范围，沿用实验 5-1、图 5-1，未增加小节或题号。

本轮另筛读 7 篇[机构原始完整摘要](../../references/proceedings/ISCA/2024/institutional-abstracts.json)，逐项核对 DOI、作者、标题与抽取节点。结果为 3 篇排除、3 篇备查、1 篇正文候选；没有新增 PDF 或重点正文范围，也没有扩大提纲。

AIO 与第一章“先算清约束”的方法相关，但只凭摘要不能采用 AccMe 的误差或调度收益。后续读取时要核对：算法级工作单位如何映射到不同加速器，启动时间包含什么，计算与访存怎样重叠，哪些参数需要实测校准，再与已有 Roofline／MAD-Max 案例比较。机构记录列出作者 accepted version，但匿名下载请求返回 403；不能把开放文件元数据当作 PDF 已归档。

DS-GL 的 PNNL 页面使用较早题名，DOI、六位作者、会议和页码相符，合著者列表另提供正式题名；只声明读过这份机构摘要，不声称与出版稿逐字相同。Native DRAM Cache 的 CIM 是 Caching-In-Memory，Flagger 的对象是同态加密联邦聚合；GameStreamSR 使用渲染深度数据定位局部超分区域。这些条件与 LLM KV 池、普通 AllReduce、Computer Use 截图不同，暂不强行加入本书。PNNL 摘要的倍率排版和 Flagger 的残留公式字符原样保留，不据此引用性能结果。

当前待补完整原始摘要的日程序号为 **2、26、27、43、56、57、60、66、69、85**。获取状态与后续入口见[补查记录](../../references/proceedings/ISCA/2024/closing/README.md)；作者主页、新闻、幻灯片链接及检索片段没有关闭这些缺口。Neoscope 的 ISCA 2025 机构记录当时仅作为下一届线索，未混入本届；随后按 [ISCA 2025 阅读记录](reading-isca-2025.md)纳入该届摘要计数。
