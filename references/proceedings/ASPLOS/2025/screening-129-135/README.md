# 第 129–135 项摘要筛读

2026-09-09。七份成功响应中有四份 PDF，共 59 页。四篇完整原始摘要已读，四张首页已查看以核对身份、摘要边界和版本；没有正文选读计数。来源见 [sources.json](sources.json)，逐篇记录见 [screening.json](screening.json)。全文文本仅供后续定位，不因已抽取就计为已读。

| 条目与版本 | 本书取舍 |
| --- | --- |
| [129 QECC-Synth](129-preprint.pdf)，arXiv v4，2024-11-11，12 页 | 量子纠错布局综合，只归档。其稀疏连接、编译与 MaxSAT 设计空间不能直接移作 GPU 模型切分案例。 |
| [132 RESCQ](132-preprint.pdf)，arXiv v2，2025-03-24，16 页 | 量子资源态生产的动态调度，只归档。资源重分配和控制开销虽有一般意义，但不足以为 AI 请求调度另设内容。 |
| [133 GraphPipe](133-preprint.pdf)，arXiv v2，2024-10-28，15 页 | **正文候选**：模型分支如何改变流水深度、激活驻留和微批调度，可与第 6→10 章设备划分的主线对照。需要补读具体模型、依赖约束、设备条件与评估后再决定采用，不按摘要加速比补结论。 |
| [134 Cascade](134-author.pdf)，作者公开正式格式稿，16 页 | 备查：时序图节点状态更新与合批的取舍。此处 memory 是 TGNN 节点状态，不能直接等同于 Transformer KV。当前不扩写模型章节。 |

QECC-Synth 的作者题名比正式目录多 `Hardware`；Travis Humble 的作者稿名字未列正式元数据中的中间首字母 `S.`。两种写法均保留，其余作者顺序吻合。Cascade 作者稿题名为复数 `Networks`，正式元数据为单数 `Network`；首页 DOI 与完整作者一致。GraphPipe 的这份 v2 列出 Mengdi Wu，完整十四人名单与正式元数据吻合，不能用二次聚合页的另一作者名单覆盖原件。

RESCQ、Cascade 首页有正式 DOI，QECC-Synth、GraphPipe 首页没有；后两者依靠原始题名变体、完整作者与归档版本建立对应，不伪造出版副本。arXiv 上传日期和正式出版／日程年份分别保留。摘要中的性能数字仅作筛读信息，未据此写入正文。

GraphPipe 与前面 Spindle 的问题也需分开：前者摘要围绕单个 DNN 的图结构流水，后者已有记录涉及共享组件的多分支训练。下一步阅读重点是二者是否对同一约束作出不同选择，而非再列一种并行名词。

130 HetEC 与 135 Frugal 本轮仍缺原始摘要；[Frugal 的作者工件仓库](https://github.com/thustorage/Frugal)仅作为后续寻找论文与实验条件的线索，不运行安装或训练脚本。131、136 已在前批筛读，本批不重复计数。核验命令：`python research/2026-infra-survey/verify_asplos_graph_quantum.py`；统一索引由 `verify_asplos2025_coverage.py` 更新。本批不新增大纲节、实验或配图。

后续选读 GraphPipe 物理页 3–9，查看页 3、8、9 的图，见[正文记录](GRAPHPIPE-READING.md)。从正文候选转为现有实验 10-5 的计数变体：区分在途微批与样本，并保留 PP+DP、默认调度与 V100 评估边界。其他三篇仍没有正文阅读计数，上表为最初摘要筛选判断。
