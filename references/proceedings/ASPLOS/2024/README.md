# ASPLOS 2024：官方摘要与阅读状态

已将[官方日程](../../discovery/2026-09-08/asplos2024-program.html)的 193 个 DOI 条目与[官方摘要页](../../discovery/2026-09-08/asplos2024-abstracts.html)中的 193 个摘要一一匹配。当前按日程顺序完成 **193／193** 篇完整摘要筛选；Korch 作者版本已选读物理页 1–13。本届三卷 PDF 全文归档尚未完成。

[manifest.json](manifest.json)保存 DOI、原摘要标题、完整摘要、段落哈希及实际筛选状态；[逐项取舍](../../../../research/2026-infra-survey/screening-asplos-2024.tsv)与[阅读笔记](../../../../research/2026-infra-survey/reading-asplos-2024.md)记录候选、备查和排除理由。候选只是需要读正文的材料，不代表已加入大纲。

初次日程提取把 16 个获奖标签误当成全部或部分标题，现已按原始 HTML 修正，DOI 和原顺序保留；见[修正记录](../../catalog-review/2026-09-08/extraction-corrections.json)。第 7 篇 T3 的官方摘要混入图中文字，第 18 篇 WYTIWYG 的摘要含损坏的速度比符号，保留来源问题，不自行补数。

维护：`python references/reconcile_asplos.py`。程序复用已有筛选记录，重新核对原始 HTML，不下载或执行论文代码。

[Korch 作者 arXiv v1](selected/korch-arxiv-v1.pdf)来自作者出版页，related DOI 与正式日程一致；[文本](selected/korch-arxiv-v1.txt)、[页级阅读与版本差异](selected/korch-reading.json)和[响应清单](selected-sources.json)均保留。作者说明修正了正式版笔误，不将此文件视为出版卷的字节副本。当前本届正文选读 1 篇，TCCL 的失败 PDF 响应及作者源码跟读仍不计入。
