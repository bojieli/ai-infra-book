# omni-understanding-request — qwen3-omni-30b-a3b-instruct

输入：`{"audio_cache_hits": [false], "dtype": "bf16", "image_cache_hits": [false], "image_grids": [[1, 40, 40]], "mel_lengths": [1000], "output_tokens": 32, "routing": "balanced", "text_tokens": 128, "video_cache_hits": [false], "video_grids": [[4, 20, 30]]}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| matrix_flops | 12,752,865,312,768 |
| accounted_scalar_flops | 25,967,702,223 |
| accounted_interface_bytes | 397,185,380,638 |
| prompt_positions | 1,258 |
| output_tokens | 32 |
| decode_calls | 31 |
| consumed_positions | 1,289 |
| kv_bytes_per_position | 98,304 |
| kv_after_prefill_bytes | 123,666,432 |
| kv_after_last_forward_bytes | 126,713,856 |
| logical_thinker_parameters | 30,532,646,912 |
| uniform_thinker_parameter_bytes | 61,065,293,824 |
| delivered_feature_bytes | 16,916,480 |
| first_output_latency_seconds | `null` |
| request_latency_seconds | `null` |
| complete_runtime_peak_bytes | `null` |

| 请求节点 | 依赖 | 矩阵FLOPs | 已计标量 | 已计接口bytes |
| --- | --- | --- | --- | --- |
| prompt_embedding_lookup | [] | 0 | 0 | 10315600 |
| audio_encoder | ['prompt_embedding_lookup'] | 211204423680 | 184427010 | 1955579266 |
| audio_placeholder_replace | ['audio_encoder'] | 0 | 0 | 10839274 |
| image_encoder | ['audio_placeholder_replace'] | 1737739468800 | 7548505920 | 16761237512 |
| image_placeholder_replace | ['image_encoder'] | 0 | 0 | 11945194 |
| video_encoder | ['image_placeholder_replace'] | 2308010803200 | 7161043140 | 16290726352 |
| video_placeholder_replace | ['video_encoder'] | 0 | 0 | 12764394 |
| joint_deepstack_pack | ['video_placeholder_replace'] | 0 | 0 | 36867774 |
| thinker_prefill | ['joint_deepstack_pack'] | 8276252295168 | 10687752810 | 168610441216 |
| thinker_decode_0 | ['thinker_prefill'] | 7073955840 | 12358593 | 6239781896 |
| thinker_decode_1 | ['thinker_decode_0'] | 7074742272 | 12364737 | 6239892488 |
| thinker_decode_2 | ['thinker_decode_1'] | 7075528704 | 12370881 | 6240003080 |
| thinker_decode_3 | ['thinker_decode_2'] | 7076315136 | 12377025 | 6240113672 |
| thinker_decode_4 | ['thinker_decode_3'] | 7077101568 | 12383169 | 6240224264 |
| thinker_decode_5 | ['thinker_decode_4'] | 7077888000 | 12389313 | 6240334856 |
| thinker_decode_6 | ['thinker_decode_5'] | 7078674432 | 12395457 | 6240445448 |
| thinker_decode_7 | ['thinker_decode_6'] | 7079460864 | 12401601 | 6240556040 |
| thinker_decode_8 | ['thinker_decode_7'] | 7080247296 | 12407745 | 6240666632 |
| thinker_decode_9 | ['thinker_decode_8'] | 7081033728 | 12413889 | 6240777224 |
| thinker_decode_10 | ['thinker_decode_9'] | 7081820160 | 12420033 | 6240887816 |
| thinker_decode_11 | ['thinker_decode_10'] | 7082606592 | 12426177 | 6240998408 |
| thinker_decode_12 | ['thinker_decode_11'] | 7083393024 | 12432321 | 6241109000 |
| thinker_decode_13 | ['thinker_decode_12'] | 7084179456 | 12438465 | 6241219592 |
| thinker_decode_14 | ['thinker_decode_13'] | 7084965888 | 12444609 | 6241330184 |
| thinker_decode_15 | ['thinker_decode_14'] | 7085752320 | 12450753 | 6241440776 |
| thinker_decode_16 | ['thinker_decode_15'] | 7086538752 | 12456897 | 6241551368 |
| thinker_decode_17 | ['thinker_decode_16'] | 7087325184 | 12463041 | 6241661960 |
| thinker_decode_18 | ['thinker_decode_17'] | 7088111616 | 12469185 | 6241772552 |
| thinker_decode_19 | ['thinker_decode_18'] | 7088898048 | 12475329 | 6241883144 |
| thinker_decode_20 | ['thinker_decode_19'] | 7089684480 | 12481473 | 6241993736 |
| thinker_decode_21 | ['thinker_decode_20'] | 7090470912 | 12487617 | 6242104328 |
| thinker_decode_22 | ['thinker_decode_21'] | 7091257344 | 12493761 | 6242214920 |
| thinker_decode_23 | ['thinker_decode_22'] | 7092043776 | 12499905 | 6242325512 |
| thinker_decode_24 | ['thinker_decode_23'] | 7092830208 | 12506049 | 6242436104 |
| thinker_decode_25 | ['thinker_decode_24'] | 7093616640 | 12512193 | 6242546696 |
| thinker_decode_26 | ['thinker_decode_25'] | 7094403072 | 12518337 | 6242657288 |
| thinker_decode_27 | ['thinker_decode_26'] | 7095189504 | 12524481 | 6242767880 |
| thinker_decode_28 | ['thinker_decode_27'] | 7095975936 | 12530625 | 6242878472 |
| thinker_decode_29 | ['thinker_decode_28'] | 7096762368 | 12536769 | 6242989064 |
| thinker_decode_30 | ['thinker_decode_29'] | 7097548800 | 12542913 | 6243099656 |

prefill；所有decode逐次工作见JSON。

| 矩阵 | M | K | N | 层重复 | 已汇总FLOPs |
| --- | --- | --- | --- | --- | --- |
| q | 1258 | 2048 | 4096 | 48 | 1013075410944 |
| k | 1258 | 2048 | 512 | 48 | 126634426368 |
| v | 1258 | 2048 | 512 | 48 | 126634426368 |
| o | 1258 | 4096 | 2048 | 48 | 1013075410944 |
| router | 1258 | 2048 | 128 | 48 | 31658606592 |
| expert_gate | 10064 | 2048 | 768 | 48 | 1519613116416 |
| expert_up | 10064 | 2048 | 768 | 48 | 1519613116416 |
| expert_down | 10064 | 768 | 2048 | 48 | 1519613116416 |
| output_head | 1258 | 2048 | 152064 | 1 | 783550513152 |

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

音频缓存身份及实际miss分段：`{"miss_item_indices": [0], "actual_miss_chunk_execution": {"padded_mel_width": 100, "after_cnn_width": 13, "attention_window_positions": 104, "convolution_chunk_batch_limit": 500, "convolution_groups": 1, "retained_cnn_group_outputs_bytes": 1996800, "max_single_group_output_bytes": 1996800}, "actual_miss_segments": [{"audio": 0, "start_embedding": 0, "length": 104}, {"audio": 0, "start_embedding": 104, "length": 26}], "segment_audio_index_scope": "Indices address the compact miss batch, mapped by miss_item_indices.", "required_cache_identity": ["model/source revision", "processed mel content", "dtype", "attention execution path", "batch padded CNN width and resulting segmentation window"], "validity": "Caller asserts cache identity matches the intended encoder execution. Equal embedding counts do not prove equal features. Removing hits may change the padded width/attention segmentation of short miss items; this ledger reports their actual miss batch, not equivalence to an uncached full batch."}`

DeepStack注入：`{"branches": 3, "visual_positions": 1000, "consumer_layers": [0, 1, 2], "additions": 6144000, "gather_clone_add_scatter_interface_bytes": 110592000, "injected_only_during_prefill": true}`

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
