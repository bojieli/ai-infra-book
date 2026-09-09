# ASPLOS 2025：157、159–163 摘要筛选

本批完成 157、159、160、161、162 五篇的一手完整摘要，取得五份公开 PDF、共 78 页。只读摘要并核对首页身份，实际看了五张首页，**正文阅读 0 页**。163 Hardware Sentinel 保留原始摘要缺口，不能用转载摘要、搜索结果或 Meta 博客填充论文阅读计数。

| 节目序号 | 论文与本次版本 | 摘要理解与 AI Infra 取舍 |
| --- | --- | --- |
| 157 | [Toleo](https://arxiv.org/abs/2410.12749v1)，2024-10-16 arXiv v1，16 页 | freshness 指防止旧内存值被重放；以可信 smart memory 与 CXL IDE 保存版本元数据，避免 Merkle tree 的规模开销，并压缩版本信息。摘要的 168 GB 设备保护 28 TB 内存池、240 倍压缩是该设计的主张，不是一般 CXL 的容量或性能保证。可留作机密计算/内存池背景，当前不选正文；不能把 freshness 误写成 KV cache 命中或模型结果更新。 |
| 159 | [Contract Shadow Logic](https://arxiv.org/abs/2407.12232v1)，2024-07-17 arXiv v1，15 页 | 以软件—硬件 contract 验证 OoO 处理器的投机执行安全，并与其它 RTL 验证方案比较。对象是硬件安全验证，摘要没有 AI workload 的推算或性能结果；归档后不选正文。这里的 speculation 不是 LLM 推测解码。 |
| 160 | [ElasticMiter](https://infoscience.epfl.ch/server/api/core/bitstreams/515cc1b0-7772-4d4e-b0bd-915ee7a4587c/content)，EPFL 正式排版稿，16 页 | 验证 latency-insensitive dataflow circuit 的等价性，再验证用于简化电路的 graph rewrite。与 HLS 编译正确性相关，不能直接等同于模型计算图融合或自动 kernel 优化。当前主线不需要展开形式验证，故不选正文。 |
| 161 | [Robustness Verification for Checking Crash Consistency of Non-volatile Memory](https://feihe.github.io/materials/asplos25.pdf)，作者公开正式排版稿，15 页 | PMVerify 通过执行顺序约束、符号编码与 SMT 检查 crash consistency 的 robustness 性质，在 PMDK 示例上比较检测能力。它没有证明 GPU checkpoint、分布式训练或 persistent KV 的正确恢复，不能因“持久化”相同就套用；不选正文。 |
| 162 | [Proactive Runtime Detection of Aging-Related Silent Data Corruptions](https://par.nsf.gov/servlets/purl/10627157)，NSF 公共归档稿，16 页 | Vega 从老化的门级建模生成短测试并融合进应用或封装成库；摘要示例是 RISC-V CPU 的 ALU/FPU，报告平均 0.8% 开销。可作为“运行成功不等于结果正确”的可靠性背景；尚非 GPU、大模型训练故障检测证据，不设正文候选。 |
| 163 | Hardware Sentinel，正式 DOI `10.1145/3676641.3716258`，本次未得原始摘要/PDF | Crossref 核实标题与五名作者但没有摘要；ACM landing/PDF 均 403，web 打开摘要页同样失败。Meta 介绍文章给出了原论文链接，但该介绍不是论文摘要。保持未读，暂不根据二手摘要判断正文价值。 |

Toleo 与 Vega 的正式 DOI 均在 ASPLOS 2024 Volume 4，节目在 2025 年。Toleo 作者首页的 June 2024 消息明确记录了接收与报告延期，且同一出版条目列出了三名作者和正式 DOI。归档时保留出版卷与节目年份，不把 arXiv 日期改成正式出版日期。

Contract Shadow Logic 的 arXiv 页面注明已被 ASPLOS 2025 接收，标题、五名作者与正式 DOI 元数据一致；但是预印本只有 15 页，正式条目为 17 页。找到的 EPFL 正式稿请求返回 429，响应已留存。本次摘要是 arXiv v1 原文，不声称与正式摘要逐字相同，也未把缺失的两页算入公开 PDF。

ElasticMiter 的正式元数据将 Lana Josipović 的姓写成 `Josipovi?`；PDF 首页和引文清楚显示 `Josipović`。本包仅记录这个来源编码差异与别名映射，不修改共享 manifest。

PDF 摘要边界已经看图核过。ElasticMiter 的提取串在 Abstract 标题后插入了右栏的引文续行，故从真正摘要首句到末句提取；Vega 的摘要从左栏续到右栏，默认文本中夹入版权页脚，核验器按两个明确原文区间重提取，排除这段页脚。其它文字仅合并空白，没有改写原始摘要。

对 Hardware Sentinel 的补充材料仅保留 [Meta 2025-07-22 介绍文章](https://engineering.fb.com/2025/07/22/data-infrastructure/how-meta-keeps-its-ai-hardware-reliable/) 的来源身份与论文链接，不将文章中的 fleet 指标替代论文实验。Connected Papers 等转载和搜索摘要只用于找来源，未作为完整原始摘要归档。

本批不增加大纲、不建立新的实验或正文选读候选。后续若全书确实需要机密内存或 SDC 的具体问题，再另行指定正文范围。
