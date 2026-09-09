# qwen-binomial-tree-collective — qwen3-8b

输入：`{"bandwidth_bytes_per_second": 50000000000, "batch": 1, "message_dtype": "BF16", "participants": 8, "root": 0, "segmentation": false, "startup_ns": 2000, "tokens": 1}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| activation_shape | `[1, 4096]` |
| message_bytes_per_rank | 8,192 |
| rounds_per_phase | 3 |
| all_reduce_rounds | 6 |
| all_reduce_network_send_bytes | 114,688 |
| all_reduce_global_reduction_adds | 28,672 |
| maximum_rank_send_bytes | 24,576 |
| maximum_rank_receive_bytes | 24,576 |
| all_reduce_startup_seconds | 1.2e-05 |
| all_reduce_bandwidth_seconds | 9.8304e-07 |
| all_reduce_modeled_seconds | 1.298304e-05 |
| dense_tp_all_reduce_calls | 72 |
| dense_tp_serial_collective_seconds | 0.00093477888 |
| measured_collective_seconds | `null` |

| 阶段 | 轮次 | sender → receiver (bytes) |
| --- | ---: | --- |
| reduce | 0 | 1 → 0 (8192); 3 → 2 (8192); 5 → 4 (8192); 7 → 6 (8192) |
| reduce | 1 | 2 → 0 (8192); 6 → 4 (8192) |
| reduce | 2 | 4 → 0 (8192) |
| broadcast | 0 | 0 → 4 (8192) |
| broadcast | 1 | 0 → 2 (8192); 4 → 6 (8192) |
| broadcast | 2 | 0 → 1 (8192); 2 → 3 (8192); 4 → 5 (8192); 6 → 7 (8192) |

| Rank | 发送 bytes | 接收 bytes | 标量归约加法 |
| --- | ---: | ---: | ---: |
| 0 | 24576 | 24576 | 12288 |
| 1 | 8192 | 8192 | 0 |
| 2 | 16384 | 16384 | 4096 |
| 3 | 8192 | 8192 | 0 |
| 4 | 24576 | 24576 | 8192 |
| 5 | 8192 | 8192 | 0 |
| 6 | 16384 | 16384 | 4096 |
| 7 | 8192 | 8192 | 0 |

计量条件：

- Same Qwen3 Dense BF16 [B*T,H] partial activation on every rank. Basic TP calls two output all-reduces per layer; no device placement or backend dispatch claim.
- Binomial reduction rooted at zero followed by the reverse edge schedule for broadcast. Non-power-of-two groups skip absent partners; p=1 is identity. Integer replay validates this schedule, not floating-point bitwise equivalence.
- Each edge sends the full M-byte tensor. Each round completes before the next, with independent simultaneous directed edges and one startup per round. This unsegmented algorithm is not a double binary tree, recursive halving/doubling or a model of every library tree.
- Network volume is 2(p-1)M, equal to ring all-reduce volume, but rank traffic is nonuniform and critical-path transfers are full tensors. Message-size-dependent performance differs despite equal total volume.
- Per-rank reduction additions are separate scalar work; precision, reduction service time, topology hops, link sharing, launch, segmentation and overlap are excluded from the declared timing model.
- Bandwidth is one-direction effective link bandwidth; startup and bandwidth defaults are teaching assumptions. Serial 2L total is not complete TP iteration latency or measured NCCL performance.

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
