# 为什么原自建成本偏高：优化审计

原比较是**未启用推测解码、效率未经校准的分析基线**，不能代表优化后的自建成本，也不足以认定 API 更便宜或某款 GPU 最优。原算术结果保留用于复现；结论以本审计限定。可复算的时间归因与条件敏感性见 [AUDIT-RESULTS.md](AUDIT-RESULTS.md)，机器记录见 [audit.json](audit.json)。

## MTP / 推测解码确实漏算了

[DeepSeek V4 的 SGLang 配置](https://github.com/sgl-project/sglang/blob/main/docs_new/cookbook/autoregressive/DeepSeek/DeepSeek-V4.mdx)覆盖 Flash 与 Pro 的 MTP 推测解码；原比较只研究 Flash 与 K3，Pro 不扩入本题。[K3 的实现说明](https://www.lmsys.org/blog/2026-07-27-kimi-k3-day0-support)提供独立训练的 DSpark 草稿模型与块验证。两者都可通过一次目标模型验证提交多个 token，但不能把 K3 的 DSpark 草稿直接当成 V4 原生 MTP 头。原脚本给 Flash 的完整 checkpoint 预留了容量，却未执行 MTP、未计算加速；K3 也完全未计算推测收益。

一次验证周期平均提交 A 个最终输出 token，耗时 t_draft + t_verify + t_restore/schedule，则净 decode 加速 S = A×t_plain / (t_draft+t_verify+t_restore/schedule)。A 包含该实现实际提交的所有 token，不能把草稿长度、接受率或接受长度直接当成 S。批量验证可以摊薄权重读取、kernel 启动和同步，但仍需计算多个位置的 attention、专家与验证工作。

K3 的实现还用 ReplaySSM 降低验证窗口中的 KDA 状态保存成本；该收益针对临时状态，不是把全部 KV 或模型显存按相同比例缩小。[DSpark 方法说明](https://www.lmsys.org/blog/2026-07-06-dspark-sglang/)解释了为何负载增大后应按边际成本裁剪验证长度。实际 200K／1M 的近满历史、Agent 任务、接受长度分布、卡型和并发必须一起测；不能把短上下文的加速比例直接迁移。24×7 有工作不等于小 batch 的 latency-bound 阶段已经充分利用硬件。

## 比遗漏 MTP 更影响原结论的假设

- central 给 K3 每层固定加 150 µs，共 13.95 ms／token，未用生产 trace 校准。逐层算子融合、通信融合和执行重叠会改变这一项，不能把它视作优化后常数。
- 每增长窗口 10% 即全量重建不是用户要求，也不是 K3 的必然行为。它在 200K／1M 情景分别摊入约 9.18／9.26 ms／输出。长时间满窗口确实需要历史管理，但应按真实压缩、前缀保留和 checkpoint 重放策略计费。若改重建策略，GPU prefill 与 API 缓存命中必须同时更新。
- 原 K3 prefill 沿用 compact MLA 的逻辑矩阵口径；实际后端可能采用不同的 prefill 路径，尚不能作为校准速度。tile=32、矩阵效率、专家不均衡等也是叠加的未校准参数。
- DCP、低比特权重与 FP8 MLA 缓存已部分计入；EP 放置、PD 分离调度、融合／重叠、动态状态池和推测临时状态未完整建模。原模型固定五份 KDA 状态槽、20% 显存余量，不能代表每种优化配置。
- 原候选只枚举 2 的幂次 batch，并要求至少 30 token/s。上述开销容易让候选刚好跌出速度门槛，迫使并发减半；硬件排序因此会出现离散跳变。

[SGLang K3 cookbook](https://docs.sglang.io/cookbook/autoregressive/Moonshotai/Kimi-K3)给出了后端、DCP、PD、状态池及推测配置的组合约束；这些优化需要在同一个可运行配置中验证，不能把不同配置的最好数字叠乘。优化审计不将零逐层开销当作新 central，不凭空设定 MTP 的接受率，也不将固定并发敏感性当作显存可行性证明。

## 当前可以回答什么

原结果中 K3 比 API 贵约 2.2／4.0 倍，首先反映了上述未优化基线和附加假设，不能归因为模型本身必然昂贵。敏感性把 decode 的净加速单独变化，保留原 prefill 成本：这是可复算的条件题，不是新的部署报价。生产级比较还须重算草稿及验证容量、并发与硬件选择，并用真实轨迹校准重建策略和 kernel 时间。

GPU 零售租金与官方 API 售价也不是同一供应链成本：运营商采购条件和内部部署成本未公开，不能假定其折扣、补贴或利润来填平差额。现有证据足以撤回“未优化基线代表自建成本”的解释，尚不足以宣布哪款卡或 API 必然最便宜。
