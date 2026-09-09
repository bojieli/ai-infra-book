# RL 中的状态、版本与可复现性

核对于 2026-09-08。[官方资料及版本](../references/framework-history/2026-09-08/rl-consistency/README.md)支持机制分析；下列数字是独立教学输入，没有运行模型或测得训练收益。面试方向另见[第三批资料](../references/interviews/2026-09-08/third-pass/README.md)，不以面经答案代替实现依据。

## 从归约顺序到服务结果

第 5 章已经比较一行一个工作组与拆分归约。把 Qwen3 同一行放在不同 batch 中，分块、split-K／split-KV 或指令选择可能改变累加顺序。一个固定形状的 kernel 重复运行相同，并不能证明变更 batch 后仍逐位相同；atomic add 只是可能原因之一，去掉它不能修复所有形状相关差异。[Thinking Machines Lab 原文](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)把问题落在 RMSNorm、矩阵乘和注意力的具体归约上。

SGLang 2025 的实现把 chunk 边界与注意力归约切分配合起来，又加入请求自己的采样种子；CUDA Graph 能减少提交成本，仍需选择兼容的后端和缓存路径。该公告的 Qwen3-8B、TP1、H100 图执行表与 H200 离线表是两组实验，不能拼成一个统一加速比。当前指南增加了 MoE 示例和后端兼容范围，实验必须锁定版本后验证。[历史公告](https://www.lmsys.org/blog/2025-09-22-sglang-deterministic/)、[当前指南](https://docs.sglang.io/docs/advanced_features/deterministic_inference)

vLLM v0.12.0 与固定当前提交的支持范围也不同。当前文档把同硬件、同版本作为边界；主机调度可重复、batch 改变后数值不变、随机采样可重复分别处理。验证时先比较同 token 的 logits／logprob，再看自然生成；不同 seed 可得到不同样本，同 seed 可复验同一路径，但不保证不同 seed 一定生成不同答案。[版本文档](../references/framework-history/2026-09-08/rl-consistency/vllm-batch-invariance-012.md)、[当前文档](../references/framework-history/2026-09-08/rl-consistency/vllm-reproducibility-current.md)

## 概率比中的三份身份

RL 中分别记录实际生成样本的行为策略、更新前的训练策略，以及正在优化的当前策略。相同权重不代表不同引擎的数值路径相同；生成记录中的 logprob 与训练端重算值也不能不加区分地替换。

先固定同一 token、条件前缀与概率支持，下面检查的是当前策略相对实际行为分布的 `r_behavior = π_current / μ`。PPO 的更新比 `r_update = π_current / π_old` 与采样修正 `w = π_old / μ` 分别定义；未裁剪时两者乘积为 `r_behavior`，但不能由此认为不同裁剪位置等价。

一个最小反例：假定某 token 的真实行为 logprob 与当前 logprob 都是 `−3`，对应比值为 `exp(−3−(−3))=1`。若错误地用 `−3.25` 的重算值覆盖分母，就得到 `exp(0.25)≈1.2840`。若题设对这里的 `r_behavior` 设诊断上界 `1.2`，它已越过上界，即使这个例子根本没有参数更新。数值不是对真实框架误差的测量；目的是让读者先检查概率的身份和定义。

同一个 `−3.25` 若明确属于 `π_old`，则 `r_update≈1.2840` 与 `w≈0.7788` 都是定义清楚的值，乘积仍为 1。错误在于混淆身份后覆盖行为记录，不在于重算本身。[固定 AReaL 指南](../references/framework-history/2026-09-08/rl-consistency/areal-async-current.html#decoupled-ppo-objective)甚至要求启用 decoupled loss 时开启 `recompute_logprobs`；这只支持保留两类记录的必要性，本例不声称复现其完整 loss。实际使用哪个比值、怎样裁剪或截断，回到选定算法核对。

[R3 与 NeMo RL 的既有资料](execution-feedback.md)处理专家离散选择这一部分：记录逻辑专家 ID，在当前权重下重算分数与输出；它不消除所有浮点差异，也不解决异步策略滞后。`8192 × 48 × 8 × 2` 为 6 MiB 路由 ID，int32 则为 12 MiB，另计 mask、版本和传输。这个小记录不包含 KV，更不是旧输出的回放。batch invariance、Routing Replay 和 off-policy 处理要按原因分别检验。

## 更新权重时保留什么

沿 AReaL 的公开流程看一次暂停与恢复：已生成 token、环境状态和对应行为 logprob 可以继续作为轨迹；新策略需要的 KV 却不能只因为 token 相同就视为有效。指南在权重交接后重算 KV，再继续未完成生成；每个生成 token 保留实际策略版本。[异步机制](https://areal-ai.io/docs/en/algorithms/async.html)、[权重交接](https://areal-ai.io/AReaL/en/tutorial/gsm8k_grpo.html#weight-update-process)

复用 Qwen3-8B 的 8K BF16 例子，一份逻辑 KV 为 1.125 GiB。需要区分同权重抢占后的换出／取回、权重更新后的重建，以及保留整套旧权重继续采样三种方案。最后一种要继续占用旧权重与旧 KV，并处理样本滞后；不是无条件复用 1.125 GiB 就省掉重算。重建时间应从第 2、8 章的 prefill 工作与实测推算，不能用缓存容量直接当作 HBM 读取量。

资源配比也要算到有效输入：假定生成能力为 12 条轨迹／秒，验证器为 6 条／秒，学习端为 8 条／秒；验证后又有 25% 因题设中的版本准入规则不可用，则稳定供给上界为 `min(8, min(12,6)×0.75)=4.5` 条／秒。继续扩生成卡不能提高这一上界，还可能堆积队列。这里的过滤位置、比例和单位都是教学假设，不是说 AReaL 必然丢弃四分之一数据，也不把轨迹数当作相同 token 工作量。

## 放回既有实验

第 5.1／实验 5-1 为归约变体增加数值对照；第 8.1 的批处理解释为什么同一请求会遇到不同形状。第 10.5／实验 10-8 画 token、权重版本与 KV 的时间线，计算交接和重建；实验 10-9 先检查重复运行、batch 变化、跨引擎三种差异，再逐项开启确定性路径和 Routing Replay。保留效率、正确性与失败配置，不仅记录开关。

Qwen3 Dense 用于 batch 变化的基础对照，MoE replay 沿已支持的 Qwen3-30B-A3B 配方。V4／K3 仍是全书架构与资源主例，但上述指南的测试名单不能证明它们在任意后端组合上已获得相同保证。整段内容解释既有优化的适用边界，没有增加一个确定性技术专章。
