# ISCA 2024：目录与公开稿

2026-09-08 将官方日程的 **87 个论文条目**匹配至不同出版 DOI：[清单](manifest.json)。其中 70 项经标题规范化匹配，17 项有标题改写、产品标记或作者记录差异，逐项保留在[标题与作者核对](title-variants.json)。原始日程第 54 项本身连写两个标题，未将其拆成两篇；出版作者字段的个别合并／顺序差异也保留原值。

最初四次响应中，一次单 DOI 查询返回 429，ISBN 查询只取得整卷元数据；容器标题查询的前 1,000 个排序结果中有 98 项属于此 DOI 前缀。对照日程，87 项为论文，另 11 项为前后附页。这说明覆盖了已归档日程，不说明排序查询覆盖全部数据库记录；查询未提供论文摘要。

目前保存 **70 份公开稿、1,081 个物理页面**：原有 [GhOST](isca24-ghost-author-pdf.pdf) 及[公开稿清单中的 69 篇](public-manifest.json)。其中 Splitwise 复用仓库已有 PDF，不重复下载。77 篇完整原始摘要已筛选（70 篇来自公开 PDF，另 7 篇来自机构原始 HTML／JSON），取舍见[阅读记录](../../../../research/2026-infra-survey/reading-isca-2024.md)；Orojenesis 的物理页 1–14 已选读，图 18–22 已查看；MAD-Max 物理页 5–8 已选读，图 7–9 和表 I–III 已查看；FEATHER 物理页 2–13 已选读，相关图表范围见[记录](feather-reading.json)。其余 **10 篇完整摘要**及更多公开稿仍待获取，整届归档与正文阅读尚未完成。

[响应记录](selected-sources.json)保留原件与哈希，包含一次 429 和两次 404。OpenAlex 的 87 项查询只用于位置发现；随后通过作者、机构及 arXiv 取得更多公开稿，前 70 篇摘要阅读依据 PDF 本身；新增 7 篇的机构原始记录与抽取位置见[摘要证明](institutional-abstracts.json)。机构封面计入物理页数，作者版本保留修订号，不假定与出版稿逐页相同。

LLMCompass 当前归档的是 2023 年 arXiv v1，题为 *A Hardware Evaluation Framework for Large Language Model Inference*；[Princeton 出版页](isca24-llmcompass-institution.html)用于核对其会议身份，不能把 14 页早稿说成 17 页正式稿。ALISA 与 PID-Comm 也保留各自早稿；PID-Comm 的 PDF 摘要与搜索摘要报告的速度不同，本轮没有采用速度数字。Orojenesis 的旧 MIT 链接返回 404，改用[作者列出的公开稿](isca24-orojenesis-author-index.html)；其原文问题及选读范围见[记录](orojenesis-reading.json)。

Princeton 的首次 PDF 请求连接中断，没有取得 HTTP 响应体，未计为一份 PDF 或 HTTP 失败响应；后续使用 arXiv 公开版。一次临时采集器的元数据覆盖遗漏了 Orojenesis 响应行，已重新请求并确认 PDF 逐字节相同后恢复记录；其时间戳明确记为这次复核。

只读本地快照的再生成：`python references/reconcile_isca2024.py`。它按标题和人工确认的身份对照匹配，保留已有阅读字段，不依赖 DOI 序号与日程序号恰好相邻这一现象。验证入口为 `research/2026-infra-survey/verify_isca2024.py`。

新增 16 篇的[筛选批次记录](screening-batch-2026-09-08.json)保存摘要范围、七次未收到响应的连接失败及其成功重试，以及四张首页的摘要边界检查。新增公开稿共 249 页，仅计完整摘要筛读。Atomique 保存的是会后 2024 年 11 月的 arXiv v3；QuTracer 为 NSF 托管的 arXiv v2；Constable、ElasticRec 各保留 v1。大学托管的 GreenSKU 论文页脚下载日期不作为出版日期。该批次四篇候选仍需正文核对，尚未新增提纲内容。

[架构与建模批次](screening-batch-models-2026-09-08.json)新增 17 份公开稿／259 页，均已筛读完整摘要。MAD-Max arXiv v3 的[选读记录](madmax-reading.json)仅声明物理页 5–8，未运行模拟器或验证作者性能数据。NeuraChip 保存 arXiv v3，MegIS 保存 v1；AMD 论文公开首页的 13 个作者名与出版元数据的 12 条记录存在合并问题，已单列说明。

[本次补充批次](screening-batch-remainder-2026-09-08.json)新增 19 份公开稿／299 页和完整摘要筛读，12 篇备查、7 篇不纳入；未增加正文选读或提纲内容。六张页面图核对封面、作者及双栏摘要范围，其中 Tartan 的摘要在物理第 2 页。其 ACM 封面所列 2025 发布日期、2026 下载日期与 ISCA 2024 会议身份分别保留，未据封面改变会议年份。纠错 PiM 保存 arXiv v2，DRAMScope、BlissCam 保存 v1；公开版与正式稿的页数不混用。该批结束时仍有 17 个日程条目缺完整原始摘要及公开正文。

另选读已有 FEATHER 公开稿的物理页 2–13，重点区分容量／总流量、bank 服务与前后算子布局。四张页面图和已有 CUDA 13.2.1 文档的选读范围保存于[读取记录](feather-reading.json)。三篇重点论文累计声明 30 个物理页的正文范围；不是整届全文阅读。教学计数接入第 4、5 章，未执行作者代码或采用原文性能倍率。

本轮通过机构出版页及 NVA 原始 JSON 新增 7 篇完整摘要筛选：3 篇排除、3 篇备查、AIO 保留正文候选。公开 PDF 仍为 70 份／1,081 页，正文选读仍为 3 篇／30 个声明页面；机构摘要未计作 PDF。DS-GL 的机构早题名、AIO 的作者姓名展开及不同日期字段、API 空壳和失败响应均见[补查记录](closing/README.md)。另 10 篇摘要继续保留缺口；本轮未增加提纲、实验或图号。
