# 同任务质量与资源比较：现有基线及待运行配对

已有证据：固定Qwen3-8B BF16检索实验，8个不同任务、每任务4次自然生成（并发/重复条件），32次中28次严格JSON评分正确。n512-r0四次均错，其他七题均对。不是32个独立任务，也不是任何通用能力结论。calibration和fixed-length计时执行不进入质量样本。baseline.py调用公共kv_quality的来源与评分验证，再逐原始输出重新评分。

资源连接：原prompt_token_ids和完整output_ids（含EOS）在声明冷请求、串行采样、last-position head策略下代入Qwen8工作量；prefill一次，decode为G−1次。资源账与实际应用latency并列，不从FLOPs推时延、不把串行次数当观测modelcalls。两个测试核评分/重复身份与最终KV边界。

最小配对实验：选择已有官方配置的Qwen3-32B作为第二模型。复用完全相同的8组messages与expected，严格JSON评分；按原脚本自然模式temperature=0、max_tokens=128、ignore_eos=False，记录完整模板、tokenizer revision、input IDs、output IDs、stop reason、实际耗时和运行环境。模型种子及并发/重复条件按原记录保留；不能重用8B的token IDs作为32B的输入，也不能用fixed-length模式补齐质量样本。必须执行第二模型并保留失败/截断结果，当前尚未运行。

配对报告逐task列两模型正确/错误和请求资源，按任务而非重复次数统计差异。8题仅能提供这一检索任务集上的有限证据，不足以宣称等效或普遍替代；不得因全对而扩大结论。若要判断能力非劣，需预先指定容许差值、置信要求并扩充独立任务，而非重复同8题提高名义样本量。

经济点另需：固定相同负载分布、质量门槛、TTFT/完成延迟SLO、并发与成本单位，保存测量时段/失败/排队记录。当前baseline没有第二模型结果或共同成本记录，economic_winner=null。不能用不同条件的厂商分数、容量通过或每token FLOPs冒充S01/S06验收。

专家top-k变体（S11）不能直接复用这组已训练Dense模型比较。需在共同训练数据/预算下得到变体权重，或将仅更改top-k的推理消融明确标为消融；保留路由/输出/评分，分别讨论训练变化和推理变化。现有未训练颗粒度变体没有这些记录。

执行包已准备：prepared-run/run.py 与 probe.py逐字节复制已锁原脚本，保留calibration、warmup、natural/fixed交错及seed808随机试次顺序。prepare.py重新调用原fixture生成函数，逐任务校验messages/expected/seed/rows/ID与原基线一致；8B token IDs不复制到目标任务清单。manifest列目标32B config SHA与所有工件SHA。必须使用目标固定权重及tokenizer，并确认运行环境符合协议；实验包准备成功不等于目标运行时已验证。

当前本机观察：arm64，103079215104字节内存；默认Python可发现mlx，未发现torch/vllm/transformers；默认HF缓存仅发现Qwen3-8B-MLX-4bit而未发现32B。这里只检查当前本机与默认缓存，不宣称全部远端或其他环境均不可用。未用MLX4bit替代原BF16/vLLM基线。第二模型尚未运行。
