# llama70-single-device-capacity-scan — deepseek-r1-distill-llama-70b

输入：`{"capacities": [24000000000, 48000000000, 80000000000], "group_size": 128, "kv_element_bytes": 2, "length": 8192, "scale_bytes": 2, "workspace_bytes": 2147483648}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| logical_parameters | 70,553,706,496 |
| bf16_weight_bytes | 141,107,412,992 |
| eight_bit_scheme_bytes | 73,725,919,232 |
| four_bit_scheme_bytes | 39,500,398,592 |
| bf16_kv_bytes_per_request | 2,684,354,560 |
| measured_resident_bytes | `null` |

| 矩阵位宽 | 预算 GB | 权重 bytes | 工作区 bytes | 每请求 KV bytes | 权重及工作区够放 | 最大并发 |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| 16 | 24 | 141107412992 | 2147483648 | 2684354560 | False | 0 |
| 16 | 48 | 141107412992 | 2147483648 | 2684354560 | False | 0 |
| 16 | 80 | 141107412992 | 2147483648 | 2684354560 | False | 0 |
| 8 | 24 | 73725919232 | 2147483648 | 2684354560 | False | 0 |
| 8 | 48 | 73725919232 | 2147483648 | 2684354560 | False | 0 |
| 8 | 80 | 73725919232 | 2147483648 | 2684354560 | True | 1 |
| 4 | 24 | 39500398592 | 2147483648 | 2684354560 | False | 0 |
| 4 | 48 | 39500398592 | 2147483648 | 2684354560 | True | 2 |
| 4 | 80 | 39500398592 | 2147483648 | 2684354560 | True | 14 |

矩阵逐行打包与 scale 元数据分项：

| 位宽 | 参数载荷 bytes | scale bytes |
| --- | ---: | ---: |
| 16 | 141107412992 | 0 |
| 8 | 72656371712 | 1069547520 |
| 4 | 38430851072 | 1069547520 |

逐权重形状、copies 和打包字节见 JSON；并发只在声明工作区预算下成立。

计量条件：

- Shapes reuse the pinned public DeepSeek R1 Distill Llama70 adapter: 80 bias-free Llama layers, no Q/K head norms, untied vocabulary matrices; no nominal 70e9 substitution. This is TP=PP=DP=1 whole-model residency, not a distributed placement or kernel compatibility claim.
- BF16 baseline keeps all parameters at two bytes. Low-bit teaching schemes quantize eligible 2-D linear matrices per output row and K group, retaining embedding, vocabulary head, router and one-dimensional norm parameters as BF16.
- Each quantized row packs independently, rounding partial bytes upward; each ceil(K/group_size) group has scale_bytes metadata. Symmetric scheme has no zero points. No claim of a particular released quantized checkpoint, kernel support or quality equivalence.
- KV uses pinned full-history GQA geometry and BF16. Every concurrent request has the same retained length; no physical prefix sharing, paging slack, offloading or parallel replication.
- Capacities are explicit single-device byte budgets (defaults 24/48/80 decimal GB), not aggregate eight-card memory and not assertions about a specific SKU. Actual allocatable budget must account for reservations.
- Workspace is an explicit reserved budget, not a computed allocator peak. Maximum requests is conditional on it; temporary dequantization, graph pools and batch-dependent workspace may require more.
- Zero requests can mean weights/workspace already fail or insufficient room for one KV. The fit flag and signed remaining bytes distinguish these cases. No throughput or deployability is inferred.

固定来源：

- [configs/models/deepseek-r1-distill-llama-70b/config.json](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-70B/resolve/b1c0b44b4369b597ad119a196caf79a9c40e141e/config.json)，SHA256 `95ef9768e4741543dbfaf0c274f101855883ff338b235c99eca2b6a4f4abee12`。
- [sources/deepseek-r1-distill-llama-70b/model.safetensors.index.json](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-70B/resolve/b1c0b44b4369b597ad119a196caf79a9c40e141e/model.safetensors.index.json)，SHA256 `3b91e78c60e2708c9354d46fe4fc20520d0a12713e13d5ffab60118305c96620`。
- [sources/deepseek-r1-distill-llama-70b/README.md](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-70B/resolve/b1c0b44b4369b597ad119a196caf79a9c40e141e/README.md)，SHA256 `d26d26ddb518fee60c6c6bf7a708bd751b1619d93a4944f188143693d956c77f`。
- [sources/deepseek-r1-distill-llama-70b/modeling_llama.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/llama/modeling_llama.py)，SHA256 `9f7e93602e876a8f3f171e4911df5a5898ac407b8eb8982099e52b53daf0469e`。
- [sources/deepseek-r1-distill-llama-70b/configuration_llama.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/llama/configuration_llama.py)，SHA256 `c13469c62dc2c4fe76cc5bc50e6db2de21e302dae259945ef03308f0ac429ff6`。
- [research/llama70-adapter/modeling_rope_utils.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/modeling_rope_utils.py)，SHA256 `c28b3e88edca8fdb5497e5c36091bf753db49bd94ace33a84e9f9c61cbf66032`。
