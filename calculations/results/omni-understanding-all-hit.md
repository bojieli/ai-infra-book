# omni-understanding-request — qwen3-omni-30b-a3b-instruct

输入：`{"audio_cache_hits": [true], "dtype": "bf16", "image_cache_hits": [true], "image_grids": [[1, 40, 40]], "mel_lengths": [1000], "output_tokens": 32, "routing": "balanced", "text_tokens": 128, "video_cache_hits": [], "video_grids": []}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| matrix_flops | 4,378,703,167,488 |
| accounted_scalar_flops | 4,648,368,753 |
| accounted_interface_bytes | 286,628,597,420 |
| prompt_positions | 658 |
| output_tokens | 32 |
| decode_calls | 31 |
| consumed_positions | 689 |
| kv_bytes_per_position | 98,304 |
| kv_after_prefill_bytes | 64,684,032 |
| kv_after_last_forward_bytes | 67,731,456 |
| logical_thinker_parameters | 30,532,646,912 |
| uniform_thinker_parameter_bytes | 61,065,293,824 |
| delivered_feature_bytes | 7,086,080 |
| first_output_latency_seconds | `null` |
| request_latency_seconds | `null` |
| complete_runtime_peak_bytes | `null` |

| 请求节点 | 依赖 | 矩阵FLOPs | 已计标量 | 已计接口bytes |
| --- | --- | --- | --- | --- |
| prompt_embedding_lookup | [] | 0 | 0 | 5395600 |
| audio_feature_cache_read | ['prompt_embedding_lookup'] | 0 | 0 | 532480 |
| audio_placeholder_replace | ['audio_feature_cache_read'] | 0 | 0 | 5923474 |
| image_encoder | ['audio_placeholder_replace'] | 0 | 0 | 0 |
| image_feature_cache_read | ['image_encoder'] | 0 | 0 | 6553600 |
| image_placeholder_replace | ['image_feature_cache_read'] | 0 | 0 | 7029394 |
| thinker_prefill | ['image_placeholder_replace'] | 4173672480768 | 4376673810 | 95175510016 |
| thinker_decode_0 | ['thinker_prefill'] | 6602096640 | 8672193 | 6173426696 |
| thinker_decode_1 | ['thinker_decode_0'] | 6602883072 | 8678337 | 6173537288 |
| thinker_decode_2 | ['thinker_decode_1'] | 6603669504 | 8684481 | 6173647880 |
| thinker_decode_3 | ['thinker_decode_2'] | 6604455936 | 8690625 | 6173758472 |
| thinker_decode_4 | ['thinker_decode_3'] | 6605242368 | 8696769 | 6173869064 |
| thinker_decode_5 | ['thinker_decode_4'] | 6606028800 | 8702913 | 6173979656 |
| thinker_decode_6 | ['thinker_decode_5'] | 6606815232 | 8709057 | 6174090248 |
| thinker_decode_7 | ['thinker_decode_6'] | 6607601664 | 8715201 | 6174200840 |
| thinker_decode_8 | ['thinker_decode_7'] | 6608388096 | 8721345 | 6174311432 |
| thinker_decode_9 | ['thinker_decode_8'] | 6609174528 | 8727489 | 6174422024 |
| thinker_decode_10 | ['thinker_decode_9'] | 6609960960 | 8733633 | 6174532616 |
| thinker_decode_11 | ['thinker_decode_10'] | 6610747392 | 8739777 | 6174643208 |
| thinker_decode_12 | ['thinker_decode_11'] | 6611533824 | 8745921 | 6174753800 |
| thinker_decode_13 | ['thinker_decode_12'] | 6612320256 | 8752065 | 6174864392 |
| thinker_decode_14 | ['thinker_decode_13'] | 6613106688 | 8758209 | 6174974984 |
| thinker_decode_15 | ['thinker_decode_14'] | 6613893120 | 8764353 | 6175085576 |
| thinker_decode_16 | ['thinker_decode_15'] | 6614679552 | 8770497 | 6175196168 |
| thinker_decode_17 | ['thinker_decode_16'] | 6615465984 | 8776641 | 6175306760 |
| thinker_decode_18 | ['thinker_decode_17'] | 6616252416 | 8782785 | 6175417352 |
| thinker_decode_19 | ['thinker_decode_18'] | 6617038848 | 8788929 | 6175527944 |
| thinker_decode_20 | ['thinker_decode_19'] | 6617825280 | 8795073 | 6175638536 |
| thinker_decode_21 | ['thinker_decode_20'] | 6618611712 | 8801217 | 6175749128 |
| thinker_decode_22 | ['thinker_decode_21'] | 6619398144 | 8807361 | 6175859720 |
| thinker_decode_23 | ['thinker_decode_22'] | 6620184576 | 8813505 | 6175970312 |
| thinker_decode_24 | ['thinker_decode_23'] | 6620971008 | 8819649 | 6176080904 |
| thinker_decode_25 | ['thinker_decode_24'] | 6621757440 | 8825793 | 6176191496 |
| thinker_decode_26 | ['thinker_decode_25'] | 6622543872 | 8831937 | 6176302088 |
| thinker_decode_27 | ['thinker_decode_26'] | 6623330304 | 8838081 | 6176412680 |
| thinker_decode_28 | ['thinker_decode_27'] | 6624116736 | 8844225 | 6176523272 |
| thinker_decode_29 | ['thinker_decode_28'] | 6624903168 | 8850369 | 6176633864 |
| thinker_decode_30 | ['thinker_decode_29'] | 6625689600 | 8856513 | 6176744456 |

prefill；所有decode逐次工作见JSON。

| 矩阵 | M | K | N | 层重复 | 已汇总FLOPs |
| --- | --- | --- | --- | --- | --- |
| q | 658 | 2048 | 4096 | 48 | 529891590144 |
| k | 658 | 2048 | 512 | 48 | 66236448768 |
| v | 658 | 2048 | 512 | 48 | 66236448768 |
| o | 658 | 4096 | 2048 | 48 | 529891590144 |
| router | 658 | 2048 | 128 | 48 | 16559112192 |
| expert_gate | 5264 | 2048 | 768 | 48 | 794837385216 |
| expert_up | 5264 | 2048 | 768 | 48 | 794837385216 |
| expert_down | 5264 | 768 | 2048 | 48 | 794837385216 |
| output_head | 658 | 2048 | 152064 | 1 | 409838026752 |

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

DeepStack注入：`{"branches": 3, "visual_positions": 400, "consumer_layers": [0, 1, 2], "additions": 2457600, "gather_clone_add_scatter_interface_bytes": 44236800, "injected_only_during_prefill": true}`

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
