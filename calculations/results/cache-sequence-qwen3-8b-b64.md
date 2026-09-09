# cache-sequence — qwen3-8b

输入：`{"batch": 64, "element_bytes": 2, "prefix_hit": 6144, "prompt": 8192, "recurrent_bytes": 4, "steps": 1024}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| reference_variant | `"native_gqa"` |
| decode_prior_history_records_per_request | 8,912,384 |
| decode_visible_pairs_per_request | 8,913,408 |
| uncached_recompute_pairs_per_request | 38,842,575,872 |
| cached_decode_projection_rows | 65,536 |
| uncached_recompute_projection_rows | 570,458,112 |
| prefill_full_pairs_per_request | 33,558,528 |
| prefill_suffix_pairs_per_request | 14,681,088 |
| saved_prefill_pairs_per_request | 18,877,440 |
| saved_new_token_projection_rows | 393,216 |
| decode_prior_history_read_payload_bytes | 84,107,807,686,656 |
| decode_append_write_bytes | 9,663,676,416 |
| final_persistent_state_bytes | 86,973,087,744 |
| actual_hbm_traffic_bytes | `null` |

各路径是比较场景，不能将各行相加：

| 路径 | 每请求每 token bytes | 累计旧历史读 bytes | 追加写 bytes | 最终状态 bytes | Decode QK/PV FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| native_gqa | 147,456 | 84,107,807,686,656 | 9,663,676,416 | 86,973,087,744 | 336,469,885,452,288 |
| counterfactual_mha | 589,824 | 336,431,230,746,624 | 38,654,705,664 | 347,892,350,976 | 336,469,885,452,288 |
| counterfactual_mqa | 18,432 | 10,513,475,960,832 | 1,207,959,552 | 10,871,635,968 | 336,469,885,452,288 |

| 路径 | 完整 prefill QK/PV FLOPs | 命中前缀后 QK/PV FLOPs | 完整写 bytes | 命中后写 bytes | 前缀状态 bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| native_gqa | 1,266,792,014,020,608 | 554,192,515,104,768 | 77,309,411,328 | 19,327,352,832 | 57,982,058,496 |
| counterfactual_mha | 1,266,792,014,020,608 | 554,192,515,104,768 | 309,237,645,312 | 77,309,411,328 | 231,928,233,984 |
| counterfactual_mqa | 1,266,792,014,020,608 | 554,192,515,104,768 | 9,663,676,416 | 2,415,919,104 | 7,247,757,312 |

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

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
