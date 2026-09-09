# cache-sequence — qwen3-235b-a22b

输入：`{"batch": 1, "element_bytes": 2, "prefix_hit": 6144, "prompt": 8192, "recurrent_bytes": 4, "steps": 1024}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| reference_variant | `"native_gqa"` |
| decode_prior_history_records_per_request | 8,912,384 |
| decode_visible_pairs_per_request | 8,913,408 |
| uncached_recompute_pairs_per_request | 38,842,575,872 |
| cached_decode_projection_rows | 1,024 |
| uncached_recompute_projection_rows | 8,913,408 |
| prefill_full_pairs_per_request | 33,558,528 |
| prefill_suffix_pairs_per_request | 14,681,088 |
| saved_prefill_pairs_per_request | 18,877,440 |
| saved_new_token_projection_rows | 6,144 |
| decode_prior_history_read_payload_bytes | 1,715,740,868,608 |
| decode_append_write_bytes | 197,132,288 |
| final_persistent_state_bytes | 1,774,190,592 |
| actual_hbm_traffic_bytes | `null` |

各路径是比较场景，不能将各行相加：

| 路径 | 每请求每 token bytes | 累计旧历史读 bytes | 追加写 bytes | 最终状态 bytes | Decode QK/PV FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| native_gqa | 192,512 | 1,715,740,868,608 | 197,132,288 | 1,774,190,592 | 27,455,008,014,336 |
| counterfactual_mha | 3,080,192 | 27,451,853,897,728 | 3,154,116,608 | 28,387,049,472 | 27,455,008,014,336 |
| counterfactual_mqa | 48,128 | 428,935,217,152 | 49,283,072 | 443,547,648 | 27,455,008,014,336 |

| 路径 | 完整 prefill QK/PV FLOPs | 命中前缀后 QK/PV FLOPs | 完整写 bytes | 命中后写 bytes | 前缀状态 bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| native_gqa | 103,366,709,477,376 | 45,220,569,808,896 | 1,577,058,304 | 394,264,576 | 1,182,793,728 |
| counterfactual_mha | 103,366,709,477,376 | 45,220,569,808,896 | 25,232,932,864 | 6,308,233,216 | 18,924,699,648 |
| counterfactual_mqa | 103,366,709,477,376 | 45,220,569,808,896 | 394,264,576 | 98,566,144 | 295,698,432 |

KDA recurrent／短卷积槽的逐调用读写另见 JSON；未并入全历史读取列。

计量条件：

- P prompt tokens are already processed before G subsequent one-token calls. Call i starts with P+i history and appends one token; total prior records = GP+G(G-1)/2. This is G model calls, not an unqualified API output-token count.
- Prior-history read excludes the current record; visible attention operands include it; append writes are separate. Query heads ideally reuse every K/V record once per call. These are logical payloads, not summed HBM traffic.
- MHA/MQA are architecture counterfactuals with unchanged Q heads and head width; they are not alternative execution modes of the downloaded GQA weights or evidence of equal quality. KV projections/cache change; QK/PV matrix work does not.
- K3 compact is an algebraic alternative to reference expanded MLA. Only MLA QK/PV is in attention FLOPs; KDA, projection, FFN, normalization and output-head work are outside this ledger.
- Prefix reuse skips C token rows and C(C+1)/2 causal pairs; suffix queries still attend to cached prefix. Final unshared per-request cache capacity is unchanged. Prefix lookup, transfer, reference counting and physical sharing are not modeled.
- K3 prefix checkpoint must include recurrent and convolution state at the exact prefix boundary, not merely MLA history. Per-decode read/write of those state objects is a declared payload, not an allocator or HBM trace. K3 config/checkpoint A_log shape discrepancy remains documented separately.
- Full prompt hit has zero new prompt attention work; producing first logits still requires cached boundary output or recomputation, which this state/attention-only calculation does not include.
- Without cache, every call recomputes all P+i+1 positions. Projection rows and causal attention pairs are reported separately; this does not eliminate temporary KV tensors or imply zero peak memory.
- No workspace, weights, padding, parallel replication, quantization metadata or cache-offloading costs are included. Explicit bytes describe uniform teaching state formats.

固定来源：

- [configs/models/qwen3-235b-a22b/config.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/config.json)，SHA256 `0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4`。
- [sources/qwen3-235b-a22b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/model.safetensors.index.json)，SHA256 `53dd34fac4a29fc7ee58fa9d92c7892ea6884431c3bd3d0dc93def7bbd0b8b78`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
