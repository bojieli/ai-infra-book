# qwen-dense-communication-path — qwen3-8b

输入：`{"bandwidth_bytes_per_second": 50000000000, "batch_per_replica": 1, "dp": 1, "logit_element_bytes": 4, "pp": 1, "startup_ns": 2000, "tokens": 8192, "tp": 8}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| activation_bytes | 67,108,864 |
| full_last_position_logit_bytes | 607,744 |
| vocabulary_logit_shard_bytes | 75,968 |
| selected_token_id_bytes | 4 |
| nonempty_communication_operations | 75 |
| network_send_bytes_per_replica | 68,589,513,244 |
| network_send_bytes_all_replicas | 68,589,513,244 |
| operation_stage_accounted_bytes | `[68589513244]` |
| serial_communication_path_seconds | 0.17353778328 |
| startup_seconds | 0.002064 |
| bandwidth_seconds | 0.17147378328000001 |
| predicted_iteration_seconds | `null` |

| 操作 | PP | 层 | 轮次 | 每副本网络发送 bytes | 模型 μs |
| --- | ---: | --- | ---: | ---: | ---: |
| vocabulary_embedding_reduce | 0 | None | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 0 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 0 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 1 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 1 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 2 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 2 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 3 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 3 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 4 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 4 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 5 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 5 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 6 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 6 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 7 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 7 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 8 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 8 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 9 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 9 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 10 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 10 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 11 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 11 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 12 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 12 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 13 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 13 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 14 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 14 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 15 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 15 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 16 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 16 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 17 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 17 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 18 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 18 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 19 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 19 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 20 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 20 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 21 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 21 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 22 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 22 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 23 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 23 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 24 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 24 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 25 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 25 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 26 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 26 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 27 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 27 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 28 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 28 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 29 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 29 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 30 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 30 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 31 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 31 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 32 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 32 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 33 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 33 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 34 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 34 | 14 | 939524096 | 2376.810240 |
| attention_output_reduce | 0 | 35 | 14 | 939524096 | 2376.810240 |
| ffn_output_reduce | 0 | 35 | 14 | 939524096 | 2376.810240 |
| last_position_logits_all_gather | 0 | None | 7 | 4254208 | 24.635520 |
| selected_token_first_stage_broadcast | 0 | None | 3 | 28 | 6.000240 |

计量条件：

- One forward plus selected-token feedback for the next call. Input vocabulary embedding shards produce masked partial hidden vectors and need an all-reduce, in addition to two output reductions per decoder layer.
- Hidden states are replicated across TP ranks at PP boundaries; matching-rank sends are explicit and not deduplicated. The basic placement is inherited from dense-placement, not inferred from aggregate device memory.
- Only last-position vocabulary logits are gathered, regardless of input token count. Default four-byte wire logits are a scenario choice, not a claim about every framework output dtype. All-gather is the declared sampling strategy, not the only distributed sampling algorithm.
- Sampling computation is excluded. Last-stage rank 0 sends int32 IDs to first-stage rank 0 when PP>1; first-stage TP broadcasts them. Scheduler metadata, RNG coordination, masks and position control messages are not included.
- Operations lie on the declared serial dependency path for one microbatch. Summed communication models omit compute, overlap, queueing and pipeline bubbles, so no full iteration time is reported.
- All links in each collective/PP boundary are assumed independent with the same effective one-direction bandwidth and startup. Shared fabric resources and physical hops require the separate traffic mapper.
- DP duplicates bytes across independent replicas but does not multiply this per-replica path time. Global shared-network throughput cannot be inferred without mapping those replicas.
- Norm statistics use local complete hidden/head vectors in this placement and require no extra cross-rank normalization reduction. Other sequence-parallel layouts would change that communication graph.

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
