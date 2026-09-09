# I17／I18／I21 精选回答路径核对

2026-09-09。只读题表及其直接引用的案例和固定资料；本次只新增这份报告，没有修改问题、案例、框架资料或计算程序，没有增加公司原题，没有运行框架或联网补规格。适用的 AGENTS.md 检查沿用同轮审查，未发现。

**结论：未发现算术错误。I17 有 1 项值得补明的概率比定义；I18 与 I21 在已声明的教学条件下讲通。** 后两题的实际版本支持、质量与尾延迟仍待测，不能把这些未测条件当成当前算例的错误。

| 路径 | 判断 | 当前边界 |
| --- | --- | --- |
| I17 概率分母与行为版本 | 计量定义缺口，见下文 | 数学例正确；需要明确正在检查哪一个比值及哪个比值进入 clip |
| I18 rollout 与恢复 | 无新增问题 | 4.5 条／秒是指定过滤位置和能力下的供给上界，不证明全部队列稳定或同等训练质量 |
| I21 路由费用与时限 | 无新增问题 | 费用交点与联合条件均正确；命中／质量独立性和给定完整耗时已明确，不能替代联合实测记录 |

## 唯一修正建议：I17 先给概率比命名，再说分母能否重算

**定位。** [题表](interview-directions.md)第 55 行；[RL 状态案例](../../case-studies/rl-state-and-reproducibility.md)第 15–19 行。题表已经要求区分行为策略、旧训练策略与当前策略，并对齐 token、mask 及 raw／processed logprob，这些要求正确。

案例将“真实行为 logprob＝当前 logprob＝−3”作为基准，错误覆盖行为分母为 −3.25 后得到 `exp(0.25)=1.2840254`，其算术成立。但是接到 PPO／GRPO／AReaL 时，还应先说明这个例子检查的是当前相对行为的比值，而非笼统地把训练端重算 logprob 都判为错。

令 `μ` 是实际产生该 token 的行为分布，`π_old` 是选定的旧训练策略，`π_θ` 是当前策略。仅作为概率身份的代数记号，可以分别列出：

```text
r_behavior = π_θ / μ
r_update   = π_θ / π_old
w          = π_old / μ
r_behavior = r_update × w
```

哪个比值用于更新约束、哪个用于采样分布修正，以及是否 clipping／截断，要由所选 loss 明确规定；**不能由上述代数恒等式推断不同 clipping 位置等价**。使用同一 token、支持集和条件前缀，才有这些逐项关系。

沿原例保留 `log μ=−3、log π_θ=−3、log π_old=−3.25`，则三个数为 `1、1.2840254、0.7788008`。其中 1.284 可以是定义清楚的 `r_update`；只有本来要计算 `r_behavior`，却把行为记录覆盖成旧训练值时，才是原例所批评的分母替换。没有权重更新也不能跳过数值路径与分布定义的检查。

固定 [AReaL 异步指南](../../references/framework-history/2026-09-08/rl-consistency/areal-async-current.html)的 **Decoupled PPO Objective** 明确列出 `use_decoupled_loss` 与 `recompute_logprobs`，并要求前者开启时后者为 true；关闭重算时则复用推理后端 logprob。因此，“保存行为概率”与“训练端另行重算”可以同时需要。这份指南支持上述边界判断，但本次没有追到 loss 源码，不将上面示意符号宣称为当前 AReaL 的完整目标公式。

**可执行修改。** 只需在原案例第 17 行前加一句：“下面先检查当前策略相对实际行为分布的 `r_behavior`；PPO 更新比与采样修正比另按所用 loss 定义。”将题表对应提示收紧为：“分别标明每个概率比的分子、分母、生成／重算位置与 clip 位置，行为记录不被另一份值覆盖。”保留原来的 −3／−3.25 算例，无须增加新题或额外算法小节。

**验收。** 配套 trace 中能分别找到原行为 logprob、重算的旧训练 logprob、当前 logprob 和各自版本／分布定义；同一字段不能在未留身份的情况下被覆盖。Routing Replay 只处理其声明的离散专家选择，不据此推断全部概率比应为 1。

## I18 的供给、采样与恢复核对结果

直接回答见[题表](interview-directions.md)第 56 行；恢复和采样追问在第 69、87 行。

- [RL 状态案例](../../case-studies/rl-state-and-reproducibility.md)第 23–27 行：生成／验证／学习为 12／6／8 条每秒，25% 在验证后按版本准入过滤，`min(8,min(12,6)×0.75)=4.5` 正确。改变过滤位置、轨迹长度分布或准入规则后需要重算，原文已经限定；4.5 是输出上界，不代表以 12 条／秒持续向容量 6 的验证器提交仍能保持有限队列。
- [固定 AReaL 流程](../../references/framework-history/2026-09-08/rl-consistency/areal-grpo-current.html)明确保存每 token 的 logprob／版本，交接时暂停生成、同步权重、更新版本，然后重算 KV 并恢复。它支持保留 token 与复用旧 KV 是两件事；不是对任意后端或任意跨版本训练的保证。
- [长尾与流式案例](../../case-studies/rollout-tail-and-sampling.md)第 15–17 行：两个独立槽只取先完成回答，长回答概率从 1/2 降至 1/4；期望墙钟 13/4＝3.25 秒，合计槽时间 13/2＝6.5 秒，均正确。第 31 行按样本数加权得到梯度 2.5、直接平均为 2，也正确，并已要求 token 归一化时更换分母。
- [恢复案例](../../case-studies/rl-scheduling-and-recovery.md)第 30–39 行：790／490 秒相差一次 300 秒 rollout，依赖轨迹保存在故障角色外、更新尚未提交及可恢复检查点，条件已写明。实际恢复后仍要核对行为版本、优化器、数据位置和准入；不同角色的 GPU·秒未冒充墙钟时间。

没有发现将轨迹条数直接当作等价 token 工作、将抢先完成当作采样无偏，或将数值正确当作已验证收敛的断言。下一步应做的是既有实验的版本／质量验证，本次不另提结构修改。

## I21 的费用与联合时限核对结果

直接回答见[题表](interview-directions.md)第 59 行与[路由案例](../../case-studies/routing-cost-and-completion.md)第 7–42 行。全部输入是假想服务，未把厂商真实单价代入。

独立有理数复算得到：A 通过任务成本 `109/8000=0.013625`；B 全命中 `41/4900≈0.00836735`；B 半命中 `253/9800≈0.02581633`。费用交点为 `1291/1520≈84.9342%`，联合质量和 6 秒门槛为 `45/49≈91.8367%`，与[既有结果](routing-cost-arithmetic.json)一致。

失败调用的费用仍在分子，通过任务数在分母；不是假设独立重试得到成功的期望费用。案例明确了请求命中比例 `h`、前缀 token 命中比例与全部输入缓存比例 `0.95h` 的区别。完成时间 4／12／10 秒是包含排队和生成的整体教学输入，没有重复叠加思考时间。

`0.98h≥0.90` 使用命中与质量独立的教学模型，已经在原文标明。它不保证实际 1000 次回放必然达到该联合比例，也不能用两个实测边际比例相乘替代逐任务联合计数。真实服务仍需记录命中、通过与完成时刻；原案例已要求联合记录，因此本次不将该条件判为缺失。

从原始归档重新选读的 [Claude 缓存文档](../../references/outline-checks/2026-09-07/platform-routing/claude-prompt-cache.html)确实将输入分成 cache read、cache creation 与剩余 input；[Gemini 价格页](../../references/outline-checks/2026-09-07/platform-routing/gemini-api-pricing.html)确实标明生成计价包含 thinking。二者只支持字段去重方法，不能推导出相同 usage schema，案例也没有这样外推。价格、缓存预热／写入／存储和工具费在真实合同下仍须另补。

## 阅读范围与复算记录

题表按 I17／I18／I21 的三行、相关追问及直接引用读取；四份上述 case-studies 全文读取。`calculate_routing_cost.py` 全文静态读取，**没有运行它**，因为其主入口会写共享结果；另用本轮临时内存中的 Fraction 算式独立比较既有 JSON，未写派生脚本。

固定资料选读范围：AReaL async 的 article 派生文本第 18–87 行，重点为部分轨迹、版本滞后与重算开关；GRPO 的 article 派生文本第 411–435、832–846 行，分别对应样本字段与权重交接；Thinking Machines 原文的 True on-policy RL 段；Claude 去掉 script/style 后派生文本第 823–867 行；Gemini 同法派生文本第 241 行附近的包含 thinking 计价标签。派生行号只用于复述本次选读，真实定位以原始页面标题和字段为准。此前论文及源码的阅读范围另看各自 README；本次没有重新通读 RollPacker／RobustRL 论文或全部实现。

本轮独立算术检查：`exp(0.25)`；供给 `9/2`；四种回答组合的概率与槽时间；样本权重梯度 `5/2`；恢复 `790/490` 秒；I21 三项费用和两个精确交点。结果均与已声明教学算例相符。未产生框架运行、质量或 SLO 的新证据。

关键输入 SHA256：

```text
interview-directions.md
  f82ac26fd8805b522b68a3678a3dfe89130b395fcae70630048fa5c88f555af7
case-studies/rl-state-and-reproducibility.md
  fc13b00a1c6740cbf2be67b3f41987c36603241e1928f67e9ae12df8b5ef466b
case-studies/rollout-tail-and-sampling.md
  e4c939ffe78f5fea733e0747d64a6b2b1b1a5d12d0e8dfcd6e48d06dca399574
case-studies/rl-scheduling-and-recovery.md
  f5e4c46ecf9402576c1b8a33c35cd13ce763cb1e4d336de4ce88da4ac5f87380
case-studies/routing-cost-and-completion.md
  6290b8bd11961d25f082fd4a3a20bd3ba9ac962cfd6480844809488b0169b029
research/2026-infra-survey/routing-cost-arithmetic.json
  17760500aa6570a5b9dc7c0b1f7ec3927114ea7b620b18390eb4b67707f421c3
rl-consistency/areal-async-current.html
  31af46c71e0282b3979e464af56c96ed9b0600484813119efebf76858d15f08e
rl-consistency/areal-grpo-current.html
  0b772a961e02c1fdc1f8d6ee54fc76e4a8df50f752b42a6de2d09d277e98dc29
platform-routing/claude-prompt-cache.html
  e895b3701b35ef833389051f9b014c59335defd2785978ae06a67c68da9f0195
platform-routing/gemini-api-pricing.html
  c89e8db6293d8cd1c8ccf29548269c9f1dd2a6600854a6af07b180325741550a
```
