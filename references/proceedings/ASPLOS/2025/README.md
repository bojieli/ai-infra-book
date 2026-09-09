# ASPLOS 2025：出版目录核对

官方主日程的 **184 个条目**均已按原页面 DOI 匹配出版方提交给 Crossref 的元数据，见 [manifest.json](manifest.json)。这批出版元数据没有摘要。后续已另行归档 90 份代表公开 PDF／1555 页，另存 PipeLLM 作者版本及批次内的替代／相关版本；筛读 98 篇原始摘要，其中十七篇有声明范围的正文阅读；其余 86 篇摘要与更多公开正文待补。

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

当前统一入口为 [reading-coverage.json](reading-coverage.json)：按 184 个正式日程 DOI 合并原清单与后续三批阅读记录，覆盖 **108 篇完整摘要、100 份代表 PDF／1,706 页、21 篇声明正文范围**，仍缺 76 篇摘要。它是由原始记录生成的总索引；下文原清单的 98／90／17 及逐批数字保留为阶段历史，不与新批次重复相加。

新增八篇来自 [COMET／POD／TAPAS](serving-113-117/README.md)及[编译器与测试筛选](screening-111-123/README.md)。其中 COMET、POD、TAPAS、Ratte 合计选读 30 页，只补现有量化、混合批处理、资源约束和 Agent 优化实验的判断条件，其余四篇归档备查。MetaMut 属于正式 2024 卷、2025 日程，保留原始年份。维护命令为 `python research/2026-infra-survey/verify_asplos2025_coverage.py`；该检查复核原清单及后续批次的来源、身份与页级证据，再生成统一索引。它不代表全部正文已读。

[selected-sources.json](selected-sources.json) 另存 177 份响应：4 次 OpenAlex 批量查询覆盖 184 个日程 DOI，其他为公开稿、作者页、单条元数据、查找失败响应及 Faiss 官方文档。OpenAlex 仅作位置发现，不将其聚合摘要或可用位置当作完整原始资料。90 份代表 PDF 均有页数、原件哈希、可搜索文本和首页身份核对；[public-location-map.json](public-location-map.json) 保存回到位置查询的路径。十六份非 200 响应，以及返回实验室首页／非论文页面的响应均未计入 PDF。

[98 篇摘要](public-abstracts.json)直接来自作者 arXiv 页面、作者／机构论文 PDF 或作者摘要页，逐项保存来源及提取范围。作者稿可能晚于正式出版，HAL 的封面页与正文页也分开计；不混用卷页码。具体取舍见[阅读记录](../../../../research/2026-infra-survey/reading-asplos-2025.md)，其中 IKS、FSMoE 作者 v1 的物理页 1–13 各已读，相关图已查看；其余 PDF 主要完成身份与摘要核对。页级范围见 [IKS](iks-reading.json) 与 [FSMoE](fsmoe-reading.json)，历史模型和数值疑点留在阅读记录。

核验：`python research/2026-infra-survey/verify_asplos2025_public.py`。它核对已有来源、摘要提取、页级阅读和取舍记录，不证明全部论文集已归档或全文已读。

2026-09-09 新增 15 份响应：11 份代表 PDF／180 页、两份 arXiv 摘要与版本页、两份未取得论文的响应。新增完整摘要为日程 11、12、13、18、20、21、22、27、28、34、35；首 session 及其他编号仍有缺口。第 27 项[昇腾算子分析](ascend-components-reading.json)的物理页 2–14 已选读，五页公式／图表实际查看。其框架接入与教学计算见[专题记录](../../../../research/2026-infra-survey/reading-asplos-2025.md)。QRCC 的卷号冲突、DarwinGame 的较晚预印本与占位出版字段留在逐篇版本备注，不修改原件。

Earth+ 的 2024 作者 v1 有六位作者，含 Ranveer Chandra；已归档正式 DOI 的 Crossref 记录列五位，未列该名字。题名与其余五位作者一致，按较早作者版本归档；此处仅记录元数据差异，不推断正式 PDF 的作者名单已经变更。

2026-09-09 继续按问题选读 [Diffuse](diffuse-reading.json) 物理页 2–13 与 [CXLfork](cxlfork-reading.json) 物理页 2–14，共 25 页和八张实际查看图页。分别补充片内→跨卡融合的依赖，以及 CPU 环境恢复的驻留与共享读取；未新增摘要／PDF，不把其余参考文献计为已读。

2026-09-09 补读 [DarwinGame](darwingame-reading.json) 物理页 1–13 与七张实际查看图页。作者工件的占位入口、评分和决赛差距留在[对照归档](../../../framework-history/2026-09-09/tuning-measurement/README.md)；仅补测量条件，论文原件、摘要和 PDF 数量不变。

2026-09-09 增加[十六份响应](middle-screening-notes.json)，其中十三份有效 PDF／260 页及十三篇完整摘要；另补 [PICACHU](picachu-reading.json) 的十一页正文范围与五张图页。该批完成时共 47 份 PDF／811 页、48 篇摘要、七篇选读范围。新 PDF 中 DaCapo 作者版的 72 页包含附录，Mint 保留占位 DOI，RTL 去重属于正式 2024 卷；逐篇版本备注不混入最终出版页数。本轮其余新 PDF 只完成身份与完整摘要阅读。

2026-09-09 继续选读 [Apophenia](apophenia-reading.json) 物理页 2–12、16–17，六页图像已查看；当前八篇有声明正文范围，PDF／摘要数量不变。工件及固定框架路径收在[独立归档](../../../framework-history/2026-09-09/trace-identification/README.md)，保留原始响应和精确读取范围。

2026-09-09 补读 [PipeLLM](pipellm-reading.json) 的[十五页正式格式作者稿](pipellm/README.md)，物理页 1–13 与六页图像已读。旧十四页 v1 保留为代表副本，新增版本不重复计算论文或摘要；当前九篇有声明正文范围。作者工件和 vLLM 抢占／KV connector 的差距接入已有主机搬运案例，未运行工件。

2026-09-09 补读 [StreamGrid](streamgrid-reading.json) 十一页与 [ARC](arc-reading.json) 十二页，九张正文图页实际查看。两篇均转为备查：分别保留算法质量与缓冲约束、原子争用与额外指令的判断，不增加主大纲内容。当前十一篇有声明正文范围，并不表示十一篇全文读完。

同批[十四份响应](storage-screening-notes.json)补八份代表 PDF／130 页、十篇完整摘要；累计 55 份代表 PDF／941 页、58 篇摘要，尚缺 126 篇摘要。另有一次 TLS 传输失败，单列而不计为响应。IBM／SNU 机构摘要保留精确 HTML 元素；两个跨栏 PDF 摘要已查看首页图像。第 57／59／62 项保留缺口，未以搜索摘要或 2026 Top Picks 版本替代正式论文。

2026-09-09 增加[十六份响应](heterogeneous-screening-notes.json)，含十份代表 PDF／169 页及十篇完整摘要；第 65／66 项仍缺完整摘要，另留一次已由作者备用链接解决的传输错误。NACHO 的机构封面与实际论文页分开核对，FlexSP／Spindle 保留 arXiv v3 日期而不冒称出版副本。三页摘要图像已查看。累计 65 份代表 PDF／1110 页、68 篇完整摘要，尚缺 116 篇。

同批选读 [Helix](helix-reading.json) 物理页 1–15 与五页图像，现共十二篇有声明正文范围。其异构请求路径与 vLLM 静态 PP 的差距见[专题笔记](../../../framework-history/2026-09-09/heterogeneous-pipelines/NOTES.md)；只补现有第 6 章实验的变体。llm.npu、FlexSP、Spindle 留作候选待读，未据摘要采用性能结论。

2026-09-09 再选读 [FlexSP](flexsp-reading.json) 物理页 2–13、17 和 [llm.npu](llm-npu-reading.json) 物理页 2–15，合计 27 页及 14 张已查看图页，现共十四篇有声明正文范围，摘要与 PDF 数量不变。原始摘要筛选判断保留为历史，当前取舍按正文更新。固定分支、MLLM v1／2026 AOT 和十二个源码／文档范围见[专题笔记](../../../framework-history/2026-09-09/sequence-and-npu/NOTES.md)。Spindle 仍待本阶段后的独立正文核对；本轮未运行工件。

2026-09-09 并行选读 [Spindle](spindle-reading.json) 物理页 2–13、18–20，八张图页已查看；当前十五篇有声明正文范围，摘要数量不变。固定研究分支的五个读取范围与可手算的分支／重配对照见[专题笔记](../../../framework-history/2026-09-09/spindle-wavefront/NOTES.md)，仅接 10.3.1／实验 10-5 的选做变体。

2026-09-09 合并第 77–110 项中的两批交接材料：30 篇完整摘要、25 份代表 PDF／445 页。原始文件继续位于 [原交接目录](pending-077-110/README.md)，不因目录名含 pending 而重复下载或计数。[身份核验](pending-077-110/identity-audit.json)保留题名变体、完整作者和 DOI 的证据；93、96、98 仅以作者版本题名与完整作者关联，未补造原文没有的 DOI。另存一次连接失败，未计入 60 个新增 HTTP 响应。

新增选读范围为 NeuSight 物理页 2–14（沿用已核实并行阅读范围）和 PartIR 物理页 3–5（主任务新读）；分别见[预测校准](../../../framework-history/2026-09-09/neusight-calibration/NOTES.md)与[分片策略](../../../framework-history/2026-09-09/partir-shardy/NOTES.md)。摘要与代表 PDF 的数量不等于全文完成数量，PartIR 剩余方法、评估和证明仍未计入已读。

第 123／128 项的[缺口补查](screening-111-128/README.md)新增两篇完整摘要、两份 PDF／31 页，均归档不采用，不增加正文选读范围。
