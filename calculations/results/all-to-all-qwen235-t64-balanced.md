# qwen-moe-pairwise-all-to-all — qwen3-235b-a22b

输入：`{"bandwidth_bytes_per_second": 50000000000, "counts": [[64, 64, 64, 64, 64, 64, 64, 64], [64, 64, 64, 64, 64, 64, 64, 64], [64, 64, 64, 64, 64, 64, 64, 64], [64, 64, 64, 64, 64, 64, 64, 64], [64, 64, 64, 64, 64, 64, 64, 64], [64, 64, 64, 64, 64, 64, 64, 64], [64, 64, 64, 64, 64, 64, 64, 64], [64, 64, 64, 64, 64, 64, 64, 64]], "expert_placement": "equal contiguous groups", "participants": 8, "payload_dtype": "BF16", "routing": "balanced", "startup_ns": 2000, "tokens_per_rank": 64}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| hidden_size | 4,096 |
| top_k | 8 |
| experts_per_rank | 16 |
| assignments_per_source | 512 |
| vector_payload_bytes | 8,192 |
| local_assignments | 512 |
| remote_assignments | 3,584 |
| dispatch_network_send_bytes | 29,360,128 |
| combine_network_send_bytes | 29,360,128 |
| dispatch_maximum_receive_bytes | 3,670,016 |
| dispatch_endpoint_service_lower_seconds | 7.340032e-05 |
| dispatch_pairwise_modeled_seconds | 8.740031999999999e-05 |
| dispatch_plus_combine_modeled_seconds | 0.00017480063999999998 |
| measured_seconds | `null` |

dispatch

| rank | 发送 bytes | 接收 bytes |
| --- | ---: | ---: |
| 0 | 3670016 | 3670016 |
| 1 | 3670016 | 3670016 |
| 2 | 3670016 | 3670016 |
| 3 | 3670016 | 3670016 |
| 4 | 3670016 | 3670016 |
| 5 | 3670016 | 3670016 |
| 6 | 3670016 | 3670016 |
| 7 | 3670016 | 3670016 |

| Offset | 有向边 (bytes) | 阶段 μs |
| --- | --- | ---: |
| 1 | 0 → 1 (524288); 1 → 2 (524288); 2 → 3 (524288); 3 → 4 (524288); 4 → 5 (524288); 5 → 6 (524288); 6 → 7 (524288); 7 → 0 (524288) | 12.485760 |
| 2 | 0 → 2 (524288); 1 → 3 (524288); 2 → 4 (524288); 3 → 5 (524288); 4 → 6 (524288); 5 → 7 (524288); 6 → 0 (524288); 7 → 1 (524288) | 12.485760 |
| 3 | 0 → 3 (524288); 1 → 4 (524288); 2 → 5 (524288); 3 → 6 (524288); 4 → 7 (524288); 5 → 0 (524288); 6 → 1 (524288); 7 → 2 (524288) | 12.485760 |
| 4 | 0 → 4 (524288); 1 → 5 (524288); 2 → 6 (524288); 3 → 7 (524288); 4 → 0 (524288); 5 → 1 (524288); 6 → 2 (524288); 7 → 3 (524288) | 12.485760 |
| 5 | 0 → 5 (524288); 1 → 6 (524288); 2 → 7 (524288); 3 → 0 (524288); 4 → 1 (524288); 5 → 2 (524288); 6 → 3 (524288); 7 → 4 (524288) | 12.485760 |
| 6 | 0 → 6 (524288); 1 → 7 (524288); 2 → 0 (524288); 3 → 1 (524288); 4 → 2 (524288); 5 → 3 (524288); 6 → 4 (524288); 7 → 5 (524288) | 12.485760 |
| 7 | 0 → 7 (524288); 1 → 0 (524288); 2 → 1 (524288); 3 → 2 (524288); 4 → 3 (524288); 5 → 4 (524288); 6 → 5 (524288); 7 → 6 (524288) | 12.485760 |

combine

| rank | 发送 bytes | 接收 bytes |
| --- | ---: | ---: |
| 0 | 3670016 | 3670016 |
| 1 | 3670016 | 3670016 |
| 2 | 3670016 | 3670016 |
| 3 | 3670016 | 3670016 |
| 4 | 3670016 | 3670016 |
| 5 | 3670016 | 3670016 |
| 6 | 3670016 | 3670016 |
| 7 | 3670016 | 3670016 |

| Offset | 有向边 (bytes) | 阶段 μs |
| --- | --- | ---: |
| 1 | 0 → 1 (524288); 1 → 2 (524288); 2 → 3 (524288); 3 → 4 (524288); 4 → 5 (524288); 5 → 6 (524288); 6 → 7 (524288); 7 → 0 (524288) | 12.485760 |
| 2 | 0 → 2 (524288); 1 → 3 (524288); 2 → 4 (524288); 3 → 5 (524288); 4 → 6 (524288); 5 → 7 (524288); 6 → 0 (524288); 7 → 1 (524288) | 12.485760 |
| 3 | 0 → 3 (524288); 1 → 4 (524288); 2 → 5 (524288); 3 → 6 (524288); 4 → 7 (524288); 5 → 0 (524288); 6 → 1 (524288); 7 → 2 (524288) | 12.485760 |
| 4 | 0 → 4 (524288); 1 → 5 (524288); 2 → 6 (524288); 3 → 7 (524288); 4 → 0 (524288); 5 → 1 (524288); 6 → 2 (524288); 7 → 3 (524288) | 12.485760 |
| 5 | 0 → 5 (524288); 1 → 6 (524288); 2 → 7 (524288); 3 → 0 (524288); 4 → 1 (524288); 5 → 2 (524288); 6 → 3 (524288); 7 → 4 (524288) | 12.485760 |
| 6 | 0 → 6 (524288); 1 → 7 (524288); 2 → 0 (524288); 3 → 1 (524288); 4 → 2 (524288); 5 → 3 (524288); 6 → 4 (524288); 7 → 5 (524288) | 12.485760 |
| 7 | 0 → 7 (524288); 1 → 0 (524288); 2 → 1 (524288); 3 → 2 (524288); 4 → 3 (524288); 5 → 4 (524288); 6 → 5 (524288); 7 → 6 (524288) | 12.485760 |

计量条件：

- One MoE layer: each source owns tokens_per_rank tokens, each chooses top_k distinct experts. Equal contiguous expert groups are a declared placement. Counts specify assignments by source/destination rank, not observed router output.
- BF16 vector width comes from official Qwen3 MoE hidden_size. Send one vector per token-expert assignment even if several selected experts share a destination. Destination token deduplication, multicast and metadata are excluded.
- Diagonal assignments remain local and cause no network traffic. Combine transposes dispatch counts, returning one full-width expert output per assignment; probability weighting and final sum are compute work outside this ledger.
- Pairwise offset rounds have at most one send and one receive per rank. Independent full-duplex directed links run concurrently; the next round waits for the largest transfer of the current round. Globally empty rounds are skipped.
- Endpoint bandwidth lower bound uses the maximum total sent or received by any rank. Summed round maxima include barrier imbalance; equal global bytes can therefore produce different endpoint and schedule times.
- No topology hop count, shared-switch contention, expert execution, pipeline overlap, pack/unpack, padding, startup implementation or measured bandwidth is claimed. Declared link conditions are teaching inputs.

固定来源：

- [configs/models/qwen3-235b-a22b/config.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/config.json)，SHA256 `0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4`。
- [sources/qwen3-235b-a22b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/model.safetensors.index.json)，SHA256 `53dd34fac4a29fc7ee58fa9d92c7892ea6884431c3bd3d0dc93def7bbd0b8b78`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
