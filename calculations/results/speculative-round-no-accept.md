# speculative-round — 

输入：`{"accepted_counts": [10, 0, 0, 0, 0], "baseline_token_ns": 50000, "commit_ns": 10000, "draft_ns": 40000, "draft_tokens": 4, "history": 1024, "model": "qwen3-8b", "remaining_output_tokens": null, "verify_ns": 100000}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| rounds | 10 |
| total_drafted_tokens | 40 |
| accepted_draft_tokens | 0 |
| draft_acceptance_fraction_exact | `"0"` |
| mean_accepted_drafts_exact | `"0"` |
| mean_delivered_tokens_exact | `"1"` |
| delivered_tokens | 10 |
| total_speculative_ns | 1,500,000 |
| matched_baseline_ns | 500,000 |
| time_per_delivered_token_exact_ns | `"150000"` |
| unweighted_round_time_per_token_exact_ns | `"150000"` |
| matched_time_speedup_exact | `"1/3"` |
| target_verify_rows | 5 |
| target_verify_matrix_flops_per_round | 78,709,719,040 |
| target_verify_matrix_flops_total | 787,097,190,400 |
| matched_serial_matrix_flops_total | 157,407,641,600 |
| target_peak_kv_bytes | 151,732,224 |
| target_verify_new_kv_bytes | 737,280 |
| total_discarded_target_kv_bytes | 5,898,240 |

| 接受草稿 | 次数 | 实际交付 | 保留新增KV bytes | 丢弃新增KV bytes | 匹配串行FLOPs |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 10 | 1 | 147456 | 589824 | 15740764160 |

计量条件：

- 计量一个固定起点history的轮次分布，accepted_counts[a]是连续接受a个草稿的观察次数／教学次数，不由独立位置接受概率推断，也不是顺次增长历史的完整请求回放。
- 目标验证输入为一个待处理token加k个草稿，共k+1行，并为所有行计算logits。每轮产出a个接受草稿及一个补偿／额外token，尚未考虑EOS时为a+1；显式remaining_output_tokens只截断交付，验证工作仍已执行。
- 规范化回滚约定：起点history条已缓存，最后输出token待处理；提交m个新输出后只保留m条新增输入KV，最新输出仍待处理。验证分配k+1条，保留m条、丢弃k+1-m条。引擎可能采用其它预分配／提交布局，需另核。
- baseline比较交付相同m个token的逐次目标decode，逐步增长history计算矩阵工作；验证块使用因果配对，不能把其工作当成m次单token简单相乘。
- draft/verify/commit和baseline_token_ns均为独立教学时长，按串行相加；草稿模型形状／状态、运行时重叠与真实检查点不在本例。目标矩阵工作来自官方Qwen配置，不能从计数推出草稿准确率。
- 总体每token时间为总时间/总交付，不是各轮time/tokens等权平均；接受率只数草稿，平均交付包含额外token。这里验证收支，不实现拒绝采样或证明目标采样分布一致。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
