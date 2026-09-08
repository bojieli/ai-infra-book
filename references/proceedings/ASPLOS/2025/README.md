# ASPLOS 2025：出版目录核对

官方主日程的 **184 个条目**均已按原页面 DOI 匹配出版方提交给 Crossref 的元数据，见 [manifest.json](manifest.json)。这批出版元数据没有摘要。后续已另行归档 23 份公开 PDF、筛读 24 篇原始摘要，其中两篇重点正文已读；其余 160 篇摘要与更多公开正文待补。

| 日程对应的正式卷 | 匹配条目 | 出版元数据中的日期 |
| --- | ---: | --- |
| [ASPLOS 2024 Volume 4，10.1145/3622781](volume-3622781.json) | 24 | 2024-04-27 |
| [ASPLOS 2025 Volume 1，10.1145/3669940](volume-3669940.json) | 72 | 2025-03-30 |
| [ASPLOS 2025 Volume 2，10.1145/3676641](volume-3676641.json) | 88 | 2025-03-30 |

按 presentation year 保存本目录，并在逐篇记录中单列正式卷和出版日期，不能将 184 篇全部标成 2025 出版。这 24 篇与已核 ASPLOS 2024 主日程的 193 个 DOI 不重叠；后续归档以 DOI 去重。上表日期忠实保留出版元数据，不根据演讲时间推断上线日期。

[sources.json](sources.json) 保存 8 份响应：3 个卷记录、3 个 ISBN 查询及 2 个标题查询。ISBN 查询均成功返回零条，不代表对应论文不存在；标题查询各返回 1,000 个条目，筛出与日程相符的 184 个 DOI。它们覆盖了这份日程，**不能据此证明正式卷没有其他条目**。未采用搜索结果中无关论文的标题、摘要或结论。

出版标题中的 `<scp>`／`<i>` 标签和实体需要先归一化。处理后保留 4 项真实题名差异：CIPHERMATCH 的日程重复了一个 Packing；Spectre-RSB 与 TNIC 的出版题名增加副标题；PIM Is All You Need 的出版题名将 LLM 展开为 Large Language Model。均由原日程 DOI 确认身份，不凭模糊标题匹配。

维护：`python references/reconcile_asplos2025.py` 只读取已归档数据，保留后续逐篇阅读与 PDF 状态。核对见 [metadata-audit.json](metadata-audit.json)。下一步获取本届公开摘要／作者稿与可访问出版正文，再决定重点阅读，不由题名向大纲添加技术结论。

## 公开稿与读取进度

[selected-sources.json](selected-sources.json) 另存 56 份响应：4 次 OpenAlex 批量查询覆盖 184 个日程 DOI，其他为公开稿、作者页、单条元数据、查找失败响应及 Faiss 官方文档。OpenAlex 仅作位置发现，不将其聚合摘要或可用位置当作完整原始资料。23 份有效 PDF 均有页数、原件哈希、可搜索文本和首页身份核对；[public-location-map.json](public-location-map.json) 保存回到位置查询的路径。三份失败响应未计入 PDF。

[24 篇摘要](public-abstracts.json)直接来自作者 arXiv 页面、作者／机构论文 PDF 或作者摘要页，逐项保存来源及提取范围。作者稿可能晚于正式出版，HAL 的封面页与正文页也分开计；不混用卷页码。具体取舍见[阅读记录](../../../../research/2026-infra-survey/reading-asplos-2025.md)，其中 IKS、FSMoE 作者 v1 的物理页 1–13 各已读，相关图已查看；其余 PDF 主要完成身份与摘要核对。页级范围见 [IKS](iks-reading.json) 与 [FSMoE](fsmoe-reading.json)，历史模型和数值疑点留在阅读记录。

核验：`python research/2026-infra-survey/verify_asplos2025_public.py`。它核对已有来源、摘要提取、页级阅读和取舍记录，不证明全部论文集已归档或全文已读。
