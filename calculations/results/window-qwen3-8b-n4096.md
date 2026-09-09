# memory-concurrency — qwen3-8b

输入：`{"bandwidth_bytes_per_second": 1000000000000, "batch": 1, "latency_ns": 500, "length": 8192, "transaction_bytes": 128, "transactions": 4096}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| logical_kv_payload_bytes | 1,207,959,552 |
| allocated_window_bytes | 524,288 |
| outstanding_window_bytes | 524,288 |
| active_transactions | 4,096 |
| throughput_bounds_exact_bytes_per_second | `{"interface": "1000000000000", "transaction_window": "1048576000000"}` |
| effective_bandwidth_upper_exact_bytes_per_second | `"1000000000000"` |
| serial_service_can_reach_interface | `true` |
| binding_limiters | `["interface"]` |
| required_window_bytes | 500,000.0 |
| required_transactions | 3,907 |
| transaction_limited_bytes_per_second | 1,048,576,000,000.0 |
| effective_bandwidth_upper_bytes_per_second | 1,000,000,000,000.0 |
| bandwidth_utilization_upper | 1.0 |
| ideal_interface_service_seconds | 0.001207959552 |
| window_constrained_service_lower_seconds | 0.001207959552 |
| finite_transfer_lower_seconds | 0.001207959552 |
| assumed_fixed_size_transfer_count | 9,437,184 |
| assumed_fixed_size_payload_bytes | 1,207,959,552 |
| limiter | `"interface"` |
| measured_bandwidth_bytes_per_second | `null` |
| predicted_decode_seconds | `null` |

计量条件：

- KV payload uses pinned Qwen3 configuration, BF16 and one logical visit per stored K/V record. Weight reads, new token writes, caches, repeated tile loads and other operators are excluded.
- N counts independent outstanding interface transactions across the device, not batch size, threads, warps or SM count. No hardware queue capacity is inferred from the model configuration.
- At the declared workload latency L, transaction rate is bounded by N/L and bandwidth by min(B,Ns/L). Required N=ceil(BL/s). B is one-direction bytes/s, L is integer ns, s is bytes per transaction.
- Latency and bandwidth must describe the same interface and workload. These defaults are teaching assumptions, not H100 or Mess measurements. A pointer-chase probe is not automatically the latency of every model transaction.
- Payload divided by the throughput bound is a resource service lower bound. Finite transfer also cannot finish before one assumed latency; startup, dependency chains and drain can make it longer. No exact schedule or attainable performance is claimed.
- Allocated slots and active independent requests are distinct: active_transactions defaults to all slots, but source-side completion waiting may reduce it to one. An optional service_interval_ns is a sustainable serialized initiation interval (or non-pipelined service duration), not automatically a single-request latency. The combined bound is min(B, active*m/T, m/tau); tied limiters are retained. Required transaction count only satisfies the window condition, not a serial-service limit.
- Transaction count rounds the whole logical payload upward as a separate fixed-size-transfer scenario; real alignment, coalescing, page walks and cache misses require execution evidence.

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
