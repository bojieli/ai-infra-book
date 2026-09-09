# ASPLOS 2025：GPU 与存储六篇摘要筛选

2026-09-09。本批只处理 program order 173、174、176、177、178、179。开始时六篇均为 `abstract_read=false`、`selected_reading=null`、无代表 PDF；[开始快照](selection-snapshot.json)保留 reading-coverage 与 manifest 哈希。没有修改共享索引、大纲或案例，没有 Git 操作，没有运行第三方代码、框架或实验。

已读六份一手完整摘要，包含一份明确由官方实验室工件关联的匿名稿；归档五份代表 PDF 共 76 页，但**只核首页题名／作者／DOI（如有）与摘要，正文阅读仍为 0**。五张首页图均已目视核对。首页其余引言或图形没有作为正文证据；不能把完整 PDF 下载量计为正文阅读量。另读 Virgo v1 摘要只用于版本比较，不增加独立论文数。

## 正式身份与原件

所有正式 DOI、题名、作者均从[原始 Crossref 响应](registry-original.json)中重新提取，未只信旧索引的匹配布尔值；正式题名还与[原始会议 program](program-original.html)核对。两份原始归档的复制字节和来源位置保留在 [local-copy-provenance.json](local-copy-provenance.json)。这两份是已有档案的字节复制，不伪造新的联网采集日期。

| 序号 | 正式 DOI | 完整摘要来源 | 版本边界 |
|---|---|---|---|
| 173 Virgo | `10.1145/3676641.3716281` | arXiv HTML v2；PDF 首页复核 | 18 页 v2，首页有正式 DOI／作者 |
| 174 Towards Unified Analysis of GPU Consistency | `10.1145/3622781.3674174` | 作者公开 PDF 首页 | 16 页稿，首页有正式 DOI／作者；正式 ASPLOS 2024 Vol.4，2025 program 展示 |
| 176 Optimizing Datalog for the GPU | `10.1145/3669940.3707274` | arXiv HTML v5；PDF 首页复核 | 13 页预印本，正式版 15 页；HTML 与 PDF 作者顺序有差异，见下文 |
| 177 MaxEmbed | `10.1145/3622781.3674172` | 作者公开 PDF 首页 | 15 页稿，首页有正式 DOI／作者；正式 ASPLOS 2024 Vol.4，2025 program 展示 |
| 178 AnyKey | `10.1145/3669940.3707279` | 作者机构页面的完整 JSON-LD 摘要 | 同一对象和 citation metadata 均包含正式 DOI、题名、六位作者 |
| 179 NOR Flash I/O | `10.1145/3676641.3716272` | 官方实验室固定工件中的匿名 PDF 首页 | 14 页稿，首页无作者／DOI；正式版 15 页，禁止写成出版版摘要已逐字核验 |

本批六个 ACM landing 请求均返回 403，保留原始响应；Virgo 的 Berkeley 搜索定位链接返回 404，文件虽有 `.pdf` 后缀，实际是 146 字节错误响应，明确排除代表 PDF。最后六个 DOI endpoint 请求中，176／177 返回有效 Crossref JSON，其余四个返回 429 空体；空体和状态均保存，不循环重试。两份成功响应的 DOI、题名和作者与原始归档一致。全部请求的原始／最终 URL、UTC 时间、状态、头、长度与 SHA-256 见 `sources-*.json.results.json`，原件不改写。

## 173：Virgo——值得后续读正文，但先不采用性能数字

摘要把问题落在矩阵单元与 SIMT 核的耦合：寄存器容量和带宽限制操作粒度；将矩阵单元移到核簇层面，改变操作数／累加器访问、指令处理开销与矩阵／SIMT 并发。这里的 cluster 是**单芯片内部的 SIMT 核簇**，不是第 6 章的超节点，也不是第 7 章的数据中心集群。[arXiv v2](https://arxiv.org/abs/2408.12073v2)

与本书最直接的连接是 4.3.1“片上存储与数据复用”或 4.4.3“矩阵与向量单元的协作”。现有提纲已经讲 TMEM／累加器与供数；本候选的新增判断应是：**性能需求在什么条件下迫使我们改变计算单元边界，而不只是增加寄存器或带宽**。若正文核验支持，可用一个粒度、访问量和控制工作比较接入原小节，不新增章节或核心实验。

必须保留版本差异：v1 摘要写相对单一 core-coupled baseline，active power 最多下降 66.3%、active energy 最多下降 77.2%；v2 改为相对 Ampere-style／Hopper-style 两基线，on-chip active power 分别下降 67.3%／24.2%。不能将功率、能量、基线混在同一对比中，更不能把 style 原型写成实测 A100／H100。[v1 摘要原件](173-arxiv-v1.html)、[v2 原件](173-arxiv.html)与两个重提取摘要均保留。

摘要说明使用 synthesizable RTL，并不证明流片或产品测试。本批没有核技术节点、时钟、面积、等 MAC 预算、功耗测量方法、融合负载、完整服务收益或软件可用性；这些是下一次是否正式采用的必要正文问题。本轮只标后续正文候选，不将数字回填硬件规格表。

## 174：GPU Consistency——保留延伸，不新增正文

作者将 PTX 与 Vulkan 的一致性模型纳入 Dartagnan，目标是分析真实 GPU 程序的正确性；摘要称模型验证过程中发现原 PTX／Vulkan 模型的两个问题。它说明“跑出相同结果”与“并发语义正确”之间存在距离，适合作为 5.3.5 验证条件、5.4.5 设备侧同步的延伸阅读。[作者公开稿](https://hernanponcedeleon.github.io/pdfs/asplos2024.pdf)

但本批没有核模型版本、覆盖范围、工具约束和问题后续修订状态。不能据该摘要声称当前 CUDA/Vulkan 有相同漏洞，也不能把它当作实际 AI kernel 加速或生产运行时采用证据。现有提纲已包含同步和固定验证边界，暂不再加一段正文或实验。首页完整摘要止于 ACM Reference Format，右栏代码图没有混入摘要。

## 176：Datalog——不为“用 GPU”强接到模型编译

GPUlog 面向递归关系运算，摘要介绍 HISA 数据结构，任务包括静态分析、网络监测和社交数据分析；45 倍是摘要所述相对 CPU Soufflé 的特定 httpd points-to 分析结果。它不是深度学习模型推理／训练结果，不能改写成“GPU 相对 CPU 的普遍加速”。[arXiv v5](https://arxiv.org/abs/2311.02206v5)

本书目前不以逻辑数据库为贯穿负载；仅因出现 GPU、稀疏或编译字样就接入第 5 章，会使原主线变散。本批不采用。将来若增写 AI 工具执行中的规则推理，需要先有真实调用工作负载，再决定是否读正文。

身份差异已经显式保留：正式元数据与 PDF 首页顺序是 Sun、Shovon、Gilray、Kumar、Micinski；arXiv HTML 最后两位为 Micinski、Kumar。核验器只允许这一已观测排列，并检查 PDF 题名／作者、作者自己的 [ASPLOS 2025 出版介绍](https://kmicinski.com/modern-deduction/2025/02/12/post-2.html)确实链接此 arXiv ID。PDF 13 页、无首页 DOI，不能冒充 15 页正式排版稿。默认 pdftotext 会把首页右栏引言插在 Abstract 标题后，因此摘要取 HTML 的明确 abstract 块，未采用错误的整段截取。

## 177：MaxEmbed——容量换复制，是否少读物理页

摘要的问题是 DLRM 的 embedding 项小于 SSD 读取粒度，导致逻辑有效数据与实际页读取量不一致。既有共现项聚类使用互不相交的簇，可能限制可共同放置的组合；MaxEmbed 以额外复制改善布局，并安排在线查询处理。它是本批第二个值得后续读正文的候选。[作者公开稿](https://minhui-xie.github.io/papers/asplos24-maxembed.pdf)

建议只考虑接入 9.5.2 已有的 SSD 小块访问／写放大讨论，新增判断是：**总驻留字节增加，能否通过少读无用物理页降低查询代价**。它与第 9 章“不是只求最少副本／最小容量”的主线有关，但 DLRM 参数 embedding 与 LLM 随上下文生成的 KV 状态不同；没有直接迁移优化的证据。不要把论文中的 key-value 存储词汇等同于 attention KV。

摘要的“最多 18.7%”只保留为作者摘要主张，不用于推算本书 KV 池收益。后续正文要核访问分布、读取粒度、额外副本、更新/构建/查找成本及基线；如果这些假设与书中状态不对应，保留跨负载对照即可。先不增加新实验，也不把算法名放进提纲的特性清单。

## 178：AnyKey——不能把 KV-SSD 当成 attention KV

机构完整摘要指出，一些 KV-SSD 为 value 大于 key 的负载优化，而较大 key 会扩大元数据并降低性能；AnyKey 针对不同 key/value 尺寸改变元数据管理。该页面的 description／og:description 是截断文本，**没有把它们当完整摘要**；采用 ScholarlyArticle JSON-LD 的完整 `abstract`，同时重核同对象的 DOI、题名、六位作者。[机构原件](https://erica.scholarworks.kr/item/9e5cea29-a225-4e86-81f8-8225c8f1647e)

这可以提醒工程师核物理数据及元数据，但本批摘要没有建立具体 AI 请求、KV 状态或缓存身份结构。因此不据题名“All Workload Types”推成所有 AI 存储场景都更快，不为它增正文候选。书中已有容量／访问量／元数据区别，无须再用一个未经负载对接的 SSD 案例重复。

## 179：NOR Flash——已有一手匿名稿，仍不采用

工件稿摘要讨论 RAM 受限微控制器的 NOR 文件系统，将块级索引与磨损均衡调整到较粗的文件层，以减少扫描和更新开销。其直接任务是 NOR／FreeRTOS 文件系统，不是服务器 SSD、LLM 权重/KV 存储或本书端边云图像传输。当前主线没有必须依赖这篇论文的判断，因此不采用。[官方实验室工件](https://github.com/HIT-HSSL/NF2FS)

归档固定提交 `30b997ad3b42fb8c02f344b08ae716d119f87042` 的 README 与 PDF，分别重算 Git blob SHA-1 并匹配 GitHub tree；仅将仓库当原件来源，没有执行其中代码。README 顶部明确标同题 ASPLOS'25 论文，并把设计／评估指向 `/doc/NF2FS.pdf`。这建立了正式题名与匿名工件稿的关系，**没有补造 PDF 本身缺失的作者、DOI或出版页数**。

正式题名／作者／DOI由会议 program 和 Crossref 档案核对；所获工件稿是 14 页匿名版，正式出版页码为 1076–1090，共 15 页。作者稿摘要已读，但其与出版版摘要是否逐字相同仍未验证。记录应连同该版本限定导入，不能只留下 `abstract_read=true` 而丢掉版本备注。

## 交接与阅读证据

[reading-records.json](reading-records.json)包含六条记录、原始响应清单、摘要字符串哈希与文件哈希、PDF及首页图哈希、提取规则、作者顺序差异和未决条件。[editorial-inputs.json](editorial-inputs.json)保留对照的大纲哈希和实际读取范围。论文机制以上均限于摘要，不把搜索自动返回的引言或正文片段计为精读；也未因首页恰有代码图而增加正文阅读数。

`verify.py` 从原 HTML／JSON-LD／PDF 重新提取摘要，并重新核原始注册信息、PDF 首页身份和固定工件关系；不只信摘要字符串或记录中的身份布尔值。允许不同 Poppler 版本出现可诊断提取差异，但本版要求重提结果与归档字节相同，不静默放宽哈希。

原始 HTTP 失败、匿名版缺口与预印本差异均保留，不将失败请求记为有效 PDF，不将旧版本摘要另算一篇。统计是六篇完整一手摘要、五份完整 PDF 下载、五个首页身份/摘要范围、零页正文精读。是否把匿名工件版纳入总覆盖表，由主代理按现有规范连同版本信息决定。
