# MICRO 2025 归档与阅读

2026-09-08：官方主日程的 **123 篇论文均已匹配出版 DOI**，116 项标题规范化匹配，7 项改题和作者字段差异逐项核对。取得 **13 份代表公开稿／208 页**，另保留一份 15 页早期版本；已筛读 13 篇完整原始摘要，5 篇正文候选、4 篇备查、4 篇排除，110 篇摘要待补。首轮五篇候选中，StreamTensor 物理页 3–14 与 LLM.265 页 4–13 已选读，共 22 页；两项推导接入既有实验，另外三篇候选正文待核。没有采用论文的硬件性能比值。

- [日程与出版清单](manifest.json)：保留原日程顺序、两种题名、作者、页码和阅读状态。
- [七项题名与作者差异](title-variants.json)：Stratum、Sonar、GateBleed、ORCHES、OneAdapt、OmniSim，以及 RowHammer 防御侧信道论文。
- [26 份响应原件](sources.json)：24 份成功、2 份 HTTP 403；[另一次 TLS 失败](fetch-supplement.json)没有取得响应正文，不算下载。
- [公开副本线索](public-location-map.json)：四次查询返回 66 条 OpenAlex 记录，覆盖 65 个不同 DOI，其中一个 DOI 对应两条记录；其余 58 个 DOI 的定位元数据缺失，不表示没有公开稿。该索引不充当原始摘要。
- [正文选读](../../../../research/2026-infra-survey/reading-micro-2025.md)：[StreamTensor](streamtensor-reading.json)、[LLM.265](llm265-reading.json)，含页级原文和六张实际查看的页图；另有[两份官方能力表快照](selected-sources.json)。
- [13 篇摘要证据](public-abstracts.json)：保存原文范围、PDF 版本、两份机构重复摘要和七张实际查看的身份／摘要页图。
- [阅读与取舍](../../../../research/2026-infra-survey/reading-micro-2025.md)、[筛选表](../../../../research/2026-infra-survey/screening-micro-2025.tsv)和[独立校验](../../../../research/2026-infra-survey/micro2025-audit.json)。

Crossref 排序查询返回 300 项，其中 123 项属于本届 DOI 前缀，正好匹配主日程；查询没有遍历全部搜索结果，不能单独证明取得正式整卷。整卷 PDF 和 LongSight 出版方 PDF 均返回 403，原响应保留；此前卷主页的 403、卷身份查询的 429 留在原发现目录，不重复计入本轮响应。

GPU 核心分析论文的早期 arXiv v1 题名为 *Analyzing Modern NVIDIA GPU cores*；本轮另取得 UPC 机构稿 *Dissecting and Modeling the Architecture of Modern GPU Cores*，以该稿作代表。两份文件共 31 页，只计一篇摘要；早期稿只核书目信息。Stratum 和 LLM.265 的机构完整摘要与 PDF 对照，也不重复计篇。LLM.265 的 MICRO 2025 论文与检索中出现的 IEEE Micro 2026 短文分开，后者未计入本届。

Stratum 的摘要跨左右栏，抽取时剔除夹入的版权脚注；Label Propagation 论文物理第 1 页是作者页，摘要在第 2 页。Flexing RISC-V 的 arXiv 边栏写 2025-10-28，题页写 10 月 29 日，均保留；量子泄漏推断的公开 v1 也晚于会议日期。StreamTensor 的摘要止于 ACM 引用格式之前。

LongSight 的作者列表页有两处需要区分：Martínez 页面少列 Jinkwon Kim，附近几篇不同题名复用了 LongSight DOI；Alian 新站的 LongSight 条目列五位作者并指向同一出版 PDF。旧站存在证书主机名不匹配，按 HTML 明示跳转到新站后只核相应条目，没有绕过证书校验或把跳转页记为论文。

维护：`python references/reconcile_micro2025.py` 使用本地缓存重新匹配并保留阅读状态；`python research/2026-infra-survey/verify_micro2025.py` 检查来源、身份、摘要边界与计数。本批没有运行论文代码、模型或硬件实验。
