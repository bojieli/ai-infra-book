# SGLang 重叠执行与 Ollama 容量规划

获取和核读日期为 2026-09-08；[清单](sources.json)保存原始 URL、日期、SHA-256 和提交。源码仅阅读下列范围，没有运行或全量审计。文件树仅用于定位文件，不作为实现已读的证据。

## SGLang

- [2025-05-05 H100 部署](sglang-ep-2025.html)：读 Two-batch Overlap、对应消融、Limitations and Future Work。重点为 DeepEP 元数据等待时的提交顺序，以及切小 batch 后的效率损失；模拟 MTP 与实测分开。
- [2025-06-16 GB200 第一期](sglang-gb200-2025-june.html)：读 Methods、End-to-end Performance、batch 消融与 Future Work。NVLink 环境改变两微批重叠的取舍；沿用旧基线与人为饱和负载不作单变量对照。
- [2025-09-25 GB200 第二期](sglang-gb200-2025-sept.html)：读 Methods、End-to-end Performance、Accuracy 的文字段落；质量图未估读。combine 与 down GEMM／共享专家重叠，精度、内核、EP 和 batch 同时变化，不能独立归因总加速。
- 当前固定提交 `c99d906effa8bd05573995127f0d4a0984c5a96a`：[two_batch_overlap](sglang-two-batch.py) 第 60–180 行，读请求／token 切分及退回序列边界的条件；[operations_strategy](sglang-operations-strategy.py) 第 225–330 行，重点为 Qwen3 MoE prefill 与 decode／验证的操作顺序；[single_batch_overlap](sglang-single-batch.py) 全文件，读硬件／后端条件、事件、信号和 SM 预算。这些辅助接口不证明每个模型入口均调用它们，实际实验还需确认路径。

## Ollama

| 快照 | 提交与已读位置 | 采用边界 |
| --- | --- | --- |
| 2024 年 10 月以前最后一次修改调度文件的提交 | `abed273de3a6183d734f0f3f0f129d7bd08ac4b4`，提交时间 2024-09-11；[scheduler](ollama-2024-scheduler.go) 第 210–285、688–738 行 | 容量预测、单 GPU 优先与同类多 GPU 候选；并发上下文也进入预算。日期来自按路径的提交查询，不是 release 日期。 |
| 2025 年 10 月以前最后一次修改调度文件的提交 | `05d53457af8fda79c0e3884f316144d6c2aed5b9`，提交时间 2025-09-17；[scheduler](ollama-2025-scheduler.go) 第 385–470 行；[llm server](ollama-2025-llm-server.go) 第 140–205、650–850 行 | 新引擎与旧兼容路径共存；fit／allocate／commit 反馈逐步修正放置，发生分配失败时会退让。 |
| 获取日固定主线 | `83ed7d9965b1ee07e0f0b29fd46e47c31f0fcab8`，提交时间 2026-09-05；[scheduler](ollama-current-scheduler.go) 第 515–615 行；[llm server](ollama-current-llm-server.go) 第 1–175 行 | GGML 模型转交 upstream llama-server，启动前仍有容量预测；MLX 为另一客户端路径。不把主线快照当作所有已发布版本。 |

[2025-09-23 内存调度公告](ollama-memory-2025.html)正文与支持范围已读。其“精确”描述限定当时新引擎路径，不能替代预留、可用内存变化和实际分配检查。2024 的 llm server 原件随比较保存，但本轮未读实现主体；当前代码的后续子进程分配实现未作全量追踪。

案例落在 5.3.5、7.2.3、9.1.4、9.4.1 和 10.4.3，推算见[资源共享笔记](../../../../case-studies/resource-sharing-and-placement.md)。本文不证明三套框架的 2024–2026 完整版本史已经读完。

后续权重卸载阶段补读 2024 llm server 的 1–135、182–201 行，并复核 GB200 的 Scaling Down by Offloading 段；当前 llama-server 放置与内存报告的新增读取范围见[执行资料](../offload-execution/README.md)。这不改变上文原阶段的阅读声明。
