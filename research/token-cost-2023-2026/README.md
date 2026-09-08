# 2023—2026 年 token 成本下降专题调研

已按作者要求分为两部分：完整调研报告与原始资料；在现有大纲合适位置放置简短 placeholder。截止日为 2026-09-07。

- [完整报告](report.md)：15 个部分，分析固定能力价格、能力密度、模型架构、芯片、量化与内核、vLLM、MTP／推测解码、缓存与分离式服务、商业价格、成功任务成本和跨层归因。
- [原始资料与阅读索引](../../references/token-cost/2026-09-07/README.md)：67 项来源，其中 20 项新下载、47 项复用已核验原件，含 40 份 PDF；另存 18 幅原图。
- [大纲落点](outline-placement.md)：18 条占位，覆盖 9 章；第一章提出问题，终章回收，后续扩写按报告补齐。
- [可复算数据](data/epoch-frontiers.csv)与[计算记录](calculations.json)：119 条公开历史观测、五组端点比较与明确标注假设的资源／任务算例。
- [价格图 SVG](figures/price-frontiers.svg)：从原始表重绘，历史观测止于各系列最后记录，没有向 2026 年外推。
- [核对结果](verification.json)：来源、图像、链接、算例与大纲占位检查。

主要结论：数量级下降有证据，但“2023—2026 年所有同等智能 token 统一降低 1000 倍”未被这些材料证明。vLLM 的 2.7 倍属于 v0.6.0 的一组版本改进；GIL 竞争是其中一项。MTP、量化、批处理、硬件与缓存存在交互，不能将各自最大倍率直接相乘。

```sh
python research/token-cost-2023-2026/analyze.py
python research/token-cost-2023-2026/verify.py
```

`archive_sources.py` 与 `archive_media.py` 用于补齐本专题原件；已保存的原件不随重复运行更新。要采集新的价格或版本，请另开日期快照。来源清单和逐项阅读范围分别保存在 `source-plan.json`、`reading-notes.json`；未开展本书 GPU 实测，也未将预测或厂商估计标为实测。

这是一项独立完成的专题，不表示仓库中另一个“2024–2026 长期调研”目标已完成。当前目标回合产生了报告、原件归档、可复算数据与实际大纲占位，属于 progress。
