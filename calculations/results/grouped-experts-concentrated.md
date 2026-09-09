# grouped-experts — 

输入：`{"counts": null, "model": "qwen3-235b-a22b", "participants": 8, "placement": "contiguous", "replicas": null, "routing": "concentrated", "tile_k": 32, "tile_m": 64, "tile_n": 128, "tokens": 128}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| experts | 128 |
| active_experts | 8 |
| token_expert_tasks | 1,024 |
| additional_physical_copies | 0 |
| rerouted_token_expert_tasks | 0 |
| replica_weight_bytes | 0 |
| replica_weight_bytes_per_rank | `[0, 0, 0, 0, 0, 0, 0, 0]` |
| equivalent_full_model_kv_tokens_per_rank_floor | `[0, 0, 0, 0, 0, 0, 0, 0]` |
| baseline_max_rank_padded_flops | 38,654,705,664 |
| max_rank_padded_flops_reduction | 0 |
| added_padded_flops | 0 |
| padded_token_rows | 1,024 |
| valid_matrix_flops | 38,654,705,664 |
| padded_matrix_flops | 38,654,705,664 |
| padding_work_ratio_exact | `"1"` |
| max_rank_valid_flops | 38,654,705,664 |
| max_rank_padded_flops | 38,654,705,664 |
| valid_rank_imbalance_exact | `"8"` |
| padded_rank_imbalance_exact | `"8"` |
| distinct_expert_weight_bytes | 301,989,888 |
| tile_schedule_weight_read_bytes | 603,979,776 |
| tile_schedule_next_level_bytes | 920,649,728 |
| extra_weight_tile_reads_bytes | 301,989,888 |

| rank | 非空物理副本 | token—专家任务 | 有效FLOPs | 完全补齐FLOPs | 权重tile读取bytes | 接口总bytes |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 8 | 1024 | 38654705664 | 38654705664 | 603979776 | 920649728 |
| 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| 4 | 0 | 0 | 0 | 0 | 0 | 0 |
| 5 | 0 | 0 | 0 | 0 | 0 | 0 |
| 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| 7 | 0 | 0 | 0 | 0 | 0 | 0 |

| 逻辑专家 | 物理副本 | rank | 有效M | 补齐M |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 128 | 128 |
| 1 | 0 | 0 | 128 | 128 |
| 2 | 0 | 0 | 128 | 128 |
| 3 | 0 | 0 | 128 | 128 |
| 4 | 0 | 0 | 128 | 128 |
| 5 | 0 | 0 | 128 | 128 |
| 6 | 0 | 0 | 128 | 128 |
| 7 | 0 | 0 | 128 | 128 |
| 8 | 0 | 0 | 0 | 0 |
| 9 | 0 | 0 | 0 | 0 |
| 10 | 0 | 0 | 0 | 0 |
| 11 | 0 | 0 | 0 | 0 |
| 12 | 0 | 0 | 0 | 0 |
| 13 | 0 | 0 | 0 | 0 |
| 14 | 0 | 0 | 0 | 0 |
| 15 | 0 | 0 | 0 | 0 |
| 16 | 0 | 1 | 0 | 0 |
| 17 | 0 | 1 | 0 | 0 |
| 18 | 0 | 1 | 0 | 0 |
| 19 | 0 | 1 | 0 | 0 |
| 20 | 0 | 1 | 0 | 0 |
| 21 | 0 | 1 | 0 | 0 |
| 22 | 0 | 1 | 0 | 0 |
| 23 | 0 | 1 | 0 | 0 |
| 24 | 0 | 1 | 0 | 0 |
| 25 | 0 | 1 | 0 | 0 |
| 26 | 0 | 1 | 0 | 0 |
| 27 | 0 | 1 | 0 | 0 |
| 28 | 0 | 1 | 0 | 0 |
| 29 | 0 | 1 | 0 | 0 |
| 30 | 0 | 1 | 0 | 0 |
| 31 | 0 | 1 | 0 | 0 |
| 32 | 0 | 2 | 0 | 0 |
| 33 | 0 | 2 | 0 | 0 |
| 34 | 0 | 2 | 0 | 0 |
| 35 | 0 | 2 | 0 | 0 |
| 36 | 0 | 2 | 0 | 0 |
| 37 | 0 | 2 | 0 | 0 |
| 38 | 0 | 2 | 0 | 0 |
| 39 | 0 | 2 | 0 | 0 |
| 40 | 0 | 2 | 0 | 0 |
| 41 | 0 | 2 | 0 | 0 |
| 42 | 0 | 2 | 0 | 0 |
| 43 | 0 | 2 | 0 | 0 |
| 44 | 0 | 2 | 0 | 0 |
| 45 | 0 | 2 | 0 | 0 |
| 46 | 0 | 2 | 0 | 0 |
| 47 | 0 | 2 | 0 | 0 |
| 48 | 0 | 3 | 0 | 0 |
| 49 | 0 | 3 | 0 | 0 |
| 50 | 0 | 3 | 0 | 0 |
| 51 | 0 | 3 | 0 | 0 |
| 52 | 0 | 3 | 0 | 0 |
| 53 | 0 | 3 | 0 | 0 |
| 54 | 0 | 3 | 0 | 0 |
| 55 | 0 | 3 | 0 | 0 |
| 56 | 0 | 3 | 0 | 0 |
| 57 | 0 | 3 | 0 | 0 |
| 58 | 0 | 3 | 0 | 0 |
| 59 | 0 | 3 | 0 | 0 |
| 60 | 0 | 3 | 0 | 0 |
| 61 | 0 | 3 | 0 | 0 |
| 62 | 0 | 3 | 0 | 0 |
| 63 | 0 | 3 | 0 | 0 |
| 64 | 0 | 4 | 0 | 0 |
| 65 | 0 | 4 | 0 | 0 |
| 66 | 0 | 4 | 0 | 0 |
| 67 | 0 | 4 | 0 | 0 |
| 68 | 0 | 4 | 0 | 0 |
| 69 | 0 | 4 | 0 | 0 |
| 70 | 0 | 4 | 0 | 0 |
| 71 | 0 | 4 | 0 | 0 |
| 72 | 0 | 4 | 0 | 0 |
| 73 | 0 | 4 | 0 | 0 |
| 74 | 0 | 4 | 0 | 0 |
| 75 | 0 | 4 | 0 | 0 |
| 76 | 0 | 4 | 0 | 0 |
| 77 | 0 | 4 | 0 | 0 |
| 78 | 0 | 4 | 0 | 0 |
| 79 | 0 | 4 | 0 | 0 |
| 80 | 0 | 5 | 0 | 0 |
| 81 | 0 | 5 | 0 | 0 |
| 82 | 0 | 5 | 0 | 0 |
| 83 | 0 | 5 | 0 | 0 |
| 84 | 0 | 5 | 0 | 0 |
| 85 | 0 | 5 | 0 | 0 |
| 86 | 0 | 5 | 0 | 0 |
| 87 | 0 | 5 | 0 | 0 |
| 88 | 0 | 5 | 0 | 0 |
| 89 | 0 | 5 | 0 | 0 |
| 90 | 0 | 5 | 0 | 0 |
| 91 | 0 | 5 | 0 | 0 |
| 92 | 0 | 5 | 0 | 0 |
| 93 | 0 | 5 | 0 | 0 |
| 94 | 0 | 5 | 0 | 0 |
| 95 | 0 | 5 | 0 | 0 |
| 96 | 0 | 6 | 0 | 0 |
| 97 | 0 | 6 | 0 | 0 |
| 98 | 0 | 6 | 0 | 0 |
| 99 | 0 | 6 | 0 | 0 |
| 100 | 0 | 6 | 0 | 0 |
| 101 | 0 | 6 | 0 | 0 |
| 102 | 0 | 6 | 0 | 0 |
| 103 | 0 | 6 | 0 | 0 |
| 104 | 0 | 6 | 0 | 0 |
| 105 | 0 | 6 | 0 | 0 |
| 106 | 0 | 6 | 0 | 0 |
| 107 | 0 | 6 | 0 | 0 |
| 108 | 0 | 6 | 0 | 0 |
| 109 | 0 | 6 | 0 | 0 |
| 110 | 0 | 6 | 0 | 0 |
| 111 | 0 | 6 | 0 | 0 |
| 112 | 0 | 7 | 0 | 0 |
| 113 | 0 | 7 | 0 | 0 |
| 114 | 0 | 7 | 0 | 0 |
| 115 | 0 | 7 | 0 | 0 |
| 116 | 0 | 7 | 0 | 0 |
| 117 | 0 | 7 | 0 | 0 |
| 118 | 0 | 7 | 0 | 0 |
| 119 | 0 | 7 | 0 | 0 |
| 120 | 0 | 7 | 0 | 0 |
| 121 | 0 | 7 | 0 | 0 |
| 122 | 0 | 7 | 0 | 0 |
| 123 | 0 | 7 | 0 | 0 |
| 124 | 0 | 7 | 0 | 0 |
| 125 | 0 | 7 | 0 | 0 |
| 126 | 0 | 7 | 0 | 0 |
| 127 | 0 | 7 | 0 | 0 |

计量条件：

- 官方Qwen MoE单层gate/up/down矩阵，BF16操作数与FP32 tile累加器。逻辑任务按官方top-k路由直方图，集中／均衡为教学输入，placement只改变专家归属不改变逻辑路由。
- 每个非空专家独立对M/K/N向上补齐指定tile，空专家不启动；完全执行padded tile给矩阵工作上界，真实kernel可跳过部分无效指令，不能当实测issued FLOPs。
- 复用gemm_tiles的output-stationary载荷：每输出tile跨K保留累加器，输出tile之间不保留输入，边界读取只计有效元素。权重随M块重读，A随N块重读；不把补齐FLOPs比例乘到有效字节上。
- 这是选定工作缓冲与下一层之间的访存模型，不自动等于HBM。gate/up分别读输入，中间结果物化，激活非线性、路由、dispatch/combine、数据重排、融合与缓存复用不在本子账。
- 基础placement等量放专家；replicas额外指定相同逻辑专家的rank副本，任务按商和余数均分，余数给原副本优先，每个任务仅执行一次。保留原权重，空闲新副本仍占容量；不是修改top-k。
- 新增权重按单层每物理副本计，KV等价仅将每rank新增容量除以官方全模型BF16 GQA每token容量取整，假定对照保存未切分完整KV，不证明实际EP布局或剩余容量。
- rerouted任务仅表示从基础owner分给新副本的assignment；没有token源rank或身份，不能推断实际网络增减、去重或迁移时间。最忙工作减少也不保证速度提高，未计设备速度、kernel调度和通信。

固定来源：

- [configs/models/qwen3-235b-a22b/config.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/config.json)，SHA256 `0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4`。
- [sources/qwen3-235b-a22b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/model.safetensors.index.json)，SHA256 `53dd34fac4a29fc7ee58fa9d92c7892ea6884431c3bd3d0dc93def7bbd0b8b78`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
