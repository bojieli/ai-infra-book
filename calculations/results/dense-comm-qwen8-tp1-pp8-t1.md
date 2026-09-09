# qwen-dense-communication-path — qwen3-8b

输入：`{"bandwidth_bytes_per_second": 50000000000, "batch_per_replica": 1, "dp": 1, "logit_element_bytes": 4, "pp": 8, "startup_ns": 2000, "tokens": 1, "tp": 1}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| activation_bytes | 8,192 |
| full_last_position_logit_bytes | 607,744 |
| vocabulary_logit_shard_bytes | 607,744 |
| selected_token_id_bytes | 4 |
| nonempty_communication_operations | 8 |
| network_send_bytes_per_replica | 57,348 |
| network_send_bytes_all_replicas | 57,348 |
| operation_stage_accounted_bytes | `[8192, 8192, 8192, 8192, 8192, 8192, 8192, 4]` |
| serial_communication_path_seconds | 1.7146959999999998e-05 |
| startup_seconds | 1.6e-05 |
| bandwidth_seconds | 1.14696e-06 |
| predicted_iteration_seconds | `null` |

| 操作 | PP | 层 | 轮次 | 每副本网络发送 bytes | 模型 μs |
| --- | ---: | --- | ---: | ---: | ---: |
| vocabulary_embedding_reduce | 0 | None | 0 | 0 | 0.000000 |
| attention_output_reduce | 0 | 0 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 0 | 0 | 0 | 0 | 0.000000 |
| attention_output_reduce | 0 | 1 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 0 | 1 | 0 | 0 | 0.000000 |
| attention_output_reduce | 0 | 2 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 0 | 2 | 0 | 0 | 0.000000 |
| attention_output_reduce | 0 | 3 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 0 | 3 | 0 | 0 | 0.000000 |
| attention_output_reduce | 0 | 4 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 0 | 4 | 0 | 0 | 0.000000 |
| pipeline_hidden_transfer | 0 | None | 1 | 8192 | 2.163840 |
| attention_output_reduce | 1 | 5 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 1 | 5 | 0 | 0 | 0.000000 |
| attention_output_reduce | 1 | 6 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 1 | 6 | 0 | 0 | 0.000000 |
| attention_output_reduce | 1 | 7 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 1 | 7 | 0 | 0 | 0.000000 |
| attention_output_reduce | 1 | 8 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 1 | 8 | 0 | 0 | 0.000000 |
| attention_output_reduce | 1 | 9 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 1 | 9 | 0 | 0 | 0.000000 |
| pipeline_hidden_transfer | 1 | None | 1 | 8192 | 2.163840 |
| attention_output_reduce | 2 | 10 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 2 | 10 | 0 | 0 | 0.000000 |
| attention_output_reduce | 2 | 11 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 2 | 11 | 0 | 0 | 0.000000 |
| attention_output_reduce | 2 | 12 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 2 | 12 | 0 | 0 | 0.000000 |
| attention_output_reduce | 2 | 13 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 2 | 13 | 0 | 0 | 0.000000 |
| attention_output_reduce | 2 | 14 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 2 | 14 | 0 | 0 | 0.000000 |
| pipeline_hidden_transfer | 2 | None | 1 | 8192 | 2.163840 |
| attention_output_reduce | 3 | 15 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 3 | 15 | 0 | 0 | 0.000000 |
| attention_output_reduce | 3 | 16 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 3 | 16 | 0 | 0 | 0.000000 |
| attention_output_reduce | 3 | 17 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 3 | 17 | 0 | 0 | 0.000000 |
| attention_output_reduce | 3 | 18 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 3 | 18 | 0 | 0 | 0.000000 |
| attention_output_reduce | 3 | 19 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 3 | 19 | 0 | 0 | 0.000000 |
| pipeline_hidden_transfer | 3 | None | 1 | 8192 | 2.163840 |
| attention_output_reduce | 4 | 20 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 4 | 20 | 0 | 0 | 0.000000 |
| attention_output_reduce | 4 | 21 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 4 | 21 | 0 | 0 | 0.000000 |
| attention_output_reduce | 4 | 22 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 4 | 22 | 0 | 0 | 0.000000 |
| attention_output_reduce | 4 | 23 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 4 | 23 | 0 | 0 | 0.000000 |
| pipeline_hidden_transfer | 4 | None | 1 | 8192 | 2.163840 |
| attention_output_reduce | 5 | 24 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 5 | 24 | 0 | 0 | 0.000000 |
| attention_output_reduce | 5 | 25 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 5 | 25 | 0 | 0 | 0.000000 |
| attention_output_reduce | 5 | 26 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 5 | 26 | 0 | 0 | 0.000000 |
| attention_output_reduce | 5 | 27 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 5 | 27 | 0 | 0 | 0.000000 |
| pipeline_hidden_transfer | 5 | None | 1 | 8192 | 2.163840 |
| attention_output_reduce | 6 | 28 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 6 | 28 | 0 | 0 | 0.000000 |
| attention_output_reduce | 6 | 29 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 6 | 29 | 0 | 0 | 0.000000 |
| attention_output_reduce | 6 | 30 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 6 | 30 | 0 | 0 | 0.000000 |
| attention_output_reduce | 6 | 31 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 6 | 31 | 0 | 0 | 0.000000 |
| pipeline_hidden_transfer | 6 | None | 1 | 8192 | 2.163840 |
| attention_output_reduce | 7 | 32 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 7 | 32 | 0 | 0 | 0.000000 |
| attention_output_reduce | 7 | 33 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 7 | 33 | 0 | 0 | 0.000000 |
| attention_output_reduce | 7 | 34 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 7 | 34 | 0 | 0 | 0.000000 |
| attention_output_reduce | 7 | 35 | 0 | 0 | 0.000000 |
| ffn_output_reduce | 7 | 35 | 0 | 0 | 0.000000 |
| last_position_logits_all_gather | 7 | None | 0 | 0 | 0.000000 |
| selected_token_to_first_stage | 7 | None | 1 | 4 | 2.000080 |
| selected_token_first_stage_broadcast | 0 | None | 0 | 0 | 0.000000 |

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
