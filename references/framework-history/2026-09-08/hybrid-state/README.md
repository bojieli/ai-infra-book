# 混合模型前缀缓存的版本证据

获取与核读：2026-09-08。[sources.json](sources.json)记录 18 份成功响应的 URL、时间、字节和 SHA-256；另复用三份已有原件。[reading-proof.json](reading-proof.json)逐项登记 21 份文本的行、DOM 字符或 JSON 字段范围。未将整份源码下载当作全部实现已读，没有执行下载代码或模型，没有采用图中的性能数字。

## vLLM：匹配粒度、状态准入与物理所有权

[v0.5.5 APC](vllm-055-apc.txt)全文核读，以全前缀链标识不可变 KV 块；2024-08-23 的发布身份已在[量化资料](../kv-quantization/vllm-055-release.json)核对。历史文档中的感知图像哈希是设想，未采用为安全的精确复用规则。

[K3 预览文章](vllm-k3-preview.html)选读前缀缓存节，[正式文章](vllm-k3-release.html)选读部分块、多级复用和保留策略。文章展示时间分别为 2026-07-22／27；现存正文按获取日保存，PR 日期独立核对：

| PR | 合入日期（UTC） | 本书采用的范围 |
| --- | --- | --- |
| [#37898](vllm-pr-37898.json) | 2026-06-10 | 明确 Marconi-style 准入，利用普通 KV 命中发现尚未保存的共享循环状态；不是论文 radix 实现的逐行移植 |
| [#45939](vllm-pr-45939.json) | 2026-06-22 | 细粒度前缀链和部分块登记的基础原语；该 PR 自身不提供完整调度／检查点物化 |
| [#45845](vllm-pr-45845.json) | 2026-06-23 | 将间隔保留接入循环状态；其历史 Kimi-Linear 测试不替换成 K3 结果 |
| [#47782](vllm-pr-47782.json) | 2026-07-13 | 稀疏保留仍可保留后来发现的共享边界 |
| [#49502](vllm-pr-49502.json) | 2026-07-27 | 部分尾块交接、精确边界与 CoW 生命周期；未独立复现提交者测试 |

固定当前 SHA 为 `5133e1d28594d5939552003f32b55a3fb18556a1`，身份复用[已归档响应](../kv-quantization/vllm-commit.json)。[协调器](vllm-coordinator.txt)读行 567–705、735–918，核对分组对齐与迭代寻找共同边界；[块池](vllm-block-pool.txt)读 446–568，确认登记部分哈希只是元数据；[单类管理器](vllm-single-manager.txt)读 1810–1872，核对生产请求保留旧块、排队复制后移交缓存块的生命周期。没有审完全部 worker、复制 kernel 或连接器调用链。

[混合缓存设计文档](vllm-hybrid-design.txt)全文已读，但它显式基于较早的 `458e74eb907f96069e6d8a4f3c9f457001fef2ea`，仍有 Mamba WIP 等早期措辞。文件存在于当前树不意味着其中的限制仍是当前实现上限。该文仅支持分组、对齐和页大小权衡。

[2026-04-21 混合 SSM 分离文章](vllm-hybrid-disagg.html)选读状态布局、传输、评估文字与限制。其 Mamba2 三段卷积传输、当时 GDN 路线图、HMA 异构块长限制均保留历史语境；8×H200／Nemotron 的 PD 比较关闭了前缀缓存，不能与 K3 快照命中拼成一项收益。本轮不采用其性能曲线。

## SGLang：共同前缀上的不同状态

复用[2026-08-11 Unified Radix Cache 原文](../../../outline-checks/2026-09-07/framework-evolution/sglang-unified-cache.html)，本轮精读组件和可恢复边界两节：遍历深度可以超过安全复用深度，候选位置需所有活动组件同意；一次拒绝也不能直接结束遍历。K3 的 MAMBA 组件表示 KDA 状态的恢复规则，不是把模型名称改成 Mamba。

固定 SHA `5aab054ec8ce6b6100fbfb7aafe67d632a7df3aa`，身份见[响应](../kv-quantization/sglang-commit.json)。[统一缓存](sglang-unified.txt)只读 515–541 的入口、动作与 finalizer，遍历原理由上述文章支持，没有冒充整套树核心审查。[K3 计算器](sglang-k3-ratio.txt)读 1–195，明确 69／24 层、FP32 循环状态、BF16 卷积和注意力 TP 内复制的紧凑 MLA。算例再与[模型固定配置](../../../outline-checks/2026-09-07/model-accounting/kimi-k3-config.json)核对。

计算器中的请求槽位、overlap、DP attention、DCP 和推测中间状态分别受配置影响；正文只计算一份检查点，未把其默认比例当作全系统精确容量。代码中的 PP 等比例解释也不推广到任意不均匀层分布。[可选检查点池](sglang-checkpoint-pool.txt)只读 301–373 的 headroom 和分配检查，其 INT8 选项、精度与量化 kernel 未审，不用于本轮预算。

## Ollama：可恢复边界与本地执行

复用并重读 [2026-06-11 MLX 文章](../speculative-execution/ollama-mlx-performance-2026.html)的既有完整正文抽取，采用 Agent 分支、reasoning 删除与选择性快照，不采用速度或质量图。固定 SHA `83ed7d9965b1ee07e0f0b29fd46e47c31f0fcab8`，身份见[响应](../kv-quantization/ollama-commit.json)。

[recurrent cache](ollama-recurrent.txt)与 [cache trie](ollama-cache-trie.txt)全文已读：递推状态是 FP32，恢复要求精确 offset；中间快照依赖执行到相应位置，切分 trie 不能凭空恢复一个未保存的位置；每个有状态层均须具备快照。该 recurrent 路径明确 batch=1。Clone／Pin 的底层实现与调用方全部恢复流程未审，不把 API 调用直接换算成立刻复制两份物理容量，也不从这段通用代码推出 Ollama 支持完整 K3。

采用与数字见[混合状态算例](../../../../case-studies/hybrid-prefix-state.md)。机制研究、历史测试和拟做的真实实验分别记录，保留既有章节、实验和图号。
