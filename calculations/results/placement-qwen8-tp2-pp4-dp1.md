# qwen-dense-parallel-placement — qwen3-8b

输入：`{"batch_per_replica": 1, "capacity_bytes": 24000000000, "dp": 1, "history": 8192, "kv_dtype": "BF16", "pp": 4, "tokens": 1, "tp": 2, "weight_dtype": "BF16", "workspace_bytes": 2147483648}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| cards | 8 |
| global_requests | 1 |
| logical_parameters_per_replica | 8,190,735,360 |
| physical_weight_bytes | 16,382,087,168 |
| excess_weight_bytes_over_unsharded_replicas | 616,448 |
| physical_kv_bytes | 1,208,107,008 |
| maximum_card_resident_bytes | 4,657,428,992 |
| all_cards_fit_declared_budget | `true` |
| physical_matrix_flops | 19,968,622,592 |
| pipeline_network_send_payload_bytes | 49,152 |
| predicted_iteration_seconds | `null` |

| DP / PP / TP | 层 | Q heads | KV heads | 权重 bytes | KV bytes | 总预算占用 bytes | 可容纳 |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| 0 / 0 / 0 | [0, 1, 2, 3, 4, 5, 6, 7, 8] | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] | [0, 1, 2, 3] | 2358923776 | 151013376 | 4657420800 | True |
| 0 / 0 / 1 | [0, 1, 2, 3, 4, 5, 6, 7, 8] | [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31] | [4, 5, 6, 7] | 2358923776 | 151013376 | 4657420800 | True |
| 0 / 1 / 0 | [9, 10, 11, 12, 13, 14, 15, 16, 17] | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] | [0, 1, 2, 3] | 1736593920 | 151013376 | 4035090944 | True |
| 0 / 1 / 1 | [9, 10, 11, 12, 13, 14, 15, 16, 17] | [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31] | [4, 5, 6, 7] | 1736593920 | 151013376 | 4035090944 | True |
| 0 / 2 / 0 | [18, 19, 20, 21, 22, 23, 24, 25, 26] | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] | [0, 1, 2, 3] | 1736593920 | 151013376 | 4035090944 | True |
| 0 / 2 / 1 | [18, 19, 20, 21, 22, 23, 24, 25, 26] | [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31] | [4, 5, 6, 7] | 1736593920 | 151013376 | 4035090944 | True |
| 0 / 3 / 0 | [27, 28, 29, 30, 31, 32, 33, 34, 35] | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] | [0, 1, 2, 3] | 2358931968 | 151013376 | 4657428992 | True |
| 0 / 3 / 1 | [27, 28, 29, 30, 31, 32, 33, 34, 35] | [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31] | [4, 5, 6, 7] | 2358931968 | 151013376 | 4657428992 | True |

逐卡权重矩阵形状、copies、矩阵工作及 TP／PP 消息见 JSON。工作区为显式预算，非实际峰值。

计量条件：

- Basic BF16 Qwen3 Dense inference: TP splits query heads, FFN intermediate width and vocabulary rows. Output/down projections split their input axes. Per-head and hidden norm scales replicate on TP ranks.
- KV head identities follow each rank query heads and the official GQA grouping. A KV head crossing multiple TP ranks is physically replicated, including its K/V projection weights and work; it is never divided into fractional heads.
- PP uses contiguous nearly equal layer counts; embedding exists only on the first stage, final norm and untied vocabulary head only on the last. Head runs on the last new position; no tied endpoint handling is inferred.
- DP means independent inference replicas, each with batch_per_replica requests and its own weights/cache. No training gradient synchronization is added.
- Capacity is checked per physical card with an explicit workspace reservation. BF16 state is retained through history+tokens. Quantization, allocator peaks, activation lifetimes and real backend feasibility remain separate.
- Matrix work includes local projections/head and valid causal attention only, not scalar operations. Replicated K/V projection work is counted on every executing rank; DP increases aggregate work with aggregate requests.
- Two output all-reduces per local layer is the declared basic TP graph; message bytes are full activation, not link traffic. Vocabulary-parallel embedding reduction, logits collection/sampling, norm/cast communication require a fuller execution graph.
- PP transfers full replicated hidden activation from each TP rank to its matching next-stage rank. Payload totals therefore include TP copies; alternate sharded pipeline interfaces need different placement. No overlap, bubbles, bandwidth or latency prediction is claimed.

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
