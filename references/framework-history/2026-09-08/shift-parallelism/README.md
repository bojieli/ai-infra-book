# ArcticInference：并行切换的版本与执行范围

本次归档 22 份响应，21 份成功，一份历史文档路径返回 404；见 [sources.json](sources.json)。按 [readings.json](readings.json)声明的范围读取公告、配置、CLI、模型加载、KV 绑定、通信组、attention 交换和图调度；没有运行下载的源码、导入框架或执行模型。完整调用链、模型兼容性和硬件收益仍需实测。

## 时间与代码身份

- 2025-05-29 的 Snowflake 公告，只读“Why not combine them?”与“Introducing Shift Parallelism”所在完整文本块及发布日期，不把组合优化的宣传数字作为单项收益。
- ArcticInference `v0.0.7` 发布于 2025-05-29，当前查询解析到 `6b3cbafa6ce4bccde370e600f6327a0d8b4956b6`。其配套 extra 固定 vLLM 0.8.4；选读配置、参数、runner 的双模型加载／KV 绑定、token 阈值及两套图捕获。
- [ASPLOS 2026 论文](../../../proceedings/ASPLOS/2026/paper-004.pdf)为 arXiv `2509.16495v2`，2026-01-26；页 1–12 已选读，主要性能实验使用 vLLM 0.9.2。它与另一篇 Arctic Inference 综合报告分开。
- 当前 main 固定在 `aca5d9a8a62474035c15d114d40a01abc8c94b51`，提交时间 2026-09-08；项目版本字段为 `0.3.1.dev0`，不能当作已安装的稳定发行版。当前插件检查的 vLLM 版本为 0.26.0。十一项发布记录只核标签与日期，未据此声称完整版本史读完。

## 机制及必须核实的差异

2025 的选读实现已经分别加载基础与切换模型、绑定同一 KV，并以 `total_num_scheduled_tokens` 选择模式。基础模式把 token 补齐到 SP 倍数，切换模式使用自己的捕获形状。当前选读实现仍采用这些主要取舍，并增加分别保存和切换图分派表、按模式标记图统计、匹配 KV 层上下文，以及对非顺序通信组的 logits 词表分片重排。这里比较两个固定快照，不将当前差异都声称为 2026 首创。

当前 `ulysses.py` 用 rank 张量转置建立 SP 与全 TP 组，attention 前后各一次 All-to-All；KV 头不足时在发送缓冲复制。当前 `runner.py` 加载第二套权重，并将相应 attention 的 `kv_cache` 绑定到基础模型。需同时检查数值、状态身份与输出顺序，不能只比较缓冲大小。

有两处文档与代码不一致，实验固定显式参数并记录生效路径：

1. 当前指南写默认阈值 256，选读的 2025 与当前 CLI／配置均为 512；当前 runner 比较的是实际调度 token 总数。指南中的 batch 不能直接解释为请求数。
2. 当前 `utils.py` 与 `pyproject.toml` 注释写版本不符时跳过 patch，但实际 `plugin.py` 在显式启用且版本不符时抛出异常；未启用则提前返回。插件还设置 V1 runner。以读到的控制流记录条件，不根据注释宣称已成功运行。

当前 `runner.py` 的加载和捕获路径会对部分自定义 AllReduce 作禁用／回退处理；因此算法字节估算之后，还必须测真正执行的 collective 和 Graph 路径。这里只选读相关函数范围，未审计所有后端、捕获完成路径或每种模型。

对应[Qwen3 的状态、容量与通信推算](../../../../case-studies/parallel-switching-and-state.md)，用于当前第 6→9 章既有实验。头顺序与双权重的判断进入大纲；版本、参数和实现细节保留在此。
