# ASPLOS 2025 节目顺序 77–90 摘要筛选交接

仅在 `/tmp/ai-infra-parallel-asplos` 工作；没有修改仓库、提交或推送。79、87 已在基线中筛选，本批跳过。新增 12 份完整原始摘要、10 份代表 PDF（182 页）；另保留 BitSpec 替代 PDF 和 CtXnL 关联预印本，不重复计数。共 27 份原始响应，含 3 份 ACM 403 响应。实际查看 12 张摘要／身份页，正文阅读新增为 0。

机器交接文件：`merge-ready.json`。全部原始字节与抽取文件带 SHA-256；允许根代理移入仓库时改路径，不能改原始字节。

| 顺序 | 论文 | 决策 | 对书的关系及边界 |
|---|---|---|---|
| 77 | Vela: A Virtualized LLM Training System with GPU Direct and RoCE | 候选待读 | KVM、SR-IOV 与 GPU Direct RoCE 的生产训练路径适合作为虚拟化边界案例；须读正文核对网络拓扑、模型切分和理想吞吐分母，摘要中的约 80% 不能当作 MFU。 |
| 78 | Forecasting GPU Performance for Deep Learning Training and Inference | 候选待读 | NeuSight 将硬件约束与 tile 级学习预测组合，适合补充纸笔下界何时需要实测校准；先核对训练样本、GPU 与库版本，再决定是否采用，摘要误差不是通用精度保证。 |
| 80 | PartIR: Composing SPMD Partitioning Strategies for Machine Learning | 候选待读 | PartIR 把模型与分片策略分开并允许渐进组合，适合连接矩阵切分、通信代价与编译器；须核对论文 API、公开实现和运行时集成之间的差距。 |
| 81 | Using Analytical Performance/Power Model and Fine-Grained DVFS to Enhance AI Accelerator Energy Efficiency | 候选待读 | 算子级 DVFS 与性能／功耗建模直接关联资源瓶颈，候选用于说明降频是否延长关键路径；仅摘要可知针对昇腾的毫秒级调频，不能推广成任意 GPU 能力或整机能耗结论。 |
| 82 | Early Termination for Hyperdimensional Computing Using Inferential Statistics | 不采用 | 面向 HDC 分类器的统计早停，模型、误差结构与本书 Transformer 推理主线不同；不作为推测解码或 reasoning 提前停止的直接依据。 |
| 83 | Saving Energy with Per-Variable Bitwidth Speculation | 不采用 | BitSpec 针对小型处理器整数变量的位宽推测与纠错执行，不能等同 LLM 权重量化；保留筛选记录，避免编译章节扩成通用嵌入式处理器综述。 |
| 84 | ShadowLoad: Injecting State into Hardware Prefetchers | 不采用 | 研究 CPU 硬件预取器侧信道，超出本书 Agent 沙箱容量、启动和调度主线；不以此补充攻击实现细节。 |
| 85 | Skia: Exposing Shadow Branches | 不采用 | Skia 面向服务器 CPU 前端和分支目标缓冲，不直接解释 AI 算子或模型服务的关键瓶颈；保留记录，不增加通用 CPU 微架构支线。 |
| 86 | Hierarchical prefetching: A software-hardware instruction prefetcher for server applications | 不采用 | 服务器指令预取与通用代码工作集优化，缺少本书模型资源计算的直接落点；不因涉及数据中心就加入 AI 网络或推理章节。 |
| 88 | Formalising CXL Cache Coherence | 背景备查 | 可用于核对 CXL.cache 一致性语义与协议证明边界，不能当作 CXL.mem 内存池带宽或 KV 共享性能的证据；无需展开数万条证明。 |
| 89 | CTXNL: A Software-Hardware Co-designed Solution for Efficient CXL-Based Transaction Processing | 背景备查 | 事务处理的选择性一致性说明一致性语义也有代价；目前不能把 OLTP 吞吐提升迁移为 KV 池收益，需独立核对 AI 对象的读写及可见性要求。 |
| 90 | ByteFS: System Support for (CXL-based) Memory-Semantic Solid-State Drives | 背景备查 | 字节／块双接口、主机及设备缓存协调可供多级缓存写放大背景参考；ByteFS 的可编程 SSD 与仿真结果不等于真实 CXL KV 池实现。 |

版本与完整性：

- Vela：IBM 标题多了 and，但 DOI 和 25 位作者相同；摘要可计，PDF 403，正文未读。
- NeuSight：HTML 摘要与 v3 PDF 摘要文字不同；双方保留，本批摘要记录指定为 HTML。
- PartIR：v4 PDF 36 页，正式出版页码只有 17 页，不能以篇幅猜测同版；HTML 包含准确正式 DOI，PDF 作者名单列齐 17 人。
- BitSpec：作者和机构两份 PDF 摘要都写平均节能 9.9%，不是把搜索中 Zenodo 的 14.4% 直接搬过来。两份字节不同，只计 1 篇。
- Skia：从 Princeton 实验室找到正式 DOI 的 PDF，正文编码有连字和约等号抽取错误；摘要采用机构 HTML，图像检查核对了原文。
- Hierarchical Prefetching：17 页文件包含机构封面；摘要在物理第 2 页，正式页码 529。
- CtXnL：作者页面提供正式标题、9 位作者及 DOI，摘要可计。关联 arXiv v2 改了标题，HTML 漏列 Yijin Guan，PDF 列齐 9 人且不含正式 DOI；保留为关联版本，暂不算代表 PDF。
- ByteFS：HTML 有未展开的 TeX 宏，PDF 已正确显示 ByteFS；保留两种原文，摘要出处明确。

下一步优先读正文的候选为 Vela、NeuSight、PartIR、昇腾 DVFS。其余项目没有因为标题出现 CXL、数据中心或量化就扩进主线。
