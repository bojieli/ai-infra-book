# qwen-single-device-capacity-scan — qwen3-235b-a22b

输入：`{"capacities": [24000000000, 48000000000, 80000000000], "group_size": 128, "kv_element_bytes": 2, "length": 32768, "scale_bytes": 2, "workspace_bytes": 2147483648}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| logical_parameters | 235,093,634,560 |
| bf16_weight_bytes | 470,187,269,120 |
| eight_bit_scheme_bytes | 240,041,483,264 |
| four_bit_scheme_bytes | 123,142,036,480 |
| bf16_kv_bytes_per_request | 6,308,233,216 |
| measured_resident_bytes | `null` |

| 矩阵位宽 | 预算 GB | 权重 bytes | 工作区 bytes | 每请求 KV bytes | 权重及工作区够放 | 最大并发 |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| 16 | 24 | 470187269120 | 2147483648 | 6308233216 | False | 0 |
| 16 | 48 | 470187269120 | 2147483648 | 6308233216 | False | 0 |
| 16 | 80 | 470187269120 | 2147483648 | 6308233216 | False | 0 |
| 8 | 24 | 240041483264 | 2147483648 | 6308233216 | False | 0 |
| 8 | 48 | 240041483264 | 2147483648 | 6308233216 | False | 0 |
| 8 | 80 | 240041483264 | 2147483648 | 6308233216 | False | 0 |
| 4 | 24 | 123142036480 | 2147483648 | 6308233216 | False | 0 |
| 4 | 48 | 123142036480 | 2147483648 | 6308233216 | False | 0 |
| 4 | 80 | 123142036480 | 2147483648 | 6308233216 | False | 0 |

矩阵逐行打包与 scale 元数据分项：

| 位宽 | 参数载荷 bytes | scale bytes |
| --- | ---: | ---: |
| 16 | 470187269120 | 0 |
| 8 | 236388375552 | 3653107712 |
| 4 | 119488928768 | 3653107712 |

逐权重形状、copies 和打包字节见 JSON；并发只在声明工作区预算下成立。

计量条件：

- Shapes and copies reuse Qwen3 Dense/MoE weight enumeration audited against official checkpoint indices. MoE stores every expert, not only activated parameters.
- BF16 baseline keeps all parameters at two bytes. Low-bit teaching schemes quantize eligible 2-D linear matrices per output row and K group, retaining embedding, vocabulary head, router and one-dimensional norm parameters as BF16.
- Each quantized row packs independently, rounding partial bytes upward; each ceil(K/group_size) group has scale_bytes metadata. Symmetric scheme has no zero points. No claim of a particular released quantized checkpoint, kernel support or quality equivalence.
- KV uses pinned full-history GQA geometry and BF16. Every concurrent request has the same retained length; no physical prefix sharing, paging slack, offloading or parallel replication.
- Capacities are explicit single-device byte budgets (defaults 24/48/80 decimal GB), not aggregate eight-card memory and not assertions about a specific SKU. Actual allocatable budget must account for reservations.
- Workspace is an explicit reserved budget, not a computed allocator peak. Maximum requests is conditional on it; temporary dequantization, graph pools and batch-dependent workspace may require more.
- Zero requests can mean weights/workspace already fail or insufficient room for one KV. The fit flag and signed remaining bytes distinguish these cases. No throughput or deployability is inferred.

固定来源：

- [configs/models/qwen3-235b-a22b/config.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/config.json)，SHA256 `0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4`。
- [sources/qwen3-235b-a22b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/model.safetensors.index.json)，SHA256 `53dd34fac4a29fc7ee58fa9d92c7892ea6884431c3bd3d0dc93def7bbd0b8b78`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
