# 会议论文集归档

这部分保存逐届会议目录及公开论文全集，与按章节精选的主参考库分开索引，避免把所有下载条目都挤进正文资料表。每卷 `manifest.json` 记录 URL、获取日期、文件长度、SHA-256、页数与下载状态；MLSys 按逐篇 PDF 保存并提供 `sources.tsv`，USENIX 保存官方整卷、目录和勘误。文件下载不代表已经阅读。

- [MLSys 2024](MLSys/2024/README.md)
- [MLSys 2025](MLSys/2025/README.md)
- [MLSys 2026](MLSys/2026/README.md)

MLSys 三卷共 233 篇（37／61／135），均已保存 PDF 与可搜索文本，全部完整摘要已筛选。2024、2025、2026 年分别有两篇、五篇、六篇的重点章节已读；其余候选仍需正文比较，不是全卷全文阅读完成。[2026 阅读记录](../../research/2026-infra-survey/reading-mlsys-2026.md)保留逐项取舍，最新补读 TriInfer 的阶段调度与部署比较。

维护：`python references/archive_proceedings.py --years 2024 2025 2026`。程序按已保存文件的哈希复用完成项；运行中不要同时启动另一份相同下载任务。失败项保留原因，抽取文本失败不能记作已读。

已归档的目录快照也会复用，恢复下载不会悄悄替换当时的官方清单。2025 ReaL、2026 GriNNder／TriInfer 的文本分页符数量与 PDF 页数不一致，重新抽取结果相同；查页码时使用原 PDF 或 `pdftotext -f/-l`，不要把文本分页符下标直接当成 PDF 页码。校验记录见[阶段审计](../../research/2026-infra-survey/archive-audit.json)。

## OSDI 与 NSDI 公开整卷

| 会议 | 2024 | 2025 | 2026 |
| --- | --- | --- | --- |
| OSDI | [53 篇](OSDI/2024/README.md) | [53 篇](OSDI/2025/README.md) | [136 篇](OSDI/2026/README.md) |
| NSDI | [112 篇](NSDI/2024/README.md) | [83 篇](NSDI/2025/README.md) | [150 篇](NSDI/2026/README.md) |

六卷包含 587 篇正式论文，整卷共 11,127 个 PDF 页面；另存六份目录及官方页面所列的七份勘误。逐项比对目录标题和对应正文首页，2026 年两场 keynote 不计入论文数。OSDI 2024、2025 均已筛完 53 篇完整摘要，分别补读三篇和两篇正文相关页；见 [2024 取舍](../../research/2026-infra-survey/reading-osdi-2024.md)与 [2025 取舍](../../research/2026-infra-survey/reading-osdi-2025.md)。OSDI 2026 的 136 篇摘要也已筛完并选读三篇；NSDI 2024 已筛完 112 篇完整摘要并选读四篇的 47 页，见[本轮取舍](../../research/2026-infra-survey/reading-nsdi-2024.md)。NSDI 2025 的 83 篇完整摘要已筛完，ByteCheckpoint／AutoCCL 共 27 页已选读并与整卷核对，见[2025 取舍](../../research/2026-infra-survey/reading-nsdi-2025.md)。NSDI 2026 的 150 篇完整摘要已全部筛完，ServeGen 的 12 页和 RollPacker 的 14 页正文已选读，并与整卷逐页核对，见[2026 取舍](../../research/2026-infra-survey/reading-nsdi-2026.md)。已有按章节阅读的个别论文继续保留原记录，不把整卷下载当作全文读完。

维护：`python references/archive_usenix.py --conferences osdi24 osdi25 osdi26 nsdi24 nsdi25 nsdi26 --workers 2`；核对：`python research/2026-infra-survey/verify_usenix.py`。仅下载公开链接，不含参会者名单或注册专享 ZIP。

OSDI 2026 的整卷文本含 2,649 个分页符，而物理 PDF 为 2,620 页，校验直接按 PDF 页码抽取首页。六篇的日程／目录标题与正文有小差异，另有一篇标题的装饰字母 D 未被文本抽取；原题和核对说明均保存在清单及[USENIX 校验报告](../../research/2026-infra-survey/usenix-archive-audit.json)。

筛选、重点章节阅读与大纲取舍记录见[长期调研](../../research/2026-infra-survey/README.md)。ASPLOS、ISCA、MICRO 的 2024–2026 [入口核对](discovery/2026-09-08/README.md)已保存官方日程、ASPLOS 2024 摘要集和逐篇 DOI 线索；当前仍未完成对应论文集归档及阅读。日程提取数与正式论文数分开，不以访问失败响应充作论文。

[ASPLOS 2024](ASPLOS/2024/README.md)已将 193 个官方摘要与日程 DOI 一一匹配，193 篇完整摘要均已筛选，并选读 Korch 作者版本物理页 1–13；其余候选正文待核。[目录复核](catalog-review/2026-09-08/README.md)修正 16 个获奖标签和一个空白时段，并将 ASPLOS 2026 的 168 个详细条目匹配至不同正式 DOI，保留页面顶部 167 的差异。另归档两份作者 PDF 用于出版信息核对；不将其下载计入重点章节阅读。

[ASPLOS 2025 出版目录核对](ASPLOS/2025/README.md)将官方主日程的 184 个 DOI 全部匹配到出版元数据，包含 24 个 ASPLOS 2024 Volume 4 条目。两份查询覆盖本日程，不能证明正式卷全集；匹配结果没有摘要，另由作者／机构来源取得 23 份公开稿，筛读 24 篇原始摘要并选读 IKS 的 13 页正文；其余 160 篇摘要及更多正文继续归档。

[ISCA 2024](ISCA/2024/README.md)已将日程的 87 项匹配至出版 DOI，另分出 11 项前后附页。70 项标题规范化匹配，17 项保留人工核对的题名与作者差异；目前归档覆盖 18 份公开稿、274 页（含复用已有 Splitwise），已筛 18 篇完整原始摘要，选读 Orojenesis 物理页 1–14。另 69 篇摘要及更多公开稿仍待归档，不计作整卷已读。
