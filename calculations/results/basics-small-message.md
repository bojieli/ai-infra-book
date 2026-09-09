# resource-basics — nominal-teaching-model

输入：`{"card_capacity_bytes": 80000000000, "cards": 2, "link_bits_per_second": 400000000000, "link_efficiency": 1.0, "messages": 1, "metadata_bytes_per_card": 0, "parameters": 70000000000, "payload_bytes": 4096, "shard_parameters": [35000000000, 35000000000], "startup_seconds": 3e-06, "state_bytes_per_card": 0, "weight_bits": 16, "workspace_bytes_per_card": 0}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| weight_payload_bytes | 140,000,000,000 |
| weight_payload_GB | 140.0 |
| weight_payload_GiB | 130.385160446167 |
| per_card_capacity_GB | 80.0 |
| per_card_capacity_GiB | 74.50580596923828 |
| aggregate_capacity_bytes | 160,000,000,000 |
| aggregate_occupied_bytes | 140,000,000,000 |
| aggregate_capacity_sufficient | `true` |
| every_card_fits_declared_budget | `true` |
| raw_one_direction_bytes_per_second | 50,000,000,000.0 |
| raw_one_direction_GB_per_second | 50.0 |
| raw_one_direction_GiB_per_second | 46.566128730773926 |
| ideal_payload_service_seconds | 8.192e-08 |
| modeled_payload_service_seconds | 8.192e-08 |
| modeled_startup_seconds | 3e-06 |
| modeled_serial_transfer_seconds | 3.0819200000000002e-06 |
| startup_bandwidth_crossover_payload_bytes | 150,000.0 |
| measured_transfer_seconds | `null` |

| 卡 | 权重 bytes | 元数据 bytes | 状态 bytes | 工作区 bytes | 可用容量 bytes | 剩余 bytes | 声明预算可容纳 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 70,000,000,000 | 0 | 0 | 0 | 80,000,000,000 | 10,000,000,000 | True |
| 1 | 70,000,000,000 | 0 | 0 | 0 | 80,000,000,000 | 10,000,000,000 | True |

计量条件：

- 70B means exactly 70×10^9 nominal teaching parameters, not the count of Llama/Qwen or a downloaded checkpoint. Decimal GB=10^9 bytes and binary GiB=2^30 bytes.
- Storage width is not a hardware compute precision/accumulator declaration. Packed bytes round up separately per card; real per-tensor/group padding, scales and zero points must be provided in metadata or a model-specific adapter.
- Default sharding is an arithmetic balanced partition, not proof that a real model supports this placement. Explicit shards must conserve parameters; replication and actual layer/TP constraints need separate placement calculations.
- State, workspace and metadata are explicit per-card reserved bytes. Zero means excluded from this teaching example, not proven absent in deployment. A fit is conditional on these declared budgets.
- 400 Gb/s converts to 50 GB/s raw in one direction. Do not double that rate for a one-way transfer. Efficiency is a scenario assumption for protocol/shared-path losses, not a measured device specification.
- payload_bytes is the total serial payload across messages, not the size of each message. Model time is messages×startup + total_payload/effective_bandwidth; startup and bandwidth terms are not a measured latency or a parallel schedule.

固定来源：

