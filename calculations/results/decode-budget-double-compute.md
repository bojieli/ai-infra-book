# nominal-decode-budget — nominal-70b-teaching-model

输入：`{"accumulator": "FP32", "bandwidth_multiplier": 1.0, "batch": 1, "compute_input": "BF16", "compute_multiplier": 2, "device": "h100-sxm", "kv_append_bytes_per_request": 0, "kv_history_bytes_per_request": 0, "metadata_bytes": 0, "parameters": 70000000000, "sparsity": "dense", "weight_bits": 8, "workspace_bytes": 0}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| matrix_flops | 140,000,000,000 |
| weight_payload_bytes | 70,000,000,000 |
| declared_read_write_bytes | 70,000,000,000 |
| declared_resident_bytes | 70,000,000,000 |
| nominal_capacity_bytes | 80,000,000,000 |
| fits_declared_budget | `true` |
| arithmetic_intensity_flops_per_byte | 2.0 |
| compute_service_seconds | 7.074994946432182e-05 |
| memory_service_seconds | 0.020895522388059702 |
| resource_lower_bound_seconds | 0.020895522388059702 |
| capacity_feasible_throughput_upper_tokens_per_second | 47.857142857142854 |
| compute_memory_crossover_batch | 296 |
| crossover_fits_declared_capacity | `true` |
| dominant_resource | `"memory"` |
| measured_decode_seconds | `null` |

计量条件：

- Nominal N parameters use approximate 2NB dense matrix FLOPs; no actual architecture, attention correction or output-head distinction is inferred. Qwen actual operators remain in forward/projection-bound.
- Official H100 SXM BF16 input/FP32 accumulator/dense Tensor peak is selected strictly. Storage may be 4/8 bits; assumed dequantized BF16 operands use this peak, not INT8 TOPS or native FP4 peak. Conversion work and buffers require additional accounting.
- Weights and supplied metadata are read once and reused across the batch. Each request reads its declared history and writes its append once. KV values are explicit teaching bytes, not borrowed from a different model configuration.
- Resident budget includes declared weights/metadata, end-of-step KV and workspace. Device nominal GB is converted using 10^9; reserved runtime space must be represented in workspace. Zero extras mean excluded, not proven absent.
- Compute and memory service can overlap only as a lower-bound assumption: take max, not sum. Failed capacity leaves a runnable resource bound and throughput null, while component arithmetic remains visible.
- Multipliers are hypothetical resource changes relative to the official profile, not other hardware SKUs. Crossover solves shared_bytes + B*KV_bytes = B*2N*bandwidth/compute; no positive denominator means this model never becomes compute dominated.
- No kernel padding, launch, communication, non-matrix arithmetic, quality impact or measured efficiency is included. This is the initial chapter-one estimate, not complete model/token latency.

固定来源：

- [sources/hardware/nvidia-h100-page.html](https://www.nvidia.com/en-us/data-center/h100/)，SHA256 `8fe697dfa96dceeeed6e7a16517294e15d9100cc0e9f1e6e5edbce78699b4681`。
- [../references/files/specs/nvidia-h100.pdf](https://dam-cdn.nvd.orangelogic.com/AssetLink/705n6ur546g0uk43w0117r17n8042d73.pdf)，SHA256 `3641614979809a027a8aabdc2e77639efb8fcd0f8dc7873a22ba2125489f5a27`。
- [sources/hardware/nvidia-ptx-isa-9-3.html](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html)，SHA256 `940cc68f858cefdf82425b47ee3bac3afde447c8a85b95f43d7d6fb1f46b4413`。
- [research/h05-next-review/cuda-programming-guide-12.8.1.html](https://docs.nvidia.com/cuda/archive/12.8.1/cuda-c-programming-guide/index.html)，SHA256 `cdc49d93372b4e03e94d56f24345373f82ad76b8663c745073463263009637ce`。
