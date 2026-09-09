# speculative-budget — 

输入：`{"baseline_token_ns": 1000000, "options": [{"accepted_counts": [1, 3], "commit_ns": 0, "draft_ns": 100000, "id": "draft-1", "verify_ns": 1000000}, {"accepted_counts": [4, 3, 9], "commit_ns": 0, "draft_ns": 100000, "id": "draft-2", "verify_ns": 1150000}, {"accepted_counts": [64, 48, 36, 27, 81], "commit_ns": 0, "draft_ns": 100000, "id": "draft-4", "verify_ns": 1400000}], "output_tokens": 1, "setup_ns": 2000000}`

时长与接受直方图为教学输入；结果是有限输出请求的精确期望，不是实测延迟。

| 结果 | 值 |
| --- | ---: |
| output_tokens | 1 |
| baseline_ns | 1,000,000 |
| optimal_expected_ns_exact | `"1000000"` |
| expected_speedup_exact | `"1"` |
| first_action | `"baseline"` |
| preparation_probability_exact | `"0"` |
| fixed_best | `"baseline"` |

| 策略 | 期望完成ns | 期望轮数 | 期望草稿数 | 期望截断产出 | 使用准备概率 |
| --- | --- | --- | --- | --- | --- |
| adaptive | 1000000 | 1 | 0 | 0 | 0 |
| baseline | 1000000 | 1 | 0 | 0 | 0 |
| draft-1 | 3100000 | 1 | 1 | 3/4 | 1 |
| draft-2 | 3250000 | 1 | 2 | 21/16 | 1 |
| draft-4 | 3500000 | 1 | 4 | 525/256 | 1 |

| 剩余输出 | 已准备 | 选择 | 期望剩余ns |
| ---: | --- | --- | --- |
| 1 | False | baseline | 1000000 |
| 1 | True | baseline | 1000000 |

计量条件：

- 有限输出上限的教学期望模型；每个候选的连续接受长度直方图与成本在各轮、各历史位置保持不变。分布不是由单一平均接受率推断，默认计数特意构造自独立3/4接受概率。
- 状态为剩余输出数和是否完成草稿准备；首次选择草稿支付setup一次，普通decode不触发准备。所有草稿选项共享同一准备状态与费用，不代表多个独立检查点可免费互换。
- 每轮产出a+1，交付min(remaining,a+1)；末轮截断不减已付起草、验证和提交费用。剩余为0时不启动任何工作。不模拟随机EOS、prefill、工具、排队或任务成功率。
- Bellman递推逐状态最小化期望完成时间，基线也是候选；各固定长度策略另行递推，不能用输出数乘稳态每token时间代替有限请求。仅在给定平稳成本／概率与单请求目标下最优，不是已部署在线学习策略。
- 时长和直方图均为显式教学输入，未从官方模型FLOPs或硬件峰值推定实际延迟；模型矩阵与KV工作另见speculative-round。

固定来源：

