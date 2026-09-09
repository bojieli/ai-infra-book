# qwen-dense-parallel-placement — qwen3-32b

输入：`{"batch_per_replica": 1, "capacity_bytes": 24000000000, "dp": 1, "history": 8192, "kv_dtype": "BF16", "pp": 1, "tokens": 1, "tp": 8, "weight_dtype": "BF16", "workspace_bytes": 2147483648}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| cards | 8 |
| global_requests | 1 |
| logical_parameters_per_replica | 32,762,123,264 |
| physical_weight_bytes | 65,533,722,624 |
| excess_weight_bytes_over_unsharded_replicas | 9,476,096 |
| physical_kv_bytes | 2,147,745,792 |
| maximum_card_resident_bytes | 10,607,667,200 |
| all_cards_fit_declared_budget | `true` |
| physical_matrix_flops | 81,149,034,496 |
| pipeline_network_send_payload_bytes | 0 |
| predicted_iteration_seconds | `null` |

| DP / PP / TP | 层 | Q heads | KV heads | 权重 bytes | KV bytes | 总预算占用 bytes | 可容纳 |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| 0 / 0 / 0 | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63] | [0, 1, 2, 3, 4, 5, 6, 7] | [0] | 8191715328 | 268468224 | 10607667200 | True |
| 0 / 0 / 1 | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63] | [8, 9, 10, 11, 12, 13, 14, 15] | [1] | 8191715328 | 268468224 | 10607667200 | True |
| 0 / 0 / 2 | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63] | [16, 17, 18, 19, 20, 21, 22, 23] | [2] | 8191715328 | 268468224 | 10607667200 | True |
| 0 / 0 / 3 | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63] | [24, 25, 26, 27, 28, 29, 30, 31] | [3] | 8191715328 | 268468224 | 10607667200 | True |
| 0 / 0 / 4 | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63] | [32, 33, 34, 35, 36, 37, 38, 39] | [4] | 8191715328 | 268468224 | 10607667200 | True |
| 0 / 0 / 5 | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63] | [40, 41, 42, 43, 44, 45, 46, 47] | [5] | 8191715328 | 268468224 | 10607667200 | True |
| 0 / 0 / 6 | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63] | [48, 49, 50, 51, 52, 53, 54, 55] | [6] | 8191715328 | 268468224 | 10607667200 | True |
| 0 / 0 / 7 | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63] | [56, 57, 58, 59, 60, 61, 62, 63] | [7] | 8191715328 | 268468224 | 10607667200 | True |

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

- [configs/models/qwen3-32b/config.json](https://huggingface.co/Qwen/Qwen3-32B/resolve/9216db5781bf21249d130ec9da846c4624c16137/config.json)，SHA256 `97e295b63283935788fac5e4f8860862a56d4089538cafc93f0431f2ebe483bb`。
- [sources/qwen3-32b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-32B/resolve/9216db5781bf21249d130ec9da846c4624c16137/model.safetensors.index.json)，SHA256 `bed42c6c55274bc08a1f616bceb3bcb84b3f02cb6584c573bd18c6519291ecd0`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
