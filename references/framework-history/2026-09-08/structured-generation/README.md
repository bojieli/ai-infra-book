# 结构化生成：历史接口与当前执行

本批 [sources.json](sources.json) 归档 9 份成功响应，[reading-proof.json](reading-proof.json) 记录逐段范围和复用的 SGLang 2024 文章。固定 vLLM `537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e`、SGLang `c99d906effa8bd05573995127f0d4a0984c5a96a`；身份沿用此前 [vLLM](../speculative-execution/vllm-tree.json)／[SGLang](../overlap-placement/sglang-current-tree.json) tree。没有执行下载源码、GPU／模型或 cloud 请求。

| 原件 | 实际读取范围 |
| --- | --- |
| [vLLM 2025 文章](vllm-structured-2025.html)、[文本](vllm-structured-2025.txt) | 文本 77–150 行：V0 限制、XGrammar 接入与当时 V1 计划；没有采用图中成绩，未读完整历史引言 |
| [Ollama 2024 文章](ollama-structured-2024.html)、[文本](ollama-structured-2024.txt) | 文本 1–61 行：2024-12-06 公告、schema 与初始示例 |
| [vLLM 当前指南](vllm-current-guide.md) | 1–65、170–218 行：新 API、后端选择与 reasoning 例子；文档支持描述和完整验证链分开 |
| [vLLM manager](vllm-current-manager.py) | 35–98、115–202、220–391 行：编译线程、external_launcher 例外、按请求创建、填 mask、推测推进／回滚、reasoning 边界；未审计完整 scheduler／runner |
| [vLLM XGrammar backend](vllm-current-xgrammar.py) | 33–137、150–214 行：编译缓存、schema／grammar／tag、mask 分配及验证回滚；底层库未完整审计 |
| [SGLang 当前指南](sglang-current-guide.mdx) | 1–24、177–333 行：后端与 structural tag 的两种格式；示例只静态阅读 |
| [SGLang reasoning 指南](sglang-current-reasoning.mdx) | 1–45 行：自由思考与受约束输出的边界和示例；旧模型示例不作为全部当前支持清单 |
| [SGLang XGrammar backend](sglang-current-xgrammar.py) | 30–144 行：CPU mask、可用时 pinned memory、设备传输／应用、accept 与 rollback；其余编译器、调度与推测调用链未读 |
| [Ollama 当前指南](ollama-current-guide.html)、[文本](ollama-current-guide.txt) | 文本 1–57、85–125、424–433 行：本地 JSON／schema、Cloud 边界与消费端验证 |

[SGLang v0.4 原件](../../../outline-checks/2026-09-07/framework-evolution/sglang-v04.txt)复读 132–145 行。历史文章、当前文档和固定源码是代表时点，不以 2026 的采集日期当作所有机制的首发日。

XGrammar 直接复用 [MLSys 2025 正式 PDF](../../../proceedings/MLSys/2025/papers/mlsys2025-5c20ca4b0b20b0bd2f1d839dc605e70f.pdf)，物理页 1–11 已读、页 8 图 8 已查看，详见 [paper-reading.json](paper-reading.json)。没有重复下载，也没有阅读附录和后半参考文献；历史性能基线及语法正确率的适用范围保留。

采用与算例见[工具参数生成](../../../../case-studies/structured-generation.md)。它深化第 9.1／9.3 与第 12.1，沿用实验 9-2 和现有配图，不增加小节。
