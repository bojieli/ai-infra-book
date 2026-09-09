# qwen-dense-communication-path — qwen3-8b

输入：`{"bandwidth_bytes_per_second": 50000000000, "batch_per_replica": 1, "dp": 1, "logit_element_bytes": 4, "pp": 4, "startup_ns": 2000, "tokens": 1, "tp": 2}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| activation_bytes | 8,192 |
| full_last_position_logit_bytes | 607,744 |
| vocabulary_logit_shard_bytes | 303,872 |
| selected_token_id_bytes | 4 |
| nonempty_communication_operations | 79 |
| network_send_bytes_per_replica | 1,852,936 |
| network_send_bytes_all_replicas | 1,852,936 |
| operation_stage_accounted_bytes | `[327684, 311296, 311296, 902660]` |
| serial_communication_path_seconds | 0.00032252944000000003 |
| startup_seconds | 0.00030399999999999996 |
| bandwidth_seconds | 1.852944e-05 |
| predicted_iteration_seconds | `null` |

| 操作 | PP | 层 | 轮次 | 每副本网络发送 bytes | 模型 μs |
| --- | ---: | --- | ---: | ---: | ---: |
| vocabulary_embedding_reduce | 0 | None | 2 | 16384 | 4.163840 |
| attention_output_reduce | 0 | 0 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 0 | 0 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 0 | 1 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 0 | 1 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 0 | 2 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 0 | 2 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 0 | 3 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 0 | 3 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 0 | 4 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 0 | 4 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 0 | 5 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 0 | 5 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 0 | 6 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 0 | 6 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 0 | 7 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 0 | 7 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 0 | 8 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 0 | 8 | 2 | 16384 | 4.163840 |
| pipeline_hidden_transfer | 0 | None | 1 | 16384 | 2.163840 |
| attention_output_reduce | 1 | 9 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 1 | 9 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 1 | 10 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 1 | 10 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 1 | 11 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 1 | 11 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 1 | 12 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 1 | 12 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 1 | 13 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 1 | 13 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 1 | 14 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 1 | 14 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 1 | 15 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 1 | 15 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 1 | 16 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 1 | 16 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 1 | 17 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 1 | 17 | 2 | 16384 | 4.163840 |
| pipeline_hidden_transfer | 1 | None | 1 | 16384 | 2.163840 |
| attention_output_reduce | 2 | 18 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 2 | 18 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 2 | 19 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 2 | 19 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 2 | 20 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 2 | 20 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 2 | 21 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 2 | 21 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 2 | 22 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 2 | 22 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 2 | 23 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 2 | 23 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 2 | 24 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 2 | 24 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 2 | 25 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 2 | 25 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 2 | 26 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 2 | 26 | 2 | 16384 | 4.163840 |
| pipeline_hidden_transfer | 2 | None | 1 | 16384 | 2.163840 |
| attention_output_reduce | 3 | 27 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 3 | 27 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 3 | 28 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 3 | 28 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 3 | 29 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 3 | 29 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 3 | 30 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 3 | 30 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 3 | 31 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 3 | 31 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 3 | 32 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 3 | 32 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 3 | 33 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 3 | 33 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 3 | 34 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 3 | 34 | 2 | 16384 | 4.163840 |
| attention_output_reduce | 3 | 35 | 2 | 16384 | 4.163840 |
| ffn_output_reduce | 3 | 35 | 2 | 16384 | 4.163840 |
| last_position_logits_all_gather | 3 | None | 1 | 607744 | 8.077440 |
| selected_token_to_first_stage | 3 | None | 1 | 4 | 2.000080 |
| selected_token_first_stage_broadcast | 0 | None | 1 | 4 | 2.000080 |

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
