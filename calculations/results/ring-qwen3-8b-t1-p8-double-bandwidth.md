# qwen-ring-collective — qwen3-8b

输入：`{"bandwidth_bytes_per_second": 100000000000, "batch": 1, "message_dtype": "BF16", "message_scope": "full activation per rank for all-reduce", "participants": 8, "startup_ns": 2000, "tokens": 1}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| activation_shape | `[1, 4096]` |
| message_bytes_per_rank | 8,192 |
| chunk_bytes | 1,024 |
| all_reduce_rounds | 14 |
| all_reduce_send_bytes_per_rank | 14,336 |
| all_reduce_receive_bytes_per_rank | 14,336 |
| all_reduce_network_send_bytes | 114,688 |
| all_reduce_global_reduction_adds | 28,672 |
| all_reduce_startup_seconds | 2.8e-05 |
| all_reduce_bandwidth_seconds | 1.4336e-07 |
| all_reduce_modeled_seconds | 2.814336e-05 |
| dense_tp_all_reduce_calls | 72 |
| dense_tp_serial_collective_seconds | 0.00202632192 |
| measured_collective_seconds | `null` |

| 阶段 | 轮次 | sender → receiver : chunk (bytes) |
| --- | ---: | --- |
| reduce_scatter | 0 | 0 → 1 : 0 (1024); 1 → 2 : 1 (1024); 2 → 3 : 2 (1024); 3 → 4 : 3 (1024); 4 → 5 : 4 (1024); 5 → 6 : 5 (1024); 6 → 7 : 6 (1024); 7 → 0 : 7 (1024) |
| reduce_scatter | 1 | 0 → 1 : 7 (1024); 1 → 2 : 0 (1024); 2 → 3 : 1 (1024); 3 → 4 : 2 (1024); 4 → 5 : 3 (1024); 5 → 6 : 4 (1024); 6 → 7 : 5 (1024); 7 → 0 : 6 (1024) |
| reduce_scatter | 2 | 0 → 1 : 6 (1024); 1 → 2 : 7 (1024); 2 → 3 : 0 (1024); 3 → 4 : 1 (1024); 4 → 5 : 2 (1024); 5 → 6 : 3 (1024); 6 → 7 : 4 (1024); 7 → 0 : 5 (1024) |
| reduce_scatter | 3 | 0 → 1 : 5 (1024); 1 → 2 : 6 (1024); 2 → 3 : 7 (1024); 3 → 4 : 0 (1024); 4 → 5 : 1 (1024); 5 → 6 : 2 (1024); 6 → 7 : 3 (1024); 7 → 0 : 4 (1024) |
| reduce_scatter | 4 | 0 → 1 : 4 (1024); 1 → 2 : 5 (1024); 2 → 3 : 6 (1024); 3 → 4 : 7 (1024); 4 → 5 : 0 (1024); 5 → 6 : 1 (1024); 6 → 7 : 2 (1024); 7 → 0 : 3 (1024) |
| reduce_scatter | 5 | 0 → 1 : 3 (1024); 1 → 2 : 4 (1024); 2 → 3 : 5 (1024); 3 → 4 : 6 (1024); 4 → 5 : 7 (1024); 5 → 6 : 0 (1024); 6 → 7 : 1 (1024); 7 → 0 : 2 (1024) |
| reduce_scatter | 6 | 0 → 1 : 2 (1024); 1 → 2 : 3 (1024); 2 → 3 : 4 (1024); 3 → 4 : 5 (1024); 4 → 5 : 6 (1024); 5 → 6 : 7 (1024); 6 → 7 : 0 (1024); 7 → 0 : 1 (1024) |
| all_gather | 0 | 0 → 1 : 1 (1024); 1 → 2 : 2 (1024); 2 → 3 : 3 (1024); 3 → 4 : 4 (1024); 4 → 5 : 5 (1024); 5 → 6 : 6 (1024); 6 → 7 : 7 (1024); 7 → 0 : 0 (1024) |
| all_gather | 1 | 0 → 1 : 0 (1024); 1 → 2 : 1 (1024); 2 → 3 : 2 (1024); 3 → 4 : 3 (1024); 4 → 5 : 4 (1024); 5 → 6 : 5 (1024); 6 → 7 : 6 (1024); 7 → 0 : 7 (1024) |
| all_gather | 2 | 0 → 1 : 7 (1024); 1 → 2 : 0 (1024); 2 → 3 : 1 (1024); 3 → 4 : 2 (1024); 4 → 5 : 3 (1024); 5 → 6 : 4 (1024); 6 → 7 : 5 (1024); 7 → 0 : 6 (1024) |
| all_gather | 3 | 0 → 1 : 6 (1024); 1 → 2 : 7 (1024); 2 → 3 : 0 (1024); 3 → 4 : 1 (1024); 4 → 5 : 2 (1024); 5 → 6 : 3 (1024); 6 → 7 : 4 (1024); 7 → 0 : 5 (1024) |
| all_gather | 4 | 0 → 1 : 5 (1024); 1 → 2 : 6 (1024); 2 → 3 : 7 (1024); 3 → 4 : 0 (1024); 4 → 5 : 1 (1024); 5 → 6 : 2 (1024); 6 → 7 : 3 (1024); 7 → 0 : 4 (1024) |
| all_gather | 5 | 0 → 1 : 4 (1024); 1 → 2 : 5 (1024); 2 → 3 : 6 (1024); 3 → 4 : 7 (1024); 4 → 5 : 0 (1024); 5 → 6 : 1 (1024); 6 → 7 : 2 (1024); 7 → 0 : 3 (1024) |
| all_gather | 6 | 0 → 1 : 3 (1024); 1 → 2 : 4 (1024); 2 → 3 : 5 (1024); 3 → 4 : 6 (1024); 4 → 5 : 7 (1024); 5 → 6 : 0 (1024); 6 → 7 : 1 (1024); 7 → 0 : 2 (1024) |

计量条件：

- Qwen3 Dense BF16 [B*T,H] partial output per rank; two row-parallel output all-reduces per layer is an explicit basic TP execution assumption, not every backend implementation.
- Reduce-scatter starts with the full M-byte partial tensor on each rank and ends with M/p reduced bytes; all-gather starts with those M/p bytes and ends with M bytes. Do not interpret M as per-rank input for both phases.
- Every round sends one chunk to the next rank. After reduce-scatter rank r owns reduced chunk (r+1) mod p; all-gather follows that ownership. p=1 is an identity with zero communication.
- Per-rank sent and received bytes are separate endpoint counters. Network payload sums sends once, not sends plus receives. Physical hops, shared links, multiport paths and staging require a topology model.
- Time assumes a balanced ring with simultaneous independent directed edges, one startup per round and one-direction effective link bandwidth. Reduction compute, launch, contention, overlap and channels are not measured here.
- Reduction scalar additions are logical counts; accumulator precision and floating-point reassociation require a backend-specific analysis. They are not Tensor FLOPs.
- Serial 2L-call total deliberately excludes overlap and fusion. Only communication for the stated TP path is counted; weights, KV placement, compute and device feasibility are separate.

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
