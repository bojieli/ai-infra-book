# omni-understanding-request — qwen3-omni-30b-a3b-instruct

输入：`{"audio_cache_hits": [], "dtype": "bf16", "image_cache_hits": [], "image_grids": [], "mel_lengths": [], "output_tokens": 32, "routing": "balanced", "text_tokens": 128, "video_cache_hits": [], "video_grids": []}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| matrix_flops | 977,333,649,408 |
| accounted_scalar_flops | 813,255,903 |
| accounted_interface_bytes | 253,050,814,712 |
| prompt_positions | 128 |
| output_tokens | 32 |
| decode_calls | 31 |
| consumed_positions | 159 |
| kv_bytes_per_position | 98,304 |
| kv_after_prefill_bytes | 12,582,912 |
| kv_after_last_forward_bytes | 15,630,336 |
| logical_thinker_parameters | 30,532,646,912 |
| uniform_thinker_parameter_bytes | 61,065,293,824 |
| delivered_feature_bytes | 0 |
| first_output_latency_seconds | `null` |
| request_latency_seconds | `null` |
| complete_runtime_peak_bytes | `null` |

| 请求节点 | 依赖 | 矩阵FLOPs | 已计标量 | 已计接口bytes |
| --- | --- | --- | --- | --- |
| prompt_embedding_lookup | [] | 0 | 0 | 1049600 |
| thinker_prefill | ['prompt_embedding_lookup'] | 785224040448 | 642506880 | 63439138816 |
| thinker_decode_0 | ['thinker_prefill'] | 6185287680 | 5415873 | 6114812936 |
| thinker_decode_1 | ['thinker_decode_0'] | 6186074112 | 5422017 | 6114923528 |
| thinker_decode_2 | ['thinker_decode_1'] | 6186860544 | 5428161 | 6115034120 |
| thinker_decode_3 | ['thinker_decode_2'] | 6187646976 | 5434305 | 6115144712 |
| thinker_decode_4 | ['thinker_decode_3'] | 6188433408 | 5440449 | 6115255304 |
| thinker_decode_5 | ['thinker_decode_4'] | 6189219840 | 5446593 | 6115365896 |
| thinker_decode_6 | ['thinker_decode_5'] | 6190006272 | 5452737 | 6115476488 |
| thinker_decode_7 | ['thinker_decode_6'] | 6190792704 | 5458881 | 6115587080 |
| thinker_decode_8 | ['thinker_decode_7'] | 6191579136 | 5465025 | 6115697672 |
| thinker_decode_9 | ['thinker_decode_8'] | 6192365568 | 5471169 | 6115808264 |
| thinker_decode_10 | ['thinker_decode_9'] | 6193152000 | 5477313 | 6115918856 |
| thinker_decode_11 | ['thinker_decode_10'] | 6193938432 | 5483457 | 6116029448 |
| thinker_decode_12 | ['thinker_decode_11'] | 6194724864 | 5489601 | 6116140040 |
| thinker_decode_13 | ['thinker_decode_12'] | 6195511296 | 5495745 | 6116250632 |
| thinker_decode_14 | ['thinker_decode_13'] | 6196297728 | 5501889 | 6116361224 |
| thinker_decode_15 | ['thinker_decode_14'] | 6197084160 | 5508033 | 6116471816 |
| thinker_decode_16 | ['thinker_decode_15'] | 6197870592 | 5514177 | 6116582408 |
| thinker_decode_17 | ['thinker_decode_16'] | 6198657024 | 5520321 | 6116693000 |
| thinker_decode_18 | ['thinker_decode_17'] | 6199443456 | 5526465 | 6116803592 |
| thinker_decode_19 | ['thinker_decode_18'] | 6200229888 | 5532609 | 6116914184 |
| thinker_decode_20 | ['thinker_decode_19'] | 6201016320 | 5538753 | 6117024776 |
| thinker_decode_21 | ['thinker_decode_20'] | 6201802752 | 5544897 | 6117135368 |
| thinker_decode_22 | ['thinker_decode_21'] | 6202589184 | 5551041 | 6117245960 |
| thinker_decode_23 | ['thinker_decode_22'] | 6203375616 | 5557185 | 6117356552 |
| thinker_decode_24 | ['thinker_decode_23'] | 6204162048 | 5563329 | 6117467144 |
| thinker_decode_25 | ['thinker_decode_24'] | 6204948480 | 5569473 | 6117577736 |
| thinker_decode_26 | ['thinker_decode_25'] | 6205734912 | 5575617 | 6117688328 |
| thinker_decode_27 | ['thinker_decode_26'] | 6206521344 | 5581761 | 6117798920 |
| thinker_decode_28 | ['thinker_decode_27'] | 6207307776 | 5587905 | 6117909512 |
| thinker_decode_29 | ['thinker_decode_28'] | 6208094208 | 5594049 | 6118020104 |
| thinker_decode_30 | ['thinker_decode_29'] | 6208880640 | 5600193 | 6118130696 |

prefill；所有decode逐次工作见JSON。

| 矩阵 | M | K | N | 层重复 | 已汇总FLOPs |
| --- | --- | --- | --- | --- | --- |
| q | 128 | 2048 | 4096 | 48 | 103079215104 |
| k | 128 | 2048 | 512 | 48 | 12884901888 |
| v | 128 | 2048 | 512 | 48 | 12884901888 |
| o | 128 | 4096 | 2048 | 48 | 103079215104 |
| router | 128 | 2048 | 128 | 48 | 3221225472 |
| expert_gate | 1024 | 2048 | 768 | 48 | 154618822656 |
| expert_up | 1024 | 2048 | 768 | 48 | 154618822656 |
| expert_down | 1024 | 768 | 2048 | 48 | 154618822656 |
| output_head | 128 | 2048 | 152064 | 1 | 79725330432 |

first_decode；所有decode逐次工作见JSON。

| 矩阵 | M | K | N | 层重复 | 已汇总FLOPs |
| --- | --- | --- | --- | --- | --- |
| q | 1 | 2048 | 4096 | 48 | 805306368 |
| k | 1 | 2048 | 512 | 48 | 100663296 |
| v | 1 | 2048 | 512 | 48 | 100663296 |
| o | 1 | 4096 | 2048 | 48 | 805306368 |
| router | 1 | 2048 | 128 | 48 | 25165824 |
| expert_gate | 8 | 2048 | 768 | 48 | 1207959552 |
| expert_up | 8 | 2048 | 768 | 48 | 1207959552 |
| expert_down | 8 | 768 | 2048 | 48 | 1207959552 |
| output_head | 1 | 2048 | 152064 | 1 | 622854144 |

last_decode；所有decode逐次工作见JSON。

| 矩阵 | M | K | N | 层重复 | 已汇总FLOPs |
| --- | --- | --- | --- | --- | --- |
| q | 1 | 2048 | 4096 | 48 | 805306368 |
| k | 1 | 2048 | 512 | 48 | 100663296 |
| v | 1 | 2048 | 512 | 48 | 100663296 |
| o | 1 | 4096 | 2048 | 48 | 805306368 |
| router | 1 | 2048 | 128 | 48 | 25165824 |
| expert_gate | 8 | 2048 | 768 | 48 | 1207959552 |
| expert_up | 8 | 2048 | 768 | 48 | 1207959552 |
| expert_down | 8 | 768 | 2048 | 48 | 1207959552 |
| output_head | 1 | 2048 | 152064 | 1 | 622854144 |

音频缓存身份及实际miss分段：`{"miss_item_indices": [], "actual_miss_chunk_execution": null, "actual_miss_segments": [], "segment_audio_index_scope": "Indices address the compact miss batch, mapped by miss_item_indices.", "required_cache_identity": ["model/source revision", "processed mel content", "dtype", "attention execution path", "batch padded CNN width and resulting segmentation window"], "validity": "Caller asserts cache identity matches the intended encoder execution. Equal embedding counts do not prove equal features. Removing hits may change the padded width/attention segmentation of short miss items; this ledger reports their actual miss batch, not equivalence to an uncached full batch."}`

DeepStack注入：`{"branches": 0, "visual_positions": 0, "consumer_layers": [], "additions": 0, "gather_clone_add_scatter_interface_bytes": 0, "injected_only_during_prefill": true}`

计量条件：

- One understanding request generating text, not Talker/codec audio output. text_tokens includes all caller-tokenized control/delimiter/template positions; processed patch grids and valid mel lengths are explicit. No tokenizer, raw media preparation or language prefix-cache hit is inferred.
- Audio, image and video features replace existing placeholders; they are not appended a second time. Image and video encoder calls stay separate as in the pinned wrapper. Encoder feature-cache hits remove their encoder work, never their placeholder positions or Thinker prefill.
- Thinker uses its actual 48-layer GQA/top-8 of128 MoE structure; no 6ND or advertised active-parameter scaling. Balanced/concentrated expert histograms are declared conditional inputs at every layer. Matrix work is sum of selected expert rows; resident capacity includes all experts.
- Source lm_head processes all prompt rows. Prefill produces output token one; exactly G-1 one-token forwards produce the rest. Last returned token is not consumed, so final KV has P+G-1 positions.
- DeepStack image/video features are combined when both exist and injected after Thinker layers0/1/2 during prefill only. Add/gather/clone/scatter counted once here, not in both encoder and language totals.
- The dependency chain follows the declared serial source path; kernel concurrency, modality parallel serving and cache transport schedules require separate measured/input evidence. Totals are accounted matrices/scalars/interfaces; special primitives, router dispatch internals, sampling, mRoPE index construction and complete runtime allocation remain gaps.
- Thinker attention matrices count valid causal query/key pairs. Dense masked eager kernels may perform additional masked products; no physical kernel work is asserted. Input-audio execution uses the declared segmented varlen path and its source-specific boundaries.
- Logical Thinker parameter count is config/source derived, not checkpoint-header verified. Uniform operands/KV dtype is a comparison convention; no timing is fabricated from peak compute or this interface sum.

固定来源：

- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/qwen3-omni-30b-a3b-instruct/README.md](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct/resolve/26291f793822fb6be9555850f06dfe95f2d7e695/README.md)，SHA256 `0e44065c4c4a27071f7239afd5b5a33af5bc2e437dd7ea9950e51aafabfde3df`。
- [configs/models/qwen3-omni-30b-a3b-instruct/config.json](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct/resolve/26291f793822fb6be9555850f06dfe95f2d7e695/config.json)，SHA256 `eab5093d47807aaf894119506b238b2b1cee70d08456e894fee9a012d88f2e0d`。
- [sources/qwen3-omni-30b-a3b-instruct/generation_config.json](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct/resolve/26291f793822fb6be9555850f06dfe95f2d7e695/generation_config.json)，SHA256 `7fa40989be8e43c078907810c41c25d33747523afce3d5a34d5850f930c886cb`。
- [sources/qwen3-omni-30b-a3b-instruct/preprocessor_config.json](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct/resolve/26291f793822fb6be9555850f06dfe95f2d7e695/preprocessor_config.json)，SHA256 `b10e27fd4542cf89ec7145942b87f3e65408d4e9f9d031a29acdd293c15fb3fc`。
- [sources/qwen3-omni-30b-a3b-instruct/tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct/resolve/26291f793822fb6be9555850f06dfe95f2d7e695/tokenizer_config.json)，SHA256 `dc3c31c3bdaedd5016382bb3cbe07323026775ad51f5a4fb564505992ae4a670`。
- [research/generative-audio-analysis/transformers/src/transformers/models/qwen3_omni_moe/modeling_qwen3_omni_moe.py](https://raw.githubusercontent.com/huggingface/transformers/8cb5963cc22174954e7dca2c0a3320b7dc2f4edc/src/transformers/models/qwen3_omni_moe/modeling_qwen3_omni_moe.py)，SHA256 `809eaeb4d40cb0e59965a85b5f85ddc07e9ab7b6cdae84972c711f8cdadec296`。
- [research/generative-audio-analysis/transformers/src/transformers/models/qwen3_omni_moe/configuration_qwen3_omni_moe.py](https://raw.githubusercontent.com/huggingface/transformers/8cb5963cc22174954e7dca2c0a3320b7dc2f4edc/src/transformers/models/qwen3_omni_moe/configuration_qwen3_omni_moe.py)，SHA256 `779bf4b816425448d5d3a2ffa57928d1c7b7c10e2d66b09371fceaee62bcbf89`。
- [research/generative-audio-analysis/transformers-current/src/transformers/models/qwen3_omni_moe/modeling_qwen3_omni_moe.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_omni_moe/modeling_qwen3_omni_moe.py)，SHA256 `0ec28dd7714f09de8749edc958c25c0ebcc0628c9c2a0dca3abd905e7cddab04`。
