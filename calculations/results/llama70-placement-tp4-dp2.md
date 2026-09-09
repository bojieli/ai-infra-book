# llama70-parallel-placement — deepseek-r1-distill-llama-70b

输入：`{"batch_per_replica": 1, "capacity_bytes": 24000000000, "dp": 2, "history": 8192, "kv_dtype": "BF16", "pp": 1, "tokens": 1, "tp": 4, "weight_dtype": "BF16", "workspace_bytes": 2147483648}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| cards | 8 |
| global_requests | 2 |
| logical_parameters_per_replica | 70,553,706,496 |
| physical_weight_bytes | 282,230,652,928 |
| excess_weight_bytes_over_unsharded_replicas | 15,826,944 |
| physical_kv_bytes | 5,369,364,480 |
| maximum_card_resident_bytes | 38,097,485,824 |
| all_cards_fit_declared_budget | `false` |
| physical_matrix_flops | 320,961,773,568 |
| pipeline_network_send_payload_bytes | 0 |
| predicted_iteration_seconds | `null` |

| DP / PP / TP | 层 | Q heads | KV heads | 权重 bytes | KV bytes | 总预算占用 bytes | 可容纳 |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| 0 / 0 / 0 | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79] | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] | [0, 1] | 35278831616 | 671170560 | 38097485824 | False |
| 1 / 0 / 0 | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79] | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] | [0, 1] | 35278831616 | 671170560 | 38097485824 | False |
| 0 / 0 / 1 | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79] | [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31] | [2, 3] | 35278831616 | 671170560 | 38097485824 | False |
| 1 / 0 / 1 | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79] | [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31] | [2, 3] | 35278831616 | 671170560 | 38097485824 | False |
| 0 / 0 / 2 | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79] | [32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47] | [4, 5] | 35278831616 | 671170560 | 38097485824 | False |
| 1 / 0 / 2 | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79] | [32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47] | [4, 5] | 35278831616 | 671170560 | 38097485824 | False |
| 0 / 0 / 3 | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79] | [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63] | [6, 7] | 35278831616 | 671170560 | 38097485824 | False |
| 1 / 0 / 3 | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79] | [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63] | [6, 7] | 35278831616 | 671170560 | 38097485824 | False |

逐卡权重矩阵形状、copies、矩阵工作及 TP／PP 消息见 JSON。工作区为显式预算，非实际峰值。

计量条件：

- Public DeepSeek R1 Distill Llama70 BF16 inference: TP splits query heads, FFN intermediate width and vocabulary rows; output/down projections split input axes. Hidden norms replicate; there are no Q/K head norms. pretraining_tp=1 fixes the source model reference, not the declared deployment TP degree.
- KV head identities follow each rank query heads and the official GQA grouping. A KV head crossing multiple TP ranks is physically replicated, including its K/V projection weights and work; it is never divided into fractional heads.
- PP uses contiguous nearly equal layer counts; embedding exists only on the first stage, final norm and untied vocabulary head only on the last. Head runs on the last new position; no tied endpoint handling is inferred.
- DP means independent inference replicas, each with batch_per_replica requests and its own weights/cache. No training gradient synchronization is added.
- Capacity is checked per physical card with an explicit workspace reservation. BF16 state is retained through history+tokens. Quantization, allocator peaks, activation lifetimes and real backend feasibility remain separate.
- Matrix work includes local projections/head and valid causal attention only, not scalar operations. Replicated K/V projection work is counted on every executing rank; DP increases aggregate work with aggregate requests.
- Two output all-reduces per local layer is the declared basic TP graph; message bytes are full activation, not link traffic. Vocabulary-parallel embedding reduction, logits collection/sampling, norm/cast communication require a fuller execution graph.
- PP transfers full replicated hidden activation from each TP rank to its matching next-stage rank. Payload totals therefore include TP copies; alternate sharded pipeline interfaces need different placement. No overlap, bubbles, bandwidth or latency prediction is claimed.

固定来源：

- [configs/models/deepseek-r1-distill-llama-70b/config.json](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-70B/resolve/b1c0b44b4369b597ad119a196caf79a9c40e141e/config.json)，SHA256 `95ef9768e4741543dbfaf0c274f101855883ff338b235c99eca2b6a4f4abee12`。
- [sources/deepseek-r1-distill-llama-70b/model.safetensors.index.json](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-70B/resolve/b1c0b44b4369b597ad119a196caf79a9c40e141e/model.safetensors.index.json)，SHA256 `3b91e78c60e2708c9354d46fe4fc20520d0a12713e13d5ffab60118305c96620`。
- [sources/deepseek-r1-distill-llama-70b/README.md](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-70B/resolve/b1c0b44b4369b597ad119a196caf79a9c40e141e/README.md)，SHA256 `d26d26ddb518fee60c6c6bf7a708bd751b1619d93a4944f188143693d956c77f`。
- [sources/deepseek-r1-distill-llama-70b/modeling_llama.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/llama/modeling_llama.py)，SHA256 `9f7e93602e876a8f3f171e4911df5a5898ac407b8eb8982099e52b53daf0469e`。
- [sources/deepseek-r1-distill-llama-70b/configuration_llama.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/llama/configuration_llama.py)，SHA256 `c13469c62dc2c4fe76cc5bc50e6db2de21e302dae259945ef03308f0ac429ff6`。
- [research/llama70-adapter/modeling_rope_utils.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/modeling_rope_utils.py)，SHA256 `c28b3e88edca8fdb5497e5c36091bf753db49bd94ace33a84e9f9c61cbf66032`。
