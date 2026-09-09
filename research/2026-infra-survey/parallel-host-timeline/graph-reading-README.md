# 图执行：历史路径、动态选择与拷贝成本

核对日期 2026-09-08。[来源清单](sources.json)保存十项官方来源的 URL、原件、哈希和具体阅读范围；SGLang 公告复用已有原件，另存正文抽取。没有运行下载的源码、推理引擎或 GPU 实验。

| 来源 | 已读内容与采用范围 |
| --- | --- |
| [vLLM v0.6.0 runner](vllm-060-model-runner.py) | capture 开头、执行分派和 CUDAGraphRunner；decode 条件、固定输入及更新。其“200 token 后收益很小”等历史注释不作通用规律。 |
| [v0.6.0 发布元数据](vllm-060-release.json) | 发布时间为 2024-09-04 UTC；未读整篇发布说明。 |
| [vLLM v0.9.2 编译指南](vllm-092-compile.md) | Cudagraph Capture 到文末：attention 外的分段捕获、输出缓冲、可选完整捕获；前面编译部分未读。 |
| [v0.9.2 发布元数据](vllm-092-release.json) | 发布时间为 2025-07-07 UTC；不是双模式 PR 的合入日期。 |
| [双模式 PR #20059](vllm-dual-graph-pr20059.json) | 创建于 2025-06-25、合并于 2025-08-15；仅元数据，不宣称审完此 PR 的实现。 |
| [固定主线设计文档](vllm-current-cuda-graphs.md) | Markdown 全部文字；图与外链未逐项读。仍含旧后端名单、未来时态和简化原型，以其解释设计动机，不据此保证当前全部默认配置。 |
| [固定主线 dispatcher](vllm-current-dispatcher.py) | 132–325 行：形状描述、注册、LoRA 数量与 FULL→PIECEWISE→NONE 的可用路径选择；不是对全部 runner／编译 pass 的审计。 |
| [SGLang BCG PR #19102](sglang-bcg-pr19102.json) | 2026-02-21 创建、04-11 合并；这是 PR 时间，不将创建时间单独当作完整代码首发证明。 |
| [SGLang prefill BCG PR #22218](sglang-bcg-prefill-pr22218.json) | 2026-04-07 创建、04-24 合并；元数据核对，未读 diff。 |
| [SGLang 2026-08 公告正文](sglang-advanced-graph-article.txt) | 全部正文及文字图注；边界缓冲拷贝、token／request padding、图池复用与捕获上限。未独立提取柱状图或核验其未归档源码。 |

两份固定主线文件均取自 vLLM 提交 `51da0ca66c8065619c79e35dff97aa99aeaf5644`；当前主线不等于每个正式安装版本。上述分派根据配置、后端与 batch 寻找可用图，不能写成已实现 GraCE 的逐段实测最优选择。GraCE 是 PyTorch 2.4 上的研究原型，其旧框架对照不覆盖当前 vLLM／SGLang。

计算、正文落点与实验变体见[图执行取舍](../../../../case-studies/graph-execution-tradeoffs.md)。模型仍以 Qwen3／V4／K3 贯穿，论文和公告的 XLNet、gpt-oss、GLM 等保留为有条件的历史实例，不移用性能倍数。
