# qwen-moe-destination-dedup — qwen3-235b-a22b

输入：`{"bandwidth_bytes_per_second": 50000000000, "combine_element_bytes": 4, "participants": 8, "pattern": "clustered", "routes": "Explicit per-token routes are preserved in the JSON result.", "startup_ns": 2000, "tokens_per_rank": 64}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| per_assignment_dispatch_bytes | 29,360,128 |
| deduplicated_dispatch_bytes | 3,670,016 |
| per_assignment_combine_bytes | 58,720,256 |
| destination_combined_return_bytes | 7,340,032 |
| dispatch_saved_bytes | 25,690,112 |
| combine_saved_bytes | 51,380,224 |
| original_source_reduction_adds | 14,680,064 |
| destination_reduction_adds | 14,680,064 |
| remaining_source_reduction_adds | 0 |
| assignment_pairwise_seconds | 0.00024820096 |
| dedup_pairwise_seconds | 5.552512e-05 |
| metadata_bytes | `null` |
| measured_seconds | `null` |

| 源 rank | 按 assignment 的目的计数 | 按 token 去重的目的计数 |
| --- | --- | --- |
| 0 | [64, 64, 64, 64, 64, 64, 64, 64] | [8, 8, 8, 8, 8, 8, 8, 8] |
| 1 | [64, 64, 64, 64, 64, 64, 64, 64] | [8, 8, 8, 8, 8, 8, 8, 8] |
| 2 | [64, 64, 64, 64, 64, 64, 64, 64] | [8, 8, 8, 8, 8, 8, 8, 8] |
| 3 | [64, 64, 64, 64, 64, 64, 64, 64] | [8, 8, 8, 8, 8, 8, 8, 8] |
| 4 | [64, 64, 64, 64, 64, 64, 64, 64] | [8, 8, 8, 8, 8, 8, 8, 8] |
| 5 | [64, 64, 64, 64, 64, 64, 64, 64] | [8, 8, 8, 8, 8, 8, 8, 8] |
| 6 | [64, 64, 64, 64, 64, 64, 64, 64] | [8, 8, 8, 8, 8, 8, 8, 8] |
| 7 | [64, 64, 64, 64, 64, 64, 64, 64] | [8, 8, 8, 8, 8, 8, 8, 8] |

归约工作转移：`{"destination_adds_per_rank": [1835008, 1835008, 1835008, 1835008, 1835008, 1835008, 1835008, 1835008], "source_adds_per_rank": [0, 0, 0, 0, 0, 0, 0, 0]}`；逐 token 专家身份见 JSON。

计量条件：

- One layer, equal contiguous expert placement. Explicit token identities are (source rank, token index); top-k expert IDs are unique and checked against official Qwen3 MoE configuration.
- Dispatch sends a BF16 token once per destination rank, then that rank reuses it for its selected experts. This does not reduce expert GEMM rows or the number of token-expert computations.
- Combine assumes routing weights are applied to each expert output before summing experts on the destination; return one partial per token/destination. The final source sums destination partials. Total scalar additions are conserved but their placement changes.
- Default return elements are four-byte scenario values for both baseline and destination-combined paths; dispatch is two bytes. This is not a claim about the pinned inference backend wire dtype.
- Reassociation preserves exact-real algebra but need not preserve floating-point bits. Numerical quality, rounding, execution placement and output compatibility need backend checks.
- Counts alone cannot determine deduplication: clustered and spread routes can have the same assignment histogram but different token destination unions. Synthetic patterns are controlled examples, not measured model routing.
- Diagonal local work never enters network phases. Metadata, probability transport, pack/unpack, buffers, multicast fabric and additional dependencies are excluded; modeled phase sums are not end-to-end speedups.

固定来源：

- [configs/models/qwen3-235b-a22b/config.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/config.json)，SHA256 `0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4`。
- [sources/qwen3-235b-a22b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/model.safetensors.index.json)，SHA256 `53dd34fac4a29fc7ee58fa9d92c7892ea6884431c3bd3d0dc93def7bbd0b8b78`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
