# POD 的上层调用边界

2026-09-09 静态核对，未运行框架或 GPU。vLLM 固定为 `385dce36bcee42309924a5ece951a96db3dce7f2`，SGLang 固定为 `eb42598bddb146ac6c8e67cb63022e7420ed82ec`。九份响应包含两个提交、四份路径树查询及三个源码文件；[sources.json](sources.json)保存原始来源，[reading.json](reading.json)保存实际读过的行范围。路径树仅用于定位，不等于已搜索全仓库源码。

问题来自前面的 [POD 论文与 FlashInfer 实现对照](../pod-implementation/README.md)：底层库同时支持两个阶段的注意力，不能据此认定上层混合批次已经调用这种实现。需要看实际 backend 的入口、分支和输出合并。

在 [vLLM backend](vllm-backend.py) 所读普通注意力分支中，decode token 放在前部，prefill token 放在后部。`num_prefill_tokens > 0` 与 `num_decode_tokens > 0` 是两个分别判断的分支。非 TRTLLM 路径分别使用 prefill／decode wrapper，分别转换所需 query dtype 和写入输出片段；DCP 分支还涉及独立通信、临时输出和合并。所读后段另有 TRTLLM／XQA 路径及专门限制，不能将一种分派描述成所有设备的统一执行。

在 [SGLang backend](sglang-backend.py) 所读范围中，`forward_extend` 与 `forward_decode` 使用各自 wrapper。extend 的 paged 路径直接使用分页 KV；ragged 且有缓存前缀的分支分别产生当前片段和既有前缀的输出及 LSE，再调用 `_safe_merge_state`。这是**同一次注意力的上下文分解**，不能与“把其他请求的 prefill／decode 共驻到 SM”混为一谈。decode 路径另有 KV 写入和条件反量化工作区准备，wrapper 内核时间也不是整个方法的耗时。

三个下载文件中没有找到 `PODWithPagedKVCacheWrapper`、`POD` 或 `pod_` 文本。此结果只限于列出的文件；其他后端、插件、生成代码、未来版本和底层库内部路径没有被排除。我们确认的是这些已读分支显式调用的接口，**不能据此给出整个 vLLM／SGLang 未采用 POD 的结论**。也没有检查当前环境实际安装的 FlashInfer 版本，不能把上次固定的库提交自动当作这两个框架的运行依赖。

对第 5→8 章的用途是区分三个问题：请求是否混合成一个批次；注意力是否拆成若干上下文分段；设备上是否让不同阶段有效共驻。它们需要不同的证据。实验沿用现有混合批次与 CUDA Graph 变体，记录 backend、dtype、DCP、wrapper、合并和完整迭代的 profile，再与前文共享计算／带宽下界对照。两次 Python 调用不是两次 kernel 的计数，也不凭调用顺序推断 GPU 已同步等待。没有新增核心实验或性能数字。

论文研究版、FlashInfer 库、上层 backend 是三份不同证据；本批补当前调用边界，不新增论文阅读数量，也不把两份当前快照冒称完整 2024–2026 演进史。

初次按 commit SHA 查询的响应保留该 SHA；后续使用提交元数据的 tree SHA 查询原始树，按 Git blob 哈希验证三个下载文件。四份树查询不算四个版本。
