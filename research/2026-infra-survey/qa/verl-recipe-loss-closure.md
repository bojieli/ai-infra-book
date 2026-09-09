# 实验 10-8：固定 verl 配方的 loss 与更新闭合

2026-09-09。仅核对 `verl@d040717b21af2e23e8e789a3e354cff2394ae2de` 的已封存 main/control 配方：单卡、CP/SP=1、DP=1、FSDP `NO_SHARD`。**每步四个 prompt、各两次生成，形成一个八回答 mini batch；八个单回答 micro batch 共用 20 个有效回答 token 的分母，累积梯度后裁剪并调用一次 AdamW 更新。** 本轮没有执行框架、模型或 GPU。

[证据包](../../../references/framework-history/2026-09-09/verl-recipe-loss-closure/README.md)保存九个固定提交原文件、精确选读范围与本地证据 SHA。实验 `patch/` 的四个原件均匹配 `sources.json` 的 `original_sha256`，下列原件行号不是补丁后行号。

## 已闭合的调用路径

| 固定提交中的位置 | 本配方执行含义 |
| --- | --- |
| 原 `ray_trainer.py:1327–1376` | `ppo_mini_batch_size=4` 乘 `rollout.n=2`，传入 global/mini=8、epochs=1。不是两次四回答更新。 |
| `engine_workers.py:606–645、712–714` | 将 micro=1、dynamic=False 注入 engine；构造 `partial(ppo_loss, config=actor_config)`；`update_actor` 进入 `TrainingWorker.train_mini_batch`。 |
| 同文件 `242–313、342–375`；`engine/base.py:113–132` | 八回答仅形成一个 mini batch；BaseEngine 先清梯度，调用完整 forward/backward batch，随后一次 optimizer step。 |
| 原 `transformer_impl.py:719–772、1545–1597` | 切微批前求 `loss_mask.sum()`，保存 DP SUM 后的 `batch_num_tokens`；八个微批依次算 loss 并 backward，不在循环里更新参数。 |
| `workers/utils/losses.py:57–144`；`core_algos.py:1285–1376、1140–1206` | `ppo_loss` 把计数写入 global_batch_info；vanilla policy objective 调用 token-mean 聚合：`masked_sum(loss,mask)/batch_num_tokens*dp_size`。 |
| 原 `transformer_impl.py:777–829、491–496`；`workers/config/optimizer.py:298–351` | 全批累积后按上限 1.0 裁剪，有限梯度才更新；生效 optimizer 为 `torch.optim.AdamW`。bf16 路径没有 fp16 GradScaler。 |

主任务 GRPO、控制任务 `reinforce_plus_plus` 改变 advantage 估计；两者生效 `policy_loss.loss_mode` 都是 `vanilla`，不能由控制算法名推成另一个 REINFORCE loss。entropy 系数零，KL loss 关闭。这里的逐 token policy-ratio clipping 与最后的梯度范数裁剪是两件事。

## 20 个 token 的分母与不等长回答

`workers/utils/padding.py:23–94` 令 `loss_mask=response_mask`；`ppo_loss` 用同一回答 mask。读取 main/control 的 `tensor-export.json`，对两步的四个训练批重数，结果均为：

```text
封存顺序的回答长度：2, 3, 2, 3, 3, 2, 3, 2
有效回答 token：20（含每条回答末尾的结束 token 151645）
有效 input token：366（prompt + response，用于相应计算量，非 loss 分母）
每更新：1 个八回答 mini batch → 8 个单回答 micro batch → 1 次 optimizer 更新
```

分母不是回答数 8、最大 response 长度 16、padding 后的 128 或 input 总数 366。每微批贡献 `Lᵢ=Σⱼℓᵢⱼ/20`；八次 backward 累积 `∇ΣᵢLᵢ`，不能再除以 8。若写成每回答的 token 平均 loss，短回答系数为 2/20=10%，长回答为 3/20=15%，并非每回答 1/8。系数不代表各回答实际梯度向量或范数必然成比例。

用真实长度、**虚构的教学标量**说明：设短回答每 token 的 loss 为 `θ/5`，长回答为 `2θ/5`。四条短回答共 8 token、四条长回答共 12 token，累积后 `L=[8θ/5+24θ/5]/20=8θ/25`，梯度 0.32。若每微批先各自取均值、再平均八份，会变成 0.30；若用了共同分母又除以 8，则为 0.04。保持分母 20 时，仅把相同样本重新分成 1、2、4、8 条一组，精确分数结果不变。这个自写标量核验没有替换实际 advantage 或运行框架，也不证明 GPU 改微批后逐位一致。

## 必须保留的执行边界

实际 actor 配置 `use_no_sync_for_gradient_accumulation=False`，main/control 的 `stdout.log` 第 93 行一致；`use_dynamic_bsz=False` 在第 180 行。原 `_gradient_sync_context:687–717` 仅当开关 True 时对非最后微批进入 no_sync。**不能把“前七个微批不通信、最后一个同步”写成这次实跑的行为。** world size 1 自动 NO_SHARD 的日志分别在 main 第 986 行、control 第 991 行，本配方没有跨卡同步收益证据。

已有实验的 optimizer state step 为 1、2；主任务梯度为零，FP32 变化来自 AdamW 衰减；控制任务裁剪前 norm 约 1.618257、0.049961，前者触发上限裁剪。观测补丁在裁剪前/更新后记录，没有替换 loss 或 optimizer 计算。这些是原有实跑结果，不是本轮新实验，也不支持质量改善结论。没有 micro size 的 A/B 运行或每次训练 forward 的完整 loss 张量，因而不声称独立重建了全部模型梯度；CP/DP>1、异步或大型模型另有证据要求。

## 接回提纲与核验

第 10.5.1／实验 10-8 只需补上“4 prompt×2回答 → 8微批 → 同一20-token分母 → 一次裁剪/更新”这个解释，以及 no_sync=False／单卡边界。它说明微批怎样控制执行资源，同时保持训练目标；无需增加算法或框架专题。

`python references/framework-history/2026-09-09/verl-recipe-loss-closure/verify.py` 已通过：九个固定原件 SHA/HTTP/URL、26 个本地证据 SHA、四个 patch 原件身份、关键 AST 调用顺序/分母表达式、四个训练批 mask 计数及精确分数标量例。结果在 `verification.json`，实际阅读范围在 `reading.json`。AST 检查属于证据一致性检查，不是程序语义形式证明。本轮未修改大纲、实验原件或 Git，补读到此收束。
