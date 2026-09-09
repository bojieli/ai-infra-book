# qwen-moe-pairwise-all-to-all — qwen3-235b-a22b

输入：`{"bandwidth_bytes_per_second": 50000000000, "counts": [[1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1]], "expert_placement": "equal contiguous groups", "participants": 8, "payload_dtype": "BF16", "routing": "balanced", "startup_ns": 2000, "tokens_per_rank": 1}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| hidden_size | 4,096 |
| top_k | 8 |
| experts_per_rank | 16 |
| assignments_per_source | 8 |
| vector_payload_bytes | 8,192 |
| local_assignments | 8 |
| remote_assignments | 56 |
| dispatch_network_send_bytes | 458,752 |
| combine_network_send_bytes | 458,752 |
| dispatch_maximum_receive_bytes | 57,344 |
| dispatch_endpoint_service_lower_seconds | 1.14688e-06 |
| dispatch_pairwise_modeled_seconds | 1.5146879999999998e-05 |
| dispatch_plus_combine_modeled_seconds | 3.0293759999999995e-05 |
| measured_seconds | `null` |

dispatch

| rank | 发送 bytes | 接收 bytes |
| --- | ---: | ---: |
| 0 | 57344 | 57344 |
| 1 | 57344 | 57344 |
| 2 | 57344 | 57344 |
| 3 | 57344 | 57344 |
| 4 | 57344 | 57344 |
| 5 | 57344 | 57344 |
| 6 | 57344 | 57344 |
| 7 | 57344 | 57344 |

| Offset | 有向边 (bytes) | 阶段 μs |
| --- | --- | ---: |
| 1 | 0 → 1 (8192); 1 → 2 (8192); 2 → 3 (8192); 3 → 4 (8192); 4 → 5 (8192); 5 → 6 (8192); 6 → 7 (8192); 7 → 0 (8192) | 2.163840 |
| 2 | 0 → 2 (8192); 1 → 3 (8192); 2 → 4 (8192); 3 → 5 (8192); 4 → 6 (8192); 5 → 7 (8192); 6 → 0 (8192); 7 → 1 (8192) | 2.163840 |
| 3 | 0 → 3 (8192); 1 → 4 (8192); 2 → 5 (8192); 3 → 6 (8192); 4 → 7 (8192); 5 → 0 (8192); 6 → 1 (8192); 7 → 2 (8192) | 2.163840 |
| 4 | 0 → 4 (8192); 1 → 5 (8192); 2 → 6 (8192); 3 → 7 (8192); 4 → 0 (8192); 5 → 1 (8192); 6 → 2 (8192); 7 → 3 (8192) | 2.163840 |
| 5 | 0 → 5 (8192); 1 → 6 (8192); 2 → 7 (8192); 3 → 0 (8192); 4 → 1 (8192); 5 → 2 (8192); 6 → 3 (8192); 7 → 4 (8192) | 2.163840 |
| 6 | 0 → 6 (8192); 1 → 7 (8192); 2 → 0 (8192); 3 → 1 (8192); 4 → 2 (8192); 5 → 3 (8192); 6 → 4 (8192); 7 → 5 (8192) | 2.163840 |
| 7 | 0 → 7 (8192); 1 → 0 (8192); 2 → 1 (8192); 3 → 2 (8192); 4 → 3 (8192); 5 → 4 (8192); 6 → 5 (8192); 7 → 6 (8192) | 2.163840 |

combine

| rank | 发送 bytes | 接收 bytes |
| --- | ---: | ---: |
| 0 | 57344 | 57344 |
| 1 | 57344 | 57344 |
| 2 | 57344 | 57344 |
| 3 | 57344 | 57344 |
| 4 | 57344 | 57344 |
| 5 | 57344 | 57344 |
| 6 | 57344 | 57344 |
| 7 | 57344 | 57344 |

| Offset | 有向边 (bytes) | 阶段 μs |
| --- | --- | ---: |
| 1 | 0 → 1 (8192); 1 → 2 (8192); 2 → 3 (8192); 3 → 4 (8192); 4 → 5 (8192); 5 → 6 (8192); 6 → 7 (8192); 7 → 0 (8192) | 2.163840 |
| 2 | 0 → 2 (8192); 1 → 3 (8192); 2 → 4 (8192); 3 → 5 (8192); 4 → 6 (8192); 5 → 7 (8192); 6 → 0 (8192); 7 → 1 (8192) | 2.163840 |
| 3 | 0 → 3 (8192); 1 → 4 (8192); 2 → 5 (8192); 3 → 6 (8192); 4 → 7 (8192); 5 → 0 (8192); 6 → 1 (8192); 7 → 2 (8192) | 2.163840 |
| 4 | 0 → 4 (8192); 1 → 5 (8192); 2 → 6 (8192); 3 → 7 (8192); 4 → 0 (8192); 5 → 1 (8192); 6 → 2 (8192); 7 → 3 (8192) | 2.163840 |
| 5 | 0 → 5 (8192); 1 → 6 (8192); 2 → 7 (8192); 3 → 0 (8192); 4 → 1 (8192); 5 → 2 (8192); 6 → 3 (8192); 7 → 4 (8192) | 2.163840 |
| 6 | 0 → 6 (8192); 1 → 7 (8192); 2 → 0 (8192); 3 → 1 (8192); 4 → 2 (8192); 5 → 3 (8192); 6 → 4 (8192); 7 → 5 (8192) | 2.163840 |
| 7 | 0 → 7 (8192); 1 → 0 (8192); 2 → 1 (8192); 3 → 2 (8192); 4 → 3 (8192); 5 → 4 (8192); 6 → 5 (8192); 7 → 6 (8192) | 2.163840 |

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
