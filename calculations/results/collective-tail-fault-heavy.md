# collective-tail — 

输入：`{"exchange_speedup": 2, "model": "qwen3-8b", "observations": [{"count": 97, "exchange_ns": 400000, "name": "normal", "ready_ns": [0, 0, 0, 0], "recovery_ns": 0}, {"count": 1, "exchange_ns": 400000, "name": "late-rank", "ready_ns": [0, 0, 0, 2000000], "recovery_ns": 0}, {"count": 2, "exchange_ns": 400000, "name": "recovery", "ready_ns": [0, 0, 0, 0], "recovery_ns": 10000000}], "post_compute_ns": 0, "tokens": 1024}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| payload_bytes_per_rank | 8,388,608 |
| ranks | 4 |
| observation_count | 100 |
| baseline_mean_exact_ns | `"620000"` |
| faster_exchange_mean_exact_ns | `"420000"` |
| aligned_ready_mean_exact_ns | `"600000"` |
| baseline_p99_exact_ns | `"10400000"` |
| faster_exchange_p99_exact_ns | `"10200000"` |
| baseline_max_exact_ns | `"10400000"` |

| 策略 | 平均 ns | p50 ns | p99 ns | max ns |
| --- | ---: | ---: | ---: | ---: |
| baseline | 620000 | 400000 | 10400000 | 10400000 |
| faster_exchange | 420000 | 200000 | 10200000 | 10200000 |
| aligned_ready | 600000 | 400000 | 10400000 | 10400000 |
| no_recovery | 420000 | 400000 | 400000 | 2400000 |

计量条件：

- 官方hidden_size确定每rank BF16 [tokens,H]载荷；就绪、交换、恢复与后续计算时间为显式教学记录，不由payload或峰值带宽推断。
- 屏障教学模型：全部rank就绪后交换，随后串行恢复和后续计算。不能提前分块推进；真实集合通信需逐rank时间线校准。rank_wait之和是rank时间，不能加到墙钟时间。
- 四策略逐条配对：仅缩短交换、将就绪对齐到该条最早时刻、消除显式恢复，以及原始。它们是条件式反事实，不保证部署可实现。恢复不会随交换加速自动缩短。
- count为有限记录的整数重复次数；p50/p99取排序后ceil(p*N)项，不插值。保留同一条记录中就绪、交换和恢复的联合关系，不相加边际分位数、不假设独立、不拟合故障概率。
- 观察分位数不等于总体SLO或统计置信结论；未模拟多次集合通信、故障重试、检查点回滚或完整训练作业。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
