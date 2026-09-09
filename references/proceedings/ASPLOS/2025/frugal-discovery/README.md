# Frugal 寻源与 HetEC 原始摘要

本轮保存七份 HTTP 响应，四份成功、两份 ACM 403 和一份网站路径 404；地址、日期和原始字节哈希见 [sources.json](sources.json)。没有取得论文 PDF，不将名为 `frugal-acm-pdf.response` 的失败响应算成 PDF。

Frugal 的 [Shiwei Gao 作者主页](gsw.html)及 [Shaoxun Zeng 作者主页](shaoxun.html)均把论文链接指向 `10.1145/3669940.3707245`；前者按钮名为 PDF，但目标实际是出版页面。本轮该 [出版页面](frugal-acm.html)和 [PDF 请求](frugal-acm-pdf.response)都返回 403。此结论仅限本次请求，不表示所有公开来源都不可获取，更不表示论文不存在。

[Frugal 作者工件页](frugal.html)的 README 已读：其中给出构建步骤、统一实验脚本 `src/kg/scripts/bench.py`、配置入口 `exp_config.py`，以及微基准、知识图谱、推荐三个绘图 notebook。它有助于后续定位实验条件，但没有提供完整论文摘要或足以核验搬移策略、GPU 配置和性能收益的原文。本轮没有安装容器、下载数据集、运行脚本或推断“普通 GPU 可以训练任意大模型”；工件页快照也未冒称固定源码提交。

并行寻源取得 [PNNL 的 HetEC 页面](hetec.html)，完整摘要已读并按 `#abstract-head` 所在内容块提取为 [130-abstract.txt](130-abstract.txt)。题名、正式 DOI 与日程第 130 项一致。机构引文作者列表使用 et al.，不据此声称完整作者名单已经重新核验。页面显示的 2025-09-05 与所列会议日期分别保留，不推断这是论文首次发表时间。

HetEC 讨论不同量子纠错码之间的容量、数据移动和执行时间取舍；其 ancilla bus 不是本书 CPU/GPU 互连。只归档完整摘要，不扩写章节，也不计正文阅读。[screening.json](screening.json)仅有这一篇有效摘要记录，Frugal 仍保留缺口。

核验：`python research/2026-infra-survey/verify_frugal_discovery.py`。检查原始响应、失败状态、机构摘要提取、DOI 和作者主页目标，并由统一阅读索引接入第 130 项。没有增加核心实验或配图。
