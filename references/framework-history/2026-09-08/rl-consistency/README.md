# 推理可复现性与 RL 状态交接

获取于 2026-09-08，原件与 SHA-256 见 [sources.json](sources.json)。这是已读范围记录，没有执行 GPU、训练或质量实验。

| 来源 | 已读范围 | 版本及使用边界 |
| --- | --- | --- |
| [Thinking Machines Lab：推理非确定性](thinking-machines-determinism.html) | 引言、浮点与 atomic 讨论、batch invariance、三类归约、Implementation、True on-policy RL 正文 | 用于解释固定调用的重复性与改变 batch 后的一致性。性能曲线与全部脚注未逐项核读；不把文中历史引擎路径当作当前框架，也不沿用其中所有性能数字。 |
| [SGLang 2025 公告](sglang-determinism-2025.html) | 正文、结果表、实现和 Future Work 读完；图像曲线未取数 | 2025-09-22，页面注明 9 月 24 日更新；使用说明为 ≥0.5.3。当时主要验证 Qwen3-8B，CUDA Graph 表为 H100，离线时延表为 H200；缓存、TP 与模型限制须随表保留。 |
| [SGLang 当前指南](sglang-determinism-current.html) | 主文、后端兼容表、采样与验证说明读完 | 相比 2025 公告，列出 Qwen3-30B-A3B，并把 Triton 与 Radix Cache 列为兼容。FlashInfer 的缓存限制仍在表内；这是当前文档，不是所有历史安装版本。 |
| [vLLM v0.12.0 指南](vllm-batch-invariance-012.md) | 全文 | [发布元数据](vllm-v012-release.json)确认 2025-12-03 正式发布；不是该特性的首次合入日期。该版要求 NVIDIA CC ≥9.0，已有 Dense／MoE 测试名单。 |
| [vLLM 当前 batch invariance](vllm-batch-invariance-current.md)及[可复现性](vllm-reproducibility-current.md) | 两份文档全文 | 固定提交 `51da0ca66c8065619c79e35dff97aa99aeaf5644`，仍标 beta；文档扩到 CC ≥8.0 和指定 Triton 后端的 Intel XPU。当前主线与 stable 网页覆盖略有差异，不把主线新增项归于所有正式版本。只承诺所述同硬件、同版本条件。 |
| [AReaL 异步 RL](areal-async-current.html) | 全文 | 部分轨迹可以跨策略版本，滞后控制与解耦目标各有作用；文档中的经验范围不是所有任务的最佳值。 |
| [AReaL GRPO 流程](areal-grpo-current.html) | Overview 至异步收集／staleness、Weight Update Process 至文末；中间训练分发／算法实现段只部分读过 | 轨迹保存 token、mask、logprob 与版本；权重交接先暂停生成，再分发、更新版本并重算 KV 后恢复。当前公开指南的路径，不反推 DeepSeek-V4 未公开部署。 |

三个 vLLM 文档站请求返回 429，响应原件及哈希保留在各条目的 `initial_fetch`；随后从官方 GitHub 的版本标签或固定提交获取 Markdown。失败页不作为正文来源。下载代码仓库中的文档不等于审计全部实现，其他源码和论文脚注没有据此登记为已读。

教学计算与章节安排见[RL 状态与可复现性](../../../../case-studies/rl-state-and-reproducibility.md)。同一轮面试资料只帮助选问题，技术答案独立核对以上原始来源。
