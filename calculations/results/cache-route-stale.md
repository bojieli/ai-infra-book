# cache-route — 

输入：`{"full_compute_ns": 180000000, "hit_probability": "9/10", "host_gpu_bytes_per_second": 25000000000, "lookup_ns": 10000000, "model": "qwen3-8b", "prefix_tokens": 8192, "queue_a_ns": 80000000, "queue_b_ns": 20000000, "remote_bytes_per_second": 5000000000, "requests_per_second": 16, "retrieval_after_queue": false, "slo_ns": 220000000, "suffix_tokens": 256, "warm_compute_ns": 10000000}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| prefix_state_bytes | 1,207,959,552 |
| cold_matrix_flops | 138,406,909,706,240 |
| warm_matrix_flops | 4,813,831,012,352 |
| saved_matrix_flops | 133,593,078,693,888 |
| remote_transfer_ns_exact | `"1207959552/5"` |
| host_gpu_transfer_ns_exact | `"1207959552/25"` |
| remote_equal_recompute_bytes_per_second_exact | `"13107200000000000/1428837"` |
| remote_payload_demand_bytes_per_second | 19,327,352,832 |
| remote_payload_demand_strictly_below_bandwidth | `false` |
| a_valid_hit_ns_exact | `"90000000"` |
| a_all_tiers_miss_ns_exact | `"260000000"` |
| a_expected_ns_exact | `"107000000"` |
| a_p99_ns_exact | `"260000000"` |
| a_slo_pass_probability_exact | `"9/10"` |
| a_mean_better_than_b | `true` |
| a_p99_passes_slo | `false` |
| strict_mean_hit_probability_threshold_exact | `"6/17"` |
| fastest_known_valid_path | `"A valid HBM"` |

| 路径 | GPU等待ns | 状态取回耗时ns | 首token ns |
| --- | ---: | --- | --- |
| A valid HBM | 80000000 | 0 | 90000000 |
| B recompute | 20000000 | 0 | 200000000 |
| B remote through host | 20000000 | 7497757312/25 | 7747757312/25 |
| A CPU copy survives | 80000000 | 1207959552/25 | 90000000 |

计量条件：

- 同一官方Qwen前缀和新suffix的矩阵工作独立复算；full/warm计算时间是教学输入，不由FLOPs比例外推。只预测首token，不是完整生成或任务质量。
- 远端整份状态先到host，再经H2D到GPU，lookup和两段复制串行；默认可与GPU队列等待重叠，完成为max(queue,ready)+warm。retrieval_after_queue则等待queue后才开始取回，不能混用两种依赖。
- ready字段是取回自身耗时；默认从到达起算，after_queue时从GPU可执行时刻起算。HBM已命中与CPU副本仍在是分别声明的有效状态，不把GPU淘汰当作全部失效。
- A失效概率采用两点分布：有效HBM命中或全部层级失效重算，无额外失败探测成本。p是校准输入而非框架评分；排队与淘汰相关性、部分前缀命中及事件恢复未模拟。
- p99按最小累计概率达到99%的值，等号保留。平均优于B不保证尾延迟SLO；概率阈值为未裁剪代数值，须与0≤p≤1共同判断。
- 带宽和请求率是有效服务教学假设；共享链路仅检查payload需求，未建队列。单请求有利不保证持续服务，需求严格低于带宽也不证明SLO。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
