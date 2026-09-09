# kv-restore — 

输入：`{"host_capacity_bytes": 268435456, "model": "qwen3-8b", "next_use_ns": 100000000, "offload_bandwidth": 25000000000, "recompute_ns": 50000000, "restore_bandwidth": 25000000000, "tokens": 1024, "transfer_startup_ns": 10000}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| kv_snapshot_bytes | 150,994,944 |
| input_token_id_bytes | 4,096 |
| replay_backbone_matrix_flops | 14,534,471,319,552 |
| replay_backbone_scalar_flops | 7,078,585,344 |
| replay_special_ops | `{"sin": 131072, "cos": 131072, "rsqrt": 1549312, "negate": 547356672, "exp": 1057554432, "compare_max": 603389952, "mask_decisions": 1207959552}` |
| replay_new_kv_write_bytes | 150,994,944 |
| offload_exact_ns | `"151244944/25"` |
| restore_exact_ns | `"151244944/25"` |
| prefetch_start_exact_ns | `"2348755056/25"` |
| offload_return_stall_exact_ns | `"0"` |
| recompute_start_ns | 50,000,000 |
| recompute_stall_ns | 0 |
| host_snapshot_fits | `true` |

| 策略 | 容量可行 | 恢复等待 ns | KV释放时长 ns | 搬运 bytes | 重算矩阵 FLOPs |
| --- | --- | ---: | ---: | ---: | ---: |
| keep | True | 0 | 0 | 0 | 0 |
| offload_prefetch | True | 0 | 2197510112/25 | 301989888 | 0 |
| drop_recompute | True | 0 | 50000000 | 0 | 14534471319552 |

计量条件：

- 原始token ID与固定权重可用，快照是官方模型BF16完整历史。重算使用标准backbone前向、无lm_head；矩阵、标量和特殊运算分列，不声称这是仅生成KV的最小裁剪图。
- recompute_ns是独立给定的教学服务时长，不从峰值FLOPs推断。重算还读权重和中间状态，不能把KV写字节或token数当全部重算成本。
- next_use_ns是已知的未来使用时刻；offload立即开始，完整复制结束后才释放本地KV，再尽可能晚地整块预取；预取启动时预留整个本地快照，两个方向串行且各有启动。
- 丢弃立即释放原KV，重算尽可能晚开始；重算一开始就预留完整KV容量。因此释放byte*ns只计释放到重新预留的间隔，不将重算期间当空闲显存。
- offload需要host_capacity容纳完整快照，输入token ID按int32另列；keep与recompute假设执行时本地容量可用。未计其它工作对容量和带宽的争用、pinned分配、权重装载或发布同步。
- 三策略展示恢复等待与释放容量时间的权衡，不自动按最短延迟选keep；保留KV可能挤占别的请求，这需要服务队列与容量收益联合评估。next_use未知、预取预测错误和淘汰策略不在本例。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
