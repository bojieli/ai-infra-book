# MICRO 2024 归档与阅读

2026-09-09 更新：按 DOI 去重后的[统一覆盖](reading-coverage.json)现为 **84 篇完整摘要、72 份代表 PDF／1,106 个物理页、4 篇声明正文选读范围**，还有 29 篇摘要缺口。[第九批](parallel-abstracts-ninth/NOTES.md)新增 4 篇摘要、2 份 PDF／31 页，正文新增 0；本批首页视读由阅读代理完成，主代理复核摘要文本与归档证据。另有 [vTrain](vtrain-body-reading/NOTES.md) 新增物理页 4–7 的正文选读与第 7 页视读，摘要和 PDF 不重复计数。以下 2026-09-08 数字保留为原始归档快照，不代表当前累计。

2026-09-08：原始日程提取的 123 项已分成 **113 篇正式论文与 10 个海报／博士生论坛活动**。113 篇均匹配出版 DOI：101 项标题规范化匹配，12 项题名和作者差异逐项复核；另分出出版元数据中的 11 项前后附页。原日程序号保留，不重新编号。

已取得 **39 份代表公开稿、602 个 PDF 页面**，其中 38 份为本目录下载，SN40L 的 14 页复用主参考库。另读 Stellar、LUCIE 的机构原始完整摘要，共 **41 篇完整摘要**：Mess 纳入既有算例、15 篇正文候选、15 篇备查、10 篇排除；余下 72 篇摘要尚待补。Mess 物理页 3–6 已选读，其余论文的身份／摘要核对不计为正文阅读。

- [日程与出版清单](manifest.json)：保留原题、出版题、作者、页码及读取状态。
- [12 项题名差异](title-variants.json)：包含日程自身将题名续文放进作者字段，以及改题、拼写和作者版本差异。
- [53 份请求原件](sources.json)：49 份成功响应、4 份失败；成功响应中含一份同名但属于 EuroSys 的 Trinity，单独注明且不计入本届 PDF／摘要数量。复用稿不记作新下载。
- [41 篇摘要证据](public-abstracts.json)：原文字符范围、来源、版本、哈希与逐项取舍；13 张实际查看的身份页图只证明相应范围。
- [新增 26 篇摘要](expanded-abstracts.json)：25 份匹配 PDF／381 页及 LUCIE 机构摘要。新增 7 篇正文候选、10 篇备查、9 篇排除；未增加正文选读或大纲内容。
- [公开副本线索](public-location-map.json)：三份 OpenAlex 原始响应覆盖 113 个 DOI，仅作定位线索，不充当原始摘要或全文证据。
- [Mess 正文记录](mess-reading.json)：4 页完整选读文本、表 I／图 3 实际查看范围及未采用的数字。
- [阅读取舍](../../../../research/2026-infra-survey/reading-micro-2024.md)与[独立校验](../../../../research/2026-infra-survey/micro2024-audit.json)。

Crossref 排序查询返回 250 项，其中 124 项属于本届 DOI 前缀，支持 113 篇日程论文及 11 项附页的对应；该查询不是正式整卷 API，不能据此声称取得了整卷全文。卷身份请求返回 429；Stellar 和 FuseMax 的两条旧 PDF 路径返回 404。FuseMax 改用 arXiv v3，Stellar 改用作者实验室完整摘要，原失败响应保留，不反复请求同一路径。

扩展筛读中，旧 IACOMA 论文列表返回 404；AdapTiV 实验室公告只核对了题名，尚无完整摘要。Mosaic 的作者 PDF 与机构完整摘要相互核对，同一篇只计一次。Trinity 最初取得 EuroSys 数据存储论文，已另取正确的 MICRO FHE 加速器稿；两份原件分别保留。

公开稿版本按原件记录：Fine-Grained Program Versioning 的 URL 含 2025，但 PDF 标明 MICRO 2024；Self-Managing DRAM 保存 arXiv v9（2025-08-06），出版元数据中的第六项 ETH Zurich 是机构，PDF 实际列五位作者。SOFA 的出版记录写 Qinze Yang，公开 v1 写 Qize Yang，分别保留。RAHP 首页是机构封面，摘要在物理第 2 页。HgPCN 为会后公开的 2025-01-14 v1，不改写会议年份。

Neu10 保存 MICRO 2024 原论文的 arXiv v3，不与 2025 IEEE Micro 的 Top Picks 短文混淆。SN40L 复用 v2，其作者表和早期日程的两项名字不同；按实际版本保留。日程中的 FlashLLM 改题为 Cambricon-LLM，不与其他同名软件论文混为一条。Flag-Proxy 和 Duplex 的完整题名续文原本落在日程作者字段，已与出版记录及首页核对。

维护：`python references/reconcile_micro2024.py` 在本地缓存上重新匹配并保留阅读范围；`python research/2026-infra-survey/verify_micro2024.py` 检查来源、抽取、计数与算例。没有运行下载源码、模型或硬件 benchmark。Mess 仅深化已有 1.3.3／实验 1-4／图 1-3 与 4.3.3；没有新增小节或实验。
