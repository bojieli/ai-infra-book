# omni-vision-encoding — qwen3-omni-30b-a3b-instruct

输入：`{"cache_hits": [true, true], "dtype": "bf16", "grid_thw": [[1, 40, 40], [4, 20, 30]], "seconds_per_grid": [null, null]}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| encoder_items_executed | 0 |
| encoder_cache_hits | 2 |
| executed_patches | 0 |
| executed_merged_positions | 0 |
| delivered_visual_positions | 1,000 |
| executed_bidirectional_pairs | 0 |
| matrix_flops | 0 |
| scalar_flops | 0 |
| logical_vision_parameters | 538,631,408 |
| parameter_bytes_declared_dtype | 1,077,262,816 |
| complete_encoder_feature_bytes | 16,384,000 |
| feature_components | 4 |
| component_width | 2,048 |
| interface_read_bytes | 0 |
| interface_write_bytes | 0 |
| persistent_decode_kv_bytes | 0 |
| complete_runtime_peak_bytes | `null` |
| predicted_latency_seconds | `null` |

Omni视觉编码；每行FLOPs已乘repeats。时间块之间不做视觉attention。

| 矩阵 | 输入 | 权重/右矩阵 | repeats | 矩阵FLOPs | 读/写接口bytes |
| --- | --- | --- | --- | --- | --- |
| patch_embedding | [0, 1536] | [1536, 1152] | 1 | 0 | 0/0 |
| block_qkv | [0, 1152] | [1152, 3456] | 27 | 0 | 0/0 |
| block_attention_output | [0, 1152] | [1152, 1152] | 27 | 0 | 0/0 |
| block_mlp_up | [0, 1152] | [1152, 4304] | 27 | 0 | 0/0 |
| block_mlp_down | [0, 4304] | [4304, 1152] | 27 | 0 | 0/0 |
| final_up | [0, 4608] | [4608, 4608] | 1 | 0 | 0/0 |
| final_out | [0, 4608] | [4608, 2048] | 1 | 0 | 0/0 |
| deepstack_8_up | [0, 4608] | [4608, 4608] | 1 | 0 | 0/0 |
| deepstack_8_out | [0, 4608] | [4608, 2048] | 1 | 0 | 0/0 |
| deepstack_16_up | [0, 4608] | [4608, 4608] | 1 | 0 | 0/0 |
| deepstack_16_out | [0, 4608] | [4608, 2048] | 1 | 0 | 0/0 |
| deepstack_24_up | [0, 4608] | [4608, 4608] | 1 | 0 | 0/0 |
| deepstack_24_out | [0, 4608] | [4608, 2048] | 1 | 0 | 0/0 |

| 非矩阵步骤 | 元素数 | repeats | 已汇总标量工作 | 已汇总特殊函数 |
| --- | --- | --- | --- | --- |
| patch_embedding_bias | 0 | 1 | 0 | {} |
| position_interpolate | 0 | 1 | 0 | {} |
| position_temporal_repeat_layout | 0 | 1 | 0 | {} |
| position_add | 0 | 1 | 0 | {} |
| rope_frequency_outer | 0 | 1 | 0 | {} |
| rope_gather_duplicate_trig | 0 | 1 | 0 | {'cos': 0, 'sin': 0} |
| block_norm1 | 0 | 27 | 0 | {'rsqrt': 0} |
| block_qkv_bias | 0 | 27 | 0 | {} |
| block_rope_qk | 0 | 27 | 0 | {'sign_negation': 0} |
| block_attention_output_bias | 0 | 27 | 0 | {} |
| block_residual1 | 0 | 27 | 0 | {} |
| block_norm2 | 0 | 27 | 0 | {'rsqrt': 0} |
| block_mlp_up_bias | 0 | 27 | 0 | {} |
| block_gelu_tanh | 0 | 27 | 0 | {'tanh': 0} |
| block_mlp_down_bias | 0 | 27 | 0 | {} |
| block_residual2 | 0 | 27 | 0 | {} |
| final_norm | 0 | 1 | 0 | {'rsqrt': 0} |
| final_up_bias | 0 | 1 | 0 | {} |
| final_gelu_erf | 0 | 1 | 0 | {'erf': 0} |
| final_out_bias | 0 | 1 | 0 | {} |
| deepstack_8_norm | 0 | 1 | 0 | {'rsqrt': 0} |
| deepstack_8_up_bias | 0 | 1 | 0 | {} |
| deepstack_8_gelu_erf | 0 | 1 | 0 | {'erf': 0} |
| deepstack_8_out_bias | 0 | 1 | 0 | {} |
| deepstack_16_norm | 0 | 1 | 0 | {'rsqrt': 0} |
| deepstack_16_up_bias | 0 | 1 | 0 | {} |
| deepstack_16_gelu_erf | 0 | 1 | 0 | {'erf': 0} |
| deepstack_16_out_bias | 0 | 1 | 0 | {} |
| deepstack_24_norm | 0 | 1 | 0 | {'rsqrt': 0} |
| deepstack_24_up_bias | 0 | 1 | 0 | {} |
| deepstack_24_gelu_erf | 0 | 1 | 0 | {'erf': 0} |
| deepstack_24_out_bias | 0 | 1 | 0 | {} |

逐项grid/时间/命中：`[{"index": 0, "grid_thw": [1, 40, 40], "cache_hit": true, "premerge_patches": 1600, "merged_positions": 400, "attention_pairs_executed": 0, "feature_components": 4, "feature_bytes": 6553600, "temporal_position_ids": null, "temporal_position_note": "Thinker time scale times explicit seconds; does not change vision attention or patch count."}, {"index": 1, "grid_thw": [4, 20, 30], "cache_hit": true, "premerge_patches": 2400, "merged_positions": 600, "attention_pairs_executed": 0, "feature_components": 4, "feature_bytes": 9830400, "temporal_position_ids": null, "temporal_position_note": "Thinker time scale times explicit seconds; does not change vision attention or patch count."}]`

独立Thinker注入接口：`{"visual_encoder_layers": [8, 16, 24], "thinker_destination_layers": [0, 1, 2], "injected_feature_bytes": 12288000, "injection_adds": 6144000, "injection_gather_clone_add_scatter_interface_bytes": 110592000, "note": "Separate consumer-side source gather→clone→add→scatter: 9 operand transfers per element; excluded from encoder totals. Final features fill the original visual positions; DeepStack does not multiply their count."}`

计量条件：

- Already processed patch grids only. Static image temporal duplication is in the 1536-element patch contraction; no raw image decode/resize/normalization or frame sampling is counted.
- Miss items form one packed encoder call: projections consume total patches and share one weight read per matrix/layer; attention remains independent for each temporal spatial block. Cache-hit items skip encoding but still deliver all four feature components and participate in Thinker injection.
- 27 layers, width1152, FFN4304, 16 heads of72, final and three DeepStack mergers of width4608 to2048 follow official Omni config. Position table2304 follows the locked config class default, not VL4 substitution.
- Spatial learned positions are interpolated once per spatial grid then repeated over time. Interpolation weights/sums use embedding dtype in this source; rotary table and Q/K rotary arithmetic use FP32 interfaces. They must not be copied from the VL4 FP32 interpolation byte convention.
- FA2 cu_seqlens and the explicit non-FA2 split both prohibit attention across temporal blocks/items. Total pairs=sum(T*(Hgrid*Wgrid)^2), never the square of total packed tokens.
- Scalar formulas declare LayerNorm/GELU/softmax arithmetic; special functions are separate primitive counts. Index construction, interpolation coefficient arithmetic, inv_freq initialization, casts/backend fusion and sampling metadata processing are not claimed as complete runtime instructions.
- Cache hits are caller-verified identities, not inferred from equal dimensions. Declared interfaces are not measured HBM or residency peaks. Logical parameters include bias/norm/position tensors but have not been checked against checkpoint headers.

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
