# qwen-pcie-numa-staging — qwen3-8b

输入：`{"dram_bytes_per_second": 40000000000, "intersocket_bytes_per_second": 8000000000, "order": "grouped", "pcie_bytes_per_second": 12000000000, "placement": "all-a", "rank_to_gpu": [0, 1, 2, 3], "startup_ns": 0, "tokens": 1024}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| message_bytes | 8,388,608 |
| logical_send_bytes | 50,331,648 |
| aggregate_resource_lower_seconds | 0.003145728 |
| sum_round_resource_lower_seconds | 0.0031457280000000004 |
| barrier_lower_with_startup_seconds | 0.0031457280000000004 |
| buffer_resident_bytes | `null` |
| measured_all_reduce_seconds | `null` |

| GPU 发送 → 接收 | 缓冲 NUMA | 依次经过的资源（重复项表示重复服务） |
| --- | --- | --- |
| 0 → 1 | A | gpu0_to_host → dram_A → dram_A → gpu1_from_host |
| 1 → 2 | A | gpu1_to_host → dram_A → dram_A → A_to_B → gpu2_from_host |
| 2 → 3 | A | gpu2_to_host → B_to_A → dram_A → dram_A → A_to_B → gpu3_from_host |
| 3 → 0 | A | gpu3_to_host → B_to_A → dram_A → dram_A → gpu0_from_host |

| 物理资源 | bytes | bytes/s | 服务 ms |
| --- | ---: | ---: | ---: |
| A_to_B | 25165824 | 8000000000 | 3.145728 |
| B_to_A | 25165824 | 8000000000 | 3.145728 |
| dram_A | 100663296 | 40000000000 | 2.516582 |
| gpu0_from_host | 12582912 | 12000000000 | 1.048576 |
| gpu0_to_host | 12582912 | 12000000000 | 1.048576 |
| gpu1_from_host | 12582912 | 12000000000 | 1.048576 |
| gpu1_to_host | 12582912 | 12000000000 | 1.048576 |
| gpu2_from_host | 12582912 | 12000000000 | 1.048576 |
| gpu2_to_host | 12582912 | 12000000000 | 1.048576 |
| gpu3_from_host | 12582912 | 12000000000 | 1.048576 |
| gpu3_to_host | 12582912 | 12000000000 | 1.048576 |

计量条件：

- Four-GPU teaching topology: G0/G1 on NUMA A and G2/G3 on B. Logical ring schedule comes from the actual Qwen3-8B BF16 [T,4096] activation payload.
- Every edge stages through exactly one host buffer: sender writes it, receiver reads it, with no extra CPU memcpy. Allocation process identity does not identify buffer NUMA placement.
- GPU-to-host and host-to-GPU PCIe are independent directional resources. Each NUMA DRAM has a shared read-plus-write bandwidth, so its resource appears twice per staged transfer. A-to-B and B-to-A are independent directions.
- All rates are explicit effective teaching inputs, not official GPU/P2P specifications or measured bandwidth. This path does not require assuming consumer-GPU P2P support.
- Aggregate maximum service time is a lower bound. Summing per-round resource maxima additionally respects declared ring round barriers; startup is optional. Intra-round path dependencies, host bridges, protocol bytes, reductions and synchronization can raise actual time.
- Traffic is not buffer residency: no double-buffer depth or allocation lifetime has been supplied, so buffer capacity remains unknown. Physical hops sum resource service without relabeling it as logical collective payload.

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
