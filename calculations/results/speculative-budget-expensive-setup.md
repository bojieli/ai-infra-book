# speculative-budget — 

输入：`{"baseline_token_ns": 1000000, "options": [{"accepted_counts": [1, 3], "commit_ns": 0, "draft_ns": 100000, "id": "draft-1", "verify_ns": 1000000}, {"accepted_counts": [4, 3, 9], "commit_ns": 0, "draft_ns": 100000, "id": "draft-2", "verify_ns": 1150000}, {"accepted_counts": [64, 48, 36, 27, 81], "commit_ns": 0, "draft_ns": 100000, "id": "draft-4", "verify_ns": 1400000}], "output_tokens": 16, "setup_ns": 2000000000}`

时长与接受直方图为教学输入；结果是有限输出请求的精确期望，不是实测延迟。

| 结果 | 值 |
| --- | ---: |
| output_tokens | 16 |
| baseline_ns | 16,000,000 |
| optimal_expected_ns_exact | `"16000000"` |
| expected_speedup_exact | `"1"` |
| first_action | `"baseline"` |
| preparation_probability_exact | `"0"` |
| fixed_best | `"baseline"` |

| 策略 | 期望完成ns | 期望轮数 | 期望草稿数 | 期望截断产出 | 使用准备概率 |
| --- | --- | --- | --- | --- | --- |
| adaptive | 16000000 | 16 | 0 | 0 | 0 |
| baseline | 16000000 | 16 | 0 | 0 | 0 |
| draft-1 | 67455274273446875/33554432 | 10077389773/1073741824 | 10077389773/1073741824 | 1822251675/4294967296 | 1 |
| draft-2 | 134827784397109375/67108864 | 7808721883/1073741824 | 7808721883/536870912 | 14044802727/17179869184 | 1 |
| draft-4 | 67396793001015625/33554432 | 6142485355/1073741824 | 6142485355/268435456 | 399234551151/274877906944 | 1 |

| 剩余输出 | 已准备 | 选择 | 期望剩余ns |
| ---: | --- | --- | --- |
| 1 | False | baseline | 1000000 |
| 1 | True | baseline | 1000000 |
| 2 | False | baseline | 2000000 |
| 2 | True | draft-1 | 1350000 |
| 3 | False | baseline | 3000000 |
| 3 | True | draft-2 | 1775000 |
| 4 | False | baseline | 4000000 |
| 4 | True | draft-4 | 2337500 |
| 5 | False | baseline | 5000000 |
| 5 | True | draft-4 | 2712500 |
| 6 | False | baseline | 6000000 |
| 6 | True | draft-4 | 53196875/16 |
| 7 | False | baseline | 7000000 |
| 7 | True | draft-4 | 242103125/64 |
| 8 | False | baseline | 8000000 |
| 8 | True | draft-4 | 545115625/128 |
| 9 | False | baseline | 9000000 |
| 9 | True | draft-4 | 1220403125/256 |
| 10 | False | baseline | 10000000 |
| 10 | True | draft-4 | 1339184375/256 |
| 11 | False | baseline | 11000000 |
| 11 | True | draft-4 | 94232440625/16384 |
| 12 | False | baseline | 12000000 |
| 12 | True | draft-4 | 408629459375/65536 |
| 13 | False | baseline | 13000000 |
| 13 | True | draft-4 | 881211896875/131072 |
| 14 | False | baseline | 14000000 |
| 14 | True | draft-4 | 1892359559375/262144 |
| 15 | False | baseline | 15000000 |
| 15 | True | draft-4 | 2019527403125/262144 |
| 16 | False | baseline | 16000000 |
| 16 | True | draft-4 | 137612697471875/16777216 |

计量条件：

- 有限输出上限的教学期望模型；每个候选的连续接受长度直方图与成本在各轮、各历史位置保持不变。分布不是由单一平均接受率推断，默认计数特意构造自独立3/4接受概率。
- 状态为剩余输出数和是否完成草稿准备；首次选择草稿支付setup一次，普通decode不触发准备。所有草稿选项共享同一准备状态与费用，不代表多个独立检查点可免费互换。
- 每轮产出a+1，交付min(remaining,a+1)；末轮截断不减已付起草、验证和提交费用。剩余为0时不启动任何工作。不模拟随机EOS、prefill、工具、排队或任务成功率。
- Bellman递推逐状态最小化期望完成时间，基线也是候选；各固定长度策略另行递推，不能用输出数乘稳态每token时间代替有限请求。仅在给定平稳成本／概率与单请求目标下最优，不是已部署在线学习策略。
- 时长和直方图均为显式教学输入，未从官方模型FLOPs或硬件峰值推定实际延迟；模型矩阵与KV工作另见speculative-round。

固定来源：

