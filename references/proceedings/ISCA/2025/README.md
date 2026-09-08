# ISCA 2025：目录、公开稿与摘要

2026-09-08 将[官方日程](../../discovery/2026-09-08/isca2025-program.html)的 **135 个报告条目**匹配至出版 DOI：[清单](manifest.json)。134 项主标题规范化匹配，一项 Gaudi 论文的官方日程合写主标题和副标题，而出版元数据将两者分开；13 位作者及顺序一致，差异保留于[核对记录](title-variants.json)。

[论文集元数据](volume-3695053.json)给出 DOI `10.1145/3695053`、ISBN `9798400712616` 和 2025-06-20 出版日期。容器标题查询的 1,000 项排序结果中，135 项属于该卷，恰好覆盖已归档日程；不能据此声称是出版 API 的穷尽全集。ISBN 查询只返回论文集本身，没有返回逐篇文章或摘要。ACM 论文集网页返回 403 验证页，未当作论文集正文。

[公开位置清单](public-location-map.json)对应四份 OpenAlex 查询的 135 项 DOI，仅作寻找作者及机构公开稿的线索。摘要阅读依据后续取得的原件；二手摘要字段没有计入已读内容。[响应清单](selected-sources.json)保存 63 份响应的 URL、时间、状态、字节数和哈希，包括 ACM 与两份 Edinburgh PDF 入口的 3 次 403，以及 Neo 作者页的 1 次 404。

目前有 **36 篇论文的代表公开 PDF／549 个物理页面**，其中 35 份／534 页为新下载，DeepSeek 的 15 页 v2 复用原有文件；另存 MTIA 早期 12 页稿作版本比较，合计 37 个 PDF 文件／561 页，不重复计算论文。完整摘要已筛 **39 篇**：36 篇 PDF 原文，加 LIA、Hybe、Neoscope 三篇作者机构摘要。Oaken 物理页 2–12、MeshSlice 物理页 3–13 已选读；其余 **96 篇完整摘要**及更多公开稿待补。

[摘要证明](public-abstracts.json)保存抽取模式、字符范围、身份、版本和取舍；[扩大筛选批次](expanded-abstracts.json)保留新增 20 篇在正文选读前的判断。[阅读记录](../../../../research/2026-infra-survey/reading-isca-2025.md)当前为 10 篇排除、16 篇备查、11 篇正文候选和 2 篇采用。12 张实际查看的首页／摘要页只确认身份与边界；正文图表另记，全文页数与已读页数分开。

## 版本与范围

- FRED 采用 arXiv v2，PDF 已用正式题名，原始索引仍显示旧题名；ISBN 占位符和缺少 DOI 前缀的问题保留。按论文题名、五位作者和出版元数据匹配，未将索引摘要替代 PDF 摘要。
- H²-LLM 来自合著者公开页，摘要跨两栏；脚注与版权行不进入摘要。Oaken 保存会前 v1，右栏图和页脚的占位符单列，未采用图中倍率。
- Finesse v1、AIM v1 与 DeepSeek v2 是会后公开／修订版，保留原 URL 和日期。DeepSeek 只补入会议筛选，不重新下载，也不因历史报告改回本书主模型。
- [LIA 的 Google 页面](lia-google-index.html)使用较短题名，但链接指向同一 DOI，六位作者一致。其完整摘要已读，[作者仓库 README](lia-author-readme.json)另提供模型和运行参数线索；未取得论文 PDF，也未执行镜像或命令。
- [Neoscope 的 NVA JSON](../2024/closing/033-related-3.json)复用前轮线索，本轮才纳入 ISCA 2025 摘要计数；没有混入 ISCA 2024。元数据中的文件开放日期与会议年份分开。
- [AMALI README](amali-readme.json)仅提供 trace、配置和输出的静态阅读；代码仓库不是论文摘要，不能据此认定模拟器误差或框架功能。

离线再生成：`python references/reconcile_isca2025.py`；声明范围的独立校验：`python research/2026-infra-survey/verify_isca2025.py`。缓存再生成保留阅读证据，并分别统计机构摘要、PDF 与正文选读。此阶段未执行下载源码或运行 GPU；Oaken 深化既有 9.4.4／实验 9-8／图 9-7，MeshSlice 深化既有 6.2.2／实验 6-2／图 6-2 并衔接 11.2.3。

AIM 的原始抽取记录已将摘要标为物理第 2 页。独立校验最初把所有摘要限定为第 1 页而失败；实际查看 AIM 前两页后确认第 1 页仅列题名与作者，修正校验的页码条件并保留两张图，未改变已读摘要或数量。

Oaken 的[正文记录](oaken-reading.json)保存 11 页文本和四张实际查看的图表／公式页，采用到[格式与执行算例](../../../../case-studies/kv-quantization-and-execution.md)。图注互换、质量基线与模拟／综合口径的限制单列，不沿用论文性能倍率。

## 扩大筛选与 MeshSlice

本批新增 33 份响应，含 19 篇论文的 20 个 PDF 版本、Hybe 完整机构摘要和作者文件线索。ARTERY 的第 1 页是封面，完整摘要在物理第 2 页；SpecEE、Ecco、TrioSim 的摘要分段抽取并排除中间版权脚注。MTIA 的正式 DOI 公开稿增加 Xun Jiao／Jiyuan Zhang，出版表中的 Ajit Matthews 与 PDF 的 Ajit Mathews 拼写差异保留；Ecco 公开稿另含 Jiaqi Zhang，不覆盖出版作者表。

MeshSlice [正文记录](meshslice-reading.json)保存 11 页选读和三张实际查看的图表页；[矩阵与流水算例](../../../../case-studies/mesh-shape-and-slicing.md)接入 6.2.2／实验 6-2／图 6-2，并衔接 11.2.3。作者论文的模拟、真实 TPU 运行和预计重叠分别记录；Qwen3 教学数字由固定模型配置计算，不采用历史训练加速比。NetCrafter 作者页的 slides 不是论文，Neo 404 不是摘要；这些入口不计入已读数量。
