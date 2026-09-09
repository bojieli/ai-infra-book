# omni-input-audio-encoder — qwen3-omni-30b-a3b-instruct

输入：`{"attention_path": "segmented_varlen", "element_bytes": 2, "mel_lengths": [1, 9]}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| matrix_flops | 4,947,107,840 |
| scalar_flops | 3,555,139 |
| parameter_elements | 647,927,168 |
| weight_interface_bytes | 1,295,854,336 |
| activation_read_bytes | 7,323,652 |
| activation_write_bytes | 6,347,776 |
| output_embeddings_per_audio | `[1, 2]` |
| output_embedding_elements | 6,144 |
| output_embedding_bytes | 12,288 |
| padded_cnn_positions | 4 |
| valid_encoder_positions | 3 |
| segmented_bidirectional_pairs | 5 |
| source_unmasked_eager_pairs | 9 |
| persistent_decode_kv_bytes | 0 |
| positional_buffer_elements | 1,920,000 |
| complete_runtime_peak_bytes | `null` |
| predicted_latency_seconds | `null` |

输入音频编码；每行乘repeats。完整chunk与attention分段边界保留在JSON。

组批：`{"padded_mel_width": 9, "after_cnn_width": 2, "attention_window_positions": 16, "convolution_chunk_batch_limit": 500, "convolution_groups": 1, "retained_cnn_group_outputs_bytes": 61440, "max_single_group_output_bytes": 61440}`

| 算子 | 类型 | 形状 | repeats | 矩阵FLOPs | 标量工作 | 特殊操作 |
| --- | --- | --- | --- | --- | --- | --- |
| mel_chunk_pad | copy | {'input': [128, 10], 'output': [2, 1, 128, 9]} | 1 | 0 | 0 | {} |
| conv2d_1 | conv2d | {'input': [2, 1, 128, 9], 'weight': [480, 1, 3, 3], 'output': [2, 480, 64, 5]} | 1 | 5529600 | 307200 | {} |
| conv_gelu_1 | activation | {'elements': 307200} | 1 | 0 | 0 | {'gelu': 307200} |
| conv2d_2 | conv2d | {'input': [2, 480, 64, 5], 'weight': [480, 480, 3, 3], 'output': [2, 480, 32, 3]} | 1 | 796262400 | 92160 | {} |
| conv_gelu_2 | activation | {'elements': 92160} | 1 | 0 | 0 | {'gelu': 92160} |
| conv2d_3 | conv2d | {'input': [2, 480, 32, 3], 'weight': [480, 480, 3, 3], 'output': [2, 480, 16, 2]} | 1 | 265420800 | 30720 | {} |
| conv_gelu_3 | activation | {'elements': 30720} | 1 | 0 | 0 | {'gelu': 30720} |
| concat_and_layout | copy | {'concat': [2, 480, 16, 2], 'flatten': [4, 7680]} | 1 | 0 | 0 | {} |
| conv_out | linear | {'input': [4, 7680], 'weight': [1280, 7680], 'output': [4, 1280]} | 1 | 78643200 | 0 | {} |
| chunk_position_add | position | {'padded': [2, 2, 1280]} | 1 | 0 | 5120 | {} |
| remove_padding | gather | {'input': [2, 2, 1280], 'output': [3, 1280]} | 1 | 0 | 0 | {} |
| attention_norm | layernorm | {'input': [3, 1280]} | 32 | 0 | 26883 | {'rsqrt': 3} |
| q | linear | {'input': [3, 1280], 'weight': [1280, 1280], 'output': [3, 1280]} | 32 | 9830400 | 3840 | {} |
| k | linear | {'input': [3, 1280], 'weight': [1280, 1280], 'output': [3, 1280]} | 32 | 9830400 | 3840 | {} |
| v | linear | {'input': [3, 1280], 'weight': [1280, 1280], 'output': [3, 1280]} | 32 | 9830400 | 3840 | {} |
| qk | attention | {'heads': 20, 'head_dim': 64, 'positions': 3, 'accounted_pairs': 5} | 32 | 12800 | 0 | {} |
| scale_softmax | attention | {'heads': 20, 'pairs': 5} | 32 | 0 | 340 | {'exp': 100, 'max_compare': 40} |
| pv | attention | {'heads': 20, 'head_dim': 64, 'positions': 3, 'accounted_pairs': 5} | 32 | 12800 | 0 | {} |
| attention_output | linear | {'input': [3, 1280], 'weight': [1280, 1280], 'output': [3, 1280]} | 32 | 9830400 | 3840 | {} |
| attention_residual | residual | {'input': [3, 1280]} | 32 | 0 | 3840 | {} |
| ffn_norm | layernorm | {'input': [3, 1280]} | 32 | 0 | 26883 | {'rsqrt': 3} |
| ffn_fc1 | linear | {'input': [3, 1280], 'weight': [5120, 1280], 'output': [3, 5120]} | 32 | 39321600 | 15360 | {} |
| ffn_gelu | activation | {'elements': 15360} | 32 | 0 | 0 | {'gelu': 15360} |
| ffn_fc2 | linear | {'input': [3, 5120], 'weight': [1280, 5120], 'output': [3, 1280]} | 32 | 39321600 | 3840 | {} |
| ffn_residual | residual | {'input': [3, 1280]} | 32 | 0 | 3840 | {} |
| post_norm | layernorm | {'input': [3, 1280]} | 1 | 0 | 26883 | {'rsqrt': 3} |
| proj1 | linear | {'input': [3, 1280], 'weight': [1280, 1280], 'output': [3, 1280]} | 1 | 9830400 | 3840 | {} |
| projection_gelu | activation | {'elements': 3840} | 1 | 0 | 0 | {'gelu': 3840} |
| proj2_to_thinker | linear | {'input': [3, 1280], 'weight': [2048, 1280], 'output': [3, 2048]} | 1 | 15728640 | 6144 | {} |

计量条件：

- Input understanding audio encoder only, not Talker/output codec. Inputs are valid precomputed mel frames; resampling/STFT/mel filter/log normalization and raw feature masking are separate.
- Every utterance is split into at most 100-frame CNN chunks, then ALL chunks in this call are padded to the largest valid chunk before batches of at most 500 chunks are convolved. Output length is 13*floor(N/100)+ceil((N%100)/8), not ceil(N/8).
- Non-causal attention segments are built per original audio after padding removal; their maximum is batch-padded CNN width times 8. Thus mixed batches can alter the segmentation window of a short input. No autoregressive KV cache is retained.
- Default segmented_varlen counts full bidirectional squares within cu_seqlens blocks. The locked source calls encoder layers without its prepared block mask; source_unmasked_eager therefore counts one total square and is not semantically equivalent. No backend is executed here.
- All learned encoder weights, convolution/linear biases, LayerNorm scale/bias and projection to Thinker are included as logical parameter elements. Sinusoidal positions are a separate buffer. Checkpoint-header validation and mixed runtime formats are not claimed.
- Matrix FMA=2; bias/LayerNorm/residual/softmax scalar work and GELU/exp/rsqrt primitive counts are separate. Conv products include source padding. Operator bytes are declared interfaces, not measured HBM or allocation peaks.
- BF16-size/FP32-size uniform operands are comparison formats. Source FP16-only clipping is not executed in this declared BF16/FP32 path. Library dispatch, actual dtype conversions, mask construction, kernel padding and preprocessing remain runtime gaps.

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
