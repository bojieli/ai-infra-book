# 会议目录与出版信息核对

本阶段保存 **15 份请求响应**，详见 [sources.json](sources.json)。五份 DBLP 响应虽然为 HTTP 200，内容是浏览器验证页面；两份 ACM 为 403，一份 Crossref 为 429。它们均不能算作取得目录或论文。其余七份包括出版元数据、一次无结果查询、两份作者 PDF 和一个作者机构页面，读取范围逐项声明。

## ASPLOS 2026 的 167 与 168

[官方日程](../../discovery/2026-09-08/asplos2026-program.html)顶部写 167 unique papers，详细日程列 168 个不同标题。现在 **168 个详细条目均匹配到不同正式 DOI**，其中 159 个通过规范化标题匹配，9 个核对了题名变化与作者名单；见[完整映射](asplos2026-program-doi-map.json)。保留原页面的 167，不凭这个汇总数字删除论文；未找到官方对差异原因的解释。

| 这份日程中的匹配来源 | 篇数 | 出版元数据的日期 |
| --- | --- | --- |
| ASPLOS 2026 第一卷，`10.1145/3760250` | 20 | 2025-12-11 |
| ASPLOS 2026 第二卷，`10.1145/3779212` | 132 | 2026-03-22 |
| ASPLOS 2025 第三卷，`10.1145/3676642` | 16 | 2025-08-06 |

这是详细日程的组成，不宣称上述每卷的正式全集仅有这些条目。第二卷查询还返回三场 keynote 的出版记录，已按官方日程分开，未加进 168 篇论文。

题名变化包括 HistoRL／RhymeRL、Lambda-trim／λ-trim 和 Transforming／Reconfigurable Torus Fabrics。λ-trim 的前两名作者顺序不同；CHERI-SIMT 的作者中间名、TiNA 的 Nan／Nam 也保留差异。机构公开的 [HybridTier PDF](hybridtier-author.pdf)、[λ-trim PDF](lambda-trim-author.pdf)只读取第一页用于书目信息核对；[Google Wave 页面](wave-google.html)只核题名、作者与年份。两份 PDF 共 35 页已归档，不算 35 页已读，也不增加摘要筛选或重点章节阅读数量。

最初按 2026 出版日期检索，只得到第二卷相关记录；按 ISBN 的第一卷查询返回零结果，不能证明卷内没有论文。后续[无年份限制的查询](asplos2026-no-year-query.json)返回 1,000 条搜索结果，从中完成日程映射。该查询共有更多结果，**没有遍历整个结果集**；因此它能支持逐篇匹配，不能单独证明会议全集完整。原始响应、派生映射和哈希分别保留。

## 修正初次提取

[修正记录](extraction-corrections.json)保留 16 个 ASPLOS 2024 获奖标签错误的修改前后题名，以及 ISCA 2026 第 158 个空白时段。原始 HTML 未改，日程原顺序未重排。ISCA 2026 的有效标题条目由 173 改为 172，八份日程合计由 1,186 改为 **1,185**；这是日程条目总数，尚未逐届核验为正式论文总数。

ASPLOS 2024 的 193 个官方摘要已匹配，前 48 篇完成筛选，详见[阅读记录](../../../../research/2026-infra-survey/reading-asplos-2024.md)。本阶段没有据标题或摘要向大纲加入新的性能结论。

复核入口：`python references/reconcile_asplos.py`、`python research/2026-infra-survey/verify_catalogs.py`。来源正文、书目信息、摘要筛选和全文阅读保持独立状态。
