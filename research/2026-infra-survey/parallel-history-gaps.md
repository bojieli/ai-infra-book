# 框架演进的有界缺口复核

2026-09-09；只读复核现有资料，仅写本文件。没有下载新文献或源码，没有改演进表、覆盖表、大纲或 Git。结论是：**不再新增独立主题，只建议收束一处已有专题——把主机调度的演进接成同一条请求时间线。** 本次未发现需要为了凑两个缺口再扩张书的理由。

## 唯一建议优先补齐的链条：减少 CPU 工作与隐藏 CPU 等待

### 已覆盖什么

- [框架演进表](../../case-studies/framework-evolution.md) 已有 vLLM 2024 分块到 2025 V1 统一进度、2024→2026 图执行、2026 推测执行；SGLang 已有 2024 v0.4 CPU/GPU 重叠和 2026 Spec V2。
- [图执行记录](../../references/framework-history/2026-09-08/graph-selection/README.md) 的历史 runner、分段/全图与当前 dispatcher，主要证明捕获范围和图分派。所读范围不等于完整 engine loop、调度与结果返回链。
- [分块调度记录](../../references/framework-history/2026-09-08/chunk-scheduling/README.md) 已清楚说明统一 token 进度、KV 约束、占位与抢占；所读代码集中在预算/准入分支，没有连到 CPU 如何提前处理下一批。
- [推测执行记录](../../references/framework-history/2026-09-08/speculative-execution/README.md) 已读 SGLang Spec V2 公告、vLLM P-EAGLE 的使用条件及相关配置。SGLang 2026 公告明确分开前一批的结果清理与下一批 KV 分配；vLLM 的运行命令含 `--async-scheduling`，但开关名称或复现命令本身不是已审完整异步调度源码。
- 当前 [LoRA 准入阅读记录](../../references/framework-history/2026-09-09/lora-admission/reading.json) 对 scheduler 的记录是 809–877 行准入范围。文件其他位置虽有 async/PP、in-flight/stale 输出等关键词，本次只做定位，不能把文件已经下载当作那些分支已经审读。

### 真正未讲通的判断

**同一份 Qwen3-8B decode 工作，CPU 是少做了几次工作，还是把相同工作提前做了？采样输出尚未返回时，下一步到底哪些数据已经能准备？**

这决定第 5 章采用的 `max(主机准备, GPU 执行)` 是否成立，以及第 8 章的批次、结束/取消、推测接受长度或约束状态会不会重新引入等待。图捕获减少提交、多步调度减少调度频率、异步结果处理与提前准备下一批，并不是同一项机制；三者也不能各自取一个公告加速比相乘。

已有 `graph-execution-tradeoffs.md` 的假想时间线、NanoFlow 的并发计算和 Spec V2 的局部说明已经足够建立方法。缺的是**用一条真实引擎路径验证那条时间线的依赖条件，并说清各时点的变化**，而不是再引入一种模型、另一篇调度论文或一个新性能名词。

### 最小的一手补读范围

优先复用已归档原件，再补固定调用链；不建议广搜论文。

1. **2024 起点：vLLM 多步调度与异步输出。** 已归档 [v0.6.0 官方 release](../../references/framework-history/2026-09-08/graph-selection/vllm-060-release.json) 的 Performance Update 明确同时列出 multi-step scheduling 与 asynchronous output processor，链接到 [PR #7789](https://github.com/vllm-project/vllm/pull/7789)、[PR #7049](https://github.com/vllm-project/vllm/pull/7049)，并保留当时的限制入口。本次只新读 release 开头，不采用其倍数，也未读两份 PR。下一步只追当时一次多步循环与一次结果处理的调用/测试，确认何时调度、何时提交、何时检测结束；不读完整 changelog。
2. **2024 的独立对照：SGLang v0.4。** 已归档 [v0.4 公告](../../references/outline-checks/2026-09-07/framework-evolution/sglang-v04.txt) 第 27–38 行解释提前一批、future tokens 与 CUDA event；其 [固定源码链接](https://github.com/sgl-project/sglang/blob/85e1a6f3aa5a2288ca85fe3fe922c733b6533fa7/python/sglang/srt/managers/scheduler.py#L399) 是合适起点。公告自身限定了示例 profile 的 Triton attention backend，不能把“zero-overhead”当作所有后端条件。只需补这条旧循环与下一步输入如何接续，不重复已有缓存路由内容。
3. **2025 过渡：固定 V1 版本的 engine loop。** 现有 v0.8.0 scheduler 已固定至 `966f933ee1cd7c9a41db60de5c7ff98657005251`。沿同提交的 `vllm/v1/engine/core.py` 和相关 worker/输出处理入口，检查进程/队列边界及 token 回传。**这是待读路径，不宣称该版本已经具备今天 `AsyncScheduler` 的全部行为。** 获取于 2026 年、不断更新的 V1 guide 不能反推出 2025 年每个功能的发布日期。
4. **2026 落地：只补一份完整普通 decode 路径，再加一个现有变体。** 归档 vLLM 目录已经列出 `vllm/v1/core/sched/async_scheduler.py`、`vllm/v1/engine/core.py`、`vllm/config/scheduler.py`、`tests/v1/core/test_async_scheduler.py` 和 `tests/v1/e2e/general/test_async_scheduling.py`。先固定同一提交，读负责下一批与结果回收的函数及有意义的测试；随后在已支持配置中只加推测或结构化输出之一。SGLang 从已经读过的 Spec V2 公告回到其所链接的 scheduler/worker 实现；公告与配置不替代完整生效路径。只选一套引擎做实验，另一套保留历史方法对照。

上述建议来源是待补读清单。除说明已读的归档文字外，本次没有下载/运行这些源码，也没有确认所有候选路径的当前功能或兼容组合。

### 放入哪里，怎样停止继续加内容

- 主落点保持 **5.4.3 主机提交与设备执行 → 8.1.3 连续批处理 / 8.1.5 图重放**，实验沿用 **5-8、8-2**。用同一 Qwen3-8B 的两到三次实际 decode 迭代，在既有时间图上标批次决定、输入就绪、GPU 前向、采样、回传/清理和下一步提交。先预测重叠上限，再检查 profile。
- 推测变体继续放在 **8.3**，只说明实际接受长度与状态更新带来的依赖；PP 只在已有 **6.2.3 / 9.6** 实验真正启用时才加入，不为做兼容矩阵另外开专题。
- **完成条件**：能解释一个普通 decode 请求和一个既有变体中，为什么 CPU 等待可以隐藏或不能隐藏；明确版本/后端/状态条件，且能把真实 trace 对回书里的时间线。无需覆盖所有模型、硬件、图模式、PP 和推测方法的笛卡尔积。

## 其余专题建议收束

- 图执行与主机调度合用一条时间线，减少“更多图模式、更多论文原型”的并列介绍。
- 前缀复用、KV 层次、事件路由已经覆盖数据身份、可用位置、缺失事件与预测状态；优先完成同一请求的命中/等待/重算记录，不再为框架各列一套缓存功能史。
- MoE 分派、EPLB、动态 EP 已区分分派、重排、组规模和论文/主线边界；以 Qwen3 算例核完一个候选的资源收支即可，不再加入更多负载均衡器名称。
- 多 LoRA、量化、结构化生成与权重交接也已有明确接口/实现差距。剩余设备 trace 和完整系统实验属于**验证工作**，不应靠继续读 release 填成“阅读还没完成”。

来源目录中有历史章号仍作为当时阅读背景保留；本建议统一采用当前第 5/6/8/9 章，不把旧阅读记录的章号当作新增主题缺口。

## 本次审读凭据

阅读主要范围：演进表第 1–54 行及后续相关关键词定位；覆盖表全文；graph-selection、chunk-scheduling、speculative-execution 三份 README 全文；`graph-execution-tradeoffs.md` 第 1–75 行、`chunking-and-state-transfer.md` 第 1–42 行、`parallel-switching-and-state.md` 全文。另外查看 LoRA `reading.json` 的相关 scope，补读 v0.6.0 release 开头、SGLang v0.4 第 22–38 行和 Spec V2 第 148–170 行。没有新增会议论文阅读量或设备结果。

文件 SHA-256 在本次写入时登记如下；用户/根任务继续编辑后应重新核对，不能假设行号与内容不变：

登记时间：2026-09-09T05:51:41.426440+00:00。

| 输入 | SHA-256 |
| --- | --- |
| `case-studies/framework-evolution.md` | `271930ce73983f2ea450a688a6468d2881e0fb287411253efc4af727cfb81d7e` |
| `research/2026-infra-survey/framework-coverage.md` | `d63b7f15dab968c1c3d2da646511dbd26e829be0ce14d00ea6d82944110ed432` |
| `references/framework-history/2026-09-08/graph-selection/README.md` | `9857f235b4263c322a0b87aaf637e5fbce1eccad298b4723727c949d7f86220e` |
| `references/framework-history/2026-09-08/chunk-scheduling/README.md` | `cc7c6ae297dbe90066b356cad52b3920921edc5225ccd21a11c5ce9d85dcb464` |
| `references/framework-history/2026-09-08/speculative-execution/README.md` | `4f0458dae25d861c51baa415f67567eac125f85170382808a287b8fec7a099ce` |
| `references/framework-history/2026-09-09/lora-admission/reading.json` | `38e64af050cc85b32d91e94d90ed509c211a1d4ab14e84943e81df74a91ea928` |
