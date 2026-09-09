# qwen-rl-cycle-matrix — qwen3-235b-a22b

输入：`{"accepted_samples": 16, "head_strategy": "dense", "output_tokens": 256, "prompt_tokens": 1024, "prompts": 8, "reference_passes": 1, "rollout_replicas": 1, "samples_per_prompt": 4, "teacher_passes": 0, "update_epochs": 1}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| generated_samples | 32 |
| accepted_samples | 16 |
| acceptance_fraction | 0.5 |
| generated_output_tokens | 8,192 |
| accepted_output_tokens | 4,096 |
| training_input_tokens_per_epoch | 20,464 |
| supervised_tokens_per_epoch | 4,096 |
| prefill_calls_per_sample | 1 |
| decode_calls_per_sample | 255 |
| first_decode_matrix_flops | 1,481,358,966,784 |
| last_decode_matrix_flops | 1,506,394,767,360 |
| rollout_matrix_flops | 1,805,377,490,386,944 |
| cycle_matrix_flops | 6,420,684,167,184,384 |
| matrix_flops_per_accepted_sample | 401,292,760,449,024.0 |
| matrix_flops_per_accepted_output_token | 1,567,549,845,504.0 |
| policy_parameter_state_bytes | 4,231,685,422,080 |
| bf16_weight_snapshot_bytes | 470,187,269,120 |
| independent_unicast_weight_sync_bytes | 470,187,269,120 |
| verifier_work | `null` |
| complete_cycle_flops | `null` |
| predicted_cycle_seconds | `null` |

| 阶段 | 样本 | 次数 | 矩阵 FLOPs |
| --- | ---: | ---: | ---: |
| rollout_prefill | 32 | 1 | 1424438889283584 |
| rollout_decode | 32 | 255 | 380938601103360 |
| reference_scoring | 32 | 1 | 1846122670718976 |
| teacher_scoring | 32 | 0 | 0 |
| policy_update | 16 | 1 | 2769184006078464 |

计量条件：

- 教学 RL 批次：所有 prompt 和 response 等长，无 EOS 提前停止、重试、跨样本前缀共享或 speculative decoding。先生成全部候选再评分／筛选；拒收样本仍消耗 rollout 和评分。accepted_samples 是已声明的本批整数结果，不用概率倒推一个确定的成功数。
- prefill 最后位置产生第一个输出，随后 G-1 次 decode；不再把最后一个已生成 token 喂回模型。Qwen 有效因果注意力随历史呈仿射，首尾等差求和严格复现逐步矩阵计量；专家路由采用已有 balanced 情景，无容量 padding。
- 训练／评分输入长度 P+G-1，标签是 G 个输出，位置从 P-1 至 P+G-2。普通 dense head 计算全部位置；compact 假设只对这 G 个位置计算 head，backbone 仍完整执行。
- reference 和 teacher 是与 policy 相同配置的独立快照，每 pass 对全部候选做 teacher-forced 前向；次数可为零。仅报告矩阵工作，不含 log-softmax、KL、优势估计、奖励／规则验证或辅助损失，也不冒充实际奖励模型配置。
- update_epochs 次完整遍历已接受样本，计前向与反向矩阵；批次均为分析聚合规模，不代表能同时放入某张卡。优化器更新、激活、重计算、微批调度、通信及等待另算，未用 FLOPs 直接预测周期时间。
- 周期末同步一次完整 BF16 policy 权重到每个 rollout 副本，独立 unicast 发送量为副本数乘快照大小；不含优化器状态，不假定广播树、增量更新或参数转换。policy 状态与 rollout/reference/teacher 常驻内存不混加成设备峰值。
- 有效样本归一化包含拒收候选开销；质量、真实吞吐和各阶段有效供给未知，不能仅按工作量大小决定增配哪类设备。本例不声称复现 V4/K3 的 RL 系统。

固定来源：

- [configs/models/qwen3-235b-a22b/config.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/config.json)，SHA256 `0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4`。
- [sources/qwen3-235b-a22b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/model.safetensors.index.json)，SHA256 `53dd34fac4a29fc7ee58fa9d92c7892ea6884431c3bd3d0dc93def7bbd0b8b78`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
