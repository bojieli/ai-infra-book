# ASPLOS 2025：出版目录核对

官方主日程的 **184 个条目**均已按原页面 DOI 匹配出版方提交给 Crossref 的元数据，见 [manifest.json](manifest.json)。这批出版元数据没有摘要。后续已另行归档 34 份公开 PDF、筛读 35 篇原始摘要，其中六篇有声明范围的正文阅读；其余 149 篇摘要与更多公开正文待补。

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

[selected-sources.json](selected-sources.json) 另存 71 份响应：4 次 OpenAlex 批量查询覆盖 184 个日程 DOI，其他为公开稿、作者页、单条元数据、查找失败响应及 Faiss 官方文档。OpenAlex 仅作位置发现，不将其聚合摘要或可用位置当作完整原始资料。34 份有效 PDF 均有页数、原件哈希、可搜索文本和首页身份核对；[public-location-map.json](public-location-map.json) 保存回到位置查询的路径。四份非 200 响应，以及一份以 200 返回的实验室首页均未计入 PDF。

[35 篇摘要](public-abstracts.json)直接来自作者 arXiv 页面、作者／机构论文 PDF 或作者摘要页，逐项保存来源及提取范围。作者稿可能晚于正式出版，HAL 的封面页与正文页也分开计；不混用卷页码。具体取舍见[阅读记录](../../../../research/2026-infra-survey/reading-asplos-2025.md)，其中 IKS、FSMoE 作者 v1 的物理页 1–13 各已读，相关图已查看；其余 PDF 主要完成身份与摘要核对。页级范围见 [IKS](iks-reading.json) 与 [FSMoE](fsmoe-reading.json)，历史模型和数值疑点留在阅读记录。

核验：`python research/2026-infra-survey/verify_asplos2025_public.py`。它核对已有来源、摘要提取、页级阅读和取舍记录，不证明全部论文集已归档或全文已读。

2026-09-09 新增 15 份响应：11 份代表 PDF／180 页、两份 arXiv 摘要与版本页、两份未取得论文的响应。新增完整摘要为日程 11、12、13、18、20、21、22、27、28、34、35；首 session 及其他编号仍有缺口。第 27 项[昇腾算子分析](ascend-components-reading.json)的物理页 2–14 已选读，五页公式／图表实际查看。其框架接入与教学计算见[专题记录](../../../../research/2026-infra-survey/reading-asplos-2025.md)。QRCC 的卷号冲突、DarwinGame 的较晚预印本与占位出版字段留在逐篇版本备注，不修改原件。

Earth+ 的 2024 作者 v1 有六位作者，含 Ranveer Chandra；已归档正式 DOI 的 Crossref 记录列五位，未列该名字。题名与其余五位作者一致，按较早作者版本归档；此处仅记录元数据差异，不推断正式 PDF 的作者名单已经变更。

2026-09-09 继续按问题选读 [Diffuse](diffuse-reading.json) 物理页 2–13 与 [CXLfork](cxlfork-reading.json) 物理页 2–14，共 25 页和八张实际查看图页。分别补充片内→跨卡融合的依赖，以及 CPU 环境恢复的驻留与共享读取；未新增摘要／PDF，不把其余参考文献计为已读。

2026-09-09 补读 [DarwinGame](darwingame-reading.json) 物理页 1–13 与七张实际查看图页。作者工件的占位入口、评分和决赛差距留在[对照归档](../../../framework-history/2026-09-09/tuning-measurement/README.md)；仅补测量条件，论文原件、摘要和 PDF 数量不变。
