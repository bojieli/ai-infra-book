# omni-input-audio-encoder — qwen3-omni-30b-a3b-instruct

输入：`{"attention_path": "segmented_varlen", "element_bytes": 2, "mel_lengths": [801]}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| matrix_flops | 174,959,943,680 |
| scalar_flops | 154,769,705 |
| parameter_elements | 647,927,168 |
| weight_interface_bytes | 1,295,854,336 |
| activation_read_bytes | 295,347,573 |
| activation_write_bytes | 261,163,520 |
| output_embeddings_per_audio | `[105]` |
| output_embedding_elements | 215,040 |
| output_embedding_bytes | 430,080 |
| padded_cnn_positions | 117 |
| valid_encoder_positions | 105 |
| segmented_bidirectional_pairs | 10,817 |
| source_unmasked_eager_pairs | 11,025 |
| persistent_decode_kv_bytes | 0 |
| positional_buffer_elements | 1,920,000 |
| complete_runtime_peak_bytes | `null` |
| predicted_latency_seconds | `null` |

输入音频编码；每行乘repeats。完整chunk与attention分段边界保留在JSON。

组批：`{"padded_mel_width": 100, "after_cnn_width": 13, "attention_window_positions": 104, "convolution_chunk_batch_limit": 500, "convolution_groups": 1, "retained_cnn_group_outputs_bytes": 1797120, "max_single_group_output_bytes": 1797120}`

| 算子 | 类型 | 形状 | repeats | 矩阵FLOPs | 标量工作 | 特殊操作 |
| --- | --- | --- | --- | --- | --- | --- |
| mel_chunk_pad | copy | {'input': [128, 801], 'output': [9, 1, 128, 100]} | 1 | 0 | 0 | {} |
| conv2d_1 | conv2d | {'input': [9, 1, 128, 100], 'weight': [480, 1, 3, 3], 'output': [9, 480, 64, 50]} | 1 | 248832000 | 13824000 | {} |
| conv_gelu_1 | activation | {'elements': 13824000} | 1 | 0 | 0 | {'gelu': 13824000} |
| conv2d_2 | conv2d | {'input': [9, 480, 64, 50], 'weight': [480, 480, 3, 3], 'output': [9, 480, 32, 25]} | 1 | 29859840000 | 3456000 | {} |
| conv_gelu_2 | activation | {'elements': 3456000} | 1 | 0 | 0 | {'gelu': 3456000} |
| conv2d_3 | conv2d | {'input': [9, 480, 32, 25], 'weight': [480, 480, 3, 3], 'output': [9, 480, 16, 13]} | 1 | 7763558400 | 898560 | {} |
| conv_gelu_3 | activation | {'elements': 898560} | 1 | 0 | 0 | {'gelu': 898560} |
| concat_and_layout | copy | {'concat': [9, 480, 16, 13], 'flatten': [117, 7680]} | 1 | 0 | 0 | {} |
| conv_out | linear | {'input': [117, 7680], 'weight': [1280, 7680], 'output': [117, 1280]} | 1 | 2300313600 | 0 | {} |
| chunk_position_add | position | {'padded': [9, 13, 1280]} | 1 | 0 | 149760 | {} |
| remove_padding | gather | {'input': [9, 13, 1280], 'output': [105, 1280]} | 1 | 0 | 0 | {} |
| attention_norm | layernorm | {'input': [105, 1280]} | 32 | 0 | 940905 | {'rsqrt': 105} |
| q | linear | {'input': [105, 1280], 'weight': [1280, 1280], 'output': [105, 1280]} | 32 | 344064000 | 134400 | {} |
| k | linear | {'input': [105, 1280], 'weight': [1280, 1280], 'output': [105, 1280]} | 32 | 344064000 | 134400 | {} |
| v | linear | {'input': [105, 1280], 'weight': [1280, 1280], 'output': [105, 1280]} | 32 | 344064000 | 134400 | {} |
| qk | attention | {'heads': 20, 'head_dim': 64, 'positions': 105, 'accounted_pairs': 10817} | 32 | 27691520 | 0 | {} |
| scale_softmax | attention | {'heads': 20, 'pairs': 10817} | 32 | 0 | 863260 | {'exp': 216340, 'max_compare': 214240} |
| pv | attention | {'heads': 20, 'head_dim': 64, 'positions': 105, 'accounted_pairs': 10817} | 32 | 27691520 | 0 | {} |
| attention_output | linear | {'input': [105, 1280], 'weight': [1280, 1280], 'output': [105, 1280]} | 32 | 344064000 | 134400 | {} |
| attention_residual | residual | {'input': [105, 1280]} | 32 | 0 | 134400 | {} |
| ffn_norm | layernorm | {'input': [105, 1280]} | 32 | 0 | 940905 | {'rsqrt': 105} |
| ffn_fc1 | linear | {'input': [105, 1280], 'weight': [5120, 1280], 'output': [105, 5120]} | 32 | 1376256000 | 537600 | {} |
| ffn_gelu | activation | {'elements': 537600} | 32 | 0 | 0 | {'gelu': 537600} |
| ffn_fc2 | linear | {'input': [105, 5120], 'weight': [1280, 5120], 'output': [105, 1280]} | 32 | 1376256000 | 134400 | {} |
| ffn_residual | residual | {'input': [105, 1280]} | 32 | 0 | 134400 | {} |
| post_norm | layernorm | {'input': [105, 1280]} | 1 | 0 | 940905 | {'rsqrt': 105} |
| proj1 | linear | {'input': [105, 1280], 'weight': [1280, 1280], 'output': [105, 1280]} | 1 | 344064000 | 134400 | {} |
| projection_gelu | activation | {'elements': 134400} | 1 | 0 | 0 | {'gelu': 134400} |
| proj2_to_thinker | linear | {'input': [105, 1280], 'weight': [2048, 1280], 'output': [105, 2048]} | 1 | 550502400 | 215040 | {} |

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
